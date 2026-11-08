"""
RoboSketch-RL  |  Stage 4 ablation T1: behaviour-cloning (BC) warm start (proposal 3.4 / section 8 item 14).
Arm `bc200`: gen2 `param200` protocol EXACTLY (train family, vision reward, privileged global 64-px observation,
max_steps 240, step 0.014, 8 envs, PPO n_steps 512, batch 256, 6 epochs, gamma 0.99, ent 0.02, lr 3e-4, 200k PPO
steps, same seed) - except that BEFORE PPO the policy's action MEAN is pre-trained by behaviour cloning on
demonstrations from an analytic expert that traces the target outline. No change to draw_env.py.

Expert (privileged; reads the env's target parameters): from the pen's start point it walks the outline at full
step length (closed shapes: once round, back to the start; line: to the nearer end, then to the far end), then
holds still (action 0). Demonstrations: DEMO_EPS episodes of the TRAIN family (no held-out targets), reset seeds
30_000 + 1000*seed + j (disjoint from eval seeds 20_000..20_015), at most IDLE_CAP still steps kept per episode.
BC: MSE between the policy's mean (dx, dy) and the expert's, Adam lr BC_LR, BC_EPOCHS epochs, batch 256;
log_std and the value head are NOT trained (PPO keeps its default exploration noise). pen_down is ignored by the
env (pen_always_down=True) and is not cloned.

Also recorded per run (descriptive): `bc0` = the cloned policy before any PPO, and `expert` = the expert itself.
Compared with param200 (results/gen2_*.jsonl), paired by (shape, seed): 4 shapes x seeds {0,100} = 8 runs.
Pre-registered in docs/RESEARCH_LOG.md "T1 BC warm start launched".
  $env:OMP_NUM_THREADS=1; $env:MKL_NUM_THREADS=1
  conda run -n robosketch --no-capture-output python rl/bc_experiment.py --seeds 0 100 --shapes line circle --shard a
  conda run -n robosketch --no-capture-output python rl/bc_experiment.py --seeds 0 100 --shapes square triangle --shard b
  conda run -n robosketch --no-capture-output python rl/bc_experiment.py --aggregate
"""
import argparse
import glob
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import targets as T
from experiment import warn_config_drift, _sd
from gen_experiment import _make, _paired
import gen2_experiment as G2

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results", "bc.jsonl")
SHAPES = G2.SHAPES
EVAL_SETS = G2.EVAL_SETS
TIMESTEPS = 200_000          # PPO steps, same as param200
ARM = "bc200"
DEMO_EPS = 200               # fixed before running, not tuned
IDLE_CAP = 20
BC_EPOCHS = 20
BC_BATCH = 256
BC_LR = 1e-3
CIRCLE_N = 96                # polygon vertices used to trace the circle


class Expert:
    """Analytic outline tracer. Call reset(env) after env.reset(); then act(env) each step."""

    def reset(self, env):
        s, th = env.target_params
        lo, hi = T._extent(512)
        h = (hi - lo) / 2.0 * s
        a = np.deg2rad(th)
        ca, sa = np.cos(a), np.sin(a)
        name = env.shape_name
        if name == "line":
            loc, closed = [[-h, 0], [h, 0]], False
        elif name == "circle":
            r = int(round(h))                                   # as in targets.make_param
            t = np.linspace(0, 2 * np.pi, CIRCLE_N, endpoint=False)
            loc, closed, ca, sa = np.stack([r * np.cos(t), r * np.sin(t)], 1), True, 1.0, 0.0
        elif name == "square":
            loc, closed = [[-h, -h], [h, -h], [h, h], [-h, h]], True
        else:
            loc, closed = [[0, -h], [-h, h], [h, h]], True
        p = np.asarray(loc, float)
        x512 = p[:, 0] * ca - p[:, 1] * sa + 256.0
        y512 = p[:, 0] * sa + p[:, 1] * ca + 256.0
        r = env.canvas_res
        cpx = (x512 + 0.5) * r / 512.0 - 0.5                    # INTER_AREA 512 -> canvas pixel centres
        rpx = (y512 + 0.5) * r / 512.0 - 0.5
        verts = np.array([env._px_to_world(c, w) for c, w in zip(cpx, rpx)])
        if closed:
            verts = np.vstack([verts, verts[:1]])
        dense = [verts[0]]                                       # ~0.5 mm spacing along the outline
        for v0, v1 in zip(verts[:-1], verts[1:]):
            n = max(1, int(np.ceil(np.linalg.norm(v1 - v0) / 5e-4)))
            dense += [v0 + (v1 - v0) * (k / n) for k in range(1, n + 1)]
        dense = np.array(dense)
        start = np.asarray(env.pen_xy, float)
        i0 = int(np.argmin(((dense - start) ** 2).sum(1)))
        if closed:
            body = dense[:-1]
            path = np.vstack([body[i0:], body[:i0 + 1]])
        else:
            first = dense[i0::-1] if i0 <= len(dense) - 1 - i0 else dense[i0:]
            second = dense if i0 <= len(dense) - 1 - i0 else dense[::-1]
            path = np.vstack([first, second])
        self.path = np.vstack([start[None], path])
        seg = np.linalg.norm(np.diff(self.path, axis=0), axis=1)
        self.cum = np.concatenate([[0.0], np.cumsum(seg)])
        self.prog = 0.0
        self.finished = False

    def act(self, env):
        nxt = min(self.prog + env.step_size, self.cum[-1])
        if self.cum[-1] - self.prog < 1e-9:
            self.finished = True
            return np.array([0.0, 0.0, 1.0], np.float32)
        tgt = np.array([np.interp(nxt, self.cum, self.path[:, 0]), np.interp(nxt, self.cum, self.path[:, 1])])
        d = np.clip((tgt - np.asarray(env.pen_xy, float)) / env.step_size, -1.0, 1.0)
        self.prog = nxt
        return np.array([d[0], d[1], 1.0], np.float32)


def collect_demos(shape, seed, max_steps, step_size, n_eps=DEMO_EPS):
    env = _make(shape, "train", 50_000 + seed, max_steps, step_size)()
    ex, obs_l, act_l, ious = Expert(), [], [], []
    for j in range(n_eps):
        obs, _ = env.reset(seed=30_000 + 1000 * seed + j)
        ex.reset(env)
        done, idle, info = False, 0, {}
        while not done and idle < IDLE_CAP:
            a = ex.act(env)
            obs_l.append(np.transpose(obs, (2, 0, 1)).copy()); act_l.append(a[:2])
            idle += ex.finished
            obs, r, term, trunc, info = env.step(a)
            done = term or trunc
        ious.append(info.get("iou", 0.0))
    env.close()
    return np.stack(obs_l), np.stack(act_l).astype(np.float32), float(np.mean(ious))


def bc_pretrain(model, obs, acts, seed, epochs=BC_EPOCHS):
    import torch as th
    pol = model.policy
    params = [p for n, p in pol.named_parameters() if n != "log_std" and not n.startswith("value_net")]
    opt = th.optim.Adam(params, lr=BC_LR)
    rng = np.random.default_rng(seed)
    pol.set_training_mode(True)
    hist = []
    for ep in range(epochs):
        idx, tot = rng.permutation(len(obs)), 0.0
        for b in range(0, len(idx), BC_BATCH):
            j = idx[b:b + BC_BATCH]
            o = th.as_tensor(obs[j], device=pol.device)
            y = th.as_tensor(acts[j], device=pol.device)
            mean = pol.get_distribution(o).distribution.mean[:, :2]
            loss = ((mean - y) ** 2).mean()
            opt.zero_grad(); loss.backward(); opt.step()
            tot += float(loss.detach()) * len(j)
        hist.append(tot / len(obs))
    pol.set_training_mode(False)
    return hist


def evaluate(shape, seed, max_steps, step_size, eval_eps, policy=None):
    """policy=None -> the expert. Same targets (reset seeds 20_000+ep) as param200."""
    out = {}
    for name, es in EVAL_SETS.items():
        env = _make(shape, es, 10_000 + seed, max_steps, step_size)()
        ex = Expert()
        ious, peaks, paths, steps = [], [], [], []
        for ep in range(eval_eps):
            obs, _ = env.reset(seed=20_000 + ep)
            ex.reset(env)
            done, info = False, {}
            while not done:
                a = ex.act(env) if policy is None else policy.predict(obs, deterministic=True)[0]
                obs, r, term, trunc, info = env.step(a)
                done = term or trunc
            ious.append(info["iou"]); peaks.append(info["peak_iou"])
            paths.append(info["path_ratio"]); steps.append(info["steps_used"])
        env.close()
        out[name] = {"iou": float(np.mean(ious)), "peak_iou": float(np.mean(peaks)),
                     "path_ratio": float(np.mean(paths)), "steps_used": float(np.mean(steps)),
                     "iou_eps": [round(float(x), 4) for x in ious]}
    return out


def build_model(shape, seed, n_envs, max_steps, step_size):
    from stable_baselines3 import PPO
    from stable_baselines3.common.vec_env import DummyVecEnv, VecMonitor
    venv = VecMonitor(DummyVecEnv([_make(shape, "train", seed + i, max_steps, step_size) for i in range(n_envs)]))
    model = PPO("CnnPolicy", venv, verbose=0, seed=seed, n_steps=512, batch_size=256,
                n_epochs=6, gamma=0.99, ent_coef=0.02, learning_rate=3e-4)
    return model, venv


def train_eval(shape, seed, n_envs, max_steps, step_size, eval_eps):
    model, venv = build_model(shape, seed, n_envs, max_steps, step_size)
    t0 = time.time()
    obs, acts, demo_iou = collect_demos(shape, seed, max_steps, step_size)
    hist = bc_pretrain(model, obs, acts, seed)
    bc_sec = time.time() - t0
    bc0 = evaluate(shape, seed, max_steps, step_size, eval_eps, policy=model)
    model.learn(total_timesteps=TIMESTEPS, progress_bar=False)
    out = evaluate(shape, seed, max_steps, step_size, eval_eps, policy=model)
    expert = evaluate(shape, seed, max_steps, step_size, eval_eps, policy=None)
    venv.close()
    meta = {"demo_samples": int(len(obs)), "demo_true_iou": round(demo_iou, 4),
            "bc_loss_first": round(hist[0], 5), "bc_loss_last": round(hist[-1], 5), "bc_seconds": round(bc_sec, 1)}
    return out, bc0, expert, meta


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
    warn_config_drift(done, {"max_steps": args.max_steps, "step_size": args.step_size,
                             "eval_eps": args.eval_eps, "timesteps": TIMESTEPS})
    shapes = args.shapes or SHAPES
    todo = [(s, ARM, k) for k in args.seeds for s in shapes if (s, ARM, k) not in done]
    print(f"{len(done)} runs done, {len(todo)} to go (seeds={args.seeds})\n", flush=True)
    for i, (shape, arm, seed) in enumerate(todo, 1):
        print(f"[{i}/{len(todo)}] {shape:8s} {ARM} seed={seed} ...", flush=True)
        m, bc0, ex, meta = train_eval(shape, seed, args.n_envs, args.max_steps, args.step_size, args.eval_eps)
        rec = {"shape": shape, "arm": ARM, "seed": seed, "mode": "vision", "timesteps": TIMESTEPS,
               "demo_eps": DEMO_EPS, "idle_cap": IDLE_CAP, "bc_epochs": BC_EPOCHS, "bc_lr": BC_LR,
               "max_steps": args.max_steps, "step_size": args.step_size, "eval_eps": args.eval_eps,
               "torch_threads": __import__("torch").get_num_threads(), **meta,
               "eval": m, "eval_bc0": bc0, "eval_expert": ex}
        with open(shard, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")
        print("        -> " + "  ".join(f"{n} {m[n]['iou']:.3f}" for n in EVAL_SETS)
              + f"  | bc0 train {bc0['train']['iou']:.3f} heldout {bc0['heldout']['iou']:.3f}", flush=True)
    if not args.shard:
        aggregate()


def aggregate():
    bc, g2 = load_done(), G2.load_done()
    cells = sorted({(s, k) for (s, a, k) in bc if (s, "param200", k) in g2})
    if not cells:
        print("no complete cells yet.")
        return

    def get(src, arm, field="eval"):
        return lambda ev, key="iou": np.array([src[(s, arm, k)][field][ev][key] for s, k in cells])
    G, B = get(g2, "param200"), get(bc, ARM)
    B0, E = get(bc, ARM, "eval_bc0"), get(bc, ARM, "eval_expert")
    print(f"\n=== T1 BC warm start vs param200: TRUE IoU, n={len(cells)} (shape, seed) cells, 16 targets/set ===")
    print(f"{'arm':<16}" + "".join(f"{e:>20}" for e in EVAL_SETS))
    rows = (("param200", G), (ARM, B), ("bc0 (no PPO)", B0), ("expert", E))
    for lab, g in rows:
        print(f"{lab:<16}" + "".join(f"{g(e).mean():>12.3f} +/-{_sd(g(e)):.3f}" for e in EVAL_SETS))
    print("peak IoU")
    for lab, g in rows:
        print(f"{lab:<16}" + "".join(f"{g(e, 'peak_iou').mean():>20.3f}" for e in EVAL_SETS))

    def line(label, x, y):
        d, up, m, t = _paired(x, y)
        print(f"  {label:<52} {d:+.3f}  {up}/{m} up  t={t:+.2f}")

    print(f"\nPRIMARY    heldout IoU, {ARM} - param200 (>0 = BC warm start helps; crit |t|=2.37 at n=8)")
    line(f"heldout: {ARM} - param200", B("heldout"), G("heldout"))
    print(f"\nSECONDARY  {ARM} - param200 on the other sets")
    for e in ("train", "default", "heldout_scale", "heldout_rot"):
        line(f"{e}: {ARM} - param200", B(e), G(e))
    print("\nLOSS train->heldout")
    for lab, g in (("param200", G), (ARM, B), ("bc0", B0), ("expert", E)):
        print(f"  {lab}: {np.mean(g('train') - g('heldout')):+.3f}")
    line(f"loss: param200 - {ARM} (>0 = BC loses LESS)", G("train") - G("heldout"), B("train") - B("heldout"))
    print("\nDESCRIPTIVE  what PPO did to the cloned policy (bc200 - bc0)")
    for e in ("train", "heldout"):
        line(f"{e}: {ARM} - bc0", B(e), B0(e))
    print("  path_ratio " + "  ".join(f"{lab} {g('heldout', 'path_ratio').mean():.2f}"
                                       for lab, g in ((ARM, B), ("bc0", B0), ("expert", E))) + "  (heldout)")
    print("  demo samples " + " ".join(str(bc[(s, ARM, k)]["demo_samples"]) for s, k in cells)
          + " | bc loss first->last " + " ".join(f"{bc[(s, ARM, k)]['bc_loss_first']:.3f}->{bc[(s, ARM, k)]['bc_loss_last']:.4f}"
                                                for s, k in cells))
    print(f"\nper (shape, seed) heldout IoU:  cell   param200   {ARM}   bc0   expert")
    for i, (s, k) in enumerate(cells):
        print(f"  {s:9s} seed={k:<4d} {G('heldout')[i]:.3f}  {B('heldout')[i]:.3f}  {B0('heldout')[i]:.3f}  {E('heldout')[i]:.3f}")


def smoke(args):
    """No PPO. Expert quality on every shape (train set only) + one BC fit, bc0 scored on the TRAIN set only."""
    for shape in SHAPES:
        env = _make(shape, "train", 1, args.max_steps, args.step_size)()
        ex, ious, peaks = Expert(), [], []
        for ep in range(8):
            obs, _ = env.reset(seed=90_000 + ep)
            ex.reset(env)
            done, info = False, {}
            while not done:
                obs, r, term, trunc, info = env.step(ex.act(env))
                done = term or trunc
            ious.append(info["iou"]); peaks.append(info["peak_iou"])
        print(f"expert {shape:8s} train: final IoU {np.mean(ious):.3f}  peak {np.mean(peaks):.3f}  "
              f"(min {np.min(ious):.3f})  path len {ex.cum[-1]:.3f} m = {ex.cum[-1] / args.step_size:.0f} steps")
        env.close()
    shape = args.shapes[0] if args.shapes else "square"
    t0 = time.time()
    obs, acts, demo_iou = collect_demos(shape, 7, args.max_steps, args.step_size)
    print(f"\ndemos {shape}: {len(obs)} samples, obs {obs.shape}, mean |a| {np.abs(acts).mean():.3f}, "
          f"demo IoU {demo_iou:.3f}, {time.time() - t0:.0f}s")
    model, venv = build_model(shape, 7, 2, args.max_steps, args.step_size)
    print(f"policy obs space {model.policy.observation_space.shape}")
    t0 = time.time()
    hist = bc_pretrain(model, obs, acts, 7)
    print(f"BC loss by epoch: {' '.join(f'{h:.4f}' for h in hist)}  ({time.time() - t0:.0f}s)")
    env = _make(shape, "train", 7, args.max_steps, args.step_size)()
    ious = []
    for ep in range(8):
        o, _ = env.reset(seed=91_000 + ep)
        done, info = False, {}
        while not done:
            o, r, term, trunc, info = env.step(model.predict(o, deterministic=True)[0])
            done = term or trunc
        ious.append(info["iou"])
    print(f"bc0 {shape} TRAIN-set IoU (8 eps, not eval targets): {np.mean(ious):.3f}")
    venv.close()


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
    smoke(a) if a.smoke else (aggregate() if a.aggregate else run(a))
