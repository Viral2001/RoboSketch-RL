"""
RoboSketch-RL  |  Can the agent be taught to stop?
-------------------------------------------------
`rl/overrun.py` measured the problem: every trained agent traces its shape in
the first ~15% of the episode, overshoots it by 0.034-0.131 IoU in the few steps
straight afterwards, and then sits on a frozen canvas for the remaining ~74% of
the episode. The mean loss, 0.064 IoU, is larger than the entire truth-vs-vision
difference H2 exists to measure.

THREE ARMS, one question each:

  baseline  - `max_steps=240`, no way to stop. What every recorded result used.

  plateau   - the ENVIRONMENT ends the episode after 20 steps with no
              improvement. Cheap and needs no change to the action space.
              This arm was expected to recover the wasted SAMPLE BUDGET (74%
              of every episode was doing nothing) but NOT to fix the overshoot,
              because a plateau detector is lagging: replaying an already
              trained agent with it gave 240 -> 51 steps and an IoU unchanged
              at 0.470, the damage already drawn by the time the detector fires.
              That reasoning turned out to hold only for a FROZEN policy.
              Trained WITH the detector present, the policy never learns the
              overshooting behaviour in the first place - and this is the
              winning arm (see the results entry in docs/RESEARCH_LOG.md).

  stop      - the AGENT gets a 4th action head, "I am finished". Expected to be
              the only arm that could prevent the overshoot, on the reasoning
              that only the policy knows the moment it has completed the shape.
              It cannot be retrofitted to an existing model - the head has to be
              trained. Measured: it cuts the overshoot but its IoU gain is not
              statistically supported, so the expectation was wrong twice over.

WHAT TO LOOK AT. `iou` is the headline, but `overshoot` (= peak - final) is the
quantity this experiment is about, and `steps_used` says whether the agent
learned to stop at all. An arm that lowers `overshoot` while holding `peak_iou`
is a real win; an arm that lowers `overshoot` by also lowering `peak_iou` has
just learned to stop too early, which is worse.

Reward is `truth` throughout - this is a question about episode structure, not
about perception, and mixing it with H2 would confound the two.

  conda run -n robosketch python rl/overshoot_ablation.py --seeds 0 1 --timesteps 200000
  conda run -n robosketch python rl/overshoot_ablation.py --aggregate
"""
import argparse
import json
import os
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from experiment import train_eval, warn_config_drift

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results", "overshoot_ablation.jsonl")
SHAPES = ["line", "circle", "square", "triangle"]
MODE = "truth"

ARMS = {
    "baseline": {},
    "plateau": {"plateau_patience": 20},
    "stop": {"allow_stop": True},
}
ARM_ORDER = ["baseline", "plateau", "stop"]


def _sd(x):
    """Sample standard deviation (ddof=1), 0.0 when there is nothing to spread.

    Every +/- printed by this module is estimated from a handful of seeds, so it
    is a sample statistic. ddof=0 would understate it by ~18-29% at n=2-3.
    """
    x = np.asarray(x, float)
    return float(x.std(ddof=1)) if x.size > 1 else 0.0

def load_done():
    """Read every shard of this ablation's results.

    The sweep can be split across concurrent processes (`--shapes`), each
    writing its own shard, so that a 2-core machine can keep both cores busy.
    Separate files rather than one shared file: concurrent appends from several
    processes are not worth trusting for results we cannot regenerate cheaply.
    """
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


def run(args):
    os.makedirs(os.path.dirname(RESULTS), exist_ok=True)
    shapes = args.shapes or SHAPES
    shard = RESULTS if not args.shard else RESULTS.replace(".jsonl", f"_{args.shard}.jsonl")
    done = load_done()
    warn_config_drift(done, {"timesteps": args.timesteps,
                             "max_steps": args.max_steps})
    combos = [(shape, arm, seed) for seed in args.seeds
              for shape in shapes for arm in ARM_ORDER]      # seed-major
    todo = [c for c in combos if c not in done]
    print(f"{len(done)} runs done, {len(todo)} to go "
          f"(seeds={args.seeds}, {args.timesteps} steps each)\n", flush=True)
    for k, (shape, arm, seed) in enumerate(todo, 1):
        print(f"[{k}/{len(todo)}] {shape:8s} {arm:8s} seed={seed} ...", flush=True)
        m = train_eval(shape, MODE, seed, args.timesteps, args.n_envs,
                       args.max_steps, args.step_size, env_kwargs=ARMS[arm],
                       stop_bias=args.stop_bias)
        rec = {"shape": shape, "arm": arm, "seed": seed, "mode": MODE,
               "iou": round(m["iou"], 4), "peak_iou": round(m["peak_iou"], 4),
               "overshoot": round(m["overshoot"], 4),
               "steps_used": round(m["steps_used"], 1),
               "coverage": round(m["coverage"], 4),
               "path_ratio": round(m["path_ratio"], 3),
               "timesteps": args.timesteps, "max_steps": args.max_steps}
        with open(shard, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")
        print(f"        -> IoU {m['iou']:.3f}  peak {m['peak_iou']:.3f}  "
              f"overshoot {m['overshoot']:.3f}  steps {m['steps_used']:.0f}",
              flush=True)
    print(f"\nablation complete for shapes={shapes} seeds={args.seeds}.")
    if not args.shard:            # a shard is one worker; it does not summarise
        aggregate()


def _cell(done, shape, arm, key):
    return [r[key] for (s, a, sd), r in done.items()
            if s == shape and a == arm and key in r]


def aggregate():
    done = load_done()
    if not done:
        print("no results yet - run the sweep first.")
        return

    print("\n=== Overshoot ablation (ground-truth reward, mean over seeds) ===")
    print("iou = what gets reported | peak = best drawing in the episode")
    print("overshoot = peak - iou (lower is better) | steps = episode length used\n")
    hdr = (f"{'shape':<9} {'arm':<9} {'IoU':>14} {'peak':>8} {'overshoot':>10}"
           f" {'steps':>7} {'path':>7} {'n':>3}")
    print(hdr)
    print("-" * len(hdr))
    for shape in SHAPES:
        for arm in ARM_ORDER:
            v = _cell(done, shape, arm, "iou")
            if not v:
                continue
            pk = _cell(done, shape, arm, "peak_iou")
            ov = _cell(done, shape, arm, "overshoot")
            st = _cell(done, shape, arm, "steps_used")
            pr = _cell(done, shape, arm, "path_ratio")
            print(f"{shape:<9} {arm:<9} {np.mean(v):>8.3f} +/-{_sd(v):4.3f} "
                  f"{np.mean(pk):>8.3f} {np.mean(ov):>10.3f} {np.mean(st):>7.0f} "
                  f"{np.mean(pr):>7.2f} {len(v):>3}")
        print()

    # Arm means are printed only over the cells where EVERY arm has a run, so a
    # partially finished (or shard-interrupted) sweep cannot compare one arm on
    # four shapes against another on two - which would measure the shapes, not
    # the arms.
    common = [(s, sd) for s in SHAPES
              for sd in sorted({d for (sh, a, d) in done if sh == s})
              if all((s, arm, sd) in done for arm in ARM_ORDER)]
    if not common:
        print("\nno (shape, seed) cell yet has all three arms - no comparison possible.")
        _figure(done)
        return
    print("-" * len(hdr))
    print(f"balanced over {len(common)} (shape, seed) cells where all three arms ran")
    print(f"{'ALL':<9} {'':<9} {'IoU':>14} {'peak':>8} {'overshoot':>10} {'steps':>7}")
    for arm in ARM_ORDER:
        v = [done[(s, arm, sd)]["iou"] for s, sd in common]
        pk = [done[(s, arm, sd)]["peak_iou"] for s, sd in common]
        ov = [done[(s, arm, sd)]["overshoot"] for s, sd in common]
        st = [done[(s, arm, sd)]["steps_used"] for s, sd in common]
        print(f"{'':<9} {arm:<9} {np.mean(v):>8.3f} +/-{_sd(v):4.3f} "
              f"{np.mean(pk):>8.3f} {np.mean(ov):>10.3f} {np.mean(st):>7.0f}")
    _paired(done, common)
    _figure(done)


def _paired(done, common):
    """Each arm against the baseline, paired within (shape, seed).

    Paired, not pooled: the arms share seeds, and a pooled std over all baseline
    runs would carry the shape-to-shape spread (line ~0.33 vs square ~0.47) into
    a threshold meant to represent run-to-run noise. That is the exact error
    this project made once already, on the O1 ablation, where it reported "no
    measurable effect" for an effect that was there.
    """
    print("\n=== paired vs baseline (same shape and seed in every pair) ===")
    for arm in ARM_ORDER[1:]:
        d_iou, d_pk, d_ov, d_st = [], [], [], []
        for s, sd in common:
            b, a = done[(s, "baseline", sd)], done[(s, arm, sd)]
            d_iou.append(a["iou"] - b["iou"])
            d_pk.append(a["peak_iou"] - b["peak_iou"])
            d_ov.append(a["overshoot"] - b["overshoot"])
            d_st.append(a["steps_used"] - b["steps_used"])
        n = len(d_iou)
        di, dp, dov = np.array(d_iou), np.array(d_pk), np.array(d_ov)
        se = di.std(ddof=1) / np.sqrt(n) if n > 1 else float("nan")
        t = di.mean() / se if se and se > 0 else float("nan")
        # The bar an arm has to clear, in order:
        #   (a) the IoU gain must be statistically supported, not just positive -
        #       a positive mean with t<1.5 and half the pairs going the wrong way
        #       is noise, and calling that a fix is how the O1 ablation was first
        #       misread (in the other direction);
        #   (b) the overshoot must actually fall;
        #   (c) peak IoU must be held - "no overshoot" bought by stopping before
        #       there is anything to overshoot is not a fix, it is a worse agent.
        consistent = abs(t) > 2.2 and int((di > 0).sum()) >= 0.8 * n
        if dp.mean() < -0.02 and dov.mean() < -0.01:
            v = "NOT A FIX - overshoot gone because it stops before finishing"
        elif not consistent and dov.mean() < -0.01:
            v = ("overshoot cut, but the IoU gain is not supported "
                 f"(t={t:+.2f}, {int((di > 0).sum())}/{n}) - inconclusive")
        elif consistent and dov.mean() < -0.01 and dp.mean() > -0.02:
            v = "FIXES IT - overshoot cut, peak held, IoU up consistently"
        elif consistent and di.mean() > 0:
            v = "better, but not via the overshoot"
        elif abs(t) < 1.5:
            v = "no measurable effect"
        else:
            v = "suggestive, not conclusive"
        print(f"  {arm:9s} n={n:<3d} IoU {di.mean():+.3f} (t={t:+.2f}, "
              f"{int((di > 0).sum())}/{n} up)  peak {dp.mean():+.3f}  "
              f"overshoot {dov.mean():+.3f}  steps {np.mean(d_st):+.0f}")
        print(f"            -> {v}")


def _figure(done):
    W, H = 1240, 500
    img = np.full((H, W, 3), 255, np.uint8)
    F = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(img, "Overshoot ablation: can the agent be taught to stop?",
                (24, 32), F, 0.64, (0, 0, 0), 1, cv2.LINE_AA)
    cv2.putText(img, "solid = reported IoU    hatched cap = IoU lost to the overshoot",
                (24, 54), F, 0.44, (110, 110, 110), 1, cv2.LINE_AA)
    cols = {"baseline": (60, 60, 60), "plateau": (200, 140, 60), "stop": (70, 160, 90)}
    x0, y0, bw, gap, plotH, ymax = 90, 410, 44, 70, 300, 0.7
    cv2.line(img, (x0 - 18, y0), (W - 30, y0), (150, 150, 150), 1)
    for gy in (0.2, 0.4, 0.6):
        yy = int(y0 - gy / ymax * plotH)
        cv2.line(img, (x0 - 18, yy), (W - 30, yy), (238, 238, 238), 1)
        cv2.putText(img, f"{gy:.1f}", (x0 - 58, yy + 5), F, 0.45, (90, 90, 90), 1, cv2.LINE_AA)
    for i, shape in enumerate(SHAPES):
        cx = x0 + i * (gap + len(ARM_ORDER) * bw)
        for j, arm in enumerate(ARM_ORDER):
            v = _cell(done, shape, arm, "iou")
            if not v:
                continue
            pk = _cell(done, shape, arm, "peak_iou")
            bx = cx + j * bw
            bh = int(np.mean(v) / ymax * plotH)
            ph = int(np.mean(pk) / ymax * plotH)
            # the cap between reported and peak = what the overshoot cost
            cv2.rectangle(img, (bx, y0 - ph), (bx + bw - 6, y0 - bh), (205, 205, 205), -1)
            cv2.rectangle(img, (bx, y0 - bh), (bx + bw - 6, y0), cols[arm], -1)
            cv2.putText(img, f"{np.mean(v):.2f}", (bx - 2, y0 - ph - 8), F,
                        0.38, cols[arm], 1, cv2.LINE_AA)
            cv2.putText(img, arm[:4], (bx, y0 + 16), F, 0.34, (120, 120, 120), 1, cv2.LINE_AA)
        cv2.putText(img, shape, (cx + 20, y0 + 36), F, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
    for k, arm in enumerate(ARM_ORDER):
        cv2.rectangle(img, (W - 200, 74 + k * 20), (W - 186, 86 + k * 20), cols[arm], -1)
        cv2.putText(img, arm, (W - 180, 85 + k * 20), F, 0.45, cols[arm], 1, cv2.LINE_AA)
    out = os.path.join(ROOT, "output", "results_overshoot.png")
    cv2.imwrite(out, img)
    print("\nfigure: output/results_overshoot.png")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs="+", default=[0, 1])
    ap.add_argument("--shapes", nargs="+", choices=SHAPES,
                    help="run only these shapes (to split the sweep across processes)")
    ap.add_argument("--shard", default="",
                    help="name for this worker's results file, e.g. --shard a")
    ap.add_argument("--timesteps", type=int, default=200_000)
    ap.add_argument("--stop-bias", type=float, default=-2.0,
                    help="initial bias of the stop head; -2.0 makes an untrained "
                         "episode ~160 steps instead of ~3, so the agent can see "
                         "a finished shape before it can exploit the exit")
    ap.add_argument("--n-envs", type=int, default=8)
    ap.add_argument("--max-steps", type=int, default=240)
    ap.add_argument("--step-size", type=float, default=0.014)
    ap.add_argument("--aggregate", action="store_true")
    a = ap.parse_args()
    aggregate() if a.aggregate else run(a)
