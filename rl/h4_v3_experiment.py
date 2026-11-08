"""
RoboSketch-RL  |  H4 v3 - does a camera help once it can see the PEN ON THE PAPER?
-------------------------------------------------
Follow-up to H4 and H4-short (proposal 4.3), both null on camera-vs-fk recovery.

WHAT THE ORACLE CHECK FOUND (RESEARCH_LOG 2026-10-29). The paper-shift loss is
recoverable: an arm that KNOWS the shift loses 0.013 IoU at 60 steps, trained arms
lose 0.129-0.147. So the nulls are not "nothing to recover".

THE SUSPECTED CAUSE, an observation we chose. `DrawEnv._obs` drew the pen marker
from the pen's WORLD position, with no sheet offset. After a shift the marker and
the ink disagree by 5-10 px and the policy has to INFER the offset. The `camera`
arm saw only a photograph of the ink and never the pen tip against the paper -
which is the one thing a real camera provides that forward kinematics cannot.

THE TEST. Two new arms, identical to `true` and `camera` except that the observation
marks the pen where it actually LANDS on the sheet (`pen_marker_frame="sheet"`):

  true_sheet     privileged ceiling, with the pen on the sheet
  camera_sheet   ours, with the pen on the sheet

Comparison arms are NOT re-run. `fk`, `camera` (world-frame marker) and `true`
(world-frame marker) come from `results/h4_short_*.jsonl`: same shapes, seeds,
timesteps, max_steps=60, eval episodes and OMP_NUM_THREADS=1, and the default
`pen_marker_frame="world"` was proved bit-identical to the pre-change environment
(observations and rewards, four configurations). `fk` is deliberately unchanged:
kinematics has no way to know the sheet moved, so giving it the sheet-frame pen
would hand it information D01's condition cannot have.

PRE-REGISTERED ANALYSIS (fixed before any v3 run; n = 8 (shape, seed) cells,
two-sided 5%, critical t(7) = 2.365). All are paired within (shape, seed)
difference-in-differences, i.e. how much less an arm LOSES from its own clean score:
  PRIMARY    camera_sheet vs fk, on paper_shift. This is the disturbance the sheet
             marker addresses and the claim D01 has to be answered on.
  SECONDARY  camera_sheet vs camera (world marker): is the marker itself the cause?
  CONTROL    true_sheet vs fk. If even the privileged arm does not recover with the
             pen on the sheet, the marker is not the missing ingredient.
  slip and ink_failure are reported but are not primary: neither moves the sheet,
  and ink_failure does not bite (open-loop loses ~0.013).
  No optional stopping. If the primary |t| lands between 1.5 and 2.365, the only
  permitted follow-up is adding seeds {200, 300} for ALL arms, reporting every seed.

Scoring is always TRUE IoU of the real paper.

  $env:OMP_NUM_THREADS=1; $env:MKL_NUM_THREADS=1; conda run -n robosketch --no-capture-output python rl/h4_v3_experiment.py --seeds 0 100 --shapes line circle     --shard a --timesteps 200000 --max-steps 60
  $env:OMP_NUM_THREADS=1; $env:MKL_NUM_THREADS=1; conda run -n robosketch --no-capture-output python rl/h4_v3_experiment.py --seeds 0 100 --shapes square triangle --shard b --timesteps 200000 --max-steps 60
  conda run -n robosketch --no-capture-output python rl/h4_v3_experiment.py --aggregate
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
RESULTS = os.path.join(ROOT, "results", "h4_v3.jsonl")
SHAPES = ["line", "circle", "square", "triangle"]
NEW_ARMS = ["true_sheet", "camera_sheet"]
BASE_ARMS = ["open_loop", "true", "fk", "camera"]
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
    return _rows("h4_v3_*.jsonl") | _rows("h4_v3.jsonl")


def _env(shape, arm, kind, seed, max_steps, step_size):
    kw = dict(shape=shape, max_steps=max_steps, step_size_m=step_size,
              disturbance=kind, seed=seed, pen_marker_frame="sheet")
    if arm == "camera_sheet":
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
    base = _rows("h4_short_*.jsonl")
    warn_config_drift(base, {"timesteps": args.timesteps, "max_steps": args.max_steps})
    combos = [(s, a, k) for k in args.seeds for s in shapes for a in NEW_ARMS]
    todo = [c for c in combos if c not in done]
    print(f"H4 v3: max_steps={args.max_steps}, timesteps={args.timesteps}")
    print(f"{len(done)} runs done, {len(todo)} to go\n", flush=True)
    omp = os.environ.get("OMP_NUM_THREADS", "unset")
    for i, (shape, arm, seed) in enumerate(todo, 1):
        print(f"[{i}/{len(todo)}] {shape:8s} {arm:12s} seed={seed} (omp={omp}) ...", flush=True)
        res = train_and_eval(shape, arm, seed, args.timesteps, args.n_envs,
                             args.max_steps, args.step_size, args.eval_eps)
        rec = {"shape": shape, "arm": arm, "seed": seed,
               "timesteps": args.timesteps, "max_steps": args.max_steps,
               "step_size": args.step_size, "eval_eps": args.eval_eps,
               "omp_threads": omp, "pen_marker_frame": "sheet"}
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


def _figure(rows, cells):
    F = cv2.FONT_HERSHEY_SIMPLEX
    kinds = EVAL_KINDS[1:]
    arms = ["fk", "camera", "camera_sheet", "true", "true_sheet"]
    color = {"fk": (60, 140, 200), "camera": (120, 120, 230), "camera_sheet": (40, 40, 190),
             "true": (150, 150, 150), "true_sheet": (60, 60, 60)}
    W, H = 1360, 640
    img = np.full((H, W, 3), 255, np.uint8)
    cv2.putText(img, "H4 v3: does putting the pen on the sheet let a camera recover?",
                (46, 40), F, 0.72, (0, 0, 0), 2, cv2.LINE_AA)
    cv2.putText(img, "max_steps=60; scored on TRUE IoU; n=%d (shape, seed) cells; arms ending "
                "in _sheet see the pen where it lands on the paper" % len(cells),
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
    comps = [("camera_sheet", "fk", "PRIMARY: camera_sheet - fk"),
             ("camera_sheet", "camera", "marker effect: camera_sheet - camera"),
             ("true_sheet", "fk", "CONTROL: true_sheet - fk")]
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
    out = os.path.join(ROOT, "output", "h4_v3_disturbance_recovery.png")
    cv2.imwrite(out, img)
    print("\nwrote %s" % out)


def aggregate():
    new = load_done()
    base = _rows("h4_short_*.jsonl")
    rows = {**base, **new}
    cells = sorted({(s, k) for (s, a, k) in rows
                    if all((s, aa, k) in rows for aa in BASE_ARMS + NEW_ARMS)})
    if not cells:
        print("no (shape, seed) cell has every arm yet "
              f"({len(new)}/16 new runs done).")
        return
    print("=== H4 v3 (max_steps=60): true IoU under each disturbance ===")
    print("fk, camera, true, open_loop are the H4-short rows; *_sheet are new\n")
    print("balanced over %d (shape, seed) cells" % len(cells))
    print("%-13s %s" % ("", "".join("%14s" % k for k in EVAL_KINDS)))
    means = {}
    for arm in BASE_ARMS + NEW_ARMS:
        means[arm] = {k: float(np.mean([rows[(s, arm, sd)][f"iou_{k}"] for s, sd in cells]))
                      for k in EVAL_KINDS}
        print("%-13s %s" % (arm, "".join("%14.3f" % means[arm][k] for k in EVAL_KINDS)))
    print("\ndrop from own clean score (positive = got worse):")
    for arm in ("fk", "camera", "camera_sheet", "true", "true_sheet", "open_loop"):
        print("  %-13s %s" % (arm, "  ".join(
            "%s %+.3f" % (k, means[arm]["none"] - means[arm][k]) for k in EVAL_KINDS[1:])))
    crit = _tcrit(len(cells))
    for title, a, b in (("PRIMARY    camera_sheet vs fk", "camera_sheet", "fk"),
                        ("SECONDARY  camera_sheet vs camera (world marker)", "camera_sheet", "camera"),
                        ("CONTROL    true_sheet vs fk", "true_sheet", "fk"),
                        ("          true_sheet vs true (world marker)", "true_sheet", "true")):
        print(f"\n{title}  (diff-in-diff, > 0 = {a} loses LESS; crit t={crit:.2f}, n={len(cells)})")
        for k in EVAL_KINDS[1:]:
            d = _did(rows, cells, a, b, k)
            m, t = _tstat(d)
            flag = ("  <-- clears crit" if (len(d) >= 8 and abs(t) >= crit) else "")
            print(f"  {k:12s} {m:+.3f}  {int((d > 0).sum())}/{len(d)} up  t={t:+.2f}{flag}")
    cg = np.array([rows[(s, "camera_sheet", sd)]["iou_none"] - rows[(s, "fk", sd)]["iou_none"]
                   for s, sd in cells], float)
    m, t = _tstat(cg)
    print(f"\n  clean gap camera_sheet - fk: {m:+.3f}  t={t:+.2f}  (NOT evidence of recovery)")
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
