# OBSOLETE - DO NOT FOLLOW (2026-10-19 02:55)

**H4 is already finished and written up**: `### H4 RESULT` in `docs/RESEARCH_LOG.md`
(written 02:47 by another Claude Code session), HANDOFF.md updated. Running the steps below
would create a DUPLICATE log entry. Follow `docs/HANDOFF.md` instead (its "Next" says: ask the
user). This file is kept only as a record.

---

# H4 FINISH - exact steps for whoever finishes H4 (written 2026-10-19 by Claude Code)

Do these in order. Do not skip, reorder, or "improve" any step. Do not edit any `.py` file.
High thinking for steps 3-5.

## Step 1 - Is the sweep finished?
```
conda run -n robosketch python -c "import json,glob;r=[json.loads(l) for p in glob.glob('results/h4_experiment_*.jsonl') for l in open(p) if l.strip()];k={(x['shape'],x['arm'],x['seed']) for x in r};print('rows',len(r),'unique',len(k),'bad_cfg',[x for x in r if x['timesteps']!=200000 or x['max_steps']!=240])"
```
- `rows 32 unique 32 bad_cfg []` -> go to Step 2.
- rows < 32 -> check processes (PowerShell):
  `Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Select ProcessId,CommandLine`
  - an `h4_experiment.py` worker still running -> **wait. Do nothing else.** Tell the user
    "N/32 done, still running" and stop.
  - no worker running and rows < 32 -> a worker crashed (known: exit code 4). Relaunch ONLY
    the shard that is missing rows, in the background, with exactly:
    ```
    $env:OMP_NUM_THREADS=1; $env:MKL_NUM_THREADS=1; conda run -n robosketch --no-capture-output python rl/h4_experiment.py --seeds 0 100 --shapes line circle --shard a --timesteps 200000 --eval-eps 10
    $env:OMP_NUM_THREADS=1; $env:MKL_NUM_THREADS=1; conda run -n robosketch --no-capture-output python rl/h4_experiment.py --seeds 0 100 --shapes square triangle --shard b --timesteps 200000 --eval-eps 10
    ```
    (PowerShell, repo root. Never without the two thread variables.)
    (shard a = line+circle, shard b = square+triangle; finished runs are skipped
    automatically.) Tell the user and stop.
- unique < rows, or bad_cfg not empty -> **stop and tell the user. Do not analyse.**

## Step 2 - Run the analysis and SHOW the full output in your reply
```
conda run -n robosketch python rl/h4_experiment.py --aggregate
```
It must say `balanced over 8 (shape, seed) cells`. If not 8 -> stop, tell the user.

## Step 2b - Run the verdict script and SHOW its full output
```
conda run -n robosketch python rl/h4_verdict.py
```
It recomputes the PRIMARY diff-in-diff, cross-checks it, and applies the Step 4 rule.
- Its numbers must match the Step 2 PRIMARY lines (same value, same t). Any mismatch, or
  `FAIL`, or `NO VERDICT` -> stop and tell the user.
- **Paste its table into the log as-is.** Do not retype numbers, do not change verdict words.
  (Tested 2026-10-19 on the n=4 interim data: matched the aggregate exactly.)
Steps 3-4 below describe what the script does; they are the rule, not extra work.

## Step 3 - Check the script (AGENTS.md section 6, rule 2)
For each of slip / paper_shift / ink_failure, the `PRIMARY` value must equal
`fk drop - camera drop` from the line just above it (within 0.002, rounding). Show it with
python, not in your head, e.g. `python -c "print(-0.021 - 0.008)"`. If any mismatch -> stop and
tell the user; do not write a result.

## Step 4 - Decide each verdict. Mechanical. Use ONLY the PRIMARY t and crit (2.36 at n=8).
For each disturbance, the FIRST matching row wins:

| condition (from the printed output) | verdict word to write |
|---|---|
| `!! ... barely bites` printed for it | **uninformative** - disturbance too weak to test recovery (NOT "camera does not help") |
| t >= crit | camera **recovers better** than fk |
| t <= -crit | camera recovers **worse** than fk (a real negative result) |
| 1.5 <= abs(t) < crit | **no detectable difference, borderline** -> after writing, ASK the user whether to add seeds 200 and 300 (all arms, all shapes). Do NOT launch them yourself. |
| otherwise | **no detectable difference** (never "no difference" / "no effect") |

FORBIDDEN: using the `secondary absolute camera - fk` line for any verdict; calling the
`clean gap` recovery; writing any number that is not visible in the Step 2 output.

## Step 5 - Append to the END of docs/RESEARCH_LOG.md (do not edit older entries)
Heading: `### H4 RESULT (32/32 runs, 8 shape x seed cells)` - placed after the existing
2026-10-19 "Stage 3 begins: H4" entry content, i.e. at the end of the file.
Contents, in this order:
1. The command, and the full aggregate output pasted in a ``` block.
2. The table printed by `rl/h4_verdict.py`, pasted unchanged, with its two header lines.
3. Clean gap line (camera - fk with no disturbance, n, t) and one sentence: it is NOT recovery.
4. Compare with the interim n=4 table already in the log (paper_shift +0.007 t=0.30 etc.):
   did the direction hold? One sentence per disturbance. No new claims.
5. What this means for D01 (one short paragraph): only paper_shift / slip / ink_failure verdicts
   as decided in Step 4. If ink_failure is "uninformative", say H4 has NOT tested the
   invisible-to-kinematics case yet.
6. `#### Honest limits` - include ALL of these:
   - n = 8 pairs (2 seeds x 4 shapes); |t| < 2.36 is not significant; direction only.
   - Reward asymmetry: fk (and true) rewarded from the TRUE canvas, camera from vision -
     biased AGAINST camera. A camera loss must be read with this in mind.
   - open_loop is an analytic tracer, not a trained policy: a floor for reactivity, not skill.
   - Disturbance sizes chosen to be visible but survivable; not calibrated to a real arm.
   - Mixed thread settings (HANDOFF "Open issues"): the 2026-10-17 Antigravity rows (line +
     triangle at seed 0, line/open_loop at seed 100) used DEFAULT threads, all later rows
     `OMP_NUM_THREADS=1`. Seeded runs here are not thread-invariant. Each (shape, seed) cell is
     internally consistent, so the paired diff-in-diff is fair; absolute means mix two
     settings. Rows record neither threads nor eval_eps (see log entry "H4 bookkeeping").
   - Fixed camera: this is about feedback, not camera realism (that was Stage 2).

## Step 6 - Update docs/HANDOFF.md
Running: nothing. Last done: H4 result + verdicts. Next: ask the user (options already listed
in HANDOFF "Next" step 4). Move "ink_failure may be too weak" to resolved or confirmed per the
result. Keep HANDOFF under 60 lines.

## Step 7 - Tell the user in 3-5 Hinglish lines, then STOP
What was found per disturbance (verdict words), and the one question: what next (or the
seeds 200/300 question if Step 4 hit "borderline"). Do not start the next experiment.
