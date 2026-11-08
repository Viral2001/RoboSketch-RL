# GEMINI.md - extra rules for Gemini / Antigravity

**`AGENTS.md` is the main manual. Read it first and follow it completely.** This file only
adds Gemini-specific rules; where they conflict, this file wins.

1. **"continue" = AGENTS.md section 0.** Start with `docs/HANDOFF.md`, check running
   processes, then act. Do not start by re-reading the whole project.
2. **Before writing any number into a document, show the command output it came from** in
   your reply. If you cannot point to the output line, do not write the number.
3. **Before writing a conclusion, re-read AGENTS.md section 6** (analysis rules) and check
   each one against what you wrote. The two mistakes made in this repo by a fast model were
   (a) copying a script's comparison without checking its reference and (b) reading "drop"
   as "change". Both look correct on the page.
4. **Use high thinking for**: analysis, statistics, log entries, anything going in the paper,
   and any edit to `rl/draw_env.py`, `rl/perception.py` or `rl/disturb.py`. Low/medium is fine
   for launching runs, plots and file housekeeping.
5. **One task per turn.** Do the task, finish it (AGENTS.md section 7), report, stop. Do not
   chain into the next item on your own unless the user said "continue" again.
6. **Terminal commands**: never run anything that deletes, overwrites `results/`, kills a
   python process, or installs/upgrades packages without asking the user first.
7. **Do not use the browser agent or any upload/share feature** with project files
   (AGENTS.md section 2).
8. If a sweep is running and there is nothing else in HANDOFF.md to do, say so and stop.
   Do not invent work.
