"""Deck part 1 - title, agenda, project overview, system vision."""
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

from deck_kit import (ACCENT, BAD, BODY, CW, FAINT, GOOD, H, INK, LINE, M, MUTED, W,
                      NAVY, PRIMARY, SLATE, VIOLET, WARN, WASH, WASH2, WHITE,
                      arrow, bullets, card, chip, code, decision_slide, elbow,
                      eqn, kpi, legend, node, note, pic, pipeline, qa, rect,
                      section, slide, table, title_slide, txt)


def build(prs):
    # ------------------------------------------------------------ 1 title --
    s = title_slide(
        prs,
        "RoboSketch-RL",
        "Vision-Guided Reinforcement Learning for\nAutonomous Robotic Drawing",
        "Progress Review  ·  Phases A–C complete\nSimulator, perception and first learned policies",
        "M.Tech Research Project\n6 August 2026",
        tagline="Teaching a low-cost robotic arm to LEARN to draw — not programming it to draw.")
    note(s, """
Opening line: "This project asks whether a low-cost robotic arm can LEARN to draw
by trial and error, guided by what a camera sees — instead of replaying a
trajectory a human computed for it."

Where we are: the simulator, the perception pipeline and the reinforcement-learning
environment are all built and validated, and a PPO agent has already learned to
draw a line, circle, square and triangle from scratch. Everything in this deck is
a measured result from the project's research log, not a plan.

Deck structure: overview -> system vision -> completed work -> technical design ->
programming -> RL design -> mathematics -> vision -> timeline -> roadmap ->
anticipated questions -> backup slides.
""")

    # ----------------------------------------------------------- 2 agenda --
    s = slide(prs, "What this deck covers", "agenda",
              "Twelve sections: where we are, how it is built, why every choice was made, and what comes next.")
    items = [
        ("01", "Project overview", "Problem, motivation, objectives, contributions", PRIMARY),
        ("02", "Overall system vision", "Architecture, learning pipeline, why RL", PRIMARY),
        ("03", "Progress so far", "Every completed stage: what / why / alternatives / result", GOOD),
        ("04", "Technical design", "Modules, data flow, MDP, environment, coordinates", ACCENT),
        ("05", "Programming details", "Languages, libraries, classes, code flow", ACCENT),
        ("06", "Reinforcement-learning design", "State, action, reward, training strategy", VIOLET),
        ("07", "Mathematical foundations", "Transforms, kinematics, reward, optimisation", VIOLET),
        ("08", "Computer vision", "Acquisition, preprocessing, similarity metrics", ACCENT),
        ("09", "Development timeline", "Research -> design -> build -> results", SLATE),
        ("10", "Future roadmap", "Experiments, hardware, letters, publication", WARN),
        ("11", "Anticipated questions", "Prepared answers with evidence", NAVY),
        ("12", "Backup slides", "Definitions, derivations, literature, references", NAVY),
    ]
    colw, x0, y0, hgt = (CW - 0.26) / 2, M, 1.58, 0.42
    for i, (num, ttl, sub, col) in enumerate(items):
        cx = x0 + (i % 2) * (colw + 0.26)
        cy = y0 + (i // 2) * (hgt + 0.10)
        rect(s, cx, cy, colw, hgt, fill=WASH, line=None,
             shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.08)
        rect(s, cx, cy, 0.045, hgt, fill=col)
        txt(s, cx + 0.16, cy + 0.09, 0.42, 0.26, num, size=12, color=col, bold=True)
        txt(s, cx + 0.62, cy + 0.055, 3.2, 0.28, ttl, size=12.5, color=INK, bold=True)
        txt(s, cx + 0.62, cy + 0.235, colw - 0.78, 0.24, sub, size=9.5, color=MUTED)
    txt(s, M, 6.52, CW, 0.3,
        "Every design decision in this deck answers five questions: what did we do · why · how does it work · "
        "what else was possible · why is this better.",
        size=11, color=MUTED, italic=True, align=PP_ALIGN.CENTER)
    note(s, """
Tell the guide how to navigate: sections 1-2 are the conceptual frame, section 3 is
the evidence of work done, sections 4-8 are the technical depth (design, code,
RL, maths, vision), 9-10 are timeline and plan, and 11-12 are prepared answers and
backup material.

If time is short, the essential path is: 04 (problem) -> 10 (architecture) ->
15 (progress board) -> 30 (results) -> 74 (roadmap).
""")

    # =================================================== SECTION 1 =========
    section(prs, 1, "Project Overview",
            "The research problem, why it matters, what we set out to answer, and what this "
            "work will contribute to the literature.",
            ["Problem statement", "Motivation", "Research objectives",
             "Hypotheses H1–H4", "Expected contributions"])

    # ------------------------------------------------- 4 problem statement --
    s = slide(prs, "Problem statement", "01 · project overview")
    rect(s, M, 1.52, CW, 0.92, fill=WASH2, line=None,
         shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.05)
    rect(s, M, 1.52, 0.06, 0.92, fill=PRIMARY)
    txt(s, M + 0.28, 1.66, CW - 0.6, 0.7,
        "Can a low-cost robotic arm learn to draw geometric shapes accurately "
        "through reinforcement learning guided by visual feedback, instead of "
        "executing pre-computed trajectories?",
        size=17, color=INK, bold=True, spacing=1.22)

    y = 2.72
    node(s, M, y, 5.6, 1.62, "THE CONVENTIONAL WAY  —  programmed",
         "A human derives the path, solves inverse kinematics offline, and the arm\n"
         "replays the joint angles open-loop. The robot never perceives the result.\n"
         "Change the pen, the paper height or the arm — and it silently fails.",
         color=BAD, fill=WHITE, title_size=12, sub_size=10.5)
    node(s, M + 6.57, y, 5.6, 1.62, "THIS PROJECT  —  learned",
         "The arm is given a goal image and a way to SEE what it drew. It discovers\n"
         "the motion itself by trial and error, scored on how closely the drawing\n"
         "matches the target. The skill is learned, so it can adapt.",
         color=GOOD, fill=WHITE, title_size=12, sub_size=10.5)
    arrow(s, M + 5.72, y + 0.81, M + 6.45, y + 0.81, color=SLATE, lw=1.6)

    y2 = 4.62
    txt(s, M, y2, CW, 0.28, "THE THREE HARD PARTS OF THAT QUESTION", size=10.5,
        color=PRIMARY, bold=True)
    parts = [
        ("Perception", "The robot must judge its own drawing from a camera image, "
                       "not from privileged internal coordinates.", ACCENT),
        ("Credit assignment", "A drawing is hundreds of tiny motions; the reward must "
                              "tell the agent which of them helped.", VIOLET),
        ("Transfer", "A policy learned in simulation must survive the move to real, "
                     "imprecise, ~Rs.10,000 hardware.", WARN),
    ]
    cw3 = (CW - 0.44) / 3
    for i, (t, b, c) in enumerate(parts):
        card(s, M + i * (cw3 + 0.22), y2 + 0.32, cw3, 1.36, t, b, accent=c,
             body_size=10.5)
    note(s, """
Say the problem statement out loud from the box — it is the one fixed element of
the project; everything technical below it is deliberately flexible.

The contrast slide is the heart of the pitch. A pre-programmed drawing robot is a
solved, 40-year-old problem: you compute the trajectory, run inverse kinematics
offline, and replay joint angles. It works only because the world is exactly as
assumed. Our robot instead receives a GOAL and FEEDBACK, and must find the motion
itself.

If asked "isn't drawing a circle trivial?": yes — drawing IS trivial; LEARNING to
draw is not. The circle is the measuring instrument, not the product. The product
is a system that improves from experience, which is what generalises to welding
along a seam the robot can see, or writing on a surface that moved.

The three hard parts are the honest technical difficulties, and each maps to a
later section: perception -> section 8, credit assignment -> section 6 reward
design, transfer -> section 10 sim-to-real.
""")

    # ---------------------------------------------------- 5 motivation ------
    s = slide(prs, "Motivation — why this problem is worth solving", "01 · project overview")
    left = M
    txt(s, left, 1.50, 5.9, 0.28, "THE SCIENTIFIC MOTIVATION", size=10.5,
        color=PRIMARY, bold=True)
    bullets(s, [
        "Drawing is a **precision, continuous-control, closed-loop** task with an "
        "objective, pixel-level score — rare and valuable as an RL benchmark.".replace("**", ""),
        "It exposes the sim-to-real gap sharply: 1 mm of error is visible to the eye "
        "and measurable in IoU.",
        "It isolates a real open question — does learning from a CAMERA match learning "
        "from perfect internal coordinates?",
        "Most published drawing robots are trajectory players; learned, vision-scored "
        "drawing on low-cost hardware is far less studied.",
    ], left, 1.82, 5.9, 2.2, size=12)

    txt(s, left, 4.10, 5.9, 0.28, "THE PRACTICAL MOTIVATION", size=10.5,
        color=ACCENT, bold=True)
    bullets(s, [
        "Under Rs.10,000 of hardware — the science is reproducible by any student lab.",
        "Everything before hardware is free: simulation costs only CPU time.",
        "The result is visible. You can literally watch the policy improve.",
    ], left, 4.42, 5.9, 1.5, size=12, bullet_color=ACCENT)

    rx = M + 6.35
    txt(s, rx, 1.50, CW - 6.35, 0.28, "THE SAME SKILL, ELSEWHERE", size=10.5,
        color=VIOLET, bold=True)
    apps = [
        ("Manufacturing", "Welding / gluing / sealing along a seam the robot sees, even when the part shifts."),
        ("Electronics", "Placing small components using camera feedback rather than perfect positioning."),
        ("Healthcare", "Assistive and surgical tools that correct in real time from what they observe."),
        ("Documents", "Handwriting, signature reproduction, automated form filling."),
        ("Education & art", "Machines that demonstrate motor skills or produce physical artwork."),
    ]
    for i, (t, b) in enumerate(apps):
        cy = 1.84 + i * 0.94
        rect(s, rx, cy, CW - 6.35, 0.84, fill=WASH, line=None,
             shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.06)
        rect(s, rx, cy, 0.045, 0.84, fill=VIOLET)
        txt(s, rx + 0.18, cy + 0.09, 2.0, 0.26, t, size=11.5, color=VIOLET, bold=True)
        txt(s, rx + 0.18, cy + 0.35, CW - 6.75, 0.44, b, size=10.5, color=BODY,
            spacing=1.12)
    note(s, """
Lead with the scientific motivation — a guide cares more about why this is a
research problem than about the application list.

Key argument: drawing is one of the few manipulation tasks with a dense, objective,
pixel-level ground truth. You can score every attempt exactly (IoU against the
target), which makes it an unusually clean testbed for questions about reward
design and sim-to-real transfer.

The practical motivation matters for feasibility: total hardware cost stays under
Rs.10,000, and every result so far cost nothing but CPU time.

The applications column answers "so what?" — the transferable skill is
"learn a precise, vision-guided motion", which is exactly what seam welding,
component placement and assistive robotics need.
""")

    # -------------------------------------------- 6 objectives + questions --
    s = slide(prs, "Research objectives and questions", "01 · project overview")
    txt(s, M, 1.48, 5.85, 0.28, "OBJECTIVES", size=10.5, color=PRIMARY, bold=True)
    objs = [
        ("O1", "Build a physics-accurate simulated drawing system: arm, pen, paper, ink."),
        ("O2", "Build a perception pipeline that recovers the drawing from a camera image."),
        ("O3", "Formulate drawing as a Markov Decision Process and design a reward that "
               "makes it learnable."),
        ("O4", "Train and compare RL agents (PPO, then SAC) across a curriculum of shapes."),
        ("O5", "Compare a vision-based reward against a ground-truth reward."),
        ("O6", "Transfer the learned policy to a low-cost physical arm and quantify the gap."),
        ("O7", "Publish a reproducible, low-cost benchmark and the accompanying study."),
    ]
    for i, (k, t) in enumerate(objs):
        cy = 1.80 + i * 0.53
        chip(s, M, cy + 0.03, 0.42, 0.26, k, color=PRIMARY, fill=WASH2, size=9.5)
        txt(s, M + 0.54, cy, 5.3, 0.5, t, size=11.5, color=BODY, spacing=1.14)

    rx = M + 6.35
    txt(s, rx, 1.48, CW - 6.35, 0.28, "RESEARCH QUESTIONS", size=10.5, color=VIOLET,
        bold=True)
    rqs = [
        ("RQ1", "Can a low-cost arm learn to draw recognisable shapes from scratch, "
                "with no scripted trajectory?", GOOD, "answered in sim — see §3"),
        ("RQ2", "Does a vision-based reward work as well as a ground-truth reward?",
         WARN, "baseline built; vision arm next"),
        ("RQ3", "Which algorithm learns faster and more reliably — PPO or SAC?",
         WARN, "PPO done; SAC next"),
        ("RQ4", "Which reward formulation gives the fastest, most stable learning?",
         GOOD, "4 designs already compared"),
        ("RQ5", "Do pen-space actions transfer to hardware better than joint-space?",
         MUTED, "planned, phase D"),
        ("RQ6", "How accurately can geometric shapes be reproduced, and where does "
                "accuracy break down?", GOOD, "IoU 0.42–0.51 baseline"),
    ]
    for i, (k, t, c, st) in enumerate(rqs):
        cy = 1.80 + i * 0.86
        rect(s, rx, cy, CW - 6.35, 0.76, fill=WASH, line=None,
             shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.06)
        rect(s, rx, cy, 0.045, 0.76, fill=c)
        txt(s, rx + 0.18, cy + 0.07, 0.6, 0.24, k, size=10.5, color=c, bold=True)
        txt(s, rx + 0.80, cy + 0.06, CW - 7.4, 0.48, t, size=10.5, color=BODY,
            spacing=1.12)
        txt(s, rx + 0.80, cy + 0.52, CW - 7.4, 0.22, st, size=9, color=c, italic=True)
    note(s, """
Objectives are what we BUILD; research questions are what we ANSWER. Guides often
probe whether a student can tell those apart, so state it explicitly.

Status colours on the right: green = evidence already in hand, amber = in flight,
grey = planned. O1-O3 are complete, O4 is partially complete (PPO done, SAC next),
O5-O7 are ahead of us.

RQ4 is worth dwelling on: we did not just pick a reward — we ran four distinct
reward designs and documented the failure mode of each. That comparison is itself
a contribution and is covered in detail on the reward-iteration slide.
""")

    # ------------------------------------------------------ 7 hypotheses ----
    s = slide(prs, "Hypotheses under test", "01 · project overview",
              "Each hypothesis has a defined test, a metric, and a control condition — so it can actually be falsified.")
    table(s, ["", "Hypothesis", "How it is tested", "Metric", "Status"],
          [["H1", "A low-cost arm can learn to draw basic shapes with vision-guided RL",
            "Train on the shape ladder; compare against an untrained policy and a "
            "scripted IK baseline", "IoU, coverage, success rate",
            "supported in sim"],
           ["H2", "A vision-based reward works as well as (or better than) a "
                  "ground-truth reward",
            "Train two identical agents; swap only the reward source",
            "final IoU, sample efficiency", "baseline done"],
           ["H3", "Pen-space actions transfer to hardware better than joint-space actions",
            "Train both action parameterisations; measure the sim-to-real drop",
            "IoU(sim) − IoU(real)", "planned"],
           ["H4", "One algorithm (PPO vs SAC) learns faster / more reliably for this task",
            "Identical env, reward and budget; 3 seeds each",
            "learning curves, variance", "PPO done"]],
          M, 1.90, CW, colw=[0.5, 3.3, 3.6, 2.0, 1.5], size=10.5, row_h=0.86,
          header_h=0.36,
          cell_colors={(0, 4): GOOD, (1, 4): WARN, (2, 4): MUTED, (3, 4): WARN},
          bold_col0=True)
    txt(s, M, 5.55, CW, 0.28, "THE CONTROL CONDITION — why the 'baseline' work is not throwaway",
        size=10.5, color=PRIMARY, bold=True)
    rect(s, M, 5.86, CW, 0.86, fill=WASH2, line=None,
         shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.05)
    txt(s, M + 0.24, 5.98, CW - 0.5, 0.66,
        "H2 requires BOTH a ground-truth-reward agent and a vision-reward agent to compare. "
        "That is why we deliberately built the ground-truth version first: it is experimental "
        "condition #1, the control group — not a stepping stone we throw away. It also honours "
        "the change-one-variable-at-a-time principle: get a known-working system, then swap "
        "only the reward.",
        size=11.5, color=BODY, spacing=1.2)
    note(s, """
This slide pre-empts a very likely question: "why did you build a ground-truth
reward if the whole point is vision?"

Answer: because H2 is a comparison. You cannot claim a vision reward is as good as
a ground-truth reward without running both. The ground-truth agent IS the control
group. Building it first also follows the change-one-variable principle: we now
have a known-good system in which only the reward source changes.

H1 is "supported in sim" — be careful with wording. We have evidence in simulation
across four shapes; the hardware half of H1 is not yet tested. Never overclaim.

H3 and H4 are honest future work; the environment was designed so both can be run
by changing one flag or one class.
""")

    # -------------------------------------------------- 8 contributions -----
    s = slide(prs, "Expected contributions", "01 · project overview")
    conts = [
        ("C1", "A reproducible low-cost benchmark",
         "An open simulated drawing environment (Gymnasium-compatible) plus a "
         "sub-Rs.10,000 hardware recipe, so others can repeat and extend the study.",
         PRIMARY),
        ("C2", "An empirical reward-design study for stroke drawing",
         "Four documented reward formulations with their failure modes — the "
         "'draw-nothing', 'don't-move', 'scribble' and 'central-blob' local optima, "
         "and the fix for each.", VIOLET),
        ("C3", "A controlled vision-reward vs ground-truth-reward comparison",
         "The same agent, same environment, only the reward source changed — a "
         "clean answer to whether camera feedback is sufficient.", ACCENT),
        ("C4", "A quantified sim-to-real gap for drawing on low-cost hardware",
         "IoU measured in simulation and on the physical arm, with the "
         "pen-space vs joint-space action comparison that explains part of it.", WARN),
        ("C5", "An engineering account of the non-obvious failures",
         "Measured, documented traps: centre-of-mass vs link-frame readout, "
         "null-space IK degradation, invisible debug-line ink, texture caching — "
         "each cost hours and none are in the tutorials.", GOOD),
    ]
    for i, (k, t, b, c) in enumerate(conts):
        cy = 1.56 + i * 1.06
        rect(s, M, cy, CW, 0.94, fill=WASH, line=LINE,
             shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.05)
        rect(s, M, cy, 0.055, 0.94, fill=c)
        chip(s, M + 0.20, cy + 0.30, 0.46, 0.30, k, color=c, fill=WHITE, size=10.5)
        txt(s, M + 0.82, cy + 0.13, 4.4, 0.34, t, size=12.5, color=INK, bold=True,
            spacing=1.05)
        txt(s, M + 0.82, cy + 0.47, 4.4, 0.4, "", size=8, color=WHITE)
        txt(s, M + 5.35, cy + 0.16, CW - 5.6, 0.7, b, size=11, color=BODY, spacing=1.16)
    note(s, """
Distinguish contributions from objectives: objectives are tasks, contributions are
what the community gets.

C5 deserves emphasis with a research guide. Reproducibility failures in robotics
are usually caused by exactly this class of undocumented trap — and we have them
measured, not anecdotal. Every one is recorded in docs/RESEARCH_LOG.md with the
experiment that exposed it.

Be honest about novelty: RL, IK and OpenCV are all standard. The contribution is in
the combination, the controlled comparisons, and the rigour of the reproducible
low-cost study. That is a legitimate contribution and we should say so plainly
rather than overclaim a new algorithm.
""")

    # =================================================== SECTION 2 =========
    section(prs, 2, "Overall System Vision",
            "How the pieces fit together end to end — from a target image, through the "
            "learning loop, to ink on paper — and why learning is the right tool here.",
            ["End-to-end architecture", "The learning loop",
             "Input → drawing workflow", "Why RL, not programming"])

    # ------------------------------------------------- 10 architecture ------
    s = slide(prs, "End-to-end system architecture", "02 · system vision",
              "Four layers. The agent only ever speaks pen-space; every arm-specific detail is confined to the bottom layer.")
    lanes = [
        ("LEARNING", VIOLET, 1.66),
        ("TASK / REWARD", GOOD, 2.80),
        ("PERCEPTION", ACCENT, 3.94),
        ("EMBODIMENT", PRIMARY, 5.08),
    ]
    for name, col, y in lanes:
        rect(s, M, y, 1.55, 0.92, fill=WASH, line=None,
             shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.08)
        rect(s, M, y, 0.05, 0.92, fill=col)
        txt(s, M + 0.16, y + 0.30, 1.34, 0.36, name, size=10, color=col, bold=True,
            spacing=1.0)

    bx = M + 1.78
    FLOW_W = CW - 1.05                      # right gutter reserved for the feedback loop
    bw = (FLOW_W - 1.78 - 0.66) / 3
    def row(y, col, boxes):
        for i, (t, sb) in enumerate(boxes):
            node(s, bx + i * (bw + 0.33), y, bw, 0.92, t, sb, color=col, fill=WHITE,
                 title_size=11, sub_size=9)

    row(1.66, VIOLET, [("Policy π(a|s)", "CNN over a 64×64×3 observation"),
                       ("PPO / SAC", "Stable-Baselines3 optimiser"),
                       ("Action  [dx, dy, pen]", "a nudge in pen space")])
    row(2.80, GOOD, [("Target shape", "rl/targets.py — binary mask"),
                     ("Reward function", "IoU-delta + proximity shaping"),
                     ("Episode logic", "reset / step / terminate")])
    row(3.94, ACCENT, [("Virtual camera", "top-down RGB + segmentation"),
                       ("OpenCV extraction", "crop → threshold → binarise"),
                       ("Metrics", "IoU · MSE · coverage · chamfer")])
    row(5.08, PRIMARY, [("Inverse kinematics", "pen (x,y) → 7 joint angles"),
                        ("PyBullet physics", "KUKA iiwa + paper mesh"),
                        ("Canvas / ink", "the authoritative drawing")])

    for i in range(3):
        cx = bx + i * (bw + 0.33) + bw / 2
        arrow(s, cx, 2.62, cx, 2.76, color=FAINT, lw=1.0)
        arrow(s, cx, 3.76, cx, 3.90, color=FAINT, lw=1.0)
        arrow(s, cx, 4.90, cx, 5.04, color=FAINT, lw=1.0)
    right = bx + 3 * bw + 2 * 0.33          # right edge of the flow columns
    loop_x = right + 0.55
    elbow(s, [(right + 0.04, 5.54), (loop_x, 5.54), (loop_x, 2.12),
              (right + 0.04, 2.12)], color=SLATE, lw=1.5)
    txt(s, loop_x + 0.06, 3.28, 1.0, 0.3, "feedback", size=9.5, color=SLATE, bold=True)
    txt(s, loop_x + 0.06, 3.54, 1.0, 0.7, "reward +\nnew state", size=8.5,
        color=MUTED, spacing=1.2)
    txt(s, M, 6.42, CW, 0.32,
        "Portability principle: the agent decides in PEN space; only the Embodiment layer knows what an arm is. "
        "Swapping the KUKA for the real 6-DOF arm changes the URDF and the IK call — the learned brain is untouched.",
        size=11, color=MUTED, italic=True)
    note(s, """
Walk it top-down, then close the loop.

LEARNING: a convolutional policy reads a small 3-channel image and outputs a
continuous action - a small nudge of the pen plus a pen-down signal.

TASK/REWARD: the target shape and the scoring live here. This layer decides what
"good" means. It is deliberately separate from the agent so we can swap the reward
(ground truth vs vision) without touching the policy - that is exactly what H2
needs.

PERCEPTION: the camera and OpenCV. Today it validates the pipeline; in the H2
experiment it becomes the reward source; on hardware it is the ONLY source.

EMBODIMENT: inverse kinematics turns the pen-space decision into joint angles;
PyBullet simulates the physics; the numpy canvas records the ink.

The key architectural claim - and a likely question - is the portability principle
at the bottom. Because the action is a pen-space nudge, everything arm-specific is
isolated in one layer. That is what makes H3 (pen-space vs joint-space transfer)
testable and what makes the policy portable to the real arm.
""")

    # -------------------------------------------------- 11 learning loop ----
    s = slide(prs, "The learning pipeline", "02 · system vision",
              "One interaction — state, action, reward — repeated hundreds of thousands of times.")
    cx, cy = 4.05, 4.05
    node(s, 1.05, 3.35, 2.75, 1.30, "AGENT", "policy π_θ(a | s)\nCNN + PPO", color=VIOLET,
         fill=WASH, title_size=14, sub_size=10.5)
    node(s, 8.55, 3.35, 3.72, 1.30, "ENVIRONMENT  (DrawEnv)",
         "pen kinematics · canvas · target\nreward · episode bookkeeping",
         color=GOOD, fill=WASH, title_size=14, sub_size=10.5)

    elbow(s, [(3.85, 3.70), (6.20, 3.70), (6.20, 3.62), (8.50, 3.62)], color=PRIMARY, lw=1.8)
    txt(s, 5.05, 3.22, 2.6, 0.5, "action  aₜ = [dx, dy, pen]", size=11.5, color=PRIMARY,
        bold=True, align=PP_ALIGN.CENTER)
    elbow(s, [(8.50, 4.30), (6.20, 4.30), (6.20, 4.38), (3.85, 4.38)], color=ACCENT, lw=1.8)
    txt(s, 4.95, 4.46, 2.8, 0.7, "state  sₜ₊₁ (64×64×3 image)\nreward  rₜ (a single number)",
        size=11.5, color=ACCENT, bold=True, align=PP_ALIGN.CENTER, spacing=1.15)

    node(s, 1.05, 1.62, 2.75, 1.28, "OBJECTIVE",
         "maximise expected return\nJ(θ) = E[ Σ γᵗ rₜ ]", color=VIOLET, fill=WHITE,
         title_size=11.5, sub_size=10)
    arrow(s, 2.42, 2.94, 2.42, 3.31, color=VIOLET, lw=1.3)
    node(s, 8.55, 1.62, 3.72, 1.28, "WHAT THE ENVIRONMENT HOLDS",
         "target mask · numpy canvas · pen (x,y)\ndistance transform · step counter",
         color=GOOD, fill=WHITE, title_size=11.5, sub_size=10)
    arrow(s, 10.4, 2.94, 10.4, 3.31, color=GOOD, lw=1.3)

    txt(s, M, 5.28, CW, 0.28, "ONE EPISODE  =  ONE ATTEMPT AT THE DRAWING", size=10.5,
        color=PRIMARY, bold=True)
    pipeline(s, [("reset()", "blank canvas,\npen at centre"),
                 ("step ×240", "nudge · ink ·\nscore · observe"),
                 ("terminate", "IoU ≥ 0.60\nor step limit"),
                 ("return", "Σ rewards →\npolicy update"),
                 ("repeat", "≈ 1,700 episodes\nper 400k steps")],
             M, 5.60, CW, 0.98,
             colors=[PRIMARY, ACCENT, GOOD, VIOLET, SLATE])
    note(s, """
This is the canonical RL loop; make sure it is stated in the language of THIS
project, because a guide will test whether the abstraction is understood concretely.

The agent sees a state (a small three-channel image), picks an action (a nudge of
the pen and a pen-down flag), and the environment returns the next state and a
scalar reward. Nothing else passes between them - the agent never receives joint
angles, and the environment never sees the network weights.

Numbers to have ready: an episode is 240 steps; 400,000 training steps is roughly
1,700 episodes; the kinematic backend runs about 420 environment steps per second
on CPU, so 400k steps is roughly 15-20 minutes of training per shape.

The objective box is the formal statement: maximise the expected discounted sum of
rewards, gamma = 0.99. Because our reward telescopes to the final IoU (proved in
section 7), maximising that return is literally maximising drawing accuracy.
""")

    # ------------------------------------------------------- 12 workflow ----
    s = slide(prs, "Workflow — from a target image to ink on paper", "02 · system vision")
    steps = [
        ("1  TARGET", "A shape is rendered as a binary mask\n(line / circle / square / triangle)",
         PRIMARY, "rl/targets.py"),
        ("2  OBSERVE", "Target + drawing-so-far + pen position\nstacked into a 64×64×3 image",
         ACCENT, "DrawEnv._obs()"),
        ("3  DECIDE", "The CNN policy outputs a continuous\npen nudge [dx, dy, pen_down]",
         VIOLET, "PPO CnnPolicy"),
        ("4  ACT", "IK converts the pen target into joint\nangles; the motors drive there",
         PRIMARY, "DrawEnv._move_arm()"),
        ("5  INK", "A segment is drawn on the canvas at the\npen's ACTUAL measured position",
         GOOD, "cv2.line on canvas"),
        ("6  SCORE", "IoU against the target → reward;\ncamera + OpenCV in the H2 condition",
         ACCENT, "rl/metrics.py"),
        ("7  LEARN", "PPO updates the policy from the\ncollected (s, a, r, s′) batch",
         VIOLET, "SB3 PPO.learn()"),
        ("8  DRAW", "The trained policy is replayed to\nproduce the final drawing",
         GOOD, "train.py evaluate()"),
    ]
    bw = (CW - 3 * 0.28) / 4
    for i, (t, b, c, f) in enumerate(steps):
        col, rw = i % 4, i // 4
        x = M + col * (bw + 0.28)
        y = 1.62 + rw * 2.05
        rect(s, x, y, bw, 1.72, fill=WHITE, line=LINE,
             shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.05)
        rect(s, x, y, bw, 0.36, fill=c, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.12)
        rect(s, x, y + 0.22, bw, 0.14, fill=c)
        txt(s, x + 0.14, y + 0.05, bw - 0.28, 0.28, t, size=11, color=WHITE, bold=True)
        txt(s, x + 0.14, y + 0.48, bw - 0.28, 0.8, b, size=10.5, color=BODY, spacing=1.18)
        txt(s, x + 0.14, y + 1.40, bw - 0.28, 0.24, f, size=9, color=MUTED, italic=True)
        if col < 3:
            arrow(s, x + bw + 0.03, y + 0.86, x + bw + 0.25, y + 0.86, color=SLATE, lw=1.3)
    elbow(s, [(M + 3 * (bw + 0.28) + bw / 2, 3.40), (M + 3 * (bw + 0.28) + bw / 2, 3.55),
              (M + bw / 2, 3.55), (M + bw / 2, 3.64)], color=SLATE, lw=1.3)
    elbow(s, [(M + 3 * (bw + 0.28) + bw / 2, 5.42), (M + 3 * (bw + 0.28) + bw / 2, 6.62),
              (M + bw / 2 + 0.9, 6.62)], color=VIOLET, lw=1.5, dashed=True)
    txt(s, M + 1.4, 6.44, 6.0, 0.3, "training loop — steps 2→7 repeat ≈400,000 times per shape",
        size=10, color=VIOLET, italic=True, bold=True)
    note(s, """
This is the same loop as the previous slide, but written as the concrete sequence a
guide can follow, with the file that implements each step.

Two subtleties worth pointing out because they show engineering judgement:

Step 5 - ink is deposited at the pen's ACTUAL measured position, not at the
position we commanded. When the arm backend is enabled, the motors lag the target
by a few millimetres, and the saved drawing records where the pen really went. That
means the agent learns to compensate for its own dynamics rather than being scored
on a fiction.

Step 4 is optional at training time. We run a kinematic backend (the pen point
moves directly) for fast RL iteration, and the full IK + physics backend when we
want realism. The drawing and reward logic are byte-identical in both - only the
means of moving the pen changes. That is what makes the comparison fair.
""")

    # ------------------------------------------------ 13 why RL ------------
    s = slide(prs, "Why reinforcement learning instead of traditional programming?",
              "02 · system vision")
    cols = [
        ("SCRIPTED TRAJECTORY", BAD, [
            "Human computes every waypoint; IK solved offline; arm replays angles.",
            "Open loop — it never looks at the paper.",
            "A shifted sheet, a worn pen or a servo with backlash breaks it silently.",
            "A new shape means new code written by a human.",
            "Verdict: solves DRAWING, not LEARNING TO DRAW. We keep it — as the "
            "non-learning baseline to compare against.",
        ]),
        ("SUPERVISED LEARNING", WARN, [
            "Needs labelled examples: 'in this state, the correct action is …'.",
            "Nobody knows the correct action — the optimal stroke sequence is not "
            "a known label.",
            "Producing labels would need an expert controller — the very thing we "
            "are trying to obtain.",
            "Cannot improve past the demonstrator; it imitates, it does not optimise.",
            "Verdict: wrong tool — no supervision signal exists.",
        ]),
        ("REINFORCEMENT LEARNING", GOOD, [
            "Needs only a SCORE, not a label — and we have an exact one: IoU with "
            "the target.",
            "Closed loop: the agent observes the drawing so far and reacts.",
            "Optimises the objective directly, discovering strategies no one wrote.",
            "Handles the sequential, delayed-credit nature of a stroke.",
            "Verdict: the natural formulation — 'act, observe, be scored, improve'.",
        ]),
    ]
    cw3 = (CW - 0.48) / 3
    for i, (t, c, items) in enumerate(cols):
        x = M + i * (cw3 + 0.24)
        rect(s, x, 1.52, cw3, 4.30, fill=WHITE, line=LINE,
             shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.04)
        rect(s, x, 1.52, cw3, 0.44, fill=c, shape=MSO_SHAPE.ROUNDED_RECTANGLE,
             radius=0.10)
        rect(s, x, 1.78, cw3, 0.18, fill=c)
        txt(s, x, 1.60, cw3, 0.3, t, size=12, color=WHITE, bold=True,
            align=PP_ALIGN.CENTER)
        bullets(s, items[:-1], x + 0.18, 2.10, cw3 - 0.36, 2.6, size=10.5,
                bullet_color=c)
        rect(s, x + 0.14, 5.06, cw3 - 0.28, 0.66, fill=WASH, line=None,
             shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.06)
        txt(s, x + 0.26, 5.14, cw3 - 0.52, 0.55, items[-1], size=10, color=c,
            bold=True, spacing=1.12)
    rect(s, M, 6.02, CW, 0.72, fill=WASH2, line=None,
         shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.05)
    txt(s, M + 0.24, 6.14, CW - 0.5, 0.5,
        "The honest framing: RL is not 'better at drawing a circle' — a scripted arm draws a "
        "cleaner circle today. RL is better at ACQUIRING the skill from feedback, which is what "
        "generalises when the world stops matching the assumptions.",
        size=11.5, color=INK, spacing=1.2, bold=True)
    note(s, """
This is the single most likely question in the viva, so answer it before it is
asked - and answer it honestly.

The scripted baseline is genuinely better at drawing a clean circle right now. Do
not pretend otherwise; we keep it deliberately as the non-learning control to
compare against, which is standard practice.

The real argument is about what is being solved. A scripted trajectory encodes a
human's solution; it cannot recover when the pen slips, the paper moves or a servo
has backlash, because it never perceives the result. RL encodes a way of ACQUIRING
solutions from feedback.

Why not supervised learning is the sharper technical point: supervised learning
needs (state, correct action) pairs, and no such label exists here. To generate one
you would need an expert controller - precisely what we are trying to learn. RL
needs only a scalar score, and IoU gives us an exact one. That is why the problem
is naturally an MDP and not a regression.
""")
