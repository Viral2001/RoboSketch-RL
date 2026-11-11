# PAPER_PLAN - claims, evidence, and what is still missing

_Written 2026-10-19 by Claude Code. Any agent writing paper or thesis text must follow this.
Update the **Status** column when evidence changes; never upgrade a claim without new
evidence logged in `docs/RESEARCH_LOG.md`._

---

## 1. The paper in one sentence

> Drawing agents are trained on a privileged canvas that no real robot has. We measure what
> is lost when a robot learns to draw from **what its camera sees** instead - and whether
> seeing the paper lets it recover from errors that kinematics alone cannot detect.

It is a **measurement paper**. The contribution is careful numbers on a question the three
closest papers name as open (quote them - section 5), not a new algorithm.

---

## 2. Claims map

Status key: **READY** = evidence logged, wording fixed · **PENDING** = experiment running or
not run · **AT RISK** = evidence may not support it.

| # | Claim (use this wording or weaker) | Evidence | Status | Limits that MUST appear next to it |
|---|---|---|---|---|
| C1 | A policy trained from a camera reward shows **no detectable difference** in true drawing accuracy from one trained on the privileged canvas. **UPDATE 2026-10-31: on independent seeds 100/200/300 (n=12) the two are statistically EQUIVALENT within +/-0.05 IoU (TOST p=0.008, 90% CI [-0.024,+0.033]; margin fixed before the run) - use this wording and cite THIS sweep; the evidence text below describes the older seeds-0,1,2 sweeps.** | H2 sweep (`results/h2_seeds.jsonl`, log 2026-08-12): mean 0.354 vs 0.382, n=3/shape. Re-run of the SAME seeds with a different thread setting (`h2_peak*.jsonl`, log "H2 PEAK-vs-FINAL") - **not independent**: gap +0.013, t=+0.57, 8/12; **the sign of the gap flipped between sweeps**. | READY | "No detectable difference" is not "equivalent" - no equivalence test (TOST) has been run. Shape-dependent (triangle favours truth in sweep 1). 200k steps, 4 simple shapes. **Both H2 sweeps used seeds 0,1,2 - adjacent seeds share 7 of 8 env streams (F6), so seed spread is understated and the two sweeps are not independent samples.** |
| C2 | The camera reward is **not exploited** during training. | H3 (log "H3 RESULT"): mean perceived-minus-true gap -0.0001 over 3328 episodes, corr 0.997-0.999; truth control exactly 0. | READY | n=1 seed per shape. Tested on the fixed camera only. |
| C3 | The result **survives a much worse camera**: training across randomised cameras buys nothing, because a fixed-camera policy already transfers to a held-out camera that recovers < 40% of the ink. | Stage 2 (log "STAGE 2 RESULT"): held-out drop 0.014 (fixed arm), randomised - fixed on held-out -0.011, t=-0.67. | READY | n=2 seeds. Effect is carried by 3 of 8 camera axes (5 inert by construction - say so). Camera is in the observation here, so absolute IoU is not comparable to C1. |
| C4 | **Seeing the paper lets the agent recover from disturbances that forward kinematics cannot see** (answers D01). | H4 series (log: H4-short nulls, `### H4 v3 RESULT`, `### H4 v4 RESULT`). H4-short: two nulls (|t|<=0.79). v3 (simulator-given offset): not a camera result. **v4 (offset ESTIMATED from the photo, n=8):** paper_shift loss fk +0.147, camera +0.136, camera_est +0.070, true-offset arm +0.019; camera_est vs fk +0.077, 8/8 up, t=+6.39; vs true-offset arm -0.051, t=-8.92. slip / ink_failure: no detectable effect (ink_failure barely bites).  **Confirmation (seeds 200/300, pre-registered, log `### H4 v4 confirmation RESULT`):** paper_shift loss fk +0.165, camera_est +0.046, true-offset +0.016; camera_est vs fk +0.119, 8/8, t=+8.32, clean gap +0.006 (t=+0.37) -> recovery, not a head start; vs true offset -0.030, t=-2.42. Pooled n=16: +0.098, 16/16, t=+9.32. Cost: vs the world-marker camera arm, camera_est loses MORE to ink_failure (-0.036, t=-5.29) and slip (-0.021, t=-2.64). | **PARTIAL, REPLICATED** (paper_shift only; simulation only) | Section 3 row "better on paper_shift only". v4 design replicated on fresh seeds (4 seeds total); the H4 SERIES (v1-v4) was exploratory, say so. State the estimator's ink_failure/slip cost. Pure-translation shift, near-fixed simulated camera, estimator (phase correlation) written knowing the shift model. Camera-derived estimate still clearly worse than the true offset. Never state C4 from the absolute camera - fk gap: that includes a clean gap and is not recovery. |
| C5 | Learned drawing agents **finish early and overshoot**; most of the episode is idle. An environment-side plateau stop recovers +0.055 IoU and cuts episodes ~5x. | Overrun + overshoot ablation (log 2026-09-03, "OVERSHOOT ABLATION RESULT"): baseline 0.378 -> plateau 0.433, 240 -> 50 steps. | READY (overrun exists) / **AT RISK** (plateau as a "fix") | Ground-truth reward only; 2 seeds. A methodological finding - present it as a pitfall others should check for, not as the main result. `plateau_patience` has no grace period, so its gain is confounded with a shorter exploration horizon (HANDOFF open issue) - needs a 4th arm before it is called a fix. **4th arm done (2026-11-04, `### C5 4th arm RESULT`): a plain 50-step horizon (`short50`) is not distinguishable from the plateau stop (plateau - short50 +0.016, t=+0.63) and gives ~71% of its gain (+0.039, t=+1.59). Do NOT call the plateau stop a fix; say the overrun is real and that shorter episodes help, with adaptive stopping not shown to add anything.** |
| C6 | Remaining-time in the observation gives a modest, shape-dependent gain. | O1 (log "O1 RESULT"): +0.039, 9/12 paired. | READY (minor) | Shape-dependent; default off. Ablation table only. |
| C7 | A practical one: seeded RL results on this stack are **not thread-invariant**. | Log 2026-09-03 "A reproducibility limit". | READY (minor) | Goes in the reproducibility statement, not the results. |
| C8 | **Honest limit, must be stated:** a scripted outline tracer (no learning; privileged: it knows the target's exact scale/rotation) reaches 0.72-0.74 TRUE IoU on every eval set, far above the learned agents on the same targets (param200: default 0.279, train 0.292, held-out 0.118). | T1 aggregate (log `### T1 BC warm start RESULT`, `expert` row, n=8 cells x 16 targets; same eval targets as param200). | READY as a limit | The paper's claim is the reward-SOURCE gap (truth vs camera), not that RL draws well; the learner is far from the ceiling. Do not write "the agent draws accurately"; say the absolute level is low and that a trivial scripted tracer is much higher. The tracer is privileged (it reads the target parameters), so it is a ceiling for the environment, not a perception-based baseline; a classical non-learning comparator now exists (ergodic control, proposal 4.7, log `### Ergodic baseline RESULT`): ~0.30 TRUE IoU on every set (held-out 0.306) - level with PPO at home (0.279-0.292), far above PPO off-distribution (0.118), level with the ego-view agent (0.298); descriptive only, privileged, not a perception-based baseline. |
| C9 | **Negative result:** a line-first curriculum (100k steps on `line`, then 200k on the target) is WORSE than training from scratch: final TRUE IoU 0.246 vs 0.418 (-0.173, 5/6 cells worse, t=-2.99 at n=6 cells; behind at every checkpoint; no jump-start). | RQ4 aggregate (log `### RQ4 curriculum RESULT`; 3 shapes x 2 seeds, one deterministic episode per run). | READY as a limit / negative finding | Say only: this naive pre-train-on-line curriculum did not help (negative transfer) in this setup. No mechanism claim (untested); other source rungs, lr/entropy resets, larger budgets not tried. Do not write "curricula do not work". |
| C10 | **Pen up/down (A2), first step:** giving the agent the pen decision on single-stroke shapes: final TRUE IoU 0.329 vs 0.418 always-down (-0.090, 5/6 worse, t=-2.29, n=6: NOT significant); slower start; pen down ~10% of eval steps; SNR 1.67 (now informative). | A2 aggregate (log `### A2 pen-free RESULT`). | READY as a limit | Write "no detectable effect on final IoU, slower learning". Does not show multi-stroke glyphs are drawable. |
| C11 | **IoU hides legibility (digits):** pen-free PPO on digits reaches TRUE IoU ~0.30 for both one-stroke (1,7: 0.309) and two-stroke (4,8: 0.293) digits, but an in-house recogniser reads 3/4 one-stroke runs as the right digit and 0/4 two-stroke runs. | Stage 6 digits aggregate (log `### Stage 6 digits RESULT`), descriptive, n=4 per group. | EXPLORATORY | Use only as motivation for a recognisability metric next to IoU. No test, stroke count confounded with digit identity, recogniser is in-house with no human rating. |
| C12 | **PPO vs SAC (RQ3), side result:** with the same vision reward and 200k env steps on the size/rotation task, SAC (update-to-data 0.25, one untuned config) reaches train-family TRUE IoU 0.051 vs PPO 0.292 (-0.241, 0/8 cells up, t=-9.71); it is behind on all 5 eval sets. | `results/sac_a/b.jsonl` vs `results/gen2_*.jsonl`; log `### RQ3 PPO vs SAC RESULT`. | MEASURED (pre-registered primary) | Wording: "SAC at this budget and configuration is far behind PPO". Do NOT say "PPO is better than SAC" in general (SAC may be starved; no tuning for either; PPO rows from an earlier run). Do NOT quote the "SAC loses less train->held-out" row (+0.147, t=+4.12) as generalisation: it is a floor effect (SAC starts at 0.051). No wall-clock pairing (PPO time not recorded). |

---

## 3. How the paper changes with the H4 result (decide BEFORE reading the result)

Apply the pre-registered test in the 2026-10-19 log entry. Then:

| H4 outcome (primary diff-in-diff, n=8) | Paper framing |
|---|---|
| **Camera recovers better** on ink_failure (and it bites), t >= 2.365 | Full story: C1-C3 say camera learning costs nothing; C4 says it buys recovery D01 cannot have. Title can name recovery. |
| Camera better on slip or paper_shift only; ink_failure **uninformative** (barely bites) | Partial. C4 is stated only for the disturbances that showed it. Re-sizing ink_failure (h4v2) becomes the priority before submission - **ask the user**. |
| **No detectable difference** on disturbances that do bite | Honest negative: the paper becomes "learning to draw from a camera costs nothing measurable (C1-C3) - but in simulation it also buys no recovery over kinematic sync". Still publishable as a measurement; D01's position is then **supported, not refuted**, and the paper must say so plainly. |
| **Camera recovers worse** | Report it. Look at the reward asymmetry first (fk was rewarded from the true canvas - section "Design" of the H4 log entry); a fair re-run with fk on a vision-quality reward may be needed. Ask the user. |

Never pick the framing after looking at which one reads best.

---

## 4. What is still missing before submission

Ordered by how much a reviewer would care:
1. **H4: v4 = partial (2026-10-30), REPLICATED on seeds {200,300} (2026-11-08, +0.119, 8/8, t=+8.32).** The paper may say the v4 result replicated; the H4 series before it was exploratory. ink_failure still too small to test (open-loop loses 0.013).
2-3. **DONE 2026-10-31 (equivalence test + spaced-seed H2 re-run, seeds 100/200/300, n=12 cells).** Log `### H2 spaced RESULT`.
   truth 0.388 vs camera 0.384, d=+0.004, t=+0.27; TOST at +/-0.05 (margin fixed before the run): 90% CI [-0.024, +0.033],
   p=0.008 -> EQUIVALENT within 0.05 IoU (also on peak IoU). C1 may now say "equivalent within 0.05 IoU in simulation (TOST)".
   Use the NEW sweep only; do not pool with the old seeds-0,1,2 sweeps (not independent; on those the same test does NOT
   pass: CI [-0.007, +0.063]). Limits stay: fixed camera, fixed shapes (see generalisation limit), 3 seeds, simulation.
4. **Generalisation (proposal section 5.4): DONE 2026-10-31 - and it is a LIMIT, not a pass.** Log `### Generalisation RESULT`.
   Fixed-target agents lose 0.146 IoU on mildly resized/rotated targets (t=+4.26) and reach 0.074 on held-out ones; training
   on a size/rotation family gives 0.118 (+0.044, 8/8, t=+7.35) but both arms lose most of their home score. State it
   plainly in Limitations; do NOT claim the agent "generalises" or "draws arbitrary shapes". Earlier claims C1-C6 hold for
   the fixed-picture setting only - say so next to each. Part 2 (2026-11-01, `### Generalisation part 2 RESULT`): 3x training (600k) does NOT close the gap (heldout +0.013, t=+0.95; loss grows 0.174 -> 0.230); size-only and rotation-only held-out each cost IoU (+0.132, +0.100), neither dominates. Say "not a training-budget problem at 3x", not "never". Open: architecture/observation fixes (Stage 4). Tried and null: more training (3x), CoordConv (O3), action chunking K=5 (A1: collapses, held-out +0.003), BC warm start (T1: held-out -0.005, t=-0.39; the cloned policy scores 0.591 on train before RL and PPO drops it to 0.292). The expert reaches ~0.72 on every set, so the ceiling is the learner/reward, not the environment. O2 (2026-11-01, `### O2 egocentric RESULT`): a pen-centred 64-px window lifts held-out IoU 0.118 -> 0.298 (+0.181, 8/8, t=+7.00) and cuts the train->held-out loss 0.174 -> 0.042 (diff-in-diff t=+4.11). Zoom control (`### O2z zoom control RESULT`): the same pixel density without pen-centring gains only +0.020 held-out (t=+2.03, n.s.); ego - that control = +0.161 (t=+8.04). Camera in the loop (`### O2c RESULT`, held-out camera): ego_cam vs global_cam held-out 0.273 vs 0.130 (+0.143, 6/8, t=+3.54); loss 0.189 -> 0.038 (diff-in-diff t=+4.25); no gain at home (train t=-0.70); `line` is worse with ego in both seeds. O3 (`### O3 CoordConv RESULT`): adding x/y coordinate planes to the global view does NOT fix held-out (+0.008, t=+0.97) though it helps on the training family (+0.039, t=+8.32), so the loss grows (0.174 -> 0.205).
5. **Baseline comparison:** open-loop / IK tracer numbers exist inside H4; report them. PPO
   vs SAC (RQ3) DONE 2026-11-11 (claim C12); a side result, not a headline.
6. **Real camera or real robot:** not required for a simulation measurement paper at
   ICRA/IROS, but expect the question. The thesis needs at least a plan (Stage 7).

---

## 5. Related work - positioning (do not overclaim)

Cannot claim as new: RL for robot drawing (D01, D02, D05, D09), vision-based rewards
(Sermanet RSS'17, Singh RSS'19), visual feedback in drawing (FRIDA ICRA'23; e-David ~2009 -
**must be cited**). Our gap is stated by the closest papers themselves - quote these:
- **D01** Lee et al. ICRA 2022: *"using a camera as an observation of canvas in the future
  work could be of great help in the synchronization step"*
- **D03** Kotani & Tellex ICRA 2019: *"closing the learning loop by enabling the robot to
  inspect what it has drawn"*
- **D09** Luo et al. ICRA 2024: *"a lack of real-world training scenarios to bridge the
  sim2real gap. We leave these challenges as our future work."*

Before quoting any number from a paper, check its mark in `research_papers/STUDY_NOTES.md`:
◆ read in full, ◇ abstract only - **open the PDF before quoting a ◇ paper**.

---

## 6. Section skeleton (IEEE conference, 6-8 pages)

1. **Introduction** - the privileged-canvas problem; D01's camera-free argument; our question;
   contributions = C1, C3, C4 (if it holds), C5.
2. **Related work** - section 5 above.
3. **Setup** - PyBullet KUKA arm, pen-space actions, `DrawEnv`, simulated camera
   (`rl/perception.py`), reward modes (truth / vision), observation sources (true / fk /
   camera), true-IoU scoring everywhere.
4. **Experiments** - H2 (C1), H3 (C2), DR (C3), H4 (C4), overshoot (C5). One table each,
   n and t in every table.
5. **Discussion** - what the null results mean; reward asymmetry in H4; simulation-only.
6. **Limitations** - n=2-3 seeds; 4 shapes; simulation; thread non-invariance.
7. **Conclusion.**

Figures that exist: `output/results_h2_seeds.png`, `results_h3.png`, `results_overshoot.png`,
`results_o1.png`. Missing: H4 figure (per-disturbance drop by arm), DR figure.

---

## 7. Rules for any agent writing paper text

- Every number must be traceable to a RESEARCH_LOG entry or a script's `--aggregate` output.
  Put the source in a comment next to it while drafting (`<!-- log: STAGE 2 RESULT -->`).
- Use the wording in section 2 or weaker. Never strengthen it.
- "No detectable difference", never "no difference" / "the same" / "equivalent" (until the
  TOST in section 4.2 is done).
- Keep drafts in `docs/paper/` (local only - AGENTS.md section 2: never upload or share).
  The draft is `docs/paper/main.tex`; workflow and tools in `docs/paper/README.md`.
  **`check_paper.py` must report 0 errors** before any section is called done.
- **Citations: only cite papers that are in `research_papers/README.md`**, using the metadata
  there (it was verified against the arXiv API). Never write a reference from memory - AI
  models invent plausible-looking papers and wrong venues. A paper not in the library must be
  added to it first, with its metadata checked on arXiv / the publisher page.
- Slides (PPT) follow the same rules: numbers from section 2, wording no stronger than section 2.
- Remind the user before submission: check the venue's policy on disclosing AI-assisted
  writing (IEEE asks for it in the acknowledgments).
