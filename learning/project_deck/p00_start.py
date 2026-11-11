"""Section 0 - start here: title, how to use, the project in one picture, map, timeline."""
from kit import *  # noqa: F401,F403
from kit import _blank, _state


def title_slide(prs):
    s = _blank(prs)
    _state["n"] += 1
    _state["section"] = ""
    rect(s, 0, 0, W, H, fill=NAVY)
    rect(s, 0, 0, W, 0.20, fill=PRIMARY)
    rect(s, 0, 0.20, W * 0.42, 0.06, fill=ACCENT)
    txt(s, 1.1, 1.35, 11, 0.4, "LEARN THE WHOLE PROJECT  ·  FROM ZERO TO THE FINAL RESULTS",
        size=13, color=ACCENT, bold=True)
    txt(s, 1.1, 1.85, 11, 1.0, "RoboSketch-RL", size=52, color=WHITE, bold=True)
    txt(s, 1.1, 2.85, 11, 0.9, "A robot arm that learns to draw — and what it loses (or gains) "
        "by learning from its camera", size=22, color=RGBColor(0xC9, 0xD4, 0xE8))
    rect(s, 1.13, 3.95, 2.0, 0.035, fill=PRIMARY)
    txt(s, 1.1, 4.15, 11, 1.3,
        ["Robotics, computer vision, machine learning, reinforcement learning, PPO, "
         "statistics — explained from the basics, every equation typeset, every design "
         "choice with its WHY, every result with its numbers and its limits."],
        size=16, color=RGBColor(0xA9, 0xB6, 0xCE), spacing=1.3)
    rect(s, 1.1, 5.55, 11.1, 0.012, fill=RGBColor(0x2C, 0x3A, 0x5C))
    txt(s, 1.1, 5.75, 6.0, 1.0, ["Viral Kanani  ·  individual research project",
                                 "State of the project: 8 Nov 2026 (simulation complete)"],
        size=13, color=RGBColor(0xA9, 0xB6, 0xCE), spacing=1.35)
    txt(s, 7.0, 5.75, 5.2, 1.0, ["Every number traces to docs/RESEARCH_LOG.md",
                                 "Speaker notes = your tutor, in Hinglish"],
        size=13, color=RGBColor(0xA9, 0xB6, 0xCE), spacing=1.35, align=PP_ALIGN.RIGHT)
    note(s, """
Namaste Viral! Yeh deck aapke liye hai - taaki aap poora project zero se samajh sako aur
interview me har design choice ka "kyun" (why) bata sako.

Kaise padhna hai: har slide par English me short points hain (jo aap interview me bol sakte ho).
Neeche speaker notes me main tutor ki tarah Hinglish me detail me samjhata hoon - pehle simple
idea, phir math, phir "is project me yeh kahan aaya aur kyun".

Ek zaroori niyam: is deck ka har number project ke apne records se aaya hai - docs/paper/main.tex,
docs/PAPER_PLAN.md, README.md ya docs/RESEARCH_LOG.md ki kisi dated entry se. Har slide ke notes
ke end me "Source:" likha hai. Jo chhote "toy" examples hain (jaise 2-link arm ka hisaab), woh
deck ki apni script (teach_figs.py) ne compute kiye hain - woh project ke results NAHI hain, aur
slide par "toy" likha hai.

Deck ke end me glossary, formula sheet aur ek quiz hai - khud ko test karne ke liye.
""")


def how_to_use(prs):
    s = slide(prs, "How to use this deck", "start here",
              "Read in order once; afterwards jump by section. Colours always mean the same thing.")
    items = [(PRIMARY, "Structure", "what the system is and how it is built"),
             (ACCENT, "Vision / data", "camera, images, measurements"),
             (VIOLET, "Maths / learning", "equations and the WHY strips"),
             (GOOD, "Result", "measured, logged, survived a test"),
             (WARN, "Caveat", "a limit, a confound, a challenge"),
             (BAD, "Negative / wrong", "an idea that failed or a bug")]
    for i, (c, t, d) in enumerate(items):
        r, k = divmod(i, 3)
        x, y = M + k * 4.08, s._top + 0.05 + r * 1.0
        rect(s, x, y, 3.92, 0.85, fill=WASH, line=LINE, shape=MSO_SHAPE.ROUNDED_RECTANGLE,
             radius=0.08)
        rect(s, x + 0.18, y + 0.22, 0.40, 0.40, fill=c, shape=MSO_SHAPE.ROUNDED_RECTANGLE,
             radius=0.25)
        txt(s, x + 0.75, y + 0.10, 3.1, 0.32, t, size=15, color=c, bold=True)
        txt(s, x + 0.75, y + 0.45, 3.1, 0.32, d, size=12, color=MUTED)
    bullets(s, [
        "Every topic follows the same path: everyday idea → precise definition → equation → "
        "where it lives in RoboSketch-RL → WHY it was chosen.",
        "Equation slides: the big equation on top, every symbol explained below it, a tiny "
        "worked example on the right, and a purple WHY strip at the bottom.",
        "Result slides always give n, mean ± sd, the paired difference, pairs up (k/n) and t — "
        "and say what the result does NOT show.",
        "End of deck: glossary, a 3-slide formula sheet and a self-test quiz with answers.",
    ], M, s._top + 2.15, CW, 2.6, start=16)
    strip(s, "Rule used everywhere: a result counts only if it was measured, logged, and survived "
          "a fair, pre-stated statistical test.", GOOD)
    note(s, """
Rangon ka matlab fix hai: neela = system ka structure, cyan = camera/data, purple = math aur
"WHY" (kyun), hara = measured result, amber = caveat/limit, laal = jo galat nikla ya bug tha.

Har topic ek hi raaste se aata hai: roz-marra ka idea -> sahi definition -> equation -> project me
kahan -> kyun chuna. Agar koi equation slide bhaari lage, to pehle neeche wali WHY strip padho,
phir symbols, phir example.

Result slides par hamesha paanch cheezen hongi: n (kitne paired runs), mean +/- sd, paired
difference, kitne pairs me ek arm aage tha (k/n), aur t statistic. Section 8 me yeh sab zero se
samjhaya hai.
""")


def big_picture(prs):
    s = slide(prs, "The whole project in one picture", "start here",
              "A learning loop: the agent moves a pen, ink lands, a score comes back, the agent improves.")
    y = s._top + 0.35
    steps_ = [("TARGET", "line / circle /\nsquare / triangle", PRIMARY),
              ("AGENT", "CNN policy\ntrained with PPO", VIOLET),
              ("ACTION", "move pen by\n(dx, dy)", VIOLET),
              ("PEN + PAPER", "pen moves (KUKA + IK\nfor validation); ink lands", PRIMARY),
              ("SEE IT", "exact canvas (truth)\nOR camera photo", ACCENT),
              ("REWARD", "did IoU with the\ntarget go up?", GOOD)]
    bw, gap = 1.72, 0.33
    for i, (t, sb, c) in enumerate(steps_):
        x = M + i * (bw + gap)
        node(s, x, y, bw, 1.35, t, sb, color=c, title_size=14, sub_size=11.5)
        if i < len(steps_) - 1:
            arrow(s, x + bw + 0.04, y + 0.67, x + bw + gap - 0.04, y + 0.67, lw=1.8)
    xa = M + 5 * (bw + gap) + bw / 2
    xb = M + 1 * (bw + gap) + bw / 2
    elbow(s, [(xa, y + 1.37), (xa, y + 1.95), (xb, y + 1.95), (xb, y + 1.39)], color=GOOD, lw=2.2)
    txt(s, xb + 0.5, y + 2.0, 7.5, 0.35, "repeat ~200,000 steps: the agent learns which moves raise the score",
        size=13, color=GOOD, bold=True)
    card(s, M, y + 2.62, 5.95, 1.65, "THE RESEARCH TWIST",
         ["The reward (and later the observation) can come from a simulated CAMERA instead of the "
          "exact digital canvas. A real robot only has the camera. We measure what that costs."],
         accent=ACCENT)
    card(s, M + 6.2, y + 2.62, CW - 6.2, 1.65, "THE FAIRNESS RULE",
         ["Whatever an agent saw or was rewarded with, it is always SCORED on the true canvas "
          "(true IoU). No agent gets credit for what its camera merely believes."],
         accent=GOOD)
    strip(s, "One sentence: teach a pen-drawing agent by trial and error, judged by what a camera "
          "sees, and measure honestly whether that is as good as perfect information.", PRIMARY)
    note(s, """
Poora project ek loop hai. Target shape hai (jaise circle). Agent ek neural network hai jo
decide karta hai ki pen ko is step me kitna (dx, dy) khiskana hai. Inverse kinematics (IK) us
pen-move ko robot ke joints ke angles me badalta hai (training me hum pen point ko seedha
khiskate hain - fast backend; IK wala arm validation ke liye hai). Ink paper par girti hai.
Phir score: drawing target se kitna milti hai (IoU). Score badha = positive reward.

Research twist: yeh score DO jagah se aa sakta hai - exact digital canvas se (jo asli robot ke
paas nahi hota) ya camera ki photo se (jo asli robot ke paas hota hai). Hum naapte hain ki camera
se seekhne me kitna nuksaan hota hai, aur kya camera galtiyon (jaise paper khisakna) se ubarne
me madad karta hai.

Fairness rule yaad rakhna - interview me zaroor poocha jayega: evaluation hamesha TRUE IoU par
hota hai. Camera wala agent apne camera ko "bewakoof" bana ke score nahi le sakta.
""", "README.md 'How it works'; rl/draw_env.py (info['iou'] is always the true IoU); "
       "rl/experiment.py (200k timesteps)")


def six_sentences(prs):
    s = slide(prs, "The project in six sentences", "start here")
    rows = [("PROBLEM", "Learned drawing agents are rewarded from an exact virtual canvas — a "
             "'privileged' signal no physical robot has.", PRIMARY),
            ("SETUP", "A simulated KUKA arm (PyBullet) moves a pen in small steps; a PPO agent "
             "with a CNN learns from images; scoring is true IoU.", VIOLET),
            ("QUESTION 1", "How much accuracy is lost when the reward comes from a camera "
             "instead of the truth?  → none detectable: equivalent within ±0.05 IoU (TOST).", ACCENT),
            ("QUESTION 2", "Does seeing the paper help when things go wrong?  → yes for a paper "
             "shift (replicated), no detectable gain for pen slip or ink failure.", GOOD),
            ("LIMITS", "Simulation only, four simple shapes, modest absolute IoU (~0.4), weak "
             "generalisation, far below a scripted tracer.", WARN),
            ("NOT CLAIMED", "Not 'RL drawing is new', not 'vision rewards are new', not "
             "'visual feedback for drawing is new'. It is a measurement.", BAD)]
    for i, (lab, t, c) in enumerate(rows):
        y = s._top + 0.02 + i * 0.86
        chip(s, M, y + 0.18, 1.75, 0.42, lab, color=c, size=11.5)
        txt(s, M + 2.0, y + 0.05, CW - 2.05, 0.8, t, size=16, color=BODY, anchor=MSO_ANCHOR.MIDDLE)
        if i < len(rows) - 1:
            rect(s, M + 2.0, y + 0.84, CW - 2.05, 0.01, fill=LINE)
    note(s, """
Agar koi aapse 1 minute me project poochhe, to yeh 6 lines bolo:
1) Problem: drawing agents ko ek perfect digital canvas se reward milta hai - yeh "privileged"
   signal hai, asli robot ke paas nahi hota.
2) Setup: PyBullet me KUKA arm, pen chhote steps me chalta hai, PPO agent CNN se images dekh kar
   seekhta hai, aur score true IoU hai.
3) Sawaal 1: camera se reward dene par kitni accuracy jaati hai? Jawab: koi detectable nuksaan
   nahi - TOST test se +/-0.05 IoU ke andar "equivalent".
4) Sawaal 2: kya paper dekhne se galtiyon se ubarna aasaan hota hai? Paper shift ke liye haan
   (replicated), pen slip / ink failure ke liye koi detectable fayda nahi.
5) Limits: sirf simulation, 4 simple shapes, absolute IoU ~0.4, generalisation kamzor, scripted
   tracer se kaafi neeche.
6) Claim NAHI: RL drawing naya nahi, vision reward naya nahi, visual feedback naya nahi. Yeh ek
   careful measurement hai.
""", "README.md 'Main results'; docs/PAPER_PLAN.md section 2 (C1, C4, C8); AGENTS.md section 1")


def deck_map(prs, toc):
    s = slide(prs, "Map of the deck", "start here", "Slide numbers are filled in automatically.")
    secs = [(1, "The problem & the research question", "privileged canvas, D01, what is claimed"),
            (2, "Robotics from scratch", "joints, FK, IK, Jacobian, pen space, PyBullet"),
            (3, "Computer vision from scratch", "images, camera, threshold, IoU, phase correlation"),
            (4, "Machine-learning basics", "neural nets, loss, gradient descent, CNNs"),
            (5, "Reinforcement learning from scratch", "MDP, return, value, Bellman, policy"),
            (6, "Policy gradients → PPO", "advantage, GAE, clipping, our hyper-parameters, SAC"),
            (7, "The drawing environment", "observation, action, reward, episode, bugs that shaped it"),
            (8, "Experimental method & statistics", "seeds, paired t, diff-in-diff, TOST"),
            (9, "Results, one by one", "H1–H6, generalisation, Stage 4, extensions"),
            (10, "What we can and cannot claim", "claims map, wording, threats to validity"),
            (11, "What comes next", "sim-to-real, letters"),
            (12, "Review", "glossary, formula sheet, self-test quiz")]
    for i, (n, t, d) in enumerate(secs):
        r, k = divmod(i, 2)
        x, y = M + k * 6.15, s._top + 0.02 + r * 0.83
        pg = toc.get(n)
        txt(s, x, y + 0.04, 0.75, 0.5, f"{n:02d}", size=24, color=PRIMARY, bold=True)
        txt(s, x + 0.8, y + 0.02, 4.4, 0.34, t, size=15, color=INK, bold=True)
        txt(s, x + 0.8, y + 0.38, 4.4, 0.3, d, size=11.5, color=MUTED)
        if pg:
            txt(s, x + 5.1, y + 0.08, 0.9, 0.4, f"p. {pg}", size=13, color=SLATE, bold=True,
                align=PP_ALIGN.RIGHT)
    note(s, """
Deck ke 12 hisse hain. Section 1 batata hai problem kya hai. Section 2-6 "foundation" hain -
robotics, computer vision, machine learning, RL aur PPO ka math. Inko samajh liya to baaki sab
aasaan hai. Section 7 hamara drawing environment hai - observation, action, reward, aur woh bugs
jinhone design ko shape kiya. Section 8 statistics hai - result ko "result" kehne ka haq kaise
milta hai. Section 9 me har experiment ka result hai. Section 10 claims aur limits, 11 aage kya,
12 revision (glossary, formula sheet, quiz).

Suggestion: pehli baar shuru se end tak padho. Interview se pehle sirf Section 1, 7, 9, 10 aur
quiz dobara dekh lo.
""")


def timeline(prs):
    s = slide(prs, "How the project unfolded (Jul – Nov 2026)", "start here",
              "Dates are the headings of docs/RESEARCH_LOG.md.")
    ev = [("24 Jul", "Simulator: IK to 0.1 mm, pen ink, virtual camera (Phase B done)", PRIMARY),
          ("5 Aug", "RL begins: DrawEnv + PPO; first learned line (IoU 0.508)", VIOLET),
          ("7–12 Aug", "Camera reward (H2); multi-seed sweep; literature review (33 papers)", ACCENT),
          ("23 Aug", "H3: no reward exploitation; overrun / overshoot discovered", GOOD),
          ("3 Sep", "Code review finds two bugs; thread count changes seeded results", BAD),
          ("12 Sep", "Camera randomisation: buys nothing (negative result)", WARN),
          ("19–28 Oct", "H4 v1 and H4-short: two nulls; diff-in-diff lesson; seed-overlap lesson", BAD),
          ("29–30 Oct", "Oracle check → H4 v3 (privileged) → H4 v4: camera estimates the offset", ACCENT),
          ("31 Oct", "H2 re-run on spaced seeds: equivalent (TOST); generalisation is a limit", GOOD),
          ("1–7 Nov", "Stage 4–6: ego view helps; curriculum, chunking, BC do not; digits", VIOLET),
          ("8 Nov", "H4 v4 replicated on fresh seeds (pre-registered); paper draft v2", GOOD)]
    top = s._top + 0.05
    rh = (6.95 - top) / len(ev)
    rect(s, M + 1.62, top + 0.1, 0.03, rh * len(ev) - 0.2, fill=LINE)
    for i, (d, t, c) in enumerate(ev):
        y = top + i * rh
        txt(s, M, y, 1.45, rh, d, size=13, color=c, bold=True, align=PP_ALIGN.RIGHT,
            anchor=MSO_ANCHOR.MIDDLE)
        rect(s, M + 1.555, y + rh / 2 - 0.08, 0.16, 0.16, fill=c, shape=MSO_SHAPE.OVAL)
        txt(s, M + 1.95, y, CW - 2.0, rh, t, size=14.5, color=BODY, anchor=MSO_ANCHOR.MIDDLE)
    note(s, """
Project ka safar - taaki aapko pata ho kaunsi cheez kab aur kyun hui:
- July end: simulator bana - IK 0.1 mm tak accurate, pen ink chhodta hai, virtual camera dekhta hai.
- 5 Aug: RL shuru. Pehli baar agent ne line banana seekha (IoU 0.508).
- Aug: camera reward (H2), multi-seed, aur 33 papers ka literature review.
- 23 Aug: H3 - agent camera ko cheat nahi kar raha. Aur ek unexpected finding: agent jaldi
  khatam kar leta hai, phir overshoot karta hai, phir baaki episode khaali baitha rehta hai.
- 3 Sep: review me mere (AI ke) do bugs pakde gaye; thread count se seeded result badalta hai.
- 12 Sep: camera randomisation ne kuch nahi diya - negative result, honestly report kiya.
- Oct: H4 - sabse important experiment. Pehle do design null aaye. Phir oracle check, v3, v4.
- 31 Oct: H2 dobara spaced seeds par - equivalence test pass. Generalisation ek limit nikli.
- Nov: Stage 4-6 ablations; 8 Nov ko H4 v4 fresh seeds par replicate hua; paper draft.

Interview tip: yeh kahani batati hai ki project "seedha" nahi chala - nulls aaye, bugs mile, aur
har baar honestly log kiya gaya. Yahi research maturity hai.
""", "docs/RESEARCH_LOG.md headings dated 2026-07-23 to 2026-11-08; first line IoU 0.508 from "
       "'First PPO training experiments on line'")


def build(prs, toc):
    title_slide(prs)
    how_to_use(prs)
    big_picture(prs)
    six_sentences(prs)
    deck_map(prs, toc)
    timeline(prs)
