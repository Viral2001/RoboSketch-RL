"""
RoboSketch-RL  |  Stage 4 ablation O2: does an EGOCENTRIC observation improve generalisation?
-------------------------------------------------
Arm `ego`: trained on the "train" size/rotation family, 200k steps, observation = a 64-px window of the canvas centred
on the pen (DrawEnv(obs_view="ego"); channels target, drawn, sheet-mask). Everything else is the gen2 `param200` protocol
(vision reward, privileged observation, 240 steps, step 0.014, PPO settings, 16 targets per set, reset seeds 20000+ep).
The comparison arm is `param200` from results/gen2*.jsonl (global observation, same seeds/shapes/settings; it reproduced the
earlier sweep bit-for-bit), so only the ego runs are new: 4 shapes x seeds {0,100} = 8 runs, ~17 min each.

Pre-registered in docs/RESEARCH_LOG.md "O2 egocentric ablation launched".

  $env:OMP_NUM_THREADS=1; $env:MKL_NUM_THREADS=1
  conda run -n robosketch --no-capture-output python rl/ego_experiment.py --seeds 0 100 --shapes line circle --shard a
  conda run -n robosketch --no-capture-output python rl/ego_experiment.py --seeds 0 100 --shapes square triangle --shard b
  conda run -n robosketch --no-capture-output python rl/ego_experiment.py --aggregate
"""
import argparse
import glob
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from draw_env import DrawEnv
from experiment import warn_config_drift, _sd
from gen_experiment import _paired
import gen2_experiment as G2

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results", "ego.jsonl")
SHAPES = G2.SHAPES
EVAL_SETS = G2.EVAL_SETS
TIMESTEPS = 200_000


def load_done():
    done = {}
    for path in sorted(glob.glob(RESULTS.replace(".jsonl", "*.jsonl"))):
        with open(path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    r = json.loads(line)
                    done[(r["shape"], r["arm"], r["seed"])] = r
    return done


def _make(shape, split, seed, max_steps, step_size):
    return lambda: DrawEnv(shape=shape, use_arm=False, max_steps=max_steps, step_size_m=step_size,
                           reward_mode="vision", target_split=split, obs_view="ego", seed=seed)


def train_eval(shape, seed, n_envs, max_steps, step_size, eval_eps):
    from stable_baselines3 import PPO
    from stable_baselines3.common.vec_env import DummyVecEnv, VecMonitor

    venv = VecMonitor(DummyVecEnv([_make(shape, "train", seed + i, max_steps, step_size)
                                   for i in range(n_envs)]))
    model = PPO("CnnPolicy", venv, verbose=0, seed=seed, n_steps=512, batch_size=256,
                n_epochs=6, gamma=0.99, ent_coef=0.02, learning_rate=3e-4)
    model.learn(total_timesteps=TIMESTEPS, progress_bar=False)
    out = {}
    for name, es in EVAL_SETS.items():
        env = _make(shape, es, 10_000 + seed, max_steps, step_size)()
        ious, peaks = [], []
        for ep in range(eval_eps):
            obs, _ = env.reset(seed=20_000 + ep)
            done, info = False, {}
            while not done:
                a, _ = model.predict(obs, deterministic=True)
                obs, r, term, trunc, info = env.step(a)
                done = term or trunc
            ious.append(info["iou"]); peaks.append(info["peak_iou"])
        env.close()
        out[name] = {"iou": float(np.mean(ious)), "peak_iou": float(np.mean(peaks)),
                     "iou_eps": [round(float(x), 4) for x in ious]}
    venv.close()
    return out


def run(args):
    os.makedirs(os.path.dirname(RESULTS), exist_ok=True)
    shard = RESULTS if not args.shard else RESULTS.replace(".jsonl", f"_{args.shard}.jsonl")
    done = load_done()
    warn_config_drift(done, {"max_steps": args.max_steps, "step_size": args.step_size,
                             "eval_eps": args.eval_eps, "timesteps": TIMESTEPS})
    shapes = args.shapes or SHAPES
    todo = [(s, "ego", k) for k in args.seeds for s in shapes if (s, "ego", k) not in done]
    print(f"{len(done)} runs done, {len(todo)} to go (seeds={args.seeds})\n", flush=True)
    for i, (shape, arm, seed) in enumerate(todo, 1):
        print(f"[{i}/{len(todo)}] {shape:8s} ego seed={seed} ...", flush=True)
        m = train_eval(shape, seed, args.n_envs, args.max_steps, args.step_size, args.eval_eps)
        rec = {"shape": shape, "arm": "ego", "seed": seed, "mode": "vision", "timesteps": TIMESTEPS,
               "max_steps": args.max_steps, "step_size": args.step_size, "eval_eps": args.eval_eps,
               "torch_threads": __import__("torch").get_num_threads(), "eval": m}
        with open(shard, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")
        print("        -> " + "  ".join(f"{n} {m[n]['iou']:.3f}" for n in EVAL_SETS), flush=True)
    if not args.shard:
        aggregate()


def aggregate():
    ego, glob_ = load_done(), G2.load_done()
    cells = sorted({(s, k) for (s, a, k) in ego if (s, "param200", k) in glob_})
    if not cells:
        print("no complete cells yet.")
        return
    ge = lambda ev, key="iou": np.array([ego[(s, "ego", k)]["eval"][ev][key] for s, k in cells])
    gg = lambda ev, key="iou": np.array([glob_[(s, "param200", k)]["eval"][ev][key] for s, k in cells])
    print(f"\n=== O2 egocentric vs global observation: TRUE IoU, n={len(cells)} (shape, seed) cells, 16 targets/set ===")
    print(f"{'arm':<10}" + "".join(f"{e:>20}" for e in EVAL_SETS))
    for lab, g in (("global", gg), ("ego", ge)):
        print(f"{lab:<10}" + "".join(f"{g(e).mean():>12.3f} +/-{_sd(g(e)):.3f}" for e in EVAL_SETS))
    print("peak IoU:  " + "   ".join(f"{lab} " + "/".join(f"{g(e, 'peak_iou').mean():.3f}" for e in EVAL_SETS)
                                   for lab, g in (("global", gg), ("ego", ge))))

    def line(label, x, y):
        d, up, m, t = _paired(x, y)
        print(f"  {label:<52} {d:+.3f}  {up}/{m} up  t={t:+.2f}")

    print("\nPRIMARY    held-out (size+rotation), ego - global  (>0 = egocentric view generalises better; crit |t|=2.37 at n=8)")
    line("heldout: ego - global", ge("heldout"), gg("heldout"))
    print("\nSECONDARY  ego - global on the other sets")
    for e in ("train", "default", "heldout_scale", "heldout_rot"):
        line(f"{e}: ego - global", ge(e), gg(e))
    print("\nLOSS from own home set (train -> held-out)")
    for lab, g in (("global", gg), ("ego", ge)):
        print(f"  {lab}: size+rot {np.mean(g('train') - g('heldout')):+.3f}   size-only {np.mean(g('train') - g('heldout_scale')):+.3f}"
              f"   rotation-only {np.mean(g('train') - g('heldout_rot')):+.3f}")
    line("loss (train->heldout): global - ego (>0 = ego loses LESS)", gg("train") - gg("heldout"), ge("train") - ge("heldout"))
    print("\nper (shape, seed) heldout IoU:  cell   global   ego")
    for i, (s, k) in enumerate(cells):
        print(f"  {s:9s} seed={k:<4d} {gg('heldout')[i]:.3f}  {ge('heldout')[i]:.3f}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs="+", default=[0, 100])
    ap.add_argument("--n-envs", type=int, default=8)
    ap.add_argument("--max-steps", type=int, default=240)
    ap.add_argument("--step-size", type=float, default=0.014)
    ap.add_argument("--eval-eps", type=int, default=16)
    ap.add_argument("--shapes", nargs="+", choices=SHAPES)
    ap.add_argument("--shard", default="")
    ap.add_argument("--aggregate", action="store_true")
    a = ap.parse_args()
    aggregate() if a.aggregate else run(a)
