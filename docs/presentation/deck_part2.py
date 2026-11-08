"""Deck part 2 - everything completed so far, stage by stage."""
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

from deck_kit import (ACCENT, BAD, BODY, CW, FAINT, GOOD, H, INK, LINE, M, MUTED,
                      NAVY, PRIMARY, SLATE, TINT_AMBER, TINT_BLUE, TINT_GREEN,
                      TINT_RED, TINT_VIOLET, VIOLET, W, WARN, WASH, WASH2, WHITE,
                      arrow, bar_chart, bullets, card, chip, code,
                      decision_slide, elbow, eqn, kpi, legend, node, note, pic,
                      pipeline, qa, rect, section, slide, table, txt)


def build(prs):
    section(prs, 3, "Progress So Far",
            "Every completed stage, in the form the review asks for: what was done, why it "
            "was necessary, what else was considered, why this was chosen, what went wrong, "
            "and what the measurements say.",
            ["Phase A · environment", "Phase B · simulator + vision",
             "Phase C · reinforcement learning", "Results across the task ladder"])

    # ------------------------------------------------- progress at a glance --
    s = slide(prs, "Progress at a glance", "03 · progress",
              "Phases A–C are complete and validated. The first learned drawings exist.")
    phases = [
        ("A", "ENVIRONMENT", "conda env, full RL/vision stack", GOOD, "done"),
        ("B1–B3", "SIMULATOR", "arm + paper + pen-tip readout", GOOD, "done"),
        ("B4", "KINEMATICS", "IK to 0.108 mm, workspace mapped", GOOD, "done"),
        ("B5", "INK", "pen leaves a real, camera-visible mark", GOOD, "done"),
        ("B6", "PERCEPTION", "virtual camera + OpenCV, IoU 0.88", GOOD, "done"),
        ("C1", "TASK + METRICS", "targets, IoU/MSE/chamfer, validated", GOOD, "done"),
        ("C2", "RL ENVIRONMENT", "Gymnasium DrawEnv, check_env passes", GOOD, "done"),
        ("C3", "REWARD DESIGN", "4 formulations, traps found and fixed", GOOD, "done"),
        ("C4", "PPO TRAINING", "4 shapes learned from scratch", GOOD, "done"),
        ("C5", "SAC + VISION REWARD", "H2 / H4 experimental arms", WARN, "next"),
        ("D", "HARDWARE", "physical arm, sim-to-real transfer", MUTED, "planned"),
        ("E", "PAPER", "experiments, figures, submission", MUTED, "planned"),
    ]
    cw4 = (CW - 3 * 0.20) / 4
    for i, (k, t, b, c, st) in enumerate(phases):
        x = M + (i % 4) * (cw4 + 0.20)
        y = 1.66 + (i // 4) * 1.06
        rect(s, x, y, cw4, 0.94, fill=WHITE, line=LINE,
             shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.05)
        rect(s, x, y, 0.05, 0.94, fill=c)
        txt(s, x + 0.18, y + 0.10, 1.3, 0.24, k, size=10, color=c, bold=True)
        txt(s, x + cw4 - 1.1, y + 0.10, 0.95, 0.24, st, size=9, color=c,
            align=PP_ALIGN.RIGHT, italic=True)
        txt(s, x + 0.18, y + 0.36, cw4 - 0.36, 0.26, t, size=12, color=INK, bold=True)
        txt(s, x + 0.18, y + 0.62, cw4 - 0.36, 0.26, b, size=9.5, color=MUTED)

    txt(s, M, 5.06, CW, 0.28, "HEADLINE NUMBERS", size=10.5, color=PRIMARY, bold=True)
    kpis = [("0.108 mm", "worst pen positioning error", PRIMARY, "81-point raster, physics settled"),
            ("0.88", "IoU of camera perception\nvs ground truth", ACCENT, "thin ~1.5 mm stroke recovered"),
            ("0.508", "best learned IoU (line)\nfrom 0.079 untrained", GOOD, "6.4× improvement"),
            ("4 / 4", "shapes learned from scratch", VIOLET, "line, circle, square, triangle"),
            ("~420", "environment steps per second\n(kinematic, CPU)", SLATE, "400k steps ≈ 16 min / shape")]
    kw = (CW - 4 * 0.18) / 5
    for i, (v, l, c, sub) in enumerate(kpis):
        kpi(s, M + i * (kw + 0.18), 5.38, kw, 1.34, v, l, color=c, sub=sub)
    note(s, """
This is the board to leave on screen if the guide wants the summary in thirty
seconds. Green = complete and measured, amber = in flight, grey = planned.

The four headline numbers are the ones to memorise:

0.108 mm - worst pen positioning error over an 81-point raster of the whole
drawing area, with motors driven and physics settled. That is far below the ~1.5 mm
pen width, so kinematics is not the accuracy bottleneck.

0.88 IoU - how well the virtual camera plus OpenCV recovers a drawing compared with
the ground-truth canvas. Anything above ~0.85 on a stroke this thin is strong.

0.508 IoU on the line, up from 0.079 for the untrained policy - the core evidence
that learning happened.

4/4 shapes - the whole first rung of the task ladder was learned, not just one
lucky case.

Be ready for "why is IoU only 0.5?" - answer on the results slide: IoU is brutally
strict for thin strokes, and the largest single cost is a known, fixable start-point
artifact.
""")

    # --------------------------------------------------------- stage A ------
    decision_slide(
        prs, "03 · progress  ·  phase a", "Stage A — development environment",
        "Before any research code: a reproducible, working scientific stack.",
        what=[
            "Fixed the toolchain: Python 3.10 in a dedicated conda environment "
            "named `robosketch`.",
            "Installed PyBullet 3.25, Gymnasium 1.3, Stable-Baselines3 2.9, "
            "PyTorch 2.13, OpenCV 5.0.",
            "Captured it in environment.yml so the setup is one command.",
        ],
        why=[
            "Reproducibility is a research requirement, not a convenience — a "
            "reviewer must be able to recreate the results.",
            "The RL stack pulls PyTorch; deciding late would have meant "
            "re-installing everything mid-experiment.",
        ],
        alternatives=[
            "Plain pip + venv — the obvious default.",
            "Install Microsoft C++ Build Tools and compile PyBullet from source.",
            "Docker / WSL2 Linux container.",
            "Google Colab for everything.",
        ],
        chosen=[
            "pip FAILED: PyBullet publishes no Windows wheel, so pip fell back to a "
            "source build and stopped at 'Microsoft Visual C++ 14.0 or greater is "
            "required'.",
            "conda-forge ships a PREBUILT PyBullet binary — no compiler, no admin "
            "rights, which also matches how scientific robotics stacks are normally "
            "distributed.",
            "Colab rejected: no display for GUI debugging, sessions disconnect, and "
            "it cannot reach a physical Arduino later.",
        ],
        challenges=[
            "A full day lost to the missing PyBullet wheel — the error surfaced as a "
            "C++ compiler error, which hides the real cause.",
            "Conda was already on the machine under a renamed base environment, "
            "which made diagnosis confusing.",
        ],
        result=[
            "Verified working: `import pybullet` → API 202010061, KUKA URDF "
            "available; torch, SB3, OpenCV all import.",
            "environment.yml committed; every run uses "
            "`conda run -n robosketch python …`.",
            "Documented in the log as a reproducibility note for the Methods "
            "section — others hitting the same wall now have the fix.",
        ],
        notes_text="""
This looks like a housekeeping slide, but it earns its place for two reasons.

First, it is a genuine reproducibility finding that belongs in the Methods chapter:
PyBullet has no Windows PyPI wheel, so the standard pip instruction in every
tutorial fails on Windows with a misleading C++ compiler error. Anyone trying to
reproduce this work on Windows will hit it. We document the conda-forge fix.

Second, it demonstrates a decision principle used throughout the project: when
blocked, enumerate the options, choose on stated criteria, and record why. Here the
criteria were: no admin rights needed, no compiler, and a stack that matches how
scientific binaries are normally shipped.

If asked why not Docker or WSL2: they would work, but they add a layer between the
code and the USB serial port we will need for the physical arm later, and they are
a heavier barrier for someone reproducing the work.
""")

    # ------------------------------------------------------ stage B1-B3 -----
    decision_slide(
        prs, "03 · progress  ·  phase b", "Stage B1–B3 — the simulated world",
        "A robot arm, a sheet of paper, and a way to know exactly where the pen is.",
        what=[
            "Loaded a KUKA iiwa 7-DOF arm and a ground plane in PyBullet; added "
            "per-joint sliders and a live pen-tip (x, y, z) readout.",
            "Built sim/viewer.py: DPI-aware window, tidy panels, clean shutdown.",
            "Later added sim/05_interactive_draw.py — a hands-on sandbox where a "
            "human drives the pen and real ink appears.",
        ],
        why=[
            "Everything downstream — IK, ink, camera, reward — needs a trustworthy "
            "world and a trustworthy pen position first.",
            "A visual sandbox makes silent geometry bugs obvious; a number that "
            "looks fine can still be the wrong point in space.",
        ],
        alternatives=[
            "Gazebo — the ROS standard for robot simulation.",
            "MuJoCo — fastest contacts, common in recent RL papers.",
            "Isaac Sim — GPU-accelerated, photorealistic.",
            "Build a custom 6-DOF URDF of the target hardware immediately.",
        ],
        chosen=[
            "PyBullet: runs natively on Windows (Gazebo effectively needs Linux + "
            "ROS), steps fast headless — which is what millions of RL steps need — "
            "and is pure Python with no ROS dependency.",
            "KUKA iiwa is bundled and has well-tested IK, so the drawing engine could "
            "be built without simultaneously debugging a custom URDF: two hard things "
            "at once is how projects stall.",
            "MuJoCo recorded as the escape hatch if throughput ever binds; the "
            "bottleneck here is reward design, not physics speed.",
        ],
        challenges=[
            "The window was blurry: Windows 11 runs at 125–150 % scaling and "
            "PyBullet's OpenGL window is not DPI-aware, so Windows upscaled it. "
            "Fixed with SetProcessDpiAwareness(2) before connecting.",
            "Closing the window mid-frame raised pybullet.error; every script now "
            "exits cleanly.",
            "PyBullet's debug GUI chops the first character off every label — a "
            "library-side cosmetic bug; irrelevant because training is headless.",
        ],
        result=[
            "Arm loads, 7 sliders work, live pen-tip readout confirmed visually.",
            "Interactive sandbox validated headless: a mocked diagonal stroke gave "
            "3,664 inked pixels with row/col correlation −0.90 — the correct "
            "orientation.",
            "Simulator choice recorded with rationale for the Methods section; the "
            "swap to a hardware-matched URDF is a one-file change.",
        ],
        notes_text="""
The important content here is the simulator choice, because a guide may well ask
"why not Gazebo, everyone uses ROS?"

Answer on three grounds. Platform: Gazebo effectively requires Linux or WSL2 plus
ROS, and our development and future Arduino hardware are on Windows. Throughput:
Gazebo is built for full-system realism, not for stepping an environment millions
of times; PyBullet steps fast headless. Complexity: our arm is a servo arm driven
over serial - we do not need the ROS ecosystem, and adding it would add a large
dependency for no scientific gain.

MuJoCo is the strongest genuine alternative and we say so openly. We did not switch
because the setup is already validated to 0.1 mm and the project bottleneck is
reward design and perception, not contact physics. It is recorded as the escape
hatch if training throughput ever becomes the limit.

Why the KUKA and not the real arm model from day one: to avoid debugging a custom
URDF and the drawing engine at the same time. Because the agent acts in pen space,
the arm is nearly interchangeable - only the URDF and the IK call change.
""")

    # ------------------------------------------------ B4 - the four bugs ----
    s = slide(prs, "Stage B4 — inverse kinematics: four silent failures",
              "03 · progress  ·  phase b",
              "Naive IK 'worked' and was wrong by centimetres. Each fault was found by measurement, not by inspection.")
    probs = [
        ("1", "MEASURING THE WRONG POINT",
         "getLinkState(link)[0] returns the link's CENTRE OF MASS, not the link "
         "frame that IK actually targets.",
         "Constant ~20 mm bias at every target: we asked for z = 0.020 and read "
         "z = 0.0002.",
         "Use index 4 — worldLinkFramePosition.", BAD),
        ("2", "IK CONFIGURATION",
         "Position-only IK reached the point but left the pen slanted at 41° — "
         "useless for drawing. Null-space hints looked helpful.",
         "Null-space limits/ranges/restPoses degraded accuracy ~400×, from "
         "0.007 mm to 2.835 mm.",
         "Pass targetOrientation (pen vertical); do NOT pass null-space hints.", BAD),
        ("3", "UNREACHABLE WORKSPACE",
         "Plain IK ignores joint limits, so it happily returns poses the arm "
         "cannot physically adopt.",
         "Joint 3 driven ~13° past its limit; the pen landed ~70 mm off and no "
         "amount of settling fixed it — structural, not lag.",
         "Map the true reachable area and constrain the paper to it.", WARN),
        ("4", "THE WRIST HITS THE FLOOR",
         "Asking the wrist's own frame to sit 2 cm above the ground fails — the "
         "link is a solid body resting on the floor.",
         "28–35 mm error with the pen down, but pen-up worked — which is exactly "
         "what isolated the cause.",
         "Model a virtual pen: a 0.10 m rod below the wrist.", WARN),
    ]
    cw2 = (CW - 0.26) / 2
    for i, (n, t, cause, evid, fix, c) in enumerate(probs):
        x = M + (i % 2) * (cw2 + 0.26)
        y = 1.86 + (i // 2) * 2.46
        rect(s, x, y, cw2, 2.28, fill=WHITE, line=LINE,
             shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.04)
        rect(s, x, y, cw2, 0.40, fill=c, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.10)
        rect(s, x, y + 0.22, cw2, 0.18, fill=c)
        txt(s, x + 0.18, y + 0.07, 0.4, 0.26, n, size=11.5, color=WHITE, bold=True)
        txt(s, x + 0.56, y + 0.07, cw2 - 0.7, 0.26, t, size=11.5, color=WHITE, bold=True)
        txt(s, x + 0.20, y + 0.50, cw2 - 0.4, 0.5, cause, size=10.5, color=BODY,
            spacing=1.15)
        rect(s, x + 0.20, y + 1.06, cw2 - 0.4, 0.62, fill=WASH, line=None,
             shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.06)
        txt(s, x + 0.32, y + 1.10, 1.1, 0.22, "EVIDENCE", size=8.5, color=MUTED,
            bold=True)
        txt(s, x + 0.32, y + 1.30, cw2 - 0.64, 0.4, evid, size=10, color=BODY,
            spacing=1.12)
        txt(s, x + 0.20, y + 1.78, 0.55, 0.24, "FIX", size=9, color=GOOD, bold=True)
        txt(s, x + 0.72, y + 1.76, cw2 - 0.92, 0.44, fix, size=10.5, color=GOOD,
            spacing=1.12)
    note(s, """
This is the slide that shows research method rather than coding. Every one of these
four faults produced a system that LOOKED like it worked.

Problem 1 is the most instructive. PyBullet's getLinkState returns a tuple; index 0
is the centre of mass and index 4 is the link frame. Inverse kinematics targets the
link frame. Reading index 0 gave a constant 20 mm bias - and constant biases are
exactly the kind of error you rationalise away. We caught it because we asked for
z = 0.020 and read back z = 0.0002; that is not noise, that is the wrong quantity.

Problem 2 is counter-intuitive and worth telling as a story: PyBullet's null-space
arguments look like the "proper" way to respect joint limits, and every example
passes them. Measured over six targets they made accuracy about 400 times worse.
The lesson - measure the configuration you actually use, do not trust the example
code.

Problem 3 is the difference between LAG and STRUCTURAL error. If the error falls
when you allow more settling time, it is lag. If it does not, the pose is physically
unattainable. Joint 3 was being driven 13 degrees past its limit.

Problem 4 was diagnosed by a differential observation - pen-up worked, pen-down did
not - which pointed straight at floor contact. The fix, modelling a virtual pen, is
also more faithful to the real robot, which will genuinely hold a pen.
""")

    # ------------------------------------ B4 - measurements + workspace -----
    s = slide(prs, "Stage B4 — measured, not assumed", "03 · progress  ·  phase b")
    txt(s, M, 1.46, 6.1, 0.28, "IK CONFIGURATION — MEASURED OVER 6 TARGETS", size=10.5,
        color=PRIMARY, bold=True)
    table(s, ["IK variant", "mean position error", "pen tilt", ""],
          [["position only, plain", "0.003 mm", "41°", "unusable"],
           ["position only + null-space", "0.911 mm", "41°", "unusable"],
           ["position + orientation, plain", "0.007 mm", "0.00°", "CHOSEN"],
           ["position + orientation + null-space", "2.835 mm", "0.06°", "400× worse"]],
          M, 1.78, 6.1, colw=[2.5, 1.5, 0.9, 1.2], size=10, row_h=0.42,
          cell_colors={(0, 3): BAD, (1, 3): BAD, (2, 3): GOOD, (3, 3): BAD})
    txt(s, M, 3.72, 6.1, 0.6,
        "A 41° pen tilt still 'reaches' the target — the position error is tiny. It is simply "
        "useless for drawing, which is why orientation must be constrained.",
        size=10.5, color=MUTED, italic=True, spacing=1.15)

    txt(s, M, 4.36, 6.1, 0.28, "FINAL VALIDATED PERFORMANCE", size=10.5, color=GOOD,
        bold=True)
    txt(s, M, 4.62, 6.1, 0.3,
        "81-point serpentine raster of the whole drawing box · motors driven · physics settled",
        size=9.5, color=MUTED, italic=True)
    res = [("0.108", "worst pen-down position\nerror  (mm)"), ("0.001°", "pen tilt"),
           ("0.000°", "joint-limit\novershoot"), ("0", "points worse\nthan 1 mm")]
    rw = (6.1 - 3 * 0.14) / 4
    for i, (v, l) in enumerate(res):
        kpi(s, M + i * (rw + 0.14), 4.94, rw, 1.16, v, l, color=GOOD, fill=WHITE)
    txt(s, M, 6.20, 6.1, 0.55,
        "Pen-up transitions: 0.107 mm at 60 settle steps → 0.011 mm at ≥120. The apparent "
        "1.5 mm pen-up error was settling LAG, not a limit — proved by sweeping settle steps.",
        size=10, color=BODY, spacing=1.15)

    # workspace map
    mx, my = M + 6.45, 1.46
    txt(s, mx, my, CW - 6.45, 0.28, "REACHABLE WORKSPACE — MAPPED EXPERIMENTALLY",
        size=10.5, color=ACCENT, bold=True)
    px0, py0, pw, ph = mx + 0.32, my + 0.46, 4.85, 2.72
    # world x: 0.00 -> 0.75 m across;  world y: +0.30 (top) -> -0.30 (bottom)
    def wx(v):
        return px0 + v / 0.75 * pw
    def wy(v):
        return py0 + (0.30 - v) / 0.60 * ph
    rect(s, px0, py0, pw, ph, fill=WHITE, line=LINE, lw=0.75)
    # zones
    rect(s, wx(0.0), py0, wx(0.35) - wx(0.0), ph, fill=TINT_RED, line=None)
    rect(s, wx(0.45), py0, wx(0.75) - wx(0.45), ph, fill=TINT_GREEN, line=None)
    txt(s, wx(0.02), py0 + 0.20, 1.35, 0.6, "UNREACHABLE\nx ≤ 0.35 m\n(arm cannot fold\nthat close)",
        size=8.5, color=BAD, bold=True, spacing=1.15)
    txt(s, wx(0.455), py0 + 0.06, 1.9, 0.3, "SUB-MILLIMETRE ZONE  x ≥ 0.45 m",
        size=8.5, color=GOOD, bold=True)
    # adopted box + paper
    rect(s, wx(0.45), wy(0.20), wx(0.65) - wx(0.45), wy(-0.20) - wy(0.20),
         fill=None, line=PRIMARY, lw=1.8)
    rect(s, wx(0.45), wy(0.10), wx(0.65) - wx(0.45), wy(-0.10) - wy(0.10),
         fill=WASH2, line=ACCENT, lw=1.0)
    txt(s, wx(0.455), wy(0.03), 1.5, 0.28, "paper 20×20 cm", size=8.5, color=ACCENT,
        bold=True, align=PP_ALIGN.CENTER)
    txt(s, wx(0.44), wy(-0.215), 2.4, 0.28, "adopted drawing box — 20 × 40 cm",
        size=8.5, color=PRIMARY, bold=True)
    # base + axes
    rect(s, wx(0.0) - 0.055, wy(0.0) - 0.055, 0.11, 0.11, fill=SLATE,
         shape=MSO_SHAPE.OVAL)
    txt(s, wx(0.0) - 0.30, wy(0.0) + 0.09, 0.75, 0.24, "base", size=8.5, color=SLATE,
        align=PP_ALIGN.CENTER, bold=True)
    arrow(s, px0, py0 + ph + 0.10, px0 + pw, py0 + ph + 0.10, color=FAINT, lw=1.0)
    txt(s, px0, py0 + ph + 0.16, pw, 0.24, "world +x  (metres from the base)   0.00 → 0.75",
        size=8.5, color=MUTED)
    txt(s, mx + 0.15, py0 + ph + 0.52, 5.1, 0.72,
        "Adopted box: x ∈ [0.45, 0.65] m, y ∈ [−0.20, 0.20] m. Mapped by COMMANDING the motors "
        "and letting physics settle — never with resetJointState, which teleports joints, "
        "ignores joint limits and silently over-reports accuracy. Surface height barely matters "
        "inside the safe zone, so the paper can rest on the ground plane.",
        size=10, color=BODY, spacing=1.15)
    note(s, """
Two things to communicate here: the numbers, and the methodology that produced them.

The IK table is a genuine experimental comparison over six targets. The row to point
at is the last one - adding the null-space hints, which every tutorial passes, made
the error 400 times worse. We use position + orientation with no null-space hints.

The 41-degree pen tilt row makes an important point: position error alone is a
misleading metric. The pen reached the right point while pointing sideways. You must
measure the quantity you actually care about.

The workspace map was produced experimentally, not from the datasheet. Below about
x = 0.35 m the arm cannot fold tightly enough toward its own base; joint 3 gets
driven past its limit. From x = 0.45 m outward we measured sub-millimetre accuracy
across the full y range, so we adopted a 20 cm x 40 cm safe box and put the 20 cm
paper inside it.

The methodological point at the bottom is the one to stress: we validate through
setJointMotorControl2 plus settled physics, never resetJointState. resetJointState
teleports the joints and silently ignores joint limits, so it reports an accuracy
the real arm could never achieve. That distinction is what makes the 0.108 mm figure
trustworthy.
""")

    # -------------------------------------------------------- B5 ink --------
    s = slide(prs, "Stage B5 — the pen leaves a mark", "03 · progress  ·  phase b",
              "Two objects, one drawing: the numpy canvas is the DATA; the textured paper is only a picture of it.")
    node(s, M, 1.80, 5.0, 1.42, "THE CANVAS  (numpy array)",
         "A 512×512 image we paint into. It is the authoritative drawing:\n"
         "saved to disk, scored by the reward, compared to the target.",
         color=GOOD, fill=WASH, title_size=13, sub_size=10.5)
    node(s, M + 7.17, 1.80, 5.0, 1.42, "THE PAPER  (textured mesh)",
         "A flat quad in the 3D world wearing the canvas as a texture.\n"
         "It exists so a human — and the camera — can SEE the stroke.",
         color=ACCENT, fill=WASH, title_size=13, sub_size=10.5)
    arrow(s, M + 5.06, 2.51, M + 7.11, 2.51, color=SLATE, lw=1.6,
          label="uploaded every 20 points", label_dy=-0.30, label_w=2.4)
    rect(s, M, 3.42, CW, 0.62, fill=WASH2, line=None,
         shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.05)
    txt(s, M + 0.22, 3.53, CW - 0.5, 0.45,
        "Consequence for training: for headless RL we never render ink through PyBullet at all — "
        "we maintain the numpy canvas directly. Texture reload goes through disk and is far too "
        "slow for millions of steps. The camera path is applied only in the H2 vision condition.",
        size=11, color=INK, spacing=1.16, bold=True)

    txt(s, M, 4.24, CW, 0.28, "WHY THE INK IS A TEXTURE AND NOT A DEBUG LINE  —  measured",
        size=10.5, color=PRIMARY, bold=True)
    boxes = [
        ("p.addUserDebugLine", "A stroke drawn this way changed 0 pixels in a rendered "
         "camera image — it is a viewer-only overlay. It would have looked perfect on "
         "screen while being completely invisible to the reward function.", BAD),
        ("Ink at the ACTUAL pen position", "Ink is deposited where the pen really is, "
         "not where it was commanded. Worst tracking deviation while drawing: 2.8 mm "
         "(line), 4.8 mm (square) — visible as rounded corners.", GOOD),
        ("Real arms cut corners too", "That lag is a genuine system dynamic the agent "
         "must learn around, not an error to hide. It is tunable via settle steps and "
         "maxVelocity if a sharper trace is wanted.", VIOLET),
    ]
    cw3 = (CW - 0.44) / 3
    for i, (t, b, c) in enumerate(boxes):
        card(s, M + i * (cw3 + 0.22), 4.56, cw3, 1.52, t, b, accent=c, body_size=10.5)
    note(s, """
The canvas-versus-paper separation is the central architectural idea of this stage,
and it pays off twice.

The canvas is a numpy array - the actual data. The paper is a textured mesh whose
only job is to be visible. Keeping them separate means that for fast headless
training we can skip the 3D rendering entirely and just maintain the array, which is
what makes 420 steps per second possible.

The debug-line finding is worth telling as a cautionary tale. PyBullet's
addUserDebugLine is the obvious way to draw a stroke, and it looks perfect in the
GUI. We measured it: a stroke drawn that way changed exactly zero pixels in a
rendered camera image, because it is a viewer overlay, not scene geometry. Had we
built on it, the whole vision pipeline would have scored a blank sheet - and we
would have discovered that only much later, in the RL phase.

The third point is a design decision people often get wrong: we ink at the pen's
measured position, not its commanded position. The motors lag by a few millimetres
during continuous motion. Recording the truth means the agent is scored on what it
actually drew, so it learns to compensate for its own dynamics. Real arms cut
corners too, so this is realism, not sloppiness.
""")

    # -------------------------------------------- B5 traps + results --------
    s = slide(prs, "Stage B5 — three traps that would have corrupted every result",
              "03 · progress  ·  phase b")
    traps = [
        ("GEOM_BOX does not UV-map a texture",
         "A texture painted with four coloured quadrants rendered on a box's top face "
         "as ONE flat colour — the face samples only a tiny uniform patch of the image.",
         "Symptoms that wasted hours: an all-black canvas 'worked'; a centred X "
         "'worked' by luck; a top-half fill did nothing at all.",
         "The paper became a mesh quad with explicit UVs (assets/paper_quad.obj). "
         "Verified: all four quadrants render at ~25 % each."),
        ("p.changeTexture is a no-op in this build",
         "Measured 0 / 4 on every probe — in DIRECT and GUI, with both TinyRenderer "
         "and the hardware renderer.",
         "Reloading the texture from a PNG (loadTexture + changeVisualShape) updates "
         "reliably: 4 / 4.",
         "refresh_paper() writes to disk and reloads, every 20 pen points."),
        ("The world→pixel mapping was transposed",
         "The first version mapped world x → image row and y → column. Left unchecked, "
         "EVERY drawing would have been mirrored — and the reward would have scored a "
         "mirrored image against the target.",
         "Verified against physics: ink painted at a world point vs a reference sphere "
         "placed at the same point, on all four edges, agreeing within ~3 px.",
         "col = (x − x_min)/width × (RES−1)   ·   row = (y_max − y)/height × (RES−1)"),
    ]
    for i, (t, a, b, fix) in enumerate(traps):
        y = 1.56 + i * 1.62
        rect(s, M, y, CW, 1.46, fill=WHITE, line=LINE,
             shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.04)
        rect(s, M, y, 0.05, 1.46, fill=BAD)
        txt(s, M + 0.22, y + 0.12, 5.0, 0.3, t, size=12, color=INK, bold=True)
        txt(s, M + 0.22, y + 0.44, 5.0, 0.9, a, size=10.5, color=BODY, spacing=1.16)
        txt(s, M + 5.45, y + 0.14, 3.3, 0.24, "EVIDENCE", size=8.5, color=MUTED,
            bold=True)
        txt(s, M + 5.45, y + 0.38, 3.3, 1.0, b, size=10, color=BODY, spacing=1.15)
        txt(s, M + 8.95, y + 0.14, 3.1, 0.24, "FIX", size=8.5, color=GOOD, bold=True)
        txt(s, M + 8.95, y + 0.38, 3.1, 1.0, fix, size=10, color=GOOD, spacing=1.15,
            font="Consolas" if i == 2 else None)
    rect(s, M, 6.42, CW, 0.46, fill=WASH2, line=None,
         shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.05)
    txt(s, M + 0.22, 6.50, CW - 0.5, 0.32,
        "Common thread: all three produced a system that looked right. Only a measurement "
        "against an independent reference exposed them.",
        size=11, color=INK, bold=True)
    note(s, """
Keep the tone factual here - these are findings, not confessions. Each is a genuine
contribution to reproducibility, because none of them appears in the documentation
or tutorials.

Trap 1: a PyBullet GEOM_BOX does not map a texture across its faces the way you
expect; the top face samples a tiny uniform patch. This sent us down a long false
trail because some test patterns coincidentally appeared to work. The fix was to
make the paper a mesh quad with explicit UV coordinates, then verify all four
quadrants of a test texture render at 25 percent each.

Trap 2: changeTexture, the documented fast path for updating a texture, is simply a
no-op in this build - zero out of four probes, in every renderer combination. So we
reload from a PNG file instead. A related bug bit us later: loadTexture caches by
filename, so reusing a filename silently returns the first version. That froze the
photographed paper at an early frame. We now write a unique filename every refresh.

Trap 3 is the most dangerous because it is invisible: the world-to-pixel mapping was
transposed. Every drawing would have been mirrored, and the reward would have scored
a mirrored image against the target - so the agent would have learned to draw
backwards, and nothing would have looked obviously wrong. We fixed it by validating
against physics: paint ink at a world point, place a reference sphere at the same
point, and check they land within about 3 pixels of each other on all four edges.
""")

    # ------------------------------------------------- B5 results figure ----
    s = slide(prs, "Stage B5 — validated results", "03 · progress  ·  phase b",
              "Every drawing checked against expected geometry, not just eyeballed.")
    pic(s, "fig_b5_drawings.png", 0, 0, center_in=(M, 1.62, CW, 3.05))
    table(s, ["shape", "pen points", "inked px", "geometry check", "verdict"],
          [["line", "241", "2,492", "rows 252–259 (pen width); cols 74–430 vs expected "
                                    "77–434; mean row 255.1 vs 256", "pass"],
           ["square", "484", "8,451", "centre hollow (0 px inside); spans 314 × 313 px "
                                      "— square to 1 px", "pass"]],
          M, 4.92, CW, colw=[1.0, 1.1, 1.1, 7.2, 1.0], size=10.5, row_h=0.46,
          cell_colors={(0, 4): GOOD, (1, 4): GOOD})
    txt(s, M, 6.28, CW, 0.6,
        "Note the deliberate separation that paid off: validate_b5 checks the saved CANVAS array, "
        "not the rendered paper — which is exactly why it kept passing while the texture was "
        "silently stale. A green test only covers what it actually inspects.",
        size=11, color=BODY, spacing=1.18, italic=True)
    note(s, """
Point out that "it looks like a line" is not a result. For the line we checked that
the inked rows span 252 to 259 - eight pixels, which is the pen width - and that the
columns span 74 to 430 against an expected 77 to 434, with a mean row of 255.1
against a geometric centre of 256. For the square we checked the centre is completely
hollow and the spans are 314 by 313 pixels, square to within one pixel.

The closing note is a genuinely useful testing lesson. Our B5 validation inspects the
saved canvas array. When the texture-caching bug froze the rendered paper, the test
kept passing - correctly, because the canvas really was fine. The bug lived in the
rendering path, which that test does not cover. Good separation of concerns hid the
bug until the camera needed it in B6. Worth saying plainly: a passing test tells you
about the thing it inspects, and nothing else.
""")

    # ----------------------------------------------------- B6 pipeline -----
    s = slide(prs, "Stage B6 — the robot sees its own drawing", "03 · progress  ·  phase b",
              "Closes the architecture loop: robot draws → camera captures → OpenCV extracts → IoU scores.")
    pic(s, "fig_vision_pipeline.png", 0, 0, center_in=(M, 1.62, CW, 2.72))
    steps = [("PARK THE ARM", "straight up over the base,\n0 arm pixels in frame"),
             ("CAPTURE", "top-down virtual camera,\n480×480 RGB + segmentation"),
             ("ISOLATE PAPER", "segmentation mask → crop;\noff-paper forced to white"),
             ("THRESHOLD", "greyscale, fixed cut at 128,\nbinary inverse"),
             ("COMPARE", "resize to canvas res,\nIoU vs ground truth")]
    pipeline(s, steps, M, 4.52, CW, 0.98,
             colors=[PRIMARY, ACCENT, ACCENT, ACCENT, GOOD])
    txt(s, M, 5.72, CW, 0.28, "ORIENTATION — CALIBRATED, NOT ASSUMED", size=10.5,
        color=PRIMARY, bold=True)
    rect(s, M, 6.00, CW, 0.72, fill=WASH, line=LINE,
         shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.05)
    txt(s, M + 0.22, 6.10, CW - 0.5, 0.55,
        "We painted an asymmetric marker, captured it, and tested all EIGHT dihedral transforms "
        "(4 rotations × mirror) of the perceived image against the known canvas. rot0 won at "
        "IoU 0.998; the next best scored 0.68. So the camera up-vector [0, 1, 0] already matches "
        "the canvas convention — no correction needed, and now we can prove it.",
        size=11, color=BODY, spacing=1.18)
    note(s, """
This stage closes the loop in the architecture diagram: the robot can now perceive
its own output. Today it validates the pipeline; in the H2 experiment it becomes the
reward source; on real hardware it will be the only source of truth.

Walk the four panels left to right - raw camera frame, OpenCV extraction, the
ground-truth canvas, and the overlay showing agreement.

The orientation calibration is the part to emphasise as method. Rather than assuming
the camera image is aligned with our canvas convention, we painted an asymmetric
marker and tested all eight dihedral transforms - four rotations times an optional
mirror. The identity transform scored 0.998 IoU and the runner-up scored 0.68. That
gap is decisive: we can now assert alignment with evidence instead of hoping. The
same procedure will be needed, and will be reused, when a real camera looks at real
paper.
""")

    # ------------------------------------------------ B6 problems + result --
    s = slide(prs, "Stage B6 — three problems, and the results", "03 · progress  ·  phase b")
    ps = [("THE ARM OCCLUDES THE PAPER",
           "A top-down camera looks straight through the arm, which after drawing is bent "
           "over the sheet. First capture: arm filled the frame, paper ~40 % visible, "
           "perceived ink ≈ 0.",
           "Park the arm before the photo. Measured several poses; straight up over the "
           "base gives 100 % paper visible and 0 arm pixels. Real drawing rigs do the same.",
           BAD),
          ("OTSU THRESHOLD FOOLED BY THE ARM",
           "With the dark arm in frame, Otsu's method split arm-versus-paper and "
           "classified the thin stroke as background — the stroke is a tiny minority of "
           "pixels, so it loses.",
           "With the arm parked, a FIXED threshold at 128 on paper-masked pixels is "
           "robust in this controlled white-paper / black-ink scene.",
           WARN),
          ("loadTexture CACHES BY FILENAME  (the big one)",
           "The paper texture was frozen at an early frame: the camera saw only a fragment "
           "of the drawing even though the saved canvas was perfect. refresh_paper reused "
           "two filenames.",
           "Proved directly: rewriting one filename with 5 % / 30 % / 60 % black kept the "
           "camera at 5 % (dark = 5865 constant); unique filenames tracked correctly "
           "(5865 → 35535 → 71415). Fix: a unique filename every call.",
           BAD)]
    for i, (t, a, b, c) in enumerate(ps):
        y = 1.52 + i * 1.30
        rect(s, M, y, CW, 1.16, fill=WHITE, line=LINE,
             shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.04)
        rect(s, M, y, 0.05, 1.16, fill=c)
        txt(s, M + 0.22, y + 0.12, 3.5, 0.5, t, size=11.5, color=INK, bold=True,
            spacing=1.1)
        txt(s, M + 3.90, y + 0.13, 4.0, 0.94, a, size=10, color=BODY, spacing=1.15)
        txt(s, M + 8.10, y + 0.13, CW - 8.3, 0.94, b, size=10, color=GOOD, spacing=1.15)

    txt(s, M, 5.50, 7.0, 0.28, "VALIDATED PERCEPTION RESULTS  (headless, asserted)",
        size=10.5, color=PRIMARY, bold=True)
    table(s, ["shape", "perceived px", "ground-truth px", "area ratio", "IoU"],
          [["line", "2,861", "2,492", "1.15", "0.871"],
           ["square", "9,582", "8,451", "1.13", "0.882"]],
          M, 5.80, 7.0, colw=[1.2, 1.6, 1.8, 1.2, 1.2], size=10.5, row_h=0.36,
          cell_colors={(0, 4): GOOD, (1, 4): GOOD})
    card(s, M + 7.3, 5.50, CW - 7.3, 1.36, "READING THE NUMBERS",
         "Perceived strokes are ~14 % thicker than ground truth — camera and texture "
         "filtering widen a thin line. IoU 0.87–0.88 is strong for recovering a ~1.5 mm "
         "stroke; the overlay is almost entirely agreement.",
         accent=ACCENT, body_size=10)
    note(s, """
Three problems, each caught by measurement.

Occlusion: obvious in hindsight, invisible until you look at the frame. A top-down
camera sees the arm, not the paper. We park the arm straight up over its base, far
from the paper, and measured that this leaves 100 percent of the paper visible with
zero arm pixels. Real drawing rigs do exactly this - shoot between strokes, or mount
the camera clear of the arm.

Otsu: a nice illustration of an algorithm being used outside its assumptions. Otsu
finds the threshold that best separates two pixel populations. With the dark arm in
frame the two dominant populations are arm and paper, so the thin stroke - a tiny
minority - gets classified as background. Once the arm is parked, a fixed threshold
is both simpler and more robust in this controlled scene. On real hardware, with
uneven lighting, we will revisit this and likely use adaptive thresholding.

The texture cache was the expensive one. loadTexture caches by file path, so
rewriting the same filename returns the stale first version. We proved it with a
controlled probe - write 5, 30 and 60 percent black to the same filename and watch
the dark-pixel count stay constant at 5865, then repeat with unique filenames and
watch it track. Note also the earlier log entry we later superseded: an initial
reading suggested changeTexture worked, but that probe counted dark pixels over the
whole frame instead of the paper only. We corrected the record. Keeping that
correction visible is part of doing this honestly.
""")

    # ------------------------------------------------- C1 targets/metrics ---
    decision_slide(
        prs, "03 · progress  ·  phase c", "Stage C1 — the task and how it is scored",
        "rl/targets.py and rl/metrics.py — what to draw, and what 'close' means.",
        what=[
            "targets.py: line, circle, square and triangle as binary masks in canvas "
            "pixel space, plus canvas_to_mask() so a drawing lands in the same "
            "convention.",
            "metrics.py: IoU, MSE, coverage, precision and chamfer distance, with a "
            "summary() that returns all five.",
        ],
        why=[
            "The reward function and the evaluation must use ONE definition of "
            "accuracy — otherwise you optimise one thing and report another.",
            "Targets must live in the same pixel space as the drawing, so a perfect "
            "trace overlaps the target exactly.",
        ],
        alternatives=[
            "Score in continuous space: distance from the pen path to a parametric "
            "curve.",
            "Compare rendered vector paths rather than rasters.",
            "Use a single metric (IoU) and nothing else.",
        ],
        chosen=[
            "Raster masks generalise to ANY target — including handwritten digits and "
            "letters later, which have no parametric form.",
            "IoU is the headline metric because it penalises both misses and stray "
            "ink; chamfer is kept as a softer companion that still rewards a stroke "
            "that is close but not overlapping.",
            "Multiple metrics guard against optimising an artefact of one score.",
        ],
        challenges=[
            "Choosing the target stroke width: a 1–2 px target is punishing — one "
            "pixel of drift collapses IoU. Set to 14 px, narrowing later as a "
            "difficulty step.",
            "Defining edge cases: IoU of two empty masks is 1.0 (nothing to draw, "
            "nothing drawn); chamfer of one empty mask is infinite.",
        ],
        result=[
            "Validated against hand-computed cases: identical → IoU 1, MSE 0, "
            "chamfer 0; disjoint → IoU 0; HALF-OVERLAP → IoU exactly 1/3 "
            "(measured 0.333).",
            "Chamfer verified monotonic: near < far. Coverage monotonic in overlap.",
            "All assertions pass — the scorer is trustworthy before anything depends "
            "on it.",
        ],
        notes_text="""
The half-overlap test is the one to quote if challenged on rigour. If two identical
shapes overlap by exactly half, the intersection is half of one shape and the union
is one and a half, so IoU must be exactly one third. We measured 0.333. That is a
closed-form check, not a smoke test - the metric is provably correct before anything
depends on it.

Why raster masks rather than comparing to a parametric curve: because the task ladder
ends in handwritten digits and letters, which have no clean parametric form. A raster
representation is uniform across the whole curriculum, and it is also exactly what a
camera gives us - which keeps the ground-truth and vision conditions comparable.

Why several metrics: IoU is strict and penalises both missing the target and inking
where you should not. Chamfer is softer - it rewards a stroke that is close but not
overlapping, which distinguishes "nearly right" from "completely wrong" in a way IoU
cannot. Coverage and precision decompose IoU into recall-like and precision-like
parts, which is what let us diagnose the scribble failure mode later.

The 14-pixel stroke width was a deliberate choice, and it is honest to flag it as a
limitation: a wider target makes the task learnable. Narrowing it is the natural next
difficulty step.
""")

    # ------------------------------------------------------ C2 DrawEnv -----
    decision_slide(
        prs, "03 · progress  ·  phase c", "Stage C2 — the reinforcement-learning environment",
        "rl/draw_env.py — DrawEnv, a Gymnasium environment. The heart of the project.",
        what=[
            "A standard Gymnasium environment with reset() and step(action).",
            "State: a 64×64×3 image — target, drawn-so-far, pen-position marker.",
            "Action: [dx, dy, pen_down], continuous, in PEN space.",
            "Two interchangeable backends: kinematic (fast) and full IK + physics.",
        ],
        why=[
            "Gymnasium is the standard interface, so any RL library — Stable-"
            "Baselines3, RLlib, CleanRL — can drive it without modification.",
            "A clean interface is what makes the H2, H3 and H4 comparisons a change "
            "of one argument rather than a rewrite.",
        ],
        alternatives=[
            "Joint-space actions (7 joint deltas) — arm-specific.",
            "A low-dimensional vector state (pen x, y + a few features) instead of "
            "an image.",
            "Absolute pen targets instead of relative nudges.",
            "Always run the full physics backend.",
        ],
        chosen=[
            "Pen-space actions make the policy portable across arms; the arm-specific "
            "part is confined to IK. This is also H3, so it must be a choice we can "
            "flip.",
            "An image state carries the target and the partial drawing without "
            "hand-designed features, and it generalises to letters later.",
            "Relative nudges suit IK, which is seeded from the current pose — small "
            "continuous steps track far better than jumps (measured in B4).",
            "The dual backend lets us iterate fast and then verify under real "
            "dynamics; drawing and reward logic are IDENTICAL in both.",
        ],
        challenges=[
            "Image observations mean a CNN policy and much slower learning than a "
            "vector state would give.",
            "The full-physics backend runs one environment only (single PyBullet "
            "client), so vectorised training uses the kinematic backend.",
            "Getting the observation to carry pen state: the pen marker is drawn at "
            "255 when down and 128 when up, so one channel encodes both.",
        ],
        result=[
            "Stable-Baselines3 check_env passes; the environment is deterministic "
            "under a fixed seed.",
            "Sanity-checked against two references: a contour-tracing ORACLE beats "
            "random by a wide margin on all four shapes (line: +1.5 vs −26), and an "
            "idle policy draws nothing.",
            "Both backends run end to end.",
        ],
        notes_text="""
DrawEnv is the single most important file in the project, so be ready to defend
every choice on this slide.

Pen-space versus joint-space is the headline decision. The agent says "move the pen
1 cm this way"; inverse kinematics turns that into joint angles. Everything
arm-specific lives in the URDF and the IK call, so swapping to the real 6-DOF arm
does not invalidate the learned policy. It is also hypothesis H3, so the environment
must support both - and it does.

Why an image state rather than a small vector: the target has to be part of the
state, or the policy could only ever learn one shape. An image carries the target,
the partial drawing and the pen position with no hand-designed features, and the
same representation will work for letters. The cost is honest: a CNN policy learns
more slowly than an MLP on a vector state would.

Why relative nudges: B4 measured that IK is seeded from the arm's current pose, so
small continuous steps track far better than large jumps. Forcing a reseed to a fixed
home pose made accuracy worse - 1.55 mm versus 0.009 mm. Drawing naturally moves in
small steps, so the action space matches the physics.

The validation deserves a mention. check_env passing only proves the interface is
legal. What proves the environment is meaningful is the oracle test: a scripted
contour-tracer scores about +1.5 on the line where a random policy scores about -26,
and an idle policy draws nothing. That confirms the reward actually rewards drawing
the shape - before any training time is spent.
""")

    # ---------------------------------------------------- C3 reward design --
    s = slide(prs, "Stage C3 — reward design: four iterations, four failure modes",
              "03 · progress  ·  phase c",
              "Each run 300–400k PPO steps. Every failure was a genuine local optimum, and each fix is a documented design decision.")
    table(s, ["#", "reward design", "result  (IoU / coverage)", "what the agent actually did", "diagnosis"],
          [["1", "coverage − stray − time", "0.06 → 0.14  /  0.91",
            "SCRIBBLE — covered the line by scrawling a blob over the whole region",
            "stray penalty too weak; coverage is gameable"],
           ["2", "IoU-delta + proximity shaping", "0.06 → 0.12  /  0.43",
            "CENTRAL BLOB — covered the easy middle, would not risk extending to the ends",
            "no incentive to reach the far, low-density ends"],
           ["3", "+ thicker target, finer control, done-bonus", "0.09 → 0.30  /  0.89",
            "ZIGZAG — swept the FULL line, but wobbled vertically",
            "pen wider than target + no smoothness cost"],
           ["4", "+ matched pen width + action-smoothness penalty", "0.08 → 0.508  /  0.87",
            "RECOGNISABLE LINE — mild blob at the fixed start point",
            "accepted; start-point artefact is the next fix"]],
          M, 1.94, CW, colw=[0.4, 3.0, 2.0, 4.0, 2.8], size=10, row_h=0.72,
          header_h=0.36, bold_col0=True,
          cell_colors={(3, 2): GOOD, (2, 2): WARN})

    txt(s, M, 5.10, CW, 0.28, "TWO LOCAL OPTIMA THAT ARE WORTH THE PAPER ON THEIR OWN",
        size=10.5, color=PRIMARY, bold=True)
    lo = [("THE 'DRAW NOTHING' TRAP",
           "With a coverage-only reward plus stray and time penalties, random exploration "
           "almost never hits a thin target — so the safe optimum is pen_down = 0. Reward "
           "improves, IoU stays 0.",
           "FIX  dense potential-based proximity shaping (pulls the pen toward the target "
           "without changing the optimal policy) + pen_always_down for the first rung.", BAD),
          ("THE 'DON'T MOVE' TRAP",
           "With the pen always down, freezing it (dx≈dy≈0) inks nothing and dodges every "
           "stray penalty. Reward was climbing (−7.9 → −4.6) — converging to freeze.",
           "FIX  rebalance so coverage dominates: cover_bonus 1→3, stray 0.5→0.2, "
           "time→0. Coverage then rose 0.06 → 0.21 in 60k steps.", WARN)]
    cw2 = (CW - 0.26) / 2
    for i, (t, a, f, c) in enumerate(lo):
        x = M + i * (cw2 + 0.26)
        rect(s, x, 5.40, cw2, 1.42, fill=WHITE, line=LINE,
             shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.04)
        rect(s, x, 5.40, 0.05, 1.42, fill=c)
        txt(s, x + 0.20, 5.50, cw2 - 0.4, 0.26, t, size=11, color=c, bold=True)
        txt(s, x + 0.20, 5.78, cw2 - 0.4, 0.62, a, size=10, color=BODY, spacing=1.15)
        txt(s, x + 0.20, 6.46, cw2 - 0.4, 0.32, f, size=10, color=GOOD, spacing=1.15)
    note(s, """
This is the richest research content in the deck so far, and it maps directly to
research question 4.

The story is a sequence, and each step has a named failure mode:

Design 1, a coverage-based reward, produced a SCRIBBLE. Coverage only asks "did you
ink over the target", so scrawling a blob across the whole region scores well. The
structural fix was switching to IoU-delta: stray ink lowers IoU, so scribbling is now
self-penalising. That single change removed the scribble optimum by construction, not
by tuning.

Design 2 produced a CENTRAL BLOB - it covered the easy middle and would not risk the
ends.

Design 3 swept the full line but ZIGZAGGED, because the pen was wider than the target
and nothing penalised wobble.

Design 4 added a matched pen width and an action-smoothness penalty and produced a
recognisable line at IoU 0.508.

The two local optima at the bottom are classic sparse-reward traps and we hit both.
"Draw nothing" is the sparse-reward problem in its purest form: with a thin target,
random exploration almost never scores, so not drawing is safest. The fix - dense
potential-based shaping - is principled rather than a hack, and section 7 shows why:
Ng's theorem says potential-based shaping does not change the optimal policy.

One tuning lesson worth quoting: the smoothness penalty must be scaled to the reward.
At 0.15 it accumulated to -24 over 240 steps and swamped the IoU signal, so the agent
just minimised motion. At 0.02 it contributes about -3, comparable to the IoU term,
and it straightened the stroke.
""")

    # --------------------------------------------------- C4 final results ---
    s = slide(prs, "Stage C4 — the whole task ladder, learned", "03 · progress  ·  phase c",
              "PPO · CnnPolicy · 400k steps per shape · ground-truth (baseline) reward · kinematic backend.")
    pic(s, "fig_montage.png", 0, 0, center_in=(M, 1.66, 7.15, 2.60))
    table(s, ["shape", "IoU untrained", "IoU trained", "×", "coverage", "model"],
          [["line", "0.079", "0.508", "6.4×", "0.87", "ppo_line_kin.zip"],
           ["circle", "0.000", "0.443", "—", "0.93", "ppo_circle_kin.zip"],
           ["square", "0.000", "0.493", "—", "0.80", "ppo_square_kin.zip"],
           ["triangle", "0.000", "0.421", "—", "0.71", "ppo_triangle_kin.zip"]],
          M, 4.46, 7.15, colw=[1.1, 1.3, 1.2, 0.6, 1.1, 1.9], size=10, row_h=0.34,
          header_h=0.34,
          cell_colors={(0, 2): GOOD, (1, 2): GOOD, (2, 2): GOOD, (3, 2): GOOD})
    bar_chart(s, M + 7.42, 1.66, CW - 7.42, 2.85,
              ["line", "circle", "square", "triangle"],
              [("untrained", (0.079, 0.0, 0.0, 0.0)),
               ("trained (400k steps)", (0.508, 0.443, 0.493, 0.421))],
              colors=[FAINT, GOOD], title="Final IoU vs target", max_scale=0.6)
    card(s, M + 7.42, 4.64, CW - 7.42, 2.12, "READING THESE RESULTS",
         ["All four are clearly recognisable: the circle closes, the square has four "
          "corners, the triangle has an apex.",
          "IoU 0.42–0.51 is a solid first-pass baseline for continuous-control drawing "
          "on a thin stroke — not a ceiling.",
          "Progression was monotone and interpretable: nothing → central blob → "
          "full-width sweep → smoother trace. That IS the learning-curve evidence for H1.",
          "Common artefact: a stray 'tail' from the paper centre to the shape — the pen "
          "starts at the centre with pen_always_down, so it inks while travelling. "
          "Biggest single remaining IoU cost, and cleanly fixable."],
         accent=GOOD)
    txt(s, M, 6.94, 7.15, 0.28,
        "Renders: output/trained_<shape>_kin_after.png  ·  models/ppo_<shape>_kin.zip",
        size=9, color=MUTED, italic=True)
    note(s, """
This is the core proof-of-concept for the thesis: the arm learned to draw through
trial and error, not by replaying a scripted trajectory. That is the evidence for
H1 in simulation.

Expect the question "why is IoU only about 0.5 - is that good?" Three points.

First, IoU on a thin stroke is brutally strict. Two parallel strokes offset by one
stroke width score zero, even though a human would say they match. It is the right
metric precisely because it is unforgiving, but the absolute number needs that
context.

Second, the largest single cost is a known artefact, not a learning failure. The pen
starts at the paper centre with the pen always down, so it inks a tail while
travelling to the shape. Every shape shows it. Fixing it - start lifted, or start on
the shape - is the very next experiment and should lift IoU noticeably.

Third, and most important, the shape of the progression is the evidence, not the
absolute number. It went from drawing nothing, to a central blob, to a full-width
sweep, to a recognisable trace. That monotone, interpretable improvement is what
distinguishes learning from luck.

Be precise about what this does and does not show: it is the ground-truth-reward
BASELINE, in simulation, with PPO, on the kinematic backend. The vision reward, SAC,
and hardware are all still ahead.
""")

    # ------------------------------------------------- progress summary -----
    s = slide(prs, "What is proven, and what is not", "03 · progress",
              "Being precise about the strength of each claim is what separates a result from a demo.")
    cols = [("ESTABLISHED  —  measured evidence", GOOD, [
        "A simulated arm positions a pen to 0.108 mm across the whole drawing area.",
        "The drawing engine deposits ink at the pen's true position and is "
        "geometry-verified.",
        "A virtual camera + OpenCV recovers the drawing at IoU 0.87–0.88.",
        "The scoring metrics are correct against closed-form cases.",
        "A Gymnasium environment implements the drawing MDP and passes check_env.",
        "PPO learns all four ladder shapes from scratch — 0.42–0.51 IoU, up from ~0.",
        "Four reward designs compared, with named failure modes and fixes.",
    ]), ("NOT YET ESTABLISHED  —  open work", WARN, [
        "That a VISION reward matches a ground-truth reward  (H2 — control group "
        "built, experiment not run).",
        "That PPO is the better algorithm here  (H4 — SAC not yet trained).",
        "That the policy survives transfer to real hardware  (H3 — no physical arm "
        "yet).",
        "That pen-space actions transfer better than joint-space  (H3).",
        "Anything about handwriting, digits or letters  (later ladder rungs).",
        "Robustness to lighting, paper shift, pen wear  (real-world conditions).",
        "Comparison against a scripted IK baseline on equal terms  (planned).",
    ])]
    cw2 = (CW - 0.30) / 2
    for i, (t, c, items) in enumerate(cols):
        x = M + i * (cw2 + 0.30)
        rect(s, x, 1.66, cw2, 4.62, fill=WHITE, line=LINE,
             shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.04)
        rect(s, x, 1.66, cw2, 0.44, fill=c, shape=MSO_SHAPE.ROUNDED_RECTANGLE,
             radius=0.10)
        rect(s, x, 1.92, cw2, 0.18, fill=c)
        txt(s, x + 0.22, 1.74, cw2 - 0.44, 0.3, t, size=12, color=WHITE, bold=True)
        bullets(s, items, x + 0.22, 2.26, cw2 - 0.46, 3.9, size=11, bullet_color=c)
    rect(s, M, 6.44, CW, 0.48, fill=WASH2, line=None,
         shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.05)
    txt(s, M + 0.22, 6.53, CW - 0.5, 0.32,
        "Everything in the left column is reproducible from the repository today: "
        "`conda run -n robosketch python rl/train.py --shape circle --timesteps 400000`.",
        size=11, color=INK, bold=True)
    note(s, """
Volunteering the limits before being asked is the strongest move available in a
review. It signals that you know the difference between evidence and expectation,
and it takes the sting out of the questions that were coming anyway.

Left column: every item is backed by a measurement recorded in the research log, and
every one is reproducible from the repository today.

Right column: none of these are claimed. H2 has its control group built but the
experiment has not been run. H4 needs SAC. H3 needs hardware that does not exist yet.
Letters and digits are later rungs of the ladder. Robustness to real lighting and
paper shift is entirely untested, because there is no real camera yet.

If asked "so what is the single biggest risk?", the honest answer is the sim-to-real
gap: everything so far lives in a simulator where the pen is perfect and the paper
never moves. The mitigation is architectural - pen-space actions and a vision-based
reward are precisely the choices that make transfer plausible - but it is a
mitigation, not a result.
""")
