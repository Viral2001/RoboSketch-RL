# RoboSketch-RL — progress presentation

`RoboSketch-RL_Progress_Review.pptx` — 84 slides, 16:9, speaker notes on every slide.

The deck is **generated from code**, so it can be rebuilt whenever the results change.

## Rebuild

```bash
conda run -n robosketch python docs/presentation/make_figures.py   # figures from output/
conda run -n robosketch python docs/presentation/build_deck.py     # the .pptx
```

Optional QA (no PowerPoint needed):

```bash
conda run -n robosketch python docs/presentation/preview.py    # raster each slide -> preview/
conda run -n robosketch python docs/presentation/check_deck.py # bounds + notes coverage
```

## Files

| file | role |
|---|---|
| `build_deck.py` | orchestrator — imports the six content parts, saves the .pptx |
| `deck_kit.py` | the design system: palette, type scale, title band, cards, flow nodes, arrows, tables, equation blocks, code panels, charts, Q&A cards, auto-fit |
| `deck_part1.py` | title · agenda · §1 project overview · §2 system vision |
| `deck_part2.py` | §3 progress so far — every completed stage |
| `deck_part3.py` | §4 technical design · §5 programming details |
| `deck_part4.py` | §6 RL design · §7 mathematics · §8 computer vision |
| `deck_part5.py` | §9 timeline · §10 future roadmap |
| `deck_part6.py` | §11 anticipated questions · §12 backup slides |
| `make_figures.py` | composes slide-ready figures from the real results in `output/` |
| `preview.py` | renders the .pptx to PNGs with PIL for layout QA |
| `check_deck.py` | reports out-of-bounds shapes and speaker-note coverage |

## Editing

Slides are ordinary PowerPoint shapes, so the .pptx can be edited by hand — but changes
there are lost on the next rebuild. Prefer editing the `deck_part*.py` source.

Every completed stage uses `deck_kit.decision_slide(...)`, which lays out the six panels
*what we did · why it was necessary · alternatives considered · why this approach ·
challenges faced · result / evidence*. Adding a new stage is one call.

## Sources

All content traces to `docs/RESEARCH_LOG.md` and the artefacts in `output/`, `models/`
and the code itself. No numbers in the deck are invented.

## Research-results deck (added 2026-10-19)

`RoboSketch-RL_Research_Results.pptx` - 13 slides that mirror the paper (`docs/paper/main.tex`),
built by `deck_paper.py` (uses `deck_kit.py`; independent of the missing `deck_part3-6.py`):

```
conda run -n robosketch --no-capture-output python docs/presentation/deck_paper.py
```

Same rules as the paper: numbers from RESEARCH_LOG entries named in each slide's speaker notes,
wording from `docs/PAPER_PLAN.md`. **Slide 9 (H4 result) is a deliberate PENDING placeholder** -
replace it only after the "H4 RESULT" log entry exists; never fill it with interim numbers.
Also update slide 13's last card and the title slide then. `[TODO: ...]` on the title slide =
presenter / institution / date.
