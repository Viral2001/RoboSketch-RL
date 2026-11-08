"""
RoboSketch-RL  |  H5 - does open-loop error grow with stroke count? (proposal 4.4)
-------------------------------------------------
H5: error in an open-loop drawing plan GROWS with the number of strokes executed,
while a closed-loop controller's does not. This reproduces, in our setting, the
measurement FRIDA (A01, Fig. 11) made on real hardware: without replanning,
deviation "grows linearly as the plan is executed".

THE CONTROLLED CONTRAST. Both arms follow the SAME analytic plan along the target
outline. They differ in exactly one thing:

  open_loop    executes the planned action deltas blind. It assumes each commanded
               move happened as commanded.
  closed_loop  re-aims every step at the next waypoint FROM THE PEN'S ACTUAL
               POSITION. It replans from observation.

This is NOT a learned policy. The closed-loop arm is an analytic position-feedback
controller, so the experiment isolates the effect of replanning from the effect of
training. It says nothing about whether a trained RL policy replans this well.

EXECUTION NOISE is added to the action before the environment sees it (the
environment is not modified), identically for both arms within a (shape, episode):

  jitter       an independent Gaussian on every step (a random walk if uncorrected;
               expected deviation grows ~ sqrt(steps))
  bias         one constant offset per episode, added every step (a calibration or
               backlash error; expected deviation grows ~ linearly in steps)

The two are separate conditions because they predict different growth laws, and
FRIDA's "linear" is a claim about SYSTEMATIC error. Noise levels are in action units
(1.0 = one full step = ~8.9 canvas px).

DEVIATION at step t = distance in canvas px from the pen's actual position to the
nearest target-outline pixel. Growth is summarised by the per-episode linear slope
(px per step) and by the deviation over the final fifth of the episode. True IoU of
the finished drawing is reported alongside.

  python rl/h5_error_growth.py                 # run (resumable)
  python rl/h5_error_growth.py --aggregate     # table + figure
"""
import argparse
import json
import os
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from draw_env import DrawEnv

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results", "h5_error_growth.jsonl")
FIGURE = os.path.join(ROOT, "output", "h5_error_growth.png")
SHAPES = ["line", "circle", "square", "triangle"]
ARMS = ["open_loop", "closed_loop"]
# (name, kind, level in action units)
CONDITIONS = [("clean", "none", 0.0),
              ("jitter_lo", "jitter", 0.05), ("jitter_mid", "jitter", 0.10),
              ("jitter_hi", "jitter", 0.25),
              ("bias_lo", "bias", 0.005), ("bias_mid", "bias", 0.010),
              ("bias_hi", "bias", 0.020)]
MAX_STEPS = 240
STEP_SIZE = 0.014
CURVE_EVERY = 4
_T_CRIT = {3: 3.182, 7: 2.365, 9: 2.262, 11: 2.201, 15: 2.131, 19: 2.093, 23: 2.069,
           31: 2.040, 47: 2.012}


def _sd(x):
    x = np.asarray(x, float)
    return float(x.std(ddof=1)) if x.size > 1 else 0.0


def _tstat(d):
    d = np.asarray(d, float)
    if d.size < 2:
        return float(d.mean()) if d.size else float("nan"), float("nan")
    se = d.std(ddof=1) / np.sqrt(d.size)
    return float(d.mean()), (float(d.mean() / se) if se > 0 else float("nan"))


def _tcrit(n):
    df = n - 1
    k = min(_T_CRIT, key=lambda q: abs(q - df))
    return _T_CRIT[k] if abs(k - df) <= 4 else 1.96


def load_done():
    done = {}
    if os.path.exists(RESULTS):
        with open(RESULTS, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    r = json.loads(line)
                    done[(r["shape"], r["cond"], r["arm"], r["ep"])] = r
    return done


def _contour(env):
    cnts, _ = cv2.findContours((env.target > 127).astype(np.uint8) * 255,
                               cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    pts = max(cnts, key=cv2.contourArea).reshape(-1, 2)          # (col, row)
    c0, r0 = env._world_to_px(*env.pen_xy)
    k = int(np.argmin((pts[:, 0] - c0) ** 2 + (pts[:, 1] - r0) ** 2))
    return np.roll(pts, -k, axis=0)


def _dist_to_outline(env):
    """Per-pixel distance (canvas px) to the nearest target-outline pixel."""
    cnts, _ = cv2.findContours((env.target > 127).astype(np.uint8) * 255,
                               cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    line = np.zeros(env.target.shape, np.uint8)
    cv2.drawContours(line, [max(cnts, key=cv2.contourArea)], -1, 255, 1)
    return cv2.distanceTransform(255 - line, cv2.DIST_L2, 3)


def run_episode(shape, arm, kind, level, ep):
    """One episode. The noise realisation is fixed by (shape, kind, ep) alone, so
    the two arms see exactly the same disturbance and can be paired."""
    seed = 70_000 + ep
    env = DrawEnv(shape=shape, max_steps=MAX_STEPS, step_size_m=STEP_SIZE,
                  seed=seed, obs_source="true")
    env.reset(seed=seed)
    rng = np.random.default_rng([seed, SHAPES.index(shape), 0 if kind == "none" else
                                 (1 if kind == "jitter" else 2)])
    jit = rng.standard_normal((MAX_STEPS, 2)) * (level if kind == "jitter" else 0.0)
    bias = rng.standard_normal(2) * (level if kind == "bias" else 0.0)

    pts = _contour(env)
    dist = _dist_to_outline(env)
    step_px = env.step_size / (2 * 0.10) * (env.canvas_res - 1)
    planned = np.array(env._world_to_px(*env.pen_xy), float)     # open-loop's belief
    devs, info = [], {}
    for t in range(MAX_STEPS):
        wp = pts[min(int(t * len(pts) / MAX_STEPS), len(pts) - 1)].astype(float)
        if arm == "closed_loop":
            cur = np.array(env._world_to_px(*env.pen_xy), float)  # observed position
        else:
            cur = planned                                          # assumed position
        d = wp - cur
        n = np.hypot(*d)
        if n > 1e-6:
            d = d / n * min(n, step_px)
        planned = planned + d                    # what open-loop believes happened
        a = np.array([d[0] / step_px, -d[1] / step_px], np.float32)
        a = np.clip(a + jit[t] + bias, -1.0, 1.0)             # execution noise
        _, _, term, trunc, info = env.step(np.array([a[0], a[1], 1.0], np.float32))
        c, r = env._world_to_px(*env.pen_xy)
        devs.append(float(dist[r, c]))
        if term or trunc:
            break
    devs = np.asarray(devs, float)
    x = np.arange(len(devs))
    last = max(1, len(devs) // 5)
    rec = {"shape": shape, "cond": None, "arm": arm, "ep": ep, "n_steps": len(devs),
           "slope": float(np.polyfit(x, devs, 1)[0]) if len(devs) > 2 else 0.0,
           "mean_dev": float(devs.mean()), "final_dev": float(devs[-last:].mean()),
           "iou": float(info.get("iou", 0.0)),
           "curve": [round(float(v), 2) for v in devs[::CURVE_EVERY]]}
    env.close()
    return rec


def run(args):
    os.makedirs(os.path.dirname(RESULTS), exist_ok=True)
    done = load_done()
    todo = [(s, c, a, e) for e in range(args.eps) for s in SHAPES
            for c in CONDITIONS for a in ARMS if (s, c[0], a, e) not in done]
    print(f"{len(done)} episodes done, {len(todo)} to go\n", flush=True)
    for i, (shape, (name, kind, level), arm, ep) in enumerate(todo, 1):
        rec = run_episode(shape, arm, kind, level, ep)
        rec["cond"], rec["kind"], rec["level"] = name, kind, level
        with open(RESULTS, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")
        if i % 40 == 0 or i == len(todo):
            print(f"[{i}/{len(todo)}] {shape:8s} {name:10s} {arm:11s} ep={ep} "
                  f"slope={rec['slope']:+.3f} final_dev={rec['final_dev']:.2f}", flush=True)
    print("\ndone.", flush=True)
    aggregate()


def _plot(done):
    F = cv2.FONT_HERSHEY_SIMPLEX
    names = [c[0] for c in CONDITIONS]
    W, H = 1500, 760
    img = np.full((H, W, 3), 255, np.uint8)
    cv2.putText(img, "H5: open-loop vs closed-loop deviation as the plan executes",
                (40, 36), F, 0.7, (0, 0, 0), 2, cv2.LINE_AA)
    cv2.putText(img, "same analytic plan, same execution noise; deviation = px from the "
                "pen to the target outline; mean over shapes x episodes",
                (40, 58), F, 0.42, (110, 110, 110), 1, cv2.LINE_AA)
    col = {"open_loop": (60, 70, 200), "closed_loop": (170, 120, 40)}
    cols, rows = 4, 2
    pw, ph = 300, 220
    shown = [n for n in names if n != "clean"]
    ymax = 1.0
    curves = {}
    for n in shown:
        for arm in ARMS:
            cs = [r["curve"] for (s, c, a, e), r in done.items() if c == n and a == arm]
            if cs:
                m = min(len(c) for c in cs)
                curves[(n, arm)] = np.mean([c[:m] for c in cs], axis=0)
                ymax = max(ymax, float(curves[(n, arm)].max()))
    ymax *= 1.1
    for k, n in enumerate(shown):
        x0 = 60 + (k % cols) * (pw + 50)
        y0 = 130 + ph + (k // cols) * (ph + 90)
        cv2.rectangle(img, (x0, y0 - ph), (x0 + pw, y0), (215, 215, 215), 1)
        cv2.putText(img, n, (x0, y0 - ph - 8), F, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
        for f in (0, 0.5, 1.0):
            yy = int(y0 - f * ph)
            cv2.line(img, (x0, yy), (x0 + pw, yy), (238, 238, 238), 1)
            cv2.putText(img, "%.0f" % (f * ymax), (x0 - 34, yy + 4), F, 0.38,
                        (110, 110, 110), 1, cv2.LINE_AA)
        for arm in ARMS:
            c = curves.get((n, arm))
            if c is None:
                continue
            xs = np.linspace(0, pw, len(c))
            pts = [(int(x0 + x), int(y0 - v / ymax * ph)) for x, v in zip(xs, c)]
            for p, q in zip(pts[:-1], pts[1:]):
                cv2.line(img, p, q, col[arm], 2, cv2.LINE_AA)
        cv2.putText(img, "step", (x0 + pw // 2 - 12, y0 + 18), F, 0.4,
                    (110, 110, 110), 1, cv2.LINE_AA)
    for i, arm in enumerate(ARMS):
        cv2.line(img, (1100, 600 + i * 20), (1120, 600 + i * 20), col[arm], 2)
        cv2.putText(img, arm, (1130, 605 + i * 20), F, 0.45, col[arm], 1, cv2.LINE_AA)
    os.makedirs(os.path.dirname(FIGURE), exist_ok=True)
    cv2.imwrite(FIGURE, img)
    print("\nwrote %s" % FIGURE)


def aggregate():
    done = load_done()
    if not done:
        print("no results yet.")
        return
    eps = sorted({e for (_, _, _, e) in done})
    cells = [(s, e) for s in SHAPES for e in eps]
    print("=== H5: open-loop vs closed-loop deviation under execution noise ===")
    print("deviation = px from the pen to the target outline (canvas is 128 px; "
          "one full step ~ 8.9 px)")
    print("slope = per-episode linear growth, px per step; final = mean over the last "
          "fifth of the episode\n")
    hdr = "%-11s %-6s %6s | %17s %17s | %15s %15s | %11s" % (
        "condition", "kind", "level", "slope open", "slope closed",
        "final open", "final closed", "IoU o / c")
    print(hdr); print("-" * len(hdr))
    stats = {}
    for name, kind, level in CONDITIONS:
        row = {}
        for arm in ARMS:
            rs = [done[(s, name, arm, e)] for s, e in cells if (s, name, arm, e) in done]
            row[arm] = rs
        ok = [(s, e) for s, e in cells
              if (s, name, "open_loop", e) in done and (s, name, "closed_loop", e) in done]
        if not ok:
            continue
        g = lambda arm, key: np.array([done[(s, name, arm, e)][key] for s, e in ok], float)
        stats[name] = ok
        print("%-11s %-6s %6.3f | %+8.3f+/-%6.3f %+8.3f+/-%6.3f | %7.2f+/-%5.2f %7.2f+/-%5.2f"
              " | %.3f/%.3f" % (
                  name, kind, level,
                  g("open_loop", "slope").mean(), _sd(g("open_loop", "slope")),
                  g("closed_loop", "slope").mean(), _sd(g("closed_loop", "slope")),
                  g("open_loop", "final_dev").mean(), _sd(g("open_loop", "final_dev")),
                  g("closed_loop", "final_dev").mean(), _sd(g("closed_loop", "final_dev")),
                  g("open_loop", "iou").mean(), g("closed_loop", "iou").mean()))
    print("\n=== the H5 test: paired open_loop - closed_loop, within (shape, episode) ===")
    print("positive = open-loop deviation grows MORE than closed-loop")
    for name, kind, level in CONDITIONS:
        ok = stats.get(name)
        if not ok or name == "clean":
            continue
        g = lambda arm, key: np.array([done[(s, name, arm, e)][key] for s, e in ok], float)
        for key, label in (("slope", "slope (px/step)"), ("final_dev", "final dev (px)")):
            d = g("open_loop", key) - g("closed_loop", key)
            m, t = _tstat(d)
            print("  %-11s %-15s %+8.3f  n=%d  %d/%d up  t=%+7.2f  (crit %.2f)" % (
                name, label, m, len(d), int((d > 0).sum()), len(d), t, _tcrit(len(d))))
    # growth law: does open-loop deviation scale like sqrt(t) (random walk) or t?
    print("\n=== growth law of the OPEN-LOOP arm (log-log slope of mean deviation vs step) ===")
    print("exponent ~0.5 = random walk, ~1.0 = linear (FRIDA's claim); closed-loop for contrast")
    for name, kind, level in CONDITIONS:
        if name == "clean":
            continue
        out = []
        for arm in ARMS:
            cs = [r["curve"] for (s, c, a, e), r in done.items() if c == name and a == arm]
            if not cs:
                continue
            m = np.mean([c[:min(len(c) for c in cs)] for c in cs], axis=0)
            x = np.arange(len(m)) * CURVE_EVERY + 1.0
            sel = (x >= 8) & (m > 1e-3)
            out.append("%s %.2f" % (arm, np.polyfit(np.log(x[sel]), np.log(m[sel]), 1)[0])
                       if sel.sum() > 5 else "%s n/a" % arm)
        print("  %-11s %s" % (name, "   ".join(out)))
    _plot(done)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--eps", type=int, default=12,
                    help="noise realisations per (shape, condition); both arms share each")
    ap.add_argument("--aggregate", action="store_true")
    a = ap.parse_args()
    aggregate() if a.aggregate else run(a)
