# RoboSketch-RL — Paper Study Notes

Systematic per-paper analysis. Companion to [`README.md`](README.md) (the index and ranking)
and [`COMPARATIVE_ANALYSIS.md`](COMPARATIVE_ANALYSIS.md) (cross-paper synthesis).

Started 2026-08-12.

## Reading-depth marker — read this first

Honesty about what has actually been read matters more than a tidy-looking document.

| Marker | Meaning |
|---|---|
| ◆ | **Full first-hand read** of the paper's method, experiments and results sections. Numbers, equations and hyperparameters below are quoted from the PDF. |
| ◇ | **Abstract + verified metadata + targeted sections only.** The analysis reflects the paper's established content but has *not* been verified line-by-line against the PDF. **Do not quote specific numbers from a ◇ entry in the thesis without reading the PDF first.** |

Current status: **8 papers at ◆**, 25 at ◇. The ◇ queue is listed at the end of this
document in priority order.

---
---

# PART 1 — Foundational

## F01 ◇ Proximal Policy Optimization Algorithms (Schulman et al., 2017)

- **Problem statement.** Policy-gradient methods are unstable: a single large update can collapse the policy. TRPO fixes this with a hard KL constraint but requires second-order optimisation and is complex to implement.
- **Research gap.** No first-order, easily-implemented method with TRPO-like reliability.
- **Objectives.** A policy-gradient algorithm that is simple, general, sample-efficient enough for practical use, and stable across many domains without per-task tuning.
- **Methodology.** Clipped surrogate objective `L^CLIP = E[min(r_t(θ)Â_t, clip(r_t(θ), 1−ε, 1+ε)Â_t)]` where `r_t(θ)` is the probability ratio of new to old policy. Multiple epochs of minibatch SGD on each batch of rollouts. GAE(λ) for advantage estimation. Optional value-function and entropy-bonus terms in a combined loss.
- **Architecture.** Shared or separate actor–critic MLP/CNN; on-policy, no replay buffer.
- **RL formulation.** Generic; the contribution is the optimisation objective, not a task formulation.
- **Environment / dataset.** MuJoCo continuous control, Atari.
- **Experimental setup.** Benchmarked against TRPO, A2C, CEM, vanilla PG across many tasks; hyperparameter sweeps.
- **Results.** Matches or beats TRPO at a fraction of the implementation and compute cost; became the field default.
- **Limitations.** **On-policy** — every gradient step needs fresh environment interaction, so it is sample-hungry. Sensitive to `clip_range`, advantage normalisation and reward scaling. No principled exploration mechanism beyond the entropy bonus.
- **Future work.** Adaptive KL variants; better exploration.

**→ RoboSketch-RL implications.**
1. Our reward magnitudes (`iou_weight=10.0` × IoU-delta, plus a `+2.0` terminal bonus) are unnormalised and can be large relative to the shaping terms. PPO is known to be sensitive to advantage scale — worth checking `explained_variance` and value loss in the logs before blaming the reward design.
2. PPO's on-policy cost is the reason training on the physical arm will be impractical. This is the honest justification for the sim-first strategy, and the argument for SAC (F02) at the hardware stage.
3. Cite as `arXiv:1707.06347`; note there is no peer-reviewed venue, which is normal for this paper.

---

## F02 ◇ Soft Actor-Critic (Haarnoja et al., ICML 2018)

- **Problem statement.** Model-free deep RL is sample-inefficient and brittle to hyperparameters, which blocks real-robot use.
- **Research gap.** Off-policy methods (DDPG) are sample-efficient but notoriously unstable; on-policy methods (PPO/TRPO) are stable but sample-hungry. Nothing was both.
- **Objectives.** A stable, sample-efficient, off-policy actor–critic for continuous control.
- **Methodology.** Maximum-entropy RL: maximise `Σ E[r(s_t,a_t) + αH(π(·|s_t))]`. Off-policy actor–critic with a replay buffer, twin Q-functions (clipped double-Q to reduce overestimation), a stochastic Gaussian actor with reparameterised sampling, and (in the v2 paper) automatic tuning of the temperature α against an entropy target.
- **RL formulation.** Generic continuous control.
- **Environment / dataset.** MuJoCo benchmark suite; later real-robot tasks.
- **Results.** State-of-the-art sample efficiency and stability; substantially fewer environment steps than PPO for comparable return; robust across seeds.
- **Limitations.** More hyperparameters and memory (replay buffer) than PPO; the entropy target needs setting per action-space dimensionality; off-policy replay can be harmed by strongly non-stationary rewards.
- **Future work.** Real-robot learning; hierarchical extensions.

**→ RoboSketch-RL implications.**
1. **RQ3 (PPO vs SAC) is well-motivated but must be run fairly.** Report *both* equal-environment-steps and equal-wall-clock comparisons — SAC does far more gradient work per environment step, so an env-steps-only plot flatters it and a wall-clock-only plot flatters PPO. Report both, with 5+ seeds (see R03).
2. The entropy term is a *principled* exploration mechanism. RoboSketch-RL currently buys exploration with hand-tuned shaping (`prox_weight=0.4`, `start_on_target=True`, deterministic start). SAC would let us test whether those crutches are still needed — a clean ablation.
3. **Caution for our vision reward:** SAC's replay buffer stores rewards computed at collection time. Our `reward_mode="vision"` reward is a deterministic function of the canvas, so replay is sound — but if the perception model is ever randomised (domain randomization, V01), stored rewards become stale. Recompute rewards on sample, or accept the noise deliberately and say so.
4. Two of the closest drawing papers — D01 (Lee et al.) and D09 (CalliRewrite) — both chose SAC over PPO for the drawing/motor task. That is meaningful prior evidence, and a reviewer will ask why we started with PPO.

---

## F03 ◇ Continuous Control with Deep RL / DDPG (Lillicrap et al., ICLR 2016)

- **Problem.** DQN cannot handle continuous action spaces; discretisation explodes combinatorially.
- **Method.** Deterministic policy gradient + DQN machinery: replay buffer, target networks with soft (Polyak) updates, exploration by additive action noise (Ornstein–Uhlenbeck).
- **Results.** Solves >20 simulated physics tasks from low-dimensional state and, for some, from pixels.
- **Limitations.** Notoriously unstable and hyperparameter-sensitive; Q-value overestimation; deterministic policy makes exploration entirely dependent on the injected noise.
- **→ Implications.** We should *not* use DDPG. Its importance is as background: **Learning to Paint (D02) uses model-based DDPG**, and most classical "drawing robot control with DRL" papers use DDPG. Reading them requires this. Also the lineage DDPG → TD3 → SAC justifies choosing SAC directly for RQ3 rather than adding a DDPG arm.

---

## F04 ◇ Hindsight Experience Replay (Andrychowicz et al., NeurIPS 2017)

- **Problem.** Goal-conditioned tasks with sparse binary rewards are nearly unlearnable — the agent almost never sees a success.
- **Research gap.** The standard workaround is hand-crafted reward shaping, which is task-specific, laborious, and can change the optimal policy if done carelessly.
- **Methodology.** Store transitions with the *achieved* goal as well as the intended one. When replaying, relabel the goal: a trajectory that failed to reach `g` but reached `g'` is a *successful* trajectory for `g'`. Combined with an off-policy algorithm (DDPG/SAC) and a goal-conditioned policy `π(a|s,g)`.
- **RL formulation.** State augmented with goal; reward is sparse `r = −[‖achieved − goal‖ > ε]`.
- **Results.** Solves pushing/sliding/pick-and-place from sparse rewards where DDPG alone fails completely; transfers to a physical robot.
- **Limitations.** Requires a well-defined goal space and an achieved-goal mapping; off-policy only; relabelling strategy (`future`, `final`, `episode`) matters.

**→ RoboSketch-RL implications — this is a major structural opportunity.**

RoboSketch-RL currently trains **one policy per shape** (`--shape line`, `--shape circle`, …) with a hand-shaped dense reward containing four tuned terms (`iou_weight`, `prox_weight`, `smooth_penalty`, terminal `+2.0`). This is exactly the situation HER was invented to remove.

The HER reformulation of our task: the **goal is the target mask itself**, and the **achieved goal is the canvas the agent actually drew**. Every episode, however bad, is a *perfect* demonstration of drawing the shape it happened to draw. That converts our sparsest signal into dense supervision for free, and it yields **one goal-conditioned policy over arbitrary target shapes** rather than four separate specialists — a far stronger result and the natural bridge to digits and letters.

Caveat to think through honestly: HER's guarantees are cleanest when the goal space is low-dimensional and the achieved-goal mapping is exact. A full binary mask is high-dimensional. A practical middle path is to relabel with the *drawn mask* as the goal and keep the IoU reward, which remains exactly computable. This is a genuine research question worth an experiment, not a foregone conclusion.

---

## F05 ◇ End-to-End Training of Deep Visuomotor Policies (Levine, Finn, Darrell, Abbeel, JMLR 2016)

- **Problem.** Robot systems hand-engineer perception, state estimation and control separately; the perception module is not optimised for the control task it serves.
- **Research gap.** No practical method to train a pixels-to-torques policy on a real robot — naive policy search is far too sample-hungry.
- **Methodology.** **Guided Policy Search**: a trajectory-centric RL method (local time-varying linear-Gaussian controllers, fitted dynamics) generates good trajectories, and the deep CNN policy is trained by *supervised learning* to match them, with a BADMM constraint keeping the two consistent. This converts an RL problem into supervised learning.
- **Architecture — the part that matters most for us.** A CNN whose conv features are converted to **2-D spatial feature points via a spatial softmax**: for each channel, take the softmax over spatial positions and compute the expected `(x, y)`. This produces an explicit list of image-space coordinates, then concatenated with robot state and passed to fully-connected layers.
- **Environment.** Real PR2 robot; tasks requiring tight hand–eye coordination (hanging a coat hanger, inserting a block, screwing a cap onto a bottle).
- **Results.** End-to-end training substantially outperforms training perception and control separately; ~92k-parameter network learns from a modest number of real-robot trials.
- **Limitations.** GPS needs a reasonably good trajectory-optimisation setup and instrumented state during training; not a drop-in for arbitrary tasks.

**→ RoboSketch-RL implications — a concrete, cheap architectural upgrade.**

Our observation is a 64×64×3 image (target, drawn, pen-marker) fed to Stable-Baselines3's default `NatureCNN`, which flattens conv features into a dense layer. That architecture throws away explicit spatial structure and has to re-learn "where things are" from scratch.

Our task is **almost purely spatial**: *where* is the pen, *where* is uncovered target, *which direction* should the pen move. A spatial-softmax head outputs precisely that — a set of `(x, y)` feature points — which is a far better inductive bias. This is a low-risk, high-expected-value experiment: swap the CNN, hold everything else fixed, compare sample efficiency.

Related and complementary: **Learning to Paint (D02) uses CoordConv as the first layer** of both actor and critic for the same reason — a plain convolution is translation-invariant and therefore literally cannot represent absolute position, which our task depends on. Our pen-marker channel is a workaround for this; CoordConv or spatial-softmax is the principled fix.

---

## F06 ◇ A Neural Representation of Sketch Drawings — sketch-rnn (Ha & Eck, ICLR 2018)

- **Problem.** Generative models of images work in pixel space; humans draw as *sequences of strokes*. No good generative model of vector sketches existed.
- **Methodology.** Sequence-to-sequence VAE. Bidirectional-RNN encoder → latent `z` → autoregressive RNN decoder emitting a Gaussian mixture over `(Δx, Δy)` plus a 3-way categorical pen state.
- **Stroke representation (the citation we need).** Each point is `(Δx, Δy, p₁, p₂, p₃)` where `p₁` = pen down (draw to next point), `p₂` = pen up (move without drawing), `p₃` = end of sketch.
- **Dataset.** **QuickDraw** — millions of human doodles across hundreds of categories, with stroke order and timing.
- **Results.** Generates coherent, recognisable vector sketches; latent-space interpolation and analogies work; conditional and unconditional generation.
- **Limitations.** Requires stroke-sequence supervision; struggles with complex multi-object scenes.

**→ RoboSketch-RL implications.**
1. **This is the correct citation for our action space.** `DrawEnv.action_space = [dx, dy, pen_down]` is exactly the sketch-rnn stroke representation. Cite it rather than presenting the action space as an arbitrary choice.
2. **The pen-state channel becomes essential at the letters stage.** We currently hard-code `pen_always_down=True`, so `action[2]` is ignored. Every multi-stroke glyph (`4`, `5`, `i`, `t`, `E`) is *unreachable* under that setting — the agent must draw a connecting stroke, which is stray ink and directly caps achievable IoU. This is a known, dated limitation to fix before the digits rung.
3. **QuickDraw is the citable dataset for the digits/letters stage.** Note that three of our closest neighbours use it: D01 (Lee et al.) trains Commander on Quick, Draw!; D09 (CalliRewrite) pre-trains on QuickDraw; sketch-rnn introduced it. Using it puts us in an established evaluation lineage instead of four bespoke analytic shapes.

---
---

# PART 2 — Directly Related

## D01 ◆ From Scratch to Sketch: Deep Decoupled Hierarchical RL for Robotic Sketching Agent
**Lee, Kim, Lee, Zhang — Seoul National University — ICRA 2022 — arXiv:2208.04833**

> **The single most important paper for this project.** Read it twice.

- **Problem statement.** Build a robot sketching agent that learns *both* skills required to draw — deciding **what stroke to place next** (in-mind intelligence) and **how to move the arm to realise it** (embodiment control) — entirely from scratch, with no demonstrations, hand-crafted rules, or inverse kinematics.
- **Research gap (their words, paraphrased).** (a) Stroke-Based Rendering research is developed under *virtual* rendering assumptions, so its outputs are hard to execute with real drawing tools. (b) Robotic drawing systems that do exist plan motion by inverse kinematics or manual control, giving "strict and lacking spontaneity" movement. (c) **"there are still no studies which have considered RL mechanism for both SBR and low-level robot control simultaneously."**
- **Objectives.** Effectiveness (integrate both sub-tasks), scalability (no expensive demonstration data; any robot can learn to sketch), robustness/flexibility (work across drawing tools and surfaces).
- **Methodology — Deep Decoupled Hierarchical RL (DHRL).** Two policies trained **independently**, composed only at deployment:
  - **Commander** (high level, "imaginary canvas"): decides the next stroke.
  - **Stroker** (low level, physical arm): executes that stroke as joint motion.
  - They explicitly reject joint end-to-end HRL training: *"applying such approach to our task is unrealistic because of the substantial gap between imaginary stroke planning and physical joint controls. Moreover, if trained together, they form mutual dependency which makes replacing the trained policy unavailable, and makes it hard to track the training progress."*
- **RL formulation.**

  | | **Commander** | **Stroker** |
  |---|---|---|
  | State | `(V_t, pos_t)` — imaginary canvas + pen-position channel | `(j₁…j₆)` — the six joint angles only |
  | Goal | `g^C = I` (complete target image) | `g^S = a^C` (Commander's stroke) |
  | Action | `a^C = (down, Δx, Δy)`, all in `[0,1]`; `down > 0.5` ⇒ ink. A **short straight line** from the current pen position, bounded inside a fixed-length square | `(Δj₁…Δj₆)` — joint-angle changes |
  | Reward | `r^C_t = d(V_t, I) − d(V_{t−1}, I)` where `d` is an adversarially-trained **discriminator** (SNGAN spectral normalisation for stability) | `r^S = −10√((g_x−pt_x)² + (g_y−pt_y)² + 5(g_z−pt_z)²) + 5·cos_sim(g_xy, pt_xy) − √((γ_g−γ_t)² + (ψ_g−ψ_t)²)` |
  | Episode | 50 strokes | **1 step** (one stroke = one episode) |
  | Algorithm | SAC, 3M steps | SAC, 5M steps, in MuJoCo |

  Design notes worth stealing: the `z` term is weighted ×5 because "z axis determines pen lifting crucial for sketching"; the cosine-similarity term is scaled ×5 because "the direction of the pen movement is more important than the distance"; Stroker is trained from **9 fixed initial poses** with randomly sampled goals, re-initialised every 100 goals to escape degenerate poses.
- **Why the straight-line stroke.** They deliberately reject Bézier-curve strokes (used by Learning to Paint, SPIRAL, and others): *"complicated stroke is not a best option when a stroke is physically rendered with real drawing tools like pen or board markers, because the stroke determined by the large parameter space is such a burden for the low-level physical controller to search."* They accept degraded aesthetics because "modeled strokes like Bézier curve are eventually equal to the sum of our basic strokes."
- **Vision / feedback mechanism — the crux.** **There is no camera.** After each stroke, Stroker reports its pen-tip position (obtained by **forward kinematics**, not vision) back to Commander, which updates its imaginary canvas. They call this "synchronization" and present camera-free operation as a *feature*: *"We attribute our agent's robustness to our camera-free methodology, which ignores unnecessary visual features such as surface texture, colors, and thicknesses while focusing on the main drawings in imaginary canvas."*
- **Environment / dataset.** Commander trained on **Quick, Draw!** doodles. Stroker trained in **MuJoCo** mimicking the real setup. Imaginary canvas **42×42 px** ↔ real canvas **21×21 cm** (0.5 cm = 1 px; distances 0.25–0.75 cm round to 1 px).
- **Experimental setup.** UR5e + Robotiq 2F-85 gripper. **Spring-mounted pen case** to avoid the UR5e's protective stop on contact force. Three tool/surface combinations: whiteboard + board marker, A4 paper + ballpoint pen, drawing paper + crayon. Evaluated on a hand-drawn dataset of doodles, characters, numbers and geometries **not seen in training**.
- **Results.** Training curves (Fig. 5) show L2 distance between target and Commander's drawing decreasing, plus Euclidean/angle error for Stroker. Qualitative results (Figs. 6, 8, 9) show good target reproduction and near-identical sketches across all three tool/surface combinations. **Ablation:** the "No sync" row of Fig. 9 produces clearly impaired sketches — synchronisation is load-bearing.
- **Evaluation metrics.** L2 distance, Euclidean distance to goal, angle error, Euler-angle error for pen rotation. **No IoU. No quantitative table of drawing accuracy.** The drawing-quality evidence is entirely qualitative.
- **Limitations (stated and observed).** Tendency to omit fine details (e.g. strawberry seeds). Stroker's moves "were learned and not completely accurate," so sketches contain slight errors. No real-world visual information at all. Results are qualitative.
- **Future work — quote this in our paper.**
  > *"Although our method does not include real-world visual information for simplification, using a camera as an observation of canvas in the future work could be of great help in the synchronization step to reduce discrepancies when using more diverse drawing tools like brush and spray."*

**→ RoboSketch-RL implications — this defines our position in the literature.**

1. **Our novelty claim survives, and gets sharper.** The closest published system to ours is *deliberately camera-free* and states that adding camera observation of the canvas is valuable future work. RoboSketch-RL's H2 — an agent rewarded from camera perception rather than privileged ground truth — is precisely the loop they left open. **This quote belongs in our introduction as the gap statement.**
2. **But their reason for going camera-free is a real threat we must answer.** They argue camera-free is *more robust* because it ignores nuisance visual variation. Our paper must show the vision loop earns its cost: it must be demonstrated to **fix an error that forward-kinematic synchronisation cannot** — pen slip, paper shift, ink failure, miscalibration. That is a specific, runnable experiment (see the proposal document), and without it a reviewer can reasonably say "D01 already works, without a camera."
3. **Their decoupling argument is the answer to our scaling problem.** Our flat pen-space policy conflates stroke planning with motion. Their two-level split (and its justification) is the template for our letters stage.
4. **Adopt their straight-line stroke justification.** It independently validates our `(dx, dy)` pen-space action over the Bézier action spaces of D02/D05, on explicitly *physical-realizability* grounds. Good citation for a design choice we already made.
5. **Beat them on rigour.** They report no IoU and no quantitative accuracy table. Our multi-seed IoU/MSE/chamfer protocol with a ground-truth baseline is already more rigorous. That is a legitimate, defensible secondary contribution — say so explicitly.

---

## D02 ◆ Learning to Paint With Model-based Deep Reinforcement Learning
**Huang, Heng, Zhou — Megvii / Peking University — ICCV 2019 — arXiv:1903.04411**

- **Problem statement.** Decompose a target image into a sequence of hundreds of strokes that recreate it on a canvas, without human painting experience or stroke-tracking supervision.
- **Research gap.** Prior SBR uses greedy per-step search (slow, myopic) or requires user interaction. Prior RL painters (SPIRAL) fail to recover fine detail in complex images; StrokeNet fails to generalise to colour images; discrete stroke-parameter spaces are too coarse for texture-rich painting.
- **Objectives.** Long-horizon stroke planning; continuous stroke parameters; efficient training.
- **RL formulation.**
  - **State** `s_t = (C_t, I, t)` — canvas bitmap, target image bitmap, **and the step number `t`**. They state explicitly that `t` "acts as additional information to instruct the agent the remaining number of steps."
  - **Action** `a_t = (x₀,y₀,x₁,y₁,x₂,y₂, r₀,t₀, r₁,t₁, R,G,B)` — a quadratic Bézier curve with per-endpoint thickness and transparency, plus colour. 13 continuous dimensions.
  - **Reward** `r(s_t,a_t) = L_t − L_{t+1}`, where `L` is the **WGAN-GP discriminator score** between canvas and target — *not* a pixel metric. They report: *"we find rewards derived from D scores is better than L₂ distance."*
  - **Episode** — fixed number of strokes (5 for MNIST, 40 SVHN, 200 CelebA, 400 ImageNet).
- **Methodology.**
  - **Neural renderer.** A network (FC layers → conv → **sub-pixel upsampling**, which avoids checkerboard artefacts) maps stroke parameters to a rendered stroke image. Trained by supervised learning on randomly generated strokes from a graphics renderer. Being differentiable, it makes the transition `s_{t+1} = trans(s_t, a_t)` differentiable.
  - **Model-based DDPG.** Unlike standard DDPG where the critic takes `(s_t, a_t)`, here the critic is a **value function `V(s_t)`** and the actor maximises `r(s_t, π(s_t)) + V(trans(s_t, π(s_t)))` — gradients flow through the differentiable renderer into the actor. `V(s_t) = r(s_t,a_t) + γV(s_{t+1})`.
  - **Action Bundle.** The agent predicts **k = 5 strokes per step**; the renderer renders them in order; the discount becomes `γ^k`. *"We experimentally find that setting k = 5 is a good choice that significantly improves the performance and the learning speed."*
- **Architecture.** ResNet-18-style actor and critic; **CoordConv as the first layer of both actor and critic**; WN + TReLU (BatchNorm helps the actor but not the critic); PatchGAN-style discriminator; soft target networks for actor, critic **and** discriminator.
- **Environment / dataset.** MNIST, SVHN, CelebA, ImageNet — all resized to **128×128**. Explicit train/test split (2,000 held-out images) **to test generalisation to unseen targets**.
- **Results.** High-fidelity reproductions across all four datasets. 200 strokes in ~2.1 s on a 2.2 GHz CPU; 9.5× faster on a 2080Ti. Ablations in Fig. 7 compare 20/200/1000 strokes, opaque vs transparent strokes, and **ℓ₂ reward vs discriminator reward** (discriminator wins).
- **Limitations.** Purely virtual — no robot. And, as FRIDA (A01) demonstrates empirically, the unconstrained stroke model is the problem: allowing arbitrarily large strokes with varying opacity produces plans that **cannot be executed** by a real robot (FRIDA measures its sim2real gap at Δ = 0.156, the worst of the three methods compared).
- **Future work.** Different stroke designs; better renderers.

**→ RoboSketch-RL implications — three concrete, actionable findings.**

1. **We have a probable POMDP bug.** `DrawEnv`'s observation is `(target, drawn, pen-marker)` — it **does not include the step count or remaining budget**, yet the episode is hard-truncated at `max_steps=120` and the reward includes a per-step structure. Two states with identical canvases but 5 vs 100 steps remaining have different optimal actions, and our agent cannot tell them apart. Learning to Paint includes `t` in the state precisely for this reason. **Adding a normalised `t/max_steps` channel (or scalar, via a Dict observation) is a cheap, well-motivated fix.**
2. **Action Bundle ≈ action chunking, validated in our exact task family.** Predicting `k` pen moves per policy step improved both performance *and* learning speed for them at `k=5`. This is the same mechanism Diffusion Policy (A04) generalises. It is also a far more principled way to get smooth strokes than our `smooth_penalty=0.02` heuristic penalty on action differences.
3. **CoordConv.** A plain CNN is translation-invariant and therefore structurally unable to represent absolute canvas position. Our third observation channel (a drawn pen-marker blob) is a hand-rolled workaround. CoordConv — or F05's spatial softmax — is the principled fix, and D02 found it necessary in the same setting.
4. **The discriminator reward beats L₂ — but note what that means for us.** Their targets are photographs with no "correct" stroke decomposition, so a perceptual/adversarial reward is right. Our targets are *binary geometric masks* where IoU is a genuinely meaningful objective. We should say this explicitly rather than let a reviewer assume we simply did not know about learned rewards.

---

## D03 ◆ Teaching Robots To Draw
**Kotani & Tellex — Brown University — ICRA 2019**

- **Problem statement.** Given a bitmap image of handwritten characters or a line drawing, infer a sequence of pen commands that reproduces it, drawing **each target stroke in one continuous motion**.
- **Research gap.** (a) Motion planners (RRT/RRT*) find *a* path but not a *continuous, human-like stroke*. (b) Existing robot-writing systems need external stroke-order information — human gestures, predefined per-character paths — which makes teaching new characters hard for novice users. (c) *"More recent deep-RL approaches learn a general drawing policy, yet frequently do not draw each target stroke in one continuous fluent motion; instead it frequently backtracks over a previously-drawn area to write over it again"* — and they *"require millions of frames of data during training."*
- **Objectives.** Learn general handwriting knowledge from data; generalise to unseen characters and unseen alphabets; run on real robots.
- **Methodology.** **Supervised learning, not RL.** Two cooperating networks over a 100×100 target image:
  - **Local Model** — follows one stroke to its end. State `s^L_t` = three images: already-visited region, the target region continuously connected to the current location, and the difference image (unvisited target). A residual CNN encodes to `(100,100,64)`, then **a 5×5×64 patch centred on the current pen location is extracted** (they describe this as "a structural attention mechanism"), flattened to 1600, fed to an **LSTM**, then two heads: sigmoid touch/untouch and argmax over the 5×5 locational grid. Action `a_t = (Δx, Δy, touch)` with `Δ ∈ [−2, +2]`.
  - **Global Model** — when `touch = 0`, predicts the `(x, y)` start of the next stroke over the full image (cross-entropy over `N²` positions). State = four images including the recently-drawn stroke and the difference image.
- **Dataset.** **KanjiVG** (Japanese Kanji with ordered SVG stroke lists): 10,000 characters train / 2,000 validation, augmented with shifting, scaling and shearing. ~12.5 strokes/character × ~15.8 local actions/stroke ≈ 200 actions/character. **Trained per-stroke (1–20 actions), resetting the LSTM at each stroke**, to keep sequences short.
- **Metrics.** **Pixel accuracy = `TP/(T + P − TP)`** — note this is *exactly IoU*. **Stroke accuracy** — for each drawn stroke, best IoU against any target stroke, averaged.
- **Results (Table I, train / test).**

  | Model | Pixel acc. | Stroke acc. |
  |---|---|---|
  | **Proposed (local + global, LSTM, extraction)** | 0.9988 / **0.9990** | 0.9630 / **0.9646** |
  | LSTM → fully-connected | 0.9985 / 0.9973 | 0.9564 / 0.9532 |
  | Extraction → "initial extraction" (5×5 from raw images) | 0.9964 / 0.9957 | 0.8746 / 0.8822 |
  | (3) + FC instead of LSTM | 0.9995 / 0.9999 | 0.8666 / 0.8809 |
  | **Global model only (no local model)** | **0.2693 / 0.2773** | **0.1565 / 0.1680** |

  Generalises to Greek, Hindi, Tamil, Urdu, Yiddish, Chinese, Korean, French, English cursive — **alphabets disjoint from the Kanji training set** — plus a Mona Lisa line sketch.
- **Ablation insight.** The **local model with its restricted 5×5 action space is the whole game**: it has 25 choices where the global model has 10,000. Removing it collapses performance by ~4×. The LSTM contributed surprisingly little (0.9630 → 0.9564).
- **Robot demonstration.** Baxter (marker rigidly attached to gripper) — *"there is significant error in the drawn characters, due to position errors in the robot's end effector."* MOVO (Kinova Jaco + Kinect 2) — "reproduces the target image very accurately." Preprocessing required: skeletonisation to line-width 1, resize to 100×100.
- **Limitations.** Needs stroke-ordered training data (KanjiVG). Open loop — no observation of what was actually drawn. Baxter's end-effector error visibly degrades output.
- **Future work — quote this too.**
  > *"we are interested in closing the learning loop by enabling the robot to inspect what it has drawn and improve its drawing policy based on observation of what it actually drew."*

  and, on the Baxter errors: *"In the future we plan to explore an end-to-end closed loop learning of policies for writing to mitigate this problem."*

**→ RoboSketch-RL implications.**

1. **A second independent "closed the loop is future work" statement**, from ICRA 2019, three years before D01's. Two of the four closest papers in the field name our contribution as unaddressed. That is a strong, honest, citable gap.
2. **Their "pixel accuracy" is our IoU** — so our metric is directly comparable to a published ICRA baseline. Use their name-mapping in the paper to make the comparison legible.
3. **A sobering calibration on our numbers.** They reach 0.999 IoU; our PPO agents reach 0.36–0.51 true IoU. The tasks are not identical (they draw skeletonised 1-px targets with supervision from stroke-ordered data; we draw thick strokes from scratch with no demonstrations), but **we must not present 0.4 IoU as a strong drawing result.** The honest framing is that our contribution is about the *reward source*, with drawing accuracy as a controlled variable — and we should say plainly that supervised methods achieve far higher fidelity.
4. **The 5×5 local-window result is a strong architectural signal.** Restricting the action to a small neighbourhood of the current pen position, and *observing* a small window around it, is what made their model work — a 4× effect in the ablation. **D08 (Jia & Manocha) independently arrives at the same design** with its egocentric observation window. Two independent papers converging on local/egocentric observation is about as strong as architectural evidence gets, and our env uses a *global* 64×64 view. This is the single best-supported change available to us.
5. **KanjiVG is a citable, stroke-ordered dataset** for the letters stage, and their skeletonisation preprocessing is a directly reusable recipe.

---

## D04 ◆ Autonomous Visual Rendering using Physical Motion
**Prabhakar, Mavrommati, Schultz, Murphey — Northwestern — WAFR 2016 — arXiv:1709.02758**

- **Problem statement.** How can a robot render a visual symbol (a letter, a photograph) using its *own* physical motion, without task-specific hardware or software co-designed for drawing?
- **Research gap.** Drawing systems are typically co-designed with the task — mechanically specialised robots plus bespoke algorithms — which does not generalise across robots or across images.
- **Objectives.** Reduce dependence on task-specific robots; reduce algorithmic complexity; make one software solution work on multiple robotic embodiments and on both letters and photographs.
- **Methodology — ergodic control.** Represent the target image as a **spatial distribution `φ(x)`** (higher intensity = higher density). A trajectory is *ergodic* with respect to `φ` if the time it spends in a region is proportional to that region's density. Minimise the **ergodic metric**

  `ε = Σ_k Λ_k |c_k − φ_k|²`,  `Λ_k = 1/(1+‖k‖²)^s`,  `s = (n+1)/2`

  with Fourier basis `F_k(x) = (1/h_k)·Π_i cos(k_i π x_i / L_i)`, spatial coefficients `φ_k = ∫ φ(x)F_k(x)dx`, and trajectory coefficients `c_k = (1/T)∫₀ᵀ F_k(x(t))dt`.
- **Three control algorithms compared.**

  | | CFEC | E-iSAC | PTO |
  |---|---|---|---|
  | Time horizon | infinitesimal | non-zero receding | finite, non-receding |
  | Closed-loop | ✔ | ✔ | ✔ |
  | Nonlinear dynamics | | ✔ | ✔ |
  | Control saturation | ✔ | ✔ | |
  | Continuous control | | | ✔ |
  | Weight on control | | ✔ | ✔ |
  | Efficient to compute | ✔ | ✔ | ✘ (numerical integration of many ODEs) |

- **Experimental setup.** Rendering the letter "N" and photographs, over 60 s, with first-order (single-integrator) and second-order (double-integrator) dynamics; Baxter robot experiments.
- **Results.** All three methods produce recognisable output but with **dramatically different styles**: CFEC's infinitesimal horizon gives large aggressive motions; E-iSAC is intermediate; **PTO with single-integrator dynamics "most closely resembles typical human penmanship."** They also observe that *"other drawing algorithms implicitly optimize (or at least improve) ergodicity."*
- **Limitations.** Renders *tone/coverage*, not stroke structure — the trajectories are scribble-like paths whose time-average matches the image, not clean strokes. PTO is computationally expensive. No learning, so no adaptation to execution error beyond the closed-loop control itself.

**→ RoboSketch-RL implications.**

1. **This should replace "naive IK" as our classical baseline.** Beating a hand-written IK trajectory follower is not a publishable comparison — it is a strawman. Ergodic control is a rigorous, closed-loop, citable, *general-purpose* method for exactly our problem. Comparing PPO against E-iSAC is a real result either way it lands.
2. **The ergodic metric is a serious alternative objective to IoU**, with a property IoU lacks: the `Λ_k` weighting makes it sensitive to *multi-scale* spatial structure rather than treating every pixel independently. For thick strokes on a coarse canvas, IoU saturates and stops discriminating; the ergodic metric does not. Worth evaluating as a supplementary metric even if we keep IoU as the reward.
3. **Their qualitative finding — that the objective and the dynamics jointly determine drawing "style"** — is a useful framing for interpreting our agents' scribbly failure modes: those are properties of the objective, not just of optimisation failure.

---

## D05 ◇ SPIRAL: Synthesizing Programs for Images using Reinforced Adversarial Learning
**Ganin, Kulkarni, Babuschkin, Eslami, Vinyals — DeepMind — ICML 2018**

- **Problem.** Learn to produce *programs* (sequences of drawing commands) that recreate images, using a **non-differentiable** external renderer, with no supervision on the programs themselves.
- **Method.** An RL agent emits stroke/program commands to an off-the-shelf renderer (libmypaint, or a 3-D scene renderer). A **discriminator** trained to distinguish rendered outputs from real images supplies the reward — an adversarial, learned objective. Distributed advantage-actor-critic training at large scale.
- **Tasks.** MNIST digits (drawn in a **single continuous brush motion**), Omniglot, CelebA, and 3-D scene reconstruction.
- **Results.** Produces samples clearly recognisable as handwritten digits; recovers structure of more complex images; works without any stroke-order data.
- **Limitations.** Enormous compute (distributed, many actors). Struggles to recover fine detail in complex images (noted by D02). Produces redundant/backtracking strokes (noted by D03).
- **→ Implications.** (a) Direct evidence that the **MNIST-digits rung of our roadmap is reachable by RL** — de-risking our roadmap. (b) The discriminator-as-reward pattern is the main alternative to IoU when there is no pixel-aligned target. (c) A caution on scope: SPIRAL needed DeepMind-scale compute; our compute budget bounds what we should promise for the digits stage. (d) D03 and D02 both criticise SPIRAL specifically (backtracking strokes, missing detail) — useful for our related-work critique.

---

## D06 ◇ Unsupervised Doodling and Painting with Improved SPIRAL (Mellor et al., DeepMind, 2019)

- Scaled-up SPIRAL with improved training and richer datasets, and — most usefully for us — **extensive qualitative analysis of what the drawing agent actually learns**: intermediate canvases, stroke orders, and how the reward shapes emergent drawing style.
- **→ Implications.** Their analysis methodology is the model for our qualitative-results section. IoU tables alone will not convince a robotics reviewer that the agent learned to *draw*; showing the stroke sequence and intermediate canvases will. We already save intermediate output — we should present it this way.

---

## D07 ◇ Learning to Sketch with Deep Q Networks and Demonstrated Strokes (Zhou et al., BMVC 2018)

- **Method.** Value-based (DQN) sketching over a discretised stroke action space, **bootstrapped with demonstrated strokes**, in a coarse-to-fine two-stage pipeline.
- **→ Implications.** Concrete evidence that demonstrations sharply reduce training time for sketch agents. **This is unusually cheap for us**: our targets are analytic shapes, so we can generate *perfect* expert demonstrations for free (trace the target with the pen) — something SPIRAL and Learning to Paint could not do for photographs. A BC warm start is therefore near-zero-cost and well-supported by D07 **and** D08.

---

## D08 ◆ Sim-to-Real Brush Manipulation using Behavior Cloning and Reinforcement Learning
**Jia & Manocha — University of Maryland — arXiv:2309.08457 (2023)**

- **Problem statement.** Train a painting agent in simulation that transfers to a real robot arm holding a real, *deformable* brush.
- **Research gap.** Prior learning-based painting either needs expert demonstrations for reward design (Xie et al.), or requires explicit environmental modelling, or stays in simulation. Deformable brushes are hard to model.
- **RL formulation.**
  - **Action** `a_t = [α_t, l_t, w_t, c_t] ∈ ℝ⁶`, each normalised to `[0,1]`: stroke **angle**, **length**, **width**, **colour**. Notably `w = 0` ⇒ brush lifted off the canvas (their pen-up mechanism).
  - **Observation — egocentric.** *"the paintbrush remains centered on the canvas, with the canvas and reference image adjusted accordingly."* Formally `o_t = { s_t[h_p ± h_o/2, w_p ± w_o/2],  s*[h_p ± h_o/2, w_p ± w_o/2] }` — matched crops of the **canvas** and the **reference image** around the pen position. They report this *"simplifies the action space, eliminates the need for a replay buffer, and renders training in a continuous action space and large state space feasible."*
  - **Reward** — normalised loss improvement: `r_t = (L(s_{t−1}, s*) − L(s_t, s*)) / L(s₀, s*)`, giving `r_t ∈ (−∞, 1]`, where `L` is an **L_{1/2}** loss (not L₂) — chosen *"to incentivize the painting to match the color and shape of the reference image precisely rather than aiming for an average color."*
  - **Adaptive horizon** `t̂_max = arg min_i (r_i > r_thresh)`, increased gradually during training.
- **Methodology.**
  - **Behaviour cloning initialises the RL policy**, with the BC action space a *subspace* of the RL action space (direction and on/off-canvas actions), specifically to bridge BC and RL in the real setup.
  - **Curriculum learning**: the number of sampled trajectories increases over training; the agent *"tends to seek rewards greedily within the limited time steps"* early on and produces longer strokes later.
  - **Difficulty-based sampling**, because the reference image must change during training to prevent overfitting.
- **Architecture.** Conv 64@8×8 s4 → conv 64@4×4 s2 → conv 64@3×3 → FC 512, ReLU throughout.
- **Sim-to-real — the most transferable part.**
  - **Hybrid Pressure Estimation (Algorithm 2)**: recursive **binary search** over `[a_p_min, a_p_max]` to learn a mapping `M(s)` from desired stroke to real robot configuration, using **image analysis of the drawn strokes instead of force sensors** (*"precise force sensors are often unavailable"*). Two observation modes: stroke images (indirect) and end-effector images (direct, gives the deformation limit by linear fitting).
  - **2-D → 3-D action projection**: `[x_robot, y_robot, z_robot]ᵀ = [R  T; 0  1]·[x_painting, y_painting, 1]ᵀ` — i.e. find the painting plane in the robot's 3-D configuration space, computed like a camera extrinsic calibration.
  - Three effects that do **not** map directly: stroke thickness (only via contact force), colour (monochrome; requires dipping), tilt (their 3-DoF robot cannot).
  - **Gaussian stroke modelling** for stylisation: a long stroke is a sequence of segments whose centroid/pressure follows a Gaussian; varying mean/σ changes artistic style (Fig. 4 shows mean 0.5/σ 0.3 vs mean 0.7/σ 0.8).
- **Hardware.** **UltraArm** (low-cost arm), RealSense D415, paintbrush, water pot — with the **camera mounted on the end-effector** (eye-in-hand).
- **Results.** Qualitative: reproduces both painterly images and Chinese characters (KanjiVG reference) in simulation (MyPaint) and on the real robot; transfers artistic style.
- **Limitations.** Largely qualitative evaluation; monochrome in the real setup; 3-DoF arm cannot tilt the brush.

**→ RoboSketch-RL implications — this is our Phase D blueprint.**

1. **Egocentric observation, independently confirmed.** D08 and D03 arrive at local/egocentric observation windows by different routes and both report it as decisive. Our global 64×64 observation is the outlier. **Highest-confidence architectural change available.**
2. **Reward normalisation.** Their `r_t` is divided by the initial loss, making reward scale comparable across targets. Our `iou_weight * Δ IoU` is unnormalised, so a target with large area and a target with small area produce systematically different reward scales — which matters the moment we train **one** policy over **many** shapes (the HER/goal-conditioned direction). Cheap fix, real benefit.
3. **The ink model is a first-class sim-to-real gap.** Their entire pressure-estimation algorithm exists because the tool–surface interaction is what actually breaks transfer. Our ink model is one line — `cv2.line(canvas, c0, c1, 255, 2*pen_radius_px, LINE_AA)` — with `pen_radius_px` derived from a hard-coded `0.0035 m` assumed stroke width. **That constant is currently unvalidated and is likely our largest single reality gap.** Their binary-search-with-image-analysis procedure is directly adoptable and needs no force sensor — which suits a ₹10,000 budget.
4. **Their 2-D→3-D projection** is exactly the calibration our pen-space policy will need on hardware, and it justifies our pen-space action abstraction: the policy stays 2-D; a calibrated homography plus IK handles the robot.
5. **BC warm start + curriculum**, both used here and both cheap for us.
6. **Eye-in-hand vs overhead camera is a real design decision** we have not consciously made. D08 uses eye-in-hand; FRIDA (A01) uses a fixed DSLR. For *reward from the whole canvas* a fixed overhead camera is right; for *stroke-level precision* eye-in-hand is better. Worth stating our choice and why.

---

## D09 ◆ CalliRewrite: Recovering Handwriting Behaviors from Calligraphy Images without Supervision
**Luo, Wu, Lian — Peking University — ICRA 2024 — arXiv:2405.15776**

- **Problem statement.** Given only an image of a calligraphic glyph, recover a plausible writing order **and** tool-aware control trajectories, for diverse writing instruments, **without labelled demonstrations**.
- **Research gap.** Prior calligraphy robots rely on laborious annotation and heavy supervision, which fails for out-of-distribution scenarios (ancient scripts, unknown fonts). Also, *"in calligraphy robots, the significance of tools is seldom discussed"* — trajectory optimisation and search methods fall short for tool-dependent control.
- **Objectives.** Unsupervised, low-resource, generalise to unseen fonts/scripts, and adapt control to different physical instruments.
- **Methodology — two stages, coarse-to-fine.**
  - **(a) Coarse Sequence Extraction.** CNN encoder + **unsupervised LSTM** emits quadratic Bézier strokes `B_t = (p, x₀,y₀, x₁,y₁, x₂,y₂, w₀,w₁)` where `p` is pen down/up and `w` are endpoint widths. Trained with four unsupervised losses:
    - **Perceptual loss** — VGG-16 features at `relu1_2, relu2_2, relu3_3, relu5_1`, each layer normalised by its running mean to prevent loss-scale fluctuation.
    - **Regularization loss** `L_reg = (1/T)Σ(1 − p_t)` — penalises pen lifts (fewer, longer strokes).
    - **Smoothness loss** — cosine similarity between consecutive control-point vectors, scaled by 0.5.
    - **Angle loss** — constrains stroke start direction to the human arm's comfortable range (**≈ +75° to −165°**) via cosine similarity, applied at pen-down transitions.
    - **Progressive training**: phase 1 on QuickDraw (general decomposition), phase 2 on 1,000 glyphs from KaiTi-GB2312 + KanjiVG.
  - **(b) Tool-Aware Fine-tuning — the RL stage, in "CalliEnv" (OpenAI Gym + Tianshou).**
    - **State** `S_t = (h, r, l, θ, ρ, δx, δy, vx, vy)` — a **9-dimensional vector, not an image**: stroke progress `h`, utensil geometry `r, l, θ`, current curvature `ρ`, prior actions as offsets, and movement direction.
    - **Action** `a_t = (δx, δy)` — displacement of the discretised control point `P_t` (plus `θ` for a flat-tip marker).
    - **Constrained exploration** — the exploration zone is restrained to `P_t + a_t` around the coarse trajectory: *"we focus on the exploration process around the coarse trajectory, avoiding the disruption of ineffective experiences."*
    - **Adaptive shape reward** (Eq. 8), piecewise on stroke progress `h`:
      `R_ada = √(r_max/r_t)·‖1/r_t − 1/r_{t−1}‖` for `h ∈ [0.2, 0.8]` (smoothness via curvature change in the stroke body), and `(o_in − o_out)/o_tool` for `h ∈ [0,0.2) ∪ (0.8,1]` (alignment at the endpoints: tool pixels inside the glyph minus outside, normalised by tool area).
    - **Terminal reward** `R_fin = 80 · IoU(I', I)`. They state the ×80 factor exists *"to improve the sensitivity of the SAC algorithm to reward shaping."*
    - **Total** `R = (1/T)Σ_t R_ada + R_fin`.
    - **Algorithm: SAC.** Actor `(|s|, 64, 128, |a|)`; Critic `(|s|+|a|, 128, 128, 1)`; `α = 0.95`, `γ = 0.95`, `τ = 0.95`; `policy_lr = q_lr = 1e-4`; replay `2²⁰`; batch `2¹⁰`; **150 epochs × 10,000 steps = 1.5M steps**.
  - **Tool models (Fig. 3).** Fude pen (semi-minor/major axis `r`, `l`, rotation `θ`, dynamics-controlled), flat-tip marker (half-width/half-length, rigid, `θ` user-controlled), calligraphy brush (radius, droplet length, `θ` dynamics-controlled). *"The parameters and movement dynamics are all approximation results from the real world."*
- **Metrics.** **SNR (Stroke Number Ratio)** `= N_s / N_gt` — lower is better, measures stroke continuity/fragmentation. **Chamfer Distance (CD)** — contour similarity of the redrawn glyph.
- **Results (Table V, 200 Kaiti-style Chinese glyphs).**

  | Method | Supervision | SNR ↓ | CD ↓ |
  |---|---|---|---|
  | Learning to Paint (D02) | RL | 5.660 | 6.978 |
  | General Virtual Sketching | Unsupervised | 5.602 | 2.092 |
  | **CalliRewrite (theirs)** | Unsupervised | **1.199** | **1.979** |
  | VectorNet | Supervised | 1.039 | 1.614 |

  Low-resource study (Table III): SNR/CD are optimal at **1,000 training glyphs**; 2,000 and 5,000 do not improve. Ablation (Table IV): `L_smo` + `L_ang` together give the best SNR (1.199) and CD (1.979); either alone is worse.
- **Robot.** **Dobot Magician, 4-DoF** — a low-cost arm. Calibration procedure: *"leave traces on the paper at varying z heights, measure widths, calculate r, and establish the z–r connection through linear fitting."* Rewrites Chinese (Oracle → Cursive), English cursive with a fude pen, and **unseen Ancient Egyptian and Tamil** characters.
- **Limitations & future work (their Fig. 10 failure cases and conclusion).** Inaccurate stroke segmentation and **error accumulation in the robotic arm**; *"imprecision in tool modeling, and a lack of real-world training scenarios to bridge the sim2real gap. We leave these challenges as our future work."*

**→ RoboSketch-RL implications.**

1. **A third independent "the sim2real / real-world feedback gap is future work" statement**, this time from ICRA 2024 — the most recent close neighbour. The gap our project targets is live, acknowledged, and recent.
2. **Our reward architecture is validated by a peer-reviewed neighbour.** They use dense per-step shaping + a large-multiplier IoU terminal reward; we use IoU-delta + potential shaping + a `+2.0` terminal bonus. The structures match. Note their explicit remark that the **terminal multiplier's magnitude mattered** — our `+2.0` on top of `10 × ΔIoU` is comparatively tiny and is worth a sensitivity sweep.
3. **SNR is a metric we should adopt immediately.** It measures stroke fragmentation, which IoU is blind to — an agent can achieve decent IoU with a scribbly, discontinuous path. And note that **Learning to Paint scores worst on SNR (5.66)**: RL stroke agents are specifically prone to fragmented, overlapping strokes. This is very likely a failure mode present in our agents that we currently have no metric to detect.
4. **The z→stroke-width linear fit on a Dobot Magician is our exact hardware situation.** It is a concrete, cheap, budget-compatible real2sim calibration recipe, and it is what should replace our hard-coded `0.0035 m` stroke width.
5. **Constrained exploration around a coarse trajectory** is a strong idea for our letters stage: generate a coarse plan (analytically, or with a small supervised model), then let RL refine within a bounded tube. This is the same "prior → refine" pattern as A07 (Sketch-to-Skill) and D08's BC warm start.
6. **1,000 training samples is enough** for the sequence model. Reassuring for a small project — we do not need a large dataset for the letters stage.

---

## D10 ◇ Multi-Pen Robust Robotic 3D Drawing Using Closed-Loop Planning
**Liu, Wan, Koyama, Harada — Osaka University — IEEE T-ASE (arXiv:2009.14501)**

- **Problem.** Robustly draw on **3-D surfaces** with pens that the robot **picks up and grasps** (rather than pens rigidly bolted to the flange), with multiple pen changes.
- **Method.** A closed-loop pipeline: visual detection of the surface → mapping 2-D strokes onto the 3-D surface → grasp planning to pick up a pen → **in-hand pen pose estimation** → force control during contact → **error detection and recovery**, repeating until each stroke is successfully drawn.
- **Results.** Robust drawing across surfaces and pens; explicit recovery from execution failures.
- **Limitations.** No learning — every capability is engineered. Requires accurate perception and force control hardware.
- **→ Implications.** (a) This is the **honest classical baseline**: it shows how much is achievable *without* RL, and it is the bar a reviewer will hold us to. (b) Its error-detection-and-recovery module is an *engineered* version of what our RL policy should acquire *implicitly* — which suggests the single most convincing experiment we can run: **inject a disturbance (pen slip / paper shift / partial ink failure) mid-episode and show the closed-loop RL policy recovers while an open-loop IK plan does not.** That converts our "closed-loop vision" claim from an assertion into a measurement.

---

## D11 ◇ SketcherX: AI-Driven Interactive Robotic Drawing with Diffusion Model and Vectorization
**Song, Kang, Kwak — Seoul National University — arXiv:2409.15292 (2024)**

- **Method.** Two-agent system: a face-processing/vectorization agent and a drawing agent; a LoRA-fine-tuned diffusion model provides stylisation; strokes are vectorised and executed by the arm. Optimised for speed (interactive portrait drawing).
- **→ Implications.** (a) A 2024 systems contrast that uses **no RL** and still produces high-quality, fast, deployed drawing — a reminder that our novelty must rest on the *learning and feedback* claim, not on output quality. (b) Its vectorisation front-end is a plausible way to convert arbitrary target images into stroke sets that our RL agent could consume, replacing analytic shapes.

---
---

# PART 3 — Advanced Methods

## A01 ◆ FRIDA: A Collaborative Robot Painter with a Differentiable, Real2Sim2Real Planning Environment
**Schaldenbrand, McCann, Oh — CMU — ICRA 2023 (Best Paper in Deployed Systems finalist) — arXiv:2210.00664**

- **Problem statement.** Enable a robot to paint towards **high-level semantic goals** (a text description, a style image, a sketch) rather than pixel-replicating an input, and to adapt as the painting physically evolves.
- **Research gap.** Two camps, both inadequate. **Engineered systems** (Dark Factory portraits, e-David) meticulously minimise the sim2real gap for one specific setup but *"are not generalizable to different equipment or settings"* and generally only replicate a given image. **Learning-enabled systems** plan strokes in simulation and execute them, but *"due to a huge sim2real gap, brush stroke plans based directly on simulation methods produce poor-quality paintings or are even infeasible on real robot systems."* They name D02 (Huang et al.) as an example, and note that D01 (Lee et al.) *"is designed to plan once and execute a given plan as is without observation feedback in the loop."*
- **Objectives.** A high-fidelity differentiable painting simulator; planning under stochastic execution; semantic goals; an intuitive multimodal interface.
- **Methodology.**
  - **Brush stroke model.** Three parameters: thickness `h` (how hard the brush is pressed), bend `b`, length `l`; plus canvas location `(x, y)`, orientation `θ`, colour `ρ`. Trajectory = cubic Bézier.
  - **Real2Sim2Real — the key technique.** During a **calibration phase**, the robot paints random brush strokes; these are photographed; a network **`param2stroke`** (two linear layers → two convolutional layers → bilinear upscaler) is trained to map `(h, l, b)` → the stroke's **actual appearance map**. Crucially, *"our definition of thickness connects the parameter space with a brush tool and a robot"* — the simulator is fitted to the robot's real marks. Because painting is slow, they **augment** a small real dataset using differentiable rigid transformations and a stamping methodology, rather than collecting thousands of real strokes.
  - **Differentiable simulated painting.** `param2stroke` output → pad to canvas size → rotate/translate → colorize → composite onto the canvas. The whole rendering path is differentiable, so a loss on the rendered canvas back-propagates to the **stroke parameters**, updated by SGD. (Planning is **gradient descent, not RL**.)
  - **Planning with feedback (Algorithm 1).** `canvas = camera()`; render the remaining plan onto the *photograph of the real canvas*; compute the objective; SGD-update the plan; execute a batch of strokes; re-photograph; re-optimise. Continual re-planning against reality.
  - **Objectives.** (1) CLIP image–text cosine similarity; (2) style loss = EMD between VGG style features; (3) simple replication `‖r(p) − t‖²`; (4) semantic replication `‖CLIP_conv(r(p)) − CLIP_conv(t)‖²`.
- **Experimental setup.** Rethink Sawyer robot; **Canon EOS Rebel T7** DSLR observing the canvas; 11×14 inch canvas board; premixed acrylics in palette trays, up to 12 colours; brush rigidly attached and held perpendicular; **"Indirect, diffused lighting is necessary, since direct lighting can cause too much glare from the wet paint into the camera."**
- **Results — the numbers that matter to us.**
  - **Stroke model fidelity** (mean L₁ over 50 samples, modelled vs real strokes): FRIDA **0.012 train / 0.018 test** vs DiffVG 0.028 / 0.028, significant at *p* < 0.01.
  - **Sim2real gap, whole paintings** (Fig. 9; Δ = MSE between the simulated plan and a photograph of the real painting):

    | Method | Δ (sim2real gap) |
    |---|---|
    | Huang et al. 2019 — Learning to Paint (RL) | 0.156 |
    | Schaldenbrand & Oh 2021 | 0.066 |
    | **FRIDA** | **0.029** |

    Their diagnosis of the RL method: *"allowing strokes that are huge in size and have varying opacity; however, when we fed the strokes to a painting robot, the painting produced was vastly dissimilar to both the simulation and target image."*
  - **Replanning matters, quantitatively.** Fig. 11: **without** replanning, the deviation between the current canvas and the initial plan *"grows linearly as the plan is executed"*; **with** replanning, the plan adapts. Measured over ~800 brush strokes.
  - **Human evaluation.** 103 Amazon Mechanical Turk participants; the semantic objective was preferred by **73.3%** (replication question) and **68.3%** (high-level question), both significantly above 50% at *p* < 0.01.
- **Limitations.** Gradient-based planning, not RL — no learned policy, so every new painting requires a fresh optimisation. Requires a good camera and controlled lighting. Paint/brush handling is heavily engineered (rags, water, palettes).

**→ RoboSketch-RL implications — the highest-value paper in the library for Phase D.**

1. **Adopt Δ = MSE(simulated canvas, photograph of real canvas) as our sim-to-real metric.** We currently have *no* sim-to-real metric at all. This one is published, simple, and gives us a number to compare against (0.029 / 0.066 / 0.156). This alone materially strengthens the eventual hardware chapter.
2. **Fit the ink model instead of guessing it.** `param2stroke` is the general form; **D09's z→width linear fit is the budget version**. Our `pen_radius_px` currently derives from a hard-coded `0.0035 m`. Replace with a fitted model from real pen strokes. Same for the camera model: `cam_px=150` and the `>60` threshold in `_perceive()` are guesses that should be measured.
3. **The linear error growth without replanning is the strongest published argument for our closed-loop premise** — and it is a measurable claim we can reproduce in simulation *today*, with no hardware: run an agent open-loop (plan once from the initial state, execute blind) vs closed-loop, inject realistic execution noise, and plot deviation against stroke count. That is a compelling figure and it directly answers D01's camera-free objection.
4. **FRIDA's critique of Learning to Paint is a warning about action spaces.** An action space that is expressive in simulation but not physically realisable destroys transfer (Δ = 0.156). Our pen-space `(dx, dy)` with IK is conservative and physically grounded — that is a strength worth stating, backed by both FRIDA's measurement and D01's stroke-design argument.
5. **Practical hardware notes for free:** indirect diffuse lighting (glare kills the camera reward), rigid tool attachment, camera-observes-canvas geometry.
6. **A strong non-RL baseline exists.** Gradient descent through a differentiable renderer works very well. If we can build a differentiable version of our ink model — which is easy for a thin line — we could compare PPO against direct trajectory optimisation. A reviewer will ask why RL is needed when gradients are available; our answer must be about *execution error and unmodelled dynamics*, and we should demonstrate it rather than assert it.

---

## A02 ◇ CoFRIDA: Self-Supervised Fine-Tuning for Human-Robot Co-Painting (Schaldenbrand et al., ICRA 2024, Best Paper on HRI)

- **Method.** Self-supervised fine-tuning of an image-generation model to produce *drawable* continuations of a partially-drawn canvas, enabling turn-taking co-painting with a human. Training pairs (partial canvas → completion) are generated automatically.
- **→ Implications.** (a) The self-supervised pair-generation trick maps directly onto generating training targets for our agent at no labelling cost. (b) "Drawability-aware generation" — constraining a generative model to outputs the robot can physically produce — is a good future-work direction. (c) Evidence that this field rewards HRI and interaction framings at top venues.

---

## A03 ◇ CLIPasso: Semantically-Aware Object Sketching (Vinker et al., SIGGRAPH 2022, Best Paper)

- **Problem.** Generate sketches at controllable levels of abstraction without training on sketch datasets.
- **Method.** A sketch is a set of Bézier curves; control points are optimised **directly by gradient descent** through a **differentiable rasteriser (DiffVG)** against a **CLIP-based perceptual loss** (both semantic CLIP-embedding distance and geometric distance in intermediate CLIP layers). Abstraction is controlled by the number of strokes. Saliency-based initialisation of stroke positions.
- **Results.** Recognisable, structurally faithful sketches at very low stroke counts; works on arbitrary object categories with no sketch training data.
- **Limitations.** Per-image optimisation (slow, no learned policy); requires a foreground object; not robot-aware.

**→ RoboSketch-RL implications — an objection we must answer.**

1. **IoU is the wrong objective the moment we reach letters.** IoU measures ink overlap. A `3` drawn with the right ink coverage but the wrong topology scores well; a perfectly legible `3` shifted two pixels scores badly. CLIPasso is the definitive demonstration that *perceptual/semantic* objectives produce better sketches than pixel objectives. **Concrete recommendation: at the digits/letters stage, report a recognisability metric alongside IoU** — e.g. the confidence of a small MNIST/EMNIST classifier on the drawn canvas. That is cheap, quantitative, and directly addresses the critique.
2. **Stroke count as an explicit abstraction/efficiency knob** is a cleaner formulation than our `time_penalty`.
3. Another instance of "gradient descent through a differentiable renderer" as a strong non-RL alternative (see A01).

---

## A04 ◇ Diffusion Policy: Visuomotor Policy Learning via Action Diffusion (Chi et al., RSS 2023 / IJRR 2025)

- **Problem.** Behaviour-cloned visuomotor policies struggle with **multimodal** action distributions (several valid ways to do the task), high-dimensional action spaces, and training instability.
- **Method.** Represent the policy as a **conditional denoising diffusion process over action sequences** ("action chunks") conditioned on recent visual observations, executed with **receding-horizon control** (predict `T_p` steps, execute `T_a` of them, re-plan). Time-series diffusion transformer / CNN variants.
- **Results.** Benchmarked on 15 tasks across 4 robot platforms; large average improvement over prior BC methods; notably stable training.
- **Limitations.** It is **behaviour cloning** — it needs demonstrations and does not optimise a reward. Inference cost from iterative denoising.

**→ RoboSketch-RL implications.**

1. **Drawing is intensely multimodal**, and this explains a failure mode we should look for. A square can be traced clockwise or counter-clockwise from any of four corners — eight-plus equally optimal policies. A unimodal Gaussian PPO policy at a corner will **average** the modes and move diagonally into the square's interior. If our agents produce cut corners or interior scribble, this is very likely the cause, not insufficient training.
2. **Action chunking is the fix that does not require abandoning RL.** D02's "Action Bundle" (`k = 5`) is the same idea and is *already validated in our exact task family*. Predicting a short sequence of pen moves per policy step is a better-motivated route to smooth strokes than `smooth_penalty`.
3. As a comparison arm: a Diffusion Policy trained by BC on our free analytic demonstrations would be a strong, modern baseline — and it would sharpen the question of what RL buys us over imitation.

---

## A05 ◇ Stroke-based Rendering: From Heuristics to Deep Learning (Nolte, Melnik, Ritter, 2022 — survey)

- Taxonomy of the whole field: rule-based heuristics → stroke optimisation → differentiable vector graphics → RL agents → transformers → robotic applications. Traces the lineage from sketch-rnn onward.
- **→ Implications.** Read this **before** writing related work. It will tell us which lineage to claim, which comparisons reviewers expect, and which of our ideas already have established names. It is the cheapest possible insurance against a "the authors appear unaware of X" review.

---

## A06 ◇ Robot Synesthesia: A Sound and Emotion Guided AI Painter (Misra, Schaldenbrand, Oh, CMU, 2023)

- Converts audio/emotional input into a painting objective on the FRIDA platform.
- **→ Implications.** Evidence that in this field the accepted locus of novelty is **the objective/reward channel**, not the controller. That directly de-risks RoboSketch-RL's positioning: "we change where the reward comes from" is a publishable form of contribution here.

---

## A07 ◇ Sketch-to-Skill: Bootstrapping Robot Learning with Human Drawn Trajectory Sketches (Yu et al., 2025)

- Three stages: train a Sketch→3-D Trajectory generator; obtain trajectories and execution experience; pre-train a manipulation policy by BC, then refine with RL and guided exploration.
- **→ Implications.** The **"generate a prior → clone it → refine with RL"** recipe, which recurs in D07, D08, D09 and here. For us the prior is free: the analytic target *is* the ideal trajectory. This is very likely a faster path to letters than pure PPO exploration.

---

## A08 ◇ L2D2: Robot Learning from 2D Drawings (2025)

- Uses human 2-D drawings as robot supervision, handling the 2-D→3-D ambiguity.
- **→ Implications.** Keeps related work current; its 2-D↔3-D correspondence treatment matters if we ever leave the flat paper plane.

---
---

# PART 4 — Robotics and Vision (sim-to-real)

## V01 ◇ Domain Randomization for Transferring DNNs from Simulation to the Real World (Tobin et al., IROS 2017)

- **Problem.** Models trained on simulated images fail on real images (the reality gap); real data is expensive.
- **Method.** Randomise the simulator's *visual* parameters so aggressively — object textures and colours, lighting number/position/colour, camera pose, background, distractor objects, random noise — that the real world becomes just another sample from the training distribution. No realism required.
- **Results.** An object detector trained **only** on non-realistic randomised renders localises real objects to ~1.5 cm and supports real grasping.
- **Limitations.** Randomising too widely makes the task harder to learn (may need more capacity/data); does not address dynamics; choosing ranges is an art.

**→ RoboSketch-RL implications — directly actionable for H2.**

Our vision reward is computed by `DrawEnv._perceive()`, which currently models the camera as exactly two fixed operations: `cv2.resize` to `cam_px=150` and a threshold at `>60`. On real hardware, **none of these will hold**: lighting varies, paper is off-white and textured, the pen's contrast varies with ink flow, the camera has perspective and lens distortion, exposure drifts, and shadows from the arm fall across the paper.

**As written, `_perceive()` is a very optimistic camera.** H2's headline result — vision reward ≈ ground-truth reward — is therefore currently a claim about *one idealised camera*, and we should say so plainly.

The fix is a specific new experiment, **H4**: randomise the perception model during training — camera pose jitter and perspective warp, lighting/exposure gain, paper texture and colour, ink contrast, Gaussian blur, sensor noise, threshold jitter — and test whether (a) the agent still learns, and (b) the resulting policy is *more* robust when evaluated under perception conditions it never saw. That converts H2 from "vision works in an ideal sim" to "vision works across a distribution of realistic cameras," which is a much more defensible claim and requires no hardware.

---

## V02 ◇ Sim-to-Real Transfer of Robotic Control with Dynamics Randomization (Peng et al., ICRA 2018)

- **Method.** Randomise *physical* parameters during training — link masses, friction, damping, actuator gains, **control latency**, external perturbations — and use a **recurrent policy** so it can implicitly identify which dynamics it is currently in (online system identification without an explicit estimator).
- **Results.** Zero-shot transfer of a pushing policy from simulation to a real Fetch arm.
- **Limitations.** Wider randomisation costs sample efficiency; some gaps (unmodelled compliance, backlash) resist randomisation.

**→ RoboSketch-RL implications.**

1. **The simulated arm is a KUKA iiwa; the planned hardware is a ~₹10,000 arm with MG996R hobby servos.** The gap in backlash, compliance, tracking lag and repeatability is enormous — far larger than the gaps this paper addresses. Randomising `force=800`, `maxVelocity=10`, joint damping and especially **control latency** in `DrawEnv._move_arm()` is the standard mitigation and is nearly free to implement.
2. **Our pen-space action abstraction already buys much of this robustness** — the policy commands pen positions, and IK absorbs the arm's specifics. That is a genuine design strength, and it is *measurable*: train with `use_arm=True` under randomised dynamics and show IoU degrades gracefully. Claiming it without measuring it would be weaker than the evidence we can easily obtain.
3. Recurrent policies (SB3's `RecurrentPPO`) are the drop-in for implicit system identification, and would also help with the partial observability noted under D02.

---

## V03 ◇ Sim-to-Real Transfer in Deep RL for Robotics: a Survey (Zhao, Peña Queralta, Westerlund, IEEE SSCI 2020)

- Structured survey of transfer techniques: **domain randomization** (visual and dynamics), **domain adaptation**, **system identification**, **learning with disturbances**, **meta-learning**, **knowledge distillation**, and combinations, with trade-offs.
- **→ Implications.** Use it to *choose* a transfer strategy deliberately and defend that choice, rather than reporting "we randomised some things." It also supplies the citation scaffolding for the Phase D section. Note this is the survey **D01 also cites** — using it puts us in the same methodological conversation.

---
---

# PART 5 — Reinforcement Learning methodology

## R01 ◇ Unsupervised Perceptual Rewards for Imitation Learning (Sermanet, Xu, Levine, RSS 2017)

- **Problem.** Real-robot RL needs a reward, but ground-truth task state is unavailable without instrumentation.
- **Method.** From a small number of unlabelled human demonstration videos, discover intermediate **sub-goals**, and build a **dense perceptual reward** from progress through pretrained deep visual features. Then learn the task with real-robot RL using that reward alone.
- **Results.** Learns real manipulation (door opening) from a handful of demonstration videos, with a reward derived purely from vision.
- **Limitations.** Needs demonstrations; the discovered reward can be brittle to viewpoint and appearance change.

**→ RoboSketch-RL implications.**
1. **The argument structure is exactly our H2 argument** — "ground truth is unavailable on real hardware, therefore derive the reward from perception" — published in 2017. We must cite it as prior art and be careful not to present the *idea* of a perceptual reward as novel. Our contribution is the drawing-specific instantiation and, above all, the **quantified equivalence measurement**.
2. It offers a route for target shapes with **no analytic mask** (a photograph, a freehand sketch), where our IoU-against-a-known-mask reward simply does not exist.

---

## R02 ◆ End-to-End Robotic Reinforcement Learning without Reward Engineering
**Singh, Yang, Hartikainen, Finn, Levine — UC Berkeley — RSS 2019 — arXiv:1904.07854**

> **The most important paper in the library for positioning our novelty honestly.**

- **Problem statement.** End-to-end RL from pixels promises to remove hand-engineered perception — but then the *reward function* is specified manually, which *"requires either designing the very same perception pipeline that end-to-end reinforcement learning promises to avoid, or else instrumenting the environment with additional sensors."*
- **Research gap.** IRL needs expert demonstrations (burdensome, unnatural to provide, and demonstrating *how* defeats the point of autonomous discovery). Naive goal classifiers get **exploited**: *"the policy can learn to exploit the classifier, reaching states that are different from those that the classifier was trained on and fool it into outputting a success label erroneously."* VICE fixes exploitation but is on-policy and needs ~50k positive examples.
- **Objectives.** Learn robotic skills from images with **no** hand-designed reward, minimal human supervision, and few enough real-world samples to run on an actual robot.
- **Methodology — VICE-RAQ.**
  - A **classifier `g` over pixel observations** provides the reward: `r(s) = log p_g(y|s)`.
  - **VICE** (off-policy extension): the classifier is trained *adversarially* — positives are user-provided goal images, negatives are mined from the policy's own replay buffer — so the agent cannot simply walk outside the classifier's training distribution. Discriminator form `D_ψ(s,a) = exp(f_ψ(s,a)) / (exp(f_ψ(s,a)) + π(a|s))`. Action labels for positives are sampled from the current policy, removing the need for users to supply actions.
  - **RAQ (active queries)**: periodically show the user the state with the **highest predicted success probability** since the last query — `k = arg max_t log p_g(y=1|s_t)` — and ask for a binary success label. They note the max-entropy heuristic is *not* the right query rule here: the goal is to eliminate **false positives**, so querying high-confidence states is far more effective. 25–75 queries per run.
  - **mixup regularization** on the classifier: `s̃ = λs_i + (1−λ)s_j`, `ỹ = λy_i + (1−λ)y_j`, `λ ~ Beta(α,α)`. Without it the classifier gives a hard decision boundary — effectively a sparse reward. Mixup smooths it into a shaped reward, *"increasing both the stability and efficiency of the reinforcement learning process."*
  - **SAC** as the RL algorithm.
- **Architecture.** Two conv layers (8 filters sim / 32 real) each with max-pooling, then two FC layers of 256 units, ReLU. **The same architecture is used for the policy, the critic and the learned reward function.** Observations are 48×48 RGB (sim) / 84×84 (real). *"No other observations (such as joint angles or end-effector position) are provided to the policy."*
- **Environment / experimental setup.**
  - Simulated: Visual Pusher, Visual Door Opening, Visual Picker (7-DoF Sawyer model, end-effector position control). 10 goal examples per task; active query every 25k / 10k / 1k timesteps respectively.
  - Real: 7-DoF Sawyer; pushing a mug onto a coaster, draping cloth over a box, placing a book on a shelf between other books. **1–4 hours of real interaction.**
  - **Protocol: 5 random seeds per method per task**, plotting the mean in bold with each individual seed faint behind it.
  - **Baselines: sparse ground-truth reward, naive classifier, RAQ, VICE, VICE-RAQ.**
- **Results.** VICE-RAQ best on all tasks; nearly 100% success on Visual Door Opening across seeds. **The naive classifier and the sparse ground-truth reward baselines fail on most seeds.** VICE and RAQ show high inter-seed variance; VICE-RAQ has relatively low variance late in training.
- **Limitations.** Needs a modest number of human binary queries; classifier exploitation is mitigated, not eliminated; tasks have a single well-defined success condition.

**→ RoboSketch-RL implications — this reshapes how we should state H2.**

1. **Sharpen the novelty claim; do not overstate it.** "A reward from vision instead of privileged ground truth" is *established prior art* (R01 2017, R02 2019). Presenting it as new would be a serious related-work failure. What **is** ours, and is defensible:
   - The **drawing** instantiation, where the ground-truth reward is a *dense spatial mask* rather than a binary success label — so the comparison is far more informative than success/failure. We can measure the vision reward's cost in **IoU units**, not just success rate.
   - A **quantified equivalence result**: perception-only reward loses ≈ 0.04 mean true IoU versus privileged ground truth (0.41 vs 0.45), with the vision agent *better* on the circle. Framed as a *measurement*, that is a legitimate contribution — and it is exactly what D01, D03 and D09 all left unmeasured.
2. **We must test for reward exploitation — this is the sharpest threat to H2.** R02's central failure mode is the policy fooling the reward model. Our `_perceive()` downsamples and thresholds, which means **thin strokes can dilate and merge, and near-misses can threshold into apparent hits**. A concrete, runnable experiment: for vision-trained agents, plot `reward_iou − true_iou` over training. If the gap grows, the agent is learning to exploit the camera model. `DrawEnv` already logs both values in `info` (`"iou"` and `"reward_iou"`), **so this analysis can be run on existing data today.** If the gap is flat, that is a genuinely strong positive result for H2 and should be a figure in the paper.
3. **Adopt their evaluation protocol**: 5 seeds, mean-bold-plus-faint-individual-seeds plots, and a **sparse ground-truth baseline** alongside our dense one. Our multi-seed sweep is already headed here; matching an RSS protocol makes it publishable.
4. **mixup-style smoothing of the perception model** is a principled way to soften our hard `>60` threshold, which currently creates a discontinuous reward surface.

---

## R03 ◇ How to Train Your Robot with Deep RL: Lessons We've Learned (Ibarz, Tan, Finn, Kalakrishnan, Pastor, Levine, IJRR 2021)

- A candid retrospective on real-world robot RL from the Google Brain robotics team: reward specification, the **automatic reset problem**, safety, sample efficiency, non-stationarity, evaluation and reproducibility, illustrated with case studies.
- **→ Implications.**
  1. **Evaluation standards**: multiple seeds, report variance not just means, define success precisely, evaluate on held-out conditions. Directly relevant to the multi-seed sweep already running.
  2. **The reset problem** is free in simulation and expensive on hardware. Our Phase D plan must answer: who replaces the paper, and what happens when the pen runs dry? This belongs in the hardware design, not discovered later.
  3. **Reproducibility checklist** — worth conforming to explicitly, given that reproducibility is already one of this project's stated values.

---

## R04 ◇ Curriculum Learning for RL Domains: A Framework and Survey (Narvekar et al., JMLR 2020)

- **Framework.** Curriculum learning decomposes into **task generation**, **task sequencing**, and **knowledge transfer**.
- **Evaluation metrics.** **Jump-start** (initial performance boost from the curriculum), **time-to-threshold** (steps to reach a target performance), **asymptotic performance**.
- **→ Implications.** RoboSketch-RL's task ladder (line → circle → square → triangle → digits → letters) is currently an *assumed* curriculum that has never been tested. This survey turns it into a measurable contribution:
  - **A concrete experiment we can run now, with no new machinery:** train `triangle` from scratch vs. from a `line`-pretrained policy, and report jump-start and time-to-threshold. If the curriculum helps, that is a result; if it does not, that is *also* a result and an honest one.
  - Automatic curriculum generation (sequencing target shapes by difficulty during training) is a plausible route to a stronger novelty claim than a hand-ordered ladder.
  - D08 and D09 both use progressive/curriculum training in the drawing domain, so this is well-precedented here.

---

## R05 ◇ Gymnasium: A Standard Interface for RL Environments (Towers et al., NeurIPS D&B)

- The standard RL environment API: `reset(seed=…)`, `step() → (obs, reward, terminated, truncated, info)`, spaces, wrappers, vectorisation.
- **→ Implications.** The correct citation for `DrawEnv`. More importantly: **releasing `DrawEnv` as a benchmark environment is itself a citable contribution.** A "RoboSketchBench" — a suite of drawing tasks with standard targets, metrics (IoU/MSE/chamfer/SNR) and baselines — would be a genuinely useful community artefact and materially improves the paper's impact story. Conforming carefully to the API (correct `terminated` vs `truncated` semantics, proper seeding, registered env IDs) is a prerequisite.

> **Also cite:** Raffin et al., *Stable-Baselines3: Reliable RL Implementations*, **JMLR 22(268):1–8, 2021** — the PPO/SAC implementation actually used.

---
---

# Remaining full-read queue (◇ → ◆), in priority order

Reading these in order will retire the remaining uncertainty. Each is expected to take 30–60 minutes.

| Priority | Paper | Why it needs a first-hand read |
|---|---|---|
| 1 | **D10** Multi-Pen 3D Drawing | We need its actual quantitative results to use it as the classical baseline. |
| 2 | **V01** Domain Randomization | We will implement its randomisation list directly into `_perceive()`; get the specifics right. |
| 3 | **D05** SPIRAL | Its MNIST setup is the template for our digits rung; need the exact formulation. |
| 4 | **R01** Unsupervised Perceptual Rewards | Prior art for our core claim — must be characterised precisely, not from memory. |
| 5 | **A03** CLIPasso | If we adopt a perceptual/recognisability metric, we need the loss details. |
| 6 | **F04** HER | If we go goal-conditioned, the relabelling strategies matter in detail. |
| 7 | **A05** SBR Survey | Read fully before writing related work. |
| 8 | **R04** Curriculum survey | Need the precise metric definitions for the curriculum experiment. |
| 9 | **F05** Visuomotor Policies | Spatial-softmax implementation details. |
| 10 | **V02** Dynamics Randomization | Randomisation ranges and the recurrent-policy setup. |
| 11–25 | F01–F03, F06, D06, D07, D11, A02, A04, A06–A08, V03, R03, R05 | Background depth; lower marginal value. |
