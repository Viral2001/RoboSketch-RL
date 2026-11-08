"""
RoboSketch-RL  |  slide preview renderer (layout QA)
-------------------------------------------------
There is no PowerPoint/LibreOffice on this machine, so this renders an
approximate raster of each slide straight from the .pptx XML (shapes, fills,
text, tables, pictures) using PIL. Good enough to catch overlaps, overflow and
off-slide elements before the deck is opened for real.

Run:  conda run -n robosketch python docs/presentation/preview.py [slide_numbers...]
Out:  docs/presentation/preview/slide_XXX.png
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont
from pptx import Presentation
from pptx.util import Emu

HERE = os.path.dirname(os.path.abspath(__file__))
PPTX = os.path.join(HERE, "RoboSketch-RL_Progress_Review.pptx")
OUT = os.path.join(HERE, "preview")
os.makedirs(OUT, exist_ok=True)

SCALE = 110          # pixels per inch
EMU_IN = 914400.0

FONTS = {}
FONT_FILES = {
    ("Segoe UI", False): "C:/Windows/Fonts/segoeui.ttf",
    ("Segoe UI", True): "C:/Windows/Fonts/segoeuib.ttf",
    ("Consolas", False): "C:/Windows/Fonts/consola.ttf",
    ("Consolas", True): "C:/Windows/Fonts/consolab.ttf",
    ("Cambria Math", False): "C:/Windows/Fonts/cambria.ttc",
    ("Cambria Math", True): "C:/Windows/Fonts/cambriab.ttf",
}


def font(name, size_pt, bold):
    key = (name, bold, round(size_pt, 1))
    if key not in FONTS:
        path = FONT_FILES.get((name, bold)) or FONT_FILES[("Segoe UI", bold)]
        px = max(6, int(size_pt * SCALE / 72.0))
        try:
            FONTS[key] = ImageFont.truetype(path, px)
        except Exception:
            FONTS[key] = ImageFont.load_default()
    return FONTS[key]


def px(emu):
    return int(round(emu / EMU_IN * SCALE))


def rgb(color_obj, default=(120, 120, 120)):
    try:
        c = color_obj.rgb
        return (c[0], c[1], c[2])
    except Exception:
        return default


def wrap(draw, text, fnt, max_w):
    lines = []
    for raw in text.split("\n"):
        words, cur = raw.split(" "), ""
        for w in words:
            trial = (cur + " " + w).strip()
            if draw.textlength(trial, font=fnt) <= max_w or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = w
        lines.append(cur)
    return lines


def draw_tf(draw, tf, x, y, w, h, anchor="t", warn=None, tag=""):
    cy = y + 2
    blocks = []
    for p in tf.paragraphs:
        text = "".join(r.text for r in p.runs) or ""
        if not p.runs:
            blocks.append((text, 12, False, (60, 60, 60), 1, 0, "l"))
            continue
        r0 = p.runs[0]
        sz = r0.font.size.pt if r0.font.size else 14
        nm = r0.font.name or "Segoe UI"
        bold = bool(r0.font.bold)
        col = rgb(r0.font.color, (40, 40, 40))
        ls = p.line_spacing or 1.15
        sa = p.space_after.pt if p.space_after else 0
        al = {1: "l", 2: "c", 3: "r"}.get(p.alignment, "l") if p.alignment else "l"
        try:
            al = {"LEFT": "l", "CENTER": "c", "RIGHT": "r"}.get(str(p.alignment).split()[0], "l")
        except Exception:
            pass
        blocks.append((text, sz, bold, col, ls, sa, al, nm))
    total = 0
    rendered = []
    for b in blocks:
        text, sz, bold, col, ls, sa, al = b[:7]
        nm = b[7] if len(b) > 7 else "Segoe UI"
        fnt = font(nm, sz, bold)
        lines = wrap(draw, text, fnt, w - 4) if text else [""]
        lh = sz * SCALE / 72.0 * ls
        total += lh * len(lines) + sa * SCALE / 72.0
        rendered.append((lines, fnt, col, lh, sa, al))
    if anchor == "m":
        cy = y + max(0, (h - total) / 2)
    for lines, fnt, col, lh, sa, al in rendered:
        for ln in lines:
            tw = draw.textlength(ln, font=fnt)
            tx = x + 2
            if al == "c":
                tx = x + (w - tw) / 2
            elif al == "r":
                tx = x + w - tw - 2
            draw.text((tx, cy), ln, font=fnt, fill=col)
            cy += lh
        cy += sa * SCALE / 72.0
    if warn is not None and total > h + 6:
        warn.append(f"      overflow {tag}: text {total/SCALE*72:.0f}pt-h in box "
                    f"{h/SCALE*72:.0f}pt-h")
    return total


def render(prs, idx, sld, problems):
    W = px(prs.slide_width)
    H = px(prs.slide_height)
    img = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(img)
    warn = []
    for shp in sld.shapes:
        try:
            x, y, w, h = px(shp.left), px(shp.top), px(shp.width), px(shp.height)
        except Exception:
            continue
        if x < -4 or y < -4 or x + w > W + 4 or y + h > H + 4:
            warn.append(f"      off-slide: {shp.shape_type} at "
                        f"({x/SCALE:.2f},{y/SCALE:.2f}) size {w/SCALE:.2f}x{h/SCALE:.2f}")
        st = str(shp.shape_type)
        if "PICTURE" in st:
            try:
                im = Image.open(shp.image.blob and __import__("io").BytesIO(shp.image.blob))
                img.paste(im.convert("RGB").resize((max(1, w), max(1, h))), (x, y))
            except Exception:
                d.rectangle([x, y, x + w, y + h], outline=(200, 0, 200))
            continue
        if "TABLE" in st or shp.has_table if hasattr(shp, "has_table") else False:
            pass
        if getattr(shp, "has_table", False):
            tbl = shp.table
            cy = y
            for r, row in enumerate(tbl.rows):
                rh = px(row.height)
                cx = x
                for c, cell in enumerate(row.cells):
                    cwid = px(tbl.columns[c].width)
                    fill = (255, 255, 255)
                    try:
                        fill = rgb(cell.fill.fore_color, (255, 255, 255))
                    except Exception:
                        pass
                    d.rectangle([cx, cy, cx + cwid, cy + rh], fill=fill,
                                outline=(225, 230, 238))
                    draw_tf(d, cell.text_frame, cx + 6, cy + 2, cwid - 10, rh - 4,
                            anchor="m", warn=warn, tag=f"table r{r}c{c}")
                    cx += cwid
                cy += rh
            continue
        if getattr(shp, "has_chart", False):
            d.rectangle([x, y, x + w, y + h], fill=(246, 248, 252),
                        outline=(180, 190, 205))
            d.text((x + 8, y + 8), "[chart]", font=font("Segoe UI", 11, True),
                   fill=(90, 100, 120))
            continue
        is_conn = "CONNECTOR" in st or shp.__class__.__name__ == "Connector"
        if is_conn:
            col = rgb(shp.line.color, (140, 150, 165))
            try:
                flip_h = shp._element.spPr.xfrm.get("flipH") == "1"
                flip_v = shp._element.spPr.xfrm.get("flipV") == "1"
            except Exception:
                flip_h = flip_v = False
            x1, y1, x2, y2 = x, y, x + w, y + h
            if flip_h:
                x1, x2 = x2, x1
            if flip_v:
                y1, y2 = y2, y1
            d.line([x1, y1, x2, y2], fill=col, width=2)
            continue
        fill = None
        try:
            if shp.fill.type is not None and str(shp.fill.type).startswith("SOLID"):
                fill = rgb(shp.fill.fore_color, (240, 240, 240))
        except Exception:
            fill = None
        outline = None
        try:
            if shp.line.fill.type is not None and str(shp.line.fill.type).startswith("SOLID"):
                outline = rgb(shp.line.color, (200, 200, 200))
        except Exception:
            outline = None
        if fill or outline:
            d.rectangle([x, y, x + w, y + h], fill=fill, outline=outline)
        if shp.has_text_frame and shp.text_frame.text.strip():
            anchor = "m" if str(getattr(shp.text_frame, "vertical_anchor", "")).startswith("MIDDLE") else "t"
            draw_tf(d, shp.text_frame, x + 4, y + 3, w - 8, h - 6, anchor=anchor,
                    warn=warn, tag=f"'{shp.text_frame.text[:26]}'")
    img.save(os.path.join(OUT, f"slide_{idx:03d}.png"))
    if warn:
        problems.append((idx, warn))
    return img


def main():
    which = [int(a) for a in sys.argv[1:]] if len(sys.argv) > 1 else None
    prs = Presentation(PPTX)
    problems = []
    for i, sld in enumerate(prs.slides, start=1):
        if which and i not in which:
            continue
        render(prs, i, sld, problems)
    def ascii_(t):
        return t.encode("ascii", "replace").decode("ascii")

    print(f"rendered -> {OUT}")
    if problems:
        print("\nLAYOUT WARNINGS")
        for idx, ws in problems:
            print(f"  slide {idx}:")
            for w in ws:
                print(ascii_(w))
    else:
        print("no layout warnings")


if __name__ == "__main__":
    main()
