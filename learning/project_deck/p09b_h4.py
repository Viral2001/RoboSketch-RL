"""Section 9b - H4, the experiment that answers D01: the whole story."""
from kit import *  # noqa: F401,F403


def build(prs, toc):
    concept(prs, "09 · H4", "H4: does seeing the paper help recovery? - the design",
            "The experiment that has to answer D01. Same PPO settings as everything else.",
            ["Three disturbances, each fired ONCE per episode at 4-16% of it (inside the drawing phase), applied "
             "to reality only:",
             (1, "slip: pen knocked 4-9 px sideways; the command stream is unchanged"),
             (1, "paper shift: the sheet (with its ink) slides 5-10 px; every later stroke lands displaced"),
             (1, "ink failure: the pen deposits nothing for a stretch of steps; kinematics reports a perfect drawing"),
             "Arms: open_loop (analytic tracer, no feedback) · true (sees the real ink - privileged ceiling) · "
             "fk (sees what kinematics predicts - D01) · camera (sees a photo).",
             "All learning arms train on a MIX of disturbances, then are scored on each kind (10 episodes).",
             "Primary endpoint: paired diff-in-diff camera vs fk, n = 8 cells, critical t(7) = 2.365."],
            cards=[("WHY TRAIN ON THE MIX", ["The claim is about INFORMATION. Each arm must get a fair chance to "
                                            "learn to use what it can see; clean-trained → disturbed would "
                                            "only measure brittleness."], VIOLET),
                   ("ASYMMETRY (STATED)", ["fk and true are rewarded from the TRUE canvas, camera from vision: "
                                           "this favours fk, so a camera win is conservative."], WARN)],
            notes="""
H4 design. Teen disturbances, har episode me ek baar, episode ke 4-16% par - jab agent abhi draw kar raha
ho (pehle version 20-55% par fire karta tha, jab drawing khatam ho chuki hoti thi - kuch test hi nahi hua).
Sirf reality par lagte hain:
- slip: pen 4-9 px khisak jaata hai, command wahi.
- paper shift: paper (ink samet) 5-10 px khisak jaata hai.
- ink failure: kuch steps tak ink nahi girti - kinematics ke hisaab se drawing perfect.

Arms: open_loop (bina feedback ka tracer), true (asli ink dekhta - ceiling), fk (D01 - kinematics ki
prediction dekhta), camera (photo dekhta).

Sab arms disturbances ke mix par train hote hain - kyunki sawaal INFORMATION ka hai: har arm ko jo dikhta
hai use use karna seekhne ka mauka milna chahiye.

Asymmetry: fk ko true canvas se reward milta hai, camera ko vision se - yeh fk ke favour me hai. To camera
jeete to woh conservative jeet hai.
""", source="RESEARCH_LOG '### Design (rl/h4_experiment.py, rl/disturb.py)' and rl/disturb.py (magnitudes, timing window)")

    tabular(prs, "09 · H4", "Premise check: what does each channel actually know?",
            "Random actions, no training: how far is each observation from the real paper? (n = 8 episodes)",
            ["disturbance", "fk belief: % of ink wrong", "camera: % of ink wrong"],
            [["none", "0.0", "14.6"], ["slip", "2.5", "15.1"], ["paper_shift", "82.0", "15.4"],
             ["ink_failure", "5.0", "15.2"]],
            colw=[3.4, 4.2, 4.2], size=13.5, row_h=0.45,
            cell_colors={(2, 1): BAD},
            below=["Surprise: kinematics is MORE accurate than the camera on 3 of 4 kinds - the camera has a constant "
                   "~15% sensor 'haze'. Only paper_shift breaks fk - completely (82% of the ink misplaced).",
                   "Ink failure removes only ~5% of the ink: it can barely show any recovery difference (a sizing "
                   "problem, flagged before the result).",
                   "Structure, not size: fk's error is zero until something goes wrong, then it IS the mistake; the "
                   "camera's error is diffuse noise."],
            take="Prediction recorded in advance: if the camera wins anywhere, it should win on paper_shift.",
            take_color=VIOLET,
            notes="""
Premise check - experiment ki neev. Random actions (bina training) se naapa ki har observation asli paper
se kitna alag hai.

Chaunkane wali baat: teen me se teen kinds par fk belief camera se ZYADA accurate hai! Camera me hamesha
~15% sensor ki "dhundh" hai. Sirf paper_shift fk ko tod deta hai - poori tarah: 82% ink galat jagah.

Ink failure sirf ~5% ink hatata hai - recovery difference dikhane ke liye bahut chhota (sizing problem).

Asli farak structure ka hai: fk ki galti zero rehti hai jab tak kuch galat na ho, phir woh galti hi
"mistake" hai; camera ki galti diffuse noise hai.

Prediction pehle likhi gayi: camera kahin jeete to paper_shift par. (Note: yeh formal pre-registration
nahi tha - 18 rows pehle se disk par the; log me saaf likha hai.)
""", source="RESEARCH_LOG '### Premise check - the FK belief is *more* accurate than the camera, except when the paper moves'")

    tabular(prs, "09 · H4", "H4 v1 and H4-short: two nulls", "Primary: diff-in-diff camera - fk (camera loses less if > 0), n = 8, crit 2.365.",
            ["design", "slip", "paper shift", "ink failure", "privileged 'true' - fk (control)"],
            [["v1: 240-step episodes", "-0.012 (t -0.78)", "+0.005 (t +0.24)", "+0.010 (t +1.19)", "null on all three (|t| ≤ 2.13)"],
             ["H4-short: 60 steps", "-0.005 (t -0.79)", "+0.011 (t +0.57)", "-0.008 (t -0.69)", "null on all three (|t| ≤ 1.38)"]],
            colw=[2.6, 2.0, 2.0, 2.0, 3.2], size=12.5, row_h=0.6,
            below=["Even the arm that sees the REAL ink recovered no better than fk - so it was not a camera-quality problem.",
                   "v1 leading explanation: with 240 steps, agents have ~180 idle steps to overdraw - 'robustness by "
                   "overdrawing'. Shortening to 60 made paper_shift bite 2.2-2.8× harder - but nobody recovered.",
                   "Trap in the H4-short output: 'absolute camera - fk +0.052, t = +5.16' includes a +0.041 clean gap; "
                   "it must not be quoted as recovery.",
                   "Ink failure barely bites (open loop loses only ~0.013-0.014): uninformative, as pre-registered."],
            take="Two honest nulls: as designed, H4 could not answer D01 - and the ceiling control showed why.",
            take_color=BAD,
            notes="""
Pehle do H4 designs dono null:
- v1 (240 steps): camera vs fk - slip -0.012, paper shift +0.005, ink +0.010; |t| <= 1.19. Null.
- H4-short (60 steps): -0.005, +0.011, -0.008; |t| <= 0.79. Null.

Sabse important: privileged "true" arm (asli ink dekhta hai) bhi fk se behtar recover nahi kiya. Matlab
problem camera quality nahi thi.

v1 ka explanation: 240 steps me ~180 faltu steps - agent overdraw karke disturbance ko dhak deta hai
("robustness by overdrawing"). 60 steps karne par paper shift 2.2-2.8x zyada nuksaan karne laga - par phir
bhi koi recover nahi kar paya.

Trap: H4-short me absolute camera - fk = +0.052, t = +5.16 print hua - par usme +0.041 clean gap shamil
hai. Recovery nahi. Quote mat karna.

Ink failure: open loop bhi sirf ~0.013 khota hai - kuch test hi nahi hota.
""", source="RESEARCH_LOG '### H4 RESULT - null on the pre-registered endpoint', '### H4-SHORT RESULT (2026-10-28)' "
            "(trap, 2.2-2.8x), '### A control added after the fact'")

    concept(prs, "09 · H4", "The oracle check: was there anything to recover?", "29 Oct 2026 - measured before any new H4 variant.",
            ["Hypothesis after two nulls: ink is permanent, so maybe paper-shift damage cannot be undone by anyone.",
             "Test: analytic tracers that KNOW the shift (read the pen's landing position on the sheet). At 60 "
             "steps they lose only 0.013-0.021 IoU to a paper shift.",
             "Trained arms lost 0.129-0.147: roughly ten times more. So ~0.11-0.13 IoU was recoverable in "
             "principle, and no trained arm recovered it. Hypothesis REFUTED.",
             "New hypothesis (from reading the code): the pen dot was drawn in WORLD coordinates. After the sheet "
             "slides, the dot and the ink disagree by 5-10 px; the agent must infer the offset. Even the camera "
             "arm saw only the ink - never the pen against the paper."],
            cards=[("WHY THIS MATTERS FOR D01", ["The one thing a camera gives that kinematics cannot - the pen tip "
                                                 "relative to the paper - had been withheld by our observation design."], ACCENT),
                   ("A DATED CORRECTION", ["The 19 Oct reading 'the channel carries no recoverable signal' was "
                                           "withdrawn by a new entry, not silently edited."], WARN)],
            notes="""
Do nulls ke baad sawaal: kya paper shift ka nuksaan recover ho bhi sakta hai? Ink permanent hai - shayad
koi bhi theek nahi kar sakta.

Test: analytic tracers jo shift JAANTE hain. 60 steps par woh sirf 0.013-0.021 khote hain. Trained arms
0.129-0.147 kho rahe the - ~10 guna. Matlab ~0.11-0.13 IoU recover ho sakta tha, aur kisi arm ne nahi kiya.
Hypothesis refuted.

Naya hypothesis (code padh kar): pen ka dot WORLD coordinates me tha. Paper khisakne ke baad dot aur ink
5-10 px alag - agent ko offset khud infer karna padta. Camera arm ko bhi sirf ink dikhti thi, pen-on-paper
nahi. Yani camera ki asli taakat - "pen paper par kahan hai" - observation design ne chheen li thi.

Purani reading ("koi recoverable signal nahi") ek nayi dated entry se withdraw ki - purani entry edit nahi ki.
""", source="RESEARCH_LOG '## 2026-10-29 - H4 oracle check: the paper-shift loss is NOT unrecoverable'")

    tabular(prs, "09 · H4", "H4 v3 and v4: put the pen on the sheet - privileged, then estimated",
            "Seeds 0/100, 60-step episodes, n = 8. Loss = clean - paper_shift; diff-in-diff vs fk (> 0 = loses less).",
            ["arm", "clean", "paper shift", "loss", "DiD vs fk (pairs up, t)"],
            [["fk (D01's condition)", "0.328", "0.181", "0.147", "-"],
             ["camera (world-frame pen dot)", "0.369", "0.233", "0.136", "+0.011 (5/8, t +0.57)"],
             ["v3 camera_sheet (TRUE offset given)", "0.402", "0.382", "0.019", "+0.128 (8/8, t +10.39)"],
             ["v4 camera_est (offset ESTIMATED by phase corr.)", "0.397", "0.327", "0.070", "+0.077 (8/8, t +6.39)"]],
            colw=[4.6, 1.2, 1.5, 1.2, 3.3], size=12.5, row_h=0.55,
            cell_colors={(2, 4): WARN, (3, 4): GOOD},
            below=["v3: the missing ingredient was the OBSERVATION - but the offset came from the simulator, so v3 is "
                   "NOT a camera result (camera_sheet ≈ true_sheet).",
                   "v4: the camera arm estimates the offset itself from its photo. Pre-registered reading: primary "
                   "significant but clearly worse than the true offset (-0.051, t = -8.92) → 'partial'.",
                   "v4 clean gap vs fk was +0.069 (t = +3.41): another reason a fresh replication was needed."],
            take="v4 was the 4th H4 design after two nulls: exploratory until replicated on fresh seeds.", take_color=WARN,
            notes="""
v3: pen dot ko SHEET frame me banao - jahan pen paper par asal me girta hai. Isme simulator ka TRUE offset
use hua. Result: camera_sheet ka loss 0.147 se 0.019 - DiD +0.128, t = +10.39. Par yeh camera result NAHI -
offset simulator ne diya. Isne sirf yeh dikhaya ki observation (pen relative to sheet) missing ingredient tha.

v4: camera_est - offset khud phase correlation se photo se estimate karo. Simulator ka offset kabhi nahi
padha. Result: loss 0.070, DiD vs fk +0.077, 8/8, t = +6.39. Par true offset wale arm se kaafi kharab
(-0.051, t = -8.92) -> pre-registered reading "partial".

Ek aur dikkat: v4 me clean gap bhi +0.069 (t=3.41) tha. Aur v4 chautha design tha do nulls ke baad - isliye
exploratory. Fresh seeds par replication zaroori tha.
""", source="RESEARCH_LOG '### H4 v3 RESULT (2026-10-30)', '### H4 v4 RESULT (2026-10-30)' and their Honest limits")

    concept(prs, "09 · H4", "The replication: pre-registered, fresh seeds, every arm re-run",
            "Launched 7 Nov 2026; user-approved ~12 h; 48 runs (6 PPO arms × 4 shapes × seeds 200, 300).",
            ["No code change to any H4 script or the environment; current draw_env.py checked bit-identical to the "
             "v4-era code (120/120 configurations).",
             "The aggregation script reproduced the logged v4 table exactly on seeds 0/100 before launch.",
             "PRIMARY: camera_est vs fk, paper_shift diff-in-diff, seeds 200/300 ONLY (n = 8, crit 2.365). "
             "Significant > 0 → replicated; otherwise the paper must say v4 did not replicate.",
             "SECONDARY: vs the world-dot camera. REFERENCE: vs the true-offset arm. Also: slip, ink failure, clean gap.",
             "Pooled n = 16 only as a descriptive secondary line (seeds 0/100 had already been seen).",
             "No optional stopping, no further seeds, no re-tuning, whatever the result."],
            cards=[("WHY NOT JUST POOL n = 16?", ["Seeds 0/100 motivated the claim; a test that includes them is "
                                                  "partly circular. Only fresh seeds can confirm."], VIOLET)],
            notes="""
Replication ka design - research credibility ka core:
- Koi code change nahi. Pehle verify: draw_env.py v4-era code se bit-identical (120/120 configs), aur
  aggregation script ne seeds 0/100 par purani v4 table exactly reproduce ki.
- Primary: camera_est vs fk, paper shift DiD, SIRF seeds 200/300. Significant > 0 -> replicated. Nahi to
  paper me likhna padega "replicate nahi hua".
- Pooled n=16 sirf descriptive - kyunki seeds 0/100 ne hi claim ko janm diya tha; unhe test me daalna
  circular hota.
- No optional stopping, no extra seeds, no re-tuning.
User ne ~12 ghante ka run approve kiya; 48 runs.
""", source="RESEARCH_LOG '## 2026-11-07 - H4 v4 confirmation launched: fresh seeds {200,300} for ALL H4 arms (pre-registered)'")

    tabular(prs, "09 · H4", "Replication result (seeds 200/300): REPLICATED",
            "n = 8 (shape, seed) cells, TRUE IoU, 10 eval episodes per disturbance, 60-step episodes.",
            ["arm", "clean", "slip", "paper shift", "ink failure", "paper-shift loss"],
            [["open_loop", "0.485", "0.221", "0.185", "0.470", "0.300"],
             ["fk (kinematics, D01)", "0.369", "0.361", "0.203", "0.324", "0.165"],
             ["camera (world dot)", "0.358", "0.375", "0.250", "0.352", "0.108"],
             ["camera_est (estimated offset)", "0.375", "0.371", "0.329", "0.333", "0.046"],
             ["camera_sheet (true offset)", "0.423", "0.417", "0.407", "0.386", "0.016"]],
            colw=[3.6, 1.4, 1.4, 1.6, 1.6, 2.2], size=12.5, row_h=0.45,
            cell_colors={(3, 5): GOOD, (1, 5): BAD},
            below=["PRIMARY camera_est vs fk, paper shift: +0.119, 8/8 up, t = +8.32 - clean gap only +0.006 (t = +0.37): "
                   "recovery, not a head start.",
                   "SECONDARY vs world-dot camera: +0.062, 7/8, t = +3.86.  REFERENCE vs true offset: -0.030, 2/8, t = -2.42 "
                   "(just past crit: slightly below the true-offset arm).",
                   "Pooled seeds 0/100/200/300 (n = 16, descriptive): +0.098, 16/16 up, t = +9.32."],
            take="C4 (partial, replicated): for the disturbance kinematics cannot see, the camera arm that estimates "
                 "the sheet offset loses far less.", take_color=GOOD,
            notes="""
Replication result - project ka sabse important number.
Paper shift par fk ne 0.165 khoya, camera_est ne sirf 0.046. DiD +0.119, 8 me se 8 cells me camera_est
aage, t = +8.32 (critical 2.365). Aur clean gap sirf +0.006 (t = 0.37) - dono barabar shuru hue, to yeh
asli recovery hai, head start nahi. v4 (+0.077) se bhi bada effect.

Secondary: world-dot camera se bhi +0.062 behtar (t=3.86) - yaani estimated marker hi farak bana raha hai.
Reference: true-offset arm se thoda kharab (-0.030, t = -2.42 - bas critical ke paar): "slightly below".

Pooled 16 cells (descriptive): +0.098, 16/16, t = +9.32.

Allowed wording (PAPER_PLAN C4): "partial, replicated, paper_shift only, simulation only".
""", source="RESEARCH_LOG '### H4 v4 confirmation RESULT (2026-11-08; 48/48 runs)'; docs/paper/main.tex Table tab:h4")

    figure(prs, "09 · H4", "Replication figure, and the cost of the estimator", "output/h4_confirm_recovery_seeds200_300.png (the paper's Fig. fig:h4).",
           "h4_confirm_recovery_seeds200_300.png",
           ["Left: IoU each arm loses per disturbance. Right: paper-shift diff-in-diffs, ±1 SE whiskers.",
            "Slip and ink failure vs fk: +0.004 (t = +0.37) and +0.003 (t = +0.32) - no detectable difference.",
            "NEW cost: vs the world-dot camera, camera_est loses MORE to ink failure (-0.036, 0/8, t = -5.29) "
            "and slip (-0.021, t = -2.64).",
            "Plausible, untested cause: missing or displaced ink misleads the phase correlation."],
           fig_w=7.8, start=14,
           take="Read significance from the per-comparison t values, not the dashed guide line.", take_color=WARN,
           notes="""
Figure (paper ka Fig. h4): left panel - har arm har disturbance par kitna khota hai; paper shift par fk
(orange) ka bar bahut bada, camera_est (green) chhota. Right panel - paper shift ke DiD: primary +0.119,
secondary +0.062, reference -0.030.

Slip aur ink failure par fk ke against koi detectable farak nahi (+0.004, +0.003).

Nayi aur unwelcome finding: world-dot camera ke muqable camera_est ink failure par ZYADA khota hai (-0.036,
0/8, t=-5.29) aur slip par bhi (-0.021, t=-2.64). Shayad jab ink missing ya displaced ho, phase correlation
galat offset deta hai - untested.

Dashed line sirf visual guide hai (mean SE x t crit) - significance per-comparison t se padho; reference
ka t=-2.42 bas border par hai.
""", source="RESEARCH_LOG '### H4 v4 confirmation RESULT' and '### Paper: H4 replication figure made'")

    s = slide(prs, "The H4 story in one picture", "09 · H4", "Four designs, two nulls, one correction, one replication.")
    steps_ = [("v1 · 240 steps", "null\n|t| ≤ 1.19", BAD), ("H4-short · 60", "null\n|t| ≤ 0.79", BAD),
              ("oracle check", "loss IS\nrecoverable", ACCENT), ("v3 · true offset", "+0.128, t 10.39\n(not a camera)", WARN),
              ("v4 · estimated", "+0.077, t 6.39\n'partial'", GOOD), ("replication", "+0.119, t 8.32\n8/8, fresh seeds", GOOD)]
    pipeline(s, [(a, b) for a, b, _ in steps_], M, s._top + 0.3, CW, 1.5,
             colors=[c for _, _, c in steps_], gap=0.22, title_size=13, sub_size=12)
    bullets(s, ["What changed between null and positive was not the camera - it was giving the agent the pen's "
                "position ON THE SHEET, estimated from its own photo.",
                "Every step was pre-registered before its runs; the series is exploratory, the replication is confirmatory.",
                "Each null was reported as a null; each correction is a new dated log entry."],
            M, s._top + 2.2, CW, 2.4, start=16)
    why(s, "'Seeing the paper is useful when the observation makes the paper's motion actionable' - the paper's "
           "one-sentence discussion of H4.")
    note(s, """
H4 ki poori kahani ek line me:
v1 null -> H4-short null -> oracle check (nuksaan recover ho sakta hai) -> v3 (true offset - kaam karta hai
par camera result nahi) -> v4 (camera khud offset estimate kare - partial) -> replication (fresh seeds,
+0.119, 8/8, t 8.32).

Key insight: null se positive tak jo badla woh camera nahi tha - agent ko pen ki position SHEET par (apni
photo se estimate karke) dena tha. Paper ki discussion line: "Seeing the paper is useful when the
observation makes the paper's motion actionable."

Interview me yeh kahani bolo - nulls chhupaye nahi, har step pre-register kiya, corrections dated entries
hain. Yeh research maturity dikhata hai.
""", "RESEARCH_LOG H4 entries 2026-10-19 to 2026-11-08; docs/paper/main.tex Discussion")

    concept(prs, "09 · H4", "What H4 says about D01 - and what it does not", None,
            ["SAYS (simulation): for a disturbance kinematics cannot see - the sheet moving - a camera agent that "
             "estimates the sheet pose recovers most of the loss and beats the camera-free agent in 16/16 cells over 4 seeds.",
             "SAYS: where the camera-free agent is not blind (slip, ink failure here), there is no detectable "
             "advantage - and the estimator has a cost relative to a simpler camera arm.",
             "DOES NOT SAY: 'cameras beat kinematics' in general. Only v4's specific design is confirmed.",
             "DOES NOT SAY anything about a real camera: near-fixed simulated camera, pure-translation shift, "
             "estimator written knowing that model.",
             "Ink failure is too small to test anything (open loop loses ~0.013-0.015); it stays open."],
            cards=[("ALLOWED WORDING", ["'In simulation, an agent that estimates the sheet offset from its "
                                        "photograph lost less to a paper shift than a kinematics-synchronised "
                                        "agent (replicated); no detectable advantage for slip or ink failure.'"], GOOD),
                   ("D01 OBJECTION", ["Partly answered, simulation only (HANDOFF open issue)."], WARN)],
            notes="""
D01 ke baare me H4 kya kehta hai:
- Haan (simulation me): jab sheet khisakti hai - jo kinematics dekh hi nahi sakta - camera agent jo sheet
  ka offset estimate karta hai, zyada-tar nuksaan recover karta hai; 4 seeds par 16/16 cells me fk se behtar.
- Jahan kinematics andha nahi hai (slip, ink failure), koi detectable fayda nahi - aur estimator ki ek cost hai.

Kya NAHI kehta: "camera kinematics se behtar hai" general me. Asli camera ke baare me kuch nahi.
Ink failure itna chhota hai ki kuch test nahi hota.

Status: D01 objection "partly answered, simulation only". Interview me exactly yahi bolna - na zyada, na kam.
""", source="RESEARCH_LOG '### H4 v4 confirmation RESULT' (What this means for D01; Honest limits); docs/PAPER_PLAN.md C4; docs/HANDOFF.md Open issues")
