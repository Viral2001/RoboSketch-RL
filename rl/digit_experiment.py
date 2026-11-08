"""
RoboSketch-RL  |  Stage 6 step 2b(iii): can a pen-free PPO agent draw DIGITS?  (first multi-stroke test; descriptive, no hypothesis test)
Digits: '1' and '7' (ONE stroke each) vs '4' and '8' (TWO strokes each, a pen lift is needed to draw them without joining the strokes).
Arm = `penfree` exactly as rl/penfree_experiment.py (DrawEnv(pen_always_down=False), vision reward, privileged global 64-px obs,
240 steps, step 0.014, 8 envs, gen2 PPO settings, 200k steps, evaluated at 0/50k/100k/150k/200k with ONE deterministic episode),
only the target is a glyph from rl/glyphs.py (additive DrawEnv option, shape='0'..'9').
Per run we log TRUE IoU (the score), peak IoU, pen-down fraction, SNR (drawn strokes / target strokes) and, at every checkpoint, the
v2 recognisability numbers from rl/recognise11.py: P(target digit), P(reject) and `legible` (top-1 == target AND P >= 0.5).
8 runs = 4 digits x seeds {0,100}. No baseline arm (always-down cannot draw 4/8; the generic cost of the pen bit is already measured in A2).
Pre-registered in docs/RESEARCH_LOG.md "Stage 6 step 2b".
  $env:OMP_NUM_THREADS=1; $env:MKL_NUM_THREADS=1
  conda run -n robosketch --no-capture-output python rl/digit_experiment.py --seeds 0 100 --shapes 1 4 --shard a
  conda run -n robosketch --no-capture-output python rl/digit_experiment.py --seeds 0 100 --shapes 7 8 --shard b
  conda run -n robosketch --no-capture-output python rl/digit_experiment.py --aggregate
"""
import argparse
import glob
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from experiment import warn_config_drift
from draw_env import DrawEnv
import curriculum_experiment as C
import penfree_experiment as P
import recognise11 as RC
import glyphs as G

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results", "digits.jsonl")
DIGITS = ["1", "7", "4", "8"]
ARM = "penfree_digit"


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
    env = P._make(shape, 10_000 + seed, max_steps, step_size)()
    obs, _ = env.reset(seed=20_000)
    done, info, down, n = False, {}, 0, 0
    while not done:
        a, _ = model.predict(obs, deterministic=True)
        obs, r, term, trunc, info = env.step(a)
        done = term or trunc
        down += int(env.pen_down)
        n += 1
    pr = RC.probs(env.canvas)
    k = G.NAMES.index(shape)
    p_t, p_rej, legible = float(pr[k]), float(pr[RC.REJ]), bool(pr.argmax() == k and pr[k] >= 0.5)
    env.close()
    return dict(iou=float(info["iou"]), peak=float(info["peak_iou"]), down=down / max(n, 1), snr=float(info["snr"]),
                p_target=p_t, p_reject=p_rej, legible=legible)


def train_eval(shape, seed, n_envs, max_steps, step_size):
    from stable_baselines3 import PPO
    from stable_baselines3.common.vec_env import DummyVecEnv, VecMonitor
    venv = VecMonitor(DummyVecEnv([P._make(shape, seed + i, max_steps, step_size) for i in range(n_envs)]))
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
    shapes = args.shapes or DIGITS
    todo = [(s, k) for k in args.seeds for s in shapes if (s, k) not in done]
    print(f"{len(done)} runs done, {len(todo)} to go (seeds={args.seeds})\n", flush=True)
    for i, (shape, seed) in enumerate(todo, 1):
        print(f"[{i}/{len(todo)}] digit {shape} {ARM} seed={seed} ...", flush=True)
        curve = train_eval(shape, seed, args.n_envs, args.max_steps, args.step_size)
        rec = {"shape": shape, "arm": ARM, "seed": seed, "mode": "vision", "chunk": C.CHUNK,
               "max_steps": args.max_steps, "step_size": args.step_size, "n_strokes": G.n_strokes(shape),
               "recogniser": "recognise_cnn_v2.pt",
               "torch_threads": __import__("torch").get_num_threads()}
        for key, nm in (("iou", "iou_curve"), ("peak", "peak_curve"), ("down", "pen_down_frac_curve"), ("snr", "snr_curve"),
                        ("p_target", "p_target_curve"), ("p_reject", "p_reject_curve")):
            rec[nm] = [round(c[key], 4) for c in curve]
        rec["legible_curve"] = [int(c["legible"]) for c in curve]
        with open(shard, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")
        print("        -> IoU " + " ".join(f"{c['iou']:.3f}" for c in curve)
              + " | P(target) " + " ".join(f"{c['p_target']:.2f}" for c in curve)
              + " | legible " + "".join(str(int(c["legible"])) for c in curve), flush=True)
    if not args.shard:
        aggregate()


def aggregate():
    d = load_done()
    if not d:
        print("no runs yet.")
        return
    print(f"\n=== Stage 6 digits, pen-free PPO, 200k steps, TRUE IoU + recognise_cnn_v2 (descriptive; n=runs, not a test) ===")
    print(f"{'digit':>5} {'strokes':>7} {'seed':>5} {'finalIoU':>9} {'peakIoU':>8} {'P(tgt)':>7} {'P(rej)':>7} {'legible':>8} {'pen-down':>9} {'SNR':>5}")
    rows = []
    for (s, k), r in sorted(d.items(), key=lambda kv: (DIGITS.index(kv[0][0]) if kv[0][0] in DIGITS else 9, kv[0][1])):
        rows.append((s, r))
        print(f"{s:>5} {r['n_strokes']:>7} {k:>5} {r['iou_curve'][-1]:>9.3f} {r['peak_curve'][-1]:>8.3f} {r['p_target_curve'][-1]:>7.2f} "
              f"{r['p_reject_curve'][-1]:>7.2f} {('yes' if r['legible_curve'][-1] else 'no'):>8} {r['pen_down_frac_curve'][-1]:>9.2f} {r['snr_curve'][-1]:>5.2f}")
    print("\ngroup means at 200k (runs):")
    for lab, ns in (("1-stroke (1,7)", 1), ("2-stroke (4,8)", 2)):
        g = [r for s, r in rows if r["n_strokes"] == ns]
        if g:
            f = lambda key, fn=np.mean: fn([x[key][-1] for x in g])
            print(f"  {lab}: n={len(g)}  IoU {f('iou_curve'):.3f}  P(target) {f('p_target_curve'):.2f}  legible {f('legible_curve'):.2f}  "
                  f"pen-down {f('pen_down_frac_curve'):.2f}  SNR {f('snr_curve'):.2f}")
    print("\nmean IoU curve (all runs) 0/50/100/150/200k: " + " ".join(f"{v:.3f}" for v in np.mean([r["iou_curve"] for _, r in rows], axis=0)))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs="+", default=[0, 100])
    ap.add_argument("--n-envs", type=int, default=8)
    ap.add_argument("--max-steps", type=int, default=240)
    ap.add_argument("--step-size", type=float, default=0.014)
    ap.add_argument("--shapes", nargs="+", choices=DIGITS)
    ap.add_argument("--shard", default="")
    ap.add_argument("--aggregate", action="store_true")
    a = ap.parse_args()
    aggregate() if a.aggregate else run(a)
