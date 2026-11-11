"""Section 9c - H5, H6/overrun, generalisation, Stage 4, extensions, negative results."""
from kit import *  # noqa: F401,F403


def build(prs, toc):
    figure(prs, "09 · H5", "H5: open-loop error grows, closed-loop stays flat",
           "Same analytic plan, same execution noise; open loop executes blind, closed loop re-aims from the pen's actual position.",
           "h5_crop.png",
           ["4 shapes × 20 noise draws × 7 conditions; paired, n = 80 per condition.",
            "Final deviation open - closed: +3.9 to +18.9 px, 79-80/80 pairs, t = +11.4 to +13.9.",
            "Closed loop stays under 1.6 px; its IoU 0.480-0.483 under bias vs clean 0.486; open loop falls to 0.112-0.256.",
            "Growth law: constant bias → linear (log-log slope 1.00-1.02, FRIDA's 'linear'); random jitter → √steps (0.47-0.48)."],
           fig_w=7.2, start=14,
           take="Supports 'feedback beats blind execution' - NOT 'a camera beats kinematics' (D01's encoders would pass this too).",
           take_color=WARN,
           notes="""
H5: bina feedback ke plan chalao to error badhta jaata hai; feedback ke saath flat rehta hai. FRIDA ne asli
arm par yeh dekha tha ("grows linearly"). Humne simulator me reproduce kiya.

Design: dono arms SAME analytic plan follow karte hain. Open loop andha chalta hai; closed loop har step
pen ki actual position se agle waypoint par aim karta hai. Noise dono par same (paired). Do kinds: jitter
(har step random) aur bias (constant offset).

Result: closed loop < 1.6 px; open loop tak 19 px. Paired t 11-14. Growth law: bias -> linear (slope
~1.00), jitter -> sqrt(steps) (slope ~0.47) - random walk! Physics wale ke liye familiar.

Bahut zaroori limit: closed loop ko pen ki noise-free actual position milti hai - jo joint encoders bhi dete
hain. To D01 bhi yeh test pass karta. Yeh "feedback matters" dikhata hai, "camera matters" nahi. Aur yeh
RL result nahi - analytic controllers hain.
""", source="RESEARCH_LOG '## 2026-10-28 - H5: open-loop error grows with the plan, closed-loop does not' "
            "(result, paired table, growth law, 'What this does and does not show')")

    figure(prs, "09 · H6", "H6: agents finish early, overshoot, then idle", "True IoU at every step of a deterministic evaluation (400k single-run agents).",
           "results_overrun.png",
           ["Peak IoU at step 12-41 of 240: the shape is traced in the first ~10-17% of the episode.",
            "A short overshoot right after completion; then the canvas freezes for on average 74% of the episode.",
            "Mean IoU lost to the overshoot: 0.064 - more than twice the then-H2 gap (0.028).",
            "Why: no stop action and the pen always down; a Gaussian policy (ent 0.02) never lands exactly on 'stand still'."],
           fig_w=7.6, start=14,
           take="Every IoU in this project is measured AFTER the overshoot: peak IoU is reported beside final IoU.",
           take_color=WARN,
           notes="""
H6 ek unexpected finding thi (23 Aug) - path_ratio zyada kyun hai, yeh dhoondhte hue mili.
Har step par true IoU record kiya: agent shape ko episode ke pehle 10-17% me hi bana leta hai (peak step
12-41 / 240). Phir thoda overshoot (aage nikal jaata hai) aur phir canvas freeze - average 74% episode
bekaar.

Overshoot se average 0.064 IoU khota hai - us waqt ke poore H2 gap (0.028) ka do guna.

Kyun: stop action nahi, pen hamesha neeche, aur Gaussian policy exactly "ruk jaao" par kabhi nahi girti.

Consequence: har reported IoU overshoot ke BAAD naapa gaya hai - isliye ab peak IoU bhi saath me report hota hai.
Aur H4 v1 ka "robustness by overdrawing" isi idle time se juda tha.
""", source="RESEARCH_LOG '### UNEXPECTED FINDING - agents finish early, overshoot, then idle for 74% of the episode'")

    tabular(prs, "09 · H6", "Fixing the overrun? Plateau stop, stop action, short horizon",
            "Truth reward, 4 shapes × seeds 0/1, paired n = 8 (seeds 0/1 overlap - F6 - kept only to pair with old runs).",
            ["arm", "true IoU", "peak", "overshoot", "steps", "vs baseline (pairs up, t)"],
            [["baseline (240 steps)", "0.378 ± 0.056", "0.411", "0.034", "240", "-"],
             ["plateau stop (env ends it)", "0.433 ± 0.043", "0.442", "0.009", "50", "+0.055 (7/8, t +2.56)"],
             ["stop action (agent ends it)", "0.402 ± 0.064", "0.402", "0.000", "22", "+0.024 (5/8, t +0.96)"],
             ["short50 (plain 50-step episodes)", "0.417 ± 0.054", "0.433", "0.016", "50", "+0.039 (6/8, t +1.59)"]],
            colw=[3.5, 1.9, 1.0, 1.4, 1.0, 3.0], size=12.5, row_h=0.45,
            below=["4th arm (pre-registered): plateau - short50 = +0.016, 6/8, t = +0.63 → cannot be separated; a plain short "
                   "horizon gives ~71% of the plateau gain. Do NOT call the plateau stop a 'fix'.",
                   "H2 peak-vs-final re-run: scoring at the peak changed the H2 gap by only -0.0108 (SE 0.0224) - the "
                   "overshoot does not bias H2."],
            take="C5: the overrun is real and shorter episodes help; adaptive stopping is not shown to add anything.",
            take_color=WARN,
            notes="""
Overrun ka ilaaj? Teen arms + ek 4th arm:
- Plateau stop (environment episode khatam kare jab IoU badhna band ho): 0.433 vs baseline 0.378, +0.055,
  7/8, t=+2.56 - pehle "fixes it" bola gaya.
- Stop action (agent khud "done" bole): +0.024, t=0.96 - inconclusive. (Isi arm me +2 bonus bug tha.)
- Confound: plateau arm ke episodes ~50 steps - shorter horizon. 4th arm short50 (bas 50 step episodes):
  0.417. Plateau - short50 = +0.016, t = 0.63 - alag nahi kar sakte. Short horizon akela gain ka ~71% deta hai.
  Isliye plateau stop ko "fix" NAHI bolna.

Aur H2 peak-vs-final: peak par score karne se H2 gap sirf -0.0108 badla - overshoot H2 ko bias nahi karta.

Limit: seeds 0/1 (F6 overlap) - purane runs se pair karne ke liye.
""", source="RESEARCH_LOG '### OVERSHOOT ABLATION RESULT', '### C5 4th arm RESULT (2026-11-04)', '### H2 PEAK-vs-FINAL RESULT'; "
            "docs/PAPER_PLAN.md C5")

    figure(prs, "09 · generalisation", "Does it draw, or memorise four pictures?",
           "Vision reward, 200k steps, n = 8 cells, 16 distinct targets per set, TRUE IoU.", "gen_generalisation.png",
           ["Fixed-target agent: default 0.381 → train range 0.235 → HELD-OUT 0.074.",
            "Trained on a size/rotation family: 0.279 / 0.292 / 0.118.",
            "Held-out, family - fixed: +0.044, 8/8, t = +7.35 - helps, but both lose most of their home score.",
            "Memorisation: the fixed agent already loses 0.146 (t = +4.26) on targets within 20% size and 15° of its own."],
           fig_w=7.4, start=14,
           take="A LIMIT, not a pass: earlier claims (H2, H4 …) hold for the fixed-picture setting only.", take_color=BAD,
           notes="""
Reviewer ka sawaal: kya agent drawing seekh raha hai ya 4 pictures ratt raha hai?
Test: targets ka size aur rotation badlo. Held-out = size 0.6-0.8, rotation 15-45 deg (training range ke bahar).

Fixed-target agent: apne default par 0.381, thode badle (train range) par 0.235, held-out par 0.074!
Family par trained agent: 0.279 / 0.292 / 0.118. Held-out par +0.044 (8/8, t=+7.35) - madad karta hai, par
dono apne "ghar" ke score ka zyada-tar hissa kho dete hain.

Memorisation evidence: fixed agent targets jo sirf 20% size aur 15 deg alag hain, un par bhi 0.146 khota hai.

Isliye: yeh LIMIT hai. H2, H4 jaise saare claims "fixed-picture setting" ke liye hain. "Arbitrary shapes
draw karta hai" kabhi nahi bolna.
""", source="RESEARCH_LOG '### Generalisation RESULT (2026-10-31)'; docs/PAPER_PLAN.md section 4 item 4")

    tabular(prs, "09 · Stage 4", "What moves held-out accuracy? Five controlled ablations",
            "All paired with the family-trained global-view agent 'param200' (held-out 0.118), n = 8, crit 2.365.",
            ["change", "held-out IoU", "vs param200 (pairs up, t)", "verdict"],
            [["3× training (600k steps)", "0.131", "+0.013 (5/8, t +0.95)", "not a budget problem (at 3×)"],
             ["O2 ego view (64 px around the pen)", "0.298", "+0.181 (8/8, t +7.00)", "STRONG"],
             ["O2z same pixel density, not centred", "0.137", "ego - this: +0.161 (8/8, t +8.04)", "it is the centring"],
             ["O2c ego with a camera in the loop", "0.273 vs 0.130", "+0.143 (6/8, t +3.54)", "survives perception"],
             ["O3 CoordConv (x, y planes)", "0.126", "+0.008 (4/8, t +0.97)", "no help"],
             ["A1 action chunking (5 moves)", "0.120", "+0.003 (t +0.17); train -0.189 (t -15.55)", "hurts"],
             ["T1 behaviour-cloning warm start", "0.113", "-0.005 (5/8, t -0.39)", "no help"]],
            colw=[3.7, 1.8, 3.8, 2.5], size=11.5, row_h=0.44, align="left",
            cell_colors={(1, 3): GOOD, (2, 3): GOOD, (3, 3): GOOD, (4, 3): BAD, (5, 3): BAD, (6, 3): BAD},
            below=["O2c's comparison is ego_cam vs global_cam, both under the held-out camera (0.273 vs 0.130). "
                   "The line is the exception: worse with ego in both seeds."],
            take="Only the pen-centred view moved held-out accuracy; more steps, coordinates, chunking and BC did not.",
            take_color=VIOLET,
            notes="""
Stage 4: generalisation limit todne ke liye paanch controlled ablations, sab param200 (held-out 0.118) se paired:
- 3x training: +0.013, t=0.95 - budget problem nahi (kam se kam 3x par).
- O2 ego view: pen ke aas-paas ka 64 px window, pen hamesha centre me. Held-out 0.118 -> 0.298, +0.181,
  8/8, t=+7.00. Sabse bada effect.
- O2z: kya yeh bas zoom (pixel density) hai? Same density bina centring: ego isse +0.161 aage (t=+8.04) -
  centring hi kaam kar raha hai.
- O2c: camera loop me ho tab bhi: 0.273 vs 0.130, t=+3.54 - perception ke saath bhi bachta hai. Line
  exception - ego ke saath kharab.
- O3 CoordConv: +0.008 - madad nahi.
- A1 chunking (5 moves ek saath): held-out barabar par training shapes par -0.189 - nuksaan, scribble karta hai.
- T1 BC warm start: -0.005 - koi fayda nahi.

Sirf ego view ne farak dala. Kyun? Hypothesis (untested): pen-relative frame me "agla move" sawaal shape
ke size/position se independent ho jaata hai.
""", source="RESEARCH_LOG '### Generalisation part 2 RESULT', '### O2 egocentric RESULT', '### O2z zoom control RESULT', "
            "'### O2c RESULT', '### O3 CoordConv RESULT', '### A1 chunking RESULT', '### T1 BC warm start RESULT'")

    figure(prs, "09 · Stage 4", "Why might a pen-centred view generalise better?", "Illustration (toy): the same square seen two ways.",
           "ego_toy.png",
           ["Global view: the whole sheet; the policy must map 'where on the sheet' to 'which way to move' - "
            "different for every size and rotation.",
            "Ego view: the pen is always at the centre; the question becomes local - 'which way does the stroke "
            "continue from here?' - similar for any size.",
            "This is a HYPOTHESIS: the experiments show it is the centring (not zoom, not coordinates), not why.",
            "Ego was tested without H4 disturbances; it relies on knowing where the pen is."],
           fig_w=6.6, start=15,
           take="Strongest lever found on generalisation; mechanism untested.", take_color=WARN,
           notes="""
Ego view kyun kaam karta hai - ek hypothesis (test nahi hua):
Global view me agent ko poori sheet dikhti hai; use seekhna padta hai "sheet par is jagah ho to is taraf
chalo" - har size/rotation ke liye alag. Ego view me pen hamesha centre me hai; sawaal local ban jaata hai -
"yahan se stroke kis taraf jaata hai?" - jo kisi bhi size par milta-julta hai.

Experiments ne dikhaya ki farak CENTRING se hai (zoom se nahi - O2z; coordinates se nahi - O3). "Kyun" nahi
dikhaya.

Limit: ego H4 disturbances ke saath test nahi hua, aur pen ki position pata honi chahiye (asli robot par
kinematics se estimate).
""", source="RESEARCH_LOG '### O2 egocentric RESULT' honest limits, '### O3 CoordConv RESULT' ('pen-relative frame is the "
            "remaining hypothesis, untested'); figure = toy (teach_figs.py)")

    tabular(prs, "09 · absolute level", "How good is 'good'? Baselines that do not learn",
            "Same targets and scoring (TRUE IoU, 16 targets per set). Descriptive - the baselines are deterministic.",
            ["method", "default", "train", "held-out", "note"],
            [["scripted outline tracer (privileged)", "0.718", "0.736", "0.725", "reads the target's exact size/rotation"],
             ["ergodic controller (D04-style, privileged)", "0.300", "0.305", "0.306", "spreads ink; path ratio 8-35"],
             ["PPO, global view (param200)", "0.279", "0.292", "0.118", "the learner most results use"],
             ["PPO, ego view", "0.338", "0.340", "0.298", "Stage 4's best"],
             ["behaviour clone BEFORE PPO (bc0)", "0.443", "0.591", "0.142", "PPO then took it DOWN to 0.292 on train"]],
            colw=[3.9, 1.2, 1.2, 1.3, 4.2], size=12, row_h=0.47, align="left",
            cell_colors={(4, 4): BAD},
            take="C8: the claims are about the GAP between reward sources, not about drawing quality - the learner is far "
                 "below a trivial tracer.", take_color=WARN,
            notes="""
Absolute level kitna achha hai? Bina learning wale baselines se compare:
- Scripted tracer (target ka exact size/rotation padhta hai): ~0.72-0.74 har set par. Matlab environment
  0.3 par capped nahi - limit learner/reward me hai.
- Ergodic controller (non-learning, target mask padhta hai): ~0.30 har set par - PPO ke ghar ke score ke
  barabar, held-out par PPO (0.118) se kahin upar, ego (0.298) ke barabar.
- BC: tracer ko clone kiya to RL se pehle hi train par 0.591 - phir PPO ne use 0.292 tak GIRA diya (0/8,
  t=-10.27). PPO ne achha start "unlearn" kiya. Kyun - untested.

Interview line: "My claims are about the gap between reward sources, not drawing quality; a scripted
tracer is far ahead of my learner, and I say so."
""", source="RESEARCH_LOG '### T1 BC warm start RESULT' (expert and bc0 rows), '### Ergodic baseline RESULT', '### O2 egocentric RESULT'; "
            "docs/PAPER_PLAN.md C8")

    tabular(prs, "09 · extensions", "Extensions: curriculum, pen-free, digits", "One deterministic eval episode per run; n = 6 (3 shapes × 2 seeds) or descriptive.",
            ["question", "result", "verdict"],
            [["RQ4: pre-train on the line, then the shape?", "final 0.246 vs scratch 0.418 (-0.173, 5/6 worse, t = -2.99, crit ~2.57); "
              "behind at every checkpoint; no jump-start", "HURTS (negative transfer)"],
             ["A2: let the agent lift the pen (single-stroke shapes)", "0.329 vs 0.418 (-0.090, 5/6 worse, t = -2.29); slower start; "
              "pen down ~10% of steps; SNR 1.67", "no detectable effect on final IoU"],
             ["Digits (pen-free; 1, 7 vs 4, 8)", "IoU 0.309 (one-stroke) vs 0.293 (two-stroke); recogniser reads 3/4 vs 0/4 "
              "as the right digit", "IoU hides legibility (exploratory)"],
             ["RQ3: PPO vs SAC (8 cells, 200k steps)", "train-family IoU SAC 0.051 vs PPO 0.292 (-0.241, 0/8 up, t = -9.71); "
              "SAC behind on all 5 eval sets", "SAC far behind at this budget (not 'PPO is better')"]],
            colw=[3.6, 6.0, 2.2], size=11.5, row_h=0.75, align="left",
            cell_colors={(0, 2): BAD, (1, 2): WARN, (2, 2): WARN, (3, 2): BAD},
            take="Wording: 'this naive curriculum did not help' - never 'curricula do not work'; digits are "
                 "motivation for a legibility metric, not a result; SAC: 'far behind at this budget', not 'PPO is better'.",
            take_color=WARN,
            notes="""
Extensions:
- RQ4 curriculum: pehle 100k steps line par, phir shape. Result: final 0.246 vs scratch 0.418 - 0.173
  KAM, 6 me se 5 cells me kharab, t=-2.99 (critical ~2.57 at df 5). Negative transfer. Wording: "yeh
  naive curriculum kaam nahi kiya" - "curricula kaam nahi karte" NAHI.
- A2 pen-free: agent ko pen uthane ka control diya. 0.329 vs 0.418, t=-2.29 - significant nahi -> "no
  detectable effect on final IoU", par learning slow. Pen sirf ~10% steps par neeche - chhote bursts me ink.
- Digits: 1 aur 7 (ek stroke) vs 4 aur 8 (do stroke). IoU almost same (0.309 vs 0.293), par recogniser ne
  ek-stroke wale 3/4 sahi padhe, do-stroke wale 0/4. Matlab IoU legibility chhupa leta hai. n=4 per group,
  koi test nahi, stroke count digit identity se confounded.
- RQ3 PPO vs SAC: SAC 0.051 vs PPO 0.292 train-family IoU, 8 me se 0 cells me aage, t=-9.71. Par SAC ko
  low update ratio (0.25) mila aur tuning nahi hui - "is budget par bahut peeche", "PPO behtar" nahi.
""", source="RESEARCH_LOG '### RQ4 curriculum RESULT', '### A2 pen-free RESULT', '### Stage 6 digits RESULT', "
            "'### RQ3 PPO vs SAC RESULT'; docs/PAPER_PLAN.md C9-C12")

    figure(prs, "09 · extensions", "Digit targets (Stage 6) and why IoU is not enough for glyphs",
           "The project's own stroke skeletons for digits 0-9 (rl/glyphs.py); 4, 8 and 9 need a pen lift.",
           "glyph_sheet.png",
           ["An in-house CNN recogniser with a 'reject' class (blank, scribbles, shapes) judges legibility: "
            "legible = top-1 is the target AND P(target) ≥ 0.5.",
            "Calibration showed IoU and legibility dissociate: a 60-px shift (IoU 0.047) is still read; cutting "
            "20% of each stroke (IoU 0.675) halves P(target).",
            "Limits: recogniser trained on my own synthetic data; no human rating; n = 4 per group."],
           fig_w=6.4, start=15, take="Next metric for letters/writing: legibility next to IoU.", take_color=VIOLET,
           notes="""
Stage 6 ke liye digits ke target banaye (glyphs.py) - 4, 8, 9 ke liye pen uthana padta hai.

Legibility ke liye ek chhota CNN recogniser (reject class ke saath - pehle version ne scribble ko '8' padh
liya tha P=1.00 se!). Rule: top-1 sahi aur P(target) >= 0.5.

Calibration se dikha IoU aur legibility alag cheezen hain: poora digit 60 px khiska (IoU 0.047) - phir bhi
padha jaata hai; har stroke ka 20% kaato (IoU 0.675) - P(target) aadha ho jaata hai. Isliye letters/
writing ke liye IoU ke saath legibility metric chahiye.

Limits: recogniser hamare apne synthetic data par trained, koi human rating nahi.
""", source="RESEARCH_LOG '## 2026-11-06 - Stage 6 step 2a' and '## 2026-11-06 - Stage 6 step 2b' (v2 calibration); "
            "'### Stage 6 digits RESULT'")

    grid(prs, "09 · negative results", "Negative results - reported plainly", "A negative result is a result (AGENTS.md rule 7).",
         [("CAMERA RANDOMISATION", ["Bought nothing (held-out -0.011, t = -0.67) - because the fixed camera already transferred."], BAD),
          ("H4 v1 AND H4-SHORT", ["Two pre-registered nulls; even the privileged arm did not recover."], BAD),
          ("CURRICULUM", ["Line-first made things worse: 0.246 vs 0.418 (t = -2.99)."], BAD),
          ("CHUNKING, BC, COORDCONV, 3× STEPS", ["No held-out gain; chunking hurt in-distribution (-0.189); PPO unlearned the BC start."], BAD),
          ("WRONG PREDICTIONS", ["O1 would cut the overshoot (no); camera wins most on paper shift in v1 (no); "
                                 "plateau stop is a fix (cannot separate from a short horizon)."], WARN),
          ("SAC FAR BEHIND", ["0.051 vs PPO 0.292 train-family IoU (t = -9.71, 0/8) - at a low update ratio, one setting."], BAD),
          ("MISSED", ["Ink failure never big enough to test; held-out camera missed "
                      "its intended range (0.394 vs 0.45-0.60) - reported as measured."], WARN)],
         cols=3, take="Interview line: 'I report what I measured, including what did not work - with the same numbers and tests.'",
         take_color=VIOLET,
         notes="""
Negative results - inhe chhupana nahi, garv se batana hai:
- Camera randomisation: kuch nahi diya.
- H4 v1 aur H4-short: do nulls.
- Curriculum: nuksaan.
- Chunking, BC warm start, CoordConv, 3x steps: held-out par koi fayda nahi; chunking ne nuksaan kiya; PPO ne
  BC ki achhi shuruaat "unlearn" kar di.
- Galat predictions: O1 overshoot kam karega (nahi); v1 me camera paper shift par sabse zyada jeetega (nahi);
  plateau stop ek fix hai (short horizon se alag nahi kar sake).
- SAC: 0.051 vs PPO 0.292 - bahut peeche (par low update ratio, koi tuning nahi).
- Missed: ink failure kabhi itna bada nahi ki test ho; held-out camera apne target range se bahar
  - jo mila woh report kiya.

Interview me yeh slide aapki credibility banati hai.
""", source="RESEARCH_LOG RESULT entries (STAGE 2, H4, H4-SHORT, RQ4, A1, T1, O3, Generalisation part 2, O1, C5 4th arm, "
            "RQ3 RESULT, Calibration)")
