"""
RoboSketch-RL  |  research presentation builder
-------------------------------------------------
Generates the progress-review deck (PowerPoint, 16:9, with speaker notes) from
the project's real code, results and research log.

Run:
    conda run -n robosketch python docs/presentation/make_figures.py
    conda run -n robosketch python docs/presentation/build_deck.py

Output: docs/presentation/RoboSketch-RL_Progress_Review.pptx
"""
import importlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from deck_kit import new_deck  # noqa: E402

PARTS = ["deck_part1", "deck_part2", "deck_part3", "deck_part4", "deck_part5",
         "deck_part6"]
OUTFILE = os.path.join(HERE, "RoboSketch-RL_Progress_Review.pptx")


def main():
    prs = new_deck("RoboSketch-RL  ·  Vision-Guided RL for Autonomous Robotic Drawing")
    for name in PARTS:
        try:
            mod = importlib.import_module(name)
        except ModuleNotFoundError:
            print(f"  [skip] {name} (not written yet)")
            continue
        importlib.reload(mod)
        before = len(prs.slides._sldIdLst)
        mod.build(prs)
        print(f"  [ok]   {name:12s} -> {len(prs.slides._sldIdLst) - before:3d} slides")
    prs.save(OUTFILE)
    print(f"\n{len(prs.slides._sldIdLst)} slides written to {OUTFILE}")


if __name__ == "__main__":
    main()
