# RoboSketch-RL — Proposed Revisions After the Literature Review

**Date:** 2026-08-12
**Basis:** [`research_papers/README.md`](../research_papers/README.md) (33 papers, ranked),
[`research_papers/STUDY_NOTES.md`](../research_papers/STUDY_NOTES.md) (per-paper analysis, 8 read in full),
[`research_papers/COMPARATIVE_ANALYSIS.md`](../research_papers/COMPARATIVE_ANALYSIS.md) (synthesis and gap map).

> **Nothing in the project has been changed.** This document proposes changes and explains
> the evidence for each. Decisions are yours; each item is separable and independently
> reversible.
>
> — *original note, 2026-08-12; superseded, see below.*

> **STATUS UPDATE — 2026-09-03.** §8 **Stage 1 has been executed** (research log,
> 2026-08-23). O1, the §4.5 metrics and the §4.2 / H3 analysis are implemented and measured;
> an **unplanned Stage 1b** (§4.8, the overrun/overshoot effect — the one consequential
> finding this review did not anticipate) is running now. Completed proposals are
> **annotated in place and left intact**, including the one the review got wrong, so the
> predictions can still be read against what actually happened. Status keys used throughout:
> **✅ done · 🔵 in progress · ⬜ untouched · ❗ the review was wrong about this.**

---

## 0. The one-paragraph summary

The literature **confirms the project's premise and sharpens its claim**. The gap RoboSketch-RL
targets — a drawing agent that learns from what a camera sees rather than from privileged
ground truth — is explicitly named as unaddressed future work by the three closest papers
(ICRA 2019, ICRA 2022, ICRA 2024). However, the review also shows that (a) "reward from
perception" is not itself new (RSS 2017, RSS 2019 — we must cite, not claim it), (b) our
simulated camera is currently too idealised to support the H2 claim as strongly as it could,
and (c) one experiment is close to essential and is currently missing: **a demonstration that
visual feedback fixes an error that the alternative — forward-kinematic tracking, used by our
closest competitor — cannot.** Alongside these, the review surfaced several cheap environment
improvements, each backed by two or more independent papers.

---

## 1. Revised research positioning

### 1.1 Keep the problem statement

Unchanged, and now well-supported: *a robotic arm that learns to draw through reinforcement
learning, guided by visual feedback of its own drawing, transferable to low-cost hardware.*

### 1.2 Replace the novelty statement

**Current framing** (README): *"teaching the robot how to learn to draw rather than programming how to draw."*

This is true but it is **not a research contribution** — D01, D02, D05, D07, D08 and D09 all
teach robots/agents to learn to draw. A reviewer would reject this framing immediately.

**Proposed framing:**

> Existing learning-based drawing agents are rewarded from a *privileged* signal — an exact
> virtual canvas (D01, D02, D05, D09) or a supervised stroke plan (D03) — which does not exist
> on physical hardware. Systems that do observe the real canvas use vision for *replanning*
> (FRIDA) or *error recovery* (Liu et al.), never as the learning signal. Consequently the
> field does not know **what accuracy is lost when a drawing agent learns from perception
> instead of from truth.** We measure it.

This is defensible because it is a **measurement**, not an invention claim, and because the
three closest papers state the gap themselves:

| Paper | Venue | Their own words |
|---|---|---|
| D01 Lee et al. | ICRA 2022 | *"using a camera as an observation of canvas in the future work could be of great help in the synchronization step…"* |
| D03 Kotani & Tellex | ICRA 2019 | *"we are interested in closing the learning loop by enabling the robot to inspect what it has drawn…"* |
| D09 Luo et al. | ICRA 2024 | *"…a lack of real-world training scenarios to bridge the sim2real gap. We leave these challenges as our future work."* |

### 1.3 Add a mandatory related-work acknowledgement

R01 (Sermanet et al., RSS 2017) and R02 (Singh et al., RSS 2019) established learning from
perceptual rewards in manipulation. **These must be cited prominently.** Our position relative
to them: theirs is a *binary success classifier* for manipulation; ours is a *dense spatial
reward* for drawing, which is what makes a quantitative accuracy-equivalence result possible
at all.

---

## 2. Revised research questions and hypotheses

Current project hypotheses are H1 (RL can learn to draw) and H2 (vision reward ≈ truth reward).
Proposed set:

| ID | Statement | Status | Evidence needed |
|---|---|---|---|
| **H1** | A model-free RL agent can learn to draw geometric targets in pen space without demonstrations. | ✅ shown (IoU 0.36–0.51, single-run) | ✅ multi-seed sweep complete (4 shapes × 2 modes × 3 seeds); note §4.8 — these are *post-overshoot* scores |
| **H2** | An agent rewarded **only from camera perception** reaches drawing accuracy statistically indistinguishable from one rewarded with privileged ground truth. | 🟡 shown for **one idealised camera** (0.41 vs 0.45); the n=3 sweep gap is 0.028 | multi-seed + **§4.1 domain randomization** + **§4.8 — the overshoot confound must be cleared before write-up** |
| **H3** *(new)* | The perception-rewarded agent does **not** learn to exploit the camera model (i.e. the gap between perceived and true IoU does not grow during training). | ✅ **shown** (2026-08-23): mean gap **−0.0001** over 3328 episodes, corr(true, perceived) 0.997–0.999, truth-control gap exactly 0.000000 | **§4.2 — done.** ❗ It was *not* runnable on existing data: per-episode logging had to be added and all four shapes re-run. Limits: n=1 seed/shape, and re-test under §4.1 |
| **H4** *(new)* | Closed-loop visual feedback **recovers from execution disturbances that forward-kinematic tracking cannot detect** (pen slip, paper shift, ink failure). | ⬜ untested | **§4.3 — the linchpin experiment** |
| **H5** *(new)* | Error in an open-loop drawing plan **grows with stroke count**, while a closed-loop policy's does not. | ⬜ untested | §4.4 (reproduces FRIDA Fig. 11 in our setting) |
| **H6** *(new 2026-08-23 — **not anticipated by this review**)* | The reported final IoU **understates what the policies learned**: agents complete the shape in the first ~15% of the episode, overshoot it, then idle on a frozen canvas for ~74% of the episode. Camera-rewarded agents lose ~2× as much to this as ground-truth ones, so **H2's gap may be an artifact of when we stop measuring rather than of what the agents learned.** | 🔵 the effect is **measured** (mean 0.064 IoU lost, n=1 per cell); the **confound on H2 is a hypothesis under test, not a result** | **§4.8** — overshoot ablation (running), **plus a re-run of the H2 sweep logging peak IoU alongside final IoU**, n=3 |
| **RQ3** | How do PPO and SAC compare on this task? | ⬜ planned | equal-env-steps **and** equal-wall-clock, ≥5 seeds |
| **RQ4** *(new)* | Does the shape curriculum (line→circle→square→triangle) actually help? | ⬜ untested | §4.6 — jump-start / time-to-threshold (R04) |

H3 and H4 are the two additions that most strengthen the paper. H4 in particular is what
answers our closest competitor. **H6, added after the fact, now outranks both in urgency** —
until it is settled, the H2 number itself is in question (§4.8).

---

## 3. Proposed changes to the RL formulation

Each item lists its evidence, effort, and expected value. **None have been implemented.**
*(2026-08-12.)* **Status 2026-09-03: O1 is implemented behind a default-off flag and measured**
(status note under §3.1); **every other item in this section is still untouched.** A2 has since
acquired a second, independent motivation it did not have on 12 Aug — see §4.5.

### 3.1 Observation — three changes

| # | Change | Why | Evidence | Effort |
|---|---|---|---|---|
| **O1** ✅ | **Add remaining-time to the observation** (a normalised `t/max_steps` scalar or a constant-valued 4th channel). | The episode is hard-truncated at `max_steps=120`, but the agent cannot see how many steps remain. Two identical canvases with 5 vs 100 steps left require different actions — so the task is currently **partially observable**, and PPO is being asked to solve an impossible inference. | **D02** puts the step number `t` in the state for exactly this reason: *"the step number t acts as additional information to instruct the agent the remaining number of steps."* | trivial |
| **O2** ⬜ | **Add an egocentric crop** — a second observation stream centred on the pen (e.g. a 32×32 window of target + canvas around the pen tip), alongside or instead of the global view. | Our global 64×64 view forces the agent to locate the pen and reason about fine placement at coarse resolution simultaneously. | **Strongest converged finding in the review.** D03's 5×5 local extraction is worth **4× stroke accuracy** in ablation (0.963 → 0.157 without it). D08 independently: egocentric windows *"render training … feasible."* D01 bounds the stroke to a square around the pen. | low |
| **O3** ⬜ | **Use a spatially-aware CNN** — CoordConv first layer, or a spatial-softmax head — instead of SB3's default `NatureCNN`. | A plain CNN is translation-invariant and structurally cannot represent absolute position; our pen-marker channel is a hand-rolled workaround for this. | **D02** uses CoordConv in both actor and critic. **F05** (Levine et al.) introduced spatial softmax for precisely this class of spatial robot task. | low |

**✅ O1 — status: implemented and measured (2026-08-23).** `DrawEnv(time_in_obs=True)` appends
a constant-valued 4th channel = `255 · steps / max_steps`. **Default is `False`**, so every
number recorded before that date stays reproducible — verified by reloading the 3-channel
`models/ppo_square_kin.zip` and reproducing IoU 0.470 exactly, and independently by reproducing
the 12 Aug `line / truth / seed 0` cell (0.334 vs 0.3337) through the modified code path.
Ablation: 4 shapes × 3 seeds × 2 arms × 200k steps, ground-truth reward, identical protocol on
both arms (`rl/o1_ablation.py` → `results/o1_ablation.jsonl`). Reward is truth throughout, so
O1's observability question is never confounded with H2's perception question.

| metric (paired within shape × seed) | mean Δ | sd | pairs up | t | reading |
|---|---|---|---|---|---|
| **IoU** | **+0.039** | 0.062 | **9/12** | +2.17 | suggestive, not conclusive |
| peak IoU | +0.040 | 0.062 | 9/12 | +2.22 | probably real |
| overshoot | +0.001 | 0.034 | 5/12 | +0.11 | **no effect** |
| path_ratio | +0.998 | 3.835 | 7/12 | +0.90 | no effect |

**Verdict: a modest, shape-dependent gain — real enough to keep, too small to headline.**
Triangle (+0.073, all three seeds up) and square (+0.064) carry it; line is marginal (+0.026)
and circle is flat-to-negative (−0.008). No variance claim is available: seed spread narrowed on
two shapes and widened on two.

❗ **The mechanism predicted for O1 was wrong.** The stated reason for expecting it to matter was
that the end of the episode is where the damage happens and O1 tells the agent the end is coming.
Measured overshoot change: **+0.001, 5/12 pairs, t = 0.11 — completely flat.** O1 helps, but not
by fixing the overrun; that problem is untouched by it and belongs entirely to §4.8. O1 also does
*not* reduce wandering — `path_ratio` moved the wrong way on balance, and roughly doubled on the
square (2.68 → 6.19) while that shape's IoU improved.

**Decision: keep the flag, leave the default off for now.** It is not free — a 4th channel
changes the observation shape and invalidates every saved 3-channel model — and a +0.04 effect
does not justify breaking compatibility while the overrun, which costs 0.064 and may interact
with it, is unsettled.

*(An analysis bug worth recording: the first verdict this harness printed was "no measurable
effect", because it compared the mean change against the std of all baseline runs **pooled**,
which contains the shape-to-shape spread as well as seed noise. Both arms share seeds, so the
correct test is paired within (shape, seed). The wrong number was on screen first.)*

### 3.2 Action — two changes

| # | Change | Why | Evidence | Effort |
|---|---|---|---|---|
| **A1** | **Action chunking**: predict `k` pen moves per policy step (start with `k = 3–5`), execute them in order, and discount by `γ^k`. | Currently one `(dx, dy)` per step, with jerkiness suppressed by a hand-tuned `smooth_penalty=0.02`. Chunking produces smooth strokes *structurally* rather than by penalty. | **D02's "Action Bundle"**, `k=5`, in our exact task family: *"significantly improves the performance and the learning speed."* **A04** (Diffusion Policy) generalises this to SOTA. | low |
| **A2** | **Re-enable pen up/down before the digits/letters rung** (`pen_always_down=False`, and train the `action[2]` head). | With `pen_always_down=True`, every multi-stroke glyph (`4`, `5`, `i`, `E`) is *unreachable* — the agent must draw a connecting stroke, which is stray ink and hard-caps achievable IoU. | **F06** (sketch-rnn) — the `(Δx, Δy, pen-state)` representation our action space already mirrors. D01, D03 and D09 all carry an explicit pen/touch bit. | medium |

### 3.3 Reward — two changes, and one deliberate non-change

| # | Change | Why | Evidence | Effort |
|---|---|---|---|---|
| **R1** | **Normalise the reward** by the target's initial "distance" (e.g. divide the IoU-delta term by the target area, or by `L(s₀)`), so reward scale is comparable across shapes. | `iou_weight * ΔIoU` is unnormalised, so a large-area target and a small-area target produce systematically different reward magnitudes. Harmless with one policy per shape; **breaks the moment we train one policy over many targets** (§3.5). | **D08**: `r_t = (L(s_{t−1},s*) − L(s_t,s*)) / L(s₀,s*)`. | trivial |
| **R2** | **Sweep the terminal-bonus magnitude.** Ours is `+2.0` on top of `10 × ΔIoU`. | D09 uses a terminal reward of `80 · IoU` and states the large multiplier exists *"to improve the sensitivity of the SAC algorithm to reward shaping."* Ours may be far too small to shape behaviour at all. | **D09**. | trivial |
| — | **Keep IoU as the reward for geometric shapes.** | The field's dominant alternative is a learned discriminator (D01, D02, D05) — correct when targets are photographs with no canonical stroke decomposition. Our targets are **binary geometric masks**, where IoU is genuinely meaningful. **State this reasoning in the paper** so it reads as a considered choice rather than an oversight. | D02, D05, D01 (contrast); D03 and D09 both use IoU. | — |

### 3.4 Training procedure — one addition

| # | Change | Why | Evidence | Effort |
|---|---|---|---|---|
| **T1** | **Behaviour-cloning warm start.** Generate perfect expert trajectories analytically (trace the target outline), pre-train the policy on them, then refine with PPO/SAC. | Removes the exploration burden that our shaping terms (`prox_weight`, `start_on_target`, deterministic start) currently paper over — and would let us *ablate those crutches away*, which is a cleaner story. | Four independent papers use "prior → clone → refine": **D07** (demonstrated strokes), **D08** (BC initialises RL), **D09** (constrained exploration around a coarse sequence), **A07**. **And it is unusually cheap for us** — our analytic targets give free perfect demonstrations, which SPIRAL and Learning to Paint could not have. | low |

### 3.5 The one structural change worth considering — goal-conditioned drawing

**Current:** one policy per shape (`--shape line`, `--shape circle`, …), four separate agents.

**Proposed (optional, higher effort):** a **single goal-conditioned policy** `π(a | s, g)` where
`g` is the target mask, trained across many targets, with **HER-style relabelling** — treat the
canvas the agent actually drew as a target it succeeded at.

- **Why it is attractive:** it converts four specialists into one general drawing agent; it is the natural bridge to digits and letters; and HER replaces hand-tuned shaping with principled dense supervision. It is a substantially stronger result.
- **Evidence:** F04 (HER); D01's Commander is already goal-conditioned on the target image; D08 explicitly changes the reference image during training to prevent overfitting.
- **Honest caveat:** HER's guarantees are cleanest for low-dimensional goals; a full binary mask is high-dimensional. Treat this as a **research question with an experiment**, not a foregone conclusion.
- **Recommendation:** do **not** attempt this before H2/H3/H4 are settled. It is the right *next* paper, or the extension section of this one.

---

## 4. Proposed experiment programme

Ordered by (value ÷ effort). The first three are the ones that most change the paper.
**§4.8 was added on 2026-08-23 and is kept at the end only to preserve this document's
numbering — by value ÷ effort it now ranks first, and §8 sequences it first.**

### 4.1 ★★★★★ Perception domain randomization — *strengthens H2, no hardware needed*

**What.** Randomise `DrawEnv._perceive()` during training instead of using the fixed
`resize(150px) + threshold(>60)`: camera-pose jitter and perspective warp, lighting/exposure
gain, paper texture and off-white colour, ink-contrast variation, Gaussian blur, sensor noise,
threshold jitter.

**Why.** As written, `_perceive()` is a very optimistic camera. H2's current result is a claim
about *one idealised camera*, not about cameras. Randomising converts it into "vision reward
works across a distribution of realistic cameras" — a far more defensible claim, and the
standard sim-to-real practice.

**Evidence.** V01 (Tobin et al., IROS 2017).
**Measure.** True IoU of vision-trained agents under (a) the training camera, (b) held-out camera conditions never seen in training. Compare against the current fixed-camera agent.

### 4.2 ★★★★★ Reward-exploitation analysis (H3) — ✅ **DONE 2026-08-23: no exploitation found**

**What.** For every vision-trained run, plot `reward_iou − true_iou` against training steps.

**Why.** R02's central failure mode is a policy learning to **fool** the reward model. In
drawing there is a concrete mechanism: downsampling and thresholding can dilate thin strokes
and turn near-misses into apparent hits — so an agent could look accurate to the camera while
drawing worse. Nobody has tested this for drawing.

**Why it is nearly free.** `DrawEnv.step()` **already returns both values** in `info` —
`info["iou"]` (true) and `info["reward_iou"]` (perceived). If they are in the existing logs, this
is a plotting exercise; if not, it is a one-line logging change and a re-run.

❗ **Correction — the "runnable today, on existing data" claim was wrong.** `step()` does return
both values in `info`, but nothing was *storing* them: `results/h2_seeds.jsonl` records only each
run's **final** IoU, not the perceived/true pair over training. There was no plot to make. The
work actually needed an SB3 callback logging `(iou, reward_iou, gap, path_ratio, snr)` at every
episode end to `results/h3_<shape>_<mode>_s<seed>.jsonl` (`rl/h3_exploitation.py`), and a **full
re-run of all four shapes**. Cheap — but not free, and not retrospective. *(Lesson for the rest
of this document: "we already have the data" has to be checked against the log files, not against
the `info` dict.)*

**Either outcome is publishable.** A flat gap is strong positive evidence for H2. A growing gap
is a genuine finding about perceptual rewards in drawing.

**✅ RESULT (2026-08-23) — the camera reward is not being exploited.** 4 shapes × 200k steps,
camera reward, every episode logged (832 per run, 3328 total), plus a 200k `truth` control.

| shape | mean gap | max abs gap | gap over final 10% | corr(true, perceived) |
|---|---|---|---|---|
| line | −0.0049 | 0.0177 | −0.0095 | 0.9989 |
| circle | −0.0013 | 0.0290 | −0.0077 | 0.9970 |
| square | +0.0051 | 0.0210 | +0.0078 | 0.9985 |
| triangle | +0.0006 | 0.0232 | +0.0010 | 0.9969 |
| **all** | **−0.0001** | **0.0290** | — | — |

- 95% of all gaps fall within ±0.013; the largest single-episode excursion in the whole
  experiment is 0.029, still below the ±0.05 seed spread of the H2 sweep.
- The two signs cancel — line and circle slightly negative (the camera **under**-credits the
  agent), square and triangle slightly positive. No systematic direction, which is what a proxy
  with no exploitable structure looks like.
- **The control passed exactly:** a `truth` run has `reward_iou == iou` by construction, and its
  measured gap is 0.000000000 over 832 episodes — so the logging was known trustworthy *before*
  any vision run was interpreted.

**Claim (defensible):** across 200k steps of training on four shapes, a policy optimising
camera-perceived IoU gains **no measurable perceived-IoU credit it has not actually earned**.
R02's failure mode does not appear here. Unlike H2 itself, this is a statement about the
*training process*, not only the endpoint. **Honest limits:** n=1 seed per shape (the H2 sweep's
n=3 shows ±0.05 seed spread, so a small per-shape effect could hide inside this), and this tests
the *fast proxy* camera — a randomised camera (§4.1) has far more structure to exploit and must
be re-tested. Figure: `output/results_h3.png`.

### 4.3 ★★★★★ Disturbance recovery (H4) — *the linchpin experiment*

**What.** Mid-episode, inject a disturbance the agent was not told about:
1. **pen slip** — displace the pen by a few mm without updating the commanded position;
2. **paper shift** — translate/rotate the canvas mid-drawing;
3. **ink failure** — a stretch of steps where the pen deposits no ink.

Compare three conditions: **(a)** open-loop IK trajectory, **(b)** FK-synchronised closed loop
(D01's method — the agent believes its own kinematics), **(c)** vision-in-the-loop (ours).

**Why this is essential.** D01 argues camera-free is *more* robust because it ignores nuisance
visual variation, and it works well. **Without this experiment, D01 is a complete answer to our
motivation.** The whole justification for a camera is that it detects errors kinematics cannot
— an FK-synchronised agent believes the pen is where it commanded it, and ink failure is
literally invisible to it. This experiment turns our central claim from an assertion into a
measurement.

**Measure.** Final true IoU under each disturbance × each condition, ≥5 seeds.

### 4.4 ★★★★☆ Open-loop error growth (H5)

**What.** Plan once from the initial state and execute blind, vs. re-deciding each step from
the observed canvas, under realistic execution noise. Plot deviation against stroke count.

**Why.** FRIDA (A01, Fig. 11) measured exactly this on real hardware — without replanning,
deviation *"grows linearly as the plan is executed"* over ~800 strokes. Reproducing it in our
setting is cheap, gives a compelling figure, and directly supports the closed-loop premise.

### 4.5 ★★★★☆ Add the missing metrics — ✅ **SNR done (and honestly, uninformative for now)**

| Metric | Source | What it catches that IoU misses |
|---|---|---|
| **SNR** (stroke number ratio = drawn strokes / ground-truth strokes) ✅ | D09 | **Stroke fragmentation.** An agent can score decent IoU with a scribbly, discontinuous path. Notably **Learning to Paint scores worst of all methods on SNR (5.660)** — RL stroke agents are *specifically* prone to this, so it is likely present in ours and currently invisible. |
| **Δ sim2real** = MSE(simulated canvas, photograph of real canvas) | A01 | Transfer quality. We have no sim-to-real metric at all. Published reference points exist: 0.029 (FRIDA) / 0.066 / 0.156 (RL). |
| **Recognisability** (classifier confidence on the drawn canvas) | A03 (CLIPasso's argument) | **Legibility.** At the digits/letters rung, IoU rewards ink overlap, not whether a human (or a classifier) can read the digit. Nobody in the surveyed set reports this — adding it puts us *ahead* on evaluation. |
| **path_ratio** = pen travel ÷ target outline length ✅ | *(not proposed by this review — added 2026-08-23)* | **Wandering.** 1.0 = the outline traced once, efficiently. This is the metric that actually caught our observed defect. |

**✅ Status (2026-08-23): SNR implemented — and currently uninformative, which is worth saying
plainly.** `rl/metrics.py` now provides `stroke_count`, `snr` (D09's stroke number ratio),
`target_perimeter_px` and `path_ratio`; `DrawEnv.step()` now returns `snr`, `path_ratio` and
`iou_gap` in `info` at every step, and `rl/h3_exploitation.py`'s callback records them at every
episode end. SNR is implemented faithfully — verified by cutting a square target in two
places, which gives exactly 4 strokes and SNR 4.0. **But with `pen_always_down=True` the pen never
lifts, so the drawn ink is one connected trace *by construction*, and SNR is ≈1.0 no matter how
badly the agent draws** (trained square: SNR = 1.00). The review's reasoning for SNR was right —
RL stroke agents fragment — but our action space cannot express the failure it detects. **SNR
only becomes informative once pen up/down is enabled (A2), which is a second, independent
argument for A2 beyond the multi-stroke-glyph one in §3.2.**

**What caught the defect instead: `path_ratio`.** The trained square agent scores **3.03** — the
pen travelled three times the length of the outline it was tracing. That is the zig-zag and the
spurs, finally as a number; IoU alone could never have shown it. Not a metric this review
proposed.

⬜ **Δ sim2real** (needs hardware, §6) and ⬜ **recognisability** (needs the digits rung, Stage 6)
are unchanged and untouched.

### 4.6 ★★★☆☆ Curriculum measurement (RQ4)

Train `triangle` from scratch vs from a `line`-pretrained policy; report **jump-start**,
**time-to-threshold**, **asymptotic performance** (R04's standard metrics). Our shape ladder is
currently an untested assumption. A negative result is still an honest, reportable result.

### 4.7 ★★★★☆ Upgrade the classical baseline

Replace "traditional IK + trajectory planning" with **ergodic control** (D04) — a rigorous,
closed-loop, citable, general-purpose method for exactly our problem, with published variants
(CFEC / E-iSAC / PTO). Beating a hand-written IK follower is a strawman comparison; comparing
against ergodic rendering is a real result whichever way it lands.

*Also worth acknowledging in the paper:* FRIDA shows that **gradient descent through a
differentiable renderer** works very well. For a thin line, a differentiable ink model is easy,
so a reviewer will ask "why RL when you have gradients?" Our answer must be about
**unmodelled execution error** — and §4.3/§4.4 are what demonstrate it.

### 4.8 ★★★★★ The overrun / overshoot effect (H6) — 🔵 **the finding this review did not anticipate**

*Added 2026-08-23. Found by asking where §4.5's high `path_ratio` was coming from; it was on no
list. By value ÷ effort it belongs at the top of this section, and §8 now sequences it first.*

**What was measured.** Recording true IoU at *every* step of a deterministic evaluation
(`rl/overrun.py`), across 4 shapes × 2 reward modes:

| | ground-truth arm | camera arm | difference |
|---|---|---|---|
| **final** IoU (what H2 reports) | 0.450 | 0.411 | truth +0.039 |
| **peak** IoU (before the overshoot) | 0.493 | 0.496 | camera +0.003 |
| mean IoU lost to overshoot | 0.043 | 0.085 | **camera loses ~2×** |

Mean IoU lost across all eight cells: **0.064 — more than twice the entire 0.028 truth-vs-vision
gap that H2 sets out to measure.** The pattern is consistent: the shape is traced in the first
**~10–17%** of the episode (peak at step 12–41 of 240); a **short overshoot of 4–8 steps** right
after completion costs the IoU above; the canvas then **freezes**, with 0–1 px of new ink over
the whole second half. **A mean 74% of every episode is spent on a canvas that never changes
again** — at 200k steps per run, ~150k of them on frozen canvases.

**Why it happens.** `max_steps=240`, `pen_always_down=True`, and **there is no terminate action**.
Having drawn the shape, the agent cannot stop, cannot lift the pen and cannot end the episode.
Standing still (`dx=dy=0`, re-inking one pixel) is technically reachable but is a single point in
a continuous action space that a Gaussian policy with `ent_coef=0.02` will not land on exactly —
so it drifts past the outline, then settles.

**Why it matters to the paper's central claim.** Every IoU this project has reported is measured
**after** the overshoot, so the policies are better than their scores (peak 0.355–0.578 against
reported 0.319–0.505) — and the **camera arm is hit roughly twice as hard as the ground-truth
arm**. Scored at their peak the two are level (0.493 vs 0.496); scored at the end, ground truth
appears 0.039 ahead, which is close to the whole 0.028 gap the H2 sweep reports.

> ⚠️ **This confound is a hypothesis under test, not a result, and must not be quoted as one.**
> The eight cells above are the single-run 400k models in `models/`, **n=1 per cell**, not the
> 200k × 3-seed runs the H2 table is built from. What they establish is a specific, testable
> worry: *the small edge ground truth appears to hold in H2 may be an artifact of when we stop
> measuring rather than of what the agents learned.* Note the direction — it would make the
> project's central claim **stronger**, which is exactly why it must be checked rather than
> adopted. **The test:** re-run the H2 sweep logging peak IoU alongside final IoU (the sweep
> already runs the eval loop; it is a two-line change) and compare both columns at n=3. If the
> peak columns overlap more tightly than the final columns, the overshoot is confounding H2 and
> the environment must be fixed before the paper is written.

**Fixes, and what is already known about them.** Three switches are in `DrawEnv`, all **default
off** so nothing recorded earlier moves: per-episode `peak_iou` / `overshoot` / `steps_used`
reporting (free); `plateau_patience=k` (the *environment* truncates after k steps with no reward-
IoU improvement — `truncated`, not `terminated`, so the value function still bootstraps); and
`allow_stop=True` (a 4th action head, "I am finished" — `terminated`, because the agent choosing
to end really is the end).

A smoke test already settles one of them. Replaying the trained square agent at patience
off/40/20/10 cuts episode length from 240 steps to 81/61/51 — **~4.7× shorter with the drawing
completely unchanged (IoU 0.470, overshoot 0.034 at every setting)**. So `plateau_patience`
recovers the wasted sample budget but **cannot fix the overshoot, and never will**: a plateau
detector is *lagging* by construction — "no improvement for k steps" is only observable after the
peak has passed, and the square's damage is done between steps 41 and 47. **The overshoot can
therefore only be fixed by the policy itself**, which is what `allow_stop` tests, and which is
why the stop head cannot be retrofitted to existing models — it has to be trained.

**Status.** 🔵 `rl/overshoot_ablation.py` — arms `baseline` / `plateau` / `stop` × 4 shapes ×
seeds → `results/overshoot_ablation.jsonl`, running now in two shards. The verdict rule is
written to be hard to fool: an arm counts as a fix only if it cuts the overshoot **while holding
peak IoU**; cutting the overshoot by stopping early and drawing a worse shape is reported
separately as "stops too early". Early seed-0 numbers show exactly why that rule was needed — the
stop arm is best on line (0.516, 6 steps, zero overshoot) and clearly stops too early on square
(0.266) and circle (0.303).

**Also on the fix list, untested:** annealing `ent_coef`; **A2** pen-up so the agent can lift
instead of ink; and — free, and separate from any fix — **reporting peak IoU alongside final IoU
in every future table**.

---

## 5. Proposed evaluation protocol

Adopt R02's and R03's standards wholesale — this is what makes the results publishable.

1. **≥5 random seeds** per condition (R02 uses 5; R03 insists on reporting variance).
2. **Plot mean in bold with individual seeds faint behind it** (R02's figure convention) — not just error bars, which hide bimodal seed outcomes.
3. **Report a sparse ground-truth baseline** alongside the dense one. R02 found sparse ground-truth reward *fails on most seeds* while the learned visual reward succeeds — if that holds here it is a striking result.
4. **Held-out evaluation.** D02 holds out 2,000 test images specifically to test generalisation to unseen targets. Our four fixed shapes have no held-out set at all — we currently cannot distinguish learning to draw from memorising four shapes. **This is a real weakness a reviewer will find.** Fix: randomise shape parameters (radius, size, rotation, position) and hold out a parameter range.

   ❗ **A protocol finding (2026-08-23) that lands squarely on this item.** `experiment.py`'s
   `eval_eps=8` **evaluates the same episode eight times.** The evaluation is fully
   deterministic: `start_on_target` picks the target pixel nearest the paper centre (it is not
   drawn from the RNG) and `model.predict(deterministic=True)` adds no noise. Verified directly —
   the 8 eval episodes, with the protocol's exact seeds, produce **eight pixel-identical canvases
   and IoU std 0.000000000**, and the pen start is identical for reset seeds 0, 1, 2 and 12345.
   **This does not invalidate the H2 results:** their ±std comes from the **3 training seeds**,
   which genuinely differ. But `eval_eps=8` is a no-op costing 8× the evaluation compute for one
   number, and any future claim of the form "averaged over 8 episodes" would be false.
   **The fix belongs here, not as a separate patch.** Dropping `eval_eps` to 1 saves the compute
   but leaves the evaluation with no variance at all; the right repair is to introduce *real* eval
   variation through the parameterised held-out shapes proposed above — `eval_eps` counting
   **distinct sampled targets** rather than repeats of one. Until then, evaluation figures should
   be reported as **n=1 deterministic episode per run**, not as an 8-episode mean.
5. **Report both equal-env-steps and equal-wall-clock** for the PPO-vs-SAC comparison (RQ3). SAC does far more gradient work per environment step; an env-steps-only plot flatters SAC and a wall-clock-only plot flatters PPO.
6. **Qualitative results section** in the style of D06 — intermediate canvases and stroke order, not just final images. IoU tables alone will not convince a robotics reviewer that the agent learned to *draw*.

---

## 6. Sim-to-real (Phase D) revisions

The review changed the priority order here substantially.

| Priority | Item | Evidence | Note |
|---|---|---|---|
| **1** | **Fit the ink model from real strokes.** Draw at varying pen heights, photograph, measure widths, fit `z → stroke width`. Replace the hard-coded `0.0035 m` assumed stroke width. | **D09** does exactly this on a **Dobot Magician** (a low-cost arm, like ours). **A01** does the network version (`param2stroke`, L₁ 0.018 vs DiffVG 0.028). | **This is probably our largest single reality gap** and it is currently an unvalidated constant. Costs an afternoon and a ruler. |
| **2** | **Fit the camera model** the same way. `cam_px=150` and the `>60` threshold are guesses; measure them against the real webcam. | A01's real2sim2real principle. | Feeds directly into §4.1. |
| **3** | **Adopt Δ = MSE(sim canvas, photo of real canvas)** as the sim-to-real metric. | **A01** | Gives the hardware chapter a number, with published reference points. |
| **4** | **Dynamics randomization** of `_move_arm()`: `force`, `maxVelocity`, joint damping, and especially **control latency**. | **V02** (Peng et al.) | The simulated **KUKA iiwa** vs planned **MG996R hobby servos** gap is enormous — larger than what V02 addresses. |
| **5** | **Swap the KUKA URDF for a hardware-matched arm model** before claiming transfer. | — | Already a known limitation in the README. |
| **6** | **Plan the reset problem now, not later.** Who replaces the paper? What happens when the pen runs dry? | **R03** identifies automatic reset as a top real-robot RL blocker. | Free in simulation, expensive on hardware. Belongs in the hardware design. |
| **7** | **Choose and justify camera placement.** Overhead fixed (FRIDA) vs eye-in-hand (D08). | A01 vs D08 | Overhead suits a whole-canvas reward; eye-in-hand suits stroke precision. Also: **A01 notes indirect diffuse lighting is necessary — direct light causes glare that blinds the camera.** |

---

## 7. What should *not* change, and why

Equally important, and each now has a citation behind it.

| Keep | Why the literature supports it |
|---|---|
| **Pen-space `(dx, dy)` action with IK** | D01 explicitly rejects Bézier strokes for physical realisability; A01 *measures* the cost of an unrealisable action space (Δ = 0.156 for Learning to Paint vs 0.029 for FRIDA). Our conservative action space is on the right side of this. **State it as a deliberate choice in the paper.** |
| **IoU as the reward for geometric targets** | D03 ("pixel accuracy" = IoU) and D09 (terminal `80·IoU`) both use it. The discriminator alternative is for photographic targets without canonical decompositions. |
| **Simulation-first, hardware later** | R03's core lesson; PPO's on-policy sample cost makes real-robot training impractical. |
| **The research log** | R03's reproducibility emphasis. This is already a strength — few projects have it. |
| **Potential-based proximity shaping** | Potential-based shaping provably does not change the optimal policy. It is theoretically clean; keep it, but §3.4's BC warm start may let us *ablate it away*, which would be a cleaner story. |

---

## 8. Suggested sequencing

*Revised 2026-09-03. The original sequencing is preserved item by item; status is added, and
one stage (1b) is inserted that this review did not foresee. **The one substantive change of
order: Stage 1b now precedes Stage 2**, because until the overshoot question is settled the H2
number that Stage 2 sets out to strengthen is itself in question.*

**Stage 1 — finish what is running, then bank the two free wins (days)** — ✅ **COMPLETE (2026-08-23)**
1. ✅ Multi-seed sweep complete — 4 shapes × 2 reward modes × 3 seeds, `results/h2_seeds.jsonl`.
2. ✅ **§4.2 reward-exploitation analysis (H3)** — done. ❗ It was **not** "possibly just a plot over existing logs": the logs held only final IoU, so per-episode logging had to be added and all four shapes re-run. **Result: no exploitation** — mean gap −0.0001 over 3328 episodes, corr 0.997–0.999, truth control exactly 0.000000.
3. ✅ **O1** — implemented as `DrawEnv(time_in_obs=True)`, **default off**; measured **+0.039 IoU, 9/12 paired runs**, shape-dependent (triangle/square carry it, circle flat-to-negative). Kept; default stays off until the overrun work settles. ❗ It does **not** reduce the overshoot, which was the predicted mechanism.
4. ✅ **§4.5** — `snr` **and** `path_ratio` implemented (`rl/metrics.py`) and logged per episode. SNR is correct but **≈1.0 by construction while `pen_always_down=True`**, so it stays uninformative until A2; `path_ratio` is the metric that actually caught the defect (trained square: 3.03).

**Stage 1b — the overrun / overshoot effect (§4.8) — 🔵 RUNNING. Unplanned, and it now comes before Stage 2.**
5. ✅ Measured: agents finish in the first ~15% of the episode, lose a mean **0.064 IoU** to a short post-completion overshoot, then idle on a frozen canvas for **~74%** of the episode.
6. ✅ `plateau_patience` and `allow_stop` added to `DrawEnv`, both default off. Smoke test: `plateau_patience` cuts episode length **~4.7× with the drawing completely unchanged** — it recovers the wasted sample budget but **cannot** fix the overshoot (a plateau detector lags by construction).
7. 🔵 **`rl/overshoot_ablation.py`** — `baseline` / `plateau` / `stop` × 4 shapes × seeds, running in two shards → `results/overshoot_ablation.jsonl`. Early seed-0 data already shows the stop arm helping on line and stopping too early on square and circle, which is why the verdict rule requires holding peak IoU.
8. ⬜ **Re-run the H2 sweep logging peak IoU alongside final IoU, n=3, and compare both columns.** This is the actual test of the confound in §4.8, and **it gates the H2 write-up.** A two-line change to a sweep that already runs the eval loop.
9. ⬜ Report **peak alongside final IoU** in every table from here on — free, and independent of any fix.

**Stage 2 — strengthen H2 (1–2 weeks)** — ⬜ next, once item 8 has cleared
10. **§4.1** — perception domain randomization, then re-run H2. *Still the single change that most strengthens the existing result, and needs no hardware.* It also **re-opens H3**: a randomised camera has more structure to exploit than the fast proxy §4.2 tested.
11. **§5.4** — parameterised shapes with a held-out range, closing the "memorising four shapes" hole. **This item now also carries the `eval_eps=8` fix** (§5, item 4): it is the only repair that gives the evaluation real variance instead of eight copies of one episode.

**Stage 3 — the linchpin (1–2 weeks)** — ⬜ unchanged
12. **§4.3** — disturbance recovery (H4). *Without this, D01 answers our motivation.*
13. **§4.4** — open-loop error growth (H5).

**Stage 4 — environment improvements, measured as ablations (2–3 weeks)** — ⬜ unchanged
14. **O2** egocentric observation, **O3** CoordConv/spatial-softmax, **A1** action chunking, **T1** BC warm start — each as a controlled ablation, not a silent change. These are backed by multiple papers and are also *results in themselves*. (**O1** is already done and belongs in this table when the ablations are written up.)

**Stage 5 — comparisons and baselines** — ⬜ unchanged
15. **RQ3** PPO vs SAC with the fair protocol (§5.5).
16. **§4.7** ergodic-control baseline.
17. **§4.6** curriculum measurement (RQ4).

**Stage 6 — new capability** — ⬜ unchanged, but **A2 has gained two extra reasons** since 12 Aug: it is what makes **SNR** informative (§4.5), and pen-up is one of the candidate fixes for the overshoot (§4.8).
18. **A2** pen up/down, then the digits rung (QuickDraw / EMNIST / KanjiVG), with the **recognisability metric**.
19. *Optional, likely the next paper:* **§3.5** goal-conditioned policy + HER.

**Stage 7 — hardware (Phase D)**, in the §6 priority order.

---

## 9. Risk register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| A reviewer says D01 already solves this without a camera | **high** | fatal to the framing | **§4.3 is the answer.** Run it. |
| H2 does not survive domain randomization | medium | high | Still a publishable finding — "perceptual rewards for drawing are sensitive to camera realism" is a real result. Report it honestly either way. |
| Reward exploitation is found (H3 fails) | medium | medium | Also a genuine finding, and R02 supplies the fix (mixup-style smoothing of the perception model). |
| Our IoU (0.36–0.51) looks weak next to D03's 0.999 | **high** | medium | Different problems (they are supervised on stroke-ordered data with 1-px skeletonised targets). **Pre-empt it in the paper**: state the comparison explicitly and frame drawing accuracy as a *controlled variable*, not the contribution. |
| Low-cost hardware cannot execute the policy at all | medium | high | §6 items 1, 4, 5. D09 succeeded on a 4-DoF Dobot Magician, which is encouraging evidence at our price point. |
| **H2's gap turns out to be an overshoot artifact** (§4.8) — the agents are scored after a post-completion overshoot that costs the camera arm ~2× what it costs the ground-truth arm | medium *(hypothesis under test, n=1 per cell so far)* | medium — and note it would make our claim **stronger**, which is precisely why it must be checked and not adopted | Stage 1b item 8: re-run the H2 sweep with peak IoU logged, n=3, **before** the H2 write-up. Report peak and final side by side either way. |
| Scope creep from the long improvement list | **high** | medium | Stages 1–3 are the paper. Stages 4–6 are optional strengthening. Ship the paper on Stage 3. **Stage 1b is not scope creep** — it questions the validity of the Stage-1 numbers themselves. |

---

## 10. Answers to the two questions you will be asked first

**"Why RL, when supervised learning (D03) reaches 0.999 IoU?"**
Because D03 requires stroke-ordered demonstration data (KanjiVG), and because it is
**open loop** — it cannot correct execution error, which is exactly why its Baxter results
show *"significant error … due to position errors in the robot's end effector."* Our claim is
about learning **without demonstrations** and **correcting during execution**. §4.3 and §4.4
are what turn that from a claim into evidence.

**"Why RL, when gradient descent through a differentiable renderer (FRIDA) works better?"**
Because gradients require a differentiable, *accurate* model of the world. FRIDA's own results
show the gap that opens when the model is wrong (Δ = 0.156 for a mismatched stroke model), and
its replanning experiment shows deviation growing linearly without feedback. A learned policy
that acts on **observed** state does not need the model to be right. Again: §4.3 is the
evidence, not the assertion.

---

*Prepared 2026-08-12 after reviewing 33 papers (8 read in full); **at that date no project code
had been modified**.*

*__Updated 2026-09-03.__ Stage 1 has since been implemented and measured (research log,
2026-08-23), so this is no longer a proposal-only document. New code: `rl/metrics.py`,
`rl/h3_exploitation.py`, `rl/o1_ablation.py`, `rl/overrun.py`, `rl/overshoot_ablation.py`.
`rl/draw_env.py` gained the `time_in_obs`, `plateau_patience` and `allow_stop` switches and now
reports `iou_gap`, `peak_iou`, `overshoot`, `steps_used`, `path_ratio` and `snr` per step;
`rl/experiment.py::train_eval` gained `time_in_obs` and a generic `env_kwargs`; a genuine bug was
fixed in `rl/targets.py` (it ignored its `res` argument), proven not to move any recorded result
by diffing pre- and post-fix masks at res=512. **Every behavioural change is a flag whose default
is the old behaviour**, and the pre-existing numbers were re-derived to confirm it. Proposals
that have not been executed are unchanged and remain independently reversible; the sequencing in
§8 has been revised once, and remains a recommendation, not a commitment.*
