"""
RoboSketch-RL learning deck  |  design kit + equation renderer
---------------------------------------------------------------
Self-contained copy of the project's slide design system (adapted from
docs/presentation/deck_kit.py and complete_guide/gk.py, which are NOT edited),
plus the one thing those decks lacked: equations rendered as real typeset
images (matplotlib mathtext, Computer Modern, 400 dpi, transparent PNG).

Every equation placed with `place_eq` is recorded in EQ_LOG so build.py can
check that the PNG exists and is sharp (effective resolution on the slide).
Every equation registered with a `label` goes onto the formula sheet.

IMPORTANT: always pass LaTeX as raw strings (r"..."). A plain "\r" or "\t" in a
Python string silently eats a backslash - that exact bug once broke the paper
(RESEARCH_LOG "### Paper: a \\ref eaten by a Python string escape").
"""
import hashlib
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from PIL import Image  # noqa: E402
from pptx import Presentation  # noqa: E402
from pptx.dml.color import RGBColor  # noqa: E402
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE  # noqa: E402
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN  # noqa: E402
from pptx.oxml.ns import qn  # noqa: E402
from pptx.util import Emu, Inches, Pt  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
EQDIR = os.path.join(HERE, "eq")
FIGDIR = os.path.join(HERE, "fig")
OUT = os.path.join(ROOT, "output")
PFIG = os.path.join(ROOT, "docs", "presentation", "figures")
os.makedirs(EQDIR, exist_ok=True)
os.makedirs(FIGDIR, exist_ok=True)

matplotlib.rcParams["mathtext.fontset"] = "cm"
matplotlib.rcParams["font.family"] = "DejaVu Sans"
EQ_DPI = 400

# ------------------------------------------------------------------ theme --
INK = RGBColor(0x0F, 0x17, 0x2A)
BODY = RGBColor(0x33, 0x41, 0x55)
MUTED = RGBColor(0x64, 0x74, 0x8B)
FAINT = RGBColor(0x94, 0xA3, 0xB8)
LINE = RGBColor(0xD8, 0xDF, 0xE9)
WASH = RGBColor(0xF5, 0xF7, 0xFB)
WASH2 = RGBColor(0xEC, 0xF1, 0xF8)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
TINT_RED = RGBColor(0xFB, 0xEC, 0xEC)
TINT_GREEN = RGBColor(0xEC, 0xF7, 0xF1)
TINT_BLUE = RGBColor(0xE9, 0xEF, 0xFB)
TINT_AMBER = RGBColor(0xFD, 0xF3, 0xE3)
TINT_VIOLET = RGBColor(0xF1, 0xEC, 0xFB)
NAVY = RGBColor(0x11, 0x1C, 0x39)
PRIMARY = RGBColor(0x2B, 0x4A, 0xCB)   # structure / what
ACCENT = RGBColor(0x0E, 0x9C, 0xC4)    # vision / data
GOOD = RGBColor(0x0D, 0x8A, 0x5F)      # measured result
WARN = RGBColor(0xC2, 0x7A, 0x0A)      # caveat / challenge
BAD = RGBColor(0xC0, 0x35, 0x35)       # rejected / wrong / negative
VIOLET = RGBColor(0x6D, 0x45, 0xC7)    # learning / maths
SLATE = RGBColor(0x54, 0x66, 0x82)
TINT = {PRIMARY: TINT_BLUE, ACCENT: TINT_BLUE, GOOD: TINT_GREEN, WARN: TINT_AMBER,
        BAD: TINT_RED, VIOLET: TINT_VIOLET, SLATE: WASH}
HEX = {"ink": "#0F172A", "body": "#334155", "muted": "#64748B", "line": "#D8DFE9",
       "primary": "#2B4ACB", "accent": "#0E9CC4", "good": "#0D8A5F", "warn": "#C27A0A",
       "bad": "#C03535", "violet": "#6D45C7", "slate": "#546682", "wash": "#F5F7FB"}

F = "Segoe UI"
FM = "Consolas"
W, H = 13.333, 7.5
M = 0.58
CW = W - 2 * M

_state = {"n": 0, "footer": "RoboSketch-RL  ·  Learn it from scratch", "section": ""}
EQ_LOG = []        # every placed equation: dict(path, slide, eff_dpi)
FORMULAS = []      # (group, label, latex) for the formula sheet
NOTES_SRC = []     # (slide_no, has_source)


# --------------------------------------------------------------- plumbing --
def new_deck():
    prs = Presentation()
    prs.slide_width = Inches(W)
    prs.slide_height = Inches(H)
    _state["n"] = 0
    EQ_LOG.clear()
    FORMULAS.clear()
    return prs


def _blank(prs):
    return prs.slides.add_slide(prs.slide_layouts[6])


def rect(s, x, y, w, h, fill=None, line=None, lw=0.75, shape=MSO_SHAPE.RECTANGLE,
         radius=None):
    shp = s.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    try:
        shp.shadow.inherit = False
    except Exception:
        pass
    if radius is not None and shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        try:
            shp.adjustments[0] = radius
        except Exception:
            pass
    if fill is None:
        shp.fill.background()
    else:
        shp.fill.solid()
        shp.fill.fore_color.rgb = fill
    if line is None:
        shp.line.fill.background()
    else:
        shp.line.color.rgb = line
        shp.line.width = Pt(lw)
    shp.text_frame.text = ""
    return shp


def txt(s, x, y, w, h, content, size=14, color=BODY, bold=False, italic=False,
        align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, font=F, spacing=1.12,
        space_after=3):
    box = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Inches(0.02)
    tf.margin_top = tf.margin_bottom = 0
    items = content if isinstance(content, (list, tuple)) else [content]
    for i, it in enumerate(items):
        d = {"t": it} if isinstance(it, str) else dict(it)
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = d.get("align", align)
        p.line_spacing = d.get("spacing", spacing)
        p.space_after = Pt(d.get("space_after", space_after))
        r = p.add_run()
        r.text = d["t"]
        f = r.font
        f.name = d.get("font", font)
        f.size = Pt(d.get("size", size))
        f.bold = d.get("bold", bold)
        f.italic = d.get("italic", italic)
        f.color.rgb = d.get("color", color)
    return box


def fit_size(items, w_in, h_in, start=14.0, floor=10.0, spacing=1.15, gap_pt=6):
    """Largest font (<= start) at which the strings fit a w x h box (estimate)."""
    sz = start
    while sz > floor:
        cpl = max(8, int(w_in / (sz * 0.50 / 72.0)))
        lines = sum(max(1, -(-len(str(t)) // cpl)) for t in items)
        need = lines * sz * spacing * 1.2 / 72.0 + len(items) * gap_pt / 72.0
        if need <= h_in:
            return sz
        sz -= 0.5
    return floor


def bullets(s, items, x, y, w, h, size=None, color=BODY, start=16, floor=11,
            marker="•", gap=7):
    """items: str | (1, str) sub-bullet | dict. Auto-fits the font size."""
    flat = [i if isinstance(i, str) else (i[1] if isinstance(i, tuple) else i.get("t", ""))
            for i in items]
    size = size or fit_size(flat, w - 0.1, h, start=start, floor=floor, gap_pt=gap)
    conv = []
    for it in items:
        if isinstance(it, dict):
            d = dict(it)
            d.setdefault("size", size)
            conv.append(d)
            continue
        lvl, t = it if isinstance(it, tuple) else (0, it)
        pre = f"{marker}  " if lvl == 0 else "      –  "
        conv.append({"t": pre + t, "size": size if lvl == 0 else size - 1.5,
                     "color": color if lvl == 0 else MUTED, "space_after": gap})
    return txt(s, x, y, w, h, conv, size=size, color=color)


def note(s, text, source=None):
    t = text.strip()
    if source:
        t += "\n\nSource: " + source
    s.notes_slide.notes_text_frame.text = t


# ---------------------------------------------------------------- figures --
def img_path(name):
    if os.path.isabs(name) and os.path.exists(name):
        return name
    for d in (FIGDIR, OUT, PFIG):
        p = os.path.join(d, name)
        if os.path.exists(p):
            return p
    raise FileNotFoundError(name)


def pic(s, name, x, y, w, h, border=False):
    """Fit an image inside the box (x, y, w, h), centred, aspect kept."""
    path = img_path(name)
    iw, ih = Image.open(path).size
    sc = min(w / iw, h / ih)
    dw, dh = iw * sc, ih * sc
    px, py = x + (w - dw) / 2, y + (h - dh) / 2
    if border:
        rect(s, px - 0.04, py - 0.04, dw + 0.08, dh + 0.08, fill=WHITE, line=LINE)
    return s.shapes.add_picture(path, Inches(px), Inches(py), Inches(dw), Inches(dh))


# -------------------------------------------------------------- equations --
def eq_png(latex, size=28, color=HEX["ink"]):
    """Render LaTeX (mathtext) to a transparent 400-dpi PNG; returns (path, w_in, h_in)
    where w/h are the NATURAL size, i.e. the size at which glyphs are `size` pt."""
    key = hashlib.md5(f"{latex}|{size}|{color}|{EQ_DPI}|pad0.10".encode("utf-8")).hexdigest()[:14]
    path = os.path.join(EQDIR, f"eq_{key}.png")
    if not os.path.exists(path):
        fig = plt.figure(figsize=(0.01, 0.01))
        fig.text(0, 0, "$" + latex + "$", fontsize=size, color=color)
        fig.savefig(path, dpi=EQ_DPI, transparent=True, bbox_inches="tight",
                    pad_inches=0.10)
        plt.close(fig)
    iw, ih = Image.open(path).size
    return path, iw / EQ_DPI, ih / EQ_DPI


def place_eq(s, latex, x, y, w, h, size=28, color=HEX["ink"], halign="center",
             valign="middle"):
    """Place an equation image in a box at its natural size, shrinking only if needed."""
    path, nw, nh = eq_png(latex, size, color)
    sc = min(1.0, w / nw, h / nh)
    dw, dh = nw * sc, nh * sc
    px = x + {"left": 0, "center": (w - dw) / 2, "right": w - dw}[halign]
    py = y + {"top": 0, "middle": (h - dh) / 2, "bottom": h - dh}[valign]
    shp = s.shapes.add_picture(path, Inches(px), Inches(py), Inches(dw), Inches(dh))
    iw, _ = Image.open(path).size
    EQ_LOG.append({"path": path, "slide": _state["n"], "eff_dpi": iw / dw,
                   "scale": sc, "latex": latex})
    return shp


def formula(group, label, latex):
    """Register an equation for the end-of-deck formula sheet (deduplicated)."""
    if not any(f[2] == latex for f in FORMULAS):
        FORMULAS.append((group, label, latex))


# ----------------------------------------------------------------- slides --
def slide(prs, title, kicker=None, sub=None):
    s = _blank(prs)
    _state["n"] += 1
    rect(s, 0, 0, W, H, fill=WHITE)
    if kicker:
        rect(s, M, 0.40, 0.12, 0.185, fill=PRIMARY)
        txt(s, M + 0.22, 0.36, 9.0, 0.26, kicker.upper(), size=11, color=PRIMARY, bold=True)
    tsize = 27 if len(title) <= 44 else (24 if len(title) <= 56 else 21)
    txt(s, M, 0.64, CW - 0.6, 0.55, title, size=tsize, color=INK, bold=True, spacing=0.95)
    if sub:
        txt(s, M, 1.16, CW - 0.6, 0.32, sub, size=14, color=MUTED, italic=True)
    rect(s, M, 1.50 if sub else 1.24, CW, 0.014, fill=LINE)
    txt(s, M, H - 0.40, 8.0, 0.25, _state["footer"] + ("  ·  " + _state["section"]
                                                       if _state["section"] else ""),
        size=9.5, color=FAINT)
    txt(s, W - M - 1.2, H - 0.40, 1.2, 0.25, str(_state["n"]), size=10, color=FAINT,
        align=PP_ALIGN.RIGHT)
    s._top = 1.68 if sub else 1.42
    return s


def section(prs, number, title, blurb, items, notes, toc=None):
    s = _blank(prs)
    _state["n"] += 1
    _state["section"] = f"{number:02d} {title}"
    if toc is not None:
        toc[number] = _state["n"]
    rect(s, 0, 0, W, H, fill=NAVY)
    rect(s, 0, 0, 0.16, H, fill=PRIMARY)
    txt(s, 1.1, 1.75, 3.0, 1.0, f"{number:02d}", size=66, color=PRIMARY, bold=True)
    txt(s, 1.1, 2.85, 7.4, 1.4, title, size=36, color=WHITE, bold=True, spacing=0.95)
    rect(s, 1.15, 4.25, 1.6, 0.035, fill=ACCENT)
    txt(s, 1.1, 4.45, 7.2, 2.2, blurb, size=16, color=RGBColor(0xC3, 0xCD, 0xE2),
        spacing=1.3)
    txt(s, 8.75, 1.9, 4.0, 4.9,
        [{"t": "—  " + i, "size": 14, "color": RGBColor(0x9E, 0xAE, 0xCB),
          "space_after": 9} for i in items])
    txt(s, W - M - 1.2, H - 0.40, 1.2, 0.25, str(_state["n"]), size=10,
        color=RGBColor(0x55, 0x63, 0x82), align=PP_ALIGN.RIGHT)
    note(s, notes)
    return s


def card(s, x, y, w, h, title, body=None, accent=PRIMARY, fill=WASH, title_size=14,
         body_size=None, start=15, floor=10.5):
    rect(s, x, y, w, h, fill=fill, line=LINE, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.045)
    rect(s, x, y + 0.10, 0.06, h - 0.20, fill=accent)
    px, pw = x + 0.24, w - 0.40
    txt(s, px, y + 0.12, pw, 0.32, title, size=title_size, color=accent, bold=True)
    if body:
        items = body if isinstance(body, (list, tuple)) else [body]
        bs = body_size or fit_size(items, pw, h - 0.62, start=start, floor=floor, gap_pt=5)
        txt(s, px, y + 0.50, pw, h - 0.58,
            [{"t": b, "size": bs, "color": BODY, "space_after": 5} for b in items],
            spacing=1.12)


def chip(s, x, y, w, h, text, color=PRIMARY, fill=None, size=11):
    rect(s, x, y, w, h, fill=fill or WASH2, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.35)
    txt(s, x, y, w, h, text, size=size, color=color, bold=True, align=PP_ALIGN.CENTER,
        anchor=MSO_ANCHOR.MIDDLE)


def strip(s, text, color=PRIMARY, label=None, y=6.42, h=0.58):
    rect(s, M, y, CW, h, fill=TINT.get(color, WASH2), shape=MSO_SHAPE.ROUNDED_RECTANGLE,
         radius=0.12)
    rect(s, M, y, 0.08, h, fill=color)
    lab = (label + "  ") if label else ""
    full = lab + text
    sz = 14 if len(full) < 120 else (13 if len(full) < 150 else 12)
    txt(s, M + 0.25, y, CW - 0.45, h, [{"t": full, "size": sz, "color": INK, "bold": True}],
        anchor=MSO_ANCHOR.MIDDLE)


def why(s, text, y=6.42, h=0.58):
    strip(s, text, VIOLET, "WHY ·", y=y, h=h)


def node(s, x, y, w, h, title, sub=None, color=PRIMARY, fill=None, title_size=13,
         sub_size=11):
    rect(s, x, y, w, h, fill=fill if fill is not None else WASH, line=color, lw=1.2,
         shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.10)
    if sub:
        txt(s, x + 0.06, y + 0.06, w - 0.12, h - 0.12,
            [{"t": title, "size": title_size, "color": color, "bold": True,
              "align": PP_ALIGN.CENTER, "space_after": 2},
             {"t": sub, "size": sub_size, "color": BODY, "align": PP_ALIGN.CENTER}],
            anchor=MSO_ANCHOR.MIDDLE, spacing=1.05)
    else:
        txt(s, x + 0.06, y, w - 0.12, h, title, size=title_size, color=color, bold=True,
            align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)


def _endcap(conn, head=False):
    ln = conn.line._get_or_add_ln()
    if head:
        ln.append(ln.makeelement(qn("a:headEnd"), {"type": "triangle", "w": "med", "len": "med"}))
    ln.append(ln.makeelement(qn("a:tailEnd"), {"type": "triangle", "w": "med", "len": "med"}))


def arrow(s, x1, y1, x2, y2, color=SLATE, lw=1.6, label=None, both=False, dashed=False,
          label_dx=0.0, label_dy=-0.30, label_w=2.0, label_size=11):
    c = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2),
                               Inches(y2))
    c.line.color.rgb = color
    c.line.width = Pt(lw)
    if dashed:
        c.line.dash_style = 4
    _endcap(c, head=both)
    if label:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        txt(s, mx - label_w / 2 + label_dx, my + label_dy, label_w, 0.28, label,
            size=label_size, color=color, bold=True, align=PP_ALIGN.CENTER)
    return c


def elbow(s, pts, color=SLATE, lw=1.6, dashed=False):
    for i in range(len(pts) - 1):
        (x1, y1), (x2, y2) = pts[i], pts[i + 1]
        c = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1),
                                   Inches(x2), Inches(y2))
        c.line.color.rgb = color
        c.line.width = Pt(lw)
        if dashed:
            c.line.dash_style = 4
        if i == len(pts) - 2:
            _endcap(c)


def pipeline(s, steps, x, y, w, h, colors=None, gap=0.32, title_size=13, sub_size=11):
    n = len(steps)
    bw = (w - gap * (n - 1)) / n
    for i, st in enumerate(steps):
        t, sb = st if isinstance(st, (tuple, list)) else (st, None)
        col = colors[i % len(colors)] if colors else PRIMARY
        bx = x + i * (bw + gap)
        node(s, bx, y, bw, h, t, sb, color=col, title_size=title_size, sub_size=sub_size)
        if i < n - 1:
            arrow(s, bx + bw + 0.04, y + h / 2, bx + bw + gap - 0.04, y + h / 2)
    return bw


def table(s, headers, rows, x, y, w, colw=None, size=12, row_h=0.36, header_h=0.40,
          cell_colors=None, bold_col0=True, align=None):
    nr, nc = len(rows) + 1, len(headers)
    shp = s.shapes.add_table(nr, nc, Inches(x), Inches(y), Inches(w),
                             Inches(header_h + row_h * len(rows)))
    tbl = shp.table
    if colw:
        tot = sum(colw)
        for i, c in enumerate(colw):
            tbl.columns[i].width = Emu(int(Inches(w) * c / tot))
    tbl.rows[0].height = Inches(header_h)
    for r in range(1, nr):
        tbl.rows[r].height = Inches(row_h)

    def _cell(r, c, text, bold, color, fill, al):
        cell = tbl.cell(r, c)
        cell.fill.solid()
        cell.fill.fore_color.rgb = fill
        cell.margin_left = Inches(0.08)
        cell.margin_right = Inches(0.06)
        cell.margin_top = Inches(0.02)
        cell.margin_bottom = Inches(0.02)
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf = cell.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.alignment = al
        run = p.add_run()
        run.text = str(text)
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.name = F
        run.font.color.rgb = color

    if align == "left":
        align = [PP_ALIGN.LEFT] * nc
    al = align or [PP_ALIGN.LEFT] + [PP_ALIGN.CENTER] * (nc - 1)
    for c, ht in enumerate(headers):
        _cell(0, c, ht, True, WHITE, NAVY, al[c])
    for r, row in enumerate(rows, start=1):
        base = WHITE if r % 2 == 1 else WASH
        for c, val in enumerate(row):
            col, bold = BODY, (bold_col0 and c == 0)
            if cell_colors and (r - 1, c) in cell_colors:
                col, bold = cell_colors[(r - 1, c)], True
            _cell(r, c, val, bold, col, base, al[c])
    return tbl


def code(s, x, y, w, h, lines, size=12, title=None):
    rect(s, x, y, w, h, fill=RGBColor(0x14, 0x1B, 0x2E), shape=MSO_SHAPE.ROUNDED_RECTANGLE,
         radius=0.04)
    ty = y + 0.14
    if title:
        txt(s, x + 0.2, y + 0.10, w - 0.4, 0.28, title, size=10.5,
            color=RGBColor(0x7E, 0x9C, 0xC8), bold=True, font=FM)
        ty = y + 0.44
    txt(s, x + 0.2, ty, w - 0.4, h - (ty - y) - 0.1,
        [{"t": ln, "size": size, "color": RGBColor(0xD7, 0xDF, 0xEE), "font": FM,
          "space_after": 1, "spacing": 1.05} for ln in lines])


# ------------------------------------------------------------- layouts --
def concept(prs, kicker, title, sub, points, cards=None, notes="", source=None,
            take=None, take_color=PRIMARY, left_w=6.4, start=17):
    s = slide(prs, title, kicker, sub)
    top, bottom = s._top + 0.05, (6.25 if take else 6.95)
    if cards:
        bullets(s, points, M, top, left_w, bottom - top, start=start)
        cx, cw = M + left_w + 0.3, CW - left_w - 0.3
        n, gap = len(cards), 0.16
        ch = (bottom - top - gap * (n - 1)) / n
        for i, c in enumerate(cards):
            t, b, col = c if len(c) == 3 else (c[0], c[1], PRIMARY)
            card(s, cx, top + i * (ch + gap), cw, ch, t, b, accent=col)
    else:
        bullets(s, points, M, top, CW, bottom - top, start=start)
    if take:
        if take_color == VIOLET:
            why(s, take)
        else:
            strip(s, take, take_color)
    note(s, notes, source)
    return s


def grid(prs, kicker, title, sub, cards, cols=3, notes="", source=None, take=None,
         take_color=PRIMARY, start=15):
    s = slide(prs, title, kicker, sub)
    top, bottom = s._top + 0.05, (6.25 if take else 6.95)
    n = len(cards)
    rows_n = -(-n // cols)
    gx, gy = 0.18, 0.16
    cw = (CW - gx * (cols - 1)) / cols
    ch = (bottom - top - gy * (rows_n - 1)) / rows_n
    for i, c in enumerate(cards):
        t, b, col = c if len(c) == 3 else (c[0], c[1], PRIMARY)
        r, k = divmod(i, cols)
        card(s, M + k * (cw + gx), top + r * (ch + gy), cw, ch, t, b, accent=col, start=start)
    if take:
        if take_color == VIOLET:
            why(s, take)
        else:
            strip(s, take, take_color)
    note(s, notes, source)
    return s


def figure(prs, kicker, title, sub, image, points, notes="", source=None, take=None,
           take_color=GOOD, fig_w=7.7, start=15, border=False):
    s = slide(prs, title, kicker, sub)
    top, bottom = s._top + 0.05, (6.25 if take else 6.95)
    pic(s, image, M, top, fig_w, bottom - top, border=border)
    bullets(s, points, M + fig_w + 0.3, top, CW - fig_w - 0.3, bottom - top, start=start,
            floor=10.5)
    if take:
        if take_color == VIOLET:
            why(s, take)
        else:
            strip(s, take, take_color)
    note(s, notes, source)
    return s


def tabular(prs, kicker, title, sub, headers, rows, colw=None, notes="", source=None,
            take=None, take_color=GOOD, size=13, row_h=0.40, below=None, cell_colors=None,
            align=None):
    s = slide(prs, title, kicker, sub)
    ty = s._top + 0.08
    table(s, headers, rows, M, ty, CW, colw=colw, size=size, row_h=row_h,
          cell_colors=cell_colors, align=align)
    if below:
        by = ty + 0.40 + row_h * len(rows) + 0.22
        bh = (6.25 if take else 6.95) - by
        if bh > 0.3:
            bullets(s, below, M, by, CW, bh, start=15, floor=10.5, gap=5)
    if take:
        if take_color == VIOLET:
            why(s, take)
        else:
            strip(s, take, take_color)
    note(s, notes, source)
    return s


def eq_slide(prs, kicker, title, sub, latex, symbols, example=None, why_text=None,
             notes="", source=None, label=None, group=None, eq_size=34, eq_h=1.45,
             extra=None, sym_size=22, example_title="TINY EXAMPLE", example_color=GOOD,
             sym_w=1.55):
    """One big equation, a symbol legend (each symbol typeset), an example card and a WHY strip.
    `extra` = optional list of further LaTeX lines shown under the main equation."""
    s = slide(prs, title, kicker, sub)
    top = s._top + 0.05
    lines = [latex] + list(extra or [])
    box_h = eq_h + 0.55 * (len(lines) - 1)
    rect(s, M, top, CW, box_h, fill=WASH, line=LINE, shape=MSO_SHAPE.ROUNDED_RECTANGLE,
         radius=0.06)
    rect(s, M, top + 0.12, 0.07, box_h - 0.24, fill=VIOLET)
    if len(lines) == 1:
        place_eq(s, latex, M + 0.3, top + 0.1, CW - 0.6, box_h - 0.2, size=eq_size)
    else:
        lh = (box_h - 0.2) / len(lines)
        for i, ln in enumerate(lines):
            place_eq(s, ln, M + 0.3, top + 0.1 + i * lh, CW - 0.6, lh,
                     size=eq_size if i == 0 else eq_size - 8)
    if label:
        formula(group or kicker, label, latex)
    y0 = top + box_h + 0.2
    bottom = 6.25 if why_text else 6.95
    lw = 7.0 if example else CW
    txt(s, M, y0, lw, 0.3, "WHAT EACH SYMBOL MEANS", size=12, color=VIOLET, bold=True)
    n = max(1, len(symbols))
    rh = min(0.62, (bottom - y0 - 0.38) / n)
    for i, (sym, meaning) in enumerate(symbols):
        yy = y0 + 0.36 + i * rh
        place_eq(s, sym, M, yy, sym_w, rh - 0.04, size=sym_size, halign="left")
        fs = fit_size([meaning], lw - sym_w - 0.15, rh - 0.02, start=15, floor=10.5, gap_pt=0)
        txt(s, M + sym_w + 0.1, yy, lw - sym_w - 0.15, rh - 0.02, meaning, size=fs,
            color=BODY, anchor=MSO_ANCHOR.MIDDLE)
    if example:
        ex_x = M + lw + 0.25
        card(s, ex_x, y0, CW - lw - 0.25, bottom - y0, example_title, example,
             accent=example_color, start=14.5)
    if why_text:
        why(s, why_text)
    note(s, notes, source)
    return s


def eq_fig_slide(prs, kicker, title, sub, latex, image, symbols, why_text=None, notes="",
                 source=None, label=None, group=None, eq_size=32, eq_h=1.2, extra=None,
                 fig_w=6.3, sym_size=20, after=None):
    """Equation on top; a figure bottom-left; symbol legend (+ optional text lines) bottom-right."""
    s = slide(prs, title, kicker, sub)
    top = s._top + 0.05
    lines = [latex] + list(extra or [])
    box_h = eq_h + 0.5 * (len(lines) - 1)
    rect(s, M, top, CW, box_h, fill=WASH, line=LINE, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.06)
    rect(s, M, top + 0.12, 0.07, box_h - 0.24, fill=VIOLET)
    lh = (box_h - 0.16) / len(lines)
    for i, ln in enumerate(lines):
        place_eq(s, ln, M + 0.3, top + 0.08 + i * lh, CW - 0.6, lh,
                 size=eq_size if i == 0 else eq_size - 6)
    if label:
        formula(group or kicker, label, latex)
    y0 = top + box_h + 0.18
    bottom = 6.25 if why_text else 6.95
    pic(s, image, M, y0, fig_w, bottom - y0)
    rx, rw = M + fig_w + 0.3, CW - fig_w - 0.3
    n = len(symbols)
    after_h = 0.0
    if after:
        after_h = min(1.6, 0.42 * len(after) + 0.2)
    rh = min(0.6, (bottom - y0 - 0.36 - after_h) / max(1, n))
    txt(s, rx, y0, rw, 0.3, "WHAT EACH SYMBOL MEANS", size=12, color=VIOLET, bold=True)
    sw = 1.35
    for i, (sym, meaning) in enumerate(symbols):
        yy = y0 + 0.34 + i * rh
        place_eq(s, sym, rx, yy, sw, rh - 0.04, size=sym_size, halign="left")
        fs = fit_size([meaning], rw - sw - 0.1, rh - 0.02, start=14, floor=10, gap_pt=0)
        txt(s, rx + sw + 0.08, yy, rw - sw - 0.1, rh - 0.02, meaning, size=fs, color=BODY,
            anchor=MSO_ANCHOR.MIDDLE)
    if after:
        ay = y0 + 0.36 + n * rh + 0.05
        bullets(s, after, rx, ay, rw, bottom - ay, start=14, floor=10, gap=4)
    if why_text:
        why(s, why_text)
    note(s, notes, source)
    return s


def steps_slide(prs, kicker, title, sub, rows, notes="", source=None, take=None,
                eq_w=6.2, eq_size=26, group=None):
    """A derivation: rows = [(chip label, latex, explanation, formula_label|None), ...]."""
    s = slide(prs, title, kicker, sub)
    top, bottom = s._top + 0.05, (6.25 if take else 6.95)
    n, gap = len(rows), 0.12
    rh = (bottom - top - gap * (n - 1)) / n
    for i, row in enumerate(rows):
        lab, latex, ex = row[:3]
        flab = row[3] if len(row) > 3 else None
        y = top + i * (rh + gap)
        chip(s, M, y + rh / 2 - 0.18, 1.05, 0.36, lab, color=VIOLET, size=11)
        rect(s, M + 1.18, y, eq_w, rh, fill=WASH, line=LINE, shape=MSO_SHAPE.ROUNDED_RECTANGLE,
             radius=0.05)
        place_eq(s, latex, M + 1.28, y + 0.05, eq_w - 0.2, rh - 0.1, size=eq_size)
        if flab:
            formula(group or kicker, flab, latex)
        ew = CW - 1.18 - eq_w - 0.25
        exs = ex if isinstance(ex, (list, tuple)) else [ex]
        fs = fit_size(exs, ew, rh - 0.06, start=15, floor=10.5, gap_pt=3)
        txt(s, M + 1.18 + eq_w + 0.25, y, ew, rh,
            [{"t": e, "size": fs, "color": BODY, "space_after": 3} for e in exs],
            anchor=MSO_ANCHOR.MIDDLE)
    if take:
        why(s, take)
    note(s, notes, source)
    return s


def qa_card(s, x, y, w, h, q, a=None, tag=None, accent=PRIMARY, q_size=15):
    rect(s, x, y, w, h, fill=WHITE, line=LINE, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.04)
    rect(s, x, y, 0.06, h, fill=accent)
    ty = y + 0.12
    if tag:
        chip(s, x + 0.2, y + 0.1, 0.9, 0.3, tag, color=accent, size=10)
        ty = y + 0.48
    if a is None:
        qh = h - (ty - y) - 0.1
    else:
        cpl = max(10, int((w - 0.4) / (q_size * 0.5 / 72.0)))
        qh = (-(-len(q) // cpl)) * q_size * 1.35 / 72.0 + 0.04
    fs = fit_size([q], w - 0.4, qh, start=q_size, floor=11, gap_pt=0)
    txt(s, x + 0.22, ty, w - 0.4, qh, q, size=fs, color=INK, bold=True)
    if a:
        ay = ty + qh + 0.06
        ah = y + h - ay - 0.08
        items = a if isinstance(a, (list, tuple)) else [a]
        fs2 = fit_size(items, w - 0.4, ah, start=15, floor=11, gap_pt=3)
        txt(s, x + 0.22, ay, w - 0.4, ah,
            [{"t": i, "size": fs2, "color": BODY, "space_after": 3} for i in items])
