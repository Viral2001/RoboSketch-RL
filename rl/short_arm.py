"""
RoboSketch-RL  |  C5 4th arm: is the plateau-stop gain just a SHORTER HORIZON?
-------------------------------------------------
`overshoot_ablation.py` found plateau (episode ends after 20 steps with no improvement) beats baseline (240 steps, no stop):
+0.055 IoU, 7/8 pairs, mean episode 50 steps. But plateau_patience has no grace period, so it also trains on ~5x shorter
episodes from step 1. Arm `short50`: max_steps=50, NO plateau stop, NO stop head - same average horizon, none of the
adaptive stopping. Same truth reward, 200k steps, seeds {0,1} (to pair with the existing baseline/plateau runs; note seeds
0 and 1 share 7 of 8 env streams - F6 - so this repeats the original sweep's design, not the spaced-seed rule).

  $env:OMP_NUM_THREADS=1; $env:MKL_NUM_THREADS=1
  conda run -n robosketch --no-capture-output python rl/short_arm.py --seeds 0 1 --shapes line circle --shard a
  conda run -n robosketch --no-capture-output python rl/short_arm.py --seeds 0 1 --shapes square triangle --shard b
  conda run -n robosketch --no-capture-output python rl/short_arm.py --aggregate
"""
import argparse
import glob
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from experiment import train_eval, warn_config_drift
import overshoot_ablation as OA

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results", "short_arm.jsonl")
SHAPES = OA.SHAPES
MODE = "truth"
ARM = "short50"
HORIZON = 50


def load_done():
    done = {}
    for path in sorted(glob.glob(RESULTS.replace(".jsonl", "*.jsonl"))):
        with open(path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    r = json.loads(line)
                    done[(r["shape"], r["arm"], r["seed"])] = r
    return done


def run(args):
    os.makedirs(os.path.dirname(RESULTS), exist_ok=True)
    shard = RESULTS if not args.shard else RESULTS.replace(".jsonl", f"_{args.shard}.jsonl")
    done = load_done()
    warn_config_drift(done, {"timesteps": args.timesteps, "max_steps": HORIZON})
    shapes = args.shapes or SHAPES
    todo = [(s, ARM, k) for k in args.seeds for s in shapes if (s, ARM, k) not in done]
    print(f"{len(done)} runs done, {len(todo)} to go (seeds={args.seeds})\n", flush=True)
    for i, (shape, arm, seed) in enumerate(todo, 1):
        print(f"[{i}/{len(todo)}] {shape:8s} {arm} seed={seed} ...", flush=True)
        m = train_eval(shape, MODE, seed, args.timesteps, args.n_envs, HORIZON, args.step_size)
        rec = {"shape": shape, "arm": arm, "seed": seed, "mode": MODE,
               "iou": round(m["iou"], 4), "peak_iou": round(m["peak_iou"], 4),
               "overshoot": round(m["overshoot"], 4), "steps_used": round(m["steps_used"], 1),
               "coverage": round(m["coverage"], 4), "path_ratio": round(m["path_ratio"], 3),
               "timesteps": args.timesteps, "max_steps": HORIZON}
        with open(shard, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")
        print(f"        -> IoU {m['iou']:.3f}  peak {m['peak_iou']:.3f}  overshoot {m['overshoot']:.3f}  "
              f"steps {m['steps_used']:.0f}", flush=True)
    if not args.shard:
        aggregate()


def _t(d):
    d = np.asarray(d, float)
    n = len(d)
    se = d.std(ddof=1) / np.sqrt(n) if n > 1 else float("nan")
    return d.mean(), (d > 0).sum(), n, (d.mean() / se if se and se > 0 else float("nan"))


def aggregate():
    old, new = OA.load_done(), load_done()
    cells = sorted({(s, k) for (s, a, k) in new
                    if (s, "baseline", k) in old and (s, "plateau", k) in old})
    if not cells:
        print("no complete cells yet.")
        return
    R = lambda arm, key: np.array([(new if arm == ARM else old)[(s, arm, k)][key] for s, k in cells])
    print(f"\n=== C5 4th arm: baseline vs plateau vs short50 (truth reward), n={len(cells)} (shape, seed) cells ===")
    print(f"{'arm':<10}{'IoU':>16}{'peak':>8}{'overshoot':>11}{'steps':>7}")
    for arm in ("baseline", "plateau", ARM):
        v = R(arm, "iou")
        print(f"{arm:<10}{v.mean():>9.3f} +/-{v.std(ddof=1):.3f}{R(arm, 'peak_iou').mean():>8.3f}"
              f"{R(arm, 'overshoot').mean():>11.3f}{R(arm, 'steps_used').mean():>7.0f}")

    def line(label, a, b, key="iou"):
        d, up, n, t = _t(R(a, key) - R(b, key))
        print(f"  {label:<40} {d:+.3f}  {up}/{n} up  t={t:+.2f}")

    print("\nPRIMARY    plateau - short50 IoU  (>0 = adaptive stopping adds something beyond a short horizon; crit |t|=2.37 at n=8)")
    line("IoU: plateau - short50", "plateau", ARM)
    print("\nSECONDARY")
    line("IoU: short50 - baseline", ARM, "baseline")
    line("IoU: plateau - baseline (reference, as before)", "plateau", "baseline")
    line("peak: plateau - short50", "plateau", ARM, "peak_iou")
    line("overshoot: plateau - short50", "plateau", ARM, "overshoot")
    print("\nper (shape, seed) IoU:  cell   baseline  plateau  short50")
    for i, (s, k) in enumerate(cells):
        print(f"  {s:9s} seed={k:<3d} {R('baseline', 'iou')[i]:.3f}   {R('plateau', 'iou')[i]:.3f}   {R(ARM, 'iou')[i]:.3f}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs="+", default=[0, 1])
    ap.add_argument("--shapes", nargs="+", choices=SHAPES)
    ap.add_argument("--shard", default="")
    ap.add_argument("--timesteps", type=int, default=200_000)
    ap.add_argument("--n-envs", type=int, default=8)
    ap.add_argument("--step-size", type=float, default=0.014)
    ap.add_argument("--aggregate", action="store_true")
    a = ap.parse_args()
    aggregate() if a.aggregate else run(a)
