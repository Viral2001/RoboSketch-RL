"""Section 1 - the problem and the research question."""
from kit import *  # noqa: F401,F403
from teach_figs import TOY


def build(prs, toc):
    section(prs, 1, "The problem & the research question",
            "What the robot must do, why a 'privileged canvas' is a problem, the one objection "
            "that could sink the project, and exactly what is - and is not - claimed.",
            ["The drawing task", "Privileged canvas vs camera", "The two questions",
             "D01: the camera-free objection", "What is NOT new", "Hypotheses & status"],
            """
Section 1: problem kya hai. Is section ke baad aapko ek line me bolna aana chahiye ki yeh project
kya naapta hai, aur kya claim NAHI karta. Interview me sabse pehla sawaal yahi hota hai:
"What is new here?" - aur iska sahi, honest jawab is section me hai.""", toc)

    sh = TOY["sheet"]
    s = slide(prs, "The task: draw a target shape with a pen", "01 · problem",
              "Four targets (the 'task ladder'), each a binary mask with a thick 14-px stroke at 512 px.")
    pic(s, "fig_targets.png", M, s._top + 0.02, CW, 2.25)
    bullets(s, [
        f"A {sh['side_cm']} cm × {sh['side_cm']} cm sheet in simulation (half-width 0.10 m); the "
        f"drawing is stored as a {sh['canvas_res']}×{sh['canvas_res']} image (the 'canvas').",
        "Each step the agent nudges the pen by up to 0.014 m (≈ 8.9 canvas px) in x and y; the "
        "pen starts on the target, at the target pixel nearest the sheet centre.",
        "An episode is 240 steps (60 in the H4 experiments). Then the drawing is scored.",
        "Score = IoU (overlap) between the true ink and the target: 1 = perfect, 0 = no overlap.",
    ], M, s._top + 2.45, CW, 2.35, start=16)
    strip(s, "Why thick targets? A 1-2 px target punishes any 1-px drift; a 14-px band lets the agent "
          "learn the shape first (rl/targets.py comment).", WARN)
    note(s, """
Robot ko kya karna hai? Ek target shape banana - line, circle, square, triangle. Har target ek
"mask" hai: 512x512 ki black-white image jisme 14 pixel moti line hai. Yeh 4 shapes "task ladder"
kehlate hain (aasaan se mushkil).

Paper simulation me 20 cm x 20 cm hai. Drawing 128x128 pixel ki image (canvas) me record hoti
hai. Har step par agent pen ko thoda sa (max 1.4 cm, yaani ~8.9 canvas pixel) khiskata hai. Ek
episode 240 steps ka hai (H4 me 60). End me score: IoU - drawing aur target ka overlap.

Target mota kyun? Kyunki IoU bahut sakht metric hai - agar target 1-2 pixel patla ho, to 1 pixel
idhar-udhar hone par hi IoU gir jaata hai, aur agent kabhi seekh hi nahi paata. Mota target pehle
"shape" seekhne deta hai; patla karna baad ka difficulty step hai.
""", "rl/targets.py (RES 512, STROKE_PX 14, MARGIN 0.20); rl/draw_env.py (PAPER_HALF 0.10, "
       "canvas_res 128, start_on_target); docs/paper/main.tex Setup (240 steps of 0.014 m; 60 in H4); "
       "RESEARCH_LOG H5 entry (1 step ~8.9 canvas px); sheet size computed by teach_figs.py")

    # privileged canvas vs camera
    s = slide(prs, "The privileged-canvas problem", "01 · problem",
              "Where does the 'how good is my drawing?' signal come from?")
    y1, y2 = s._top + 0.55, s._top + 2.55
    txt(s, M, y1 - 0.45, 9, 0.35, "MOST LEARNED DRAWING AGENTS (D02, D05, D06, D07, D01)", size=13,
        color=SLATE, bold=True)
    pipeline(s, [("strokes", "the agent's actions"), ("exact virtual canvas", "a perfect digital copy"),
                 ("reward", "perfect, noise-free")], M, y1, 8.4, 1.15,
             colors=[VIOLET, BAD, GOOD])
    txt(s, M, y2 - 0.45, 9, 0.35, "A PHYSICAL ROBOT", size=13, color=SLATE, bold=True)
    pipeline(s, [("pen on paper", "real ink, real errors"), ("camera photo", "blur, light, noise,\nregistration"),
                 ("reward", "imperfect")], M, y2, 8.4, 1.15, colors=[PRIMARY, ACCENT, WARN])
    card(s, M + 8.75, y1 - 0.45, CW - 8.75, 3.95, "WHY IT MATTERS",
         ["The exact canvas is 'privileged': it does not exist on a real robot.",
          "So results from canvas-trained agents may not tell us what a camera-trained robot can do.",
          "This project measures that gap, in simulation, under controlled conditions."],
         accent=VIOLET)
    strip(s, "Privileged = information available in simulation but not to the real system. Our camera "
          "arms must learn without it.", ACCENT)
    note(s, """
"Privileged" ka matlab: woh jaankari jo simulation me free me milti hai par asli robot ke paas
nahi hoti. Drawing agents (D02 Huang, D05/D06 SPIRAL, D07 Zhou, D01 Lee) apna reward ek exact
digital canvas se lete hain - har pixel bilkul sahi pata hai.

Asli robot ke paas yeh canvas nahi hota. Usko pata karna padega ki paper par kya bana - camera se.
Aur camera blur karta hai, roshni badalti hai, photo thodi tedhi ho sakti hai (registration),
noise hota hai.

To sawaal: jo agent camera ki photo se seekhta hai, kya woh utna hi achha draw karta hai jitna
perfect canvas se seekhne wala? Yahi project naapta hai. Hum koi naya algorithm nahi bana rahe -
hum ek gap ko carefully measure kar rahe hain.
""", "docs/paper/main.tex Introduction (cites D02, D05, D06, D07, D01); docs/PAPER_PLAN.md section 1")

    concept(prs, "01 · question", "The two research questions", None,
            ["Q1 - COST: how much drawing accuracy is lost when the reward comes from a camera "
             "image instead of the truth?",
             (1, "Tested by H2 (reward source is the only variable) and H3 (does the agent cheat the camera?)."),
             "Q2 - BENEFIT: does seeing the paper help when things go wrong - the paper slides, the pen "
             "slips, the ink runs out - compared with a robot that draws 'blind' from its joint angles?",
             (1, "Tested by H4 (disturbance recovery), the experiment that answers D01."),
             "Both are MEASUREMENTS with paired multi-seed statistics, not new algorithms."],
            cards=[("HOW Q1 IS JUDGED", ["Same agent, same everything, only the reward source differs.",
                                         "Scored on TRUE IoU. Equivalence tested with TOST."], ACCENT),
                   ("HOW Q2 IS JUDGED", ["Disturbance fired mid-drawing; measure how much each arm LOSES "
                                         "from its own clean score (difference-in-differences)."], GOOD)],
            take="Cost and benefit: a camera is worth adding only if it costs little (Q1) and buys "
                 "something kinematics cannot (Q2).", take_color=VIOLET,
            notes="""
Do sawaal hain, aur dono zaroori hain.

Q1 - Cost (nuksaan): camera se reward dene par accuracy kitni girti hai? Isko H2 naapta hai -
do agents bilkul same, sirf reward ka source alag (truth vs camera). H3 check karta hai ki agent
camera ko "cheat" to nahi kar raha.

Q2 - Benefit (fayda): jab kuch galat ho (paper khisak jaye, pen phisle, ink khatam ho), kya camera
wala agent behtar sambhalta hai us agent se jo sirf apne joint angles (kinematics) par bharosa
karta hai? Isko H4 naapta hai.

Kyun dono? Agar camera sirf nuksaan karta aur fayda kuch nahi, to camera lagane ka koi reason
nahi. Agar fayda hai par nuksaan bhi bahut, to bhi problem. Dono naapne se poori tasveer milti hai.
""", source="README.md 'The question'; docs/PAPER_PLAN.md section 1")

    concept(prs, "01 · the objection", "The one objection that could sink the project: D01",
            "Lee et al., ICRA 2022 - a robotic sketching agent with NO camera.",
            ["D01 keeps its virtual canvas in sync with the pen position the arm actually reaches - "
             "through the robot's own kinematic state, without a camera.",
             "It assumes that wherever the pen tip went, the mark appeared in the expected place on the sheet.",
             "The authors attribute their agent's robustness to this camera-free design.",
             "If that is enough, there is little reason to put a camera in the learning loop at all - "
             "a complete answer to this project's motivation.",
             "So H4 is the most important experiment: is there an error that kinematics CANNOT see "
             "but a camera can?"],
            cards=[("THEIR OWN WORDS (D01, Sec. V)",
                    ["\"using a camera as an observation of canvas in the future work could be of great "
                     "help in the synchronization step\""], ACCENT),
                   ("WHAT KINEMATICS CANNOT SEE", ["The sheet sliding under the pen; ink that did not land; "
                                                   "a pen knocked sideways after the joints reached the target."], WARN)],
            take="H4 asks: when the world misbehaves, does seeing the paper beat trusting the joints?",
            take_color=VIOLET,
            notes="""
D01 (Lee et al., ICRA 2022) is project ka sabse bada "challenge" hai. Unka robot bina camera ke
achha sketch karta hai. Woh apna virtual canvas robot ke kinematic state se update karte hain -
pen jahan pahuncha, wahan line bani maan lete hain. Aur woh kehte hain ki unki robustness isi
camera-free design ki wajah se hai.

Agar yeh kaafi hai, to camera ka koi fayda nahi - aur hamara pura motivation khatam. Isliye
AGENTS.md kehta hai: H4 sabse important experiment hai.

Ek sudhaar jo paper likhte waqt PDF padh kar kiya gaya: D01 "commanded" stroke nahi, balki arm
jahan ACTUALLY pahuncha woh position use karta hai. Isse arm ki tracking error pakdi jaati hai,
par paper par kya hua (paper khisakna, ink na girna) nahi. Hamara `fk` arm isi condition ko
represent karta hai.

Interesting: D01 ke authors khud future work me likhte hain ki camera "could be of great help in
the synchronization step". Yahi gap hum naap rahe hain.
""", source="AGENTS.md section 1; docs/paper/main.tex Introduction (quotes verified vs PDF 2026-11-08); "
            "RESEARCH_LOG '### Paper: intro quotes checked against the PDFs; D01 description corrected'")

    grid(prs, "01 · honesty", "What is NOT claimed (it already exists)",
         "All of these are prior art; claiming them would be wrong and easy to reject.",
         [("RL FOR ROBOT DRAWING", ["Not new: D01, D02, D05, D09 already do it."], BAD),
          ("VISION-BASED REWARDS", ["Not new: Sermanet et al. RSS'17, Singh et al. RSS'19 reward robots "
                                    "from images."], BAD),
          ("CLOSED-LOOP VISUAL FEEDBACK", ["Not new: FRIDA (ICRA'23) and the e-David painting machine "
                                           "photograph the canvas and replan."], BAD),
          ("WHAT IS CLAIMED", ["A MEASUREMENT: what learning from perception instead of truth costs, "
                               "and whether seeing the paper helps when things go wrong."], GOOD),
          ("WHY THAT IS A CONTRIBUTION", ["The closest papers name this as an open question (D01, D03, "
                                          "D09). Careful numbers on an open question are publishable."], GOOD),
          ("WORDS NEVER USED", ["'novel', 'first', 'proves', 'no difference', 'outperforms'. Use "
                                "'no detectable difference', 'equivalent within ±0.05 IoU (TOST)'."], WARN)],
         cols=3, take="Interview line: 'This is a measurement paper, not a new algorithm.'",
         notes="""
Yeh slide interview me aapko bachayegi. Teen cheezen NAYI NAHI hain, aur inko kabhi naya mat
bolna:
1) RL se robot drawing - D01, D02, D05, D09 pehle kar chuke hain.
2) Image se reward - Sermanet (RSS 2017), Singh (RSS 2019).
3) Camera se feedback le kar drawing sudharna - FRIDA (ICRA 2023), e-David machine.

To naya kya hai? Ek MEASUREMENT: camera se seekhne ki keemat kya hai, aur kya camera disturbance
me madad karta hai. Aur yeh valid contribution hai kyunki closest papers (D01, D03, D09) khud ise
open question bolte hain.

Shabdon ka dhyan: "novel", "first", "proves" kabhi nahi. "No difference" nahi - "no detectable
difference". "Equivalent" sirf tab jab TOST test pass ho (H2 me hua).
""", source="AGENTS.md section 1; docs/PAPER_PLAN.md sections 5 and 7; docs/paper/main.tex Related Work")

    tabular(prs, "01 · status", "Hypotheses and where each one stands", "Status as of 8 Nov 2026.",
            ["ID", "Statement (short)", "Status / headline evidence"],
            [["H1", "RL can learn to draw in pen space, no demos", "Yes - every shape learned (single 400k runs IoU 0.42–0.51); level modest"],
             ["H2", "Camera reward ≈ truth reward", "Equivalent within ±0.05 IoU (TOST p = 0.008, n = 12)"],
             ["H3", "Camera reward is not exploited", "No exploitation: mean gap -0.0001 over 3328 episodes"],
             ["H4", "Camera recovers from errors kinematics cannot see", "Paper shift: replicated (+0.119, 8/8, t = +8.32); slip / ink: none detectable"],
             ["H5", "Open-loop error grows, closed-loop stays flat", "Supported (shows feedback matters, not a camera)"],
             ["H6", "Agents finish early and overshoot", "Measured (mean 0.064 IoU lost); plateau stop is not a 'fix'"],
             ["RQ3", "PPO vs SAC", "SAC far behind at this budget: 0.051 vs 0.292 (t = -9.71, 0/8)"],
             ["RQ4", "Shape curriculum helps", "No - it hurts (0.246 vs 0.418, t = -2.99)"]],
            colw=[0.8, 4.2, 6.8], size=12.5, row_h=0.47, align="left",
            cell_colors={(1, 2): GOOD, (2, 2): GOOD, (3, 2): GOOD, (6, 2): BAD, (7, 2): BAD},
            take="Each line gets its own results slide in Section 9.", take_color=PRIMARY,
            notes="""
Yeh poore project ka scoreboard hai. H1 se H6 hypotheses hain, RQ3/RQ4 research questions.

H1: haan, agent drawing seekhta hai - par absolute level modest hai (~0.4-0.5 IoU).
H2: camera reward aur truth reward statistically equivalent hain +/-0.05 IoU ke andar.
H3: agent camera ko cheat nahi karta.
H4: paper shift ke liye camera (jo offset khud estimate karta hai) kinematics se kam haarta hai -
fresh seeds par replicate bhi hua. Pen slip aur ink failure par koi detectable fayda nahi.
H5: open-loop (bina feedback) error badhta jaata hai; closed-loop flat rehta hai. Dhyan: yeh
feedback ka fayda dikhata hai, camera ka nahi.
H6: agent jaldi khatam karke overshoot karta hai.
RQ3 (PPO vs SAC): 9-10 Nov 2026 ko chalaya (~30 ghante, do workers). SAC bahut peeche raha: 0.051 vs PPO 0.292, 8 me se
0 cells me aage, t=-9.71. Dhyan: SAC ko kam gradient updates mile (ratio 0.25), isliye yeh "PPO hamesha
behtar" nahi - sirf "is budget par SAC bahut peeche".
RQ4: curriculum (pehle line, phir shape) ne nuksaan kiya - negative result.

Har line ka detail Section 9 me hai.
""", source="docs/PAPER_PLAN.md section 2 (C1-C11); docs/HANDOFF.md; RESEARCH_LOG 'Full task ladder trained', "
            "'### H2 spaced RESULT', 'H3 RESULT', '### H4 v4 confirmation RESULT', H5 entry, "
            "'UNEXPECTED FINDING', '### RQ3 PPO vs SAC RESULT', '### RQ4 curriculum RESULT'")

    s = slide(prs, "The gap, in the closest papers' own words", "01 · positioning",
              "Quoted from the PDFs (checked word for word on 8 Nov 2026).")
    quotes = [("D01  Lee et al., ICRA 2022",
               "\"using a camera as an observation of canvas in the future work could be of great help "
               "in the synchronization step\"", ACCENT),
              ("D03  Kotani & Tellex, ICRA 2019",
               "\"closing the learning loop by enabling the robot to inspect what it has drawn\"", PRIMARY),
              ("D09  Luo et al., ICRA 2024",
               "\"a lack of real-world training scenarios to bridge the sim2real gap. We leave these "
               "challenges as our future work.\"", VIOLET)]
    for i, (who, q, c) in enumerate(quotes):
        y = s._top + 0.05 + i * 1.5
        card(s, M, y, CW, 1.35, who, [q], accent=c, start=17)
    strip(s, "All three name 'learning from what the robot actually sees' as future work - that is "
          "the space this measurement occupies.", GOOD)
    note(s, """
Teen closest papers khud yeh gap bolte hain - isliye hum unhe quote karte hain:
- D01 (Lee): camera canvas observe kare to synchronization me madad mil sakti hai.
- D03 (Kotani & Tellex): robot jo draw kar chuka hai use inspect karke learning loop band karna.
- D09 (Luo, CalliRewrite): real-world training scenarios ki kami, sim2real gap - future work.

Yeh quotes 8 Nov 2026 ko original PDFs se word-for-word check kiye gaye. Interview me bolna:
"The closest work names this as future work; I measured it." Bas itna - isse zyada nahi.
""", "docs/PAPER_PLAN.md section 5; RESEARCH_LOG '### Paper: intro quotes checked against the PDFs'")
