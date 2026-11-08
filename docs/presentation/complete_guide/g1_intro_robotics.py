"""Part 1 - opening, the project in one picture, foundations of robots / simulation / compute."""
from gk import *  # noqa: F401,F403
from gk import (ACCENT, BAD, BODY, CW, GOOD, INK, LINE, M, MUTED, NAVY, PRIMARY, SLATE,
                TINT_AMBER, TINT_BLUE, TINT_GREEN, VIOLET, W, H, WARN, WASH, WHITE, arrow,
                bullets, card, chip, concept, eqn, grid, kpi, node, note, pic, rect,
                section, slide, steps, strip, tabular, txt, img, analogy)
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN


def title(prs):
    from deck_kit import _blank, _state
    s = _blank(prs)
    _state["n"] += 1
    rect(s, 0, 0, W, H, fill=NAVY)
    rect(s, 0, 0, W, 0.20, fill=PRIMARY)
    rect(s, 0, 0.20, W * 0.42, 0.06, fill=ACCENT)
    txt(s, 1.1, 1.45, 11.2, 0.32, "THE COMPLETE GUIDE  ·  FROM SCRATCH TO RESULTS",
        size=12, color=ACCENT, bold=True)
    txt(s, 1.1, 1.95, 11.2, 1.5, "RoboSketch-RL", size=48, color=WHITE, bold=True)
    txt(s, 1.1, 2.85, 11.2, 0.8, "A robot arm that learns to draw from what its camera sees",
        size=24, color=RGBColor(0xC9, 0xD4, 0xE8))
    rect(s, 1.13, 3.75, 2.0, 0.035, fill=PRIMARY)
    txt(s, 1.1, 3.98, 10.8, 1.2,
        ["Every idea behind the project, explained from the basics: robots, simulation, "
         "reinforcement learning, the mathematics of PPO and SAC, computer vision, every "
         "hypothesis, every experiment, every mistake and what it taught us."],
        size=15, color=RGBColor(0xA9, 0xB6, 0xCE), spacing=1.3)
    rect(s, 1.1, 5.40, 11.1, 0.012, fill=RGBColor(0x2C, 0x3A, 0x5C))
    txt(s, 1.1, 5.62, 6.0, 1.0,
        ["Status as of 19 Oct 2026", "Simulation phase · H4 sweep complete (32/32)"],
        size=12, color=RGBColor(0xA9, 0xB6, 0xCE), spacing=1.35)
    txt(s, 7.0, 5.62, 5.2, 1.0,
        ["Unpublished research — do not share", "Every number traces to docs/RESEARCH_LOG.md"],
        size=12, color=RGBColor(0xA9, 0xB6, 0xCE), spacing=1.35, align=PP_ALIGN.RIGHT)
    note(s, """
Yeh deck poore project ko shuru se samjhata hai — maan ke chalo ki sunne wale ko robotics,
RL ya computer vision kuch nahi pata. Har section pehle basic idea deta hai (simple analogy
ke saath), phir uska math, phir hamare project me wo kahan aur kaise use hua.

Slides par English simple rakhi hai taaki guide / examiner ke saamne bhi chal sake.
Speaker notes Hinglish me hain — yeh aapke liye hain, bolne ki taiyari ke liye.

Ek zaroori baat: is deck ka har number docs/RESEARCH_LOG.md se aaya hai. Kuch bhi
"andaaze" se nahi likha. Jahan result pakka nahi hai, wahan saaf likha hai.
""")


def how_to_read(prs):
    s = slide(prs, "How to read this deck", "start here",
              "Colours carry meaning — the same colour always means the same kind of thing.")
    items = [
        (PRIMARY, "Structure", "what the system is, how it is built"),
        (ACCENT, "Vision / data", "cameras, images, measurements"),
        (VIOLET, "Learning / math", "RL concepts and derivations"),
        (GOOD, "Result", "something measured and logged"),
        (WARN, "Challenge", "a problem we hit, or a caveat"),
        (BAD, "Rejected / wrong", "an idea or claim that did not survive"),
    ]
    for i, (c, t, d) in enumerate(items):
        r, k = divmod(i, 3)
        x = M + k * 4.08
        y = 1.62 + r * 1.05
        rect(s, x, y, 3.9, 0.88, fill=WASH, line=LINE, shape=MSO_SHAPE.ROUNDED_RECTANGLE,
             radius=0.08)
        rect(s, x + 0.18, y + 0.24, 0.40, 0.40, fill=c, shape=MSO_SHAPE.ROUNDED_RECTANGLE,
             radius=0.25)
        txt(s, x + 0.75, y + 0.14, 3.0, 0.3, t, size=13, color=c, bold=True)
        txt(s, x + 0.75, y + 0.46, 3.1, 0.3, d, size=10.5, color=MUTED)
    bullets(s, [
        "Each topic goes in the same order: the everyday idea → the precise definition → "
        "the mathematics → where it appears in RoboSketch-RL.",
        "Blue strips marked SIMPLE ANALOGY give the intuition; read them first if a slide feels heavy.",
        "Tables show numbers exactly as the experiment scripts printed them. n = how many "
        "independent runs; t = the paired t-statistic (explained in Section 10).",
        "Speaker notes (below each slide) explain everything again in Hinglish.",
    ], M, 3.95, CW, 2.3, size=13)
    strip(s, "Rule used throughout: a result is only called a result if it was measured, "
          "logged, and survives a fair statistical test.", GOOD)
    note(s, """
Is deck me rang ka matlab fix hai: neela = system ka structure, cyan = camera / data,
purple = learning aur math, hara = measured result, peela/amber = challenge ya caveat,
laal = jo idea galat nikla ya reject hua.

Har topic ek hi order me aata hai: pehle roz-marra wali samajh, phir sahi definition,
phir math, phir hamare project me wo kahan use hua. Agar koi slide bhaari lage to neeche
wali "SIMPLE ANALOGY" strip pehle padho.
""")


def big_picture(prs):
    s = slide(prs, "The whole project in one picture", "overview",
              "A learning loop: the arm draws, a camera looks, a score comes back, the brain improves.")
    y = 2.05
    steps_ = [("TARGET", "a shape to draw\n(line, circle, …)", PRIMARY),
              ("AGENT", "neural network\n(the 'brain', PPO)", VIOLET),
              ("ARM + PEN", "KUKA arm in\nPyBullet simulation", PRIMARY),
              ("PAPER", "real ink lands\n(the true canvas)", SLATE),
              ("CAMERA", "photographs\nthe paper", ACCENT),
              ("SCORE", "IoU: how much the\ndrawing matches", GOOD)]
    bw, gap = 1.72, 0.33
    for i, (t, sb, c) in enumerate(steps_):
        x = M + i * (bw + gap)
        node(s, x, y, bw, 1.25, t, sb, color=c, title_size=13, sub_size=10)
        if i < len(steps_) - 1:
            arrow(s, x + bw + 0.04, y + 0.62, x + bw + gap - 0.04, y + 0.62, lw=1.6)
    # feedback arrow
    from deck_kit import elbow
    xa = M + 5 * (bw + gap) + bw / 2
    xb = M + 1 * (bw + gap) + bw / 2
    elbow(s, [(xa, y + 1.27), (xa, y + 1.85), (xb, y + 1.85), (xb, y + 1.29)],
          color=GOOD, lw=2.0)
    txt(s, xb + 0.4, y + 1.90, 6.5, 0.3, "reward: did the last move improve the drawing?",
        size=11.5, color=GOOD, bold=True)
    card(s, M, 4.45, 5.95, 1.75, "WHAT MAKES IT RESEARCH",
         ["Most drawing robots in the literature learn from a perfect digital copy of the "
          "drawing (the 'privileged canvas'). A real robot never has that — it only has a "
          "camera. We measure what is lost (and gained) by learning from the camera."],
         accent=VIOLET)
    card(s, M + 6.2, 4.45, CW - 6.2, 1.75, "WHERE WE ARE",
         ["Everything runs in simulation. The arm, ink, camera, learning and every "
          "experiment work end to end. Hardware (a ~₹10,000 6-DOF arm) comes only after "
          "the simulation results are solid."], accent=GOOD)
    strip(s, "One sentence: teach a robot to draw by trial and error, judged only by what its "
          "camera sees — and measure honestly whether that is as good as perfect information.",
          PRIMARY)
    note(s, """
Poora project ek loop hai. Ek target shape hai (jaise circle). Agent — yaani neural network
wala dimaag — decide karta hai pen ko thoda kidhar khiskana hai. Simulation me KUKA robot arm
pen ko wahan le jaata hai, paper par asli ink girti hai. Camera paper ki photo leta hai, aur
photo ko target se compare karke ek score banta hai (IoU). Score badha to reward positive.
Lakhon baar yeh loop chalta hai aur agent seekh jaata hai.

Research wali baat: zyada-tar papers me agent ko drawing ki perfect digital copy milti hai.
Asli robot ke paas aisi copy nahi hoti — sirf camera hota hai. Hum yeh naap rahe hain ki
camera se seekhne me kitna nuksaan (ya fayda) hota hai.
""")


def five_sentences(prs):
    s = slide(prs, "The project in five sentences", "overview")
    rows = [
        ("PROBLEM", "Teach a low-cost robotic arm to draw shapes (and later digits and letters) "
         "without programming the path — it must learn by trial and error.", PRIMARY),
        ("METHOD", "Reinforcement learning (PPO) in a PyBullet simulation; the agent moves the "
         "pen in small steps and is rewarded by how well the drawing matches the target.", VIOLET),
        ("TWIST", "The reward and observation can come from a simulated camera instead of the "
         "perfect digital canvas — which is the only thing a real robot would have.", ACCENT),
        ("CLAIM", "A measurement, not an invention: how much drawing accuracy is lost when the "
         "agent learns from perception instead of truth, and whether seeing the paper helps "
         "when things go wrong.", GOOD),
        ("GOAL", "An M.Tech thesis and an IEEE conference paper (ICRA / IROS / RA-L / CoRL); "
         "hardware only after simulation works.", WARN),
    ]
    for i, (lab, t, c) in enumerate(rows):
        y = 1.50 + i * 1.04
        chip(s, M, y + 0.22, 1.55, 0.42, lab, color=c, size=11)
        txt(s, M + 1.85, y + 0.10, CW - 1.9, 0.85, t, size=14.5, color=BODY, spacing=1.18)
        if i < len(rows) - 1:
            rect(s, M + 1.85, y + 0.98, CW - 1.9, 0.01, fill=LINE)
    note(s, """
Paanch line me project:
1) Problem — sasta robot arm drawing seekhe, path program kiye bina, khud try karke.
2) Method — PPO naam ka RL algorithm, PyBullet simulator me. Har step par pen thoda sa
   khiskta hai, aur drawing target se jitna milti hai utna reward.
3) Twist — reward aur observation camera se aa sakte hain, perfect canvas se nahi. Asli
   robot ke paas yahi hoga.
4) Claim — yeh koi naya algorithm nahi hai; yeh ek careful MEASUREMENT hai. Kitna accuracy
   jaata hai, aur kya camera galtiyon se ubarne me madad karta hai.
5) Goal — thesis + IEEE paper. Hardware tab, jab simulation pakka ho jaye.
""")


def agenda(prs):
    s = slide(prs, "Map of the deck", "agenda")
    secs = [
        ("01", "Robots, simulation & computers", "arms, kinematics, PyBullet, cores, threads"),
        ("02", "Machine learning & RL basics", "MDP, return, policy, value, neural nets, CNN"),
        ("03", "The mathematics of PPO", "policy gradient derived step by step, GAE, clipping"),
        ("04", "SAC and the PPO-vs-SAC comparison", "max-entropy RL, soft Q, why PPO first"),
        ("05", "Computer vision", "images, camera, thresholding, IoU and other metrics"),
        ("06", "The research problem & literature", "privileged canvas, 33 papers, hypotheses"),
        ("07", "System design", "simulator milestones, DrawEnv, reward design"),
        ("08", "Experiments and results", "H1 → H2 → H3 → overrun → O1 → Stage 2"),
        ("09", "H4 — the linchpin experiment", "disturbances, four arms, diff-in-diff"),
        ("10", "Statistics & research honesty", "paired t-test, pre-registration, mistakes"),
        ("11", "Status, roadmap & sim-to-real", "claims map, what is missing, hardware plan"),
        ("12", "Questions & glossary", "the hard questions, every term defined"),
    ]
    for i, (n, t, d) in enumerate(secs):
        r, k = divmod(i, 2)
        x = M + k * 6.15
        y = 1.48 + r * 0.88
        txt(s, x, y + 0.05, 0.75, 0.5, n, size=22, color=PRIMARY, bold=True)
        txt(s, x + 0.80, y + 0.04, 5.2, 0.3, t, size=13.5, color=INK, bold=True)
        txt(s, x + 0.80, y + 0.38, 5.2, 0.3, d, size=10.5, color=MUTED)
    note(s, """
Deck ke 12 hisse hain. Pehle 5 hisse "foundation" hain — robotics, RL, PPO ka math, SAC,
aur computer vision. Inhe samajh liya to baaki project apne aap samajh aayega.
Section 6 se project ki asli kahani shuru hoti hai: research problem, system design,
experiments, H4 (sabse important experiment), statistics, aur aage ka plan.
""")


# ------------------------------------------------------------------- section 1
def robots(prs):
    section(prs, 1, "Robots, simulation & computers",
            "Before any learning: what a robot arm is, how you tell it where to go, why we "
            "simulate first, and what the computer underneath is actually doing.",
            ["Links, joints, degrees of freedom", "Forward & inverse kinematics",
             "Task space vs joint space", "Physics simulation & PyBullet",
             "CPU cores, threads, RAM"])

    concept(prs, "01 · robots", "What is a robot arm?",
            "A chain of rigid links connected by motorised joints, ending in a tool.",
            ["Link = a rigid piece (like your upper arm). Joint = a motor that rotates one "
             "link relative to the previous one (like your elbow).",
             "Degrees of freedom (DOF) = number of independent joints. Each joint adds one "
             "way the arm can move.",
             "The tool at the end is the end-effector — for us, a pen.",
             "A pen tip on a flat sheet needs only x, y (where) + z (up/down) + keeping the "
             "pen vertical, so 6 DOF is plenty; 7 DOF adds redundancy (many poses reach the same point).",
             "Simulation uses the KUKA iiwa (7 DOF, bundled with PyBullet). Hardware target: "
             "a low-cost 6-DOF arm (~₹10,000, hobby servos)."],
            cards=[("WHY KUKA FOR NOW", ["Zero download, well-tested inverse kinematics, lets "
                                         "the drawing engine be built fast.",
                                         "Swapping arms later = swap the robot model file (URDF) "
                                         "+ IK. The learning part does not change."], PRIMARY),
                   ("ALTERNATIVES", ["Franka Panda (also bundled — one-line swap).",
                                     "A custom MG996R-servo arm model now: rejected — debugging "
                                     "a new arm model and the drawing engine at once is two hard "
                                     "problems at the same time."], SLATE)],
            analog="Your own arm: shoulder, elbow, wrist are joints; upper arm, forearm, hand are "
                   "links; the pen in your fingers is the end-effector.",
            notes="""
Robot arm = links (sakht tukde) + joints (motor wale jod). Hamara apna haath socho: kandha,
kohni, kalaai joints hain; upper arm, forearm, haath links hain; ungliyon me pakda pen
end-effector hai.

DOF matlab kitne independent joints. Paper par pen chalane ke liye x, y, z aur pen ko seedha
rakhna — 6 DOF kaafi hai. Simulation me KUKA iiwa (7 DOF) use kiya kyunki wo PyBullet ke
saath free aata hai aur uska IK achha tested hai. Asli hardware ~10,000 rupaye ka 6-DOF arm
hoga. Arm badalna = sirf robot ki model file (URDF) aur IK badalna; seekhne wala dimaag
same rahega — kyunki agent "pen kidhar jaye" sochta hai, "motor kitna ghume" nahi.
""")

    steps(prs, "01 · kinematics", "Forward kinematics: joint angles → pen position",
          "Easy direction: if you know every angle, geometry tells you where the pen is.",
          [("2-link", ["x = L₁·cos θ₁ + L₂·cos(θ₁ + θ₂)", "y = L₁·sin θ₁ + L₂·sin(θ₁ + θ₂)"],
            ["A planar arm with two links of length L₁, L₂ and joint angles θ₁, θ₂.",
             "Each link adds its own vector; the second link's angle is measured from the first."]),
           ("general", "T₀ₙ = T₀₁(θ₁) · T₁₂(θ₂) · … · Tₙ₋₁,ₙ(θₙ)",
            ["Real arms chain one 4×4 transform per joint (rotation + translation).",
             "Multiply them all: the last column of T₀ₙ is the tool position."]),
           ("in code", "p.getLinkState(arm, link)[4]  → world position of the link frame",
            ["PyBullet does this for us. A real bug here: index [0] is the link's centre of "
             "mass, not its frame — it silently reported a constant ~20 mm error until fixed "
             "to index [4]."])],
          take="FK is always unique: one set of angles gives exactly one pen position.",
          notes="""
Forward kinematics (FK) aasaan direction hai: saare joint angles pata hain to geometry se pen
ki position nikal lo. Do link wale arm ka formula slide par hai — har link apna vector jodta
hai.

Asli arm me har joint ke liye ek 4x4 matrix hoti hai, sabko multiply karo to pen ki position
mil jaati hai. PyBullet yeh khud karta hai.

Ek asli bug jo humne pakda: getLinkState ka index [0] link ka centre-of-mass deta hai, link ka
frame nahi. Isse har jagah ~20 mm ki galti dikh rahi thi. Index [4] lagane se theek hua.
Aisi chhoti galtiyan pura result bigaad deti hain — isliye har cheez measure ki.
""")

    tabular(prs, "01 · kinematics", "Inverse kinematics: pen position → joint angles",
            "The hard direction — and the bridge between the agent's decision and the motors.",
            ["IK variant (measured over 6 targets)", "mean position error", "pen tilt", "verdict"],
            [["position only", "0.003 mm", "41°", "pen slanted — useless"],
             ["position only + null-space hints", "0.911 mm", "41°", "worse"],
             ["position + orientation (pen vertical)", "0.007 mm", "0.00°", "CHOSEN"],
             ["position + orientation + null-space", "2.835 mm", "0.06°", "~400× worse"]],
            colw=[4.2, 2.2, 1.5, 3.0], cell_colors={(2, 3): GOOD, (0, 3): BAD, (3, 3): BAD},
            below=["IK answers 'which angles put the pen at (x, y, z)?' — there may be many "
                   "answers or none; PyBullet solves it numerically (calculateInverseKinematics).",
                   "Four problems had to be solved: wrong measurement point · pen orientation · "
                   "reachable area (safe box x 0.45–0.65 m, y ±0.20 m) · the wrist hitting the "
                   "floor (fixed with a virtual 10 cm pen).",
                   "Final validation over an 81-point raster: worst error 0.108 mm, tilt 0.001°, "
                   "0 points above 1 mm."],
            take="Lesson: small continuous moves are far more reliable for IK than big jumps — "
                 "and drawing naturally moves in small steps.", take_color=GOOD,
            notes="""
Inverse kinematics (IK) ulti direction hai: pen ko (x, y, z) par chahiye, to joints ko kitna
ghumana hai? Iske kai jawab ho sakte hain ya ek bhi nahi. PyBullet ise numerically solve
karta hai.

Table dikhata hai ki IK ko kaise configure kiya. Sirf position maangne par error tiny tha par
pen 41 degree tircha tha — drawing ke liye bekaar. Position + orientation (pen seedha) maangne
par 0.007 mm error aur 0 degree tilt — yahi chuna. "Null-space hints" madadgar lagte hain par
accuracy ~400 guna kharab karte hain.

Chaar problem solve kiye: galat point naapna, pen ka angle, arm kahan tak pahunch sakta hai
(safe box), aur kalaai ka zameen se takrana (iska hal: 10 cm ka virtual pen). Final result:
81 points par sabse badi galti 0.108 mm.
""")

    concept(prs, "01 · design choice", "Task space vs joint space — what the agent controls",
            "The agent says 'move the pen by (dx, dy)'; IK turns that into motor angles.",
            ["Joint-space action: the agent outputs a change for every motor (dθ₁ … dθ₇). "
             "Tied to one specific arm.",
             "Task-space action (ours): the agent outputs a pen nudge (dx, dy) and pen up/down. "
             "IK converts it to joint angles for whichever arm is attached.",
             "Consequence: the 'brain' is portable. Moving from the KUKA to a cheap 6-DOF arm "
             "changes only the robot model + IK, not the learned policy's meaning.",
             "The literature backs this: D01 rejects curve-based strokes because real arms cannot "
             "execute them; FRIDA measures the cost of an unrealistic action space."],
            cards=[("ACTION = [dx, dy, pen_down]", ["dx, dy in [−1, 1], scaled by a step size "
                                                    "(1.4 cm per step in the experiments).",
                                                    "pen_down in [0, 1]; for the first task rung "
                                                    "the pen is kept down (just trace)."], VIOLET),
                   ("TWO BACKENDS", ["use_arm=False: move the pen point directly — fast, used for "
                                     "training.", "use_arm=True: drive the real IK KUKA — slower, "
                                     "includes measured motor lag (2.8–4.8 mm)."], PRIMARY)],
            analog="Telling a driver 'go 10 m north' (task space) instead of 'turn the wheel 12° "
                   "and press the pedal 30%' (joint space) — the instruction works in any car.",
            notes="""
Agent kya control karta hai? Do option the. Joint space: har motor ko alag se bolo kitna
ghume — yeh ek specific arm se bandh jaata hai. Task space (hamara): agent sirf bolta hai
"pen ko dx, dy khiskao", aur IK usse joint angles me badal deta hai.

Fayda: dimaag portable hai. KUKA se sasta arm — sirf robot model aur IK badlega.
Analogy: driver ko "10 meter uttar jao" bolna, na ki "steering 12 degree ghumao aur pedal 30%
dabao". Pehli instruction kisi bhi gaadi me kaam karti hai.

Training ke liye fast backend use hota hai (pen seedha khiskta hai). Arm wala backend
realistic hai par slow.
""")

    grid(prs, "01 · simulation", "Why simulate first — and why PyBullet",
         "RL needs millions of tries. On a real arm that is weeks of wear; in simulation it is minutes.",
         [("WHAT A PHYSICS SIMULATOR DOES", ["Computes, many times a second, how bodies move "
                                              "under motor forces, gravity and contact.",
                                              "Gives exact ground truth for free (pen position, "
                                              "ink), which real life never does."], PRIMARY),
          ("PYBULLET (CHOSEN)", ["Runs natively on Windows; fast headless stepping for RL; "
                                 "pure Python; widely used in RL robotics papers.",
                                 "Installed from conda-forge — pip has no Windows wheel and "
                                 "needs a C++ compiler."], GOOD),
          ("GAZEBO (REJECTED)", ["Built for full-system realism with ROS; effectively needs "
                                 "Linux/WSL2. Not built for RL throughput."], BAD),
          ("MUJOCO (ESCAPE HATCH)", ["Faster, better contacts, free, common in recent RL papers. "
                                     "Not switching: our setup is already validated to 0.1 mm "
                                     "and the bottleneck is reward + vision, not physics speed."], WARN),
          ("WHAT WE SIMULATE", ["The arm (KUKA), the paper (a mesh with a texture), the ink "
                                "(a numpy image updated by the pen), and a virtual camera.",
                                "For training, ink is drawn straight into the image — far faster "
                                "than rendering."], ACCENT),
          ("THE PRICE", ["A simulation is never reality. Every hardware gap (servo lag, stroke "
                         "width, lighting) must be measured later — the 'sim-to-real' stage."], WARN)],
         cols=3, take="R03's core lesson for real-robot RL: train in simulation, transfer later.",
         notes="""
RL ko laakhon koshishen chahiye. Asli arm par yeh hafton ka ghisaav hai; simulation me minutes.
Physics simulator har second kai baar calculate karta hai ki cheezen motor force, gravity aur
contact se kaise hilengi — aur sach (pen kahan hai, ink kahan hai) free me deta hai.

PyBullet chuna kyunki Windows par chalta hai, tez hai, Python hai. Gazebo ROS ke saath Linux
maangta hai. MuJoCo achha alternative hai par hamara setup already 0.1 mm tak validate ho chuka
tha, isliye switch nahi kiya.

Keemat: simulation kabhi reality nahi hoti — servo ka lag, stroke ki motai, roshni — sab baad
me hardware par naapna padega. Ise sim-to-real kehte hain.
""")

    concept(prs, "01 · computers", "The machine underneath: cores, threads, RAM",
            "Why the experiments run two at a time, and why 'same seed' is not always 'same result'.",
            ["Core = one independent calculator inside the CPU. This laptop: 2 physical cores "
             "(4 logical via hyper-threading).",
             "One PPO training run keeps roughly one core busy, so 2 runs in parallel is the "
             "sensible maximum here. A third would slow all of them and risk running out of RAM.",
             "RAM = working memory. Each run holds a neural network, 8 environments and image "
             "buffers. Exhausting RAM crashes a process — a likely (unconfirmed) cause of the "
             "occasional 'exit code 4' crashes.",
             "Thread = a stream of work. The maths library can split one calculation across "
             "threads; the ORDER of floating-point additions then changes slightly.",
             "Measured: the same seeded run gave IoU 0.175 with 2 threads and 0.195 with 1. "
             "So every sweep fixes OMP_NUM_THREADS=1."],
            cards=[("CPU vs GPU", ["A GPU has thousands of small cores — great for big image "
                                   "networks. Our network is small, so the CPU is fine."], PRIMARY),
                   ("RESUMABLE SWEEPS", ["Every finished run is appended to a results file at "
                                         "once; a crashed sweep restarts and skips what is done."], GOOD)],
            analog="Cores are chefs, RAM is counter space. Two chefs cook two dishes well; a third "
                   "dish with no counter space ruins everything.",
            notes="""
Core = CPU ke andar ek chef. Is laptop me 2 physical cores hain (4 logical). Ek PPO training
lagbhag ek core busy rakhti hai, isliye 2 runs ek saath chalte hain. Teesra chalaya to sab slow
aur RAM khatam hone ka khatra.

RAM = counter ki jagah. Har run me neural network, 8 environments aur images rehte hain. RAM
khatam = process crash. "Exit code 4" wale crash shayad isi wajah se — par confirm nahi hai.

Thread = kaam ki ek dhaara. Math library ek calculation ko kai threads me baant sakti hai, aur
tab decimal numbers jodne ka order thoda badal jaata hai. Isse same seed par bhi result badal
gaya: 2 threads par IoU 0.175, 1 thread par 0.195. Isliye ab har sweep OMP_NUM_THREADS=1 se
chalta hai. "Same seed" ka matlab "same result" tabhi hai jab thread count bhi same ho.
""")


def build(prs):
    title(prs)
    how_to_read(prs)
    big_picture(prs)
    five_sentences(prs)
    agenda(prs)
    robots(prs)
