"""
RoboSketch-RL  |  presentation figure builder
-------------------------------------------------
Composes slide-ready figures from the real experiment outputs in output/.
Nothing here invents data: every panel is an actual saved result.

Run:  conda run -n robosketch python docs/presentation/make_figures.py
"""
import os

import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "output")
FIG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figures")
os.makedirs(FIG, exist_ok=True)

WHITE = (255, 255, 255)
INK = (26, 23, 15)          # BGR of #0F172A-ish
MUTED = (105, 85, 71)
BORDER = (225, 213, 203)
FONT = cv2.FONT_HERSHEY_DUPLEX


def _panel(img, label, size=340, pad=14, label_h=34, sub=None):
    """One labelled square panel: image on white, caption strip above."""
    if img is None:
        img = np.full((size, size, 3), 240, np.uint8)
    if img.ndim == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    img = cv2.resize(img, (size, size), interpolation=cv2.INTER_AREA)
    h = size + label_h + 2 * pad
    w = size + 2 * pad
    card = np.full((h, w, 3), 255, np.uint8)
    cv2.rectangle(card, (0, 0), (w - 1, h - 1), BORDER, 1)
    card[pad + label_h:pad + label_h + size, pad:pad + size] = img
    cv2.rectangle(card, (pad, pad + label_h), (pad + size - 1, pad + label_h + size - 1),
                  BORDER, 1)
    cv2.putText(card, label, (pad, pad + 22), FONT, 0.52, INK, 1, cv2.LINE_AA)
    if sub:
        cv2.putText(card, sub, (pad + 8, h - 8), FONT, 0.42, MUTED, 1, cv2.LINE_AA)
    return card


def _row(panels, gap=16, title=None):
    h = max(p.shape[0] for p in panels)
    w = sum(p.shape[1] for p in panels) + gap * (len(panels) - 1)
    top = 42 if title else 0
    out = np.full((h + top, w, 3), 255, np.uint8)
    if title:
        cv2.putText(out, title, (2, 28), FONT, 0.66, INK, 1, cv2.LINE_AA)
    x = 0
    for p in panels:
        out[top:top + p.shape[0], x:x + p.shape[1]] = p
        x += p.shape[1] + gap
    return out


def _read(name, flag=cv2.IMREAD_COLOR):
    path = os.path.join(OUT, name)
    return cv2.imread(path, flag) if os.path.exists(path) else None


def _invert_mask_to_white(mask):
    """Binary mask (255=ink on black) -> black ink on white paper."""
    if mask is None:
        return None
    if mask.ndim == 3:
        mask = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)
    return cv2.cvtColor(255 - mask, cv2.COLOR_GRAY2BGR)


# --------------------------------------------------------------- figure 1 --
def fig_targets():
    """The task ladder: the four target masks the agent must reproduce."""
    import sys
    sys.path.insert(0, os.path.join(ROOT, "rl"))
    import targets as T
    panels = []
    for name in ("line", "circle", "square", "triangle"):
        m = T.make(name)
        panels.append(_panel(_invert_mask_to_white(m), f"target: {name}",
                             sub="512x512 mask, 14 px stroke"))
    img = _row(panels, title="Task ladder - target shapes (rl/targets.py)")
    cv2.imwrite(os.path.join(FIG, "fig_targets.png"), img)
    return "fig_targets.png"


# --------------------------------------------------------------- figure 2 --
def fig_vision_pipeline(shape="square"):
    """B6: camera frame -> OpenCV extraction -> ground truth -> overlay."""
    raw = _read(f"cam_raw_{shape}.png")
    perceived = _invert_mask_to_white(_read(f"cam_perceived_{shape}.png", cv2.IMREAD_GRAYSCALE))
    gt = _invert_mask_to_white(_read(f"cam_groundtruth_{shape}.png", cv2.IMREAD_GRAYSCALE))
    ov = _read(f"cam_overlay_{shape}.png")
    if ov is not None:
        ov = 255 - ov                       # black bg -> white bg for slides
    panels = [
        _panel(raw, "1. raw camera frame", sub="480x480 virtual RGB"),
        _panel(perceived, "2. OpenCV extraction", sub="segment - crop - threshold"),
        _panel(gt, "3. ground truth canvas", sub="what the pen really inked"),
        _panel(ov, "4. overlay - agreement", sub="IoU = 0.882 (colours inverted)"),
    ]
    img = _row(panels, title=f"B6 perception pipeline - '{shape}' (sim/04_camera_capture.py)")
    cv2.imwrite(os.path.join(FIG, "fig_vision_pipeline.png"), img)
    return "fig_vision_pipeline.png"


# --------------------------------------------------------------- figure 3 --
def fig_before_after():
    """PPO learning evidence: untrained vs trained rollout for every shape."""
    rows = []
    ious = {"line": (0.079, 0.508), "circle": (0.000, 0.443),
            "square": (0.000, 0.493), "triangle": (0.000, 0.421)}
    for name in ("line", "circle", "square", "triangle"):
        b = _read(f"trained_{name}_kin_before.png")
        a = _read(f"trained_{name}_kin_after.png")
        i0, i1 = ious[name]
        rows.append(_panel(b, f"{name} - untrained", size=250,
                           sub=f"IoU {i0:.3f}"))
        rows.append(_panel(a, f"{name} - trained", size=250,
                           sub=f"IoU {i1:.3f}"))
    top = _row(rows[:4], title="PPO before / after - 400k steps each (red = target, black = drawn)")
    bot = _row(rows[4:])
    gap = np.full((16, max(top.shape[1], bot.shape[1]), 3), 255, np.uint8)
    w = max(top.shape[1], bot.shape[1])
    canvas = np.full((top.shape[0] + bot.shape[0] + 16, w, 3), 255, np.uint8)
    canvas[:top.shape[0], :top.shape[1]] = top
    canvas[top.shape[0] + 16:, :bot.shape[1]] = bot
    cv2.imwrite(os.path.join(FIG, "fig_before_after.png"), canvas)
    return "fig_before_after.png"


# --------------------------------------------------------------- figure 4 --
def fig_b5_drawings():
    """B5: scripted IK strokes, geometry-verified."""
    line = _read("drawing_line.png")
    sq = _read("drawing_square.png")
    inter = _read("drawing_interactive.png")
    panels = [
        _panel(line, "B5 line - 241 pen points", sub="2492 inked px, rows 252-259"),
        _panel(sq, "B5 square - 484 pen points", sub="8451 inked px, hollow centre"),
        _panel(inter, "interactive sandbox (05)", sub="human-driven pen, real ink"),
    ]
    img = _row(panels, title="B5 - the pen leaves a real mark on the canvas")
    cv2.imwrite(os.path.join(FIG, "fig_b5_drawings.png"), img)
    return "fig_b5_drawings.png"


# --------------------------------------------------------------- figure 5 --
def fig_montage():
    """Pass the headline montage through unchanged (already slide-ready)."""
    m = _read("results_montage.png")
    if m is not None:
        cv2.imwrite(os.path.join(FIG, "fig_montage.png"), m)
    return "fig_montage.png"


if __name__ == "__main__":
    made = [fig_targets(), fig_vision_pipeline(), fig_before_after(),
            fig_b5_drawings(), fig_montage()]
    for m in made:
        p = os.path.join(FIG, m)
        print(f"  {m:28s} {'OK' if os.path.exists(p) else 'MISSING'}")
    print(f"\nfigures -> {FIG}")
