"""
Guide kit - reusable slide layouts for the complete project guide deck.

Built on ../deck_kit.py (the project's design system); only adds a handful of
data-driven layouts so ~110 slides stay visually consistent:

  concept()    bullets on the left, explanation cards on the right, analogy strip
  steps()      a numbered derivation: equation box + plain-language explanation per row
  tabular()    a table with an optional takeaway strip
  figure()     an image from output/ or figures/ with reading notes beside it
  grid()       N cards in a grid
  strip()      the coloured one-line takeaway at the bottom of a slide
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from pptx.enum.shapes import MSO_SHAPE  # noqa: E402
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN  # noqa: E402

from deck_kit import (ACCENT, BAD, BODY, CW, GOOD, INK, LINE, M, MUTED,  # noqa: E402,F401
                      NAVY, PRIMARY, SLATE, TINT_AMBER, TINT_BLUE, TINT_GREEN,
                      TINT_RED, TINT_VIOLET, VIOLET, W, H, WARN, WASH, WASH2, WHITE,
                      arrow, bullets, card, chip, code, eqn, fit_size, kpi, node, note,
                      pic, pipeline, rect, section, slide, table, txt)

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
OUT = os.path.join(ROOT, "output")
FIG = os.path.join(os.path.dirname(HERE), "figures")

TINT = {PRIMARY: TINT_BLUE, ACCENT: TINT_BLUE, GOOD: TINT_GREEN, WARN: TINT_AMBER,
        BAD: TINT_RED, VIOLET: TINT_VIOLET, SLATE: WASH}


def img(name):
    """Resolve a figure name against output/ then presentation/figures/."""
    for d in (OUT, FIG):
        p = os.path.join(d, name)
        if os.path.exists(p):
            return p
    raise FileNotFoundError(name)


def _bs(body, w, h, start=13.0):
    items = body if isinstance(body, (list, tuple)) else [body]
    return fit_size([i if isinstance(i, str) else i.get("t", "") for i in items],
                    w - 0.38, h - 0.62, start=start, floor=9.0, spacing=1.16, gap_pt=4)


def strip(s, text, color=PRIMARY, y=6.40, h=0.50, label=None):
    rect(s, M, y, CW, h, fill=TINT.get(color, WASH2), line=None,
         shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.12)
    rect(s, M, y, 0.07, h, fill=color)
    lab = (label + "  ") if label else ""
    sz = 12 if len(text) < 150 else 11
    txt(s, M + 0.25, y + (h - 0.30) / 2, CW - 0.45, h - 0.08,
        [{"t": lab + text, "size": sz, "color": INK, "bold": True}])


def analogy(s, text, y=6.40, h=0.50):
    strip(s, text, color=ACCENT, y=y, h=h, label="SIMPLE ANALOGY ·")


def concept(prs, kicker, title, sub, points, cards=None, notes="", take=None,
            take_color=PRIMARY, analog=None, left_w=None, size=13.5):
    """Bullets left, cards right (cards = [(title, body, color), ...])."""
    s = slide(prs, title, kicker, sub)
    top = s._body_top + 0.05
    bottom = 6.90
    if take:
        bottom = 6.28
    if analog:
        bottom = 5.72 if take else 6.28
    if cards:
        lw = left_w or 6.15
        bullets(s, points, M, top, lw, bottom - top, size=size)
        cx = M + lw + 0.30
        cw = CW - lw - 0.30
        n = len(cards)
        gap = 0.16
        ch = (bottom - top - gap * (n - 1)) / n
        for i, c in enumerate(cards):
            t, b, col = (c + (PRIMARY,))[:3] if len(c) == 2 else c
            card(s, cx, top + i * (ch + gap), cw, ch, t, b, accent=col,
                 body_size=_bs(b, cw, ch))
    else:
        bullets(s, points, M, top, CW, bottom - top, size=size)
    if take:
        strip(s, take, take_color)
    if analog:
        analogy(s, analog, y=5.84 if take else 6.40)
    note(s, notes)
    return s


def steps(prs, kicker, title, sub, rows, notes="", take=None, take_color=VIOLET,
          eq_w=6.3, eq_size=15, ex_size=13):
    """A derivation. rows = [(label, equation_lines, explanation), ...]."""
    s = slide(prs, title, kicker, sub)
    top = s._body_top + 0.04
    bottom = 6.28 if take else 6.90
    n = len(rows)
    gap = 0.12
    rh = (bottom - top - gap * (n - 1)) / n
    for i, (lab, eq, ex) in enumerate(rows):
        y = top + i * (rh + gap)
        chip(s, M, y + rh / 2 - 0.16, 0.95, 0.32, lab, color=VIOLET, size=9.5)
        lines = eq if isinstance(eq, (list, tuple)) else [eq]
        rect(s, M + 1.08, y, eq_w, rh, fill=WASH, line=LINE,
             shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.05)
        es = eq_size
        longest = max(len(l) for l in lines)
        while es > 10 and longest * es * 0.50 / 72.0 > eq_w - 0.35:
            es -= 0.5
        while es > 10 and len(lines) * es * 1.35 / 72.0 > rh - 0.12:
            es -= 0.5
        txt(s, M + 1.18, y + 0.04, eq_w - 0.2, rh - 0.08,
            [{"t": l, "size": es, "color": INK, "font": "Cambria Math",
              "align": PP_ALIGN.CENTER, "space_after": 2} for l in lines],
            anchor=MSO_ANCHOR.MIDDLE)
        exs = ex if isinstance(ex, (list, tuple)) else [ex]
        ew = CW - 1.08 - eq_w - 0.25
        fs = fit_size(exs, ew, rh - 0.08, start=ex_size, floor=9.0)
        txt(s, M + 1.08 + eq_w + 0.25, y + 0.02, ew, rh - 0.04,
            [{"t": e, "size": fs, "color": BODY, "space_after": 3} for e in exs],
            spacing=1.15, anchor=MSO_ANCHOR.MIDDLE)
    if take:
        strip(s, take, take_color)
    note(s, notes)
    return s


def tabular(prs, kicker, title, sub, headers, rows, colw=None, notes="", take=None,
            take_color=GOOD, size=11, row_h=0.36, align=None, cell_colors=None,
            below=None, y=None):
    s = slide(prs, title, kicker, sub)
    ty = y or (s._body_top + 0.08)
    table(s, headers, rows, M, ty, CW, colw=colw, size=size, header_size=size,
          row_h=row_h, align=align, cell_colors=cell_colors, bold_col0=True)
    if below:
        by = ty + 0.34 + row_h * len(rows) + 0.22
        bh = (6.28 if take else 6.90) - by
        bl = below if isinstance(below, (list, tuple)) else [below]
        bullets(s, bl, M, by, CW, bh, size=fit_size(bl, CW, bh, start=14, floor=9.5, spacing=1.2, gap_pt=7),
                tight=True)
    if take:
        strip(s, take, take_color)
    note(s, notes)
    return s


def figure(prs, kicker, title, sub, image, points, notes="", take=None,
           take_color=GOOD, fig_w=7.6, size=12):
    s = slide(prs, title, kicker, sub)
    top = s._body_top + 0.05
    bottom = 6.28 if take else 6.90
    pic(s, img(image), 0, 0, center_in=(M, top, fig_w, bottom - top))
    rx = M + fig_w + 0.25
    rw = CW - fig_w - 0.25
    fs = fit_size(points, rw, bottom - top, start=size, floor=9.5, spacing=1.2, gap_pt=7)
    bullets(s, points, rx, top, rw, bottom - top, size=fs)
    if take:
        strip(s, take, take_color)
    note(s, notes)
    return s


def grid(prs, kicker, title, sub, cards, cols=3, notes="", take=None, take_color=PRIMARY,
         body_size=None):
    s = slide(prs, title, kicker, sub)
    top = s._body_top + 0.05
    bottom = 6.28 if take else 6.90
    n = len(cards)
    rows_n = -(-n // cols)
    gx, gy = 0.18, 0.16
    cw = (CW - gx * (cols - 1)) / cols
    ch = (bottom - top - gy * (rows_n - 1)) / rows_n
    for i, c in enumerate(cards):
        t, b, col = c if len(c) == 3 else (c[0], c[1], PRIMARY)
        r, k = divmod(i, cols)
        card(s, M + k * (cw + gx), top + r * (ch + gy), cw, ch, t, b, accent=col,
             body_size=body_size or _bs(b, cw, ch))
    if take:
        strip(s, take, take_color)
    note(s, notes)
    return s
