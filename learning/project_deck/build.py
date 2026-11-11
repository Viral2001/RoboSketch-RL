"""
RoboSketch-RL  |  "Learn it from scratch" teaching deck
=========================================================
Rebuild (from the repo root, any shell):
    D:\\RoboSketch-RL\\.venv_docs\\Scripts\\python.exe learning\\project_deck\\build.py
Options:
    --preview          also export every slide to learning/project_deck/preview/*.png
                       through Microsoft PowerPoint (COM, via export_preview.ps1)

Output: learning/project_deck/RoboSketch-RL_Learn_From_Scratch.pptx

What it does
  1. teach_figs.make_all()  - teaching figures + toy numbers (fig/)
  2. builds the deck twice  - pass 1 records where each section starts, pass 2 prints
                              those page numbers on the "Map of the deck" slide
  3. QA                     - every shape inside the slide, every slide has speaker notes,
                              every equation PNG exists and is >= 300 dpi as placed
Uses only .venv_docs (python-pptx, matplotlib, pillow, numpy). Never touches the
conda env, rl/, sim/, results/, docs/.
"""
import importlib
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import kit  # noqa: E402
import teach_figs  # noqa: E402

PARTS = ["p00_start", "p01_problem", "p02_robotics", "p03_vision", "p04_ml", "p05_rl",
         "p06_ppo", "p07_env", "p08_stats", "p09a_results", "p09b_h4", "p09c_results",
         "p10_claims", "p11_next", "p12_review"]
OUTFILE = os.path.join(HERE, "RoboSketch-RL_Learn_From_Scratch.pptx")
# If the deck is open in PowerPoint/WPS the save fails: set DECK_OUT to write a copy under another name.
OUTFILE = os.environ.get("DECK_OUT", OUTFILE)


def build_once(toc, verbose=False):
    prs = kit.new_deck()
    for name in PARTS:
        try:
            mod = importlib.import_module(name)
        except ModuleNotFoundError as e:
            if e.name != name:
                raise
            if verbose:
                print(f"  [skip] {name} (not written yet)")
            continue
        before = len(prs.slides._sldIdLst)
        mod.build(prs, toc)
        if verbose:
            print(f"  [ok]   {name:14s} {len(prs.slides._sldIdLst) - before:3d} slides")
    return prs


def qa(path):
    from PIL import Image
    from pptx import Presentation
    prs = Presentation(path)
    Wd, Hd = prs.slide_width, prs.slide_height
    tol = int(914400 * 0.01)
    bad, missing, nsrc = [], [], 0
    for i, s in enumerate(prs.slides, 1):
        for sh in s.shapes:
            if sh.left is None or sh.width is None:
                continue
            if (sh.left < -tol or sh.top < -tol or sh.left + sh.width > Wd + tol
                    or sh.top + sh.height > Hd + tol):
                bad.append((i, sh.shape_type, round(sh.left / 914400, 2), round(sh.top / 914400, 2)))
        t = s.notes_slide.notes_text_frame.text.strip() if s.has_notes_slide else ""
        if not t:
            missing.append(i)
        if "Source:" in t:
            nsrc += 1
    eq_bad = []
    for e in kit.EQ_LOG:
        if not os.path.exists(e["path"]):
            eq_bad.append((e["slide"], "missing file"))
            continue
        im = Image.open(e["path"])
        dpi = im.info.get("dpi", (0, 0))[0]
        if e["eff_dpi"] < 300 or (dpi and round(dpi) < 300):
            eq_bad.append((e["slide"], f"eff {e['eff_dpi']:.0f} dpi"))
    print(f"\nslides                 : {len(prs.slides._sldIdLst)}")
    print(f"shapes outside slide   : {bad[:20] or 'none'}")
    print(f"slides without notes   : {missing or 'none'}")
    print(f"slides with 'Source:'  : {nsrc}")
    print(f"equation images placed : {len(kit.EQ_LOG)} (unique files "
          f"{len({e['path'] for e in kit.EQ_LOG})}); min effective dpi "
          f"{min((e['eff_dpi'] for e in kit.EQ_LOG), default=0):.0f}")
    print(f"equation problems      : {eq_bad or 'none'}")
    print(f"formula-sheet entries  : {len(kit.FORMULAS)}")
    return not bad and not missing and not eq_bad


def main():
    teach_figs.make_all()
    toc = {}
    build_once(toc)
    prs = build_once(toc, verbose=True)
    prs.save(OUTFILE)
    print(f"\nwritten: {OUTFILE}")
    ok = qa(OUTFILE)
    print("QA:", "PASS" if ok else "PROBLEMS FOUND")
    if "--preview" in sys.argv:
        ps = os.path.join(HERE, "export_preview.ps1")
        subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ps,
                        OUTFILE, os.path.join(HERE, "preview")], check=False)


if __name__ == "__main__":
    main()
