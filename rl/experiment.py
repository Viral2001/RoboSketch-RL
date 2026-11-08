"""
RoboSketch-RL  |  Phase C - multi-seed H2 experiment (publication-grade)
-------------------------------------------------
Single-run RL numbers are not credible (high variance). This runs the
ground-truth-vs-vision (H2) comparison across several seeds per shape and
records every run, so we can report mean +/- std instead of one lucky number.

RESUMABLE: each finished run is appended to results/h2_seeds.jsonl immediately,
and already-done (shape, mode, seed) combos are skipped on restart. Runs are
ordered seed-major, so even a partial sweep gives >=1 seed everywhere first.

  # run the sweep (resumes if interrupted)
  conda run -n robosketch python rl/experiment.py --seeds 0 1 2 --timesteps 200000
  # summarise what's collected so far (table + figure with error bars)
  conda run -n robosketch python rl/experiment.py --aggregate
"""
import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from draw_env import DrawEnv

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results", "h2_seeds.jsonl")
SHAPES = ["line", "circle", "square", "triangle"]
MODES = ["truth", "vision"]


def _sd(x):
    """Sample standard deviation (ddof=1), 0.0 when there is nothing to spread.

    Every +/- printed by this module is estimated from a handful of seeds, so it
    is a sample statistic. ddof=0 would understate it by ~18-29% at n=2-3.
    """
    x = np.asarray(x, float)
    return float(x.std(ddof=1)) if x.size > 1 else 0.0

def load_done():
    """Read RESULTS and any shard files beside it (`<name>_a.jsonl`, ...).

    Sharding lets the sweep be split across concurrent processes on a machine
    with few cores; each worker writes its own file so no two processes append
    to the same one.
    """
    import glob as _glob
    done = {}
    for path in sorted(_glob.glob(RESULTS.replace(".jsonl", "*.jsonl"))):
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                r = json.loads(line)
                done[(r["shape"], r["mode"], r["seed"])] = r
    return done


def warn_config_drift(done, requested, fields=("timesteps", "max_steps", "step_size")):
    """Shout if already-recorded runs were produced with different settings.

    The resume key is (shape, mode/arm, seed) only - it deliberately ignores the
    run configuration, so `--timesteps 500000` on a file built at 200000 would
    print "0 to go" and then summarise the OLD numbers under the new banner.
    Nothing enforces the match, so the least this can do is say so. Records
    written before a field existed are skipped rather than reported as drift.

    Returns the number of mismatching records.
    """
    bad = {}
    for key, r in done.items():
        for f in fields:
            if f in r and f in requested and r[f] != requested[f]:
                bad.setdefault(f, []).append((key, r[f], requested[f]))
    if bad:
        print("!" * 72)
        print("WARNING: the results file already holds runs made with different settings.")
        for f, items in sorted(bad.items()):
            got = sorted({i[1] for i in items})
            print(f"  {f}: {len(items)} recorded run(s) have {got}, "
                  f"this invocation asks for {requested[f]}")
        print("  Those runs will be REUSED as-is (the resume key ignores config).")
        print("  Use --out to start a clean file if you meant to change the setting.")
        print("!" * 72, flush=True)
    return sum(len(v) for v in bad.values())


def make_env(shape, mode, seed, max_steps, step_size, time_in_obs=False, **env_kwargs):
    def _f():
        return DrawEnv(shape=shape, use_arm=False, max_steps=max_steps,
                       step_size_m=step_size, reward_mode=mode,
                       time_in_obs=time_in_obs, seed=seed, **env_kwargs)
    return _f


def train_eval(shape, mode, seed, timesteps, n_envs, max_steps, step_size,
               eval_eps=8, time_in_obs=False, env_kwargs=None, stop_bias=None):
    """Train one PPO agent and evaluate it. Returns a dict of eval metrics.

    `time_in_obs` is the O1 ablation switch (proposal 3.1): False reproduces
    every result recorded before O1 existed, True adds the remaining-time
    channel. Everything else about the protocol is identical, which is what
    makes the two arms comparable.

    `env_kwargs` passes any other DrawEnv switch straight through (e.g.
    `allow_stop`, `plateau_patience` for the overrun work) so a new ablation
    does not need another parameter here. It is applied to BOTH the training
    envs and the evaluation env - an agent with a stop action must be evaluated
    with one.

    `stop_bias` sets the initial bias of the stop head (action dim 3). It only
    applies when `allow_stop` is on. Without it the head starts at 0, so a unit
    Gaussian puts ~31% of its mass above the 0.5 threshold and an untrained
    episode lasts ~3 steps - far too short to ever trace a closed shape, so the
    policy never sees the payoff for finishing and locks into stopping. A bias
    of -2.0 drops the per-step stop probability to ~0.6% (untrained episodes
    ~160 steps) while leaving the head free to learn to stop. This is a declared
    prior on the policy, not an environment change, and must be reported as one.
    """
    from stable_baselines3 import PPO
    from stable_baselines3.common.vec_env import DummyVecEnv, VecMonitor

    ek = dict(env_kwargs or {})
    venv = DummyVecEnv([make_env(shape, mode, seed + i, max_steps, step_size,
                                 time_in_obs, **ek)
                        for i in range(n_envs)])
    venv = VecMonitor(venv)
    model = PPO("CnnPolicy", venv, verbose=0, seed=seed,
                n_steps=512, batch_size=256, n_epochs=6, gamma=0.99,
                ent_coef=0.02, learning_rate=3e-4)
    if stop_bias is not None and ek.get("allow_stop"):
        with __import__("torch").no_grad():
            model.policy.action_net.bias[3] = float(stop_bias)
    model.learn(total_timesteps=timesteps, progress_bar=False)

    env = DrawEnv(shape=shape, use_arm=False, max_steps=max_steps,
                  step_size_m=step_size, reward_mode=mode,
                  time_in_obs=time_in_obs, seed=10_000 + seed, **ek)
    keys = ("iou", "peak_iou", "overshoot", "steps_used",
            "coverage", "snr", "path_ratio")
    acc = {k: [] for k in keys}
    for ep in range(eval_eps):
        obs, _ = env.reset(seed=20_000 + seed * 100 + ep)
        done = False
        info = {}
        while not done:
            a, _ = model.predict(obs, deterministic=True)
            obs, r, term, trunc, info = env.step(a)
            done = term or trunc
        for k in keys:
            acc[k].append(info[k])
    env.close()
    venv.close()
    return {k: float(np.mean(v)) for k, v in acc.items()}


def run(args):
    os.makedirs(os.path.dirname(RESULTS), exist_ok=True)
    shapes = args.shapes or SHAPES
    shard = RESULTS if not args.shard else RESULTS.replace(".jsonl", f"_{args.shard}.jsonl")
    done = load_done()
    warn_config_drift(done, {"timesteps": args.timesteps,
                             "max_steps": args.max_steps,
                             "step_size": args.step_size})
    combos = [(shape, mode, seed) for seed in args.seeds
              for shape in shapes for mode in MODES]        # seed-major
    todo = [c for c in combos if c not in done]
    print(f"{len(done)} runs done, {len(todo)} to go "
          f"(seeds={args.seeds}, {args.timesteps} steps each)\n", flush=True)
    for k, (shape, mode, seed) in enumerate(todo, 1):
        print(f"[{k}/{len(todo)}] {shape:8s} {mode:6s} seed={seed} ...", flush=True)
        m = train_eval(shape, mode, seed, args.timesteps, args.n_envs,
                       args.max_steps, args.step_size)
        rec = {"shape": shape, "mode": mode, "seed": seed,
               "iou": round(m["iou"], 4), "coverage": round(m["coverage"], 4),
               # peak_iou is what the policy actually achieved before it
               # overshot; `iou` is what it is scored on. Recording both is the
               # whole point of this re-run - see the overshoot entries in
               # docs/RESEARCH_LOG.md.
               "peak_iou": round(m["peak_iou"], 4),
               "overshoot": round(m["overshoot"], 4),
               "steps_used": round(m["steps_used"], 1),
               "snr": round(m["snr"], 3), "path_ratio": round(m["path_ratio"], 3),
               # the run configuration, so a file can never silently mix
               # settings: the resume key is (shape, mode, seed) only.
               "timesteps": args.timesteps, "max_steps": args.max_steps,
               "step_size": args.step_size,
               # torch's thread count changes the order of floating-point
               # reductions, so it changes a SEEDED run's result: measured, the
               # same cell gives IoU 0.175 on 2 threads and 0.195 on 1. Runs are
               # only bitwise comparable to runs with the same value here.
               "torch_threads": __import__("torch").get_num_threads()}
        with open(shard, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")
        print(f"        -> IoU {m['iou']:.3f}  peak {m['peak_iou']:.3f}  "
              f"overshoot {m['overshoot']:.3f}  coverage {m['coverage']:.3f}",
              flush=True)
    print(f"\nsweep complete for shapes={shapes} seeds={args.seeds}.")
    if not args.shard:
        aggregate()


def aggregate():
    done = load_done()
    if not done:
        print("no results yet.")
        return
    # group by (shape, mode)
    from collections import defaultdict
    g = defaultdict(list)
    for (shape, mode, seed), r in done.items():
        g[(shape, mode)].append(r["iou"])

    print("\n=== H2 multi-seed results (true IoU, mean +/- std) ===")
    print(f"{'shape':<9} {'ground-truth':>18} {'camera(vision)':>18} {'n':>4}")
    print("-" * 54)
    rows = []
    for shape in SHAPES:
        t = g.get((shape, "truth"), [])
        v = g.get((shape, "vision"), [])
        tm, ts = (np.mean(t), _sd(t)) if t else (float("nan"), 0)
        vm, vs = (np.mean(v), _sd(v)) if v else (float("nan"), 0)
        n = min(len(t), len(v))
        print(f"{shape:<9} {tm:>10.3f} +/-{ts:4.3f}  {vm:>10.3f} +/-{vs:4.3f} {n:>4}")
        rows.append((shape, tm, ts, vm, vs, len(t), len(v)))
    allt = [r["iou"] for (s, m, sd), r in done.items() if m == "truth"]
    allv = [r["iou"] for (s, m, sd), r in done.items() if m == "vision"]
    if allt and allv:
        print("-" * 54)
        print(f"{'MEAN':<9} {np.mean(allt):>10.3f} +/-{_sd(allt):4.3f}  "
              f"{np.mean(allv):>10.3f} +/-{_sd(allv):4.3f}")
    _figure(rows)


def _figure(rows):
    try:
        import cv2
    except Exception:
        return
    W, H = 1180, 460
    img = np.full((H, W, 3), 255, np.uint8)
    cv2.putText(img, "H2: ground-truth vs camera reward (true IoU, mean +/- std over seeds)",
                (24, 34), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1, cv2.LINE_AA)
    x0, y0, bw, gap, plotH = 90, 400, 60, 90, 300   # gap tightened so all 4 groups fit in W
    ymax = 0.6
    cv2.line(img, (x0 - 18, y0), (W - 30, y0), (150, 150, 150), 1)
    cv2.line(img, (x0 - 18, y0), (x0 - 18, y0 - plotH), (150, 150, 150), 1)
    for gy in (0.2, 0.4, 0.6):
        yy = int(y0 - gy / ymax * plotH)
        cv2.line(img, (x0 - 22, yy), (x0 - 14, yy), (150, 150, 150), 1)
        cv2.putText(img, f"{gy:.1f}", (x0 - 60, yy + 5), cv2.FONT_HERSHEY_SIMPLEX,
                    0.45, (90, 90, 90), 1, cv2.LINE_AA)
    for i, (shape, tm, ts, vm, vs, nt, nv) in enumerate(rows):
        cx = x0 + i * gap + i * 2 * bw
        for j, (m, s, col, lab) in enumerate([(tm, ts, (60, 60, 60), "truth"),
                                              (vm, vs, (200, 70, 60), "cam")]):
            if np.isnan(m):
                continue
            bx = cx + j * bw
            bh = int(m / ymax * plotH)
            cv2.rectangle(img, (bx, y0 - bh), (bx + bw - 8, y0), col, -1)
            ey = y0 - bh
            eh = int(s / ymax * plotH)
            cv2.line(img, (bx + (bw - 8) // 2, ey - eh), (bx + (bw - 8) // 2, ey + eh),
                     (20, 20, 20), 2)
            cv2.putText(img, f"{m:.2f}", (bx - 2, y0 - bh - 14 if j == 0 else y0 - bh - 14),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.42, col, 1, cv2.LINE_AA)
        cv2.putText(img, shape, (cx + 4, y0 + 22), cv2.FONT_HERSHEY_SIMPLEX,
                    0.5, (0, 0, 0), 1, cv2.LINE_AA)
    cv2.rectangle(img, (W - 190, 54), (W - 176, 66), (60, 60, 60), -1)
    cv2.putText(img, "ground truth", (W - 170, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (60, 60, 60), 1)
    cv2.rectangle(img, (W - 190, 74), (W - 176, 86), (200, 70, 60), -1)
    cv2.putText(img, "camera (vision)", (W - 170, 85), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 70, 60), 1)
    # name the figure after the results file, so running a second sweep into a
    # different file cannot overwrite the published figure
    stem = os.path.basename(RESULTS).replace(".jsonl", "")
    name = "results_h2_seeds.png" if stem == "h2_seeds" else f"results_{stem}.png"
    cv2.imwrite(os.path.join(ROOT, "output", name), img)
    print(f"\nfigure: output/{name}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    ap.add_argument("--timesteps", type=int, default=200_000)
    ap.add_argument("--n-envs", type=int, default=8)
    ap.add_argument("--max-steps", type=int, default=240)
    ap.add_argument("--step-size", type=float, default=0.014)
    ap.add_argument("--shapes", nargs="+", choices=SHAPES,
                    help="run only these shapes (to split the sweep across processes)")
    ap.add_argument("--shard", default="",
                    help="name for this worker's results file, e.g. --shard a")
    ap.add_argument("--out", default="h2_seeds.jsonl",
                    help="results file under results/. Use a different name to run "
                         "a fresh sweep without touching the published one.")
    ap.add_argument("--aggregate", action="store_true", help="just summarise existing results")
    args = ap.parse_args()
    RESULTS = os.path.join(ROOT, "results", args.out)
    if args.aggregate:
        aggregate()
    else:
        run(args)
