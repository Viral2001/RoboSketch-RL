"""
RoboSketch-RL  |  H4 disturbance model - the linchpin experiment (proposal 4.3)
-------------------------------------------------
WHY THIS EXPERIMENT DECIDES THE PROJECT. D01 (Lee et al., ICRA 2022) draws well
with NO camera, synchronising through forward kinematics, and argues that being
camera-free is an advantage because it ignores nuisance visual variation. If a
camera buys nothing, D01 is a complete answer to this project's motivation.

The answer has to be that a camera sees errors kinematics CANNOT. An
FK-synchronised agent believes the pen is wherever it commanded it to be. So:

  pen slip      - the pen is nudged without the command changing. FK believes
                  the old position; the paper disagrees.
  paper shift   - the sheet moves under the pen. Every subsequent stroke lands
                  displaced. FK cannot know.
  ink failure   - the pen stops depositing ink for a stretch of steps. FK's
                  belief is a perfect drawing; the paper is blank there. This is
                  the cleanest case: the error is INVISIBLE to kinematics by
                  construction, and obvious to a camera.

Until this is measured, "a camera is necessary" is an assertion. This module is
what turns it into a number.

THE THREE OBSERVATION SOURCES compared (see `DrawEnv(obs_source=...)`):

  "true"    privileged: the agent sees the real ink. Not physically available to
            any robot, and included only as a ceiling.
  "fk"      D01's condition: the agent sees what its own kinematics predict it
            drew - commanded positions, assumed-perfect ink, no knowledge of any
            disturbance.
  "camera"  ours: the agent sees a photograph of the real paper.

Scoring is always TRUE IoU of the real canvas, so a belief that happens to look
tidy earns nothing.
"""
import numpy as np

KINDS = ("none", "slip", "paper_shift", "ink_failure", "mixed")

# "mixed" draws one of the three real disturbances (or none) per episode. It is
# the TRAINING condition: each arm is trained against the whole family and then
# evaluated on each kind separately.
#
# Why train with disturbances rather than train clean and test disturbed: a
# clean-trained policy meeting a disturbance has simply been pushed
# out-of-distribution, and the result would measure brittleness. The claim being
# tested is about INFORMATION - that a camera can see an error forward
# kinematics cannot - so every arm has to be given a fair chance to learn to use
# whatever information it has.
_MIX = ("none", "slip", "paper_shift", "ink_failure")


def make(kind, rng, max_steps, canvas_res, scale=1.0):
    """Sample one disturbance for an episode.

    `at` lands in the first ~4-16% of the episode, which is WHILE THE AGENT IS
    STILL DRAWING.

    That window is set by a measurement, not a guess. `rl/overrun.py` found that
    agents trace their shape within the first ~10-17% of the episode and then sit
    on a frozen canvas for the remaining ~74%. A first version of this module
    fired the disturbance between 20% and 55% of the episode - sensible-looking,
    and useless: every disturbance landed after the drawing was already finished,
    so a pen slip cost 0.001 IoU and an ink failure cost exactly nothing. There
    was no drawing left to disturb.

    So the window has to sit inside the drawing phase: late enough that some ink
    is already committed (otherwise the agent simply starts over and nothing is
    being tested), early enough that there is still drawing left to ruin.
    """
    if kind == "mixed":
        kind = _MIX[int(rng.integers(0, len(_MIX)))]
    if kind in (None, "none"):
        return {"kind": "none"}
    lo, hi = max(2, int(0.04 * max_steps)), max(4, int(0.16 * max_steps))
    at = int(rng.integers(lo, hi))
    if kind == "slip":
        # a few mm of unannounced pen displacement, expressed in canvas px
        mag = float(rng.uniform(4.0, 9.0)) * scale
        ang = float(rng.uniform(0, 2 * np.pi))
        return {"kind": kind, "at": at,
                "dcol": mag * np.cos(ang), "drow": mag * np.sin(ang)}
    if kind == "paper_shift":
        mag = float(rng.uniform(5.0, 10.0)) * scale
        ang = float(rng.uniform(0, 2 * np.pi))
        return {"kind": kind, "at": at,
                "dcol": mag * np.cos(ang), "drow": mag * np.sin(ang)}
    if kind == "ink_failure":
        # the blackout is sized against the DRAWING phase (~15% of the episode),
        # not the episode: a 60-step outage on a 40-step drawing erases the whole
        # task rather than testing recovery from it
        dur = int(rng.integers(max(3, int(0.04 * max_steps)),
                               max(6, int(0.12 * max_steps))))
        return {"kind": kind, "at": at, "until": at + dur}
    raise ValueError(kind)


def describe(d):
    if d["kind"] == "none":
        return "none"
    if d["kind"] == "ink_failure":
        return "ink_failure steps %d-%d" % (d["at"], d["until"])
    return "%s at %d by (%.1f, %.1f) px" % (d["kind"], d["at"], d["dcol"], d["drow"])
