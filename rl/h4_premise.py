"""H4 premise check: how far does each observation source drift from the real
paper when a disturbance fires?  Random actions, no training - this measures the
INFORMATION in each channel, not any policy's use of it.

Compared at canvas resolution (128x128), i.e. the belief canvas `_belief` and
the camera image `_seen()` against the true ink `canvas`, so the 64x64
observation downsample is not part of the measurement.
"""
import os, sys, numpy as np
sys.path.insert(0, r"D:\RoboSketch-RL\rl")
from draw_env import DrawEnv

N, SEED0 = 8, 900

def drift(obs_source, kind):
    d = []
    for ep in range(N):
        kw = dict(shape="circle", max_steps=60, disturbance=kind,
                  seed=SEED0 + ep, obs_source=obs_source)
        if obs_source == "camera":
            kw.update(cam_split="fixed", reward_mode="vision")
        env = DrawEnv(**kw)
        env.reset(seed=SEED0 + ep)
        rng = np.random.default_rng(SEED0 + ep)
        done = False
        while not done:
            a = rng.uniform(-1, 1, 3).astype(np.float32); a[2] = 1.0
            _, _, term, trunc, _ = env.step(a)
            done = term or trunc
        seen = (env._belief if obs_source == "fk" else env._seen()).astype(float)
        truth = env.canvas.astype(float)
        err = float(np.abs(seen - truth).sum())
        # Mean-per-pixel understates a CONCENTRATED error: a missing stroke is a
        # handful of pixels out of 128x128. The honest denominator is the ink
        # actually on the paper, so report the error as a share of that.
        d.append((err / truth.size, err / max(truth.sum(), 1.0)))
        env.close()
    a = np.asarray(d, float)
    return a.mean(0), a.std(0, ddof=1)

print("mean |observed - true paper| per pixel (0-255), n=%d episodes, random actions" % N)
print("%-14s | %-21s | %-21s" % ("", "fk belief", "camera"))
print("%-14s | %9s %11s | %9s %11s" % ("disturbance", "per px", "% of ink", "per px", "% of ink"))
for kind in ("none", "slip", "paper_shift", "ink_failure", "mixed"):
    (fm, fs), (cm, cs) = drift("fk", kind), drift("camera", kind)
    print("%-14s | %4.2f+-%4.2f %6.1f+-%4.1f | %4.2f+-%4.2f %6.1f+-%4.1f" % (
        kind, fm[0], fs[0], 100 * fm[1], 100 * fs[1],
        cm[0], cs[0], 100 * cm[1], 100 * cs[1]))
