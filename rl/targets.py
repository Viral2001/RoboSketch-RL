"""
RoboSketch-RL  |  Phase C - target shapes
-------------------------------------------------
The shapes the agent must learn to reproduce, as binary masks in CANVAS pixel
space (same space the drawing is inked in, so a perfect drawing overlaps the
target exactly).

Convention: a target is a uint8 image, 255 = "the pen should ink here",
0 = background. Strokes are drawn with a realistic pen width so a real drawn
stroke can actually cover them.

Task ladder (per the project scope): line -> circle -> square -> triangle,
then later digits/letters.
"""
import cv2
import numpy as np

# default canvas resolution (matches the drawing canvas RES in sim/03)
RES = 512
# target stroke width in pixels. Deliberately generous: a thin 1-2 px target is
# very hard for continuous control to stay on (IoU is punishing to 1 px drift).
# A wider stroke gives the agent tolerance to learn the shape first; it can be
# narrowed later as a difficulty step.
STROKE_PX = 14
# keep shapes inside this fraction of the canvas so they stay well on the paper
MARGIN = 0.20


def _blank(res=RES):
    return np.zeros((res, res), dtype=np.uint8)


def _extent(res=RES):
    """Pixel bounds [lo, hi] of the usable drawing region (with margin)."""
    lo = int(res * MARGIN)
    hi = int(res * (1 - MARGIN))
    return lo, hi


def _stroke(res=RES):
    """Stroke width scaled to the canvas, so a shape rendered at a smaller res
    keeps the same *relative* thickness (STROKE_PX is defined at RES)."""
    return max(1, int(round(STROKE_PX * res / RES)))


def line(res=RES):
    """A horizontal line across the middle of the sheet."""
    img = _blank(res)
    lo, hi = _extent(res)
    mid = res // 2
    cv2.line(img, (lo, mid), (hi, mid), 255, _stroke(res), lineType=cv2.LINE_AA)
    return _binarize(img)


def circle(res=RES):
    """A centred circle."""
    img = _blank(res)
    lo, hi = _extent(res)
    r = (hi - lo) // 2
    cv2.circle(img, (res // 2, res // 2), r, 255, _stroke(res), lineType=cv2.LINE_AA)
    return _binarize(img)


def square(res=RES):
    """A centred square outline."""
    img = _blank(res)
    lo, hi = _extent(res)
    cv2.rectangle(img, (lo, lo), (hi, hi), 255, _stroke(res), lineType=cv2.LINE_AA)
    return _binarize(img)


def triangle(res=RES):
    """A centred upward triangle outline."""
    img = _blank(res)
    lo, hi = _extent(res)
    mid = res // 2
    pts = np.array([[mid, lo], [lo, hi], [hi, hi]], np.int32)
    cv2.polylines(img, [pts], isClosed=True, color=255, thickness=_stroke(res),
                  lineType=cv2.LINE_AA)
    return _binarize(img)


SHAPES = {
    "line": line,
    "circle": circle,
    "square": square,
    "triangle": triangle,
}


def make(name, res=RES):
    """Return the target mask for a named shape."""
    if name not in SHAPES:
        raise ValueError(f"unknown shape '{name}'. choices: {list(SHAPES)}")
    return SHAPES[name](res)


# ------------------------------------------------------------------------------
# Parameterised shapes (proposal 5.4). A shape is the default one scaled by `s`
# about the sheet centre and rotated by `theta` degrees. Two disjoint ranges, so
# a policy can be trained on one and tested on the other:
#   train    s in [0.8, 1.0]   |theta| <= 15 deg
#   heldout  s in [0.6, 0.8)   |theta| in [15, 45] deg   (both outside train)
# Measured furthest ink pixel from the centre (fraction of canvas width): train
# 0.439, heldout 0.354; the default s=1 square/triangle corner is already ~0.42.
# The sheet edge is 0.5, so every shape stays on the sheet.
PARAM_RANGES = {
    "train":   {"scale": (0.8, 1.0), "rot": (0.0, 15.0)},
    "heldout": {"scale": (0.6, 0.8), "rot": (15.0, 45.0)},
    # one factor held out at a time (added 2026-10-31 to split the "heldout" failure):
    "heldout_scale": {"scale": (0.6, 0.8), "rot": (0.0, 15.0)},   # new size, train rotation
    "heldout_rot":   {"scale": (0.8, 1.0), "rot": (15.0, 45.0)},  # train size, new rotation
}


def sample_params(rng, split):
    """Draw (scale, rotation in degrees) from the 'train' or 'heldout' range.
    The rotation sign is random, its magnitude comes from the range."""
    if split not in PARAM_RANGES:
        raise ValueError(f"unknown split '{split}'. choices: {list(PARAM_RANGES)}")
    r = PARAM_RANGES[split]
    s = float(rng.uniform(*r["scale"]))
    theta = float(rng.uniform(*r["rot"])) * (1.0 if rng.random() < 0.5 else -1.0)
    return s, theta


def make_param(name, scale=1.0, theta=0.0, res=RES):
    """Target mask for a named shape scaled by `scale` and rotated by `theta`
    degrees about the sheet centre (y axis points down, as in image space)."""
    if name not in SHAPES:
        raise ValueError(f"unknown shape '{name}'. choices: {list(SHAPES)}")
    lo, hi = _extent(res)
    h = (hi - lo) / 2.0 * scale
    a = np.deg2rad(theta)
    ca, sa = float(np.cos(a)), float(np.sin(a))

    def pts(local):
        # elementwise, NOT `@`: a BLAS matmul here loads MKL's libiomp5 next to
        # torch's libomp and aborts with OMP Error #15 once torch is imported.
        p = np.asarray(local, float)
        x = p[:, 0] * ca - p[:, 1] * sa + res / 2.0
        y = p[:, 0] * sa + p[:, 1] * ca + res / 2.0
        return np.round(np.stack([x, y], axis=1)).astype(np.int32)

    img = _blank(res)
    w = _stroke(res)
    if name == "line":
        p = pts([[-h, 0], [h, 0]])
        cv2.line(img, tuple(p[0]), tuple(p[1]), 255, w, lineType=cv2.LINE_AA)
    elif name == "circle":
        cv2.circle(img, (res // 2, res // 2), int(round(h)), 255, w, lineType=cv2.LINE_AA)
    elif name == "square":
        cv2.polylines(img, [pts([[-h, -h], [h, -h], [h, h], [-h, h]])], True, 255, w,
                      lineType=cv2.LINE_AA)
    else:  # triangle
        cv2.polylines(img, [pts([[0, -h], [-h, h], [h, h]])], True, 255, w,
                      lineType=cv2.LINE_AA)
    return _binarize(img)


def _binarize(img):
    """Anti-aliased grey -> crisp binary mask (255 / 0)."""
    return (img > 40).astype(np.uint8) * 255


def canvas_to_mask(canvas):
    """Convert a drawing canvas (white paper, black ink; BGR or grey) to the
    same 255=ink / 0=blank mask convention as the targets."""
    if canvas.ndim == 3:
        grey = cv2.cvtColor(canvas, cv2.COLOR_BGR2GRAY)
    else:
        grey = canvas
    return (grey < 128).astype(np.uint8) * 255
