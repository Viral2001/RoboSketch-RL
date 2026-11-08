"""
RoboSketch-RL  |  Perception domain randomisation (proposal 4.1)
-------------------------------------------------
THE PROBLEM. `DrawEnv._perceive()` models the camera as a fixed
`resize(150px) + threshold(>60)`. That is a very optimistic camera, and it is
always the *same* camera. So the H2 result - "a camera reward matches a
ground-truth reward" - is really a claim about ONE idealised camera, not about
cameras. A reviewer is entitled to ask whether it survives a camera that is
blurrier, dimmer, noisier, or mounted slightly off-axis.

THE FIX (Tobin et al., IROS 2017). Sample the camera's parameters from a
distribution during training. A policy that keeps working across many cameras
is learning to draw, not learning one sensor's quirks.

WHAT IS RANDOMISED, in the order a real imaging chain applies it:

  paper_tone    the sheet is not pure white
  ink_contrast  how dark the ink actually reads against it
  warp_px       camera pose: the sheet is not perfectly fronto-parallel
  scale_px      effective sensor resolution
  blur_sigma    defocus / lens softness
  gain          exposure
  noise_sd      sensor noise
  thresh_frac   where the binarisation threshold sits between the ink level
                and the paper level (0 = right on the ink, 1 = right on the
                paper). Expressed as a FRACTION, not an absolute grey level:
                an absolute threshold is meaningless once paper_tone, gain and
                ink_contrast move the two levels around - a fixed "60" that
                separates black ink from white paper sits BELOW faint ink on
                dingy paper, and would detect nothing at all.

TWO DISJOINT DISTRIBUTIONS. `train` is what the agent sees while learning.
`heldout` is deliberately OUTSIDE it on every axis - blurrier, dimmer, noisier,
more warped, coarser, with a threshold the agent never met. Testing on `heldout`
asks whether the policy generalises across cameras or merely across the range it
was shown. Reporting only training-camera numbers would be the perception
equivalent of testing on the training set.

PER-EPISODE, NOT PER-STEP. The parameters are drawn once per episode and held
fixed for its duration. This matters more than it looks: the reward is
`iou(t) - iou(t-1)`, so if the camera changed between two steps the difference
would contain camera noise as well as drawing progress, and the agent would be
rewarded and punished for things it did not do. A real camera does not change
mid-episode either.
"""
import cv2
import numpy as np

# Ranges are (low, high), sampled uniformly. `heldout` never overlaps `train`.
TRAIN = {
    "paper_tone":   (0.90, 1.00),   # 1.0 = pure white paper
    "ink_contrast": (0.75, 1.00),   # 1.0 = ink reads pure black
    "warp_px":      (0.0,  1.5),    # RESIDUAL registration error, canvas px
    "scale_px":     (96,   128),    # effective camera resolution
    "blur_sigma":   (0.0,  1.2),
    "gain":         (0.85, 1.20),   # exposure multiplier
    "noise_sd":     (0.0,  8.0),    # additive sensor noise, grey levels
    "thresh_frac":  (0.45, 0.85),   # spans the old fixed camera's 0.765
}

HELDOUT = {
    "paper_tone":   (0.78, 0.88),   # dingier paper
    "ink_contrast": (0.55, 0.72),   # fainter ink
    "warp_px":      (2.0,  3.0),    # a worse residual, still rectified
    "scale_px":     (76,   92),     # coarser sensor
    "blur_sigma":   (1.3,  1.8),    # softer
    "gain":         (0.60, 0.78),   # dimmer
    "noise_sd":     (10.0, 16.0),   # noisier
    "thresh_frac":  (0.28, 0.43),   # a tighter threshold than training ever
                                    # showed: strokes come back thinner
}

# CALIBRATION NOTE. The held-out set has to be a WORSE camera, not a BROKEN one:
# a sensor so bad that every agent scores ~0 would be replaced in reality, and
# would make the comparison measure nothing. The criterion set in advance was
# ~0.45-0.60 of the true ink recovered, against ~0.76 for training and 0.88 for
# the real B6 camera.
#
# MEASURED, AFTER THREE ADJUSTMENTS: 0.394 mean (line 0.284, circle 0.349,
# square 0.524, triangle 0.418) - see rl/perception_calibration.py, which
# regenerates these numbers. That is BELOW the criterion, and the ranges were
# then left alone: continuing to turn the knob until the number lands inside a
# target chosen by the same person is how a calibration quietly becomes a
# result. The achieved value is what is reported anywhere it is quoted.
#
# The shortfall sits almost entirely on the LINE, and that is a property of the
# shape rather than a bad setting: the FIXED camera only recovers 0.665 of a
# perfect line either. A 14-px stroke at res 512 is ~3.5 px at 128, and
# downsample-plus-threshold thins it. Quote these per shape, never pooled.
#
# HONEST SCOPE. Five of the eight axes below move the recovered IoU by less
# than 0.01 in a single-axis ablation, and for gain / paper_tone / ink_contrast
# that is correct physics rather than a defect: the threshold is derived from
# the ink and paper levels as the sensor sees them, so photometric variation
# cancels by construction, exactly as an auto-thresholding pipeline behaves.
# The effect is carried by scale_px, blur_sigma and warp_px. Calling this an
# "8-axis camera distribution" would overstate it.

# The fixed camera every result before 2026-09-12 was produced with, expressed
# in the same parameter space so the three can be compared on equal terms.
FIXED = {
    "paper_tone": 1.0, "ink_contrast": 1.0, "warp_px": 0.0,
    "scale_px": 150, "blur_sigma": 0.0, "gain": 1.0, "noise_sd": 0.0,
    # 0.765 = 195/255, the equivalent of the old `threshold(>60)` on the ink
    # mask once the image is stated the right way round (dark ink on bright
    # paper). It is NOT bit-identical to the old `_perceive`: that one resized a
    # uint8 mask and this one resizes a float image, so the two differ by
    # rounding (measured: perceived-vs-target IoU 0.4626 vs 0.4724 on the
    # trained square, ~0.01). That is fine and deliberate - `DrawEnv` still uses
    # the original `_perceive` by default, so no recorded result moves, and
    # inside the randomisation experiment EVERY arm goes through this class, so
    # the comparison is about randomisation rather than about which code
    # implements the camera.
    "thresh_frac": 195.0 / 255.0,
}


def sample_params(rng, split="train"):
    """Draw one camera from the named distribution."""
    if split == "fixed":
        return dict(FIXED)
    ranges = TRAIN if split == "train" else HELDOUT
    return {k: float(rng.uniform(lo, hi)) for k, (lo, hi) in ranges.items()}


def _warp_matrix(res, warp_px, rng):
    """Perspective transform standing in for camera-pose error.

    Each corner of the sheet is nudged independently, so the sheet is no longer
    fronto-parallel - which is what a hand-mounted camera actually gives you.
    """
    src = np.float32([[0, 0], [res, 0], [res, res], [0, res]])
    dst = src + rng.uniform(-warp_px, warp_px, size=(4, 2)).astype(np.float32)
    return cv2.getPerspectiveTransform(src, dst)


class Camera:
    """One sampled camera. Cheap enough to call every step of training.

    `perceive(canvas)` takes the true ink mask (255 = ink) and returns what this
    camera would recover, as a binary mask at canvas resolution.
    """

    def __init__(self, canvas_res, params, rng):
        self.res = canvas_res
        self.p = params
        # the warp is fixed for the camera's lifetime - it is a mounting error,
        # not per-frame noise - so build the matrix once
        self.M = (_warp_matrix(canvas_res, params["warp_px"], rng)
                  if params["warp_px"] > 1e-6 else None)
        self._rng = rng

    def perceive(self, canvas):
        p = self.p
        # 1. form the greyscale image a camera would actually see: off-white
        #    paper with ink that is dark but not necessarily black
        paper = 255.0 * p["paper_tone"]
        img = np.full((self.res, self.res), paper, np.float32)
        ink = canvas > 127
        img[ink] = paper * (1.0 - p["ink_contrast"])

        # 2. camera pose
        if self.M is not None:
            # BORDER_CONSTANT at the paper level, NOT replicate: replicating
            # smears an ink pixel that touches the canvas edge into a stripe up
            # to warp_px wide along the whole border (measured +34-39% phantom
            # ink). Outside the sheet a camera sees paper, not more ink.
            img = cv2.warpPerspective(img, self.M, (self.res, self.res),
                                      flags=cv2.INTER_LINEAR,
                                      borderMode=cv2.BORDER_CONSTANT,
                                      borderValue=float(paper))

        # 3. sensor resolution - the dominant term, and the only one the old
        #    fixed model had
        s = max(32, int(round(p["scale_px"])))
        small = cv2.resize(img, (s, s), interpolation=cv2.INTER_AREA)

        # 4. defocus
        if p["blur_sigma"] > 1e-3:
            k = int(2 * round(2 * p["blur_sigma"]) + 1)
            small = cv2.GaussianBlur(small, (k, k), p["blur_sigma"])

        # 5. exposure, 6. sensor noise
        small *= p["gain"]
        if p["noise_sd"] > 1e-3:
            small += self._rng.normal(0.0, p["noise_sd"], small.shape)
        # A real sensor saturates. Without this clip a gain above 1 widens the
        # ink-paper separation while the noise stays fixed, so over-exposure
        # would IMPROVE the signal-to-noise ratio - the opposite of what an
        # over-exposed photograph does.
        np.clip(small, 0.0, 255.0, out=small)

        # 7. binarise. The threshold is placed between the ink and paper levels
        #    AS THE SENSOR SEES THEM (i.e. after gain), which is what any real
        #    pipeline does - a fixed grey level would simply stop working when
        #    the exposure changes. Gain therefore does not destroy detection;
        #    it degrades the signal-to-noise ratio, because the noise below is
        #    added at a fixed magnitude regardless of how bright the image is.
        ink_lvl = paper * (1.0 - p["ink_contrast"]) * p["gain"]
        paper_lvl = paper * p["gain"]
        thresh = ink_lvl + p["thresh_frac"] * (paper_lvl - ink_lvl)
        binv = (small < thresh).astype(np.uint8) * 255

        # 8. back to canvas resolution for scoring
        back = cv2.resize(binv, (self.res, self.res), interpolation=cv2.INTER_LINEAR)
        return (back > 50).astype(np.uint8) * 255


def describe(params):
    return "  ".join(f"{k}={v:.2f}" if isinstance(v, float) else f"{k}={v}"
                     for k, v in sorted(params.items()))
