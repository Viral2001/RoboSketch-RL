"""
RoboSketch-RL  |  Stage 4 ablation O3: does CoordConv (2 extra x/y ramp planes) help the GLOBAL view generalise?
Arm `coord`: gen2 `param200` protocol (train family, 200k, vision reward, privileged observation, global 64-px view) plus
DrawEnv(coord_channels=True). Compared with param200 (global) and ego, paired by (shape, seed): 4 shapes x seeds {0,100} = 8 runs.
Pre-registered in docs/RESEARCH_LOG.md "O3 CoordConv launched".
  $env:OMP_NUM_THREADS=1; $env:MKL_NUM_THREADS=1
  conda run -n robosketch --no-capture-output python rl/coord_experiment.py --seeds 0 100 --shapes line circle --shard a
  conda run -n robosketch --no-capture-output python rl/coord_experiment.py --seeds 0 100 --shapes square triangle --shard b
  conda run -n robosketch --no-capture-output python rl/coord_experiment.py --aggregate
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
RESULTS = os.path.join(ROOT, "results", "coord.jsonl")
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
                           reward_mode="vision", target_split=split, coord_channels=True, seed=seed)


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
    todo = [(s, "coord", k) for k in args.seeds for s in shapes if (s, "coord", k) not in done]
    print(f"{len(done)} runs done, {len(todo)} to go (seeds={args.seeds})\n", flush=True)
    for i, (shape, arm, seed) in enumerate(todo, 1):
        print(f"[{i}/{len(todo)}] {shape:8s} coord seed={seed} ...", flush=True)
        m = train_eval(shape, seed, args.n_envs, args.max_steps, args.step_size, args.eval_eps)
        rec = {"shape": shape, "arm": "coord", "seed": seed, "mode": "vision", "timesteps": TIMESTEPS,
               "max_steps": args.max_steps, "step_size": args.step_size, "eval_eps": args.eval_eps,
               "torch_threads": __import__("torch").get_num_threads(), "eval": m}
        with open(shard, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")
        print("        -> " + "  ".join(f"{n} {m[n]['iou']:.3f}" for n in EVAL_SETS), flush=True)
    if not args.shard:
        aggregate()


def aggregate():
    co, glob_ = load_done(), G2.load_done()
    import ego_experiment as E1
    egod = E1.load_done()
    cells = sorted({(s, k) for (s, a, k) in co if (s, "param200", k) in glob_})
    if not cells:
        print("no complete cells yet.")
        return
    def get(src, arm):
        return lambda ev, key="iou": np.array([src[(s, arm, k)]["eval"][ev][key] for s, k in cells])
    arms = [("global", get(glob_, "param200")), ("coord", get(co, "coord"))]
    if all((s, "ego", k) in egod for s, k in cells):
        arms.append(("ego", get(egod, "ego")))
    G, C = arms[0][1], arms[1][1]
    print(f"\n=== O3 CoordConv vs plain global view: TRUE IoU, n={len(cells)} (shape, seed) cells, 16 targets/set ===")
    print(f"{'arm':<10}" + "".join(f"{e:>20}" for e in EVAL_SETS))
    for lab, g in arms:
        print(f"{lab:<10}" + "".join(f"{g(e).mean():>12.3f} +/-{_sd(g(e)):.3f}" for e in EVAL_SETS))

    def line(label, x, y):
        d, up, m, t = _paired(x, y)
        print(f"  {label:<52} {d:+.3f}  {up}/{m} up  t={t:+.2f}")

    print("\nPRIMARY    heldout IoU, coord - global (>0 = CoordConv helps; crit |t|=2.37 at n=8)")
    line("heldout: coord - global", C("heldout"), G("heldout"))
    print("\nSECONDARY  coord - global on the other sets")
    for e in ("train", "default", "heldout_scale", "heldout_rot"):
        line(f"{e}: coord - global", C(e), G(e))
    print("\nLOSS train->heldout")
    for lab, g in arms:
        print(f"  {lab}: {np.mean(g('train') - g('heldout')):+.3f}")
    line("loss: global - coord (>0 = coord loses LESS)", G("train") - G("heldout"), C("train") - C("heldout"))
    print("\nper (shape, seed) heldout IoU:  cell   global   coord")
    for i, (s, k) in enumerate(cells):
        print(f"  {s:9s} seed={k:<4d} {G('heldout')[i]:.3f}  {C('heldout')[i]:.3f}")


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
