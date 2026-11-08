"""
RoboSketch-RL  |  Generalisation, part 2: is the limit a TRAINING BUDGET problem, and which factor breaks it?
-------------------------------------------------
Follow-up to rl/gen_experiment.py (log "### Generalisation RESULT": both arms lose most of their home score on held-out
size+rotation). Same protocol (vision reward, 240 steps, step 0.014, PPO settings, 16 targets per set, same reset seeds).

  param200  trained on the "train" family, 200k steps  (= the earlier `param` arm, re-run so it is scored on the new sets)
  param600  same, 600k steps (3x the budget)

Scored on: default, train, heldout (size AND rotation new), heldout_scale (only size new), heldout_rot (only rotation new).
Pre-registered in docs/RESEARCH_LOG.md "Generalisation part 2 launched". Resumable, key = (shape, arm, seed).

  $env:OMP_NUM_THREADS=1; $env:MKL_NUM_THREADS=1
  conda run -n robosketch --no-capture-output python rl/gen2_experiment.py --seeds 0 100 --shapes line circle --shard a
  conda run -n robosketch --no-capture-output python rl/gen2_experiment.py --seeds 0 100 --shapes square triangle --shard b
  conda run -n robosketch --no-capture-output python rl/gen2_experiment.py --aggregate
"""
import argparse
import glob
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from experiment import warn_config_drift, _sd
from gen_experiment import _make, _paired, load_done as load_gen1

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results", "gen2.jsonl")
SHAPES = ["line", "circle", "square", "triangle"]
ARMS = {"param200": 200_000, "param600": 600_000}          # arm -> training timesteps
EVAL_SETS = {"default": None, "train": "train", "heldout": "heldout",
             "heldout_scale": "heldout_scale", "heldout_rot": "heldout_rot"}


def load_done():
    done = {}
    for path in sorted(glob.glob(RESULTS.replace(".jsonl", "*.jsonl"))):
        with open(path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    r = json.loads(line)
                    done[(r["shape"], r["arm"], r["seed"])] = r
    return done


def train_eval(shape, arm, seed, n_envs, max_steps, step_size, eval_eps):
    from stable_baselines3 import PPO
    from stable_baselines3.common.vec_env import DummyVecEnv, VecMonitor

    venv = VecMonitor(DummyVecEnv([_make(shape, "train", seed + i, max_steps, step_size)
                                   for i in range(n_envs)]))
    model = PPO("CnnPolicy", venv, verbose=0, seed=seed, n_steps=512, batch_size=256,
                n_epochs=6, gamma=0.99, ent_coef=0.02, learning_rate=3e-4)
    model.learn(total_timesteps=ARMS[arm], progress_bar=False)
    out = {}
    for name, es in EVAL_SETS.items():
        env = _make(shape, es, 10_000 + seed, max_steps, step_size)()
        ious, peaks = [], []
        for ep in range(eval_eps):
            obs, _ = env.reset(seed=20_000 + ep)         # same targets for every agent
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
                             "eval_eps": args.eval_eps})
    shapes = args.shapes or SHAPES
    # long runs last within a seed so a partial sweep still yields complete param200 cells first
    todo = [(s, a, k) for k in args.seeds for a in ARMS for s in shapes if (s, a, k) not in done]
    print(f"{len(done)} runs done, {len(todo)} to go (seeds={args.seeds})\n", flush=True)
    for i, (shape, arm, seed) in enumerate(todo, 1):
        print(f"[{i}/{len(todo)}] {shape:8s} {arm:9s} seed={seed} ...", flush=True)
        m = train_eval(shape, arm, seed, args.n_envs, args.max_steps, args.step_size, args.eval_eps)
        rec = {"shape": shape, "arm": arm, "seed": seed, "mode": "vision", "timesteps": ARMS[arm],
               "max_steps": args.max_steps, "step_size": args.step_size, "eval_eps": args.eval_eps,
               "torch_threads": __import__("torch").get_num_threads(), "eval": m}
        with open(shard, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")
        print("        -> " + "  ".join(f"{n} {m[n]['iou']:.3f}" for n in EVAL_SETS), flush=True)
    if not args.shard:
        aggregate()


def aggregate():
    done = load_done()
    cells = sorted({(s, k) for (s, a, k) in done
                    if all((s, x, k) in done for x in ARMS)})
    if not cells:
        print("no complete (shape, seed) cells yet.")
        return
    g = lambda arm, ev, key="iou": np.array([done[(s, arm, k)]["eval"][ev][key] for s, k in cells])
    n = len(cells)
    print(f"\n=== Generalisation part 2: TRUE IoU, vision reward, n={n} (shape, seed) cells, 16 targets per set ===")
    print(f"{'arm':<10}" + "".join(f"{e:>20}" for e in EVAL_SETS))
    for arm in ARMS:
        print(f"{arm:<10}" + "".join(f"{g(arm, e).mean():>12.3f} +/-{_sd(g(arm, e)):.3f}" for e in EVAL_SETS))
    print("peak IoU:")
    for arm in ARMS:
        print(f"  {arm:<9}" + "".join(f"{g(arm, e, 'peak_iou').mean():>8.3f} {e[:6]}" for e in EVAL_SETS))

    def line(label, x, y):
        d, up, m, t = _paired(x, y)
        print(f"  {label:<58} {d:+.3f}  {up}/{m} up  t={t:+.2f}")

    print(f"\nPRIMARY    heldout (size+rotation), param600 - param200  (>0 = more training helps; crit |t|=2.37 at n=8)")
    line("heldout: param600 - param200", g("param600", "heldout"), g("param200", "heldout"))
    print("\nSECONDARY  more training on each held-out set (param600 - param200)")
    for e in ("train", "heldout_scale", "heldout_rot"):
        line(f"{e}: param600 - param200", g("param600", e), g("param200", e))
    print("\nWHICH FACTOR BREAKS IT  (loss = IoU on train set - IoU on that held-out set; >0 = got worse)")
    for arm in ARMS:
        ls = g(arm, "train") - g(arm, "heldout_scale")
        lr = g(arm, "train") - g(arm, "heldout_rot")
        lb = g(arm, "train") - g(arm, "heldout")
        print(f"  {arm}: size-only loss {ls.mean():+.3f}   rotation-only loss {lr.mean():+.3f}   both {lb.mean():+.3f}")
        line(f"  {arm}: size-only loss - rotation-only loss", ls, lr)
    print("\nCONSISTENCY  param200 here vs the earlier gen sweep's `param` (same seeds/settings; expect identical if deterministic)")
    old = load_gen1()
    if all((s, "param", k) in old for s, k in cells):
        for ev in ("train", "heldout"):
            o = np.array([old[(s, "param", k)]["eval"][ev]["iou"] for s, k in cells])
            print(f"  {ev}: earlier {o.mean():.3f}  now {g('param200', ev).mean():.3f}  "
                  f"max |diff| {np.abs(o - g('param200', ev)).max():.4f}")
    print("\nper (shape, seed) heldout IoU:  cell   param200   param600")
    for i, (s, k) in enumerate(cells):
        print(f"  {s:9s} seed={k:<4d} {g('param200','heldout')[i]:.3f}  {g('param600','heldout')[i]:.3f}")


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
