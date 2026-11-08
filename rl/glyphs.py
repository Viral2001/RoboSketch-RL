"""
RoboSketch-RL  |  Stage 6 - digit glyph targets (multi-stroke) + skeletons
-------------------------------------------------------------------------
Hand-defined stroke skeletons for the digits 0-9, in a unit box
(x in about [-0.7, 0.7], y in [-1, 1], y DOWN like image space). A glyph is a
LIST OF STROKES; a stroke is an (N,2) polyline. Several digits need a pen lift
(4, 8, 9 here), which is why pen_always_down=True cannot draw them (proposal A2).

NOT a font and NOT human handwriting: these are my own schematic skeletons, so a
classifier trained on them (rl/recognise.py) measures "looks like our template",
not human legibility. Same stroke width / margin / canvas convention as
rl/targets.py (255 = ink). Nothing here changes any existing module.
"""
import cv2
import numpy as np

from targets import RES, _extent, _stroke, _binarize   # run with rl/ on sys.path


def _arc(cx, cy, rx, ry, a0, a1, n=24):
    """Points on an ellipse arc, angles in degrees, 0 = +x, 90 = DOWN (image space)."""
    a = np.deg2rad(np.linspace(a0, a1, n))
    return np.stack([cx + rx * np.cos(a), cy + ry * np.sin(a)], axis=1)


def _poly(*pts):
    return np.asarray(pts, float)


def _cat(*parts):
    return np.concatenate(parts, axis=0)


def _skeletons():
    g = {}
    g["0"] = [_arc(0, 0, 0.55, 1.0, 0, 360, 40)]
    g["1"] = [_poly((-0.4, -0.55), (0.1, -1.0), (0.1, 1.0))]
    g["2"] = [_cat(_arc(0, -0.5, 0.55, 0.5, 180, 405, 20), _poly((-0.6, 1.0), (0.65, 1.0)))]
    g["3"] = [_cat(_arc(0, -0.5, 0.5, 0.5, 200, 450, 18), _arc(0, 0.5, 0.55, 0.5, 270, 520, 18))]
    g["4"] = [_poly((0.35, -1.0), (-0.65, 0.45), (0.7, 0.45)),
              _poly((0.35, -1.0), (0.35, 1.0))]
    g["5"] = [_cat(_poly((0.55, -1.0), (-0.45, -1.0), (-0.5, -0.1)),
                   _arc(0, 0.4, 0.6, 0.6, -125, 140, 20))]
    g["6"] = [_cat(_poly((0.4, -1.0), (-0.5, 0.15)), _arc(0, 0.45, 0.55, 0.55, 190, 550, 30))]
    g["7"] = [_poly((-0.6, -1.0), (0.6, -1.0), (-0.2, 1.0))]
    g["8"] = [_arc(0, -0.5, 0.45, 0.5, 0, 360, 28), _arc(0, 0.5, 0.55, 0.5, 0, 360, 28)]
    g["9"] = [_arc(0, -0.45, 0.55, 0.55, 0, 360, 30), _poly((0.55, -0.45), (0.3, 1.0))]
    return g


GLYPHS = _skeletons()
NAMES = sorted(GLYPHS)          # '0'..'9'


def n_strokes(name):
    return len(GLYPHS[name])


def strokes_px(name, scale=1.0, theta=0.0, shift=(0.0, 0.0), res=RES, jitter=0.0, rng=None):
    """Skeleton strokes in canvas pixels (list of (N,2) float arrays).
    scale/theta as in targets.make_param (theta degrees about the sheet centre);
    shift = (dx, dy) in canvas fractions; jitter = per-vertex gaussian sd in unit-box
    units (augmentation for the classifier only)."""
    lo, hi = _extent(res)
    h = (hi - lo) / 2.0 * scale
    a = np.deg2rad(theta)
    ca, sa = float(np.cos(a)), float(np.sin(a))
    out = []
    for s in GLYPHS[name]:
        p = np.array(s, float)
        if jitter > 0:
            p = p + rng.normal(0, jitter, p.shape)
        x = p[:, 0] * h
        y = p[:, 1] * h
        # elementwise rotation, NOT `@` (MKL/torch OpenMP clash, see targets.make_param)
        X = x * ca - y * sa + res / 2.0 + shift[0] * res
        Y = x * sa + y * ca + res / 2.0 + shift[1] * res
        out.append(np.stack([X, Y], axis=1))
    return out


def render(strokes, width=None, res=RES):
    """Binary 255/0 mask from pixel strokes."""
    img = np.zeros((res, res), np.uint8)
    w = _stroke(res) if width is None else max(1, int(round(width * res / RES)))
    for s in strokes:
        cv2.polylines(img, [np.round(s).astype(np.int32)], False, 255, w, lineType=cv2.LINE_AA)
    return _binarize(img)


def make_glyph(name, scale=1.0, theta=0.0, res=RES):
    """Target mask for digit `name` ('0'..'9'), same call shape as targets.make_param."""
    if name not in GLYPHS:
        raise ValueError(f"unknown glyph '{name}'. choices: {NAMES}")
    return render(strokes_px(name, scale, theta, res=res), res=res)
