"""
RoboSketch-RL  |  Stage 4 ablation A1: action chunking (D02 "action bundle").
Arm `chunk5`: gen2 `param200` protocol (train family, vision reward, privileged observation, global 64-px view, max_steps 240,
step 0.014) but the policy outputs K=5 pen moves per decision, executed in order by a wrapper (no change to draw_env.py).
Per-decision PPO settings are rescaled so the comparison is at the SAME number of environment steps:
  total decisions = 200k / K, gamma = 0.99**K (same per-env-step horizon), n_steps = 128 and batch_size = 64
  (rollout ~= 5120 env steps vs 4096; 16 minibatches per epoch, as in param200). Reward of a decision = sum_i gamma0**i * r_i.
Compared with param200 (results/gen2_*.jsonl), paired by (shape, seed): 4 shapes x seeds {0,100} = 8 runs.
Pre-registered in docs/RESEARCH_LOG.md "A1 action chunking launched".
  $env:OMP_NUM_THREADS=1; $env:MKL_NUM_THREADS=1
  conda run -n robosketch --no-capture-output python rl/chunk_experiment.py --seeds 0 100 --shapes line circle --shard a
  conda run -n robosketch --no-capture-output python rl/chunk_experiment.py --seeds 0 100 --shapes square triangle --shard b
  conda run -n robosketch --no-capture-output python rl/chunk_experiment.py --aggregate
"""
import argparse
import glob
import json
import os
import sys

import gymnasium as gym
import numpy as np
from gymnasium import spaces

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from draw_env import DrawEnv
from experiment import warn_config_drift, _sd
from gen_experiment import _paired
import gen2_experiment as G2

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results", "chunk.jsonl")
SHAPES = G2.SHAPES
EVAL_SETS = G2.EVAL_SETS
ENV_STEPS = 200_000          # same environment-step budget as param200
K = 5                        # chunk length (D02 uses 5; fixed before running, not tuned)
GAMMA0 = 0.99                # param200's per-env-step discount
ARM = f"chunk{K}"


class ChunkWrapper(gym.Wrapper):
    """One decision = K consecutive DrawEnv actions. Stops early if the episode ends inside a chunk."""

    def __init__(self, env, k=K, gamma0=GAMMA0):
        super().__init__(env)
        self.k, self.gamma0 = k, gamma0
        lo, hi = env.action_space.low, env.action_space.high
        self.adim = lo.shape[0]
        self.action_space = spaces.Box(low=np.tile(lo, k), high=np.tile(hi, k), dtype=np.float32)
        self.env_steps = 0

    def step(self, action):
        acts = np.asarray(action, np.float32).reshape(self.k, self.adim)
        total, obs, term, trunc, info = 0.0, None, False, False, {}
        for i in range(self.k):
            obs, r, term, trunc, info = self.env.step(acts[i])
            self.env_steps += 1
            total += (self.gamma0 ** i) * r
            if term or trunc:
                break
        return obs, float(total), term, trunc, info


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
    return lambda: ChunkWrapper(DrawEnv(shape=shape, use_arm=False, max_steps=max_steps, step_size_m=step_size,
                                        reward_mode="vision", target_split=split, seed=seed))


def train_eval(shape, seed, n_envs, max_steps, step_size, eval_eps):
    from stable_baselines3 import PPO
    from stable_baselines3.common.vec_env import DummyVecEnv, VecMonitor

    envs = [_make(shape, "train", seed + i, max_steps, step_size) for i in range(n_envs)]
    venv = VecMonitor(DummyVecEnv(envs))
    model = PPO("CnnPolicy", venv, verbose=0, seed=seed, n_steps=128, batch_size=64,
                n_epochs=6, gamma=GAMMA0 ** K, ent_coef=0.02, learning_rate=3e-4)
    model.learn(total_timesteps=ENV_STEPS // K, progress_bar=False)
    train_env_steps = int(sum(e.env_steps for e in venv.venv.envs))
    out = {}
    for name, es in EVAL_SETS.items():
        env = _make(shape, es, 10_000 + seed, max_steps, step_size)()
        ious, peaks, paths, steps = [], [], [], []
        for ep in range(eval_eps):
            obs, _ = env.reset(seed=20_000 + ep)         # same targets as param200
            done, info = False, {}
            while not done:
                a, _ = model.predict(obs, deterministic=True)
                obs, r, term, trunc, info = env.step(a)
                done = term or trunc
            ious.append(info["iou"]); peaks.append(info["peak_iou"])
            paths.append(info["path_ratio"]); steps.append(info["steps_used"])
        env.close()
        out[name] = {"iou": float(np.mean(ious)), "peak_iou": float(np.mean(peaks)),
                     "path_ratio": float(np.mean(paths)), "steps_used": float(np.mean(steps)),
                     "iou_eps": [round(float(x), 4) for x in ious]}
    venv.close()
    return out, train_env_steps


def run(args):
    os.makedirs(os.path.dirname(RESULTS), exist_ok=True)
    shard = RESULTS if not args.shard else RESULTS.replace(".jsonl", f"_{args.shard}.jsonl")
    done = load_done()
    warn_config_drift(done, {"max_steps": args.max_steps, "step_size": args.step_size,
                             "eval_eps": args.eval_eps, "timesteps": ENV_STEPS})
    shapes = args.shapes or SHAPES
    todo = [(s, ARM, k) for k in args.seeds for s in shapes if (s, ARM, k) not in done]
    print(f"{len(done)} runs done, {len(todo)} to go (seeds={args.seeds})\n", flush=True)
    for i, (shape, arm, seed) in enumerate(todo, 1):
        print(f"[{i}/{len(todo)}] {shape:8s} {ARM} seed={seed} ...", flush=True)
        m, n_env = train_eval(shape, seed, args.n_envs, args.max_steps, args.step_size, args.eval_eps)
        rec = {"shape": shape, "arm": ARM, "seed": seed, "mode": "vision", "timesteps": ENV_STEPS,
               "chunk_k": K, "decisions": ENV_STEPS // K, "train_env_steps": n_env,
               "max_steps": args.max_steps, "step_size": args.step_size, "eval_eps": args.eval_eps,
               "torch_threads": __import__("torch").get_num_threads(), "eval": m}
        with open(shard, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")
        print("        -> " + "  ".join(f"{n} {m[n]['iou']:.3f}" for n in EVAL_SETS)
              + f"  (train env steps {n_env})", flush=True)
    if not args.shard:
        aggregate()


def aggregate():
    ch, glob_ = load_done(), G2.load_done()
    cells = sorted({(s, k) for (s, a, k) in ch if (s, "param200", k) in glob_})
    if not cells:
        print("no complete cells yet.")
        return

    def get(src, arm):
        return lambda ev, key="iou": np.array([src[(s, arm, k)]["eval"][ev][key] for s, k in cells])
    G, C = get(glob_, "param200"), get(ch, ARM)
    print(f"\n=== A1 action chunking (K={K}) vs param200: TRUE IoU, n={len(cells)} (shape, seed) cells, 16 targets/set ===")
    print(f"{'arm':<10}" + "".join(f"{e:>20}" for e in EVAL_SETS))
    for lab, g in (("param200", G), (ARM, C)):
        print(f"{lab:<10}" + "".join(f"{g(e).mean():>12.3f} +/-{_sd(g(e)):.3f}" for e in EVAL_SETS))
    print("peak IoU")
    for lab, g in (("param200", G), (ARM, C)):
        print(f"{lab:<10}" + "".join(f"{g(e, 'peak_iou').mean():>20.3f}" for e in EVAL_SETS))

    def line(label, x, y):
        d, up, m, t = _paired(x, y)
        print(f"  {label:<52} {d:+.3f}  {up}/{m} up  t={t:+.2f}")

    print(f"\nPRIMARY    heldout IoU, {ARM} - param200 (>0 = chunking helps; crit |t|=2.37 at n=8)")
    line(f"heldout: {ARM} - param200", C("heldout"), G("heldout"))
    print(f"\nSECONDARY  {ARM} - param200 on the other sets")
    for e in ("train", "default", "heldout_scale", "heldout_rot"):
        line(f"{e}: {ARM} - param200", C(e), G(e))
    print("\nLOSS train->heldout")
    for lab, g in (("param200", G), (ARM, C)):
        print(f"  {lab}: {np.mean(g('train') - g('heldout')):+.3f}")
    line(f"loss: param200 - {ARM} (>0 = chunk loses LESS)", G("train") - G("heldout"), C("train") - C("heldout"))
    print(f"\nDESCRIPTIVE ({ARM} only; param200 rows did not record these)")
    print("  path_ratio " + "  ".join(f"{e} {C(e, 'path_ratio').mean():.2f}" for e in EVAL_SETS))
    print("  steps_used " + "  ".join(f"{e} {C(e, 'steps_used').mean():.0f}" for e in EVAL_SETS))
    print("  train env steps per run: " + " ".join(str(ch[(s, ARM, k)].get("train_env_steps")) for s, k in cells))
    print(f"\nper (shape, seed) heldout IoU:  cell   param200   {ARM}")
    for i, (s, k) in enumerate(cells):
        print(f"  {s:9s} seed={k:<4d} {G('heldout')[i]:.3f}  {C('heldout')[i]:.3f}")


def smoke():
    """Wrapper check without training: shapes, early stop, reward sum, and K=1 equivalence with the raw env."""
    raw = DrawEnv(shape="circle", use_arm=False, max_steps=240, step_size_m=0.014, reward_mode="vision",
                  target_split="train", seed=3)
    w1 = ChunkWrapper(DrawEnv(shape="circle", use_arm=False, max_steps=240, step_size_m=0.014, reward_mode="vision",
                              target_split="train", seed=3), k=1)
    rng = np.random.default_rng(0)
    o0, _ = raw.reset(seed=7); o1, _ = w1.reset(seed=7)
    same = np.array_equal(o0, o1)
    for _ in range(240):
        a = rng.uniform(raw.action_space.low, raw.action_space.high).astype(np.float32)
        o0, r0, t0, tr0, i0 = raw.step(a); o1, r1, t1, tr1, i1 = w1.step(a)
        same &= np.array_equal(o0, o1) and r0 == r1 and (t0, tr0) == (t1, tr1)
        if t0 or tr0:
            break
    print(f"K=1 wrapper identical to raw env: {same}")
    w = _make("square", "train", 5, 240, 0.014)()
    obs, _ = w.reset(seed=1)
    print(f"action space {w.action_space.shape}, obs {obs.shape}")
    n, done = 0, False
    while not done:
        obs, r, term, trunc, info = w.step(w.action_space.sample())
        n += 1; done = term or trunc
    print(f"decisions per episode {n}, env steps {info['steps_used']}, env_steps counter {w.env_steps}")


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
    ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args()
    smoke() if a.smoke else (aggregate() if a.aggregate else run(a))
