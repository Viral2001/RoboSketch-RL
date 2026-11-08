"""
RoboSketch-RL  |  Does the overshoot bias the H2 comparison?
-------------------------------------------------
THE WORRY. Every IoU the H2 result reports is measured at the END of the
episode. `rl/overrun.py` showed agents finish tracing in the first ~15% of the
episode and then overshoot, and on the four single-run 400k models the CAMERA
arm lost roughly twice as much to that overshoot as the ground-truth arm
(0.085 vs 0.043). If that holds at n=3, then part of the 0.028 gap the H2 table
reports is not "ground truth teaches better" but "we stopped the clock at a
moment that flatters ground truth".

Direction matters here. The project's claim is that a camera reward MATCHES a
ground-truth reward. A bias in this direction would make that claim STRONGER -
which is exactly why it has to be measured rather than assumed.

THE TEST. Re-run the H2 sweep recording `peak_iou` alongside `iou`, then compare
the truth-vs-vision gap two ways, paired within (shape, seed):

    gap_final = vision.iou      - truth.iou        (what H2 reports today)
    gap_peak  = vision.peak_iou - truth.peak_iou   (before either arm overshot)

  gap_peak ~ gap_final  -> the overshoot is symmetric; H2 stands as reported.
  |gap_peak| < |gap_final| -> the overshoot was inflating the gap against the
                              camera, and H2's conclusion is if anything
                              understated.
  |gap_peak| > |gap_final| -> the overshoot was masking a real gap.

Paired throughout: both arms run the same seeds, and a pooled std would carry
the shape-to-shape spread into a threshold meant to describe run-to-run noise.

  conda run -n robosketch python rl/h2_peak_analysis.py
"""
import argparse
import glob
import json
import os

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHAPES = ["line", "circle", "square", "triangle"]


def load(pattern):
    d = {}
    for path in sorted(glob.glob(os.path.join(ROOT, "results", pattern))):
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if line:
                r = json.loads(line)
                d[(r["shape"], r["mode"], r["seed"])] = r
    return d


def _paired(deltas, lo_is_better=False):
    a = np.array(deltas, float)
    n = len(a)
    if n < 2:
        return dict(n=n, mean=float(a.mean()) if n else float("nan"),
                    sd=float("nan"), t=float("nan"), up=int((a > 0).sum()))
    se = a.std(ddof=1) / np.sqrt(n)
    return dict(n=n, mean=float(a.mean()), sd=float(a.std(ddof=1)),
                t=float(a.mean() / se) if se > 0 else float("nan"),
                up=int((a > 0).sum()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pattern", default="h2_peak*.jsonl")
    a = ap.parse_args()

    d = load(a.pattern)
    if not d:
        print("no results yet for pattern", a.pattern)
        return
    cells = [(s, k) for s in SHAPES
             for k in sorted({sd for (sh, m, sd) in d if sh == s})
             if (s, "truth", k) in d and (s, "vision", k) in d]
    if not cells:
        print("no (shape, seed) cell has both arms yet.")
        return

    print("=== per-cell: truth vs vision, scored at the end and at the peak ===")
    print("%-9s %5s %8s %8s %9s %8s %8s %9s" %
          ("shape", "seed", "T final", "V final", "gap fin", "T peak", "V peak", "gap peak"))
    print("-" * 74)
    gf, gp, ovt, ovv = [], [], [], []
    for s, k in cells:
        t, v = d[(s, "truth", k)], d[(s, "vision", k)]
        if "peak_iou" not in t or "peak_iou" not in v:
            continue
        f = v["iou"] - t["iou"]
        p = v["peak_iou"] - t["peak_iou"]
        gf.append(f); gp.append(p)
        ovt.append(t["overshoot"]); ovv.append(v["overshoot"])
        print("%-9s %5d %8.3f %8.3f %+9.3f %8.3f %8.3f %+9.3f" %
              (s, k, t["iou"], v["iou"], f, t["peak_iou"], v["peak_iou"], p))
    if not gf:
        print("\nrecords carry no peak_iou - this analysis needs the re-run sweep.")
        return

    F, P = _paired(gf), _paired(gp)
    print("-" * 74)
    print("\n=== the H2 gap, paired within (shape, seed) ===")
    print("  scored at the END  (what H2 reports): mean %+.4f  sd %.4f  t=%+.2f  "
          "vision ahead %d/%d" % (F["mean"], F["sd"], F["t"], F["up"], F["n"]))
    print("  scored at the PEAK (before overshoot): mean %+.4f  sd %.4f  t=%+.2f  "
          "vision ahead %d/%d" % (P["mean"], P["sd"], P["t"], P["up"], P["n"]))

    print("\n=== how much each arm loses to its own overshoot ===")
    print("  ground truth : %.4f" % np.mean(ovt))
    print("  camera       : %.4f" % np.mean(ovv))
    dov = _paired([b - a_ for a_, b in zip(ovt, ovv)])
    print("  paired difference (camera - truth): %+.4f  t=%+.2f  (%d/%d cells "
          "where the camera loses more)" % (dov["mean"], dov["t"], dov["up"], dov["n"]))

    print("\n=== verdict ===")
    shrink = abs(F["mean"]) - abs(P["mean"])
    # Does the choice of measurement point change the H2 conclusion? Only if the
    # gap moves by more than the run-to-run noise of the gap itself.
    noise = F["sd"] / np.sqrt(max(1, F["n"]))
    if abs(dov["t"]) < 1.5:
        print("  The two arms lose statistically similar amounts to the overshoot")
        print("  (paired t=%+.2f). The n=1 finding that the camera arm loses twice"
              % dov["t"])
        print("  as much does NOT replicate at this sample size.")
    else:
        who = "camera" if dov["mean"] > 0 else "ground truth"
        print("  The %s arm loses significantly more to the overshoot "
              "(paired t=%+.2f)." % (who, dov["t"]))
    if abs(shrink) < noise:
        print("  Measuring at the peak instead of the end moves the H2 gap by "
              "%+.4f," % -shrink)
        print("  which is inside the gap's own standard error (%.4f)." % noise)
        print("  => The overshoot does NOT materially bias the H2 comparison.")
        print("     H2 stands as reported.")
    elif shrink > 0:
        print("  The gap SHRINKS by %.4f when scored at the peak (%.4f -> %.4f)."
              % (shrink, abs(F["mean"]), abs(P["mean"])))
        print("  => Part of the reported H2 gap is an artifact of when we stop")
        print("     measuring. The 'camera matches ground truth' claim is")
        print("     understated by the current protocol.")
    else:
        print("  The gap GROWS by %.4f when scored at the peak (%.4f -> %.4f)."
              % (-shrink, abs(F["mean"]), abs(P["mean"])))
        print("  => The overshoot was masking a real difference between the arms.")

    # cross-check against the originally published sweep
    old = load("h2_seeds.jsonl")
    pairs = [(d[(s, m, k)]["iou"], old[(s, m, k)]["iou"])
             for s in SHAPES for m in ("truth", "vision")
             for k in sorted({sd for (sh, mm, sd) in d if sh == s})
             if (s, m, k) in d and (s, m, k) in old]
    if pairs:
        new_v = np.array([p[0] for p in pairs])
        old_v = np.array([p[1] for p in pairs])
        threads = sorted({r.get("torch_threads") for r in d.values()})
        print("\n=== against the published sweep (%d cells) ===" % len(pairs))
        print("  mean |difference| = %.4f   max = %.4f"
              % (np.abs(new_v - old_v).mean(), np.abs(new_v - old_v).max()))
        print("  new sweep torch_threads = %s; the published sweep ran on the"
              % (threads if threads != [None] else "unrecorded"))
        print("  default (2). A seeded run is NOT reproducible across thread")
        print("  counts - measured, the same cell gives IoU 0.175 on 2 threads")
        print("  and 0.195 on 1 - so a difference here is expected and is not")
        print("  evidence that anything in the pipeline moved.")
        print("  The peak-vs-final test above is internal to THIS sweep, so it")
        print("  is unaffected either way.")


if __name__ == "__main__":
    main()
