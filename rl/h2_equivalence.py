"""
RoboSketch-RL | H2 equivalence test (TOST) - truth reward vs camera (vision) reward
-------------------------------------------------
Reads a H2-format results family (rows with shape / mode / seed / iou / peak_iou) and tests
whether the camera reward is EQUIVALENT to the truth reward within +/- MARGIN IoU.
Paired by (shape, seed) cell; d = truth - vision (>0 = truth better). Pre-registered in
docs/RESEARCH_LOG.md "H2 re-run with spaced seeds launched": margin 0.05, alpha 0.05.

  conda run -n robosketch --no-capture-output python rl/h2_equivalence.py                 # results/h2_spaced*.jsonl
  conda run -n robosketch --no-capture-output python rl/h2_equivalence.py --stem h2_seeds # any other family
"""
import argparse
import glob
import json
import os

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(stem):
    rows = {}
    for p in sorted(glob.glob(os.path.join(ROOT, "results", stem + "*.jsonl"))):
        with open(p, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    r = json.loads(line)
                    rows[(r["shape"], r["mode"], r["seed"])] = r
    return rows


def _betacf(a, b, x):
    """Continued fraction for the incomplete beta function (Numerical Recipes)."""
    tiny = 1e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    d = 1.0 / (d if abs(d) > tiny else tiny)
    h = d
    for m in range(1, 300):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d; d = 1.0 / (d if abs(d) > tiny else tiny)
        c = 1.0 + aa / c; c = c if abs(c) > tiny else tiny
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d; d = 1.0 / (d if abs(d) > tiny else tiny)
        c = 1.0 + aa / c; c = c if abs(c) > tiny else tiny
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < 1e-14:
            break
    return h


def t_cdf(t, df):
    """Student-t CDF without scipy (the env has none)."""
    import math
    if t == 0:
        return 0.5
    x = df / (df + t * t)
    lbeta = math.lgamma(df / 2) + math.lgamma(0.5) - math.lgamma(df / 2 + 0.5)
    front = math.exp(df / 2 * math.log(x) + 0.5 * math.log(1 - x) - lbeta)
    a, b = df / 2, 0.5
    ib = front * _betacf(a, b, x) / a if x < (a + 1) / (a + b + 2) else 1 - front * _betacf(b, a, 1 - x) / b
    return 1 - 0.5 * ib if t > 0 else 0.5 * ib


def t_ppf(p, df):
    lo, hi = -50.0, 50.0
    for _ in range(200):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if t_cdf(mid, df) < p else (lo, mid)
    return (lo + hi) / 2


class stats:                                       # tiny stand-in for the scipy calls used below
    class t:
        cdf = staticmethod(t_cdf)
        ppf = staticmethod(t_ppf)


def tost(d, margin, alpha=0.05):
    """Paired TOST on differences d. Returns dict with mean, sd, se, df, t's, p's, 90% CI."""
    d = np.asarray(d, float)
    n = len(d)
    m, sd = float(d.mean()), float(d.std(ddof=1))
    se = sd / np.sqrt(n)
    df = n - 1
    t_lo = (m + margin) / se          # H0: d <= -margin
    t_hi = (m - margin) / se          # H0: d >= +margin
    p_lo = float(1 - stats.t.cdf(t_lo, df))
    p_hi = float(stats.t.cdf(t_hi, df))
    tc = float(stats.t.ppf(1 - alpha, df))
    t0 = m / se
    return dict(n=n, mean=m, sd=sd, se=se, df=df, t_plain=t0,
                p_plain=float(2 * (1 - stats.t.cdf(abs(t0), df))),
                p_lo=p_lo, p_hi=p_hi, p_tost=max(p_lo, p_hi),
                ci90=(m - tc * se, m + tc * se))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stem", default="h2_spaced")
    ap.add_argument("--margin", type=float, default=0.05)
    a = ap.parse_args()
    rows = load(a.stem)
    cells = sorted({(s, k) for (s, m, k) in rows if (s, "truth", k) in rows and (s, "vision", k) in rows})
    if len(cells) < 3:
        print(f"only {len(cells)} complete (shape, seed) cells in results/{a.stem}*.jsonl - need >= 3.")
        return
    for key, label in (("iou", "FINAL true IoU"), ("peak_iou", "PEAK true IoU")):
        if any(key not in rows[(s, m, k)] for s, k in cells for m in ("truth", "vision")):
            print(f"\n({label}: not recorded in results/{a.stem}*.jsonl - skipped)")
            continue
        tr = np.array([rows[(s, "truth", k)][key] for s, k in cells])
        vi = np.array([rows[(s, "vision", k)][key] for s, k in cells])
        r = tost(tr - vi, a.margin)
        print(f"\n=== {label}: truth vs camera(vision), n={r['n']} (shape, seed) cells, results/{a.stem}*.jsonl ===")
        print(f"truth  {tr.mean():.3f} +/-{tr.std(ddof=1):.3f}    vision {vi.mean():.3f} +/-{vi.std(ddof=1):.3f}")
        print(f"d = truth - vision: mean {r['mean']:+.3f}  sd {r['sd']:.3f}  truth>vision in {(tr > vi).sum()}/{r['n']} cells")
        print(f"ordinary paired t = {r['t_plain']:+.2f} (df {r['df']}, p={r['p_plain']:.3f})")
        print(f"90% CI of d: [{r['ci90'][0]:+.3f}, {r['ci90'][1]:+.3f}]   margin +/-{a.margin}")
        print(f"TOST: p(lower)={r['p_lo']:.3f}  p(upper)={r['p_hi']:.3f}  p_TOST={r['p_tost']:.3f}  "
              f"-> {'EQUIVALENT within +/-%.2f' % a.margin if r['p_tost'] < 0.05 else 'equivalence NOT shown at +/-%.2f' % a.margin}")
    print("\nper shape (final IoU, mean over seeds): truth  vision  diff")
    for s in sorted({c[0] for c in cells}):
        ks = [k for (ss, k) in cells if ss == s]
        t = np.mean([rows[(s, 'truth', k)]['iou'] for k in ks]); v = np.mean([rows[(s, 'vision', k)]['iou'] for k in ks])
        print(f"  {s:9s} {t:.3f}  {v:.3f}  {t - v:+.3f}  (n={len(ks)})")


if __name__ == "__main__":
    main()
