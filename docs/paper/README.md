# docs/paper - the paper, built so an AI agent cannot quietly get it wrong

| File | Role |
|---|---|
| `main.tex` | IEEE conference draft. Skeleton with `\TODO{}` markers saying exactly what goes where and from which log entry. |
| `references.bib` | **Generated. Never edit.** Built from `research_papers/README.md` (metadata verified against arXiv). |
| `make_bib.py` | Regenerates `references.bib`. Run after any change to the library. |
| `check_paper.py` | Lint. **Run after every edit.** Fails on invented/unverified citations, untraceable numbers, forbidden wording, missing figures. |

## Workflow for any agent
1. Read `docs/PAPER_PLAN.md` first (claims, allowed wording, H4 framing table).
2. Fill one `\TODO` at a time. Every number gets a `% src: RESEARCH_LOG "<heading>"` comment
   on its line or within the next two lines.
3. `conda run -n robosketch --no-capture-output python docs/paper/check_paper.py` - must end
   with **0 errors** before you tell the user a section is done.
4. Need a reference that is not in the library? **Stop and tell the user.** It must be added to
   `research_papers/README.md` with verified metadata, then `make_bib.py` re-run.
5. Entries flagged `VERIFY` in `references.bib` (3 at creation: D10 year, A08 authors, R05 year): the user checks the year/authors
   on arXiv or the publisher page, fixes `research_papers/README.md`, re-runs `make_bib.py`.

## Compiling
**Locally only** (MiKTeX or TeX Live: `pdflatex main && bibtex main && pdflatex main && pdflatex main`).
Do **not** upload to Overleaf or any online editor - AGENTS.md section 2.

## Slides
The final presentation follows the same rules: numbers and wording from `docs/PAPER_PLAN.md`
section 2. Note: `docs/presentation/README.md` describes `deck_part3-6.py`, `make_figures.py`
and `preview.py`, but **those files are missing** - only `deck_part1.py`, `deck_part2.py`,
`deck_kit.py`, `build_deck.py`, `check_deck.py` exist. The existing
`RoboSketch-RL_Progress_Review.pptx` (84 slides) cannot be rebuilt from source as-is. For a new
deck, reuse `deck_kit.py` (the design system) and write new parts; ask the user which
outline they want (guide review vs. conference talk vs. thesis defence).
