# RoboSketch-RL

**Vision-Guided Reinforcement Learning for Autonomous Robotic Drawing.**

A robotic arm that *learns to draw* through trial and error, guided by what it
sees — not by pre-programmed trajectories. The agent moves a pen, looks at the
result through a camera, and improves from a reward based on how well its
drawing matches a target. Built simulation-first (PyBullet), aimed at
sim-to-real transfer onto low-cost hardware.

> **Research goal:** a publishable contribution (target venues: IEEE / ICRA /
> IROS / RA-L / CoRL), not just a working robot. The novelty is teaching the
> robot *how to learn to draw* rather than programming *how to draw*.

---

## Current status

| Phase | State |
|---|---|
| **B — Simulator** | ✅ complete (B1–B6): arm + IK (0.1 mm), pen inks paper, virtual camera + OpenCV read it back (IoU ~0.88) |
| **C — Reinforcement learning** | ✅ Gym env + PPO trains all four shapes; **H2 (vision reward) demonstrated** |
| Multi-seed confirmation | ✅ complete (24 runs, n=3 per cell) |
| Real-camera-in-the-loop | ✅ validated (proxy vs real render: mean IoU gap 0.010) |
| H3 — reward exploitation | ✅ tested, none found |
| O1 — remaining-time channel | ✅ ablated (+0.039 IoU, 9/12 pairs; modest, default off) |
| Overshoot (agents overrun their own drawing) | ✅ measured; remedy unclear — a plateau stop gives +0.055 IoU (7/8), but a plain 50-step episode is statistically indistinguishable from it (+0.016, t=+0.63), so the gain is mostly a shorter horizon |
| Does the overshoot bias H2? | ✅ tested at n=12 — **no** (moves the gap by 0.011, inside its standard error) |
| Camera realism (domain randomisation) | ✅ tested — **not the bottleneck.** A camera that loses more than half the ink costs the policy 0.014 IoU |
| H4 — does a camera see what kinematics cannot? | ✅ two designs (240 and 60 steps), 64 runs — **null both times.** Camera recovers no better than kinematics (|t| ≤ 1.19, crit 2.37), and neither does an arm with a *perfect* view of the paper. D01's objection is still unanswered. A third design (H4 v3) shows the loss is an observation problem: with the pen drawn on the sheet, paper-shift loss falls 0.14 → 0.02 for camera *and* privileged arms alike — but the offset is given by the simulator, so this does **not** show a camera helps. H4 v4 then lets the camera *estimate* the offset from the photo: paper-shift loss +0.070 vs kinematics +0.147 (diff-in-diff +0.077, 8/8, t=+6.39), but still worse than with the true offset (+0.019). **Replicated on fresh seeds 200/300** (pre-registered): kinematics loses 0.165, camera-estimate 0.046 (+0.119, 8/8, t=+8.32), with no clean head start (+0.006); slightly below the true-offset arm, and the estimator costs some robustness to ink failure and slip vs a plain camera arm. Simulation only. See below. |
| H5 — does open-loop error grow with the plan? | ✅ yes — open-loop deviation grows (linearly under a constant bias, ~√steps under jitter), a same-plan closed-loop controller stays flat (n = 80 pairs, all |t| ≥ 8). **Shows feedback matters, not that a camera does** — the controller reads the true pen position, as joint encoders would |
| Does the agent draw, or memorise four pictures? (proposal 5.4) | ✅ tested (n = 8 cells) — **partly memorised.** An agent trained on one fixed picture loses 0.146 IoU already on slightly resized/rotated versions of it, and falls to 0.074 on held-out sizes/rotations; training on a size/rotation family helps (0.118, +0.044, 8/8, t = +7.35) but does **not** fix it — both arms lose most of their home score. **Follow-up (n = 8):** 3× more training (600k) does not close the gap (held-out +0.013, t = +0.95), and size alone and rotation alone each already cost IoU (+0.132, +0.100), neither clearly worse |
| PPO vs SAC, sim-to-real | ⏳ next |

### Headline result (H2 — the project's novelty)

An agent rewarded **only from a noisy camera perception** learns to draw about
as accurately as one with perfect ground-truth knowledge — the premise the real
robot depends on (on hardware, ground truth doesn't exist).

Multi-seed, 4 shapes × 3 seeds × 200k steps, true IoU (mean ± sample std across
all 12 runs per condition — this pools shape-to-shape variation with seed noise;
the per-shape seed spreads are 0.010–0.082):

| Reward source | Mean true IoU |
|---|---|
| Ground truth | **0.382 ± 0.054** |
| Camera (vision) | **0.354 ± 0.066** |

Compared **paired within shape and seed** (the same test used for the O1
ablation), vision is 0.028 IoU behind ground truth: sd 0.068, t = −1.43 on
11 df, with vision ahead in 5 of 12 paired runs. That does not reach
significance at n=3 seeds, so the honest claim is that the two are **not
distinguishable at this sample size** — not that they are equal.

**Independent re-run (2026-10-31), seeds 100/200/300** (the sweep above used adjacent seeds 0,1,2 that share env streams),
same protocol, 12 paired cells: truth 0.388 vs camera 0.384, difference +0.004 (sd 0.055, 6/12 cells), t = +0.27.
Equivalence test (TOST, margin ±0.05 IoU fixed before the run): 90% CI of the difference [−0.024, +0.033], p = 0.008 →
**equivalent within ±0.05 IoU in simulation** (same on peak IoU). Shape-dependent (square favours truth, +0.055, n=3 per shape;
not tested per shape). Fixed camera, fixed shapes, simulation only.

The effect is shape-dependent: vision is better on the circle (+0.042); ground
truth on the triangle (−0.091), the line (−0.021) and the square (−0.042).

Don't read the error bars too hard: at n=3 the overlap test is not robust. Using
the sample std (n−1) all four shapes overlap; using the population std (n) the
line and triangle come out disjoint. The verdict flips on the choice of
denominator, which is exactly why the paired test above — which does not — is
the one the conclusion rests on.

**A second, independent 24-run sweep** (`results/h2_peak*.jsonl`) puts the gap at
**+0.013** (t = +0.57, vision ahead in 8 of 12 pairs) — the opposite sign, also
not significant. Two sweeps disagreeing on *which arm is better*, neither
reaching significance, is a stronger statement of "indistinguishable" than
either alone: the difference is not a stable quantity at n=3 seeds. Seed noise
dominates it — the circle alone swings from −0.127 to +0.159 across seeds.

**The open question (H4).** D01 (Lee et al., ICRA 2022) draws well with no camera and
argues camera-free is better. H4 trains four arms — an open-loop analytic tracer, a
privileged arm that sees the real ink, an FK arm that sees only what its kinematics
predict, and a camera arm — against pen slip, paper shift and ink failure, scoring all of
them on true IoU.

The pre-registered test came back **null**: camera − fk recovery is −0.012 / +0.005 / +0.010
across the three disturbances, all far from significance at n = 8. A ceiling control added
afterwards explains the null rather than excusing it — the **privileged** arm, which sees the
real paper perfectly, also recovers no better than the FK arm (−0.018 / −0.005 / +0.017).
The "what have I drawn so far" channel carries no recoverable signal here for *any* arm, so
there was nothing for a camera to win with.

What is large is the gap to open-loop: a rigid analytic trace loses 0.28–0.31 IoU to slip and
paper shift where every trained arm loses 0.005–0.054. That comparison confounds "sees the
paper" with "was trained at all", so it shows classical traces are fragile, not that vision
helps. **D01's objection stands unanswered**; what has changed is that the reason this design
could not answer it is now measured. Full write-up and the leading explanation
(robustness-by-overdrawing, stated as a hypothesis) are in `docs/RESEARCH_LOG.md`.

A second design cut the episode from 240 to 60 steps to remove the long blind window in
which agents can re-cover damage. It is **null again** (camera − fk recovery −0.005 / +0.011
/ −0.008, |t| ≤ 0.79). It did show the window was doing work: paper-shift loss for trained
arms rose 2.2x to 2.8x. Even the privileged arm loses 0.129 to a paper shift. A follow-up
oracle (an arm that *knows* the shift) loses only 0.013, so the loss is **not** unrecoverable:
roughly 0.11 IoU of headroom exists that no trained arm uses. The likely cause is an
observation we chose — the pen marker is drawn in world coordinates, so the camera arm is never
shown where the pen is *on the paper* — which is untested. The disturbance schedule also scales
with episode length, so this is not a pure horizon test.

![H4](output/h4_disturbance_recovery.png)
![H4-short](output/h4_short_disturbance_recovery.png)
![H4 v3](output/h4_v3_disturbance_recovery.png)
![H4 v4](output/h4_v4_disturbance_recovery.png)

**Generalisation (proposal 5.4).** Fixed-target vs size/rotation-randomised training, scored on default, train-range and held-out targets.

![Generalisation](output/gen_generalisation.png)

Follow-up (Stage 4, O2): giving the agent a pen-centred 64-px window instead of the whole sheet raised held-out IoU from 0.118 to 0.298
(+0.181, 8/8 pairs, t=+7.00) and cut the train-to-held-out loss from 0.174 to 0.042. A control with the same pixel density but no pen-centring
(whole sheet at 128 px) gained only +0.020 held-out (t=+2.03, not significant), so the gain comes from the pen-centred view, not zoom
alone. The gain survives perception: with the agent seeing only a photo (held-out camera), held-out IoU rises 0.130 -> 0.273 (+0.143, t=+3.54), though the line shape does worse with the ego view. A CoordConv control (x/y coordinate planes added to the global view) did not close the gap (held-out +0.008, t=+0.97). Caveats: 8 cells, simulated camera, pen position assumed known, simulation only.

**Supporting result (domain randomisation).** The H2 camera was a fixed, optimistic
one, so the obvious objection is that the result describes a sensor rather than
drawing. Re-running with the camera sampled per episode — and placed in the
agent's *observation* as well as its reward, which is the real robot's situation
— the camera arms (0.393 / 0.371) sit level with a privileged ground-truth arm
(0.389). A deliberately bad held-out camera, which recovers only 0.394 of a
perfect drawing's ink against 0.834 for the fixed one, costs **0.014 IoU**.
Randomising during training changes nothing (paired −0.011, t = −0.67).
Perception realism is not where the difficulty lives.

**Supporting result (H3):** across 3328 training episodes the agent's *perceived*
IoU shows no exploitable drift away from its *true* IoU — mean gap −0.0001,
correlation 0.997–0.999, and no single episode's gap exceeds 0.029 either way.
Note the mean is a *cancellation*: within a shape the sign is consistent (the
line's gap is negative in 86% of episodes, the square's positive in 84%), and
the square's gap grows over training (+0.003 → +0.008). That is a real
per-shape signal, far below the 0.02 bar for exploitation but worth re-checking
once the camera is domain-randomised.

Figures: [`output/results_h2_seeds.png`](output/results_h2_seeds.png) (truth vs
vision with error bars), [`output/results_h3.png`](output/results_h3.png)
(exploitation gap), [`output/results_montage.png`](output/results_montage.png)
(all four shapes).

> **Known measurement caveat (23 Aug).** Every IoU above is the value at the
> *end* of the episode. Agents actually trace their shape in the first ~15% of
> the episode and then overshoot it, losing a mean 0.064 IoU — more than the
> truth-vs-vision gap itself. See [`output/results_overrun.png`](output/results_overrun.png)
> and `rl/overrun.py`. It is largely fixable: ending each episode once the
> drawing stops improving (`plateau_patience=20`) raises IoU by 0.055 in 7 of 8
> paired runs while cutting the overshoot from 0.034 to 0.009 — and finishes in
> 50 steps instead of 240. See [`output/results_overshoot.png`](output/results_overshoot.png).
> **Correction (2026-11-04):** a 4th arm with a plain 50-step horizon and no plateau stop (`rl/short_arm.py`)
> is not distinguishable from the plateau stop (+0.016, t=+0.63, n=8) and recovers ~71% of its gain, so
> "largely fixable by a plateau stop" is too strong: shorter episodes help; adaptive stopping is not shown to add anything.
>
> **It does not bias the H2 comparison** — tested by re-running the whole sweep
> with peak IoU logged (24 runs, `rl/h2_peak_analysis.py`). Scoring at the peak
> instead of the end moves the gap by 0.011, inside its own standard error, and
> the two arms lose statistically indistinguishable amounts to it (truth 0.033,
> camera 0.022). So the overshoot is a quality-and-efficiency problem, not a
> correction to the headline result.

---

## Repository layout

```
sim/                    Phase B — the simulator (run these to see it)
  01_manual_control.py    move the arm's 7 joints by hand
  02_ik_reach.py          move the pen by (x, y) via inverse kinematics
  03_draw_line.py         the arm draws a line / square, saves the image
  04_camera_capture.py    arm draws, then a virtual camera + OpenCV score it
  05_interactive_draw.py  draw it yourself with the pen
  viewer.py               shared window helpers
rl/                     Phase C — reinforcement learning
  targets.py              target shapes (line, circle, square, triangle)
  metrics.py              IoU / MSE / coverage / precision / chamfer / SNR / path ratio
  draw_env.py             the Gymnasium environment (the heart of the project)
  camera.py               a real PyBullet camera render, for the vision_real reward
  train.py                train one PPO agent (truth or vision reward)
  experiment.py           multi-seed truth-vs-vision sweep (resumable)
  h3_exploitation.py      H3 - is the camera reward being gamed? (answer: no)
  overrun.py              measures the overshoot: agents finish early, then idle
  o1_ablation.py          O1 - does remaining-time in the observation help?
  overshoot_ablation.py   can the agent be taught to stop? (baseline/plateau/stop)
  watch.py                WATCH a trained agent draw, live (2D + 3D arm)
assets/paper_quad.obj   the paper (a UV-mapped mesh)
models/                 trained PPO agents (.zip)
output/                 all drawings, camera captures, and figures
results/                experiment results (JSONL)
docs/
  RESEARCH_LOG.md         complete dated lab notebook (every decision + why)
  dashboard.html          visual project overview
  learning-book/          beginner's book on the concepts
  presentation/           progress-review slide deck
watch.bat               double-click shortcut: run + watch the simulation
environment.yml         reproducible conda environment
```

---

## Setup

PyBullet has no Windows pip wheel, so the environment is built with **conda**
(prebuilt binaries, no C++ compiler needed):

```bash
conda env create -f environment.yml
conda activate robosketch
```

Stack: Python 3.10, PyBullet, Gymnasium, Stable-Baselines3 (PyTorch), OpenCV.

---

## Quick start

Everything runs through the `robosketch` environment:

```bash
# --- WATCH a trained agent draw (the fastest way to see the project work) ---
# on Windows just double-click watch.bat, or from a shell:
python rl/watch.py                                        # line, ground-truth agent
python rl/watch.py --shape circle --reward-mode vision     # the H2 camera-reward agent
python rl/watch.py --shape all --view both                 # all four + the 3D KUKA arm
python rl/watch.py --shape square --random                 # the untrained "before"
python rl/watch.py --list                                  # which agents exist
# keys in the window: SPACE pause, R restart, N next, S snapshot, +/- speed, Q quit
# --save writes an mp4 plus the final and peak-IoU drawings into output/watch/

# --- see the simulator (opens a 3D window) ---
python sim/05_interactive_draw.py            # draw with the pen yourself
python sim/04_camera_capture.py square       # arm draws, camera scores it

# --- train an agent to draw ---
python rl/train.py --shape circle --timesteps 400000               # ground-truth reward
python rl/train.py --shape circle --timesteps 400000 --reward-mode vision   # camera reward (H2)

# --- the multi-seed H2 experiment (resumable) ---
python rl/experiment.py --seeds 0 1 2 --timesteps 200000
python rl/experiment.py --aggregate          # table + error-bar figure

# --- H3: is the camera reward being exploited? ---
python rl/h3_exploitation.py --all-shapes --timesteps 200000
python rl/h3_exploitation.py --plot

# --- the overshoot: where the reported IoU actually goes ---
python rl/overrun.py                         # needs the trained models

# --- ablations (both resumable, both write their own results file) ---
python rl/o1_ablation.py --seeds 0 1 2 --timesteps 200000
python rl/overshoot_ablation.py --seeds 0 1 --timesteps 200000
```

Trained drawings appear in `output/trained_<shape>_*.png`; models in `models/`.

---

## How it works

```
target shape ─► RL agent ─► move the pen (dx, dy)
                               │  (inverse kinematics drives the arm)
                               ▼
                          pen inks the paper
                               │
                               ▼
                    camera + OpenCV read the drawing
                               │
                               ▼
              reward = how well it matches the target (IoU)
                               │
                               └──────► back to the agent
```

The agent acts in **pen space** (move the pen here), so the learned policy is
portable to any arm — inverse kinematics handles the specific robot. The reward
can come from the exact drawing (**ground-truth baseline**) or from the
camera-perceived drawing (**vision — the novelty, Hypothesis H2**).

---

## Reproducibility & honesty

- Every decision, measurement, dead-end, and bug is recorded in
  [`docs/RESEARCH_LOG.md`](docs/RESEARCH_LOG.md).
- Known limitations (to close before publication):
  - **Overshoot confound (open, untested).** Reported IoU is measured at the
    end of the episode, after agents overshoot the shape they finished tracing
    in the first ~15%. On the four single-run 400k models in `models/` (n=1 per
    cell, *not* the 3-seed sweep the H2 table is built from) the camera arm lost
    roughly twice as much as the ground-truth arm, which raises the possibility
    that part of the H2 gap is an artifact of when we stop measuring. The test
    for it — re-running the H2 sweep with peak IoU logged — has not been run.
  - **`eval_eps=8` is a no-op.** Evaluation is fully deterministic (fixed start,
    deterministic policy), so the 8 episodes are pixel-identical. The reported
    +/-std comes from the 3 *training* seeds, which is sound; but there is no
    per-episode variation, and there should be (a held-out shape range is the
    planned fix).
  - **Fixed targets.** Four hard-coded shapes, no held-out set, so we cannot yet
    separate learning to draw from memorising four shapes.
  - **One idealised camera.** The vision reward is a proxy validated against a
    real PyBullet render (mean IoU gap 0.010), but with fixed resolution and
    threshold - no domain randomisation yet, so H3's "no exploitation" result
    applies to *this* camera.
  - **SNR is not yet informative.** With `pen_always_down=True` the ink is one
    connected trace by construction, so stroke-count metrics read ~1.0 whatever
    the agent does. They become meaningful when pen up/down is enabled.
  - **The arm is a KUKA.** A hardware-matched low-cost URDF comes at the
    sim-to-real stage.

---

## Roadmap

1. ✅ Simulator (Phase B) &nbsp; 2. ✅ RL env + PPO (Phase C) &nbsp;
3. ✅ H2: vision vs ground-truth reward &nbsp; 4. 🔄 multi-seed confirmation &nbsp;
5. ⏳ real camera-in-the-loop &nbsp; 6. ⏳ PPO vs SAC (RQ3) &nbsp;
7. ⏳ handwritten digits / letters &nbsp; 8. ⏳ sim-to-real on hardware &nbsp;
9. ⏳ write the paper
