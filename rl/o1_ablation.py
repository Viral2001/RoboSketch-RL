"""
RoboSketch-RL  |  O1 ablation - does the agent need to see the clock?
-------------------------------------------------
THE PROBLEM (proposal 3.1, item O1). `DrawEnv` truncates every episode at
`max_steps`, but nothing in the observation says how many steps are left. Two
identical canvases - one with 5 steps remaining, one with 100 - look exactly the
same to the policy and demand completely different actions. The task is
therefore PARTIALLY OBSERVABLE, and PPO is being asked to solve an inference
that is not solvable from its input.

D02 (Learning to Paint, ICCV 2019) puts the step number in the state for exactly
this reason: "the step number t acts as additional information to instruct the
agent the remaining number of steps."

THE FIX. `DrawEnv(time_in_obs=True)` appends a 4th, constant-valued channel
holding 255 * steps / max_steps.

THE ABLATION. Same shapes, same seeds, same budget, same everything - only the
flag changes. Run it as a measured ablation rather than a silent improvement,
because a negative result is just as reportable as a positive one, and because
every number recorded before O1 existed was produced with the flag off.

Reward is `truth` throughout: this question is about observability, not about
H2's perception question, and mixing the two would confound them.

Metrics reported: true IoU (headline), plus `path_ratio` (proposal 4.5) - the
distance the pen travelled divided by the target outline length. The trained
agents visibly zig-zag and make excursions off the outline; path_ratio is what
makes that visible as a number, and it is a plausible thing for a clock to fix
(an agent that knows time is short has a reason to stop wandering).

  conda run -n robosketch python rl/o1_ablation.py --seeds 0 1 2 --timesteps 200000
  conda run -n robosketch python rl/o1_ablation.py --aggregate
"""
import argparse
import json
import os
import sys
from collections import defaultdict

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from experiment import train_eval, warn_config_drift

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results", "o1_ablation.jsonl")
SHAPES = ["line", "circle", "square", "triangle"]
ARMS = [False, True]          # time_in_obs off (baseline) / on (O1)
MODE = "truth"


def _sd(x):
    """Sample standard deviation (ddof=1), 0.0 when there is nothing to spread.

    Every +/- printed by this module is estimated from a handful of seeds, so it
    is a sample statistic. ddof=0 would understate it by ~18-29% at n=2-3.
    """
    x = np.asarray(x, float)
    return float(x.std(ddof=1)) if x.size > 1 else 0.0

def load_done():
    done = {}
    if os.path.exists(RESULTS):
        with open(RESULTS, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    r = json.loads(line)
                    done[(r["shape"], bool(r["time_obs"]), r["seed"])] = r
    return done


def run(args):
    os.makedirs(os.path.dirname(RESULTS), exist_ok=True)
    done = load_done()
    warn_config_drift(done, {"timesteps": args.timesteps,
                             "max_steps": args.max_steps})
    # seed-major, so an interrupted sweep still covers every cell at >=1 seed
    combos = [(shape, arm, seed) for seed in args.seeds
              for shape in SHAPES for arm in ARMS]
    todo = [c for c in combos if c not in done]
    print(f"{len(done)} runs done, {len(todo)} to go "
          f"(seeds={args.seeds}, {args.timesteps} steps each)\n", flush=True)
    for k, (shape, arm, seed) in enumerate(todo, 1):
        print(f"[{k}/{len(todo)}] {shape:8s} time_obs={str(arm):5s} seed={seed} ...",
              flush=True)
        m = train_eval(shape, MODE, seed, args.timesteps, args.n_envs,
                       args.max_steps, args.step_size, time_in_obs=arm)
        rec = {"shape": shape, "time_obs": arm, "seed": seed, "mode": MODE,
               "iou": round(m["iou"], 4), "coverage": round(m["coverage"], 4),
               # peak_iou matters here specifically: O1 tells the agent the
               # episode is ending, and the end of the episode is exactly where
               # the overshoot happens (RESEARCH_LOG 2026-08-23). Judging O1 on
               # final IoU alone could not separate "drew better" from
               # "overshot less".
               "peak_iou": round(m["peak_iou"], 4),
               "overshoot": round(m["overshoot"], 4),
               "steps_used": round(m["steps_used"], 1),
               "snr": round(m["snr"], 3), "path_ratio": round(m["path_ratio"], 3),
               "timesteps": args.timesteps}
        with open(RESULTS, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")
        print(f"        -> IoU {m['iou']:.3f}  peak {m['peak_iou']:.3f}  "
              f"overshoot {m['overshoot']:.3f}  path_ratio {m['path_ratio']:.2f}",
              flush=True)
    print("\nablation complete for the requested seeds.")
    aggregate()


def _cell(done, shape, arm, key):
    return [r[key] for (s, a, sd), r in done.items()
            if s == shape and a == arm and key in r]


def aggregate():
    done = load_done()
    if not done:
        print("no results yet - run the sweep first.")
        return

    print("\n=== O1 ablation: remaining-time channel in the observation ===")
    print("(ground-truth reward; mean +/- std over seeds; IoU higher is better,")
    print(" path_ratio closer to 1 is better - it is pen travel / outline length)\n")
    hdr = (f"{'shape':<9} {'IoU off':>14} {'IoU on':>14} {'delta':>8}"
           f" {'peak off':>9} {'peak on':>8} {'path off':>10} {'path on':>9} {'n':>3}")
    print(hdr)
    print("-" * len(hdr))
    rows, deltas = [], []
    for shape in SHAPES:
        io_off, io_on = _cell(done, shape, False, "iou"), _cell(done, shape, True, "iou")
        pr_off, pr_on = _cell(done, shape, False, "path_ratio"), _cell(done, shape, True, "path_ratio")
        pk_off, pk_on = _cell(done, shape, False, "peak_iou"), _cell(done, shape, True, "peak_iou")
        if not io_off or not io_on:
            continue
        om, os_ = np.mean(io_off), _sd(io_off)
        nm, ns = np.mean(io_on), _sd(io_on)
        d = nm - om
        deltas.append(d)
        pm = np.mean(pr_off) if pr_off else float("nan")
        pn = np.mean(pr_on) if pr_on else float("nan")
        km = np.mean(pk_off) if pk_off else float("nan")
        kn = np.mean(pk_on) if pk_on else float("nan")
        print(f"{shape:<9} {om:>8.3f} +/-{os_:4.3f} {nm:>8.3f} +/-{ns:4.3f} "
              f"{d:>+8.3f} {km:>9.3f} {kn:>8.3f} {pm:>10.2f} {pn:>9.2f} "
              f"{min(len(io_off), len(io_on)):>3}")
        rows.append((shape, om, os_, nm, ns, pm, pn))

    if rows:
        allo = [v for s in SHAPES for v in _cell(done, s, False, "iou")]
        alln = [v for s in SHAPES for v in _cell(done, s, True, "iou")]
        print("-" * len(hdr))
        print(f"{'MEAN':<9} {np.mean(allo):>8.3f} +/-{_sd(allo):4.3f} "
              f"{np.mean(alln):>8.3f} +/-{_sd(alln):4.3f} "
              f"{np.mean(alln) - np.mean(allo):>+8.3f}")
        _paired(done)
    _figure(rows)


def _paired(done):
    """Paired comparison - the only correct one here.

    Both arms run the SAME seeds, so the unit of comparison is the (shape, seed)
    PAIR, not the pooled population. An earlier version of this function tested
    the mean change against the std of all baseline runs pooled together; that
    denominator contains the shape-to-shape spread (line 0.333 vs square 0.408)
    as well as seed noise, so it is far too large and hides real effects.
    """
    print("\n=== paired analysis (same seed on both arms) ===")
    for key, lo_is_better in (("iou", False), ("peak_iou", False),
                              ("overshoot", True), ("path_ratio", True)):
        deltas = []
        for shape in SHAPES:
            seeds = sorted({sd for (s, a, sd) in done if s == shape})
            for sd in seeds:
                off = done.get((shape, False, sd))
                on = done.get((shape, True, sd))
                if off and on and key in off and key in on:
                    deltas.append(on[key] - off[key])
        if len(deltas) < 2:
            continue
        d = np.array(deltas, float)
        se = d.std(ddof=1) / np.sqrt(len(d))
        t = d.mean() / se if se > 0 else float("nan")
        up = int((d > 0).sum())
        # |t| ~ 2.2 is the conventional 5% mark at these sample sizes. Quoted as
        # an effect size: 12 paired runs on 4 hand-picked shapes is not a random
        # sample, so this is a strength-of-evidence hint, not a p-value.
        if abs(t) < 1.5:
            v = "no effect"
        elif abs(t) < 2.2:
            v = "suggestive, not conclusive"
        else:
            good = (d.mean() < 0) if lo_is_better else (d.mean() > 0)
            v = "probably real - " + ("better" if good else "WORSE")
        print(f"  {key:<11s} mean {d.mean():+7.3f}  sd {d.std(ddof=1):6.3f}  "
              f"n={len(d):<3d} {up}/{len(d)} up  t={t:+5.2f}  -> {v}")


def _figure(rows):
    if not rows:
        return
    W, H = 1180, 470
    img = np.full((H, W, 3), 255, np.uint8)
    F = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(img, "O1 ablation: remaining-time channel in the observation",
                (24, 32), F, 0.62, (0, 0, 0), 1, cv2.LINE_AA)
    cv2.putText(img, "true IoU, mean +/- std over seeds (ground-truth reward)",
                (24, 54), F, 0.45, (110, 110, 110), 1, cv2.LINE_AA)
    x0, y0, bw, gap, plotH = 96, 400, 62, 92, 290
    ymax = 0.6
    cv2.line(img, (x0 - 18, y0), (W - 30, y0), (150, 150, 150), 1)
    cv2.line(img, (x0 - 18, y0), (x0 - 18, y0 - plotH), (150, 150, 150), 1)
    for gy in (0.2, 0.4, 0.6):
        yy = int(y0 - gy / ymax * plotH)
        cv2.line(img, (x0 - 18, yy), (W - 30, yy), (238, 238, 238), 1)
        cv2.putText(img, f"{gy:.1f}", (x0 - 58, yy + 5), F, 0.45, (90, 90, 90), 1, cv2.LINE_AA)
    for i, (shape, om, osd, nm, nsd, pm, pn) in enumerate(rows):
        cx = x0 + i * gap + i * 2 * bw
        for j, (m, s, col) in enumerate([(om, osd, (60, 60, 60)),
                                         (nm, nsd, (70, 160, 90))]):
            bx = cx + j * bw
            bh = int(m / ymax * plotH)
            cv2.rectangle(img, (bx, y0 - bh), (bx + bw - 8, y0), col, -1)
            eh = int(s / ymax * plotH)
            mx = bx + (bw - 8) // 2
            cv2.line(img, (mx, y0 - bh - eh), (mx, y0 - bh + eh), (20, 20, 20), 2)
            cv2.putText(img, f"{m:.2f}", (bx - 1, y0 - bh - 14), F, 0.42, col, 1, cv2.LINE_AA)
        cv2.putText(img, shape, (cx + 6, y0 + 22), F, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
        cv2.putText(img, f"path {pm:.1f} -> {pn:.1f}", (cx - 2, y0 + 42), F,
                    0.4, (120, 120, 120), 1, cv2.LINE_AA)
    cv2.rectangle(img, (W - 210, 52), (W - 196, 64), (60, 60, 60), -1)
    cv2.putText(img, "no time channel", (W - 190, 63), F, 0.45, (60, 60, 60), 1, cv2.LINE_AA)
    cv2.rectangle(img, (W - 210, 72), (W - 196, 84), (70, 160, 90), -1)
    cv2.putText(img, "O1: time channel", (W - 190, 83), F, 0.45, (70, 160, 90), 1, cv2.LINE_AA)
    out = os.path.join(ROOT, "output", "results_o1.png")
    cv2.imwrite(out, img)
    print("\nfigure: output/results_o1.png")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    ap.add_argument("--timesteps", type=int, default=200_000)
    ap.add_argument("--n-envs", type=int, default=8)
    ap.add_argument("--max-steps", type=int, default=240)
    ap.add_argument("--step-size", type=float, default=0.014)
    ap.add_argument("--aggregate", action="store_true")
    a = ap.parse_args()
    aggregate() if a.aggregate else run(a)
