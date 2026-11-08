"""
RoboSketch-RL  |  Stage 6 / A2 (first step): what happens when the agent controls the pen (up/down) itself?
Single-stroke shapes only (circle, square, triangle): the pen-up bit cannot be NEEDED here, so this measures the COST of the extra
decision and whether the agent learns to use it, before any multi-stroke glyph (digits) is attempted.

Arm `penfree`: DrawEnv(pen_always_down=False) - action[2] > 0.5 means the pen is down (ink only if it was also down on the previous
step, draw_env.step). Everything else = the `scratch` arm of curriculum_experiment.py (default target, vision reward, privileged global
64-px obs [pen marker 255 when down, 128 when up], 240 steps, step 0.014, 8 envs, gen2 PPO settings, 200k steps, evaluated at
0/50k/100k/150k/200k with ONE deterministic episode). The paired baseline is therefore the EXISTING curriculum `scratch` rows
(same shapes, same seeds {0,100}, same code path): no new baseline runs.
Pre-registered in docs/RESEARCH_LOG.md "A2 pen-free launched".
  $env:OMP_NUM_THREADS=1; $env:MKL_NUM_THREADS=1
  conda run -n robosketch --no-capture-output python rl/penfree_experiment.py --seeds 0 100 --shapes circle square --shard a
  conda run -n robosketch --no-capture-output python rl/penfree_experiment.py --seeds 0 100 --shapes triangle --shard b
  conda run -n robosketch --no-capture-output python rl/penfree_experiment.py --aggregate
"""
import argparse
import glob
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from experiment import warn_config_drift
from gen_experiment import _paired
from draw_env import DrawEnv
import curriculum_experiment as C

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results", "penfree.jsonl")
SHAPES = C.SHAPES
ARM = "penfree"


def _make(shape, seed, max_steps, step_size):
    return lambda: DrawEnv(shape=shape, use_arm=False, max_steps=max_steps, step_size_m=step_size,
                           reward_mode="vision", pen_always_down=False, seed=seed)


def load_done():
    done = {}
    for path in sorted(glob.glob(RESULTS.replace(".jsonl", "*.jsonl"))):
        with open(path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    r = json.loads(line)
                    done[(r["shape"], r["seed"])] = r
    return done


def _eval(model, shape, seed, max_steps, step_size):
    env = _make(shape, 10_000 + seed, max_steps, step_size)()
    obs, _ = env.reset(seed=20_000)
    done, info, down, n = False, {}, 0, 0
    while not done:
        a, _ = model.predict(obs, deterministic=True)
        obs, r, term, trunc, info = env.step(a)
        done = term or trunc
        down += int(env.pen_down)
        n += 1
    env.close()
    return float(info["iou"]), float(info["peak_iou"]), down / max(n, 1), float(info["snr"])


def train_eval(shape, seed, n_envs, max_steps, step_size):
    from stable_baselines3 import PPO
    from stable_baselines3.common.vec_env import DummyVecEnv, VecMonitor
    venv = VecMonitor(DummyVecEnv([_make(shape, seed + i, max_steps, step_size) for i in range(n_envs)]))
    model = PPO("CnnPolicy", venv, verbose=0, seed=seed, n_steps=512, batch_size=256,
                n_epochs=6, gamma=0.99, ent_coef=0.02, learning_rate=3e-4)
    curve = [_eval(model, shape, seed, max_steps, step_size)]
    for _ in range(C.N_CHUNKS):
        model.learn(total_timesteps=C.CHUNK, reset_num_timesteps=False, progress_bar=False)
        curve.append(_eval(model, shape, seed, max_steps, step_size))
    venv.close()
    return curve


def run(args):
    os.makedirs(os.path.dirname(RESULTS), exist_ok=True)
    shard = RESULTS if not args.shard else RESULTS.replace(".jsonl", f"_{args.shard}.jsonl")
    done = load_done()
    warn_config_drift(done, {"max_steps": args.max_steps, "step_size": args.step_size})
    shapes = args.shapes or SHAPES
    todo = [(s, k) for k in args.seeds for s in shapes if (s, k) not in done]
    print(f"{len(done)} runs done, {len(todo)} to go (seeds={args.seeds})\n", flush=True)
    for i, (shape, seed) in enumerate(todo, 1):
        print(f"[{i}/{len(todo)}] {shape:8s} {ARM} seed={seed} ...", flush=True)
        curve = train_eval(shape, seed, args.n_envs, args.max_steps, args.step_size)
        rec = {"shape": shape, "arm": ARM, "seed": seed, "mode": "vision", "chunk": C.CHUNK,
               "max_steps": args.max_steps, "step_size": args.step_size,
               "torch_threads": __import__("torch").get_num_threads(),
               "iou_curve": [round(c[0], 4) for c in curve], "peak_curve": [round(c[1], 4) for c in curve],
               "pen_down_frac_curve": [round(c[2], 3) for c in curve], "snr_curve": [round(c[3], 3) for c in curve]}
        with open(shard, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")
        print("        -> IoU curve " + " ".join(f"{c[0]:.3f}" for c in curve)
              + " | pen-down frac " + " ".join(f"{c[2]:.2f}" for c in curve), flush=True)
    if not args.shard:
        aggregate()


def aggregate():
    d, base = load_done(), C.load_done()
    cells = sorted(c for c in d if (c[0], "scratch", c[1]) in base)
    if not cells:
        print("no complete cells yet.")
        return
    P = np.array([d[c]["iou_curve"] for c in cells])
    S = np.array([base[(s, "scratch", k)]["iou_curve"] for s, k in cells])
    print(f"\n=== A2 pen-free vs pen-always-down (curriculum `scratch` rows), TRUE IoU, default target, n={len(cells)} cells ===")
    print(f"{'target steps':<14}" + "".join(f"{j*C.CHUNK//1000:>10}k" for j in range(5)))
    for lab, M in (("always_down", S), ("penfree", P)):
        print(f"{lab:<14}" + "".join(f"{M[:, j].mean():>11.3f}" for j in range(5)))
    print(f"\n(crit |t| at n={len(cells)} is about {2.57 if len(cells) == 6 else 2.4})")
    print("PRIMARY    final IoU (200k): penfree - always_down")
    dd, up, m, t = _paired(P[:, 4], S[:, 4])
    print(f"  final IoU {dd:+.3f}  {up}/{m} up  t={t:+.2f}")
    print("SECONDARY (penfree only, final checkpoint)")
    pdf = np.array([d[c]["pen_down_frac_curve"][-1] for c in cells])
    snr = np.array([d[c]["snr_curve"][-1] for c in cells])
    pk = np.array([d[c]["peak_curve"][-1] for c in cells])
    pks = np.array([base[(s, "scratch", k)]["peak_curve"][-1] for s, k in cells])
    print(f"  pen-down fraction of the eval episode: mean {pdf.mean():.2f} (min {pdf.min():.2f}, max {pdf.max():.2f}); SNR (strokes drawn / target) mean {snr.mean():.2f}")
    print(f"  peak IoU: penfree {pk.mean():.3f} vs always_down {pks.mean():.3f}")
    print("\nper cell final IoU:  cell   always_down  penfree | pen-down frac | snr")
    for i, (s, k) in enumerate(cells):
        print(f"  {s:9s} seed={k:<4d} {S[i, 4]:.3f}  {P[i, 4]:.3f}  | {pdf[i]:.2f} | {snr[i]:.2f}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs="+", default=[0, 100])
    ap.add_argument("--n-envs", type=int, default=8)
    ap.add_argument("--max-steps", type=int, default=240)
    ap.add_argument("--step-size", type=float, default=0.014)
    ap.add_argument("--shapes", nargs="+", choices=SHAPES)
    ap.add_argument("--shard", default="")
    ap.add_argument("--aggregate", action="store_true")
    a = ap.parse_args()
    aggregate() if a.aggregate else run(a)
