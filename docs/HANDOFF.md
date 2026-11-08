# HANDOFF - current state (update at the end of EVERY session)

_Last updated: 2026-11-08 (H4 replication figure made; unattended auto-session) by Claude Code._

## Running
- Nothing running. **H4 v4 CONFIRMATION DONE 2026-11-08 - REPLICATED** (log `### H4 v4 confirmation RESULT`): seeds 200/300, camera_est loses +0.119 less than fk to paper_shift (8/8, t=+8.32), clean gap ~0 (+0.006); still slightly below true offset (-0.030, t=-2.42); NEW cost: camera_est loses more than world-marker camera to ink_failure (-0.036, t=-5.29) and slip (-0.021, t=-2.64). Pooled n=16 primary +0.098, 16/16, t=+9.32.
- **Stage 6 digits DONE** 2026-11-07 (log `### Stage 6 digits RESULT`): IoU ~0.30 for 1-stroke (1,7) and 2-stroke (4,8) digits alike, but legible 3/4 vs 0/4 (descriptive, n=4 each).
- A2 pen-free DONE: final IoU 0.329 vs always-down 0.418 (-0.090, 5/6 worse, t=-2.29: no detectable effect; slower start; pen down only ~10% of steps; SNR 1.67). Log `### A2 pen-free RESULT`.
- RQ4 curriculum finished 2026-11-05; both `tools/done/rq4_curr_*.done` exist). RQ4 RESULT: line-first curriculum HURTS (final 0.246 vs scratch 0.418, -0.173, 5/6 worse, t=-2.99) - log `### RQ4 curriculum RESULT`, PAPER_PLAN C9.
- RQ3 SAC NOT run (infeasible: ~0.76 s per gradient update -> ~10 h/run; logged `## 2026-11-05 - RQ3 PPO vs SAC NOT run`). Do not re-attempt without a GPU/smaller net.
- Previously finished (T1 ~09:00). Finished: T1 bc200 (8/8, `results/bc_a/b.jsonl`), A1 chunk5, C5 short50, H2 spaced, generalisation x2, O2/O2z/O2c, O3 (see Last done).
- **AUTO-RESTART**: task `RoboSketch-KeepAlive` -> `tools/keepalive.ps1` (logon + 5 min) relaunches unfinished `tools/jobs.json` jobs (no `tools/done/<name>.done`; OMP/MKL=1;
  worker output in `tools/job_logs/<name>.log`; gives up after 20 fails). **New sweeps go in jobs.json.** Stop: `tools/STOP`. It does NOT catch HUNG workers (0 CPU, no new row for >1 h):
  stop those by hand and the watchdog relaunches them (T1 hung once, 2026-11-05 01:46-08:00).
- **AUTO-AGENT**: task `RoboSketch-Agent` -> `tools/agent_run.ps1` starts one unattended `claude -p "continue"` (logs `tools/agent_logs/`) when online, idle 30 min, >=60 min since last,
  <8/day, no `tools/NOAGENT`. `tools/agent.lock` = auto session running: do not work in parallel. It writes "WAITING FOR USER: ..." atop "Next" when it needs a decision.

## Last done (2026-11-05)
- **T1 BC RESULT logged** (`### T1 BC warm start RESULT`; PAPER_PLAN item 4 updated). n=8: held-out bc200 0.113 vs param200 0.118 (-0.005, t=-0.39) = no effect. Cloned policy BEFORE RL
  scores 0.591 on train (2x param200) and PPO drops it to 0.292 (-0.299, 0/8, t=-10.27): PPO unlearns a good start. Expert reaches 0.72-0.74 on every set -> ceiling is the learner/reward.
- **A1 chunking RESULT logged**: held-out +0.003 (t=+0.17), train 0.292 -> 0.103 (-0.189, t=-15.55) = hurts; scribbles, never stops. Negative ablation, no re-tuning.
- **STAGE 4 COMPLETE**: ego view is the only lever (O2 +0.181 held-out, survives camera O2c); 3x training, CoordConv, chunking, BC warm start all null/negative.

## Earlier (2026-11-04)
- **C5 4th arm logged** (`### C5 4th arm RESULT`; PAPER_PLAN C5 + README corrected). n=8 (seeds 0/1, F6 overlap): plateau 0.433 vs
  short50 (plain 50-step horizon) 0.417, +0.016, t=+0.63 -> cannot separate; short horizon gives ~71% of plateau's +0.055 (t=+1.59).
  Do NOT call the plateau stop a fix. Overrun/overshoot measurement stands.
- **O3 CoordConv logged**: held-out +0.008 (t=+0.97) - no help; train +0.039 (t=+8.32). Ego gain is not 'input position handling'.

## Earlier (2026-11-01/02)
- **O2 egocentric logged** (`### O2 egocentric RESULT`; README + PAPER_PLAN item 4 updated). n=8: heldout IoU global 0.118 -> ego 0.298
  (+0.181, 8/8, t=+7.00); loss train->heldout 0.174 -> 0.042 (diff-in-diff +0.132, t=+4.11); ego also better at home (train +0.048).
  Zoom control O2z logged: global128 held-out 0.137 (+0.020 vs global64, n.s.); ego - global128 +0.161, t=+8.04 -> pen-centring,
  not zoom. **O2c (camera in loop) logged: ego_cam held-out 0.273 vs global_cam 0.130 (+0.143, t=+3.54); loss 0.189 -> 0.038 (t=+4.25); no home gain; `line` worse with ego.**
- **Generalisation part 2**: 3x training (600k) does NOT close the held-out gap (+0.013, t=+0.95) -> a LIMIT, not budget.
- (10-28..31: H2 spaced EQUIVALENT, TOST p=0.008; H4 v3/v4, oracle, H4-short, H5 - see RESEARCH_LOG. H4 v4 unreplicated.)

## Next
WAITING FOR USER: paper needs authors + affiliation + final title (only remaining paper TODOs).
1. **Paper draft v2 DONE 2026-11-08** (`docs/paper/main.tex`, check_paper 0 errors / 5 TODOs; log `## 2026-11-08 - Paper draft v2`). Quotes VERIFIED vs PDFs 2026-11-08 (all 3 exact; D01 sync wording corrected: it uses the *reached* pen position, not the commanded stroke - log `### Paper: intro quotes checked`); check_paper 0 errors / 4 TODOs. Related Work paraphrases CHECKED vs PDFs 2026-11-08 (all match except CalliRewrite wording, now fixed - log `### Paper: Related Work paraphrases checked`). COMPILED locally 2026-11-08: main.pdf 4 pages, 0 undefined refs, no overfull boxes. H4 replication FIGURE MADE 2026-11-08: `output/h4_confirm_recovery_seeds200_300.png` (`rl/h4_confirm.py --aggregate --figure`; log `### Paper: H4 replication figure made`), PLACED in main.tex as Fig. fig:h4 (attended, 2026-11-08); main.pdf now 5 pages, 0 errors. e-David CITED (library A09, 2026-11-08). Next: user to give authors/title + acknowledgment; then thesis chapters (item 2). `tools/tmp_check/` = unused helper, deletable.
2. Then: thesis chapters from the same claims map; hardware planning (Stage 7; no purchase suggestions).
3. Optional: why PPO unlearns a BC start; why camera_est < camera_sheet; digits stroke-count vs identity confound; ink_failure too small.

## Status by stage (proposal section 8)
- Stage 1 done (incl. 1b overshoot H6). Stage 2: item 10 done; item 11 (5.4) **done - a limit**.
- Stage 3: item 12 (H4) **two nulls, v3 privileged, v4 partial (camera-estimated offset helps, below true-offset arm)**;
  item 13 (H5) **done - supported (feedback, not camera)**.
- Stage 4: O2/O2z/O2c (ego) done - strong; O3 done - null; A1 done - negative; T1 done - null (PPO unlearns BC start). STAGE 4 COMPLETE. Stages 5-7 not started. No hardware yet (by design).

## Open issues
- **D01 objection only partly answered**, simulation only: v4 is the 4th H4 design (exploratory), pure-translation
  shift, near-fixed camera, estimator written by me knowing the shift model. Replicated on seeds 200/300 (2026-11-08).
- Worker crashes: exit 4 (no traceback), exit 127 / session-boundary kills. Resume covers them.
- H4 rows record neither `eval_eps` nor thread count; no models saved.
- `ink_failure` too small to test anything (open-loop loses 0.013-0.014 at both horizons).
- C5: plateau vs plain short horizon not separable (4th arm, n=8, overlapping seeds 0/1).
