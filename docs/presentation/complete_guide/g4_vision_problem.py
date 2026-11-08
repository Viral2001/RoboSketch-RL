"""Part 4 - computer vision foundations, the research problem, literature and hypotheses."""
from gk import (ACCENT, BAD, BODY, CW, GOOD, INK, LINE, M, MUTED, PRIMARY, SLATE, VIOLET,
                WARN, WASH, WHITE, arrow, bullets, card, chip, concept, figure, grid, node,
                note, pic, rect, section, slide, steps, strip, tabular, txt, analogy, img)
from pptx.enum.shapes import MSO_SHAPE


def vision(prs):
    section(prs, 5, "Computer vision",
            "How a robot 'sees' its drawing: images as numbers, a virtual camera, turning a "
            "photo into ink, and the metrics that say how close a drawing is to its target.",
            ["Images as arrays", "The virtual camera", "Thresholding",
             "IoU and the other metrics", "Fast camera model vs real render",
             "Domain randomisation"])

    concept(prs, "05 · images", "An image is just a grid of numbers",
            "Everything the camera, the reward and the policy handle is an array.",
            ["Pixel = one cell of the grid. Grayscale pixel = one number, 0 (black) to 255 (white). "
             "Colour pixel = three numbers (red, green, blue).",
             "Binary image / mask = every pixel is 0 or 1: 'ink here' or 'no ink here'. "
             "Targets and drawings are compared as masks.",
             "Resolution = grid size. The simulator's validation drawings use 512 × 512; the RL "
             "canvas (the 20 cm sheet) is 128 × 128; the policy sees a 64 × 64 version.",
             "A stroke 14 px wide at 512 is only ~3.5 px at 128 — thin strokes are fragile under "
             "down-sampling. This matters later (the camera loses thin lines first).",
             "The canvas (a numpy array) is the authoritative drawing — what is saved and scored. "
             "The textured paper in the 3D view is only a visualisation of it."],
            cards=[("THE THREE OBSERVATION CHANNELS", ["0 · the target shape", "1 · the ink drawn so far",
                                                      "2 · a marker at the pen position",
                                                      "(3 · elapsed time, only with O1)"], ACCENT),
                   ("WHY IMAGES AND NOT COORDINATES", ["The same observation format works for any "
                                                       "target — a line, a letter, a doodle — and "
                                                       "it is exactly what a real camera gives."], PRIMARY)],
            analog="A mosaic: step back and you see a picture; step close and it is just "
                   "numbered tiles. Computers only ever see the tiles.",
            notes="""
Computer ke liye image sirf numbers ka grid hai. Har pixel ek number — 0 kaala, 255 safed.
Binary mask me har pixel 0 ya 1: ink hai ya nahi. Target aur drawing masks ki tarah compare
hote hain.

Resolution: simulator validation 512x512 par, RL canvas 128x128 (20 cm ka paper), aur policy
64x64 dekhti hai. Ek patli line 512 par 14 pixel moti hai, 128 par sirf ~3.5 pixel — isliye
camera sabse pehle patli lines kho deta hai.

Asli drawing numpy canvas hai — wahi save aur score hoti hai. 3D view ka paper sirf dikhane ke
liye hai.
""")

    concept(prs, "05 · camera", "The virtual camera (simulator milestone B6)",
            "PyBullet renders the scene from a camera pose, like a photograph.",
            ["Pinhole model: a 3D point (X, Y, Z) lands on pixel u = f·X/Z + cₓ, v = f·Y/Z + c_y "
             "(f = focal length). PyBullet builds this from a view matrix (where the camera is) "
             "and a projection matrix (its field of view).",
             "We render a 480 × 480 RGB frame looking down at the paper, plus a segmentation "
             "mask that labels which pixels belong to the paper.",
             "Orientation was CALIBRATED, not assumed: an asymmetric marker was photographed and "
             "all 8 flips/rotations tested — the identity won at IoU 0.998 (next best 0.68).",
             "Problem 1: the arm hid the paper. Fix: park the arm upright before each photo — "
             "100% paper visible, 0 arm pixels.",
             "Problem 2: PyBullet's loadTexture caches by FILENAME, so the paper photo froze at an "
             "early frame. Fix: a unique filename for every refresh."],
            cards=[("WHY THIS MATTERS", ["Each bug would have produced a plausible-looking but "
                                         "wrong reward — the agent would have learned from a "
                                         "frozen or mirrored picture."], WARN),
                   ("DEBUG OVERLAYS ARE INVISIBLE", ["A stroke drawn with PyBullet's debug-line "
                                                     "tool changed 0 camera pixels. Ink must be "
                                                     "real scene content."], BAD)],
            notes="""
Virtual camera PyBullet me scene ki photo leta hai. Pinhole model: 3D point screen par
focal length aur distance ke hisaab se project hota hai. View matrix = camera kahan hai,
projection matrix = kitna wide dekhta hai.

480x480 ki colour photo, aur segmentation mask jo batata hai kaunse pixel paper ke hain.

Orientation maan kar nahi chali — ek asymmetric nishan banake 8 tarah ke flip/rotation test kiye,
identity jeeta (IoU 0.998).

Do bade bug: arm paper ko dhak raha tha (hal: photo se pehle arm ko seedha upar park karo), aur
PyBullet texture ko filename se cache karta hai, to photo purane frame par atak gayi thi (hal:
har baar naya filename). Yeh bug bina pakde reh jaate to agent galat tasveer se seekhta.
""")

    figure(prs, "05 · pipeline", "From photograph to ink: the perception pipeline",
           "Measured on the square: the camera recovers the true drawing at IoU 0.882.",
           "fig_vision_pipeline.png",
           ["1 · Raw frame: a virtual RGB photo of the sheet.",
            "2 · OpenCV extraction: keep paper pixels (segmentation), crop to the sheet, "
            "threshold dark → ink.",
            "3 · Ground truth: what the pen really inked (the canvas).",
            "4 · Overlay: agreement between 2 and 3.",
            "Line: IoU 0.871 · square: 0.882.",
            "Perceived strokes are ~14% thicker than the truth: rendering and texture filtering "
            "widen thin lines slightly."],
           fig_w=8.2, size=12.5,
           take="This is the 'real' camera. For training speed a validated fast model of it is "
                "used instead (next slides).",
           notes="""
Photo se ink tak ka pipeline: (1) virtual camera ki raw photo, (2) OpenCV: sirf paper ke pixel
rakho, crop karo, threshold lagao — dark pixel = ink, (3) asli canvas, (4) dono ka overlay.

Square par IoU 0.882, line par 0.871. Camera wali lines asli se ~14% moti dikhti hain — render
aur texture filtering patli line ko thoda phaila dete hain.

Training ke liye yeh asli camera bahut slow hai, isliye uska ek tez, validated model use hota
hai — agle slides.
""")

    steps(prs, "05 · thresholding", "Thresholding: deciding what counts as ink",
          "One number splits every pixel into 'ink' or 'paper'.",
          [("rule", "ink(x, y) = 1  if  gray(x, y) < T,  else 0",
            ["Every pixel darker than the threshold T becomes ink."]),
           ("Otsu", "T* = argmax_T  ω₀(T)·ω₁(T)·( μ₀(T) − μ₁(T) )²",
            ["Otsu's method picks T automatically: the split that makes the two groups most "
             "different (max between-class variance). ω = group sizes, μ = group means."]),
           ("failed", "Otsu with the arm in frame → split 'arm vs paper', lost the stroke",
            ["The dark arm was the biggest contrast in the picture, so Otsu separated arm from "
             "paper and called the thin stroke background."]),
           ("chosen", "arm parked + paper mask + fixed T = 128",
            ["In a controlled white-paper / black-ink scene a fixed threshold is robust. Later "
             "(Stage 2) the threshold became a FRACTION between the ink and paper levels, which "
             "is what real pipelines do."])],
          notes="""
Thresholding: har pixel ko ink ya paper me baantna. Threshold se dark = ink.

Otsu method automatically threshold chunta hai — aisa split jisme dono group sabse alag hon.
Par jab arm photo me tha, sabse bada contrast arm vs paper tha, to Otsu ne patli line ko
background bana diya.

Hal: arm park karo, sirf paper ke pixel dekho, aur fixed threshold 128 lagao. Saaf safed paper
aur kaali ink ke liye yeh robust hai. Stage 2 me threshold ko ink aur paper ke level ke beech
ek fraction bana diya — jo asli pipelines karti hain.
""")

    tabular(prs, "05 · metrics", "How close is a drawing to its target? Seven metrics",
            "D = drawn ink mask, T = target mask. Implemented in rl/metrics.py and validated on hand-made cases.",
            ["metric", "formula / definition", "reads as", "used for"],
            [["IoU", "|D ∩ T| / |D ∪ T|", "1 = perfect, 0 = no overlap; stray ink lowers it", "reward + the headline score"],
             ["coverage", "|D ∩ T| / |T|", "share of the target that got ink (recall)", "diagnostics"],
             ["precision", "|D ∩ T| / |D|", "share of the ink that is on target", "diagnostics"],
             ["MSE", "mean (D − T)²", "pixel-wise squared error", "secondary"],
             ["chamfer", "mean distance from each ink pixel to the nearest target pixel", "how far off, not just whether", "secondary"],
             ["SNR", "strokes(D) / strokes(T)", "stroke fragmentation (from D09)", "≈1 by construction while the pen stays down"],
             ["path_ratio", "pen travel / outline length", "1 = traced once, efficiently", "caught the zig-zag and overshoot"]],
            colw=[1.5, 4.2, 3.6, 2.9], size=10.5, row_h=0.43,
            below=["Validated: identical masks → IoU 1, MSE 0, chamfer 0; disjoint → IoU 0; "
                   "half-overlap → IoU exactly 1/3 (0.333).",
                   "Worked IoU example: target 100 px, drawing 100 px, 50 px shared → "
                   "50 / (100 + 100 − 50) = 1/3."],
            take="IoU is the metric that matters: it rewards covering the target AND punishes "
                 "scribbling outside it.", take_color=GOOD,
            notes="""
Drawing kitni achhi hai, isko naapne ke saat tareeke. Sabse zaroori IoU: common area / kul area.
1 = bilkul same, 0 = koi overlap nahi. Target se bahar scribble karo to union badhta hai aur IoU
girta hai — isliye "scribble karke cover karna" kaam nahi karta.

Coverage = target ka kitna hissa cover hua. Precision = ink ka kitna hissa sahi jagah. Chamfer =
ink target se kitni door hai. SNR = strokes ka ratio (pen hamesha neeche ho to ~1). path_ratio =
pen kitna chala / shape ki lambai — isne zig-zag aur overshoot pakda.

Example: target 100 pixel, drawing 100 pixel, 50 common → 50/(100+100−50) = 1/3.
""")

    tabular(prs, "05 · camera model", "A fast camera model, validated against the real render",
            "Rendering every training step would take hours; a cheap model of the camera takes milliseconds.",
            ["shape", "fast model IoU", "real camera IoU", "gap"],
            [["line", "0.298", "0.312", "0.014"], ["circle", "0.426", "0.446", "0.021"],
             ["square", "0.463", "0.462", "0.001"], ["triangle", "0.319", "0.323", "0.004"]],
            colw=[2.5, 3.0, 3.0, 2.0], size=12, row_h=0.40,
            below=["Fast model (_perceive): shrink the canvas to the camera's effective pixel count "
                   "(150 px), threshold, scale back. Same steps as the real pipeline, minus the render.",
                   "Compared on each vision-trained agent's real drawing: mean gap 0.010; the two "
                   "perceptions overlap at IoU 0.845.",
                   "Speed: 2,296 steps/s (fast model) vs 8.6 steps/s (real render, ~270× slower). "
                   "A real-camera training run that matches the proxy's would take ~6.5 hours.",
                   "A 20k-step real-camera training run was done to prove the loop works end to end "
                   "(coverage 0.08 → 0.20) — far too short to learn, as expected."],
            take="The proxy gives essentially the same reward as a real render, ~270× faster — "
                 "so the H2 results transfer to a rendered camera.", take_color=GOOD,
            notes="""
Har training step par asli camera render karna ghanton ka kaam hai. Isliye camera ka ek sasta
model banaya: canvas ko camera ke effective resolution (150 px) tak chhota karo, threshold lagao,
wapas bada karo. Asli pipeline jaisa, bas render ke bina.

Validation: har vision-trained agent ki drawing par dono se reward nikala. Average gap sirf 0.010,
aur dono perceptions 0.845 IoU par overlap karti hain. Speed: 2,296 vs 8.6 steps/second — ~270
guna tez.

Iska matlab: H2 ke saare results asli rendered camera par bhi laagu hote hain.
""")

    concept(prs, "05 · domain randomisation", "Domain randomisation: training for a camera you have not met",
            "Tobin et al. (IROS 2017): vary the simulator so reality looks like just another variation.",
            ["One fixed simulated camera is an idealisation; a real one differs in a hundred ways.",
             "Domain randomisation samples a different camera for every episode during training, "
             "so the policy cannot rely on any one camera's quirks.",
             "Our camera model (rl/perception.py) can vary eight things, in the order a real "
             "imaging chain applies them: paper tone, ink contrast, camera pose (residual "
             "warp), sensor resolution, defocus blur, exposure gain, sensor noise, threshold.",
             "TRAIN and HELD-OUT ranges are disjoint on every axis: the held-out camera is "
             "always outside anything seen in training.",
             "The camera is re-sampled per EPISODE, never per step — the reward is an IoU "
             "difference, so a camera changing mid-episode would inject noise into it."],
            cards=[("HOW MUCH INK EACH CAMERA RECOVERS", ["From a perfect drawing (upper bound), "
                                                          "mean over 4 shapes:",
                                                          "fixed 0.834 · train 0.756 · held-out 0.394",
                                                          "The held-out camera loses more than half "
                                                          "the ink."], ACCENT),
                   ("WHICH AXES MATTER", ["Only resolution, blur and residual warp move the "
                                          "result. Gain, tone, contrast, threshold cancel by "
                                          "construction (auto-threshold); noise is inert alone."], WARN)],
            analog="Practising cricket on many different pitches so a new ground on match day "
                   "is just one more pitch.",
            notes="""
Ek fixed simulated camera idealised hai; asli camera sau tarah se alag hoga. Domain
randomisation (Tobin 2017): training me har episode alag camera, taaki policy kisi ek camera ki
aadaton par na tike.

Hamara camera model 8 cheezen badal sakta hai — paper ka rang, ink ka contrast, camera ki thodi
tedhi position, resolution, blur, exposure, noise, threshold. Train aur held-out ranges har axis
par alag hain — held-out camera kabhi training me nahi dikha.

Camera har EPISODE badalta hai, har step nahi — warna reward me camera ka noise aa jaata.

Kitni ink dikhti hai: fixed camera 0.834, train 0.756, held-out sirf 0.394 — aadhi se zyada ink
gayab. Sirf resolution, blur aur warp asli farak daalte hain; baaki by construction cancel ho
jaate hain. Analogy: alag-alag pitch par practice, taaki match ka naya ground bas ek aur pitch lage.
""")


def problem(prs):
    section(prs, 6, "The research problem & the literature",
            "What exactly is being asked, what 33 papers already did, the gap they themselves "
            "point to, what we must not claim, and the hypotheses that turn the gap into tests.",
            ["Problem statement", "The privileged-canvas problem", "33-paper review",
             "The gap, in their words", "What we claim (and do not)", "Hypotheses H1–H6"])

    s = slide(prs, "The privileged-canvas problem", "06 · the problem",
              "The single idea the whole project is built around.")
    # left: simulation world
    rect(s, M, 1.62, 5.85, 3.6, fill=WASH, line=LINE, shape=MSO_SHAPE.ROUNDED_RECTANGLE,
         radius=0.04)
    txt(s, M + 0.2, 1.72, 5.4, 0.3, "IN SIMULATION (how drawing agents are usually trained)",
        size=11.5, color=PRIMARY, bold=True)
    node(s, M + 0.35, 2.25, 1.9, 1.0, "AGENT", color=VIOLET, title_size=13)
    node(s, M + 3.6, 2.25, 1.9, 1.0, "EXACT CANVAS", "every pixel known", color=GOOD,
         title_size=11)
    arrow(s, M + 3.55, 2.75, M + 2.30, 2.75, color=GOOD, lw=2.2, label="perfect reward",
          label_w=1.6)
    bullets(s, ["The reward reads the drawing straight from memory — exact, instant, free.",
                "Used by D01, D02, D05, D09 (RL drawing papers)."], M + 0.25, 3.55, 5.4, 1.5,
            size=11.5, tight=True)
    # right: real world
    x2 = M + 6.3
    rect(s, x2, 1.62, CW - 6.3, 3.6, fill=WASH, line=LINE, shape=MSO_SHAPE.ROUNDED_RECTANGLE,
         radius=0.04)
    txt(s, x2 + 0.2, 1.72, 5.4, 0.3, "ON A REAL ROBOT", size=11.5, color=BAD, bold=True)
    node(s, x2 + 0.35, 2.25, 1.9, 1.0, "AGENT", color=VIOLET, title_size=13)
    node(s, x2 + 3.6, 2.25, 1.9, 1.0, "CAMERA PHOTO", "blurry, noisy, partial", color=ACCENT,
         title_size=11)
    arrow(s, x2 + 3.55, 2.75, x2 + 2.30, 2.75, color=ACCENT, lw=2.2, label="imperfect signal",
          label_w=1.7)
    bullets(s, ["There is no digital copy of a sheet of paper. The robot only has what its "
                "camera sees — the 'privileged canvas' does not exist.",
                "So an agent trained on the exact canvas is trained on a signal it will never get."],
            x2 + 0.25, 3.55, 5.4, 1.6, size=11.5, tight=True)
    card(s, M, 5.40, CW, 0.85, "THE QUESTION",
         ["What drawing accuracy is lost when the agent learns from perception instead of truth — "
          "and does seeing the paper help when things go wrong?"], accent=VIOLET, body_size=13)
    strip(s, "Nobody had measured this. The three closest papers name it as their own open "
          "problem (next slides).", GOOD)
    note(s, """
Yeh poore project ka ek central idea hai. Simulation me drawing agents ko reward seedha memory se
milta hai — canvas ka har pixel pata hai, perfect aur free. D01, D02, D05, D09 aise hi train hue.

Asli robot ke paas kaagaz ki koi digital copy nahi hoti. Sirf camera ki photo — dhundhli, noisy,
adhuri. Isliye perfect canvas par train hua agent ek aise signal par seekh raha hai jo use asli
duniya me kabhi nahi milega. Ise hum "privileged canvas" problem kehte hain.

Sawaal: camera se seekhne me kitni accuracy jaati hai — aur kya paper dekh paana galtiyon se
ubarne me madad karta hai? Yeh pehle kisi ne naapa nahi tha.
""")

    grid(prs, "06 · literature", "The literature review: 33 papers, read with care",
         "Done before changing any code, so the plan rests on evidence rather than assumptions.",
         [("SCOPE", ["33 papers in 5 folders: Foundational 6 · Directly related 11 · Advanced "
                     "methods 8 · Robotics & vision 3 · Reinforcement learning 5."], PRIMARY),
          ("DEPTH, RECORDED HONESTLY", ["8 read in full (◆), 25 at abstract + targeted sections (◇).",
                                        "Numbers are only quoted from ◆ papers."], GOOD),
          ("METADATA VERIFIED", ["Every arXiv record checked through the arXiv API — this caught "
                                 "mis-stated venues in search summaries (e.g. CalliRewrite is "
                                 "ICRA 2024, not IROS 2024)."], ACCENT),
          ("READ IN FULL", ["D01 From Scratch to Sketch · D02 Learning to Paint · D03 Teaching "
                            "Robots To Draw · D04 Autonomous Visual Rendering · D08 Sim-to-Real "
                            "Brush · D09 CalliRewrite · A01 FRIDA · R02 RL without Reward Engineering"],
           VIOLET),
          ("OUTPUTS", ["research_papers/README.md (index) · STUDY_NOTES.md (per-paper analysis) · "
                       "COMPARATIVE_ANALYSIS.md · docs/PROJECT_PROPOSAL_v2.md (what to change)."], SLATE),
          ("TWO MISSING EXPERIMENTS", ["H3 — is the camera reward being fooled?",
                                                    "H4 — does vision recover errors that "
                                                    "kinematics cannot see? (the linchpin)"], WARN)],
         cols=3,
         notes="""
Code badalne se pehle 33 papers ka review kiya, taaki plan saboot par tike. 5 folders me baante.
8 papers poore padhe (◆), 25 ka abstract aur zaroori hisse (◇). Number sirf poore padhe papers se
quote karte hain.

Har arXiv paper ka metadata arXiv API se check kiya — search summaries me venue galat the, jaise
CalliRewrite ICRA 2024 hai, IROS nahi.

Review ne do experiments bataye jo missing the: H3 (kya camera reward ko bewakoof banaya ja raha
hai?) aur H4 (kya camera un galtiyon se ubaar sakta hai jo kinematics nahi dekh sakti?).
""")

    tabular(prs, "06 · literature", "The closest work, and how it gets its feedback",
            "The column that matters is the last one.",
            ["ID", "paper", "venue", "method", "where its learning / feedback signal comes from"],
            [["D01", "From Scratch to Sketch (Lee et al.)", "ICRA 2022", "hierarchical RL, real robot",
              "virtual canvas; camera-FREE, synchronised by forward kinematics"],
             ["D02", "Learning to Paint (Huang et al.)", "ICCV 2019", "model-based RL, strokes",
              "exact virtual canvas"],
             ["D03", "Teaching Robots To Draw (Kotani & Tellex)", "ICRA 2019", "supervised, stroke data",
              "demonstrations; open loop on the robot"],
             ["D09", "CalliRewrite (Luo et al.)", "ICRA 2024", "unsupervised + RL, Dobot arm",
              "simulated canvas"],
             ["A01", "FRIDA (Schaldenbrand et al.)", "ICRA 2023", "differentiable planning",
              "real camera — used to RE-PLAN, not as a learning reward"],
             ["R01 / R02", "Sermanet et al. / Singh et al.", "RSS 2017 / 2019", "perceptual rewards",
              "vision-based reward (for manipulation, not drawing)"],
             ["—", "e-David (Deussen et al., Konstanz)", "~2009 onwards", "painting robot",
              "optical feedback loop — the historical origin; must be cited"]],
            colw=[1.0, 3.2, 1.6, 2.5, 3.9], size=10, row_h=0.47,
            take="Learning drawing agents use a privileged canvas; systems with real cameras use "
                 "them to re-plan. Learning FROM the camera, for drawing, is the open slot.",
            take_color=VIOLET,
            notes="""
Sabse kareebi papers aur unka feedback kahan se aata hai — yahi aakhri column sabse zaroori hai.
D01 (ICRA 2022) sabse kareeb hai: RL se real robot drawing, par jaan-boojh kar camera ke bina —
forward kinematics se sync. D02 aur D09 virtual canvas par. D03 supervised hai, robot par open loop.
FRIDA (ICRA 2023) asli camera use karta hai, par re-planning ke liye, learning reward ke liye nahi.
Sermanet aur Singh ne perception se reward diya, par manipulation ke liye, drawing ke liye nahi.
e-David optical feedback painting ka origin hai — iska citation zaroori hai.

Nateeja: drawing ke learning agents privileged canvas use karte hain; camera wale systems
re-plan karte hain. Camera SE seekhna, drawing ke liye — yahi khaali jagah hai.
""")

    s = slide(prs, "The gap — in the closest papers' own words", "06 · the gap",
              "Three recent ICRA papers name this project's question as their own future work.")
    quotes = [("D01 · Lee et al. · ICRA 2022",
               "“using a camera as an observation of canvas in the future work could be of "
               "great help in the synchronization step”", VIOLET),
              ("D03 · Kotani & Tellex · ICRA 2019",
               "“we are interested in closing the learning loop by enabling the robot to "
               "inspect what it has drawn and improve its drawing policy based on observation of "
               "what it actually drew”", PRIMARY),
              ("D09 · Luo et al. · ICRA 2024",
               "“…a lack of real-world training scenarios to bridge the sim2real gap. We "
               "leave these challenges as our future work.”", ACCENT)]
    for i, (who, q, c) in enumerate(quotes):
        y = 1.62 + i * 1.47
        rect(s, M, y, CW, 1.32, fill=WASH, line=LINE, shape=MSO_SHAPE.ROUNDED_RECTANGLE,
             radius=0.05)
        rect(s, M, y, 0.07, 1.32, fill=c)
        txt(s, M + 0.3, y + 0.14, CW - 0.6, 0.3, who, size=11.5, color=c, bold=True)
        txt(s, M + 0.3, y + 0.46, CW - 0.6, 0.85, q, size=15, color=INK, italic=True,
            spacing=1.2)
    strip(s, "A strong, citable, recent gap statement — and it is theirs, not ours.", GOOD)
    note(s, """
Teen recent ICRA papers ne khud likha hai ki yeh sawaal unka future work hai. D01: camera ko canvas
ki observation ki tarah use karna madadgar ho sakta hai. D03: robot jo banaye use dekh kar apni
policy sudhaare — learning loop band karna. D09: sim2real gap aur real-world training scenarios
future work hain.

Yeh bahut mazboot gap statement hai, kyunki yeh hamara daava nahi, unke apne shabd hain.
""")

    s = slide(prs, "What we can claim — and what we must never claim", "06 · positioning",
              "Overclaiming novelty is the fastest way to a rejection.")
    card(s, M, 1.62, 5.95, 3.95, "CANNOT CLAIM (prior art exists)",
         ["'RL for robot drawing is new' — D01, D02, D05, D09 did it.",
          "'Vision-based rewards are new' — Sermanet (RSS 2017), Singh (RSS 2019).",
          "'Closed-loop visual feedback for drawing is new' — FRIDA (ICRA 2023), e-David (~2009).",
          "'Teaching a robot HOW to learn to draw' — true, but every RL drawing paper does it.",
          "Words such as 'novel', 'first to', 'outperforms', 'equivalent' (banned by the "
          "paper checker)."], accent=BAD, body_size=12)
    card(s, M + 6.2, 1.62, CW - 6.2, 3.95, "CAN CLAIM (a measurement)",
         ["Existing learning drawing agents are rewarded from a privileged canvas that no "
          "real robot has.",
          "We MEASURE what accuracy is lost when the agent learns from perception instead "
          "of truth.",
          "And whether seeing the paper helps when things go wrong (H4).",
          "Our reward is DENSE and SPATIAL (IoU), unlike the binary success classifiers of "
          "Sermanet / Singh — which is what makes an accuracy comparison possible at all."],
         accent=GOOD, body_size=12)
    strip(s, "The one objection that is fatal if unanswered: D01 draws well with NO camera and "
          "argues camera-free is better. H4 exists to answer it.", BAD, y=5.80, h=0.55)
    note(s, """
Kya daava nahi kar sakte: RL se drawing naya nahi hai, vision reward naya nahi hai, closed-loop
visual feedback naya nahi hai. "Novel", "first to", "outperforms" jaise shabd paper me band hain —
ek script inhe pakad leti hai.

Kya daava kar sakte hain: yeh ek MEASUREMENT hai. Maujooda agents privileged canvas se seekhte hain;
hum naapte hain ki camera se seekhne me kitna jaata hai, aur kya camera galtiyon me madad karta hai.
Hamara reward dense aur spatial hai (IoU), isliye accuracy compare karna possible hai.

Ek objection jo jawab na mile to project ko maar deta hai: D01 bina camera ke achha draw karta hai
aur kehta hai camera-free behtar hai. H4 isi ka jawab dene ke liye hai.
""")

    tabular(prs, "06 · hypotheses", "The hypotheses — and where each stands today",
            "Status as recorded in docs/RESEARCH_LOG.md and docs/PAPER_PLAN.md (19 Oct 2026).",
            ["ID", "statement (short)", "status"],
            [["H1", "A model-free RL agent can learn to draw shapes in pen space, no demonstrations",
              "SHOWN — every shape learned from IoU ≈ 0 to a recognisable drawing"],
             ["H2", "A camera reward gives drawing accuracy indistinguishable from a ground-truth reward",
              "SHOWN — no detectable difference (two sweeps, opposite signs, |t| < 1.5)"],
             ["H3", "The camera-rewarded agent does not learn to fool the camera",
              "SHOWN — mean gap −0.0001 over 3,328 episodes (1 seed / shape)"],
             ["H4", "Seeing the paper recovers from disturbances kinematics cannot see", h4_status()],
             ["H5", "Open-loop error grows with stroke count; closed-loop does not", "NOT STARTED"],
             ["H6", "Reported IoU understates learning: agents finish early, overshoot, then idle",
              "MEASURED — real (0.064 lost); fixable; does NOT bias H2"],
             ["RQ3", "How do PPO and SAC compare?", "PLANNED — not run"],
             ["RQ4", "Does the shape curriculum help?", "NOT STARTED"]],
            colw=[0.9, 6.9, 4.4], size=10.5, row_h=0.46,
            cell_colors={(0, 2): GOOD, (1, 2): GOOD, (2, 2): GOOD, (3, 2): WARN, (5, 2): GOOD,
                         (4, 2): MUTED, (6, 2): MUTED, (7, 2): MUTED},
            notes="""
Hypotheses aur aaj ki stithi. H1: RL agent bina demonstration ke draw karna seekh sakta hai —
dikhaya gaya. H2: camera reward aur perfect reward me koi detectable farak nahi — dikhaya gaya
(do alag sweeps me farak ka sign bhi ulta aaya). H3: agent camera ko bewakoof nahi banata —
dikhaya gaya. H4: camera disturbances se ubaarta hai — iski stithi slide par likhi hai. H5 shuru
nahi hua. H6: agents jaldi khatam karke overshoot karte hain — naapa gaya, theek ho sakta hai, aur
H2 ko bias nahi karta. RQ3 (PPO vs SAC) aur RQ4 (curriculum) abhi baaki.

Note: H4 ki line results file se build ke waqt padhi jaati hai; sweep khatam hone ke baad deck
rebuild karo to final result apne aap aa jaata hai (Section 9).
""")


def h4_status():
    import h4data
    st = h4data.summary()
    if st["final"]:
        return "DONE — null on all three disturbances (32/32); design could not discriminate"
    return f"RUNNING — {st['runs']}/32 runs; no verdict until all 8 cells exist"


def build(prs):
    vision(prs)
    problem(prs)
