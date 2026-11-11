"""Section 12 - glossary, formula sheet (built from every labelled equation), self-test quiz."""
import kit
from kit import *  # noqa: F401,F403

GLOSSARY = [
    ("Action", "What the agent outputs each step: (dx, dy, pen)."),
    ("Actor-critic", "Policy (actor) + value estimate (critic) trained together; PPO and SAC are both."),
    ("Advantage", "How much better an action was than the policy's average in that state: A = Q - V."),
    ("Agent", "The learner: here a CNN policy trained with PPO."),
    ("Bellman equation", "V(s) = E[r + γ V(s')]: value is consistent over one step."),
    ("Binary mask", "Image whose pixels are on/off; here 255 = ink or target."),
    ("Canvas", "The 128×128 image of the true ink: the authoritative drawing."),
    ("Chamfer distance", "Mean distance between two ink sets; soft, forgives near misses."),
    ("Clean gap", "Difference between two arms with NO disturbance - a head start, not recovery."),
    ("Clip range ε", "PPO keeps the probability ratio's useful range to [1-ε, 1+ε]; ε = 0.2."),
    ("CNN", "Convolutional neural network: shared small filters slid over an image."),
    ("Confound", "A second difference between arms that could explain the result."),
    ("Coverage / precision", "Share of the target inked / share of ink on the target."),
    ("Critical t", "Threshold |t| for 'detectable' at 5%; 2.365 for 8 pairs."),
    ("D01", "Lee et al., ICRA 2022: camera-free robotic sketching - the objection H4 answers."),
    ("Damped least squares", "Numerical IK step: Jacobian least squares plus damping λ; PyBullet's default."),
    ("Difference-in-differences", "Compare how much each arm LOSES from its own clean score."),
    ("Discount γ", "Weight of future rewards; 0.99 here (horizon ~100 steps)."),
    ("DOF", "Degrees of freedom: number of independent joints (KUKA: 7)."),
    ("Domain randomisation", "Train across randomly varied simulators/cameras so the real one is 'one more sample'."),
    ("Egocentric (ego) view", "Observation window centred on the pen (O2)."),
    ("End-effector", "The tool at the arm's tip: the pen."),
    ("Entropy bonus", "Reward for keeping the policy spread out; ent_coef 0.02."),
    ("Episode", "One attempt from reset to end: 240 steps (60 in H4)."),
    ("Equivalence margin Δ", "Largest difference treated as 'practically none'; 0.05 IoU, fixed in advance."),
    ("F6", "Lesson: PPO(seed=k) re-seeds envs k..k+7, so adjacent seeds overlap."),
    ("fk arm", "H4 arm that sees what kinematics predicts it drew (D01's condition)."),
    ("Forward kinematics", "From joint angles to the tool position; unique and easy."),
    ("GAE", "Generalised advantage estimation: weighted sum of TD errors, λ = 0.95."),
    ("Generalisation", "Performance on data not trained on (held-out sizes/rotations, cameras)."),
    ("Gradient descent", "Repeatedly set θ to θ - α∇L: step downhill on the loss."),
    ("Held-out", "A set deliberately outside the training range, used only for testing."),
    ("Inverse kinematics", "From a tool position to joint angles; solved numerically."),
    ("IoU", "Intersection over union of ink and target; 1 = perfect."),
    ("Jacobian", "Matrix of ∂(tool pose)/∂(joint angle): local link between joint and pen moves."),
    ("Markov property", "Next state depends only on the current state and action."),
    ("MDP", "Markov decision process (S, A, P, R, γ): the model behind RL."),
    ("Null result", "No detectable difference at this n - not proof of no difference."),
    ("Observation", "What the agent sees: 64×64 image of target, drawn, pen."),
    ("Off-/on-policy", "Reuses old data from a replay buffer (SAC) / learns only from fresh data (PPO)."),
    ("Open / closed loop", "Execute a plan blind / re-aim from feedback every step."),
    ("Overrun / overshoot", "Agents finish early, overshoot the outline, then idle (H6)."),
    ("Paired design", "Both arms run on the same (shape, seed) cells; compare cell by cell."),
    ("Path ratio", "Distance the pen travelled ÷ target outline length; 1 = efficient."),
    ("Phase correlation", "FFT method to find the shift between two images (camera_est)."),
    ("Policy", "Map from observation to a distribution over actions."),
    ("Potential-based shaping", "Bonus γΦ(s') - Φ(s); guides without changing the optimum."),
    ("PPO", "Proximal policy optimisation: policy gradient with a clipped update."),
    ("Pre-registration", "Writing the analysis and its readings down BEFORE the runs."),
    ("Privileged", "Information available in simulation but not to a real robot (the exact canvas)."),
    ("Proxy camera", "Fast resize-and-threshold camera model; validated against a real render."),
    ("PyBullet", "The physics simulator used (Windows, fast, headless)."),
    ("Return G", "Discounted sum of future rewards - what RL maximises."),
    ("SAC", "Soft actor-critic: off-policy, max-entropy; run in RQ3: far behind PPO at our budget (0.051 vs 0.292 IoU)."),
    ("Seed", "Starting point of all random choices of a run."),
    ("SNR", "Stroke-number ratio: strokes drawn ÷ strokes needed."),
    ("Standard error", "Uncertainty of a mean: s/√n."),
    ("TD error δ", "r + γV(s') - V(s): surprise relative to the value estimate."),
    ("Terminated / truncated", "Episode ended by the task / cut by a limit (future still existed)."),
    ("TOST", "Two one-sided tests: shows equivalence within a margin."),
    ("Truth / vision reward", "Reward IoU from the exact canvas / from the camera image."),
    ("World / sheet frame", "Pen position on the table / on the (possibly shifted) paper."),
]

QUIZ = [
    ("What does this project claim is new?",
     "Nothing algorithmic: it MEASURES what learning from a camera instead of the exact canvas costs, and whether "
     "seeing the paper helps recovery. RL drawing, vision rewards and visual feedback all exist."),
    ("Why is D01 'the fatal objection', and which experiment answers it?",
     "D01 draws well with no camera, syncing by kinematics; if that is enough, a camera is pointless. H4 tests "
     "errors kinematics cannot see."),
    ("Why does the agent act in pen space (dx, dy) instead of joint angles?",
     "Portable across arms (only model + IK change), physically realisable, and IK handles the 7 joints."),
    ("What does damped least squares add to plain least-squares IK?",
     "λ²I keeps JJᵀ invertible near singular poses, so steps stay finite and smooth."),
    ("Why IoU and not MSE as the reward/score?",
     "MSE is dominated by background: a blank canvas can beat a decent attempt. IoU ignores background and "
     "punishes both missing and stray ink."),
    ("Why does the IoU-delta reward 'telescope'?",
     "Σ (IoU_t - IoU_t-1) = IoU_T - IoU_0: the return equals the final IoU (×10), so maximising return ≈ "
     "maximising the drawing's score."),
    ("Why was the pen forced down in most experiments?",
     "Early agents learned 'never ink' (no ink, no penalty). Forcing the pen down removed that trap; pen-up was "
     "tested later (A2)."),
    ("What does PPO's clipping do, in one sentence?",
     "It removes any gain from moving an action's probability ratio outside [0.8, 1.2] in one update, keeping "
     "updates small and stable."),
    ("What are γ, λ and ent_coef in our PPO, and why?",
     "γ 0.99 (whole drawing counts), λ 0.95 (default bias/variance), ent_coef 0.02 (more exploration to escape traps)."),
    ("Why must seeds be spaced (0, 100, 200, 300)?",
     "PPO(seed=k) seeds the 8 envs k..k+7; seeds 0 and 1 share 7 of 8 streams, so they are not independent."),
    ("What is a paired t-test here, and what is the critical value for 8 pairs?",
     "t = mean of per-cell differences ÷ (sd/√n), df = 7; |t| ≥ 2.365 is detectable at 5%."),
    ("Why difference-in-differences in H4?",
     "Arms start at different levels; only a smaller LOSS from each arm's own clean score is recovery. The "
     "interim 'camera wins' (t = 2.45) was a head start."),
    ("What did H2 find, exactly?",
     "Truth 0.388 vs camera 0.384, d = +0.004, t = +0.27, n = 12; 90% CI [-0.024, +0.033] → equivalent within "
     "±0.05 IoU (TOST p = 0.008)."),
    ("Why is 'no detectable difference' not the same as 'equivalent'?",
     "A null only fails to find a difference; equivalence needs TOST with a margin fixed in advance."),
    ("What did the camera-randomisation experiment show?",
     "Nothing gained (-0.011, t = -0.67); the fixed-camera agent lost only 0.014 on a camera recovering 0.394 of the ink."),
    ("Why were H4 v1 and H4-short null?",
     "The pen dot was in world coordinates: after a sheet shift no arm knew where the pen was on the paper; "
     "even the privileged arm did not recover."),
    ("What is camera_est, and what was its replicated result?",
     "A camera arm that estimates the sheet offset by phase correlation. Paper shift: loses 0.046 vs fk 0.165, "
     "+0.119, 8/8, t = +8.32; clean gap +0.006."),
    ("What did H5 show - and what did it NOT show?",
     "Open-loop error grows (linear for bias, √steps for jitter); closed loop stays flat. It shows feedback "
     "matters, not that a camera beats kinematics."),
    ("Is the agent good at drawing?",
     "Modest: IoU ~0.3-0.4; a scripted tracer reaches 0.72-0.74; it generalises poorly unless the view is "
     "pen-centred. Claims are about the reward-source gap."),
    ("Name three negative results.",
     "Camera randomisation bought nothing; the line-first curriculum hurt (0.246 vs 0.418); chunking hurt and "
     "BC/CoordConv/3× steps did not help held-out accuracy."),
]


def _glossary(prs):
    per = 22
    chunks = [GLOSSARY[i:i + per] for i in range(0, len(GLOSSARY), per)]
    for k, ch in enumerate(chunks, 1):
        s = slide(prs, f"Glossary ({k}/{len(chunks)})", "12 · glossary")
        half = (len(ch) + 1) // 2
        for col, part in enumerate((ch[:half], ch[half:])):
            x = M + col * (CW / 2 + 0.1)
            w = CW / 2 - 0.1
            rh = (6.95 - s._top) / max(1, half)
            for j, (term, d) in enumerate(part):
                y = s._top + j * rh
                txt(s, x, y, 2.2, rh, term, size=12.5, color=PRIMARY, bold=True, anchor=MSO_ANCHOR.MIDDLE)
                txt(s, x + 2.25, y, w - 2.3, rh, d, size=12, color=BODY, anchor=MSO_ANCHOR.MIDDLE)
                rect(s, x, y + rh - 0.01, w, 0.008, fill=LINE)
        note(s, f"""
Glossary part {k}. Har term ki ek-line definition. Revision ke liye: definition dhak kar khud bolne ki
koshish karo, phir check karo. Kai terms (PPO, IoU, TOST, diff-in-diff, F6) ke poore explanation pichhle
sections me hain - deck map se section dhoondho.
""", "definitions summarise the earlier slides of this deck (each sourced there)")


def _formula_sheet(prs):
    items = list(kit.FORMULAS)
    per = 12
    chunks = [items[i:i + per] for i in range(0, len(items), per)]
    for k, ch in enumerate(chunks, 1):
        s = slide(prs, f"Formula sheet ({k}/{len(chunks)})", "12 · formulas",
                  "Every labelled equation of the deck, in order of appearance.")
        half = (len(ch) + 1) // 2
        rh = (6.95 - s._top) / max(1, half)
        for col, part in enumerate((ch[:half], ch[half:])):
            x = M + col * (CW / 2 + 0.12)
            w = CW / 2 - 0.12
            for j, (group, label, latex) in enumerate(part):
                y = s._top + j * rh
                rect(s, x, y + 0.03, w, rh - 0.06, fill=WASH, line=LINE, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.08)
                txt(s, x + 0.12, y + 0.05, w - 0.2, 0.22, f"{group}  ·  {label}", size=9.5, color=VIOLET, bold=True)
                place_eq(s, latex, x + 0.12, y + 0.26, w - 0.24, rh - 0.34, size=20)
        note(s, f"""
Formula sheet part {k}. Yeh deck ke saare labelled equations hain, usi order me jaise aaye. Revision tip:
har equation ke liye teen cheezen bolo - (1) har symbol ka matlab, (2) project me kahan use hua,
(3) kyun. Agar atko, to label se original slide dhoondho (Section 2-8).
""", "equations as typeset on the earlier slides (rendered by kit.eq_png)")


def _quiz(prs):
    per = 5
    chunks = [QUIZ[i:i + per] for i in range(0, len(QUIZ), per)]
    n0 = 1
    for k, ch in enumerate(chunks, 1):
        for show_answers in (False, True):
            title = f"Self-test {k}/{len(chunks)}" + (" - answers" if show_answers else " - questions")
            s = slide(prs, title, "12 · quiz", "Answer aloud before moving on." if not show_answers else None)
            top = s._top + 0.02
            rh = (6.95 - top) / len(ch)
            for j, (q, a) in enumerate(ch):
                qa_card(s, M, top + j * rh, CW, rh - 0.1, f"{n0 + j}.  {q}", a if show_answers else None,
                        accent=GOOD if show_answers else PRIMARY, q_size=15)
            if show_answers:
                note(s, f"""
Quiz {k} ke jawab. Agar koi jawab galat gaya, to us topic ka section dobara dekho. Interview me jawab
isi length ke rakho - 1-2 sentences, ek number, ek limit.
""", "answers summarise earlier slides; numbers from RESEARCH_LOG RESULT entries cited there")
            else:
                note(s, f"""
Quiz {k}: pehle khud jawab do (zor se bol kar), phir agli slide par check karo. Har jawab me koshish karo:
kya, kyun, aur ek limit.
""")
        n0 += len(ch)


def build(prs, toc):
    section(prs, 12, "Review",
            "A glossary of every term, a formula sheet built automatically from every labelled equation in the "
            "deck, and a 20-question self-test with answers.",
            ["Glossary", "Formula sheet", "Self-test quiz", "Closing"],
            """
Section 12: revision. Glossary, formula sheet (deck ke saare equations ek jagah), aur 20 sawaalon ka quiz.
Interview se ek din pehle sirf yeh section aur Section 9-10 dekh lo.""", toc)
    _glossary(prs)
    _formula_sheet(prs)
    _quiz(prs)

    s = slide(prs, "The project in one breath", "closing")
    txt(s, M, s._top + 0.3, CW, 3.0,
        [{"t": "In simulation, a pen-drawing PPO agent trained from a camera reward is equivalent, within ±0.05 IoU "
               "(TOST), to one trained on the privileged canvas, and it does not exploit the camera.", "size": 20,
          "color": INK, "space_after": 14},
         {"t": "When the paper slides - an error kinematics cannot see - an agent that estimates the sheet offset "
               "from its own photo loses far less than a camera-free agent, in a pre-registered replication.",
          "size": 20, "color": INK, "space_after": 14},
         {"t": "No detectable gain for pen slip or ink failure; modest absolute accuracy; weak generalisation; "
               "simulation only. Next: a real arm and camera.", "size": 20, "color": BODY}], spacing=1.2)
    strip(s, "Measure carefully, pre-register, pair your comparisons, and report what you found - including what did not work.", GOOD)
    note(s, """
Poora project ek saans me - yeh teen sentences yaad kar lo:
1) Simulation me camera reward se trained agent, privileged canvas wale agent ke +/-0.05 IoU ke andar
   equivalent hai (TOST), aur camera ko exploit nahi karta.
2) Jab paper khisakta hai - jo kinematics dekh nahi sakta - apni photo se sheet ka offset estimate karne wala
   agent camera-free agent se kahin kam khota hai (pre-registered replication).
3) Pen slip / ink failure par koi detectable fayda nahi; absolute accuracy modest; generalisation kamzor;
   sirf simulation. Agla kadam: asli arm aur camera.

All the best, Viral!
""", "docs/paper/main.tex Abstract and Conclusion")
