"""
RoboSketch-RL  |  What do the randomised cameras actually do?
-------------------------------------------------
The camera distributions in `perception.py` are only worth anything if their
behaviour is known rather than assumed. This script measures it, and is kept in
the repo so the numbers quoted in the log can be regenerated instead of trusted.

It answers four questions:

  1. HOW MUCH INK DOES EACH CAMERA RECOVER, per shape? Measured against a
     PERFECT drawing (the target itself), which is the upper bound - a real
     agent's canvas can only do worse. Reported per shape because the shapes
     are not equally hard: the line is a single thin stroke and suffers most.

  2. IS EVERY AXIS DOING ANYTHING? A single-axis ablation: hold the fixed
     camera and move one parameter at a time to its train / held-out midpoint.
     An axis that does not move the number is decoration, and claiming an
     "8-axis camera distribution" built on inert axes is not defensible.

  3. ARE TRAIN AND HELDOUT DISJOINT? Asserted in three places in the codebase,
     so it is checked rather than believed.

  4. WHAT DOES IT COST? `perceive()` runs every training step.

  conda run -n robosketch python rl/perception_calibration.py
"""
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import metrics as M
import perception as P
import targets as T

SHAPES = ["line", "circle", "square", "triangle"]
RES = 128
N = 40


def _target(shape):
    import cv2
    t = cv2.resize(T.make(shape, res=512), (RES, RES), interpolation=cv2.INTER_AREA)
    return (t > 127).astype(np.uint8) * 255


def recovery():
    print("=== 1. ink recovered from a PERFECT drawing (IoU of perceive(target) vs target) ===")
    print("    the upper bound: a real canvas can only do worse\n")
    print("%-9s %22s %22s %22s" % ("shape", "fixed", "train", "heldout"))
    print("-" * 78)
    worst = {}
    for shape in SHAPES:
        tgt = _target(shape)
        cells = []
        for split in ("fixed", "train", "heldout"):
            vals = []
            for i in range(N):
                rng = np.random.default_rng(2000 + i)
                cam = P.Camera(RES, P.sample_params(rng, split), rng)
                vals.append(M.iou(cam.perceive(tgt), tgt))
            cells.append((np.mean(vals), np.min(vals), np.max(vals)))
            worst.setdefault(split, []).append(np.mean(vals))
        print("%-9s %s" % (shape, " ".join("%6.3f [%.3f,%.3f]" % c for c in cells)))
    print("-" * 78)
    print("%-9s %s" % ("mean", " ".join("%6.3f          " % np.mean(worst[s])
                                        for s in ("fixed", "train", "heldout"))))
    return worst


def ablation():
    print("\n=== 2. single-axis ablation: which parameters actually matter? ===")
    print("    start from the fixed camera, move ONE axis to the midpoint of each range\n")
    tgt = _target("square")
    base = P.sample_params(np.random.default_rng(0), "fixed")
    rng = np.random.default_rng(0)
    ref = M.iou(P.Camera(RES, dict(base), rng).perceive(tgt), tgt)
    print("    fixed camera reference IoU = %.3f\n" % ref)
    print("%-14s %12s %12s" % ("axis", "at train mid", "at heldout mid"))
    print("-" * 40)
    for axis in sorted(P.TRAIN):
        row = []
        for split, ranges in (("train", P.TRAIN), ("heldout", P.HELDOUT)):
            lo, hi = ranges[axis]
            vals = []
            for i in range(N):
                r = np.random.default_rng(3000 + i)
                p = dict(base)
                p[axis] = 0.5 * (lo + hi)
                vals.append(M.iou(P.Camera(RES, p, r).perceive(tgt), tgt))
            row.append(np.mean(vals))
        flag = "   <- inert" if all(abs(v - ref) < 0.01 for v in row) else ""
        print("%-14s %12.3f %12.3f%s" % (axis, row[0], row[1], flag))

    # everything together, and everything-except-the-warp, to see how much of
    # the degradation one axis is responsible for
    for label, drop in (("all heldout midpoints", None), ("...but warp_px = 0", "warp_px")):
        vals = []
        for i in range(N):
            r = np.random.default_rng(4000 + i)
            p = {k: 0.5 * (lo + hi) for k, (lo, hi) in P.HELDOUT.items()}
            if drop:
                p[drop] = 0.0
            vals.append(M.iou(P.Camera(RES, p, r).perceive(tgt), tgt))
        print("%-28s %.3f" % (label, np.mean(vals)))


def disjoint():
    print("\n=== 3. are TRAIN and HELDOUT disjoint on every axis? ===")
    bad = 0
    for axis in sorted(P.TRAIN):
        a, b = P.TRAIN[axis], P.HELDOUT[axis]
        ov = not (a[1] < b[0] or b[1] < a[0])
        bad += ov
        print("  %-14s train%-14s heldout%-14s %s"
              % (axis, str(a), str(b), "*** OVERLAP ***" if ov else "disjoint"))
    print("  => %s" % ("ALL DISJOINT" if not bad else f"{bad} AXIS/AXES OVERLAP"))


def cost():
    print("\n=== 4. cost per perceive() call (runs every training step) ===")
    tgt = _target("square")
    for split in ("fixed", "train", "heldout"):
        rng = np.random.default_rng(0)
        cam = P.Camera(RES, P.sample_params(rng, split), rng)
        cam.perceive(tgt)
        t0 = time.perf_counter()
        for _ in range(300):
            cam.perceive(tgt)
        print("  %-8s %5.0f us" % (split, (time.perf_counter() - t0) / 300 * 1e6))


if __name__ == "__main__":
    recovery()
    ablation()
    disjoint()
    cost()
