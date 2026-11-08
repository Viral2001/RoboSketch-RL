"""
RoboSketch-RL  |  the complete guide deck (from scratch to results)
-------------------------------------------------
Rebuild:
    conda run -n robosketch --no-capture-output python docs/presentation/complete_guide/build.py
QA (layout raster + bounds/notes check):
    conda run -n robosketch --no-capture-output python docs/presentation/complete_guide/build.py --qa

Output: docs/presentation/complete_guide/RoboSketch-RL_Complete_Guide.pptx
Content sources: docs/RESEARCH_LOG.md, docs/PROJECT_PROPOSAL_v2.md, docs/PAPER_PLAN.md,
the code in rl/ and sim/, figures in output/. The H4 slides read results/h4_experiment*.jsonl
directly, so rebuilding after the sweep finishes picks up the final numbers.
"""
import importlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))

from deck_kit import new_deck  # noqa: E402

PARTS = ["g1_intro_robotics", "g2_rl_basics", "g3_ppo_sac", "g4_vision_problem",
         "g5_system_results", "g6_h4_stats_future"]
OUTFILE = os.path.join(HERE, "RoboSketch-RL_Complete_Guide.pptx")


def main():
    prs = new_deck("RoboSketch-RL  ·  The Complete Guide")
    for name in PARTS:
        try:
            mod = importlib.import_module(name)
        except ModuleNotFoundError as e:
            if e.name != name:
                raise
            print(f"  [skip] {name} (not written yet)")
            continue
        before = len(prs.slides._sldIdLst)
        mod.build(prs)
        print(f"  [ok]   {name:22s} -> {len(prs.slides._sldIdLst) - before:3d} slides")
    prs.save(OUTFILE)
    print(f"\n{len(prs.slides._sldIdLst)} slides written to {OUTFILE}")
    if "--qa" in sys.argv:
        qa()


def qa():
    import preview
    from pptx import Presentation
    preview.PPTX = OUTFILE
    preview.OUT = os.path.join(HERE, "preview")
    os.makedirs(preview.OUT, exist_ok=True)
    which = [a for a in sys.argv[1:] if a.isdigit()]
    sys.argv = [sys.argv[0]] + which
    preview.main()
    # bounds + speaker-notes coverage (same rules as ../check_deck.py)
    prs = Presentation(OUTFILE)
    W, tol = prs.slide_width, 9144
    bad, missing = [], []
    for i, s in enumerate(prs.slides, 1):
        for sh in s.shapes:
            if sh.top is None or sh.height is None:
                continue
            if sh.left <= tol and sh.top <= tol and sh.left + sh.width >= W - tol:
                continue
            if (sh.left < -tol or sh.top < -tol or sh.left + sh.width > W + tol
                    or (sh.top + sh.height) / 914400.0 > 7.44):
                bad.append(i)
        if not (s.has_notes_slide and s.notes_slide.notes_text_frame.text.strip()):
            missing.append(i)
    print("out-of-bounds shapes on slides:", sorted(set(bad)) or "none")
    print("slides without notes:", missing or "none")


if __name__ == "__main__":
    main()
