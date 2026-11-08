"""Deck part 5 - development timeline and future roadmap."""
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN

from deck_kit import (ACCENT, BAD, BODY, CW, FAINT, FM, GOOD, H, INK, LINE, M,
                      MUTED, NAVY, PRIMARY, SLATE, TINT_AMBER, TINT_BLUE,
                      TINT_GREEN, TINT_RED, TINT_VIOLET, VIOLET, W, WARN, WASH,
                      WASH2, WHITE, arrow, bullets, card, chip, code,
                      decision_slide, elbow, eqn, kpi, legend, node, note, pic,
                      pipeline, qa, rect, section, slide, table, txt)


def build(prs):
    # =================================================== SECTION 9 =========
    section(prs, 9, "Development Timeline",
            "How the work actually proceeded — from the first line of research through the "
            "simulator, the perception loop and the first learned drawings.",
            ["The timeline", "The working method",
             "What each phase produced"])

    # --------------------------------------------------- 9.1 timeline -----
    s = slide(prs, "Development timeline", "09 · timeline",
              "Foundations → simulator → perception → reinforcement learning. Nothing was built before the thing beneath it was verified.")
    lanes = [
        ("PHASE A · foundations", PRIMARY, 0.0, 0.14,
         ["problem framing, literature scoping",
          "conda environment (PyBullet blocker resolved)",
          "14-part conceptual learning book"]),
        ("PHASE B · simulator", ACCENT, 0.10, 0.52,
         ["B1–B3  arm + paper + pen-tip readout",
          "B4  inverse kinematics → 0.108 mm; workspace mapped",
          "B5  ink deposition; canvas vs paper architecture",
          "B6  virtual camera + OpenCV → IoU 0.88"]),
        ("PHASE C · reinforcement learning", GOOD, 0.55, 0.94,
         ["C1  targets + metrics (validated closed-form)",
          "C2  DrawEnv — the Gymnasium environment",
          "C3  reward design: 4 iterations, 2 local optima",
          "C4  PPO trains all four ladder shapes"]),
        ("PHASE D · experiments & hardware", WARN, 0.96, 1.0,
         ["SAC · vision reward · hardware · paper  (ahead)"]),
    ]
    tx, tw = M + 2.85, CW - 3.0
    txt(s, tx, 1.50, tw, 0.26, "23 JUL 2026", size=9, color=MUTED, bold=True)
    txt(s, tx + tw - 2.0, 1.50, 2.0, 0.26, "6 AUG 2026  ·  today", size=9, color=MUTED,
        bold=True, align=PP_ALIGN.RIGHT)
    rect(s, tx, 1.76, tw, 0.02, fill=LINE)
    for i, (name, c, t0, t1, items) in enumerate(lanes):
        y = 1.92 + i * 1.31
        h = 0.40 + 0.205 * len(items)
        rect(s, M, y, 2.65, h, fill=WASH, line=None,
             shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.06)
        rect(s, M, y, 0.05, h, fill=c)
        txt(s, M + 0.20, y + 0.12, 2.35, 0.5, name, size=11, color=c, bold=True,
            spacing=1.05)
        bx = tx + t0 * tw
        bw = max(0.5, (t1 - t0) * tw)
        rect(s, bx, y, bw, 0.34, fill=c, shape=MSO_SHAPE.ROUNDED_RECTANGLE,
             radius=0.28)
        conv = [{"t": "·  " + it, "size": 9.5, "color": BODY, "space_after": 1}
                for it in items]
        txt(s, tx + 0.05, y + 0.40, tw - 0.1, h - 0.42, conv, spacing=1.08)
    txt(s, M, 6.62, CW, 0.3,
        "Two weeks of concentrated work, and roughly half of it went into finding and proving "
        "four classes of silent failure. That is normal, and it is why the research log exists.",
        size=11, color=MUTED, italic=True)
    note(s, """
Be honest about the shape of this timeline. It is not "two weeks of coding" - it is
two weeks in which roughly half the effort went into discovering that things which
appeared to work did not.

The ordering is the point worth defending: nothing was built on top of something
unverified. Inverse kinematics was measured to 0.108 mm before ink was added. Ink was
geometry-checked before the camera looked at it. The camera pipeline was calibrated
before the reward could depend on it. The metrics were validated against closed-form
answers before any training time was spent.

If asked why Phase C moved so much faster than Phase B: because Phase B had already
established a trustworthy foundation. Once the drawing engine and metrics were
verified, building the environment and running the first PPO experiments took a day.
That is the return on the earlier caution.
""")

    # ------------------------------------------------ 9.2 working method ---
    s = slide(prs, "The working method", "09 · timeline",
              "The same loop was applied at every milestone. It is what turned engineering into evidence.")
    steps = [("DECIDE", "Write the decision down\nWITH the alternatives\nand the criteria", PRIMARY),
             ("BUILD", "Implement the smallest\nthing that could\npossibly work", ACCENT),
             ("MEASURE", "Compare against an\nINDEPENDENT reference,\nnot against intuition", GOOD),
             ("DIAGNOSE", "Change one variable\nto separate lag from\nstructural error", WARN),
             ("RECORD", "Log the number, the\nfix, and the lesson\nin RESEARCH_LOG.md", VIOLET)]
    bw = (CW - 4 * 0.30) / 5
    for i, (t, sb, c) in enumerate(steps):
        x = M + i * (bw + 0.30)
        node(s, x, 1.70, bw, 1.30, t, sb, color=c, fill=WHITE, title_size=12.5,
             sub_size=9.5)
        if i < 4:
            arrow(s, x + bw + 0.04, 2.35, x + bw + 0.26, 2.35, color=SLATE, lw=1.4)
    elbow(s, [(M + 4 * (bw + 0.30) + bw / 2, 3.04), (M + 4 * (bw + 0.30) + bw / 2, 3.26),
              (M + bw / 2, 3.26), (M + bw / 2, 3.06)], color=VIOLET, lw=1.4, dashed=True)

    txt(s, M, 3.50, CW, 0.28, "WHAT THAT LOOP ACTUALLY CAUGHT", size=10.5,
        color=PRIMARY, bold=True)
    caught = [
        ("~20 mm", "constant IK bias", "reading the centre of mass instead of the link frame", BAD),
        ("400×", "IK accuracy loss", "null-space hints that every tutorial recommends", BAD),
        ("0 px", "ink visible to the camera", "debug lines are viewer-only overlays", BAD),
        ("100 %", "flat texture on a box face", "GEOM_BOX does not UV-map across faces", BAD),
        ("stale", "frozen paper texture", "loadTexture caches by filename", BAD),
        ("mirrored", "every drawing", "the world→pixel mapping was transposed", BAD),
    ]
    cw3 = (CW - 0.44) / 3
    for i, (v, l, why, c) in enumerate(caught):
        x = M + (i % 3) * (cw3 + 0.22)
        y = 3.82 + (i // 3) * 1.00
        rect(s, x, y, cw3, 0.88, fill=WHITE, line=LINE,
             shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.04)
        rect(s, x, y, 0.05, 0.88, fill=c)
        txt(s, x + 0.20, y + 0.08, 1.5, 0.3, v, size=14, color=c, bold=True)
        txt(s, x + 1.75, y + 0.13, cw3 - 1.95, 0.24, l, size=10, color=INK, bold=True)
        txt(s, x + 0.20, y + 0.46, cw3 - 0.4, 0.36, why, size=9.5, color=MUTED,
            spacing=1.1)
    rect(s, M, 5.92, CW, 0.86, fill=WASH2, line=None,
         shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.05)
    txt(s, M + 0.26, 6.04, CW - 0.55, 0.66,
        "Not one of these six would have been found by reading the code, watching a demo, or "
        "looking at a screenshot. Each was found by comparing a component against something "
        "that could contradict it. This is the difference between a project that appears to "
        "work and one whose numbers can be trusted.",
        size=11.5, color=INK, bold=True, spacing=1.2)
    note(s, """
This slide answers a question that is rarely asked directly but is always being
assessed: does this student have a method, or are they just coding until it looks
right?

The loop is: decide with the alternatives written down, build the smallest thing that
could work, measure against an INDEPENDENT reference, diagnose by changing one
variable at a time, then record the number and the lesson.

The diagnose step deserves a sentence: the recurring technique was separating lag from
structural error. If an error shrinks when you allow more settling time, it is lag. If
it does not, the pose is physically unattainable. That one distinction resolved both
the pen-up accuracy question and the joint-limit problem.

The six numbers in the middle are the return on that method. Each represents a system
that looked correct and was not. Together they are also a genuine contribution to
reproducibility, because none of them is documented anywhere else.
""")

    # ================================================== SECTION 10 =========
    section(prs, 10, "Future Roadmap",
            "What comes next, in the order it will be done: finish the experimental arms in "
            "simulation, then hardware, then the harder task rungs, then the paper.",
            ["Immediate next steps", "The experiment matrix", "Hardware integration",
             "Sim-to-real transfer", "Digits & handwriting", "Publication"])

    # ------------------------------------------------- 10.1 next steps -----
    s = slide(prs, "Immediate next steps", "10 · roadmap",
              "Ordered by scientific value per unit of effort. The first four are days, not weeks.")
    nxt = [
        ("N1", "Fix the start-point artefact", "days",
         "Start the pen LIFTED and approach the shape pen-up, or start on the shape. The "
         "stray tail from the paper centre is the single biggest remaining IoU cost across "
         "all four shapes.",
         "Expected: a clear IoU lift on every shape, for almost no work.", GOOD),
        ("N2", "Train SAC under an identical budget", "days",
         "Same environment, same reward, same 400k steps, 3 seeds each. SAC is off-policy "
         "with a replay buffer, so it should be markedly more sample-efficient.",
         "Answers H4 / RQ3 — the algorithm comparison.", VIOLET),
        ("N3", "Switch the reward to the VISION path", "1–2 weeks",
         "Replace metrics.iou(canvas, target) with metrics.iou(perceived, target), where "
         "'perceived' comes from the camera + OpenCV pipeline already built and validated in "
         "B6. The agent then learns from what it SEES.",
         "Answers H2 / RQ2 — the central research question. Cost: the camera path is far "
         "slower, so this needs a reduced capture rate or a cached render.", ACCENT),
        ("N4", "Add the scripted IK baseline", "days",
         "Run the B5 trajectory drawer over the same targets and score it with the same "
         "metrics.",
         "Gives the non-learning control the whole study is measured against.", PRIMARY),
        ("N5", "Multi-seed runs + learning curves", "days",
         "3–5 seeds per condition with logged episode returns, so results carry variance "
         "bars instead of single numbers.",
         "Turns 'it worked' into 'it works reliably' — a reviewer requirement.", SLATE),
        ("N6", "Physics-backend verification", "1 week",
         "Re-run the trained policies with use_arm=True so they face real IK, motor lag and "
         "settling.",
         "Quantifies the kinematic→dynamic gap BEFORE adding the hardware gap on top.", WARN),
    ]
    for i, (k, t, eff, what, why, c) in enumerate(nxt):
        y = 1.56 + i * 0.90
        rect(s, M, y, CW, 0.82, fill=WHITE, line=LINE,
             shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.04)
        rect(s, M, y, 0.05, 0.82, fill=c)
        chip(s, M + 0.16, y + 0.10, 0.42, 0.26, k, color=c, fill=WASH, size=9.5)
        txt(s, M + 0.16, y + 0.44, 2.5, 0.3, t, size=11, color=INK, bold=True,
            spacing=1.05)
        chip(s, M + 2.85, y + 0.10, 0.85, 0.26, eff, color=MUTED, fill=WASH, size=8.5)
        txt(s, M + 3.90, y + 0.08, 4.6, 0.68, what, size=9.5, color=BODY, spacing=1.14)
        txt(s, M + 8.70, y + 0.10, CW - 8.9, 0.64, why, size=9.5, color=c, spacing=1.14,
            bold=True)
    note(s, """
The ordering here is deliberate and worth explaining: cheapest and most informative
first.

N1 is almost free and should visibly improve every result we have shown. Every trained
drawing carries a stray tail from the paper centre because the pen starts there with
the pen always down. Starting lifted, or starting on the shape, removes it.

N3 is the scientifically central one - it is the actual H2 experiment. Emphasise how
little code it requires: the perception pipeline already exists and is validated, so
the change is which image the reward reads. The real cost is computational, because
rendering a camera frame per step is far slower than reading a numpy array. We will
likely score from the camera every N steps rather than every step.

N5 is the one a reviewer will insist on. Right now every number is a single run.
Multi-seed results with variance are the difference between an anecdote and a result.

N6 is a subtlety worth flagging: we currently train on the kinematic backend. Before
blaming any future hardware gap on the hardware, we should measure how much of it
appears simply from moving to full IK and motor dynamics inside the simulator.
""")

    # ------------------------------------------ 10.2 experiment matrix -----
    s = slide(prs, "The planned experiment matrix", "10 · roadmap",
              "Every cell is one training run. Only one variable changes per comparison — which is what makes each claim causal.")
    table(s, ["experiment", "hypothesis", "condition A (control)", "condition B (treatment)",
              "measured by", "status"],
          [["Learning vs scripting", "H1 / RQ1", "scripted IK trajectory drawer",
            "trained PPO policy", "IoU, MSE, chamfer, success rate", "A pending, B done"],
           ["Reward source", "H2 / RQ2", "ground-truth canvas reward",
            "camera + OpenCV vision reward", "final IoU, sample efficiency", "next"],
           ["Algorithm", "H4 / RQ3", "PPO", "SAC",
            "learning curves, final IoU, variance over seeds", "PPO done"],
           ["Reward formulation", "RQ4", "coverage-based reward",
            "IoU-delta + potential shaping", "IoU, time-to-threshold, failure modes",
            "done — 4 designs"],
           ["Action space", "H3 / RQ5", "pen (task) space + IK", "joint space (Δθ)",
            "IoU(sim) − IoU(real), transfer drop", "planned"],
           ["Task difficulty", "RQ6", "14 px target stroke", "narrowed stroke, then digits "
            "and letters", "IoU vs stroke width; per-shape accuracy", "baseline done"],
           ["Embodiment fidelity", "—", "kinematic backend", "full IK + physics backend",
            "IoU drop; contribution of motor lag", "planned"],
           ["Sim-to-real", "H1 / H3", "policy in simulation", "same policy on the physical arm",
            "IoU on photographed real drawings", "planned"]],
          M, 1.90, CW, colw=[2.0, 1.2, 2.6, 2.6, 2.6, 1.6], size=9.5, row_h=0.53,
          header_h=0.36, bold_col0=True,
          cell_colors={(1, 5): WARN, (2, 5): GOOD, (3, 5): GOOD, (4, 5): MUTED,
                       (5, 5): GOOD, (6, 5): MUTED, (7, 5): MUTED, (0, 5): WARN})
    rect(s, M, 6.34, CW, 0.52, fill=WASH2, line=None,
         shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.05)
    txt(s, M + 0.24, 6.44, CW - 0.5, 0.36,
        "Every run: 3–5 seeds, identical step budget, identical evaluation protocol "
        "(5 deterministic episodes on fixed seeds). Results reported as mean ± std, never as "
        "a single number.",
        size=11, color=INK, bold=True)
    note(s, """
This is the experimental design, and it is what turns a collection of runs into a
study.

The organising principle is one variable per comparison. In the reward-source row, the
environment, the algorithm, the budget and the evaluation are all identical - only the
image the reward reads changes. That is what licenses a causal claim about the reward
source rather than a vague observation that one run went better.

The bottom bar is the protocol commitment, and it is the thing most student projects
omit. Three to five seeds, identical budgets, identical evaluation, and results
reported with variance. Without it, a difference between two runs could easily be
seed noise.

If asked how long all this takes: a 400k-step run is about 16 minutes on CPU, so a
condition with 5 seeds is under two hours. The vision-reward runs are the expensive
ones because of rendering; the hardware runs are limited by physical time, not compute.
""")

    # ------------------------------------------------- 10.3 hardware -------
    s = slide(prs, "Hardware integration", "10 · roadmap",
              "A sub-Rs.10,000 arm, deliberately chosen so the study is reproducible by any student lab.")
    txt(s, M, 1.46, 6.1, 0.28, "THE PLANNED BUILD", size=10.5, color=PRIMARY, bold=True)
    table(s, ["component", "plan", "why"],
          [["arm", "6-DOF hobby manipulator", "6 DOF is the classic minimum to place a "
            "pen at any position AND orientation"],
           ["actuators", "MG996R-class servos", "cheap, strong enough, and take a "
            "'go to this angle' command directly"],
           ["controller", "Arduino over USB serial", "simple, deterministic, no ROS "
            "needed for a servo arm"],
           ["end effector", "spring-loaded pen holder", "compliance absorbs height error "
            "so the pen keeps contact without crushing"],
           ["camera", "USB webcam on a fixed mount", "the real counterpart of the "
            "virtual camera; must be clear of the arm"],
           ["surface", "fixed paper on a rigid board", "removes one variable while the "
            "transfer is being established"]],
          M, 1.78, 6.1, colw=[1.4, 2.0, 3.4], size=9.5, row_h=0.52, header_h=0.32)
    card(s, M, 5.28, 6.1, 1.54, "WHAT THE SOFTWARE HAS TO GAIN",
         ["A URDF matching the real arm's link lengths and joint limits — measured, not "
          "guessed.",
          "A serial driver: joint angles (radians) → servo microsecond commands, with "
          "calibration offsets per joint.",
          "Camera calibration: intrinsics, plus a homography from the four paper corners.",
          "A safety layer: joint-limit clamping, velocity limits, and an emergency stop."],
         accent=WARN)

    rx = M + 6.45
    txt(s, rx, 1.46, CW - 6.45, 0.28, "WHAT ARCHITECTURE ALREADY GIVES US", size=10.5,
        color=GOOD, bold=True)
    ready = [
        ("The policy does not change", "It emits a pen-space nudge. Nothing in the network "
         "knows about the KUKA. That was the point of the pen-space decision in B4.", GOOD),
        ("The reward does not change", "IoU against a target mask, computed on a camera "
         "image — identical mathematics, a real camera instead of a virtual one.", GOOD),
        ("The vision pipeline mostly holds", "Crop → greyscale → threshold → resize → "
         "binarise survives. Finding the paper and correcting perspective are the new "
         "parts.", ACCENT),
        ("The workspace method transfers", "The same experimental procedure — command the "
         "motors, let it settle, measure — maps the real arm's reachable box.", ACCENT),
        ("What genuinely must change", "URDF, the IK target link, the serial driver, "
         "camera calibration, and tolerance for backlash and non-repeatability.", WARN),
    ]
    for i, (t, b, c) in enumerate(ready):
        y = 1.78 + i * 1.02
        rect(s, rx, y, CW - 6.45, 0.94, fill=WHITE, line=LINE,
             shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.04)
        rect(s, rx, y, 0.05, 0.94, fill=c)
        txt(s, rx + 0.20, y + 0.09, CW - 6.9, 0.26, t, size=10.5, color=c, bold=True)
        txt(s, rx + 0.20, y + 0.35, CW - 6.9, 0.55, b, size=9.5, color=BODY,
            spacing=1.14)
    note(s, """
Two messages here. First, the concrete build. Second - and more important for a design
review - how much of the software is already hardware-ready by construction.

On the hardware: a 6-DOF hobby arm with MG996R-class servos driven by an Arduino over
USB serial. No ROS, because a servo arm does not need it and adding it would be a large
dependency for no scientific gain. The spring-loaded pen holder is worth calling out as
a mechanical solution to a control problem: rather than demanding millimetre-accurate
height control, compliance absorbs the error and keeps the pen in contact.

On the software: the policy itself does not change at all, because it speaks pen space.
The reward does not change, because it is IoU on a camera image either way. The vision
pipeline mostly holds - what is new is finding the paper without a segmentation buffer
and correcting for a camera that is not perfectly perpendicular.

Be candid about what is genuinely hard: hobby servos have backlash and are not
repeatable. That is not a software problem, and it is the single biggest threat to
transfer. The mitigations are the vision-based reward, which closes the loop on the
result rather than the command, and domain randomisation during training.
""")

    # ----------------------------------------------- 10.4 sim-to-real ------
    s = slide(prs, "Sim-to-real — the transfer strategy", "10 · roadmap",
              "The single biggest risk in the project, and the four things we are doing about it before it bites.")
    txt(s, M, 1.50, CW, 0.28, "WHERE THE GAP COMES FROM", size=10.5, color=BAD,
        bold=True)
    gaps = [("Actuation", "servo backlash, non-repeatability,\nload-dependent droop", BAD),
            ("Geometry", "link lengths and joint zeros differ\nfrom the URDF", BAD),
            ("Contact", "real pen pressure, paper friction,\nink flow", WARN),
            ("Perception", "lighting, shadows, perspective,\nsensor noise", WARN),
            ("Timing", "serial latency and finite servo speed\nvs instant sim steps", WARN)]
    bw = (CW - 4 * 0.22) / 5
    for i, (t, b, c) in enumerate(gaps):
        node(s, M + i * (bw + 0.22), 1.82, bw, 1.02, t, b, color=c, fill=WHITE,
             title_size=11, sub_size=9)
    txt(s, M, 3.10, CW, 0.28, "THE FOUR MITIGATIONS — three are already built in",
        size=10.5, color=GOOD, bold=True)
    mits = [
        ("1", "PEN-SPACE ACTIONS", "already built",
         "The policy never learned the KUKA's joint geometry, so the largest single source "
         "of arm-specific overfitting is absent by construction. Swapping arms swaps the URDF "
         "and the IK call. This is also hypothesis H3 — we will MEASURE the benefit, not "
         "assume it.", GOOD),
        ("2", "VISION-BASED REWARD", "pipeline built",
         "A policy that judges its drawing from a camera is judging the same quantity in sim "
         "and on hardware. A ground-truth reward has no real-world counterpart at all — you "
         "cannot query a physical arm for perfect pen coordinates.", GOOD),
        ("3", "MEASURED, CONSTRAINED WORKSPACE", "already built",
         "Everything happens inside an experimentally verified reachable box, so the policy "
         "never learns to rely on poses near a limit or a singularity — exactly where a real "
         "arm behaves worst.", GOOD),
        ("4", "DOMAIN RANDOMISATION", "planned",
         "Randomise link lengths, servo backlash, motor gains, paper position, lighting and "
         "camera pose during training, so the policy must be robust to a FAMILY of arms "
         "rather than fitting one. The standard, well-evidenced answer to the sim-to-real "
         "gap.", WARN),
    ]
    cw2 = (CW - 0.28) / 2
    for i, (n, t, st, b, c) in enumerate(mits):
        x = M + (i % 2) * (cw2 + 0.28)
        y = 3.42 + (i // 2) * 1.72
        rect(s, x, y, cw2, 1.56, fill=WHITE, line=LINE,
             shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.04)
        rect(s, x, y, 0.05, 1.56, fill=c)
        chip(s, x + 0.18, y + 0.12, 0.34, 0.28, n, color=c, fill=WASH, size=10)
        txt(s, x + 0.62, y + 0.13, 3.0, 0.28, t, size=11, color=c, bold=True)
        chip(s, x + cw2 - 1.35, y + 0.12, 1.15, 0.28, st, color=MUTED, fill=WASH,
             size=8.5)
        txt(s, x + 0.20, y + 0.52, cw2 - 0.4, 0.94, b, size=9.5, color=BODY,
            spacing=1.16)
    note(s, """
Open by naming this as the biggest risk in the project. A guide will respect that more
than confidence.

The five sources of the gap are worth enumerating because they have different
characters. Actuation and geometry are systematic - they can be measured and modelled.
Contact and perception are stochastic and much harder. Timing is a real one people
forget: in simulation a step is instantaneous, while a real servo takes tens of
milliseconds and the serial link adds latency.

The key point about the mitigations is that three of the four are already built in.
That was not luck - pen-space actions, a vision-based reward and a constrained
workspace were all chosen in Phase B specifically because of transfer.

Mitigation 2 has the sharpest argument. A ground-truth reward has NO real-world
counterpart: you cannot ask a physical arm for perfect pen coordinates. So a
vision-based reward is not merely an interesting research variant - it is the only
version of the reward that can exist on hardware. That is why H2 is the central
question rather than a side experiment.

Domain randomisation is the planned addition and is the standard answer in the
literature. Train across a distribution of arms, and the real arm becomes just another
sample from that distribution.
""")

    # ------------------------------------------- 10.5 harder tasks ---------
    s = slide(prs, "Extending the task ladder — digits, letters, handwriting",
              "10 · roadmap")
    rungs = [("LINE", "done · IoU 0.51", GOOD), ("CIRCLE", "done · IoU 0.44", GOOD),
             ("SQUARE", "done · IoU 0.49", GOOD), ("TRIANGLE", "done · IoU 0.42", GOOD),
             ("THIN STROKE", "narrow the target", WARN),
             ("DIGITS 0–9", "multi-stroke", WARN),
             ("LETTERS", "curves + strokes", MUTED),
             ("HANDWRITING", "style + sequence", MUTED)]
    bw = (CW - 7 * 0.14) / 8
    for i, (t, sb, c) in enumerate(rungs):
        node(s, M + i * (bw + 0.14), 1.62, bw, 0.88, t, sb, color=c, fill=WHITE,
             title_size=10, sub_size=8.5)
        if i < 7:
            arrow(s, M + i * (bw + 0.14) + bw + 0.015, 2.06,
                  M + (i + 1) * (bw + 0.14) - 0.015, 2.06, color=FAINT, lw=1.1)
    txt(s, M, 2.62, CW, 0.28, "WHAT EACH NEW RUNG ACTUALLY REQUIRES", size=10.5,
        color=PRIMARY, bold=True)
    reqs = [
        ("Narrowing the stroke", "Pure difficulty scaling — no new machinery. Measures how "
         "IoU degrades with target width, which is a clean, publishable curve and a direct "
         "answer to RQ6 ('where does accuracy break down?').", ACCENT),
        ("Multi-stroke shapes (digits)", "The pen-up/pen-down decision becomes REAL. "
         "pen_always_down is switched off, so the action's third dimension starts to matter "
         "and the exploration problem gets harder — the agent must learn WHEN not to draw.",
         VIOLET),
        ("A target that varies per episode", "Today one policy is trained per shape. For "
         "digits the target must be sampled at reset, so the policy has to CONDITION on the "
         "target channel rather than memorise one shape. This is the real test of the "
         "image-observation design.", PRIMARY),
        ("Letters and handwriting", "Longer episodes, curved strokes, and stroke ORDER "
         "matters. Likely needs a longer horizon, possibly a hierarchical policy (choose a "
         "stroke, then execute it), and MNIST-style raster targets as the source of shapes.",
         WARN),
        ("Evaluation for handwriting", "IoU alone becomes insufficient — a legible 'a' in a "
         "slightly different style scores poorly. Chamfer distance and a legibility or "
         "recognition-based score (does a classifier read it correctly?) become necessary.",
         BAD),
    ]
    for i, (t, b, c) in enumerate(reqs):
        y = 2.94 + i * 0.80
        rect(s, M, y, CW, 0.72, fill=WHITE, line=LINE,
             shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.04)
        rect(s, M, y, 0.05, 0.72, fill=c)
        txt(s, M + 0.22, y + 0.20, 3.0, 0.3, t, size=11, color=c, bold=True,
            spacing=1.05)
        txt(s, M + 3.45, y + 0.08, CW - 3.7, 0.6, b, size=10, color=BODY, spacing=1.16)
    note(s, """
The ladder is a curriculum, and each rung introduces exactly one new difficulty. That
is deliberate: if several things change at once and performance drops, you cannot say
why.

The third row is the most significant architectural step, and worth dwelling on. Right
now we train one policy per shape, so strictly speaking the policy could be ignoring
the target channel entirely and simply memorising a motion. For digits, the target must
be sampled at reset, which forces the policy to actually CONDITION on the target
channel. That is the real test of the image-observation design, and it is honest to
admit we have not yet run it. A good intermediate experiment is to train one policy on
all four current shapes with the target sampled at reset.

The last row is a genuine research problem rather than an engineering one. For
handwriting, IoU stops being the right metric: a perfectly legible letter in a slightly
different style scores badly. Chamfer helps, but the principled answer is a
recognition-based score - does a character classifier read what the robot wrote? That
is a nice, concrete extension.
""")

    # ------------------------------------------- 10.6 publication ----------
    s = slide(prs, "Publication plan", "10 · roadmap",
              "What gets written, what evidence each claim needs, and where it goes.")
    txt(s, M, 1.48, 6.1, 0.28, "THE PAPER'S SPINE", size=10.5, color=PRIMARY, bold=True)
    spine = [
        ("Claim 1", "A low-cost arm can LEARN to draw geometric shapes with vision-guided "
         "RL.", "the task-ladder results + the scripted baseline", GOOD),
        ("Claim 2", "A camera-based reward is sufficient — learning from what you SEE "
         "matches learning from privileged coordinates.", "the H2 controlled comparison",
         ACCENT),
        ("Claim 3", "Reward design, not algorithm choice, is the binding constraint on "
         "this task.", "the four reward formulations + the PPO/SAC comparison", VIOLET),
        ("Claim 4", "The policy transfers to real hardware, and here is the measured gap.",
         "sim vs real IoU, with the pen-space/joint-space comparison", WARN),
        ("Contribution", "A reproducible, open, sub-Rs.10,000 benchmark for vision-guided "
         "robotic drawing.", "released environment + hardware recipe + logs", PRIMARY),
    ]
    for i, (k, t, ev, c) in enumerate(spine):
        y = 1.80 + i * 0.92
        rect(s, M, y, 6.1, 0.84, fill=WHITE, line=LINE,
             shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.04)
        rect(s, M, y, 0.05, 0.84, fill=c)
        txt(s, M + 0.20, y + 0.09, 1.2, 0.24, k, size=9.5, color=c, bold=True)
        txt(s, M + 0.20, y + 0.31, 5.7, 0.36, t, size=10, color=BODY, spacing=1.12)
        txt(s, M + 0.20, y + 0.63, 5.7, 0.2, "evidence:  " + ev, size=8.5, color=MUTED,
            italic=True)

    rx = M + 6.45
    txt(s, rx, 1.48, CW - 6.45, 0.28, "TARGET VENUES", size=10.5, color=VIOLET,
        bold=True)
    venues = [("ICRA", "IEEE Int. Conf. on Robotics and Automation — the primary robotics "
               "venue; a strong fit for a sim-to-real manipulation study."),
              ("IROS", "IEEE/RSJ Int. Conf. on Intelligent Robots and Systems — broad and "
               "receptive to complete systems work."),
              ("RA-L", "IEEE Robotics and Automation Letters — journal-speed, short format, "
               "good for a focused controlled comparison."),
              ("CoRL", "Conference on Robot Learning — the natural home for the "
               "reward-design and sim-to-real learning content.")]
    for i, (n, d) in enumerate(venues):
        y = 1.80 + i * 0.86
        rect(s, rx, y, CW - 6.45, 0.78, fill=WASH, line=None,
             shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.05)
        rect(s, rx, y, 0.045, 0.78, fill=VIOLET)
        txt(s, rx + 0.18, y + 0.09, 1.0, 0.26, n, size=11, color=VIOLET, bold=True)
        txt(s, rx + 1.20, y + 0.08, CW - 7.8, 0.62, d, size=9.5, color=BODY,
            spacing=1.14)
    card(s, rx, 5.24, CW - 6.45, 1.60, "WHAT MUST BE TRUE BEFORE SUBMISSION",
         ["Multi-seed results with variance — never single runs.",
          "The scripted, non-learning baseline measured on identical terms.",
          "At least one hardware result, even a modest one.",
          "A literature review that positions the work honestly against existing "
          "drawing robots.",
          "Code, environment file and research log released for reproduction."],
         accent=WARN)
    note(s, """
Frame the paper as four claims, each with the evidence it requires. Claim 1 is nearly
in hand once the scripted baseline is measured. Claim 2 is the central one and needs
the H2 experiment. Claim 3 is partly in hand from the reward-design work. Claim 4
needs hardware.

On venues, be realistic. ICRA and IROS are the natural robotics targets; RA-L is
attractive because it is journal-speed and suits a focused controlled comparison; CoRL
is the best fit for the learning-specific content. The choice depends on how strong
the hardware result turns out to be - without a hardware result, a workshop paper or a
simulation-focused venue is the honest option.

The bottom-right box is the discipline commitment, and it is the right note to end the
roadmap on. It says plainly what we will not do: no single-run results, no claims
without a baseline, no over-reach about hardware we have not built.

If asked for a timeline: the simulation experiments are weeks; the hardware build and
transfer are the long pole, realistically a few months.
""")
