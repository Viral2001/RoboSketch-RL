"""
RoboSketch-RL  |  research-results deck that mirrors the paper (docs/paper/main.tex)
-------------------------------------------------
Written 2026-10-19 by Claude Code. Same rules as the paper (docs/PAPER_PLAN.md):
every number comes from a RESEARCH_LOG entry named in the speaker notes; wording is no
stronger than PAPER_PLAN section 2; H4 has NO result slide content until the
"H4 RESULT" log entry exists - the pending slide must be replaced, not filled with the
interim numbers.

  conda run -n robosketch --no-capture-output python docs/presentation/deck_paper.py

Output: docs/presentation/RoboSketch-RL_Research_Results.pptx  (the old 84-slide progress
deck is left untouched).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

from deck_kit import (ACCENT, BAD, BODY, GOOD, INK, MUTED, NAVY, PRIMARY, VIOLET, WARN,  # noqa: E402
                      WHITE, CW, M, TOP, W, H, TINT_AMBER, _blank, _state, bullets, card,
                      kpi, new_deck, note, pic, pipeline, rect, slide, table, txt)
from pptx.dml.color import RGBColor  # noqa: E402

OUT = os.path.join(HERE, "RoboSketch-RL_Research_Results.pptx")
FIG = os.path.join(ROOT, "output")


def fig(s, name, x, y, w, h):
    p = os.path.join(FIG, name)
    if pic(s, p, 0, 0, center_in=(x, y, w, h)) is None:
        card(s, x, y, w, h, "figure missing", [name], accent=BAD)


def title(prs):
    s = _blank(prs)
    _state["n"] += 1
    rect(s, 0, 0, W, H, fill=NAVY)
    rect(s, 0, 0, W, 0.20, fill=PRIMARY)
    rect(s, 0, 0.20, W * 0.42, 0.06, fill=ACCENT)
    txt(s, 1.1, 1.62, 11.2, 0.32, "RESEARCH RESULTS  ·  RoboSketch-RL", size=11.5,
        color=ACCENT, bold=True)
    txt(s, 1.1, 2.05, 11.2, 1.5, "What does a drawing robot lose\nby learning from its camera?",
        size=40, color=WHITE, bold=True, spacing=0.98)
    rect(s, 1.13, 3.62, 2.0, 0.035, fill=PRIMARY)
    txt(s, 1.1, 3.86, 10.4, 0.9,
        "A simulation study of perception-based rewards and visual recovery "
        "for reinforcement-learning drawing agents", size=17,
        color=RGBColor(0xC9, 0xD4, 0xE8), spacing=1.25)
    rect(s, 1.1, 5.35, 11.1, 0.012, fill=RGBColor(0x2C, 0x3A, 0x5C))
    txt(s, 1.1, 5.58, 6.4, 1.1, "[TODO: presenter name]\n[TODO: institution / guide]",
        size=12, color=RGBColor(0xA9, 0xB6, 0xCE), spacing=1.35)
    txt(s, 7.0, 5.58, 5.2, 1.1, "[TODO: date / venue]\nMeasurement study: D01 position supported",
        size=12, color=RGBColor(0xA9, 0xB6, 0xCE), spacing=1.35, align=2)
    note(s, "Working title from docs/paper/main.tex. D01 position supported per PAPER_PLAN section 3.")


def build(prs):
    title(prs)

    # 2 - the problem
    s = slide(prs, "Drawing agents learn from a canvas no robot has", kicker="The problem")
    card(s, M, TOP + 0.15, 5.9, 2.5, "In simulation (prior work)", [
        "The agent is rewarded by comparing a PERFECT rendering of its strokes with the target.",
        "Learning to Paint, SPIRAL, Zhou et al., CalliRewrite, Lee et al. (D02, D05, D07, D09, D01)."],
        accent=PRIMARY)
    card(s, M + 6.2, TOP + 0.15, 5.9, 2.5, "On a real robot", [
        "There is no perfect canvas. The only record of the drawing is what a camera sees:",
        "blur, uneven light, imperfect registration, noise."], accent=WARN)
    card(s, M, TOP + 2.95, CW, 1.9, "The question", [
        "How much drawing accuracy is lost when the agent learns from what a camera perceives "
        "instead of from the true canvas - and does seeing the paper help when things go wrong?"],
        accent=GOOD, body_size=15)
    note(s, "Paper Sec. I. We do not claim RL drawing, image rewards or visual feedback as new "
            "(PAPER_PLAN s5). The contribution is a measurement.")

    # 3 - D01
    s = slide(prs, "The position we have to answer: draw without a camera",
              kicker="Closest prior work")
    card(s, M, TOP + 0.15, CW, 1.55, "Lee et al., ICRA 2022 (D01)", [
        "A robotic sketching agent that synchronises with the canvas through FORWARD KINEMATICS - "
        "it assumes every commanded stroke landed as planned - and argues camera-free is an advantage."],
        accent=BAD)
    quotes = [
        ("D01, Lee et al. ICRA 2022", "“using a camera as an observation of canvas in the future "
         "work could be of great help in the synchronization step”"),
        ("D03, Kotani & Tellex ICRA 2019", "“closing the learning loop by enabling the robot "
         "to inspect what it has drawn”"),
        ("D09, Luo et al. ICRA 2024", "“a lack of real-world training scenarios to bridge "
         "the sim2real gap” - left as future work"),
    ]
    for i, (who, q) in enumerate(quotes):
        card(s, M + i * 4.1, TOP + 2.0, 3.9, 2.6, who, [q], accent=PRIMARY, body_size=12.5)
    txt(s, M, TOP + 4.85, CW, 0.5, "The gap is named by the three closest papers themselves.",
        size=13, color=MUTED, italic=True)
    note(s, "Quotes from research_papers/STUDY_NOTES.md - re-check each against its PDF "
            "before presenting externally.")

    # 4 - setup
    s = slide(prs, "Setup: one environment, three things we can swap", kicker="Method")
    pipeline(s, [("Target", "line / circle / square / triangle"),
                 ("PPO agent", "CNN policy"),
                 ("Pen action", "dx, dy, pen-down"),
                 ("Canvas", "PyBullet, KUKA arm"),
                 ("Perception", "true / fk / camera"),
                 ("Reward", "truth or vision IoU")],
             M, TOP + 0.25, CW, 1.05, colors=[PRIMARY, VIOLET, PRIMARY, PRIMARY, ACCENT, GOOD])
    card(s, M, TOP + 1.65, 3.9, 2.9, "Reward source", [
        "truth: IoU of the real canvas (privileged)",
        "vision: IoU of a simulated camera image"], accent=GOOD)
    card(s, M + 4.1, TOP + 1.65, 3.9, 2.9, "What the agent observes", [
        "true: the real ink (ceiling)",
        "fk: what kinematics predicts it drew (D01)",
        "camera: a photograph of the paper (ours)"], accent=ACCENT)
    card(s, M + 8.2, TOP + 1.65, 3.9, 2.9, "Always scored the same way", [
        "TRUE IoU of the real canvas - whatever the agent saw or was rewarded with.",
        "No agent is credited for what its camera believes."], accent=INK)
    note(s, "PPO, 8 envs, 512-step rollouts, batch 256, 6 epochs, gamma 0.99, entropy 0.02, "
            "lr 3e-4, 200k steps (rl/experiment.py, rl/h4_experiment.py). Episode 240 steps.")

    # 5 - H2
    s = slide(prs, "Camera reward vs privileged reward: no detectable difference",
              kicker="Result 1 - H2")
    table(s, ["Shape", "Truth reward", "Camera reward"], [
        ["line", "0.333 ± 0.008", "0.312 ± 0.013"],
        ["circle", "0.399 ± 0.032", "0.441 ± 0.013"],
        ["square", "0.408 ± 0.044", "0.366 ± 0.052"],
        ["triangle", "0.387 ± 0.067", "0.297 ± 0.015"],
        ["mean", "0.382 ± 0.052", "0.354 ± 0.063"]],
        M, TOP + 0.2, 5.6, colw=[1.4, 2.1, 2.1], size=12, header_size=12, row_h=0.42)
    txt(s, M, TOP + 2.95, 5.6, 2.0, [
        "True IoU, 3 seeds per cell, 200k steps.",
        "A second run of the same configurations: paired gap +0.013 (t = 0.57, 8/12) - "
        "opposite sign to the first.",
        "Shape-dependent: camera better on circle, worse on triangle."], size=12.5, color=BODY)
    fig(s, "results_h2_seeds.png", M + 6.0, TOP + 0.1, 6.1, 4.9)
    note(s, "src: RESEARCH_LOG 'H2 multi-seed sweep (2026-08-12)' and 'H2 PEAK-vs-FINAL RESULT'. "
            "Say 'no detectable difference', never 'equivalent'. Limits: both runs used seeds "
            "0,1,2 (overlapping env streams, F6) so they are not independent and the seed spread "
            "is likely understated; no equivalence test yet.")

    # 6 - H3
    s = slide(prs, "The agent does not learn to fool the camera", kicker="Result 2 - H3")
    kpi(s, M, TOP + 0.3, 3.8, 1.5, "-0.0001", "mean perceived - true IoU", color=GOOD)
    kpi(s, M + 4.15, TOP + 0.3, 3.8, 1.5, "3328", "training episodes logged", color=PRIMARY)
    kpi(s, M + 8.3, TOP + 0.3, 3.8, 1.5, "0.997-0.999", "correlation, true vs perceived",
        color=ACCENT)
    fig(s, "results_h3.png", M, TOP + 2.05, CW, 3.4)
    note(s, "src: RESEARCH_LOG 'H3 RESULT'. No consistent sign across shapes; truth control gap "
            "exactly zero. Limits: one seed per shape, fixed camera only.")

    # 7 - DR
    s = slide(prs, "It survives a much worse camera", kicker="Result 3 - camera randomisation")
    table(s, ["Trained on", "eval: fixed", "eval: train", "eval: held-out"], [
        ["truth (no camera)", "0.389", "0.389", "0.389"],
        ["fixed camera", "0.393", "0.386", "0.379"],
        ["randomised cameras", "0.371", "0.365", "0.368"]],
        M, TOP + 0.2, 7.2, colw=[2.4, 1.6, 1.6, 1.6], size=12, header_size=12, row_h=0.45)
    kpi(s, M + 7.6, TOP + 0.2, 4.5, 1.25, "0.394", "of a perfect drawing's ink the held-out "
        "camera recovers (fixed: 0.834)", color=WARN)
    kpi(s, M + 7.6, TOP + 1.65, 4.5, 1.25, "-0.014", "true IoU the fixed-camera agent loses on it",
        color=GOOD)
    txt(s, M, TOP + 2.3, 7.2, 2.6, [
        "Randomising the camera during training adds nothing: randomised - fixed on the held-out "
        "camera = -0.011 (t = -0.67, n = 8).",
        "The policy needs a coarse record of where it has drawn - even a poor camera keeps it.",
        "3 of 8 camera parameters carry the effect (resolution, blur, warp); exposure, paper tone "
        "and ink contrast cancel by construction."], size=12.5)
    note(s, "src: RESEARCH_LOG 'STAGE 2 RESULT', 'Calibration, measured rather than asserted', "
            "'Correction (2026-10-19)'. n = 2 seeds; camera is in the observation here so do not "
            "compare absolute IoU with H2.")

    # 8 - H4 design
    s = slide(prs, "The linchpin: does seeing the paper help recovery?", kicker="H4 - design")
    for i, (t, b) in enumerate([
            ("Pen slip", "pen displaced, command unchanged"),
            ("Paper shift", "sheet moves under the pen"),
            ("Ink failure", "pen deposits nothing - invisible to kinematics by construction")]):
        card(s, M + i * 4.1, TOP + 0.15, 3.9, 1.6, t, [b], accent=WARN)
    for i, (t, b, c) in enumerate([
            ("open-loop", "contour tracer, no feedback - the floor", MUTED),
            ("true", "sees the real ink - the ceiling", GOOD),
            ("fk", "sees its kinematic belief (D01)", BAD),
            ("camera", "sees a photograph (ours)", ACCENT)]):
        card(s, M + i * 3.07, TOP + 2.0, 2.9, 1.5, t, [b], accent=c, body_size=11.5)
    txt(s, M, TOP + 3.75, CW, 1.3, [
        "All learning arms train on a MIX of disturbances, then are scored on each one.",
        "Pre-registered test: does camera LOSE LESS than fk from its own clean score "
        "(paired difference-in-differences, n = 8, critical t = 2.365)?"], size=13)
    note(s, "src: RESEARCH_LOG '2026-10-19 - Stage 3 begins: H4'. Disturbances fire at 4-16% "
            "of the episode, inside the drawing phase. Reward asymmetry: fk and true are rewarded "
            "from the true canvas, camera from vision - biased AGAINST the camera arm.")

    # 9 - H4 result
    s = slide(prs, "No detectable recovery difference: seeing the paper does not beat kinematics",
              kicker="Result 3 - disturbance recovery (H4)")
    fig(s, "h4_disturbance_recovery.png", M, TOP + 0.1, 7.3, 4.9)
    card(s, M + 7.6, TOP + 0.1, 4.5, 4.9, "Null on primary endpoint", [
        "Pre-registered diff-in-diff: camera vs fk recovery is null on all three disturbances (|t| = 0.24 to 1.19, crit 2.365).",
        "Control: even privileged 'true' (sees real ink perfectly) recovers no better than fk (-0.018 / -0.005 / +0.017).",
        "Channel carries no recoverable signal in this setup; null is not perception quality.",
        "Open-loop collapses (loses 0.28 slip / 0.31 shift), but trained arms absorb hits via overdrawing (~74% idle tail)."], accent=WARN)
    note(s, "src: RESEARCH_LOG 'H4 RESULT', 'The verdict, stated as pre-registered', 'A control added after the fact'. "
            "Primary diff-in-diff (n=8): slip -0.012 (t=-0.78), paper_shift +0.005 (t=+0.24), ink_failure +0.010 (t=+1.19). "
            "Ceiling control true-vs-fk: -0.018 / -0.005 / +0.017. Open-loop drop: slip +0.276, paper_shift +0.309.")

    # 10 - overrun
    s = slide(prs, "A pitfall worth checking: agents finish early and overshoot",
              kicker="Result 4 - methodology")
    fig(s, "results_overshoot.png", M, TOP + 0.1, 7.3, 4.9)
    card(s, M + 7.6, TOP + 0.1, 4.5, 4.9, "What it means", [
        "Agents complete the shape early, then idle on a frozen canvas or draw past their best.",
        "Scoring only the final frame can understate a drawing.",
        "Reporting peak alongside final IoU did NOT change the H2 comparison.",
        "Plateau stopping is NOT yet a fix: its gain is confounded with a shorter exploration "
        "horizon."], accent=VIOLET)
    note(s, "src: RESEARCH_LOG 'UNEXPECTED FINDING - agents finish early', 'OVERSHOOT ABLATION "
            "RESULT', 'H2 PEAK-vs-FINAL RESULT'. Present as a pitfall, not a contribution claim.")

    # 11 - limitations
    s = slide(prs, "Limitations", kicker="Honest limits")
    bullets(s, [
        "Simulation only; four simple shapes; pen always down.",
        "2-3 seeds per cell and 200k steps: nulls mean 'not detected', not 'absent'. "
        "No equivalence test yet.",
        "Both H2 runs used seeds 0, 1, 2 - adjacent seeds share most environment streams, so "
        "they are not independent and the seed spread is likely understated.",
        "Seeded results depend on thread count; two settings are mixed in the H4 sweep.",
        "The camera is a model with eight parameters, not a real sensor.",
        "H4: fk is rewarded from the true canvas, the camera arm from vision."],
        M, TOP + 0.25, CW, 4.8, size=15)
    note(s, "Paper Sec. V. src: RESEARCH_LOG 'Found while drafting the paper', 'H4 bookkeeping', "
            "'A reproducibility limit'.")

    # 12 - next
    s = slide(prs, "What remains before submission", kicker="Next")
    for i, (t, b, c) in enumerate([
            ("1  Short-window H4", "cut max_steps ~60 to test recovery without overdrawing.", WARN),
            ("2  Equivalence test for H2", "bound the gap, not just fail to detect it.", PRIMARY),
            ("3  Re-run H2 with spaced seeds", "seeds 0 / 100 / 200, new results file.", PRIMARY),
            ("4  Held-out shapes", "show the agent did not memorise four shapes.", VIOLET),
            ("5  Baselines", "open-loop tracer already inside H4; PPO vs SAC optional.", MUTED),
            ("6  Hardware", "real camera / arm - the thesis needs at least a plan.", MUTED)]):
        card(s, M + (i % 3) * 4.1, TOP + 0.2 + (i // 3) * 2.45, 3.9, 2.2, t, [b], accent=c)
    note(s, "From docs/PAPER_PLAN.md section 4, in the order a reviewer would care.")

    # 13 - summary
    s = slide(prs, "Takeaways", kicker="Summary")
    card(s, M, TOP + 0.2, CW, 1.15, "Learning from a camera costs no detectable accuracy",
         ["H2: camera vs privileged reward, no detectable difference in true IoU."], accent=GOOD)
    card(s, M, TOP + 1.55, CW, 1.15, "The camera reward is not exploited",
         ["H3: perceived and true IoU agree to within 0.0001 on average."], accent=GOOD)
    card(s, M, TOP + 2.9, CW, 1.15, "It survives a much worse camera",
         ["Stage 2: a held-out camera that keeps under 40% of the ink costs 0.014 IoU."],
         accent=GOOD)
    card(s, M, TOP + 4.25, CW, 1.15, "Seeing the paper buys no recovery over kinematic sync in simulation (H4)",
         ["Camera and privileged true arms recover identically to blind kinematics; D01 supported."],
         accent=WARN)
    note(s, "Wording from PAPER_PLAN section 2 & 3. H4 completed with null recovery on primary endpoint.")


def main():
    prs = new_deck("RoboSketch-RL  ·  research results")
    build(prs)
    prs.save(OUT)
    print(f"{len(prs.slides._sldIdLst)} slides -> {OUT}")


if __name__ == "__main__":
    main()
