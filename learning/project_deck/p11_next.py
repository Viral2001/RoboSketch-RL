"""Section 11 - what comes next: sim-to-real, letters."""
from kit import *  # noqa: F401,F403


def build(prs, toc):
    section(prs, 11, "What comes next",
            "Simulation is complete. The next questions are whether the measurements hold on a real arm with a "
            "real camera, and how to move from shapes to digits and letters.",
            ["The sim-to-real gap", "What hardware would test", "Towards letters"],
            """
Section 11: aage kya. Hardware ki planning ek alag document me hai - yahan sirf yeh ki simulation se reality
tak kya-kya gap hai aur kaunse measurements dobara karne honge. (Is deck me koi purchase advice nahi.)""", toc)

    tabular(prs, "11 · sim-to-real", "The sim-to-real gap, in the proposal's priority order",
            "docs/PROJECT_PROPOSAL_v2.md section 6 (no purchase advice here - a separate document covers hardware).",
            ["#", "gap", "why it matters"],
            [["1", "Fit the ink model from real strokes (pen height → stroke width)", "the 3.5 mm pen width is an unvalidated constant - probably the largest gap"],
             ["2", "Fit the camera model to the real webcam", "cam_px = 150 and the threshold are guesses"],
             ["3", "Measure sim-to-real with Δ = MSE(sim canvas, photo of real canvas)", "gives hardware results a number (FRIDA's metric)"],
             ["4", "Dynamics randomisation of the arm (force, speed, latency)", "a hobby-servo arm is far from a simulated KUKA"],
             ["5", "Swap the KUKA model for a hardware-matched arm", "required before claiming transfer"],
             ["6", "Plan resets: who replaces the paper, refills the pen?", "free in simulation, expensive on hardware"],
             ["7", "Camera placement and lighting (overhead vs eye-in-hand; diffuse light)", "glare can blind the camera"]],
            colw=[0.5, 5.6, 5.7], size=12, row_h=0.5, align="left",
            take="Pen-space actions mean the learned policy's meaning survives an arm swap; only the model + IK change.",
            take_color=VIOLET,
            notes="""
Sim-to-real gap - proposal ki priority order:
1) Ink model: asli strokes se fit karo (pen ki height -> line ki motai). Abhi 3.5 mm ek guess hai - shayad
   sabse bada gap.
2) Camera model asli webcam se fit karo (cam_px 150, threshold guesses hain).
3) Sim-to-real ka number: MSE(sim canvas, real canvas ki photo) - FRIDA ka metric.
4) Arm ki dynamics randomise karo (force, speed, latency) - hobby servos KUKA se bahut alag.
5) KUKA model ki jagah asli arm ka model.
6) Reset ka plan: paper kaun badlega, pen kaun bharega.
7) Camera placement aur roshni - glare camera ko andha kar deta hai.

Pen-space action ka fayda yahan dikhta hai: arm badle to sirf model + IK badalte hain.
""", source="docs/PROJECT_PROPOSAL_v2.md section 6; docs/HANDOFF.md 'Next' item 2 (hardware planning, no purchase suggestions)")

    concept(prs, "11 · hardware", "What a real robot would have to re-test", None,
            ["H2 with a real camera: is the camera reward still within ±0.05 IoU of a reference? (On hardware there "
             "is no exact canvas - a high-resolution scan after each episode could serve as 'truth' for scoring.)",
             "H4 with a real sheet shift: does an offset estimated from a real photo (perspective, lighting, a hand "
             "in view) still let the agent recover? Phase correlation assumed a pure translation.",
             "Ink failure with a size that actually bites - it never did in simulation.",
             "Throughput: on-policy PPO needs ~200k steps per run; on hardware that is impractical - train in "
             "simulation, fine-tune or evaluate on the robot.",
             "Everything above is planning; nothing on hardware has been run."],
            cards=[("WHAT TRANSFERS FOR FREE", ["The measurement design: paired arms, true-IoU scoring, pre-registered "
                                                "diff-in-diff, spaced seeds."], GOOD),
                   ("WHAT DOES NOT", ["The numbers. Every result in this deck is a simulation result."], BAD)],
            notes="""
Asli robot par kya dobara test karna hoga:
- H2 asli camera ke saath. Problem: hardware par exact canvas nahi hota - har episode ke baad ek
  high-resolution scan "truth" ka kaam kar sakta hai (yeh ek planning idea hai).
- H4 asli paper shift ke saath - asli photo me perspective, roshni, haath; phase correlation pure translation
  maanta hai.
- Ink failure jo sach me nuksaan kare.
- Throughput: PPO ko ~200k steps chahiye - hardware par train karna practical nahi; simulation me train,
  robot par evaluate / fine-tune.

Jo transfer hota hai: measurement ka design. Jo nahi hota: numbers - sab simulation ke hain.
""", source="docs/PAPER_PLAN.md section 4 item 6; docs/PROJECT_PROPOSAL_v2.md section 6; RESEARCH_LOG H4 v4 honest limits")

    concept(prs, "11 · letters", "From shapes to digits and letters", None,
            ["Multi-stroke glyphs need the pen-up decision (A2): it trains, but slower, and inks in short bursts "
             "(pen down ~10% of steps).",
             "Digits showed IoU is not enough: similar IoU, very different legibility. Report a recogniser score "
             "(with a reject class) next to IoU.",
             "Generalisation is the main limit for writing: a letter must be drawable at many sizes - the pen-centred "
             "view is the lever found so far.",
             "Optional next paper (proposal 3.5): a goal-conditioned policy - one agent, target as input - with "
             "hindsight relabelling (HER).",
             "Separate stroke order and stroke count from digit identity before claiming anything about strokes."],
            cards=[("ORDER OF WORK (HANDOFF)", ["Paper first (authors, acknowledgment); then hardware planning; "
                                               "optional: why PPO unlearns a BC start, why camera_est < camera_sheet."], PRIMARY)],
            notes="""
Shapes se letters tak:
- Multi-stroke ke liye pen-up chahiye (A2) - train hota hai par slow, chhote bursts me ink.
- Digits ne dikhaya IoU kaafi nahi - recogniser score bhi chahiye.
- Sabse badi limit generalisation - letter alag-alag size me banana hoga; ego view abhi tak ka best lever.
- Optional agla paper: goal-conditioned policy + HER (hindsight experience replay).
- Stroke count aur digit identity ko alag karke test karna.

HANDOFF ke hisaab se order: paper (authors, acknowledgment) -> hardware planning -> optional sawaal.
""", source="docs/HANDOFF.md 'Next'; docs/PROJECT_PROPOSAL_v2.md sections 3.5 and 8 (Stage 6); RESEARCH_LOG A2 and digits RESULT entries")
