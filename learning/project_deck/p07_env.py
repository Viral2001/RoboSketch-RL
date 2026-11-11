"""Section 7 - the drawing environment (rl/draw_env.py) and the bugs that shaped it."""
from kit import *  # noqa: F401,F403
from teach_figs import TOY


def build(prs, toc):
    section(prs, 7, "The drawing environment",
            "DrawEnv (rl/draw_env.py) is the Gymnasium environment every experiment runs on. Every "
            "design choice in it has a reason - and several came from bugs or failed first attempts.",
            ["One step, end to end", "Observation channels", "Action", "Reward equation",
             "Why IoU-delta telescopes", "Reward-design history", "Episode design", "Bugs that shaped it"],
            """
Section 7: hamara environment - project ka dil. Yahan har choice ka "kyun" hai: observation me kya,
action kaisa, reward ka exact formula, episode kitna lamba, pen kahan se shuru. Aur woh bugs jo
measurement se pakde gaye. Interview me "walk me through your environment" ka jawab yahi section hai.""", toc)

    s = slide(prs, "One environment step, end to end", "07 · DrawEnv.step()",
              "What happens between the agent choosing an action and receiving its reward.")
    row1 = [("1 ACTION", "dx, dy × 0.014 m;\npen down?"), ("2 CLAMP", "keep the pen\non the sheet"),
            ("3 MOVE", "pen point (fast)\nor IK KUKA arm"), ("4 DISTURB", "H4 only: slip,\nsheet shift, no ink")]
    row2 = [("5 INK", "line from old to new\npen point on canvas"), ("6 BELIEF", "fk / camera_est: what\nkinematics expects"),
            ("7 SCORE", "true IoU; reward IoU\nfrom truth or camera"), ("8 OBSERVE", "64×64 image for\nthe next action")]
    y1, y2 = s._top + 0.15, s._top + 1.95
    pipeline(s, row1, M, y1, CW, 1.3, colors=[VIOLET, PRIMARY, PRIMARY, WARN], title_size=14, sub_size=12)
    pipeline(s, row2, M, y2, CW, 1.3, colors=[PRIMARY, SLATE, GOOD, ACCENT], title_size=14, sub_size=12)
    bw = (CW - 0.32 * 3) / 4
    elbow(s, [(M + 3 * (bw + 0.32) + bw / 2, y1 + 1.32), (M + 3 * (bw + 0.32) + bw / 2, y1 + 1.6),
              (M + bw / 2, y1 + 1.6), (M + bw / 2, y2 - 0.02)], color=SLATE)
    bullets(s, ["Disturbances act on REALITY only (the canvas); the agent's command stream and the "
                "kinematic belief never hear about them.",
                "info['iou'] is always the TRUE IoU; info['reward_iou'] is what the agent optimised. Their "
                "difference over training is the H3 exploitation test."],
            M, s._top + 3.5, CW, 1.2, start=15)
    why(s, "Keeping 'what really happened' (canvas) separate from 'what the agent believes / sees' is what "
           "makes H2, H3 and H4 measurable at all.")
    note(s, """
Ek step me kya hota hai:
1) Action: dx, dy (x 0.014 m) aur pen neeche/upar.
2) Clamp: pen paper ke bahar na jaye.
3) Move: fast backend me pen point seedha naye point par; use_arm=True ho to IK wala KUKA.
4) Disturb (sirf H4): pen slip, paper shift ya ink failure - SIRF asli canvas par.
5) Ink: purane se naye point tak line canvas par.
6) Belief: fk arm aur camera_est ke liye ek "belief canvas" - kinematics ke hisaab se ink kahan gayi.
7) Score: true IoU (hamesha asli canvas), aur reward ke liye IoU - truth ya camera se.
8) Observe: agle action ke liye 64x64 image.

Sabse important design idea: "asal me kya hua" (canvas) aur "agent kya sochta/dekhta hai" (belief,
camera photo) ALAG rakhe gaye. Isi se H2 (reward source), H3 (perceived vs true gap) aur H4 (belief
vs reality) naape ja sake.
""", source="rl/draw_env.py step() (disturbances 'applied to REALITY only', belief canvas, info dict)")

    concept(prs, "07 · observation", "What the agent sees: the observation channels", "A uint8 image, 64 × 64 × C.",
            ["Channel 0 - the TARGET shape.",
             "Channel 1 - what has been DRAWN. Its source is the key experimental variable: the true "
             "canvas (privileged), the fk belief (D01's condition), or a camera photo.",
             "Channel 2 - a dot at the PEN position (255 if the pen is down, 128 if up). In H4 v3/v4 the dot "
             "can be placed in the SHEET frame (true or estimated offset).",
             "Optional, default OFF: a time-left channel (O1), two coordinate ramps (O3 CoordConv), or an "
             "egocentric window centred on the pen (O2).",
             "Every option is additive and default-off, and was checked bit-identical against the "
             "previous environment before use - so no recorded result moved."],
            cards=[("WHY IMAGES, NOT NUMBERS", ["A camera gives images; to compare 'learning from truth' with "
                                                "'learning from a camera' fairly, both arms must see the same "
                                                "kind of input."], ACCENT),
                   ("WHY A PEN DOT", ["The policy must know where the pen is relative to the shape. A dot "
                                      "in the same image makes that a spatial pattern the CNN can read."], VIOLET)],
            notes="""
Observation = 64x64 ki image, kuch channels:
- Channel 0: target shape.
- Channel 1: ab tak kya draw hua. YAHI experiment ka main variable hai - kahan se aata hai? True canvas
  (privileged), fk belief (D01 ki condition: kinematics ke hisaab se), ya camera ki photo.
- Channel 2: pen ki position par ek dot (pen neeche = 255, upar = 128). H4 v3/v4 me yeh dot "sheet
  frame" me bhi lag sakta hai.
- Optional (default off): time channel (O1), coordinate planes (O3), ego window (O2).

Har option "additive, default OFF" hai aur use karne se pehle bit-identical check hua - purane results
nahi badle. Yeh discipline zaroori hai: ek file me do versions ka data mix na ho.

Images kyun, numbers kyun nahi? Camera images deta hai; truth vs camera fair comparison ke liye dono
arms ko same kism ka input chahiye.
""", source="rl/draw_env.py _obs, _obs_ego and constructor comments; RESEARCH_LOG H4 v3 / O2 / O3 'What changed' (bit-identical checks)")

    concept(prs, "07 · action", "What the agent does: the action", None,
            ["action = [dx, dy, pen] with dx, dy ∈ [-1, 1] and pen ∈ [0, 1].",
             "dx, dy are multiplied by the step size: 0.014 m in every experiment (≈ 8.9 canvas px).",
             "The new pen position is clamped to the sheet; the pen moves in a straight line, inking a "
             "connected segment.",
             "pen_always_down = True in almost every experiment: the pen bit is ignored and the pen always inks.",
             "A2 'pen-free' and the digits use pen > 0.5 = down.",
             "Smoothness: the reward charges 0.02 × mean |a_t - a_t-1| over the first three dims."],
            cards=[("WHY PEN ALWAYS DOWN", ["The first runs found 'never put the pen down' optimal: no ink, no "
                                            "stray-ink penalty. Forcing the pen down (and tracing single-stroke "
                                            "shapes first) removed that trap."], BAD),
                   ("WHY 0.014 m STEPS", ["Small enough for accurate, IK-friendly motion; large enough to trace a "
                                          "shape in ~30 steps (tracer: 12-33 steps)."], PRIMARY)],
            notes="""
Action: [dx, dy, pen]. dx, dy -1 se 1 ke beech, step size 0.014 m se multiply (~8.9 canvas px). Naya
point paper par clamp hota hai, aur pen seedhi line me chalta hai.

pen_always_down = True (lagbhag har experiment me): pen hamesha neeche, pen bit ignore. Kyun? Pehle
runs me agent ne seekha ki pen kabhi neeche hi mat rakho - koi ink nahi, koi stray-ink penalty nahi,
"safe" optimum. Pen ko force karne se trap toota. Pen-up/down baad me A2 aur digits me test kiya.

Smoothness penalty: 0.02 * mean|a_t - a_(t-1)| - jhatkedaar moves kam. 0.15 bahut zyada tha (agent ne
hilna hi band kar diya), 0.02 sahi.

0.014 m kyun? IK ke liye chhote moves achhe; aur shape ~30 steps me trace ho jaati hai (scripted tracer
12-33 steps me).
""", source="rl/draw_env.py action_space and step(); docs/paper/main.tex Setup; RESEARCH_LOG '### Reward shaping - "
            "two local optima' and 'First PPO training experiments on line' (smoothness 0.15 vs 0.02); "
            "'### T1 ... Checks before launch' (expert path 12-33 steps); H5 entry (~8.9 px per step)")

    eq_slide(prs, "07 · reward", "The reward, exactly as coded",
             "Dense shaping toward a higher IoU, computed every step.",
             r"r_t=10\,\Delta\mathrm{IoU}_t+0.4\,\Delta\Phi_t-0.02\,\overline{|a_t-a_{t-1}|}+2\cdot\mathbf{1}\left[\mathrm{IoU}_t\geq 0.6\right]",
             [(r"\Delta\mathrm{IoU}_t", "IoU_t - IoU_t-1 of the REWARD canvas (truth, or camera in vision mode)"),
              (r"\Delta\Phi_t", "change in potential: -(pen's distance to the target)"),
              (r"\overline{|a_t-a_{t-1}|}", "mean change of dx, dy, pen since the last step (jerkiness)"),
              (r"\mathbf{1}[\cdot]", "success bonus: never paid in practice (best peak 0.516)")],
             example=["iou_weight 10: makes the IoU term dominate (one full drawing ≈ a few reward units).",
                      "prox_weight 0.4: the potential pull, no bigger than needed.",
                      "smooth_penalty 0.02: 0.15 swamped the IoU signal and the agent stopped moving.",
                      "time_penalty 0: a per-step cost encouraged 'freeze'."],
             example_title="THE WEIGHTS, AND WHY", example_color=PRIMARY, eq_size=27,
             why_text="Reward the thing we score (IoU), help the agent find it (potential), discourage jitter - "
                      "and nothing else.",
             label="DrawEnv reward", group="Environment",
             notes="""
Reward ka exact formula (code se):
r = 10 * delta IoU + 0.4 * delta Phi - 0.02 * jerk + 2 (agar IoU >= 0.6).

- 10 * delta IoU: main term. Drawing ka IoU badha -> reward. Vision mode me yeh IoU camera ki photo se
  aata hai - YAHI H2 ka variable hai.
- 0.4 * delta Phi: potential shaping - pen target ke paas aaye to bonus.
- 0.02 * jerk: actions me achanak badlav ka chhota penalty - smooth strokes.
- +2 success bonus: IoU 0.6 par - par kisi agent ne kabhi chhua nahi (best peak 0.516), to practically
  kabhi nahi mila.

Weights kyun? 10 taaki IoU dominate kare; 0.4 sirf utna pull jitna chahiye; smoothness 0.15 par agent
ne hilna band kar diya tha - 0.02 sahi nikla; time penalty 0 kyunki per-step cost "freeze" ko badhava deta tha.

Dhyan: reward agent ko training me milta hai; SCORE (evaluation) hamesha true IoU.
""", source="rl/draw_env.py defaults (iou_weight 10.0, prox_weight 0.4, smooth_penalty 0.02, time_penalty 0.0, done_iou 0.60) "
            "and _reward / step(); RESEARCH_LOG 'BUG 1' (best peak 0.516) and 'First PPO training experiments on line'")

    t = TOY["tele"]
    eq_slide(prs, "07 · reward", "Why IoU-delta: the rewards add up to the final IoU",
             "A telescoping sum - every intermediate IoU cancels.",
             r"\sum_{t=1}^{T}10\left(\mathrm{IoU}_t-\mathrm{IoU}_{t-1}\right)=10\left(\mathrm{IoU}_T-\mathrm{IoU}_0\right)",
             [(r"\mathrm{IoU}_0", "IoU at the start (0: nothing drawn yet)"),
              (r"\mathrm{IoU}_T", "IoU at the end of the episode"),
              (r"T", "number of steps in the episode")],
             example=[f"Toy IoU sequence {t['ious']}",
                      f"→ sum of 10·ΔIoU = {t['sum']:.2f} = 10 × final IoU.",
                      "Note the last step: IoU fell 0.40 → 0.38 (overshoot) and that step was PUNISHED.",
                      "(computed by teach_figs.py)"],
             why_text="Maximising return ≈ maximising the final drawing's IoU (ignoring γ and the small shaping "
                      "terms) - and scribbling cannot pay, because stray ink lowers IoU.",
             label="Telescoping IoU-delta reward", group="Environment",
             notes="""
IoU-delta reward ki khoobsurti: har step ka reward 10*(IoU_t - IoU_(t-1)). Poore episode ka sum karo
to beech ke saare terms cancel ho jaate hain (telescoping series) - bachta hai 10*(IoU_final - IoU_start).
Start par IoU 0, to total = 10 * final IoU.

Matlab: return maximize karna ~ final IoU maximize karna (gamma aur chhote shaping terms ko chhod kar).
Agent ko woh cheez optimise karne ko mil rahi hai jis par hum use score karte hain.

Toy (script se): IoU 0 -> 0.10 -> 0.25 -> 0.40 -> 0.38; total reward 3.8 = 10 x 0.38. Aakhri step par
IoU gira (overshoot) to us step ko negative reward mila.

Scribble kyun nahi chalta: faltu ink union badhati hai -> IoU girta hai -> reward negative. Pehla
coverage-based reward isi wajah se fail hua tha (agla slide).
""", source="rl/draw_env.py _reward comment ('Telescopes over the episode to the final IoU'); toy numbers by teach_figs.py")

    tabular(prs, "07 · reward history", "How the reward was designed: four attempts on the line",
            "Each run 300-400k steps; each version fixed the previous failure (log, 5 Aug 2026).",
            ["#", "reward design", "IoU / coverage", "failure mode"],
            [["1", "coverage - stray ink - time", "0.06→0.14 / 0.06→0.91", "SCRIBBLE: a blob over the whole region"],
             ["2", "IoU-delta + proximity", "0.06→0.12 / →0.43", "CENTRAL BLOB: covers the easy middle only"],
             ["3", "+ thicker target, finer control, reachable bonus", "0.09→0.30 / →0.89", "ZIGZAG: full sweep, but wobbles"],
             ["4", "+ matched pen width + smoothness penalty 0.02", "0.08→0.508 / →0.87", "recognisable line ✓"]],
            colw=[0.5, 4.6, 2.6, 4.1], size=12.5, row_h=0.5, align="left",
            cell_colors={(3, 3): GOOD, (0, 3): BAD, (1, 3): BAD, (2, 3): WARN},
            below=["Before this: two traps - 'draw nothing' (fixed by potential shaping + pen always down) and "
                   "'don't move' (fixed by making coverage dominate and dropping the time penalty).",
                   "Then the whole task ladder learned (400k each): line 0.508, circle 0.443, square 0.493, "
                   "triangle 0.421 - all recognisable; a stray 'tail' from the centre start remained."],
            take="Lesson: the reward IS the specification. Each failure showed what the reward really asked for.",
            take_color=VIOLET,
            notes="""
Reward design ek baar me nahi bana - chaar koshishein, har ek ne pichhli galti theek ki:
1) Coverage - stray - time: agent ne poore area par blob scribble kar diya (stray penalty kamzor).
2) IoU-delta + proximity: beech ka aasaan hissa dhaka, ends tak jaane ka risk nahi liya.
3) Mota target, finer control, pahunch-yogya bonus: poori line sweep ki, par zig-zag.
4) Pen width target se match + smoothness 0.02: pehchaanne laayak line, IoU 0.508 (0.079 se).

Usse pehle do traps: "draw nothing" aur "don't move".

Phir chaaron shapes 400k steps par: line 0.508, circle 0.443, square 0.493, triangle 0.421. Ek artifact
bacha: centre se shape tak ek "tail" - jiska fix agla slide.

Interview lesson: "the reward is the specification" - agent wahi karta hai jo reward kehta hai, chahe
aapka matlab kuch aur ho. Isliye har failure se pata chala ki reward asal me kya maang raha tha.
""", source="RESEARCH_LOG '### First PPO training experiments on line (2026-08-05)', '### Reward shaping - two local optima', "
            "'### Full task ladder trained (2026-08-05)'")

    concept(prs, "07 · episode", "Episode design: length, start point, evaluation", None,
            ["Length: 240 steps of 0.014 m (60 in the H4 series). Agents trace a shape in the first 10-17% "
             "of the episode - the long tail later became a finding (overrun, H6).",
             "Start: on the target, at the target pixel nearest the sheet centre. The original centre start "
             "left an inked 'tail' to the shape.",
             "A RANDOM on-target start was tried first and backfired: the line fell from 0.51 to 0.22 - "
             "extra variance the policy had to absorb.",
             "Evaluation: deterministic actions; scored on TRUE IoU. With a fixed target and a deterministic "
             "start, 'eval_eps = 8' replayed ONE episode eight times (pixel-identical) - found and documented.",
             "The ± in fixed-target tables therefore comes from training seeds, never from eval episodes."],
            cards=[("WHY A DETERMINISTIC START", ["Low-variance initial conditions make a specific target learnable; "
                                                  "randomising is a generalisation choice, not a free improvement."], VIOLET),
                   ("WHERE VARIATION IS REAL", ["Parameterised targets (16 distinct per set) and random cameras give "
                                                "evaluations with genuine variety."], GOOD)],
            notes="""
Episode design:
- Lambai: 240 steps (H4 me 60). Baad me pata chala agent pehle 10-17% me hi shape bana leta hai - baaki
  episode faltu (overrun finding, H6).
- Start: target par, centre ke sabse paas wale target pixel par. Pehle centre se start hota tha aur
  pen-always-down ki wajah se centre se shape tak ek "tail" ban jaati thi.
- Random start pehle try kiya - ulta nuksaan: line 0.51 se 0.22. Har episode alag start = extra variance.
- Evaluation deterministic hai. Fixed target + fixed start -> "8 eval episodes" asal me ek hi episode 8
  baar (pixel-identical) tha. Yeh pakda gaya aur documented hai - isliye fixed-target tables me +/- sirf
  training seeds se aata hai.

Generalisation experiments me (16 alag targets per set) aur random cameras ke saath evaluation me asli
variety hai.
""", source="rl/draw_env.py reset() comments; RESEARCH_LOG '### Start-tail fix (2026-08-07)' and "
            "'### Protocol finding - eval_eps=8 evaluates the same episode eight times'; 'UNEXPECTED FINDING'")

    tabular(prs, "07 · bugs", "Bugs that shaped the environment (all found by measuring)", None,
            ["bug", "what it did", "fix / consequence"],
            [["Stop action paid the success bonus", "+1.99 reward at step 1 on a blank canvas; the stop arm "
              "optimised a different reward", "'reached' separated from 'terminated'; arm re-run"],
             ["Perimeter under-measured ~1.9×", "path_ratio inflated on closed shapes (square '3.03' was really 1.59)",
              "RETR_LIST contours; values converted exactly, originals archived"],
             ["Smoothness over 4 dims", "dx/dy smoothing 25% weaker in the stop arm - a confound",
              "averaged over the first 3 dims always"],
             ["Camera only in the REWARD", "held-out-camera evaluation gave byte-identical drawings: it measured nothing",
              "with a camera, the agent also SEES through it"],
             ["Camera model (F4-F13)", "warp 56% of all degradation; 78% of 'train' draws were upsamples; "
              "phantom border ink; no saturation", "six fixes BEFORE the sweep"]],
            colw=[3.0, 5.0, 3.8], size=11.5, row_h=0.62, align="left",
            take="Pattern: a confound or bug that changes WHAT is measured is worse than a crash - it gives a "
                 "plausible, wrong number.", take_color=BAD,
            notes="""
Environment ke bugs - sab measurement se pakde gaye:
1) Stop action ko success bonus mil raha tha: step 1 par khaali canvas par +1.99. Stop arm asal me ek
   alag reward optimise kar raha tha - uska "collapse" kharida hua tha, seekha hua nahi. Fix + re-run.
2) Perimeter ~1.9x kam naapa ja raha tha (closed shapes ke annulus ka andar wala kinara chhoot raha tha)
   - path_ratio phool gaya. "Square ne 3 guna travel kiya" asal me 1.59 tha. Exact conversion kiya, purani
   files results/_pre_perimeter_fix/ me archived.
3) Smoothness penalty 4 dims par average - stop arm me dx/dy smoothing 25% kamzor - confound.
4) Camera sirf reward me tha, observation me nahi: held-out camera par evaluation me drawings
   byte-identical! Kyunki evaluation me reward hota hi nahi. Fix: camera ho to agent usi se DEKHE bhi -
   jo asli robot ka sach hai.
5) Camera model ke 6 issues (F4-F13) sweep se PEHLE review me theek.

Pattern yaad rakho: crash se bura woh bug hai jo ek plausible par galat number deta hai.
""", source="RESEARCH_LOG '## 2026-09-03 - Two bugs of mine, found by review' (BUG 1, BUG 2, third fix); "
            "'#### The design flaw the smoke test found'; '### Pre-run review of the perception model - six fixes'")

    tabular(prs, "07 · bugs", "Bugs in the METHOD (statistics and bookkeeping)", None,
            ["problem", "what went wrong", "rule adopted"],
            [["eval_eps = 8", "eight identical deterministic episodes", "use real variety (16 distinct targets)"],
             ["pooled sd as denominator", "O1 first read 'no measurable effect' - shape spread buried a real effect", "pair within (shape, seed)"],
             ["ddof = 0 vs 1", "error-bar overlap 'flipped' on the choice of sd", "sample sd (ddof = 1) everywhere"],
             ["adjacent seeds (F6)", "PPO re-seeds envs k…k+7: seeds 0 and 1 share 7 of 8 streams", "seeds 0, 100, 200, 300"],
             ["thread count", "same seed: IoU 0.175 on 2 threads, 0.195 on 1", "OMP=MKL=1; record threads"],
             ["absolute gap ≠ recovery", "interim H4 'camera wins' (t = 2.45) was a clean head start", "difference-in-differences"],
             ["mislabelled 'drop'", "DR printed +0.006; the true drop was +0.014", "recompute every difference"]],
            colw=[2.6, 5.6, 3.6], size=11.5, row_h=0.5, align="left",
            take="Every rule in AGENTS.md section 6 exists because one of these once produced a wrong number.",
            take_color=WARN,
            notes="""
Method ke bugs - statistics aur bookkeeping:
- eval_eps 8: aath identical episodes (deterministic).
- Pooled sd: O1 me pehle "no effect" aaya kyunki denominator me shapes ke beech ka farak bhi tha. Sahi:
  (shape, seed) ke andar paired.
- ddof 0 vs 1: n=3 par error bars ka overlap sd ke formula par flip ho gaya. Ab hamesha sample sd.
- F6: PPO(seed=k) envs ko k..k+7 se seed karta hai - seeds 0 aur 1 ke 7/8 streams same. Ab spaced seeds.
- Thread count: same seed, 2 threads par 0.175, 1 par 0.195. Ab OMP/MKL = 1 aur record.
- Absolute gap vs recovery: interim H4 me "camera jeeta" (t=2.45) asal me clean head start tha.
  DiD se recovery ~0 (t=0.30).
- DR me "drop" galat column se compare hua (+0.006 vs sahi +0.014).

AGENTS.md section 6 ka har rule isi list se aaya hai. Section 8 inhe detail me sikhata hai.
""", source="RESEARCH_LOG 'Protocol finding - eval_eps=8'; '#### A bug in this entry's own analysis' (O1); "
            "'### Statistics housekeeping'; 'fix F6' (2026-09-12); '### A reproducibility limit worth knowing'; "
            "'### Interim warning' (2026-10-19); '### Correction (2026-10-19)'")

    tabular(prs, "07 · summary", "Design choices at a glance", None,
            ["choice", "why", "alternative rejected"],
            [["pen-space action (dx, dy)", "portable across arms; physically realisable", "joint angles; Bézier strokes"],
             ["IoU-delta reward", "telescopes to final IoU; stray ink self-penalising", "coverage reward (scribbles); MSE"],
             ["potential shaping", "escapes 'draw nothing'; keeps the optimum", "sparse reward only"],
             ["pen always down (first rung)", "removes the no-ink trap", "learn pen up/down from the start"],
             ["start on target, nearest centre", "no tail; low variance", "centre start; random start"],
             ["64-px image observation", "same input type as a camera; fast", "state vectors (unfair to camera)"],
             ["fast proxy camera", "same reward signal (gap 0.010), ~270× faster", "real render every step"],
             ["score on TRUE IoU always", "no credit for fooling the camera", "score on perceived IoU"],
             ["PPO, SB3 defaults", "stable on CPU; algorithm not a variable", "SAC (~7.6 h/run; run later, far behind)"]],
            colw=[3.4, 4.6, 3.8], size=11.5, row_h=0.44, align="left",
            notes="""
Yeh poore environment ka cheat-sheet hai - har choice, uska kyun, aur kya reject hua. Interview se
pehle ise ek baar padh lena:
- Pen-space action: kisi bhi arm par chalega; Bezier strokes asli arm execute nahi kar sakta.
- IoU-delta: telescope hoke final IoU; coverage reward scribble karwata tha; MSE "kuch na karo" ko
  inaam deta.
- Potential shaping: "draw nothing" se bachata hai.
- Pen always down: no-ink trap hatata hai.
- Start on target: tail nahi, variance kam.
- Image observation: camera bhi image deta hai - fair comparison.
- Proxy camera: same signal, 270x tez.
- Score hamesha true IoU.
- PPO with defaults: algorithm variable nahi bana.
""", source="summary of the preceding Section 7 slides (each sourced there)")
