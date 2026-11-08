"""
RoboSketch-RL  |  Generalisation experiment (proposal 5.4, closes "memorises 4 shapes")
-------------------------------------------------
Question: does the camera-rewarded agent learn to DRAW a shape, or does it memorise the
one fixed picture of it?  Two training regimes, same everything else (reward_mode="vision",
H2 protocol: 240 steps, 0.014 m, 200k PPO steps):

  fixed   trained on the single default target (what every earlier result used)
  param   trained on randomly sized/rotated targets (targets.PARAM_RANGES["train"])

Every trained agent is then scored (TRUE IoU) on three target sets, 16 distinct episodes
each, the SAME 16 targets for every agent (paired):

  default  the one fixed target            (home turf of `fixed`)
  train    new size/rotation, train range   (home turf of `param`)
  heldout  size AND rotation outside the train range - seen by NEITHER arm

Pre-registered readings are in docs/RESEARCH_LOG.md ("Generalisation experiment launched").
Resumable (key = shape, arm, seed); `--aggregate` summarises. Use seeds 0 100.

  $env:OMP_NUM_THREADS=1; $env:MKL_NUM_THREADS=1
  conda run -n robosketch --no-capture-output python rl/gen_experiment.py --seeds 0 100 --shapes line circle --shard a
  conda run -n robosketch --no-capture-output python rl/gen_experiment.py --seeds 0 100 --shapes square triangle --shard b
  conda run -n robosketch --no-capture-output python rl/gen_experiment.py --aggregate
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

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results", "gen.jsonl")
SHAPES = ["line", "circle", "square", "triangle"]
ARMS = {"fixed": None, "param": "train"}          # arm -> target_split used for TRAINING
EVAL_SETS = {"default": None, "train": "train", "heldout": "heldout"}
MODE = "vision"


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
    return lambda: DrawEnv(shape=shape, use_arm=False, max_steps=max_steps,
                           step_size_m=step_size, reward_mode=MODE,
                           target_split=split, seed=seed)


def train_eval(shape, arm, seed, timesteps, n_envs, max_steps, step_size, eval_eps):
    from stable_baselines3 import PPO
    from stable_baselines3.common.vec_env import DummyVecEnv, VecMonitor

    split = ARMS[arm]
    venv = VecMonitor(DummyVecEnv([_make(shape, split, seed + i, max_steps, step_size)
                                   for i in range(n_envs)]))
    model = PPO("CnnPolicy", venv, verbose=0, seed=seed, n_steps=512, batch_size=256,
                n_epochs=6, gamma=0.99, ent_coef=0.02, learning_rate=3e-4)
    model.learn(total_timesteps=timesteps, progress_bar=False)

    out = {}
    for name, es in EVAL_SETS.items():
        env = _make(shape, es, 10_000 + seed, max_steps, step_size)()
        ious, peaks = [], []
        for ep in range(eval_eps):
            # reset seed is shared by every agent, so every agent sees the same targets
            obs, _ = env.reset(seed=20_000 + ep)
            done, info = False, {}
            while not done:
                a, _ = model.predict(obs, deterministic=True)
                obs, r, term, trunc, info = env.step(a)
                done = term or trunc
            ious.append(info["iou"])
            peaks.append(info["peak_iou"])
        env.close()
        out[name] = {"iou": float(np.mean(ious)), "peak_iou": float(np.mean(peaks)),
                     "iou_eps": [round(float(x), 4) for x in ious]}
    venv.close()
    return out


def run(args):
    os.makedirs(os.path.dirname(RESULTS), exist_ok=True)
    shard = RESULTS if not args.shard else RESULTS.replace(".jsonl", f"_{args.shard}.jsonl")
    done = load_done()
    warn_config_drift(done, {"timesteps": args.timesteps, "max_steps": args.max_steps,
                             "step_size": args.step_size, "eval_eps": args.eval_eps})
    shapes = args.shapes or SHAPES
    todo = [(s, a, k) for k in args.seeds for s in shapes for a in ARMS
            if (s, a, k) not in done]
    print(f"{len(done)} runs done, {len(todo)} to go (seeds={args.seeds})\n", flush=True)
    for i, (shape, arm, seed) in enumerate(todo, 1):
        print(f"[{i}/{len(todo)}] {shape:8s} {arm:6s} seed={seed} ...", flush=True)
        m = train_eval(shape, arm, seed, args.timesteps, args.n_envs, args.max_steps,
                       args.step_size, args.eval_eps)
        rec = {"shape": shape, "arm": arm, "seed": seed, "mode": MODE,
               "timesteps": args.timesteps, "max_steps": args.max_steps,
               "step_size": args.step_size, "eval_eps": args.eval_eps,
               "torch_threads": __import__("torch").get_num_threads(), "eval": m}
        with open(shard, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")
        print("        -> " + "  ".join(f"{n} {m[n]['iou']:.3f}" for n in EVAL_SETS), flush=True)
    if not args.shard:
        aggregate()


def _paired(x, y):
    """mean(x-y), pairs with x>y, paired t (n-1 df)."""
    d = np.asarray(x, float) - np.asarray(y, float)
    se = _sd(d) / np.sqrt(len(d)) if len(d) > 1 else float("nan")
    return float(d.mean()), int((d > 0).sum()), len(d), float(d.mean() / se) if se else float("nan")


def aggregate():
    done = load_done()
    cells = sorted({(s, k) for (s, a, k) in done if ("fixed" in ARMS and
                    (s, "fixed", k) in done and (s, "param", k) in done)})
    if not cells:
        print("no complete (shape, seed) cells yet.")
        return
    g = lambda arm, ev, key="iou": np.array([done[(s, arm, k)]["eval"][ev][key] for s, k in cells])
    n = len(cells)
    print(f"\n=== Generalisation: TRUE IoU, vision reward, n={n} (shape, seed) cells, "
          f"{done[(cells[0][0], 'fixed', cells[0][1])]['eval_eps']} distinct targets per set ===")
    print(f"{'arm trained on':<16}" + "".join(f"{e:>20}" for e in EVAL_SETS))
    for arm in ARMS:
        print(f"{arm:<16}" + "".join(f"{g(arm, e).mean():>12.3f} +/-{_sd(g(arm, e)):.3f}" for e in EVAL_SETS))
    print("\npeak IoU (best IoU reached during the episode):")
    for arm in ARMS:
        print(f"  {arm:<10}" + "".join(f"{g(arm, e, 'peak_iou').mean():>10.3f} {e}" for e in EVAL_SETS))

    def line(label, x, y):
        d, up, m, t = _paired(x, y)
        print(f"  {label:<46} {d:+.3f}  {up}/{m} up  t={t:+.2f}")

    print(f"\nPRIMARY    held-out targets, param - fixed (>0 = parameterised training generalises better; crit |t|=2.37 at n=8)")
    line("heldout: param - fixed", g("param", "heldout"), g("fixed", "heldout"))
    print("\nLOSS each arm suffers going from its OWN home set to heldout (own home: fixed=default, param=train)")
    lf = g("fixed", "default") - g("fixed", "heldout")
    lp = g("param", "train") - g("param", "heldout")
    print(f"  fixed loss {lf.mean():+.3f}   param loss {lp.mean():+.3f}")
    line("loss: fixed - param (>0 = param loses LESS)", lf, lp)
    print("\nREFERENCE")
    line("param on train vs fixed on default (home vs home)", g("param", "train"), g("fixed", "default"))
    line("param: default - train (does param still draw the fixed shape?)", g("param", "default"), g("param", "train"))
    line("fixed: default - train", g("fixed", "default"), g("fixed", "train"))
    line("param: train - heldout", g("param", "train"), g("param", "heldout"))
    print("\nper (shape, seed) heldout IoU:  cell   fixed   param")
    for i, (s, k) in enumerate(cells):
        print(f"  {s:9s} seed={k:<4d} {g('fixed','heldout')[i]:.3f}  {g('param','heldout')[i]:.3f}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs="+", default=[0, 100])
    ap.add_argument("--timesteps", type=int, default=200_000)
    ap.add_argument("--n-envs", type=int, default=8)
    ap.add_argument("--max-steps", type=int, default=240)
    ap.add_argument("--step-size", type=float, default=0.014)
    ap.add_argument("--eval-eps", type=int, default=16)
    ap.add_argument("--shapes", nargs="+", choices=SHAPES)
    ap.add_argument("--shard", default="")
    ap.add_argument("--aggregate", action="store_true")
    a = ap.parse_args()
    aggregate() if a.aggregate else run(a)
