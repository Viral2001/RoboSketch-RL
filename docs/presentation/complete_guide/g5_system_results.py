"""Part 5 - system design (simulator, DrawEnv, reward) and the experimental journey H1 → Stage 2."""
from gk import (ACCENT, BAD, BODY, CW, GOOD, INK, LINE, M, MUTED, PRIMARY, SLATE, VIOLET,
                WARN, WASH, WHITE, arrow, bullets, card, chip, concept, figure, grid, node,
                note, pic, pipeline, rect, section, slide, steps, strip, tabular, txt, analogy, img)
from deck_kit import decision_slide
from pptx.enum.shapes import MSO_SHAPE


# =========================================================== SYSTEM DESIGN ===
def system(prs):
    section(prs, 7, "System design",
            "How the pieces fit: a validated simulator, a Gymnasium environment, a reward "
            "designed by measuring failures, and an experiment harness built to be hard to fool.",
            ["Architecture & code map", "Simulator milestones B1–B6", "DrawEnv in detail",
             "The reward function & its maths", "Reward-design iterations",
             "Experiment infrastructure"])

    s = slide(prs, "Architecture: five layers, one direction of data", "07 · architecture",
              "Each layer only depends on the one below it — so a change can be tested in isolation.")
    layers = [("SIMULATOR", "sim/ · PyBullet · KUKA arm\nIK · ink · virtual camera", PRIMARY),
              ("ENVIRONMENT", "rl/draw_env.py · Gymnasium\nobs · action · reward · episode", VIOLET),
              ("LEARNER", "Stable-Baselines3 PPO\nCnnPolicy · 8 parallel envs", VIOLET),
              ("EXPERIMENTS", "rl/*_experiment.py\nresumable sweeps → results/*.jsonl", ACCENT),
              ("ANALYSIS & RECORD", "--aggregate · paired tests\ndocs/RESEARCH_LOG.md", GOOD)]
    pipeline(s, layers and [(t, sb) for t, sb, _ in layers], M, 1.85, CW, 1.45,
             colors=[c for _, _, c in layers], gap=0.32, sub_size=9.5, title_size=12)
    grid_y = 3.65
    cards = [("PERCEPTION", "rl/perception.py (camera model + domain randomisation), "
                            "rl/camera.py (real render).", ACCENT),
             ("TARGETS & METRICS", "rl/targets.py (line, circle, square, triangle), "
                                   "rl/metrics.py (IoU, SNR, path_ratio, …).", PRIMARY),
             ("DISTURBANCES", "rl/disturb.py — slip, paper shift, ink failure (H4).", WARN),
             ("VIEWER", "rl/watch.py + watch.bat — watch a trained agent draw, live, with "
                        "true vs camera views.", SLATE)]
    w = (CW - 3 * 0.16) / 4
    for i, (t, b, c) in enumerate(cards):
        card(s, M + i * (w + 0.16), grid_y, w, 1.95, t, [b], accent=c, body_size=11)
    strip(s, "Design rule: every behavioural change is a flag whose default is the OLD behaviour, "
          "so no recorded number can silently move.", GOOD, y=5.85)
    note(s, """
System paanch layers me hai, aur data ek hi direction me jaata hai. Sabse neeche simulator
(PyBullet, KUKA arm, IK, ink, camera). Uske upar environment (DrawEnv — observation, action,
reward). Uske upar learner (PPO). Phir experiment scripts jo resumable sweeps chalati hain aur
results JSONL files me likhti hain. Sabse upar analysis aur research log.

Saath me perception module (camera model), targets aur metrics, disturbances (H4), aur viewer
(trained agent ko live draw karte dekhna).

Ek zaroori niyam: har naya behaviour ek flag hai jiska default purana behaviour hai. Isse koi bhi
purana number chupke se nahi badal sakta.
""")

    tabular(prs, "07 · simulator", "Building the simulator: milestones B1 – B6",
            "Phase B, completed in two days (23–24 Jul 2026) — every milestone verified by measurement.",
            ["#", "milestone", "result", "the problem that had to be solved"],
            [["B1–B3", "load arm + paper; joint sliders; live pen-tip readout", "done",
              "link index [0] = centre of mass, not the frame → ~20 mm phantom error"],
             ["B4", "inverse kinematics: aim the pen at (x, y)", "worst error 0.108 mm",
              "pen tilt, unreachable zone, wrist hitting the floor (virtual 10 cm pen)"],
             ["B5", "the pen leaves a mark", "line + square geometry verified",
              "debug lines invisible to cameras; box faces don't map textures; world→pixel was transposed"],
             ["B6", "the robot sees its own drawing", "camera IoU 0.871 / 0.882",
              "arm occludes the paper; Otsu fooled; texture cached by filename"],
             ["+", "interactive drawing sandbox (sim/05)", "draw by hand with sliders",
              "user feedback: the viewport moved, not the arm"]],
            colw=[0.8, 3.6, 2.3, 5.5], size=10.5, row_h=0.55,
            cell_colors={(1, 2): GOOD, (2, 2): GOOD, (3, 2): GOOD},
            below=["Motor tracking lag is real dynamics, not error: while drawing continuously the "
                   "pen trails its target by up to 2.8 mm (line) / 4.8 mm (square) — rounded "
                   "corners. Ink is laid where the pen ACTUALLY is."],
            take="Phase B lesson: a bug that looks fine on screen can silently corrupt every "
                 "reward later — so everything was checked against physics.", take_color=WARN,
            notes="""
Simulator do din me bana (23–24 July), aur har milestone measurement se verify hua. B1–B3: arm,
paper, sliders — aur galat index wala 20 mm ka bug. B4: IK, sabse badi galti 0.108 mm. B5: pen
nishan chhodta hai — debug lines camera ko nahi dikhti, box texture map nahi karta, aur world se
pixel mapping ulti thi (drawing mirror ho jaati!). B6: camera — arm paper dhak raha tha, Otsu fail,
texture cache bug.

Motor lag asli dynamics hai: continuous drawing me pen apne target se 2.8–4.8 mm peeche rehta hai —
square ke kone gol ho jaate hain. Ink wahin girti hai jahan pen sach me hai.
""")

    grid(prs, "07 · simulator · B5", "B5 — four findings before the pen could leave a usable mark",
         "Each one would have silently corrupted the vision pipeline later.",
         [("1 · DEBUG LINES ARE INVISIBLE", ["addUserDebugLine is a viewer overlay: a stroke drawn "
                                             "that way changed 0 pixels in a camera image. Ink must "
                                             "be real scene content."], BAD),
          ("2 · BOXES DON'T MAP TEXTURES", ["A 4-colour test texture rendered as one flat colour on "
                                            "a box face. Fix: the paper is a mesh quad with "
                                            "explicit UVs — all four quadrants then render ~25% each."], WARN),
          ("3 · changeTexture IS A NO-OP", ["Measured 0/4 on every probe. Reloading the texture "
                                            "from a PNG works 4/4 — so the paper refreshes from "
                                            "disk every 20 points."], WARN),
          ("4 · THE MAPPING WAS TRANSPOSED", ["col = (x − x_min)/width·(RES−1);  "
                                              "row = (y_max − y)/height·(RES−1).",
                                              "Verified against physics within ~3 px. Unchecked, "
                                              "every drawing would have been scored mirrored."], BAD)],
         cols=2,
         take="Architecture that followed: the numpy canvas is the authoritative drawing; the "
              "textured paper is only its picture.", take_color=PRIMARY,
         notes="""
B5 me chaar cheezen pakdi. (1) Debug lines sirf screen par dikhti hain, camera ko nahi — ink
asli scene ka hissa honi chahiye. (2) Box par texture sahi map nahi hota — paper ko mesh banaya.
(3) changeTexture kaam hi nahi karta — PNG se reload karna padta hai. (4) Pixel mapping ulti thi —
bina pakde har drawing mirror ho kar score hoti.

Isse architecture tay hua: numpy canvas asli drawing hai, 3D paper uski sirf tasveer.
""")

    s = slide(prs, "DrawEnv — the environment, in detail", "07 · environment",
              "rl/draw_env.py: the file every recorded number depends on.")
    chans = [("ch 0", "TARGET", "the shape to reproduce", PRIMARY),
             ("ch 1", "DRAWN", "ink so far — true, FK belief or camera photo", ACCENT),
             ("ch 2", "PEN", "a marker at the pen", VIOLET),
             ("ch 3", "TIME", "elapsed fraction (O1 only)", SLATE)]
    txt(s, M, 1.55, 6.0, 0.3, "OBSERVATION — 64 × 64 image, one channel per idea", size=12,
        color=INK, bold=True)
    for i, (c, t, d, col) in enumerate(chans):
        y = 1.95 + i * 0.78
        chip(s, M, y + 0.14, 0.75, 0.36, c, color=col, size=10)
        txt(s, M + 0.9, y + 0.05, 1.5, 0.3, t, size=12.5, color=col, bold=True)
        txt(s, M + 2.4, y + 0.08, 3.7, 0.6, d, size=11, color=BODY)
    card(s, M + 6.35, 1.55, CW - 6.35, 1.55, "ACTION — [dx, dy, pen_down]",
         ["dx, dy in [−1, 1] × 1.4 cm per step, clamped to the sheet.",
          "pen_down kept on for the first rung (pen_always_down) — the agent just traces."],
         accent=VIOLET, body_size=11.5)
    card(s, M + 6.35, 3.22, CW - 6.35, 1.45, "EPISODE",
         ["Starts with the pen on the target pixel nearest the sheet centre (deterministic).",
          "Lasts 240 steps; ends early only at reward-IoU ≥ 0.60 (never reached)."],
         accent=PRIMARY, body_size=11.5)
    card(s, M + 6.35, 4.79, CW - 6.35, 1.45, "INFO (logged every step, never seen by the agent)",
         ["true IoU · reward IoU · their gap · peak IoU · overshoot · path_ratio · SNR · coverage"],
         accent=GOOD, body_size=11.5)
    card(s, M, 5.15, 6.1, 1.09, "SWITCHES (all default OFF = original behaviour)",
         ["reward_mode · obs_source · cam_split · disturbance · time_in_obs · plateau_patience · "
          "allow_stop · use_arm"], accent=SLATE, body_size=10.5)
    strip(s, "Whatever the agent sees, info['iou'] is always the TRUE IoU — the only number "
          "any result is scored on.", GOOD)
    note(s, """
DrawEnv hamara environment hai. Observation 64x64 image ke channels: target, ab tak ki ink (asli,
FK ka andaaza, ya camera photo — experiment ke hisaab se), pen ka nishan, aur O1 me samay.

Action: dx, dy (1.4 cm per step tak) aur pen_down; pehle task me pen hamesha neeche.
Episode: pen target ke us pixel par shuru hota hai jo paper ke centre ke sabse paas hai; 240 steps.
Success bonus 0.60 IoU par milta — par koi agent kabhi wahan tak nahi pahuncha.

Har step par bahut kuch log hota hai jo agent nahi dekhta: true IoU, reward IoU, gap, peak,
overshoot, path_ratio. Saare naye features flags hain jinka default band hai.
""")

    steps(prs, "07 · reward", "The reward function — three terms",
          "r = 10·ΔIoU + 0.4·ΔΦ − 0.02·|Δa|      (and +2 at IoU ≥ 0.60, never reached)",
          [("accuracy", "10 · ( IoUₜ − IoUₜ₋₁ )",
            ["Reward the CHANGE in IoU. Covering target pixels raises it; stray ink lowers it, "
             "so scribbling is self-penalising. IoU comes from the true canvas (truth mode) or "
             "from the camera image (vision mode)."]),
           ("guidance", "0.4 · ( Φ(sₜ) − Φ(sₜ₋₁) ),   Φ(s) = −dist(pen, nearest target pixel)",
            ["Potential-based shaping: a dense 'warmer / colder' signal that pulls the pen "
             "towards the shape, even before any target pixel has been inked."]),
           ("smoothness", "− 0.02 · mean | aₜ − aₜ₋₁ |   (over dx, dy, pen)",
            ["Penalises jerky direction changes → straighter strokes. Scale matters: 0.15 "
             "swamped the IoU signal and the agent learned to barely move."]),
           ("scoring", "evaluation always uses TRUE IoU",
            ["Even a camera-rewarded agent is judged on the real paper."])],
          notes="""
Reward ke teen hisse. (1) Accuracy: IoU ka badlav × 10. Target cover karo to badhta hai, bahar
ink girao to ghatta hai — scribble apne aap saza paata hai. Truth mode me IoU asli canvas se,
vision mode me camera image se. (2) Guidance: "garam-thanda" signal — pen target ke jitna paas,
utna achha. Isse shuruaat me, jab abhi koi ink sahi jagah nahi giri, tab bhi disha milti hai.
(3) Smoothness: jhatke wali movement par chhota penalty. Iska size zaroori hai — 0.15 rakha to
agent ne hilna hi band kar diya; 0.02 sahi raha.

Evaluation hamesha true IoU par.
""")

    steps(prs, "07 · reward · maths", "Two properties of the reward, proved — and one caveat",
          "Why this reward measures what we care about.",
          [("telescoping", ["Σₜ₌₁..T ( IoUₜ − IoUₜ₋₁ ) = IoU_T − IoU₀ = IoU_T",
                            "(IoU₀ = 0: the sheet starts blank)"],
            ["The undiscounted sum of accuracy rewards IS the final IoU. Maximising return = "
             "maximising drawing accuracy. Cannot be gamed by stray ink."]),
           ("shaping", ["F(s, s′) = γ·Φ(s′) − Φ(s)   ⇒   Σₜ γᵗ Fₜ = γ^T Φ(s_T) − Φ(s₀)",
                        "(Ng, Harada & Russell, 1999)"],
            ["A potential difference telescopes too, so it adds a constant that does not depend "
             "on the actions in between: dense guidance that leaves the optimal policy unchanged."]),
           ("caveat", "code uses Φ(s′) − Φ(s), i.e. γ = 1 in F, while PPO discounts with γ = 0.99",
            ["Noticed while preparing this deck (not yet in the research log): the guarantee "
             "then holds only approximately — the mismatch is (1 − γ)·Φ = 0.01·Φ per step. "
             "Similarly, with γ = 0.99 the discounted return weights early IoU gains slightly more."])],
          take="Both effects are small at γ = 0.99, but a reviewer may ask; the precise statement is "
               "'approximately policy-invariant'.", take_color=WARN,
          notes="""
Reward ki do properties ka proof. (1) Telescoping: IoU ke badlav ka jod = final IoU (shuru me
paper khaali, IoU 0). Matlab reward maximise karna = drawing accuracy maximise karna.
(2) Potential-based shaping (Ng 1999): potential ka farak bhi telescope ho jaata hai, isliye
optimal policy nahi badalti.

Ek caveat jo yeh deck banate waqt dikha (research log me abhi nahi hai): Ng ki guarantee ke liye
F = gamma·Phi(s') − Phi(s) chahiye; code Phi(s') − Phi(s) use karta hai, jabki PPO gamma 0.99
se discount karta hai. To guarantee exact nahi, approximate hai — farak har step par 0.01 × Phi.
Isi tarah discounted return shuruaati IoU gains ko thoda zyada weight deta hai. Dono chhote hain,
par paper me "approximately policy-invariant" likhna sahi hoga.
""")

    tabular(prs, "07 · reward design", "Designing the reward by watching it fail",
            "First PPO runs on 'line' (300–400k steps each): every design exposed a new failure mode.",
            ["#", "reward design", "IoU (start → end)", "what the agent did instead"],
            [["0", "coverage only, pen up/down free", "→ 0", "'draw nothing' — the safe optimum"],
             ["0b", "pen always down", "→ 0 (reward rising)", "'don't move' — freeze to dodge stray penalties"],
             ["1", "coverage − stray − time", "0.06 → 0.14", "scribble a blob over the region"],
             ["2", "IoU-delta + proximity", "0.06 → 0.12", "cover the easy middle, never the ends"],
             ["3", "+ thicker target, finer control", "0.09 → 0.30", "sweep the full line, but zig-zag"],
             ["4", "+ pen width matched + smoothness 0.02", "0.08 → 0.508", "a recognisable line"]],
            colw=[0.6, 4.2, 2.4, 5.0], size=11, row_h=0.45,
            cell_colors={(5, 3): GOOD, (0, 3): BAD, (1, 3): BAD},
            below=["Trap 1 fix: dense potential-based proximity shaping + keep the pen down on the "
                   "first rung. Trap 2 fix: make coverage dominate (cover bonus 1 → 3, stray 0.5 → 0.2).",
                   "Switching coverage → IoU-delta structurally removed the scribble optimum."],
            take="Lesson (RQ4 material): on thin-stroke targets a sparse IoU reward alone is "
                 "not learnable — dense spatial shaping is needed to escape do-nothing optima.",
            take_color=VIOLET,
            notes="""
Reward ek baar me sahi nahi bana — har design ne ek nayi galti dikhayi. Pehle agent ne seekha
"kuch mat banao" (safe). Pen hamesha neeche kiya to seekha "hilo mat". Coverage reward diya to
blob scribble kiya. IoU-delta diya to sirf aasaan beech wala hissa. Target mota kiya to poori line
par zig-zag. Pen ki motai match ki aur smoothness penalty lagaya — tab ek pehchaanne layak line
bani, IoU 0.508.

Seekh: patli lines par sirf IoU reward bahut sparse hai — dense guidance (shaping) zaroori hai.
""")

    grid(prs, "07 · infrastructure", "Experiment infrastructure — built to be hard to fool",
         "Most of these exist because a specific mistake happened once.",
         [("RESUMABLE SWEEPS", ["Each finished run is appended to results/*.jsonl immediately; "
                                "a restart skips what is done. Survives the unexplained "
                                "'exit code 4' crashes."], GOOD),
          ("SEED-MAJOR, SHARDED", ["All shapes get seed 0 before any gets seed 100, so a partial "
                                   "sweep is still balanced. Two workers split by shape."], PRIMARY),
          ("CONFIG-DRIFT WARNING", ["warn_config_drift() shouts if a resumed sweep's timesteps or "
                                    "max_steps differ from the recorded runs."], WARN),
          ("ONE VARIABLE AT A TIME", ["Every ablation goes through the same train_eval code path "
                                      "as the baseline; only the flag under test differs."], VIOLET),
          ("PAIRED STATISTICS", ["Arms share seeds, so the (shape, seed) pair is the unit of "
                                 "analysis — never a pooled std (Section 10)."], ACCENT),
          ("APPEND-ONLY LOG", ["docs/RESEARCH_LOG.md: every decision with its reason. Corrections "
                               "are new dated entries, never silent rewrites."], SLATE)],
         cols=3,
         notes="""
Experiment ka dhaancha aisa banaya ki galti pakdi jaye. Har run turant file me likha jaata hai —
crash ho to restart karo, jo ho chuka woh skip. Seed-major order: pehle saari shapes ka seed 0,
phir seed 100 — taaki adhoora sweep bhi balanced rahe. Settings badal gayi to warning. Har ablation
same code path se — sirf ek flag badalta hai. Statistics paired. Aur research log append-only —
galti sudharni ho to nayi dated entry, purani chupke se nahi badalti.
""")


# ======================================================= EXPERIMENT JOURNEY ===
def journey(prs):
    section(prs, 8, "Experiments and results",
            "The project's history as a chain of questions: each result raised the next "
            "question — and several of our own predictions turned out to be wrong.",
            ["First learned drawings (H1)", "Vision vs truth reward (H2)",
             "Is the camera fooled? (H3)", "The overrun discovery (H6)",
             "O1, bugs, overshoot ablation", "Stage 2: domain randomisation"])

    tabular(prs, "08 · timeline", "The timeline, July → October 2026",
            "Dates from docs/RESEARCH_LOG.md.",
            ["when", "what happened", "outcome"],
            [["23–24 Jul", "environment, simulator B1–B6", "arm, IK (0.1 mm), ink, camera — Phase B done"],
             ["5 Aug", "DrawEnv, reward iterations, first PPO", "first learned line (IoU 0.508); all 4 shapes"],
             ["6–12 Aug", "H2 vision reward; multi-seed; real-camera check; 84-slide review deck", "camera ≈ truth; proxy validated"],
             ["12 Aug", "literature review: 33 papers", "re-framed as a measurement; H3/H4 added"],
             ["23 Aug", "Stage 1: metrics, O1, H3", "no reward exploitation; overrun discovered"],
             ["3 Sep", "review: 2 bugs fixed; overshoot ablation", "plateau stop +0.055 IoU"],
             ["Sep", "H2 re-run with peak IoU", "overshoot does not bias H2"],
             ["12 Sep – 17 Oct", "Stage 2: perception domain randomisation", "no effect — nothing to fix"],
             ["17–19 Oct", "Stage 3: H4 disturbance recovery", "analysis corrected; sweep finishing"]],
            colw=[1.8, 5.6, 4.8], size=11, row_h=0.47,
            notes="""
Project ki timeline. July ke aakhir me simulator. 5 August ko pehli baar agent ne line banana
seekha. August me H2 (camera reward) aur literature review. 23 August Stage 1 — aur overrun ki
khoj. 3 September do bugs aur overshoot ablation. September me H2 dobara peak IoU ke saath.
September-October me Stage 2 (domain randomisation). Aur ab H4 — sabse zaroori experiment.
""")

    figure(prs, "08 · H1", "The first learned drawings: before and after",
           "PPO, 400k steps per shape, ground-truth reward. Red = target, black = what the agent drew.",
           "fig_before_after.png",
           ["Untrained: IoU 0.079 (line) and 0.000 for the closed shapes — a dot.",
            "Trained: line 0.508 · circle 0.443 · square 0.493 · triangle 0.421.",
            "All four recognisable; none clean: zig-zags, spurs, and a 'tail' from the sheet "
            "centre to the shape (the pen started at the centre with the pen down).",
            "This is H1: the arm LEARNED to draw by trial and error — no path was programmed."],
           fig_w=7.4, size=12.5,
           take="Proof of concept: from IoU ≈ 0 to recognisable shapes, purely from a reward.",
           notes="""
Pehli seekhi hui drawings. Untrained agent sirf ek bindu banata hai (IoU ~0). 400k steps ke baad:
line 0.508, circle 0.443, square 0.493, triangle 0.421. Chaaron pehchaan me aati hain, par saaf
nahi — zig-zag, spurs, aur centre se shape tak ek "poonchh" (pen centre se shuru hota tha, neeche
dabbe hue).

Yahi H1 hai: arm ne khud try karke draw karna seekha — koi path program nahi kiya.
""")

    tabular(prs, "08 · start-tail fix", "Fixing the tail — and learning that randomness is not free",
            "The pen started at the sheet centre with the pen down, so it inked its way to the shape.",
            ["shape", "centre start (with tail)", "random on-target start", "deterministic nearest-centre start"],
            [["line", "0.51", "0.22 (worse)", "0.505"], ["square", "0.49", "—", "0.470"],
             ["triangle", "0.42", "—", "0.468"], ["circle", "0.44", "—", "0.357 (does not close)"]],
            colw=[2.0, 3.0, 3.2, 4.0], size=11.5, row_h=0.42, cell_colors={(0, 2): BAD},
            below=["First try — start on a RANDOM target pixel — backfired: line 0.51 → 0.22. A "
                   "random start is extra variance the policy has to absorb.",
                   "Deterministic start (target pixel nearest the centre): tail gone; net ≈ a wash "
                   "overall. A different defect remains: short spurs off the outline mid-trace.",
                   "Side effect discovered later: with a deterministic start AND deterministic "
                   "actions, every evaluation episode is identical (see the protocol finding)."],
            take="Lesson: randomising initial conditions is a generalisation choice, not a free "
                 "improvement.", take_color=WARN,
            notes="""
Poonchh (tail) theek karne ki koshish. Pehle random target pixel se shuru kiya — line 0.51 se
0.22 par gir gayi. Random start ek extra variance hai jo policy ko sambhalna padta hai.
Phir deterministic start (centre ke sabse paas wala target pixel) — tail gayab, kul mila kar
lagbhag barabar. Circle thoda gira (poora band nahi hota).

Baad me pata chala iska side effect: start bhi fixed aur action bhi deterministic, to har
evaluation episode bilkul same — "8 episodes" asal me ek hi episode 8 baar.
""")

    tabular(prs, "08 · H2", "H2, first look: camera reward vs ground-truth reward",
            "Single runs, 400k steps each, scored on TRUE IoU. The reward is the only thing that differs.",
            ["shape", "ground-truth reward", "camera (vision) reward"],
            [["line", "0.505", "0.447"], ["circle", "0.357", "0.425 (camera better)"],
             ["square", "0.470", "0.453"], ["triangle", "0.468", "0.319"],
             ["mean", "0.450", "0.411"]],
            colw=[3.0, 4.5, 4.7], size=12, row_h=0.42, cell_colors={(4, 1): INK, (4, 2): INK},
            below=["The camera model: perceived-vs-true IoU ~0.83 (the real camera was ~0.88). The "
                   "agent never sees a perfect drawing — only the camera's version.",
                   "Reading: learning from a camera is VIABLE — within ~0.04 of perfect information.",
                   "Not yet evidence: one run per cell. RL varies a lot between seeds."],
            take="Single runs are not credible — the next step was a multi-seed sweep.",
            take_color=WARN,
            notes="""
H2 pehli baar: camera reward vs perfect reward. Sirf reward badla, baaki sab same. Score hamesha
true IoU. Mean 0.450 vs 0.411 — camera sirf ~0.04 peeche, aur circle par aage.

Matlab camera se seekhna sambhav hai. Par yeh ek-ek run hai — RL me seeds ke beech bahut farak
hota hai. Isliye agla kadam multi-seed sweep tha.
""")

    figure(prs, "08 · H2", "H2 with seeds: no detectable difference",
           "4 shapes × 2 reward modes × 3 seeds × 200k steps = 24 runs (results/h2_seeds.jsonl).",
           "results_h2_seeds.png",
           ["Means: ground truth 0.382 ± 0.054, camera 0.354 ± 0.066 (sample sd).",
            "Paired within (shape, seed): camera − truth = −0.028, sd 0.068, t = −1.43 "
            "(11 df), camera ahead in 5 of 12.",
            "|t| = 1.43 is well below significance: NO DETECTABLE DIFFERENCE.",
            "Shape-dependent: camera better on circle, truth better on triangle.",
            "The error-bar 'overlap' test flipped with the choice of sd convention — so the claim "
            "rests on the paired test, not on bars."],
           fig_w=7.6, size=12,
           take="Defensible claim C1: camera reward reaches the same true accuracy as the privileged "
                "canvas — no detectable difference (not 'equivalent': no equivalence test yet).",
           notes="""
Seeds ke saath H2: 24 runs. Ground truth 0.382, camera 0.354. Paired test (same shape, same seed
ke jode): farak −0.028, t = −1.43 — significant hone se kaafi door. Isliye: koi detectable farak
nahi. Shape ke hisaab se: circle par camera behtar, triangle par truth.

Ek seekh: error bars overlap karte hain ya nahi, yeh sd ke formula (ddof) par palat gaya. Isliye
daava paired test par tika hai, bars par nahi. "Equivalent" nahi likh sakte — uske liye
equivalence test (TOST) chahiye, jo abhi nahi hua.
""")

    figure(prs, "08 · H3", "H3: is the agent fooling the camera?",
           "A camera-rewarded agent might learn tricks the camera scores well but the paper does not.",
           "results_h3.png",
           ["Logged true AND perceived IoU at the end of every training episode: 4 shapes × "
            "832 episodes = 3,328 episodes, plus a truth control.",
            "Mean gap (perceived − true): −0.0001. 95% of gaps within ±0.013; largest 0.029.",
            "True and perceived IoU correlate at 0.997–0.999 throughout training.",
            "Control: the truth run's gap is exactly 0.000000 — the logging is trustworthy.",
            "Per-shape sign is consistent (line under-credited, square over-credited); the "
            "square's gap rises slightly but stays far below the 0.02 bar."],
           fig_w=7.4, size=11.5,
           take="Claim C2: no exploitable drift. Limits: 1 seed per shape; fixed camera only.",
           notes="""
H3 ka sawaal: kahin agent camera ko bewakoof to nahi bana raha — aisi cheezen jo camera ko achhi
lagein par asli paper par nahi? Har training episode ke ant me true aur perceived IoU dono log kiye:
3,328 episodes.

Average farak −0.0001. 95% gaps ±0.013 ke andar, sabse bada 0.029. Dono 0.997–0.999 correlate
karte hain. Control (truth run) ka gap bilkul zero — logging bharose layak.

Ek shape ke andar sign consistent hai (line par camera kam credit deta, square par zyada), aur
square ka gap thoda badhta hai — par 0.02 ki seema se bahut neeche. Claim: koi exploit nahi.
""")

    figure(prs, "08 · H6 · discovery", "The surprise: agents finish early, overshoot, then idle",
           "Found by asking why path_ratio was so high. Not on any plan.",
           "results_overrun.png",
           ["The shape is traced in the first ~10–17% of the episode (peak IoU at step 12–41 of 240).",
            "A short overshoot right after completion costs IoU — usually within 4–8 steps.",
            "Then the canvas FREEZES: on average 74% of every episode changes nothing.",
            "Mean IoU lost to the overshoot: 0.064 — more than twice the whole H2 gap (0.028).",
            "Why: no 'stop' action, pen always down, and a Gaussian policy cannot hold exactly still."],
           fig_w=8.0, size=11.5,
           take="Every IoU reported until then was measured AFTER the overshoot — and ~74% of the "
                "training budget was spent on frozen canvases.", take_color=WARN,
           notes="""
Ek anokhi khoj: agent shape episode ke pehle 10–17% me hi bana leta hai. Uske turant baad thoda
aage nikal jaata hai (overshoot) aur IoU girta hai. Phir canvas jam jaata hai — average 74% episode
me kuch nahi badalta.

Overshoot me average 0.064 IoU jaata hai — H2 ke poore farak (0.028) se do guna zyada!
Wajah: rukne ka koi action nahi, pen hamesha neeche, aur Gaussian policy bilkul sthir nahi reh
sakti.

Matlab ab tak ka har IoU overshoot ke BAAD naapa gaya tha, aur training ka 74% budget jame hue
canvas par barbaad ho raha tha.
""")

    concept(prs, "08 · protocol", "A protocol finding: '8 evaluation episodes' were one episode, 8 times",
            "Found while checking whether the overrun survives across episodes.",
            ["The start is deterministic (target pixel nearest the centre) and evaluation uses "
             "deterministic actions — so there is no randomness left anywhere.",
             "Verified: the 8 evaluation episodes produce 8 pixel-identical canvases, IoU sd 0.000000000.",
             "Does NOT invalidate H2: its ± comes from 3 training seeds, which genuinely differ.",
             "But any claim 'averaged over 8 episodes' would have been false — 8× the compute for one number.",
             "Real evaluation variance arrived later: a randomised camera (Stage 2) and random "
             "disturbances (H4) make eval_eps > 1 meaningful."],
            cards=[("FIX ON THE ROADMAP", ["Parameterised shapes with a held-out range (proposal "
                                           "§5.4): real variation, and a test of generalisation "
                                           "instead of memorising four shapes."], PRIMARY),
                   ("WHY IT MATTERS", ["'n' must count independent things. Eight copies of one "
                                       "episode are n = 1."], WARN)],
            notes="""
Ek protocol galti pakdi: "8 evaluation episodes" asal me ek hi episode 8 baar tha. Start fixed,
action deterministic — koi randomness bachi hi nahi. Aath bilkul same canvas, IoU ka sd zero.

H2 galat nahi hota — uska ± teen training seeds se aata hai jo sach me alag hain. Par "8 episodes
ka average" likhna galat hota. Baad me randomised camera (Stage 2) aur random disturbances (H4)
ne evaluation me asli variation laya. Seekh: n sirf independent cheezon ko ginta hai.
""")

    tabular(prs, "08 · O1", "O1: telling the agent how much time is left",
            "24 runs: 4 shapes × 3 seeds × 2 arms × 200k steps, ground-truth reward. Paired by (shape, seed).",
            ["metric", "mean change (on − off)", "sd", "pairs up", "t", "reading"],
            [["IoU", "+0.039", "0.062", "9/12", "+2.17", "suggestive, not conclusive"],
             ["peak IoU", "+0.040", "0.062", "9/12", "+2.22", "probably real"],
             ["overshoot", "+0.001", "0.034", "5/12", "+0.11", "no effect"],
             ["path_ratio", "+0.998", "3.835", "7/12", "+0.90", "no effect"]],
            colw=[1.8, 2.6, 1.2, 1.5, 1.2, 3.9], size=11.5, row_h=0.42,
            cell_colors={(0, 5): WARN, (1, 5): GOOD},
            below=["Per shape: triangle +0.073 (all 3 seeds up), square +0.064, line +0.026, circle −0.008.",
                   "MY PREDICTION WAS WRONG: O1 was expected to reduce the overshoot (the overshoot "
                   "happens near the end, and O1 shows the end coming). Overshoot change: +0.001, t = 0.11.",
                   "An analysis bug was caught here too: the first verdict compared against a POOLED "
                   "std (shape spread + seed noise) and said 'no effect'; the paired test shows the gain."],
            take="Kept, default OFF: a modest, shape-dependent +0.04 — not worth breaking saved "
                 "3-channel models.", take_color=PRIMARY,
            notes="""
O1: observation me "kitna samay bacha" jodna. Result: +0.039 IoU, 12 me se 9 jodon me sudhaar,
t = 2.17 — suggestive, conclusive nahi. Shape ke hisaab se: triangle aur square me fayda, circle
me nahi.

Meri prediction galat nikli: socha tha O1 overshoot kam karega. Overshoot ka badlav +0.001 — zero.
Yeh bhi log kiya, kyunki restart ka kaaran yahi prediction tha.

Ek analysis bug bhi pakda: pehle pooled std se compare kiya to "koi asar nahi" aaya; paired test
ne sahi tasveer dikhayi. Decision: feature rakha, par default band.
""")

    grid(prs, "08 · honesty", "Two bugs of our own — found by review, fixed, and logged",
         "3 Sep 2026: five parallel reviews; every finding re-verified before acting on it.",
         [("BUG 1 (CRITICAL) · THE STOP BUTTON PAID A PRIZE",
           ["A new 'stop' action set terminated = True, and the +2.0 success bonus was paid on "
            "terminated — so pressing stop on a BLANK canvas earned +1.99.",
            "The stop arm was optimising a different reward: its collapse was bought, not learned.",
            "Fix: pay the bonus only on reaching IoU ≥ 0.60. Stop now returns −0.0067, same as not stopping.",
            "No published number affected (the flag existed for one day)."], BAD),
          ("BUG 2 · THE OUTLINE LENGTH WAS HALVED",
           ["target_perimeter_px used only the OUTER contour of each closed shape, under-measuring "
            "circle / square / triangle by ~1.9× — so path_ratio was inflated ~1.9× on them.",
            "The headline 'square path_ratio 3.03' was wrong; corrected: 1.59.",
            "Values were converted exactly (a constant per shape); originals archived."], WARN),
          ("ALSO FIXED", ["An untrained stop head stops ~31% of steps → episodes of 3.9 steps; an "
                          "initial bias of −2.0 gives ~87-step episodes (a declared prior).",
                          "Smoothness averaged over 4 dims in the stop arm → 25% weaker: now always "
                          "over the first 3."], SLATE),
          ("CORRECTIONS TO OUR OWN DOCS", ["'perceived never runs ahead of true' → false (51% of "
                                           "episodes); 'every error bar overlaps' → depends on the sd "
                                           "convention; claims re-based on the paired test."], ACCENT)],
         cols=2,
         notes="""
Apne do bugs. Bug 1 (critical): naya "stop" action episode khatam karta tha, aur success bonus
(+2) "episode khatam" par milta tha — to khaali canvas par stop dabao aur +1.99 lo! Stop arm alag
reward optimise kar raha tha. Theek kiya: bonus sirf asli success par. Koi published number
prabhavit nahi.

Bug 2: closed shapes ki outline ki lambai aadhi naapi ja rahi thi (sirf bahar ki edge), to
path_ratio ~1.9 guna zyada aata tha. "Square 3.03" galat tha, sahi 1.59.

Aur apne documents me bhi galat daave sudhaare. Har sudhaar nayi dated entry ke roop me log hua.
""")

    figure(prs, "08 · overshoot ablation", "Can the overshoot be fixed? Environment vs policy",
           "24 runs: baseline / plateau-stop / learned-stop × 4 shapes × 2 seeds × 200k. Grey caps = IoU lost to overshoot.",
           "results_overshoot.png",
           ["plateau: the ENVIRONMENT ends the episode after k steps with no improvement.",
            "stop: the AGENT gets a 'finished' action.",
            "Paired vs baseline (8 pairs): plateau +0.055 IoU, t = +2.56, 7/8 up — overshoot "
            "0.034 → 0.009, episodes 240 → 50 steps, peak IoU UP +0.030.",
            "stop: +0.024, t = +0.96, 5/8 — inconclusive; it stops at step ~22, before there is "
            "anything to overshoot. Best single cell: triangle 0.498.",
            "Confound not yet controlled: plateau trains on ~5× more (shorter) episodes."],
           fig_w=7.3, size=11.5,
           take="Effect real (C5); mechanism not established — a 4th arm (plateau with a grace "
                "period, or max_steps = 50) is needed before calling it a fix.", take_color=WARN,
           notes="""
Overshoot theek ho sakta hai? Do tareeke: plateau — environment khud episode khatam kare jab k steps
tak sudhaar na ho; stop — agent ko "ho gaya" button do.

Plateau jeeta: +0.055 IoU, 8 me 7 jodon me sudhaar, t = 2.56; overshoot 0.034 se 0.009; episode
240 se 50 steps; aur peak IoU bhi badha. Stop inconclusive — woh step ~22 par hi ruk jaata hai.

Par ek confound: plateau arm ko chhote episodes ki wajah se ~5 guna zyada episodes milte hain.
Effect asli hai, mechanism abhi sabit nahi — chautha arm chahiye.
""")

    concept(prs, "08 · lesson", "A wrong prediction, and the distinction that explains it",
            "Before the ablation the log said: 'the overshoot can only be fixed by the policy itself'. The data said the opposite.",
            ["The reasoning: a plateau detector LAGS — 'no improvement for k steps' is only "
             "visible after the peak has passed, so it cannot catch an overshoot.",
             "Tested on an already-trained agent, that was exactly right: patience 40 / 20 / 10 cut "
             "episodes 240 → 51 steps and left IoU unchanged at 0.470.",
             "But with the plateau stop present DURING TRAINING, the agent never learns to "
             "overshoot — the episode ends before wandering is ever practised or rewarded.",
             "An evaluation-time filter and a training-time condition are different interventions. "
             "A result about the first was quoted as if it settled the second."],
            cards=[("THE GENERAL LESSON", ["Ask: 'measured on a frozen policy, or on one trained "
                                           "under the condition?' Both are valid questions with "
                                           "different answers."], VIOLET),
                   ("WHY RECORD IT", ["The wrong prediction is in the log with a REFUTED banner. "
                                      "Hiding refuted predictions makes the remaining ones look "
                                      "more reliable than they are."], GOOD)],
            notes="""
Ek galat prediction aur uski seekh. Socha tha plateau detector late hota hai — peak ke baad hi
pata chalta hai — isliye overshoot nahi pakad sakta. Trained agent par test kiya to sach tha: IoU
0.470 hi raha.

Lekin jab plateau stop TRAINING ke dauraan maujood hai, agent overshoot seekhta hi nahi — episode
pehle hi khatam ho jaata hai. Evaluation-time filter aur training-time condition do alag cheezen
hain. Yeh galat prediction log me "REFUTED" banner ke saath hai — chhupaya nahi.
""")

    tabular(prs, "08 · H2 re-check", "Does the overshoot bias H2? Re-running the whole sweep",
            "A second independent 24-run H2 sweep, now logging PEAK IoU (before any overshoot) alongside FINAL IoU.",
            ["scored at", "mean gap (camera − truth)", "sd", "t", "camera ahead"],
            [["the END (what H2 reports)", "+0.0128", "0.0775", "+0.57", "8/12"],
             ["the PEAK (before overshoot)", "+0.0020", "0.0646", "+0.11", "8/12"],
             ["published sweep, end (12 Aug)", "−0.0280", "0.0680", "−1.43", "5/12"]],
            colw=[3.6, 3.1, 1.4, 1.4, 1.9], size=12, row_h=0.45,
            below=["Moving the scoring point changes the gap by −0.011, well inside its standard error "
                   "(0.022): the overshoot does NOT bias H2. H2 stands.",
                   "The worry came from n = 1 models (camera seemed to lose 2× more to overshoot). At "
                   "n = 12 it does not replicate: mean overshoot truth 0.033, camera 0.022 (t = −1.37).",
                   "Bonus finding: two independent sweeps gave OPPOSITE signs (−0.028 vs +0.013), both "
                   "|t| < 1.5 — a stronger statement of 'indistinguishable' than either alone. Seed "
                   "noise dwarfs the effect (circle swings −0.127 → +0.159 across seeds)."],
            take="Labelling the n = 1 worry 'a hypothesis, not a result' when it was first written "
                 "down did its job: it was tested, not adopted.", take_color=GOOD,
            notes="""
Kya overshoot H2 ko bias karta hai? Poora H2 sweep dobara chalaya, ab peak IoU bhi record kiya.
End par farak +0.013, peak par +0.002 — badlav sirf −0.011, jo standard error (0.022) ke andar hai.
Overshoot H2 ko bias nahi karta.

Jo chinta thi (camera overshoot me do guna zyada khota hai) woh n = 1 se aayi thi; n = 12 par
dohrayi nahi gayi.

Bonus: do alag sweeps me farak ka sign ulta aaya (−0.028 aur +0.013), dono insignificant. Yeh
"farak nahi pakda ja sakta" ka aur mazboot saboot hai — seed ka noise effect se kahin bada hai.
""")


# ============================================================== STAGE 2 ======
def stage2(prs):
    decision_slide(
        prs, "08 · stage 2", "Stage 2: does H2 survive a worse camera?",
        "Proposal §4.1 — perception domain randomisation (rl/perception.py, rl/dr_experiment.py).",
        ["Replaced the single fixed camera with a sampled one (8 axes).",
         "Three training arms: truth (no camera) · fixed camera · randomised camera.",
         "Each evaluated under fixed, train and HELD-OUT cameras; always TRUE IoU."],
        ["H2 was measured with one optimistic camera (resize + threshold).",
         "That makes H2 a claim about a sensor, not about cameras.",
         "The literature review rated this the #1 threat to validity."],
        ["Real camera in the loop (270× slower — impractical).",
         "A single 'realistic' fixed camera (which realism?).",
         "Leave H2 as is (a reviewer would object)."],
        ["Domain randomisation (Tobin 2017) is the standard, hardware-free answer.",
         "Disjoint train / held-out ranges make generalisation measurable."],
        ["Design flaw: the camera only touched the REWARD, so at evaluation (no reward) it had no "
         "effect at all — byte-identical results. Fix: the agent now also SEES through the camera.",
         "Six perception fixes before running (next slide)."],
        ["Randomisation buys nothing: −0.011 on the held-out camera, t = −0.67.",
         "Because nothing needed fixing: the fixed-camera agent loses only 0.014 on a camera "
         "that recovers 39% of the ink."],
        notes_text="""
Stage 2 ka sawaal: kya H2 ek kharab camera par bhi tikta hai? H2 ek optimistic camera se naapa
gaya tha — matlab woh ek sensor ke baare me daava tha, cameras ke baare me nahi.

Kiya: 8 cheezen badalne wala camera model, teen training arms (truth, fixed camera, randomised
camera), aur har ek ko fixed, train aur held-out camera par test kiya.

Ek bada design flaw mila: camera sirf reward ko chhoota tha. Evaluation me reward hota hi nahi, to
camera ka koi asar nahi tha — results byte-identical. Hal: ab agent camera se DEKHTA bhi hai — jo
asli robot ki stithi hai.

Result: randomisation se koi fayda nahi — kyunki theek karne layak kuch tha hi nahi. Fixed camera
wala agent us camera par bhi sirf 0.014 khota hai jo sirf 39% ink dikhata hai.
""")

    tabular(prs, "08 · stage 2", "Six bugs in the camera model, fixed before spending the compute",
            "A review run against perception.py BEFORE the sweep: a bug found now costs minutes; afterwards, the whole run.",
            ["#", "finding", "fix"],
            [["F4", "the perspective warp caused 56% of all degradation — modelling an UNrectified sheet, which the real pipeline is not",
              "reduced to a residual registration error; now ~13%"],
             ["F5", "TRAIN and HELD-OUT overlapped on the threshold axis, though the code asserts they are disjoint",
              "held-out moved to (0.28, 0.43); all 8 axes verified disjoint"],
             ["F7", "edge padding smeared ink at the border into a stripe: +34–39% phantom ink",
              "pad with the paper level — outside the sheet a camera sees paper"],
             ["F9", "78% of training 'resolutions' were UP-samples (no loss at all)",
              "capped at the canvas: train 96–128 px, held-out 76–92 px"],
             ["F11", "no sensor saturation: over-exposure IMPROVED the signal",
              "clip to [0, 255] after gain and noise"],
             ["F13", "a typo such as 'Train' silently selected the held-out camera",
              "assert the split name"],
             ["F6", "seeds 0 and 1 share 7 of 8 environment streams in SB3",
              "use seeds 0 and 100"]],
            colw=[0.7, 7.0, 4.5], size=10.5, row_h=0.50,
            take="Also measured, not tuned: the held-out camera recovers 0.394 of the ink (target was "
                 "0.45–0.60). Ranges were left alone rather than adjusted until a number looked right.",
            take_color=WARN,
            notes="""
Sweep chalane se pehle camera model ka review kiya — chhe bug mile. Perspective warp 56% kharabi
de raha tha (ek aisa tedha paper jo asli pipeline me hota hi nahi). Train aur held-out ranges
overlap kar rahi thi. Border par ink ki patti ban rahi thi (34–39% nakli ink). 78% training
resolution asal me upsampling thi (koi nuksaan hi nahi). Over-exposure signal ko behtar bana raha
tha (ulta physics). Ek typo galat camera chun leta.

Aur: held-out camera 0.394 ink dikhata hai, jabki lakshya 0.45–0.60 tha. Ranges ko tab tak nahi
ghumaya jab tak number pasand na aaye — jo mila wahi report kiya.
""")

    tabular(prs, "08 · stage 2", "Stage 2 result: randomisation does not help — because nothing was broken",
            "24 runs: 3 training arms × 4 shapes × 2 seeds × 200k. Balanced over 8 (shape, seed) cells. TRUE IoU.",
            ["trained on", "eval: fixed camera", "eval: train camera", "eval: HELD-OUT camera"],
            [["truth (no camera at all)", "0.389 ± 0.051", "0.389", "0.389"],
             ["fixed camera", "0.393 ± 0.051", "0.386 ± 0.044", "0.379 ± 0.041"],
             ["randomised camera", "0.371 ± 0.062", "0.365 ± 0.057", "0.368 ± 0.056"]],
            colw=[3.4, 2.9, 2.9, 3.0], size=12, row_h=0.45,
            below=["Paired, randomised − fixed, on the held-out camera: −0.011, t = −0.67, 3/8 up → "
                   "no detectable effect.",
                   "The fixed-camera agent drops only 0.014 (0.393 → 0.379) on a camera it never saw, "
                   "which recovers just 39% of a perfect drawing's ink.",
                   "Harder setting than H2 (the camera is in the OBSERVATION too) — yet camera arms "
                   "sit level with the privileged truth arm. Do not compare these absolute IoUs with H2's."],
            take="Claim C3: the policy needs to know roughly where it has been, not a good picture of "
                 "its drawing. Camera realism is not where the difficulty lives.", take_color=GOOD,
            notes="""
Stage 2 ka result. Truth arm 0.389. Fixed-camera arm apne camera par 0.393, aur kabhi na dekhe
held-out camera par 0.379 — sirf 0.014 ki giraavat, jabki woh camera aadhi se zyada ink kho deta
hai. Randomised arm ne held-out par fixed se 0.011 kam kiya, t = −0.67 — koi detectable asar nahi.

Matlab: policy ko apni drawing ki achhi tasveer nahi chahiye, bas mota-mota pata hona chahiye ki
pen kahan-kahan ja chuka hai. Aur yeh H2 se kathin setting hai — yahan camera observation me bhi
hai — phir bhi camera arms truth arm ke barabar hain. Yeh ek negative result hai jo kaam ka hai:
ek bada threat-to-validity hat gaya.
""")


def build(prs):
    system(prs)
    journey(prs)
    stage2(prs)
