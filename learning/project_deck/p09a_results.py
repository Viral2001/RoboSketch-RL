"""Section 9a - results: overview, H1, H2, H3, camera randomisation."""
from kit import *  # noqa: F401,F403


def build(prs, toc):
    section(prs, 9, "Results, one by one",
            "Each experiment: the question, the design, the figure, the numbers (n, mean ± sd, paired "
            "difference, k/n, t), what it shows - and what it does NOT show. Negative results included.",
            ["Overview", "H1 learns to draw", "H2 camera vs truth (TOST)", "H3 exploitation",
             "Camera randomisation", "H4 - the full story", "H5, H6 / overrun",
             "Generalisation & Stage 4", "Curriculum, pen-free, digits", "Negative results"],
            """
Section 9: results. Har result ek hi format me: sawaal -> design -> figure -> numbers -> kya dikhata
hai -> kya NAHI dikhata. Negative results bhi utne hi detail me hain - woh bhi result hain.
Sabse lamba hissa H4 hai (kyunki D01 ka jawab wahi hai).""", toc)

    tabular(prs, "09 · overview", "All results on one slide", "Simulation only. Details on the following slides.",
            ["experiment", "headline (true IoU)", "verdict"],
            [["H2 camera vs truth reward (n = 12)", "0.384 vs 0.388, d = +0.004, t = +0.27, TOST p = 0.008", "equivalent ±0.05"],
             ["H3 reward exploitation", "perceived - true = -0.0001 over 3328 episodes", "not exploited"],
             ["Camera randomisation (n = 8)", "held-out camera: randomised - fixed = -0.011, t = -0.67", "no help (negative)"],
             ["H4 paper shift, replication (n = 8)", "camera_est loses 0.046, fk 0.165: +0.119, 8/8, t = +8.32", "recovery (replicated)"],
             ["H4 slip / ink failure", "+0.004 / +0.003 vs fk; estimator costs vs plain camera", "none detectable"],
             ["H5 open vs closed loop (n = 80)", "open-loop deviation grows; closed-loop flat", "feedback matters"],
             ["H6 overrun / overshoot", "peak at step 12-41 of 240; mean 0.064 lost", "measured pitfall"],
             ["Generalisation (n = 8)", "held-out 0.074 (fixed) → 0.118 (family) → 0.298 (ego view)", "a limit; ego helps"],
             ["Curriculum (n = 6)", "0.246 vs 0.418, t = -2.99", "hurts (negative)"],
             ["Pen-free A2 (n = 6)", "0.329 vs 0.418, t = -2.29", "no detectable effect"]],
            colw=[3.7, 5.6, 2.5], size=11.5, row_h=0.43, align="left",
            cell_colors={(0, 2): GOOD, (1, 2): GOOD, (2, 2): BAD, (3, 2): GOOD, (4, 2): WARN,
                         (5, 2): GOOD, (6, 2): WARN, (7, 2): WARN, (8, 2): BAD, (9, 2): WARN},
            notes="""
Poore project ke results ek slide par. Isko yaad kar lo - interview me "what did you find?" ka jawab:
- H2: camera reward aur truth reward equivalent (+/-0.05 IoU, TOST).
- H3: camera reward exploit nahi hua.
- Camera randomisation: koi fayda nahi - negative result, kyunki problem camera realism thi hi nahi.
- H4: paper shift par camera_est ne fk se +0.119 kam khoya, 8/8, t=+8.32, fresh seeds par replicate.
  Slip/ink failure par kuch detectable nahi; estimator ki cost bhi dikhi.
- H5: feedback (closed loop) error ko badhne nahi deta.
- H6: agent jaldi khatam karta, overshoot karta.
- Generalisation: ek limit; ego view bahut madad karta hai.
- Curriculum: nuksaan. Pen-free: koi detectable farak nahi (par slow).
""", source="docs/paper/main.tex sections IV-A..IV-G; README.md 'Main results'; RESEARCH_LOG RESULT entries named on each later slide")

    figure(prs, "09 · H1", "H1: a PPO agent learns to draw every shape", "Before vs after 400k steps, truth reward, single runs (5 Aug 2026).",
           "fig_before_after.png",
           ["Untrained → trained true IoU: line 0.079 → 0.508, circle 0.000 → 0.443, square 0.000 → 0.493, "
            "triangle 0.000 → 0.421.",
            "All four are recognisable - learned by trial and error, no demonstrations, no scripted path.",
            "Visible defects: zig-zag strokes, spurs off the outline, and (here) a tail from the old centre start.",
            "Single runs, so no statistics - H1 is the proof of concept; the multi-seed sweeps came next."],
           fig_w=7.4, take="H1 supported - but the absolute level is modest (~0.4-0.5), and a scripted tracer "
                           "reaches ~0.72-0.74 (see 'absolute level').", take_color=WARN,
           notes="""
H1: kya RL agent bina demonstrations ke drawing seekh sakta hai? Haan. 400k steps ke single runs: line
0.079 -> 0.508, circle 0 -> 0.443, square 0 -> 0.493, triangle 0 -> 0.421. Chaaron pehchaanne laayak.

Kamiyan bhi dikhti hain: zig-zag, outline se bahar spurs, aur centre-start wali tail (baad me fix).

Yeh single runs hain - koi statistics nahi. H1 proof-of-concept hai. Aur honest framing: absolute level
modest hai; ek scripted tracer ~0.72-0.74 tak pahunchta hai. Project ka claim "agent achha draw karta
hai" NAHI hai - claim reward-source gap ke baare me hai.
""", source="RESEARCH_LOG '### Full task ladder trained (2026-08-05)'; docs/PAPER_PLAN.md C8")

    figure(prs, "09 · H1", "What trained drawings look like", "Deterministic nearest-centre start, truth reward, 400k steps. Black = ink, pink = target.",
           "demo_live_agents.png",
           ["Line 0.505, circle 0.357, square 0.470, triangle 0.468 (IoU printed on the image).",
            "The tail is gone; the circle no longer fully closes (0.443 → 0.357): net ≈ a wash.",
            "Strokes are jagged: IoU only partly punishes a zig-zag path - hence path_ratio.",
            "This is the README figure; it is what 'IoU ≈ 0.4-0.5' looks like."],
           fig_w=8.0, start=15,
           notes="""
Yeh README wala figure hai - IoU 0.4-0.5 asal me kaisa dikhta hai. Deterministic start (target par,
centre ke paas) ke baad: line 0.505, circle 0.357, square 0.470, triangle 0.468.

Tail chali gayi, par circle ab poora band nahi hota (0.443 -> 0.357) - net lagbhag barabar.

Strokes jagged hain - IoU zig-zag ko poori tarah punish nahi karta, isliye path_ratio metric add kiya.

Interview tip: is figure ko dikha ke bolo "IoU 0.5 is recognisable but far from perfect - which is why
the paper is about the gap between reward sources, not drawing quality."
""", source="RESEARCH_LOG '### Start-tail fix (2026-08-07)' (deterministic-start retrain table); README.md figure")

    concept(prs, "09 · H2", "H2: does a camera reward cost accuracy? - the design", None,
            ["Two arms, identical in everything except where the reward's IoU comes from: the exact canvas "
             "('truth') or the simulated camera image ('vision').",
             "Observation stays the privileged canvas here - only the REWARD is degraded (the camera-in-the-"
             "observation case is the randomisation experiment).",
             "4 shapes × seeds 100, 200, 300 = 12 paired (shape, seed) cells; 200k steps; 240-step episodes.",
             "Pre-registered (31 Oct): equivalence by TOST with margin ±0.05 IoU, α = 0.05 each side; peak IoU "
             "reported beside final IoU; NOT pooled with the earlier overlapping-seed sweeps.",
             "Both arms scored on TRUE IoU."],
            cards=[("WHY SPACED SEEDS", ["Both earlier sweeps used seeds 0, 1, 2 (7/8 env streams shared) and "
                                         "their sign flipped - so the main result was re-run cleanly."], WARN),
                   ("WHY TOST", ["'No detectable difference' invites 'underpowered'; an equivalence test with a "
                                 "fixed margin answers that."], VIOLET)],
            notes="""
H2 ka design: do arms bilkul same, sirf reward ka IoU kahan se aata hai - exact canvas (truth) ya camera
image (vision). Observation dono me privileged canvas - sirf reward degrade hua. (Camera observation
me bhi ho - woh domain randomisation experiment hai.)

4 shapes x seeds 100/200/300 = 12 paired cells, 200k steps, 240-step episodes. Pre-registered: TOST
margin +/-0.05. Purane sweeps ke saath pool nahi kiya (woh independent nahi the).

Kyun dobara chalaya? Dono purane sweeps seeds 0,1,2 par the (F6 overlap) aur unka sign flip ho gaya
tha. Aur "no detectable difference" pe reviewer bolta "underpowered" - TOST uska jawab hai.
""", source="RESEARCH_LOG '## 2026-10-31 - H2 re-run with spaced seeds launched (pre-registered)'")

    figure(prs, "09 · H2", "H2 result: camera reward ≈ truth reward (equivalent within ±0.05)",
           "Spaced seeds 100/200/300, n = 12 paired cells, TRUE IoU.", "h2_spaced_crop.png",
           ["Truth 0.388 ± 0.062 vs camera 0.384 ± 0.059.",
            "Paired d = truth - camera = +0.004 (sd 0.055); truth ahead in 6/12; t = +0.27.",
            "90% CI of d: [-0.024, +0.033], inside ±0.05: TOST p = 0.008 → EQUIVALENT.",
            "Peak IoU too: 0.424 vs 0.415, d = +0.009, p_TOST = 0.008.",
            "Per shape (n = 3, untested): square +0.055, triangle +0.020, line -0.028, circle -0.030."],
           fig_w=6.6, start=15, take="C1: 'equivalent within ±0.05 IoU in simulation (TOST)' - pooled over 4 "
                                     "shapes, fixed pictures, fixed proxy camera.", take_color=GOOD,
           notes="""
H2 result: truth 0.388 +/- 0.062, camera 0.384 +/- 0.059. Paired difference +0.004, 12 me se 6 me truth
aage (coin flip), t = +0.27. 90% CI [-0.024, +0.033] poora +/-0.05 ke andar: TOST p = 0.008 ->
EQUIVALENT within 0.05 IoU. Peak IoU par bhi equivalent.

Kya NAHI dikhata: per-shape equivalence nahi - square par truth +0.055 aage (margin se zyada), line/circle
par camera aage - par n=3 per shape, test nahi. Claim 4 shapes pooled hai. Margin 0.03 hota to pass nahi
hota. Fixed proxy camera, fixed pictures, simulation.

Allowed wording: "equivalent within +/-0.05 IoU in simulation (TOST)".
""", source="RESEARCH_LOG '### H2 spaced RESULT (2026-10-31; 24/24 runs, seeds 100/200/300)' and its Honest limits; "
            "docs/paper/main.tex Sec. IV-A; figure output/results_h2_spaced.png (cropped copy)")

    tabular(prs, "09 · H2", "H2's history - why the final number is the spaced-seed sweep", None,
            ["sweep", "truth", "camera", "difference / test", "status"],
            [["single runs, 400k (7 Aug)", "0.450", "0.411", "n = 1 per shape, no test", "superseded"],
             ["seeds 0,1,2 (12 Aug)", "0.382", "0.354", "camera - truth -0.028, t = -1.43, 5/12", "overlapping seeds"],
             ["same seeds, re-run with peak (Sep)", "-", "-", "camera - truth +0.013, t = +0.57 (sign flipped)", "not independent"],
             ["seeds 0,1,2 under TOST", "0.382", "0.354", "CI [-0.007, +0.063]: equivalence NOT shown", "contrast only"],
             ["seeds 100/200/300 (31 Oct)", "0.388", "0.384", "+0.004, t = +0.27, TOST p = 0.008", "THE RESULT"]],
            colw=[3.1, 1.0, 1.1, 4.5, 2.1], size=12, row_h=0.5, align="left",
            cell_colors={(4, 4): GOOD, (1, 4): WARN, (2, 4): WARN},
            below=["Peak vs final (Sep re-run): moving the scoring point changed the gap by only -0.0108 (SE 0.0224): "
                   "the overshoot does not bias H2. The earlier n = 1 hint that the camera arm overshoots ~2× more "
                   "did not replicate (0.022 vs 0.033)."],
            take="Report the pre-registered sweep; mention the disagreement; never pool non-independent sweeps.",
            take_color=VIOLET,
            notes="""
H2 ka itihaas - kyunki interview me "why do you trust this number?" poocha ja sakta hai:
- 7 Aug single runs: 0.450 vs 0.411 - n=1, koi test nahi.
- 12 Aug seeds 0,1,2: 0.382 vs 0.354, t = -1.43 - par seeds overlapping.
- Same seeds dobara (thread setting alag) peak ke saath: sign flip (+0.013) - independent nahi.
- Purane seeds par TOST: CI +0.05 cross karta hai -> equivalence nahi dikhi.
- 31 Oct spaced seeds: +0.004, TOST p=0.008 -> yahi result.

Peak vs final: overshoot H2 ko bias nahi karta (gap sirf -0.0108 badla, SE 0.0224 ke andar). n=1 wala
hint ki camera arm 2x overshoot karta hai, n=12 par replicate nahi hua (0.022 vs 0.033) - refuted
hypothesis, jo pehle hi "hypothesis, not result" label ki gayi thi.

Rule: pre-registered sweep report karo, disagreement chhupao mat, non-independent sweeps pool mat karo.
""", source="RESEARCH_LOG '### H2 experiment - VISION reward', '### H2 multi-seed sweep (2026-08-12)', "
            "'### H2 PEAK-vs-FINAL RESULT', '### H2 spaced RESULT'; '### Statistics housekeeping' (0.382/0.354)")

    figure(prs, "09 · H3", "H3: the camera reward is not exploited", "4 shapes × 200k steps, every training episode logged (3328 episodes), camera reward.",
           "results_h3.png",
           ["Perceived - true IoU, mean over 3328 episodes: -0.0001; largest single-episode gap 0.029.",
            "True and perceived IoU correlate at 0.997-0.999 throughout training.",
            "Control: the truth-reward run's gap is exactly 0 (logging is trustworthy).",
            "Limits: one seed per shape; within a shape the sign is consistent (square slightly positive and "
            "rising, below the 0.02 bar); tested on the fixed camera only."],
           fig_w=7.4, start=14.5, take="C2: no exploitable drift - the agent is not learning to 'please the camera' "
                                       "instead of drawing.", take_color=GOOD,
           notes="""
H3: kya agent camera ko "bewakoof" bana raha hai - aisi drawing jo camera ko achhi lage par asli me na ho?
Har training episode me perceived IoU aur true IoU dono log kiye (3328 episodes).

Result: average gap -0.0001; sabse bada ek episode me 0.029; correlation 0.997-0.999. Control: truth run
me gap exactly 0 - logging sahi hai.

Honest nuances (audit ke baad): "perceived kabhi true se aage nahi jaata" galat tha - 51.1% episodes me
aage tha; shapes ke andar sign consistent hai (line negative, square positive aur thoda badhta hua, par
0.02 ki seema se neeche). To sahi wording: "no exploitable drift". n=1 seed per shape, fixed camera only.

Figure left: gap over training (flat ~0). Right: true (solid) vs perceived (dashed) - saath-saath.
""", source="RESEARCH_LOG '### H3 RESULT - the camera reward is not being exploited' and the 2026-09-03 documentation "
            "corrections table; docs/PAPER_PLAN.md C2")

    tabular(prs, "09 · camera randomisation", "Does it survive a worse camera? (Stage 2)",
            "3 training arms × 4 shapes × 2 seeds, each scored under 3 cameras; camera now in the OBSERVATION too. TRUE IoU, n = 8.",
            ["trained on", "eval: fixed camera", "eval: train camera", "eval: HELD-OUT camera"],
            [["truth (no camera)", "0.389 ± 0.051", "0.389", "0.389"],
             ["fixed camera", "0.393 ± 0.051", "0.386 ± 0.044", "0.379 ± 0.041"],
             ["randomised cameras", "0.371 ± 0.062", "0.365 ± 0.057", "0.368 ± 0.056"]],
            colw=[3.0, 2.9, 2.9, 3.0], size=13, row_h=0.45,
            below=["Paired, randomised - fixed: fixed cam -0.022 (t = -1.09), train cam -0.020 (t = -1.05), "
                   "held-out cam -0.011 (3/8 up, t = -0.67): randomisation buys nothing detectable.",
                   "The fixed-camera agent fell from 0.393 to 0.379 (-0.014) on a camera that recovers only 0.394 "
                   "of a perfect drawing's ink (fixed camera: 0.834).",
                   "Not comparable with H2's absolute IoU: here the camera gates the observation as well."],
            take="Negative result worth having: camera realism is not where the difficulty lives.", take_color=WARN,
            notes="""
Stage 2: kya H2 ek bahut achhe camera ki wajah se tha? Teen arms: truth (no camera), fixed camera, aur
randomised cameras par training. Teeno ko teen cameras par test kiya: fixed, train, held-out. Yahan camera
observation me bhi hai - agent ko sirf photo dikhti hai.

Result: randomisation se koi fayda nahi - held-out camera par -0.011 (t=-0.67). Aur asli finding: fixed
camera wala agent held-out camera par sirf 0.014 gira (0.393 -> 0.379) - jabki woh camera perfect drawing
ki aadhi se zyada ink kho deta hai (0.394 vs 0.834).

Matlab policy ko apni drawing ki achhi tasveer nahi chahiye - bas mota-mota pata hona chahiye ki pen kahan
ja chuka hai.

Dhyan: "drop" ki correction - script ne pehle +0.006 print kiya tha (galat column); sahi +0.014.
Absolute numbers H2 se compare mat karna (task alag hai).
""", source="RESEARCH_LOG '### STAGE 2 RESULT - domain randomisation does not help' and '### Correction (2026-10-19)'; "
            "'### Calibration, measured rather than asserted' (0.394 vs 0.834)")

    concept(prs, "09 · camera randomisation", "What the randomisation result does and does not show", None,
            ["SHOWS: a policy trained with one camera transfers to a much worse, never-seen camera at small "
             "cost (-0.014), and training across cameras adds nothing detectable (t = -0.67).",
             "SHOWS: taking the canvas away from the agent and giving it a photograph cost nothing measurable "
             "(fixed camera 0.393, randomised 0.371, truth 0.389 - all within noise).",
             "DOES NOT SHOW: 'no effect' - n = 8 (2 seeds), all |t| < 1.1: 'no detectable effect'.",
             "DOES NOT SHOW: an 8-axis robustness result - only resolution, blur and residual warp move the "
             "camera; 5 axes are inert by construction.",
             "Possible confound: the randomised arm's reward is noisier at the same budget - irrelevant here "
             "because it did not help."],
            cards=[("WHY IT HELPS THE PAPER", ["A reviewer's 'would this survive a worse camera?' now has a "
                                               "measured answer instead of an argument."], GOOD),
                   ("PROPOSAL VS REALITY", ["The plan expected randomisation to be essential. It was not - "
                                            "reported as found."], WARN)],
            notes="""
Kya dikhata hai: ek camera par trained policy bahut kharab, kabhi na dekhe camera par chhoti cost (-0.014)
ke saath chalti hai; aur kai cameras par training se kuch extra nahi milta. Agent ko canvas ki jagah photo
dena bhi measurable nuksaan nahi karta.

Kya NAHI dikhata: "no effect" - sirf 2 seeds, n=8, |t| < 1.1 -> "no detectable effect". Aur "8-axis
robustness" bhi nahi - asal me sirf 3 axes (resolution, blur, warp) kuch karte hain.

Plan me socha tha randomisation zaroori hoga - nahi nikla. Yahi reported hai. Paper ke liye fayda:
reviewer ka "worse camera?" sawaal ab measured jawab rakhta hai.
""", source="RESEARCH_LOG '### STAGE 2 RESULT' (#### The reason is more interesting than the result; #### Honest limits); "
            "docs/PAPER_PLAN.md C3")
