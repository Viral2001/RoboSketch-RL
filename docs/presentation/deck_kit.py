"""
RoboSketch-RL  |  slide design kit
-------------------------------------------------
A small design system on top of python-pptx so every slide in the deck shares
one visual language: palette, type scale, title band, cards, flows, tables,
equation blocks and speaker notes.

Used by build_deck.py. Nothing project-specific lives here.
"""
import os

from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

# ------------------------------------------------------------------ theme --
INK = RGBColor(0x0F, 0x17, 0x2A)          # near-black slate  (headings)
BODY = RGBColor(0x33, 0x41, 0x55)         # body text
MUTED = RGBColor(0x64, 0x74, 0x8B)        # captions
FAINT = RGBColor(0x94, 0xA3, 0xB8)
LINE = RGBColor(0xD8, 0xDF, 0xE9)         # hairline borders
WASH = RGBColor(0xF5, 0xF7, 0xFB)         # card background
WASH2 = RGBColor(0xEC, 0xF1, 0xF8)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

TINT_RED = RGBColor(0xFB, 0xEC, 0xEC)     # pale zone fills for diagrams
TINT_GREEN = RGBColor(0xEC, 0xF7, 0xF1)
TINT_BLUE = RGBColor(0xE9, 0xEF, 0xFB)
TINT_AMBER = RGBColor(0xFD, 0xF3, 0xE3)
TINT_VIOLET = RGBColor(0xF1, 0xEC, 0xFB)

NAVY = RGBColor(0x11, 0x1C, 0x39)         # section dividers / title slide
PRIMARY = RGBColor(0x2B, 0x4A, 0xCB)      # indigo - structure, "what"
ACCENT = RGBColor(0x0E, 0x9C, 0xC4)       # cyan   - vision / data
GOOD = RGBColor(0x0D, 0x8A, 0x5F)         # green  - results, validated
WARN = RGBColor(0xC2, 0x7A, 0x0A)         # amber  - challenges
BAD = RGBColor(0xC0, 0x35, 0x35)          # red    - failures / rejected
VIOLET = RGBColor(0x6D, 0x45, 0xC7)       # purple - RL / learning
SLATE = RGBColor(0x54, 0x66, 0x82)

F = "Segoe UI"                             # UI font, present on every Windows
FM = "Consolas"                            # monospace for code / equations

W, H = 13.333, 7.5                         # 16:9 canvas, inches
M = 0.58                                   # left / right margin
CW = W - 2 * M                             # usable content width
TOP = 1.34                                 # first content row
BOT = 6.92                                 # last usable y

FIGDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figures")

_state = {"n": 0, "footer": "RoboSketch-RL"}


# --------------------------------------------------------------- plumbing --
def new_deck(footer="RoboSketch-RL"):
    prs = Presentation()
    prs.slide_width = Inches(W)
    prs.slide_height = Inches(H)
    _state["footer"] = footer
    _state["n"] = 0
    return prs


def _blank(prs):
    return prs.slides.add_slide(prs.slide_layouts[6])


def _noshadow(shp):
    try:
        shp.shadow.inherit = False
    except Exception:
        pass
    return shp


def rect(slide, x, y, w, h, fill=None, line=None, lw=0.75, shape=MSO_SHAPE.RECTANGLE,
         radius=None):
    s = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    _noshadow(s)
    if radius is not None and shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        try:
            s.adjustments[0] = radius
        except Exception:
            pass
    if fill is None:
        s.fill.background()
    else:
        s.fill.solid()
        s.fill.fore_color.rgb = fill
    if line is None:
        s.line.fill.background()
    else:
        s.line.color.rgb = line
        s.line.width = Pt(lw)
    s.text_frame.text = ""
    return s


def txt(slide, x, y, w, h, content, size=14, color=BODY, bold=False, italic=False,
        align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, font=F, spacing=1.15,
        space_after=3, wrap=True):
    """content: a string, or a list of items.

    Each item may be a plain string or a dict:
      {"t": text, "size":, "color":, "bold":, "italic":, "font":, "level":,
       "align":, "space_before":, "bullet": True/False}
    """
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = wrap
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
        if d.get("space_before"):
            p.space_before = Pt(d["space_before"])
        p.level = d.get("level", 0)
        r = p.add_run()
        r.text = d["t"]
        f = r.font
        f.name = d.get("font", font)
        f.size = Pt(d.get("size", size))
        f.bold = d.get("bold", bold)
        f.italic = d.get("italic", italic)
        f.color.rgb = d.get("color", color)
    return box


def bullets(slide, items, x, y, w, h, size=14, color=BODY, tight=False,
            bullet_color=PRIMARY, marker="•"):
    """items: str | (level, str) | dict. Level 1 items get an en-dash marker."""
    conv = []
    for it in items:
        if isinstance(it, dict):
            conv.append(it)
            continue
        lvl, text = it if isinstance(it, tuple) else (0, it)
        pre = f"{marker}  " if lvl == 0 else "–  "
        conv.append({"t": pre + text, "size": size if lvl == 0 else size - 1,
                     "color": color if lvl == 0 else MUTED,
                     "level": lvl, "space_after": 3 if tight else 7})
    return txt(slide, x, y, w, h, conv, size=size, color=color)


def note(slide, text):
    slide.notes_slide.notes_text_frame.text = text.strip()


def pic(slide, name, x, y, w=None, h=None, center_in=None):
    """Place a figure. If center_in=(x,y,w,h) the image is fitted and centred."""
    path = name if os.path.isabs(name) else os.path.join(FIGDIR, name)
    if not os.path.exists(path):
        return None
    if center_in:
        from PIL import Image
        bx, by, bw, bh = center_in
        iw, ih = Image.open(path).size
        s = min(bw / iw, bh / ih)
        dw, dh = iw * s, ih * s
        return slide.shapes.add_picture(path, Inches(bx + (bw - dw) / 2),
                                        Inches(by + (bh - dh) / 2),
                                        Inches(dw), Inches(dh))
    kw = {}
    if w:
        kw["width"] = Inches(w)
    if h:
        kw["height"] = Inches(h)
    return slide.shapes.add_picture(path, Inches(x), Inches(y), **kw)


# ----------------------------------------------------------------- slides --
def slide(prs, title, kicker=None, sub=None, rule=True):
    """Standard content slide with title band, kicker, footer and page number."""
    s = _blank(prs)
    _state["n"] += 1
    rect(s, 0, 0, W, H, fill=WHITE)
    # accent tick + kicker
    if kicker:
        rect(s, M, 0.40, 0.12, 0.185, fill=PRIMARY)
        txt(s, M + 0.22, 0.36, 7.0, 0.26, kicker.upper(), size=10.5, color=PRIMARY,
            bold=True)
    tsize = 25 if len(title) <= 46 else (22 if len(title) <= 58 else 19.5)
    txt(s, M, 0.62 + (0.04 if tsize < 25 else 0), CW - 1.2, 0.52, title, size=tsize,
        color=INK, bold=True, spacing=0.95)
    if sub:
        txt(s, M, 1.10, CW - 2.4, 0.30, sub, size=12.5, color=MUTED, italic=True)
    if rule:
        rect(s, M, 1.19 if not sub else 1.44, CW, 0.014, fill=LINE)
    # footer
    txt(s, M, H - 0.42, 8.0, 0.25, _state["footer"], size=9, color=FAINT)
    txt(s, W - M - 1.2, H - 0.42, 1.2, 0.25, str(_state["n"]), size=9, color=FAINT,
        align=PP_ALIGN.RIGHT)
    s._body_top = 1.62 if sub else 1.40
    return s


def section(prs, number, title, blurb, items=None, notes_text=None):
    """Full-bleed dark divider slide."""
    s = _blank(prs)
    _state["n"] += 1
    rect(s, 0, 0, W, H, fill=NAVY)
    rect(s, 0, 0, 0.16, H, fill=PRIMARY)
    txt(s, 1.15, 2.05, 3.0, 1.0, f"{number:02d}", size=64, color=PRIMARY, bold=True)
    txt(s, 1.15, 3.05, 9.5, 0.9, title, size=34, color=WHITE, bold=True, spacing=0.95)
    rect(s, 1.2, 4.02, 1.6, 0.03, fill=ACCENT)
    txt(s, 1.15, 4.28, 8.6, 1.2, blurb, size=14.5,
        color=RGBColor(0xC3, 0xCD, 0xE2), spacing=1.3)
    if items:
        txt(s, 8.7, 2.15, 3.6, 3.6,
            [{"t": "—  " + i, "size": 12, "color": RGBColor(0x8E, 0x9E, 0xBB),
              "space_after": 9} for i in items])
    txt(s, W - M - 1.2, H - 0.42, 1.2, 0.25, str(_state["n"]), size=9,
        color=RGBColor(0x55, 0x63, 0x82), align=PP_ALIGN.RIGHT)
    default = (f"SECTION {number} — {title}.\n\n{blurb}\n\n"
               "Use this divider as a breath and a signpost: say in one sentence what "
               "this section will establish, then move on. "
               + (("The slides ahead cover: " + " · ".join(items) + ".")
                  if items else ""))
    note(s, notes_text or default)
    return s


def title_slide(prs, title, subtitle, meta_left, meta_right, tagline=None):
    s = _blank(prs)
    _state["n"] += 1
    rect(s, 0, 0, W, H, fill=NAVY)
    rect(s, 0, 0, W, 0.20, fill=PRIMARY)
    rect(s, 0, 0.20, W * 0.42, 0.06, fill=ACCENT)
    txt(s, 1.1, 1.62, 11.2, 0.32, "M.TECH RESEARCH PROJECT  ·  PROGRESS REVIEW",
        size=11.5, color=ACCENT, bold=True)
    txt(s, 1.1, 2.05, 11.2, 1.5, title, size=42, color=WHITE, bold=True, spacing=0.98)
    rect(s, 1.13, 3.42, 2.0, 0.035, fill=PRIMARY)
    txt(s, 1.1, 3.66, 10.4, 0.9, subtitle, size=17.5,
        color=RGBColor(0xC9, 0xD4, 0xE8), spacing=1.25)
    if tagline:
        txt(s, 1.1, 4.62, 10.4, 0.4, tagline, size=12.5, color=RGBColor(0x8E, 0x9E, 0xBB),
            italic=True)
    rect(s, 1.1, 5.35, 11.1, 0.012, fill=RGBColor(0x2C, 0x3A, 0x5C))
    txt(s, 1.1, 5.58, 5.4, 1.1, meta_left, size=12, color=RGBColor(0xA9, 0xB6, 0xCE),
        spacing=1.35)
    txt(s, 7.0, 5.58, 5.2, 1.1, meta_right, size=12, color=RGBColor(0xA9, 0xB6, 0xCE),
        spacing=1.35, align=PP_ALIGN.RIGHT)
    return s


# ------------------------------------------------------------ composables --
def fit_size(items, w_in, h_in, start=11.0, floor=8.5, spacing=1.16, gap_pt=4):
    """Largest font (<= start) at which `items` fit a w_in x h_in text area."""
    sz = start
    while sz > floor:
        cpl = max(8, int(w_in / (sz * 0.503 / 72.0)))     # chars per line
        lines = sum(max(1, -(-len(str(t)) // cpl)) for t in items)
        need = lines * sz * spacing / 72.0 + len(items) * gap_pt / 72.0
        if need <= h_in:
            return sz
        sz -= 0.5
    return floor


def card(slide, x, y, w, h, title, body=None, accent=PRIMARY, fill=WASH,
         title_size=12.5, body_size=None, bar=True, mono=False, border=True):
    """A titled panel with a coloured left bar."""
    rect(slide, x, y, w, h, fill=fill, line=LINE if border else None,
         shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.045)
    if bar:
        rect(slide, x, y + 0.10, 0.055, h - 0.20, fill=accent)
    px = x + (0.22 if bar else 0.16)
    pw = w - (0.38 if bar else 0.32)
    txt(slide, px, y + 0.13, pw, 0.28, title, size=title_size, color=accent, bold=True)
    if body:
        items = body if isinstance(body, (list, tuple)) else [body]
        bs = body_size or fit_size([i if isinstance(i, str) else i.get("t", "")
                                    for i in items], pw, h - 0.60)
        conv = []
        for it in items:
            if isinstance(it, dict):
                d = dict(it)
                d.setdefault("size", bs)
                conv.append(d)
            else:
                conv.append({"t": it, "size": bs, "color": BODY,
                             "space_after": 4,
                             "font": FM if mono else F})
        txt(slide, px, y + 0.45, pw, h - 0.55, conv, spacing=1.16)
    return None


def kpi(slide, x, y, w, h, value, label, color=PRIMARY, sub=None, fill=WASH):
    rect(slide, x, y, w, h, fill=fill, line=LINE, shape=MSO_SHAPE.ROUNDED_RECTANGLE,
         radius=0.06)
    vs = 27 if len(str(value)) <= 6 else (22 if len(str(value)) <= 9 else 18)
    while vs > 12 and len(str(value)) * vs * 0.55 / 72.0 > w - 0.12:
        vs -= 1
    txt(slide, x, y + 0.14 + (27 - vs) * 0.006, w, 0.55, value, size=vs, color=color,
        bold=True, align=PP_ALIGN.CENTER, spacing=0.9)
    nl = label.count("\n") + 1
    lh = nl * 10.5 * 1.16 / 72.0
    txt(slide, x + 0.08, y + 0.70, w - 0.16, lh + 0.04, label, size=10.5, color=BODY,
        align=PP_ALIGN.CENTER, spacing=1.16)
    if sub:
        txt(slide, x + 0.06, y + 0.74 + lh, w - 0.12, 0.3, sub, size=9, color=MUTED,
            align=PP_ALIGN.CENTER, spacing=1.1)


def chip(slide, x, y, w, h, text, color=PRIMARY, fill=None, size=10.5):
    fill = fill or WASH2
    rect(slide, x, y, w, h, fill=fill, line=None, shape=MSO_SHAPE.ROUNDED_RECTANGLE,
         radius=0.35)
    txt(slide, x, y + (h - 0.22) / 2 - 0.02, w, 0.24, text, size=size, color=color,
        bold=True, align=PP_ALIGN.CENTER)


def node(slide, x, y, w, h, title, sub=None, color=PRIMARY, fill=None,
         title_size=12, sub_size=9.5, shape=MSO_SHAPE.ROUNDED_RECTANGLE):
    """A flow-diagram node: tinted box, bold label, optional small caption."""
    fill = fill if fill is not None else WASH
    rect(slide, x, y, w, h, fill=fill, line=color, lw=1.1, shape=shape, radius=0.10)
    if sub:
        # vertically centre the (title + n-line caption) group inside the box
        nl = sub.count("\n") + 1
        th = title_size / 72.0 * 1.35
        sh = nl * sub_size / 72.0 * 1.28
        y0 = y + max(0.05, (h - th - sh - 0.06) / 2)
        txt(slide, x + 0.06, y0, w - 0.12, th, title, size=title_size,
            color=color, bold=True, align=PP_ALIGN.CENTER, spacing=1.0)
        txt(slide, x + 0.06, y0 + th + 0.05, w - 0.12, sh, sub, size=sub_size,
            color=MUTED, align=PP_ALIGN.CENTER, spacing=1.12)
    else:
        txt(slide, x + 0.06, y, w - 0.12, h, title, size=title_size, color=color,
            bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, spacing=1.05)


def _endcap(conn, tail=True, head=False, kind="triangle"):
    ln = conn.line._get_or_add_ln()
    if head:
        e = ln.makeelement(qn("a:headEnd"), {"type": kind, "w": "med", "len": "med"})
        ln.append(e)
    if tail:
        e = ln.makeelement(qn("a:tailEnd"), {"type": kind, "w": "med", "len": "med"})
        ln.append(e)


def arrow(slide, x1, y1, x2, y2, color=SLATE, lw=1.4, dashed=False, both=False,
          label=None, label_dx=0.0, label_dy=-0.28, label_size=9.5,
          label_color=None, label_w=1.6):
    c = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1),
                                   Inches(x2), Inches(y2))
    c.line.color.rgb = color
    c.line.width = Pt(lw)
    if dashed:
        c.line.dash_style = 4  # MSO_LINE_DASH_STYLE.DASH
    _endcap(c, tail=True, head=both)
    if label:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        txt(slide, mx - label_w / 2 + label_dx, my + label_dy, label_w, 0.26, label,
            size=label_size, color=label_color or color, align=PP_ALIGN.CENTER,
            bold=True)
    return c


def elbow(slide, pts, color=SLATE, lw=1.4, arrow_end=True, dashed=False):
    """Poly-line built from straight segments through pts [(x,y), ...]."""
    for i in range(len(pts) - 1):
        (x1, y1), (x2, y2) = pts[i], pts[i + 1]
        c = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1),
                                       Inches(x2), Inches(y2))
        c.line.color.rgb = color
        c.line.width = Pt(lw)
        if dashed:
            c.line.dash_style = 4
        if arrow_end and i == len(pts) - 2:
            _endcap(c)


def pipeline(slide, steps, x, y, w, h, colors=None, gap=0.30, sub_size=9.5,
             title_size=11.5, arrow_color=SLATE):
    """Horizontal box-and-arrow flow. steps = [(title, sub), ...]."""
    n = len(steps)
    bw = (w - gap * (n - 1)) / n
    for i, st in enumerate(steps):
        t, sb = st if isinstance(st, (tuple, list)) else (st, None)
        col = (colors[i % len(colors)] if colors else PRIMARY)
        bx = x + i * (bw + gap)
        node(slide, bx, y, bw, h, t, sb, color=col, title_size=title_size,
             sub_size=sub_size)
        if i < n - 1:
            arrow(slide, bx + bw + 0.05, y + h / 2, bx + bw + gap - 0.05, y + h / 2,
                  color=arrow_color, lw=1.5)
    return bw


def table(slide, headers, rows, x, y, w, colw=None, size=10.5, header_size=10.5,
          row_h=0.30, header_h=0.34, header_fill=NAVY, header_color=WHITE,
          zebra=True, align=None, cell_colors=None, bold_col0=False):
    """A clean, hand-styled table (python-pptx default styles are too heavy)."""
    nr, nc = len(rows) + 1, len(headers)
    shp = slide.shapes.add_table(nr, nc, Inches(x), Inches(y), Inches(w),
                                 Inches(header_h + row_h * len(rows)))
    tbl = shp.table
    tbl.first_row = True
    tbl.horz_banding = False
    try:
        tbl._graphic_frame.graphic.graphicData.tbl.tblPr.set("firstRow", "1")
    except Exception:
        pass
    if colw:
        tot = sum(colw)
        for i, cwi in enumerate(colw):
            tbl.columns[i].width = Emu(int(Inches(w) * cwi / tot))
    tbl.rows[0].height = Inches(header_h)
    for r in range(1, nr):
        tbl.rows[r].height = Inches(row_h)

    def _cell(r, c, text, bold, color, fill, sz, al):
        cell = tbl.cell(r, c)
        cell.fill.solid()
        cell.fill.fore_color.rgb = fill
        cell.margin_left = Inches(0.09)
        cell.margin_right = Inches(0.07)
        cell.margin_top = Inches(0.03)
        cell.margin_bottom = Inches(0.03)
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf = cell.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.alignment = al
        p.line_spacing = 1.0
        r0 = p.add_run()
        r0.text = str(text)
        r0.font.size = Pt(sz)
        r0.font.bold = bold
        r0.font.name = F
        r0.font.color.rgb = color

    aligns = align or [PP_ALIGN.LEFT] * nc
    for c, htxt in enumerate(headers):
        _cell(0, c, htxt, True, header_color, header_fill, header_size, aligns[c])
    for r, row in enumerate(rows, start=1):
        base = WHITE if (r % 2 == 1 or not zebra) else WASH
        for c, val in enumerate(row):
            fill = base
            color = BODY
            bold = bold_col0 and c == 0
            if cell_colors and (r - 1, c) in cell_colors:
                color = cell_colors[(r - 1, c)]
                bold = True
            _cell(r, c, val, bold, color, fill, size, aligns[c])
    return tbl


def eqn(slide, x, y, w, lines, size=15, h=None, color=INK, caption=None,
        fill=WASH, align=PP_ALIGN.CENTER):
    """A boxed equation block. `lines` = str | list of str/dict."""
    items = lines if isinstance(lines, (list, tuple)) else [lines]
    h = h or (0.34 + 0.36 * len(items) + (0.24 if caption else 0))
    rect(slide, x, y, w, h, fill=fill, line=LINE, shape=MSO_SHAPE.ROUNDED_RECTANGLE,
         radius=0.05)
    conv = []
    for it in items:
        d = {"t": it} if isinstance(it, str) else dict(it)
        d.setdefault("size", size)
        d.setdefault("color", color)
        d.setdefault("font", "Cambria Math")
        d.setdefault("align", align)
        d.setdefault("space_after", 5)
        conv.append(d)
    txt(slide, x + 0.16, y + 0.16, w - 0.32, h - 0.3, conv)
    if caption:
        txt(slide, x + 0.16, y + h - 0.30, w - 0.32, 0.26, caption, size=9.5,
            color=MUTED, align=align, italic=True)
    return h


def code(slide, x, y, w, h, lines, size=10, title=None, fill=RGBColor(0x14, 0x1B, 0x2E)):
    """A dark code panel. lines = list of str, or dicts for coloured lines."""
    rect(slide, x, y, w, h, fill=fill, line=None, shape=MSO_SHAPE.ROUNDED_RECTANGLE,
         radius=0.04)
    ty = y + 0.12
    if title:
        txt(slide, x + 0.18, y + 0.10, w - 0.36, 0.26, title, size=9.5,
            color=RGBColor(0x7E, 0x9C, 0xC8), bold=True, font=FM)
        ty = y + 0.40
    conv = []
    for ln in lines:
        d = {"t": ln} if isinstance(ln, str) else dict(ln)
        d.setdefault("size", size)
        d.setdefault("color", RGBColor(0xD7, 0xDF, 0xEE))
        d.setdefault("font", FM)
        d.setdefault("space_after", 1)
        d.setdefault("spacing", 1.08)
        conv.append(d)
    txt(slide, x + 0.18, ty, w - 0.36, h - (ty - y) - 0.10, conv)


def legend(slide, x, y, entries, size=9.5, gap=0.14, box=0.13):
    """entries = [(color, label), ...] laid out horizontally."""
    cx = x
    for col, lab in entries:
        rect(slide, cx, y + 0.035, box, box, fill=col,
             shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.25)
        est = 0.075 * len(lab) + 0.10
        txt(slide, cx + box + 0.07, y, est, 0.22, lab, size=size, color=MUTED)
        cx += box + 0.07 + est + gap


def bar_chart(slide, x, y, w, h, categories, series, colors=None, title=None,
              max_scale=None, number_format="0.00", font_size=10):
    cd = CategoryChartData()
    cd.categories = categories
    for nm, vals in series:
        cd.add_series(nm, vals)
    gf = slide.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(x), Inches(y),
                                Inches(w), Inches(h), cd)
    ch = gf.chart
    ch.has_title = bool(title)
    if title:
        ch.chart_title.text_frame.text = title
        ch.chart_title.text_frame.paragraphs[0].runs[0].font.size = Pt(11)
        ch.chart_title.text_frame.paragraphs[0].runs[0].font.color.rgb = INK
    ch.has_legend = len(series) > 1
    if ch.has_legend:
        ch.legend.position = XL_LEGEND_POSITION.TOP
        ch.legend.include_in_layout = False
        ch.legend.font.size = Pt(font_size)
        ch.legend.font.color.rgb = BODY
    ch.font.size = Pt(font_size)
    ch.font.name = F
    ch.font.color.rgb = BODY
    va = ch.value_axis
    va.has_major_gridlines = True
    va.major_gridlines.format.line.color.rgb = LINE
    va.major_gridlines.format.line.width = Pt(0.5)
    va.tick_labels.number_format = number_format
    va.tick_labels.number_format_is_linked = False
    if max_scale:
        va.maximum_scale = max_scale
    va.minimum_scale = 0
    va.format.line.color.rgb = LINE
    ch.category_axis.format.line.color.rgb = LINE
    for i, plot_series in enumerate(ch.plots[0].series):
        if colors:
            plot_series.format.fill.solid()
            plot_series.format.fill.fore_color.rgb = colors[i % len(colors)]
        plot_series.format.line.fill.background()
    ch.plots[0].gap_width = 60
    ch.plots[0].overlap = -10
    return ch


def qa(slide, question, answer, x, y, w, h, tag=None, accent=PRIMARY, q_size=12.5,
       a_size=None):
    """A question card for the anticipated-questions section.

    Both the question and the answer auto-shrink so the card never overflows.
    """
    rect(slide, x, y, w, h, fill=WHITE, line=LINE, shape=MSO_SHAPE.ROUNDED_RECTANGLE,
         radius=0.035)
    rect(slide, x, y, 0.05, h, fill=accent)
    if tag:
        chip(slide, x + 0.18, y + 0.13, min(1.5, 0.10 * len(tag) + 0.35), 0.26, tag,
             color=accent, size=8.5)
    iw = w - 0.44
    ty = y + (0.46 if tag else 0.14)
    # question: how many lines at q_size?
    qcpl = max(10, int(iw / (q_size * 0.503 / 72.0)))
    qlines = max(1, -(-len(question + "Q  ") // qcpl))
    qh = qlines * q_size * 1.12 / 72.0
    txt(slide, x + 0.20, ty, iw, qh + 0.06, "Q  " + question, size=q_size, color=INK,
        bold=True, spacing=1.12)
    items = answer if isinstance(answer, (list, tuple)) else [answer]
    ay = ty + qh + 0.12
    ah = y + h - ay - 0.12
    sz = a_size or fit_size(items, iw, ah, start=11.0, floor=8.0, spacing=1.2,
                            gap_pt=4)
    txt(slide, x + 0.20, ay, iw, ah,
        [{"t": a, "size": sz, "color": BODY, "space_after": 4} for a in items],
        spacing=1.2)


def decision_slide(prs, kicker, title, sub, what, why, alternatives, chosen,
                   challenges, result, notes_text, result_color=GOOD):
    """The repeatable 'what / why / alternatives / chosen / challenges / result'
    layout used for every completed stage."""
    s = slide(prs, title, kicker, sub)
    y0, gap = 1.62, 0.20
    cw = (CW - 2 * gap) / 3
    ch1 = 2.32
    card(s, M, y0, cw, ch1, "WHAT WE DID", what, accent=PRIMARY)
    card(s, M + cw + gap, y0, cw, ch1, "WHY IT WAS NECESSARY", why, accent=ACCENT)
    card(s, M + 2 * (cw + gap), y0, cw, ch1, "ALTERNATIVES CONSIDERED", alternatives,
         accent=SLATE)
    y1 = y0 + ch1 + 0.22
    ch2 = 2.28
    card(s, M, y1, cw, ch2, "WHY THIS APPROACH", chosen, accent=VIOLET)
    card(s, M + cw + gap, y1, cw, ch2, "CHALLENGES FACED", challenges, accent=WARN)
    card(s, M + 2 * (cw + gap), y1, cw, ch2, "RESULT / EVIDENCE", result,
         accent=result_color, fill=RGBColor(0xF1, 0xF9, 0xF5))
    note(s, notes_text)
    return s
