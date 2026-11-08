"""
H4 numbers for the deck, read straight from results/h4_experiment*.jsonl at build time.

Uses the SAME functions as rl/h4_experiment.py --aggregate and rl/h4_verdict.py
(load_done, _tstat, _tcrit), and the same pre-registered decision rule, so the deck can
never disagree with the scripts. Rebuild the deck after the sweep finishes and the final
table appears automatically.
"""
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, "rl"))

import h4_experiment as H  # noqa: E402

TOTAL_RUNS = 32


def summary():
    done = H.load_done()
    common = [(s, k) for s in H.SHAPES
              for k in sorted({kk for (ss, aa, kk) in done if ss == s})
              if all((s, a, k) in done for a in H.ARMS)]
    n = len(common)
    out = {"runs": len(done), "cells": n, "final": n >= 8 and len(done) >= TOTAL_RUNS,
           "means": {}, "rows": [], "gap": None, "crit": H._tcrit(n) if n > 1 else None}
    if n < 2:
        return out

    def col(arm, kind):
        return np.array([done[(s, arm, sd)][f"iou_{kind}"] for s, sd in common], float)

    for arm in H.ARMS:
        out["means"][arm] = {k: float(np.mean(col(arm, k))) for k in H.EVAL_KINDS}
    gm, gt = H._tstat(col("camera", "none") - col("fk", "none"))
    out["gap"] = (gm, gt)
    for k in H.EVAL_KINDS[1:]:
        drop = {a: float(np.mean(col(a, "none") - col(a, k))) for a in H.ARMS}
        did = (col("camera", k) - col("camera", "none")) - (col("fk", k) - col("fk", "none"))
        m, t = H._tstat(did)
        ctl = (col("true", k) - col("true", "none")) - (col("fk", k) - col("fk", "none"))
        cm, ct = H._tstat(ctl)
        crit = out["crit"]
        if n < 8:
            v = "interim — no verdict (n < 8)"
        elif drop["open_loop"] < 0.03:
            v = "uninformative — disturbance too weak"
        elif t >= crit:
            v = "camera recovers better than fk"
        elif t <= -crit:
            v = "camera recovers worse than fk"
        elif abs(t) >= 1.5:
            v = "no detectable difference (borderline)"
        else:
            v = "no detectable difference"
        out["rows"].append({"kind": k, "drop": drop, "did": m, "t": t,
                            "up": int((did > 0).sum()), "n": n, "verdict": v,
                            "ctl": cm, "ctl_t": ct})
    return out
