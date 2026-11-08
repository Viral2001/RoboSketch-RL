# RoboSketch-RL — Comparative Analysis & Research-Gap Map

Cross-paper synthesis built on [`STUDY_NOTES.md`](STUDY_NOTES.md).
Written 2026-08-12, after the paper collection and the first deep-reading pass.

**Purpose.** Turn 33 papers into (a) a defensible statement of what is and is not already
done, (b) a list of findings that multiple independent papers agree on, and (c) an honest
assessment of where RoboSketch-RL's contribution actually lies — including the arguments
a reviewer would use against it.

---

## 1. The landscape: who does what

Every system that draws, compared on the axes that matter to us.

| Paper | Year | Learns? | Algorithm | Action space | Reward / objective | **Sees its own drawing?** | Real robot |
|---|---|---|---|---|---|---|---|
| **D04** Ergodic rendering | 2016 | ✘ control | ergodic (CFEC/E-iSAC/PTO) | continuous control | ergodic metric ε | closed-loop on **state** | Baxter |
| **D05** SPIRAL | 2018 | ✔ RL | distributed A2C | brush program | **discriminator** | canvas only (virtual) | ✘ |
| **D07** Learning to Sketch | 2018 | ✔ RL | DQN + demos | discrete strokes | pixel/perceptual | canvas only (virtual) | ✘ |
| **D02** Learning to Paint | 2019 | ✔ RL | model-based DDPG | Bézier, 13-D | **WGAN-GP discriminator** | canvas only (virtual) | ✘ |
| **D03** Teaching Robots To Draw | 2019 | ✔ supervised | seq. prediction (LSTM) | (Δx, Δy, touch), 5×5 local | cross-entropy vs demos | ✘ **open loop** | Baxter, MOVO |
| **D10** Multi-Pen 3D Drawing | 2021 | ✘ engineered | closed-loop planning | Cartesian strokes | geometric error | ✔ **vision + force** | industrial arm |
| **D01** From Scratch to Sketch | **2022** | ✔ RL ×2 | **SAC** (hierarchical) | (down, Δx, Δy) + Δjoints | **discriminator** | ✘ **forward kinematics only** | UR5e |
| **A01** FRIDA | 2023 | ✘ gradient planning | SGD thru diff. renderer | (h, l, b, x, y, θ, ρ) | CLIP / VGG / L₂ | ✔ **DSLR, replans** | Sawyer |
| **D08** Sim-to-Real Brush | 2023 | ✔ BC → RL | policy gradient | (α, l, w, c), 6-D | normalised L_{1/2} | canvas (**eye-in-hand**) | UltraArm |
| **D09** CalliRewrite | **2024** | ✔ unsup + RL | **SAC** | (δx, δy) on control pts | shape shaping + **80·IoU** | ✘ simulated tool only | Dobot Magician |
| **D11** SketcherX | 2024 | ✔ diffusion | LoRA diffusion + vectorise | vector strokes | perceptual/style | ✘ | custom arm |
| **RoboSketch-RL** | 2026 | ✔ RL | **PPO** (→ SAC) | **(dx, dy, pen)** pen-space | **IoU-delta + shaping** | ✔ **camera reward (H2)** | planned |

**Read the "sees its own drawing?" column.** It is the axis on which this project sits.

---

## 2. Convergent findings — where independent papers agree

These carry far more weight than any single paper's claim. Each is a design recommendation
with at least two independent sources.

### 2.1 Local / egocentric observation beats a global view — **strongest signal in the library**

| Source | Form | Evidence |
|---|---|---|
| **D03** (ICRA 2019) | Extract a **5×5×64 patch** centred on the pen from the encoded image | Ablation: removing the local model collapses stroke accuracy **0.963 → 0.157** |
| **D08** (2023) | **Egocentric window**: pen stays centred, canvas and reference crop around it | *"simplifies the action space, eliminates the need for a replay buffer, and renders training … feasible"* |
| **D01** (ICRA 2022) | Stroke bounded inside a **fixed-length square** around the current pen position | Chosen so the low-level controller has a tractable search space |

Three independent groups, three different architectures, same conclusion: **restrict what the
agent looks at, and what it can do, to a neighbourhood of the pen.**
`DrawEnv` currently gives a **global 64×64 view** with a pen-marker channel. This is the
outlier, and the best-supported change available.

### 2.2 Coarse plan → RL refinement beats pure RL exploration

| Source | Form |
|---|---|
| **D07** | DQN bootstrapped with demonstrated strokes |
| **D08** | Behaviour cloning initialises the RL policy; BC action space ⊂ RL action space |
| **D09** | Unsupervised LSTM produces a coarse stroke sequence; SAC refines **inside a constrained exploration tube** around it |
| **A07** | Sketch → 3-D trajectory prior → BC → RL refinement |

Four papers, one recipe. **And for us the prior is free**: our targets are analytic, so a
perfect expert trajectory can be generated in closed form. SPIRAL and Learning to Paint could
not do this (their targets are photographs). This is an unusually cheap win.

### 2.3 The action space must be *physically realisable*, not merely expressive

- **D01** deliberately rejects Bézier strokes: *"complicated stroke is not a best option when a stroke is physically rendered with real drawing tools … the stroke determined by the large parameter space is such a burden for the low-level physical controller."*
- **A01** *measures* the consequence: Learning to Paint's unconstrained strokes give a sim2real gap of **Δ = 0.156** vs FRIDA's **0.029** — *"the painting produced was vastly dissimilar to both the simulation and target image."*

**RoboSketch-RL's `(dx, dy)` pen-space action is on the right side of this.** It is a design
strength backed by both an argument and a measurement — and worth stating explicitly rather
than leaving as an unremarked choice.

### 2.4 Action chunking / bundling helps in this exact task family

- **D02**: "Action Bundle" — predict **k = 5** strokes per step; *"significantly improves the performance and the learning speed."*
- **A04** (Diffusion Policy): action-sequence prediction with receding-horizon execution is the current SOTA visuomotor formulation.

Our `smooth_penalty=0.02` is a heuristic surrogate for what chunking achieves structurally.

### 2.5 The tool/ink model is a first-class sim-to-real gap, and it must be *fitted*, not guessed

| Source | Method |
|---|---|
| **A01** | `param2stroke` network fitted to **photographed real brush strokes** (L₁ 0.018 test vs DiffVG 0.028) |
| **D08** | Recursive binary search over pressure, using **image analysis instead of force sensors** |
| **D09** | *"leave traces on the paper at varying z heights, measure widths, calculate r, and establish the z–r connection through linear fitting"* — on a **Dobot Magician**, a low-cost arm |

`DrawEnv` draws ink with `cv2.line(..., 2*pen_radius_px, LINE_AA)`, where `pen_radius_px`
comes from a hard-coded assumed stroke width of `0.0035 m`. **That constant is currently
unvalidated and is a strong candidate for our largest single reality gap.** D09's method costs
one afternoon and a ruler.

### 2.6 Open-loop drawing accumulates error — measurably

- **A01**, Fig. 11: without replanning, deviation from the initial plan *"grows linearly as the plan is executed"* over ~800 strokes.
- **D03**: Baxter's output shows *"significant error … due to position errors in the robot's end effector"*; MOVO (more precise) is much better.
- **D09**, Fig. 10: failure cases attributed partly to *"error accumulation in the robotic arm."*
- **D10**: an entire engineered error-detection-and-recovery subsystem exists for this reason.

**This is the empirical case for RoboSketch-RL's premise**, made by four independent papers.

---

## 3. Where do rewards come from? A taxonomy

Reward source is the field's real axis of variation — the controllers are largely
interchangeable.

| Reward source | Papers | Needs pixel-aligned target? | Needs demos? | Works on real hardware without instrumentation? |
|---|---|---|---|---|
| Pixel distance (L₂ / L_{1/2}) | D08, A01 (simple objective) | ✔ | ✘ | ✔ if the canvas is observable |
| **IoU / overlap** | D03 ("pixel accuracy"), D09 (terminal), **RoboSketch-RL** | ✔ | ✘ | ✔ if the canvas is observable |
| Learned discriminator (GAN) | **D01**, D02, D05 | ✘ | ✘ | ✔ but needs discriminator training |
| Perceptual (VGG / CLIP) | A01, A03, D09 (coarse stage) | ✘ | ✘ | ✔ |
| Ergodic metric | D04 | ✔ (as a distribution) | ✘ | ✔ |
| Learned goal classifier | **R02**, R01 | ✘ | goal images only | ✔ — this is the point |
| Geometric error to a planned path | D10 | ✔ | ✘ | ✔ with vision + force |

Two observations that matter for our paper.

1. **We are the only project in the table computing IoU from a *simulated camera perception* of the canvas rather than from the canvas itself.** Everyone else either computes the reward on the exact virtual canvas (D01, D02, D05, D09) or photographs a real canvas for *planning* rather than for a *learning reward* (A01, D10).
2. **But "reward from perception rather than privileged state" is established prior art** (R01 2017, R02 2019) in manipulation. We must cite it and must not claim the idea as new. Our claim has to be narrower and quantitative — see §6.

---

## 4. Evaluation metrics — what the field actually reports

| Metric | Used by | Measures | Blind to |
|---|---|---|---|
| IoU / "pixel accuracy" | D03, D09, **us** | ink overlap | stroke order, continuity, legibility |
| MSE / L₂ | A01, D02, **us** | pixel disagreement | structure |
| Chamfer distance | D09, **us** | contour proximity | topology |
| **SNR (stroke number ratio)** | **D09** | **stroke fragmentation** | placement accuracy |
| **Δ sim2real (MSE sim vs photo)** | **A01** | **transfer quality** | absolute drawing quality |
| Human preference study | A01 (103 AMT raters) | perceived quality | objectivity |
| Ergodic metric ε | D04 | multi-scale spatial match | stroke structure |
| Recognisability | *(nobody in this set)* | legibility | fidelity |
| Qualitative figures only | **D01**, D08, D11 | — | everything |

**Three findings.**

1. **D01 — our closest competitor — reports no quantitative drawing-accuracy metric at all.** Our multi-seed IoU/MSE/chamfer protocol is already more rigorous than the state of the art in robotic sketching RL. That is a legitimate secondary contribution and should be stated.
2. **We are missing two metrics the field has and we do not.**
   - **SNR** (D09) detects the scribbly/fragmented stroke failure mode that IoU cannot see. Notably, **Learning to Paint scores worst of all methods on SNR (5.660)** — RL stroke agents are *specifically* prone to this. It is very likely present in our agents and currently invisible to us.
   - **Δ sim2real** (A01) is the metric our Phase D chapter needs and does not yet have. Published reference points exist: 0.029 (FRIDA) / 0.066 / 0.156 (RL).
3. **Nobody reports recognisability.** At the digits/letters rung, IoU rewards ink overlap, not legibility — CLIPasso's (A03) central argument. A classifier-confidence metric on the drawn canvas would be cheap, and would put us *ahead* of the field on evaluation rather than behind it.

---

## 5. Research gaps

Ordered by how well each is supported and how well it fits this project's constraints.

### GAP 1 — No drawing agent learns from what a camera actually sees ★★★★★

The clearest gap, and the one this project is already aimed at. It is not our assertion — it
is stated as future work by three separate papers, including the two closest and the most
recent.

> **D01** (ICRA 2022): *"Although our method does not include real-world visual information for simplification, using a camera as an observation of canvas in the future work could be of great help in the synchronization step…"*

> **D03** (ICRA 2019): *"we are interested in closing the learning loop by enabling the robot to inspect what it has drawn and improve its drawing policy based on observation of what it actually drew."*

> **D09** (ICRA 2024): *"imprecision in tool modeling, and a lack of real-world training scenarios to bridge the sim2real gap. We leave these challenges as our future work."*

**Status in this project:** partially addressed. H2 demonstrates it under a *simulated* camera.
**Honest caveat:** `DrawEnv._perceive()` models the camera as `resize(150px) + threshold(>60)` — an idealised camera with no lighting, texture, perspective, blur, or noise variation. The H2 result is currently a claim about *one idealised camera*, not about cameras.

### GAP 2 — Vision-based *reward* vs vision-based *planning* is unmeasured in drawing ★★★★☆

A01 and D10 both use vision, but for **replanning/error-correction**, not as the learning
signal. D01/D02/D05/D09 compute the reward on an exact virtual canvas. Nobody has asked:
**how much drawing accuracy do you lose by learning from perception instead of from truth?**

**Status:** this is precisely H2, and we already have a first answer (0.41 vs 0.45 mean true IoU, single-run). This is our sharpest and most defensible contribution — provided it is framed as a *measurement*, not as an invention.

### GAP 3 — No reward-exploitation analysis for perceptual rewards in drawing ★★★★☆

R02's central failure mode is that policies learn to **fool** the reward model. In drawing this
is a concrete, plausible mechanism: downsampling and thresholding can make thin strokes dilate
and merge, and near-misses threshold into apparent hits — so an agent could learn to *look*
accurate to the camera while drawing worse.

Nobody has tested this for drawing. **We can, today, on existing data**: `DrawEnv` already
records both `info["iou"]` (true) and `info["reward_iou"]` (perceived). Plotting their gap over
training either exposes exploitation or provides strong positive evidence for H2. Either
outcome is publishable, and running it is cheap.

### GAP 4 — Sim-to-real for *low-cost* drawing arms is barely covered ★★★☆☆

D09 (Dobot Magician) and D08 (UltraArm) are the only low-cost-arm drawing papers here, and
neither closes the visual loop. Everyone else uses UR5e, Sawyer, Baxter, or industrial arms —
an order of magnitude more precise than MG996R hobby servos. **A ₹10,000 arm that learns to
draw with visual feedback is genuinely under-explored**, and it aligns with this project's
budget rather than fighting it.

### GAP 5 — The task ladder is assumed, never measured ★★★☆☆

Everyone (including us) uses a progressive/curriculum scheme (D08 curriculum learning, D09
progressive training, our line→circle→square→triangle→digits→letters ladder), but **nobody
measures whether it helps.** R04 provides the standard metrics (jump-start, time-to-threshold,
asymptotic performance). A small, clean, publishable experiment sits here and needs no new
machinery.

### GAP 6 — No standard benchmark for robotic drawing ★★★☆☆

Every paper here uses its own targets, metrics, and setup — which is why D01 can be
"state of the art" with purely qualitative results. A Gymnasium-conformant **RoboSketchBench**
(standard targets, IoU/MSE/chamfer/SNR, reference baselines, seeds) would be a real community
artefact and is nearly free given what already exists in `rl/`.

---

## 6. Novelty positioning — the honest version

### What we cannot claim

- ✘ **"RL for robotic drawing is new."** D01, D02, D05, D07, D08, D09 all did it.
- ✘ **"Vision-based rewards are new."** R01 (2017) and R02 (2019) established this in manipulation.
- ✘ **"Closed-loop visual feedback for drawing robots is new."** A01 replans from a DSLR; D10 detects and recovers from errors; e-David has had an optical feedback loop since ~2009.
- ✘ **"Our drawing quality is impressive."** D03 reaches 0.999 IoU (supervised). We are at 0.36–0.51 true IoU. Different problems, but we must not invite the comparison by overclaiming.

### What we can claim, and defend

1. **The measurement nobody has made.** *For the robotic drawing task, an agent rewarded solely from camera perception achieves drawing accuracy statistically indistinguishable from one rewarded with privileged ground truth* — quantified in IoU, over multiple seeds, across a shape suite. This is the exact question the three closest papers left open, and it is a prerequisite for any real drawing robot, since on hardware ground truth does not exist.
2. **Being the first drawing agent to close the loop through perception rather than forward kinematics.** D01 synchronises via FK and explicitly names camera observation as future work. Doing it, and showing *when it matters* (see the disturbance experiment below), is a contribution.
3. **Rigour as a secondary contribution.** Multi-seed, multi-metric, ground-truth-controlled evaluation in a subfield whose state of the art (D01) reports qualitative figures.
4. **A reusable benchmark environment**, if we choose to release it.

### The three objections a reviewer will raise, and what defeats each

| Objection | Source | What defeats it |
|---|---|---|
| **"D01 works fine without a camera — and argues camera-free is *more robust*."** | D01 explicitly: camera-free *"ignores unnecessary visual features such as surface texture, colors, and thicknesses"* | Show a failure that FK synchronisation **cannot** detect: inject pen slip / paper shift / ink failure mid-episode, and show the vision-in-the-loop policy recovers while an FK-synchronised or open-loop policy does not. **This experiment is the linchpin of the paper.** Without it, D01 is a complete answer to our motivation. |
| **"Perceptual rewards are old (R01, R02)."** | R01 2017, R02 2019 | Cite both prominently. Reframe from *invention* to *measurement*: theirs is a binary success classifier for manipulation; ours is a dense spatial reward for drawing, which permits a far more informative accuracy-equivalence result. |
| **"Your simulated camera is too easy."** | Our own `_perceive()`: fixed `cam_px=150`, fixed `>60` threshold | Domain-randomise the perception model (V01) and show H2 holds **across a distribution** of cameras — lighting, texture, blur, noise, perspective, threshold. Requires no hardware. This is the single change that most strengthens the existing result. |

---

## 7. Method-transfer map: what to take from where

| Idea | Source | Effort | Expected value |
|---|---|---|---|
| Add step/time-remaining to the observation (fix partial observability) | D02 | trivial | ★★★★☆ |
| Log and plot `reward_iou − true_iou` (reward-exploitation test) | R02 | trivial | ★★★★★ |
| Add SNR (stroke fragmentation) metric | D09 | trivial | ★★★★☆ |
| Egocentric / local observation window | D03, D08 | low | ★★★★★ |
| Normalise reward by initial loss | D08 | trivial | ★★★☆☆ |
| CoordConv or spatial-softmax CNN | D02, F05 | low | ★★★★☆ |
| Action chunking (predict k pen moves) | D02, A04 | low | ★★★★☆ |
| BC warm start from free analytic demonstrations | D07, D08, A07 | low | ★★★★☆ |
| Visual domain randomization of `_perceive()` | V01 | low | ★★★★★ |
| Open-loop vs closed-loop error-growth experiment | A01 | low | ★★★★★ |
| Disturbance-recovery experiment | D10, A01 | medium | ★★★★★ |
| Curriculum measurement (jump-start / time-to-threshold) | R04 | low | ★★★☆☆ |
| Ergodic control as the classical baseline | D04 | medium | ★★★★☆ |
| Pen-up/down for multi-stroke glyphs | F06 | medium | ★★★★☆ (required for letters) |
| Goal-conditioned policy + HER relabelling | F04 | high | ★★★★☆ |
| Hierarchical decoupling (planner / motor) | D01 | high | ★★★☆☆ |
| Fitted ink model (z → stroke width) | D09, A01 | needs hardware | ★★★★★ (Phase D) |
| Δ sim2real metric | A01 | needs hardware | ★★★★★ (Phase D) |
| Dynamics randomization of the arm | V02 | low | ★★★★☆ (Phase D) |
| Recognisability metric for digits/letters | A03 | low | ★★★★☆ (later rung) |
| Release as a benchmark environment | R05 | medium | ★★★☆☆ |

---

## 8. Summary judgement

The literature **supports** this project's core premise and **sharpens** its claim.

- The gap RoboSketch-RL targets is real, recent and explicitly acknowledged by the three closest papers (D01 ICRA 2022, D03 ICRA 2019, D09 ICRA 2024).
- The contribution must be framed as a **quantified measurement** ("what does perception-only reward cost, in IoU?"), not as the invention of visual rewards — R01/R02 have priority and must be cited.
- The result as it stands is **under-defended in one specific way**: the simulated camera is too idealised. Domain randomisation of the perception model (V01) is the highest-value strengthening available, and it needs no hardware.
- One experiment is missing and is close to essential: **showing a case where visual feedback succeeds and forward-kinematic synchronisation fails.** Without it, D01 is a complete answer to our motivation.
- Several cheap, well-supported improvements to the environment are available (egocentric observation, step-count in state, action chunking, BC warm start, SNR metric) — each backed by two or more independent papers.

Concrete, sequenced proposals follow in
[`../docs/PROJECT_PROPOSAL_v2.md`](../docs/PROJECT_PROPOSAL_v2.md).
