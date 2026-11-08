"""
RoboSketch-RL  |  H4 v4 - can a camera ESTIMATE the sheet offset itself?
-------------------------------------------------
H4 v3 (RESEARCH_LOG 2026-10-30) found that drawing the pen marker where the pen lands ON THE
SHEET removes the paper-shift loss (camera_sheet / true_sheet lose ~0.02 vs ~0.14). But that
marker used the simulator's TRUE sheet offset, so it did not test a camera. D01's condition
(kinematics only) cannot know the offset; the question is whether the camera can supply it.

THE TEST. New arm `camera_est`: obs_source="camera", cam_split="fixed", reward_mode="vision",
pen_marker_frame="estimated". The offset is estimated from the photograph by phase correlation
between the arm's kinematic belief canvas and the photo (DrawEnv._estimate_offset). No
privileged offset is read. Measured accuracy with random actions (steps 40-59, 24 episodes):
mean error 0.48 px against a 7.6 px mean shift.

Comparison arms are NOT re-run: fk, camera, true, open_loop from results/h4_short_*.jsonl and
true_sheet, camera_sheet from results/h4_v3_*.jsonl (same shapes, seeds, timesteps, max_steps=60,
eval episodes, OMP_NUM_THREADS=1; defaults proved bit-identical earlier, and this change only adds
a new pen_marker_frame value).

PRE-REGISTERED ANALYSIS (fixed before any v4 run; n = 8 (shape, seed) cells, critical t(7)=2.365,
paired diff-in-diff = how much LESS an arm loses from its own clean score):
  PRIMARY    camera_est vs fk, paper_shift.  (the D01 comparison)
  SECONDARY  camera_est vs camera (world marker), paper_shift.
  REFERENCE  camera_est vs camera_sheet (privileged offset): is the estimate as good as the truth?
  Readings fixed now: primary sig + camera_est ~ camera_sheet -> a camera supplies what kinematics
  cannot (answers D01 in simulation); primary sig but clearly worse than camera_sheet -> partial;
  primary not sig -> the estimate does not get used by PPO within 200k steps. No optional stopping;
  if primary |t| in 1.5-2.365 the only follow-up is seeds {200,300} for ALL arms.
Scoring is always TRUE IoU.

  $env:OMP_NUM_THREADS=1; $env:MKL_NUM_THREADS=1; conda run -n robosketch --no-capture-output python rl/h4_v4_experiment.py --seeds 0 100 --shapes line circle     --shard a --timesteps 200000 --max-steps 60
  $env:OMP_NUM_THREADS=1; $env:MKL_NUM_THREADS=1; conda run -n robosketch --no-capture-output python rl/h4_v4_experiment.py --seeds 0 100 --shapes square triangle --shard b --timesteps 200000 --max-steps 60
  conda run -n robosketch --no-capture-output python rl/h4_v4_experiment.py --aggregate
"""
import argparse
import glob
import json
import os
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from draw_env import DrawEnv
from experiment import warn_config_drift
import h4_short_experiment as S          # reuse its plotting panel and statistics

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results", "h4_v4.jsonl")
SHAPES = ["line", "circle", "square", "triangle"]
NEW_ARMS = ["camera_est"]
BASE_ARMS = ["open_loop", "true", "fk", "camera", "true_sheet", "camera_sheet"]
EVAL_KINDS = ["none", "slip", "paper_shift", "ink_failure"]
_tstat, _tcrit, _sd = S._tstat, S._tcrit, S._sd


def _rows(pattern):
    out = {}
    for path in sorted(glob.glob(os.path.join(ROOT, "results", pattern))):
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    r = json.loads(line)
                    out[(r["shape"], r["arm"], r["seed"])] = r
    return out


def load_done():
    return _rows("h4_v4_*.jsonl") | _rows("h4_v4.jsonl")


def _env(shape, arm, kind, seed, max_steps, step_size):
    kw = dict(shape=shape, max_steps=max_steps, step_size_m=step_size,
              disturbance=kind, seed=seed, pen_marker_frame="estimated")
    if arm == "camera_est":
        kw.update(obs_source="camera", cam_split="fixed", reward_mode="vision")
    else:                                    # true_sheet
        kw.update(obs_source="true")
    return DrawEnv(**kw)


def evaluate(model, shape, arm, seed, max_steps, step_size, eval_eps):
    out = {}
    for kind in EVAL_KINDS:
        ious = []
        for ep in range(eval_eps):
            env = _env(shape, arm, kind, 60_000 + seed * 100 + ep, max_steps, step_size)
            obs, _ = env.reset(seed=60_000 + seed * 100 + ep)
            done, info = False, {}
            while not done:
                a, _ = model.predict(obs, deterministic=True)
                obs, r, term, trunc, info = env.step(a)
                done = term or trunc
            ious.append(info["iou"])
            env.close()
        out[kind] = (float(np.mean(ious)), _sd(ious))
    return out


def train_and_eval(shape, arm, seed, timesteps, n_envs, max_steps, step_size, eval_eps):
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
    # compare against the baseline rows the comparison arms will come from
    base = _rows("h4_short_*.jsonl") | _rows("h4_v3_*.jsonl")
    warn_config_drift(base, {"timesteps": args.timesteps, "max_steps": args.max_steps})
    combos = [(s, a, k) for k in args.seeds for s in shapes for a in NEW_ARMS]
    todo = [c for c in combos if c not in done]
    print(f"H4 v4: max_steps={args.max_steps}, timesteps={args.timesteps}")
    print(f"{len(done)} runs done, {len(todo)} to go\n", flush=True)
    omp = os.environ.get("OMP_NUM_THREADS", "unset")
    for i, (shape, arm, seed) in enumerate(todo, 1):
        print(f"[{i}/{len(todo)}] {shape:8s} {arm:12s} seed={seed} (omp={omp}) ...", flush=True)
        res = train_and_eval(shape, arm, seed, args.timesteps, args.n_envs,
                             args.max_steps, args.step_size, args.eval_eps)
        rec = {"shape": shape, "arm": arm, "seed": seed,
               "timesteps": args.timesteps, "max_steps": args.max_steps,
               "step_size": args.step_size, "eval_eps": args.eval_eps,
               "omp_threads": omp, "pen_marker_frame": "estimated"}
        for k, (m, sd) in res.items():
            rec[f"iou_{k}"] = round(m, 4)
            rec[f"sd_{k}"] = round(sd, 4)
        with open(shard, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")
        print("        -> " + "  ".join(f"{k}:{res[k][0]:.3f}" for k in EVAL_KINDS),
              flush=True)
    print("\ndone.", flush=True)


def _did(rows, cells, a, b, k):
    """Paired diff-in-diff (a - b): how much LESS arm a loses to disturbance k."""
    return np.array([(rows[(s, a, sd)][f"iou_{k}"] - rows[(s, a, sd)]["iou_none"])
                     - (rows[(s, b, sd)][f"iou_{k}"] - rows[(s, b, sd)]["iou_none"])
                     for s, sd in cells], float)


def _figure(rows, cells, out=None, title=None):
    """out/title optional (added 2026-11-08 for the seeds-200/300 confirmation figure); defaults = original v4 figure."""
    F = cv2.FONT_HERSHEY_SIMPLEX
    kinds = EVAL_KINDS[1:]
    arms = ["fk", "camera", "camera_est", "camera_sheet", "true_sheet"]
    color = {"fk": (60, 140, 200), "camera": (120, 120, 230), "camera_est": (40, 160, 40), "camera_sheet": (40, 40, 190),
             "true": (150, 150, 150), "true_sheet": (60, 60, 60)}
    W, H = 1360, 640
    img = np.full((H, W, 3), 255, np.uint8)
    cv2.putText(img, title or "H4 v4: can the camera estimate the sheet offset itself?",
                (46, 40), F, 0.72, (0, 0, 0), 2, cv2.LINE_AA)
    cv2.putText(img, "max_steps=60; scored on TRUE IoU; n=%d (shape, seed) cells; camera_est estimates "
                "the offset from the photo" % len(cells),
                (46, 64), F, 0.44, (110, 110, 110), 1, cv2.LINE_AA)
    drops = {a: [float(np.mean([rows[(s, a, sd)]["iou_none"] - rows[(s, a, sd)][f"iou_{k}"]
                                for s, sd in cells])) for k in kinds] for a in arms}
    hi = max(max(v) for v in drops.values()) + 0.03
    lo = min(0.0, min(min(v) for v in drops.values())) - 0.02
    p1 = S._Panel(img, 110, 520, 600, 380, (lo, hi),
                  "IoU lost to the disturbance, vs that arm's own clean score",
                  "lost IoU (higher = hurt more)")
    gw = 600 // len(kinds)
    for ki, k in enumerate(kinds):
        base = 110 + ki * gw + gw // 2
        for ai, a in enumerate(arms):
            p1.bar(base + int((ai - 2) * gw / 6.3), int(gw / 14), drops[a][ki], color[a])
        p1.xlabel(base, k)
    for ai, a in enumerate(arms):
        y = 142 + ai * 18
        cv2.rectangle(img, (124, y - 8), (140, y + 2), color[a], -1)
        cv2.putText(img, a, (146, y), F, 0.42, color[a], 1, cv2.LINE_AA)
    comps = [("camera_est", "fk", "PRIMARY: camera_est - fk"),
             ("camera_est", "camera", "SECONDARY: camera_est - camera"),
             ("camera_est", "camera_sheet", "REFERENCE: camera_est - camera_sheet")]
    vals = []
    for a, b, _ in comps:
        d = _did(rows, cells, a, b, "paper_shift")
        vals.append((float(d.mean()), float(d.std(ddof=1) / np.sqrt(d.size))))
    crit = _tcrit(len(cells))
    span = max([abs(m) + s for m, s in vals] + [crit * max(s for _, s in vals)]) * 1.3
    p2 = S._Panel(img, 830, 520, 460, 380, (-span, span),
                  "paper_shift: diff-in-diff (loses LESS > 0)", "paired, within (shape, seed)")
    gw2 = 460 // len(comps)
    for ci, ((m, se), (_, _, lab)) in enumerate(zip(vals, comps)):
        cx = 830 + ci * gw2 + gw2 // 2
        p2.bar(cx, int(gw2 / 5), m, (60, 70, 200) if m > 0 else (200, 70, 60))
        p2.whisker(cx, m - se, m + se)
        p2.xlabel(cx, lab.split(":")[0], scale=0.4)
        p2.xlabel(cx, "%+.3f" % m, dy=34, color=(40, 40, 40), scale=0.40)
    for sign in (+1, -1):
        p2.hline(sign * crit * float(np.mean([s for _, s in vals])), (190, 120, 60))
    cv2.putText(img, "dashed: +/- t(%d)=%.2f x mean SE; a bar must clear it. whiskers = +/-1 SE"
                % (len(cells) - 1, crit), (830, 586), F, 0.40, (190, 120, 60), 1, cv2.LINE_AA)
    out = out or os.path.join(ROOT, "output", "h4_v4_disturbance_recovery.png")
    cv2.imwrite(out, img)
    print("\nwrote %s" % out)


def aggregate():
    new = load_done()
    base = _rows("h4_short_*.jsonl") | _rows("h4_v3_*.jsonl")
    rows = {**base, **new}
    cells = sorted({(s, k) for (s, a, k) in rows
                    if all((s, aa, k) in rows for aa in BASE_ARMS + NEW_ARMS)})
    if not cells:
        print("no (shape, seed) cell has every arm yet "
              f"({len(new)}/8 new runs done).")
        return
    print("=== H4 v4 (max_steps=60): true IoU under each disturbance ===")
    print("fk, camera, true, open_loop: H4-short rows; true_sheet, camera_sheet: v3 rows; camera_est is new\n")
    print("balanced over %d (shape, seed) cells" % len(cells))
    print("%-13s %s" % ("", "".join("%14s" % k for k in EVAL_KINDS)))
    means = {}
    for arm in BASE_ARMS + NEW_ARMS:
        means[arm] = {k: float(np.mean([rows[(s, arm, sd)][f"iou_{k}"] for s, sd in cells]))
                      for k in EVAL_KINDS}
        print("%-13s %s" % (arm, "".join("%14.3f" % means[arm][k] for k in EVAL_KINDS)))
    print("\ndrop from own clean score (positive = got worse):")
    for arm in ("fk", "camera", "camera_est", "camera_sheet", "true", "true_sheet", "open_loop"):
        print("  %-13s %s" % (arm, "  ".join(
            "%s %+.3f" % (k, means[arm]["none"] - means[arm][k]) for k in EVAL_KINDS[1:])))
    crit = _tcrit(len(cells))
    for title, a, b in (("PRIMARY    camera_est vs fk", "camera_est", "fk"),
                        ("SECONDARY  camera_est vs camera (world marker)", "camera_est", "camera"),
                        ("REFERENCE  camera_est vs camera_sheet (true offset)", "camera_est", "camera_sheet"),
                        ("          camera_est vs true_sheet", "camera_est", "true_sheet")):
        print(f"\n{title}  (diff-in-diff, > 0 = {a} loses LESS; crit t={crit:.2f}, n={len(cells)})")
        for k in EVAL_KINDS[1:]:
            d = _did(rows, cells, a, b, k)
            m, t = _tstat(d)
            flag = ("  <-- clears crit" if (len(d) >= 8 and abs(t) >= crit) else "")
            print(f"  {k:12s} {m:+.3f}  {int((d > 0).sum())}/{len(d)} up  t={t:+.2f}{flag}")
    cg = np.array([rows[(s, "camera_est", sd)]["iou_none"] - rows[(s, "fk", sd)]["iou_none"]
                   for s, sd in cells], float)
    m, t = _tstat(cg)
    print(f"\n  clean gap camera_est - fk: {m:+.3f}  t={t:+.2f}  (NOT evidence of recovery)")
    if len(cells) < 8:
        print("\n  INTERIM: fewer than 8 cells. No verdict.")
    _figure(rows, cells)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs="+", default=[0, 100])
    ap.add_argument("--shapes", nargs="+", choices=SHAPES)
    ap.add_argument("--shard", default="")
    ap.add_argument("--timesteps", type=int, default=200_000)
    ap.add_argument("--n-envs", type=int, default=8)
    ap.add_argument("--max-steps", type=int, default=60)
    ap.add_argument("--step-size", type=float, default=0.014)
    ap.add_argument("--eval-eps", type=int, default=10)
    ap.add_argument("--aggregate", action="store_true")
    a = ap.parse_args()
    aggregate() if a.aggregate else run(a)
