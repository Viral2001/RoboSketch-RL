"""Part 6 - H4 (data-driven), statistics & research honesty, status & roadmap, Q&A, glossary."""
from gk import (ACCENT, BAD, BODY, CW, GOOD, INK, LINE, M, MUTED, NAVY, PRIMARY, SLATE, VIOLET,
                WARN, WASH, WHITE, W, H, arrow, bullets, card, chip, concept, grid, node, note,
                rect, section, slide, steps, strip, tabular, txt, analogy)
from deck_kit import qa
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN

import h4data

KIND_LABEL = {"slip": "slip", "paper_shift": "paper shift", "ink_failure": "ink failure"}


# ================================================================== H4 ======
def h4(prs, st):
    section(prs, 9, "H4 — the linchpin experiment",
            "Does seeing the paper let the agent recover from errors that forward kinematics "
            "cannot see? Without an answer, the closest published system is a complete reply "
            "to this project's motivation.",
            ["Why H4 decides the framing", "Three disturbances", "Four arms",
             "Premise check", "Difference-in-differences", "Pre-registered rule", "The result"])

    concept(prs, "09 · why", "Why H4 decides how the paper is framed",
            "D01 (Lee et al., ICRA 2022) draws well with NO camera — and argues that is an advantage.",
            ["D01 synchronises through forward kinematics (FK): the robot BELIEVES the pen is "
             "wherever it commanded it, and that the ink landed.",
             "Its argument: a camera adds nuisance variation (light, blur) and buys nothing.",
             "If that is true, H2 / Stage 2 only show the camera costs nothing — not that it is needed.",
             "The camera's only possible advantage: it sees errors FK cannot — the pen slipping, the "
             "paper moving, the pen running dry.",
             "So: knock the drawing off course mid-episode and measure who recovers better — an "
             "agent that sees the paper, or one that trusts its kinematics."],
            cards=[("THE THREE CLOSEST SAY", ["D01 itself lists a camera as future work for the "
                                              "synchronisation step — but never tests it."], VIOLET),
                   ("WHAT EACH OUTCOME MEANS", ["Camera recovers better → the camera is justified.",
                                               "No detectable difference → the camera buys nothing "
                                               "here — or the task cannot show recovery at all. "
                                               "Telling these apart needs a ceiling arm."],
                    WARN)],
            notes="""
H4 kyun sabse zaroori hai: D01 bina camera ke achha draw karta hai aur kehta hai camera-free
behtar hai. Woh forward kinematics se chalta hai — robot maan leta hai ki pen wahin hai jahan
bheja, aur ink gir gayi.

Agar yeh sahi hai to hamare H2 aur Stage 2 sirf yeh dikhate hain ki camera ka nuksaan nahi —
yeh nahi ki camera zaroori hai. Camera ka ek hi sambhavit fayda hai: woh galtiyan dekh sakta hai
jo kinematics nahi dekh sakti — pen fisalna, paper khisakna, ink khatam hona.

Isliye drawing ke beech me gadbad karo aur naapo ki kaun behtar sambhalta hai. Agar farak nahi
mila to imaandari se likhna padega ki D01 ki baat simulation me sahi saabit hui.
""")

    tabular(prs, "09 · design", "Three disturbances that kinematics cannot see",
            "rl/disturb.py. One per episode, fired at 4–16% of the episode (steps 9–37 of 240) — while the agent is still drawing.",
            ["disturbance", "what happens", "size", "what FK believes"],
            [["slip", "the pen is knocked sideways; the command stream is unchanged",
              "4–9 canvas px", "pen is where it was commanded"],
             ["paper shift", "the sheet slides under the pen; every later stroke lands displaced",
              "5–10 canvas px", "nothing moved"],
             ["ink failure", "the pen deposits nothing for a stretch of steps",
              "9–27 steps (4–12%)", "a perfect drawing — invisible to FK by construction"]],
            colw=[1.9, 5.0, 2.2, 3.1], size=11.5, row_h=0.55,
            below=["The timing window comes from a measurement: agents finish their shape in the first "
                   "~10–17% of the episode (the overrun finding).",
                   "A first version fired at 20–55% — sensible-looking and useless: every disturbance "
                   "landed on a finished drawing. A slip cost 0.001 IoU; an ink failure cost exactly nothing.",
                   "All learning arms TRAIN on 'mixed' (one of none / slip / shift / ink per episode) and "
                   "are scored on each kind separately, 10 episodes each — every arm gets a fair chance "
                   "to learn to use what it can see."],
            take="Training clean and testing disturbed would measure brittleness. The question is "
                 "about INFORMATION, so every arm trains with disturbances.", take_color=PRIMARY,
            notes="""
Teen disturbances: slip (pen ko dhakka, command same), paper shift (paper khisak jaata hai, aage
ki har line hat kar girti hai), ink failure (kuch steps tak pen se ink nahi nikalti — FK ke hisaab
se drawing perfect hai).

Kab: episode ke 4–16% par, yaani steps 9–37 — jab agent abhi draw kar raha hai. Pehle version me
20–55% par aata tha, aur bekaar tha: tab tak drawing khatam ho chuki hoti thi.

Saare learning arms "mixed" disturbances par train hote hain aur har disturbance par alag se
score hote hain. Sawaal information ka hai, isliye sabko seekhne ka fair mauka diya.
""")

    grid(prs, "09 · design", "Four arms: what each agent is allowed to see",
         "Same PPO, same reward rules, same shapes and seeds — only the observation's drawing channel differs.",
         [("OPEN-LOOP  (floor)", ["Not a learner: an analytic tracer that walks the outline, "
                                  "ignoring all feedback — a classical IK pipeline.",
                                  "Its loss under a disturbance = the cost of having no feedback."], SLATE),
          ("TRUE  (ceiling)", ["Sees the real ink. No physical robot has this; included only as "
                               "an upper reference."], GOOD),
          ("FK  (D01's condition)", ["Sees what its own kinematics say it drew: commanded positions, "
                                     "ink assumed to land, no knowledge of any disturbance."], WARN),
          ("CAMERA  (ours)", ["Sees a photograph of the paper as it actually is (fixed camera — "
                              "this is about feedback, not camera realism)."], ACCENT)],
         cols=2,
         take="Reward asymmetry, recorded in advance: true and fk are rewarded from the TRUE canvas, "
              "camera from vision — this biases the comparison AGAINST the camera.", take_color=WARN,
         notes="""
Chaar arms. Open-loop: seekhne wala agent nahi, ek fixed tracer jo bina feedback outline par
chalta hai — classical IK pipeline jaisa. True: asli ink dekhta hai — kisi asli robot ke paas
nahi, sirf upper reference. FK: D01 ki stithi — jo kinematics kehti hai wahi dekhta hai. Camera:
paper ki photo.

Ek asymmetry pehle se likh di thi: true aur fk ko reward asli canvas se milta hai, camera ko vision
se. Yeh comparison ko camera ke KHILAAF jhukata hai — camera jeete to conservative jeet; haare to
yeh dhyan me rakhna.
""")

    tabular(prs, "09 · premise check", "Premise check: is the FK belief actually wrong when things go wrong?",
            "rl/h4_premise.py — random actions, no training: the INFORMATION in each channel, measured at canvas resolution.",
            ["disturbance", "FK belief: error per pixel", "FK: as % of ink", "camera: error per pixel",
             "camera: as % of ink"],
            [["none", "0.00 ± 0.00", "0.0%", "2.50 ± 0.70", "14.6%"],
             ["slip", "0.44 ± 0.23", "2.5%", "2.56 ± 0.78", "15.1%"],
             ["paper shift", "13.55 ± 4.37", "82.0%", "2.58 ± 0.74", "15.4%"],
             ["ink failure", "0.74 ± 0.33", "5.0%", "2.50 ± 0.75", "15.2%"]],
            colw=[2.2, 2.7, 2.0, 2.7, 2.6], size=11.5, row_h=0.42,
            cell_colors={(2, 1): BAD, (2, 2): BAD},
            below=["Surprise: by pixel error the FK belief is CLOSER to the truth than the camera on three "
                   "of four kinds. Only paper shift breaks FK — completely (82% of the ink misplaced).",
                   "The camera's error is a constant, diffuse haze (~15%); FK's error is zero when nothing "
                   "is wrong and consists ENTIRELY of the missing or displaced stroke when something is.",
                   "Which costs more cannot be decided from pixel distances — that is why H4 trains agents. "
                   "Prediction written in advance: if the camera wins anywhere, it should win most on paper "
                   "shift and least on ink failure."],
            take="'The camera sees more' is false by this metric — the honest statement is subtler.",
            take_color=WARN,
            notes="""
Premise check: kya disturbance ke time FK ka andaaza sach me galat hota hai? Bina training ke,
random actions se naapa. Hairaani wali baat: teen me se teen cases me FK ka andaaza camera se
ZYADA sahi hai (pixel error me). Sirf paper shift FK ko poori tarah tod deta hai — 82% ink galat
jagah.

Camera ki galti ek lagataar dhundh hai (~15%), har baar same. FK ki galti tab zero hai jab sab
theek ho, aur jab gadbad ho to poori ki poori galti wahi missing stroke hai. Kaunsi zyada nuksaan
karti hai — yeh pixel se tay nahi hota, isliye agents train kiye. Pehle se likhi prediction: camera
kahin jeete to sabse zyada paper shift par.
""")

    steps(prs, "09 · analysis", "Difference-in-differences: measuring recovery, not starting level",
          "The comparison has to subtract how good each arm was BEFORE anything went wrong.",
          [("trap", "camera − fk  under a disturbance",
            ["The two arms do not start level: with NO disturbance the camera arm already scored "
             "higher. A gap under disturbance can just be that clean gap again."]),
           ("drop", "dropₐ(k) = IoUₐ(none) − IoUₐ(k)",
            ["How much arm a LOSES under disturbance k, from its own clean score (positive = worse)."]),
           ("DiD", "DiD(k) = drop_fk(k) − drop_camera(k)",
            ["Positive = the camera degrades less = it recovers better. Computed within each "
             "(shape, seed) pair, then averaged: n = 8 pairs."]),
           ("test", "t = mean(DiD) / ( sd(DiD) / √n ),   significant if |t| ≥ 2.365 (n = 8)",
            ["A one-sample paired t-test (Section 10)."]),
           ("caught", "interim, n = 4:  absolute gap t = 2.45  →  DiD t = 0.30",
            ["At 18/32 runs the script declared 'camera recovers better' (paper shift). Almost all "
             "of that gap was the +0.053 clean gap. The verdict logic was corrected BEFORE the "
             "remaining runs."])],
          notes="""
Difference-in-differences: dono arms barabar shuru nahi karte — bina disturbance ke bhi camera
arm aage tha. Isliye disturbance ke time ka seedha farak sirf woh shuruaati farak dobara naap
sakta hai.

Sahi tareeka: har arm apne clean score se kitna GIRA (drop). Phir fk ka drop minus camera ka drop
= DiD. Positive matlab camera kam gira = behtar sambhala. Har (shape, seed) jode me nikal ke
average, n = 8, aur t-test.

Yeh galti sach me pakdi gayi: 18/32 runs par script ne bola "camera behtar recover karta hai"
(t = 2.45). Par woh lagbhag poora shuruaati farak tha; DiD me t sirf 0.30. Baaki runs se PEHLE
logic sudhaara.
""")

    tabular(prs, "09 · pre-registration", "The rule was fixed before the last 14 runs — and what each outcome means",
            "From the 2026-10-19 log entry and docs/PAPER_PLAN.md §3. Decided before reading the result.",
            ["per disturbance (first match wins)", "verdict", "what it means for the paper"],
            [["open-loop loses < 0.03", "uninformative", "the disturbance barely bites; a null says nothing — re-size it (new sweep, your decision)"],
             ["t ≥ 2.365", "camera recovers better", "the camera buys recovery D01 cannot have"],
             ["t ≤ −2.365", "camera recovers worse", "report it; check the reward asymmetry first"],
             ["1.5 ≤ |t| < 2.365", "borderline", "the only permitted follow-up: seeds 200 and 300 for ALL arms"],
             ["otherwise", "no detectable difference", "honest negative: camera learning costs nothing (C1–C3) but buys no recovery in simulation; D01 supported"]],
            colw=[3.0, 2.6, 6.6], size=11, row_h=0.55,
            below=["Only the PRIMARY diff-in-diff decides. The absolute camera − fk gap is reported as "
                   "secondary and labelled as including the clean gap.",
                   "No optional stopping: no adding seeds until a number 'looks significant', no switching "
                   "the metric after seeing the data."],
            take="Never pick the framing after seeing which one reads best.", take_color=VIOLET,
            notes="""
Niyam aakhri 14 runs se pehle fix kar diya gaya tha. Har disturbance ke liye: agar open-loop bhi
0.03 se kam khota hai to disturbance kamzor hai — "uninformative". t ≥ 2.365 to camera behtar.
t ≤ −2.365 to camera badtar. 1.5 aur 2.365 ke beech to sirf ek follow-up allowed: sab arms ke liye
seeds 200 aur 300. Warna "no detectable difference".

Har nateeje ka paper par kya asar hoga, yeh bhi pehle se likha tha. Result dekhne ke baad framing
chunna mana hai.
""")

    # ---------------- the result (data-driven) ----------------
    final = st["final"]
    title = ("H4 result — 32/32 runs, 8 (shape, seed) cells" if final else
             f"H4 — interim: {st['runs']}/32 runs, {st['cells']} complete cells (no verdict yet)")
    rows = []
    cc = {}
    for i, r in enumerate(st["rows"]):
        d = r["drop"]
        rows.append([KIND_LABEL[r["kind"]], f"{d['camera']:+.3f}", f"{d['fk']:+.3f}",
                     f"{d['open_loop']:+.3f}", f"{r['did']:+.3f}", f"{r['up']}/{r['n']}",
                     f"{r['t']:+.2f}", r["verdict"]])
        cc[(i, 7)] = (GOOD if "better" in r["verdict"] else BAD if "worse" in r["verdict"]
                      else WARN if ("uninformative" in r["verdict"] or "borderline" in r["verdict"])
                      else INK)
    gm, gt = st["gap"] if st["gap"] else (float("nan"), float("nan"))
    means = st["means"]
    mline = ("Means, no disturbance: open-loop {:.3f} · true {:.3f} · fk {:.3f} · camera {:.3f}."
             .format(means["open_loop"]["none"], means["true"]["none"], means["fk"]["none"],
                     means["camera"]["none"])) if means else ""
    tabular(prs, "09 · result", title,
            "Read from results/ at build time, same functions as h4_verdict.py. Drop: + = got worse.",
            ["disturbance", "camera drop", "fk drop", "open-loop drop", "diff-in-diff", "pairs up",
             "t", "verdict (pre-registered rule)"],
            rows, colw=[1.6, 1.3, 1.1, 1.5, 1.4, 1.1, 0.9, 3.3], size=11, row_h=0.50,
            cell_colors=cc,
            below=[f"Clean gap (camera − fk, no disturbance): {gm:+.3f}, t = {gt:+.2f} — not recovery.",
                   "Ceiling control (added AFTER the null, not pre-registered): privileged true − fk = "
                   + " · ".join(f"{KIND_LABEL[r['kind']]} {r['ctl']:+.3f} (t {r['ctl_t']:+.2f})"
                                for r in st["rows"]) + ".",
                   mline,
                   f"Critical t for n = {st['cells']}: {st['crit']:.3f}." if st["crit"] else ""],
            take=("Open-loop collapses under slip and paper shift (it cannot react); the learning "
                  "arms lose far less — and the camera arm does not recover detectably better than fk."
                  if final else "Interim numbers: shown for transparency only. No verdict below 8 cells."),
            take_color=WARN,
            notes="""
H4 ka result — yeh table deck build karte waqt seedha results file se banti hai, wahi functions jo
aggregate script aur verdict script use karti hain. Isliye deck aur scripts kabhi alag number
nahi dikha sakte.

Kaise padhein: "drop" = apne clean score se kitna gira. Diff-in-diff positive = camera kam gira.
Verdict pre-registered niyam se mechanically aata hai.

Final (32/32) data me: slip aur paper shift par open-loop bahut girta hai (wo react nahi kar
sakta), learning arms thoda hi girte hain, aur camera arm fk se detectably behtar recover nahi
karta. Ink failure itna kamzor nikla ki open-loop bhi mushkil se girta hai — isliye woh
"uninformative" hai: wahan null result kuch nahi batata.

Research log me final H4 entry Gemini docs/H4_FINISH.md ke hisaab se likhega; yeh slide sirf
wahi numbers dikhati hai.
""")

    if final:
        bites = [r for r in st["rows"] if not r["verdict"].startswith("uninformative")]
        weak = [KIND_LABEL[r["kind"]] for r in st["rows"] if r["verdict"].startswith("uninformative")]
        better = [KIND_LABEL[r["kind"]] for r in bites if "better" in r["verdict"]]
        worse = [KIND_LABEL[r["kind"]] for r in bites if "worse" in r["verdict"]]
        border = [KIND_LABEL[r["kind"]] for r in bites if "borderline" in r["verdict"]]
        pts = []
        if bites and not better and not worse:
            pts.append("PRE-REGISTERED VERDICT: no detectable difference in recovery between camera and "
                       "fk on " + ", ".join(KIND_LABEL[r["kind"]] for r in bites) + " — a null on the "
                       "primary endpoint (effects below ~0.04 IoU could not be seen at n = 8).")
            pts.append("CEILING CONTROL (added after the null, labelled as such): the privileged true "
                       "arm, which sees the real ink perfectly, ALSO recovers no better than fk. So the "
                       "null is not about camera quality — in this task the 'drawn so far' channel "
                       "carries no recoverable signal for any arm.")
            pts.append("Therefore H4 as designed could not answer D01 either way. D01's objection "
                       "STILL STANDS UNANSWERED — nothing here shows a camera is unnecessary.")
        if better:
            pts.append("Camera recovers better on: " + ", ".join(better) + ".")
        if worse:
            pts.append("Camera recovers worse on: " + ", ".join(worse) +
                       " — read with the reward asymmetry, which favours fk.")
        if border:
            pts.append("Borderline on: " + ", ".join(border) +
                       " — the only permitted follow-up is seeds 200 and 300 for all arms.")
        if weak:
            pts.append(", ".join(weak).capitalize() + " is uninformative by the rule fixed in "
                       "advance: open-loop loses only 0.013; the outage removes ~5% of the ink.")
        pts.append("Leading explanation — a HYPOTHESIS: robustness by over-drawing. Agents keep "
                   "moving over the shape for ~74% of the episode (H6), so they blindly re-cover "
                   "damage; open-loop traces once and collapses. Not checkable from saved rows.")
        concept(prs, "09 · meaning", "What the H4 result does — and does not — say",
                "Pre-registered verdict first; the control added afterwards is labelled as such.",
                pts,
                cards=[("HONEST LIMITS", ["n = 8 pairs (2 seeds × 4 shapes): |t| < 2.36 "
                                          "is not significant.",
                                          "Reward asymmetry favours fk.",
                                          "Disturbance sizes are not calibrated to a real arm.",
                                          "Mixed thread settings across rows (within-cell pairs "
                                          "unaffected).",
                                          "Simulation, fixed camera."], WARN),
                       ("WHAT FOLLOWS (YOUR DECISION)", ["Re-run H4 with no free repair window "
                                                         "(short episodes or plateau stop) — the only "
                                                         "option that could still answer D01.",
                                                         "Or H5, or held-out shapes (§5.4)."], PRIMARY)],
                left_w=6.6, size=12.5,
                notes="""
H4 ka matlab (research log ki "H4 RESULT" entry ke mutabik). Pre-registered verdict: camera aur fk
ke recovery me koi detectable farak nahi — teeno disturbances par null.

Phir ek control joda gaya (null dekhne ke BAAD — yeh saaf likha hai, pre-registered nahi): "true"
arm jo asli ink bilkul perfect dekhta hai, woh bhi fk se behtar recover nahi karta. Matlab null
camera ki quality ki wajah se nahi — is task me "ab tak kya bana" wali jaankari se kisi bhi arm ko
recovery me madad nahi milti. Isliye yeh design D01 ka sawaal kisi bhi taraf decide nahi kar sakta
tha. D01 ka objection abhi bhi khula hai.

Sambhavit wajah (sirf hypothesis): agents shape banane ke baad 74% episode tak usi par ghoomte
rehte hain, to nuksaan ko bina dekhe hi dobara cover kar dete hain. Agla kadam aapka decision:
chhote episodes ke saath H4 dobara, ya H5, ya naye shapes.

Limits: sirf 8 jode, reward asymmetry fk ke paksh me, disturbance ka size kisi asli arm se
calibrate nahi, simulation aur fixed camera.
""")


# ============================================================ STATISTICS ====
def stats(prs):
    section(prs, 10, "Statistics & research honesty",
            "The handful of statistical ideas every result in this deck rests on — and the "
            "mistakes this project actually made, each turned into a rule.",
            ["Why seeds; mean and sd", "The paired t-test", "'No detectable difference'",
             "Paired vs pooled", "Pre-registration", "Mistakes → rules"])

    steps(prs, "10 · basics", "Why many seeds — and how to summarise them",
          "An RL result from one run is an anecdote.",
          [("seed", "seed = the starting number of the random generator",
            ["Network initialisation, exploration noise and environment randomness all follow "
             "from it. Different seed → a genuinely different training run."]),
           ("spread", "H2 (2nd sweep), circle, camera − truth:  seed 0 → −0.127,  seed 2 → +0.159",
            ["The same comparison flips sign between seeds. One run cannot tell an effect from luck."]),
           ("mean", "x̄ = (1/n) Σ xᵢ",
            ["The typical value across runs."]),
           ("sd", "s = √( Σ (xᵢ − x̄)² / (n − 1) )",
            ["Sample standard deviation (ddof = 1). Dividing by n instead (ddof = 0) under-states "
             "spread; at n = 3 it even flipped an 'error bars overlap' conclusion — so the project "
             "standardised on n − 1."])],
          notes="""
Seed = random generator ka shuruaati number. Usse network ki shuruaat, exploration ka noise,
environment ki randomness sab tay hote hain. Alag seed = sach me alag training run.

RL me seeds ke beech bahut farak hota hai: H2 me circle par ek seed par camera −0.127 peeche, doosre
par +0.159 aage. Ek run se effect aur kismat me farak nahi kar sakte.

Mean aur standard deviation: sd me (n − 1) se bhaag dete hain (sample sd). n se bhaag dene par
spread kam dikhta hai — n = 3 par isne ek "error bars overlap" wala conclusion hi palat diya tha.
""")

    steps(prs, "10 · paired t-test", "The paired t-test, step by step",
          "Used for every comparison in this project, because the arms share seeds.",
          [("pair", "dᵢ = (arm B − arm A) for the SAME shape and seed,   i = 1 … n",
            ["Pairing removes everything the two runs share — shape difficulty, seed luck."]),
           ("t", "t = d̄ / ( s_d / √n )",
            ["Mean difference divided by its standard error. Large |t| = the difference is big "
             "compared with its own noise."]),
           ("example", "H2: d̄ = −0.0280, s_d = 0.0680, n = 12  →  t = −0.0280 / 0.0196 = −1.43",
            ["Reproduces the logged value exactly."]),
           ("decide", "significant at 5% if |t| ≥ t_crit(n − 1):   n=4 → 3.18 · n=8 → 2.365 · n=12 → 2.20",
            ["Small n needs a bigger t. With 8 pairs, |t| < ~2.4 is not significant."]),
           ("report", "always: n · mean ± sd · paired difference · pairs up (k/n) · t",
            ["'Pairs up' (e.g. 9/12) shows whether an average is driven by one outlier."])],
          notes="""
Paired t-test: same shape aur same seed wale do runs ka farak lo (d). Isse dono me jo common hai —
shape ki kathinai, seed ki kismat — hat jaata hai. t = farak ka average / uska standard error.
Bada |t| matlab farak apne noise se bada hai.

Example: H2 me average farak −0.028, sd 0.068, 12 jode → t = −1.43. Log me bhi yahi hai.
Significant hone ke liye |t| ek critical value se bada chahiye: 8 jodon par 2.365. Har table me
n, mean, sd, farak, kitne jode upar, aur t — sab likhte hain.
""")

    concept(prs, "10 · language", "'No detectable difference' is not 'no difference'",
            "The single most important phrase discipline in this project.",
            ["A non-significant test means the data cannot distinguish the arms at this sample size. "
             "It does NOT show they are the same.",
             "With n = 8–12 pairs the test can only detect fairly large effects; a small real "
             "difference could hide inside the noise.",
             "Showing two things are the SAME needs an equivalence test (TOST): pick a margin "
             "(e.g. ±0.05 IoU) and show the difference is confidently inside it. Not yet done "
             "for H2 — listed as missing before submission.",
             "So the paper says 'no detectable difference', never 'no difference', 'the same', "
             "'equivalent' or 'outperforms' — and docs/paper/check_paper.py fails a draft that does."],
            cards=[("ALLOWED", ["no detectable difference", "suggestive, not conclusive",
                                "no exploitable drift", "approximately", "in simulation"], GOOD),
                   ("BANNED", ["no difference · the same · equivalent", "novel · first to",
                               "outperforms · recovers better (without the test)"], BAD)],
            notes="""
Sabse zaroori bhasha ka niyam: "farak nahi pakda gaya" ka matlab "farak nahi hai" nahi hai. 8–12
jodon ke saath test sirf bade farak pakad sakta hai; chhota asli farak noise me chhup sakta hai.

"Same" saabit karne ke liye equivalence test (TOST) chahiye — ek margin chuno (jaise ±0.05 IoU) aur
dikhao ki farak us margin ke andar hai. H2 ke liye abhi nahi hua — submission se pehle zaroori list
me hai. Isliye paper me "no detectable difference" likhte hain; ek script "equivalent",
"outperforms" jaise shabd pakad leti hai.
""")

    tabular(prs, "10 · mistakes → rules", "Mistakes this project actually made — each became a rule",
            "Recorded in the research log and AGENTS.md §6. Every one looked correct on the page.",
            ["mistake", "what happened", "rule now"],
            [["pooled denominator", "O1 first reported 'no effect' using the std of all runs pooled (shape spread + seed noise); paired t = 2.17",
              "arms share seeds → always pair within (shape, seed)"],
             ["absolute vs recovery", "H4 interim said 'camera recovers better' (t 2.45); it was the clean gap (DiD t 0.30)",
              "when arms start at different levels, compare how much each LOSES"],
             ["wrong reference column", "the DR aggregate printed a drop of +0.006 against the wrong camera; true +0.014",
              "a printed number is not verified — recompute it from the table above it"],
             ["drop vs change", "a write-up read a 'drop' of −0.003 as a loss — it is a GAIN",
              "say the direction in words: 'fell from 0.393 to 0.379'"],
             ["reward bug", "a stop button collected the success bonus on a blank canvas",
              "gate bonuses on success, not on episode end"],
             ["n = 1 hypothesis", "'camera loses 2× to overshoot' — did not replicate at n = 12",
              "label untested ideas 'hypothesis, not result' until tested"],
             ["thread count", "the same seed gave 0.175 vs 0.195 IoU with 2 vs 1 threads",
              "fix OMP_NUM_THREADS; record it with the seed"]],
            colw=[2.2, 6.0, 4.0], size=10, row_h=0.50,
            take="A negative result is a result. Report the number you got, not the one you hoped for.",
            take_color=GOOD,
            notes="""
Is project me sach me hui galtiyan, aur har ek se bana niyam. Pooled std se compare karna (O1 me
"koi asar nahi" aaya, jabki paired test me asar tha). Absolute farak ko recovery samajhna (H4
interim). Script ka galat column se compare karna (+0.006 asal me +0.014). "Drop" ko "change"
padhna (−0.003 drop asal me fayda hai). Stop button ka bonus bug. n = 1 se bani dhaarna jo n = 12
par nahi tiki. Aur thread count se result badalna.

Saar: negative result bhi result hai. Jo number mila wahi likho, jo chahiye tha woh nahi.
""")


# ================================================================ STATUS =====
def status(prs, st):
    section(prs, 11, "Status, roadmap & sim-to-real",
            "Which claims are ready for a paper, what a reviewer would still ask for, the staged "
            "plan, and how the work moves from simulation to a ₹10,000 arm.",
            ["Claims map C1–C7", "What is missing", "Roadmap stages 1–7", "Sim-to-real plan",
             "Risks"])

    c4 = ("NOT SUPPORTED by this design — null; ceiling control shows it could not discriminate" if st["final"]
          else f"PENDING — {st['runs']}/32 runs")
    tabular(prs, "11 · claims", "The claims map — what the paper can say today",
            "From docs/PAPER_PLAN.md §2. Wording in this column or weaker; never stronger.",
            ["#", "claim", "evidence", "status"],
            [["C1", "camera reward = privileged reward in true accuracy: no detectable difference",
              "two H2 sweeps, opposite signs, |t| < 1.5", "READY"],
             ["C2", "the camera reward is not exploited", "H3: gap −0.0001 over 3,328 episodes", "READY"],
             ["C3", "survives a much worse camera; randomisation buys nothing", "Stage 2: held-out drop 0.014", "READY"],
             ["C4", "seeing the paper recovers from disturbances FK cannot see", "H4", c4],
             ["C5", "agents finish early and overshoot; plateau stop +0.055", "overshoot ablation, 2 seeds",
              "READY (effect) / AT RISK (as a fix)"],
             ["C6", "remaining time in the observation: modest gain", "O1: +0.039, 9/12", "READY (minor)"],
             ["C7", "seeded RL here is not thread-invariant", "0.175 vs 0.195", "READY (reproducibility)"]],
            colw=[0.7, 5.6, 3.4, 2.5], size=10.5, row_h=0.50,
            cell_colors={(0, 3): GOOD, (1, 3): GOOD, (2, 3): GOOD, (3, 3): WARN, (4, 3): WARN,
                         (5, 3): GOOD, (6, 3): GOOD},
            take="It is a measurement paper: careful numbers on a question the closest papers name "
                 "as open — not a new algorithm.", take_color=VIOLET,
            notes="""
Paper kya keh sakta hai: C1 (camera reward aur perfect reward me detectable farak nahi), C2 (camera
reward exploit nahi hota), C3 (bahut kharab camera par bhi tikta hai) — teeno ready. C4 (H4) is design se
support nahi hua — null, aur ceiling control ke mutabik design farak dikha hi nahi sakta tha. C5 (overshoot) effect ready,
"fix" ke roop me abhi risk me. C6 aur C7 chhote claims.

Yeh measurement paper hai — naya algorithm nahi, ek khule sawaal par saavdhaan numbers.
""")

    grid(prs, "11 · gaps", "What a reviewer would still ask for",
         "PAPER_PLAN §4, ordered by how much a reviewer would care.",
         [("1 · AN H4 THAT CAN ANSWER D01", ["H4 is complete but could not discriminate (ceiling "
                                             "control). A re-run with no free repair window is the "
                                             "main open decision — yours to make."], WARN),
          ("2 · EQUIVALENCE TEST FOR C1", ["TOST with a stated margin (e.g. ±0.05 IoU), pooled across "
                                           "both H2 sweeps. Analysis only — no new training."], VIOLET),
          ("3 · GENERALISATION", ["Parameterised shapes with a held-out range (proposal §5.4). "
                                  "Otherwise: 'it memorised four shapes'."], PRIMARY),
          ("4 · BASELINES", ["Open-loop / IK tracer numbers already exist inside H4 — report them. "
                             "PPO vs SAC is nice to have."], SLATE),
          ("5 · REAL CAMERA / ROBOT", ["Not required for a simulation measurement paper at ICRA/IROS, "
                                       "but expect the question. The thesis needs at least a plan."], ACCENT),
          ("6 · REWARD-SHAPING NOTE", ["State the shaping guarantee as approximate (γ mismatch, "
                                       "Section 7) — a one-line fix in the text."], WARN)],
         cols=3,
         notes="""
Reviewer abhi kya maangega: (1) aisa H4 jo sach me D01 ka jawab de sake — maujooda design
discriminate nahi kar paya; chhote episodes ke saath dobara chalana aapka decision. (2) H2 ke liye equivalence test — sirf analysis,
nayi training nahi. (3) Generalisation — naye shape parameters par test, warna "chaar shapes ratt
liye". (4) Baselines — open-loop numbers H4 me already hain. (5) Asli camera ya robot — simulation
paper ke liye zaroori nahi, par sawaal aayega. (6) Reward shaping wali chhoti baat text me sahi likhna.
""")

    tabular(prs, "11 · roadmap", "The staged plan and where we are",
            "docs/PROJECT_PROPOSAL_v2.md §8. Stages 1–3 are the paper; 4–6 strengthen it; 7 is hardware.",
            ["stage", "content", "status"],
            [["1", "multi-seed H2 · H3 exploitation · O1 · missing metrics", "DONE"],
             ["1b", "overrun / overshoot (H6) · H2 peak-vs-final", "DONE (plateau 4th arm still open)"],
             ["2", "perception domain randomisation · parameterised shapes (§5.4)", "DR DONE · §5.4 not started"],
             ["3", "H4 disturbance recovery · H5 open-loop error growth",
              "H4 DONE (32/32) · H5 not started" if st["final"] else "H4 running · H5 not started"],
             ["4", "egocentric observation, CoordConv, action chunking, BC warm start — as ablations", "not started"],
             ["5", "PPO vs SAC (RQ3) · ergodic-control baseline · curriculum (RQ4)", "not started"],
             ["6", "pen up/down (A2) → digits and letters, recognisability metric", "not started"],
             ["7", "hardware (Phase D), in the sim-to-real priority order", "not started (by design)"]],
            colw=[0.9, 7.6, 3.7], size=11, row_h=0.47,
            cell_colors={(0, 2): GOOD, (1, 2): GOOD, (3, 2): GOOD if st["final"] else WARN},
            take="Next step is a decision, not a default: H4 without a free repair window, H5, or "
                 "§5.4 shapes — the plan says ask, do not pick.", take_color=PRIMARY,
            notes="""
Plan ke saat stages. Stage 1 aur 1b poore. Stage 2 me DR poora, naye-shape wala hissa baaki.
Stage 3 me H4 poora, H5 baaki. Stage 4–6 baad me, aur Stage 7 hardware — jaan-boojh kar sabse ant
me. Agla kadam aapka decision hai: ink failure ko bada karke H4 v2, ya H5, ya naye shapes, ya paper
likhna shuru karna.
""")

    tabular(prs, "11 · sim-to-real", "From simulation to a ₹10,000 arm: the plan (Phase D)",
            "Proposal §6 — re-prioritised by the literature review.",
            ["#", "step", "why", "evidence"],
            [["1", "fit the ink model from real strokes (pen height → stroke width)",
              "the hard-coded 3.5 mm stroke width is probably the largest reality gap", "D09 did it on a Dobot Magician; A01"],
             ["2", "fit the camera model to the real webcam", "cam_px and threshold are guesses", "A01's real2sim2real"],
             ["3", "report Δ = MSE(sim canvas, photo of the real canvas)", "gives hardware results a number", "A01 reference points"],
             ["4", "randomise dynamics, especially control latency", "KUKA motors vs hobby servos is a huge gap", "V02 (Peng et al.)"],
             ["5", "swap the KUKA model for the real arm's", "transfer cannot be claimed otherwise", "—"],
             ["6", "plan resets: who replaces the paper? the pen runs dry?", "automatic reset is a top real-robot RL blocker", "R03"],
             ["7", "camera placement and lighting (diffuse, no glare)", "overhead suits a whole-canvas reward", "A01 vs D08"]],
            colw=[0.6, 4.6, 4.2, 2.8], size=10.5, row_h=0.50,
            take="Because the agent acts in PEN space, only the arm model + IK change — the learned "
                 "policy's meaning does not.", take_color=GOOD,
            notes="""
Simulation se asli arm tak ka plan. Sabse pehle asli ink ka model — pen ki unchai se line ki motai
— kyunki 3.5 mm ki fixed motai shayad sabse bada reality gap hai (D09 ne Dobot par yahi kiya). Phir
asli webcam ke hisaab se camera model. Phir sim aur asli canvas ka farak naapna. Servo ka latency
randomise karna. KUKA ki jagah asli arm ka model. Paper badalna aur pen sookhna kaise sambhalenge.
Aur camera ki jagah aur roshni (seedhi roshni chamak deti hai).

Kyunki agent pen space me sochta hai, sirf arm model aur IK badlega.
""")

    tabular(prs, "11 · risks", "Risk register",
            "Proposal §9, updated with what has since been measured.",
            ["risk", "status now", "mitigation"],
            [["reviewer: 'D01 already solves this without a camera'",
              "STILL OPEN — H4 null, and its ceiling control shows the design could not discriminate",
              "say it plainly; re-design H4 (no free repair window)"],
             ["H2 does not survive a realistic camera", "RETIRED — Stage 2: held-out drop 0.014",
              "—"],
             ["the camera reward is exploited", "RETIRED for the fixed camera (H3)",
              "re-check under randomised cameras if needed"],
             ["IoU 0.36–0.51 looks weak next to D03's 0.999", "open",
              "different problem (supervised, stroke-ordered data, 1-px targets) — pre-empt in the paper"],
             ["H2 gap is an overshoot artifact", "RETIRED — peak vs final gap change −0.011", "—"],
             ["scope creep", "open", "stages 1–3 are the paper; ship on those"]],
            colw=[3.8, 4.6, 3.8], size=10.5, row_h=0.55,
            cell_colors={(1, 1): GOOD, (2, 1): GOOD, (4, 1): GOOD, (0, 1): WARN},
            notes="""
Risks. Sabse bada — "D01 bina camera ke yeh kar chuka hai" — abhi bhi khula hai: H4 null aaya, aur
ceiling control ne dikhaya ki yeh design farak dikha hi nahi sakta tha. Ise saaf likhna hai aur
H4 ka naya design (bina free repair window) tay karna hai. Teen risks khatam ho chuke: kharab camera par H2,
reward exploit, aur overshoot artifact. IoU 0.4 vs D03 ka 0.999 — alag problem hai, paper me pehle
se samjhana hoga. Aur scope creep — paper stages 1–3 par chhapna.
""")


# =================================================================== Q&A =====
def questions(prs):
    section(prs, 12, "Questions & glossary",
            "The questions a guide, examiner or reviewer is most likely to ask, with honest "
            "answers — and every term in this deck defined in one line.",
            ["Why RL?", "Why not FRIDA?", "Is IoU 0.4 weak?", "Isn't it only simulation?",
             "Glossary"])

    s = slide(prs, "Anticipated questions (1/2)", "12 · q&a")
    qs = [("Why RL, when supervised learning (D03) reaches 0.999 IoU?",
           ["D03 needs stroke-ordered demonstration data and runs OPEN LOOP on the robot — its own "
            "results show 'significant error … due to position errors in the robot's end effector'.",
            "Our question is learning without demonstrations, from what the camera sees. Different "
            "problems: D03 also uses 1-px skeletonised targets."], "positioning", VIOLET),
          ("Why RL, when differentiable planning (FRIDA) works better?",
           ["Gradients need an accurate, differentiable model of the world. FRIDA's own numbers show "
            "the gap when the stroke model is wrong (Δ 0.156 vs 0.029).",
            "A policy acting on OBSERVED state does not need the model to be right."], "positioning", VIOLET),
          ("Your IoU is only ~0.4. Isn't that weak?",
           ["Drawing accuracy is the controlled variable, not the contribution: both arms of every "
            "comparison face the same task.",
            "IoU penalises every pixel of offset on a stroke only a few pixels wide; and part of the "
            "gap is the measured overshoot (0.064), which a plateau stop largely recovers."], "results", WARN),
          ("Doesn't D01 already show a camera is unnecessary?",
           ["No — and our H4 does not settle it either way. Camera vs fk: null. But a ceiling arm "
            "with PERFECT sight also recovered no better, so the task could not show recovery at all. "
            "We say so plainly; a re-designed H4 is the next step."], "H4", BAD)]
    w = (CW - 0.2) / 2
    for i, (q, a, tag, c) in enumerate(qs):
        r, k = divmod(i, 2)
        qa(s, q, a, M + k * (w + 0.2), 1.50 + r * 2.72, w, 2.55, tag=tag, accent=c)
    note(s, """
Sabse sambhavit sawaal aur imaandar jawab.
1) D03 0.999 IoU deta hai, to RL kyun? D03 ko demonstration data chahiye aur woh robot par open
   loop chalta hai — apne hi paper me end-effector ki galti maanta hai. Hamara sawaal bina
   demonstration ke, camera se seekhna hai.
2) FRIDA behtar hai to? Gradient ke liye world ka sahi model chahiye; model galat ho to FRIDA ka bhi
   farak dikhta hai. Policy jo dekhti hai us par chalti hai.
3) IoU 0.4 kamzor? Accuracy controlled variable hai, contribution nahi — har comparison me dono arm
   same task karte hain. Aur ek hissa overshoot ka hai.
4) D01? Hamara H4 ise kisi taraf decide nahi karta: camera vs fk null, aur perfect dekhne wala arm
   bhi behtar nahi — task recovery dikha hi nahi sakta. Naya design agla kadam hai.
""")

    s = slide(prs, "Anticipated questions (2/2)", "12 · q&a")
    qs = [("Isn't this all just simulation?",
           ["Yes — deliberately. RL's sample cost makes real-robot training impractical first (R03). "
            "The camera model was validated against a real render (gap 0.010) and stress-tested with "
            "a far worse camera (Stage 2). Hardware is Stage 7, with a concrete sim-to-real plan."],
           "scope", ACCENT),
          ("Are 2–3 seeds enough?",
           ["For direction, with paired tests — yes, and every table states n and t. For small "
            "effects, no: that is why we say 'no detectable difference', and why an equivalence test "
            "is on the list."], "statistics", PRIMARY),
          ("Why PPO and not SAC?",
           ["The study holds the algorithm fixed to isolate the learning signal. The simulator is "
            "cheap, PPO is stable with defaults, and image replay buffers are heavy on this machine. "
            "PPO vs SAC (RQ3) is planned, not run."], "method", VIOLET),
          ("What is actually new here?",
           ["Not RL drawing, not vision rewards, not visual feedback. The contribution is a "
            "MEASUREMENT the three closest papers name as open: what is lost — and gained — when a "
            "drawing agent learns from its camera instead of a privileged canvas."], "novelty", GOOD)]
    w = (CW - 0.2) / 2
    for i, (q, a, tag, c) in enumerate(qs):
        r, k = divmod(i, 2)
        qa(s, q, a, M + k * (w + 0.2), 1.50 + r * 2.72, w, 2.55, tag=tag, accent=c)
    note(s, """
5) Sirf simulation? Haan, jaan-boojh kar — RL ki sample cost ki wajah se. Camera model asli render se
   validate hua aur ek bahut kharab camera par bhi test hua. Hardware Stage 7 hai.
6) 2–3 seeds kaafi? Direction ke liye paired test ke saath haan; chhote effects ke liye nahi — isliye
   "no detectable difference" likhte hain.
7) PPO kyun, SAC kyun nahi? Algorithm fix rakha taaki sirf learning signal badle. SAC plan me hai.
8) Naya kya hai? Ek measurement — jo teen sabse kareebi papers ne khud khula sawaal bataya.
""")

    gl1 = [("Agent / policy π", "the learner / its rule from observation to action"),
           ("Observation / state", "what the agent sees (here a 64×64 image)"),
           ("Action", "the agent's choice: [dx, dy, pen_down]"),
           ("Reward", "one number per step saying how good it was"),
           ("Episode", "one attempt, 240 steps"),
           ("Return Gₜ", "discounted sum of future rewards"),
           ("γ (gamma)", "discount factor, 0.99 → ~100-step horizon"),
           ("Value V(s), Q(s,a)", "expected return from a state / state-action"),
           ("Advantage A", "how much better an action is than average"),
           ("TD error δ", "reward + γV(next) − V(now): the 'surprise'"),
           ("GAE (λ)", "weighted blend of n-step advantage estimates"),
           ("On- / off-policy", "learns only from fresh data / also from a replay buffer"),
           ("PPO", "on-policy actor-critic with a clipped ratio (ε = 0.2)"),
           ("SAC", "off-policy actor-critic maximising reward + entropy"),
           ("Entropy", "how random the policy is; rewarded to keep exploring")]
    gl2 = [("Forward / inverse kinematics", "angles → pen position / pen position → angles"),
           ("DOF", "degrees of freedom: number of independent joints"),
           ("URDF", "file describing a robot's links and joints"),
           ("IoU", "|drawn ∩ target| / |drawn ∪ target|; 1 = perfect"),
           ("Privileged canvas", "the exact digital drawing no real robot has"),
           ("Proxy camera", "fast validated model of the camera (_perceive)"),
           ("Domain randomisation", "train on many sampled cameras to generalise"),
           ("FK belief", "what kinematics says was drawn (D01's view)"),
           ("Overshoot / overrun", "IoU lost after finishing / idle steps afterwards"),
           ("Plateau stop", "end the episode after k steps without improvement"),
           ("Seed", "start of the random generator; one seed = one run"),
           ("Paired t-test", "test on per-pair differences; |t| ≥ crit → significant"),
           ("Diff-in-diff", "difference of each arm's own drop from its clean score"),
           ("Pre-registration", "fixing the analysis rule before seeing the data"),
           ("TOST", "equivalence test: is a difference inside ±margin?")]
    for gi, (gl, ttl) in enumerate([(gl1, "Glossary (1/2) — reinforcement learning"),
                                    (gl2, "Glossary (2/2) — robotics, vision, statistics")]):
        s = slide(prs, ttl, "12 · glossary")
        for i, (t, d) in enumerate(gl):
            r, k = divmod(i, 2) if False else (i % 8, i // 8)
            x = M + k * 6.15
            y = 1.48 + r * 0.66
            txt(s, x, y, 2.55, 0.6, t, size=12, color=PRIMARY if gi == 0 else ACCENT, bold=True)
            txt(s, x + 2.6, y, 3.4, 0.6, d, size=11.5, color=BODY, spacing=1.1)
        note(s, "Glossary — har term ek line me. Koi shabd bhool jao to yahan dekh lo." if gi == 0 else
             "Glossary ka doosra hissa — robotics, vision aur statistics ke shabd.")


def closing(prs, st):
    from deck_kit import _blank, _state
    s = _blank(prs)
    _state["n"] += 1
    rect(s, 0, 0, W, H, fill=NAVY)
    rect(s, 0, 0, 0.16, H, fill=PRIMARY)
    txt(s, 1.1, 1.0, 11, 0.6, "In one slide", size=30, color=WHITE, bold=True)
    rect(s, 1.13, 1.75, 1.6, 0.035, fill=ACCENT)
    pts = [("Built", "a validated simulator (0.1 mm IK, real ink, a calibrated camera) and a drawing "
                     "environment where an arm learns by trial and error."),
           ("Shown", "learning from the camera matches learning from the privileged canvas (no "
                     "detectable difference), is not exploited, and survives a much worse camera."),
           ("Found", "agents finish early and overshoot; an environment-side stop recovers +0.055 IoU "
                     "(mechanism still open)."),
           ("H4", ("null on all three disturbances — and even perfect sight (the ceiling arm) buys no "
                   "recovery, so this design could not answer D01; it stays open." if st["final"] else
                   f"running ({st['runs']}/32) — the result decides the paper's framing.")),
           ("Next", "your decision: H4 with no free repair window, H5, or held-out shapes (§5.4).")]
    for i, (k, t) in enumerate(pts):
        y = 2.15 + i * 0.92
        txt(s, 1.1, y, 1.6, 0.4, k.upper(), size=13, color=ACCENT, bold=True)
        txt(s, 2.8, y - 0.02, 9.6, 0.85, t, size=15, color=RGBColor(0xC9, 0xD4, 0xE8), spacing=1.2)
    txt(s, W - M - 1.2, H - 0.42, 1.2, 0.25, str(_state["n"]), size=9,
        color=RGBColor(0x55, 0x63, 0x82), align=PP_ALIGN.RIGHT)
    note(s, """
Ek slide me poora project: (1) ek validated simulator aur drawing environment banaya jisme arm
khud seekhta hai. (2) Dikhaya ki camera se seekhna perfect canvas se seekhne jaisa hai (koi
detectable farak nahi), camera ko bewakoof nahi banaya jaata, aur bahut kharab camera par bhi
chalta hai. (3) Khoja ki agents jaldi khatam karke overshoot karte hain. (4) H4: teeno par null, aur
perfect dekhne wala arm bhi behtar nahi — yeh design D01 ka jawab nahi de sakta tha. (5) Agla
kadam aapka decision.
""")


def build(prs):
    st = h4data.summary()
    h4(prs, st)
    stats(prs)
    status(prs, st)
    questions(prs)
    closing(prs, st)
