"""
RoboSketch-RL  |  Stage 5 RQ3: PPO vs SAC (proposal 5.5, fair protocol).
Arm `sac200`: the gen2 `param200` protocol EXACTLY (train size/rotation family, vision reward, privileged global 64-px
observation, max_steps 240, step 0.014, 8 envs, 200k ENV steps, same seeds, same eval sets/targets) - only the algorithm
changes: stable-baselines3 SAC (CnnPolicy), automatic entropy tuning, buffer 40k transitions (memory-optimised),
learning_starts 5k, batch 256, lr 3e-4, gamma 0.99, tau 0.005, train_freq 1 vec-step (= 8 transitions), gradient_steps 2
(update-to-data ratio 0.25: a declared compute choice, NOT tuned - SAC at ratio 1 would cost ~4x the wall clock).
Per proposal 5.5 both an equal-env-steps and a wall-clock view are needed: this file records `train_seconds`; param200
runs did not record wall clock, so only the equal-env-steps comparison is paired here.

Compared with param200 (results/gen2_*.jsonl), paired by (shape, seed): 4 shapes x seeds {0,100} = 8 runs.
Pre-registered in docs/RESEARCH_LOG.md "RQ3 SAC launched".
  $env:OMP_NUM_THREADS=1; $env:MKL_NUM_THREADS=1
  conda run -n robosketch --no-capture-output python rl/sac_experiment.py --seeds 0 100 --shapes line circle --shard a
  conda run -n robosketch --no-capture-output python rl/sac_experiment.py --seeds 0 100 --shapes square triangle --shard b
  conda run -n robosketch --no-capture-output python rl/sac_experiment.py --aggregate
"""
import argparse
import glob
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from experiment import warn_config_drift, _sd
from gen_experiment import _make, _paired
import gen2_experiment as G2

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results", "sac.jsonl")
SHAPES = G2.SHAPES
EVAL_SETS = G2.EVAL_SETS
TIMESTEPS = 200_000
ARM = "sac200"
BUFFER = 40_000
LEARNING_STARTS = 5_000
GRAD_STEPS = 2


def load_done():
    done = {}
    for path in sorted(glob.glob(RESULTS.replace(".jsonl", "*.jsonl"))):
        with open(path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    r = json.loads(line)
                    done[(r["shape"], r["arm"], r["seed"])] = r
    return done


def build_model(shape, seed, n_envs, max_steps, step_size):
    from stable_baselines3 import SAC
    from stable_baselines3.common.vec_env import DummyVecEnv, VecMonitor
    venv = VecMonitor(DummyVecEnv([_make(shape, "train", seed + i, max_steps, step_size) for i in range(n_envs)]))
    model = SAC("CnnPolicy", venv, verbose=0, seed=seed, learning_rate=3e-4, buffer_size=BUFFER,
                learning_starts=LEARNING_STARTS, batch_size=256, tau=0.005, gamma=0.99, train_freq=1,
                gradient_steps=GRAD_STEPS, ent_coef="auto", optimize_memory_usage=True,
                replay_buffer_kwargs={"handle_timeout_termination": False})
    return model, venv


def evaluate(shape, seed, max_steps, step_size, eval_eps, model):
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
    return out


def train_eval(shape, seed, n_envs, max_steps, step_size, eval_eps, timesteps=TIMESTEPS):
    model, venv = build_model(shape, seed, n_envs, max_steps, step_size)
    t0 = time.time()
    model.learn(total_timesteps=timesteps, progress_bar=False)
    sec = time.time() - t0
    out = evaluate(shape, seed, max_steps, step_size, eval_eps, model)
    venv.close()
    return out, sec, int(model.num_timesteps)


def run(args):
    os.makedirs(os.path.dirname(RESULTS), exist_ok=True)
    shard = RESULTS if not args.shard else RESULTS.replace(".jsonl", f"_{args.shard}.jsonl")
    done = load_done()
    warn_config_drift(done, {"max_steps": args.max_steps, "step_size": args.step_size,
                             "eval_eps": args.eval_eps, "timesteps": TIMESTEPS})
    shapes = args.shapes or SHAPES
    todo = [(s, ARM, k) for k in args.seeds for s in shapes if (s, ARM, k) not in done]
    print(f"{len(done)} runs done, {len(todo)} to go (seeds={args.seeds})\n", flush=True)
    for i, (shape, arm, seed) in enumerate(todo, 1):
        print(f"[{i}/{len(todo)}] {shape:8s} {ARM} seed={seed} ...", flush=True)
        m, sec, nts = train_eval(shape, seed, args.n_envs, args.max_steps, args.step_size, args.eval_eps)
        rec = {"shape": shape, "arm": ARM, "seed": seed, "mode": "vision", "timesteps": TIMESTEPS,
               "env_steps_done": nts, "buffer": BUFFER, "learning_starts": LEARNING_STARTS, "grad_steps": GRAD_STEPS,
               "max_steps": args.max_steps, "step_size": args.step_size, "eval_eps": args.eval_eps,
               "torch_threads": __import__("torch").get_num_threads(), "train_seconds": round(sec, 1), "eval": m}
        with open(shard, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")
        print("        -> " + "  ".join(f"{n} {m[n]['iou']:.3f}" for n in EVAL_SETS) + f"  | {sec/60:.1f} min", flush=True)
    if not args.shard:
        aggregate()


def aggregate():
    sac, g2 = load_done(), G2.load_done()
    cells = sorted({(s, k) for (s, a, k) in sac if (s, "param200", k) in g2})
    if not cells:
        print("no complete cells yet.")
        return
    get = lambda src, arm: (lambda ev, key="iou": np.array([src[(s, arm, k)]["eval"][ev][key] for s, k in cells]))
    P, S = get(g2, "param200"), get(sac, ARM)
    print(f"\n=== RQ3 SAC vs PPO (param200), equal ENV steps (200k): TRUE IoU, n={len(cells)} cells, 16 targets/set ===")
    print(f"{'arm':<10}" + "".join(f"{e:>20}" for e in EVAL_SETS))
    for lab, g in (("ppo", P), ("sac200", S)):
        print(f"{lab:<10}" + "".join(f"{g(e).mean():>12.3f} +/-{_sd(g(e)):.3f}" for e in EVAL_SETS))
    print("peak IoU:  " + "   ".join(f"{lab} " + "/".join(f"{g(e, 'peak_iou').mean():.3f}" for e in EVAL_SETS)
                                   for lab, g in (("ppo", P), ("sac200", S))))

    def line(label, x, y):
        d, up, m, t = _paired(x, y)
        print(f"  {label:<46} {d:+.3f}  {up}/{m} up  t={t:+.2f}")

    print("\nPRIMARY    train-family IoU, sac200 - ppo (>0 = SAC better at equal env steps; crit |t|=2.37 at n=8)")
    line("train: sac200 - ppo", S("train"), P("train"))
    print("\nSECONDARY  other sets")
    for e in ("default", "heldout", "heldout_scale", "heldout_rot"):
        line(f"{e}: sac200 - ppo", S(e), P(e))
    print("\nLOSS train->heldout")
    for lab, g in (("ppo", P), ("sac200", S)):
        print(f"  {lab}: {np.mean(g('train') - g('heldout')):+.3f}")
    line("loss: ppo - sac200 (>0 = sac loses LESS)", P("train") - P("heldout"), S("train") - S("heldout"))
    secs = [sac[(s, ARM, k)]["train_seconds"] for s, k in cells]
    print(f"\nDESCRIPTIVE sac200 wall clock per run (OMP=1, 2 workers sharing the CPU): mean {np.mean(secs)/60:.1f} min, "
          f"range {min(secs)/60:.1f}-{max(secs)/60:.1f} min; PPO wall clock was not recorded.")
    print("\nper (shape, seed) train IoU:  cell   ppo   sac200")
    for i, (s, k) in enumerate(cells):
        print(f"  {s:9s} seed={k:<4d} {P('train')[i]:.3f}  {S('train')[i]:.3f}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs="+", default=[0, 100])
    ap.add_argument("--n-envs", type=int, default=8)
    ap.add_argument("--max-steps", type=int, default=240)
    ap.add_argument("--step-size", type=float, default=0.014)
    ap.add_argument("--eval-eps", type=int, default=16)
    ap.add_argument("--shapes", nargs="+", choices=SHAPES)
    ap.add_argument("--shard", default="")
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--aggregate", action="store_true")
    a = ap.parse_args()
    aggregate() if a.aggregate else run(a)
