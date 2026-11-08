"""
RoboSketch-RL  |  The overrun effect - the agent cannot stop
-------------------------------------------------
Found while interpreting `path_ratio`, the metric added for proposal 4.5.
During training the pen was travelling 6-24x the length of the outline it was
tracing. Asking where that travel goes turned up something larger than the
metric itself.

THE MECHANISM. An episode runs for a fixed `max_steps` (240). `pen_always_down`
is True and there is no terminate action, so once the agent has drawn the shape
it cannot stop, cannot lift the pen, and cannot end the episode. It has to keep
moving with the pen down for the remaining steps - and every one of those steps
inks.

Standing still is *technically* available (dx = dy = 0 draws a dot on the spot),
but it is a single point in a continuous action space that a Gaussian policy
with an entropy bonus (ent_coef=0.02) will not settle on exactly.

THE MEASUREMENT. Record IoU at every step of a deterministic evaluation, find
the peak, and compare it to the IoU the episode is finally scored on.

WHY IT MATTERS. Every number this project has reported is the FINAL IoU - which
is measured after the agent has spent most of the episode damaging its own best
drawing. The gap is not small: it is larger than the entire truth-vs-vision
difference that H2 set out to measure.

  conda run -n robosketch python rl/overrun.py
"""
import argparse
import os
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from draw_env import DrawEnv
from h3_exploitation import PALETTE, _Axes, _legend

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "output")
SHAPES = ["line", "circle", "square", "triangle"]
MODELS = [("truth", "ppo_%s_kin.zip"), ("vision", "ppo_%s_kin_vision.zip")]


def trace(model, shape, max_steps, step_size):
    """Per-step IoU, ink count and pen travel for one deterministic episode."""
    env = DrawEnv(shape=shape, max_steps=max_steps, step_size_m=step_size, seed=999)
    obs, _ = env.reset(seed=1000)
    ious, inks, paths, done = [], [], [], False
    while not done:
        a, _ = model.predict(obs, deterministic=True)
        obs, r, term, trunc, info = env.step(a)
        ious.append(info["iou"])
        inks.append(int((env.canvas > 127).sum()))
        paths.append(info["path_len_px"])
        done = term or trunc
    env.close()
    return np.array(ious), np.array(inks), np.array(paths)


def describe(ious, inks):
    """peak step, the step the drawing stops changing, and the step the canvas
    stops gaining ink at all."""
    peak_k = int(np.argmax(ious)) + 1
    ch = np.abs(np.diff(ious)) > 1e-6
    settle_k = (int(np.nonzero(ch)[0].max()) + 2) if ch.any() else peak_k
    dink = np.diff(inks) > 0
    frozen_k = (int(np.nonzero(dink)[0].max()) + 2) if dink.any() else peak_k
    return peak_k, settle_k, frozen_k


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-steps", type=int, default=240)
    ap.add_argument("--step-size", type=float, default=0.014)
    a = ap.parse_args()

    from stable_baselines3 import PPO

    curves, rows = {}, []
    for mode, pat in MODELS:
        for shape in SHAPES:
            f = os.path.join(ROOT, "models", pat % shape)
            if not os.path.exists(f):
                continue
            ious, inks, paths = trace(PPO.load(f, device="cpu"), shape,
                                      a.max_steps, a.step_size)
            curves[(mode, shape)] = ious
            peak_k, settle_k, frozen_k = describe(ious, inks)
            rows.append((shape, mode, float(ious[-1]), float(ious.max()),
                         float(ious.max() - ious[-1]), peak_k, settle_k, frozen_k,
                         len(ious)))

    hdr = ("%-9s %-7s %8s %8s %7s %7s %8s %9s %8s" %
           ("shape", "reward", "final", "peak", "lost", "peak@", "settle@",
            "frozen@", "idle"))
    print(hdr)
    print("-" * len(hdr))
    for shape, mode, fin, peak, lost, pk, st, fr, n_steps in rows:
        # denominator is the episode ACTUALLY run, not the configured max_steps:
        # DrawEnv can end early (done_iou, or a stop action), and dividing by the
        # cap would understate the idle share of a short episode.
        idle = 100.0 * (n_steps - fr) / max(1, n_steps)
        print("%-9s %-7s %8.3f %8.3f %7.3f %7d %7d %9d %7.0f%%" %
              (shape, mode, fin, peak, lost, pk, st, fr, idle))
    print("-" * len(hdr))
    lost = [r[4] for r in rows]
    idles = [100.0 * (r[8] - r[7]) / max(1, r[8]) for r in rows]
    print("mean IoU lost to the post-completion overshoot: %.3f" % np.mean(lost))
    print("   for scale, the entire H2 truth-vs-vision gap is 0.028")
    print("mean peak reached at step %.0f of %.0f; canvas frozen from step %.0f"
          % (np.mean([r[5] for r in rows]), np.mean([r[8] for r in rows]),
             np.mean([r[7] for r in rows])))
    print("mean share of the episode spent with a FROZEN canvas: %.0f%%" % np.mean(idles))
    print("""
READ IT CAREFULLY. The agents do not damage their drawing throughout the
episode - the IoU curves are flat for most of it. What happens is:
  1. the shape is traced within the first ~10-17% of the episode,
  2. a SHORT overshoot right after completion costs the IoU above,
  3. the canvas then freezes - no new ink for the rest of the episode.
So the loss is a completion problem (no terminate action, no pen lift), and
the remaining ~80% of every episode is wasted sample budget, not damage.

NOTE: evaluation is fully deterministic (deterministic start + deterministic
policy), so repeating the episode adds nothing - one run per cell IS the
answer, not a sample of one.""")

    _figure(curves, rows, a.max_steps)


def _figure(curves, rows, max_steps):
    if not curves:
        return
    W, H = 1320, 560
    img = np.full((H, W, 3), 255, np.uint8)
    F = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(img, "Agents finish in the first ~15% of the episode, overshoot, then idle",
                (40, 34), F, 0.66, (0, 0, 0), 2, cv2.LINE_AA)

    imax = max(c.max() for c in curves.values())
    panels = [("truth", 100, "ground-truth reward"), ("vision", 760, "camera reward")]
    for mode, x0, title in panels:
        ax = _Axes(img, x0, 470, 500, 320, (0, max_steps), (0, imax * 1.15),
                   title + "\n ", "step within the episode", "true IoU")
        leg = []
        for i, shape in enumerate(SHAPES):
            c = curves.get((mode, shape))
            if c is None:
                continue
            col = PALETTE[i % len(PALETTE)]
            xs = np.arange(1, len(c) + 1)
            ax.line(xs, c, col, 2)
            k = int(np.argmax(c >= 0.99 * c.max()))
            # peak marked with a filled dot, the scored final value with a ring
            cv2.circle(img, (ax.px(k + 1), ax.py(c[k])), 4, col, -1, cv2.LINE_AA)
            cv2.circle(img, (ax.px(len(c)), ax.py(c[-1])), 4, col, 1, cv2.LINE_AA)
            leg.append((shape, col, False))
        # legend goes low-right, where every curve has already plateaued
        _legend(img, x0 + 330, 380, leg)
    cv2.putText(img, "filled dot = peak IoU      hollow ring = the IoU actually reported "
                     "     flat tail = canvas frozen, budget wasted",
                (100, 520), F, 0.46, (110, 110, 110), 1, cv2.LINE_AA)
    out = os.path.join(OUT, "results_overrun.png")
    cv2.imwrite(out, img)
    print("\nfigure: output/results_overrun.png")


if __name__ == "__main__":
    main()
