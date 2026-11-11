"""Section 10 - what can and cannot be claimed; threats to validity."""
from kit import *  # noqa: F401,F403


def build(prs, toc):
    section(prs, 10, "What we can and cannot claim",
            "The claims map of docs/PAPER_PLAN.md: each claim, its evidence, its status, and the limits that "
            "must be said in the same breath. Then the threats to validity.",
            ["Claims map C1-C11", "Allowed vs forbidden wording", "Threats to validity",
             "Framing fixed before the H4 result"],
            """
Section 10: claims. Yeh section interview ke liye sabse practical hai - kya bol sakte ho aur kya nahi.
PAPER_PLAN ka rule: "use this wording or weaker, never stronger". Har claim ke saath uski limit bolni hai.""", toc)

    tabular(prs, "10 · claims", "The claims map (PAPER_PLAN section 2)", "Use this wording or weaker - never stronger.",
            ["#", "claim (short)", "status", "limit to say with it"],
            [["C1", "Camera reward ≈ truth reward: equivalent within ±0.05 IoU (TOST)", "READY", "4 shapes pooled, fixed pictures, proxy camera, 3 seeds"],
             ["C2", "The camera reward is not exploited", "READY", "1 seed per shape; fixed camera only"],
             ["C3", "Survives a much worse camera; randomisation adds nothing detectable", "READY", "2 seeds; effect carried by 3 of 8 axes"],
             ["C4", "Camera arm estimating the sheet offset loses less to a paper shift", "PARTIAL, REPLICATED", "paper shift only; simulation; estimator cost on slip/ink"],
             ["C5", "Agents finish early and overshoot", "READY / plateau AT RISK", "plateau stop not separable from a short horizon"],
             ["C6", "Time-left channel: modest, shape-dependent gain", "READY (minor)", "+0.039, 9/12; default off"],
             ["C7", "Seeded RL results are not thread-invariant", "READY (minor)", "reproducibility statement"],
             ["C8", "A scripted tracer (0.72-0.74) is far above the learner", "READY as a limit", "privileged tracer; claims are about the gap"],
             ["C9", "Line-first curriculum hurts", "READY as negative", "one naive curriculum, n = 6"],
             ["C10", "Pen-free: no detectable effect on final IoU, slower", "READY as a limit", "single-stroke shapes only"],
             ["C11", "IoU hides legibility (digits)", "EXPLORATORY", "n = 4 per group, no test, in-house recogniser"]],
            colw=[0.6, 5.0, 2.2, 4.0], size=10.5, row_h=0.42, align="left",
            cell_colors={(3, 2): GOOD, (4, 2): WARN, (10, 2): WARN},
            notes="""
PAPER_PLAN ka claims map - project ka "contract". Har claim ke saath status aur woh limit jo saath me
bolni hi hai:
C1 H2 equivalence (TOST) - limits: shapes pooled, fixed pictures, proxy camera, 3 seeds.
C2 no exploitation - 1 seed per shape.
C3 worse camera - 2 seeds, sirf 3 axes asar karte hain.
C4 H4 - PARTIAL, REPLICATED: sirf paper shift, simulation, estimator ki cost.
C5 overrun - real; plateau stop "fix" nahi.
C6 time channel - minor.
C7 thread non-invariance - reproducibility statement me.
C8 tracer limit - claims gap ke baare me hain, drawing quality ke nahi.
C9 curriculum negative. C10 pen-free limit. C11 digits exploratory.

Interview me kabhi kisi claim ko is table se zyada strong mat bolna.
""", source="docs/PAPER_PLAN.md section 2 (claims map C1-C11, status column)")

    s = slide(prs, "Wording: what to say, what never to say", "10 · wording")
    card(s, M, s._top + 0.05, CW / 2 - 0.1, 4.75, "SAY", [
        "'This is a measurement, not a new algorithm.'",
        "'No detectable difference' (when |t| < critical).",
        "'Equivalent within ±0.05 IoU in simulation (TOST, margin fixed before the run).'",
        "'In simulation, the camera arm that estimates the sheet offset lost less to a paper shift than the "
        "kinematics arm, in a pre-registered replication; no detectable advantage for slip or ink failure.'",
        "'The absolute level is modest; a scripted tracer is much higher.'"], accent=GOOD, start=15)
    card(s, M + CW / 2 + 0.1, s._top + 0.05, CW / 2 - 0.1, 4.75, "NEVER SAY", [
        "'novel', 'first', 'proves', 'outperforms', 'state of the art'.",
        "'No difference' / 'the same' (without TOST).",
        "'Cameras beat kinematics' (only one disturbance, one design).",
        "'The agent draws accurately' or 'generalises to arbitrary shapes'.",
        "'The plateau stop fixes the overshoot'; 'curricula do not work'.",
        "Any number from the absolute camera - fk gap as 'recovery'."], accent=BAD, start=15)
    strip(s, "Rule (PAPER_PLAN section 7): wording no stronger than the claims map; every number traceable to a log entry.", VIOLET)
    note(s, """
Kya bolna hai, kya kabhi nahi:
SAY: "measurement, not a new algorithm"; "no detectable difference"; "equivalent within +/-0.05 IoU (TOST)";
H4 ka exact sentence; "absolute level modest, tracer higher".
NEVER: novel, first, proves, outperforms; "no difference" bina TOST; "cameras beat kinematics" general me;
"agent accurately draws / arbitrary shapes"; "plateau stop fixes"; "curricula don't work"; absolute camera - fk
gap ko recovery bolna.

Paper ka check_paper.py in forbidden words par error deta hai - yeh rules automated hain.
""", "docs/PAPER_PLAN.md sections 2 and 7; AGENTS.md section 1; RESEARCH_LOG '### Paper scaffolding (2026-10-19)'")

    grid(prs, "10 · validity", "Threats to validity - and how each was handled", None,
         [("INTERNAL: REWARD ASYMMETRY", ["In H4 the fk arm is rewarded from the TRUE canvas - favouring fk. Stated; "
                                          "makes the camera win conservative."], WARN),
          ("INTERNAL: SEEDS & THREADS", ["Few seeds (2-3 per config); adjacent-seed overlap (F6); thread-dependence. "
                                         "Spaced seeds, OMP = 1, paired tests."], WARN),
          ("INTERNAL: FORKING PATHS", ["Four H4 designs. The series is labelled exploratory; v4 was replicated on "
                                       "fresh, pre-registered seeds."], WARN),
          ("EXTERNAL: SIMULATION", ["One arm model, a simulated near-fixed camera, pure-translation sheet shift, "
                                    "no real robot or camera at all."], BAD),
          ("EXTERNAL: TASK SCOPE", ["Four simple shapes, fixed pictures; agents generalise poorly; absolute IoU ~0.3-0.4."], BAD),
          ("CONSTRUCT: WHAT IOU MEASURES", ["IoU ignores zig-zag (path ratio) and legibility (digits). "
                                            "Peak IoU reported beside final."], WARN)],
         cols=3, notes="""
Threats to validity - reviewer kya bolega aur hamara jawab:
Internal (kya result sahi naapa?):
- Reward asymmetry: H4 me fk ko true canvas se reward - fk ke favour me; camera ki jeet isliye conservative.
- Seeds/threads: kam seeds, F6 overlap, thread dependence -> spaced seeds, OMP=1, paired tests.
- Forking paths: 4 H4 designs try kiye -> series exploratory; v4 ko fresh seeds par pre-registered replicate kiya.
External (kya bahar laagu hota hai?):
- Sirf simulation: ek arm, simulated camera, pure translation shift, koi real robot/camera nahi.
- Task scope: 4 shapes, fixed pictures, weak generalisation, IoU ~0.3-0.4.
Construct (kya metric sahi cheez naapta hai?):
- IoU zig-zag aur legibility ignore karta hai -> path ratio, peak IoU, recogniser.
""", source="docs/paper/main.tex 'Discussion and Limitations'; docs/PAPER_PLAN.md C1-C11 limits; RESEARCH_LOG H4 'Reward asymmetry'")

    tabular(prs, "10 · framing", "The paper's framing was fixed BEFORE the H4 result", "PAPER_PLAN section 3 - 'never pick the framing after looking at which one reads best'.",
            ["H4 outcome (primary diff-in-diff)", "paper framing"],
            [["Camera recovers better on ink failure (and it bites)", "full story: camera costs nothing (C1-C3) and buys recovery D01 cannot have"],
             ["Better on slip or paper shift only; ink failure uninformative", "PARTIAL: C4 stated only for the disturbance that showed it  ← what happened"],
             ["No detectable difference where disturbances bite", "honest negative: camera costs nothing but buys nothing; D01 supported"],
             ["Camera recovers worse", "report it; check the reward asymmetry first"]],
            colw=[4.6, 7.2], size=12.5, row_h=0.62, align="left", cell_colors={(1, 1): GOOD},
            take="Deciding the story before seeing the data is what makes the story believable.", take_color=VIOLET,
            notes="""
PAPER_PLAN section 3 me H4 ke har possible result ke liye paper ki framing PEHLE se likhi thi:
- Ink failure par camera jeete -> poori kahani.
- Sirf slip ya paper shift par jeete -> PARTIAL (yahi hua: paper shift).
- Kahin farak nahi -> honest negative; D01 supported.
- Camera haare -> report karo, asymmetry check karo.

Kyun? Result dekh kar "jo achha lage" woh kahani chunna - yeh bias hai. Pehle se tay karne se kahani par
bharosa hota hai.
""", source="docs/PAPER_PLAN.md section 3")
