"""Deck part 3 - technical design and programming details."""
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN

from deck_kit import (ACCENT, BAD, BODY, CW, FAINT, FM, GOOD, H, INK, LINE, M,
                      MUTED, NAVY, PRIMARY, SLATE, TINT_AMBER, TINT_BLUE,
                      TINT_GREEN, TINT_RED, TINT_VIOLET, VIOLET, W, WARN, WASH,
                      WASH2, WHITE, arrow, bullets, card, chip, code,
                      decision_slide, elbow, eqn, kpi, legend, node, note, pic,
                      pipeline, qa, rect, section, slide, table, txt)


def build(prs):
    # =================================================== SECTION 4 =========
    section(prs, 4, "Technical Design",
            "The system as an engineer would read it: modules and their contracts, how data "
            "moves, and the precise definition of the environment the agent lives in.",
            ["Architecture & repository", "Module responsibilities", "Data flow",
             "State · action · reward · episode", "Coordinates & representation"])

    # ------------------------------------------------- 4.1 architecture ----
    s = slide(prs, "Software architecture — separation of concerns",
              "04 · technical design",
              "Each layer knows only the layer below it. That is what makes every experimental arm a one-line change.")
    layers = [
        ("EXPERIMENT LAYER", "rl/train.py", "Chooses the shape, algorithm, budget and "
         "backend; evaluates before/after; saves models and renders.", VIOLET),
        ("AGENT LAYER", "Stable-Baselines3 (PPO / SAC)", "Owns the neural network and the "
         "optimiser. Sees only Gymnasium's reset/step contract — it knows nothing about "
         "robots.", PRIMARY),
        ("ENVIRONMENT LAYER", "rl/draw_env.py — DrawEnv", "The MDP: observation "
         "construction, action application, reward computation, episode termination.",
         GOOD),
        ("TASK LAYER", "rl/targets.py · rl/metrics.py", "What to draw and what 'close' "
         "means. Pure functions on images — no simulator, no agent, trivially testable.",
         ACCENT),
        ("EMBODIMENT LAYER", "PyBullet + IK  (sim/*.py)", "Arm URDF, inverse kinematics, "
         "physics stepping, paper mesh, virtual camera. The only arm-aware code.", SLATE),
    ]
    for i, (t, files, desc, c) in enumerate(layers):
        y = 1.56 + i * 0.90
        rect(s, M, y, CW, 0.80, fill=WHITE, line=LINE,
             shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.04)
        rect(s, M, y, 0.055, 0.80, fill=c)
        txt(s, M + 0.22, y + 0.10, 2.7, 0.28, t, size=11.5, color=c, bold=True)
        txt(s, M + 0.22, y + 0.40, 2.7, 0.28, files, size=9.5, color=MUTED, font=FM)
        txt(s, M + 3.15, y + 0.16, CW - 3.4, 0.6, desc, size=11, color=BODY,
            spacing=1.15)
        if i < len(layers) - 1:
            arrow(s, M + 1.6, y + 0.82, M + 1.6, y + 0.88, color=FAINT, lw=1.0)
    rect(s, M, 6.14, CW, 0.72, fill=WASH2, line=None,
         shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.05)
    txt(s, M + 0.24, 6.24, CW - 0.5, 0.55,
        "The payoff, concretely: switching PPO→SAC touches the experiment layer only. Switching "
        "ground-truth→vision reward touches the environment layer only. Switching KUKA→the real "
        "arm touches the embodiment layer only. Three hypotheses, three isolated changes.",
        size=11, color=INK, bold=True, spacing=1.18)
    note(s, """
The design principle is that each layer depends only on the layer below, and the
dependencies never run upward. Stable-Baselines3 has no idea a robot exists - it
sees a Gymnasium environment. DrawEnv has no idea which algorithm is training it.
targets.py and metrics.py are pure functions on numpy images, with no simulator
import at all, which is why they could be unit-tested against closed-form answers.

If asked "why does this architecture matter, isn't it over-engineering for a student
project?" - point at the bottom box. The three open hypotheses each require swapping
exactly one component while holding everything else fixed. That is only possible
because the boundaries were drawn deliberately. A monolithic script would force us
to re-verify the whole system for every experiment, and any difference in results
would be confounded.
""")

    # -------------------------------------------------- 4.2 repo tree ------
    s = slide(prs, "Repository structure", "04 · technical design",
              "Small, deliberate, and organised by role rather than by file type.")
    tree = [
        ("RoboSketch-RL/", "", NAVY, 0, ""),
        ("├─ sim/", "the simulator and perception — Phase B", PRIMARY, 1, ""),
        ("│   ├─ 01_manual_control.py", "arm + paper + joint sliders + pen-tip readout", MUTED, 2, "102"),
        ("│   ├─ 02_ik_reach.py", "inverse kinematics; the workspace study", MUTED, 2, "180"),
        ("│   ├─ 03_draw_line.py", "ink deposition, canvas↔paper, world→pixel mapping", MUTED, 2, "245"),
        ("│   ├─ 04_camera_capture.py", "virtual camera + OpenCV extraction + IoU", MUTED, 2, "236"),
        ("│   ├─ 05_interactive_draw.py", "human-driven drawing sandbox", MUTED, 2, "147"),
        ("│   └─ viewer.py", "shared GUI helpers (DPI, panels, labels)", MUTED, 2, "78"),
        ("├─ rl/", "the reinforcement-learning system — Phase C", GOOD, 1, ""),
        ("│   ├─ targets.py", "target shapes as binary masks", MUTED, 2, "104"),
        ("│   ├─ metrics.py", "IoU · MSE · coverage · precision · chamfer", MUTED, 2, "86"),
        ("│   ├─ draw_env.py", "DrawEnv — the Gymnasium environment", MUTED, 2, "250"),
        ("│   └─ train.py", "PPO training + before/after evaluation", MUTED, 2, "106"),
        ("├─ assets/paper_quad.obj", "UV-mapped quad — the paper mesh", ACCENT, 1, ""),
        ("├─ models/", "trained policies: ppo_<shape>_kin.zip  ×4", VIOLET, 1, ""),
        ("├─ output/", "drawings, camera captures, figures, montage", ACCENT, 1, ""),
        ("├─ docs/RESEARCH_LOG.md", "the lab notebook — every decision + rationale", WARN, 1, ""),
        ("├─ docs/learning-book/", "14-part conceptual book (foundations)", WARN, 1, ""),
        ("├─ docs/presentation/", "this deck + its figure generators", WARN, 1, ""),
        ("└─ environment.yml", "the reproducible conda environment", SLATE, 1, ""),
    ]
    for i, (name, desc, c, lvl, loc) in enumerate(tree):
        y = 1.52 + i * 0.253
        txt(s, M + 0.05, y, 4.3, 0.25, name, size=10.5 if lvl < 2 else 10,
            color=c if lvl < 2 else BODY, bold=(lvl < 2), font=FM)
        if desc:
            txt(s, M + 4.55, y + 0.005, 6.3, 0.25, desc, size=10, color=MUTED)
        if loc:
            txt(s, M + 11.0, y + 0.005, 1.0, 0.25, loc + " loc", size=9, color=FAINT,
                align=PP_ALIGN.RIGHT)
    rect(s, M + 8.9, 6.28, CW - 8.9, 0.58, fill=WASH, line=LINE,
         shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.05)
    txt(s, M + 9.05, 6.37, CW - 9.2, 0.42, "1,534 lines of project Python\n"
        "— deliberately small and readable", size=10, color=BODY, spacing=1.15)
    note(s, """
Two organising choices worth mentioning.

First, the sim scripts are numbered 01 to 05 because they are a progression, not a
library: each one is a milestone that can be run and watched independently, and each
builds on the verified machinery of the one before. 04 literally imports 03 rather
than duplicating the drawing code, which means the camera experiment and the drawing
experiment cannot drift apart.

Second, docs/RESEARCH_LOG.md is a first-class artefact, not an afterthought. Every
decision in this deck traces to a dated entry there with its rationale and the
measurement that justified it. That log is what makes the thesis writable and the
work auditable.

The total is about 1,500 lines of project Python. Keeping it small is deliberate -
this is research code that has to be read and trusted, not a product.
""")

    # ------------------------------------------------ 4.3 module table -----
    s = slide(prs, "Module-by-module — what each file owns, and why it exists",
              "04 · technical design")
    table(s, ["module", "owns", "key entry points", "why it is a separate module"],
          [["rl/targets.py", "The task definition — what shape to draw",
            "make(name)  ·  canvas_to_mask()",
            "Adding a new target must not require touching the environment or the agent."],
           ["rl/metrics.py", "The definition of accuracy",
            "iou · mse · coverage · precision · chamfer · summary",
            "One definition of 'close' shared by the REWARD and the EVALUATION, so we "
            "cannot optimise one thing and report another."],
           ["rl/draw_env.py", "The MDP — state, action, reward, episode",
            "DrawEnv.reset() · .step() · ._reward() · ._obs() · ._world_to_px()",
            "The only file that knows the task IS a reinforcement-learning problem."],
           ["rl/train.py", "The experiment — algorithm, budget, evaluation",
            "make_env() · evaluate() · main()",
            "Experiment configuration must be swappable without editing the environment."],
           ["sim/03_draw_line.py", "Ink physics — canvas, paper texture, world→pixel",
            "ink() · world_to_px() · refresh_paper() · drive() · solve_ik()",
            "The verified drawing engine; imported by 04 rather than duplicated."],
           ["sim/04_camera_capture.py", "Perception — camera model and extraction",
            "top_down_camera() · capture() · extract_drawing()",
            "The vision path is isolated so it can replace ground truth in the H2 "
            "condition without touching anything else."],
           ["sim/viewer.py", "GUI ergonomics (DPI, panels, labels)",
            "connect_gui() · crisp_window() · tidy_panels() · label()",
            "Platform workarounds belong in one place, not scattered through the "
            "experiment scripts."]],
          M, 1.62, CW, colw=[2.1, 2.7, 3.3, 4.2], size=9.5, row_h=0.66, header_h=0.34,
          bold_col0=True)
    note(s, """
The column that matters most for a design question is the last one: why is this a
separate module at all?

metrics.py is the clearest case. The reward function and the evaluation both call the
same iou(). If they were separate implementations, we could train against one
definition and report another - a subtle and very common way for results to become
meaningless.

The relationship between sim/03 and sim/04 is worth noting: 04 loads 03 as a module
and reuses its drawing machinery rather than copying it. When we fixed the texture
caching bug in 03, the camera experiment inherited the fix automatically.

viewer.py exists purely to keep platform workarounds - DPI awareness, panel hiding,
the label-chopping fix - in one place. That is a small thing, but it means the
experiment scripts read as experiments.
""")

    # ------------------------------------------------- 4.4 data flow -------
    s = slide(prs, "Data flow — one environment step, end to end",
              "04 · technical design",
              "Follow a single action through the system. Every arrow is a real function call.")
    boxes = [
        (0.62, 1.72, 2.35, 0.80, "POLICY", "CNN over 64×64×3", VIOLET),
        (3.45, 1.72, 2.35, 0.80, "action [dx, dy, pen]", "3 floats in [−1,1]", VIOLET),
        (6.28, 1.72, 2.55, 0.80, "scale by step_size", "×0.014 m → metres", PRIMARY),
        (9.31, 1.72, 3.40, 0.80, "clamp to paper bounds", "|x−0.55|≤0.10, |y|≤0.10", PRIMARY),
        (9.31, 2.92, 3.40, 0.80, "move the pen", "kinematic OR IK + 6 physics steps", PRIMARY),
        (6.28, 2.92, 2.55, 0.80, "read TRUE position", "getLinkState[4]", PRIMARY),
        (3.45, 2.92, 2.35, 0.80, "ink the segment", "cv2.line on canvas", GOOD),
        (0.62, 2.92, 2.35, 0.80, "score: IoU", "metrics.iou(canvas, target)", GOOD),
        (0.62, 4.12, 2.35, 0.80, "reward", "IoU-delta + shaping", GOOD),
        (3.45, 4.12, 2.35, 0.80, "build observation", "stack 3 channels @64²", ACCENT),
        (6.28, 4.12, 2.55, 0.80, "termination check", "IoU≥0.60 or step≥240", ACCENT),
        (9.31, 4.12, 3.40, 0.80, "return (obs, r, term, trunc, info)", "back to the agent", ACCENT),
    ]
    for x, y, w, h, t, sb, c in boxes:
        node(s, x, y, w, h, t, sb, color=c, fill=WHITE, title_size=10.5, sub_size=8.5)
    # arrows along the serpentine
    for a, b in [(0, 1), (1, 2), (2, 3)]:
        arrow(s, boxes[a][0] + boxes[a][2] + 0.04, 2.12, boxes[b][0] - 0.04, 2.12,
              color=SLATE, lw=1.3)
    arrow(s, 11.0, 2.54, 11.0, 2.88, color=SLATE, lw=1.3)
    for a, b in [(4, 5), (5, 6), (6, 7)]:
        arrow(s, boxes[a][0] - 0.04, 3.32, boxes[b][0] + boxes[b][2] + 0.04, 3.32,
              color=SLATE, lw=1.3)
    arrow(s, 1.79, 3.74, 1.79, 4.08, color=SLATE, lw=1.3)
    for a, b in [(8, 9), (9, 10), (10, 11)]:
        arrow(s, boxes[a][0] + boxes[a][2] + 0.04, 4.52, boxes[b][0] - 0.04, 4.52,
              color=SLATE, lw=1.3)
    arrow(s, 11.01, 4.96, 11.01, 5.10, color=VIOLET, lw=1.4)
    txt(s, 7.60, 5.06, 5.11, 0.26,
        "…the agent receives this observation and the loop repeats  ↺", size=9.5,
        color=VIOLET, bold=True, align=PP_ALIGN.RIGHT)

    txt(s, M, 5.22, CW, 0.28, "THREE DESIGN DECISIONS VISIBLE IN THIS FLOW", size=10.5,
        color=PRIMARY, bold=True)
    d3 = [("Clamp, don't terminate",
           "Walking off the paper clamps the pen to the boundary instead of ending the "
           "episode. Early termination would teach the agent that leaving the sheet is a "
           "cheap way to stop collecting penalties."),
          ("Ink at the TRUE position",
           "With the physics backend the motors lag the commanded target by millimetres. "
           "We read the achieved pose (link frame, index 4) and ink there, so the agent is "
           "scored on what it really drew."),
          ("Score the canvas, not the render",
           "The reward reads the numpy canvas directly. The 3D texture is display only, so "
           "training never pays the cost of rendering — this is what gives ~420 steps/s.")]
    cw3 = (CW - 0.44) / 3
    for i, (t, b) in enumerate(d3):
        card(s, M + i * (cw3 + 0.22), 5.54, cw3, 1.30, t, b,
             accent=[PRIMARY, GOOD, ACCENT][i])
    note(s, """
Trace one action out loud: the policy emits three numbers; dx and dy are scaled by
the step size to metres; the target is clamped to the paper; the pen is moved either
kinematically or by IK plus six physics steps; we read where it actually ended up;
we ink a connected segment from the previous point to this one; we score the canvas;
we compute the reward; we rebuild the observation; we check termination; we return.

The three decisions at the bottom are the ones a careful reviewer will probe.

Clamping instead of terminating is a subtle but important reward-design point. If
leaving the paper ended the episode, an agent that is accumulating negative reward
would learn to walk off the sheet deliberately - the classic "suicide" behaviour in
RL when termination is cheaper than continuing.

Inking at the true position rather than the commanded position is what keeps the
system honest under real dynamics.

Scoring the canvas rather than a render is a pure performance decision, and it is
the difference between 420 steps per second and something unusably slow.
""")

    # ------------------------------------------------ 4.5 the MDP ----------
    s = slide(prs, "The MDP — state, action, reward, episode", "04 · technical design",
              "The formal definition the agent actually optimises. Every element is a deliberate choice.")
    quad = [
        ("STATE  /  OBSERVATION", VIOLET,
         ["A 64×64×3 uint8 image — three stacked channels:",
          "ch 0  ·  TARGET — the shape to reproduce",
          "ch 1  ·  DRAWN — everything inked so far",
          "ch 2  ·  PEN — a filled marker at the pen position,\n"
          "         255 when the pen is down, 128 when lifted",
          "Markov: the canvas summarises all past actions, so no history is needed.",
          "Why an image: it carries the target and progress with no hand-designed "
          "features, and the same representation will work for letters."]),
        ("ACTION", PRIMARY,
         ["Continuous Box(3): [dx, dy, pen_down], each in [−1, 1] / [0, 1].",
          "dx, dy are scaled by step_size = 0.014 m → a nudge of up to 1.4 cm.",
          "Expressed in PEN (task) space, not joint space — portable across arms.",
          "pen_down is currently forced ON (pen_always_down) for single-stroke shapes; "
          "it becomes a real decision for multi-stroke letters.",
          "Why relative: IK is seeded from the current pose, so small continuous steps "
          "track far better than jumps (measured in B4)."]),
        ("REWARD", GOOD,
         ["r  =  10·ΔIoU  +  0.4·(Φₜ − Φₜ₋₁)  −  0.02·|aₜ − aₜ₋₁|  (+2 on success)",
          "ΔIoU — the change in Intersection-over-Union this step. Telescopes over the "
          "episode to the final IoU.",
          "Φ = −distance from the pen to the nearest target pixel — dense, "
          "potential-based shaping.",
          "Smoothness term penalises jerky direction changes → straighter strokes.",
          "Why IoU-delta and not coverage: stray ink LOWERS IoU, so scribbling is "
          "self-penalising by construction."]),
        ("EPISODE", ACCENT,
         ["reset(): blank canvas, pen at the paper centre, lifted, step counter 0.",
          "terminated — IoU ≥ 0.60 (the goal is reached; +2 bonus).",
          "truncated — 240 steps elapsed (the time limit).",
          "Leaving the paper does NOT end the episode; the pen is clamped to the "
          "boundary instead.",
          "Why: early termination on failure would teach the agent that walking off "
          "the sheet is a cheap escape from accumulating penalties."]),
    ]
    cw2 = (CW - 0.28) / 2
    for i, (t, c, items) in enumerate(quad):
        x = M + (i % 2) * (cw2 + 0.28)
        y = 1.66 + (i // 2) * 2.62
        rect(s, x, y, cw2, 2.46, fill=WHITE, line=LINE,
             shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.04)
        rect(s, x, y, cw2, 0.40, fill=c, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.10)
        rect(s, x, y + 0.22, cw2, 0.18, fill=c)
        txt(s, x + 0.20, y + 0.07, cw2 - 0.4, 0.28, t, size=11.5, color=WHITE, bold=True)
        conv = [{"t": ("•  " if j else "") + it, "size": 9.5 if j else 10,
                 "color": BODY if j else INK, "bold": j == 0,
                 "font": FM if (j == 0 and i == 2) else None,
                 "space_after": 4} for j, it in enumerate(items)]
        conv = [{k: v for k, v in d.items() if v is not None} for d in conv]
        txt(s, x + 0.20, y + 0.50, cw2 - 0.40, 1.9, conv, spacing=1.14)
    note(s, """
This slide is the formal contract, and a guide may ask you to justify any element.

On the state: the key property is Markov - the current observation must be enough to
act on, with no memory of the past. Our canvas channel contains every stroke made so
far, so it summarises the entire history. That is why no recurrent network is needed.
The pen channel encodes both position and pen state in one channel by using 255 for
down and 128 for up.

On the action: continuous, three-dimensional, in pen space. Two follow-up questions
are likely. Why continuous rather than discrete? Because drawing is a continuous
control problem, and discretising it either coarsens the strokes or explodes the
action space. Why is pen_down currently forced on? Because the first rung of the task
ladder is single-stroke shapes; a pen-up decision has no benefit there and only makes
exploration harder. It becomes a genuine decision for letters.

On the reward: the headline is the IoU-delta term. Because the per-step rewards are
differences in IoU, they telescope - they sum to the final IoU minus the initial. So
maximising return is literally maximising the accuracy of the finished drawing. The
proximity term is potential-based, which by Ng's theorem does not change which policy
is optimal; it only makes the gradient easier to find.

On the episode: the clamp-don't-terminate choice is the one to defend, as on the
previous slide.
""")

    # --------------------------------------------- 4.6 simulation design ---
    s = slide(prs, "Simulation design — the scene, precisely specified",
              "04 · technical design")
    specs = [
        ("ROBOT", PRIMARY, [
            ("model", "KUKA iiwa 7-DOF (bundled kuka_iiwa/model.urdf)"),
            ("base", "fixed at the world origin"),
            ("home pose", "[0, 0.5, 0, −1.5, 0, 1.2, 0] rad — 'elbow down'"),
            ("control", "POSITION_CONTROL, force = 800 N·m, maxVelocity = 10 rad/s"),
            ("tip link", "index numJoints−1; pose read from getLinkState[4]"),
        ]),
        ("VIRTUAL PEN", ACCENT, [
            ("length", "0.10 m rod hanging below the wrist"),
            ("wrist z (down)", "paper_z + 0.10 m — what IK actually targets"),
            ("wrist z (up)", "paper_z + 0.15 m (0.05 m lift)"),
            ("why", "the wrist is a solid body; below ~0.06 m clearance it hits the floor"),
            ("nib", "≈1.5 mm in sim; 2 px radius on the 128² RL canvas"),
        ]),
        ("PAPER & CANVAS", GOOD, [
            ("geometry", "0.20 × 0.20 m sheet centred at (0.55, 0.00), top z = 0.003 m"),
            ("mesh", "UV-mapped quad (assets/paper_quad.obj), NOT a GEOM_BOX"),
            ("canvas", "512² numpy in sim · 128² in the RL environment"),
            ("texture", "reloaded from a UNIQUE PNG filename every 20 pen points"),
            ("authority", "the numpy canvas is the drawing; the texture only displays it"),
        ]),
        ("CAMERA", VIOLET, [
            ("eye / target", "(0.55, 0.00, 0.55) looking down at (0.55, 0.00, 0.003)"),
            ("up vector", "[0, 1, 0] — verified to match the canvas convention"),
            ("projection", "FOV 24°, aspect 1.0, near 0.1 m, far 1.0 m"),
            ("resolution", "480 × 480 RGB + segmentation mask"),
            ("renderer", "TinyRenderer headless · hardware OpenGL in the GUI"),
        ]),
    ]
    cw2 = (CW - 0.28) / 2
    for i, (t, c, rows) in enumerate(specs):
        x = M + (i % 2) * (cw2 + 0.28)
        y = 1.58 + (i // 2) * 2.66
        rect(s, x, y, cw2, 2.48, fill=WASH, line=LINE,
             shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.04)
        rect(s, x, y + 0.10, 0.05, 2.28, fill=c)
        txt(s, x + 0.22, y + 0.12, cw2 - 0.44, 0.28, t, size=11.5, color=c, bold=True)
        for j, (k, v) in enumerate(rows):
            ry = y + 0.48 + j * 0.39
            txt(s, x + 0.22, ry, 1.35, 0.3, k, size=9, color=MUTED, font=FM)
            txt(s, x + 1.62, ry - 0.02, cw2 - 1.85, 0.36, v, size=9.5, color=BODY,
                spacing=1.1)
    note(s, """
Have these numbers ready; a guide who works with robots will ask for at least one of
them.

The pen-length choice is the one with a story. The KUKA's wrist link is a solid body.
If you ask its own frame to sit 2 cm above the floor, it simply cannot get there - we
measured 28 to 35 mm of error, and only with the pen down, which is what pointed at
floor contact. Minimum measured clearance is about 0.06 m, so we model a 0.10 m pen
with margin. It is also more faithful: the real robot will hold an actual pen.

The paper being a mesh quad rather than a box is not a stylistic choice - a box's top
face samples only a tiny uniform patch of the texture, so most of a drawing would
never appear on it. We verified the mesh renders all four quadrants of a test texture
at 25 percent each.

The camera parameters were chosen so the 20 cm sheet nearly fills the frame from
0.55 m up - hence the narrow 24 degree field of view. The up-vector was calibrated
against all eight dihedral transforms rather than assumed.
""")

    # ------------------------------------- 4.7 coordinates + representation -
    s = slide(prs, "Coordinate systems and drawing representation",
              "04 · technical design",
              "Four frames, two conversions. Getting either conversion wrong silently mirrors or shifts every result.")
    frames = [("WORLD", "metres, PyBullet\nx forward, y left, z up\nbase at origin", PRIMARY),
              ("JOINT", "7 angles, radians\narm-specific\n(IK output)", SLATE),
              ("CANVAS", "pixels, 128² or 512²\ncol → +x, row → −y\nthe drawing", GOOD),
              ("OBSERVATION", "pixels, 64²\nsame convention,\ndownsampled", ACCENT)]
    bw = 2.55
    for i, (t, sb, c) in enumerate(frames):
        node(s, M + i * (bw + 0.55), 1.72, bw, 1.10, t, sb, color=c, fill=WHITE,
             title_size=11.5, sub_size=9)
        if i < 3:
            arrow(s, M + i * (bw + 0.55) + bw + 0.06, 2.27,
                  M + (i + 1) * (bw + 0.55) - 0.06, 2.27, color=SLATE, lw=1.4)
    txt(s, M + bw + 0.02, 2.86, 0.5 + bw, 0.26, "inverse kinematics", size=9,
        color=SLATE, align=PP_ALIGN.CENTER, italic=True)
    txt(s, M + 2 * (bw + 0.55) - 0.55, 2.86, 0.55, 0.26, "ink", size=9,
        color=SLATE, align=PP_ALIGN.CENTER, italic=True)
    txt(s, M + 3 * (bw + 0.55) - 0.58, 2.86, 0.6, 0.26, "resize", size=9,
        color=SLATE, align=PP_ALIGN.CENTER, italic=True)

    eqn(s, M, 3.24, 6.05,
        ["col  =  (x − (cx − half)) / (2·half)  ×  (RES − 1)",
         "row  =  ((cy + half) − y) / (2·half)  ×  (RES − 1)"],
        size=13,
        caption="world (metres) → canvas (pixels).  Column follows world +x; row follows world −y.")
    card(s, M + 6.35, 3.24, CW - 6.35, 1.24, "VERIFIED AGAINST PHYSICS",
         "An earlier version mapped x→row and y→col. Every drawing would have been "
         "mirrored — and the reward would have scored a mirrored image, so nothing would "
         "have looked wrong. Checked by painting ink at a world point and placing a "
         "reference sphere at the same point: agreement within ~3 px on all four edges.",
         accent=BAD)

    txt(s, M, 4.72, CW, 0.28, "HOW A DRAWING IS REPRESENTED  —  and how error is computed",
        size=10.5, color=PRIMARY, bold=True)
    reps = [("The drawing", "A single-channel uint8 raster. 255 = ink, 0 = blank. A stroke "
             "is a connected cv2.line segment from the previous pen point to the new one — "
             "not isolated dots, so fast motion still leaves a continuous trace.", GOOD),
            ("The target", "The same convention, produced by targets.py at 512² and "
             "resized to the canvas resolution, then re-binarised at >127 so anti-aliasing "
             "cannot leak grey pixels into the comparison.", ACCENT),
            ("The error", "IoU = |A∩B| / |A∪B| between the two masks. Reported alongside "
             "MSE, coverage (recall), precision, and chamfer distance in pixels — five "
             "views of one comparison.", VIOLET)]
    cw3 = (CW - 0.44) / 3
    for i, (t, b, c) in enumerate(reps):
        card(s, M + i * (cw3 + 0.22), 5.04, cw3, 1.60, t, b, accent=c)
    note(s, """
Four frames and the conversions between them. Two of these conversions are where
silent, catastrophic bugs live.

World to joint is inverse kinematics - covered in the maths section.

World to canvas is the pixel mapping in the box. Note the sign asymmetry: the column
increases with world x, but the row DECREASES with world y, because image rows run
downward while the world y axis runs left. Our first version had the two axes
transposed. The failure mode is the dangerous kind: every drawing mirrored, scored
against a target in the correct orientation, and no visible symptom - the agent would
simply have learned to draw backwards. We now verify it against physics.

On representation: strokes are connected line segments, not dots. That matters
because at 1.4 cm per step a dot-based renderer would produce a dotted line and the
IoU would be dominated by the gaps rather than by the trajectory.

Re-binarising the target after resizing matters too - anti-aliased grey pixels would
otherwise be counted inconsistently between the two masks.
""")

    # =================================================== SECTION 5 =========
    section(prs, 5, "Programming Details",
            "The implementation itself: languages, libraries, the classes and functions that "
            "carry the work, how control flows through a training run, and how the files "
            "talk to one another.",
            ["Languages & libraries", "Key classes and functions",
             "Code flow of a training run", "Module communication",
             "Core algorithms"])

    # ------------------------------------------------- 5.1 the stack -------
    s = slide(prs, "Languages and libraries — and why each one", "05 · programming")
    libs = [
        ("Python 3.10", "language", "The lingua franca of RL and computer vision. Every "
         "library we need has first-class Python bindings; C++ would cost weeks and buy "
         "nothing, since the heavy loops are inside the libraries.", PRIMARY),
        ("PyBullet 3.25", "physics + robot simulation", "Rigid-body physics, URDF loading, "
         "inverse kinematics, synthetic cameras. Native on Windows, pure Python, fast "
         "headless stepping — which is what millions of RL steps need.", PRIMARY),
        ("Gymnasium 1.3", "RL environment interface", "The standard reset/step API. "
         "Implementing it means ANY RL library can train on our environment without "
         "modification — including ones we have not chosen yet.", GOOD),
        ("Stable-Baselines3 2.9", "RL algorithms", "Reliable, well-tested implementations "
         "of PPO and SAC. Re-implementing PPO would risk subtle bugs and add nothing "
         "scientific — the contribution is the environment and reward, not the optimiser.",
         VIOLET),
        ("PyTorch 2.13", "neural networks", "The backend for SB3; provides the CNN policy "
         "and the autograd/optimiser machinery. CPU is sufficient at this scale.", VIOLET),
        ("OpenCV 5.0", "computer vision + rasterising", "Two jobs: drawing the ink and "
         "targets (cv2.line, cv2.circle) and the perception pipeline (threshold, resize, "
         "distanceTransform). Battle-tested and fast.", ACCENT),
        ("NumPy 2.x", "arrays and maths", "The canvas, the masks, the observation tensor "
         "and every metric are numpy arrays. It is the common currency between all the "
         "other libraries.", ACCENT),
        ("conda-forge", "environment management", "Ships PREBUILT scientific binaries. "
         "This is what solved the PyBullet-on-Windows blocker, and it makes the setup "
         "reproducible with one command.", SLATE),
    ]
    for i, (n, role, why, c) in enumerate(libs):
        y = 1.50 + i * 0.665
        rect(s, M, y, CW, 0.60, fill=WHITE, line=LINE,
             shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.04)
        rect(s, M, y, 0.05, 0.60, fill=c)
        txt(s, M + 0.20, y + 0.06, 2.3, 0.26, n, size=11, color=c, bold=True)
        txt(s, M + 0.20, y + 0.31, 2.3, 0.24, role, size=9, color=MUTED, italic=True)
        txt(s, M + 2.70, y + 0.10, CW - 2.95, 0.46, why, size=10, color=BODY,
            spacing=1.14)
    note(s, """
The framing to use for every row is "what would we lose by not using it, and what did
we consider instead?"

On Stable-Baselines3, expect the question "why not implement PPO yourself - wouldn't
that show more?" The answer is a research-priorities answer: our contribution is the
environment, the reward design and the comparisons. A hand-rolled PPO would introduce
a plausible source of bugs and make our results harder to trust, because a reviewer
could always ask whether a poor result came from our implementation rather than from
the task. Using a well-tested reference implementation makes the comparisons cleaner.

On Gymnasium, the point is future-proofing: because DrawEnv implements the standard
interface, we can run RLlib or CleanRL later without touching the environment.

On PyTorch and CPU: at 64x64 observations with a small CNN, CPU training runs at about
420 environment steps per second, so a 400k-step run takes roughly a quarter of an
hour. A GPU becomes worthwhile if we scale the observation resolution or move to
larger networks for letters.
""")

    # --------------------------------------------- 5.2 classes / functions --
    s = slide(prs, "Key classes and functions", "05 · programming",
              "The contracts that matter — what each one takes, returns and guarantees.")
    table(s, ["signature", "returns", "responsibility / guarantee"],
          [["class DrawEnv(gym.Env)", "—",
            "The MDP. Holds the canvas, the target, the pen state and the distance "
            "transform. Two backends behind one interface."],
           ["DrawEnv.reset(seed)", "(obs, info)",
            "Blank canvas, pen at the paper centre and lifted, counters zeroed, potential "
            "re-initialised. Deterministic for a given seed."],
           ["DrawEnv.step(action)", "(obs, reward, terminated, truncated, info)",
            "Applies one nudge, inks, scores, and reports. info carries iou and coverage "
            "for logging and evaluation."],
           ["DrawEnv._reward(iou)", "float",
            "IoU-delta + potential-based proximity shaping − time cost. The only place "
            "the objective is defined."],
           ["DrawEnv._obs()", "uint8 [64,64,3]",
            "Stacks target, drawing and pen marker. Downsamples with INTER_AREA so thin "
            "strokes survive resizing."],
           ["DrawEnv._world_to_px(x, y)", "(col, row)",
            "The verified world→canvas mapping, clipped to the canvas."],
           ["DrawEnv._move_arm(x, y, down)", "(x, y) achieved",
            "IK + POSITION_CONTROL + 6 physics steps; returns where the pen ACTUALLY "
            "arrived, not where it was asked to go."],
           ["metrics.iou / mse / coverage / precision / chamfer", "float",
            "Pure functions on two binary masks. Defined edge cases: both empty → IoU 1; "
            "one empty → chamfer ∞."],
           ["targets.make(name)", "uint8 mask",
            "The target shape at 512², binarised at >40 to kill anti-aliasing."],
           ["train.evaluate(model, …)", "(mean IoU, mean coverage, render)",
            "Deterministic rollouts on a fixed seed — the before/after measurement."]],
          M, 1.68, CW, colw=[3.9, 2.5, 5.9], size=9.5, row_h=0.48, header_h=0.34)
    note(s, """
Point out that every method has a stated guarantee, not just a behaviour.

reset is deterministic for a given seed - which is what makes the before/after
evaluation a fair comparison rather than a coin flip. We evaluate on seeds 1000 to
1004 both before and after training.

_move_arm returning the ACHIEVED position rather than the requested one is the
contract that keeps the whole system honest under real dynamics.

The metrics functions are pure - two arrays in, a float out, no state, no simulator.
That is what made it possible to test them against closed-form answers, and it is why
the same function can serve the reward and the evaluation.

If asked which single function to read first, say DrawEnv.step - roughly thirty lines
that contain the entire task definition.
""")

    # ------------------------------------------------- 5.3 code flow -------
    s = slide(prs, "Code flow — what happens when you launch a training run",
              "05 · programming")
    code(s, M, 1.60, 6.15, 2.35, [
        "$ conda run -n robosketch python rl/train.py \\",
        "      --shape circle --timesteps 400000 --n-envs 8",
        "",
        "  n_steps=512  batch_size=256  n_epochs=6",
        "  gamma=0.99   ent_coef=0.02   lr=3e-4",
        "  policy=CnnPolicy   8 parallel environments",
    ], title="the command", size=10)
    flow = [
        ("1", "train.main() parses the arguments and creates 8 DrawEnv instances inside a "
              "DummyVecEnv, wrapped in VecMonitor for episode statistics.", PRIMARY),
        ("2", "PPO is constructed with a CnnPolicy — SB3 inspects the observation space "
              "(64×64×3 uint8) and builds a small convolutional feature extractor.", VIOLET),
        ("3", "evaluate() runs 5 deterministic episodes with the UNTRAINED policy and saves "
              "a render. This is the before measurement.", ACCENT),
        ("4", "model.learn() begins the loop: collect 512 steps × 8 envs = 4,096 "
              "transitions, compute GAE advantages, then 6 epochs of clipped-surrogate "
              "updates on minibatches of 256.", VIOLET),
        ("5", "Each environment step: DrawEnv.step() nudges the pen, inks the canvas, "
              "calls metrics.iou(), computes the shaped reward, rebuilds the observation.",
         GOOD),
        ("6", "An episode ends at IoU ≥ 0.60 or 240 steps; the environment auto-resets and "
              "VecMonitor records the episode return and length.", GOOD),
        ("7", "After ~98 policy updates (400k steps), evaluate() runs again — the after "
              "measurement — and the model plus both renders are saved.", ACCENT),
    ]
    for i, (n, t, c) in enumerate(flow):
        y = 1.62 + i * 0.735
        x = M + 6.45
        rect(s, x, y, CW - 6.45, 0.66, fill=WHITE, line=LINE,
             shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.04)
        chip(s, x + 0.14, y + 0.19, 0.32, 0.28, n, color=c, fill=WASH, size=10)
        txt(s, x + 0.58, y + 0.08, CW - 7.2, 0.55, t, size=10, color=BODY,
            spacing=1.14)
    card(s, M, 4.12, 6.15, 1.30, "THROUGHPUT",
         ["≈420 environment steps / second (kinematic backend, CPU).",
          "400,000 steps ≈ 16 minutes per shape · ≈1,700 episodes.",
          "The physics backend is far slower and runs a single environment, so it is "
          "used for verification rather than for bulk training."],
         accent=SLATE)
    card(s, M, 5.54, 6.15, 1.34, "WHY 8 PARALLEL ENVIRONMENTS",
         ["PPO is on-policy: it learns only from data the CURRENT policy generated.",
          "Running 8 copies collects a diverse batch quickly and decorrelates samples, "
          "which stabilises the gradient estimate.",
          "DummyVecEnv runs them in one process — at this speed the overhead of separate "
          "processes would cost more than it saves."],
         accent=PRIMARY)
    note(s, """
Walk the seven steps. The parts to emphasise are 3 and 7 - the before and after
measurements. Evaluating the untrained policy with exactly the same procedure as the
trained one is what turns "it draws a circle" into "IoU improved from 0.000 to 0.443
under identical evaluation conditions".

Step 4 contains the PPO specifics. Collect 4,096 transitions, compute generalised
advantage estimates, then six epochs of clipped-surrogate updates on minibatches of
256. Roughly 98 such updates make up a 400k-step run.

On parallel environments, the reason is specific to on-policy algorithms. PPO can
only learn from data generated by the current policy, so it must discard its batch
after each update. Running eight copies gathers a larger, more diverse batch before
each update, which lowers the variance of the gradient estimate. We use DummyVecEnv
rather than SubprocVecEnv because at 420 steps per second the inter-process
communication would cost more than the parallelism gains.

Be ready for "why entropy coefficient 0.02?" - it keeps the policy stochastic enough
to keep exploring. With a thin target and a shaped reward, a policy that becomes
deterministic too early tends to settle into one of the local optima we documented.
""")

    # -------------------------------------------- 5.4 module communication --
    s = slide(prs, "How the files communicate", "05 · programming",
              "Imports flow one way. There are no cycles, and nothing below imports anything above it.")
    nodes = {
        "train": (5.15, 1.66, 3.0, 0.72, "rl/train.py", "the experiment", VIOLET),
        "sb3": (9.05, 1.66, 3.10, 0.72, "stable_baselines3", "PPO · CnnPolicy", VIOLET),
        "env": (5.15, 2.86, 3.0, 0.78, "rl/draw_env.py", "DrawEnv (gym.Env)", GOOD),
        "targets": (1.05, 4.14, 2.55, 0.72, "rl/targets.py", "shape masks", ACCENT),
        "metrics": (4.05, 4.14, 2.55, 0.72, "rl/metrics.py", "IoU · MSE · chamfer", ACCENT),
        "pybullet": (7.05, 4.14, 2.55, 0.72, "pybullet", "IK + physics", PRIMARY),
        "cv2": (10.05, 4.14, 2.10, 0.72, "cv2 / numpy", "raster + maths", SLATE),
        "sim03": (1.05, 5.62, 3.55, 0.78, "sim/03_draw_line.py", "ink engine · world→px", PRIMARY),
        "sim04": (5.15, 5.62, 3.55, 0.78, "sim/04_camera_capture.py", "camera + OpenCV extraction", ACCENT),
        "viewer": (9.15, 5.62, 3.0, 0.78, "sim/viewer.py", "GUI helpers", SLATE),
    }
    for k, (x, y, w, h, t, sb, c) in nodes.items():
        node(s, x, y, w, h, t, sb, color=c, fill=WHITE, title_size=10.5, sub_size=9)
    arrow(s, 6.65, 2.40, 6.65, 2.82, color=SLATE, lw=1.4)
    arrow(s, 8.20, 2.02, 9.01, 2.02, color=SLATE, lw=1.4)
    arrow(s, 5.60, 3.66, 3.10, 4.10, color=SLATE, lw=1.3)
    arrow(s, 6.15, 3.66, 5.35, 4.10, color=SLATE, lw=1.3)
    arrow(s, 7.10, 3.66, 8.10, 4.10, color=SLATE, lw=1.3)
    arrow(s, 7.70, 3.66, 10.6, 4.10, color=SLATE, lw=1.3)
    arrow(s, 5.11, 6.01, 4.66, 6.01, color=ACCENT, lw=1.4)
    txt(s, 4.10, 6.14, 2.0, 0.24, "loaded by path", size=8.5, color=ACCENT, bold=True,
        align=PP_ALIGN.CENTER)
    arrow(s, 2.80, 5.58, 2.80, 4.90, color=FAINT, lw=1.2, dashed=True)
    arrow(s, 8.74, 6.01, 9.11, 6.01, color=FAINT, lw=1.2, dashed=True)
    txt(s, 1.05, 2.30, 3.6, 0.9,
        "The RL stack (top) and the simulator scripts (bottom) share the same "
        "conventions — paper geometry, world→pixel mapping, pen model — but the "
        "training path deliberately does NOT import PyBullet unless use_arm=True.",
        size=10, color=BODY, spacing=1.18)
    legend(s, M, 6.60, [(SLATE, "python import"), (ACCENT, "module load by path"),
                        (FAINT, "shared convention, not an import")])
    note(s, """
The claim to make here is that the dependency graph is acyclic and shallow, which is
what makes the system testable.

train imports draw_env and Stable-Baselines3. draw_env imports targets, metrics, cv2
and numpy - and imports PyBullet ONLY when use_arm is true, inside _setup_arm. That
lazy import is deliberate: the fast training path never even loads the physics engine.

targets and metrics import nothing but cv2 and numpy. They sit at the bottom of the
graph, which is exactly why they could be validated against closed-form answers in
isolation.

The one unusual edge is sim/04 loading sim/03 by file path using importlib, because
the filenames start with digits and are therefore not importable as normal modules.
That was a conscious trade: the numeric prefixes communicate the milestone
progression to a reader, and the one place that needs to import across them uses
importlib. The alternative - renaming everything - would have lost the narrative
ordering that makes the simulator scripts readable as a sequence.
""")

    # ------------------------------------------------- 5.5 algorithms ------
    s = slide(prs, "Core algorithms, in the code that runs", "05 · programming")
    code(s, M, 1.58, 5.95, 2.52, [
        {"t": "# DrawEnv.step - the whole task in ~20 lines", "color": FAINT},
        "dx, dy = action[0]*step, action[1]*step",
        "nx = clip(pen.x + dx, x_min, x_max)      # stay on paper",
        "ny = clip(pen.y + dy, y_min, y_max)",
        "ax, ay = move_arm(nx, ny) if use_arm else (nx, ny)",
        "",
        {"t": "if pen_down and was_down:                # connected stroke", "color": FAINT},
        "    cv2.line(canvas, px(pen), px(ax,ay), 255, w)",
        "",
        "iou    = metrics.iou(canvas, target)",
        "reward = self._reward(iou)",
        "reward -= smooth * mean(|action - prev_action|)",
        "terminated = iou >= 0.60",
        "truncated  = steps >= 240",
    ], title="1 · the environment step", size=9)
    code(s, M + 6.22, 1.58, CW - 6.22, 2.52, [
        {"t": "# the reward - IoU-delta + potential-based shaping", "color": FAINT},
        "d_iou   = iou - prev_iou            # telescopes to final IoU",
        "r       = 10.0 * d_iou",
        "",
        {"t": "# Phi = -(distance from pen to nearest target pixel)", "color": FAINT},
        "phi     = -target_dt[row, col]      # precomputed once",
        "r      += 0.4 * (phi - prev_phi)    # Ng et al. shaping",
        "r      -= time_penalty              # currently 0",
        "",
        {"t": "# potential-based => optimal policy is UNCHANGED", "color": FAINT},
        {"t": "# but the gradient is far easier to find", "color": FAINT},
    ], title="2 · the reward function", size=9)
    code(s, M, 4.28, 5.95, 2.55, [
        {"t": "# inverse kinematics - the configuration we measured best", "color": FAINT},
        "down = getQuaternionFromEuler([pi, 0, 0])   # pen vertical",
        "a = calculateInverseKinematics(",
        "        arm, tip_link, [x, y, wrist_z],",
        "        targetOrientation = down,       # REQUIRED",
        "        maxNumIterations  = 200,",
        "        residualThreshold = 1e-5)",
        {"t": "        # NO lowerLimits/upperLimits/jointRanges/restPoses:", "color": FAINT},
        {"t": "        # null-space hints degraded accuracy ~400x", "color": FAINT},
        "for j in joints:",
        "    setJointMotorControl2(arm, j, POSITION_CONTROL,",
        "                          a[j], force=800, maxVelocity=10)",
    ], title="3 · pen space → joint space", size=9)
    code(s, M + 6.22, 4.28, CW - 6.22, 2.55, [
        {"t": "# perception - camera frame -> clean binary drawing", "color": FAINT},
        "paper = (seg == paper_id)              # segmentation mask",
        "y0,y1,x0,x1 = bounding_box(paper)      # crop to the sheet",
        "grey  = cvtColor(rgb[y0:y1, x0:x1], RGB2GRAY)",
        "grey[~paper_crop] = 255                # force off-paper white",
        "_, binv = threshold(grey, 128, 255, THRESH_BINARY_INV)",
        "out = resize(binv, (RES, RES), INTER_AREA)",
        "out = (out > 40) * 255                 # re-binarise",
        {"t": "# fixed threshold, not Otsu: with the dark arm in frame Otsu", "color": FAINT},
        {"t": "# split arm-vs-paper and lost the thin stroke entirely", "color": FAINT},
    ], title="4 · the vision pipeline", size=9)
    note(s, """
These four blocks are the entire technical core, and they are short on purpose.

Block 1 - the environment step. Note the clip that keeps the pen on the paper, and
the cv2.line that connects the previous pen point to the new one so a stroke is
continuous rather than dotted.

Block 2 - the reward. Two terms. The IoU-delta telescopes: summed over an episode it
equals the final IoU minus the initial, so maximising return maximises accuracy. The
proximity term uses a distance transform computed once at construction, so the dense
shaping costs a single array lookup per step rather than a search.

Block 3 - inverse kinematics. Highlight the comment: we deliberately do NOT pass the
null-space arguments that most examples include, because we measured them making
accuracy about 400 times worse. Passing targetOrientation, on the other hand, is
mandatory - without it the pen reaches the point at a 41 degree tilt.

Block 4 - perception. The comment records why we use a fixed threshold rather than
Otsu: with the dark arm in frame Otsu separates arm from paper and classifies the
thin stroke as background.

The general point worth making: every non-obvious line carries the measurement that
justified it, in a comment. That is how the code and the research log stay in sync.
""")

    # ------------------------------------- 5.6 engineering practice --------
    s = slide(prs, "Engineering practice — how we know the code is right",
              "05 · programming",
              "Every component was validated against an independent reference BEFORE anything depended on it.")
    practice = [
        ("CLOSED-FORM TESTS", ACCENT,
         "metrics.py is checked against answers derived by hand: identical masks → IoU 1, "
         "MSE 0, chamfer 0; disjoint → IoU 0; exactly half-overlapping → IoU exactly 1/3 "
         "(measured 0.333)."),
        ("PHYSICAL CROSS-CHECKS", PRIMARY,
         "The world→pixel mapping was verified by painting ink at a world point and placing "
         "a reference sphere at the same point — agreement within ~3 px on all four edges."),
        ("EXHAUSTIVE CALIBRATION", VIOLET,
         "Camera orientation was not assumed: all 8 dihedral transforms of the perceived "
         "image were scored against the known canvas. rot0 won at IoU 0.998 vs 0.68 for the "
         "runner-up."),
        ("BEHAVIOURAL ORACLES", GOOD,
         "Before training, the environment was checked with three reference policies: a "
         "contour-tracing oracle (should score well: +1.5), random (should score badly: "
         "−26), and idle (should draw nothing). All behaved as required."),
        ("DIFFERENTIAL DIAGNOSIS", WARN,
         "Faults were isolated by changing one variable: pen-up worked while pen-down "
         "failed → floor contact. Error fell with more settle steps → lag, not a structural "
         "limit."),
        ("HEADLESS ASSERTIONS", SLATE,
         "Every milestone has a headless validation run that asserts on geometry — inked "
         "pixel counts, row/column spans, hollow interiors — rather than on appearance."),
    ]
    cw3 = (CW - 0.44) / 3
    for i, (t, c, b) in enumerate(practice):
        card(s, M + (i % 3) * (cw3 + 0.22), 1.68 + (i // 3) * 1.72, cw3, 1.56, t, b,
             accent=c)
    rect(s, M, 5.20, CW, 1.52, fill=WASH2, line=None,
         shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.05)
    txt(s, M + 0.28, 5.32, CW - 0.6, 0.3, "THE PRINCIPLE BEHIND ALL SIX", size=10.5,
        color=PRIMARY, bold=True)
    txt(s, M + 0.28, 5.62, CW - 0.6, 1.0,
        "In this project every single serious bug produced a system that LOOKED correct: the "
        "20 mm centre-of-mass bias, the invisible debug-line ink, the flat-coloured box texture, "
        "the cached texture, the transposed pixel mapping. None would have been caught by "
        "inspection, a demo, or a screenshot. They were caught because each component was "
        "compared against an independent reference before anything was built on top of it — "
        "and because the comparison was written down.",
        size=11.5, color=BODY, spacing=1.22)
    note(s, """
If there is one slide that demonstrates research maturity rather than coding ability,
this is it.

The unifying observation is at the bottom: every serious bug in this project produced
a system that looked correct. A 20 mm constant bias looks like a working arm. Ink
drawn as a debug overlay looks like a perfect stroke. A box that renders one flat
colour looks like a coloured sheet of paper. A cached texture looks like a paper that
simply has not been drawn on yet. A transposed pixel mapping looks like a normal
drawing.

None of these would be caught by reading the code, running a demo, or looking at a
screenshot. They were caught by comparing each component against an INDEPENDENT
reference - a hand-derived number, a physical marker, an exhaustive transform search,
a reference policy - before anything was built on top of it.

The behavioural oracle idea is worth explaining if there is time: before spending
hours of training, we checked that a scripted contour-tracer scores well, random
scores badly, and idle draws nothing. If those three do not order correctly, the
reward is wrong and no amount of training will fix it.
""")
