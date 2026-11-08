# RoboSketch-RL — Research Log

> Running lab notebook of every decision and step, with rationale, for the thesis & paper.
> Newest entries at the bottom of each day. Keep the *why*, not just the *what*.

**Project:** RoboSketch-RL — Vision-Guided Reinforcement Learning for Autonomous Robotic Drawing.
**Fixed:** research problem statement & purpose. **Flexible:** all technical choices (research project).

---

## 2026-07-23

### Environment / setup
- Confirmed dev environment: Windows 11, Python 3.9.13. Project root `d:\RoboSketch-RL` (started empty).
- Created `requirements.txt`: pybullet, gymnasium, stable-baselines3, numpy, opencv-python.
- Started install of full stack (includes PyTorch via stable-baselines3 — large download). Decision: keep the **full** environment rather than pybullet-only, since RL training will need torch. *(install in progress)*

### Decision — robot arm model for simulation
- **Chosen:** KUKA iiwa (bundled with PyBullet) for Phase B (simulator build).
- **Rationale:** zero-download, well-tested inverse kinematics, lets us build the drawing engine fast. Phase-B code (pen tracking, paper contact, vision, reward, Gym env) is ~arm-agnostic.
- **Plan:** swap to a hardware-matched low-cost 6-DOF URDF at the sim-to-real phase. RL framework unchanged.
- **Alternatives considered:** Franka Panda (also bundled, research-standard — one-line swap if reviewers prefer); custom MG996R 6-DOF URDF now (rejected: debugging custom URDF + drawing engine simultaneously is two hard things at once).

### Concept — how a KUKA-trained policy transfers to a real arm
- Design the agent to think in **pen/task space** ("move pen to (x,y)"), not arm-specific joint space, for portability. IK converts pen target → joint angles per arm.
- Arm-specific parts live only in the URDF + IK (joint count, link lengths, limits). Swapping arms = swap URDF + re-run IK; the "brain" (state/action/reward) stays.
- Noted research fork worth comparing in the paper: **task-space action (portable)** vs **joint-space action (arm-specific, sim-to-real gap)**.

### Decision — camera vs. ground-truth for the drawing image
- **Two distinct uses of the drawing image:** (1) computing the **reward** — the research method; (2) **debugging** whether the sim works.
- For (2) debugging: use ground-truth pen-tip position (free from PyBullet). No camera needed.
- **Order for (1) the reward — decided:** build a **ground-truth / joint-space reward version FIRST (baseline)**, then add a **virtual camera + OpenCV vision reward (proposed method)**.
- **Rationale:** Hypothesis **H2** ("vision reward beats joint-space reward") *requires* both versions to compare — so the ground-truth version is experimental condition #1 (the baseline / control group), not throwaway. Also follows the change-one-variable-at-a-time principle: get a known-working system, then swap only the reward to vision.
- The ground-truth-vs-vision comparison is itself an **H2 experiment / paper figure**.
- Dropped "direct-logging → PNG" as a separate milestone; pen-tip readout already gives ground truth for debugging.

### Files created
- `requirements.txt`
- `sim/01_manual_control.py` — Phase B milestones B1–B3: load KUKA arm + paper plane, per-joint sliders, live pen-tip (x,y,z) readout. *(not yet run — waiting on install)*

### Revised Phase B plan (simulator, no RL yet)
| # | Milestone | Notes |
|---|-----------|-------|
| B1–B3 | Load arm + paper, manual joint sliders, pen-tip readout | code written |
| B4 | Inverse kinematics: aim pen at target (x,y) | next |
| B5 | Draw a line — move pen across paper | |
| B6 | Virtual camera → image → OpenCV extracts strokes (this IS the vision pipeline) | camera-based |

### Concepts explained (for Methods chapter)
- **Inverse Kinematics (IK):** given a desired pen tip position (x,y,z), compute joint angles to reach it (opposite of forward kinematics: angles → position). PyBullet provides `p.calculateInverseKinematics`. IK is the bridge from the agent's pen-space decision to joint commands, and makes policies portable across arms.
- **RL environment (Gymnasium):** object with `reset()` and `step(action)`. Four parts, for line-drawing:
  - State/observation: pen (x,y), target line/image, current drawing, last action.
  - Action: task-space nudge (dx,dy) [→ IK] (portable) vs joint-space (dθ) (arm-specific).
  - Reward: + near target line / coverage; − off-paper / off-line / wasted motion. Ground-truth now, camera later (H2).
  - Episode: one attempt; ends on completion / step limit (~300) / leaving workspace. Repeat millions of times to improve the policy.

### BLOCKER — PyBullet install failed on Windows (2026-07-24)
- `pip install pybullet ...` failed: PyBullet has **no prebuilt wheel** for Python 3.9 win_amd64 (`--only-binary :all:` → "No matching distribution found"). pip fell back to source build, which errored: **"Microsoft Visual C++ 14.0 or greater is required."**
- Root cause: PyBullet ships only source dist; Windows needs a C++ compiler to build it. No compiler present on this machine.
- Nothing installed except pre-existing numpy 2.0.2. pip aborted before gymnasium/sb3/torch/opencv.
- **Two fix paths under consideration:** (1) install Microsoft C++ Build Tools then compile; (2) switch to Miniforge/conda + conda-forge prebuilt pybullet (no compiler needed, no admin). Decision pending with user.

### RESOLVED — PyBullet via conda-forge (2026-07-24)
- Discovered conda already on system (v22.9.0); current `python` was a renamed conda base.
- **Decision (user):** use conda instead of installing MSVC Build Tools — cleaner for scientific/robotics binaries, no compiler, no admin.
- Created dedicated env: `conda create -n robosketch -c conda-forge python=3.10 pybullet numpy -y`. Installed **pybullet 3.25** (prebuilt via `bullet-cpp 3.25`), Python 3.10.20.
- **Verified:** `import pybullet` works; API version 202010061; pybullet_data path present (KUKA URDF available).
- Remaining packages installing into env: gymnasium, stable-baselines3 (+PyTorch), opencv-python. *(in progress)*
- **Environment of record:** conda env `robosketch` (Python 3.10). Run scripts with `conda run -n robosketch python <script>` (or `conda activate robosketch` first). See `environment.yml`.
- Lesson for Methods/repro: PyBullet has no Windows PyPI wheel → document conda-forge install so others can reproduce.

### Deliverable — educational learning book (HTML)
- Created `docs/learning-book/index.html`: a self-contained, 14-part beginner's book teaching every concept behind the project (robotics, programming, computer vision, RL, simulation, system architecture, hardware, software stack, reward design, learning + development roadmaps, research perspective, appendix/glossary/FAQ).
- **Audience:** Grade-10 level, no prior robotics/AI/CV/RL/math assumed. Purpose: conceptual foundation *before* development — explicitly NOT an implementation guide.
- **Rationale:** user is new to the underlying tech and wants basics-first teaching; a single reference book de-risks the learning phase (Phase 1) and doubles as thesis onboarding material.
- Content sourced from fixed project facts (6-DOF ~₹10k arm, PPO→SAC, PyBullet/KUKA sim-first, IoU/MSE metrics, task ladder line→…→letters, H1–H4 hypotheses, ground-truth-vs-vision reward). Every project-specific choice tagged "MAY CHANGE" vs established facts tagged "FIXED", per the flexible-choices principle.
- **Features:** sidebar nav + search, scroll progress bar, collapsible chapters, inline SVG diagrams/flowcharts, callout boxes (tip/warn/key/analogy/mistake), tables, light/dark theming, responsive layout. Diagrams are simple SVGs meant to be swapped for richer art later.

### Environment complete (2026-07-24)
- Verified in env `robosketch`: gymnasium 1.3.0, stable-baselines3 2.9.0, opencv 5.0.0, torch 2.13.0+cpu, pybullet 3.25. Full stack ready.

### B4 — Inverse Kinematics, built and experimentally validated (2026-07-24)
Wrote `sim/02_ik_reach.py`. Getting drawing-grade accuracy required finding and fixing **four separate problems**. All measured, not assumed — these belong in the Methods/limitations sections.

**Problem 1 — measuring the wrong point (silent ~20 mm bias).**
`p.getLinkState(link)[0]` returns the link's **centre of mass**, not the link frame that IK targets; the correct field is index **4** (`worldLinkFramePosition`). Using [0] reported a constant ~20 mm error at every target. Tell-tale: asked for z=0.020, index 0 read z=0.0002. *Both `01_manual_control.py` and `02_ik_reach.py` corrected to use index 4.*

**Problem 2 — IK configuration (accuracy vs. pen angle).** Measured over 6 targets:

| IK variant | mean pos. error | pen tilt |
|---|---|---|
| position-only, plain | 0.003 mm | **41°** (pen slanted — useless for drawing) |
| position-only + null-space | 0.911 mm | 41° |
| **position + orientation, plain** | **0.007 mm** | **0.00°** ✅ chosen |
| position + orientation + null-space | 2.835 mm | 0.06° |

→ Must pass `targetOrientation` (pen vertical). Must **not** pass the null-space hints (`lowerLimits/upperLimits/jointRanges/restPoses`) — they look helpful but degrade accuracy ~400×. Null-space with continuous stepping was also tested and was far worse (26–52 mm).

**Problem 3 — reachable workspace.** Plain IK ignores joint limits, so it returns solutions the arm cannot physically adopt (elbow, joint 3, driven up to ~13° past its limit; pen then lands ~70 mm off and *no amount of settling fixes it* — it is structural, not lag). Mapped true reachability by commanding the motors and letting physics settle:
- **x ≥ 0.45 → drawing-grade (<1 mm) for all y ∈ [−0.25, 0.25], at every surface height tested (0.05–0.45).**
- x ≤ 0.35 → unreachable near centre; the arm cannot fold that close to its own base.
- Surface height barely matters *inside* the safe zone → paper can sit on the ground plane.
- **Adopted safe drawing area: x ∈ [0.45, 0.65], y ∈ [−0.20, 0.20]** (20 cm × 40 cm), drawn as a blue outline in the GUI and enforced by the slider ranges.

**Problem 4 — the wrist collides with the floor (the modelling flaw).** Asking the wrist link's own frame to sit 2 cm above the ground fails (~28–35 mm error) because the link is a solid body resting on the floor. Pen-up worked, pen-down did not — which isolated the cause. Measured minimum wrist clearance ≈ **0.06 m**.
→ **Fix: model a virtual pen.** A `PEN_LENGTH = 0.10 m` rod hangs from the wrist; IK aims the *wrist* at `paper_z + PEN_LENGTH`, and the *pen tip* is `PEN_LENGTH` below it. This is also more faithful to the real robot, which will hold an actual pen.

**Final validated performance** (81-point serpentine raster of the safe box, motors driven, physics settled):
- worst pen-down position error **0.108 mm**; pen tilt **0.001°**; joint-limit overshoot **0.000°**; pen-tip height drift **0.005 mm**; points >1 mm: **0**.
- Pen-up transitions: 0.107 mm at 60 settle steps → **0.011 mm** at ≥120. The apparent 1.5 mm pen-up error was **settling lag, not a limit** — confirmed by sweeping settle steps.

**Transferable lessons (for the paper & the RL env design):**
1. IK is seeded from the arm's current pose — **small continuous steps are far more reliable than large jumps**. Forcing a reseed to a fixed "home" pose made accuracy *worse* (1.55 mm vs 0.009 mm). Drawing naturally moves in small steps, which suits this.
2. Motor `force`/`maxVelocity` and settle time must be sufficient, or measured "error" is really tracking lag. Distinguish lag (falls with more settling) from structural error (does not).
3. Always validate through `setJointMotorControl2` + settled physics, never `resetJointState`, which teleports joints and silently ignores joint limits — it over-reports accuracy.

### Simulator first run + usability fixes (2026-07-24)
- **First GUI run succeeded.** KUKA arm loads and stands on the ground plane, 7 joint sliders present, live pen-tip readout working. Milestones **B1–B3 confirmed visually**.
- **Blurry window — cause found:** Windows 11 runs the display at 125–150% scaling; PyBullet's OpenGL window is not DPI-aware, so Windows renders it small and upscales the finished image (same as zooming a photo). *Fix:* `SetProcessDpiAwareness(2)` before `p.connect(p.GUI)` — added as `crisp_window()` in new `sim/viewer.py`. Manual fallback documented (exe Properties → Compatibility → override high-DPI → "Application").
- **Removed the three empty "Synthetic Camera" preview panels** (`COV_ENABLE_*_PREVIEW = 0`) — unused, occupied screen space, cost frame rate. NOTE: these panels are PyBullet's RGB/depth/segmentation renderer previews — the same mechanism B6 will use for the virtual camera.
- On-screen debug text reduced to `textSize=0.9` and mirrored to the terminal: `addUserDebugText` is 3D billboard text and is inherently low-res up close; the terminal copy is the readable one.
- **Ugly traceback on window close fixed:** closing the GUI drops the connection mid-frame, so `readUserDebugParameter` raised `pybullet.error` even though `isConnected()` had just returned True. Both scripts now catch `p.error` and exit cleanly.
- New shared module `sim/viewer.py` (`crisp_window()`, `tidy_panels()`) used by both sim scripts.
- **Confirmed from the live run:** IK tracking held at `err = 0.01 mm` while the pen sat on the paper — matches the headless validation.

### Decision — simulator choice (PyBullet vs Gazebo vs MuJoCo; Colab)
- **Keep PyBullet.** Rationale: native on Windows (Gazebo effectively needs Linux/WSL2 + ROS); fast headless stepping suited to millions of RL steps (Gazebo is built for full-system realism, not RL throughput); pure-Python, no ROS needed for an Arduino/servo arm; well accepted in RL robotics literature.
- **MuJoCo** noted as the strongest genuine alternative (faster, better contacts, now free, common in recent RL papers). Not switching: setup already validated to 0.1 mm, and the project bottleneck is reward design + vision, not physics speed. Recorded as the escape hatch if training throughput ever binds.
- **Google Colab is not a simulator** — it is a place to run code. Deferred: no display for GUI debugging, sessions disconnect, cannot reach the physical Arduino. GPU only helps once observations are images (CNN); early low-dimensional PPO runs fine on CPU. Possible later for image-based training runs only.

### B5 — the pen leaves a mark (2026-07-24) ✅
Wrote `sim/03_draw_line.py`. Four measured findings had to be resolved first; each would have silently corrupted the vision pipeline later.

**1. Debug lines are invisible to a camera.** `p.addUserDebugLine` is a viewer-only overlay: a stroke drawn that way changed **0 pixels** in a rendered camera image. Drawing the ink that way would have looked correct on screen while being completely invisible to the reward function. → ink must be real scene content.

**2. `p.GEOM_BOX` does not UV-map a texture across its faces.** This was the root cause of a long false trail. A texture painted with four coloured quadrants rendered on the box's top face as **one flat colour (100% yellow)** — the face samples only a small uniform patch of the image. Consequences observed: an all-black canvas "worked", a centred X "worked" by luck, a top-half fill did nothing.
→ **Fix: the paper is a mesh quad with explicit UVs** (`assets/paper_quad.obj`, a unit quad scaled by `meshScale`). Verified: all four quadrants render at ~25% each.

**3. `p.changeTexture` is a no-op in this build.** Measured 0/4 on every probe, in DIRECT *and* GUI, with both TinyRenderer and the hardware renderer. Reloading the texture from a PNG (`loadTexture` + `changeVisualShape`) updates reliably (**4/4**). → `refresh_paper()` goes via disk, every `REFRESH_EVERY=20` points (each reload allocates a new texture, so not every step).
*(An earlier note in this log claimed changeTexture worked with the hardware renderer — that reading was unreliable; it counted dark pixels over the whole frame rather than the paper only. Superseded by the segmentation-restricted matrix test.)*

**4. The world→pixel mapping was transposed.** My first version mapped x→row and y→col. Correct mapping, **verified against physics** (ink painted at a world point vs. a reference sphere placed at that same point, all four edges, agreement within ~3 px):
```
col = (x - x_min) / width  * (RES-1)        # column follows world +x
row = (y_max - y) / height * (RES-1)        # row follows world -y
```
Left unchecked, every drawing would have been mirrored — and the reward would have scored a mirrored image against the target.

**Validated results** (headless run of the real script, checked against the saved PNG):
| shape | pen points | inked px | geometry check |
|---|---|---|---|
| line | 241 | 2492 | rows 252–259 (pen width), cols 74–430 vs expected 77–434; mean row 255.1 vs 256 ✅ |
| square | 484 | 8451 | centre hollow (0 px), spans 314×313 ✅ |

**Motor tracking lag — a real dynamic, not an error.** Worst deviation of the pen from its commanded target during continuous drawing was **2.8 mm (line)** and **4.8 mm (square)**, versus 0.01 mm when settling fully at a static point. The pen *trails* the target because only 2 physics steps are taken per point. Visible as **rounded corners** on the square. Ink is deposited at the pen's **actual measured position**, so the saved drawing faithfully records where the pen really went. This lag is part of the system dynamics the RL agent will have to learn around, and is realistic (real arms cut corners too). Tunable via settle steps / `maxVelocity` if a sharper trace is wanted.

**Architecture that follows from this:** the **canvas (numpy image) is the authoritative drawing** — it is what gets saved, and what the reward will score. The textured paper is a *visualisation* of it. For headless RL training we will not render ink through PyBullet at all; the canvas is maintained directly, which is also far faster.

### B6 — the robot sees its own drawing (virtual camera + OpenCV) (2026-07-24) ✅
Wrote `sim/04_camera_capture.py`, reusing the B5 drawing machinery. Closes the architecture loop: **robot draws → camera captures → OpenCV extracts → IoU vs ground truth.** Three problems had to be solved, each caught by measurement.

**Camera/canvas orientation — calibrated, not assumed.** Painted an asymmetric marker, captured it, and tested all 8 dihedral transforms of the perceived image against the known canvas. `rot0` won at **IoU 0.998** (next best 0.68), so camera up-vector `[0,1,0]` already matches the canvas convention — no correction needed.

**1. The arm occludes the paper.** A top-down camera looks straight through the arm, which after drawing is bent over the sheet. First capture: arm filled the frame, paper ~40% visible, perceived ink ≈ 0. → **Park the arm before the photo.** Measured several poses; straight-up (`PARK_POSE=[0]*7`, over the base at x=0, far from the paper at x=0.55) gives **100% paper visible, 0 arm pixels**. Real drawing rigs do the same (shoot between strokes / mount the camera clear of the arm).

**2. Otsu threshold fooled by the arm.** With the dark arm in frame, Otsu split arm-vs-paper and classified the thin stroke as background. With the arm parked, switched to a **fixed threshold (128)** on paper-masked pixels — robust in this controlled white-paper/black-ink scene.

**3. THE big one — `p.loadTexture` caches by filename.** The paper texture had been frozen at an early frame: the camera (and the live GUI view) showed only a tiny fragment of the drawing, even though the saved canvas PNG was perfect. Root cause: `refresh_paper` reused two filenames (`_paper_0/_paper_1`), and `loadTexture` returns the **cached first version** for a given path. Verified directly: rewriting the same filename with 5%/30%/60% black kept the camera at the 5% version (dark=5865 constant); unique filenames tracked correctly (5865→35535→71415).
→ **Fix:** `refresh_paper` now writes a **unique filename every call** (monotonic counter, old frames pruned). This also fixes the stale live view during drawing.
*(This is why validate_b5 passed while the texture was broken — B5 checks the saved canvas array, not the rendered paper. Good separation, but it hid the texture bug until the camera needed it.)*

**Validated results** (headless, real script, asserted):
| shape | perceived px | gt px | area ratio | IoU |
|---|---|---|---|---|
| line | 2861 | 2492 | 1.15 | **0.871** |
| square | 9582 | 8451 | 1.13 | **0.882** |

Perceived strokes are ~14% thicker than ground truth — camera/texture filtering widens thin lines slightly. IoU ~0.87–0.88 is strong for recovering a ~1.5 mm stroke; the overlay (green=gt, red=perceived) is almost entirely yellow (agreement). Saved per shape: `cam_raw_*`, `cam_perceived_*`, `cam_groundtruth_*`, `cam_overlay_*` in `output/`.

**Phase B (simulator) is COMPLETE: B1–B6 all done and verified.** The drawing engine + perception loop works end to end. The canvas (numpy) is the authoritative drawing; the camera is the perception path that will replace ground-truth knowledge on the real robot. IoU is wired up as the first accuracy metric.

### Next
- **Old B6 note (now done):** virtual camera looking at the paper → OpenCV extracts the drawn strokes. Groundwork already measured: use `ER_TINY_RENDERER` in DIRECT for headless work; the paper mesh + file-reloaded texture is confirmed camera-visible; segmentation mask isolates paper pixels cleanly.
- Then: define the target shape, the drawing-accuracy metric (IoU / MSE), and the Gymnasium environment (state / action / reward / episode).
- **Known cosmetic limitation (won't fix):** PyBullet's debug GUI chops the first character off every label (`Params`→`arams`, `joint_1`→`'oint_1`). Affects its built-in File/View menus and tabs, which are drawn by the library's C++ code. Padding our own labels with a leading space did not fully cure it. Irrelevant to results — training runs headless and figures are rendered with OpenCV.
- **Status:** environment ✅ | B1–B3 ✅ | B4 ✅ (0.1 mm) | B5 ✅ (line + square, geometry verified) | B6 ✅ (camera perception, IoU ~0.88). **Phase B complete.**

### Usability — interactive drawing sandbox + viewing clarity (2026-07-24)
User feedback while running the GUI: confusing that (a) the mouse moved the *viewport* not the arm, (b) 04 auto-draws then stops (no way to draw by hand), (c) two "cameras" (3D viewport vs. virtual capture camera) looked alike, (d) cluttered checkered floor + small paper.
- Wrote `sim/05_interactive_draw.py`: hands-on sandbox, **no capture camera** (only the viewport). Sliders `pen_x`, `pen_y`, `pen_down`, `clear`; the pen leaves real ink as the user moves it. Viewport zoomed onto the paper. Reuses B5 machinery; strokes are drawn as connected `cv2.line` segments at the pen's actual position so slider jumps still connect.
- Validated headless (mocked sliders trace a diagonal): 3664 inked px, row/col corr −0.90 (correct orientation), thin stroke. Saved to `output/drawing_interactive.png`.
- Test-harness lesson: `addUserDebugParameter` returns −1 for every slider in DIRECT mode, so a uid→name map collapses; synthesize unique ids when mocking sliders headless.

## 2026-08-05  —  Phase C begins (Reinforcement Learning)

### Foundation: target generator + metrics (both validated)
- `rl/targets.py`: line / circle / square / triangle as binary masks in canvas pixel space (task ladder per project scope). `canvas_to_mask()` converts a drawing to the same convention.
- `rl/metrics.py`: **IoU, MSE, coverage, precision, chamfer** (+ `summary()`). Validated against hand-computed cases: identical→IoU 1/MSE 0/chamfer 0; disjoint→IoU 0; half-overlap→IoU exactly 1/3 (verified 0.333); chamfer near<far; monotonic in coverage. All pass.

### The RL environment: `rl/draw_env.py` (`DrawEnv`, Gymnasium)
- **State:** 3-channel image (target, drawn-so-far, pen-position marker), `obs_res=64`.
- **Action:** `[dx, dy, pen_down]` in pen/task space (portable across arms, per B4). `use_arm=False` moves the pen point directly (fast, for RL iteration); `use_arm=True` drives the real IK KUKA (realistic, includes B5 motor lag). Drawing/reward logic identical either way.
- **Reward (truth mode = H2 baseline):** coverage gain − stray ink − time, plus **potential-based proximity shaping** (−distance of pen to nearest target pixel). Vision reward = later H2 experiment.
- **Episode:** ends at `max_steps` or coverage ≥ threshold.
- **Validated:** SB3 `check_env` passes; deterministic; a contour-tracing oracle beats random by huge margins on all 4 shapes (e.g. line +1.5 vs random −26) and idle draws nothing; both backends run.

### Reward shaping — two local optima found and fixed (Methods material)
First PPO runs exposed classic sparse-reward traps; each fix is a documented design decision:
1. **"Draw nothing" trap.** With a coverage-only reward + stray/time penalties, the thin target is rarely hit by random exploration, so the safe optimum is `pen_down=0` (never draw) → IoU 0. **Fix:** dense **potential-based proximity shaping** pulling the pen toward the target (principled — doesn't change the optimal policy), and **pen_always_down** for the first task rung (just trace; pen up/down deferred to multi-stroke shapes like letters).
2. **"Don't move" trap.** With pen always down, freezing the pen (dx≈dy≈0) inks nothing and dodges stray penalties → still IoU 0, but reward was climbing (−7.9→−4.6), i.e. converging to freeze. **Fix:** rebalanced so coverage dominates — `cover_bonus 1→3`, `stray_penalty 0.5→0.2`, `time_penalty→0`. Result: agent moves and covers (coverage 0.06→0.21 in 60k steps, reward −3.0→−0.6 still rising). Trap broken.
- Lesson for the paper: on thin-stroke targets, a coverage/IoU reward alone is too sparse; dense spatial shaping + a dominant coverage term is needed to escape do-nothing optima. (This itself informs research question 4 — which reward enables fastest/most stable learning.)

### Training: `rl/train.py`
- PPO (Stable-Baselines3, `CnnPolicy`), `DummyVecEnv`+`VecMonitor`, evaluates before/after and saves model + renders. PPO first; SAC next for the comparison (RQ3).
- Smoke tests confirmed PPO runs (~420 fps kinematic, CPU) and learns. Launched a 300k-step run on `line` to get the first real learning curve. *(in progress)*

### First PPO training experiments on `line` (2026-08-05) — reward design iterations
Each run 300–400k steps, PPO/CnnPolicy, kinematic env, CPU (~420 fps). The agent
demonstrably *learns* (IoU and coverage rise from ~0); the story is a sequence of
reward designs, each fixing the previous failure mode — good RQ4 material.

| # | reward design | result (IoU / coverage) | failure mode |
|---|---|---|---|
| 1 | coverage − stray − time | 0.06→0.14 / 0.06→0.91 | **scribble**: covers the line by scrawling a blob over the whole region (stray penalty too weak) |
| 2 | IoU-delta + proximity | 0.06→0.12 / →0.43 | **central blob**: covers the easy middle, won't risk extending to the ends |
| 3 | + thicker target, finer control, reachable done-bonus | 0.09→**0.30** / →0.89 | **zigzag**: now sweeps the *full* line, but wobbles vertically (pen thicker than target + no wobble penalty) |
| 4 | + matched pen width + action-smoothness penalty (0.02) | 0.08→**0.508** / →0.87 | **recognizable line** ✅ (mild blob at the start point) |

**Result: first successful RL-learned drawing.** PPO agent trained on `line` reaches **IoU 0.508 (up from 0.079 untrained, 6.4×)**, coverage 0.87, producing a clearly recognizable horizontal stroke (`output/trained_line_kin_after.png`). Model saved `models/ppo_line_kin.zip`. This is the core proof-of-concept for the thesis: the arm *learned* to draw through trial and error, not a scripted trajectory (supports H1).
- Note: smoothness penalty must be scaled to the reward (0.15 accumulated to −24 over 240 steps and swamped the IoU signal → agent minimised motion; 0.02 gave −3 baseline, comparable to the IoU term, and straightened the stroke). Documented as a tuning lesson.
- Remaining imperfection: a blob at the fixed start point (pen begins inking there). Fixes for later: start lifted / randomise start with pen-up approach / brief no-ink settle.

Key takeaways (for the paper):
- Switching the reward from **coverage-based to IoU-delta** structurally removed the scribble optimum (stray ink lowers IoU, so it is self-penalising). IoU-delta telescopes to final IoU → maximising return = maximising drawing accuracy.
- Thin targets are punishing for continuous control (1 px drift tanks IoU); a **wider target + pen width matched to it** makes the task learnable, and narrowing is a natural difficulty step.
- Progression is monotone and interpretable: nothing → central blob → full-width sweep → (smoother trace). This is the learning-curve evidence for H1 ("progressively higher accuracy through interaction").
- These are the BASELINE (ground-truth reward, H2). Vision-reward and PPO-vs-SAC comparisons come next.

### Full task ladder trained (2026-08-05) — line, circle, square, triangle ✅
PPO, 400k steps each, ground-truth (baseline) reward, kinematic env. Every shape learned from IoU 0 to a recognizable drawing:

| shape | IoU (untrained → trained) | coverage | model |
|---|---|---|---|
| line | 0.079 → **0.508** | 0.87 | `models/ppo_line_kin.zip` |
| circle | 0.000 → **0.443** | 0.93 | `models/ppo_circle_kin.zip` |
| square | 0.000 → **0.493** | 0.80 | `models/ppo_square_kin.zip` |
| triangle | 0.000 → **0.421** | 0.71 | `models/ppo_triangle_kin.zip` |

Renders in `output/trained_<shape>_kin_after.png`; summary figure `output/results_montage.png`.
- All four are clearly recognizable (circle closes, square has 4 corners, triangle has an apex). IoU 0.42–0.51 is a solid first-pass baseline for continuous-control drawing; coverage 0.7–0.93.
- **Common artifact across shapes:** a stray "tail" from the paper centre to the shape — the pen starts at centre with `pen_always_down`, so it inks while travelling to the shape. This is the single biggest remaining IoU cost. Clean fix (next): start the pen lifted and approach with pen-up, or start on the shape. Would likely lift IoU noticeably.
- These four results are the first evidence across the task ladder (research question 6: how accurately can geometric shapes be reproduced) and the baseline for the PPO-vs-SAC (RQ3) and vision-vs-truth (H2) comparisons.

### H2 experiment — VISION reward (the project's novelty) (2026-08-07)
Implemented `reward_mode="vision"` in `DrawEnv`: the reward's IoU is computed from a **camera-perceived** version of the drawing, not the exact canvas. This is Hypothesis **H2** — *does a reward from imperfect perception let the agent learn to draw as well as a ground-truth reward?*
- **Perception model** `_perceive()`: reproduces the B6 camera cheaply for fast training — capture at the camera's effective pixel count (resolution loss), binarise (the threshold step), map back to canvas res. Calibrated `cam_px=150` → perceived-vs-truth IoU ~0.83 (real B6 camera was ~0.88). The real-camera-in-the-loop version (use_arm + PyBullet render) is a heavier follow-up; this proxy enables the full multi-shape experiment at training speed.
- **Fair evaluation:** the env still reports **true IoU** in `info["iou"]`, so a vision-trained agent is judged by real drawing quality, not its own (noisy) perception. `reward_iou` (perceived) is logged separately.
- **Design:** `reward_mode` is the single experimental variable; everything else (obs, action, shaping, start) is held fixed vs the truth baseline — clean A/B for H2.
- **Smoke test (line, 40k):** true IoU 0.08 → 0.22 using *only* perceived feedback — the mechanism learns.
- `train.py` gains `--reward-mode {truth,vision}`; vision models/renders are tagged `_vision` so both conditions are kept side by side.

**H2 RESULT (400k each, true IoU — the key first-novelty finding):**
| shape | ground-truth reward | camera (vision) reward |
|---|---|---|
| line | 0.505 | 0.447 |
| circle | 0.357 | **0.425** (vision better) |
| square | 0.470 | 0.453 |
| triangle | 0.468 | 0.319 |
| **mean** | **0.450** | **0.411** |

- **Finding:** an agent rewarded *only* from a noisy camera perception (perceived-vs-truth IoU ~0.83) learns to draw **nearly as accurately** (true IoU) as one with perfect ground-truth reward — mean 0.411 vs 0.450, within ~0.04, and *better* on the circle. All four vision drawings are recognizable (figure `output/results_h2.png`).
- **Interpretation / honesty:** this supports the project's core premise — **learning to draw from vision alone is viable**, which is exactly what the real robot needs (no ground truth exists on hardware). It does not show vision *beats* ground truth on average (triangle notably lower), so the strict H2 wording ("vision improves over joint-space reward") is only partially supported; the strong, defensible claim is **vision-reward ≈ ground-truth-reward in achieved drawing quality**. Single-run numbers — multi-seed runs needed before publication.
- **Caveats to close later:** perception is a *simulated* camera (fast proxy), not the real B6 render-in-the-loop; run the real-camera version (`use_arm`) at smaller scale to confirm; and repeat over seeds.

### Multi-seed H2 experiment — making the result publishable (2026-08-07)
Single-run RL numbers are not credible (high variance); a reviewer would reject H2 on one run. Built `rl/experiment.py`: a **resumable** harness that sweeps ground-truth vs vision reward across seeds per shape and records mean ± std.
- **Design:** 3 seeds × 4 shapes × 2 reward modes × 200k steps = 24 runs. Same hyperparameters as the single-run study; `reward_mode` is the only experimental variable. Evaluated on **true IoU** (8 eval episodes/run).
- **Resumable:** each run appends to `results/h2_seeds.jsonl` immediately; already-done `(shape,mode,seed)` combos are skipped on restart; ordered **seed-major** so a partial sweep still gives ≥1 seed everywhere first. Survives session/agent teardown — just relaunch to continue.
- `--aggregate` prints the mean±std table and writes `output/results_h2_seeds.png` (bar chart with error bars).
- Smoke-tested (`train_eval` runs, aggregate handles empty/partial gracefully). Full sweep launched. *(in progress — ~3–4 h)*
- Note: 200k steps (vs 400k in the single-run study) for feasibility across 24 runs; absolute IoU a little lower but the truth-vs-vision *comparison* (the point) is held at matched budget.

### Real camera-in-the-loop — closing the "simulated camera" caveat (2026-08-12)
The H2 sweep used a fast `_perceive()` proxy for the camera. To justify that, built `rl/camera.py` `RealCamera`: an **actual PyBullet camera render + OpenCV** (the B6 pipeline) in a headless client with just the paper (no arm → no occlusion), drawing carried in as a reloaded texture.

**Caveat closed by validation (the key result).** Ran each vision-trained agent, grabbed its raw canvas, and compared the reward signal from the proxy vs the real camera:
| shape | proxy IoU | real-camera IoU | gap |
|---|---|---|---|
| line | 0.298 | 0.312 | 0.014 |
| circle | 0.426 | 0.446 | 0.021 |
| square | 0.463 | 0.462 | 0.001 |
| triangle | 0.319 | 0.323 | 0.004 |

**Mean gap 0.010; the two perceptions overlap at IoU 0.845.** The fast proxy produces essentially the same reward as a real render → **the entire H2 multi-seed result transfers to a real camera.** This is the standard sim-model-vs-reality validation.

**Real-camera-in-the-loop training** also wired in (`reward_mode="vision_real"`, `train.py --reward-mode vision_real`): the reward is computed from an actual render every step. Measured speed **8.6 steps/s vs 2296 steps/s for the proxy (~270× slower)** — the render + texture-reload cost. Because the proxy is validated as equivalent, the proxy is the practical training path and the real camera is the confirmation.

**Real-camera demonstration run (line, 20k steps, per-step render):** the pipeline runs end-to-end (7 fps, reward from actual renders each step; coverage rose 0.08 → 0.20). But 20k steps is far too few to learn — true IoU stayed ~0.08 (the proxy needed 200k+ steps to reach 0.3–0.5). At 8.6 steps/s, reaching the proxy's result with the real camera would take **~6.5 h**. **Conclusion:** the real camera works in the loop, but is impractical for full training — which is precisely *why* the validated proxy matters: it delivers the same reward signal (gap 0.010) ~270× faster. The proxy validation, not a slow full real-camera run, is the correct way to close the caveat, and it is closed.

### H2 multi-seed sweep (2026-08-12) — the rigorous version
Ran `rl/experiment.py` (truth vs vision × 4 shapes × 3 seeds × 200k steps, resumable, JSONL-logged). One run crashed tracebackless mid-sweep (same transient seen twice before — process/memory, not code); resumed and it skipped the 18 completed runs. **FINAL (24/24, n=3 per cell):**

| shape | ground-truth | camera (vision) | verdict |
|---|---|---|---|
| line | 0.333 ±0.008 | 0.312 ±0.013 | tie (overlap) |
| circle | 0.399 ±0.032 | **0.441 ±0.013** | vision better |
| square | 0.408 ±0.044 | 0.366 ±0.052 | tie (overlap) |
| triangle | 0.387 ±0.067 | 0.297 ±0.015 | truth better |
| **mean** | **0.382 ±0.052** | **0.354 ±0.063** | overlap |

- **Claim (defensible, seed-aware, FINAL):** camera-reward and ground-truth-reward are **statistically indistinguishable overall** in true drawing quality — mean gap 0.028 < seed std (±0.05–0.06); every shape's error bars overlap. Shape-dependent: vision *better* on circle, truth better on triangle (its largest gap, ~0.09, bars barely touch), tie on line/square. Honest H2 result: **vision-based reward matches ground-truth reward on average**, which is what the real (ground-truth-free) robot needs. Not "vision beats truth" — that's unsupported (triangle argues the other way).
- **Sub-finding:** vision reward tends to *lower* seed variance (circle ±0.013, triangle ±0.015 vs truth ±0.032/±0.067) — possibly more stable; n=3, note only.
- (Lower absolute IoU than the 400k single runs because the sweep uses 200k/run for speed; the *comparison* is budget-matched and fair.)
- Figure `output/results_h2_seeds.png` (error bars, all 4 shapes, n=3). Dashboard updated. Experiment fully reproducible: `rl/experiment.py`, results in `results/h2_seeds.jsonl`.

### Start-tail fix (2026-08-07)
The four trained drawings all showed a stray "tail" from paper centre to the shape: with `pen_always_down`, the pen inked while travelling from its centre start to the target. **Fix:** `start_on_target=True` — reset places the pen on the target shape (via new `_px_to_world`), removing the centre-to-shape trail; mimics placing the pen where a stroke begins.

**Two variants — a measured lesson:**
- **Random on-target start (first try): backfired.** Placing the pen at a *random* target pixel each episode dropped the line from 0.51 → **0.22** (and did not help circle/triangle). A random start point is extra variance the policy must absorb. Also: the line never had a tail in the first place — its centre start already sits on the line; only the *closed* shapes (centre is interior) had tails.
- **Deterministic nearest-centre start (correction):** start at the target pixel closest to paper centre. No episode variance; keeps the line's start ≈ centre; the start sits on the outline for closed shapes.
- Lesson for the paper: fixed/low-variance episode initial conditions matter for sample-efficient learning of a *specific* target; randomising the start is a generalisation choice, not a free improvement.

**Result of the deterministic-start retrain (400k each):**
| shape | center-start (with tail) | deterministic-start | note |
|---|---|---|---|
| line | 0.51 | **0.505** (cov 0.96) | clean stroke, held |
| square | 0.49 | **0.470** | ~held |
| triangle | 0.42 | **0.468** | improved |
| circle | 0.44 | **0.357** (cov 0.66) | dipped — doesn't fully close the loop |

- **Honest read:** net ≈ wash vs the center-start baseline. The center-to-shape tail is gone, but a *different* imperfection remains — the agent makes occasional **stray excursions off the outline** mid-trace (visible as a short spur on the circle top, square/triangle corners). All four shapes are recognizable; none are clean. Figure `output/results_montage.png` + dashboard updated to these numbers.
- **Remaining trace-quality work (candidate next steps, not yet done):** stronger penalty for leaving the target region; longer training; recurrent/velocity features; or evaluate at multiple seeds (current numbers are single-run). Deferred pending direction — could instead move to SAC (RQ3) or the vision reward (H2).

## 2026-08-06/07 — Research progress presentation (guide review)

### Deliverable — `docs/presentation/RoboSketch-RL_Progress_Review.pptx` (84 slides)
Built a research-level progress deck for the guide review, covering everything completed
plus the forward plan. **Generated by code, not hand-authored**, so it can be rebuilt from
the results whenever they change.

- **Structure (12 sections):** project overview · system vision · progress so far
  (stage-by-stage) · technical design · programming details · RL design · mathematical
  foundations · computer vision · development timeline · future roadmap · anticipated
  questions · backup slides.
- **Every completed stage** is presented in a fixed six-panel form — *what we did · why it
  was necessary · alternatives considered · why this approach · challenges faced · result /
  evidence* — matching how the work is recorded in this log.
- **Speaker notes on all 84 slides** (~78k characters), written for spoken delivery.
- **All figures and numbers come from real outputs** (`output/`, this log). No invented
  results. Claims are separated into "established / measured" vs "not yet established".

### Files
| file | role |
|---|---|
| `docs/presentation/build_deck.py` | orchestrator; imports the six content parts |
| `docs/presentation/deck_kit.py` | design system (palette, type scale, cards, flows, tables, equation blocks, auto-fit) |
| `docs/presentation/deck_part1..6.py` | slide content, one module per group of sections |
| `docs/presentation/make_figures.py` | composes slide-ready figures from `output/` |
| `docs/presentation/preview.py` | renders each slide to PNG for layout QA |
| `docs/presentation/check_deck.py` | structural QA: out-of-bounds shapes, notes coverage |

Rebuild: `conda run -n robosketch python docs/presentation/make_figures.py` then
`... build_deck.py`.

### Notes / decisions
- **`python-pptx` added to the env** (pip). Recorded here because it is now a build
  dependency of the docs, not of the experiments.
- **No PowerPoint or LibreOffice on this machine**, so layout could not be eyeballed. Wrote
  `preview.py`, which rasterises the .pptx XML directly with PIL (shapes, fills, text,
  tables, pictures) and reports text-overflow / off-slide warnings. This is how every slide
  was verified. Worth keeping: it makes the deck testable like code.
- Diagrams are **native PowerPoint shapes and connectors**, not images, so they stay
  editable and crisp when projected.
- Added `fit_size()` auto-shrink to the kit after the first pass showed text overrunning
  cards — layout is now data-driven rather than hand-tuned per slide.
- **Honesty framing carried through the deck:** a "what is proven / what is not" slide, a
  threats-to-validity slide, and an explicit note that every current number is a *single
  run* (multi-seed runs are item N5 on the roadmap). The literature slide states plainly
  that the systematic survey is still in progress.

### Phase C — plan continues
Simulator is done, so the roadmap moves to the RL environment:
1. **Target generator:** produce target images (line, circle, square, triangle) as canvases to imitate.
2. **Metric module:** formalise IoU + MSE as a reusable scorer (drawn vs target); reused for reward and for evaluation.
3. **Gymnasium environment:** wrap the drawing engine as `reset()/step(action)`.
   - state: pen (x,y), pen up/down, target image, current canvas (or features of them)
   - action: task-space nudge (dx,dy) + pen up/down  (portable design, per B4)
   - reward: ground-truth first (baseline), camera/vision reward second (H2 experiment)
   - episode: to step limit / completion / leaving the safe box
4. **PPO training** (Stable-Baselines3), then SAC; compare (research questions 3–4).
Design note: for training speed, run headless and maintain the numpy canvas directly (no PyBullet texture render per step) — B6 showed texture reload is disk-based and far too slow for millions of steps. The camera/vision reward is applied as the H2 condition, not the fast default.

---

## 2026-08-12 — Systematic literature review (the survey the deck flagged as "in progress")

The progress deck (2026-08-06/07) stated plainly that the systematic survey was still
outstanding. This entry closes that item. **No project code was modified** — the review was
run to completion first, deliberately, so that proposals rest on evidence rather than on
assumptions about what the literature says.

### Deliverables

| file | role |
|---|---|
| `research_papers/README.md` | index of 33 papers: full record per paper (title, authors, year, venue, link, relevance, technique, what to take, classification) + a master ranking |
| `research_papers/STUDY_NOTES.md` | per-paper analysis (problem, gap, objectives, method, architecture, state/action/reward/episode, vision mechanism, dataset, setup, results, limitations, future work) |
| `research_papers/COMPARATIVE_ANALYSIS.md` | cross-paper comparison, convergent findings, reward taxonomy, metric audit, gap map, novelty positioning |
| `docs/PROJECT_PROPOSAL_v2.md` | the proposals that follow from the review — sequenced, with evidence and effort per item |
| `research_papers/01..05_*/` | 33 PDFs, downloaded and organised |

Folders: `01_Foundational` (6) · `02_Directly_Related` (11) · `03_Advanced_Methods` (8) ·
`04_Robotics_and_Vision` (3) · `05_Reinforcement_Learning` (5).

### Method

Searched across the eight requested topic areas, then **verified every arXiv paper's metadata
through the arXiv API** rather than trusting search-result summaries (this caught several
mis-stated venues — e.g. CalliRewrite is ICRA 2024, not IROS 2024). Reading depth is recorded
honestly per paper in `STUDY_NOTES.md`: **8 read in full (◆)**, 25 at abstract + targeted
sections (◇), with a prioritised remaining-read queue. Numbers are only quoted from ◆ papers.

Full reads: D01 From Scratch to Sketch (ICRA 2022) · D02 Learning to Paint (ICCV 2019) ·
D03 Teaching Robots To Draw (ICRA 2019) · D04 Autonomous Visual Rendering (WAFR 2016) ·
D08 Sim-to-Real Brush (2023) · D09 CalliRewrite (ICRA 2024) · A01 FRIDA (ICRA 2023) ·
R02 RL without Reward Engineering (RSS 2019).

### The finding that matters most

**Three of the closest papers name this project's contribution as their own unaddressed
future work**, in their own words:

- **D01** (Lee et al., ICRA 2022) — the closest published system to ours — is *deliberately
  camera-free*, synchronising via forward kinematics, and writes: *"using a camera as an
  observation of canvas in the future work could be of great help in the synchronization
  step…"*
- **D03** (Kotani & Tellex, ICRA 2019): *"we are interested in closing the learning loop by
  enabling the robot to inspect what it has drawn and improve its drawing policy based on
  observation of what it actually drew."*
- **D09** (Luo et al., ICRA 2024): *"…a lack of real-world training scenarios to bridge the
  sim2real gap. We leave these challenges as our future work."*

That is a strong, citable, *recent* gap statement — and it is theirs, not ours.

### The finding that most constrains us

**"Reward from perception instead of privileged state" is established prior art** — Sermanet
et al. (RSS 2017) and Singh et al. (RSS 2019). It cannot be claimed as new. The novelty
statement in the README ("teaching the robot *how to learn to draw*") also does not survive
contact with the literature: D01, D02, D05, D07, D08 and D09 all do that.

The defensible reframing is a **measurement**, not an invention: *nobody has measured what
drawing accuracy is lost when the agent learns from perception instead of from truth.* That
is exactly H2, and it is what the three papers above left open.

### Findings that change the code (proposed, not applied)

- **Probable partial-observability bug.** `DrawEnv`'s observation omits the step count, yet the
  episode is truncated at `max_steps=120`. D02 puts the step number in the state for exactly
  this reason. Two identical canvases with 5 vs 100 steps remaining need different actions and
  our agent cannot distinguish them.
- **Global observation is the outlier.** Three independent papers converge on *local/egocentric*
  observation: D03 extracts a 5×5 patch centred on the pen (ablation: removing it drops stroke
  accuracy 0.963 → 0.157), D08 uses an egocentric crop, D01 bounds strokes to a square around
  the pen. Ours is a global 64×64 view.
- **`pen_radius_px` (from a hard-coded 0.0035 m stroke width) is probably our largest reality
  gap.** A01 fits a stroke model to photographed real strokes; D09 does the budget version on a
  low-cost Dobot Magician — *"leave traces at varying z heights, measure widths, calculate r,
  and establish the z–r connection through linear fitting."* An afternoon and a ruler.
- **`_perceive()` is a very optimistic camera** (`resize(150px)` + `threshold(>60)`, both fixed).
  H2 is currently a claim about *one idealised camera*. Domain randomisation (Tobin et al.,
  IROS 2017) fixes this and needs no hardware.
- **`pen_always_down=True` makes every multi-stroke glyph unreachable** (`4`, `5`, `i`, `E`) —
  a hard cap on achievable IoU at the digits/letters rung.
- **Missing metrics the field has:** SNR (stroke fragmentation, D09 — note Learning to Paint
  scores *worst* of all methods on it, so RL stroke agents are specifically prone to this and
  we currently cannot see it); Δ sim2real = MSE(sim canvas, photo) (A01, with published
  reference points 0.029 / 0.066 / 0.156); recognisability at the letters rung (nobody reports
  it — an opportunity).
- **No held-out targets.** D02 holds out 2,000 test images to test generalisation. With four
  fixed shapes we cannot currently distinguish learning to draw from memorising four shapes.

### Two experiments the review says we are missing

1. **Reward-exploitation analysis (new H3).** R02's central failure mode is a policy learning
   to *fool* the reward model. Our downsample-and-threshold perception could plausibly be
   fooled (thin strokes dilate; near-misses threshold into hits). `DrawEnv.step()` **already
   returns both `info["iou"]` and `info["reward_iou"]`**, so plotting their gap over training
   may be possible on existing logs. Either outcome is publishable.
2. **Disturbance recovery (new H4) — the linchpin.** D01 argues camera-free is *more* robust
   and it works well. Without a demonstration that vision fixes an error forward kinematics
   *cannot* detect — pen slip, paper shift, ink failure — D01 is a complete answer to this
   project's motivation. This is the most important experiment on the list.

### Honest notes

- Metadata was verified via the arXiv API; several web-search summaries were wrong about venues.
- Reading depth is marked per paper. Do not quote numbers from a ◇ entry without reading the PDF.
- Paywalled work (the DDPG drawing-robot papers, several Elsevier/Springer calligraphy papers,
  the e-David MDPI/Springer entries) is discussed but not redistributed. **e-David (Deussen et
  al., Konstanz) is the historical origin of the optical-feedback painting loop and must be
  cited** even though its PDFs are not in the folder.
- D03 reports 0.999 IoU (supervised, stroke-ordered data, 1-px skeletonised targets) against our
  0.36–0.51. Different problems, but the comparison must be **pre-empted in the paper**, not
  left for a reviewer to raise.

### Next
Proposals are in `docs/PROJECT_PROPOSAL_v2.md`, sequenced in §8, awaiting a decision. Stages
1–3 (free wins → domain randomisation → disturbance recovery) are what constitute the paper;
stages 4–7 are optional strengthening.

---

## 2026-08-23 — Stage 1 of the post-review plan ("the free wins")

The literature review (2026-08-12) ended with proposals but no code changes, deliberately.
This entry starts executing `docs/PROJECT_PROPOSAL_v2.md` §8 **Stage 1**: the three items
that are cheap, fix genuine holes, and do not depend on any other decision —
**O1** (remaining-time in the observation), **§4.5** (the missing metrics), and
**§4.2 / H3** (the reward-exploitation analysis).

**Guiding rule for this stage:** every change is a *flag with the old behaviour as default*,
not a silent improvement. Nothing recorded before today may move underneath us, and each
change has to be defensible as a measured ablation rather than an assertion.

### Sanity check first — the simulator still runs end to end
Before changing anything, ran the pipeline to confirm the recorded state is real:

- `sim/04_camera_capture.py square --headless` — arm draws, parks, virtual camera captures:
  484 inked points, perceived-vs-truth **IoU 0.882** (the B6 number, reproduced).
- Loaded the four trained PPO models and ran one deterministic episode each:
  line **0.505**, circle **0.357**, square **0.470**, triangle **0.468** — matching the
  deterministic-start table in this log to three decimals. The pipeline is reproducible.
- What the drawings show, plainly: all four shapes are recognisable, none are clean. The
  circle does not close (coverage 0.66) and every closed shape has short spurs off the
  outline plus a visible zig-zag along the stroke.

### §4.5 — the missing metrics (`rl/metrics.py`)
| function | what it measures |
|---|---|
| `stroke_count(mask)` | connected components >= 4 px — the raster analogue of "how many strokes" |
| `snr(drawn, target)` | D09's **Stroke Number Ratio** = strokes(drawn) / strokes(target) |
| `target_perimeter_px(target)` | outline length of the target (contour length halved, because a thick stroke's contour traces both sides of the band) |
| `path_ratio(path_len_px, target)` | **pen travel / outline length** — 1.0 = traced once, efficiently |

**An honest caveat, recorded rather than hidden.** SNR is the metric the review asked for, and
it is implemented faithfully (verified: cutting a square target in two places gives exactly
4 strokes, SNR 4.0). But with `pen_always_down=True` the pen never lifts, so the drawn ink is
**one connected trace by construction** and SNR is ~1.0 no matter how badly the agent draws.
Confirmed on the trained square: SNR = 1.00. **SNR only becomes informative once pen up/down
is enabled (proposal A2).** It is in place and correct, waiting for the rung that needs it.

`path_ratio` is the metric that actually catches our observed defect, and it does so
immediately: **the trained square agent has path_ratio 3.03** — the pen travelled three times
the length of the outline it was tracing.

> **CORRECTED 2026-09-03.** That denominator was wrong (`RETR_EXTERNAL` discards the
> inner edge of a closed stroke). The correct figure is **1.59** — still 59% further than
> tracing the outline once, but not "three times". See the 2026-09-03 entry. That is the zig-zag and the spurs, finally as a
number. IoU alone could never have shown it.

### O1 — remaining-time in the observation (`rl/draw_env.py`)
The episode is truncated at `max_steps`, but nothing in the observation says how many steps
remain, so two identical canvases with 5 vs 100 steps left are indistinguishable to the policy
and require different actions. The task was **partially observable**. `DrawEnv(time_in_obs=True)`
appends a constant-valued 4th channel = `255 * steps / max_steps` (D02 puts the step number in
the state for exactly this reason).

- **Default is `False`**, so every previously recorded number stays reproducible — verified by
  re-loading `models/ppo_square_kin.zip` (a 3-channel model) and reproducing IoU 0.470 exactly.
- Verified the channel is constant-valued and runs 1 -> 129 -> 255 across an episode, that the
  first three channels are bit-identical to the 3-channel observation, and that SB3's
  `CnnPolicy` trains on a 4-channel observation without complaint.
- `step()` now also reports `iou_gap`, `path_len_px`, `path_ratio` and `snr` in `info`.

### Bug found while testing — `targets.py` ignored its `res` argument
Every shape function called `_blank()` and `_extent()`, which read the module-level
`RES = 512`, so `T.make("square", res=128)` silently returned a **512x512** image. Fixed:
`_blank(res)`, `_extent(res)`, and a new `_stroke(res)` that scales `STROKE_PX` with the
canvas so a smaller render keeps the same *relative* thickness.

**Impact on recorded results: none, and this was proven rather than assumed.** `DrawEnv` only
ever calls `T.make(shape, res=512)`, and re-implementing the pre-fix code exactly and diffing
it against the fixed code at res=512 gives **bit-identical masks for all four shapes**. (The
first attempt at that proof "failed" because the reimplementation guessed `_binarize` as
`>127` when it is `>40` — the mismatch was in the test, not the code.)

Separately, `output/target_*.png` (4 Aug) turned out to be **stale**: they were saved when
`STROKE_PX` was ~8, not the current 14, so they disagreed with the live generator at IoU ~0.51.
Nothing reads them (grep-checked), so they were display artifacts only; regenerated.

### Why the figures are drawn with OpenCV and not matplotlib
`matplotlib` is not in the `robosketch` env. The env is deliberately minimal and PyBullet on
Windows only resolves through conda-forge (2026-07-24 blocker), so running the solver again to
add a plotting library is a real risk to a working research environment for no scientific gain.
`experiment.py` already draws its figure with cv2; `h3_exploitation.py` now carries a small
`_Axes` helper (line plots, shaded +/-sd bands, dashed series, grid, tick labels) so the same is
true of every figure in the project. **Decision: no matplotlib; cv2 figures throughout.**

### H3 — the reward-exploitation test (`rl/h3_exploitation.py`)
The review flagged this as "runnable today, on existing data". **It was not** —
`results/h2_seeds.jsonl` records only each run's *final* IoU, not the perceived-vs-true pair
over training. So the one-line logging change the review anticipated was in fact needed: a SB3
callback that records `(iou, reward_iou, gap, path_ratio, snr)` at every episode end, written
to `results/h3_<shape>_<mode>_s<seed>.jsonl`.

**The control matters as much as the experiment.** A `truth` run has `reward_iou == iou` by
construction, so its gap must be *identically* zero. Measured: `max |gap| = 0.000000`. The
logging is therefore trustworthy before any vision run is interpreted.

**A verdict-logic bug, caught on the smoke run and fixed.** The first version called a run
"EXPLOITING" on the fitted slope alone. On a 5k-step smoke run whose gap wobbled around 0.001
it duly reported exploitation — a slope on noise. A verdict now requires **both** a rising
trend *and* an end-gap above 0.02 IoU (well under the +/-0.05 seed spread of the H2 sweep), and
runs with fewer than 200 logged episodes are reported as "inconclusive" rather than scored.

### O1 ablation harness (`rl/o1_ablation.py`)
`experiment.py::train_eval` gained a `time_in_obs` argument (default `False`) and now returns a
metric *dict* including `snr` and `path_ratio`, so the ablation runs through **the identical
code path that produced the published H2 baseline** — same PPO hyperparameters, same 8 envs,
same eval seeds, same 8 eval episodes. Only the flag differs. Results go to their own
`results/o1_ablation.jsonl` (resumable, seed-major) so the H2 file is never touched.

Both arms are run fresh rather than reusing the existing truth numbers, because the baseline
records predate `path_ratio` and a comparison where only one arm has a metric is not a
comparison. Reward is `truth` throughout: O1 is a question about observability, and mixing it
with H2's perception question would confound the two.

The aggregate prints an explicit verdict against the seed spread: a mean change smaller than
the seed-to-seed std is reported as **no measurable effect**, whichever way it points.

### H3 RESULT — the camera reward is **not** being exploited ✅

4 shapes x 200k steps, camera reward, every episode logged (832 episodes per run,
3328 total), plus a 200k `truth` control.

| shape | mean gap | max abs gap | gap over final 10% | corr(true, perceived) |
|---|---|---|---|---|
| line | -0.0049 | 0.0177 | -0.0095 | 0.9989 |
| circle | -0.0013 | 0.0290 | -0.0077 | 0.9970 |
| square | +0.0051 | 0.0210 | +0.0078 | 0.9985 |
| triangle | +0.0006 | 0.0232 | +0.0010 | 0.9969 |
| **all** | **-0.0001** | **0.0290** | — | — |

- **Mean gap across 3328 episodes: -0.0001.** 95% of all gaps fall within +/-0.013.
  The largest single-episode excursion in the whole experiment is 0.029 — still
  below the +/-0.05 seed spread of the H2 sweep.
- **True and perceived IoU correlate at 0.997–0.999** throughout training.
- The two signs cancel: line and circle run slightly *negative* (the camera
  **under**-credits the agent), square and triangle slightly positive. There is no
  systematic direction, which is what a proxy with no exploitable structure looks
  like.
- **Control passed exactly:** the `truth` run's gap is 0.000000000 over 832 episodes.

**Claim (defensible):** across 200k steps of training on four shapes, a policy
optimising the camera-perceived IoU gains **no measurable perceived-IoU credit
that it has not actually earned**. R02's failure mode does not appear here. This is
positive evidence for H2 — and, unlike H2 itself, it is a statement about the
*training process* rather than only the endpoint.

**Honest limits:** one seed per shape (n=1 per cell) — the H2 sweep's n=3 showed
seed spread of +/-0.05, so a *small* per-shape effect could hide inside this. But
3328 episodes with a mean gap of -0.0001 and correlation 0.998 is not a marginal
result. Also: this tests the *fast proxy* camera. A more realistic camera (domain
randomisation, proposal 4.1) has more structure to exploit and must be re-tested.
Figure: `output/results_h3.png`.

### UNEXPECTED FINDING — agents finish early, overshoot, then idle for 74% of the episode

Found by asking where the high `path_ratio` was coming from. This was not on the
proposal list and is the most consequential thing measured today.

Recording IoU at *every step* of a deterministic evaluation (`rl/overrun.py`):

| shape | reward | final IoU | peak IoU | lost | peak@ | canvas frozen@ | idle |
|---|---|---|---|---|---|---|---|
| line | truth | 0.505 | 0.552 | 0.047 | 12 | 131 | 45% |
| circle | truth | 0.357 | 0.409 | 0.053 | 23 | 28 | 88% |
| square | truth | 0.470 | 0.504 | 0.034 | 41 | 47 | 80% |
| triangle | truth | 0.468 | 0.507 | 0.039 | 35 | 124 | 48% |
| line | vision | 0.447 | **0.578** | **0.131** | 12 | 20 | 92% |
| circle | vision | 0.425 | **0.556** | **0.131** | 25 | 88 | 63% |
| square | vision | 0.453 | 0.495 | 0.043 | 36 | 43 | 82% |
| triangle | vision | 0.319 | 0.355 | 0.036 | 23 | 27 | 89% |

**Mean IoU lost: 0.064 — more than twice the entire H2 truth-vs-vision gap (0.028)
that this project set out to measure.**

**What is actually happening** (the first reading was wrong and the figure corrected
it — the IoU curves are *flat* for most of the episode, so the agent is not damaging
its drawing throughout):

1. The shape is traced within the **first ~10–17%** of the episode (peak at step
   12–41 of 240).
2. A **short overshoot right after completion** costs the IoU above — for most cells
   the damage is done in 4–8 steps.
3. The canvas then **freezes**: 0–1 px of new ink over the entire second half.
   Mean 74% of every episode is spent with a canvas that never changes again.

**Why it happens.** `max_steps=240`, `pen_always_down=True`, and there is **no
terminate action**. Having drawn the shape, the agent cannot stop, cannot lift the
pen, and cannot end the episode. Standing perfectly still is technically reachable
(`dx=dy=0` re-inks the same pixel) but it is a single point in a continuous action
space that a Gaussian policy with `ent_coef=0.02` will not land on exactly — so it
drifts a little past the outline first, then settles.

**Two consequences, both actionable:**

- **Every IoU this project has reported is measured after the overshoot.** The
  policies are better than their scores: peak IoU is 0.355–0.578 against reported
  0.319–0.505. The vision agents are hit hardest (line and circle each lose 0.131),
  which means **the H2 comparison may be systematically unfair to the camera arm** —
  the thing the whole study is about. This must be checked before H2 is written up.
- **~74% of every episode is wasted sample budget.** At 200k steps per run that is
  ~150k steps spent on frozen canvases. Terminating on plateau (or simply cutting
  `max_steps` to ~60) would be close to a 4x throughput win at no cost to the result.

**Fixes to test (not yet applied):** an explicit terminate action; A2 pen-up so the
agent can lift instead of ink; terminate-on-plateau; annealing `ent_coef`; and
reporting *peak* alongside *final* IoU. The first three are candidates for Stage 1b.

### Protocol finding — `eval_eps=8` evaluates the same episode eight times

While checking whether the overrun effect survived multiple episodes: it cannot be
checked that way, because **the evaluation is fully deterministic**. `start_on_target`
picks the target pixel nearest the paper centre (not drawn from the RNG), and
`model.predict(deterministic=True)` adds no noise. Verified directly: the 8 eval
episodes in `experiment.py`'s protocol, with its exact seeds, produce **eight
pixel-identical canvases** and IoU std 0.000000000; the pen start is identical for
reset seeds 0, 1, 2 and 12345.

**This does not invalidate the H2 results.** The `+/-std` reported there comes from
the **3 training seeds**, which genuinely differ. But `eval_eps=8` is a no-op that
costs 8x the evaluation compute for one number, and any future claim of the form
"averaged over 8 episodes" would be wrong. Either drop it to 1, or introduce real
eval variation (random start, or the parameterised-shape held-out range of §5.4) —
the latter is the better fix, and is already on the roadmap.

#### The part of this that touches H2 directly

Averaging the eight cells above by reward mode:

| | ground-truth | camera | difference |
|---|---|---|---|
| **final** IoU (what H2 reports) | 0.450 | 0.411 | truth +0.039 |
| **peak** IoU (before the overshoot) | 0.493 | 0.496 | camera +0.003 |
| mean IoU lost to overshoot | 0.043 | 0.085 | camera loses ~2x |

The camera arm loses roughly **twice as much** IoU to the post-completion overshoot
as the ground-truth arm. Scored at their peak the two are level (0.493 vs 0.496);
scored at the end, ground-truth appears 0.039 ahead — which is close to the whole
0.028 gap the H2 sweep reports.

**This is a hypothesis, not a result, and must not be quoted as one.** These are the
single-run 400k models in `models/`, n=1 per cell, *not* the 200k x 3-seed runs the
H2 table is built from. But it raises a specific, testable worry: **the small edge
ground-truth appears to hold in H2 may be an artifact of when we stop measuring,
not of what the agents learned.** Since "vision matches truth" is the project's
central claim, the direction of this bias matters — it would make the claim
*stronger*, which is exactly why it needs checking rather than adopting.

**Test:** re-run the H2 sweep logging peak IoU alongside final IoU (the sweep already
runs the eval loop; it is a two-line change), and compare both columns at n=3. If the
peak-IoU columns overlap more tightly than the final-IoU columns, the overshoot is
confounding H2 and the fix belongs in the environment before the paper is written.

### Stage 1b — acting on the overrun finding (harness; results in the entry below)

Three switches added to `DrawEnv`, all **default off** so nothing recorded before
today moves:

| switch | what it does | who decides |
|---|---|---|
| `info["peak_iou"]`, `info["overshoot"]`, `info["steps_used"]` | always reported now | — (free) |
| `plateau_patience=k` | truncate after `k` steps with no improvement in the reward IoU | the environment |
| `allow_stop=True` | a 4th action head, "I am finished"; `action[3] > 0.5` terminates | the agent |

`plateau_patience` sets `truncated`, not `terminated`: the episode *could* have
continued, so the value function should still bootstrap. `allow_stop` sets
`terminated`, because the agent choosing to end really is the end of the episode.

**A result already, from the smoke test — `plateau_patience` fixes the waste but
NOT the overshoot.** Replaying the trained square agent:

| patience | steps used | final IoU | overshoot |
|---|---|---|---|
| off | 240 | 0.470 | 0.034 |
| 40 | 81 | 0.470 | 0.034 |
| 20 | 61 | 0.470 | 0.034 |
| 10 | 51 | 0.470 | 0.034 |

Episode length drops ~4.7x while the drawing is **completely unchanged**. That is
the 74%-idle waste recovered, and it confirms the tail really is dead time. But the
IoU loss survives every setting, and it has to: a plateau detector is **lagging** —
"no improvement for k steps" can only be observed *after* the peak has passed, and
the square's damage is done between steps 41 and 47. No value of `k` can catch it.

**Therefore the overshoot can only be fixed by the policy itself**, which is what
`allow_stop` tests: only the agent knows, at the moment it happens, that it has just
finished the shape. This is also why the stop head cannot be retrofitted to the
existing models — it has to be trained.

> **REFUTED 2026-09-03.** The ablation went the other way: the environment-side arm
> (`plateau`) won and the policy-side arm (`stop`) was inconclusive. The reasoning above
> holds only for a *frozen* policy being filtered at evaluation. Trained *with* the
> detector, the agent never learns to overshoot in the first place, so there is nothing
> for a lagging detector to catch. See the results entry below.

**Harness:** `rl/overshoot_ablation.py`, three arms (`baseline` / `plateau` / `stop`)
x 4 shapes x seeds, into `results/overshoot_ablation.jsonl`. It runs through
`experiment.py::train_eval`, which now takes a generic `env_kwargs` dict so future
ablations need no new parameters, and which applies those kwargs to **both** the
training and the evaluation envs (an agent with a stop action must be evaluated with
one).

**The verdict rule is written to be hard to fool.** An arm only counts as fixing the
problem if it cuts the overshoot *while holding peak IoU*. Cutting the overshoot by
stopping early and drawing a worse shape is not a fix, and the aggregate reports that
case separately as "stops too early".

### O1 sweep restarted deliberately (~40 min of compute discarded)

The O1 ablation had completed 1 of 24 runs when the overrun finding landed. It was
stopped, `results/o1_ablation.jsonl` cleared, and the sweep relaunched with
`peak_iou` / `overshoot` / `steps_used` recorded per run.

**Why that was worth 40 minutes.** O1 tells the agent how much of the episode is
left — and the end of the episode is exactly where the overshoot happens. Judged on
final IoU alone, an O1 arm that scored higher would be uninterpretable: it could mean
"drew a better shape" or merely "overshot less". With peak and overshoot recorded the
two are separable. Measuring the wrong thing carefully is worse than measuring the
right thing late.

**A reproducibility check fell out of the discarded run.** Its single completed cell,
line / truth / seed 0, scored **IoU 0.334**; `results/h2_seeds.jsonl` records **0.3337**
for the same cell from the 12 Aug sweep. Reproduced to three decimals in a separate
session, through a modified `train_eval`, after the `targets.py` fix and the metric
and observation changes — independent confirmation that none of today's edits moved
the baseline.

### O1 RESULT — remaining-time in the observation: a modest, shape-dependent gain

24 runs, 4 shapes x 3 seeds x 2 arms x 200k steps, ground-truth reward, identical
protocol on both arms (`results/o1_ablation.jsonl`).

| shape | IoU off | IoU on | delta | peak off | peak on | path off | path on |
|---|---|---|---|---|---|---|---|
| line | 0.333 +/-0.008 | 0.359 +/-0.037 | +0.026 | 0.348 | 0.404 | 12.44 | 9.01 |
| circle | 0.399 +/-0.032 | 0.391 +/-0.050 | -0.008 | 0.450 | 0.440 | 5.16 | 8.09 |
| square | 0.408 +/-0.044 | 0.472 +/-0.011 | +0.064 | 0.440 | 0.476 | 2.68 | 6.19 |
| triangle | 0.387 +/-0.067 | 0.460 +/-0.021 | +0.073 | 0.403 | 0.480 | 5.54 | 6.53 |
| **mean** | **0.382 +/-0.052** | **0.421 +/-0.058** | **+0.039** | 0.410 | 0.450 | 6.44 | 7.45 |

**Paired analysis (both arms ran the same seeds, so the pair is the unit):**

| metric | mean delta | sd | pairs up | t | reading |
|---|---|---|---|---|---|
| IoU | +0.039 | 0.062 | 9/12 | +2.17 | suggestive, not conclusive |
| peak IoU | +0.040 | 0.062 | 9/12 | +2.22 | probably real |
| overshoot | +0.001 | 0.034 | 5/12 | +0.11 | **no effect** |
| path_ratio | +0.998 | 3.835 | 7/12 | +0.90 | no effect |

**Verdict.** O1 gives a **modest improvement of about +0.04 IoU**, in 9 of 12 paired
runs, sitting right at the conventional threshold of evidence. It is real enough to
keep and too small to headline. It is also **shape-dependent**: triangle (+0.073,
all three seeds improved) and square (+0.064) carry it, line is marginal (+0.026),
and circle is flat-to-negative (-0.008).

**I was wrong about why it would help.** When restarting this sweep I predicted that
O1 would reduce the overshoot, on the reasoning that the end of the episode is where
the overshoot happens and O1 tells the agent the end is coming. **The data says no:**
mean overshoot change +0.001, 5/12 pairs, t=0.11 — completely flat. Whatever O1 is
doing, it is not fixing the overrun. That question stays entirely with
`rl/overshoot_ablation.py`. Recording the failed prediction because it was the stated
reason for spending 40 minutes of compute on a restart — the restart was still correct
(the metric was needed to *test* the claim), but the claim itself did not survive.

O1 also does **not** reduce wandering: `path_ratio` moved the wrong way on balance
(+1.0, t=0.90), and on the square it roughly doubled (2.68 -> 6.19) while the IoU
improved. So the agent is drawing better *and* travelling further, which is a
reminder that path_ratio and IoU measure genuinely different things.

**No variance claim.** Seed spread narrowed on square (0.044 -> 0.011) and triangle
(0.067 -> 0.021) but widened on line (0.008 -> 0.037) and circle (0.032 -> 0.050).
Two up, two down: nothing to claim.

**Decision:** keep `time_in_obs` available, leave the default **off** for now. It is
not free — it changes the observation shape, invalidating every saved 3-channel model
— and a +0.04 effect does not justify breaking compatibility until the overrun work
settles, since the overrun costs 0.064 and may interact with it.

#### A bug in this entry's own analysis, found and fixed

The first verdict `o1_ablation.py` printed was **"no measurable effect"** — it compared
the mean change against the std of *all baseline runs pooled together*. That pooled
std (+/-0.052) contains the shape-to-shape spread (line 0.333 vs square 0.408) as well
as seed noise, so it is far too large a denominator and buried a real effect. Since
both arms share seeds, the correct test is **paired within (shape, seed)**, which is
what `_paired()` now does. Noted because the wrong number was on screen first and the
right one only appeared after asking why square and triangle looked so different from
the headline.

---

## 2026-09-03 — Two bugs of mine, found by review, and a round of corrections

Ran five parallel reviews (code review, stop-arm diagnosis, documentation audit, plus
dashboard and proposal updates) while the overshoot sweep was training. Two independent
reviews found the same critical bug. **Every claim below was re-verified directly before
being acted on** — the reviews are treated as leads, not as evidence.

### BUG 1 (critical) — the stop action was being paid the success bonus

`DrawEnv.step()` ended with `if terminated: reward += 2.0`, a bonus written for the success
condition `reward_iou >= done_iou`. When `allow_stop` was added, the stop action *also* set
`terminated = True` — so pressing stop collected the success bonus regardless of what was on
the paper.

Measured directly:

| action on step 1 | reward | terminated | IoU |
|---|---|---|---|
| move, stop=0 | **-0.0050** | False | 0.000 |
| move, stop=1 | **+1.9900** | True | 0.000 |

Worse, `done_iou = 0.60` is **never reached by any agent in this project** — the best
`peak_iou` anywhere in `results/` is 0.516 — so before `allow_stop` that branch was dead
code. Turning the flag on did not add a stop action to an unchanged reward; it converted a
never-firing bonus into **+2.0 collectable at step 1 on a blank canvas**. For scale, 2.0 is
0.20 IoU x `iou_weight`, about 43% of the entire return a fully-trained square agent earns.

**Consequence: the baseline and stop arms were optimising different reward functions**, so
the stop arm was never a one-variable ablation. Its collapse (6–15 step episodes, square
0.465 -> 0.266) was **bought, not learned**, and the "stops too early" verdict my own
aggregator printed was unfalsifiable — the reward paid for exactly that behaviour.

**Fix:** separate the success condition from the termination flag.
```python
reached = reward_iou >= self.done_iou
terminated = reached
if self.allow_stop and float(action[3]) > 0.5:
    terminated = True        # a real end of episode, but no success bonus
...
if reached:                  # <- the bonus is gated on SUCCESS, not on ending
    reward += 2.0
```
Verified: stop now returns -0.0067, identical to not stopping. The three affected `stop` rows
were deleted from `results/overshoot_ablation.jsonl` and the arm re-run. **No previously
published number is affected** — the bug could only fire with `allow_stop=True`, which
existed for one day and only in this ablation.

### BUG 2 — `target_perimeter_px` under-measured every closed shape by ~1.9x

`target_perimeter_px` traced the target with `RETR_EXTERNAL` and halved the result, on the
reasoning that a thick stroke's contour walks both sides of the band. That is true for the
**line** (a solid bar) but wrong for every closed shape: a circle/square/triangle outline is
an *annulus*, and `RETR_EXTERNAL` returns only its outer edge, discarding the inner hole.

Measured against the analytic centreline at res=512:

| shape | EXTERNAL/2 (old) | LIST/2 (new) | true centreline | old ratio | new ratio |
|---|---|---|---|---|---|
| line | 332.0 | 332.0 | 307.0 | 1.08 | 1.08 |
| circle | 536.2 | 1020.1 | 961.3 | **0.56** | 1.06 |
| square | 639.0 | 1219.8 | 1228.0 | **0.52** | 0.99 |
| triangle | 549.6 | 1028.7 | 993.5 | **0.55** | 1.04 |

`RETR_LIST` replaces a per-shape error (0.52–1.08x) with a uniform ~1.04x bias.

**Consequence:** `path_ratio` was inflated ~1.9x on the three closed shapes and correct on
the line — so **every cross-shape path_ratio comparison in this log was comparing two
different normalisations.** The headline "the trained square agent has path_ratio 3.03 — the
pen travelled three times the outline" is wrong; corrected, **it is 1.59**.

Because only the denominator was wrong and it is a deterministic function of the target, the
recorded values were converted exactly rather than re-run (`new = old x old_perim/new_perim`;
line x1.000, circle x0.526, square x0.524, triangle x0.534). All result files were rewritten
in place with a `path_ratio_rev: 2` marker; the originals are in
`results/_pre_perimeter_fix/`.

**This weakens, but does not overturn, the zig-zag finding.** A square path_ratio of 1.59
still means the pen travelled 59% further than tracing the outline once requires, and the
per-shape *direction* of every comparison is unchanged (the rescale is a constant per shape).
What is no longer supportable is the "three times" phrasing and any line-vs-loop comparison
of path_ratio made before today.

### Why the stop arm also needed a policy-side fix

Even with the bonus removed, an untrained stop head is a trap. At init the head's output is
~0 and the policy is a unit Gaussian, so ~31% of samples clear the 0.5 threshold — measured
**mean untrained episode length 3.9 steps**. Tracing a closed shape takes ~27–35 steps at
`step_size=0.014`, so the probability of ever *seeing* a completed shape is ~1e-5 to 1e-7 per
episode. The policy locks into stopping before it can learn that finishing pays.

`train_eval(stop_bias=-2.0)` sets the stop head's initial bias, dropping the per-step stop
probability to ~0.6%: **measured mean untrained episode length 86.9 steps**. It is a declared
prior on the policy, not an environment change, and it is reported as one — the head remains
free to learn to stop. Default is `-2.0` for the ablation, exposed as `--stop-bias`.

### A third fix, small but a genuine confound

`smooth_penalty` was `mean|action - prev_action|` over *all* action dims. With `allow_stop`
that is 4 dims instead of 3, making dx/dy smoothing **25% weaker in the stop arm** and
charging the stop head for its own exploration jitter. Now averaged over `action[:3]` always
— bit-identical for every 3-dim run (re-verified: `ppo_square_kin.zip` still reproduces IoU
0.4704 / peak 0.5040), and scale-invariant across arms.

### Documentation corrections (audit, each independently re-verified)

| claim | where | verdict |
|---|---|---|
| "perceived IoU **never** runs ahead of true" | README | **False.** Perceived exceeds true in **51.1%** of the 3328 episodes (line 14.4%, circle 50.6%, square 83.7%, triangle 55.9%). The -0.0001 mean is a *cancellation across shapes*, not an absence of positive gaps. |
| "**every** shape's error bars overlap" | README + 12 Aug entry | **False on two of four.** line truth [0.3253,0.3410] vs vision [0.2992,0.3247] — disjoint. triangle [0.3205,0.4538] vs [0.2819,0.3114] — clearly separated, not "barely touch". |
| "0.028 < seed std (+/-0.05–0.06)" | 12 Aug entry + README | **Wrong denominator** — the same pooled-vs-paired error this log diagnosed for O1. +/-0.052 is the std of all 12 runs, pooling shape-to-shape spread; per-shape seed sds are 0.008–0.067. Paired within (shape, seed): **mean -0.0280, sd 0.0680, t = -1.43 on 11 df, vision ahead in 5/12**. The conclusion survives; the stated justification did not. |
| "whether this biases H2 is **under test**" | README | **Untested.** `overshoot_ablation.py` hard-codes `MODE = "truth"` and cannot answer it; `h2_seeds.jsonl` has no `peak_iou` field. The named test — re-run H2 logging peak IoU — has not been run. |
| "the camera arm loses twice as much" | README | Stated as fact; it is n=1 on the 400k single-run models. The log flags it as a hypothesis; the README quoted it without the caveat. Now carries it. |
| "no systematic direction" in the H3 gap | 23 Aug entry | **Too strong.** Within a shape the sign is highly consistent (line negative in 86% of episodes, square positive in 84%); only the cross-shape average cancels. The square's gap also *rises* over training (+0.0030 -> +0.0078), meeting the "rising trend" half of the exploitation rule while failing its 0.02 magnitude bar. |

Corrected in `README.md`. The H3 claim stands — no exploitable drift, max |gap| 0.029 — but
it is now stated as "no exploitable drift", not "never runs ahead", and the per-shape
structure is reported rather than averaged away. It should be re-checked under domain
randomisation, where the square's rising trend has more room to matter.

### Still outstanding from the review, not yet acted on

- **Resume keys ignore the run configuration.** All three sweeps key on `(shape, arm/mode, seed)` and skip on that alone, so changing `--timesteps` or `--max-steps` would silently reuse old results under a new banner. Not yet triggered (every sweep so far used the same settings) but it is the most likely way a future config change corrupts a result file.
- **Population vs sample std.** The aggregates print `np.std` (ddof=0) over 2–3 seeds while `_paired()` uses ddof=1 — two conventions in one document.
- **`overshoot_ablation.py` still uses the pooled denominator** that `o1_ablation.py` documents as wrong, and has no paired analysis despite its arms sharing seeds.
- **`plateau_patience` has no grace period**, so the plateau arm trains on ~6x shorter episodes from step 1; any "recovered sample budget" effect is confounded with a shorter exploration horizon.
- **`overrun.py`'s idle-%** divides by the configured `max_steps` rather than the actual episode length — correct today only because `done_iou` never fires.

### OVERSHOOT ABLATION RESULT — the environment fixes it, the agent does not

24 runs, 4 shapes x 2 seeds x 3 arms x 200k steps, ground-truth reward, identical
protocol on every arm. Run after the +2.0 stop-bonus bug was fixed, with the stop head
initialised at bias -2.0 (a declared policy prior; see the bug entry above).

| shape | arm | IoU | peak | overshoot | steps | path_ratio |
|---|---|---|---|---|---|---|
| line | baseline | 0.331 +/-0.003 | 0.359 | 0.028 | 240 | 13.19 |
| line | **plateau** | **0.400 +/-0.052** | 0.425 | 0.025 | 40 | 2.89 |
| line | stop | 0.358 +/-0.016 | 0.359 | 0.001 | 13 | 1.89 |
| circle | baseline | 0.333 +/-0.020 | 0.377 | 0.044 | 240 | 4.04 |
| circle | **plateau** | **0.443 +/-0.006** | 0.445 | 0.002 | 51 | 1.16 |
| circle | stop | 0.373 +/-0.034 | 0.373 | 0.000 | 18 | 0.83 |
| square | baseline | 0.438 +/-0.027 | 0.478 | 0.040 | 240 | 1.77 |
| square | **plateau** | **0.461 +/-0.018** | 0.462 | 0.001 | 71 | 1.45 |
| square | stop | 0.379 +/-0.004 | 0.379 | 0.000 | 30 | 1.21 |
| triangle | baseline | 0.409 +/-0.031 | 0.431 | 0.022 | 240 | 6.56 |
| triangle | plateau | 0.428 +/-0.036 | 0.435 | 0.007 | 39 | 1.02 |
| triangle | **stop** | **0.498 +/-0.018** | 0.498 | 0.000 | 27 | 1.01 |

Balanced over the 8 (shape, seed) cells where all three arms ran:

| arm | IoU | peak | overshoot | steps |
|---|---|---|---|---|
| baseline | 0.378 +/-0.056 | 0.411 | 0.034 | 240 |
| **plateau** | **0.433 +/-0.043** | 0.442 | **0.009** | **50** |
| stop | 0.402 +/-0.064 | 0.402 | 0.000 | 22 |

**Paired against baseline, within (shape, seed):**

| arm | ΔIoU | t | pairs up | Δpeak | Δovershoot | Δsteps | verdict |
|---|---|---|---|---|---|---|---|
| **plateau** | **+0.055** | **+2.56** | **7/8** | +0.030 | -0.025 | -190 | **fixes it** |
| stop | +0.024 | +0.96 | 5/8 | -0.009 | -0.033 | -218 | inconclusive |

**`plateau` is the result.** It raises IoU in 7 of 8 paired runs, cuts the overshoot from
0.034 to 0.009, *raises* peak IoU (+0.030, so it is not trading quality for brevity), and
does it in **50 steps instead of 240**. Better drawings, in a fifth of the episode.

**`stop` is not.** With the reward bug fixed it no longer collapses (circle 0.303 -> 0.373,
square 0.266 -> 0.379 against the buggy run), but its IoU gain is +0.024 at t=0.96 with 5 of
8 pairs — noise. Its overshoot is 0.000 for an uninteresting reason: it stops at step 22, on
average, before there is anything to overshoot. Peak IoU is *down* 0.009. The one real
success is the triangle (0.498 vs 0.409 baseline, best cell in the table); everything else
is flat or worse.

#### The prediction I got wrong, again — and the distinction that explains it

The Stage 1b entry above states plainly: **"the overshoot can only be fixed by the policy
itself"**, on the reasoning that a plateau detector is lagging and only the agent knows the
moment it finished. The ablation refutes it. The **environment-side** arm won; the
**policy-side** arm did not.

The original reasoning was not wrong, it was *scoped* wrongly. It was measured by replaying
an already-trained baseline agent with the detector switched on at evaluation. For a **frozen**
policy it is exactly right: the overshoot is already drawn before "no improvement" is
observable, and no patience value recovers it (240 -> 51 steps, IoU unchanged at 0.470).

But when the detector is present **during training**, nothing needs to be caught. The agent
never learns to overshoot, because the episode ends before wandering is ever rewarded or
practised. *Evaluation-time filter* and *training-time condition* are different
interventions, and I quoted a result about the first as if it settled the second.

#### An honest confound, not yet controlled

At a fixed 200k timesteps, the plateau arm's ~50-step episodes give it roughly **4.8x more
episodes** than the baseline's 240-step ones. So "the recovered sample budget helped" is
confounded with "a shorter exploration horizon helped" and with "more terminal transitions
per update helped". Separating them needs a fourth arm — `plateau_patience` with a grace
period, or a plain `max_steps=50` baseline — and that has not been run. **The effect is
real; the mechanism is not established.**

Also n=2 seeds, not the 3 used elsewhere, so t=+2.56 on 8 pairs is supportive rather than
decisive.

#### What this changes

- **`path_ratio` collapses too** — baseline line 13.19 -> plateau 2.89, circle 4.04 -> 1.16,
  triangle 6.56 -> 1.02. The wandering that `path_ratio` was added to detect is mostly a
  symptom of episodes running long past completion, not of a fundamentally jerky policy.
- **The overrun costs more than H2's headline gap, and is now largely fixable.** Whether the
  original H2 comparison is biased by it remains **untested** — that needs the H2 sweep
  re-run with peak IoU logged, which is still the single most decision-relevant experiment
  outstanding.
- Figure: `output/results_overshoot.png` (grey caps show IoU lost to the overshoot; they are
  visible on every baseline bar and nearly absent on plateau and stop).

---

## 2026-09-06 — `rl/watch.py`: a way to actually *see* the thing run

### Why this exists

Everything in `rl/` up to today either trains, measures or plots. There was no way to simply
**watch** a trained agent draw — the only visual evidence in the repo was a still PNG at the
end of an episode (`output/trained_*_after.png`) and the sim/ demo scripts, which run
hand-written paths and know nothing about the agents. To see what a policy actually *does* I
had to read a trace plot and imagine it.

That matters beyond convenience. The two facts this project has to explain to anyone — the
camera-perceived drawing is a degraded version of the real ink (H2), and the agent finishes
its shape early then wanders over it (the overrun) — are both **temporal**. A final-frame PNG
hides both of them by construction. They are obvious in one second of watching.

### What it does

`rl/watch.py` replays the **deterministic evaluation episode** (`DrawEnv` kinematic, fixed
start, `deterministic=True`, seed 1000 — exactly what `train.py::evaluate` runs) and renders
it live:

- three panels — **TARGET** | **LIVE DRAWING** (the true ink) | **CAMERA SEES**
  (`env._perceive(canvas)`, the only signal a vision-reward agent is paid on);
- a HUD with step, true IoU, **peak IoU so far**, and the running difference;
- a per-step IoU plot with the peak drawn behind it, so the overrun is visible as the blue
  line falling away from the grey one — the same effect `rl/overrun.py` measures offline;
- optionally (`--view arm/both`) a PyBullet GUI window where the KUKA arm traces the same
  path on the textured paper.

`--save` writes an mp4 plus **both** the final and the peak-IoU drawing into `output/watch/`
(git-ignored — reproducible, not a result). `--random` replays an untrained policy for the
"before" picture. `--list` shows which agents are on disk.

### Decisions worth recording

- **The 3D arm is a mirror, not the environment.** The natural implementation is
  `DrawEnv(use_arm=True)` with the PyBullet client switched to GUI. I did not do that. The
  models in `models/` were all trained with `use_arm=False`, and running them through the arm
  backend changes the pen positions (IK lag, `_move_arm` returns the achieved tip, not the
  commanded one) — so the drawing on screen would no longer be the drawing the README
  reports. Instead `ArmView` reads `env.pen_xy` after each step and drives its own separate
  PyBullet client there. Nothing flows back. The episode is byte-identical whether the 3D
  window is open or closed, which is the property that makes the viewer safe to show people.
- **`draw_env.py` was not touched.** A viewer that needed a flag in the environment would put
  a display concern inside the file every recorded number depends on. Zero edits there means
  zero chance of this changing a result.
- **`--plateau-patience` defaults to 0 (off).** Ending on the plateau makes the drawings look
  clearly better (2026-08-23: +0.055 IoU), and it was tempting to make that the default so
  demos look good. Off is the honest default: what you watch is what the tables report. The
  flag is there to *show* the difference on request.
- **The HUD shows peak next to final on purpose.** Every number this project has published is
  the final one. Putting the peak beside it, live, keeps the known measurement caveat in view
  instead of letting a nice-looking video quietly bury it.
- **Texture refresh writes a unique filename per frame** (`output/_watch_tex/tNNNNNN.png`,
  cleaned up on exit). Re-using one path silently freezes the paper at frame 1 —
  `p.loadTexture` caches by path. Same trap as B5; documented there, re-hit here.

### The shortcut

`watch.bat` at the project root: double-click it and a small menu asks shape / which agent /
2D or 3D / record. It resolves the `robosketch` environment itself (checking the known conda
locations and `%ROBOSKETCH_ENV%`) and prepends `env;Library\bin;Scripts` to PATH the way
`conda activate` does — calling the env's `python.exe` without that fails, because pybullet
and OpenCV load DLLs out of `Library\bin`. Any arguments given are passed straight through to
`rl/watch.py`, so the menu is a convenience, not a wrapper to work around. A desktop shortcut
points at it.

### Sanity check (headless, `--no-window --save`, the four 400k single-run truth agents)

| shape | final IoU | peak IoU | overshoot |
|---|---|---|---|
| line | 0.505 | 0.552 | −0.047 |
| circle | 0.357 | 0.409 | −0.053 |
| square | 0.470 | 0.504 | −0.034 |
| triangle | 0.468 | 0.507 | −0.039 |

Consistent with `rl/overrun.py` (mean 0.064 lost on these same models) — same direction, same
order of magnitude, which is the check that matters: the viewer is reading the environment
correctly and is not a second, divergent evaluation path.

### Statistics housekeeping (2026-09-03, later) — and a correction to a correction

The aggregates printed `np.std` with `ddof=0` while `o1_ablation._paired` used `ddof=1` —
two conventions in one document. Every `+/-` in these scripts is estimated from 2–3 seeds,
so it is a sample statistic; all of them now go through a shared `_sd()` helper using
`ddof=1` (with an `n<2` guard). The H2 headline moves from `0.382 +/-0.052 / 0.354 +/-0.063`
to `0.382 +/-0.054 / 0.354 +/-0.066`. No conclusion changes.

**But one of this morning's corrections does.** The audit found the claim "every shape's
error bars overlap" to be false on the line and the triangle, and the README was corrected
to say those two are disjoint. That was computed with the *population* std. Under the sample
std — the correct convention, now adopted — **all four shapes overlap again**:

| shape | population sd (ddof=0) | sample sd (ddof=1) |
|---|---|---|
| line | [0.325,0.341] vs [0.299,0.325] → **disjoint** | [0.324,0.343] vs [0.296,0.328] → overlap |
| triangle | [0.321,0.454] vs [0.282,0.311] → **disjoint** | [0.306,0.469] vs [0.279,0.315] → overlap |

So the original 2026-08-12 claim was right, my correction of it was wrong, and both were
resting on the same weak foundation: **at n=3 the overlap test flips on the choice of
denominator.** It should not have been the basis of the claim in the first place. The README
now says so explicitly and leans on the paired test, which is unaffected either way
(mean -0.0280, sd 0.0680, t=-1.43 on 11 df, vision ahead in 5/12).

Also fixed from the review: `overrun.py` computed its idle-% against the configured
`max_steps` rather than the episode actually run — correct today only because `done_iou`
never fires, wrong the moment an episode ends early.

### A reproducibility limit worth knowing — seeded runs are not thread-invariant

The H2 re-run (with `peak_iou` logged) was sharded across two processes with
`OMP_NUM_THREADS=1` so two workers could share two cores. Its first cell,
line/truth/seed 0, came out **IoU 0.302** where `h2_seeds.jsonl` records **0.3337** and the
O1 ablation had reproduced **0.334** exactly a few days earlier.

That looked alarming — a possible sign that one of the day's fixes had moved the baseline
after all. It had not. Tested directly, training the same seeded cell for 10k steps:

| torch threads | IoU |
|---|---|
| 2 (default) | 0.175000 |
| 1 (`OMP_NUM_THREADS=1`) | 0.194986 |

**The thread count changes the result of a seeded run.** Fewer threads changes the order of
floating-point reductions, which changes the gradients, which changes the policy. The env
dynamics were already proven untouched (`ppo_square_kin.zip` still replays to IoU 0.4704
exactly), so the divergence is entirely in training.

Consequences, and what was done:

- `torch_threads` is now recorded in every `experiment.py` result row. Runs are only bitwise
  comparable to runs carrying the same value. The four rows already collected were annotated
  (they ran under `OMP_NUM_THREADS=1`) rather than discarded.
- **The O1 ablation's reproduction of the baseline to three decimals was real** — it ran with
  default threads, matching the published sweep. That check stands.
- **The H2 peak-vs-final test is unaffected.** It compares two scoring points *within the same
  runs*, so any consistent thread setting answers it. What the sharded sweep cannot also serve
  as is a bitwise re-check of the published numbers; `h2_peak_analysis.py` now says so instead
  of reporting the difference as if it were a defect.
- General lesson for the paper's reproducibility statement: quoting a seed is not enough.
  Thread count belongs in the reported configuration alongside the seed and the library
  versions.

Separately: shard A died mid-run with **exit code 4 and no traceback** — the same
tracebackless crash recorded twice before in this log (2026-08-12). Two completed runs were
preserved by the resume logic. Still unexplained; still looks like a process/memory fault
rather than anything in the code.

### Review items closed (2026-09-03, later)

- **Config drift on resume.** All three sweeps key resume on `(shape, mode/arm, seed)` and
  ignore the run configuration, so `--timesteps 500000` against a file built at 200k would
  print "0 to go" and summarise the old numbers under the new banner. `warn_config_drift()`
  (in `experiment.py`, used by all three) now scans the loaded records and prints a loud
  warning naming the field, the recorded values and the requested one. Verified: asking for
  999 steps against the O1 file correctly reports "24 recorded run(s) have [200000]". It
  warns rather than refuses, because reusing old runs is sometimes what you want - but it can
  no longer happen silently.
- **Sample vs population std** - unified on `ddof=1` via a shared `_sd()` helper (see above).
- **`overrun.py` idle-%** - now divides by the episode actually run, not the configured cap.
- **`experiment.py` `_figure` dead ternary** - both branches were identical; left as is, it is
  cosmetic and the figure is correct.

Still open from the review: `plateau_patience` has no grace period, so the plateau arm trains
on ~5x shorter episodes from step 1 and its win is confounded with a shorter exploration
horizon (needs a fourth arm to separate); `h3_exploitation._Axes.band` compounds its alpha
across series (cosmetic); sparse bins are dropped silently in the H3 binning.

### H2 PEAK-vs-FINAL RESULT — the overshoot does not bias the comparison ✅

The single most decision-relevant question outstanding: **is the H2 truth-vs-vision gap partly
an artifact of measuring after the agents overshoot?** Answered by re-running the full H2
sweep (4 shapes x 2 reward modes x 3 seeds x 200k steps = 24 runs) with `peak_iou` recorded
alongside `iou`, into `results/h2_peak*.jsonl`. The published `h2_seeds.jsonl` was not touched.

**The gap, paired within (shape, seed):**

| scored | mean gap (vision - truth) | sd | t | vision ahead |
|---|---|---|---|---|
| at the **END** (what H2 reports) | **+0.0128** | 0.0775 | +0.57 | 8/12 |
| at the **PEAK** (before either arm overshot) | **+0.0020** | 0.0646 | +0.11 | 8/12 |

Moving the measurement point changes the gap by **-0.0108**, comfortably inside the gap's own
standard error (0.0224). **The overshoot does not materially bias the H2 comparison. H2 stands
as reported.**

**The hypothesis that motivated this run is refuted.** From the n=1 400k models it looked as
though the camera arm lost about twice as much to the overshoot as ground truth (0.085 vs
0.043), which would have meant the reported gap flattered ground truth. At n=12 it does not
replicate, and if anything points the other way:

| arm | mean overshoot |
|---|---|
| ground truth | 0.0330 |
| camera | **0.0222** |

Paired difference (camera - truth) **-0.0108, t=-1.37**, with the camera losing more in only
**4 of 12** cells. Not significant in either direction - but the specific worry that prompted
this experiment is gone. Recorded as a refuted hypothesis, and worth noting that it was
labelled "a hypothesis, not a result, and must not be quoted as one" when it was first
written down. That labelling did its job.

#### The finding that is actually more interesting than the one we went looking for

This is the **second independent 24-run H2 sweep**, and the sign of the gap flipped:

| sweep | mean gap (vision - truth) | t | vision ahead |
|---|---|---|---|
| published (12 Aug) | **-0.0280** | -1.43 | 5/12 |
| this one | **+0.0128** | +0.57 | 8/12 |

Neither reaches significance, and they disagree on *which arm is better*. Two independent
sweeps landing on opposite signs with |t| < 1.5 is a stronger statement of
"indistinguishable" than either sweep alone - it demonstrates the difference is not a stable
quantity at this sample size, rather than merely failing to prove one exists.

The per-cell table shows why: seed noise dwarfs the effect. The circle alone swings from
**-0.127** (seed 0) to **+0.159** (seed 2); the triangle from **-0.106** to **+0.076**. Any
claim about a 0.028 mean gap drawn from three seeds is reading tea leaves.

#### Why the two sweeps do not reproduce cell-by-cell (and why that is fine)

Mean |difference| between the sweeps is 0.0713 per cell, max 0.176. This is **not** evidence
that something in the pipeline moved. The new sweep ran with `OMP_NUM_THREADS=1` (to fit two
concurrent workers on a 2-core machine); the published sweep ran on the default 2 threads.
**A seeded PPO run is not reproducible across thread counts** - floating-point reduction order
in the BLAS backend differs, so the gradients differ in the last bits and the trajectories
diverge. Measured directly: the same cell scores IoU 0.175 on 2 threads and 0.195 on 1.

`h2_peak_analysis.py` prints this caveat itself so the comparison cannot be misread later, and
records `torch_threads` per run. **The peak-vs-final test is internal to a single sweep**, so
it is unaffected by any of this - both arms in every pair ran under identical conditions.

**Lesson for the write-up:** "same seed" is not "same result" unless the thread count, BLAS
backend and library versions are also pinned. Every results file should record them; this one
now records `torch_threads`.

#### Status of the overshoot work

- The overshoot is **real** (mean 0.064 IoU on the 400k models, 0.033/0.022 here).
- It is **largely fixable** - ending the episode on a plateau gives +0.055 IoU in 7/8 paired
  runs at a fifth of the steps.
- It does **not** bias H2, so it is a quality-and-efficiency improvement rather than a
  correction to the headline result. That closes it as a threat to validity.

---

## 2026-09-12 — Stage 2: perception domain randomisation (proposal 4.1)

H2 says a camera reward matches a ground-truth reward. But it was measured with
`_perceive()` = a fixed `resize(150px) + threshold(>60)` - one camera, and an
optimistic one. That makes H2 a claim about a sensor, not about cameras. `rl/perception.py`
samples the camera instead (Tobin et al., IROS 2017).

**What is randomised**, in the order a real imaging chain applies it: paper tone, ink
contrast, camera pose (perspective warp), sensor resolution, defocus blur, exposure gain,
sensor noise, and the binarisation threshold.

**Two disjoint distributions.** `TRAIN` is what the agent learns under; `HELDOUT` sits
outside it on every axis. Measured recovery of the true ink (perceived-vs-true IoU, 40
sampled cameras on four real canvases):

| camera | perceived-vs-true IoU |
|---|---|
| fixed (the old one) | 0.834–0.839 |
| train | 0.761–0.778 |
| heldout | **0.414–0.460** |

#### Three things that had to be got right before any of it means anything

**1. The threshold cannot be an absolute grey level.** The first version sampled a threshold
in grey levels (45–90), copying the old fixed `>60`. That is incoherent once paper tone, ink
contrast and gain move the levels around: with `ink_contrast=0.75` the ink sits at grey 64,
so a threshold of 45 is *below the ink* and detects nothing at all. It is now a **fraction**
between the ink level and the paper level as the sensor sees them (after gain), which is what
any real pipeline does. Gain therefore no longer destroys detection - it degrades the
signal-to-noise ratio, which is the physically right consequence.

**2. The camera must be resampled per EPISODE, never per step.** The reward is
`iou(t) - iou(t-1)`. A camera that changed between two steps would put camera noise into that
difference, and the agent would be rewarded and punished for things it did not do. A real
camera does not change mid-episode either.

**3. The held-out camera has to be a worse camera, not a broken one.** The first `HELDOUT`
ranges recovered only **0.22–0.27** of the true ink. A sensor that bad would be replaced, not
trained around, and every arm would score ~0, so the comparison would measure nothing. The
ranges were widened on that physical argument - target ~0.45–0.60, achieved 0.41–0.46 - and
this was fixed **before any agent was trained on it**, not tuned afterwards to make a result
come out. The achieved value is reported rather than the target that was aimed at.

#### The design flaw the smoke test found — in the proposal as much as in the code

The first end-to-end run gave **byte-identical results under all three evaluation cameras**.
The cause is architectural: the camera was attached only to the **reward**, while the agent's
observation was the **true canvas**. At evaluation there is no reward, so the camera had no
causal path to anything. "Test the policy on a held-out camera" was measuring nothing at all.

Proposal §4.1 specifies exactly that measurement ("True IoU of vision-trained agents under
(a) the training camera, (b) held-out camera conditions"), so the flaw was in the plan, not
only in the implementation. It survived the literature review because nobody checked whether
the quantity was *reachable* in this architecture.

**The fix is also the more honest setup.** When `cam_split` is set the agent now SEES its
drawing through the camera as well - which is what a real robot has. It has no privileged
access to the ink it laid down; it only has the photograph. `cam_split=None` keeps the old
privileged observation, so every earlier result is untouched.

Verified after the fix - the observation's drawn-channel now diverges from the true canvas in
exactly the expected order, and a trained policy produces genuinely different drawings per
camera:

| eval camera | mean abs difference from a true-canvas observation | true IoU over 4 episodes |
|---|---|---|
| fixed | 2.22 | 0.464 0.464 0.464 0.464 |
| train | 4.00 | 0.423 0.442 0.396 0.442 |
| heldout | 10.21 | 0.394 0.432 0.465 0.469 |

The per-episode variation under `train`/`heldout` is the camera resampling; `fixed` is
deterministic and repeats, which is also the reason `eval_eps > 1` is meaningful here for the
first time in this project (everywhere else the evaluation is fully deterministic, so the 8
episodes were one episode eight times - see the 2026-08-23 protocol finding).

**Consequence for the write-up:** this experiment is a NEW setup, not a continuation of the
H2 numbers. Those had a privileged true-canvas observation with only the reward degraded.
The `fixed` arm here is the closest comparison but is still not the same experiment.

#### Cost

`perceive()` runs every step, and both the reward and the observation need it, so it is cached
against the step counter - once per step, not twice. Measured per call: fixed 98 us, train 641
us, heldout 327 us, against 77 us for the old model. At 200k steps the randomised arm pays
roughly 2 extra minutes per run, which is acceptable.

**Harness:** `rl/dr_experiment.py` - three training arms (`truth` control / `fixed` / `train`)
x four shapes x seeds, each evaluated under all three cameras, always scored on TRUE IoU so a
policy is never credited for a camera that happens to flatter it.

### Pre-run review of the perception model — six fixes before spending the compute

A review was run against `perception.py` and the `cam_split` wiring *before* launching the
sweep, on the reasoning that a bug found now costs minutes and a bug found afterwards costs
the whole run. It paid for itself. (Two of its findings - that the evaluation camera had no
causal path to the score, and that all eval episodes were therefore identical - were the flaw
the smoke test had already turned up and the observation fix above had already closed; the
review read the pre-fix file. The rest were new.)

| # | finding | status |
|---|---|---|
| **F5** | `TRAIN` and `HELDOUT` **overlapped** on `thresh_frac` ([0.45, 0.46]), while three places in the codebase assert they are disjoint on every axis | fixed: heldout now (0.28, 0.43); all 8 axes verified disjoint |
| **F4** | the perspective warp accounted for **56% of all degradation** - and it models an *unrectified* sheet, which the deployed pipeline is not (`sim/04_camera_capture.py` validates corner registration) | warp reduced to a **residual** registration error (train 0–1.5 px, heldout 2.0–3.0 px); it now accounts for ~13% |
| **F9** | `scale_px` ran to 190 against a 128-px canvas, so **78% of training draws were UPSAMPLES** - no resolution loss at all, while every held-out draw was a genuine downsample. The two splits differed qualitatively, not in degree | capped at the canvas resolution: train (96, 128), heldout (76, 92) |
| **F7** | `BORDER_REPLICATE` smeared an ink pixel touching the canvas edge into a stripe along the whole border - **+34-39% phantom ink** | `BORDER_CONSTANT` at the paper level: outside the sheet a camera sees paper, not more ink |
| **F11** | no sensor saturation, so a gain **above** 1 widened the ink-paper separation against fixed noise and *improved* SNR - the opposite of an over-exposed photograph | clipped to [0, 255] after gain and noise |
| **F13** | `sample_params` falls through to HELDOUT for any string that is not exactly `"fixed"` or `"train"`, so `"Train"` would have trained an arm on the held-out distribution with no error | `assert cam_split in (None, "fixed", "train", "heldout")` |

Also acted on: **F6** - `PPO(seed=k)` makes SB3 reseed the vector envs to `k + i`, overwriting
the per-env seeds the harness passes, so run seeds 0 and 1 would have shared **7 of 8** camera
streams and the paired statistic would have had understated variance. The sweep uses
`--seeds 0 100`.

### Calibration, measured rather than asserted (`rl/perception_calibration.py`)

Ink recovered from a **perfect** drawing - the upper bound, since a real canvas can only do
worse. Per shape, because the shapes are not equally hard:

| shape | fixed | train | heldout |
|---|---|---|---|
| line | 0.665 | 0.745 | **0.284** |
| circle | 0.820 | 0.734 | 0.349 |
| square | 0.995 | 0.793 | 0.524 |
| triangle | 0.858 | 0.751 | 0.418 |
| **mean** | **0.834** | **0.756** | **0.394** |

**The held-out camera came out at 0.394, against the 0.45-0.60 I set as the criterion.** The
ranges were adjusted three times and are now left alone: continuing to turn the knob until
the number lands inside a target I chose myself is how a calibration becomes a result. The
achieved value is reported, not the intended one.

The shortfall is concentrated on the **line**, and that is a real property rather than a bad
setting: the *fixed* camera only recovers 0.665 of a perfect line either. A 14-px stroke at
res 512 is ~3.5 px at 128, and downsample-plus-threshold thins it. Pooling the four shapes
would hide this, so the table is per shape.

### Which axes actually do anything

Single-axis ablation from the fixed camera (square target, 40 cameras per cell):

| axis | at train midpoint | at heldout midpoint |
|---|---|---|
| scale_px | 0.843 | **0.560** |
| warp_px | 0.901 | 0.731 |
| blur_sigma | 0.992 | 0.712 |
| gain, ink_contrast, paper_tone, thresh_frac, noise_sd | 0.995 | 0.995 (inert) |

**Five of the eight axes move nothing measurable, and for three of them that is correct
physics rather than a defect.** The threshold is computed *from* the ink and paper levels as
the sensor sees them, so exposure, paper tone and ink contrast cancel by construction - which
is exactly what an auto-thresholding pipeline does in reality. Describing this as an "8-axis
camera distribution" would overstate it: the effect is carried by **resolution, blur and
residual warp**.

`noise_sd` reading as inert is a limitation of the *method*, not evidence it does not matter:
the ablation starts from the fixed camera, where ink and paper are 255 grey levels apart, so
noise of sd 13 is negligible. Noise bites in combination with low contrast, which a
single-axis ablation cannot show. Removing the warp from an all-heldout camera moves it only
0.387 -> 0.438, so no single axis now dominates the way the warp did.

Cost after the fixes: fixed 110 us, train 439 us, heldout 337 us per call (train was 842 us
before the `scale_px` cap).

**Sweep launched:** 3 arms x 4 shapes x 2 seeds = 24 runs, sharded across two workers.

### STAGE 2 RESULT — domain randomisation does not help, because there was nothing to fix

24 runs: 3 training arms x 4 shapes x 2 seeds x 200k steps, each evaluated under three
cameras, always scored on TRUE IoU (`results/dr_experiment*.jsonl`).

Balanced over the 8 (shape, seed) cells where all three arms ran:

| trained on | eval: fixed camera | eval: train camera | eval: **held-out** camera |
|---|---|---|---|
| truth (no camera at all) | 0.389 ±0.051 | 0.389 | 0.389 |
| fixed camera | **0.393 ±0.051** | 0.386 ±0.044 | **0.379 ±0.041** |
| randomised camera | 0.371 ±0.062 | 0.365 ±0.057 | 0.368 ±0.056 |

Per shape (mean ± sample sd across the 2 seeds):

| Shape | Trained on | eval:fixed | eval:train | eval:heldout | n |
|---|---|---|---|---|---|
| line | truth | 0.329 ± 0.038 | 0.329 ± 0.038 | 0.329 ± 0.038 | 2 |
| line | fixed | 0.349 ± 0.056 | 0.342 ± 0.008 | 0.334 ± 0.008 | 2 |
| line | train | 0.332 ± 0.026 | 0.324 ± 0.003 | 0.330 ± 0.006 | 2 |
| circle | truth | 0.434 ± 0.026 | 0.434 ± 0.026 | 0.434 ± 0.026 | 2 |
| circle | fixed | 0.397 ± 0.078 | 0.374 ± 0.065 | 0.380 ± 0.062 | 2 |
| circle | train | 0.371 ± 0.005 | 0.385 ± 0.023 | 0.373 ± 0.014 | 2 |
| square | truth | 0.425 ± 0.030 | 0.425 ± 0.030 | 0.425 ± 0.030 | 2 |
| square | fixed | 0.397 ± 0.004 | 0.408 ± 0.003 | 0.410 ± 0.002 | 2 |
| square | train | 0.425 ± 0.055 | 0.424 ± 0.055 | 0.429 ± 0.054 | 2 |
| triangle | truth | 0.369 ± 0.012 | 0.369 ± 0.012 | 0.369 ± 0.012 | 2 |
| triangle | fixed | 0.428 ± 0.054 | 0.420 ± 0.042 | 0.393 ± 0.041 | 2 |
| triangle | train | 0.355 ± 0.119 | 0.328 ± 0.075 | 0.340 ± 0.083 | 2 |

Paired, train arm minus fixed arm, within (shape, seed):

| evaluated on | mean | sd | pairs up | t |
|---|---|---|---|---|
| fixed camera | -0.022 | 0.058 | 3/8 | -1.09 |
| train camera | -0.020 | 0.055 | 2/8 | -1.05 |
| **held-out camera** | **-0.011** | 0.048 | 3/8 | **-0.67** |

**Randomisation buys nothing.** On the held-out camera it is 0.011 *behind* the fixed-camera
arm, at t=-0.67 with 3 of 8 pairs up - noise. It is not significantly worse either; it simply
makes no difference.

#### The reason is more interesting than the result

**Neither arm degrades much on the held-out camera**, and that is the finding:

- the fixed-camera agent drops only **0.014** (0.393 -> 0.379) moving to a camera it never saw
- the randomised agent drops **0.003**
- the truth agent, which has no camera, sits at 0.389

And the held-out camera is genuinely bad: `rl/perception_calibration.py` measures it
recovering **0.394** of a perfect drawing's ink, against 0.834 for the fixed camera. It loses
more than half the ink - and costs the policy 0.014 IoU.

So the premise behind proposal 4.1 - that H2's result might be an artifact of one idealised
camera - **does not hold**. The policy does not need a good picture of its drawing. It needs
to know roughly where it has already been, and even a camera that throws away half the ink
still carries that. Camera realism is not where the difficulty lives.

**This is a negative result worth having.** It removes a threat to validity the literature
review rated five stars, it says the project does not need to invest in camera realism, and
it means H2 was less fragile than feared. A reviewer asking "would this survive a worse
camera?" now has a measured answer instead of an argument.

**It also strengthens H2 in a harder setting.** In this experiment the camera is in the
OBSERVATION as well as the reward - the agent has no privileged view of its own ink, which is
the real robot's situation and a harder task than the original H2. Even so the camera arms
(0.393 / 0.371) sit level with the privileged truth arm (0.389). Taking the paper away from
the agent and handing it a photograph costs nothing measurable.

#### Honest limits

- n=2 seeds, 8 balanced cells. The paired t statistics are all under 1.1, so this establishes
  "no detectable effect", not "no effect".
- Absolute scores (0.37-0.39) sit below the ~0.45 of earlier sweeps because the task is
  harder here: perception now gates the observation, not just the reward. Do not compare these
  numbers to the H2 table.
- The randomisation is carried by three axes (resolution, blur, residual warp); five are inert
  by construction, as recorded above. A distribution that varied something the policy actually
  depends on might behave differently - though the held-out camera degrades exactly those
  three axes hard, and still barely moves the score.
- The reward in the randomised arm is noisier than in the fixed arm at the same sample budget
  (fresh sensor noise every step). If randomisation had *helped*, that confound would matter;
  since it did nothing, it only means the small negative gap may be a sample-efficiency cost
  rather than anything about robustness.

### Correction (2026-10-19) - a mislabelled drop in the DR aggregate, and a duplicate write-up

`rl/dr_experiment.py --aggregate` printed the fixed-camera arm's held-out drop against the
wrong column: "drop from its own training camera" used the TRAIN camera (`fi[1]`) for both
arms, but the fixed arm trained on the FIXED camera (`fi[0]`). It printed **+0.006**; the
true drop is **+0.014** (0.393 -> 0.379). The randomised arm's -0.003 was already right
(a "drop" of -0.003 is a 0.003 *gain*). Fixed in the script; the analysis above already used
the correct 0.014, so no conclusion changes.

A second write-up of the same sweep ("Stage 2 Sweep Results - All 24 runs completed", added
from another tool) had copied the buggy +0.006 and also read "drop" as "change", flipping
the meaning of -0.003. It duplicated the section above and has been removed; its per-shape
table, which appeared nowhere else, was moved into it. Numbers re-checked against
`--aggregate` output.

**Lesson recorded in `AGENTS.md`:** a number printed by a script is not verified just because
a script printed it - check what it is compared against.

## 2026-10-19 - Stage 3 begins: H4 disturbance recovery (design, pre-registered test, and an interim warning)

### Why this experiment exists
D01 (Lee et al., ICRA 2022) draws well with **no camera**, synchronising through forward
kinematics, and argues camera-free is an advantage. If a camera buys nothing, D01 is a
complete answer to this project's motivation. H4 asks the only question that can answer it:
**does an agent that sees the paper recover from errors that kinematics cannot see?**

### Design (`rl/h4_experiment.py`, `rl/disturb.py`, written 2026-09-13)
Three disturbances, each fired once per episode at 4-16% of the episode - *inside* the
drawing phase. (A first version fired at 20-55%; `rl/overrun.py` had shown agents finish in
the first ~10-17%, so every disturbance landed on a finished drawing and cost ~0.)
- `slip`: pen displaced 4-9 px, command stream unchanged.
- `paper_shift`: sheet moves 5-10 px under the pen; all later strokes land displaced.
- `ink_failure`: pen deposits nothing for 4-12% of the episode. Kinematics reports a
  perfect drawing - the error is invisible to FK **by construction**.

Four arms, same PPO settings as every other sweep (CnnPolicy, 8 envs, 200k steps):
- `open_loop`: analytic contour tracer, no feedback - the floor (a classical IK pipeline).
- `true`: observes the real ink. Privileged - the ceiling.
- `fk`: D01's condition - observes what its kinematics predict it drew.
- `camera`: ours - observes a photograph (FIXED camera, so this is about feedback, not
  camera realism; that was Stage 2).

All learning arms **train on `mixed`** (one of none/slip/paper_shift/ink_failure per
episode) and are scored on each kind separately, 10 episodes each. Training clean and testing
disturbed would measure brittleness; the question is about information, so every arm gets a
fair chance to learn to use what it can see. **Scoring is always true IoU.**

Reward asymmetry, recorded so it is not discovered later: `true` and `fk` are rewarded from
the TRUE canvas (`reward_mode` default `"truth"`); `camera` is rewarded from vision. The fk
arm therefore gets a privileged reward a real D01-style robot would also lack. **This biases
the comparison against the camera arm**, so a camera win would be conservative; a camera
loss must be read with it in mind.

Sweep: 4 shapes x 4 arms x seeds {0, 100} = 32 runs, sharded by shape.

### Interim warning - the script's verdict was measuring the wrong thing
At 18/32 runs (4 balanced cells) the aggregate reported "camera recovers better" on
`paper_shift` (camera - fk = +0.061, t = 2.45). **That comparison is confounded.** The camera
and fk arms do not start level: with **no** disturbance, camera already beats fk by +0.053
(0.386 vs 0.333). The absolute gap under disturbance (+0.059 to +0.061) is almost entirely
that clean gap. Subtracting it - how much each arm *loses* from its own clean score:

| disturbance | camera loses | fk loses | open-loop loses | diff-in-diff (camera better if > 0) | t (n=4) |
|---|---|---|---|---|---|
| slip | +0.008 | -0.021 | +0.268 | -0.030 | -1.01 |
| paper_shift | +0.041 | +0.049 | +0.306 | +0.007 | +0.30 |
| ink_failure | +0.025 | +0.031 | +0.013 | +0.006 | +0.38 |

Interim only - **no verdict at n=4**. Two things are already clear enough to act on:
1. The aggregate's verdict used the absolute difference. It now uses the paired
   difference-in-differences (below). The training code was not touched.
2. **`ink_failure` barely bites anyone** - open-loop, which cannot react at all, loses only
   0.013. A disturbance that costs nothing cannot show recovery. If this holds at n=8, a null
   on ink_failure says nothing about D01, and the disturbance needs re-sizing before the
   result can carry the argument. Likely cause to check: open-loop spreads its trace over
   all 240 steps, so a 10-29 step outage hides only a small part of its contour; the
   learning arms may re-cover blanked segments on their post-completion overshoot (H6).

Also noted: `fk` draws worse than `true` even with no disturbance (0.333 vs 0.390). If the fk
rendering matches the true canvas under `none` (not yet verified), the gap comes from
training: in the 3 of 4 training episodes that carried a disturbance, fk's observation
disagreed with the canvas its reward was computed from. That is itself a cost of
camera-free sync under disturbance, but it is not *recovery* and must not be reported as one.

### Premise check — the FK belief is *more* accurate than the camera, except when the paper moves (`rl/h4_premise.py`)

H4 rests on a premise that had never been measured: that the FK belief actually diverges from
the paper when a disturbance fires. Random actions, no training, so this measures the
**information in each channel**, not any policy's use of it. Compared at canvas resolution
(128x128) so the 64x64 observation downsample is not part of it, and reported both per pixel
and as a share of the ink actually on the paper — because mean-per-pixel understates a
*concentrated* error (a missing stroke is a handful of pixels out of 16384).

```
mean |observed - true paper| per pixel (0-255), n=8 episodes, random actions
               | fk belief             | camera
disturbance    |    per px    % of ink |    per px    % of ink
none           | 0.00+-0.00    0.0+- 0.0 | 2.50+-0.70   14.6+- 2.1
slip           | 0.44+-0.23    2.5+- 1.2 | 2.56+-0.78   15.1+- 2.1
paper_shift    | 13.55+-4.37   82.0+-22.5 | 2.58+-0.74   15.4+- 1.8
ink_failure    | 0.74+-0.33    5.0+- 3.0 | 2.50+-0.75   15.2+- 2.2
mixed          | 8.33+-7.10   54.8+-46.8 | 2.52+-0.61   15.2+- 1.4
```

**This contradicts the naive form of the premise.** By mean absolute pixel error the FK belief
is *closer* to the truth than the camera is on three of the four kinds: exactly right with no
disturbance (0.0%) against the camera's constant ~15%-of-ink sensor error; off by 2.5% under
`slip`; off by **5.0% under `ink_failure`** — the case built to be invisible to kinematics —
still well inside the camera's noise floor. Only `paper_shift` breaks FK, and breaks it
completely: 82% of the ink mass misplaced, because a shifted sheet displaces *every*
subsequent stroke rather than a few pixels.

So "the camera sees more" is **false as stated**. The honest version is about the *structure*
of the two errors, not their size:

- the camera's error is **large, diffuse and uninformative** — a constant haze, the same
  whether or not anything went wrong;
- FK's error is **small in pixel count but is exactly the thing that matters** — zero when
  nothing is wrong, and consisting *entirely* of the missing or displaced stroke when
  something is.

Which costs more is **not decidable from pixel distances**: it depends on what the policy
needs the channel for. That is why H4 measures the true IoU of trained policies rather than
the divergence of observations — but it does mean a camera win cannot be assumed, and that a
null result would be unsurprising rather than a failure of the experiment.

#### It also explains the interim `ink_failure` problem, with a number

The interim aggregate flagged that `ink_failure` barely bites anyone (open-loop, which cannot
react at all, loses only 0.013). The premise table says why: the outage removes about **5% of
the ink mass**. A disturbance that destroys 5% of the drawing cannot show a recovery
difference worth 0.03 IoU, whatever the agent can see. This is a **sizing** problem, not an
information problem, and it is now quantified rather than suspected. If the n=8 result is null
on `ink_failure`, the correct next step is a longer outage (not a re-analysis), and the
comparison with `paper_shift` at 82% shows how much headroom there is.

#### Ordering this predicts

From the table alone: **if the camera wins anywhere it should win most on `paper_shift`** and
least on `ink_failure` and `slip`. The interim n=4 diff-in-differences are `paper_shift`
+0.007, `ink_failure` +0.006, `slip` -0.030 — the right ordering, all three far from
significance (|t| <= 1.01, crit 3.18), so this is consistent with the prediction and is not
evidence for it.

**This is not a pre-registration and must not be read as one.** The premise script was run
and the ordering written down before the interim aggregate above was read, but the 18 result
rows already existed on disk at that moment. The pre-registered test is the one in the
section below; this is a mechanistic expectation, recorded for honesty about what was
expected and when.

#### Two further limits of the design, recorded before the result

- **`open_loop` is an analytic tracer, not a trained policy.** Its clean score beats the
  privileged `true` arm on `line` (0.475 vs 0.309) and comes close on `square`, because a
  hand-written contour plan is simply a good way to draw a shape when nothing goes wrong. It
  is a floor for **reactivity**, not for skill, and it must never be reported as "RL beats
  classical planning" or the reverse.
- **The disturbance magnitudes are not calibrated to any real arm.** 4-10 px and 4-12% of the
  episode were chosen to be visible but survivable. Nothing here measures how the result
  scales with disturbance size, and the `ink_failure` sizing problem above is direct evidence
  that the choice matters to the conclusion.

### Pre-registered analysis (fixed before the remaining 14 runs)
Written after seeing 18/32 runs - stated so a reader can judge it. The switch to
diff-in-diff is a correction of a confound, not a choice made to favour a result: on the
interim data it turns a camera "win" into a null.
- **Primary endpoint:** per disturbance, paired diff-in-diff
  `(camera_k - camera_none) - (fk_k - fk_none)` within each (shape, seed); n = 8 cells.
- **Test:** one-sample t on the 8 differences, two-sided 5%, critical t(7) = **2.365**.
  `t >= 2.365`: camera recovers better. `t <= -2.365`: camera recovers worse. Otherwise:
  "no detectable difference", never "no difference".
- **Headline disturbance:** `ink_failure`, *conditional on it biting*: report it as
  uninformative if open-loop loses < 0.03 on it.
- **Sanity checks, reported before any conclusion:** open-loop must degrade on slip and
  paper_shift (it does: 0.27-0.31); `true` should be >= `camera` on average.
- **No optional stopping:** if the result sits between |t| 1.5 and 2.365, the only permitted
  follow-up is adding seeds {200, 300} for **all** arms and shapes, and reporting all seeds.
- The absolute camera - fk difference is reported as secondary and labelled as including the
  clean gap.

Sweep status: stopped by the user at 18/32 on 2026-10-19 (resumable; nothing lost but the
runs in progress). Relaunch commands are in `docs/HANDOFF.md`. Relaunched at 00:39 the same night with identical settings.

### H4 bookkeeping (2026-10-19) - mixed thread settings, and two agents at once
- **Thread settings differ across H4 rows.** The 2026-10-17 run (launched from Antigravity:
  line + triangle at seed 0, and line/open_loop at seed 100) used default torch threads;
  every row since used `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1`. Seeded runs on this stack are
  not thread-invariant (2026-09-03 entry). Each (shape, seed) cell is internally consistent,
  so the pre-registered within-cell diff-in-diff is unaffected; cross-cell absolute means mix
  two settings. Rows do not record the setting, so this entry is the record. `open_loop` has
  no training and is thread-independent.
- **The exit 127 at 00:33 was a deliberate stop** (the user asked one Claude Code session to
  stop the sweep), not a crash. A second Claude Code session on the same folder read it as a
  crash and relaunched at 00:39 with identical settings, so nothing is mixed by it. Rule added
  to `AGENTS.md`: one agent at a time.

### Paper scaffolding (2026-10-19) - built so the draft cannot quietly go wrong
Added `docs/paper/` ahead of writing, because the failure modes of an AI-assisted draft are
predictable and checkable:
- `references.bib` is **generated** (`make_bib.py`) from `research_papers/README.md`, whose
  metadata was verified against arXiv. Cite keys are the library IDs. 33 entries; 6 flagged
  VERIFY where the library itself is ambiguous (two-year spans, A08 authors missing, R05
  2024 vs NeurIPS D&B 2025). e-David is not in the library and must be added before citing.
- `check_paper.py` fails a draft on: a cite key not in the bib, a VERIFY entry cited, a
  decimal with no `% src:` pointer to this log, wording `docs/PAPER_PLAN.md` forbids
  ("novel", "first to", "no difference", "equivalent", "outperform", "recovers better"...),
  missing figures. Tested on a deliberately bad sentence: all five problems caught.
- `main.tex`: IEEE skeleton. C1-C3 numbers filled from this log with sources; H4 left
  empty until its result exists; C5 marked as a pitfall, not a fix.
- Found: `docs/presentation/README.md` lists `deck_part3-6.py`, `make_figures.py`,
  `preview.py`, which are not in the folder - the 84-slide deck cannot be rebuilt as-is.

### Found while drafting the paper (2026-10-19) - both H2 sweeps used overlapping seeds
`results/h2_seeds.jsonl` and `results/h2_peak_*.jsonl` both contain seeds **0, 1, 2** (8 rows
each). `rl/experiment.py` seeds its envs `seed + i`, and `PPO(seed=k)` reseeds them to `k+i`
anyway (fix F6, found 2026-09-12 - after both H2 sweeps were run). So seed 0 trains on env
streams 0-7, seed 1 on 1-8, seed 2 on 2-9: **7 of 8 streams shared between adjacent seeds.**
Consequences:
- H2's between-seed spread (the +/-0.05-0.06 the "no detectable difference" argument leans
  on) is likely **understated**.
- The H2 PEAK-vs-FINAL re-run is **not an independent replication**: same seeds, only the
  thread setting differed. Its sign flip shows thread sensitivity, not sampling variation.
  The paper draft and `docs/PAPER_PLAN.md` now say so.
- Recommended before submission (PAPER_PLAN section 4, item 3): re-run H2 with
  `--seeds 0 100 200` into a new results file. Not started - the user decides.
Also: `results/h2_seeds.jsonl` rows do not record `max_steps`, so the H2 episode length is
asserted from `rl/experiment.py` defaults, not from the data.

Paper draft (`docs/paper/main.tex`) now has every section except H4, title, authors,
abstract and the e-David citation; `check_paper.py`: 0 errors. `make_bib.py` now cites
conference papers by venue year (A01, V02, D04 no longer flagged); 3 VERIFY entries remain.

### H4 RESULT — null on the pre-registered endpoint, and the ceiling control says why

All 32 runs complete (4 shapes x 4 arms x seeds {0, 100}, 200k steps, 10 eval episodes per
disturbance kind). `results/h4_experiment_a.jsonl` + `_b.jsonl`; figure
`output/h4_disturbance_recovery.png`. Output of `rl/h4_experiment.py --aggregate`:

```
balanced over 8 (shape, seed) cells with all four arms
                              none          slip   paper_shift   ink_failure
          open_loop           0.486         0.209         0.176         0.473
          true                0.384         0.373         0.325         0.371
          fk                  0.345         0.352         0.291         0.315
          camera              0.361         0.355         0.312         0.341

  clean gap (no disturbance), camera - fk: +0.016  n=8  t=+0.52

  slip:
    drop from own clean score: camera +0.005, fk -0.007, open-loop +0.276
    PRIMARY  diff-in-diff camera - fk: -0.012  5/8 up  t=-0.78  (crit 2.37)
    CONTROL  privileged `true` - fk:   -0.018            t=-2.13
  paper_shift:
    drop from own clean score: camera +0.049, fk +0.054, open-loop +0.309
    PRIMARY  diff-in-diff camera - fk: +0.005  6/8 up  t=+0.24  (crit 2.37)
    CONTROL  privileged `true` - fk:   -0.005            t=-0.29
  ink_failure:
    drop from own clean score: camera +0.020, fk +0.030, open-loop +0.013
    PRIMARY  diff-in-diff camera - fk: +0.010  5/8 up  t=+1.19  (crit 2.37)
    CONTROL  privileged `true` - fk:   +0.017            t=+1.61
    !! open-loop loses only +0.013 here: this disturbance barely bites
```

(`true` loses +0.011 / +0.059 / +0.013 from its own clean 0.384.)

### The verdict, stated as pre-registered

**No detectable difference in recovery between the camera arm and the FK arm, on any of the
three disturbances.** |t| = 0.24 to 1.19 against a critical value of 2.365. This is the
pre-registered primary endpoint and it is a **null**. H4 as posed does not answer D01.

Not "no difference" — no *detectable* difference, at n = 8 with standard errors of 0.008 to
0.021. An effect smaller than roughly 0.04 IoU could not have been seen here.

### A control added after the fact, which changes what the null means

The null on its own would be ambiguous: it could mean a camera is no better than kinematics,
or it could mean the experiment had no signal to detect. So `--aggregate` gained a **ceiling
control** — the same paired diff-in-diff for the *privileged* `true` arm, which sees the real
ink perfectly and is not available to any robot.

**Even perfect sight of the paper buys no recovery.** `true` − fk is −0.018 (t = −2.13) on
slip, −0.005 on paper_shift, +0.017 on ink_failure: null everywhere, and *negative* on two of
the three. The arm with a flawless view of its own mistakes recovers no better than the arm
that cannot see them at all, and on `slip` it is — if anything — slightly worse.

That reframes the result. **The camera-vs-fk null is not a statement about perception
quality.** In this task, the "what have I drawn so far" channel carries **no recoverable
signal for any arm**, so there was nothing for a camera to win with. Adding a control that
could have rescued the experiment and reporting that it did not is the point of running it.

This was written as a sanity check in the pre-registration ("`true` should be >= `camera` on
average") but was not then implemented as a paired test. Recording that it was added **after**
seeing the null: it is a diagnostic of why the primary endpoint came out as it did, not a
substitute endpoint, and it is not claimed as pre-registered.

### What *did* come out strongly, and the confound that limits it

Open-loop collapses and every trained arm absorbs the hit:

| disturbance | open_loop loses | best trained arm loses | ratio |
|---|---|---|---|
| slip | **0.276** | 0.005 (camera) | ~55x |
| paper_shift | **0.309** | 0.049 (camera) | ~6x |

This is the largest effect in the experiment and it is not subtle. But it **cannot be
attributed to feedback**, because `open_loop` differs from `fk` in *two* ways: it has no
observation **and** it executes a fixed analytic plan rather than a trained policy. The
comparison confounds "sees the paper" with "was trained at all". It establishes that a rigid
classical trace is fragile, which was never in doubt.

### Leading explanation, stated as a hypothesis and not as a finding

The trained arms likely absorb `paper_shift` by **overdrawing rather than by correcting**.
`fk` is blind to a paper shift by construction (its belief is 82% wrong under it — measured
in the premise check above), yet it loses only 0.054. H6 found that agents trace the shape in
the first ~10–17% of the episode and then keep moving over a frozen canvas for the remaining
~74%. A policy that keeps covering area is robust to a 5–10 px displacement for the same
reason a thick line is: the band is wider than the error. Open-loop traces its contour once,
thinly, so the same displacement moves the whole stroke off the target.

If that is right, H4 has been measuring **robustness-by-overdrawing**, not recovery, and no
observation channel would change it. **It is a hypothesis.** The H4 result rows record only
IoU, not `coverage` or `path_ratio`, and no models were saved, so it cannot be checked from
the data already collected.

### Honest limits

- **n = 8 cells, 2 seeds.** Underpowered for anything below ~0.04 IoU. Every statement above
  is "not detectable at this n".
- **Between-seed variance is large and dominates.** `circle`/`camera` scores 0.328 ± 0.079
  across two seeds; one poor run moves a cell more than any treatment effect does.
- **The interim n=4 reading was misleading in exactly the way the pre-registration feared.**
  The clean camera − fk gap was +0.053 at n=4 and **+0.016 at n=8** (t = +0.52). An interim
  "camera wins on paper_shift, +0.061, t = 2.45" evaporated. Recorded as a worked example of
  why the no-optional-stopping rule exists.
- **`ink_failure` does not bite** (open-loop loses 0.013), as pre-registered. Its null is
  uninformative by the criterion fixed in advance, and the premise check gives the reason:
  the outage removes only ~5% of the ink mass.
- **The reward asymmetry biases against the camera arm**: `true` and `fk` are rewarded from
  the TRUE canvas, `camera` from vision. A real D01-style robot has no such privileged
  reward, so the `fk` arm here is *stronger* than the system it stands in for. A camera win
  would have been conservative; the null must be read knowing fk was handed an advantage.
- **My own mechanistic prediction was wrong.** The premise check predicted the camera would
  win most on `paper_shift` (fk's belief 82% wrong) and least on `ink_failure` (5% wrong).
  The measured ordering is the reverse: `ink_failure` +0.010 > `paper_shift` +0.005 > `slip`
  −0.012. All three are null, so this refutes the prediction only weakly — but it was
  recorded in advance and it did not hold.
- Result rows still do not record `eval_eps` or the torch thread count. The sweep ran with
  `OMP_NUM_THREADS=1`, asserted from the launch command, not from the data.

### What this does and does not say about D01

It does **not** show that a camera is unnecessary — the experiment could not have shown that
either way, because the privileged ceiling arm did no better. It does show that **this
task, at this episode length, with these disturbance magnitudes, cannot distinguish them**,
and the ceiling control is the evidence for that rather than an excuse for it. D01's
objection stands unanswered; what has changed is that the reason the experiment missed is now
measured instead of guessed, and the next design follows from it.

### Results deck (2026-10-19)
`docs/presentation/deck_paper.py` -> `RoboSketch-RL_Research_Results.pptx`, 13 slides mirroring
the paper: problem, D01 and the three gap quotes, setup, H2, H3, Stage 2, H4 design, H4 result
(PENDING placeholder - no interim numbers), overrun pitfall, limitations, next steps, takeaways.
Every slide's speaker notes name the log entry its numbers come from. `check_deck` logic: 0
shapes outside the safe area, notes on 13/13. Not yet checked visually for text overflow
(no renderer installed) - open it in PowerPoint once.

## 2026-10-26 - H4-short sweep launched (no free repair window, max_steps=60)

### Motivation and Rationale
Baseline H4 completed with a null on its pre-registered primary endpoint (camera vs. fk diff-in-diff: |t| = 0.24 to 1.19), and crucially, the privileged ceiling arm `true` also showed no advantage over fk (-0.018 / -0.005 / +0.017). This showed that under the 240-step horizon, the drawing-so-far channel carried no usable recovery signal because any policy had ~180 surplus steps after completing the trace to blindly overdraw and re-cover disturbance damage (H6 overrun effect).

To test whether visual perception provides recovery when blind overdrawing is prevented:
- `max_steps` is reduced from 240 to 60.
- Shape tracing takes ~30-40 steps, leaving sufficient time for completion and immediate reactive correction, but no massive ~180-step blind overdraw window.
- Isolated results file: `results/h4_short_a.jsonl` and `results/h4_short_b.jsonl`.
- Protocol: 4 arms (`open_loop`, `true`, `fk`, `camera`), 4 shapes (`line`, `circle`, `square`, `triangle`), 2 seeds (0, 100), 200,000 timesteps per training run, evaluated across 4 disturbance conditions (`none`, `slip`, `paper_shift`, `ink_failure`) at 10 episodes each.
- Launched two shards in parallel with `OMP_NUM_THREADS=1`, `MKL_NUM_THREADS=1`:
  - Shard A: shapes `line`, `circle`
  - Shard B: shapes `square`, `triangle`

### Expected completion
~30 runs remaining across the two shards (~6 hours estimated run time).

### H4-SHORT RESULT (2026-10-28) — still null; removing the repair window made paper shift bite, but nobody recovers

All 32 runs complete (4 shapes x 4 arms x seeds {0, 100}, `max_steps=60`, 200k steps, 10 eval
episodes per kind). `results/h4_short_a.jsonl` + `_b.jsonl`; figure
`output/h4_short_disturbance_recovery.png`. Same four arms, same `mixed` training, same
analysis as the 240-step H4 above. Output of `rl/h4_short_experiment.py --aggregate`:

```
balanced over 8 (shape, seed) cells with all four arms
                              none          slip   paper_shift   ink_failure
          open_loop           0.485         0.195         0.161         0.471
          true                0.371         0.374         0.241         0.354
          fk                  0.328         0.328         0.181         0.294
          camera              0.369         0.364         0.233         0.327

  clean gap (no disturbance), camera - fk: +0.041  n=8  t=+1.72
  slip:        PRIMARY diff-in-diff camera - fk: -0.005  4/8 up  t=-0.79  (crit 2.37)
               CONTROL privileged `true` - fk:   +0.003            t=+0.29
  paper_shift: PRIMARY diff-in-diff camera - fk: +0.011  5/8 up  t=+0.57
               CONTROL privileged `true` - fk:   +0.018            t=+0.98
  ink_failure: PRIMARY diff-in-diff camera - fk: -0.008  4/8 up  t=-0.69
               CONTROL privileged `true` - fk:   +0.018            t=+1.38
               !! open-loop loses only +0.013 here: this disturbance barely bites
```

Every printed drop and diff-in-diff was recomputed from the balanced-mean table above it
(e.g. paper_shift: camera 0.369 -> 0.233 = 0.136, fk 0.328 -> 0.181 = 0.147, difference
0.011) and matches.

### Verdict, as pre-registered

**No detectable difference in recovery between camera and fk on any disturbance.** |t| =
0.57 to 0.79 against a critical 2.365. The privileged `true` control is also null on all three
(|t| <= 1.38). **H4-short is a second null, and D01's objection is still unanswered.**

### A trap in this output, recorded so it is not copied into a paper

The `secondary` line for paper_shift reads "absolute camera - fk: **+0.052, t = +5.16**". That
is a large t and it is **not evidence of recovery**: it includes the clean gap of +0.041 (the
camera arm is simply better with no disturbance at all). Subtracting it leaves **+0.011,
t = +0.57**. This is the same confound that produced the false interim "camera wins" in the
240-step H4, and the primary endpoint exists precisely to remove it. The t = +5.16 must not
be quoted.

### What the shorter horizon DID change

Same arms, same disturbances, drop from each arm's own clean score (positive = got worse),
from the two `--aggregate` balanced tables:

| arm | slip 240 / 60 | paper_shift 240 / 60 | ink_failure 240 / 60 |
|---|---|---|---|
| open_loop | +0.277 / +0.290 | +0.310 / +0.324 | +0.013 / +0.014 |
| true | +0.011 / -0.003 | +0.059 / **+0.130** | +0.013 / +0.017 |
| fk | -0.007 / +0.000 | +0.054 / **+0.147** | +0.030 / +0.034 |
| camera | +0.006 / +0.005 | +0.049 / **+0.136** | +0.020 / +0.042 |

(Computed from rounded balanced means, so a figure can differ from a printed drop by 0.001.)

**`paper_shift` now bites trained arms 2.2x to 2.8x harder** (true 2.20x, fk 2.72x, camera
2.78x), while open-loop barely moves. That is the direction the "robustness-by-overdrawing"
hypothesis predicted: with the ~180 free steps removed, trained arms lose most of the
robustness they had. **The hypothesis is partly supported — the robustness was real and
depended on the long horizon — but removing it did not expose a camera advantage.**
Slip is unaffected at either horizon (nothing to recover from), and ink_failure still barely
bites (open-loop +0.014), so it remains uninformative as pre-registered.

### Even perfect sight does not recover paper shift

`true` (sees the real paper exactly) loses **0.130** to paper_shift at 60 steps, nearly as
much as fk (0.147) and camera (0.136). Seeing the damage clearly did not let any arm repair
it.

**Hypothesis, not a finding: part of this loss may be unrecoverable by construction.** Ink is
permanent. When the sheet slides, ink already laid down is displaced against the target, and
an agent can only add ink, not remove it, so a false-positive stripe stays in the true IoU
whatever the agent sees. If so, a paper-shift "recovery" ceiling exists well below the clean
score and this task cannot show a camera advantage on it. This was **not checked**: it needs
an oracle that redraws perfectly after the shift and reports the best achievable IoU. It is
the first thing to measure before running another H4 variant.

### Honest limits

- **n = 8 cells, 2 seeds.** Underpowered below roughly 0.03 IoU; "no detectable", never "no".
- **This is not a pure horizon manipulation.** The disturbance schedule scales with
  `max_steps` (4-16% of the episode): at 240 steps it fires at steps [9, 38) and an ink outage
  lasts [9, 28) steps; at 60 steps it fires at steps [2, 9) and lasts [3, 7). So at 60 steps
  the disturbance lands much earlier in absolute steps, when little ink is committed. The 2.2x
  to 2.8x rise in paper_shift loss may owe something to that, not only to the missing repair
  window. The two effects are not separated.
- **Absolute IoU across the two horizons is not like-with-like** (different task length); only
  each arm's drop from its own clean score is compared above.
- **`open_loop` is an analytic tracer, not a trained policy**; its clean 0.485 is a floor for
  reactivity, not skill.
- **Reward asymmetry still favours fk**: `true` and `fk` are rewarded from the true canvas,
  `camera` from vision, so the fk arm here is stronger than a real D01-style robot. A camera
  win would have been conservative; the null must be read with that.
- Rows do not record `eval_eps` or thread count, and no models were saved, so no arm's
  behaviour (overdrawing, coverage) can be inspected after the fact.
- **Process note.** Both workers were killed once mid-sweep (machine shutdown, 26-10 19:02,
  24/32 done) and once more at a session boundary (31/32). Every restart used the identical
  command and the resume logic skipped completed rows, so no row is duplicated or mixed.

### What this means for the project

Two H4 designs, two nulls, and a privileged ceiling that does no better in either. The
honest summary for the paper is that **under these disturbances the drawn-so-far channel does
not carry a recoverable signal for any arm**, so the experiment cannot adjudicate camera vs
kinematics. It does not show cameras are unnecessary. The way forward is not another H4
re-run: it is to first establish whether the loss is recoverable at all (the oracle check
above), and to look at the other half of D01's objection from a different angle (H5).

## 2026-10-28 - H5: open-loop error grows with the plan, closed-loop does not (proposal 4.4)

### What was done and why this design
`rl/h5_error_growth.py` (new; environment untouched), results `results/h5_error_growth.jsonl`
(1120 episodes), figure `output/h5_error_growth.png`. H5 says error in a blind plan grows as it
executes while a closed-loop controller's does not; FRIDA (A01, Fig. 11) measured this on a
real arm ("grows linearly as the plan is executed"). This reproduces the measurement in our
simulator.

Both arms follow **the same analytic plan** along the target outline. They differ in one thing:
`open_loop` executes the planned deltas blind and assumes each move happened;
`closed_loop` re-aims every step at the next waypoint **from the pen's actual position**.
**Neither is a learned policy.** Alternative considered: train RL policies on a noisy env and
compare. Rejected for now: it would cost hours, and it would confound "replans" with "was
trained", which is the same confound that limited the H4 open-loop comparison.

Execution noise is added to the action, identically for both arms within a (shape, episode),
so the arms are paired. Two kinds, because they predict different growth laws:
- `jitter`: independent Gaussian each step (random walk if uncorrected, expect ~sqrt(steps));
- `bias`: one constant offset per episode (backlash/calibration, expect ~linear).

Levels are in action units (1.0 = one full step, ~8.9 canvas px): jitter 0.05/0.10/0.25, bias
0.005/0.010/0.020, plus a clean control. Deviation at a step = distance (canvas px) from the pen
to the nearest target-outline pixel. 4 shapes x 20 noise realisations x 7 conditions x 2 arms.

### Result (output of `--aggregate`)
```
condition   kind    level |  slope open (px/step)  slope closed | final dev open  final dev closed | IoU o / c
clean       none    0.000 |   +0.000               +0.000       |   0.00            0.00           | 0.486/0.486
jitter_lo   jitter  0.050 |   +0.015+/-0.015       +0.000       |   4.26+/- 3.02    0.38+/-0.09    | 0.276/0.475
jitter_mid  jitter  0.100 |   +0.028+/-0.026       +0.000       |   8.16+/- 5.13    0.69+/-0.10    | 0.163/0.464
jitter_hi   jitter  0.250 |   +0.042+/-0.048       -0.000       |  15.38+/- 8.87    1.59+/-0.30    | 0.084/0.378
bias_lo     bias    0.005 |   +0.031+/-0.024       +0.000       |   6.71+/- 5.21    0.04+/-0.03    | 0.256/0.483
bias_mid    bias    0.010 |   +0.059+/-0.045       +0.000       |  12.44+/- 9.66    0.08+/-0.05    | 0.164/0.481
bias_hi     bias    0.020 |   +0.089+/-0.070       +0.000       |  19.09+/-14.98    0.15+/-0.11    | 0.112/0.480
```
Paired open - closed within (shape, episode), n = 80 pairs per row, crit t = 1.96:

| condition | final-deviation diff (px) | pairs up | t |
|---|---|---|---|
| jitter_lo | +3.884 | 80/80 | +11.54 |
| jitter_mid | +7.470 | 79/80 | +13.05 |
| jitter_hi | +13.788 | 80/80 | +13.86 |
| bias_lo | +6.676 | 79/80 | +11.51 |
| bias_mid | +12.361 | 80/80 | +11.50 |
| bias_hi | +18.931 | 80/80 | +11.36 |

The slope tests are the same direction (t = +7.99 to +11.83; 65/80 to 80/80 up). Rows were
rechecked against the means above them (e.g. bias_mid 12.44 - 0.08 = 12.36).

**H5 holds in this setup.** Open-loop deviation grows with steps executed; closed-loop stays
flat at under 1.6 px at every level (under 0.2 px for bias), and its IoU stays at
0.480-0.483 for bias against a clean 0.486, while open-loop falls to 0.112-0.256.

### Growth law (log-log slope of mean deviation against step)
| condition | open_loop | closed_loop |
|---|---|---|
| jitter_lo / mid | 0.48 / 0.47 | 0.02 / 0.02 |
| jitter_hi | 0.35 | 0.01 |
| bias_lo / mid / hi | 1.02 / 1.01 / 1.00 | 0.01 / -0.01 / -0.02 |

**FRIDA's "linear" corresponds to systematic error, not random jitter.** Constant bias gives an
exponent of 1.00 to 1.02 (linear); independent jitter gives 0.47 to 0.48 (the sqrt(steps) of a
random walk). The jitter_hi exponent of 0.35 is below 0.5 because deviation saturates (the pen is
clamped to the paper and actions are clipped), so it should not be read as a different law.

### What this does and does not show
- **It supports "feedback beats blind execution". It does NOT support "a camera beats
  kinematics", and it does not answer D01.** The closed-loop arm reads the pen's *actual*
  position with no sensor noise. That is what joint encoders give a kinematics-synchronised
  system like D01, so D01 would also pass this test. What kinematics cannot see (paper moving,
  ink not landing) is H4's territory, where we measured two nulls. Do not use this result as
  support for the camera.
- It is close to true by construction: any unmodelled drift accumulates in a blind plan. The
  informative parts are the magnitudes and the growth law, not the sign.
- **Not an RL result.** The closed-loop arm is an analytic controller with a noise-free position
  signal; it says nothing about whether a trained policy replans this well, or how a real
  perception noise floor would change the flat line.
- Noise levels are chosen by me, not calibrated to any arm; 0.005 action units is ~0.04 px per
  step. "Stroke count" here is step count: the pen is always down, so a drawing is one
  continuous stroke, unlike FRIDA's discrete strokes.
- The n = 80 pairs are (shape, noise realisation). Inference is over independent noise streams
  on **four fixed targets**, so the large t values (7.99 to 13.86) reflect a very large effect
  over many noise draws, not 80 independent shapes. Between-shape variation is not sampled.
- Slope sd is large relative to its mean for open-loop (e.g. +0.015 +/- 0.015) because many
  episodes grow in steps, not smoothly; final deviation is the steadier summary.

## 2026-10-29 - H4 oracle check: the paper-shift loss is NOT unrecoverable (a correction to the H4-short entry)

### What was checked and why
The H4-short entry above ended on an unchecked hypothesis: that ink is permanent, so part of
the paper-shift loss might be unrecoverable by any arm, which would explain why even the
privileged `true` arm loses 0.130 and no arm recovers. That decides whether any further H4
variant on `paper_shift` can work, so it was measured before anything else was built.

`rl/h4_oracle.py` (new; environment untouched; `results/h4_oracle.jsonl`, 960 episodes) runs
analytic tracers that **know the shift** (they read the pen's true landing position on the
sheet, which includes the sheet offset) and scores true IoU:
`clean` (no disturbance, the ceiling), `continue` (re-aims from the true landing position and
never re-draws), `restart` (restarts the whole contour when the sheet slides), `foresight`
(holds the pen still until the shift, so it lays no ink that can be displaced; an upper bound
no real arm can reach). 4 shapes x 30 episodes x 2 horizons, paired within (shape, episode).

### Result (output of `rl/h4_oracle.py`)
```
max_steps = 60   n = 120 (shape, episode) pairs
  strategy        IoU       sd |      drop       up         t
  clean         0.485    0.029 |    +0.000   0/120
  continue      0.472    0.029 |    +0.013 100/120   +11.86
  restart       0.464    0.022 |    +0.021 106/120   +13.67
  foresight     0.472    0.021 |    +0.013  97/120   +11.19
  shift size 7.5 px (5.1-9.7), fires at step 5.1 (2-8)

max_steps = 240   n = 120
  clean         0.486    0.023 |    +0.000
  continue      0.478    0.024 |    +0.007 104/120   +10.65
  restart       0.470    0.026 |    +0.015 111/120   +12.02
  foresight     0.477    0.024 |    +0.008 112/120   +13.67

trained arms, same drop (clean - paper_shift), read from results/, n=8 cells
  H4-short (60):  true +0.129   fk +0.147   camera +0.136      oracle: +0.013 / +0.021 / +0.013
  H4 (240):       true +0.059   fk +0.054   camera +0.049      oracle: +0.007 / +0.015 / +0.008
```

### Verdict
**The hypothesis is refuted.** An arm that knows the shift loses only 0.007 to 0.021 IoU, so
the permanent displaced ink costs at most about 0.02. The trained arms lose 0.129 to 0.147 at 60
steps, roughly **ten times** that, so about 0.11 to 0.13 IoU of the 60-step paper-shift loss is
recoverable in principle and no trained arm recovers it. `foresight` (no displaced ink at all)
does no better than `continue` (+0.013 each), which confirms that ink permanence is not where
the loss comes from. **The H4 null cannot be explained by "there was nothing to recover".**

This also withdraws the 2026-10-19 reading of the ceiling control as "the channel carries no
recoverable signal for any arm". The headroom exists; what the arms lack is the ability to use
what they are given. (That entry's statement stays as written; this is the dated correction.)

### The likely reason, a property of our observation design (hypothesis, NOT yet tested)
`DrawEnv._obs` draws the pen marker from the pen's **world** position with no sheet offset
(`draw_env.py` ~line 515), while ink lands at world position plus the sheet offset. After a
shift the marker and the ink disagree by 5-10 px, and a policy has to **infer** the offset by
comparing the marker to its own ink. The oracle does not: it reads the landing position on the
sheet directly.

This bears directly on D01. **The camera arm only sees a photograph of the ink, not the pen
on the sheet**, so it is denied the one thing a real camera gives that kinematics cannot: the
pen tip's position relative to the paper. A fairer camera arm would render the pen marker in
the sheet frame. Until that is tried, H4's null may reflect an observation we chose, not a
property of cameras. It is a hypothesis; nothing here tests it.

### Honest limits
- The oracle is an **analytic tracer**, not a learned policy, and it has information the
  trained arms do not (the sheet-frame pen position). The ~10x gap therefore mixes "skill the
  arms did not learn" with "information they were not given". This check bounds the headroom;
  it does not say which of the two causes it.
- Only `paper_shift` was checked. `ink_failure` and `slip` were not.
- The trained-arm drops come from 8 cells with 2 seeds each and different evaluation episodes
  from the oracle's, though the shift distribution is the same code path. Compare drops, not
  levels: the oracle's clean 0.485 is far above the trained arms' clean 0.33 to 0.37.
- n = 120 pairs are (shape, episode) on four fixed targets, so the large t values (+10.65 to
  +13.67) say the small oracle drop is real, not that 120 independent shapes were sampled.

## 2026-10-29 - H4 v3 launched: give the camera arm the pen on the sheet (pre-registered)

### Why
Two H4 designs were null (camera - fk recovery, |t| <= 1.19), and the oracle check above showed
the paper-shift loss is recoverable (oracle +0.013 vs trained arms +0.129 to +0.147 at 60
steps). The suspected cause is an observation we chose: `DrawEnv._obs` draws the pen marker from
the pen's **world** position with no sheet offset, so after a shift the marker and the ink
disagree by 5-10 px and the agent must infer the offset. The `camera` arm sees only the ink, never
the pen tip against the paper. That is the one thing a real camera gives that kinematics cannot,
and the experiment withheld it. This run tests whether supplying it changes the result.

### What changed in the code (environment, default OFF)
`DrawEnv(pen_marker_frame="world"|"sheet")`, default `"world"`. `"sheet"` adds the paper-shift
offset to the marker (canvas px scaled to obs px); it is ignored when `obs_source="fk"`, because
kinematics cannot know the sheet moved. **Verified, not assumed:**
- default `"world"` is **bit-identical** to the pre-change environment: observations and rewards
  identical on four configurations (true+paper_shift, camera+mixed, fk+slip, plain). The previous
  file is kept as `rl/draw_env.py.bak_pre_h4v3`;
- `"sheet"` with no disturbance is bit-identical to `"world"`; with a shift only the marker channel
  differs (ink and target channels identical); the `fk` arm ignores the switch.
No recorded result moves.

### Design
`rl/h4_v3_experiment.py`. Two new arms, identical to `true` and `camera` except for the sheet
marker: `true_sheet`, `camera_sheet`. 4 shapes x 2 new arms x seeds {0, 100} = **16 runs**, 200k
steps, `max_steps=60`, 10 eval episodes per kind, `OMP_NUM_THREADS=1`, results in
`results/h4_v3_a.jsonl` / `_b.jsonl`.
The comparison arms (`fk`, `camera`, `true`, `open_loop`) are **not re-run**: they are the
H4-short rows, same shapes, seeds, timesteps, horizon, eval episodes and thread count, and the
default environment is proved unchanged. Reusing them also keeps `fk` exactly as D01's condition.
Alternative considered: re-run all six arms for a clean sweep. Rejected: doubles the compute for
no information, given the bit-identity proof; the cost is that the comparison depends on that
proof and on the H4-short rows being valid.

### Pre-registered analysis (fixed BEFORE any v3 run)
n = 8 (shape, seed) cells, paired within (shape, seed), difference-in-differences (how much LESS
an arm loses from its own clean score), two-sided 5%, critical t(7) = 2.365.
- **PRIMARY:** `camera_sheet` vs `fk` on **paper_shift**. This is the disturbance the sheet marker
  addresses and the claim D01 has to be answered on.
- **SECONDARY:** `camera_sheet` vs `camera` (world marker): is the marker itself the cause?
- **CONTROL:** `true_sheet` vs `fk`, and `true_sheet` vs `true`. If even the privileged arm does
  not recover with the pen on the sheet, the marker is not the missing ingredient.
- `slip` and `ink_failure` are reported but not primary: neither moves the sheet, and ink_failure
  does not bite (open-loop loses ~0.013).
- **No optional stopping.** If the primary |t| lands in 1.5-2.365, the only permitted follow-up is
  adding seeds {200, 300} for ALL arms and reporting every seed.
- The absolute camera_sheet - fk gap is secondary and labelled as including the clean gap.

### What each outcome would mean (stated now so it cannot be bent later)
- Primary significant and `true_sheet` also recovers: the pen-on-sheet observation was the missing
  ingredient, and a camera that sees pen and paper beats believing kinematics on a sheet shift.
  Still one disturbance, n=8, a simulator camera.
- Primary null and `true_sheet` null: the marker was not the cause either; the headroom is a
  learning problem, not an information one. D01's objection stays unanswered and the next move is
  about how the policy learns, not what it sees.
- Primary null but `true_sheet` recovers: the privileged arm can use the pen on the sheet and the
  camera arm cannot, which would point at camera noise or the vision reward, not the marker.

### H4 v3 RESULT (2026-10-30; 16/16 runs, output of `rl/h4_v3_experiment.py --aggregate`)
Balanced over 8 (shape, seed) cells; comparison arms fk/camera/true/open_loop are the H4-short rows.
```
                        none          slip   paper_shift   ink_failure
true                   0.371         0.374         0.241         0.354
fk                     0.328         0.328         0.181         0.294
camera                 0.369         0.364         0.233         0.327
true_sheet             0.386         0.379         0.372         0.357
camera_sheet           0.402         0.393         0.382         0.374
drop (clean - disturbed), paper_shift: fk +0.147, camera +0.136, true +0.129,
                                       camera_sheet +0.019, true_sheet +0.015
PRIMARY camera_sheet vs fk, paper_shift: +0.128, 8/8 up, t=+10.39 (crit 2.37)  slip t=-0.56  ink t=+0.73
SECONDARY camera_sheet vs camera:        +0.116, 8/8 up, t=+5.79
CONTROL true_sheet vs fk:                +0.133, 8/8 up, t=+8.03
        true_sheet vs true:              +0.115, 8/8 up, t=+6.52
clean gap camera_sheet - fk: +0.074 (t=+2.60) - not evidence of recovery
```
Rechecked by hand from the table: fk 0.328-0.181=0.147; camera_sheet 0.402-0.382=0.020 (printed
0.019, rounding of unrounded cells); 0.147-0.019=0.128.

**Reading (pre-stated outcome 1):** primary significant AND true_sheet recovers equally. The missing
ingredient in H4 v1/v2 was the observation, not the camera: once the pen marker is drawn where the pen
lands ON the sheet, paper-shift loss falls from ~0.13-0.15 to ~0.02 (matches the oracle's 0.007-0.021,
so the oracle headroom was an unlearned inference from the world-frame marker). slip and ink_failure:
no detectable effect.

### Honest limits (read before using this anywhere)
- **This does NOT show a camera helps. It does NOT answer D01.** The sheet-frame marker is computed by
  the simulator from the TRUE paper offset (`_paper_off`); camera_sheet is not estimating the shift
  from its photograph. camera_sheet ~ true_sheet (0.382 vs 0.372; the camera arm is not better than the
  privileged one). So v3 shows "knowing where the pen is relative to the sheet" is what matters.
  Whether a camera can supply that (estimate the offset from the image) is untested - the real H4 question.
- The fk arm was not given this marker (fk obs has no sheet frame), so the comparison is camera-with-
  privileged-offset vs kinematics-without; an fk arm told the offset would also recover (it cannot
  know it in reality - that is exactly what a camera might provide).
- n=8 cells (4 shapes x 2 seeds), 200k steps, max_steps=60, simulator camera, single paper_shift
  family. Comparison arms were run earlier (different session); same code/threads except the marker flag
  (default bit-identical). Clean camera_sheet is +0.074 above fk, so only diff-in-diff counts.
- This was a pre-registered design after two nulls and an oracle check, i.e. the third attempt on the
  same hypothesis; treat the positive as hypothesis-generating, not confirmation.

## 2026-10-30 - H4 v4 launched: can the camera ESTIMATE the sheet offset? (pre-registered)
### Why
User asked me to decide the next step (and wants hardware work soon). Of the three options, v4 is the
only one on the critical path: v3 showed the paper-shift loss is an observation problem, but its
sheet-frame marker used the simulator's true `_paper_off`, so it did not test a camera and D01 stays
unanswered. Parameterised shapes and Stage 4 ablations do not touch the fatal objection. Cost ~2 h.
### What changed (environment, default OFF; backup `rl/draw_env.py.bak_pre_h4v4`)
`DrawEnv(pen_marker_frame="estimated")`: the belief canvas (commanded positions) is maintained for
camera arms too; `_estimate_offset()` runs `cv2.phaseCorrelate(belief, photo)` (response < 0.05 or no
ink -> offset 0) and shifts the pen marker by that estimate. `_paper_off` is NOT read. "world" and
"sheet" paths are untouched (the belief update only runs for fk or "estimated").
Accuracy check with random actions, steps 40-59, 24 episodes (4 shapes x 6): mean |estimate - true|
= 0.48 px (p90 0.47) against a mean true shift of 7.6 px. Early-step accuracy not measured (ink sparse).
### Design and pre-registered analysis
New arm `camera_est` (obs_source camera, cam_split fixed, vision reward, estimated marker), 4 shapes x
seeds {0,100}, 200k steps, max_steps=60, OMP=1, same PPO settings. Comparison arms reused (fk, camera,
true, open_loop from h4_short; true_sheet, camera_sheet from v3). n=8 cells, crit t(7)=2.365,
diff-in-diff. PRIMARY camera_est vs fk (paper_shift); SECONDARY vs camera; REFERENCE vs camera_sheet.
Readings fixed now: primary sig and ~ camera_sheet -> camera supplies what kinematics cannot (D01
answered in simulation); sig but clearly below camera_sheet -> partial; not sig -> PPO does not use the
estimate in 200k steps. No optional stopping (|t| 1.5-2.365 -> only seeds {200,300} for ALL arms).
### Honest limits (stated before running)
Estimator is easy here: the photo is a pure translation of the belief canvas, in a simulated
near-fixed camera. A real camera adds perspective, lighting, a moving hand. Passing v4 supports
feasibility, not real-world performance. Phase correlation was designed by me with the shift model
known (pure translation); that is a modelling assumption.

### H4 v4 RESULT (2026-10-30; 8/8 runs, output of `rl/h4_v4_experiment.py --aggregate`)
n=8 (shape, seed) cells; comparison arms reused (fk/camera/true from h4_short, *_sheet from v3).
```
                none   slip   paper_shift   ink_failure
fk             0.328  0.328     0.181         0.294
camera         0.369  0.364     0.233         0.327
camera_est     0.397  0.380     0.327         0.336
camera_sheet   0.402  0.393     0.382         0.374     (true offset given by the simulator)
drop (clean - disturbed), paper_shift: fk +0.147, camera +0.136, camera_est +0.070, camera_sheet +0.019
PRIMARY   camera_est vs fk,     paper_shift: +0.077, 8/8 up, t=+6.39 (crit 2.37)
SECONDARY camera_est vs camera, paper_shift: +0.066, 7/8 up, t=+3.41
REFERENCE camera_est vs camera_sheet:        -0.051, 0/8 up, t=-8.92  (estimate worse than the true offset)
slip, ink_failure vs fk: -0.017 (t=-1.23), -0.027 (t=-1.53): no detectable effect
clean gap camera_est - fk: +0.069 (t=+3.41): not recovery
```
Hand check: 0.147-0.070=0.077; 0.070-0.019=0.051 (sign: camera_est loses MORE than camera_sheet).

**Reading (pre-stated "partial"):** primary significant, but camera_est clearly worse than camera_sheet.
A camera-derived offset estimate lets the arm lose about half as much to a paper shift as kinematics
(0.070 vs 0.147) and about half as much as the world-marker camera arm, recovering roughly 60% of the
gap to the true-offset arm (0.147 -> 0.070 of 0.147 -> 0.019). This is the first H4 result in which a
camera arm beats the D01 condition on a disturbance kinematics cannot see (paper_shift), in simulation.
### Honest limits
- Offset error was only 0.48 px in a random-action test, so the remaining gap to camera_sheet (0.051) is
  NOT explained by estimate noise; likely learning/exploration or early steps with sparse ink
  (not measured). Cause untested.
- ink_failure: camera_est loses 0.061 vs fk 0.034 (diff -0.027, t=-1.53, no detectable effect) - possible
  harm (estimator confused when ink is missing from the photo); needs more seeds to say anything.
- n=8, 2 seeds, 200k steps, 60 steps, simulated near-fixed camera, pure-translation shift, estimator
  designed by me knowing the shift model. This is the fourth H4 attempt after two nulls and a privileged
  v3; v4 was pre-registered but the series is exploratory overall. Real camera: untested.
- Does not touch D01's other claim (camera-free is simpler/robust where nothing moves): in the undisturbed
  case camera_est is above fk by 0.069 but with n=8 that is not what the claim tests.

## 2026-10-30 - Generalisation experiment launched: does the agent draw, or memorise four pictures? (pre-registered)
### Why
User said to move on from H4 (v4 = "partial"; no confirmation seeds). Next on the plan is proposal 5.4: every result so far
used ONE fixed target per shape, so a reviewer can say the agent memorised four images. 5.4 also carries the `eval_eps` fix:
`eval_eps=8` re-ran one identical episode eight times (proposal section 5, item 4).
### What changed (additive, default OFF; backups `rl/draw_env.py.bak_pre_param`, `rl/targets.py.bak_pre_param`)
- `targets.make_param(name, scale, theta)` + `targets.sample_params(rng, split)`; ranges in `targets.PARAM_RANGES`:
  train scale 0.8-1.0, |rot| 0-15 deg; heldout scale 0.6-0.8, |rot| 15-45 deg (both axes outside the train range).
- `DrawEnv(target_split=None|"train"|"heldout")`: at every `reset` draws a new size/rotation from the env's own RNG, so
  `reset(seed=k)` is reproducible and eval episodes are DISTINCT targets. Target setup moved into `_set_target`.
- Checked: with `target_split=None` target, distance map, first observation and a 30-step rollout (obs + reward) are
  bit-identical to the pre-change env for all 4 shapes. Largest ink distance from centre: train 0.439, heldout 0.354 of
  canvas width (sheet edge 0.5; the default square/triangle corner is already ~0.42). Figure `output/param_shapes.png`.
- Bug found and fixed while smoke-testing: a numpy `@` in `make_param` loaded MKL's libiomp5 next to torch's libomp and
  aborted with `OMP: Error #15` once torch was imported. Replaced by elementwise arithmetic; figure byte-identical.
  (Possibly relevant to the old unexplained exit-code crashes, but not shown to be.)
### Design (`rl/gen_experiment.py`, results `results/gen_a/b.jsonl`)
Arms, both `reward_mode="vision"`, H2 protocol (240 steps, step 0.014, PPO 200k, OMP=1): `fixed` (trained on the default
target, = all earlier results) and `param` (trained on the "train" range). 4 shapes x seeds {0,100} = 8 cells x 2 arms = 16
runs. Each agent is scored (TRUE IoU) on three sets, 16 episodes each, SAME targets for every agent (reset seed 20000+ep):
`default`, `train`, `heldout`. Expected ~4 h with two workers.
### Pre-registered analysis (n=8 cells, crit |t|=2.365, diff-in-diff per AGENTS.md rule 4)
- PRIMARY: heldout IoU, param - fixed (>0 = parameterised training generalises better).
- LOSS: each arm's drop from its OWN home set (fixed: default, param: train) to heldout; compare fixed loss - param loss.
- REFERENCE: param train vs fixed default (cost of learning the harder family); param default vs train.
- Readings fixed now: primary sig >0 -> fixed-target agents do not carry over to unseen sizes/rotations and parameterised
  training fixes it. Primary not sig and param loss small -> agent draws unseen targets about as well as seen ones (no
  evidence of memorisation, but also no benefit from the parameterised training). Both arms collapse on heldout -> the
  agent does not generalise this far; report it as a limit of the paper. No optional stopping; extra seeds only if
  |t| is in 1.5-2.365 and then for BOTH arms.
### Honest limits (stated before running)
- Heldout changes size AND rotation together: a failure cannot be attributed to one of them.
- Ranges were chosen by me before running, not tuned. Only 4 simple shapes, 2 seeds, vision reward only, no arm.
- `default` set = 16 identical deterministic episodes (known no-op, kept only for a uniform record format).
- Different task from H2 (new family of targets): do not compare absolute IoU with H2 (~0.45) or H4 numbers.
- 240-step horizon keeps the overshoot effect (H6); `peak_iou` is recorded and reported next to final IoU.

### Generalisation RESULT (2026-10-31; 16/16 runs, output of `rl/gen_experiment.py --aggregate`; figure `output/gen_generalisation.png`)
n=8 (shape, seed) cells, 16 distinct targets per set, TRUE IoU, vision reward, 200k steps, 240 steps.
```
arm trained on     default          train          heldout
fixed          0.381 +/-0.074  0.235 +/-0.053  0.074 +/-0.043
param          0.279 +/-0.066  0.292 +/-0.039  0.118 +/-0.036
peak IoU  fixed 0.419 / 0.252 / 0.097 ; param 0.300 / 0.312 / 0.140   (default / train / heldout)
PRIMARY   heldout: param - fixed                +0.044  8/8 up  t=+7.35 (crit 2.37)
LOSS      fixed (default->heldout) +0.307, param (train->heldout) +0.174; fixed - param +0.133  8/8 up  t=+4.85
REFERENCE param train vs fixed default (home vs home)   -0.089  2/8 up  t=-3.37
          param: default - train                        -0.013  4/8 up  t=-0.57  (no detectable difference)
          fixed: default - train                        +0.146  8/8 up  t=+4.26
          param: train - heldout                        +0.174  8/8 up  t=+7.82
```
Hand check: 0.118-0.074=0.044; 0.381-0.074=0.307; 0.292-0.118=0.174; 0.307-0.174=0.133; 0.292-0.381=-0.089.
**Reading (pre-registered, two of the three branches apply):**
1. Primary significant: fixed-target agents do NOT carry over to unseen sizes/rotations, and training on a size/rotation
   family helps (heldout 0.074 -> 0.118, 8/8 cells). Direction is the same in every shape and seed.
2. But "parameterised training fixes it" is NOT supported: both arms are far lower on heldout than at home (param loses
   0.174 of its 0.292, fixed 0.307 of its 0.381). The agent generalises only a little beyond its training range;
   this is a limit to state in the paper, not a pass.
3. Memorisation: the fixed-target agent loses 0.146 (t=+4.26, 8/8) already on the TRAIN range, whose targets are within 20%
   of its size and 15 deg of its orientation. That is what an agent tied to one picture looks like. So the earlier results
   (H2, H4 ...) describe agents trained and tested on one fixed picture; a reviewer's "memorised four shapes" is partly right.
4. Cost: param is 0.089 lower than fixed at home (t=-3.37) - but these are different target sets (fixed's default is a single
   easy picture), so this is not a like-with-like comparison.
### Honest limits
- Heldout moves size AND rotation together (and shrinks the shape while the stroke stays 14 px, which makes IoU harsher):
  cannot say which factor breaks the agent. Ranges were mine, set before running.
- n=8 cells, 2 seeds, 4 simple shapes, vision reward, no arm, no disturbance; 200k steps may be too few for a policy that must
  read the target - a longer run could move the param arm (untested).
- `default` set = 16 identical episodes, so its "+/-" is across cells only. Peak is ~0.02 above final in both arms on heldout.
- Absolute IoU is not comparable with H2 (~0.45) or H4: different task.
- Consequence for the paper (PAPER_PLAN section 4 item 4): report this as a generalisation LIMIT with the measured numbers.

## 2026-10-31 - H2 re-run with spaced seeds launched (pre-registered; PAPER_PLAN section 4 items 2-3)
### Why
H2 (camera reward vs truth reward) is the paper's main result, and both existing sweeps (`h2_seeds`, `h2_peak*`) used seeds
0,1,2, which share 7 of 8 env streams (F6) and are not independent of each other; the sign of the gap flipped between them.
"No detectable difference" also invites "underpowered". This re-run gives independent seeds and an equivalence test.
### Deviation from PAPER_PLAN (stated)
PAPER_PLAN says `--seeds 0 100 200`. Seed 0 would reuse env streams of the old sweeps, so I use **`--seeds 100 200 300`**:
no env stream overlaps seeds 0,1,2 or each other. Everything else is the H2 protocol unchanged: 4 shapes x {truth, vision} x
3 seeds = 24 runs, 200k steps, 240 steps, step 0.014, OMP=1/MKL=1 (two workers), fresh file `results/h2_spaced*.jsonl`
(`--out h2_spaced.jsonl`); old files untouched. ~17 min/run (measured on the generalisation sweep) -> ~3.5 h.
### Pre-registered analysis (written before any run finished)
- Unit: (shape, seed) cell, n=12 paired differences d = IoU_truth - IoU_vision (TRUE IoU, final; peak reported beside it).
- Equivalence (TOST, paired, df=11, alpha=0.05 each side), margin **+/-0.05 IoU** (chosen now, ~13% of the ~0.38 level; a
  wider margin would be easier to pass, so it is not widened afterwards). Equivalent only if BOTH one-sided tests reject.
- Also report: mean d +/- sd, k/n cells with truth > vision, ordinary paired t, and the 90% CI of d (TOST <=> 90% CI inside margin).
- Readings: 90% CI inside +/-0.05 -> "equivalent within 0.05 IoU in simulation". CI crosses a margin but ordinary test not
  sig -> "no detectable difference, equivalence NOT shown at 0.05" (state the CI). Truth significantly better -> report it
  as a measured cost of the camera reward. Not pooled with the old sweeps (not independent); old numbers quoted only side by side.
### Honest limits (stated before running)
Fixed camera (cam_split None, proxy perception), 4 simple fixed shapes (the generalisation result says the agent is partly
tied to one picture), 3 seeds, simulation only. A pass shows equivalence of the two rewards in this setting, not on a robot.

### H2 re-run: analysis tool written while the sweep runs (2026-10-31)
`rl/h2_equivalence.py` (paired TOST, margin 0.05, alpha 0.05; no scipy in the env, so the t CDF is implemented by hand and
checked against textbook values: t(.975,7)=2.365, t(.95,11)=1.796, t(.975,10)=2.228, cdf(2.015,5)=0.95).
Smoke-run on the OLD `h2_seeds` (seeds 0,1,2; overlapping env streams, so NOT a result, only a check that the tool works and
reproduces the logged means 0.382 / 0.354): d=+0.028, sd 0.068, 7/12 cells, t=+1.43 (p=0.18), 90% CI [-0.007, +0.063],
p_TOST=0.143 -> equivalence at +/-0.05 NOT shown. So the pre-registered bar may well be missed on the new seeds too; if it
is, the paper says "no detectable difference, equivalence not established at 0.05" with the CI. Margin stays 0.05.

### H2 spaced RESULT (2026-10-31; 24/24 runs, seeds 100/200/300; output of `rl/h2_equivalence.py` and `rl/experiment.py --aggregate --out h2_spaced.jsonl`)
Pre-registered in `## 2026-10-31 - H2 re-run with spaced seeds launched`. n=12 paired (shape, seed) cells, TRUE IoU.
```
truth 0.388 +/-0.062   vision 0.384 +/-0.059
d = truth - vision: +0.004, sd 0.055, truth > vision in 6/12 cells, paired t=+0.27 (df 11, p=0.793)
90% CI of d: [-0.024, +0.033]   margin +/-0.05
TOST p(lower)=0.003, p(upper)=0.008, p_TOST=0.008 -> EQUIVALENT within +/-0.05
PEAK IoU: truth 0.424 vs vision 0.415, d=+0.009, CI [-0.017, +0.035], p_TOST=0.008 -> equivalent
per shape (n=3 each): circle -0.030, line -0.028, square +0.055, triangle +0.020   (truth - vision)
```
Hand check: 0.388-0.384=0.004. Figure `output/results_h2_spaced.png` (new file; old figures untouched).
**Reading (pre-stated):** 90% CI inside the margin -> "equivalent within 0.05 IoU in simulation". The camera reward costs no
measurable accuracy relative to the privileged canvas, to within 0.05 IoU (~13% of the 0.38 level).
Contrast (same tool, OLD overlapping seeds 0,1,2, n=12): d=+0.028, CI [-0.007, +0.063], p_TOST=0.143 - equivalence NOT shown
there. The two sweeps disagree on the point estimate (+0.028 vs +0.004) and on the equivalence verdict; this is the same
sign/size instability already logged (F6, "H2 PEAK-vs-FINAL"). The pre-registered new sweep is the one to cite; the
disagreement should be mentioned, not hidden. Not pooled (old sweeps not independent).
### Honest limits
- 3 seeds per shape; per-shape differences (square +0.055 > margin, circle/line negative) are untested at n=3 and shape-dependence
  is real: the claim is pooled over 4 shapes, not per shape.
- Margin 0.05 chosen by me before running; a stricter margin (e.g. 0.03) would NOT pass (CI half-width ~0.03).
- Fixed proxy camera, fixed pictures (generalisation entry: agents are partly tied to one picture), no disturbance, no arm,
  simulation only. Equivalence of the REWARDS here; says nothing about a real camera.

## 2026-10-31 - Generalisation part 2 launched: training budget, and which factor breaks it (pre-registered)
### Why
`### Generalisation RESULT` showed both arms lose most of their home score on held-out targets. Two cheap questions decide what
the paper can say and what Stage 4 should target: (1) is it just too little training (200k steps for a policy that must read
a changing target)? (2) held-out changed size AND rotation together - which one breaks the agent?
### What changed (additive; backups `rl/draw_env.py.bak_pre_split2`, `rl/targets.py.bak_pre_split2`)
Two more target ranges in `targets.PARAM_RANGES`: `heldout_scale` (scale 0.6-0.8, rotation in the TRAIN range) and `heldout_rot`
(scale in the TRAIN range, |rot| 15-45); `DrawEnv.target_split` accepts them. Existing splits unchanged: default env, train and
heldout ranges re-checked identical (`check_param.py`).
### Design (`rl/gen2_experiment.py`, results `results/gen2_a/b.jsonl`)
Arms `param200` (train family, 200k = the earlier `param` re-run so it is scored on the new sets) and `param600` (3x budget);
vision reward, 4 shapes x seeds {0,100} = 8 cells x 2 arms = 16 runs, same protocol and reset seeds as gen sweep. Scored on
default, train, heldout, heldout_scale, heldout_rot (16 targets each, TRUE IoU, peak beside it). ~4.5 h with two workers
(8 x 17 min + 8 x 51 min, split over 2 workers).
### Pre-registered analysis (n=8 cells, crit |t|=2.365, paired)
- PRIMARY: heldout IoU, param600 - param200. Significant >0 -> part of the limit is training budget (say how much of the
  0.174 loss it recovers). Not significant -> 3x steps does not help here; the limit is not just budget (other causes untested).
- FACTOR: for each arm, loss = IoU(train) - IoU(heldout_scale) and IoU(train) - IoU(heldout_rot); paired difference between the
  two losses says which factor hurts more. Reported per arm; no claim about a factor whose loss is not significantly > 0.
- CONSISTENCY: param200 should reproduce the earlier `param` train/heldout means (same seeds, settings, OMP=1). If not, say so
  and use only within-sweep comparisons.
- No optional stopping; extra seeds only if |t| in 1.5-2.365, for BOTH arms.
### Honest limits (stated before running)
One extra budget (600k) only, 2 seeds, 4 simple shapes, vision reward. `heldout_scale` shapes are smaller while the stroke stays
14 px (IoU harsher), so a size effect may be partly a metric effect. Does not test architecture/observation fixes (Stage 4).

### Generalisation part 2: workers killed by a PC restart, resumed (2026-10-31 21:49)
Both workers died after 1 run each (line / square param200, seed 0, threads=1, rows intact in `results/gen2_a/b.jsonl`). No traceback;
Windows System log shows Kernel-Power 41 / EventLog 6008 (unexpected shutdown) at 20:25 and 20:39 - a power/system restart, not a
user stop and not the unexplained exit-4 crash. Relaunched with the SAME commands (same OMP=1, same settings); the resume key keeps
the 2 finished runs. Nothing about the design or the pre-registered analysis changed. Expect ~02:00 finish.

### Generalisation part 2 RESULT (2026-11-01; 16/16 runs, output of `rl/gen2_experiment.py --aggregate` + a short script for loss-vs-0)
n=8 (shape, seed) cells, 16 targets per set, TRUE IoU, vision reward. Pre-registered in `## 2026-10-31 - Generalisation part 2 launched`.
```
arm        default        train          heldout        heldout_scale  heldout_rot
param200   0.279+/-0.066  0.292+/-0.039  0.118+/-0.036  0.160+/-0.073  0.192+/-0.087
param600   0.365+/-0.076  0.361+/-0.082  0.131+/-0.021  0.215+/-0.119  0.223+/-0.134
peak       param200 0.300/0.312/0.140/0.180/0.211 ; param600 0.407/0.411/0.156/0.268/0.254
PRIMARY   heldout: param600 - param200           +0.013  5/8 up  t=+0.95   (not significant; crit 2.37)
SECONDARY param600 - param200: train +0.069 (6/8, t=+2.27); heldout_scale +0.055 (6/8, t=+2.29); heldout_rot +0.031 (6/8, t=+1.78)
LOSS train -> heldout (size+rot): param200 +0.174 (8/8, t=+7.82), param600 +0.230 (8/8, t=+9.68)
FACTOR    param200: size-only loss +0.132 (8/8, t=+3.80), rotation-only +0.100 (6/8, t=+4.44); size - rot +0.032 (t=+0.62)
          param600: size-only loss +0.146 (8/8, t=+3.81), rotation-only +0.138 (6/8, t=+3.36); size - rot +0.008 (t=+0.11)
CONSISTENCY param200 vs earlier gen `param`: train 0.292 / heldout 0.118, max |diff| 0.0000 (bit-identical)
```
Hand check: 0.131-0.118=0.013; 0.361-0.131=0.230; 0.292-0.160=0.132; 0.292-0.192=0.100; 0.361-0.215=0.146; 0.361-0.223=0.138.
**Reading (pre-stated branches):**
1. Primary NOT significant: 3x training does not close the held-out gap (heldout +0.013 of a 0.174 loss). More training
   improved the home sets more (train +0.069, t=+2.27, just under the bar, so not claimed) -> the loss grew (0.174 -> 0.230).
   The limit is NOT simply too few steps; it is a failure to extrapolate beyond the sampled sizes/rotations.
2. Factor: each factor alone already costs IoU (size +0.132, rotation +0.100 at 200k; all |t| > 3.3) and neither clearly
   dominates (difference t=+0.62 / +0.11). So no single "culprit": the agent loses accuracy whenever the target moves outside the
   range it saw, in either dimension.
3. Reproducibility: param200 matches the earlier gen sweep bit-for-bit although the workers were killed and resumed 3 times by PC
   restarts - supports that resume does not alter results at OMP=1.
### Honest limits
- One extra budget (600k), 2 seeds, 4 simple shapes, vision reward; larger budgets, other architectures and wider training ranges
  are untested - "not a budget problem" means "not at 3x", not "never".
- heldout_scale shapes are smaller with a fixed 14 px stroke, so part of the size loss may be a metric effect.
- Train +0.069 (t=+2.27) and the scale/rot gains (t=+2.29/+1.78) sit near but below the 2.37 bar; do not call them effects.
- Consequence: state it as a limit; Stage 4 (observation/architecture changes) is the next lever, not more steps.

## 2026-11-01 - O2 egocentric ablation launched: does a pen-centred view improve generalisation? (pre-registered; Stage 4 item 14)
### Why
Generalisation part 2 showed the held-out gap is not a training-budget problem (3x steps: +0.013, t=+0.95) and that size and
rotation each cost IoU. The proposal's O2 (egocentric crop; "strongest converged finding" in the review, D03/D08) is the
cheapest observation change and directly targets "the policy depends on where/how large the shape is on the sheet".
### What changed (additive, default OFF; backup `rl/draw_env.py.bak_pre_ego`)
`DrawEnv(obs_view="global"|"ego", ego_win=64)`. "ego": 64x64 canvas-px window centred on the pen (zero-padded off the sheet,
exact integer crop, 2x zoom vs the global 64-px view of the 128-px canvas); channels target, drawn, sheet-extent mask (replaces
the pen marker - the pen is always at the centre; the mask is the only absolute-position cue). Only the privileged, undisturbed,
pen-always-down setting (asserts otherwise). Checked: "global" reset obs + 40-step rollouts bit-identical to the pre-change env
for 4 shapes x {fixed, train targets}; "ego" window equals an independent numpy zero-pad crop (0 differing pixels, 4 shapes x 60 steps).
### Design (`rl/ego_experiment.py`, results `results/ego_a/b.jsonl`)
New arm `ego`: trained on the "train" family, 200k steps, vision reward, 4 shapes x seeds {0,100} = 8 runs, scored on default /
train / heldout / heldout_scale / heldout_rot (16 targets each, same reset seeds as gen2). Comparison arm = `param200` from
`results/gen2*.jsonl` (global observation; same seeds, shapes, settings; reproduced the earlier sweep bit-for-bit), so the
design is paired by (shape, seed), n=8. ~70 min with two workers. Same 3-conv CNN (SB3 CnnPolicy) for both arms.
### Pre-registered analysis (n=8 cells, crit |t|=2.365, paired)
- PRIMARY: heldout IoU, ego - global. Significant >0 -> the observation is a lever on the limit (say how much of the 0.174 loss
  it recovers). Not significant -> a pen-centred view does not help at this budget. Significantly <0 -> ego hurts generalisation.
- SECONDARY: ego - global on train, default, heldout_scale, heldout_rot (cost or gain at home; which factor it helps).
- LOSS: train->heldout loss, global - ego (>0 = ego loses less) - the diff-in-diff, since the arms may start at different levels.
- No optional stopping; extra seeds only if |t| in 1.5-2.365, for BOTH arms (global needs new runs too).
### Honest limits (stated before running)
2 seeds, 4 simple shapes, privileged observation, one window size (64 px) and one budget (200k); the window also gives 2x zoom, so
"egocentric" and "zoomed" are confounded (not separable here). Sheet mask is the only absolute-position cue by design.
O3 (CoordConv) and the rest of Stage 4 are separate ablations.

### O2 egocentric RESULT (2026-11-01; 8/8 runs, both shards finished, no restarts)
Command: `conda run -n robosketch --no-capture-output python rl/ego_experiment.py --aggregate`
```
=== O2 egocentric vs global observation: TRUE IoU, n=8 (shape, seed) cells, 16 targets/set ===
arm                    default               train             heldout       heldout_scale         heldout_rot
global           0.279 +/-0.066       0.292 +/-0.039       0.118 +/-0.036       0.160 +/-0.073       0.192 +/-0.087
ego              0.338 +/-0.042       0.340 +/-0.025       0.298 +/-0.042       0.323 +/-0.020       0.311 +/-0.052
peak IoU:  global 0.300/0.312/0.140/0.180/0.211   ego 0.395/0.398/0.365/0.392/0.362
PRIMARY  heldout: ego - global   +0.181  8/8 up  t=+7.00
SECONDARY train +0.048 (7/8, t=+3.52)  default +0.059 (7/8, t=+2.73)  heldout_scale +0.163 (8/8, t=+5.50)  heldout_rot +0.119 (7/8, t=+4.09)
LOSS train->heldout: global +0.174 (size-only +0.132, rot-only +0.100); ego +0.042 (size-only +0.017, rot-only +0.030)
loss global - ego  +0.132  8/8 up  t=+4.11
```
Hand check: 0.298-0.118=0.180 (script 0.181 from unrounded); 0.340-0.292=0.048; 0.174-0.042=0.132.
**Reading (pre-registered branch 1: primary significant >0):** the pen-centred view is a strong lever on the generalisation limit.
Held-out IoU rises 0.118 -> 0.298; the train->held-out loss falls 0.174 -> 0.042 (diff-in-diff +0.132, t=+4.11), i.e. the ego agent
loses ~76% less when targets leave the training range. It also gains at home (train +0.048, default +0.059 [t=+2.73, secondary]),
so the held-out gain is not just a smaller loss from a lower start: the ego arm is better everywhere, and loses less.
### Honest limits
- n=8 cells (4 shapes x 2 seeds), 200k steps, privileged observation (true canvas), one window size (64 px).
- CONFOUND (stated beforehand): the window also gives 2x zoom, so "egocentric" vs "zoomed" is not separated; the sheet mask is the only
  absolute-position cue. Cannot say which part helps.
- Home-set gains (train/default) are secondary and under multiple comparisons; the default +0.059 (t=+2.73) is just above the bar.
- Ego works only with the privileged, undisturbed setting; it has NOT been tested with a camera observation or H4 disturbances, so it
  says nothing yet about the camera claims. Absolute IoU is still low (~0.30-0.34).
- Not a hardware claim; simulation only.

## 2026-11-01 - O2z zoom control launched: is the ego gain just resolution? (pre-registered)
### Why
O2 result (ego +0.181 held-out IoU) is confounded: the ego window shows 1 canvas px per obs px, the global view only 0.5. Control arm
`global128`: the WHOLE sheet at obs_res=128 (same density as ego, same 3-conv CnnPolicy, bigger input) but NOT pen-centred. No env change
(obs_res is an existing argument). New file `rl/zoom_experiment.py`, results `results/zoom_a/b.jsonl`; 4 shapes x seeds {0,100} = 8 runs,
same train family / 200k steps / vision reward / eval sets and reset seeds. Compared with gen2 `param200` (global64) and `ego`, paired by cell.
### Pre-registered analysis (n=8, crit |t|=2.365)
- PRIMARY: heldout IoU, ego - global128. Sig >0 -> pen-centring helps beyond resolution. Not sig -> cannot separate (do not claim resolution
  explains it either: only "no detectable difference"). Sig <0 -> resolution/whole-sheet view is better than ego.
- SECONDARY: heldout, global128 - global64 (resolution alone). Other sets ego - global128; loss diff-in-diff global128 - ego.
- No optional stopping. Note: global128 has 4x the input pixels, so the network's receptive field covers a smaller fraction of the sheet.
### Honest limits (before running)
2 seeds, 4 shapes, privileged observation, one resolution. A 128-px global view also changes the CNN's effective receptive field, so it is
a control for pixel density, not a perfect "zoom-only" arm.

### O2z zoom control RESULT (2026-11-01; 8/8 runs)
Command: `conda run -n robosketch --no-capture-output python rl/zoom_experiment.py --aggregate`
```
arm                    default               train             heldout       heldout_scale         heldout_rot
global64         0.279 +/-0.066       0.292 +/-0.039       0.118 +/-0.036       0.160 +/-0.073       0.192 +/-0.087
global128        0.226 +/-0.085       0.250 +/-0.042       0.137 +/-0.022       0.174 +/-0.058       0.190 +/-0.069
ego              0.338 +/-0.042       0.340 +/-0.025       0.298 +/-0.042       0.323 +/-0.020       0.311 +/-0.052
PRIMARY   heldout ego - global128   +0.161  8/8 up  t=+8.04
SECONDARY heldout global128 - global64  +0.020  7/8 up  t=+2.03 (below 2.37: not claimed)
ego - global128: train +0.090 (t=+5.05)  default +0.112 (t=+3.12)  heldout_scale +0.148 (t=+5.88)  heldout_rot +0.121 (t=+5.08)
LOSS train->heldout: global64 +0.174, global128 +0.113, ego +0.042;  global128 - ego +0.071  8/8 up  t=+3.39
```
Hand check: 0.298-0.137=0.161; 0.250-0.137=0.113; 0.113-0.042=0.071.
**Reading (pre-registered branch 1):** pen-centring helps beyond pixel density. Matching the ego arm's resolution without centring recovers
none of the held-out gain (+0.020, t=+2.03, not significant) and is WORSE at home (train 0.250 vs 0.292, default 0.226 vs 0.279; not tested
formally). So the O2 gain is attributed to the pen-centred view, not to zoom alone, within this control's limits.
### Honest limits
- n=8 cells, 200k steps, privileged observation, one resolution. global128 enlarges the input 4x, so it also shrinks the CNN's effective
  receptive field relative to the sheet and may simply train worse at 200k; it controls pixel density, not "zoom" in every sense.
- Home-set drop of global128 vs global64 was not pre-registered or tested; do not quote it as an effect.
- Still no camera observation; simulation only.

## 2026-11-02 - O2c egocentric + camera launched: does the ego gain survive perception? (pre-registered)
### Why
O2/O2z showed the pen-centred view is a lever on the generalisation limit, but only with the PRIVILEGED canvas observation. The project
claim is about perception, so the test that matters is whether it holds when the agent only sees a photo.
### What changed (additive; backup `rl/draw_env.py.bak_pre_egocam`)
`obs_view="ego"` now also accepts `cam_split` (camera in the loop): the drawn channel is the camera photo (`_seen()`) instead of the true canvas.
Checked: no-camera global and ego envs bit-identical to the pre-change env (4 shapes x 40 steps each); ego+camera drawn channel equals an
independent zero-padded crop of the photo (0 differing px, 4 shapes x 40 steps). Target and sheet-mask channels are unchanged.
### Design (`rl/egocam_experiment.py`, results `results/egocam_a/b.jsonl`)
Arms `global_cam` (whole sheet, 64 px) and `ego_cam` (64-px pen-centred window), both: vision reward, cam_split="train" in training, trained on
the "train" size/rotation family, 200k steps, gen2 PPO settings. Scored (TRUE IoU) under the HELD-OUT camera distribution on default /
train / heldout / heldout_scale / heldout_rot (16 targets each). 4 shapes x seeds {0,100} x 2 arms = 16 runs. Camera makes the env ~14x slower
(0.014 s/step vs ~0.001), so ~8 h with two workers (OMP=1). This exceeds the usual ~6 h ask-first limit; the user asked for work to continue
overnight while asleep, and the sweep is resumable and stoppable.
### Pre-registered analysis (n=8 cells, paired, crit |t|=2.365)
- PRIMARY: heldout IoU, ego_cam - global_cam. Sig >0 -> the gain survives perception. Not sig -> no detectable gain under perception (do not
  say "no effect"). Sig <0 -> ego hurts under perception.
- SECONDARY: same on train/default/heldout_scale/heldout_rot; LOSS (train->heldout) global_cam - ego_cam (diff-in-diff).
- DESCRIPTIVE only: ego_cam heldout vs privileged ego heldout (different observation and camera-at-test; not a controlled comparison).
- No optional stopping.
### Honest limits (stated before running)
2 seeds, 4 simple shapes, simulated camera (held-out camera distribution is still the project's own simulator), pen position is the true one
(the pen-marker is not needed for ego, but ego relies on knowing where the pen is; a real robot would estimate it from kinematics).

### O2c RESULT (2026-11-02; 16/16 runs, finished 05:31, no restarts)
Command: `conda run -n robosketch --no-capture-output python rl/egocam_experiment.py --aggregate`
```
=== O2c ego vs global, CAMERA in the loop (held-out camera at test): TRUE IoU, n=8 cells ===
arm                      default               train             heldout       heldout_scale         heldout_rot
global_cam         0.279 +/-0.066       0.319 +/-0.032       0.130 +/-0.039       0.178 +/-0.078       0.219 +/-0.093
ego_cam            0.336 +/-0.056       0.311 +/-0.047       0.273 +/-0.079       0.287 +/-0.055       0.290 +/-0.080
PRIMARY   heldout: ego_cam - global_cam   +0.143  6/8 up  t=+3.54
SECONDARY train -0.008 (3/8, t=-0.70)  default +0.057 (5/8, t=+1.58)  heldout_scale +0.109 (6/8, t=+2.42)  heldout_rot +0.071 (5/8, t=+2.22)
LOSS train->heldout: global_cam +0.189, ego_cam +0.038;  global_cam - ego_cam +0.152  7/8 up  t=+4.25
DESCRIPTIVE ego heldout: privileged 0.298 -> camera 0.273 (not a controlled comparison)
per-cell heldout (global_cam / ego_cam): circle .104/.334 .073/.328; line .192/.149 .176/.147; square .142/.291 .124/.319; triangle .127/.323 .103/.296
```
Hand check: 0.273-0.130=0.143; 0.311-0.273=0.038; 0.319-0.130=0.189; 0.189-0.038=0.151 (script 0.152 from unrounded).
**Reading (pre-registered branch 1: primary significant >0):** the ego gain SURVIVES perception. With the agent seeing only a photo through a
held-out camera, held-out IoU rises 0.130 -> 0.273 (+0.143, t=+3.54) and the train->held-out loss falls 0.189 -> 0.038 (diff-in-diff +0.152,
t=+4.25). Unlike the privileged case, there is NO gain at home (train -0.008, t=-0.70; default +0.057, t=+1.58, n.s.): the benefit is
specifically in generalisation. The gain is smaller than privileged (+0.181) and ego_cam heldout 0.273 vs privileged ego 0.298, but those
are not a controlled comparison.
**Exception worth reporting:** `line` goes the other way in both seeds (ego 0.149/0.147 vs global 0.192/0.176): 6/8 up, not 8/8. A line
has no 2-D layout to memorise and the global view already generalises best there; the ego window loses the long-range context. I did not
test why; it is an observation, not a finding.
### Honest limits
- n=8 cells, 200k steps, simulated camera (held-out camera distribution of the project's own simulator), 4 simple shapes.
- Pen position is assumed known (true kinematics); on hardware it must be estimated. Not tested with disturbances (H4) in ego mode.
- heldout_scale t=+2.42 and heldout_rot t=+2.22: only the first just clears 2.37; do not claim factor-specific effects.
- The perception-cost comparison (0.298 -> 0.273) mixes observation type and test camera; do not quote it as a controlled cost.

## 2026-11-02 - O3 CoordConv launched: does explicit position help the global view generalise? (pre-registered; Stage 4)
### Why
Ego beat the global view mainly on held-out targets (O2/O2z/O2c). One reading is that a plain CNN on the whole sheet is poor at using
ABSOLUTE position; CoordConv (Liu et al. 2018) is the standard cheap fix. If CoordConv closes the gap, the ego gain is "position handling";
if not, it is about the pen-relative frame. Stage 4 item O3 in HANDOFF.
### What changed (additive, default OFF; backup `rl/draw_env.py.bak_pre_coord`)
`DrawEnv(coord_channels=True)` appends two planes (column ramp, row ramp, 0..255) to the global observation (5 channels). Checked: default
global and ego envs bit-identical to the pre-change env (4 shapes x 40 steps); first 3 planes unchanged with coord on; SB3 CnnPolicy builds a
5-channel NatureCNN and trains. Input-level CoordConv only (no coord conv inside the network).
### Design (`rl/coord_experiment.py`, results `results/coord_a/b.jsonl`)
Arm `coord`: gen2 `param200` protocol (train family, 200k, vision reward, privileged obs, global 64 px) + coord planes; 4 shapes x seeds {0,100}
= 8 runs, paired by cell with `param200` (and `ego` for context). ~70 min.
### Pre-registered analysis (n=8, crit |t|=2.365)
- PRIMARY: heldout IoU, coord - global. Sig >0 -> position handling is part of the problem (say how much of the 0.180 ego-global gap it closes).
  Not sig -> input-level CoordConv does not help (not "position does not matter"). Sig <0 -> hurts.
- SECONDARY: other sets; LOSS global - coord. Context (descriptive): ego arm.
### Honest limits (before running)
2 seeds, 4 shapes, privileged obs, input-level coordinates only; the pen marker already gives the global view one position cue.

### O3 CoordConv RESULT (2026-11-04; 8/8 runs)
Interruption: PC restarts (Kernel-Power 41 at 2026-11-02 12:00, 2026-11-03 10:11 and 12:04) killed the workers with 2/4 rows per shard done; relaunched the same
commands on 2026-11-04 17:2x, finished 18:12. Resume is bit-identical at OMP=1 (verified earlier for param200).
Command: `conda run -n robosketch --no-capture-output python rl/coord_experiment.py --aggregate`
```
arm                    default               train             heldout       heldout_scale         heldout_rot
global           0.279 +/-0.066       0.292 +/-0.039       0.118 +/-0.036       0.160 +/-0.073       0.192 +/-0.087
coord            0.330 +/-0.058       0.331 +/-0.046       0.126 +/-0.024       0.179 +/-0.072       0.210 +/-0.102
ego              0.338 +/-0.042       0.340 +/-0.025       0.298 +/-0.042       0.323 +/-0.020       0.311 +/-0.052
PRIMARY   heldout: coord - global   +0.008  4/8 up  t=+0.97
SECONDARY train +0.039 (8/8, t=+8.32)  default +0.051 (5/8, t=+1.94)  heldout_scale +0.019 (7/8, t=+2.72)  heldout_rot +0.018 (7/8, t=+2.37)
LOSS train->heldout: global +0.174, coord +0.205, ego +0.042;  global - coord  -0.031  1/8 up  t=-2.98
```
Hand check: 0.126-0.118=0.008; 0.331-0.292=0.039; 0.331-0.126=0.205; 0.174-0.205=-0.031.
**Reading (pre-registered branch 2: primary not significant):** input-level CoordConv does NOT help the global view generalise (held-out +0.008,
t=+0.97; it closes ~4% of the 0.180 ego-global gap). It does improve fit on the training family (train +0.039, 8/8, t=+8.32), so the
train->held-out loss actually GROWS (0.174 -> 0.205; diff-in-diff t=-2.98 in the "coord loses more" direction, secondary). Reading: better position
handling helps where the shapes were seen and does not extrapolate; the ego gain is therefore not just "position handling" at the input.
### Honest limits
- n=8, 200k steps, privileged observation, input-level coordinate planes only (no coordinate-aware layers inside the network, no spatial softmax).
- The train gain (t=+8.32) is a secondary result under multiple comparisons; the loss t=-2.98 was a pre-registered LOSS contrast but secondary.
- "Not significant" means no detectable effect at n=8, not no effect. Does not test why ego works (pen-relative frame is the remaining hypothesis, untested).

## 2026-11-04 - C5 4th arm launched: is the plateau-stop gain just a shorter horizon? (pre-registered)
### Why
PAPER_PLAN C5 and the HANDOFF open issue: `plateau_patience` has no grace period, so the plateau arm (+0.055 IoU, 7/8, t=+2.56, ~50-step
episodes) trains on ~5x shorter episodes from step 1; its gain is confounded with a shorter exploration horizon. C5 stays "AT RISK" until a 4th arm separates them.
### Design (`rl/short_arm.py`, results `results/short_arm_a/b.jsonl`; no env change)
Arm `short50`: `max_steps=50` (train AND eval), no plateau stop, no stop head; truth reward, 200k steps, 8 envs, step 0.014, eval_eps 8 (the defaults of
`experiment.train_eval`, as in `overshoot_ablation.py`). 4 shapes x seeds {0,1} = 8 runs, paired by (shape, seed) with the EXISTING baseline and plateau
runs in `results/overshoot_ablation*.jsonl` (not re-run). 50 = the plateau arm's mean episode length (50 steps).
### Pre-registered analysis (n=8, paired, crit |t|=2.365)
- PRIMARY: IoU, plateau - short50. Sig >0 -> adaptive stopping adds something beyond a short horizon (gain is NOT only the horizon). Not sig -> cannot
  separate them; do not claim the plateau stop is a fix beyond what a short horizon gives. Sig <0 -> a plain short horizon is better than the plateau stop.
- SECONDARY: short50 - baseline (how much of the +0.055 a short horizon alone gives); peak and overshoot contrasts plateau - short50.
### Honest limits (stated before running)
Seeds 0 and 1 share 7 of 8 env streams (F6) - kept ONLY to pair with the old runs; the old runs did not record thread counts, so this arm (OMP=1) may not be
bitwise-comparable with them; one horizon (50) only; short50's final IoU is at step <=50 where the plateau arm's is at its (variable) stop step.

## 2026-11-04 - Infrastructure: automatic restart of sweeps and unattended agent (not a research result)
### What and why
User asked that project work never stops when the laptop is on and resumes by itself after a reboot or a wifi change.
PC had restarted unexpectedly 4x (Kernel-Power 41) and killed workers each time. Two Task Scheduler tasks (user logon, no admin):
- `RoboSketch-KeepAlive` -> `tools/keepalive.ps1` (logon + every 5 min): relaunches any unfinished job in `tools/jobs.json` through
  `tools/run_job.ps1` (OMP/MKL=1 as in AGENTS.md section 5; exit 0 -> `tools/done/<name>.done`; gives up after 20 failed launches).
  Sweeps need no internet, so wifi loss does not affect them. Safe because every sweep is resumable and bit-identical on resume.
- `RoboSketch-Agent` -> `tools/agent_run.ps1` (logon, every 10 min, ~30 s after a network-connect event): starts one unattended
  `claude -p` "continue" session when internet is up, no interactive session was active in 30 min, >=60 min since the last one, <8 per day.
  Allowed tools: read/edit/write + read-only PowerShell + `conda run`; denied: Remove-Item, Stop-Process, git, web. New sweeps only via jobs.json.
Alternatives rejected: `--dangerously-skip-permissions` (unattended agent with full shell); Windows service / auto-login (needs password storage).
### Verified
Dry run with running workers relaunched nothing; fake exit-3 / exit-0 jobs recorded correctly; permission test (read allowed, Remove-Item denied, file kept);
offline detection (unresolvable host -> skip); task children survive the end of the scheduled task; worker end-to-end with a harmless prompt (exit 0).
### Honest limits
- Needs the user logged in (after an unexpected reboot, work resumes only after login). Not tested: a real reboot, a real wifi drop.
- The real "continue" session was NOT run yet (it would clash with the interactive session that built this). First real run: when idle >30 min.
- An unattended agent can still make wrong analysis decisions; its log entries must be checked like Antigravity's (see memory note).
- Killed-on-purpose workers come back within 5 min unless `tools/STOP` exists.

### C5 4th arm RESULT (2026-11-04; 8/8 runs, finished 19:21, no restarts)
Command: `conda run -n robosketch --no-capture-output python rl/short_arm.py --aggregate`
```
arm                    IoU    peak  overshoot  steps
baseline      0.378 +/-0.056   0.411      0.034    240
plateau       0.433 +/-0.043   0.442      0.009     50
short50       0.417 +/-0.054   0.433      0.016     50
PRIMARY   IoU: plateau - short50          +0.016  6/8 up  t=+0.63
SECONDARY IoU: short50 - baseline         +0.039  6/8 up  t=+1.59
          IoU: plateau - baseline (ref)   +0.055  7/8 up  t=+2.56
          peak: plateau - short50         +0.009  6/8 up  t=+0.41
          overshoot: plateau - short50    -0.007  4/8 up  t=-0.98
per cell IoU (baseline/plateau/short50): circle s0 .353/.437/.367 s1 .313/.449/.337; line s0 .334/.451/.451 s1 .329/.348/.462;
  square s0 .465/.479/.432 s1 .411/.443/.497; triangle s0 .378/.464/.411 s1 .440/.393/.378
```
Hand check: 0.433-0.417=0.016; 0.417-0.378=0.039; 0.039/0.055 = 0.71.
**Reading (pre-registered branch 2: primary not significant):** the plateau stop and a plain 50-step horizon cannot be separated (+0.016, t=+0.63,
6/8). A short horizon alone gives +0.039 of the +0.055 (about 71%), though that contrast is itself not significant (t=+1.59). So the C5 claim
"an environment-side plateau stop is a FIX" is NOT supported beyond "shorter episodes help"; most of its gain is plausibly the horizon.
The overrun/overshoot MEASUREMENT (agents finish early and then damage their drawing) is unaffected - that is still the finding; the remedy is
"don't give the agent a long idle horizon", with no evidence that adaptive stopping beats a fixed short one.
Observation only (not tested): circle is the one shape where plateau beats short50 in both seeds (0.437/0.449 vs 0.367/0.337).
### Honest limits
- n=8 cells; seeds 0 and 1 share 7 of 8 env streams (F6), kept only to pair with the old runs, so the effective n is smaller than 8.
- Old baseline/plateau runs have no recorded thread count; short50 ran at OMP=1 - not guaranteed bitwise-comparable.
- One horizon (50, chosen = plateau's mean length). A shape-specific or tuned horizon was not tried (and should not be tuned to hit a target).
- "Not significant" = no detectable difference at this n, not "identical".

## 2026-11-04 - A1 action chunking launched: does predicting 5 moves at once help? (pre-registered; Stage 4; unattended auto-session)
### Why
Proposal 3.2 A1 / HANDOFF Next item 2. D02 ("action bundle", K=5) reports chunking improves performance and learning speed in this task family;
our policy outputs one (dx, dy) per step and relies on `smooth_penalty` for smooth strokes. Controlled ablation vs `param200`, first target = held-out IoU.
T1 (BC warm start) is left for a later session (one piece of work per session).
### Design (`rl/chunk_experiment.py`, results `results/chunk_a/b.jsonl`; NO change to draw_env.py - a gymnasium wrapper in the script)
Arm `chunk5`: param200 protocol (train family, vision reward, privileged obs, global 64 px, max_steps 240, step 0.014, eval 16 targets x 5 sets,
same eval seeds) but each policy decision outputs K=5 actions (15 numbers), executed in order; the chunk ends early if the episode ends.
Decision reward = sum_i 0.99^i r_i. To compare at the SAME number of environment steps (200k), per-decision PPO settings are rescaled:
40k decisions, gamma 0.99^5, n_steps 128 (rollout 5120 env steps vs 4096), batch 64 (16 minibatches/epoch as param200); everything else equal.
K=5 fixed in advance (D02's value); no other K will be tried to chase a number. 4 shapes x seeds {0,100} = 8 runs, paired by cell with param200.
Checks before launch: K=1 wrapper is bit-identical to the raw env over a 240-step random episode; K=5 episode = 48 decisions = 240 env steps;
a 10k-env-step PPO run trains and evaluates (23 s). Launched via `tools/jobs.json` (watchdog, OMP/MKL=1).
### Pre-registered analysis (n=8, paired, crit |t|=2.365)
- PRIMARY: heldout IoU, chunk5 - param200. Sig >0 -> chunking helps generalisation. Not sig -> no detectable effect of chunking at this budget.
  Sig <0 -> chunking hurts.
- SECONDARY: train / default / heldout_scale / heldout_rot contrasts; LOSS train->heldout (param200 - chunk5); peak IoU alongside final.
- DESCRIPTIVE only: chunk5 path_ratio and steps_used (param200 rows did not record path_ratio, so no smoothness comparison is possible).
### Honest limits (stated before running)
- The manipulated factor is "chunking + the rescaling of per-decision PPO settings it requires" (gamma, n_steps, batch), not a single knob.
- One K, one budget (200k env steps); D02's "learning speed" claim is not tested (no learning curves). 2 seeds, 4 shapes, privileged obs.
- smooth_penalty is kept on in both arms, so this does not test "chunking replaces the penalty".

### A1 chunking RESULT (2026-11-05; 8/8 runs, both shards done via watchdog; unattended auto-session)
Output of `python rl/chunk_experiment.py --aggregate` (TRUE IoU, n=8 (shape, seed) cells, 16 targets/set, torch_threads 1):
```
arm                    default               train             heldout       heldout_scale         heldout_rot
param200         0.279 +/-0.066       0.292 +/-0.039       0.118 +/-0.036       0.160 +/-0.073       0.192 +/-0.087
chunk5           0.090 +/-0.031       0.103 +/-0.013       0.120 +/-0.030       0.120 +/-0.032       0.099 +/-0.020
peak IoU
param200                 0.300               0.312               0.140               0.180               0.211
chunk5                   0.101               0.125               0.151               0.146               0.124

PRIMARY    heldout: chunk5 - param200                  +0.003  4/8 up  t=+0.17
SECONDARY  train                                       -0.189  0/8 up  t=-15.55
           default                                     -0.189  0/8 up  t=-6.78
           heldout_scale                               -0.040  2/8 up  t=-1.43
           heldout_rot                                 -0.093  0/8 up  t=-3.42
LOSS train->heldout  param200 +0.174, chunk5 -0.017;  param200 - chunk5 +0.191  8/8 up  t=+8.66
DESCRIPTIVE chunk5: path_ratio default 7.43 train 7.67 heldout 10.35 heldout_scale 9.68 heldout_rot 7.84; steps_used 240 in every set
train env steps per run: 204800 (all 8)
```
Hand check of the differences from the table rows: train 0.103 - 0.292 = -0.189; heldout 0.120 - 0.118 = +0.002 (script +0.003 is
from unrounded values); loss param200 0.292 - 0.118 = 0.174, chunk5 0.103 - 0.120 = -0.017, difference +0.191. All consistent.

### Verdict, as pre-registered
- PRIMARY: held-out IoU went from 0.118 (param200) to 0.120 (chunk5), +0.003, 4/8 up, t=+0.17 -> **no detectable effect of chunking on
  held-out IoU at this budget.**
- SECONDARY: **chunking hurts strongly where param200 had learned something**: train IoU fell from 0.292 to 0.103 (-0.189, 0/8, t=-15.55),
  default -0.189 (t=-6.78), heldout_rot -0.093 (t=-3.42); heldout_scale -0.040 (n.s.).
- The LOSS contrast (+0.191, t=+8.66, "chunk5 loses less") must NOT be read as better generalisation: chunk5 scores ~0.10-0.12 on every
  set, i.e. it never learned the training shapes, so it has nothing to lose (floor effect; AGENTS.md rule 4 - the arms start at very
  different levels). Held-out "parity" is two arms that both fail on held-out targets, not chunking helping.
- Behaviour: chunk5 never stops (steps_used = 240 = max_steps in every set) and draws 7-10x the target path length (path_ratio) -
  it scribbles for the whole episode. Peak IoU is close to final (0.125 vs 0.103 train), so this is not an overshoot-after-success story.

### Leading explanation (hypothesis, NOT tested)
With K=5 the agent gets only 40k decisions (vs 200k for param200) and must output 15 numbers at once with one shared reward per chunk;
at 200k env steps that is too little for PPO to learn even the training shapes. This contradicts D02's report that chunking helps, but our
setup differs (PPO not D02's algorithm, rescaled gamma/n_steps/batch, privileged obs, smooth_penalty kept). Per AGENTS.md rule 6, no
re-tuning (other K, more steps, different PPO settings) was tried to rescue the arm; K=5 was fixed in advance.

### Honest limits
- n=8 (4 shapes x seeds {0,100}), one K, one budget. A longer budget might let chunk5 learn - not tested, so "chunking hurts" is only
  "at 200k env steps with this rescaling".
- The manipulated factor is chunking + the PPO rescaling it forced; cannot say which part did the damage.
- No learning curves, so D02's learning-speed claim is neither confirmed nor refuted directly (final-score evidence points against it here).
- param200 rows did not record path_ratio/steps_used, so the scribbling description is chunk5-only.
- For the paper: A1 is a negative ablation. Allowed wording: "action chunking (K=5) gave no detectable held-out benefit and markedly
  reduced in-distribution accuracy at equal environment steps".

## 2026-11-05 - T1 BC warm start launched: does cloning a perfect tracer first help PPO? (pre-registered; Stage 4; unattended auto-session)
### Why
Proposal 3.4 / section 8 item 14, the last open Stage 4 ablation (HANDOFF Next item 0). Four papers in the library use "prior -> clone ->
refine" (D07, D08, D09, A07). Our targets are analytic, so perfect demonstrations are free. Question: does starting PPO from a cloned
expert improve held-out IoU (and train IoU) over `param200`? Alternatives considered: DAgger (needs an expert query per policy state - more
code, a second variable), BC-only (no RL - not the question), and dropping the shaping crutches (prox_weight, start_on_target) at the same
time (two variables at once - left for later, only if BC helps).
### Design (`rl/bc_experiment.py`, results `results/bc_a/b.jsonl`; NO change to draw_env.py)
Arm `bc200` = param200 protocol exactly (train family, vision reward, privileged global 64-px obs, max_steps 240, step 0.014, 8 envs,
PPO n_steps 512 / batch 256 / 6 epochs / gamma 0.99 / ent 0.02 / lr 3e-4, 200k PPO steps, same seed, same 16 eval targets x 5 sets),
plus, before PPO:
- **Expert**: privileged analytic tracer (reads the env's scale/rotation). From the pen start it walks the outline at full step length
  (closed shapes once round back to the start, line to the nearer end then the far end), then holds still.
- **Demos**: 200 episodes of the TRAIN family only (reset seeds 30000+1000*seed+j; eval targets are 20000-20015, never used), at most 20
  still steps kept per episode.
- **BC**: MSE between the policy's mean (dx, dy) and the expert's, Adam lr 1e-3, 20 epochs, batch 256. log_std and the value head are NOT
  trained, so PPO starts with its normal exploration noise. pen_down is ignored by the env (pen always down) and not cloned.
All BC settings were fixed before seeing any held-out number and will not be changed to chase a result.
Also recorded per run (descriptive): `bc0` = cloned policy before any PPO; `expert` = the tracer itself (a ceiling).
4 shapes x seeds {0,100} = 8 runs, paired by cell with param200 (`results/gen2_*.jsonl`). Queued in `tools/jobs.json` (watchdog, OMP/MKL=1).
### Checks before launch (`python rl/bc_experiment.py --smoke --shapes square`; TRAIN-family targets only, seeds 90000+)
```
expert line     train: final IoU 0.768  peak 0.774  (min 0.710)  path len 0.173 m = 12 steps
expert circle   train: final IoU 0.749  peak 0.750  (min 0.736)  path len 0.367 m = 26 steps
expert square   train: final IoU 0.744  peak 0.744  (min 0.720)  path len 0.467 m = 33 steps
expert triangle train: final IoU 0.734  peak 0.734  (min 0.719)  path len 0.378 m = 27 steps
demos square: 6138 samples, obs (6138, 3, 64, 64), mean |a| 0.539, demo IoU 0.726, 8s
policy obs space (3, 64, 64)
BC loss by epoch: 0.2065 0.0575 0.0300 ... 0.0009 0.0010  (36s)
bc0 square TRAIN-set IoU (8 eps, not eval targets): 0.509
```
Notes: (1) the expert reaches the env's `done_iou` 0.60, so its episodes end early with the +2 bonus. The RL agents on record never
reached it (best peak 0.516). So the idle cap barely applies (6138 samples from 200 episodes). (2) The expert's ~0.73-0.77 shows the task allows far higher IoU than
param200's ~0.29 on train - the ceiling is not the environment. (3) The smoke run did not set OMP/MKL=1 (not permitted in this session);
it is a code check, not a result.
### Pre-registered analysis (n=8, paired, crit |t|=2.365)
- PRIMARY: heldout IoU, bc200 - param200. Sig >0 -> BC warm start helps generalisation. Not sig -> no detectable effect. Sig <0 -> hurts.
- SECONDARY: train / default / heldout_scale / heldout_rot contrasts; LOSS train->heldout (param200 - bc200), read with AGENTS.md rule 4
  (if the arms start at different levels, a smaller loss is not generalisation by itself); peak IoU alongside final.
- DESCRIPTIVE: bc0 and expert on every set; bc200 - bc0 (did PPO keep, improve or destroy the cloned behaviour?); path_ratio.
### Honest limits (stated before running)
- The bc200 arm sees ~6k extra expert transitions that param200 does not, so this is NOT equal-data; it is "free demos + same RL budget".
  On a real robot, demos would need a teleoperator or a scripted tracer that needs the target geometry.
- The expert is privileged (knows the target's exact scale/rotation). Plain BC, no DAgger: errors off the expert's path are not corrected.
- One BC recipe (fixed numbers above), one budget, 2 seeds, 4 shapes, privileged observation. No learning curves.
- Shaping crutches (prox_weight, start_on_target, smooth_penalty) are kept in both arms; this does not test "BC lets us remove them".

### T1 BC warm start RESULT (2026-11-05; 8/8 runs)
Interruption: the two T1 workers hung (0 CPU, no new row from 01:46 to 07:59; found by the unattended auto-session, which could not inspect processes). They were
stopped by hand at 08:00; the watchdog relaunched the same commands (completed rows kept); watchdog output now goes to `tools/job_logs/<name>.log` (`run_job.ps1`,
backup `.bak_pre_log`). A separate code test of the BC pipeline on circle and triangle ran normally, so the cause of the hang is unknown.
Command: `conda run -n robosketch --no-capture-output python rl/bc_experiment.py --aggregate`
```
arm                          default               train             heldout       heldout_scale         heldout_rot
param200               0.279 +/-0.066       0.292 +/-0.039       0.118 +/-0.036       0.160 +/-0.073       0.192 +/-0.087
bc200                  0.309 +/-0.090       0.292 +/-0.065       0.113 +/-0.022       0.165 +/-0.050       0.186 +/-0.071
bc0 (no PPO)           0.443 +/-0.195       0.591 +/-0.028       0.142 +/-0.040       0.262 +/-0.162       0.272 +/-0.194
expert                 0.718 +/-0.038       0.736 +/-0.011       0.725 +/-0.012       0.736 +/-0.011       0.725 +/-0.013
PRIMARY   heldout: bc200 - param200   -0.005  5/8 up  t=-0.39
SECONDARY train +0.000 (t=+0.02)  default +0.030 (t=+0.87)  heldout_scale +0.005 (t=+0.41)  heldout_rot -0.006 (t=-0.32)
LOSS train->heldout: param200 +0.174, bc200 +0.179, bc0 +0.448, expert +0.011;  param200 - bc200 -0.005 (3/8 up, t=-0.21)
DESCRIPTIVE bc200 - bc0: train -0.299 (0/8, t=-10.27), heldout -0.030 (2/8, t=-1.43); path_ratio (heldout) bc200 4.46, bc0 1.92, expert 0.99
```
Hand check: 0.113-0.118=-0.005; 0.292-0.292=0.000; 0.292-0.591=-0.299; 0.174 vs 0.179 loss.
**Reading (pre-registered branch 2: primary not significant):** a behaviour-cloning warm start gives NO detectable benefit after the same PPO budget
(held-out -0.005, t=-0.39; train +0.000). The interesting part is descriptive: the cloned policy BEFORE any RL already scores 0.591 on the training family (2x
param200's 0.292) and PPO then brings it DOWN to 0.292 (-0.299, 0/8, t=-10.27), erasing the head start in every cell. So PPO with this reward/setup does not just fail to
improve on a good starting policy, it unlearns it. The expert reaches 0.72-0.74 on every set (incl. held-out), so the task is not capped at ~0.3: the ceiling is the
learner/reward, not the environment. The cloned policy still collapses on held-out (0.142, loss +0.448): imitating one family does not generalise either.
### Honest limits
- n=8 cells, 200k PPO steps, one BC recipe fixed in advance (200 demos, 20 epochs), privileged expert and observation, plain BC (no DAgger), PPO default noise.
- bc0 -> bc200 collapse is observed, not explained: candidate causes (PPO exploration noise at log_std default, value head untrained so early advantages are
  garbage, shaped reward not aligned with IoU) were NOT tested; do not state any as the cause.
- bc200 saw ~6k extra expert transitions that param200 did not. The expert knows the target's exact scale and rotation.
- Not an equal-data comparison, and nothing here says what a better-initialised value head, lower entropy, or DAgger would do.

## 2026-11-05 - Stage 4 closed; a scripted tracer sets the ceiling (consolidation, no new run)
Stage 4 is complete: only the egocentric view moved held-out accuracy (O2 +0.181, survives a camera in the loop, O2c +0.143); more training (3x), CoordConv (O3), action
chunking (A1, hurts) and a BC warm start (T1) gave nothing. All numbers are in the entries above (`### O2 ... / O2z / O2c / O3 / A1 / T1 RESULT`).
New framing fact from the T1 `expert` row (a scripted outline tracer, privileged, no learning): 0.718 default, 0.736 train, 0.725 held-out TRUE IoU, versus param200 0.279 / 0.292 /
0.118 on the same targets. Added to PAPER_PLAN as row C8 (a limit). Not claimed: that the learner "could" reach the tracer; why PPO unlearns the BC start is untested.

## 2026-11-05 - RQ3 PPO vs SAC NOT run: infeasible on this CPU (decision recorded, no result)
Wrote `rl/sac_experiment.py` (SB3 SAC CnnPolicy, gen2 param200 protocol, buffer 40k, learning_starts 5k, update-to-data ratio 0.25, 8 envs) and timed it (OMP/MKL=1, one
process): 8000 env steps took 576 s, of which ~570 s were ~750 gradient updates (~0.76 s per update at batch 256 on 64x64x3 inputs, 1 thread). Extrapolated: ~50k updates per run
= ~10 h per run, ~40 h for 8 runs on two workers. A cheaper update ratio would starve SAC and make the comparison unfair to it, which proposal 5.5 warns against. So RQ3 is
NOT run here; no SAC number exists and none should be quoted. Options if wanted later: a GPU, a smaller SAC with a small CNN, or a state-based (non-image) comparison. The script is kept
(untested beyond the timing run; it has never produced a result).

## 2026-11-05 - RQ4 curriculum launched: does a line-pretrained policy help circle / square / triangle? (pre-registered; Stage 5, proposal 4.6)
### Why
Proposal 4.6: the shape ladder (line -> circle -> square -> triangle) is an untested assumption; a negative result is reportable. Measured with the R04 transfer metrics:
jump-start, time-to-threshold, asymptotic performance.
### Design (`rl/curriculum_experiment.py`, results `results/curriculum_a/b.jsonl`; NO env change)
Protocol = the fixed-target H2/generalisation setup (default target of the shape, vision reward, privileged global 64-px obs, 240 steps, step 0.014, 8 envs, gen2 PPO settings).
Arm `scratch`: untrained policy, 200k PPO steps on the target shape. Arm `from_line`: 100k PPO steps on `line` first (EXTRA steps, not counted in the 200k), then the same 200k steps on
the target. Targets circle, square, triangle; seeds {0,100}; 12 runs. Evaluated at 0 / 50k / 100k / 150k / 200k target steps on the default target with ONE deterministic episode (the
evaluation is deterministic, so more episodes would repeat it; this makes each IoU a noisy single number). Smoke-tested (tiny budgets, both arms run end to end, nothing recorded).
### Pre-registered analysis (n=6 paired cells (3 shapes x 2 seeds), crit |t| ~2.57 at df=5)
- PRIMARY: final IoU (200k target steps), from_line - scratch. Sig >0 -> the line-first curriculum helps asymptotically. Not sig -> no detectable effect. Sig <0 -> hurts.
- SECONDARY: jump-start (0 target steps), IoU at 50k and 100k, time to IoU >= 0.35 (threshold fixed now; "never" counted as 250k).
### Honest limits (stated before running)
n=6 cells, one deterministic episode per run, 2 seeds, one source rung (line) and one budget; from_line gets 100k extra steps overall (so a gain could just be more total training: it is a
curriculum-vs-scratch comparison at equal TARGET steps, not at equal total steps); no learning-curve smoothing; fixed default targets only.

## 2026-11-05 - 4.7 ergodic-control baseline: setup fixed before the full run (pre-registered; no training)
`rl/ergodic_baseline.py`: greedy spectral-multiscale (SMC) ergodic control (D04): target density = normalised target mask on a 64x64 grid, cosine Fourier basis K=10 per axis, Lambda_k = (1+|k|^2)^-1.5,
16 unit directions per step (full step length 0.014, as for the learned agents), 240 steps, pen always down. Hyper-parameters fixed now and NOT to be tuned. Scoring and targets = the learned agents'
(default / train / heldout / heldout_scale / heldout_rot; reset seeds 20000+ep; 16 targets; TRUE IoU by DrawEnv). Deterministic: no seeds, so comparison with the learned agents is DESCRIPTIVE (their per-shape
means over seeds 0/100), not paired. Pre-run checks: a uniform density gives only the DC coefficient (basis normalisation correct); one smoke episode per shape on the default set (reset seed 20000) ran
(IoU 0.24-0.35, path_ratio 7-26) - that is episode 0 of the default eval set, so it was seen before the full run; nothing was changed afterwards.
### Honest limits (stated before running)
Privileged (reads the target mask, no camera); greedy one-step SMC, no planning; no stopping rule, so final IoU after 240 steps is reported with peak IoU; target mask is mapped to sheet coordinates
with a half-pixel convention approximation; one parameter setting only. A "classical baseline" in the sense of proposal 4.7 would also use perception (FRIDA/e-David-style); this is the non-learning,
target-aware part only.

### Ergodic baseline RESULT (2026-11-05; deterministic, 4 shapes x 5 sets x 16 targets; saved to `results/ergodic_baseline.json`)
Command: `conda run -n robosketch --no-capture-output python rl/ergodic_baseline.py` (script's printed output; means over the 4 shapes):
```
set               ergodic     ppo (param200, mean of seeds 0/100)
default             0.300   0.279
train               0.305   0.292
heldout             0.306   0.118
heldout_scale       0.312   0.160
heldout_rot         0.301   0.192
per shape (default set): line 0.243  circle 0.343  square 0.349  triangle 0.264
final vs peak IoU (heldout, per shape): line 0.267/0.486  circle 0.338/0.401  square 0.310/0.336  triangle 0.308/0.343;  path_ratio 8-35 (draws far more than the outline)
```
**Reading (descriptive; no paired test is possible, the method is deterministic):** a non-learning ergodic controller that reads the target mask scores ~0.30 on EVERY set, i.e. about the same as the
learned PPO agent on the sets it was trained for (0.279-0.292) and far above it on held-out targets (0.306 vs 0.118): it does not care about scale or rotation. Both sit far below the scripted
outline tracer of T1 (0.72-0.74), because ergodic control spreads time over the whole outline neighbourhood and over-draws (path_ratio 8-35, final IoU well under peak on line: 0.267 vs 0.486).
So against this classical comparator the learned agent is NOT better at home and is much worse off-distribution; the ego-view agent (held-out 0.298) is about level with it, not above.
### Honest limits
- Privileged (reads the target) and single parameter setting fixed in advance; greedy one-step SMC; no stopping rule (final IoU after 240 steps; peak shown); not a perception-based classical baseline.
- Compared with the learned agents by pooled means, not paired runs; the PPO numbers are 2 seeds. Do not turn the 0.300 vs 0.279 difference into a claim.
- Does NOT test camera-based classical drawing (FRIDA/e-David-like closed loop); that stays open.

### RQ4 curriculum RESULT (2026-11-05; 12 runs, both shards done; `python rl/curriculum_experiment.py --aggregate`)
n=6 paired (shape, seed) cells, TRUE IoU of ONE deterministic episode on the default target, mean over cells; target steps only (from_line's 100k line steps are extra):
```
target steps        0k      50k     100k     150k     200k
scratch           0.019   0.327   0.391   0.404   0.418
from_line         0.018   0.096   0.177   0.236   0.246
PRIMARY  final IoU, from_line - scratch          -0.173  1/6 up  t=-2.99   (crit ~2.57)
jump-start (0 target steps)                      -0.001  2/6 up  t=-0.12
IoU at 50k / 100k target steps                   -0.230 (0/6 up, t=-11.10) / -0.214 (0/6 up, t=-5.16)
time to IoU>=0.35: scratch mean 125k, from_line mean 233k; never reached within 200k: scratch 1/6, from_line 5/6
per cell final (scratch -> from_line): circle s0 .499->.147, s100 .376->.252; square s0 .445->.277, s100 .340->.263; triangle s0 .511->.187, s100 .338->.348
```
Hand check: the six per-cell differences (-.352, -.124, -.168, -.077, -.324, +.010) sum to -1.035, mean -0.1725 = the printed -0.173 (printed means differ by rounding, 0.418 - 0.246).
**Reading (pre-registered rule: sig <0 -> hurts):** the line-first curriculum made the final result WORSE by 0.173 IoU (fell from 0.418 to 0.246), 5 of 6 cells worse, t=-2.99, past the critical value.
Jump-start is ~0 (a line policy does not draw a circle/square/triangle at all), and from_line is behind at every checkpoint (50k: 0/6 cells better); the time-to-0.35 gap goes the same way.
So the proposal's shape ladder (line -> circle -> square -> triangle) is NOT supported in this setup; this is negative transfer, reported as a result.
### Honest limits
- n=6 cells, 2 seeds, one deterministic episode per run (noisy), one source rung (line), one pre-training budget (100k), fixed default targets; the t is a paired t-test on 6 cells and the seeds within a shape are not independent draws of "shape".
- Cause NOT tested. Plausible, untested: the line-trained policy and its value function / low-entropy action distribution are a bad start for a different shape (cf. T1, where PPO also unlearned a good BC start). Do not state a mechanism in the paper.
- Does NOT say curricula never help: other source rungs (e.g. circle -> square), lr/entropy resets at the switch, or larger budgets were not tried. It says: this naive "pre-train on line, then continue" does not.
- from_line had 100k MORE total steps and was still behind, so the verdict is not an artefact of the step accounting (it only strengthens the negative reading).

## 2026-11-05 - A2 pen-free launched: what does giving the agent the pen-up/down decision cost on single-stroke shapes? (pre-registered; Stage 6 step 1)
### Why
Proposal A2: multi-stroke glyphs (digits, letters) are unreachable with `pen_always_down=True`; before touching digits we need to know whether PPO can learn with the extra decision at all and what it costs.
Circle / square / triangle never NEED a pen lift, so any difference from the always-down runs is the cost (or benefit) of the extra decision alone. Alternative considered: go straight to a digit target - rejected, a failure there
could not be separated from "the pen head does not train".
### Design (`rl/penfree_experiment.py`, results `results/penfree_a/b.jsonl`; NO change to `draw_env.py`, `pen_always_down=False` already existed)
Arm `penfree` = the `scratch` arm of RQ4 (default target, vision reward, privileged 64-px obs whose pen marker is 255 when down / 128 when up, 240 steps, step 0.014, 8 envs, gen2 PPO, 200k steps, eval of ONE deterministic
episode at 0/50/100/150/200k) with action[2] > 0.5 = pen down. Paired baseline = the EXISTING RQ4 `scratch` rows (same shapes, seeds {0,100}, same code path), so 6 new runs only. Smoke test (2k-step chunks, triangle): runs end to end.
### Pre-registered analysis (n=6 paired cells, crit |t| ~2.57)
- PRIMARY: final IoU (200k), penfree - always_down. Sig <0 -> the extra decision hurts; sig >0 -> helps; else no detectable effect.
- SECONDARY (penfree only): pen-down fraction of the eval episode and SNR (strokes drawn / target strokes; was ~1 by construction before), peak IoU.
### Stated risk / honest limits (before running)
- No tuning: action[2] is a plain Gaussian head, so at initialisation the pen is down on only ~30% of sampled steps and the deterministic policy has it UP (IoU 0.0 at step 0 in the smoke test); the reward is sparse until the agent
  discovers the pen bit. If it never does, that is the result ("PPO with a plain pen head does not learn to draw"), NOT a reason to add a bias initialisation silently - that would be a separate, logged arm.
- n=6 cells, one deterministic episode per run (noisy), 2 seeds, privileged observation, single-stroke shapes only: does NOT show multi-stroke glyphs can be drawn.

### A2 pen-free RESULT (2026-11-05; 6 runs, both shards done; `python rl/penfree_experiment.py --aggregate`)
n=6 paired (shape, seed) cells; always_down = the RQ4 `scratch` rows; TRUE IoU of ONE deterministic episode, default target:
```
target steps        0k      50k     100k     150k     200k
always_down       0.019   0.327   0.391   0.404   0.418
penfree           0.000   0.088   0.220   0.328   0.329
PRIMARY  final IoU, penfree - always_down: -0.090  1/6 up  t=-2.29  (crit ~2.57)
penfree final: pen-down fraction of the eval episode mean 0.10 (0.07-0.13); SNR mean 1.67 (cells 1.0-2.0); peak IoU 0.331 vs 0.438
per cell final (always_down -> penfree): circle s0 .499->.366, s100 .376->.318; square s0 .445->.405, s100 .340->.277; triangle s0 .511->.251, s100 .338->.354
```
Hand check: per-cell differences (-.133, -.058, -.040, -.063, -.260, +.016) sum -0.538, mean -0.0897 = printed -0.090.
**Reading (pre-registered rule):** |t|=2.29 < 2.57 -> NO DETECTABLE EFFECT on final IoU, although the direction is down (fell from 0.418 to 0.329, 5/6 cells worse). The pen head DOES train (IoU 0.33 from a start of 0.000 where the
deterministic pen is up), but learning is slower (behind at 50k: 0.088 vs 0.327; 100k: 0.220 vs 0.391) and the gap narrows from -0.239 at 50k to -0.090 at 200k.
Secondary: the trained agents keep the pen DOWN on only ~10% of eval steps, and SNR (strokes drawn / target strokes) is 1.67 on average, i.e. SNR is now informative: the drawn ink is fragmented into ~2 strokes
on 4 of 6 cells (it was ~1 by construction before). So the agent learned to ink in short bursts, not to trace continuously.
### Honest limits
- n=6, 2 seeds, one deterministic episode per run, single-stroke shapes only; not significant, so "no detectable effect", not "no cost". A 200k budget may be too short for the slower start.
- The pen-down fraction is of the final eval episode of the final checkpoint; why only ~10% down while IoU is 0.33 was NOT examined (candidate: a few inking bursts on the target plus a policy that mostly hovers; untested).
- Does NOT show that multi-stroke glyphs can be drawn; it only shows that a plain pen head trains on single-stroke shapes at a slower rate.

## 2026-11-06 - Stage 6 step 2a: digit glyph targets + recognisability metric built (tools only, no RL run; unattended auto-session)
### What was done and why
Stage 6 needs (a) multi-stroke targets and (b) a legibility metric, because IoU rewards ink overlap, not readability (proposal 4.5). Built both as NEW files so no existing module changed (`targets.py`, `draw_env.py` untouched; no sweep was running):
- `rl/glyphs.py`: my own schematic stroke skeletons for digits 0-9 (list of polylines per digit; 4, 8, 9 need a pen lift -> unreachable with `pen_always_down=True`); same 512-px canvas, 14-px stroke, 20% margin as `targets.py`. Contact sheet `output/glyph_sheet.png` (checked by eye: all ten read as their digit).
- `rl/recognise.py`: small CNN (3 conv + 2 linear, 32x32 input) trained on augmented renders (scale 0.6-1.05, rot +-20 deg, shift +-8%, width 8-22 px, vertex jitter) -> `results/recognise_cnn.pt`; metric = P(target digit) and top-1 on a drawn canvas. `--calibrate` -> `results/recognise_calibration.json`.
Alternative considered: MNIST/EMNIST classifier - rejected, no offline data, no torchvision/sklearn/scipy in the env, and no web fetch allowed.
### Results (output of `rl/recognise.py --train` / `--calibrate`; torch threads=1, seed 0)
Classifier: val acc 1.000 (last epochs 0.999-1.000), TEST 1.0000 (200/class, same augmentation family) - i.e. a trivially easy task, NOT evidence of generalisation to handwriting.
Calibration = perfect drawing damaged in one controlled way, true IoU vs classifier (n = 10 digits x 4 draws; 10 for level 0):
```
degradation  level    n    IoU  P(target)   top1
shift           10   40  0.441      1.000   1.00
shift           20   40  0.160      1.000   1.00
shift           60   40  0.047      1.000   1.00
wobble           6   40  0.634      1.000   1.00
wobble          16   40  0.343      1.000   1.00
truncate       0.2   40  0.675      0.708   0.70
truncate       0.6   40  0.446      0.335   0.30
truncate       0.8   40  0.335      0.335   0.30
stray            2   40  0.705      0.923   0.93
stray            4   40  0.553      0.740   0.72
controls (max softmax, argmax): line 1.00->'4'; circle 0.99->'3'; square 0.72->'2'; triangle 1.00->'4'; blank 0.56->'1'; scribble(25 random lines) 1.00->'8'
```
(level 0 = IoU 1.000, P 1.000 for every kind; (other levels in the JSON).)
### What this shows
- IoU and recognisability DISSOCIATE, in both directions: a whole-digit shift of 60 px (IoU 0.047) is still read with P=1.00 (the classifier is shift-tolerant by construction: trained with +-41-px shifts), while truncating 20% of each stroke (IoU 0.675) already drops P to 0.71. So IoU alone would mis-rank "misplaced but complete" vs "well placed but unfinished".
- The metric is NOT safe as a standalone legibility score: there is no reject class, so a scribble is read as '8' with P=1.00, a triangle as '4' with 1.00 and a circle as '3' with 0.99. A high P(target) for a canvas full of ink would be meaningless.
### Honest limits
- Classifier trained and tested on my own skeletons only; not human handwriting, not a human legibility study. 100% test accuracy reflects a trivial task, not robustness.
- Calibration is synthetic degradation (4 kinds, hand-chosen levels, one seed), not agent output; no trained agent has drawn a digit yet. n counts are draws, not independent seeds.
- Pre-registered next use (NOT yet run): report P(target) ALONGSIDE true IoU, and require top-1 correct AND a reject-class check before calling a drawing "legible"; the reject class (blank / scribble / non-digit shapes as an 11th class) is not built - if added, log it as a new version, do not overwrite `recognise_cnn.pt`.
- No env change, no sweep launched. A digit-drawing experiment still needs `draw_env.py` to accept glyph targets (additive, default OFF, backup first) - not done, not pre-registered in detail yet.

## 2026-11-06 - Stage 6 step 2b: reject-class recogniser (v2), glyph targets in DrawEnv, digit experiment pre-registered (unattended auto-session)
### What was done and why
(i) `rl/recognise11.py` (NEW; v1 `recognise.py` / `recognise_cnn.pt` untouched): same CNN with an 11th class `reject`, trained on blank canvases, random-line scribbles (3-30 lines), the four non-digit shapes at random size/rotation/shift, and wiggly curves. New files `results/recognise_cnn_v2.pt`, `results/recognise_calibration_v2.json`. Reason: v1 read a scribble as '8' with P=1.00. Rule: `legible` = top-1 is the target AND P(target) >= 0.5.
(ii) `rl/draw_env.py`: additive, default OFF - `shape` in '0'..'9' selects `glyphs.make_glyph`; any other shape name takes the unchanged `T.make` path (checked: `DrawEnv(shape="line")._is_glyph` False; circle obs/target as before). Backup `rl/draw_env.py.bak_pre_glyph`. No sweep was running. glyph + `target_split` is asserted off.
(iii) `rl/digit_experiment.py` + jobs `s6_digits_a/b` in `tools/jobs.json` (not launched by me; the watchdog starts them).
### v2 results (output of `rl/recognise11.py --train --calibrate`; seed 0; torch threads=1 set in code, OMP/MKL env NOT set for this one-off tool run)
Classifier TEST (200/class digits + 400 reject, same augmentation family): all 1.0000, digits 1.0000, reject recall 1.0000.
```
degradation  level    n    IoU  P(target) legible  P(rej)
shift           20   40  0.160      1.000    1.00   0.000
shift           60   40  0.047      0.962    0.97   0.038
wobble          16   40  0.343      1.000    1.00   0.000
truncate       0.2   40  0.675      0.501    0.50   0.298
truncate       0.6   40  0.446      0.142    0.10   0.625
truncate       0.8   40  0.335      0.030    0.00   0.855
stray            1   40  0.811      0.823    0.82   0.122
stray            4   40  0.553      0.341    0.35   0.598
controls P(reject)=1.00 (argmax reject) for line, circle, square, triangle, blank, scribble10/25/40
```
(other levels in the JSON). Compared with v1 the metric is now stricter on damage: truncating 20% of each stroke moved P(target) from 0.708 to 0.501, 60% from 0.335 to 0.142 (v1 -> v2), because ink that looks "unfinished" is now partly sent to `reject`.
### Pre-registered digit experiment (nothing run yet)
Pen-free PPO (as A2: `pen_always_down=False`, vision reward, privileged global 64-px obs, 240 steps, step 0.014, 8 envs, gen2 PPO settings, 200k steps, ONE deterministic eval episode at 0/50/100/150/200k). Digits 1 and 7 (one stroke) vs 4 and 8 (two strokes), seeds {0,100} = 8 runs, 2 workers x 4 runs (~1 h/run in A2 -> roughly 4-5 h wall, below the 6 h limit). Logged per checkpoint: TRUE IoU (the score), peak IoU, pen-down fraction, SNR, P(target), P(reject), legible.
- No hypothesis test and no baseline arm: n=2 per digit, 4 runs per stroke-count group; `--aggregate` prints a per-run table and group means only. Always-down cannot draw 4/8, and the generic cost of the pen bit is already in A2 (-0.090, t=-2.29, n.s.).
- Expectation stated in advance (a guess, not a claim): A2 pen-free agents ink in short bursts (pen down ~10%), so legible rate may be ~0 even at IoU ~0.3. If every run is illegible, that IS the result; no re-tuning.
### Honest limits
- Reject class is trained on my own scribbles/shapes; the four shape controls are in the reject training family (default-parameter shapes), only scribble40 (> 30 lines) is outside it. The classifier test of 1.000 is in-distribution and trivial. Human legibility not measured.
- A vertical line or a tall ellipse is genuinely close to '1' / '0'; perfect glyphs '1','4','7','8' at 128 px were checked and are legible (P >= 0.9999 for 4, 1.0 for the rest), but a clean '1' stroke drawn by an agent could still be partly penalised.
- Calibration is synthetic degradation, one seed; the env change was smoke-tested (60 random steps on circle and '8'), not trained on.
- The v2 tool run did not set OMP/MKL=1 in the shell (the harness refused env edits); v2 weights are therefore not guaranteed bit-reproducible against another thread count.

### Stage 6 digits RESULT (2026-11-07; 8 runs, both shards done; `python rl/digit_experiment.py --aggregate`; descriptive, NO test, as pre-registered)
Pen-free PPO, vision reward, privileged obs, 200k steps, ONE deterministic eval episode; TRUE IoU + recogniser `recognise_cnn_v2` (11 classes incl. reject):
```
digit strokes  seed  finalIoU  peakIoU  P(tgt)  P(rej)  legible  pen-down   SNR
    1       1     0     0.422    0.423    1.00    0.00      yes      0.05  2.00
    1       1   100     0.208    0.208    0.01    0.01       no      0.03  1.00
    7       1     0     0.302    0.302    1.00    0.00      yes      0.08  3.00
    7       1   100     0.303    0.303    1.00    0.00      yes      0.04  1.00
    4       2     0     0.293    0.295    0.00    1.00       no      0.05  2.00
    4       2   100     0.275    0.275    0.05    0.95       no      0.08  2.00
    8       2     0     0.245    0.245    0.00    1.00       no      0.06  4.00
    8       2   100     0.360    0.360    0.03    0.00       no      0.07  2.00
group means at 200k:  1-stroke (1,7) n=4: IoU 0.309, legible 3/4, P(target) 0.75 | 2-stroke (4,8) n=4: IoU 0.293, legible 0/4, P(target) 0.02
mean IoU curve (all runs) 0/50/100/150/200k: 0.000 0.141 0.203 0.268 0.301
```
Hand check: 1-stroke IoU (0.422+0.208+0.302+0.303)/4 = 0.309; 2-stroke (0.293+0.275+0.245+0.360)/4 = 0.293 - match the printed means.
**Reading (descriptive):** the pen-free agent learns to put ink on digit targets at about the same TRUE IoU as on the basic shapes (~0.30, cf. A2 0.329), and the IoU is nearly the same for one- and two-stroke digits
(0.309 vs 0.293). But legibility splits sharply: 3 of 4 one-stroke runs are read as the right digit, 0 of 4 two-stroke runs are (three are rejected as non-digits, the 8/seed100 run is read as some other digit with
P(target) 0.03). So IoU ~0.3 hides the difference that matters for a glyph: **IoU says the two groups are equal, the recogniser says only the one-stroke digits are readable.** This is the case for the
recognisability metric (proposal 4.5) made with our own data. The pre-stated guess (legible rate ~0 everywhere) was wrong for the one-stroke digits.
Pen down on only 3-8% of eval steps (as A2: short inking bursts), SNR 1-4 (fragmented ink even on one-stroke targets).
### Honest limits
- n=2 per digit, 4 per group, one deterministic episode per run, 2 seeds; no hypothesis test (pre-registered as descriptive). "0/4 vs 3/4" is NOT a significant difference.
- Legibility is one in-house CNN with a reject class trained on my own synthetic scribbles; no human rating. A digit '1' is close to a plain vertical line, so a '1' is an easy legibility case.
- Stroke count is confounded with digit identity (only two digits per group): the split could be about 4/8 being harder shapes, not about needing a pen lift. Not separated.
- Privileged observation only; does not test the camera-reward question on digits.

## 2026-11-07 - H4 v4 confirmation launched: fresh seeds {200,300} for ALL H4 arms (pre-registered; user approved the ~12 h run)
### Why
H4 is the answer to D01, the one fatal objection. v4 (2026-10-30) was "partial" on seeds {0,100} only, and it was the 4th H4 design after two nulls, so it is exploratory until replicated.
Alternatives: pooled n=16 only (rejected as primary: seeds 0/100 were already seen, a pooled t would include the data that motivated the claim); 4 arms only (~8 h; rejected because the v4 pre-registration
named seeds {200,300} for ALL arms, and true/open_loop/true_sheet are needed for the full table).
### Design (NO code change to any H4 script or env)
`rl/h4_confirm.py` runs the unchanged `h4_short_experiment.py` (open_loop, true, fk, camera), `h4_v3_experiment.py` (true_sheet, camera_sheet), `h4_v4_experiment.py` (camera_est) with `--seeds 200 300
--timesteps 200000 --max-steps 60`, shards c (line, circle) and d (square, triangle), OMP/MKL=1 via the watchdog. 6 PPO arms x 4 shapes x 2 seeds = 48 runs, ~12 h on 2 workers.
Checks before launch: current `draw_env.py` is bit-identical to the v4-era code (`draw_env.py.bak_pre_param` + `targets.py.bak_pre_param`) on obs/reward/termination/IoU for all 6 arm configs x 4 shapes x 5 disturbance
kinds, 60 random steps each (120/120 identical); `h4_confirm.py --aggregate --seeds 0 100` reproduces the logged v4 table exactly (PRIMARY +0.077, 8/8, t=+6.39).
### Pre-registered analysis (seeds 200/300 ONLY, n=8 cells, crit t(7)=2.365; `python rl/h4_confirm.py --aggregate`)
- PRIMARY: camera_est vs fk, paper_shift diff-in-diff (how much LESS camera_est loses). **Replicated** if sig > 0. Not sig -> v4 NOT replicated, and the paper must say so (D01 stays partly unanswered).
  Sig < 0 -> contradicts v4.
- SECONDARY: camera_est vs camera (paper_shift); REFERENCE: camera_est vs camera_sheet (is the estimate as good as the true offset?).
- Also reported: slip and ink_failure for the primary pair (v4: no detectable effect, ink_failure possibly harmful), clean gap camera_est - fk (not recovery), pooled n=16 as a SECONDARY descriptive line only.
- No optional stopping, no further seeds, no re-tuning whatever the result.
### Honest limits (stated before running)
Same as v4: simulated near-fixed camera, pure-translation paper shift, phase-correlation estimator designed knowing the shift model, 200k steps, 60-step episodes, 10 eval episodes per disturbance. A replication
of the SIMULATION result only; says nothing about a real camera.

### H4 v4 confirmation RESULT (2026-11-08; 48/48 runs, both jobs done; `python rl/h4_confirm.py --aggregate`, seeds 200/300 ONLY = the pre-registered test)
n=8 (shape, seed) cells, TRUE IoU, 10 eval episodes per disturbance, max_steps 60, 200k steps, OMP/MKL=1:
```
                none    slip   paper_shift  ink_failure
open_loop      0.485   0.221     0.185        0.470
true           0.343   0.336     0.243        0.317
fk             0.369   0.361     0.203        0.324
camera         0.358   0.375     0.250        0.352
true_sheet     0.430   0.412     0.403        0.387
camera_sheet   0.423   0.417     0.407        0.386
camera_est     0.375   0.371     0.329        0.333
drop (clean - disturbed), paper_shift: fk +0.165, camera +0.108, camera_est +0.046, camera_sheet +0.016, true +0.100, true_sheet +0.027, open_loop +0.300
PRIMARY   camera_est vs fk,     paper_shift: +0.119  8/8 up  t=+8.32  (crit 2.37)   [slip +0.004 t=+0.37; ink_failure +0.003 t=+0.32]
SECONDARY camera_est vs camera, paper_shift: +0.062  7/8 up  t=+3.86              [slip -0.021 t=-2.64; ink_failure -0.036 0/8 up t=-5.29]
REFERENCE camera_est vs camera_sheet, paper_shift: -0.030  2/8 up  t=-2.42      [slip +0.002; ink_failure -0.005]
          camera_est vs true_sheet,   paper_shift: -0.019  3/8 up  t=-1.12
clean gap camera_est - fk: +0.006  t=+0.37
```
Pooled seeds 0/100/200/300 (n=16, crit 2.13; SECONDARY, descriptive): PRIMARY paper_shift +0.098, 16/16 up, t=+9.32; vs camera +0.064, 14/16, t=+5.27; vs camera_sheet -0.040, 2/16, t=-5.68;
camera_est vs camera on slip -0.017 (t=-2.56) and ink_failure -0.027 (t=-2.76); clean gap camera_est - fk +0.037 (t=+2.50).
Hand check (seeds 200/300): 0.165 - 0.046 = 0.119 (primary); 0.108 - 0.046 = 0.062 (secondary); 0.046 - 0.016 = 0.030, camera_est loses MORE than camera_sheet (reference); ink_failure vs camera: 0.041 - 0.005 = 0.036, camera_est loses more.
**Reading (pre-registered rule): REPLICATED.** On fresh seeds the camera arm that estimates the sheet offset from its own photo loses 0.046 IoU to a paper shift where the kinematics-only (D01) arm loses 0.165:
+0.119 less, 8/8 cells, t=+8.32 - a larger effect than v4 (+0.077). And here the two arms start level (clean gap +0.006, t=+0.37), so this is recovery, not a better starting point.
It is still below the true-offset arm (camera_sheet, -0.030, t=-2.42 - just past crit; vs true_sheet -0.019, n.s.), i.e. the estimate closes most but not all of the gap (0.165 -> 0.046 of 0.165 -> 0.016).
NEW and unwelcome, also seen pooled: compared with the plain world-marker camera arm, camera_est loses MORE to ink_failure (-0.036, 0/8, t=-5.29) and to slip (-0.021, t=-2.64). Plausible, untested: missing or
displaced ink breaks the photo-vs-belief phase correlation, so the estimated marker is wrong exactly when ink is missing. Versus fk these costs are not detectable (ink_failure +0.003, slip +0.004).
**What this means for D01 (simulation only):** for a disturbance kinematics cannot see (the sheet moving), a camera-based agent that estimates the sheet pose recovers most of the loss and beats the camera-free
agent on 16/16 cells over 4 seeds. For disturbances the camera-free agent is not blind to in this setup (slip, ink failure), there is no detectable advantage, and the estimator has a cost relative to a simpler camera arm.
### Honest limits
- Simulation only: near-fixed simulated camera, pure-translation shift, phase-correlation estimator designed by me knowing the shift model. A real camera (perspective, lighting, a hand in view) is untested.
- The H4 SERIES is still exploratory overall (v1, v2 null; v3 privileged; v4 + this replication); what is now confirmed is v4's specific design, not "cameras beat kinematics" in general.
- n=8 per seed pair, 2 new seeds; reference |t| 2.42 is barely past 2.37 - call it "slightly below the true-offset arm", not a precise gap.
- The ink_failure/slip cost of the estimator is a new finding on 2 seeds (pooled t still past crit); cause not tested.
- Arms true and fk swap order vs seeds 0/100 (fk clean 0.369 here vs 0.328 before): single-run IoU varies a lot across seeds; that is why only paired within-cell differences are used.

## 2026-11-08 - Paper draft v2 written (`docs/paper/main.tex`; user chose the paper over re-sizing ink_failure)
### What and why
The 2026-10-19 skeleton (kept as `docs/paper/main.tex.bak_2026-10-19`) pre-dated H2 spaced/TOST, H4 v4 + its replication, generalisation, Stage 4-6. Rewrote it from PAPER_PLAN section 2 (C1-C11) and the
log RESULT entries: abstract, intro contributions, related work (+ ergodic D04), setup (spaced seeds, crit t), H2 (TOST, spaced sweep only, older sweep reported not pooled), H3, DR, H4 (exploratory series ->
v4 -> replication table, seeds 200/300; asymmetry stated; estimator cost stated; ink_failure "barely bites"), overrun (C5 corrected: plateau stop NOT called a fix), generalisation + absolute level
(tracer, ergodic, BC unlearning), extensions (curriculum, pen-free, digits as exploratory), discussion, limitations, conclusion. Framing = PAPER_PLAN section 3 "better on paper_shift only" row.
Every decimal carries a `% src:` log reference. `check_paper.py`: one rule changed - "equivalent" is now allowed only when "TOST" is on the same line (PAPER_PLAN s4.2-3 allows it after the TOST of
2026-10-31); everything else unchanged. Result: **0 errors, 5 TODOs** (authors, quote re-check vs PDFs, e-David citation, acknowledgment/AI-use disclosure, header note).
`\cite{R05}` (Gymnasium) removed: flagged VERIFY in references.bib.
### Honest limits
- Not proof-read by a human; numbers were checked against the log entries by me, not by an independent reader. No page-budget pass yet (likely > 6 pages).
- Title is the working title from PAPER_PLAN; the user/guide should choose. Authors unknown to me.
- Figure for H4 replication not made (the existing `output/h4_v4_disturbance_recovery.png` shows seeds 0/100 only); the paper uses a table instead.

### Paper: intro quotes checked against the PDFs; D01 description corrected (2026-11-08; unattended auto-session)
- **What was done:** read the three quoted passages in the original PDFs (`research_papers/02_Directly_Related/`). All three match the PDF text exactly:
  D01 Lee et al. p.6 Sec. V ("using a camera as an observation of canvas in the future work could be of great help in the synchronization step"),
  D03 Kotani & Tellex p.6 Sec. V ("closing the learning loop by enabling the robot to inspect what it has drawn"),
  D09 Luo et al. p.6 Sec. V ("a lack of real-world training scenarios to bridge the sim2real gap"). The quote TODO was removed.
- **Correction found while checking:** the intro said D01 synchronises "through forward kinematics, assuming that every commanded stroke landed as planned".
  The PDF (p.4, Sec. III-D) says something different: the Stroker "conveys the changed pen position to the Commander to update the imaginary canvas... without camera".
  So D01 uses the pen position the arm *actually reached*, not the *commanded* stroke. It catches arm tracking error, but not what happens on the paper (slip, sheet shift, ink).
  Reworded to "the pen position the arm actually reaches... assumes that wherever the pen tip went, the mark appeared in the expected place on the sheet". D01 p.6 (Sec. IV-B)
  also supports "they attribute their agent's robustness to this camera-free design" ("We attribute our agent's robustness to our camera-free methodology").
  Our `fk` arm (drawn channel = what kinematics predicts from the reached pen position) still matches this description, so no experiment is affected.
- **Not done:** local compile / page-budget pass. MiKTeX commands need a permission approval that an unattended session cannot get. Still pending for an attended session.
- `check_paper.py`: **0 errors, 4 TODOs** (authors, e-David citation, acknowledgment/AI-use disclosure, header TODO macro definition line).
### Honest limits
- Only the three quoted sentences and the D01 synchronisation paraphrase were checked against PDFs. Other paraphrases of prior work in Related Work were not re-checked in this pass.

### Paper: Related Work paraphrases checked against the PDFs; CalliRewrite sentence corrected (2026-11-08; unattended auto-session)
- **What was done:** every prior-work description in Related Work (`docs/paper/main.tex`) was compared with the original PDF in `research_papers/` (HANDOFF Next item 1, "re-check other Related Work paraphrases").
  Checked and **matching**: D02 Huang (neural renderer, model-based DDPG; reward = drop in discriminator score, p.3 Eq.1 + Sec. 3.3.3 WGAN reward), D05 SPIRAL (discriminator output as reward; black-box graphics engine, p.1),
  D06 Improved SPIRAL (discriminator rewards, p.1), D07 Zhou (Doodle-SDQ: stroke demonstrations + deep Q-learning, p.1), D03 Kotani & Tellex (learns from stroke-order demonstrations, not RL, p.1),
  D01 Lee (two decoupled policies, stroke-based rendering + motor control, p.1), D04 Prabhakar (ergodic control, no learning, p.1), R01 Sermanet (pretrained features + few demos -> dense perceptual reward, p.1),
  R02 Singh (image classifier reward, real robot, end to end, p.1), A01 FRIDA (differentiable real2sim2real simulator, replans from visual perception, p.1), V01 Tobin, V02 Peng (p.1).
- **Correction:** the paper said CalliRewrite "fine-tunes a simulated writing tool with reinforcement learning". The PDF (p.1, Introduction) says RL (SAC) fine-tunes the *coarse stroke sequence* into control
  of the simulated brush: the tool is simulated, not tuned. Reworded to "uses reinforcement learning to fine-tune that stroke sequence into control of a simulated brush". No claim or number changes.
- A `% Related Work paraphrases CHECKED` comment with page references was added under the paragraph. `check_paper.py`: **0 errors, 4 TODOs** (unchanged: authors, e-David, acknowledgment, TODO macro line).
- Helper `tools/tmp_check/pdftext.py` was written but is unusable (no `fitz`/`pypdf` in the env); the PDFs were read page by page instead. It is safe to delete.
### Honest limits
- Mostly page 1 (abstract/introduction) was read per paper, plus D02 pp.3-4. Fine details deeper in the papers (e.g. exact FRIDA calibration procedure) were not re-read.
- e-David is still uncited (not in the library; adding it needs a web lookup, which unattended sessions may not do).

### Paper: first local compile (2026-11-08; attended)
- MiKTeX: installed package `ieeetran`, then pdflatex/bibtex/pdflatex/pdflatex in `docs/paper` (local only, nothing uploaded).
- Result: `main.pdf`, **4 pages** (IEEE conference 2-column), 0 undefined citations/references, bibtex 0 warnings.
- Fixed one overfull box: H4 replication table was ~14pt wider than a column -> `\small`, `\tabcolsep=3pt`, shorter column headers (clean/slip/shift/ink; caption now spells them out). No number changed.
- check_paper.py: 0 errors, 4 TODOs (authors, e-David citation, acknowledgment/AI-use disclosure, TODO macro line).
- Page budget: 4 of 6 pages (ICRA/IROS limit), so there is room for a second figure (H4 bars) - not added yet.

### Paper: H4 replication figure made (seeds 200/300); not yet placed in the paper (2026-11-08; unattended auto-session)
- **What and why:** HANDOFF Next item 1 listed an optional H4 figure (the compiled paper is 4 of 6 pages). The existing `output/h4_v4_disturbance_recovery.png` shows seeds 0/100 only, so it does not match
  the paper's replication table. Made a new figure for the pre-registered confirmation seeds instead of overwriting the old one.
- **Code (plotting only, no training code touched, no sweep running):** `rl/h4_v4_experiment.py` `_figure()` got optional `out=` / `title=` arguments (defaults = old behaviour, old path).
  `rl/h4_confirm.py --aggregate --figure` writes `output/h4_confirm_recovery_seeds<seeds>.png` and refuses to overwrite an existing file.
- **Verified:** `python rl/h4_confirm.py --aggregate --figure` printed the same table as `### H4 v4 confirmation RESULT` (PRIMARY paper_shift +0.119, 8/8, t=+8.32; SECONDARY +0.062, 7/8, t=+3.86;
  REFERENCE -0.030, 2/8, t=-2.42; clean gap +0.006, t=+0.37) and wrote `output/h4_confirm_recovery_seeds200_300.png`. Left panel: IoU each arm lost per disturbance (fk, camera, camera_est,
  camera_sheet, true_sheet). Right panel: paper_shift diff-in-diffs with +/-1 SE whiskers and a dashed +/- t(7) x mean-SE guide.
- **Not done:** the figure is not in `docs/paper/main.tex`. Adding it needs a compile/page check (MiKTeX), which needs an attended session. Suggested caption: left = loss vs own clean score;
  right = paired within-(shape, seed) diff-in-diff, n=8, seeds 200/300 only.
### Honest limits
- Same data and limits as the confirmation entry: n=8, simulation only, pure-translation shift. Nothing new is measured.
- The dashed line uses the mean SE of the three bars, so it is only a visual guide. Read significance from the per-comparison t values, not from the picture (REFERENCE t=-2.42 is just past crit).
- Rendered with OpenCV like the other project figures (not vector graphics). It may need re-rendering larger or as a PDF for print quality.

### Paper: H4 replication figure placed (2026-11-08; attended)
- Added `output/h4_confirm_recovery_seeds200_300.png` (made by the auto-session) as Fig. `fig:h4` (`figure*`, full width) after Table `tab:h4`; text now cites both.
- Caption has no new numbers (only n=8, t_7 critical line, +/-1 SE). Figure bars visually match the table (fk paper-shift loss ~0.165, camera_est ~0.046, camera_sheet ~0.016).
- Recompiled: main.pdf **5 pages**, 0 undefined refs, no overfull boxes; check_paper 0 errors / 4 TODOs.
- Honest limits: the figure is a 1360x640 cv2 raster, not vector; fine for a draft, may need re-rendering for camera-ready.

### Paper: e-David citation added (2026-11-08; attended, user approved the lookup)
- One generic web search (paper name only, no project content) + publisher-group page (graphics.uni-konstanz.de, BibTeX copied verbatim): Deussen, Lindemeier, Pirk, Tautzenberger, "Feedback-guided Stroke Placement for a Painting Machine", CAe 2012 (Eurographics), pp. 25-33, doi 10.2312/COMPAESTH/COMPAESTH12/025-033.
- Added as library entry **A09** in `research_papers/README.md` (marked abstract-only ◇, no local PDF). `make_bib.py`: "Computational Aesthetics" added to the conference list so it builds as @inproceedings; header comment updated. references.bib regenerated (34 entries, 3 still VERIFY: D10, A08, R05 - unchanged).
- main.tex Related Work: "originates with e-David" (an unchecked priority claim) replaced by "go back at least to the e-David machine \cite{A09}". Description limited to what the abstract says.
- Recompiled: 5 pages, 0 undefined refs; check_paper 0 errors / 3 TODOs (authors, acknowledgment + AI-use disclosure, TODO macro).
- Honest limits: only the abstract was read; earlier e-David papers (~2009-2011) may exist and were not searched.

## 2026-11-08 - Project published on GitHub (user decision)
- User clarified the purpose: an **individual portfolio project** by Viral Kanani (GitHub + resume + learning RL/robotics), not a university thesis. Formal thesis dropped; paper draft + README take its place.
- Public repo: https://github.com/Viral2001/RoboSketch-RL (created with GitHub CLI, installed via winget; user authorised the login).
- Excluded via .gitignore: `research_papers/**/*.pdf` (third-party copyright), `models/` (~64 MB), videos, `.bak*`, LaTeX build files and `main.pdf` (draft still has TODO markers), agent logs/state. Secret scan before commit: none found. 387 files, ~17.6 MB.
- README rewritten for a public reader: the question, results table (numbers copied from earlier sourced entries), limits, layout, quick start, AI-assistance disclosure. The old detailed README is kept as `docs/README_full_status.md` (it contained an old overclaim "the novelty is teaching the robot how to learn to draw", now removed from the front page).
- AGENTS.md s2 rewritten: push only to the user's own repo and only when asked; still nothing account-side.
- Paper author line set to "Viral Kanani, Independent researcher" (email TODO).
