"""
RoboSketch-RL  |  H4 follow-up - how much of the paper-shift loss is recoverable AT ALL?
-------------------------------------------------
WHY. Two H4 designs came back null, and even the privileged `true` arm (which sees
the real paper exactly) loses 0.130 IoU to a paper shift at 60 steps. One
explanation is that the loss is partly UNRECOVERABLE: ink is permanent, so when the
sheet slides, the ink already laid down travels with it and stays on the page as
false positives. If an arm with perfect knowledge of the shift also loses a lot,
then "the camera did not help" is not evidence about cameras - there was little
left to recover - and further H4 variants on paper_shift cannot work.

WHAT. Analytic oracles that KNOW the shift (they read the pen's true landing
position on the sheet, which includes the sheet offset), trace the target outline,
and are scored on true IoU:

  clean       no disturbance, same tracer. The ceiling for this task and horizon.
  continue    follows its waypoint schedule, re-aiming from the true landing
              position every step. It corrects the displacement from the shift
              onward and never re-draws what is already on the page.
  restart     the moment the sheet slides, restarts the whole contour from the
              beginning over the remaining steps (covering the displaced stroke's
              region in the correct place; the displaced ink stays as waste).
  foresight   holds the pen still until the shift has happened, then draws the
              whole contour. Knows the future, so it lays no ink that can be
              displaced. An upper bound no real arm can reach.

The drop of each oracle from `clean` is compared against the drop of the trained
arms in the H4 / H4-short results (read from results/, not retyped).

ONE DIFFERENCE FROM THE TRAINED ARMS THAT MATTERS. The oracle reads the pen's
position ON THE SHEET. The trained arms' observation draws the pen marker from the
pen's WORLD position, with no sheet offset (`DrawEnv._obs`), so after a shift the
marker and the ink disagree by 5-10 px and an agent has to INFER the offset. An
oracle ceiling above the trained arms therefore mixes two things: ink that cannot
be recovered, and an inference the arms may not have learned. This script
separates the first from nothing - it only bounds it from above.

  python rl/h4_oracle.py
  python rl/h4_oracle.py --aggregate
"""
import argparse
import glob
import json
import os
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from draw_env import DrawEnv

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results", "h4_oracle.jsonl")
SHAPES = ["line", "circle", "square", "triangle"]
STRATS = ["clean", "continue", "restart", "foresight"]
HORIZONS = [60, 240]
STEP_SIZE = 0.014


def _sd(x):
    x = np.asarray(x, float)
    return float(x.std(ddof=1)) if x.size > 1 else 0.0


def _tstat(d):
    d = np.asarray(d, float)
    if d.size < 2:
        return float(d.mean()) if d.size else float("nan"), float("nan")
    se = d.std(ddof=1) / np.sqrt(d.size)
    return float(d.mean()), (float(d.mean() / se) if se > 0 else float("nan"))


def load_done():
    done = {}
    if os.path.exists(RESULTS):
        with open(RESULTS, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    r = json.loads(line)
                    done[(r["shape"], r["T"], r["strat"], r["ep"])] = r
    return done


def _contour(env):
    cnts, _ = cv2.findContours((env.target > 127).astype(np.uint8) * 255,
                               cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    pts = max(cnts, key=cv2.contourArea).reshape(-1, 2)          # (col, row)
    c0, r0 = env._world_to_px(*env.pen_xy)
    k = int(np.argmin((pts[:, 0] - c0) ** 2 + (pts[:, 1] - r0) ** 2))
    return np.roll(pts, -k, axis=0)


def run_episode(shape, T, strat, ep):
    seed = 70_000 + ep
    env = DrawEnv(shape=shape, max_steps=T, step_size_m=STEP_SIZE, seed=seed,
                  obs_source="true",
                  disturbance="none" if strat == "clean" else "paper_shift")
    env.reset(seed=seed)
    pts = _contour(env)
    step_px = env.step_size / (2 * 0.10) * (env.canvas_res - 1)
    at = env._dist.get("at", -1)
    off_mag = 0.0
    t0 = 0                              # start of the (re)drawing schedule
    shifted = False
    info = {}
    for t in range(T):
        if strat == "foresight" and not shifted:
            a = np.zeros(2, np.float32)  # lay no ink that the shift can displace
        else:
            span = max(1, T - t0)
            wp = pts[min(int((t - t0) * len(pts) / span), len(pts) - 1)].astype(float)
            cur = np.array(env._world_to_px(*env.pen_xy), float)   # landing pos on sheet
            d = wp - cur
            n = np.hypot(*d)
            if n > 1e-6:
                d = d / n * min(n, step_px)
            a = np.array([d[0] / step_px, -d[1] / step_px], np.float32)
        _, _, term, trunc, info = env.step(np.array([a[0], a[1], 1.0], np.float32))
        if not shifted and np.any(env._paper_off != 0):
            shifted = True
            off_mag = float(np.hypot(*env._paper_off))
            if strat in ("restart", "foresight"):
                t0 = t + 1
        if term or trunc:
            break
    rec = {"shape": shape, "T": T, "strat": strat, "ep": ep, "iou": float(info["iou"]),
           "shift_at": int(at), "shift_px": off_mag}
    env.close()
    return rec


def run(args):
    os.makedirs(os.path.dirname(RESULTS), exist_ok=True)
    done = load_done()
    todo = [(s, T, st, e) for e in range(args.eps) for s in SHAPES for T in HORIZONS
            for st in STRATS if (s, T, st, e) not in done]
    print(f"{len(done)} episodes done, {len(todo)} to go\n", flush=True)
    for i, (shape, T, strat, ep) in enumerate(todo, 1):
        rec = run_episode(shape, T, strat, ep)
        with open(RESULTS, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")
        if i % 60 == 0 or i == len(todo):
            print(f"[{i}/{len(todo)}] {shape:8s} T={T:3d} {strat:9s} ep={ep} "
                  f"iou={rec['iou']:.3f}", flush=True)
    print("\ndone.", flush=True)
    aggregate()


def _arm_drops(pattern, kind="paper_shift"):
    """Mean drop (clean - disturbed) of each trained arm, balanced over cells, read
    straight from the sweep's own result rows."""
    rows = {}
    for path in sorted(glob.glob(os.path.join(ROOT, "results", pattern))):
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    r = json.loads(line)
                    rows[(r["shape"], r["arm"], r["seed"])] = r
    cells = sorted({(s, k) for (s, a, k) in rows
                    if all((s, aa, k) in rows for aa in ("open_loop", "true", "fk", "camera"))})
    out = {}
    for arm in ("true", "fk", "camera"):
        d = [rows[(s, arm, k)]["iou_none"] - rows[(s, arm, k)][f"iou_{kind}"] for s, k in cells]
        out[arm] = (float(np.mean(d)), len(d))
    return out


def aggregate():
    done = load_done()
    if not done:
        print("no results yet.")
        return
    eps = sorted({e for (_, _, _, e) in done})
    print("=== H4 oracle: best IoU reachable under a paper shift, by an arm that KNOWS the shift ===")
    print("true IoU of the finished drawing; paired within (shape, episode)\n")
    summ = {}
    for T in HORIZONS:
        cells = [(s, e) for s in SHAPES for e in eps
                 if all((s, T, st, e) in done for st in STRATS)]
        if not cells:
            continue
        g = lambda st: np.array([done[(s, T, st, e)]["iou"] for s, e in cells], float)
        clean = g("clean")
        print(f"max_steps = {T}   n = {len(cells)} (shape, episode) pairs")
        print("  %-10s %8s %8s | %9s %8s %9s %7s" % (
            "strategy", "IoU", "sd", "drop", "up", "t", "of 80"[:0] + "n"))
        for st in STRATS:
            v = g(st)
            drop = clean - v
            m, t = _tstat(drop)
            summ[(T, st)] = m
            print("  %-10s %8.3f %8.3f | %+9.3f %3d/%-4d %+7.2f %5d" % (
                st, v.mean(), _sd(v), m, int((drop > 0).sum()), len(drop), t, len(drop)))
        sp = np.array([done[(s, T, "continue", e)]["shift_px"] for s, e in cells], float)
        at = np.array([done[(s, T, "continue", e)]["shift_at"] for s, e in cells], float)
        print(f"  shift size {sp.mean():.1f} px (range {sp.min():.1f}-{sp.max():.1f}), "
              f"fires at step {at.mean():.1f} (range {int(at.min())}-{int(at.max())})\n")
    print("=== the same drop for the TRAINED arms (from results/, balanced over cells) ===")
    for label, pat, T in (("H4-short (max_steps=60)", "h4_short_*.jsonl", 60),
                          ("H4 (max_steps=240)", "h4_experiment_*.jsonl", 240)):
        d = _arm_drops(pat)
        print("  %-24s " % label + "   ".join(
            "%s %+.3f (n=%d)" % (a, m, n) for a, (m, n) in d.items()))
        print("  %-24s oracle drop: continue %+.3f  restart %+.3f  foresight %+.3f" % (
            "", summ.get((T, "continue"), float("nan")),
            summ.get((T, "restart"), float("nan")),
            summ.get((T, "foresight"), float("nan"))))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--eps", type=int, default=30)
    ap.add_argument("--aggregate", action="store_true")
    a = ap.parse_args()
    aggregate() if a.aggregate else run(a)
