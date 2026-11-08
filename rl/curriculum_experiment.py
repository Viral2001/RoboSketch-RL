"""
RoboSketch-RL  |  Stage 5 RQ4 (proposal 4.6): does a shape curriculum help?  Train a target shape from scratch vs from a
policy pre-trained on `line` (the first rung of the ladder). Standard transfer metrics (R04): jump-start, time-to-threshold,
asymptotic performance.

Both arms use the same protocol as the H2 / generalisation fixed-target runs: default target of the shape, vision reward,
privileged global 64-px observation, max_steps 240, step 0.014, 8 envs, PPO settings of gen2. Each arm gets 200k PPO steps ON
THE TARGET SHAPE, evaluated at 0/50k/100k/150k/200k target steps (the evaluation is one deterministic episode on the default
target: eval_eps > 1 would repeat the same episode, proposal section 5 item 4).
  scratch   : untrained policy -> 200k target steps.
  from_line : 100k steps on `line` first (these EXTRA steps are not counted in the 200k, disclosed), then 200k target steps.
Targets: circle, square, triangle (line is the source). 3 shapes x seeds {0,100} x 2 arms = 12 runs.
Pre-registered in docs/RESEARCH_LOG.md "RQ4 curriculum launched".
  $env:OMP_NUM_THREADS=1; $env:MKL_NUM_THREADS=1
  conda run -n robosketch --no-capture-output python rl/curriculum_experiment.py --seeds 0 100 --shapes circle square --shard a
  conda run -n robosketch --no-capture-output python rl/curriculum_experiment.py --seeds 0 100 --shapes triangle --shard b
  conda run -n robosketch --no-capture-output python rl/curriculum_experiment.py --aggregate
"""
import argparse
import glob
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from experiment import warn_config_drift, _sd
from gen_experiment import _make, _paired

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results", "curriculum.jsonl")
SHAPES = ["circle", "square", "triangle"]
ARMS = ("scratch", "from_line")
CHUNK = 50_000
N_CHUNKS = 4                 # 4 x 50k = 200k target steps
PRETRAIN = 100_000
THRESH = 0.35                # fixed in advance (TRUE IoU), used for time-to-threshold


def load_done():
    done = {}
    for path in sorted(glob.glob(RESULTS.replace(".jsonl", "*.jsonl"))):
        with open(path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    r = json.loads(line)
                    done[(r["shape"], r["arm"], r["seed"])] = r
    return done


def _venv(shape, seed, n_envs, max_steps, step_size):
    from stable_baselines3.common.vec_env import DummyVecEnv, VecMonitor
    return VecMonitor(DummyVecEnv([_make(shape, None, seed + i, max_steps, step_size) for i in range(n_envs)]))


def _eval(model, shape, seed, max_steps, step_size):
    env = _make(shape, None, 10_000 + seed, max_steps, step_size)()
    obs, _ = env.reset(seed=20_000)
    done, info = False, {}
    while not done:
        a, _ = model.predict(obs, deterministic=True)
        obs, r, term, trunc, info = env.step(a)
        done = term or trunc
    env.close()
    return float(info["iou"]), float(info["peak_iou"])


def train_eval(shape, arm, seed, n_envs, max_steps, step_size):
    from stable_baselines3 import PPO
    first = "line" if arm == "from_line" else shape
    venv = _venv(first, seed, n_envs, max_steps, step_size)
    model = PPO("CnnPolicy", venv, verbose=0, seed=seed, n_steps=512, batch_size=256,
                n_epochs=6, gamma=0.99, ent_coef=0.02, learning_rate=3e-4)
    if arm == "from_line":
        model.learn(total_timesteps=PRETRAIN, progress_bar=False)
        venv.close()
        venv = _venv(shape, seed, n_envs, max_steps, step_size)
        model.set_env(venv)
    curve = [_eval(model, shape, seed, max_steps, step_size)]
    for _ in range(N_CHUNKS):
        model.learn(total_timesteps=CHUNK, reset_num_timesteps=False, progress_bar=False)
        curve.append(_eval(model, shape, seed, max_steps, step_size))
    venv.close()
    return curve


def run(args):
    os.makedirs(os.path.dirname(RESULTS), exist_ok=True)
    shard = RESULTS if not args.shard else RESULTS.replace(".jsonl", f"_{args.shard}.jsonl")
    done = load_done()
    warn_config_drift(done, {"max_steps": args.max_steps, "step_size": args.step_size})
    shapes = args.shapes or SHAPES
    todo = [(s, a, k) for k in args.seeds for s in shapes for a in ARMS if (s, a, k) not in done]
    print(f"{len(done)} runs done, {len(todo)} to go (seeds={args.seeds})\n", flush=True)
    for i, (shape, arm, seed) in enumerate(todo, 1):
        print(f"[{i}/{len(todo)}] {shape:8s} {arm} seed={seed} ...", flush=True)
        curve = train_eval(shape, arm, seed, args.n_envs, args.max_steps, args.step_size)
        rec = {"shape": shape, "arm": arm, "seed": seed, "mode": "vision", "chunk": CHUNK, "pretrain": PRETRAIN if arm == "from_line" else 0,
               "max_steps": args.max_steps, "step_size": args.step_size,
               "torch_threads": __import__("torch").get_num_threads(),
               "iou_curve": [round(c[0], 4) for c in curve], "peak_curve": [round(c[1], 4) for c in curve]}
        with open(shard, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")
        print("        -> IoU curve " + " ".join(f"{c[0]:.3f}" for c in curve), flush=True)
    if not args.shard:
        aggregate()


def _ttt(curve):
    """first checkpoint (in target steps) with IoU >= THRESH; 250k (= never within 200k) otherwise."""
    for j, v in enumerate(curve):
        if v >= THRESH:
            return j * CHUNK
    return 5 * CHUNK


def aggregate():
    d = load_done()
    cells = sorted({(s, k) for (s, a, k) in d if a == "scratch" and (s, "from_line", k) in d})
    if not cells:
        print("no complete cells yet.")
        return
    C = lambda arm: np.array([d[(s, arm, k)]["iou_curve"] for s, k in cells])      # (cells, 5)
    S, F = C("scratch"), C("from_line")
    print(f"\n=== RQ4 curriculum: scratch vs from_line, TRUE IoU on the default target, n={len(cells)} (shape, seed) cells ===")
    print(f"{'target steps':<14}" + "".join(f"{j*CHUNK//1000:>10}k" for j in range(5)))
    for lab, M in (("scratch", S), ("from_line", F)):
        print(f"{lab:<14}" + "".join(f"{M[:, j].mean():>11.3f}" for j in range(5)))

    def line(label, x, y):
        dd, up, m, t = _paired(x, y)
        print(f"  {label:<52} {dd:+.3f}  {up}/{m} up  t={t:+.2f}")

    print(f"\n(crit |t| at n={len(cells)} is about {2.57 if len(cells) == 6 else 2.4}; one deterministic episode per run, so per-run IoU is noisy)")
    print("PRIMARY    asymptotic (200k target steps): from_line - scratch")
    line("final IoU", F[:, 4], S[:, 4])
    print("SECONDARY")
    line("jump-start (0 target steps): from_line - scratch", F[:, 0], S[:, 0])
    line("IoU at 50k target steps", F[:, 1], S[:, 1])
    line("IoU at 100k target steps", F[:, 2], S[:, 2])
    ts, tf = np.array([_ttt(c) for c in S]), np.array([_ttt(c) for c in F])
    print(f"  time to IoU>={THRESH} (target steps; 250000 = never): scratch mean {ts.mean():.0f}  from_line mean {tf.mean():.0f}  "
          f"never: scratch {int((ts == 250000).sum())}/{len(ts)}, from_line {int((tf == 250000).sum())}/{len(tf)}")
    print("\nper cell final IoU:  cell   scratch  from_line   | per cell jump-start")
    for i, (s, k) in enumerate(cells):
        print(f"  {s:9s} seed={k:<4d} {S[i, 4]:.3f}  {F[i, 4]:.3f}      | {S[i, 0]:.3f}  {F[i, 0]:.3f}")


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
