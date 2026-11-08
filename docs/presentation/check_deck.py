"""Quick structural QA on the built deck: bounds, notes coverage, slide count."""
import os

from pptx import Presentation
from pptx.util import Emu

HERE = os.path.dirname(os.path.abspath(__file__))
PPTX = os.path.join(HERE, "RoboSketch-RL_Progress_Review.pptx")
SAFE_BOTTOM_IN = 7.44        # slide is 7.5 in tall; allow a small bleed

prs = Presentation(PPTX)
W, H = prs.slide_width, prs.slide_height
tol = Emu(int(914400 * 0.01))
bad, notes, chars = [], 0, 0
for i, s in enumerate(prs.slides, 1):
    for sh in s.shapes:
        if sh.top is None or sh.height is None:
            continue
        bottom = (sh.top + sh.height) / 914400.0
        full_bleed = (sh.left <= tol and sh.top <= tol
                      and sh.left + sh.width >= W - tol)
        if full_bleed:
            continue                      # intentional background panels
        if (sh.left < -tol or sh.top < -tol or sh.left + sh.width > W + tol
                or bottom > SAFE_BOTTOM_IN):
            try:
                nm = sh.text_frame.text[:34].replace("\n", " ") if sh.has_text_frame else ""
            except Exception:
                nm = ""
            bad.append((i, round(sh.left / 914400.0, 2), round(sh.top / 914400.0, 2),
                        round(bottom, 2), nm))
    if s.has_notes_slide:
        t = s.notes_slide.notes_text_frame.text.strip()
        if t:
            notes += 1
            chars += len(t)

for b in bad[:60]:
    print("  slide %-3d  x=%-5s y=%-5s bottom=%-5s  %s"
          % (b[0], b[1], b[2], b[3], b[4].encode("ascii", "replace").decode()))
print("\n%d shapes outside the safe area" % len(bad))
print("slides            : %d" % len(prs.slides._sldIdLst))
print("with speaker notes: %d" % notes)
print("notes characters  : %d (avg %d / noted slide)"
      % (chars, chars // max(1, notes)))
