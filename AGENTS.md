# AGENTS.md - RoboSketch-RL operating manual for AI coding agents

Read this whole file before doing anything. It is short on purpose. Every rule here
exists because breaking it has already cost this project a wrong number or a lost run.

---

## 0. If the user just types "continue"

"continue" means: **pick up the project exactly where the last session left it.** Do this,
in order, every time:

0. **Only ONE agent works on this repo at a time.** If another Claude Code tab, Antigravity
   window or other agent is open on this folder, stop and ask the user to close it. Two
   agents both following HANDOFF.md duplicate work and fight over running sweeps.
   Includes the **automatic unattended agent** (`tools/agent_run.ps1`, see HANDOFF.md): if
   `tools/agent.lock` exists, an auto session is running right now - do not start work.
   New sweeps must also be added to `tools/jobs.json` so the watchdog keeps them alive.
1. **Read `docs/HANDOFF.md`.** It says what is running, what was last done, and what is next.
2. **Check what is running right now** before starting anything (PowerShell):
   ```
   Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Select-Object ProcessId,CreationDate,CommandLine | Format-List
   ```
   If a sweep is running, **do not launch it again** and do not edit the code it uses.
3. **Check for work that HANDOFF.md does not mention** - files newer than the log:
   ```
   Get-ChildItem -Recurse -File results,rl,docs | Where-Object { $_.LastWriteTime -gt (Get-Item docs/RESEARCH_LOG.md).LastWriteTime } | Select-Object FullName,LastWriteTime
   ```
4. **Read only the tail of the log** (`docs/RESEARCH_LOG.md` is 120 KB - never load it whole):
   ```
   Select-String -Path docs/RESEARCH_LOG.md -Pattern '^#{2,3} ' | Select-Object -Last 15
   Get-Content docs/RESEARCH_LOG.md -Tail 120
   ```
5. **Do the "Next" item in HANDOFF.md.** If it says "ask the user", ask - in one short question.
6. **Finish properly** (section 7): verify, log, update HANDOFF.md, tell the user in 3-5 lines.

Never invent a next step that is not in HANDOFF.md or `docs/PROJECT_PROPOSAL_v2.md` section 8.
If both are unclear, stop and ask.

---

## 1. What this project is (fixed - do not change)

**RoboSketch-RL**: a robot arm that *learns* to draw (line, circle, square, triangle, later
digits and letters) with reinforcement learning, rewarded by what a **camera** sees.
Simulation first (PyBullet, KUKA arm). Hardware (~Rs 10,000 6-DOF arm) only after
simulation works. Goal: a **thesis + IEEE paper** (ICRA / IROS / RA-L / CoRL).

**The research claim is a MEASUREMENT, not an invention:**
> Existing drawing agents are rewarded from a privileged signal (the exact virtual canvas)
> that does not exist on a real robot. We measure what drawing accuracy is lost when the
> agent learns from perception instead of truth - and whether seeing the paper helps when
> things go wrong.

**Do NOT write or imply any of these** (all are prior art - see
`research_papers/COMPARATIVE_ANALYSIS.md`):
- "RL for robot drawing is new" (D01, D02, D05, D09 did it)
- "vision-based rewards are new" (Sermanet RSS'17, Singh RSS'19)
- "closed-loop visual feedback for drawing is new" (FRIDA ICRA'23, e-David ~2009)

**The one objection that is fatal if unanswered:** D01 (Lee et al., ICRA 2022) draws well
with NO camera and argues camera-free is better. H4 (`rl/h4_experiment.py`) exists to answer
it. Treat H4 as the most important experiment in the project.

Hypotheses in use: H2 (vision reward ~ truth reward), H3 (no reward exploitation), H4
(camera recovers from disturbances kinematics cannot see), H5 (open-loop error growth),
H6 (overrun/overshoot). Plan and status: `docs/PROJECT_PROPOSAL_v2.md` section 8.

---

## 2. Confidentiality and publishing (hard rule)

Changed 2026-11-08 by the user: the project is an individual portfolio project by
**Viral Kanani**, and the code lives in a **GitHub repo** (git initialised, remote `origin`).
The user's Claude account is used on other devices.
- **Only `git push` to the user's own GitHub repo, and only when the user asks.** Check
  `git status` / staged files first: never commit `research_papers/**/*.pdf` (third-party
  copyright), `models/`, videos, logs or secrets (`.gitignore` covers these - keep it so).
- **Still never publish anything account-side:** no Claude artifacts, docs, gists,
  pastebins, shareable links, or remote/cloud Claude sessions.
- Web searches: **generic questions only.** Never put code, file contents, result numbers,
  hypothesis names or the project name in a search query.

---

## 3. Environment (Windows 11)

- Conda env **`robosketch`** (Python 3.10). Conda lives at `C:\Users\viral\New folder`.
- Always run Python through the env:
  ```
  conda run -n robosketch --no-capture-output python <script> [args]
  ```
- PyBullet comes from **conda-forge** only (`pip install pybullet` fails on Windows - do not try).
- Shell is PowerShell. No `&&` chains that assume bash; no Unix-only tools.

---

## 4. Code map

| Path | What it is |
|---|---|
| `sim/01..05_*.py` | Phase B simulator scripts (arm, IK, pen, camera). Done - do not touch. |
| `rl/draw_env.py` | **The Gymnasium environment.** Everything depends on it. |
| `rl/perception.py` | Simulated camera + `TRAIN` / `HELDOUT` camera distributions |
| `rl/disturb.py` | H4 disturbances: `slip`, `paper_shift`, `ink_failure`, `mixed` |
| `rl/targets.py`, `rl/metrics.py` | Target shapes; IoU / MSE / chamfer / snr / path_ratio |
| `rl/experiment.py` | H2 multi-seed sweep (+ `warn_config_drift`, shared by others) |
| `rl/<name>_experiment.py`, `*_ablation.py` | One file per experiment. Each has `--aggregate`. |
| `rl/watch.py` | Visualise a trained policy drawing |
| `results/*.jsonl` | **Raw results. Append-only. Never edit, never delete.** `_pre_perimeter_fix/` is archived old data. |
| `output/*.png` | Figures |
| `docs/RESEARCH_LOG.md` | **The lab notebook. Source material for the thesis.** |
| `docs/HANDOFF.md` | Session-to-session state. Update at the end of every session. |
| `docs/PROJECT_PROPOSAL_v2.md` | The plan (section 8 = sequencing and status) |
| `docs/PAPER_PLAN.md` | **Claims map for the paper** - allowed wording, evidence, limits, and how the story changes with the H4 result. Read before writing ANY paper/thesis text. |
| `docs/paper/` | **The paper draft** (`main.tex`), generated `references.bib`, and `check_paper.py` (must pass with 0 errors). Workflow: `docs/paper/README.md`. Also covers slides. |
| `research_papers/` | 33-paper library: `README.md`, `STUDY_NOTES.md`, `COMPARATIVE_ANALYSIS.md` |

---

## 5. Running experiments

Every experiment script follows the same pattern:
```
# two workers in parallel, split by SHAPE, same seeds:
$env:OMP_NUM_THREADS=1; $env:MKL_NUM_THREADS=1; conda run -n robosketch --no-capture-output python rl/h4_experiment.py --seeds 0 100 --shapes line circle     --shard a --timesteps 200000
$env:OMP_NUM_THREADS=1; $env:MKL_NUM_THREADS=1; conda run -n robosketch --no-capture-output python rl/h4_experiment.py --seeds 0 100 --shapes square triangle --shard b --timesteps 200000
# after BOTH shards finish:
conda run -n robosketch --no-capture-output python rl/h4_experiment.py --aggregate
```
Rules:
- **Seeds must be far apart: use `--seeds 0 100`, never `0 1`.** `PPO(seed=k)` reseeds the
  8 vector envs to `k+i`, so seeds 0 and 1 share 7 of 8 env streams (log fix F6).
- **Resumable.** Each script skips runs already in its `results/*.jsonl`. If a worker dies
  (this project has an unexplained **exit code 4, no traceback** crash) just relaunch the
  *same command* - completed runs are kept.
- **Run sweeps in the background** and do other work (writing, analysis) while they run.
  Training is hours; do not sit and poll.
- **Never edit `draw_env.py`, `perception.py`, `disturb.py` or the training part of an experiment script while
  its sweep is running or half-finished.** A resumed sweep would mix two versions of the
  code in one table. If a change is truly needed: stop, write to a NEW results file name,
  log why.
- **Thread count changes seeded results.** Runs are only bitwise comparable if they used the
  same `OMP_NUM_THREADS` / torch threads. Do not mix settings within one sweep. **Default
  for two parallel workers: `OMP_NUM_THREADS=1`, `MKL_NUM_THREADS=1`** (as above). Copy the
  exact launch command from HANDOFF.md; never retype it.
- **A worker that exits (e.g. code 127) right after the user stopped it was KILLED, not
  crashed.** Check HANDOFF.md and ask before relaunching anything that was stopped.
- If `warn_config_drift` prints a warning, stop and tell the user - the new runs do not
  match the old ones.
- Scoring is **always TRUE IoU** of the real paper, whatever the agent sees. Do not change that.
- Do not delete or overwrite any `.jsonl`, `.zip` model, or figure.

---

## 6. Analysis rules (where agents have actually made mistakes here)

1. **Every number you write must come from a script's printed output** (`--aggregate`), or
   from a short script you write and show. Never do arithmetic in your head.
2. **A number printed by a script is not verified just because a script printed it.** Check
   *what it is compared against*. On 2026-10-19 `dr_experiment.py` printed a fixed-arm
   "drop" of +0.006 that compared against the wrong camera column (true value +0.014), and an
   agent copied it into the log. Before quoting a difference, recompute it from the two
   numbers in the table above it.
3. **"drop" and "change" are opposites.** drop = before - after. A drop of -0.003 is a GAIN.
   State the direction in words: "fell from 0.393 to 0.379 (-0.014)".
4. **When two arms start at different levels, compare how much each LOSES, not where each
   ends.** On 2026-10-19 the H4 script declared "camera recovers better" (t=2.45) when the
   camera arm was simply better with no disturbance at all; recovery was ~0 (t=0.30). Use
   the paired difference-in-differences. A gap under disturbance that equals the clean gap
   is not recovery.
5. Always report: **n (seeds x shapes), mean +/- sd, paired difference, pairs up (k/n), t.**
   With n=8 pairs, |t| < ~2.4 is not significant. Write "no detectable effect", never
   "no effect". Never call a result significant that is not.
6. **Report the result you got, not the one you hoped for.** Do not re-tune parameters until
   a number lands in a target range you chose. If a criterion is missed, say so.
7. A **negative result is a result.** "Randomisation did nothing" was written up as a
   finding. Do not hide or soften it.
8. Compare like with like: do not compare absolute IoU across experiments with different
   setups (e.g. DR scores 0.37-0.39 are a harder task than H2's ~0.45). Say so when tempted.
9. Report **peak IoU alongside final IoU** where the script logs both (overshoot effect, H6).
10. Never quote a number from a paper marked **◇** in `research_papers/STUDY_NOTES.md`
   without opening the PDF. ◆ = read in full; ◇ = abstract only.

---

## 7. Finishing a piece of work (do all four, every time)

1. **Verify.** Run it / re-run `--aggregate` / import the module. Do not claim done without it.
2. **Log it** - append to the END of `docs/RESEARCH_LOG.md`:
   - first check the last 15 headings: **do not duplicate an entry that already exists**;
     extend it instead.
   - heading format: `## YYYY-MM-DD - <what happened>` (or `###` under the current day)
   - include: what was done, **why** (alternatives considered), the result table pasted from
     script output, an "Honest limits" list (n, confounds, what this does NOT show).
   - corrections are **new dated entries** that say what was wrong and why - never silently
     rewrite an old number.
3. **Update `docs/HANDOFF.md`** - Running / Last done / Next / Open issues. Keep it under 60
   lines; it is a state file, not a diary.
4. **Tell the user** in 3-5 short lines: what you did, the result, what is next.

---

## 8. Working with the user

- The user is **new to RL, robotics and computer vision.** Explain from basics, in plain
  language, define terms the first time. Short answers. Hinglish is fine and preferred
  when the user writes in Hinglish.
- Only the problem statement and purpose are fixed. Algorithms, reward, arm, ordering can
  change - but **propose** changes, do not make them silently.
- **No hardware purchases** are to be suggested until simulation results are complete.
- Ask before: deleting anything, changing an environment default, starting a sweep longer
  than ~6 hours, or changing what a hypothesis claims.
- If you are unsure, ask one short question rather than guessing.
