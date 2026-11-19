import base64, datetime, math, os, uuid
from lxml import etree
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE
from pptx.dml.color import RGBColor
from pptx.oxml.ns import qn

SKILL = "/Users/user3/Library/Application Support/Claude/local-agent-mode-sessions/skills-plugin/70c96888-2dd9-459e-9c07-d638a3e2fd72/9132b803-3fcf-4197-8962-0b74eb073c3c/skills/presentation-builder/assets"
OUT = "/Users/user3/Desktop/Ulkrisht/icici-logo-audit/deliverables"
NAME = "icici-logo-visibility-audit"
os.makedirs(OUT, exist_ok=True)

LOGO, IMAN, SWOOSH = (f"{SKILL}/icici-logo.png", f"{SKILL}/icici-iman.png", f"{SKILL}/title-swoosh.png")
ORANGE, MAROON, NAVY, BEIGE, GOLD, GREY, WHITE = "E77817", "97291E", "053C6D", "D1CFBB", "FDB92A", "525252", "FFFFFF"
LEFT, WIDTH, TOP = 0.83, 11.67, 0.50
AUDIT_DATE = "October 28, 2026"

# ---------------------------------------------------------------- content
WINS = [("Amazon", "On every hero banner"),
        ("Vijay Sales", "In the bank offer strip"),
        ("Cleartrip", "8+ logos, offers page"),
        ("MakeMyTrip", "Tile in Bank Offers tab"),
        ("Croma", "Top card, product page"),
        ("OnePlus", "Logo one click deep")]

GAPS = [("Tata CLiQ", 10, "RBL, HSBC, AU, HDFC, DBS +5"),
        ("Reliance Digital", 8, "SBI, HDFC, Axis, PNB, IDFC +3"),
        ("HP", 6, "SBI, Axis, HDFC, Kotak, Yes +1"),
        ("Sony", 3, "Yes, Kotak, BOB"),
        ("Ajio", 3, "HSBC, HDFC, SBI"),
        ("Zomato", 2, "RBL, SBI"),
        ("Samsung", 1, "Axis co-brand card"),
        ("Swiggy", 1, "HDFC co-brand card"),
        ("Goibibo", 1, "HDFC")]

TEXT_ONLY = [("Apple", "“Amex, Axis and", "ICICI Bank cards”"),
             ("Google Store", "“HDFC Bank or", "ICICI Bank”"),
             ("Xiaomi", "“Up to ₹3,000 off on", "ICICI Credit Card”")]

STATUS = {"logo": ("Logo shown", ORANGE), "text": ("Text only", GOLD),
          "rival": ("Rivals shown", MAROON), "none": ("No bank shown", BEIGE)}
TABLE = [("Amazon", "logo"), ("Vijay Sales", "logo"), ("Cleartrip", "logo"), ("MakeMyTrip", "logo"),
         ("Croma", "logo"), ("OnePlus", "logo"),
         ("Apple", "text"), ("Google Store", "text"), ("Xiaomi", "text"), ("LG", "none"),
         ("Tata CLiQ", "rival"), ("Reliance Digital", "rival"), ("HP", "rival"), ("Sony", "rival"),
         ("Ajio", "rival"), ("Zomato", "rival"), ("Samsung", "rival"), ("Swiggy", "rival"),
         ("Goibibo", "rival"), ("Dell", "none")]

STEPS = [("1", "Fix the nine gaps", "Rivals already hold the slot"),
         ("2", "Turn text into logo", "Apple, Google Store, Xiaomi"),
         ("3", "Bring the logo up front", "OnePlus hides it a click deep")]

# ---------------------------------------------------------------- pptx helpers
def est_lines(text, pt, width_in):
    cpl = max(1, int(width_in / (pt / 72.0 * 0.5)))
    return max(1, math.ceil(len(text) / cpl))

def text_block(slide, text, pt, rgb, left, top, width, bold=True, gap=0.0, font=None, align=None, lines=None):
    lines = lines or est_lines(text, pt, width)
    lh = pt * 1.2 / 72.0
    box = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(lh * lines))
    tf = box.text_frame
    tf.word_wrap = True
    tf.auto_size = None
    tf.vertical_anchor = MSO_ANCHOR.TOP
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    if align: p.alignment = align
    r = p.add_run(); r.text = text
    r.font.size = Pt(pt)
    r.font.name = font or ("Mulish ExtraBold" if bold else "Mulish SemiBold")
    r.font.color.rgb = RGBColor.from_string(rgb)
    return top + lh * lines + gap

def place_title_block(slide, heading, sub=None):
    if est_lines(heading, 32, WIDTH) > 2:
        raise ValueError("heading too long: " + heading)
    y = text_block(slide, heading, 32, MAROON, LEFT, TOP, WIDTH, gap=0.10)
    if sub:
        y = text_block(slide, sub, 24, NAVY, LEFT, y, WIDTH)
    return y + 0.45

def rect(slide, l, t, w, h, rgb, rounded=True):
    s = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if rounded else MSO_SHAPE.RECTANGLE,
                               Inches(l), Inches(t), Inches(w), Inches(h))
    s.fill.solid(); s.fill.fore_color.rgb = RGBColor.from_string(rgb)
    s.line.fill.background(); s.shadow.inherit = False
    if rounded: s.adjustments[0] = 0.08
    return s

def oval(slide, l, t, d, rgb):
    s = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(l), Inches(t), Inches(d), Inches(d))
    s.fill.solid(); s.fill.fore_color.rgb = RGBColor.from_string(rgb)
    s.line.fill.background(); s.shadow.inherit = False
    return s

def iman(slide):
    slide.shapes.add_picture(IMAN, Inches(0.41), Inches(6.50), Inches(0.79), Inches(0.83))

def set_date_field(paragraph, size_pt=20, color=NAVY, typeface="Mulish SemiBold"):
    p = paragraph._p
    for child in p.findall(qn("a:r")) + p.findall(qn("a:fld")):
        p.remove(child)
    fld = etree.SubElement(p, qn("a:fld"))
    fld.set("id", "{%s}" % str(uuid.uuid4()).upper())
    fld.set("type", "datetime4")
    rPr = etree.SubElement(fld, qn("a:rPr"))
    rPr.set("lang", "en-US"); rPr.set("sz", str(int(size_pt * 100))); rPr.set("dirty", "0")
    fill = etree.SubElement(rPr, qn("a:solidFill"))
    etree.SubElement(fill, qn("a:srgbClr")).set("val", color)
    etree.SubElement(rPr, qn("a:latin")).set("typeface", typeface)
    today = datetime.date.today()
    etree.SubElement(fld, qn("a:t")).text = "%s %d, %d" % (today.strftime("%B"), today.day, today.year)

def hero(prs, title, sub=None, date=False):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    s.shapes.add_picture(SWOOSH, 0, 0, prs.slide_width, prs.slide_height)
    s.shapes.add_picture(LOGO, Inches(8.02), Inches(0.19), Inches(5.06), Inches(1.06))
    text_block(s, title, 48, NAVY, 6.02, 3.63, 6.31, lines=2)
    if sub:
        text_block(s, sub, 24, MAROON, 6.01, 5.45, 5.71)
    if date:
        box = s.shapes.add_textbox(Inches(6.00), Inches(6.53), Inches(3.09), Inches(0.40))
        box.text_frame.word_wrap = True
        set_date_field(box.text_frame.paragraphs[0])
    return s

def content(prs, heading, sub):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    iman(s)
    return s, place_title_block(s, heading, sub)

def source_line(s, text):
    text_block(s, text, 15, GREY, 1.45, 6.75, 11.0, bold=False, font="Mulish Medium")

# ---------------------------------------------------------------- build pptx
prs = Presentation()
prs.slide_width, prs.slide_height = Emu(12192000), Emu(6858000)

# 1 title
hero(prs, "ICICI Bank logo visibility audit", "Festive Bonanza partner brands", date=True)

# 2 metric: 6 of 20 + dot grid
order = ["logo"] * 6 + ["text"] * 3 + ["rival"] * 9 + ["none"] * 2
s, y = content(prs, "Only 6 of 20 brands show our logo", "Brand websites with live ICICI offers")
text_block(s, str(order.count("logo")), 110, ORANGE, LEFT, y + 0.10, 2.2, font="Mulish Black", lines=1)
text_block(s, "of 20 brands", 24, NAVY, LEFT, y + 2.05, 4.0)
text_block(s, "show the ICICI Bank logo", 24, GREY, LEFT, y + 2.50, 4.6, bold=False)
d, gx, gy, x0, y0 = 0.62, 0.86, 0.86, 5.55, y + 0.10
for i, k in enumerate(order):
    oval(s, x0 + (i % 5) * gx, y0 + (i // 5) * gy, d, STATUS[k][1])
lx = 10.05
for j, k in enumerate(["logo", "text", "rival", "none"]):
    oval(s, lx, y0 + 0.12 + j * 0.86, 0.32, STATUS[k][1])
    n = order.count(k)
    text_block(s, f"{STATUS[k][0]} ({n})", 18, GREY, lx + 0.45, y0 + 0.12 + j * 0.86, 2.3, bold=False)
source_line(s, f"Source: homepages, offer and product pages, checked {AUDIT_DATE}")

# 3 wins: 3 x 2 cards
s, y = content(prs, "Where ICICI Bank shows up today", "Six brands carry our logo")
cw, ch, gx, gy = 3.63, 1.55, 0.39, 0.30
for i, (brand, line) in enumerate(WINS):
    r_, c_ = divmod(i, 3)
    x = LEFT + c_ * (cw + gx); ty = y + r_ * (ch + gy)
    rect(s, x, ty, cw, ch, BEIGE)
    oval(s, x + 0.30, ty + 0.30, 0.45, ORANGE)
    text_block(s, "✓", 20, WHITE, x + 0.30, ty + 0.36, 0.45, align=PP_ALIGN.CENTER)
    text_block(s, brand, 24, MAROON, x + 0.95, ty + 0.31, cw - 1.2)
    text_block(s, line, 18, GREY, x + 0.30, ty + 0.98, cw - 0.55, bold=False)

# 4 gaps: bars of rival banks shown, ICICI = 0
s, y = content(prs, "Rival banks fill the slot we leave empty", "Nine brands show other banks, never ICICI")
bar_max, bx, bw, rh = 10, 3.45, 4.0, 0.47
for i, (brand, n, names) in enumerate(GAPS):
    ty = y - 0.05 + i * rh
    text_block(s, brand, 18, NAVY, LEFT, ty + 0.02, 2.45, align=PP_ALIGN.RIGHT)
    w = bw * n / bar_max
    rect(s, bx, ty + 0.04, w, 0.32, [MAROON, ORANGE, NAVY, GOLD, "F4858E", "00C0F3", "917BB9", BEIGE, MAROON][i], rounded=False)
    text_block(s, str(n), 18, MAROON, bx + w + 0.12, ty + 0.02, 0.5)
    text_block(s, names, 16, GREY, 8.15, ty + 0.04, 4.35, bold=False)
source_line(s, f"Bank names and logos seen on homepage, offer and product pages, {AUDIT_DATE}")

# 5 text only
s, y = content(prs, "Three brands name ICICI, but show no logo", "A text mention is easy to miss")
cw, gap = 3.63, 0.39
for i, (brand, l1, l2) in enumerate(TEXT_ONLY):
    x = LEFT + i * (cw + gap)
    rect(s, x, y, cw, 2.55, BEIGE)
    text_block(s, brand, 24, MAROON, x + 0.30, y + 0.30, cw - 0.6)
    text_block(s, l1, 20, GREY, x + 0.30, y + 1.05, cw - 0.6, bold=False)
    text_block(s, l2, 20, GREY, x + 0.30, y + 1.45, cw - 0.6, bold=False)
text_block(s, "LG and Dell show no bank at all", 20, GREY, LEFT, y + 2.95, 11.0, bold=False)

# 6 full audit table: two columns of 10 rows
s, y = content(prs, "All 20 brands at a glance", None)
rh, colw = 0.42, 5.55
for col in range(2):
    x = LEFT + col * (colw + 0.57)
    rect(s, x, y - 0.05, colw, rh, NAVY, rounded=False)
    text_block(s, "Brand", 18, WHITE, x + 0.20, y + 0.02, 2.8)
    text_block(s, "ICICI logo status", 18, WHITE, x + 2.95, y + 0.02, 2.5)
    for r_ in range(10):
        brand, k = TABLE[col * 10 + r_]
        ty = y + (r_ + 1) * rh
        if r_ % 2 == 0:
            rect(s, x, ty - 0.05, colw, rh, "EDECE3", rounded=False)
        text_block(s, brand, 18, GREY, x + 0.20, ty + 0.02, 2.7, bold=False)
        oval(s, x + 2.95, ty + 0.08, 0.20, STATUS[k][1])
        text_block(s, STATUS[k][0], 18, GREY, x + 3.30, ty + 0.02, 2.2, bold=False)

# 7 impact
s = prs.slides.add_slide(prs.slide_layouts[6])
rect(s, 0, 0, 13.333, 7.5, ORANGE, rounded=False)
iman(s)
text_block(s, "We fund the offer.", 54, WHITE, 1.2, 2.45, 11.0, align=PP_ALIGN.CENTER)
text_block(s, "Others get the visibility.", 54, WHITE, 1.2, 3.45, 11.0, align=PP_ALIGN.CENTER)

# 8 next steps
s, y = content(prs, "Three asks for alliance managers", "Start with the nine gap brands")
cw, gap = 3.6, 0.43
for i, (num, head, body) in enumerate(STEPS):
    x = LEFT + i * (cw + gap)
    rect(s, x, y, cw, 3.2, BEIGE)
    oval(s, x + 0.35, y + 0.35, 0.75, ORANGE)
    text_block(s, num, 28, WHITE, x + 0.35, y + 0.52, 0.75, align=PP_ALIGN.CENTER)
    ny = text_block(s, head, 24, MAROON, x + 0.35, y + 1.40, cw - 0.6, gap=0.12)
    text_block(s, body, 20, GREY, x + 0.35, ny, cw - 0.6, bold=False)

# 9 thank you
hero(prs, "Thank you.")

pptx_path = f"{OUT}/{NAME}.pptx"
prs.save(pptx_path)

chk = Presentation(pptx_path)
assert any(f.get("type") == "datetime4" for f in chk.slides[0].shapes._spTree.iter(qn("a:fld")))
for i, sl in enumerate(chk.slides):
    for sh in sl.shapes:
        if sh.has_text_frame:
            for p in sh.text_frame.paragraphs:
                for r in p.runs:
                    assert "—" not in r.text
                    if r.font.size and r.font.size.pt < 15:
                        raise SystemExit(f"slide {i+1} under 15pt: {r.text}")
print("pptx ok:", pptx_path, len(chk.slides), "slides")

# ---------------------------------------------------------------- html
b64 = lambda p: base64.b64encode(open(p, "rb").read()).decode()
LOGO64, IMAN64, SWOOSH64 = b64(LOGO), b64(IMAN), b64(SWOOSH)

def dot(color, extra=""):
    return f'<span class="dot" style="background:#{color};{extra}"></span>'

dots = "".join(f'<span class="gdot" style="background:#{STATUS[k][1]}"></span>' for k in order)
legend = "".join(f'<div class="leg">{dot(STATUS[k][1])}<span>{STATUS[k][0]} ({order.count(k)})</span></div>'
                 for k in ["logo", "text", "rival", "none"])
wins = "".join(f'<div class="card win"><div class="whead"><span class="tick">&#10003;</span><h3>{b}</h3></div><p>{l}</p></div>'
               for b, l in WINS)
bars = "".join(
    f'<div class="brow"><span class="bname">{b}</span><div class="btrack"><div class="bar" style="--w:{n/10*100:.1f}%;background:#{c}"></div>'
    f'<span class="bnum">{n}</span></div><span class="bbanks">{names}</span></div>'
    for (b, n, names), c in zip(GAPS, [MAROON, ORANGE, NAVY, GOLD, "F4858E", "00C0F3", "917BB9", BEIGE, MAROON]))
textonly = "".join(f'<div class="card quote"><h3>{b}</h3><p>{a}<br>{c}</p></div>' for b, a, c in TEXT_ONLY)

def table_html(rows):
    body = "".join(f'<tr><td>{b}</td><td>{dot(STATUS[k][1])}{STATUS[k][0]}</td></tr>' for b, k in rows)
    return f'<table><thead><tr><th>Brand</th><th>ICICI logo status</th></tr></thead><tbody>{body}</tbody></table>'

steps = "".join(f'<div class="card step"><span class="num">{n}</span><h3>{h}</h3><p>{b}</p></div>' for n, h, b in STEPS)

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ICICI Logo Visibility Audit</title>
<link rel="icon" href="data:image/png;base64,{IMAN64}">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Mulish:wght@400;500;600;700;800;900&display=swap">
<style>
:root {{
  --orange:#E77817; --maroon:#97291E; --navy:#053C6D; --beige:#D1CFBB; --gold:#FDB92A; --grey:#525252; --white:#FFFFFF;
  --cw:min(100vw, 177.78vh); --in:calc(var(--cw) / 13.333);
  --ease:cubic-bezier(0.16,1,0.3,1);
}}
* {{ margin:0; padding:0; box-sizing:border-box; }}
html {{ scroll-snap-type:y mandatory; scroll-behavior:smooth; }}
body {{ font-family:'Mulish', Arial, sans-serif; background:#FFFFFF; color:var(--grey); overflow-x:hidden; }}
.pt {{ }}
.slide {{ height:100vh; scroll-snap-align:start; display:flex; align-items:center; justify-content:center; background:#FFFFFF; }}
.canvas {{ position:relative; width:var(--cw); height:calc(var(--cw) * 0.5625); overflow:hidden; }}
.u {{ position:absolute; }}
.iman {{ position:absolute; left:calc(var(--in)*0.41); top:calc(var(--in)*6.50); width:calc(var(--in)*0.79); height:calc(var(--in)*0.83); }}
.logo {{ position:absolute; left:calc(var(--in)*8.02); top:calc(var(--in)*0.19); width:calc(var(--in)*5.06); height:calc(var(--in)*1.06); }}
.hero .canvas {{ background:url('data:image/png;base64,{SWOOSH64}') center/100% 100% no-repeat #FFFFFF; }}
.hero-title {{ position:absolute; left:calc(var(--in)*6.02); top:calc(var(--in)*3.63); width:calc(var(--in)*6.31); font-size:calc(var(--in)*48/72); font-weight:800; color:var(--navy); line-height:1.2; }}
.hero-sub {{ position:absolute; left:calc(var(--in)*6.01); top:calc(var(--in)*5.45); width:calc(var(--in)*5.71); font-size:calc(var(--in)*24/72); font-weight:800; color:var(--maroon); }}
.hero-date {{ position:absolute; left:calc(var(--in)*6.00); top:calc(var(--in)*6.53); font-size:calc(var(--in)*20/72); font-weight:600; color:var(--navy); }}
.title-block {{ position:absolute; left:calc(var(--in)*0.83); top:calc(var(--in)*0.50); width:calc(var(--in)*11.67); display:flex; flex-direction:column; gap:calc(var(--in)*0.10); }}
.title-block h2 {{ font-size:calc(var(--in)*32/72); font-weight:800; color:var(--maroon); line-height:1.2; text-wrap:balance; }}
.title-block p {{ font-size:calc(var(--in)*24/72); font-weight:800; color:var(--navy); line-height:1.2; }}
.body {{ position:absolute; left:calc(var(--in)*0.83); top:calc(var(--in)*1.95); width:calc(var(--in)*11.67); }}
.source {{ position:absolute; left:calc(var(--in)*1.45); top:calc(var(--in)*6.75); font-size:calc(var(--in)*15/72); font-weight:500; color:var(--grey); }}
.dot {{ display:inline-block; width:0.8em; height:0.8em; border-radius:50%; margin-right:0.5em; vertical-align:-0.05em; }}
/* metric */
.metric-wrap {{ display:grid; grid-template-columns:calc(var(--in)*4.6) calc(var(--in)*4.3) 1fr; align-items:start; }}
.metric {{ font-size:calc(var(--in)*110/72); font-weight:900; color:var(--orange); line-height:1; }}
.metric-ctx {{ font-size:calc(var(--in)*24/72); font-weight:800; color:var(--navy); margin-top:calc(var(--in)*0.25); }}
.metric-ctx2 {{ font-size:calc(var(--in)*24/72); font-weight:600; color:var(--grey); }}
.grid {{ display:grid; grid-template-columns:repeat(5, calc(var(--in)*0.62)); gap:calc(var(--in)*0.24); }}
.gdot {{ width:calc(var(--in)*0.62); height:calc(var(--in)*0.62); border-radius:50%; }}
.leg {{ display:flex; align-items:center; font-size:calc(var(--in)*18/72); font-weight:600; margin:calc(var(--in)*0.12) 0 calc(var(--in)*0.42); }}
/* cards */
.row {{ display:flex; gap:calc(var(--in)*0.29); }}
.card {{ background:var(--beige); border-radius:calc(var(--in)*0.18); padding:calc(var(--in)*0.30); flex:1; }}
.wins {{ display:grid; grid-template-columns:repeat(3, 1fr); gap:calc(var(--in)*0.30) calc(var(--in)*0.39); }}
.win {{ min-height:calc(var(--in)*1.55); }}
.whead {{ display:flex; align-items:center; gap:calc(var(--in)*0.20); }}
.card .whead h3 {{ margin:0; }}
.win .tick {{ width:calc(var(--in)*0.45); height:calc(var(--in)*0.45); font-size:calc(var(--in)*20/72); flex:none; }}
.win p {{ margin-top:calc(var(--in)*0.18); font-size:calc(var(--in)*18/72); }}
.quotes {{ gap:calc(var(--in)*0.39); }}
.quote {{ height:calc(var(--in)*2.55); }}
.quote h3 {{ margin-top:0; margin-bottom:calc(var(--in)*0.30); }}
.tick, .num {{ display:flex; align-items:center; justify-content:center; width:calc(var(--in)*0.55); height:calc(var(--in)*0.55); border-radius:50%; background:var(--orange); color:#fff; font-weight:800; font-size:calc(var(--in)*24/72); }}
.num {{ width:calc(var(--in)*0.75); height:calc(var(--in)*0.75); font-size:calc(var(--in)*28/72); }}
.card h3 {{ font-size:calc(var(--in)*24/72); font-weight:800; color:var(--maroon); margin:calc(var(--in)*0.25) 0 calc(var(--in)*0.12); }}
.card p {{ font-size:calc(var(--in)*20/72); font-weight:600; color:var(--grey); line-height:1.35; }}
.step {{ height:calc(var(--in)*3.2); padding:calc(var(--in)*0.35); }}
.steps {{ gap:calc(var(--in)*0.43); }}
/* bars */
.brow {{ display:grid; grid-template-columns:calc(var(--in)*2.45) calc(var(--in)*4.7) 1fr; column-gap:calc(var(--in)*0.17); height:calc(var(--in)*0.47); align-items:center; }}
.bname {{ text-align:right; font-size:calc(var(--in)*18/72); font-weight:800; color:var(--navy); }}
.btrack {{ display:flex; align-items:center; }}
.bar {{ height:calc(var(--in)*0.32); width:0; transition:width 0.9s var(--ease); }}
.slide.visible .bar {{ width:calc(var(--in)*4.0 * var(--wf, 1)); }}
.bnum {{ font-size:calc(var(--in)*18/72); font-weight:800; color:var(--maroon); margin-left:calc(var(--in)*0.12); }}
.bbanks {{ font-size:calc(var(--in)*16/72); font-weight:600; color:var(--grey); }}
/* chips */
.chips {{ display:grid; grid-template-columns:repeat(5, calc(var(--in)*2.10)); gap:calc(var(--in)*0.30) calc(var(--in)*0.29); }}
.chip {{ background:var(--beige); border-radius:calc(var(--in)*0.18); height:calc(var(--in)*0.80); display:flex; align-items:center; justify-content:center; font-size:calc(var(--in)*20/72); font-weight:800; color:var(--navy); }}
.note {{ margin-top:calc(var(--in)*0.45); font-size:calc(var(--in)*20/72); font-weight:600; }}
/* table */
.tables {{ display:flex; gap:calc(var(--in)*0.57); }}
table {{ width:calc(var(--in)*5.55); border-collapse:collapse; font-size:calc(var(--in)*18/72); }}
th {{ background:var(--navy); color:#fff; font-weight:800; text-align:left; padding:calc(var(--in)*0.07) calc(var(--in)*0.20); }}
td {{ font-weight:600; padding:0 calc(var(--in)*0.20); height:calc(var(--in)*0.42); }}
tbody tr:nth-child(odd) {{ background:#EDECE3; }}
/* impact */
.impact .canvas {{ background:var(--orange); }}
.impact-text {{ position:absolute; inset:0; display:flex; flex-direction:column; align-items:center; justify-content:center; color:#fff; font-size:calc(var(--in)*54/72); font-weight:800; line-height:1.4; text-align:center; }}
/* motion */
.reveal {{ opacity:0; transform:translateY(16px); transition:opacity 0.3s var(--ease), transform 0.3s var(--ease); }}
.slide.visible .reveal {{ opacity:1; transform:none; }}
@media (prefers-reduced-motion: reduce) {{ .reveal {{ transform:none; }} .bar {{ transition:none; }} }}
.progress {{ position:fixed; top:0; left:0; height:3px; background:var(--orange); z-index:100; transition:width 0.3s; }}
.nav {{ position:fixed; right:1rem; top:50%; transform:translateY(-50%); display:flex; flex-direction:column; gap:0.6rem; z-index:100; }}
.nav button {{ width:10px; height:10px; border-radius:50%; border:2px solid var(--grey); background:transparent; cursor:pointer; padding:0; }}
@media (max-width:768px) {{ .nav {{ display:none; }} }}
</style>
</head>
<body>
<div class="progress"></div>
<nav class="nav"></nav>

<section class="slide hero"><div class="canvas">
  <img class="logo" src="data:image/png;base64,{LOGO64}" alt="ICICI Bank">
  <h1 class="hero-title reveal">ICICI Bank logo visibility audit</h1>
  <p class="hero-sub reveal">Festive Bonanza partner brands</p>
  <p class="hero-date reveal" id="deck-date"></p>
</div></section>

<section class="slide"><div class="canvas">
  <div class="title-block"><h2>Only {order.count("logo")} of 20 brands show our logo</h2><p>Brand websites with live ICICI offers</p></div>
  <div class="body metric-wrap">
    <div class="reveal"><div class="metric count-up" data-target="{order.count("logo")}">0</div><div class="metric-ctx">of 20 brands</div><div class="metric-ctx2">show the ICICI Bank logo</div></div>
    <div class="grid reveal">{dots}</div>
    <div class="reveal">{legend}</div>
  </div>
  <p class="source">Source: homepages, offer and product pages, checked {AUDIT_DATE}</p>
  <img class="iman" src="data:image/png;base64,{IMAN64}" alt="">
</div></section>

<section class="slide"><div class="canvas">
  <div class="title-block"><h2>Where ICICI Bank shows up today</h2><p>Six brands carry our logo</p></div>
  <div class="body wins reveal">{wins}</div>
  <img class="iman" src="data:image/png;base64,{IMAN64}" alt="">
</div></section>

<section class="slide"><div class="canvas">
  <div class="title-block"><h2>Rival banks fill the slot we leave empty</h2><p>Nine brands show other banks, never ICICI</p></div>
  <div class="body reveal" style="top:calc(var(--in)*1.90)">{bars}</div>
  <p class="source">Bank names and logos seen on homepage, offer and product pages, {AUDIT_DATE}</p>
  <img class="iman" src="data:image/png;base64,{IMAN64}" alt="">
</div></section>

<section class="slide"><div class="canvas">
  <div class="title-block"><h2>Three brands name ICICI, but show no logo</h2><p>A text mention is easy to miss</p></div>
  <div class="body reveal"><div class="row quotes">{textonly}</div><p class="note">LG and Dell show no bank at all</p></div>
  <img class="iman" src="data:image/png;base64,{IMAN64}" alt="">
</div></section>

<section class="slide"><div class="canvas">
  <div class="title-block"><h2>All 20 brands at a glance</h2></div>
  <div class="body tables reveal" style="top:calc(var(--in)*1.48)">{table_html(TABLE[:10])}{table_html(TABLE[10:])}</div>
  <img class="iman" src="data:image/png;base64,{IMAN64}" alt="">
</div></section>

<section class="slide impact"><div class="canvas">
  <div class="impact-text reveal"><span>We fund the offer.</span><span>Others get the visibility.</span></div>
  <img class="iman" src="data:image/png;base64,{IMAN64}" alt="">
</div></section>

<section class="slide"><div class="canvas">
  <div class="title-block"><h2>Three asks for alliance managers</h2><p>Start with the nine gap brands</p></div>
  <div class="body row steps reveal">{steps}</div>
  <img class="iman" src="data:image/png;base64,{IMAN64}" alt="">
</div></section>

<section class="slide hero"><div class="canvas">
  <img class="logo" src="data:image/png;base64,{LOGO64}" alt="ICICI Bank">
  <h1 class="hero-title reveal">Thank you.</h1>
</div></section>

<script>
document.getElementById('deck-date').textContent =
  new Date().toLocaleDateString('en-US', {{ month: 'long', day: 'numeric', year: 'numeric' }});
document.querySelectorAll('.bar').forEach(b => b.style.setProperty('--wf', parseFloat(b.style.getPropertyValue('--w')) / 100));
class SlidePresentation {{
  constructor() {{
    this.slides = document.querySelectorAll('.slide');
    this.bar = document.querySelector('.progress');
    this.nav = document.querySelector('.nav');
    this.cur = 0; this.done = new Set();
    this.slides.forEach((s, i) => {{
      const d = document.createElement('button');
      d.setAttribute('aria-label', 'Slide ' + (i + 1));
      d.addEventListener('click', () => s.scrollIntoView({{ behavior: 'smooth' }}));
      this.nav.appendChild(d);
    }});
    const io = new IntersectionObserver(es => es.forEach(e => {{
      if (!e.isIntersecting) return;
      e.target.classList.add('visible');
      this.cur = [...this.slides].indexOf(e.target);
      this.update(); this.count(e.target);
    }}), {{ threshold: 0.5 }});
    this.slides.forEach(s => io.observe(s));
    document.addEventListener('keydown', e => {{
      if (['ArrowDown', 'ArrowRight', ' ', 'PageDown'].includes(e.key)) {{ e.preventDefault(); this.go(this.cur + 1); }}
      if (['ArrowUp', 'ArrowLeft', 'PageUp'].includes(e.key)) {{ e.preventDefault(); this.go(this.cur - 1); }}
    }});
    this.update();
  }}
  go(i) {{ i = Math.max(0, Math.min(i, this.slides.length - 1)); this.slides[i].scrollIntoView({{ behavior: 'smooth' }}); }}
  update() {{
    this.bar.style.width = ((this.cur + 1) / this.slides.length * 100) + '%';
    [...this.nav.children].forEach((d, i) => {{
      d.style.background = i === this.cur ? 'var(--orange)' : 'transparent';
      d.style.borderColor = i === this.cur ? 'var(--orange)' : 'var(--grey)';
    }});
  }}
  count(slide) {{
    slide.querySelectorAll('.count-up').forEach(c => {{
      if (this.done.has(c)) return; this.done.add(c);
      const t = +c.dataset.target, st = performance.now();
      const step = now => {{ const p = Math.min((now - st) / 900, 1); c.textContent = Math.round((1 - Math.pow(1 - p, 3)) * t); if (p < 1) requestAnimationFrame(step); }};
      requestAnimationFrame(step);
    }});
  }}
}}
new SlidePresentation();
</script>
</body>
</html>
"""
html_path = f"{OUT}/{NAME}.html"
open(html_path, "w").write(html)
assert "—" not in html.split("<style>")[0] + html.split("</style>")[1].split("<script>")[0]
print("html ok:", html_path)
