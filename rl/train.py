"""
RoboSketch-RL  |  Phase C - train an agent to draw
-------------------------------------------------
Trains a PPO agent on DrawEnv to reproduce a target shape, then evaluates it
and saves the learned drawing.

This is the first RL algorithm of the study (PPO); SAC comes next for the
comparison (research questions 3-4). The reward here is the ground-truth
BASELINE (H2); the vision reward is a later experiment.

Examples:
  conda run -n robosketch python rl/train.py --shape line --timesteps 100000
  conda run -n robosketch python rl/train.py --shape square --timesteps 300000 --n-envs 8
"""
import argparse
import os
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from draw_env import DrawEnv
import metrics as M

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "output")
MODELS = os.path.join(ROOT, "models")


def make_env(shape, use_arm, max_steps, step_size, seed, reward_mode="truth",
             time_in_obs=False):
    def _f():
        return DrawEnv(shape=shape, use_arm=use_arm, max_steps=max_steps,
                       step_size_m=step_size, reward_mode=reward_mode,
                       time_in_obs=time_in_obs, seed=seed)
    return _f


def evaluate(model, shape, use_arm, max_steps, step_size, reward_mode="truth",
             episodes=5, time_in_obs=False):
    """Run the trained policy deterministically; return mean metrics + a render.

    Evaluation always uses info['iou'] = TRUE IoU, so a vision-trained agent is
    judged by real drawing quality, not by its own perception. `snr` and
    `path_ratio` (proposal 4.5) are reported alongside it: IoU is blind to a
    fragmented, zig-zagging path, and these are not."""
    env = DrawEnv(shape=shape, use_arm=use_arm, max_steps=max_steps,
                  step_size_m=step_size, reward_mode=reward_mode,
                  time_in_obs=time_in_obs, seed=999)
    ious, covs, snrs, prs, gaps = [], [], [], [], []
    render = None
    for ep in range(episodes):
        obs, _ = env.reset(seed=1000 + ep)
        done = False
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, r, term, trunc, info = env.step(action)
            done = term or trunc
        ious.append(info["iou"])
        covs.append(info["coverage"])
        snrs.append(info["snr"])
        prs.append(info["path_ratio"])
        gaps.append(info["iou_gap"])
        if ep == 0:
            render = env.render()
    env.close()
    extra = {"snr": float(np.mean(snrs)), "path_ratio": float(np.mean(prs)),
             "iou_gap": float(np.mean(gaps))}
    return float(np.mean(ious)), float(np.mean(covs)), render, extra


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shape", default="line")
    ap.add_argument("--timesteps", type=int, default=100_000)
    ap.add_argument("--n-envs", type=int, default=8)
    ap.add_argument("--max-steps", type=int, default=240)
    ap.add_argument("--step-size", type=float, default=0.014)
    ap.add_argument("--ent-coef", type=float, default=0.02)
    ap.add_argument("--use-arm", action="store_true")
    ap.add_argument("--reward-mode", choices=["truth", "vision", "vision_real"], default="truth",
                    help="truth = ground-truth (baseline); vision = fast camera proxy (H2); "
                         "vision_real = actual PyBullet camera render + OpenCV per step")
    ap.add_argument("--time-obs", action="store_true",
                    help="O1: add a remaining-time channel to the observation "
                         "(fixes the partial observability of the step limit)")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    from stable_baselines3 import PPO
    from stable_baselines3.common.vec_env import DummyVecEnv, VecMonitor

    os.makedirs(OUT, exist_ok=True)
    os.makedirs(MODELS, exist_ok=True)

    n = 1 if args.use_arm else args.n_envs      # arm backend: single client -> 1 env
    venv = DummyVecEnv([make_env(args.shape, args.use_arm, args.max_steps,
                                 args.step_size, args.seed + i, args.reward_mode,
                                 args.time_obs)
                        for i in range(n)])
    venv = VecMonitor(venv)

    model = PPO("CnnPolicy", venv, verbose=1, seed=args.seed,
                n_steps=512, batch_size=256, n_epochs=6, gamma=0.99,
                ent_coef=args.ent_coef, learning_rate=3e-4)

    tag = f"{args.shape}_{'arm' if args.use_arm else 'kin'}"
    if args.reward_mode != "truth":
        tag += f"_{args.reward_mode}"
    if args.time_obs:
        tag += "_t"
    print(f"\n=== BEFORE training ({args.reward_mode} reward) ===")
    i0, c0, r0, e0 = evaluate(model, args.shape, args.use_arm, args.max_steps,
                              args.step_size, args.reward_mode,
                              time_in_obs=args.time_obs)
    print(f"  untrained: IoU={i0:.3f} coverage={c0:.3f} "
          f"snr={e0['snr']:.2f} path_ratio={e0['path_ratio']:.2f}")
    cv2.imwrite(os.path.join(OUT, f"trained_{tag}_before.png"), r0)

    model.learn(total_timesteps=args.timesteps, progress_bar=False)

    print(f"\n=== AFTER training ===")
    i1, c1, r1, e1 = evaluate(model, args.shape, args.use_arm, args.max_steps,
                              args.step_size, args.reward_mode,
                              time_in_obs=args.time_obs)
    print(f"  trained:   IoU={i1:.3f} coverage={c1:.3f} "
          f"snr={e1['snr']:.2f} path_ratio={e1['path_ratio']:.2f} "
          f"iou_gap={e1['iou_gap']:+.3f}")
    cv2.imwrite(os.path.join(OUT, f"trained_{tag}_after.png"), r1)

    model.save(os.path.join(MODELS, f"ppo_{tag}"))
    print(f"\nIoU {i0:.3f} -> {i1:.3f}   coverage {c0:.3f} -> {c1:.3f}")
    print(f"model saved: models/ppo_{tag}.zip")
    print(f"renders: output/trained_{tag}_before.png / _after.png")


if __name__ == "__main__":
    main()
