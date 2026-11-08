"""
RoboSketch-RL  |  Does the vision reward survive a distribution of cameras?
-------------------------------------------------
Proposal 4.1. The H2 result says a camera reward matches a ground-truth reward -
but it was measured with ONE fixed, very optimistic camera. That makes it a claim
about a sensor, not about cameras. This experiment asks whether it is a claim
about drawing.

THREE TRAINING ARMS (all `reward_mode="vision"`, all through perception.Camera
so the comparison is about randomisation and not about which code renders the
camera):

  fixed   - the old camera, every episode identical. The status quo.
  train   - camera parameters resampled each episode from `perception.TRAIN`.
  truth   - the ground-truth-reward control, which has no camera at all and so
            cannot be affected by any of this. It is the ceiling the vision arms
            are trying to reach, and it also tells us whether a bad heldout score
            means "the policy is camera-specific" or "the shape is just hard".

EVALUATED UNDER TWO CAMERAS, both scored on TRUE IoU (the drawing that actually
exists on the paper, not what any camera thinks):

  train camera    - drawn from the same distribution training used
  heldout camera  - `perception.HELDOUT`, disjoint from TRAIN on every axis:
                    dingier paper, fainter ink, more off-axis, coarser, blurrier,
                    dimmer, noisier, tighter threshold. Measured to recover
                    ~0.41-0.46 IoU of the true ink, against ~0.77 for a training
                    camera and 0.84 for the fixed one.

WHAT WOULD SUPPORT THE CLAIM. The `train` arm holding up on the HELDOUT camera
while the `fixed` arm falls away. That is the sim-to-real argument: a policy
trained on one sensor learned that sensor; a policy trained across sensors
learned the task.

WHAT WOULD REFUTE IT. `fixed` transferring just as well - which would mean the
perception model is not where the difficulty lives, and H2 was never as fragile
as feared. Also a publishable answer, and it is the one that would save the
project a lot of work.

Note the evaluation camera only ever affects the REWARD the agent would see; the
score reported is always true IoU, so a policy is never credited for a camera
that happens to flatter it.

  conda run -n robosketch python rl/dr_experiment.py --seeds 0 1 --timesteps 200000
  conda run -n robosketch python rl/dr_experiment.py --aggregate
"""
import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from draw_env import DrawEnv
from experiment import warn_config_drift

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results", "dr_experiment.jsonl")
SHAPES = ["line", "circle", "square", "triangle"]

# (arm name) -> (reward_mode, cam_split used during TRAINING)
ARMS = {
    "truth": ("truth", None),
    "fixed": ("vision", "fixed"),
    "train": ("vision", "train"),
}
ARM_ORDER = ["truth", "fixed", "train"]
EVAL_CAMS = ["fixed", "train", "heldout"]


def _sd(x):
    x = np.asarray(x, float)
    return float(x.std(ddof=1)) if x.size > 1 else 0.0


def load_done():
    import glob as _glob
    done = {}
    for path in sorted(_glob.glob(RESULTS.replace(".jsonl", "*.jsonl"))):
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    r = json.loads(line)
                    done[(r["shape"], r["arm"], r["seed"])] = r
    return done


def train_and_eval(shape, arm, seed, timesteps, n_envs, max_steps, step_size,
                   eval_eps):
    """Train one agent, then score it under each evaluation camera.

    Evaluation always reports TRUE IoU. The evaluation camera changes what the
    agent would be rewarded for, which is what we want to probe - not what it is
    credited with.
    """
    from stable_baselines3 import PPO
    from stable_baselines3.common.vec_env import DummyVecEnv, VecMonitor

    mode, cam = ARMS[arm]

    def mk(i):
        return lambda: DrawEnv(shape=shape, max_steps=max_steps,
                               step_size_m=step_size, reward_mode=mode,
                               cam_split=cam, seed=seed * 97 + i)

    venv = VecMonitor(DummyVecEnv([mk(i) for i in range(n_envs)]))
    model = PPO("CnnPolicy", venv, verbose=0, seed=seed,
                n_steps=512, batch_size=256, n_epochs=6, gamma=0.99,
                ent_coef=0.02, learning_rate=3e-4)
    model.learn(total_timesteps=timesteps, progress_bar=False)
    venv.close()

    out = {}
    for ecam in EVAL_CAMS:
        # a truth-reward agent has no camera in the loop; evaluating it under
        # different cameras would be meaningless, so it is scored once and the
        # same number is reported in every column (flagged in the aggregate).
        e_mode = "vision" if mode == "vision" else "truth"
        ious, peaks = [], []
        for ep in range(eval_eps):
            # eval_eps > 1 is only meaningful because the CAMERA is resampled
            # each episode - the drawing policy and start point are
            # deterministic, so with a fixed camera every episode is identical.
            env = DrawEnv(shape=shape, max_steps=max_steps, step_size_m=step_size,
                          reward_mode=e_mode, cam_split=ecam if mode == "vision" else None,
                          seed=50_000 + seed * 100 + ep)
            obs, _ = env.reset(seed=50_000 + seed * 100 + ep)
            done = False
            info = {}
            while not done:
                a, _ = model.predict(obs, deterministic=True)
                obs, r, term, trunc, info = env.step(a)
                done = term or trunc
            ious.append(info["iou"])            # TRUE IoU, always
            peaks.append(info["peak_iou"])
            env.close()
        out[ecam] = (float(np.mean(ious)), float(np.mean(peaks)), _sd(ious))
    return out


def run(args):
    os.makedirs(os.path.dirname(RESULTS), exist_ok=True)
    shapes = args.shapes or SHAPES
    shard = RESULTS if not args.shard else RESULTS.replace(".jsonl", f"_{args.shard}.jsonl")
    done = load_done()
    warn_config_drift(done, {"timesteps": args.timesteps, "max_steps": args.max_steps})
    combos = [(s, a, k) for k in args.seeds for s in shapes for a in ARM_ORDER]
    todo = [c for c in combos if c not in done]
    print(f"{len(done)} runs done, {len(todo)} to go "
          f"(seeds={args.seeds}, {args.timesteps} steps each)\n", flush=True)
    for i, (shape, arm, seed) in enumerate(todo, 1):
        print(f"[{i}/{len(todo)}] {shape:8s} {arm:6s} seed={seed} ...", flush=True)
        res = train_and_eval(shape, arm, seed, args.timesteps, args.n_envs,
                             args.max_steps, args.step_size, args.eval_eps)
        rec = {"shape": shape, "arm": arm, "seed": seed,
               "timesteps": args.timesteps, "max_steps": args.max_steps,
               "eval_eps": args.eval_eps}
        for ecam, (iou, peak, sd) in res.items():
            rec[f"iou_{ecam}"] = round(iou, 4)
            rec[f"peak_{ecam}"] = round(peak, 4)
            rec[f"sd_{ecam}"] = round(sd, 4)
        with open(shard, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")
        print("        -> " + "  ".join(
            f"{e}:{res[e][0]:.3f}" for e in EVAL_CAMS), flush=True)
    print(f"\ndone for shapes={shapes} seeds={args.seeds}.")
    if not args.shard:
        aggregate()


def aggregate():
    done = load_done()
    if not done:
        print("no results yet - run the sweep first.")
        return
    print("\n=== Domain randomisation: true IoU under each evaluation camera ===")
    print("rows = how the agent was TRAINED, columns = the camera it is TESTED on")
    print("(the `truth` arm has no camera in the loop, so its columns are identical)\n")
    hdr = "%-9s %-7s %12s %12s %12s %4s" % ("shape", "trained", "eval:fixed",
                                            "eval:train", "eval:heldout", "n")
    print(hdr); print("-" * len(hdr))
    for shape in SHAPES:
        for arm in ARM_ORDER:
            cells = [r for (s, a, k), r in done.items() if s == shape and a == arm]
            if not cells:
                continue
            vals = [[c[f"iou_{e}"] for c in cells] for e in EVAL_CAMS]
            print("%-9s %-7s %s %4d" % (
                shape, arm,
                " ".join("%7.3f+/-%.3f" % (np.mean(v), _sd(v)) for v in vals),
                len(cells)))
        print()

    # balanced over the (shape, seed) cells where every arm ran
    common = [(s, k) for s in SHAPES
              for k in sorted({kk for (ss, aa, kk) in done if ss == s})
              if all((s, a, k) in done for a in ARM_ORDER)]
    if not common:
        print("no (shape, seed) cell has all three arms yet.")
        return
    print("-" * len(hdr))
    print(f"balanced over {len(common)} (shape, seed) cells with all three arms")
    means = {}
    for arm in ARM_ORDER:
        v = [[done[(s, arm, k)][f"iou_{e}"] for s, k in common] for e in EVAL_CAMS]
        means[arm] = [np.mean(x) for x in v]
        print("%-9s %-7s %s" % ("", arm,
              " ".join("%7.3f+/-%.3f" % (np.mean(x), _sd(x)) for x in v)))

    print("\n=== the question this experiment exists to answer ===")
    fi, tr = means.get("fixed"), means.get("train")
    if not (fi and tr):
        return
    # index 2 = heldout, index 1 = train camera
    drop_fixed = fi[0] - fi[2]   # fixed arm trained on the FIXED camera (col 0)
    drop_train = tr[1] - tr[2]   # randomised arm trained on TRAIN cameras (col 1)
    print(f"  held-out camera, fixed-trained  : {fi[2]:.3f}  "
          f"(drop from its own training camera: {drop_fixed:+.3f})")
    print(f"  held-out camera, randomised     : {tr[2]:.3f}  "
          f"(drop from its own training camera: {drop_train:+.3f})")
    d = tr[2] - fi[2]
    _paired(done, common)
    if d > 0.02:
        print(f"\n  Randomisation is worth {d:+.3f} true IoU on a camera neither")
        print("  agent trained on -> the vision reward generalises ACROSS cameras,")
        print("  not just within the one it was tuned for.")
    elif d < -0.02:
        print(f"\n  Randomisation HURTS on the held-out camera ({d:+.3f}) - the")
        print("  wider distribution cost more in learning than it bought in")
        print("  robustness at this budget.")
    else:
        print(f"\n  No material difference on the held-out camera ({d:+.3f}).")
        print("  Perception realism is not where the difficulty lives, and H2 was")
        print("  less fragile than the review feared.")


def _paired(done, common):
    """train-arm minus fixed-arm, paired within (shape, seed), per eval camera."""
    print("\n  paired (train arm - fixed arm), same shape and seed:")
    for e in EVAL_CAMS:
        d = np.array([done[(s, "train", k)][f"iou_{e}"] - done[(s, "fixed", k)][f"iou_{e}"]
                      for s, k in common], float)
        if len(d) < 2:
            continue
        se = d.std(ddof=1) / np.sqrt(len(d))
        t = d.mean() / se if se > 0 else float("nan")
        print("    eval:%-8s mean %+.3f  sd %.3f  n=%d  %d/%d up  t=%+.2f"
              % (e, d.mean(), d.std(ddof=1), len(d), int((d > 0).sum()), len(d), t))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs="+", default=[0, 1])
    ap.add_argument("--shapes", nargs="+", choices=SHAPES)
    ap.add_argument("--shard", default="")
    ap.add_argument("--timesteps", type=int, default=200_000)
    ap.add_argument("--n-envs", type=int, default=8)
    ap.add_argument("--max-steps", type=int, default=240)
    ap.add_argument("--step-size", type=float, default=0.014)
    ap.add_argument("--eval-eps", type=int, default=12,
                    help="evaluation episodes; >1 is meaningful here because the "
                         "CAMERA is resampled each episode")
    ap.add_argument("--aggregate", action="store_true")
    a = ap.parse_args()
    aggregate() if a.aggregate else run(a)
