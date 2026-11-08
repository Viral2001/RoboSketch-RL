"""Deck part 4 - RL design, mathematical foundations, computer vision."""
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN

from deck_kit import (ACCENT, BAD, BODY, CW, FAINT, FM, GOOD, H, INK, LINE, M,
                      MUTED, NAVY, PRIMARY, SLATE, TINT_AMBER, TINT_BLUE,
                      TINT_GREEN, TINT_RED, TINT_VIOLET, VIOLET, W, WARN, WASH,
                      WASH2, WHITE, arrow, bullets, card, chip, code,
                      decision_slide, elbow, eqn, kpi, legend, node, note, pic,
                      pipeline, qa, rect, section, slide, table, txt)


def build(prs):
    # =================================================== SECTION 6 =========
    section(prs, 6, "Reinforcement-Learning Design",
            "Why the problem is posed as reinforcement learning at all, and the reasoning "
            "behind every element of the formulation the agent actually optimises.",
            ["Why RL, not supervision or scripting", "State & action spaces",
             "Reward anatomy", "Exploration vs exploitation", "Training strategy"])

    # ------------------------------------------------ 6.1 why RL (formal) --
    s = slide(prs, "Why this is a reinforcement-learning problem",
              "06 · rl design",
              "Three properties of the task force the formulation — none of them is a preference.")
    props = [
        ("1  ·  NO SUPERVISION SIGNAL EXISTS", VIOLET,
         "Supervised learning needs (state → correct action) pairs. Nobody knows the "
         "correct pen nudge at step 137 of drawing a circle. Producing labels would "
         "require an expert controller — precisely the thing we are trying to learn.",
         "RL needs only a SCALAR SCORE, and we have an exact one: IoU with the target."),
        ("2  ·  THE DECISION IS SEQUENTIAL, THE REWARD DELAYED", PRIMARY,
         "The quality of a drawing depends on a whole sequence of ~240 nudges. An early "
         "stroke in the wrong place cannot be undone. This is credit assignment over "
         "time — the defining feature of an MDP, not of a regression problem.",
         "RL's value function is exactly the machinery for propagating a late outcome "
         "back to the early actions that caused it."),
        ("3  ·  THE ENVIRONMENT IS CHEAP AND SAFE TO SAMPLE", GOOD,
         "RL's main practical cost is that it needs many interactions. In simulation an "
         "interaction costs ~2.4 ms and breaks nothing. That is what makes the method "
         "affordable here, and it is why simulation comes first.",
         "≈420 steps/second · 400,000 steps ≈ 16 minutes · nothing can be damaged."),
    ]
    for i, (t, c, body, punch) in enumerate(props):
        y = 1.58 + i * 1.62
        rect(s, M, y, CW, 1.44, fill=WHITE, line=LINE,
             shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.04)
        rect(s, M, y, 0.055, 1.44, fill=c)
        txt(s, M + 0.24, y + 0.14, 5.5, 0.3, t, size=12, color=c, bold=True)
        txt(s, M + 0.24, y + 0.50, 7.2, 0.85, body, size=11, color=BODY, spacing=1.18)
        rect(s, M + 7.75, y + 0.16, CW - 7.95, 1.12, fill=WASH, line=None,
             shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.05)
        txt(s, M + 7.95, y + 0.30, CW - 8.35, 0.9, punch, size=10.5, color=c,
            bold=True, spacing=1.2)
    rect(s, M, 6.46, CW, 0.44, fill=WASH2, line=None,
         shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.05)
    txt(s, M + 0.24, 6.54, CW - 0.5, 0.3,
        "And why not a predefined trajectory? Because that solves the instance, not the problem — "
        "it is our BASELINE, not our method.",
        size=11, color=INK, bold=True)
    note(s, """
This slide answers "why RL?" rigorously rather than rhetorically. The argument is
that three properties of the task force the formulation.

First, no supervision exists. This is the decisive one. Supervised learning needs
input-output pairs, and there is no ground-truth "correct pen nudge" for a given
partial drawing. To create such labels you would need an expert controller - which is
the thing we are trying to obtain. RL sidesteps this entirely: it needs only a score,
and IoU gives us an exact one.

Second, the problem is sequential with delayed reward. Whether a drawing is good
depends on a sequence of about 240 decisions, and early mistakes cannot be undone.
That is credit assignment over time, which is what value functions and temporal
difference methods exist to solve.

Third - and this is the practical justification - RL's main cost is sample hunger,
and in simulation samples are nearly free and completely safe. About 420 steps per
second, no wear, no breakage. That is also the argument for doing simulation before
hardware.

Close with the baseline point: a predefined trajectory is not a rival method we
rejected, it is the control condition we will measure against.
""")

    # --------------------------------------------- 6.2 state / action ------
    s = slide(prs, "State and action spaces", "06 · rl design")
    txt(s, M, 1.46, 6.0, 0.28, "OBSERVATION SPACE — Box(0, 255, (64, 64, 3), uint8)",
        size=10.5, color=VIOLET, bold=True)
    chans = [("channel 0", "TARGET", "the shape to reproduce", VIOLET),
             ("channel 1", "DRAWN", "everything inked so far", GOOD),
             ("channel 2", "PEN", "marker: 255 = down, 128 = up", ACCENT)]
    for i, (k, t, d, c) in enumerate(chans):
        y = 1.80 + i * 0.72
        rect(s, M, y, 5.95, 0.62, fill=WHITE, line=LINE,
             shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.04)
        rect(s, M, y, 0.05, 0.62, fill=c)
        rect(s, M + 0.20, y + 0.11, 0.40, 0.40, fill=c,
             shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.15)
        txt(s, M + 0.78, y + 0.06, 1.5, 0.26, t, size=11, color=c, bold=True)
        txt(s, M + 0.78, y + 0.30, 1.5, 0.24, k, size=8.5, color=MUTED, font=FM)
        txt(s, M + 2.45, y + 0.17, 3.3, 0.32, d, size=10.5, color=BODY)
    bullets(s, [
        "Why an IMAGE and not a feature vector: the target must be part of the state or "
        "the policy can only learn one shape. An image carries target, progress and pen "
        "position with no hand-engineered features — and it scales to letters.",
        "Why it is MARKOV: the canvas contains every past stroke, so the observation "
        "summarises the entire history. No recurrence needed.",
        "Why 64×64: large enough to see the shape, small enough for fast CPU training. "
        "The canvas itself is kept at 128² so ink is not lost to downsampling before "
        "scoring.",
        "Why INTER_AREA resizing: it area-averages, so a thin stroke survives "
        "downsampling instead of disappearing between sample points.",
    ], M, 4.00, 5.95, 2.6, size=10.5, bullet_color=VIOLET)

    rx = M + 6.30
    txt(s, rx, 1.46, CW - 6.30, 0.28, "ACTION SPACE — Box(low=[−1,−1,0], high=[1,1,1])",
        size=10.5, color=PRIMARY, bold=True)
    table(s, ["component", "range", "meaning"],
          [["dx", "[−1, 1]", "pen displacement along world +x, scaled by step_size (0.014 m)"],
           ["dy", "[−1, 1]", "pen displacement along world +y, same scaling"],
           ["pen_down", "[0, 1]", "> 0.5 means ink; currently forced ON for single-stroke shapes"]],
          rx, 1.78, CW - 6.30, colw=[1.3, 1.1, 4.0], size=10, row_h=0.52, header_h=0.32)
    txt(s, rx, 3.58, CW - 6.30, 0.28, "PEN SPACE  vs  JOINT SPACE  —  hypothesis H3",
        size=10.5, color=PRIMARY, bold=True)
    cw2 = (CW - 6.30 - 0.20) / 2
    card(s, rx, 3.90, cw2, 2.70, "PEN (TASK) SPACE   ✓ chosen",
         ["3-dimensional, independent of the arm.",
          "Portable: a different arm needs only a new URDF + IK.",
          "Matches how a human thinks about drawing.",
          "Costs an IK solve per step, and inherits IK's failure modes near the "
          "workspace edge.",
          "IK is seeded from the current pose, so small nudges track far better than "
          "jumps — which is exactly what drawing does."],
         accent=GOOD)
    card(s, rx + cw2 + 0.20, 3.90, cw2, 2.70, "JOINT SPACE  ·  H3 rival",
         ["7-dimensional for the KUKA, 6 for the target hardware — the action space "
          "changes with the arm.",
          "No IK needed; the policy can exploit the arm's true dynamics.",
          "Not portable: a policy learned here is tied to one arm.",
          "Larger action space → slower exploration.",
          "Expected to suffer more in sim-to-real, since it encodes the simulated arm's "
          "exact geometry. That is the hypothesis to test."],
         accent=SLATE)
    note(s, """
On the observation, the question to anticipate is "why not just give it the pen
coordinates and a few numbers - it would train much faster?"

The answer has two parts. Practically, the target has to be in the state somehow, or
the policy is hard-wired to one shape; encoding an arbitrary shape as a small vector
means hand-designing features, and those features would have to change for letters.
Scientifically, we want the same representation across the whole task ladder so
results are comparable from a line all the way to handwriting. A vector-state ablation
would actually be an interesting extra experiment, and it is worth offering that.

The Markov property is worth stating explicitly because it is the formal requirement
for an MDP: the current observation must be sufficient to act optimally. Our canvas
channel accumulates every stroke, so the observation summarises the history and no
recurrent network is needed.

On the action space, the pen-versus-joint comparison IS hypothesis H3, so present it
as a genuine open question rather than a settled preference. Our expectation is that
pen space transfers better because it does not encode the simulated arm's exact
geometry, but that is precisely what the experiment is for.
""")

    # ------------------------------------------------ 6.3 reward anatomy ---
    s = slide(prs, "Anatomy of the reward function", "06 · rl design",
              "Four terms. Each exists to defeat a specific failure mode we actually observed.")
    eqn(s, M, 1.60, CW,
        ["rₜ  =  w_iou · (IoUₜ − IoUₜ₋₁)   +   w_prox · (Φₜ − Φₜ₋₁)   −   w_smooth · |aₜ − aₜ₋₁|   −   c_time   (+ 2 on success)",
         "with  w_iou = 10,   w_prox = 0.4,   w_smooth = 0.02,   c_time = 0,   Φ(s) = − dist(pen, nearest target pixel)"],
        size=13.5, h=1.02)
    terms = [
        ("IoU-DELTA   w = 10", GOOD,
         "The main objective. Rewards covering the target AND penalises stray ink, "
         "because stray ink lowers IoU.",
         "Defeats: the SCRIBBLE optimum. A coverage-only reward is gamed by scrawling "
         "over the whole region; with IoU-delta that behaviour is self-punishing.",
         "Telescopes: Σ ΔIoU = IoU_final − IoU_0, so maximising return = maximising "
         "accuracy."),
        ("PROXIMITY SHAPING   w = 0.4", VIOLET,
         "Φ = −(distance from the pen to the nearest target pixel), read from a "
         "precomputed distance transform.",
         "Defeats: the DRAW-NOTHING optimum. On a thin target, random exploration almost "
         "never scores, so 'never ink' is the safe policy.",
         "Potential-based, so by Ng et al. (1999) it provably does NOT change which "
         "policy is optimal — only how easy it is to find."),
        ("SMOOTHNESS   w = 0.02", ACCENT,
         "Penalises the change in action between consecutive steps.",
         "Defeats: the ZIGZAG artefact. Without it the agent swept the full line but "
         "wobbled vertically.",
         "Must be SCALED: at w = 0.15 it accumulated to −24 over 240 steps, swamped the "
         "IoU signal, and the agent simply stopped moving."),
        ("SUCCESS BONUS   +2", PRIMARY,
         "Granted once when IoU ≥ 0.60 and the episode terminates.",
         "Defeats: indifference to finishing. Gives a clear, reachable goal rather than "
         "an endless gradient.",
         "Set to a REACHABLE threshold — an unreachable bonus is equivalent to no bonus, "
         "and adds variance for nothing."),
    ]
    cw2 = (CW - 0.28) / 2
    for i, (t, c, what, defeats, note_) in enumerate(terms):
        x = M + (i % 2) * (cw2 + 0.28)
        y = 2.86 + (i // 2) * 2.00
        rect(s, x, y, cw2, 1.84, fill=WHITE, line=LINE,
             shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.04)
        rect(s, x, y, 0.05, 1.84, fill=c)
        txt(s, x + 0.20, y + 0.10, cw2 - 0.4, 0.26, t, size=11, color=c, bold=True)
        txt(s, x + 0.20, y + 0.38, cw2 - 0.4, 0.46, what, size=10, color=BODY,
            spacing=1.14)
        txt(s, x + 0.20, y + 0.88, cw2 - 0.4, 0.5, defeats, size=10, color=BAD,
            spacing=1.14)
        txt(s, x + 0.20, y + 1.40, cw2 - 0.4, 0.4, note_, size=9.5, color=MUTED,
            spacing=1.14, italic=True)
    note(s, """
Present each term as the answer to a failure we actually observed, not as a term we
guessed at.

The IoU-delta weight of 10 is not arbitrary - IoU changes by tiny amounts per step,
so without scaling the signal would be dwarfed by the shaping terms. The telescoping
property is the elegant part and worth stating: because each reward is a DIFFERENCE
in IoU, the sum over an episode collapses to the final IoU minus the initial. So
maximising return literally maximises drawing accuracy - there is no proxy objective.

The proximity term is the theoretically interesting one. It is potential-based, which
means it is written as the difference of a function of state. Ng, Harada and Russell
proved in 1999 that shaping of this form leaves the optimal policy unchanged. That is
why we can add dense guidance without worrying that we have quietly changed the task -
a very common way to break an RL experiment.

The smoothness weight carries a tuning lesson worth telling: at 0.15 it accumulated
to about -24 over an episode, which swamped the IoU term, and the agent learned to
stop moving. At 0.02 it contributes about -3, comparable to the IoU term, and it
straightened the stroke. Reward terms must be scaled relative to one another, not set
independently.
""")

    # ------------------------------------- 6.4 exploration / training ------
    s = slide(prs, "Exploration, exploitation and training strategy", "06 · rl design")
    txt(s, M, 1.46, 6.0, 0.28, "THE EXPLORATION PROBLEM, CONCRETELY", size=10.5,
        color=VIOLET, bold=True)
    rect(s, M, 1.76, 5.95, 1.34, fill=TINT_VIOLET, line=None,
         shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.05)
    txt(s, M + 0.24, 1.88, 5.5, 1.1,
        "The target occupies roughly 5 % of the canvas. A randomly moving pen almost never "
        "traces it, so the reward is effectively sparse — and the agent discovers that NOT "
        "drawing avoids all penalties. We watched exactly this happen: reward climbed from "
        "−7.9 to −4.6 while IoU stayed at 0.",
        size=11, color=BODY, spacing=1.2)
    mechs = [
        ("Stochastic policy + entropy bonus", "PPO's Gaussian policy explores by "
         "sampling; ent_coef = 0.02 explicitly rewards keeping the distribution wide, "
         "so the policy does not commit too early.", VIOLET),
        ("Dense potential-based shaping", "Turns a sparse problem into a dense one — "
         "there is now a gradient to follow even before the pen touches the target.",
         GOOD),
        ("Curriculum (the task ladder)", "line → circle → square → triangle → digits → "
         "letters. Debug the whole pipeline on the easiest target before the hard ones.",
         ACCENT),
        ("Constraint as curriculum", "pen_always_down removes one exploration dimension "
         "for single-stroke shapes. A wider target (14 px) gives tolerance; narrowing it "
         "is a later difficulty step.", PRIMARY),
    ]
    for i, (t, b, c) in enumerate(mechs):
        y = 3.28 + i * 0.88
        rect(s, M, y, 5.95, 0.80, fill=WHITE, line=LINE,
             shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.04)
        rect(s, M, y, 0.05, 0.80, fill=c)
        txt(s, M + 0.20, y + 0.08, 5.6, 0.26, t, size=10.5, color=c, bold=True)
        txt(s, M + 0.20, y + 0.34, 5.6, 0.42, b, size=9.5, color=BODY, spacing=1.14)

    rx = M + 6.30
    txt(s, rx, 1.46, CW - 6.30, 0.28, "TRAINING STRATEGY", size=10.5, color=PRIMARY,
        bold=True)
    table(s, ["setting", "value", "why"],
          [["algorithm", "PPO", "on-policy, stable, forgiving of reward-scale mistakes — "
            "the right first choice while the reward is still being designed"],
           ["policy", "CnnPolicy", "the observation is an image; SB3 builds a small "
            "convolutional feature extractor"],
           ["n_envs", "8 (DummyVecEnv)", "a larger, decorrelated on-policy batch → lower "
            "gradient variance"],
           ["n_steps", "512 per env", "4,096 transitions per policy update"],
           ["batch_size", "256", "16 minibatches per epoch"],
           ["n_epochs", "6", "reuse each batch 6× before discarding it (on-policy limit)"],
           ["gamma", "0.99", "a stroke's value persists over ~100 steps; a shorter "
            "horizon would make the agent myopic"],
           ["ent_coef", "0.02", "keeps exploring; without it the policy collapses into "
            "a local optimum early"],
           ["learning_rate", "3e-4", "the standard Adam setting for PPO; not yet tuned"],
           ["budget", "400k steps/shape", "≈1,700 episodes, ≈16 min on CPU"]],
          rx, 1.78, CW - 6.30, colw=[1.5, 1.5, 4.0], size=9.5, row_h=0.44,
          header_h=0.32)
    txt(s, rx, 6.36, CW - 6.30, 0.5,
        "Next: SAC (off-policy, replay buffer, far more sample-efficient) under an identical "
        "budget — that comparison is hypothesis H4.",
        size=10, color=MUTED, italic=True, spacing=1.15)
    note(s, """
Start with the concrete exploration problem, because "exploration versus
exploitation" is abstract until you show what it cost us. The target covers about 5
percent of the canvas. A random pen almost never traces it. So the reward is
effectively sparse, and the agent found the degenerate solution: do not draw, and you
cannot be penalised. We watched the reward climb from -7.9 to -4.6 while IoU stayed
flat at zero - the agent was genuinely improving at doing nothing.

Then present the four mechanisms as the response. Note that only the first is
"exploration" in the textbook sense; the other three change the PROBLEM so that less
exploration is needed. That is usually the more effective lever in practice.

On PPO as the first algorithm: the honest reason is that PPO is forgiving. Its
clipped objective limits how far the policy can move in one update, so a badly scaled
reward degrades performance rather than destroying the run. While the reward was still
being designed, that robustness was worth more than sample efficiency. SAC is the
natural next step precisely because it is more sample-efficient, and comparing them is
hypothesis H4.

Be ready to admit that the hyperparameters are mostly defaults and are not yet tuned.
That is a legitimate limitation and a planned experiment, not an oversight to hide.
""")

    # =================================================== SECTION 7 =========
    section(prs, 7, "Mathematical Foundations",
            "The equations the system actually computes — coordinate transforms, kinematics, "
            "the accuracy metrics, the reward, and the optimisation the learner performs.",
            ["Coordinate transformations", "Forward & inverse kinematics",
             "Error metrics", "Reward mathematics", "Policy optimisation"])

    # ---------------------------------------- 7.1 coordinate transforms ----
    s = slide(prs, "Coordinate transformations", "07 · mathematics")
    txt(s, M, 1.46, 5.95, 0.28, "WORLD  →  CANVAS PIXELS", size=10.5, color=PRIMARY,
        bold=True)
    eqn(s, M, 1.76, 5.95,
        ["c  =  round( (x − (cₓ − h)) / 2h · (N − 1) )",
         "r  =  round( ((c_y + h) − y) / 2h · (N − 1) )"],
        caption="cₓ, c_y = paper centre (0.55, 0.00) m · h = 0.10 m half-width · N = canvas resolution")
    txt(s, M, 2.98, 5.95, 0.62,
        "An affine map: translate the paper origin to a corner, scale metres→pixels, and FLIP "
        "the y axis because image rows increase downward while world y increases to the left. "
        "The flip is the part that was originally wrong.",
        size=10.5, color=BODY, spacing=1.18)
    txt(s, M, 3.66, 5.95, 0.28, "SCALE FACTOR", size=10.5, color=ACCENT, bold=True)
    eqn(s, M, 3.94, 5.95,
        ["s  =  (N − 1) / 2h  =  127 / 0.20  ≈  635 px per metre",
         "1 px  ≈  1.57 mm     ·     pen nib 1.5 mm  ≈  1 px"],
        caption="at N = 128 (the RL canvas). At N = 512 in the simulator, 1 px ≈ 0.39 mm.",
        size=13)
    txt(s, M, 5.26, 5.95, 0.28, "HOMOGENEOUS FORM (for the report)", size=10.5,
        color=VIOLET, bold=True)
    eqn(s, M, 5.54, 5.95,
        ["[ c , r , 1 ]ᵀ   =   M · [ x , y , 1 ]ᵀ",
         "M  =  [ [ s , 0 , −s(cₓ−h) ] , [ 0 , −s , s(c_y+h) ] , [ 0 , 0 , 1 ] ]"],
        size=11.5, h=1.24, caption="the negative s in row 2 IS the y-axis flip")

    rx = M + 6.30
    txt(s, rx, 1.46, CW - 6.30, 0.28, "CAMERA  →  IMAGE  (the perception path)",
        size=10.5, color=ACCENT, bold=True)
    eqn(s, rx, 1.76, CW - 6.30,
        ["p_img  =  Π( K · [R | t] · p_world )"],
        caption="[R|t] = the view matrix (world → camera) · K = the projection matrix · Π = perspective divide",
        size=13)
    bullets(s, [
        "View matrix from computeViewMatrix(eye, target, up) with eye = (0.55, 0, 0.55), "
        "target = (0.55, 0, 0.003), up = [0, 1, 0].",
        "Projection from computeProjectionMatrixFOV(fov = 24°, aspect = 1, near = 0.1, "
        "far = 1.0).",
        "Because the camera looks straight down at a PLANE, the projection reduces to a "
        "similarity transform: the world→image map is just a scale and a flip — the same "
        "form as the canvas map.",
        "Field of view at the paper: 2 · 0.547 · tan(12°) ≈ 0.233 m across 480 px "
        "→ ≈ 0.49 mm per pixel.",
        "We did not rely on that derivation alone: the orientation was verified "
        "empirically over all 8 dihedral transforms (IoU 0.998 vs 0.68).",
    ], rx, 3.06, CW - 6.30, 2.4, size=10.5, bullet_color=ACCENT)
    card(s, rx, 5.62, CW - 6.30, 1.20, "ON REAL HARDWARE THIS BECOMES A HOMOGRAPHY",
         "A real camera will not be perfectly perpendicular to the paper. The paper corners "
         "then map to an arbitrary quadrilateral, and the correct model is a projective "
         "homography H (8 DOF), recovered from the four corners via cv2.getPerspectiveTransform "
         "and applied with cv2.warpPerspective.", accent=WARN)
    note(s, """
Two transformations, and they have different structure - be precise about why.

World to canvas is affine: a translation, a scale, and a flip of the y axis. The flip
exists because image rows increase downward while the world y axis increases to the
left. The homogeneous matrix at the bottom left makes that explicit - the negative s
in the second row IS the flip. This is the transformation that was originally
transposed.

The scale factor is worth quoting because it makes the accuracy numbers meaningful:
at 128-pixel canvas resolution, one pixel is about 1.57 mm, and the pen nib is about
1.5 mm - so the pen is roughly one pixel wide. That is why sub-millimetre IK accuracy
matters and why IoU is so unforgiving.

World to image is in general projective, but because our virtual camera looks straight
down at a plane, the perspective divide is constant across the sheet and it collapses
to a similarity - a scale and a flip. On real hardware that will not hold: the camera
will be slightly tilted, so the paper becomes a general quadrilateral in the image and
we will need a full homography estimated from the four corners. That is a known,
planned step, and OpenCV provides it directly.
""")

    # ------------------------------------------------- 7.2 kinematics ------
    s = slide(prs, "Kinematics — from joint angles to a pen tip, and back",
              "07 · mathematics")
    txt(s, M, 1.46, 5.95, 0.28, "FORWARD KINEMATICS  —  angles → position", size=10.5,
        color=PRIMARY, bold=True)
    eqn(s, M, 1.76, 5.95,
        ["T⁰ₙ(θ)  =  T⁰₁(θ₁) · T¹₂(θ₂) · … · Tⁿ⁻¹ₙ(θₙ)",
         "p_tip  =  T⁰ₙ(θ) · [0, 0, −L_pen, 1]ᵀ"],
        caption="each Tⁱ⁻¹ᵢ is a 4×4 homogeneous transform (Denavit–Hartenberg); composition is a product",
        size=13)
    txt(s, M, 3.06, 5.95, 0.55,
        "Unique and cheap: one set of angles gives exactly one pen position. PyBullet composes "
        "these from the URDF; we never write them out by hand.",
        size=10.5, color=BODY, spacing=1.18)
    txt(s, M, 3.68, 5.95, 0.28, "INVERSE KINEMATICS  —  position → angles", size=10.5,
        color=VIOLET, bold=True)
    eqn(s, M, 3.98, 5.95,
        ["find θ  such that  T⁰ₙ(θ) = T_desired",
         "Δθ  =  J⁺(θ) · Δx        (iterate until ‖Δx‖ < ε)",
         "J⁺  =  Jᵀ(J Jᵀ + λ²I)⁻¹      damped least squares"],
        caption="J = ∂p/∂θ, the 6×n Jacobian · λ damps the solution near singularities",
        size=13)
    bullets(s, [
        "Hard because it is the INVERSE of a nonlinear map: there may be many solutions "
        "(elbow up / elbow down), or none if the target is unreachable.",
        "Solved numerically and iteratively, seeded from the CURRENT pose — which is why "
        "small steps converge far better than large jumps.",
        "Our settings: maxNumIterations = 200, residualThreshold = 1e-5, orientation "
        "constrained to pen-down, no null-space hints.",
    ], M, 5.56, 5.95, 1.3, size=10.5, bullet_color=VIOLET)

    rx = M + 6.30
    txt(s, rx, 1.46, CW - 6.30, 0.28, "WHY THE ORIENTATION CONSTRAINT IS NECESSARY",
        size=10.5, color=BAD, bold=True)
    rect(s, rx, 1.76, CW - 6.30, 1.10, fill=TINT_RED, line=None,
         shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.05)
    txt(s, rx + 0.22, 1.88, CW - 6.75, 0.9,
        "A 7-DOF arm is REDUNDANT for a 3-DOF position goal: infinitely many joint "
        "configurations reach the same point. Without an orientation constraint the solver is "
        "free to pick any of them — and it picked one with the pen tilted 41°, which reaches "
        "the target and is useless for drawing.",
        size=10.5, color=BODY, spacing=1.2)
    eqn(s, rx, 3.02, CW - 6.30,
        ["q_down  =  Euler(π, 0, 0)   →   the tool's +z faces world −z"],
        caption="constraining orientation removes the redundancy that was being misused",
        size=12)
    txt(s, rx, 3.94, CW - 6.30, 0.28, "AND WHY NOT NULL-SPACE CONTROL", size=10.5,
        color=BAD, bold=True)
    txt(s, rx, 4.24, CW - 6.30, 0.9,
        "Redundancy is normally exploited via null-space projection: Δθ = J⁺Δx + (I − J⁺J)·z, "
        "where z pushes joints toward rest poses without disturbing the tip. PyBullet exposes "
        "this through lowerLimits/upperLimits/jointRanges/restPoses.",
        size=10.5, color=BODY, spacing=1.18)
    rect(s, rx, 5.24, CW - 6.30, 0.94, fill=WASH, line=LINE,
         shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.05)
    txt(s, rx + 0.22, 5.34, CW - 6.75, 0.78,
        "In OUR configuration it made accuracy ~400× worse (0.007 mm → 2.835 mm). We measured "
        "it, so we do not use it — and we report it, because every tutorial recommends it.",
        size=10.5, color=BAD, bold=True, spacing=1.2)
    txt(s, rx, 6.32, CW - 6.30, 0.5,
        "Joint-limit compliance is instead enforced by construction: the paper lives inside the "
        "experimentally verified reachable box, so no solution needs to violate a limit.",
        size=10, color=MUTED, italic=True, spacing=1.16)
    note(s, """
Forward kinematics is straightforward: compose the per-joint homogeneous transforms
and you get the tip pose. It is unique and cheap.

Inverse kinematics is the interesting one. It is the inverse of a nonlinear map, so
there can be many solutions or none. PyBullet solves it numerically by damped least
squares - iteratively taking the pseudo-inverse of the Jacobian, with a damping term
lambda that keeps the solution well-behaved near singularities. Because it iterates
from the current pose, small steps converge better than large jumps. That single fact
justifies our relative-nudge action space.

The right-hand column explains the two IK findings mathematically rather than
anecdotally. A 7-DOF arm targeting a 3-DOF position is redundant - there is a
four-dimensional family of solutions. Without an orientation constraint the solver may
return any member of that family, and it returned one with the pen tilted 41 degrees.
Constraining orientation removes the redundancy that was being misused.

Null-space projection is the textbook way to exploit redundancy usefully, and it is
what those PyBullet arguments expose. We measured it making our accuracy about 400
times worse. Rather than argue about why, we report the measurement and enforce joint
limits a different way: by keeping the paper inside a workspace we verified
experimentally, so no solution ever needs to violate a limit.
""")

    # --------------------------------------------------- 7.3 metrics -------
    s = slide(prs, "Error metrics — the mathematics of 'how close?'",
              "07 · mathematics",
              "Five views of one comparison between two binary masks A (drawn) and B (target).")
    ms = [
        ("INTERSECTION OVER UNION", GOOD, "IoU(A,B)  =  |A ∩ B| / |A ∪ B|",
         "The headline metric. 1 = perfect, 0 = disjoint. Penalises BOTH missing the "
         "target and inking where it should not. Strict: two parallel strokes offset by "
         "one stroke width score 0.",
         "Edge case: both empty → defined as 1."),
        ("MEAN SQUARED ERROR", ACCENT, "MSE  =  (1/N) Σᵢ (Aᵢ − Bᵢ)²",
         "On binary masks this is exactly the FRACTION OF PIXELS THAT DISAGREE. Easy to "
         "read, but dominated by the huge blank background — a nearly-empty canvas already "
         "scores well.",
         "Reported for comparability with prior work; not used as the reward."),
        ("COVERAGE  (recall)", VIOLET, "Cov  =  |A ∩ B| / |B|",
         "What fraction of the target has been drawn over. Answers 'did it get "
         "everywhere?'",
         "Gameable alone — scribbling over everything gives coverage 1."),
        ("PRECISION", VIOLET, "Prec  =  |A ∩ B| / |A|",
         "What fraction of the ink landed on the target. Answers 'was it neat?'",
         "Coverage and precision decompose IoU into its two failure directions — which "
         "is how the scribble mode was diagnosed."),
        ("CHAMFER DISTANCE", PRIMARY,
         "Ch(A,B)  =  ½ ( mean_{a∈A} d(a,B)  +  mean_{b∈B} d(b,A) )",
         "Symmetric mean distance in pixels, computed with a distance transform. SOFT: a "
         "stroke that is close but not overlapping still scores well, where IoU would say "
         "0.",
         "Distinguishes 'nearly right' from 'completely wrong'. Lower is better; 0 is "
         "perfect."),
    ]
    for i, (t, c, formula, desc, note_) in enumerate(ms):
        y = 1.72 + i * 1.02
        rect(s, M, y, CW, 0.92, fill=WHITE, line=LINE,
             shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.04)
        rect(s, M, y, 0.05, 0.92, fill=c)
        txt(s, M + 0.22, y + 0.12, 2.6, 0.28, t, size=10.5, color=c, bold=True)
        txt(s, M + 0.22, y + 0.44, 2.9, 0.36, formula, size=10, color=INK,
            font="Cambria Math", bold=True)
        txt(s, M + 3.35, y + 0.12, 5.4, 0.74, desc, size=10, color=BODY, spacing=1.14)
        txt(s, M + 8.95, y + 0.14, CW - 9.15, 0.7, note_, size=9.5, color=MUTED,
            spacing=1.14, italic=True)
    rect(s, M, 6.90, CW, 0.02, fill=WHITE)
    note(s, """
The point of showing five metrics is that each one can be gamed alone, and together
they cannot.

IoU is the headline because it punishes both directions of error. Its strictness is
worth stating concretely: two parallel strokes offset by a single stroke width score
zero, even though a person would call them a near match. That is why an IoU of 0.5 on
a thin stroke is a much better result than it sounds.

MSE is included mainly for comparability with other work, and it is worth explaining
why we do not optimise it: on a mask that is 95 percent background, an empty canvas
already achieves a very low MSE. It rewards doing nothing, which is exactly the trap
we were trying to escape.

Coverage and precision are the diagnostic pair. They decompose IoU into recall and
precision. Coverage 0.91 with IoU 0.14 was the signature of the scribble failure -
everything covered, almost nothing precise. That decomposition is how we identified
the failure mode rather than just observing a low score.

Chamfer is the soft metric. It uses a distance transform, so it is cheap, and it
answers a different question: not "do they overlap" but "how far apart are they". It
distinguishes a stroke that is 3 pixels off from one that is on the other side of the
page - a distinction IoU cannot make, since both score zero.
""")

    # -------------------------------------------- 7.4 reward mathematics ---
    s = slide(prs, "Reward mathematics — two properties worth proving",
              "07 · mathematics")
    txt(s, M, 1.46, 5.95, 0.28, "1 · THE TELESCOPING PROPERTY", size=10.5, color=GOOD,
        bold=True)
    eqn(s, M, 1.76, 5.95,
        ["Σₜ₌₁ᵀ ΔIoUₜ  =  Σₜ₌₁ᵀ (IoUₜ − IoUₜ₋₁)  =  IoU_T − IoU₀  =  IoU_final",
         "(IoU₀ = 0 on a blank canvas)"],
        caption="the undiscounted return of the IoU term IS the final drawing accuracy",
        size=12.5)
    txt(s, M, 3.02, 5.95, 0.88,
        "Consequence: the agent is not optimising a proxy. Maximising cumulative reward is "
        "identical to maximising the accuracy of the finished drawing. With γ = 0.99 the "
        "equality is approximate — early progress is weighted slightly more, which mildly "
        "encourages drawing sooner. That is a desirable bias, not a bug.",
        size=10.5, color=BODY, spacing=1.2)

    txt(s, M, 3.98, 5.95, 0.28, "WHY NOT REWARD FINAL IoU ONLY?", size=10.5,
        color=BAD, bold=True)
    txt(s, M, 4.28, 5.95, 0.9,
        "A single terminal reward is mathematically equivalent in expectation but "
        "catastrophically harder to learn from: one scalar must be credited across 240 "
        "actions. The per-step delta assigns credit to the exact step that caused the "
        "improvement — the same total, delivered informatively.",
        size=10.5, color=BODY, spacing=1.2)
    txt(s, M, 5.28, 5.95, 0.28, "THE OPTIMISATION PROBLEM", size=10.5, color=VIOLET,
        bold=True)
    eqn(s, M, 5.58, 5.95,
        ["J(θ)  =  E_{τ ~ π_θ} [ Σₜ γᵗ rₜ ]        θ* = argmax_θ J(θ)",
         "∇_θ J  =  E[ ∇_θ log π_θ(aₜ|sₜ) · Âₜ ]"],
        caption="the policy-gradient theorem — the basis of PPO", size=12.5)

    rx = M + 6.30
    txt(s, rx, 1.46, CW - 6.30, 0.28, "2 · POTENTIAL-BASED SHAPING IS POLICY-INVARIANT",
        size=10.5, color=VIOLET, bold=True)
    eqn(s, rx, 1.76, CW - 6.30,
        ["F(s, a, s′)  =  γ · Φ(s′)  −  Φ(s)",
         "Φ(s)  =  − dist( pen(s),  nearest target pixel )"],
        caption="Ng, Harada & Russell (1999): any shaping of this form leaves the optimal policy unchanged",
        size=12.5)
    txt(s, rx, 3.02, CW - 6.30, 1.3,
        "Sketch of why: adding F to the reward adds exactly −Φ(s₀) + γᵀΦ(s_T) to the return of "
        "EVERY trajectory from a given start state. A constant offset cannot change which "
        "trajectory ranks highest, so argmax is preserved. What changes is the SHAPE of the "
        "objective surface — the gradient now points toward the target from anywhere on the "
        "sheet, instead of being flat until the pen happens to hit it.",
        size=10.5, color=BODY, spacing=1.2)
    rect(s, rx, 4.42, CW - 6.30, 0.94, fill=TINT_GREEN, line=None,
         shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.05)
    txt(s, rx + 0.22, 4.52, CW - 6.75, 0.78,
        "This is why the shaping term is principled rather than a hack: it changes how easily "
        "the optimum is FOUND, not what the optimum IS. That distinction is exactly what a "
        "reviewer will ask about.",
        size=10.5, color=INK, bold=True, spacing=1.2)
    txt(s, rx, 5.52, CW - 6.30, 0.28, "IMPLEMENTATION NOTE", size=10.5, color=ACCENT,
        bold=True)
    txt(s, rx, 5.82, CW - 6.30, 0.95,
        "Φ is read from a Euclidean distance transform of the target, computed ONCE in the "
        "constructor (cv2.distanceTransform on the inverted mask) and normalised by the canvas "
        "resolution. So dense shaping costs a single array lookup per step, not a nearest-"
        "neighbour search.",
        size=10.5, color=BODY, spacing=1.2)
    note(s, """
These are the two properties that make the reward defensible rather than merely
tuned, and they are the most likely place for a sharp theoretical question.

The telescoping property: because each step's reward is a difference in IoU, the sum
over an episode collapses to the final IoU. So the agent is not optimising a proxy
for drawing accuracy - it is optimising drawing accuracy itself. With discounting at
gamma = 0.99 the equality is approximate; early progress counts slightly more, which
biases the agent toward drawing sooner. We regard that as desirable.

Anticipate "why not just reward the final IoU and nothing else?" It is equivalent in
expectation, but it is a credit-assignment nightmare: one number has to be attributed
across 240 actions. The per-step delta delivers the same total reward but attributes
it to the step that actually caused the improvement.

Potential-based shaping is the theoretical result to know by name: Ng, Harada and
Russell, 1999. If the shaping term can be written as gamma times a potential at the
next state minus the potential at the current state, then the optimal policy is
unchanged. The intuition is that it adds a constant to every trajectory's return from
a given start, and a constant cannot change which trajectory is best. What it changes
is the gradient landscape - which is precisely what we needed to escape the
draw-nothing optimum.

The implementation note is a nice engineering detail: the potential is a lookup into a
distance transform computed once, so dense shaping is essentially free.
""")

    # =================================================== SECTION 8 =========
    section(prs, 8, "Computer Vision",
            "How the robot sees its own drawing: acquiring an image, turning it into a clean "
            "binary stroke, and comparing that stroke to the target.",
            ["Image acquisition", "Preprocessing pipeline", "Shape comparison",
             "Why these techniques"])

    # ------------------------------------------------- 8.1 acquisition -----
    s = slide(prs, "Image acquisition — the virtual camera", "08 · computer vision")
    txt(s, M, 1.46, 6.1, 0.28, "THE CAMERA MODEL", size=10.5, color=ACCENT, bold=True)
    table(s, ["parameter", "value", "why this value"],
          [["position (eye)", "(0.55, 0.00, 0.55) m", "directly above the paper centre, "
            "0.55 m up — clear of the arm's working volume"],
           ["look-at target", "(0.55, 0.00, 0.003) m", "the paper surface, so the optical "
            "axis is perpendicular to the sheet"],
           ["up vector", "[0, 1, 0]", "chosen so the image shares the canvas convention; "
            "VERIFIED, not assumed"],
           ["field of view", "24°", "narrow, so the 0.20 m sheet nearly fills the frame "
            "→ maximum pixels on the drawing"],
           ["near / far", "0.1 m / 1.0 m", "tight clipping range around the scene"],
           ["resolution", "480 × 480", "≈0.49 mm per pixel at the paper — about 3 px "
            "across a 1.5 mm stroke"],
           ["outputs", "RGB + segmentation", "the segmentation mask identifies paper "
            "pixels exactly, which is a luxury of simulation"],
           ["renderer", "TinyRenderer (headless)", "no GPU or display needed; hardware "
            "OpenGL is used in the GUI"]],
          M, 1.78, 6.1, colw=[1.6, 1.8, 3.6], size=9.5, row_h=0.46, header_h=0.32)
    card(s, M, 5.62, 6.1, 1.22, "THE ARM MUST BE PARKED FIRST",
         "A top-down camera looks straight through the arm. In the first capture the arm "
         "filled the frame, the paper was ~40 % visible and perceived ink was ≈0. Parking the "
         "arm straight up over its base (far from the paper at x = 0.55) gives 100 % paper "
         "visible and ZERO arm pixels — measured. Real drawing rigs do the same.",
         accent=BAD)

    rx = M + 6.45
    txt(s, rx, 1.46, CW - 6.45, 0.28, "WHAT CHANGES ON REAL HARDWARE", size=10.5,
        color=WARN, bold=True)
    changes = [
        ("Segmentation mask", "Gone. A real camera has no object IDs. Replaced by colour "
         "thresholding or contour detection to find the white sheet — or by fixing the "
         "paper and calibrating its corners once.", BAD),
        ("Perfect perpendicularity", "Gone. A real mount is slightly tilted, so the sheet "
         "becomes a general quadrilateral. Fixed by a homography from the four paper "
         "corners (cv2.getPerspectiveTransform).", BAD),
        ("Uniform lighting", "Gone. Shadows and glare break a fixed threshold. Likely "
         "replaced by adaptive thresholding, or Otsu applied AFTER cropping to the paper.",
         WARN),
        ("Clean white / black", "Degraded. Paper texture, pen bleed and camera noise. "
         "Mitigated with a blur, morphological opening, and a small-component filter.",
         WARN),
        ("Everything else", "Unchanged. Crop → greyscale → threshold → resize → binarise "
         "→ IoU is the same pipeline. That is the point of building it this way now.",
         GOOD),
    ]
    for i, (t, b, c) in enumerate(changes):
        y = 1.78 + i * 1.02
        rect(s, rx, y, CW - 6.45, 0.94, fill=WHITE, line=LINE,
             shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.04)
        rect(s, rx, y, 0.05, 0.94, fill=c)
        txt(s, rx + 0.20, y + 0.09, 2.4, 0.26, t, size=10.5, color=c, bold=True)
        txt(s, rx + 0.20, y + 0.35, CW - 6.90, 0.55, b, size=9.5, color=BODY,
            spacing=1.14)
    note(s, """
Give the camera parameters and then, more importantly, be explicit about which of them
are luxuries of simulation.

The resolution figure is the one to have ready: about 0.49 mm per pixel at the paper,
so a 1.5 mm stroke is roughly three pixels wide. That is thin, which is why recovering
it at IoU 0.88 is a good result.

The segmentation mask is the biggest simulation luxury. PyBullet tells us exactly which
pixels belong to the paper object. No real camera does that. On hardware we will either
detect the white sheet by colour and contour, or - more likely and more robustly - fix
the paper in place and calibrate its four corners once.

The perpendicularity assumption is the second luxury, and its replacement is standard:
estimate a homography from the four paper corners and warp the image to a canonical
top-down view. OpenCV does this in two calls.

The last row is the argument for having built it this way: crop, greyscale, threshold,
resize, binarise, compare - that sequence does not change. Only the way we find the
paper and correct its perspective changes. So the perception code is not throwaway
scaffolding.
""")

    # -------------------------------------------- 8.2 preprocessing --------
    s = slide(prs, "Preprocessing — camera frame to a clean binary stroke",
              "08 · computer vision")
    steps = [
        ("1", "SEGMENT", "paper = (seg == paper_id)", "Identify which pixels belong to "
         "the sheet.", ACCENT),
        ("2", "CROP", "bounding box of the paper mask", "Discard everything outside the "
         "sheet; normalises scale.", ACCENT),
        ("3", "GREYSCALE", "cvtColor(RGB → GRAY)", "Ink is defined by brightness, not "
         "hue — colour is noise here.", PRIMARY),
        ("4", "MASK OFF-PAPER", "grey[~paper] = 255", "Force anything not on the sheet to "
         "white so it can never be mistaken for ink.", PRIMARY),
        ("5", "THRESHOLD", "threshold(grey, 128, THRESH_BINARY_INV)", "Split ink from "
         "paper. Paper ≈230, ink <100 → a mid cut is robust.", GOOD),
        ("6", "RESIZE", "resize(…, INTER_AREA)", "Match the canvas resolution so the two "
         "masks are comparable pixel-for-pixel.", GOOD),
        ("7", "RE-BINARISE", "(out > 40) · 255", "Area-averaging produces grey; re-cut so "
         "the mask is strictly 0 / 255.", VIOLET),
        ("8", "COMPARE", "metrics.iou(perceived, target)", "The number that becomes the "
         "reward in the H2 vision condition.", VIOLET),
    ]
    for i, (n, t, op, why, c) in enumerate(steps):
        y = 1.58 + i * 0.655
        rect(s, M, y, CW, 0.59, fill=WHITE, line=LINE,
             shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.04)
        rect(s, M, y, 0.05, 0.59, fill=c)
        chip(s, M + 0.16, y + 0.15, 0.32, 0.28, n, color=c, fill=WASH, size=10)
        txt(s, M + 0.62, y + 0.17, 1.7, 0.26, t, size=11, color=c, bold=True)
        txt(s, M + 2.45, y + 0.18, 3.7, 0.26, op, size=9.5, color=INK, font=FM)
        txt(s, M + 6.35, y + 0.16, CW - 6.55, 0.4, why, size=10, color=BODY,
            spacing=1.1)
    rect(s, M, 6.86, CW, 0.02, fill=WHITE)
    note(s, """
Walk the eight steps; each one is a single OpenCV call, and each exists for a reason.

Step 4 is the one people miss. After cropping to the paper's bounding box, the corners
of that box may still contain non-paper pixels - the bounding box is rectangular, the
visible paper may not be. Forcing those to white guarantees they can never be counted
as ink.

Step 5 uses a FIXED threshold rather than Otsu, and that is a deliberate reversal of
the usual advice. Otsu chooses the threshold that best separates two pixel
populations. With the dark arm in frame, the two dominant populations were arm and
paper, so the thin stroke - a tiny minority of pixels - was classified as background.
Once the arm is parked and the crop is limited to the sheet, the scene is genuinely
bimodal and controlled, so a fixed mid-grey cut is both simpler and more robust.

Step 7 matters more than it looks. INTER_AREA resizing averages over source pixels, so
a black stroke on white paper produces grey edge pixels. If those greys were kept, the
two masks would be compared inconsistently. Re-binarising at a low threshold keeps thin
strokes rather than eroding them away.
""")

    # -------------------------------------------- 8.3 why these choices ----
    s = slide(prs, "Why these vision techniques — and what was rejected",
              "08 · computer vision")
    choices = [
        ("Fixed threshold", "Otsu's method · adaptive threshold · colour segmentation",
         "Otsu was FOOLED: with the dark arm in frame it split arm-vs-paper and lost the "
         "stroke. In a controlled white-paper/black-ink scene with the arm parked, a fixed "
         "mid-grey cut is simpler and more robust. On real hardware, with uneven lighting, "
         "we expect to move to adaptive thresholding — a planned, not accidental, change.",
         GOOD),
        ("Segmentation-mask crop", "Contour detection · fiducial markers · fixed ROI",
         "In simulation the segmentation buffer identifies the paper EXACTLY and free of "
         "charge, so using anything else would add error for no benefit. The real-hardware "
         "replacement (contours or a calibrated fixed ROI) is a drop-in change at one "
         "function.", GOOD),
        ("Raster IoU comparison", "Contour matching (cv2.matchShapes) · Hu moments · "
         "keypoints",
         "Shape descriptors answer 'is this the same KIND of shape' — they are invariant to "
         "position and scale, which is exactly what we must NOT be invariant to: a circle "
         "drawn in the wrong place is a wrong drawing. IoU is position-sensitive by "
         "construction.", VIOLET),
        ("Chamfer as a companion", "Hausdorff distance · earth-mover's distance",
         "Hausdorff is a MAXIMUM, so one stray pixel dominates the whole score. Chamfer "
         "averages, so it degrades gracefully — and a distance transform makes it O(N) "
         "instead of a pairwise search.", VIOLET),
        ("Park the arm, then shoot", "Camera mounted at an angle · inpainting the arm away "
         "· multiple cameras",
         "Parking is what real drawing rigs do, costs nothing, and removes the occlusion "
         "problem completely rather than compensating for it. An angled camera would also "
         "require homography correction from day one — an unnecessary variable while the "
         "pipeline was being built.", ACCENT),
        ("Deep segmentation (rejected for now)", "U-Net or similar to extract strokes",
         "Would need labelled data we do not have, adds a second learning problem inside a "
         "learning experiment, and would confound H2: a poor vision-reward result could be "
         "blamed on the segmentation network rather than on the reward. Classical CV keeps "
         "the comparison clean.", BAD),
    ]
    cw2 = (CW - 0.28) / 2
    for i, (t, alts, why, c) in enumerate(choices):
        x = M + (i % 2) * (cw2 + 0.28)
        y = 1.56 + (i // 2) * 1.78
        rect(s, x, y, cw2, 1.62, fill=WHITE, line=LINE,
             shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.04)
        rect(s, x, y, 0.05, 1.62, fill=c)
        txt(s, x + 0.20, y + 0.10, cw2 - 0.4, 0.26, t, size=11, color=c, bold=True)
        txt(s, x + 0.20, y + 0.38, cw2 - 0.4, 0.24, "considered: " + alts, size=8.5,
            color=MUTED, italic=True)
        txt(s, x + 0.20, y + 0.66, cw2 - 0.4, 0.9, why, size=9.5, color=BODY,
            spacing=1.16)
    note(s, """
This slide is built for the "why not X?" question, so it names the alternative in
every row.

The most important row is the third. Shape descriptors like Hu moments or
cv2.matchShapes are the obvious tool for "compare two shapes", and they are wrong here
for a precise reason: they are invariant to translation and scale. That invariance is
usually the selling point. For us it is disqualifying - a perfect circle drawn in the
wrong corner of the page is a failed drawing, and a descriptor would call it a match.
IoU is position-sensitive by construction, which is exactly what the task requires.

The last row is the one that shows research judgement. A learned segmentation network
would be a natural instinct, and we rejected it deliberately: it needs labelled data we
do not have, it puts a second learning problem inside the experiment, and above all it
would confound H2. If the vision-reward agent underperformed, we could not tell whether
the reward or the segmentation network was at fault. Classical, deterministic computer
vision keeps the causal claim clean.

The Hausdorff-versus-chamfer point is a nice small one: Hausdorff takes a maximum, so a
single stray pixel dominates the entire score. Chamfer averages, so it degrades
gracefully.
""")
