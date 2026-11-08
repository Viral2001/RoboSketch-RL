"""
H4 verdict table - applies the pre-registered decision rule mechanically.

Reads the same results as `h4_experiment.py --aggregate`, recomputes the PRIMARY paired
difference-in-differences independently, cross-checks it against the drop-from-clean numbers
(AGENTS.md section 6 rule 2), and prints a markdown table with the verdict word per
disturbance. The rule is the one in docs/H4_FINISH.md step 4 (first match wins):
  open-loop loses < 0.03     -> uninformative (disturbance too weak)
  t >= crit                  -> camera recovers better
  t <= -crit                 -> camera recovers worse
  1.5 <= |t| < crit          -> no detectable difference, borderline (ask user re: more seeds)
  otherwise                  -> no detectable difference

Paste the printed table; do not retype it.

    conda run -n robosketch python rl/h4_verdict.py
"""
import sys

import numpy as np

import h4_experiment as H


def main():
    done = H.load_done()
    common = [(s, k) for s in H.SHAPES
              for k in sorted({kk for (ss, aa, kk) in done if ss == s})
              if all((s, a, k) in done for a in H.ARMS)]
    n = len(common)
    if n < 8:
        print(f"only {n} balanced (shape, seed) cells - need 8. NO VERDICT. Stop.")
        return 1

    def col(arm, kind):
        return np.array([done[(s, arm, sd)][f"iou_{kind}"] for s, sd in common], float)

    gap_m, gap_t = H._tstat(col("camera", "none") - col("fk", "none"))
    crit = H._tcrit(n)
    print(f"n = {n} (shape, seed) cells; two-sided 5% crit t = {crit:.3f}")
    print(f"clean gap camera - fk (no disturbance): {gap_m:+.3f}, t = {gap_t:+.2f} "
          "- NOT recovery\n")
    print("drop = clean IoU - disturbed IoU (positive = got worse); "
          "diff-in-diff = fk drop - camera drop (positive = camera degrades less)\n")
    print("| disturbance | camera drop | fk drop | open-loop drop | diff-in-diff | up | t | verdict |")
    print("|---|---|---|---|---|---|---|---|")
    ok = True
    borderline = False
    for k in H.EVAL_KINDS[1:]:
        drop = {a: float(np.mean(col(a, "none") - col(a, k))) for a in H.ARMS}
        did = (col("camera", k) - col("camera", "none")) - (col("fk", k) - col("fk", "none"))
        m, t = H._tstat(did)
        if abs(m - (drop["fk"] - drop["camera"])) > 1e-9:
            ok = False
        if drop["open_loop"] < 0.03:
            v = "uninformative - disturbance too weak to test recovery"
        elif t >= crit:
            v = "camera recovers better than fk"
        elif t <= -crit:
            v = "camera recovers worse than fk"
        elif abs(t) >= 1.5:
            v = "no detectable difference (borderline)"
            borderline = True
        else:
            v = "no detectable difference"
        print(f"| {k} | {drop['camera']:+.3f} | {drop['fk']:+.3f} | {drop['open_loop']:+.3f} "
              f"| {m:+.3f} | {int((did > 0).sum())}/{n} | {t:+.2f} | {v} |")
    print()
    print("cross-check diff-in-diff == fk drop - camera drop:", "PASS" if ok else "FAIL - STOP, tell the user")
    if borderline:
        print("BORDERLINE present: after writing the result, ASK the user whether to add "
              "seeds 200 and 300. Do not launch them.")
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
