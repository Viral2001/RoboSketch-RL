# RoboSketch-RL — Research Paper Library

**Curated, ranked and downloaded literature base for**
*Vision-Guided Reinforcement Learning for Autonomous Robotic Drawing.*

Collected: **2026-08-12** · 33 papers · all PDFs stored locally in the folders below.

> **Purpose.** This library exists so the project becomes *research-driven* rather
> than an implementation of one arbitrary approach. Every design decision in
> RoboSketch-RL should eventually be traceable to either (a) a paper that
> justifies it, or (b) an explicit, defended departure from the literature.

**Companion documents**
- [`STUDY_NOTES.md`](STUDY_NOTES.md) — deep per-paper analysis (problem, gap, method, RL formulation, results, limitations, future work).
- [`COMPARATIVE_ANALYSIS.md`](COMPARATIVE_ANALYSIS.md) — cross-paper comparison, research-gap map, and novelty positioning.
- [`../docs/PROJECT_PROPOSAL_v2.md`](../docs/PROJECT_PROPOSAL_v2.md) — the concrete changes proposed to the project after the review.

---

## How this library is organised

| Folder | Holds | Count |
|---|---|---|
| [`01_Foundational/`](01_Foundational/) | The bedrock: the RL algorithms the project uses, end-to-end visuomotor learning, sequential sketch generation | 6 |
| [`02_Directly_Related/`](02_Directly_Related/) | Robots and agents that **actually draw** — the project's direct competitors and ancestors | 11 |
| [`03_Advanced_Methods/`](03_Advanced_Methods/) | Beyond the current scope: differentiable painting, semantic sketching, diffusion policies, sketch-conditioned robot learning | 8 |
| [`04_Robotics_and_Vision/`](04_Robotics_and_Vision/) | Sim-to-real transfer and the reality gap — needed for Phase D (hardware) | 3 |
| [`05_Reinforcement_Learning/`](05_Reinforcement_Learning/) | RL *methodology*: learning rewards from images, curriculum, practical robot-RL guidance, tooling | 5 |

**Classification tags used below**

- 🟩 **Foundational** — you must understand it to work in this area at all.
- 🟦 **Directly related** — same problem as RoboSketch-RL; defines the baseline and the related-work section.
- 🟪 **Advanced** — more capable than the current project; a source of extensions and future work.

---

## Master ranking (by importance to RoboSketch-RL)

Ranked on: *closeness to our problem* × *how much of our design it informs* × *quality of venue*.
Read in this order.

| # | Paper | Year | Venue | Class | Why it ranks here |
|---:|---|---|---|---|---|
| **1** | [From Scratch to Sketch: Deep Decoupled Hierarchical RL for Robotic Sketching Agent](02_Directly_Related/D01_FromScratchToSketch_Lee_ICRA2022.pdf) | 2022 | ICRA | 🟦 | The single closest paper in existence to RoboSketch-RL: RL agent + real arm + drawing. Defines the state of the art we must beat or differentiate from. |
| **2** | [Learning to Paint With Model-based Deep RL](02_Directly_Related/D02_LearningToPaint_Huang_ICCV2019.pdf) | 2019 | ICCV | 🟦 | The canonical stroke-RL formulation. Our `(target, canvas, pen)` observation and IoU-style reward are its descendants. Also the strongest argument for a *neural renderer*. |
| **3** | [FRIDA: A Collaborative Robot Painter with a Differentiable, Real2Sim2Real Planning Environment](03_Advanced_Methods/A01_FRIDA_Schaldenbrand_ICRA2023.pdf) | 2023 | ICRA | 🟪 | Best-in-class *real* drawing robot with a closed visual loop. Its **real2sim2real** calibration is the method that most directly de-risks our Phase D. |
| **4** | [Teaching Robots To Draw](02_Directly_Related/D03_TeachingRobotsToDraw_Kotani_ICRA2019.pdf) | 2019 | ICRA | 🟦 | Handwritten characters + line drawings on a real arm, learned not scripted — exactly the digits/alphabet rung of our roadmap, and a non-RL contrast. |
| **5** | [Proximal Policy Optimization Algorithms](01_Foundational/F01_PPO_Schulman2017.pdf) | 2017 | arXiv/OpenAI | 🟩 | The algorithm currently training every RoboSketch-RL agent. Must be cited and understood (clipped surrogate, GAE, on-policy sample cost). |
| **6** | [End-to-End Robotic RL without Reward Engineering](05_Reinforcement_Learning/R02_RLWithoutRewardEngineering_Singh_RSS2019.pdf) | 2019 | RSS | 🟩 | The strongest prior art for our headline claim (H2: reward from a camera, not from ground truth). Directly shapes how we must frame our novelty. |
| **7** | [Soft Actor-Critic](01_Foundational/F02_SAC_Haarnoja2018.pdf) | 2018 | ICML | 🟩 | The planned RQ3 comparison against PPO; the sample-efficiency argument that matters once a real arm is in the loop. |
| **8** | [Domain Randomization for Transferring DNNs from Simulation to the Real World](04_Robotics_and_Vision/V01_DomainRandomization_Tobin_IROS2017.pdf) | 2017 | IROS | 🟩 | The foundational answer to "will the camera policy survive on real hardware?" — visual randomization is the cheapest sim-to-real insurance we can buy. |
| **9** | [Autonomous Visual Rendering using Physical Motion](02_Directly_Related/D04_AutonomousVisualRendering_Prabhakar_WAFR2016.pdf) | 2016 | WAFR | 🟦 | A rigorous *control-theoretic* (ergodic) formulation of "make the image with motion" — the principled non-learning baseline our IK baseline should be upgraded to. |
| **10** | [Sim-to-Real Brush Manipulation using Behavior Cloning and RL](02_Directly_Related/D08_SimToRealBrush_BC_RL_Jia2023.pdf) | 2023 | arXiv | 🟦 | Same pipeline shape as ours (sim → real, drawing tool, RL), and shows BC-pretraining fixing exactly the exploration problem our reward shaping papers over. |
| **11** | [CalliRewrite: Recovering Handwriting Behaviors from Calligraphy Images without Supervision](02_Directly_Related/D09_CalliRewrite_Luo_ICRA2024.pdf) | 2024 | ICRA | 🟦 | Recent, unsupervised, SAC-fine-tuned, tool-aware, low-resource — the closest recent methodological neighbour, and a template for our letters/digits stage. |
| **12** | [How to Train Your Robot with Deep RL: Lessons We've Learned](05_Reinforcement_Learning/R03_HowToTrainYourRobot_Ibarz_IJRR2021.pdf) | 2021 | IJRR | 🟩 | The field's accumulated practical wisdom on evaluation protocol, reset problems, reward design and honest reporting. Will materially improve our experiments section. |
| **13** | [Sim-to-Real Transfer of Robotic Control with Dynamics Randomization](04_Robotics_and_Vision/V02_DynamicsRandomization_Peng_ICRA2018.pdf) | 2018 | ICRA | 🟩 | Our MG996R hobby servos will *not* match the simulated KUKA. This is how you make a policy tolerate that gap. |
| **14** | [Sim-to-Real Transfer in Deep RL for Robotics: a Survey](04_Robotics_and_Vision/V03_SimToRealSurvey_Zhao_SSCI2020.pdf) | 2020 | IEEE SSCI | 🟩 | Fast, structured map of every transfer technique; the citation backbone for our Phase D section. |
| **15** | [Synthesizing Programs for Images using Reinforced Adversarial Learning (SPIRAL)](02_Directly_Related/D05_SPIRAL_Ganin_ICML2018.pdf) | 2018 | ICML | 🟦 | Proves an RL agent can learn to draw MNIST digits in continuous strokes with a *learned discriminator* reward — the alternative to our hand-designed IoU reward. |
| **16** | [End-to-End Training of Deep Visuomotor Policies](01_Foundational/F05_EndToEnd_VisuomotorPolicies_Levine2016.pdf) | 2016 | JMLR | 🟩 | The origin of pixels-to-actions robot learning, and of the spatial-softmax architecture we should try in place of the default CNN. |
| **17** | [Unsupervised Perceptual Rewards for Imitation Learning](05_Reinforcement_Learning/R01_UnsupervisedPerceptualRewards_Sermanet2017.pdf) | 2017 | RSS | 🟩 | Reward-from-vision without instrumentation — the conceptual ancestor of our vision reward, and a route to rewards for shapes with no analytic target. |
| **18** | [Curriculum Learning for RL Domains: A Framework and Survey](05_Reinforcement_Learning/R04_CurriculumLearning_Survey_Narvekar_JMLR2020.pdf) | 2020 | JMLR | 🟩 | Our roadmap *is* a curriculum (line→circle→square→triangle→digits→letters). This gives it formal grounding and evaluation metrics (jump-start, time-to-threshold). |
| **19** | [Hindsight Experience Replay](01_Foundational/F04_HER_Andrychowicz2017.pdf) | 2017 | NeurIPS | 🟩 | The principled fix for our sparse/shaped-reward tension: relabel "what you drew" as "what you meant to draw". Highly applicable if we go multi-target goal-conditioned. |
| **20** | [Stroke-based Rendering: From Heuristics to Deep Learning](03_Advanced_Methods/A05_StrokeBasedRendering_Survey_Nolte2022.pdf) | 2022 | arXiv survey | 🟪 | One-stop map of the whole stroke-generation field; makes the related-work section defensible and reveals which lineage we belong to. |
| **21** | [Soft/Continuous control: DDPG](01_Foundational/F03_DDPG_Lillicrap2016.pdf) | 2016 | ICLR | 🟩 | The continuous-control ancestor of SAC/TD3 and the algorithm used by most prior *drawing-robot* control papers — needed to read them. |
| **22** | [CoFRIDA: Self-Supervised Fine-Tuning for Human-Robot Co-Painting](03_Advanced_Methods/A02_CoFRIDA_Schaldenbrand_ICRA2024.pdf) | 2024 | ICRA | 🟪 | Shows where the drawing-robot field is going (interaction, self-supervision) and how to build training data without human labels. |
| **23** | [A Neural Representation of Sketch Drawings (sketch-rnn)](01_Foundational/F06_SketchRNN_Ha2018.pdf) | 2018 | ICLR | 🟩 | The sequential-stroke representation (Δx, Δy, pen-state) that our action space already imitates — cite it, and use QuickDraw as a dataset. |
| **24** | [Learning to Sketch with Deep Q Networks and Demonstrated Strokes](02_Directly_Related/D07_LearningToSketch_DQN_Zhou2018.pdf) | 2018 | BMVC | 🟦 | Demonstration-augmented sketch RL; the value-based counterpart to our policy-gradient approach. |
| **25** | [Multi-Pen Robust Robotic 3D Drawing Using Closed-Loop Planning](02_Directly_Related/D10_MultiPen3DDrawing_ClosedLoop_Liu2021.pdf) | 2021 | IEEE T-ASE | 🟦 | The best *non-learning* closed-loop drawing system — the honest classical baseline our paper is obliged to compare against. |
| **26** | [CLIPasso: Semantically-Aware Object Sketching](03_Advanced_Methods/A03_CLIPasso_Vinker_SIGGRAPH2022.pdf) | 2022 | SIGGRAPH (TOG) | 🟪 | Best-paper-award proof that a *perceptual* loss beats a pixel loss for sketching. The direct challenge to IoU as our objective. |
| **27** | [Diffusion Policy: Visuomotor Policy Learning via Action Diffusion](03_Advanced_Methods/A04_DiffusionPolicy_Chi_RSS2023.pdf) | 2023 | RSS / IJRR | 🟪 | Current SOTA visuomotor policy class; the strongest candidate for a "modern method" comparison arm and for multimodal stroke choices. |
| **28** | [Unsupervised Doodling and Painting with Improved SPIRAL](02_Directly_Related/D06_ImprovedSPIRAL_Mellor2019.pdf) | 2019 | arXiv (DeepMind) | 🟦 | The scaled-up SPIRAL with better analysis of what the drawing agent actually learns. |
| **29** | [Sketch-to-Skill: Bootstrapping Robot Learning with Human Drawn Trajectory Sketches](03_Advanced_Methods/A07_SketchToSkill_Yu2025.pdf) | 2025 | arXiv | 🟪 | Inverts our problem (sketch → robot skill); a source of ideas for turning a target image into an initial trajectory prior (i.e. our BC warm start). |
| **30** | [L2D2: Robot Learning from 2D Drawings](03_Advanced_Methods/A08_L2D2_RobotLearningFrom2DDrawings_2025.pdf) | 2025 | arXiv | 🟪 | Very recent 2D-drawing-as-robot-supervision work; keeps our related work current. |
| **31** | [Robot Synesthesia: A Sound and Emotion Guided AI Painter](03_Advanced_Methods/A06_RobotSynesthesia_Misra2023.pdf) | 2023 | arXiv (CMU) | 🟪 | Alternative reward modalities — evidence that the objective, not the controller, is where drawing-robot novelty currently lives. |
| **32** | [SketcherX: AI-Driven Interactive Robotic Drawing with Diffusion and Vectorization](02_Directly_Related/D11_SketcherX_Song2024.pdf) | 2024 | arXiv | 🟦 | A 2024 full-system robotic portrait drawer; useful as a systems-engineering contrast (fast, LoRA/diffusion, no RL). |
| **33** | [Gymnasium: A Standard Interface for RL Environments](05_Reinforcement_Learning/R05_Gymnasium_Towers2024.pdf) | 2024 | NeurIPS D&B | 🟩 | The API our environment implements; the correct citation for `DrawEnv`, plus environment-design conventions we should conform to. |

---

# 01_Foundational

Papers you must understand to defend the project's basic choices.

### F01 — Proximal Policy Optimization Algorithms 🟩
- **Authors:** John Schulman, Filip Wolski, Prafulla Dhariwal, Alec Radford, Oleg Klimov (OpenAI)
- **Year / venue:** 2017 · arXiv:1707.06347 (de-facto standard; no formal venue)
- **Link:** https://arxiv.org/abs/1707.06347 · [local PDF](01_Foundational/F01_PPO_Schulman2017.pdf)
- **Relevance:** This *is* the algorithm in [`rl/train.py`](../rl/train.py). Every RoboSketch-RL result to date is a PPO result.
- **Technique:** On-policy policy gradient with a **clipped probability-ratio surrogate objective**, multiple epochs of minibatch updates per rollout, GAE(λ) advantage estimation, shared actor–critic network.
- **What to take:** the meaning of every hyperparameter we are currently leaving at default (`n_steps`, `batch_size`, `clip_range`, `ent_coef`, `gae_lambda`); why PPO is sample-hungry (on-policy) and therefore a poor choice for training *on real hardware*; the correct citation and a defensible justification for "PPO first".
- **Class:** Foundational.

### F02 — Soft Actor-Critic: Off-Policy Maximum Entropy Deep RL with a Stochastic Actor 🟩
- **Authors:** Tuomas Haarnoja, Aurick Zhou, Pieter Abbeel, Sergey Levine (UC Berkeley)
- **Year / venue:** 2018 · **ICML 2018** · arXiv:1801.01290
- **Link:** https://arxiv.org/abs/1801.01290 · [local PDF](01_Foundational/F02_SAC_Haarnoja2018.pdf)
- **Relevance:** The planned **RQ3** comparison (PPO vs SAC). Also the right algorithm if we ever fine-tune on the physical arm, because off-policy replay is orders of magnitude more sample-efficient.
- **Technique:** Maximum-entropy RL — maximise reward *plus* policy entropy; off-policy actor–critic with twin Q-functions, a replay buffer and (in v2) automatic temperature tuning.
- **What to take:** the entropy term is a principled exploration mechanism that would attack our "pen gets stuck in a local optimum" problem more cleanly than hand-tuned `prox_weight`; the experimental protocol for a *fair* on-policy vs off-policy comparison (compare at equal environment steps **and** equal wall-clock, report both).
- **Class:** Foundational.

### F03 — Continuous Control with Deep Reinforcement Learning (DDPG) 🟩
- **Authors:** Timothy P. Lillicrap, Jonathan J. Hunt, Alexander Pritzel, Nicolas Heess, Tom Erez, Yuval Tassa, David Silver, Daan Wierstra (DeepMind)
- **Year / venue:** 2016 · **ICLR 2016** · arXiv:1509.02971
- **Link:** https://arxiv.org/abs/1509.02971 · [local PDF](01_Foundational/F03_DDPG_Lillicrap2016.pdf)
- **Relevance:** Most existing *drawing-robot control* papers (e.g. the DDPG drawing-robot trajectory-tracking line of work) use DDPG. To read and critique them you need this.
- **Technique:** Deterministic policy gradient + DQN machinery (replay buffer, target networks) for continuous action spaces.
- **What to take:** why deterministic policies are fragile without careful exploration noise (motivates SAC); the lineage DDPG → TD3 → SAC, which lets us justify skipping DDPG in our own comparison.
- **Class:** Foundational.

### F04 — Hindsight Experience Replay 🟩
- **Authors:** Marcin Andrychowicz, Filip Wolski, Alex Ray, Jonas Schneider, Rachel Fong, Peter Welinder, Bob McGrew, Josh Tobin, Pieter Abbeel, Wojciech Zaremba (OpenAI)
- **Year / venue:** 2017 · **NeurIPS 2017** · arXiv:1707.01495
- **Link:** https://arxiv.org/abs/1707.01495 · [local PDF](01_Foundational/F04_HER_Andrychowicz2017.pdf)
- **Relevance:** RoboSketch-RL currently trains **one policy per shape** with a heavily shaped reward. HER is the standard route to a *single goal-conditioned policy over many target shapes* — the direction that would make the contribution much stronger.
- **Technique:** Goal-conditioned RL with trajectory relabelling: a failed episode toward goal *g* is replayed as a successful episode toward the goal that was actually achieved.
- **What to take:** the concrete recipe for turning "the drawing I produced" into "a target I succeeded at", which converts our sparse IoU signal into dense supervision **without** hand-designed shaping terms (`prox_weight`, `smooth_penalty`, terminal bonus) that currently make the reward hard to defend.
- **Class:** Foundational.

### F05 — End-to-End Training of Deep Visuomotor Policies 🟩
- **Authors:** Sergey Levine, Chelsea Finn, Trevor Darrell, Pieter Abbeel (UC Berkeley)
- **Year / venue:** 2016 · **JMLR 17(39):1–40** · arXiv:1504.00702
- **Link:** https://arxiv.org/abs/1504.00702 · [local PDF](01_Foundational/F05_EndToEnd_VisuomotorPolicies_Levine2016.pdf)
- **Relevance:** The paper that established learning *perception and control jointly* from pixels on a real robot — the philosophical foundation of "vision-guided" in our title.
- **Technique:** Guided Policy Search (trajectory-centric RL → supervised learning), and a CNN with a **spatial softmax** producing 2-D feature points, which is far better suited to spatial tasks than a flatten-then-dense head.
- **What to take:** replace the default SB3 `NatureCNN` in our image observation with a spatial-softmax feature-point encoder — our task is *purely* spatial (where is the pen, where is the uncovered target), which is exactly what this architecture was designed for. Expect a real sample-efficiency win.
- **Class:** Foundational.

### F06 — A Neural Representation of Sketch Drawings (sketch-rnn) 🟩
- **Authors:** David Ha, Douglas Eck (Google Brain)
- **Year / venue:** 2018 · **ICLR 2018** · arXiv:1704.03477
- **Link:** https://arxiv.org/abs/1704.03477 · [local PDF](01_Foundational/F06_SketchRNN_Ha2018.pdf)
- **Relevance:** Defines the standard stroke representation `(Δx, Δy, pen_down, pen_up, end)` — RoboSketch-RL's action space `[dx, dy, pen_down]` is precisely this, so this is the citation for our action design. Also the source of the **QuickDraw** dataset.
- **Technique:** Sequence-to-sequence VAE over stroke sequences, with a Gaussian-mixture output distribution and a bidirectional-RNN encoder.
- **What to take:** the pen-state formulation for multi-stroke shapes (needed the moment we attempt letters, where `pen_always_down=True` becomes wrong); QuickDraw as a ready-made, citable target-shape dataset for the digits/letters rung; the mixture-density idea for representing multiple valid stroke choices.
- **Class:** Foundational.

---

# 02_Directly_Related

Systems that draw. This folder defines our related-work section and our baselines.

### D01 — From Scratch to Sketch: Deep Decoupled Hierarchical RL for Robotic Sketching Agent 🟦 ★ #1
- **Authors:** Ganghun Lee, Minji Kim, Minsu Lee, Byoung-Tak Zhang (Seoul National University)
- **Year / venue:** 2022 · **ICRA 2022** · arXiv:2208.04833
- **Link:** https://arxiv.org/abs/2208.04833 · [local PDF](02_Directly_Related/D01_FromScratchToSketch_Lee_ICRA2022.pdf)
- **Relevance:** **The closest published work to RoboSketch-RL.** An RL sketching agent that both decides *what to draw* and *how to move the arm*, trained without stroke supervision, deployed on a real manipulator. Our paper must position against this one explicitly.
- **Technique:** **Decoupled hierarchical RL** — a high-level *stroke-based rendering* policy (which stroke to lay down next, in image space) and a low-level *motor control* policy (how to move the arm to realise it) are learned **independently** and then composed. This decoupling is what makes it trainable at all.
- **What to take:** (i) the two-level decomposition is a direct, principled answer to why our flat pen-space policy will struggle to scale to letters; (ii) their argument for why decoupling beats end-to-end here; (iii) their evaluation protocol and real-robot deployment details; (iv) crucially, **what they did not do** — this is where our vision-reward gap lives.
- **Class:** Directly related (the primary competitor).

### D02 — Learning to Paint With Model-based Deep Reinforcement Learning 🟦 ★ #2
- **Authors:** Zhewei Huang, Wen Heng, Shuchang Zhou (Megvii / Peking University)
- **Year / venue:** 2019 · **ICCV 2019** · arXiv:1903.04411
- **Link:** https://arxiv.org/abs/1903.04411 · [local PDF](02_Directly_Related/D02_LearningToPaint_Huang_ICCV2019.pdf)
- **Relevance:** The canonical "agent learns to reproduce a target image stroke-by-stroke" paper. Our `DrawEnv` observation (target + canvas + pen position, stacked as channels) and IoU-delta reward are the same design family.
- **Technique:** Model-based DRL with a **differentiable neural renderer** that predicts the canvas after a stroke, allowing gradients to flow through the rendering step; DDPG-style actor–critic; a **WGAN discriminator supplies the reward** instead of a pixel metric; hundreds of strokes per image.
- **What to take:** (i) the neural renderer as a way to get *dense, differentiable* credit assignment — a plausible major upgrade to our environment; (ii) the learned-discriminator reward as the principled alternative to hand-designed IoU; (iii) their evidence that model-based beats model-free by a large margin in this exact task family, which is a real threat to the "PPO on a black-box sim" design.
- **Class:** Directly related.

### D03 — Teaching Robots To Draw 🟦
- **Authors:** Atsunobu Kotani, Stefanie Tellex (Brown University, H2R Lab)
- **Year / venue:** 2019 · **ICRA 2019**
- **Link:** https://h2r.cs.brown.edu/wp-content/uploads/kotani19.pdf · [local PDF](02_Directly_Related/D03_TeachingRobotsToDraw_Kotani_ICRA2019.pdf)
- **Relevance:** Directly targets the **handwritten characters / line drawings** rung of our roadmap, on a real manipulator, learned from data rather than hand-coded paths. It also generalises to *unseen alphabets* (Greek, Tamil, Hindi) — the exact generalisation claim we would want to make.
- **Technique:** A learned model that, given an image of a drawing, infers a **continuous drawing plan** (one continuous motion per stroke) and executes it — supervised sequence learning from demonstrations, **not** RL.
- **What to take:** (i) the cross-alphabet generalisation experiment design, which is a far stronger evaluation than "four fixed shapes"; (ii) a rigorous non-RL baseline that our RL approach must justify itself against — if supervised stroke-plan prediction already solves letters, "why RL?" becomes the reviewer's first question, and we need an answer (ours: no demonstrations required, and closed-loop correction of execution error).
- **Class:** Directly related.

### D04 — Autonomous Visual Rendering using Physical Motion 🟦
- **Authors:** Ahalya Prabhakar, Anastasia Mavrommati, Jarvis Schultz, Todd Murphey (Northwestern)
- **Year / venue:** 2016/2017 · **WAFR 2016** (Workshop on the Algorithmic Foundations of Robotics) · arXiv:1709.02758
- **Link:** https://arxiv.org/abs/1709.02758 · [local PDF](02_Directly_Related/D04_AutonomousVisualRendering_Prabhakar_WAFR2016.pdf)
- **Relevance:** Formalises "produce this image using the robot's physical motion" as a **control problem with guarantees** rather than a learning problem. This is the rigorous baseline our "traditional IK + trajectory planning" comparison should actually be.
- **Technique:** **Ergodic control** — treat the target image as a spatial distribution and synthesise trajectories whose time-averaged statistics match it, with formal convergence properties; works under real dynamic constraints.
- **What to take:** a *principled, citable, non-trivial* classical baseline. Comparing PPO against naive IK is a weak result; comparing against ergodic rendering is a real one. Also a useful reframing: our IoU objective is a crude version of their distribution-matching objective.
- **Class:** Directly related (baseline).

### D05 — Synthesizing Programs for Images using Reinforced Adversarial Learning (SPIRAL) 🟦
- **Authors:** Yaroslav Ganin, Tejas Kulkarni, Igor Babuschkin, S. M. Ali Eslami, Oriol Vinyals (DeepMind)
- **Year / venue:** 2018 · **ICML 2018** · arXiv:1804.01118
- **Link:** https://arxiv.org/abs/1804.01118 · [local PDF](02_Directly_Related/D05_SPIRAL_Ganin_ICML2018.pdf)
- **Relevance:** Trains an agent to draw **MNIST digits in a single continuous brush motion** — literally the next rung of our task ladder — with *no* stroke supervision.
- **Technique:** Adversarially-trained RL: an agent emits program/stroke commands to a non-differentiable renderer; a **discriminator** trained to separate rendered from real images provides the reward; distributed A2C-style training.
- **What to take:** (i) proof that the digits rung is reachable by RL; (ii) the discriminator-as-reward mechanism, which removes the need for a pixel-aligned target — very relevant if we want to draw a digit *in the style of* a target rather than pixel-matching it; (iii) a caution: they needed enormous compute, which bounds what we should promise.
- **Class:** Directly related.

### D06 — Unsupervised Doodling and Painting with Improved SPIRAL 🟦
- **Authors:** John F. J. Mellor, Eunbyung Park, Yaroslav Ganin, Igor Babuschkin, Tejas Kulkarni, Dan Rosenbaum, Andy Ballard, Theophane Weber, Oriol Vinyals, S. M. Ali Eslami (DeepMind)
- **Year / venue:** 2019 · arXiv:1910.01007
- **Link:** https://arxiv.org/abs/1910.01007 · [local PDF](02_Directly_Related/D06_ImprovedSPIRAL_Mellor2019.pdf)
- **Relevance:** The scaled/improved SPIRAL with much better analysis of *what the drawing agent actually learns* and how the reward shapes stroke style.
- **Technique:** SPIRAL + improved training, larger renderers, richer datasets; extensive qualitative analysis of the emergent drawing behaviour.
- **What to take:** their analysis methodology — showing intermediate canvases and stroke orders to explain agent behaviour — is exactly the qualitative-results section our paper needs alongside the IoU tables.
- **Class:** Directly related.

### D07 — Learning to Sketch with Deep Q Networks and Demonstrated Strokes 🟦
- **Authors:** Tao Zhou, Chen Fang, Zhaowen Wang, Jimei Yang, Byungmoon Kim, Zhili Chen, Jonathan Brandt, Demetri Terzopoulos (Adobe / UCLA)
- **Year / venue:** 2018 · **BMVC 2018** · arXiv:1810.05977
- **Link:** https://arxiv.org/abs/1810.05977 · [local PDF](02_Directly_Related/D07_LearningToSketch_DQN_Zhou2018.pdf)
- **Relevance:** Value-based (DQN) sketching agent **bootstrapped with demonstrated strokes** — the counterpoint to our pure policy-gradient, pure-exploration approach.
- **Technique:** Deep Q-learning over a discretised stroke action space, combined with demonstration data to seed the value function; a two-stage coarse-to-fine sketching pipeline.
- **What to take:** concrete evidence that demonstrations dramatically shorten training for sketch agents — supports adding a cheap BC warm start (we can generate perfect demonstrations for free from our analytic targets, which SPIRAL/L2P could not).
- **Class:** Directly related.

### D08 — Sim-to-Real Brush Manipulation using Behavior Cloning and Reinforcement Learning 🟦
- **Authors:** Biao Jia, Dinesh Manocha (University of Maryland)
- **Year / venue:** 2023 · arXiv:2309.08457
- **Link:** https://arxiv.org/abs/2309.08457 · [local PDF](02_Directly_Related/D08_SimToRealBrush_BC_RL_Jia2023.pdf)
- **Relevance:** The same overall pipeline as RoboSketch-RL — simulate a drawing tool, learn a policy, transfer to a real robot — with the sim-to-real step actually carried out. This is our Phase D blueprint and closest methodological sibling for the transfer stage.
- **Technique:** **Behaviour cloning to bootstrap, then RL to refine**, with a simulated brush/tool model and explicit attention to the sim-to-real gap of the drawing implement itself.
- **What to take:** (i) the BC→RL curriculum, which we can adopt cheaply; (ii) the insight that the **tool model** (how ink is actually deposited) is a first-class sim-to-real gap — our `cv2.line(..., pen_radius_px)` ink model is currently an unvalidated idealisation and is likely to be our biggest reality gap, larger than the arm dynamics.
- **Class:** Directly related.

### D09 — CalliRewrite: Recovering Handwriting Behaviors from Calligraphy Images without Supervision 🟦
- **Authors:** Yuxuan Luo, Zekun Wu, Zhouhui Lian (Peking University)
- **Year / venue:** 2024 · **ICRA 2024** · arXiv:2405.15776
- **Link:** https://arxiv.org/abs/2405.15776 · [local PDF](02_Directly_Related/D09_CalliRewrite_Luo_ICRA2024.pdf)
- **Relevance:** The most recent high-quality neighbour: recovers *how to write* from *an image of writing*, with no labelled demonstrations, and fine-tunes with **SAC** on a simulated tool for real robot execution. Extremely close to our problem statement, at the letters/characters rung.
- **Technique:** Coarse-to-fine: an unsupervised image→sequence model produces a coarse stroke order, then an **RL (SAC) stage fine-tunes a simulated brush/tool** to produce tool-aware, stylised trajectories; validated on constrained low-cost writing instruments.
- **What to take:** (i) the coarse-to-fine architecture — a cheap global plan followed by RL refinement — is very likely a better fit for our letters stage than flat PPO; (ii) their unsupervised framing shows how to avoid needing demonstration data; (iii) their tool-aware simulation is the standard we should hold our ink model to.
- **Class:** Directly related.

### D10 — Multi-Pen Robust Robotic 3D Drawing Using Closed-Loop Planning 🟦
- **Authors:** Ruishuang Liu, Weiwei Wan, Keisuke Koyama, Kensuke Harada (Osaka University)
- **Year / venue:** 2020/2021 · **IEEE Transactions on Automation Science and Engineering** · arXiv:2009.14501
- **Link:** https://arxiv.org/abs/2009.14501 · [local PDF](02_Directly_Related/D10_MultiPen3DDrawing_ClosedLoop_Liu2021.pdf)
- **Relevance:** The strongest **non-learning closed-loop** drawing system: visual detection → planning → execution → error detection → recovery, on 3-D surfaces, with the pen *grasped* rather than fixed. It shows exactly how much can be achieved without RL, which is the bar our contribution must clear.
- **Technique:** Closed-loop planning with in-hand pen pose estimation, force control, and explicit error detection and recovery; repeats until strokes are successfully drawn.
- **What to take:** (i) the error-detection-and-recovery loop is a capability our RL agent gets *implicitly* — that is a genuine selling point we should measure explicitly (e.g. inject a pen-slip disturbance and show the RL policy recovers while an open-loop IK plan does not); (ii) a rigorous, quantified classical baseline to cite.
- **Class:** Directly related (baseline).

### D11 — SketcherX: AI-Driven Interactive Robotic Drawing with Diffusion Model and Vectorization 🟦
- **Authors:** Jookyung Song, Mookyoung Kang, Nojun Kwak (Seoul National University)
- **Year / venue:** 2024 · arXiv:2409.15292
- **Link:** https://arxiv.org/abs/2409.15292 · [local PDF](02_Directly_Related/D11_SketcherX_Song2024.pdf)
- **Relevance:** A complete, recent, *deployed* robotic drawing system (portraits, human-like style, interactive) that deliberately does **not** use RL — useful as a systems contrast and to keep our related work current.
- **Technique:** Two-agent architecture: a face-processing/vectorization agent and a drawing agent; fine-tuned diffusion (LoRA) for stylisation; vectorised strokes executed by the arm; optimised for speed.
- **What to take:** modern stylisation and vectorisation as a preprocessing front-end (target-image → stroke set), which could feed our RL agent richer targets than analytic shapes; also a sober reminder that for *pure image reproduction*, non-RL pipelines are extremely strong — reinforcing that our novelty must be the **learning/feedback** claim, not the drawing quality.
- **Class:** Directly related.

---

# 03_Advanced_Methods

Beyond current scope — the source of extensions, and of the "future work" section.

### A01 — FRIDA: A Collaborative Robot Painter with a Differentiable, Real2Sim2Real Planning Environment 🟪 ★ #3
- **Authors:** Peter Schaldenbrand, James McCann, Jean Oh (Carnegie Mellon University)
- **Year / venue:** 2022/2023 · **ICRA 2023** (Finalist, Best Paper in Deployed Systems) · arXiv:2210.00664
- **Link:** https://arxiv.org/abs/2210.00664 · [local PDF](03_Advanced_Methods/A01_FRIDA_Schaldenbrand_ICRA2023.pdf)
- **Relevance:** The strongest deployed drawing/painting robot with a genuine closed visual loop, and — most importantly for us — the clearest published treatment of **making the simulator match the real robot's marks**.
- **Technique:** A **fully differentiable painting simulator**; **real2sim2real** — the robot makes real strokes, they are photographed, and the simulator's stroke model is *fitted to the robot's actual marks*; planning by gradient descent through the differentiable simulator against a CLIP/text or image objective; continual re-planning from photographs of the real canvas.
- **What to take:** **This is the highest-value single technique in the entire library for us.** Our sim-to-real risk is concentrated in the ink model and the camera model, both currently hand-set constants (`pen_radius_px`, `cam_px=150`, `>60` threshold). FRIDA's real2sim2real says: *measure* them from real strokes and *fit* the simulator, instead of guessing. Also: gradient-based planning through a differentiable renderer is a strong non-RL baseline we should be aware of.
- **Class:** Advanced.

### A02 — CoFRIDA: Self-Supervised Fine-Tuning for Human-Robot Co-Painting 🟪
- **Authors:** Peter Schaldenbrand, Gaurav Parmar, Jun-Yan Zhu, James McCann, Jean Oh (CMU)
- **Year / venue:** 2024 · **ICRA 2024** (Best Paper on HRI) · arXiv:2402.13442
- **Link:** https://arxiv.org/abs/2402.13442 · [local PDF](03_Advanced_Methods/A02_CoFRIDA_Schaldenbrand_ICRA2024.pdf)
- **Relevance:** Where the field is heading — interaction and self-supervision. Also a masterclass in generating training data without human labels.
- **Technique:** Self-supervised fine-tuning of an image-generation model to produce *drawable* continuations of a partially-drawn canvas; co-painting with a human collaborator.
- **What to take:** the self-supervised data-generation trick (construct (partial canvas → completion) pairs automatically) maps neatly onto generating training targets for our agent for free; and "drawability-aware generation" is a good future-work direction.
- **Class:** Advanced.

### A03 — CLIPasso: Semantically-Aware Object Sketching 🟪
- **Authors:** Yael Vinker, Ehsan Pajouheshgar, Jessica Y. Bo, Roman Christian Bachmann, Amit Haim Bermano, Daniel Cohen-Or, Amir Zamir, Ariel Shamir
- **Year / venue:** 2022 · **SIGGRAPH 2022 / ACM TOG 41(4)** (Best Paper) · arXiv:2202.05822
- **Link:** https://arxiv.org/abs/2202.05822 · [local PDF](03_Advanced_Methods/A03_CLIPasso_Vinker_SIGGRAPH2022.pdf)
- **Relevance:** The definitive demonstration that optimising a **perceptual/semantic loss** produces far better sketches than optimising pixel overlap — a direct intellectual challenge to IoU as RoboSketch-RL's objective.
- **Technique:** Represent a sketch as a set of Bézier curves; optimise control points **directly by gradient descent** through a **differentiable rasteriser** (DiffVG) against a **CLIP-based perceptual loss**; abstraction controlled by the number of strokes.
- **What to take:** (i) a serious critique to answer: for geometric shapes IoU is defensible, but the moment we reach letters, IoU rewards *ink overlap* rather than *legibility* — we should add a recognisability metric (e.g. a digit classifier's confidence) alongside IoU; (ii) the differentiable-rasteriser + gradient-descent approach is a strong non-RL baseline; (iii) stroke-count as an explicit abstraction knob.
- **Class:** Advanced.

### A04 — Diffusion Policy: Visuomotor Policy Learning via Action Diffusion 🟪
- **Authors:** Cheng Chi, Zhenjia Xu, Siyuan Feng, Eric Cousineau, Yilun Du, Benjamin Burchfiel, Russ Tedrake, Shuran Song (Columbia / TRI / MIT)
- **Year / venue:** 2023 · **RSS 2023**; extended in **IJRR 44(10–11)** · arXiv:2303.04137
- **Link:** https://arxiv.org/abs/2303.04137 · [local PDF](03_Advanced_Methods/A04_DiffusionPolicy_Chi_RSS2023.pdf)
- **Relevance:** The current dominant visuomotor policy class. Two specific reasons it matters here: drawing is **strongly multimodal** (there are many equally good stroke orders for a square), and diffusion policies handle multimodality where a unimodal Gaussian PPO policy averages the modes and produces mush.
- **Technique:** Represent the policy as a conditional **denoising diffusion** process over *action sequences* (action chunks), with receding-horizon execution and visual conditioning; trained by behaviour cloning.
- **What to take:** (i) **action chunking / receding horizon** — predicting a short sequence of pen moves instead of one `(dx, dy)` per step is a cheap, high-value change that would smooth our strokes far better than the ad-hoc `smooth_penalty`; (ii) the multimodality argument, which explains observed failure modes; (iii) a credible "modern method" comparison arm for the paper.
- **Class:** Advanced.

### A05 — Stroke-based Rendering: From Heuristics to Deep Learning 🟪
- **Authors:** Florian Nolte, Andrew Melnik, Helge Ritter (Bielefeld University)
- **Year / venue:** 2022 · arXiv:2302.00595 (survey)
- **Link:** https://arxiv.org/abs/2302.00595 · [local PDF](03_Advanced_Methods/A05_StrokeBasedRendering_Survey_Nolte2022.pdf)
- **Relevance:** The map of the entire field our project sits inside — rule-based heuristics, stroke optimisation, differentiable vector graphics, RL agents, transformers, and robotic applications.
- **Technique:** Survey / taxonomy.
- **What to take:** read this **before** writing related work; it will tell us which lineage to claim, which comparisons reviewers will expect, and which of our "novel" ideas already have names.
- **Class:** Advanced (survey).

### A06 — Robot Synesthesia: A Sound and Emotion Guided AI Painter 🟪
- **Authors:** Vihaan Misra, Peter Schaldenbrand, Jean Oh (CMU)
- **Year / venue:** 2023 · arXiv:2302.04850
- **Link:** https://arxiv.org/abs/2302.04850 · [local PDF](03_Advanced_Methods/A06_RobotSynesthesia_Misra2023.pdf)
- **Relevance:** Evidence that in the drawing-robot field the **objective function** — not the controller — is where the novelty currently lies. Supports our decision to make the *reward source* the contribution.
- **Technique:** Multimodal (audio/emotion) guidance signals converted into a painting objective, executed on the FRIDA platform.
- **What to take:** the framing "the contribution is a new objective/reward channel for a drawing robot" is a published, accepted framing at good venues — this de-risks our H2 positioning.
- **Class:** Advanced.

### A07 — Sketch-to-Skill: Bootstrapping Robot Learning with Human Drawn Trajectory Sketches 🟪
- **Authors:** Peihong Yu, Amisha Bhaskar, Anukriti Singh, Zahiruddin Mahammad, Pratap Tokekar (University of Maryland)
- **Year / venue:** 2025 · arXiv:2503.11918
- **Link:** https://arxiv.org/abs/2503.11918 · [local PDF](03_Advanced_Methods/A07_SketchToSkill_Yu2025.pdf)
- **Relevance:** The inverse of our problem (drawing as *input* to robot learning), but the machinery — turning a 2-D drawing into a 3-D trajectory prior, then BC + RL refinement — is directly reusable for warm-starting our agent from the target shape.
- **Technique:** Sketch→3-D trajectory generator; BC pre-training on generated trajectories; RL refinement with guided exploration.
- **What to take:** the three-stage "generate prior → clone → refine with RL" recipe, which is almost certainly a faster path to letters than pure PPO exploration.
- **Class:** Advanced.

### A08 — L2D2: Robot Learning from 2D Drawings 🟪
- **Authors:** (Virginia Tech / collaborators) · see PDF
- **Year / venue:** 2025 · arXiv:2505.12072
- **Link:** https://arxiv.org/abs/2505.12072 · [local PDF](03_Advanced_Methods/A08_L2D2_RobotLearningFrom2DDrawings_2025.pdf)
- **Relevance:** Very recent work using 2-D drawings as a robot-supervision modality; keeps the related-work section current and shows the 2-D-drawing↔robot-trajectory mapping problem is live in 2025.
- **Technique:** Learning robot manipulation policies from human 2-D drawings, handling the 2-D→3-D ambiguity.
- **What to take:** the 2-D↔3-D correspondence treatment, which will matter when we move from a flat paper plane to any non-planar surface.
- **Class:** Advanced.

### A09 — Feedback-guided Stroke Placement for a Painting Machine 🟪
- **Authors:** O. Deussen, T. Lindemeier, S. Pirk, M. Tautzenberger (University of Konstanz)
- **Year / venue:** 2012 · **Computational Aesthetics in Graphics, Visualization, and Imaging 2012** (CAe '12, Annecy; Eurographics Association; pp. 25–33; doi:10.2312/COMPAESTH/COMPAESTH12/025-033)
- **Link:** https://graphics.uni-konstanz.de/publikationen/Deussen2012FeedbackguidedStroke/index.html (no local PDF; metadata copied verbatim from the publisher-group page's BibTeX on 2026-11-08; **abstract only read** ◇)
- **Relevance:** The e-David painting robot (Univ. Konstanz) — prior art for a closed optical-feedback loop in robot painting. Abstract: "painterly rendering techniques that work within a visual feedback loop of eDavid, our painting robot."
- **Technique:** Camera photographs the canvas; new strokes are placed from the difference to the target (predefined stroke candidates vs. line-integral-convolution strokes).
- **What to take:** cite it so we never imply closed-loop visual feedback for drawing is new. Feedback is used for planning, not as a learning signal.
- **Class:** Advanced (prior art).

---

# 04_Robotics_and_Vision

Everything needed to make Phase D (physical robot) work rather than fail.

### V01 — Domain Randomization for Transferring Deep Neural Networks from Simulation to the Real World 🟩
- **Authors:** Josh Tobin, Rachel Fong, Alex Ray, Jonas Schneider, Wojciech Zaremba, Pieter Abbeel (OpenAI / UC Berkeley)
- **Year / venue:** 2017 · **IROS 2017** · arXiv:1703.06907
- **Link:** https://arxiv.org/abs/1703.06907 · [local PDF](04_Robotics_and_Vision/V01_DomainRandomization_Tobin_IROS2017.pdf)
- **Relevance:** Our vision reward is computed from a **simulated** camera with fixed, hand-chosen parameters. On real hardware the lighting, paper colour, shadows, pen contrast and camera pose will all differ. This paper is the canonical fix.
- **Technique:** Randomise simulator *visual* parameters (textures, lighting, camera pose, noise, distractors) so widely that the real world looks like just another sample from the training distribution.
- **What to take:** a concrete randomisation list to add to `_perceive()` and to the virtual camera: camera pose jitter, lighting/exposure, paper texture and colour, ink contrast, blur, sensor noise, perspective warp, threshold jitter. This converts our currently-fragile fixed camera model into a robustly transferable one — and it is a cheap, high-value experiment (H4: *does visual domain randomization preserve vision-reward learning while surviving real-camera conditions?*).
- **Class:** Foundational for sim-to-real.

### V02 — Sim-to-Real Transfer of Robotic Control with Dynamics Randomization 🟩
- **Authors:** Xue Bin Peng, Marcin Andrychowicz, Wojciech Zaremba, Pieter Abbeel
- **Year / venue:** 2017/2018 · **ICRA 2018** · arXiv:1710.06537
- **Link:** https://arxiv.org/abs/1710.06537 · [local PDF](04_Robotics_and_Vision/V02_DynamicsRandomization_Peng_ICRA2018.pdf)
- **Relevance:** The simulator uses a **KUKA iiwa**; the planned hardware is a ~₹10,000 arm with MG996R hobby servos — enormous differences in backlash, compliance, tracking lag and repeatability. Dynamics randomization is the standard mitigation.
- **Technique:** Randomise physical parameters (masses, friction, damping, actuator gains, latency) during training; use a recurrent policy so it can implicitly identify the dynamics it is in.
- **What to take:** (i) randomise `force`, `maxVelocity`, joint damping and **control latency** in `_move_arm()`; (ii) the recurrent-policy trick for implicit system identification; (iii) the argument that our current pen-space action abstraction *already* buys much of this robustness — worth measuring and claiming.
- **Class:** Foundational for sim-to-real.

### V03 — Sim-to-Real Transfer in Deep Reinforcement Learning for Robotics: a Survey 🟩
- **Authors:** Wenshuai Zhao, Jorge Peña Queralta, Tomi Westerlund (University of Turku)
- **Year / venue:** 2020 · **IEEE SSCI 2020**, pp. 737–744 · arXiv:2009.13303
- **Link:** https://arxiv.org/abs/2009.13303 · [local PDF](04_Robotics_and_Vision/V03_SimToRealSurvey_Zhao_SSCI2020.pdf)
- **Relevance:** A short, structured tour of every transfer technique (domain randomization, domain adaptation, system identification, meta-learning, knowledge distillation) with their trade-offs.
- **Technique:** Survey.
- **What to take:** use it to *choose* a transfer strategy deliberately and justify it in the paper, rather than defaulting to "we randomised some things"; it also supplies the citation scaffolding for the Phase D section.
- **Class:** Foundational for sim-to-real.

---

# 05_Reinforcement_Learning

RL methodology — especially **where rewards come from**, which is this project's core claim.

### R01 — Unsupervised Perceptual Rewards for Imitation Learning 🟩
- **Authors:** Pierre Sermanet, Kelvin Xu, Sergey Levine (Google Brain)
- **Year / venue:** 2017 · **RSS 2017** · arXiv:1612.06699
- **Link:** https://arxiv.org/abs/1612.06699 · [local PDF](05_Reinforcement_Learning/R01_UnsupervisedPerceptualRewards_Sermanet2017.pdf)
- **Relevance:** The conceptual ancestor of our vision reward: derive a **dense reward directly from raw visual observation**, with no instrumentation and no ground-truth state — precisely the situation our physical robot will be in.
- **Technique:** Discover sub-goals from a few unlabelled demonstration videos using pretrained deep visual features, then build a dense perceptual reward from feature-space progress, and learn the task with real-robot RL.
- **What to take:** (i) the argument structure "ground-truth reward is unavailable on real hardware, therefore perceptual reward" — this is exactly our H2 argument and should be cited as prior art; (ii) the technique for shapes with **no analytic target mask** (photographs, freehand drawings), where our IoU-against-a-known-mask reward does not exist.
- **Class:** Foundational for the reward claim.

### R02 — End-to-End Robotic Reinforcement Learning without Reward Engineering 🟩
- **Authors:** Avi Singh, Larry Yang, Kristian Hartikainen, Chelsea Finn, Sergey Levine (UC Berkeley)
- **Year / venue:** 2019 · **RSS 2019** · arXiv:1904.07854
- **Link:** https://arxiv.org/abs/1904.07854 · [local PDF](05_Reinforcement_Learning/R02_RLWithoutRewardEngineering_Singh_RSS2019.pdf)
- **Relevance:** **The most important paper in the library for positioning our novelty.** It makes the case that manual reward engineering (instrumented setups, hand-designed perception) is the real barrier to robot RL, and learns rewards from *pixels* plus a handful of goal images.
- **Technique:** Learn a reward classifier over raw image observations from user-provided goal examples; use active queries to fix the classifier's exploitation failures (VICE-RAQ); train end-to-end on a real robot.
- **What to take:** (i) a sharper, more honest framing of H2 — our claim is not "vision rewards are new" (they are not), it is **"for the drawing task, a purely perceptual reward loses only ~0.04 IoU versus privileged ground truth"**, which is a *quantified equivalence result*, and that is a legitimate contribution; (ii) their reward-exploitation failure analysis is a threat we should test for explicitly (can our agent fool the camera reward — e.g. by exploiting thresholding to appear to cover the target?); (iii) their evaluation protocol.
- **Class:** Foundational for the reward claim.

### R03 — How to Train Your Robot with Deep RL: Lessons We've Learned 🟩
- **Authors:** Julian Ibarz, Jie Tan, Chelsea Finn, Mrinal Kalakrishnan, Peter Pastor, Sergey Levine (Google Brain)
- **Year / venue:** 2021 · **IJRR (International Journal of Robotics Research)**, Feb 2021 · arXiv:2102.02915
- **Link:** https://arxiv.org/abs/2102.02915 · [local PDF](05_Reinforcement_Learning/R03_HowToTrainYourRobot_Ibarz_IJRR2021.pdf)
- **Relevance:** A candid account of what actually goes wrong in real robot RL — reward specification, resets, safety, sample efficiency, evaluation and reproducibility. This will improve our experimental section more than any algorithmic paper.
- **Technique:** Position/retrospective paper with case studies.
- **What to take:** (i) the **evaluation protocol** standards (multiple seeds, report variance, define success rate precisely, evaluate on held-out conditions) — directly relevant to the multi-seed sweep already in progress; (ii) the automatic-reset problem, which we get for free in sim but must solve on hardware (paper feeding, pen re-inking); (iii) the reproducibility checklist.
- **Class:** Foundational (methodology).

### R04 — Curriculum Learning for Reinforcement Learning Domains: A Framework and Survey 🟩
- **Authors:** Sanmit Narvekar, Bei Peng, Matteo Leonetti, Jivko Sinapov, Matthew E. Taylor, Peter Stone
- **Year / venue:** 2020 · **JMLR 21(181):1–50** · arXiv:2003.04960
- **Link:** https://arxiv.org/abs/2003.04960 · [local PDF](05_Reinforcement_Learning/R04_CurriculumLearning_Survey_Narvekar_JMLR2020.pdf)
- **Relevance:** RoboSketch-RL's task ladder (line → circle → square → triangle → digits → letters) is an unexamined **hand-designed curriculum**. This survey turns that from an informal plan into a measurable research contribution.
- **Technique:** Framework + survey covering task generation, task sequencing and knowledge transfer, with standard evaluation metrics.
- **What to take:** (i) the metrics **jump-start**, **time-to-threshold** and **asymptotic performance** — these let us *quantify* whether our shape ladder helps at all (a real experiment: train triangle from scratch vs. from a line-pretrained policy); (ii) automatic curriculum methods as a path to a stronger novelty claim than a fixed hand-ordered ladder.
- **Class:** Foundational (methodology).

### R05 — Gymnasium: A Standard Interface for Reinforcement Learning Environments 🟩
- **Authors:** Mark Towers, Ariel Kwiatkowski, Jordan Terry, John U. Balis, Gianluca De Cola, Tristan Deleu, Manuel Goulão, Andreas Kallinteris, Markus Krimmel, Arjun KG, Rodrigo Perez-Vicente, Andrea Pierré, Sander Schulhoff, Jun Jet Tai, Hannah Tan, Omar G. Younis
- **Year / venue:** 2024 · **NeurIPS Datasets & Benchmarks 2025** · arXiv:2407.17032
- **Link:** https://arxiv.org/abs/2407.17032 · [local PDF](05_Reinforcement_Learning/R05_Gymnasium_Towers2024.pdf)
- **Relevance:** The API [`rl/draw_env.py`](../rl/draw_env.py) implements. This is the correct citation for our environment, and the reference for the conventions (`terminated` vs `truncated`, seeding, wrappers, vectorisation) we must follow if we want the environment released as a reusable benchmark.
- **Technique:** Standardised RL environment API.
- **What to take:** conformance details that matter if we release `DrawEnv` as a **benchmark environment** — which is itself a citable contribution (a "RoboSketchBench" of drawing tasks would be a genuinely useful community artefact).
- **Class:** Foundational (tooling).

> **Also cite (tooling, no PDF needed):** Raffin et al., *Stable-Baselines3: Reliable Reinforcement Learning Implementations*, **JMLR 22(268):1–8, 2021** — the PPO/SAC implementation actually used. https://jmlr.org/papers/v22/20-1364.html

---

## Coverage against the requested topics

| Requested topic | Covered by |
|---|---|
| Vision-guided robotic drawing | D01, D02, D03, D04, D10, D11, A01, A02 |
| RL for robotic manipulation | F01, F02, F03, F04, F05, R03, A04 |
| Autonomous robotic drawing | D01, D03, D04, D10, D11, A01, A06 |
| Camera/vision-based feedback control | A01, D10, D04, V01, R01, R02 |
| Learning-based trajectory generation | F06, D03, D05, D06, D07, A04, A07, A08 |
| Reward/error calculation from visual feedback | **R01, R02**, D02 (discriminator reward), D05, A03 (CLIP loss), A06 |
| Sim-to-real robotics | **V01, V02, V03**, D08, A01 (real2sim2real) |
| Advanced methods to improve the project | A01–A08, F04 (HER), R04 (curriculum), D02 (neural renderer) |

## Deliberate exclusions

Recorded so the search is reproducible and its boundaries defensible:

- **Paywalled-only work** (e.g. *Application of Deep RL in Control of Drawing Robots* (DDPG trajectory tracking); several Elsevier/Springer robot-calligraphy papers; *e-David* MDPI/Springer entries). Their *ideas* are discussed in the comparative analysis; the PDFs are not redistributable here. e-David (Deussen et al., Univ. Konstanz) is nonetheless the historical origin of the optical-feedback painting loop and **must be cited** — see https://edavid.de.
- **Vision-language-action / foundation-model policies** (RT-2, OpenVLA, SmolVLA): far beyond a ₹10,000 arm's compute and data budget; noted as future work only.
- **General grasping / assembly RL**: adjacent but not informative for a planar, quasi-static, contact-light drawing task.
