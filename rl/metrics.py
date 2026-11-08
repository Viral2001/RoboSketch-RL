"""
RoboSketch-RL  |  Phase C - drawing-accuracy metrics
-------------------------------------------------
How close is a drawing to its target? These are the project's headline metrics
(IoU, MSE) and the basis of the reward function.

All functions take two binary masks (uint8, 255 = ink/foreground, 0 = blank)
of the same shape, as produced by targets.py / targets.canvas_to_mask().
"""
import cv2
import numpy as np


def _fg(mask):
    return mask > 127


def iou(drawn, target):
    """Intersection-over-Union of the two ink regions. 1 = perfect, 0 = disjoint.

    If BOTH are empty it is defined as 1.0 (nothing to draw, nothing drawn).
    """
    A, B = _fg(drawn), _fg(target)
    inter = np.logical_and(A, B).sum()
    union = np.logical_or(A, B).sum()
    if union == 0:
        return 1.0
    return float(inter) / float(union)


def mse(drawn, target):
    """Mean squared error between the two masks, normalised to [0, 1].

    Masks are compared as 0/1 images, so MSE = fraction of pixels that disagree.
    0 = identical, 1 = every pixel wrong.
    """
    A = _fg(drawn).astype(np.float32)
    B = _fg(target).astype(np.float32)
    return float(np.mean((A - B) ** 2))


def coverage(drawn, target):
    """Fraction of the TARGET that has been drawn over (recall). 1 = fully covered."""
    B = _fg(target)
    if B.sum() == 0:
        return 1.0
    return float(np.logical_and(_fg(drawn), B).sum()) / float(B.sum())


def precision(drawn, target):
    """Fraction of the DRAWING that lands on the target. 1 = no stray ink."""
    A = _fg(drawn)
    if A.sum() == 0:
        return 1.0
    return float(np.logical_and(A, _fg(target)).sum()) / float(A.sum())


def chamfer(drawn, target, sample=None):
    """Symmetric mean distance (in pixels) between the two ink sets.

    Softer than IoU: a stroke that is close but not overlapping still scores
    well. Uses a distance transform so it is cheap. Lower = better; 0 = perfect.
    Returns np.inf if exactly one mask is empty.
    """
    A, B = _fg(drawn), _fg(target)
    if A.sum() == 0 and B.sum() == 0:
        return 0.0
    if A.sum() == 0 or B.sum() == 0:
        return float("inf")
    # distance from every pixel to the nearest foreground pixel of each mask
    dt_to_B = cv2.distanceTransform(255 - (B.astype(np.uint8) * 255), cv2.DIST_L2, 3)
    dt_to_A = cv2.distanceTransform(255 - (A.astype(np.uint8) * 255), cv2.DIST_L2, 3)
    a_to_b = dt_to_B[A].mean()
    b_to_a = dt_to_A[B].mean()
    return float((a_to_b + b_to_a) / 2.0)


def stroke_count(mask, min_area=4):
    """Number of separate ink strokes in a mask = its connected components.

    The raster analogue of D09's "stroke number": a drawing made of one
    continuous trace has 1 component; a fragmented, scribbly one has many.
    Components smaller than `min_area` px are ignored as speckle.
    """
    A = (_fg(mask).astype(np.uint8)) * 255
    if A.sum() == 0:
        return 0
    n, _, stats, _ = cv2.connectedComponentsWithStats(A, connectivity=8)
    # label 0 is the background
    return int(sum(1 for i in range(1, n) if stats[i, cv2.CC_STAT_AREA] >= min_area))


def snr(drawn, target):
    """Stroke Number Ratio (D09) = strokes(drawn) / strokes(target).

    1.0 = the drawing is made of as many strokes as the target needs.
    > 1  = FRAGMENTATION - the agent broke the shape into extra pieces.
    < 1  = strokes merged together (or nothing was drawn).

    Why this metric exists: IoU is blind to fragmentation. An agent can score a
    respectable IoU with a broken, scribbly path. D09 reports SNR for exactly
    this reason, and Learning to Paint (D02) scores WORST of all surveyed
    methods on it (5.660) - RL stroke agents are specifically prone to this.

    Caveat for our setup: with `pen_always_down=True` the pen never lifts, so
    the drawn ink is one connected trace by construction and SNR is ~1 whatever
    the agent does. It only becomes informative once pen up/down is enabled
    (proposal A2). Use `path_ratio` below for fragmentation in the meantime.
    """
    t = stroke_count(target)
    if t == 0:
        return 1.0
    return float(stroke_count(drawn)) / float(t)


def target_perimeter_px(target):
    """Total outline length of the target shape, in pixels.

    Uses the target's contours, so it is the length of the path a perfect pen
    would have to travel to trace the shape exactly once.
    """
    A = (_fg(target).astype(np.uint8)) * 255
    if A.sum() == 0:
        return 0.0
    # A thick stroke is a band, so its boundary traces BOTH sides and the
    # contour length is ~2x the centreline - hence the halving. It must be
    # RETR_LIST, not RETR_EXTERNAL: on a closed shape (circle, square, triangle)
    # the band is an annulus, and RETR_EXTERNAL returns only its outer edge,
    # discarding the inner hole. Measured against the analytic centreline at
    # res=512: EXTERNAL/2 gives 0.52-0.56x on closed shapes (and 1.08x on the
    # line, which is a solid band with no hole), while LIST/2 gives 0.99-1.06x
    # on all four - a small uniform bias instead of a per-shape one.
    cnts, _ = cv2.findContours(A, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    total = sum(cv2.arcLength(c, True) for c in cnts)
    return float(total) / 2.0


def path_ratio(path_len_px, target):
    """How much further the pen travelled than the target actually requires.

    path_ratio = (distance the pen moved) / (target outline length).
    1.0 = the pen traced the shape once, perfectly efficiently.
    > 1  = wasted travel: zig-zag along the stroke, spurs off the outline, or
           re-tracing parts already drawn.

    This is the metric that catches what SNR cannot while the pen never lifts:
    our trained agents draw visibly jagged strokes with occasional excursions
    off the outline, and IoU only partly penalises that.
    """
    L = target_perimeter_px(target)
    if L <= 0:
        return 0.0
    return float(path_len_px) / L


def summary(drawn, target, path_len_px=None):
    """All metrics at once, as a dict (handy for logging / evaluation).

    Pass `path_len_px` (the distance the pen actually travelled, from
    DrawEnv.info["path_len_px"]) to also get the path-efficiency ratio.
    """
    out = {
        "iou": iou(drawn, target),
        "mse": mse(drawn, target),
        "coverage": coverage(drawn, target),
        "precision": precision(drawn, target),
        "chamfer_px": chamfer(drawn, target),
        "snr": snr(drawn, target),
    }
    if path_len_px is not None:
        out["path_ratio"] = path_ratio(path_len_px, target)
    return out
