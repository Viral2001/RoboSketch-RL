"""
RoboSketch-RL  |  H4 - does a camera see what kinematics cannot? (proposal 4.3)
-------------------------------------------------
THE EXPERIMENT THE PROJECT RESTS ON. D01 (Lee et al., ICRA 2022) draws well with
no camera at all, synchronising through forward kinematics, and argues that
being camera-free is an ADVANTAGE. If that holds, D01 is a complete answer to
this project's motivation and there is no reason to build any of this.

The reply has to be that a camera detects errors kinematics cannot. Three
disturbances make that concrete, and the third makes it unarguable:

  slip          the pen is knocked sideways; the command stream is unchanged
  paper_shift   the sheet slides under the pen; every later stroke lands wrong
  ink_failure   the pen stops depositing ink. Forward kinematics reports a
                perfect drawing. The paper is blank. There is no kinematic
                signal whatsoever - the error is invisible BY CONSTRUCTION.

FOUR CONDITIONS:

  open_loop   an analytic tracer that follows the target outline and never looks
              at anything. No policy, no feedback - the floor.
  true        privileged: the agent sees the real ink. No robot has this; it is
              the ceiling, and the gap between it and `camera` is what
              perception costs.
  fk          D01's condition: the agent sees what its own kinematics say it
              drew - commanded positions, ink assumed to have landed, no
              knowledge that anything went wrong.
  camera      ours: the agent sees a photograph of the paper as it is.

TRAINED ON THE WHOLE FAMILY, EVALUATED ON EACH KIND. Each arm trains with
`disturbance="mixed"` and is then scored on none / slip / paper_shift /
ink_failure separately. Training clean and testing disturbed would push every
policy out of distribution and measure brittleness; the question here is about
information, so each arm gets a fair chance to learn to use whatever it can see.

Scoring is always TRUE IoU of the real paper. An arm that believes it drew
beautifully earns nothing for it - which is the entire point.

  conda run -n robosketch python rl/h4_experiment.py --seeds 0 100 --timesteps 200000
  conda run -n robosketch python rl/h4_experiment.py --aggregate
"""
import argparse
import json
import os
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import disturb as DIST
from draw_env import DrawEnv
from experiment import warn_config_drift

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results", "h4_experiment.jsonl")
SHAPES = ["line", "circle", "square", "triangle"]
ARMS = ["open_loop", "true", "fk", "camera"]
EVAL_KINDS = ["none", "slip", "paper_shift", "ink_failure"]


# two-sided 5% Student-t critical values by degrees of freedom (no scipy in env)
_T_CRIT = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365,
           8: 2.306, 9: 2.262, 10: 2.228, 11: 2.201, 12: 2.179, 13: 2.160,
           14: 2.145, 15: 2.131, 16: 2.120, 17: 2.110, 18: 2.101, 19: 2.093,
           20: 2.086}


def _tcrit(n):
    return _T_CRIT.get(n - 1, 1.96) if n > 1 else float("nan")


def _tstat(d):
    d = np.asarray(d, float)
    if d.size < 2:
        return (float(d.mean()) if d.size else float("nan")), float("nan")
    se = d.std(ddof=1) / np.sqrt(d.size)
    return float(d.mean()), (float(d.mean() / se) if se > 0 else float("nan"))


def _sd(x):
    x = np.asarray(x, float)
    return float(x.std(ddof=1)) if x.size > 1 else 0.0


def load_done():
    import glob as _glob
    done = {}
    for path in sorted(_glob.glob(RESULTS.replace(".jsonl", "*.jsonl"))):
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    r = json.loads(line)
                    done[(r["shape"], r["arm"], r["seed"])] = r
    return done


def _env(shape, arm, kind, seed, max_steps, step_size):
    """One environment configured for an arm. `camera` is the only arm that
    needs a perception model; it uses the FIXED camera so this experiment is
    about feedback and not about camera realism (that is proposal 4.1)."""
    kw = dict(shape=shape, max_steps=max_steps, step_size_m=step_size,
              disturbance=kind, seed=seed)
    if arm == "camera":
        kw.update(obs_source="camera", cam_split="fixed", reward_mode="vision")
    elif arm == "fk":
        kw.update(obs_source="fk")
    else:                        # "true" and the open-loop baseline
        kw.update(obs_source="true")
    return DrawEnv(**kw)


def open_loop_actions(env):
    """An analytic tracer: walk the target outline, ignoring all feedback.

    This is condition (a). It is not a policy - it is the plan a classical
    IK pipeline would execute open loop. It cannot react to anything, so its
    score under each disturbance is the cost of having no feedback at all.
    """
    import cv2
    tgt = env.target
    cnts, _ = cv2.findContours((tgt > 127).astype(np.uint8) * 255,
                               cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    pts = max(cnts, key=cv2.contourArea).reshape(-1, 2)      # (col, row)
    # start at the contour point nearest the pen's start, then walk in order
    c0, r0 = env._world_to_px(*env.pen_xy)
    k = int(np.argmin((pts[:, 0] - c0) ** 2 + (pts[:, 1] - r0) ** 2))
    pts = np.roll(pts, -k, axis=0)
    step_px = env.step_size / (2 * 0.10) * (env.canvas_res - 1)
    out, cur = [], np.array([c0, r0], float)
    for i in range(env.max_steps):
        tgt_pt = pts[min(int(i * len(pts) / env.max_steps), len(pts) - 1)]
        d = tgt_pt - cur
        n = np.hypot(*d)
        if n > 1e-6:
            d = d / n * min(n, step_px)
        cur = cur + d
        # canvas dcol/drow -> action units (dx right, dy UP)
        out.append(np.array([d[0] / step_px, -d[1] / step_px, 1.0], np.float32))
    return out


def evaluate(model, shape, arm, seed, max_steps, step_size, eval_eps):
    """Score one arm on every disturbance kind. Always TRUE IoU."""
    out = {}
    for kind in EVAL_KINDS:
        ious = []
        for ep in range(eval_eps):
            env = _env(shape, arm, kind, 60_000 + seed * 100 + ep, max_steps, step_size)
            obs, _ = env.reset(seed=60_000 + seed * 100 + ep)
            if arm == "open_loop":
                plan = open_loop_actions(env)
            done, t, info = False, 0, {}
            while not done:
                if arm == "open_loop":
                    a = plan[min(t, len(plan) - 1)]
                else:
                    a, _ = model.predict(obs, deterministic=True)
                obs, r, term, trunc, info = env.step(a)
                done = term or trunc
                t += 1
            ious.append(info["iou"])
            env.close()
        out[kind] = (float(np.mean(ious)), _sd(ious))
    return out


def train_and_eval(shape, arm, seed, timesteps, n_envs, max_steps, step_size,
                   eval_eps):
    model = None
    if arm != "open_loop":
        from stable_baselines3 import PPO
        from stable_baselines3.common.vec_env import DummyVecEnv, VecMonitor

        def mk(i):
            return lambda: _env(shape, arm, "mixed", seed * 97 + i, max_steps, step_size)

        venv = VecMonitor(DummyVecEnv([mk(i) for i in range(n_envs)]))
        model = PPO("CnnPolicy", venv, verbose=0, seed=seed,
                    n_steps=512, batch_size=256, n_epochs=6, gamma=0.99,
                    ent_coef=0.02, learning_rate=3e-4)
        model.learn(total_timesteps=timesteps, progress_bar=False)
        venv.close()
    return evaluate(model, shape, arm, seed, max_steps, step_size, eval_eps)


def run(args):
    os.makedirs(os.path.dirname(RESULTS), exist_ok=True)
    shapes = args.shapes or SHAPES
    shard = RESULTS if not args.shard else RESULTS.replace(".jsonl", f"_{args.shard}.jsonl")
    done = load_done()
    warn_config_drift(done, {"timesteps": args.timesteps, "max_steps": args.max_steps})
    combos = [(s, a, k) for k in args.seeds for s in shapes for a in ARMS]
    todo = [c for c in combos if c not in done]
    print(f"{len(done)} runs done, {len(todo)} to go\n", flush=True)
    for i, (shape, arm, seed) in enumerate(todo, 1):
        print(f"[{i}/{len(todo)}] {shape:8s} {arm:9s} seed={seed} ...", flush=True)
        res = train_and_eval(shape, arm, seed, args.timesteps, args.n_envs,
                             args.max_steps, args.step_size, args.eval_eps)
        rec = {"shape": shape, "arm": arm, "seed": seed,
               "timesteps": args.timesteps, "max_steps": args.max_steps}
        for k, (m, sd) in res.items():
            rec[f"iou_{k}"] = round(m, 4)
            rec[f"sd_{k}"] = round(sd, 4)
        with open(shard, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")
        print("        -> " + "  ".join(f"{k}:{res[k][0]:.3f}" for k in EVAL_KINDS),
              flush=True)
    print("\ndone.", flush=True)
    if not args.shard:
        aggregate()


# Figures are drawn with OpenCV, not matplotlib, for the reason recorded in
# `rl/h3_exploitation.py`: PyBullet on Windows only resolves through conda-forge,
# so the `robosketch` env is kept minimal and the solver is not disturbed for a
# plotting library.
_ARM_COLOR = {"open_loop": (150, 150, 150), "true": (60, 60, 60),
              "fk": (60, 140, 200), "camera": (60, 70, 200)}
_ARM_LABEL = {"open_loop": "open_loop (no feedback)", "true": "true (privileged)",
              "fk": "fk (D01's condition)", "camera": "camera (ours)"}


class _Panel:
    """A minimal cv2 bar-chart panel: data coords in, pixels out."""

    F = cv2.FONT_HERSHEY_SIMPLEX

    def __init__(self, img, x0, y0, w, h, ylim, title, ylabel):
        self.img, self.x0, self.y0, self.w, self.h, self.ylim = img, x0, y0, w, h, ylim
        cv2.rectangle(img, (x0, y0 - h), (x0 + w, y0), (215, 215, 215), 1)
        cv2.putText(img, title, (x0, y0 - h - 16), self.F, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
        cv2.putText(img, ylabel, (x0 - 58, y0 - h - 34), self.F, 0.42,
                    (110, 110, 110), 1, cv2.LINE_AA)
        for f in np.linspace(0, 1, 7):
            yv = ylim[0] + f * (ylim[1] - ylim[0])
            yy = self.py(yv)
            cv2.line(img, (x0 + 1, yy), (x0 + w - 1, yy), (238, 238, 238), 1)
            cv2.putText(img, "%+.2f" % yv, (x0 - 52, yy + 4), self.F, 0.4,
                        (110, 110, 110), 1, cv2.LINE_AA)
        yz = self.py(0.0)                      # zero line: "no change"
        cv2.line(img, (x0 + 1, yz), (x0 + w - 1, yz), (120, 120, 120), 1, cv2.LINE_AA)

    def py(self, y):
        f = (y - self.ylim[0]) / max(1e-9, self.ylim[1] - self.ylim[0])
        return int(self.y0 - f * self.h)

    def bar(self, cx, half, value, color):
        yz, yv = self.py(0.0), self.py(value)
        cv2.rectangle(self.img, (cx - half, min(yz, yv)), (cx + half, max(yz, yv)),
                      color, -1)

    def whisker(self, cx, lo, hi, color=(40, 40, 40)):
        cv2.line(self.img, (cx, self.py(lo)), (cx, self.py(hi)), color, 1, cv2.LINE_AA)
        for v in (lo, hi):
            cv2.line(self.img, (cx - 4, self.py(v)), (cx + 4, self.py(v)), color, 1,
                     cv2.LINE_AA)

    def hline(self, y, color, dashed=True):
        yy = self.py(y)
        step = 10 if dashed else self.w
        for x in range(self.x0 + 1, self.x0 + self.w - 1, step):
            cv2.line(self.img, (x, yy), (min(x + 5, self.x0 + self.w - 1), yy),
                     color, 1, cv2.LINE_AA)

    def xlabel(self, cx, text, dy=18, color=(70, 70, 70), scale=0.44):
        (tw, _), _ = cv2.getTextSize(text, self.F, scale, 1)
        cv2.putText(self.img, text, (cx - tw // 2, self.y0 + dy), self.F, scale,
                    color, 1, cv2.LINE_AA)


def _figure(done, common):
    """Two panels: what each arm LOSES to a disturbance, and the paired test.

    The left panel is the honest version of "who is more robust": each arm is
    measured against ITS OWN clean score, because the arms do not start level.
    The right panel is the pre-registered primary endpoint, with the
    significance threshold drawn so a reader can see whether it is cleared
    rather than taking a verdict on trust.
    """
    import cv2 as _cv2
    kinds = EVAL_KINDS[1:]
    W, H = 1360, 600
    img = np.full((H, W, 3), 255, np.uint8)
    _cv2.putText(img, "H4: does seeing the paper beat believing your kinematics?",
                 (46, 40), _Panel.F, 0.72, (0, 0, 0), 2, _cv2.LINE_AA)
    _cv2.putText(img, "all arms trained on the mixed disturbance family; scored on TRUE IoU "
                 "of the real paper; n=%d (shape, seed) cells" % len(common),
                 (46, 64), _Panel.F, 0.45, (110, 110, 110), 1, _cv2.LINE_AA)

    drops = {a: [] for a in ARMS}
    for a in ARMS:
        for k in kinds:
            v = [done[(s, a, sd)]["iou_none"] - done[(s, a, sd)]["iou_%s" % k]
                 for s, sd in common]
            drops[a].append(float(np.mean(v)))
    lo = min(0.0, min(min(v) for v in drops.values())) - 0.02
    hi = max(0.0, max(max(v) for v in drops.values())) + 0.04
    p1 = _Panel(img, 110, 500, 560, 380, (lo, hi),
                "IoU lost to the disturbance, vs that arm's own clean score",
                "lost IoU (higher = hurt more)")
    gw = 560 // len(kinds)
    for ki, k in enumerate(kinds):
        base = 110 + ki * gw + gw // 2
        for ai, a in enumerate(ARMS):
            cx = base + int((ai - 1.5) * gw / 5.2)
            p1.bar(cx, int(gw / 12), drops[a][ki], _ARM_COLOR[a])
        p1.xlabel(base, k)
    for ai, a in enumerate(ARMS):
        y = 142 + ai * 18
        _cv2.rectangle(img, (124, y - 8), (140, y + 2), _ARM_COLOR[a], -1)
        _cv2.putText(img, _ARM_LABEL[a], (146, y), _Panel.F, 0.42, _ARM_COLOR[a], 1,
                     _cv2.LINE_AA)

    dids, ses = [], []
    for k in kinds:
        d = np.array([(done[(s, "camera", sd)]["iou_%s" % k]
                       - done[(s, "camera", sd)]["iou_none"])
                      - (done[(s, "fk", sd)]["iou_%s" % k]
                         - done[(s, "fk", sd)]["iou_none"]) for s, sd in common], float)
        dids.append(float(d.mean()))
        ses.append(float(d.std(ddof=1) / np.sqrt(d.size)) if d.size > 1 else 0.0)
    crit = _tcrit(len(common))
    span = max([abs(m) + s for m, s in zip(dids, ses)] + [crit * max(ses + [1e-6])]) * 1.35
    p2 = _Panel(img, 830, 500, 440, 380, (-span, span),
                "PRIMARY: paired difference-in-differences, camera - fk",
                "camera degrades LESS (>0) / MORE (<0)")
    gw2 = 440 // len(kinds)
    for ki, k in enumerate(kinds):
        cx = 830 + ki * gw2 + gw2 // 2
        p2.bar(cx, int(gw2 / 5), dids[ki], (60, 70, 200) if dids[ki] > 0 else (200, 70, 60))
        p2.whisker(cx, dids[ki] - ses[ki], dids[ki] + ses[ki])
        p2.xlabel(cx, k)
        p2.xlabel(cx, "%+.3f" % dids[ki], dy=34, color=(40, 40, 40), scale=0.40)
    for sign in (+1, -1):
        p2.hline(sign * crit * float(np.mean(ses)), (190, 120, 60))
    _cv2.putText(img, "dashed: +/- t(%d)=%.2f x mean SE -- a bar must clear it to be "
                 "significant at 5%%" % (len(common) - 1, crit),
                 (830, 556), _Panel.F, 0.40, (190, 120, 60), 1, _cv2.LINE_AA)
    _cv2.putText(img, "whiskers are +/- 1 SE of the paired difference",
                 (830, 574), _Panel.F, 0.40, (110, 110, 110), 1, _cv2.LINE_AA)
    _cv2.putText(img, "Left panel bars are means over cells, not paired tests: read the "
                 "verdict from the right panel only.",
                 (110, 556), _Panel.F, 0.40, (110, 110, 110), 1, _cv2.LINE_AA)

    out = os.path.join(ROOT, "output", "h4_disturbance_recovery.png")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    _cv2.imwrite(out, img)
    print("\nwrote %s" % out)

def aggregate():
    done = load_done()
    if not done:
        print("no results yet.")
        return
    print("\n=== H4: true IoU under each disturbance, by what the agent can see ===")
    print("all arms trained on the mixed disturbance family, scored on each kind\n")
    hdr = "%-9s %-10s %s %4s" % ("shape", "sees", "".join("%14s" % k for k in EVAL_KINDS), "n")
    print(hdr); print("-" * len(hdr))
    for shape in SHAPES:
        for arm in ARMS:
            cells = [r for (s, a, k), r in done.items() if s == shape and a == arm]
            if not cells:
                continue
            print("%-9s %-10s %s %4d" % (
                shape, arm,
                "".join("%8.3f+/-%.3f" % (np.mean([c[f"iou_{k}"] for c in cells]),
                                          _sd([c[f"iou_{k}"] for c in cells]))
                        for k in EVAL_KINDS),
                len(cells)))
        print()

    common = [(s, k) for s in SHAPES
              for k in sorted({kk for (ss, aa, kk) in done if ss == s})
              if all((s, a, k) in done for a in ARMS)]
    if not common:
        print("no (shape, seed) cell has all four arms yet.")
        return
    print("-" * len(hdr))
    print(f"balanced over {len(common)} (shape, seed) cells with all four arms")
    means = {}
    for arm in ARMS:
        means[arm] = {k: np.mean([done[(s, arm, sd)][f"iou_{k}"] for s, sd in common])
                      for k in EVAL_KINDS}
        print("%-9s %-10s %s" % ("", arm,
              "".join("%14.3f" % means[arm][k] for k in EVAL_KINDS)))

    print("\n=== the question: does seeing the paper beat believing your kinematics? ===")
    # The camera and fk arms do NOT start level: their clean (undisturbed) scores
    # differ. So "camera - fk under disturbance" mostly re-measures that clean gap
    # and says nothing about RECOVERY. The H4 claim is about recovery, so the
    # PRIMARY test is a paired difference-in-differences: within each (shape, seed),
    # how much less does camera lose from its own clean score than fk does?
    # Pre-registered 2026-10-19 (RESEARCH_LOG): verdict only at >= 8 cells,
    # two-sided 5% Student-t critical value for n-1 df.
    gap = np.array([done[(s, "camera", sd)]["iou_none"] - done[(s, "fk", sd)]["iou_none"]
                    for s, sd in common], float)
    mg, tg = _tstat(gap)
    print(f"\n  clean gap (no disturbance), camera - fk: {mg:+.3f}  n={len(gap)}  t={tg:+.2f}")
    print("  (this gap is NOT evidence of recovery - it is subtracted out below)")
    for k in EVAL_KINDS[1:]:
        cam = np.array([done[(s, "camera", sd)][f"iou_{k}"] for s, sd in common], float)
        fk = np.array([done[(s, "fk", sd)][f"iou_{k}"] for s, sd in common], float)
        cam0 = np.array([done[(s, "camera", sd)]["iou_none"] for s, sd in common], float)
        fk0 = np.array([done[(s, "fk", sd)]["iou_none"] for s, sd in common], float)
        did = (cam - cam0) - (fk - fk0)          # > 0: camera degrades LESS than fk
        m, t = _tstat(did)
        ma, ta = _tstat(cam - fk)
        crit = _tcrit(len(did))
        drop_c = means["camera"]["none"] - means["camera"][k]
        drop_f = means["fk"]["none"] - means["fk"][k]
        drop_o = means["open_loop"]["none"] - means["open_loop"][k]
        print(f"\n  {k}:")
        print(f"    drop from own clean score (positive = got worse): "
              f"camera {drop_c:+.3f}, fk {drop_f:+.3f}, open-loop {drop_o:+.3f}")
        print(f"    PRIMARY  camera degrades less than fk (paired diff-in-diff): {m:+.3f}  "
              f"n={len(did)}  {int((did > 0).sum())}/{len(did)} up  t={t:+.2f}  (crit {crit:.2f})")
        print(f"    secondary  absolute camera - fk: {ma:+.3f}  t={ta:+.2f}  "
              f"(includes the clean gap {mg:+.3f} - not recovery)")
        # CEILING CONTROL. The `true` arm sees the real ink perfectly. If even IT
        # cannot recover better than fk, then no observation of the paper helps
        # here and a camera-vs-fk null says nothing about cameras - there was no
        # signal in the channel for either arm to use. Added 2026-10-19 after the
        # primary endpoint came back null on all three kinds.
        tru = np.array([done[(s, "true", sd)][f"iou_{k}"] for s, sd in common], float)
        tru0 = np.array([done[(s, "true", sd)]["iou_none"] for s, sd in common], float)
        mc, tc = _tstat((tru - tru0) - (fk - fk0))
        print(f"    CONTROL  privileged `true` degrades less than fk: {mc:+.3f}  "
              f"t={tc:+.2f}  (if this is also null, the channel carries no "
              "recoverable signal)")
        if drop_o < 0.03:
            print(f"    !! open-loop loses only {drop_o:+.3f} here: this disturbance barely "
                  "bites, so a null result says little either way")
        if len(did) < 8:
            print("    -> INTERIM: fewer than 8 (shape, seed) cells. No verdict.")
        elif t >= crit:
            print("    -> camera RECOVERS better than fk. This is the evidence "
                  "D01's argument needs answering with.")
        elif t <= -crit:
            print("    -> camera recovers WORSE than fk. A real negative result.")
        else:
            print("    -> no detectable difference in recovery (not 'no difference').")

    _figure(done, common)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs="+", default=[0, 100])
    ap.add_argument("--shapes", nargs="+", choices=SHAPES)
    ap.add_argument("--shard", default="")
    ap.add_argument("--timesteps", type=int, default=200_000)
    ap.add_argument("--n-envs", type=int, default=8)
    ap.add_argument("--max-steps", type=int, default=240)
    ap.add_argument("--step-size", type=float, default=0.014)
    ap.add_argument("--eval-eps", type=int, default=10,
                    help="episodes per disturbance kind; >1 is meaningful because "
                         "the disturbance is resampled each episode")
    ap.add_argument("--aggregate", action="store_true")
    a = ap.parse_args()
    aggregate() if a.aggregate else run(a)
