"""Build the static website for the ICICI Bank logo visibility audit.

index.html is the daily tracker (calendar of daily checks from data/daily/).
audit.html is the original 20-brand baseline audit with the deck and evidence.
Writes a self-contained static site to site/ that can be deployed to Netlify as is.
Run: python3 scripts/build_site.py
"""
import csv
import html
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
SKILL_ASSETS = ROOT / "assets"  # ICICI Bank logo and i-Man mark (from the presentation-builder brand kit)
AUDIT_DATE = "October 28, 2026"

STATUS = {
    "Logo shown": ("logo", "ICICI logo shown"),
    "Text only": ("text", "Named in text only"),
    "Rivals shown": ("rival", "Rival banks shown"),
    "No bank shown": ("none", "No bank shown"),
}
ORDER = list(STATUS)

e = html.escape


def md_inline(s):
    s = e(s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(https?://[^\s<]+)", r'<a href="\1" rel="noopener">\1</a>', s)
    return s


def md_to_html(text):
    out, in_list = [], False
    for line in text.splitlines():
        if line.startswith("- "):
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{md_inline(line[2:])}</li>")
            continue
        if in_list:
            out.append("</ul>")
            in_list = False
        if line.startswith("### "):
            out.append(f"<h4>{md_inline(line[4:])}</h4>")
        elif line.startswith("## "):
            out.append(f"<h3>{md_inline(line[3:])}</h3>")
        elif line.startswith("# "):
            continue
        elif line.strip():
            out.append(f"<p>{md_inline(line)}</p>")
    if in_list:
        out.append("</ul>")
    return "\n".join(out)


def evidence_files(cell):
    """Expand the CSV evidence cell (may hold globs) into existing file names."""
    names = []
    for part in [p.strip() for p in cell.split(";") if p.strip()]:
        names += sorted(p.name for p in (ROOT / "screenshots/evidence").glob(part))
    return names


def build():
    if SITE.exists():
        shutil.rmtree(SITE)
    for d in ("assets", "evidence", "slides", "files"):
        (SITE / d).mkdir(parents=True)

    shutil.copy(SKILL_ASSETS / "icici-logo.png", SITE / "assets/icici-logo.png")
    shutil.copy(SKILL_ASSETS / "icici-iman.png", SITE / "assets/icici-iman.png")
    for p in (ROOT / "screenshots/evidence").iterdir():
        if p.suffix in (".jpg", ".png"):
            shutil.copy(p, SITE / "evidence" / p.name)
    slides = sorted((ROOT / "screenshots/deck-preview").glob("slide*.png"),
                    key=lambda p: int(re.sub(r"\D", "", p.stem)))
    for p in slides:
        shutil.copy(p, SITE / "slides" / p.name)
    for p in (ROOT / "deliverables").iterdir():
        if p.suffix in (".pptx", ".pdf"):
            shutil.copy(p, SITE / "files" / p.name)
    shutil.copy(ROOT / "data/audit-findings.csv", SITE / "files/audit-findings.csv")
    shutil.copy(ROOT / "deliverables/icici-logo-visibility-audit.html", SITE / "deck.html")

    with open(ROOT / "data/audit-findings.csv", newline="") as f:
        rows = list(csv.DictReader(f))
    rows.sort(key=lambda r: ORDER.index(r["overall_status"]))
    counts = {k: sum(r["overall_status"] == k for r in rows) for k in ORDER}

    stats = "".join(
        f'<div class="stat {STATUS[k][0]}"><span class="num">{counts[k]}</span>'
        f'<span class="lbl">{STATUS[k][1]}</span></div>' for k in ORDER)

    filters = '<button class="chip on" data-f="all">All 20</button>' + "".join(
        f'<button class="chip" data-f="{STATUS[k][0]}">{STATUS[k][1]} ({counts[k]})</button>'
        for k in ORDER)

    cards, gallery = [], []
    for r in rows:
        cls, label = STATUS[r["overall_status"]]
        ev = evidence_files(r["evidence"])
        thumbs = "".join(
            f'<a class="thumb" href="evidence/{e(n)}" data-cap="{e(r["brand"])}: {e(n)}">'
            f'<img src="evidence/{e(n)}" alt="{e(r["brand"])} evidence" loading="lazy"></a>'
            for n in ev)
        for n in ev:
            gallery.append(
                f'<figure class="shot" data-f="{cls}"><a href="evidence/{e(n)}" data-cap="{e(r["brand"])}: {e(n)}">'
                f'<img src="evidence/{e(n)}" alt="{e(r["brand"])} evidence" loading="lazy"></a>'
                f'<figcaption><strong>{e(r["brand"])}</strong> {e(n)}</figcaption></figure>')
        product = e(r["product_page"])
        if r["product_page_checked"]:
            product += f' <span class="muted">({e(r["product_page_checked"])})</span>'
        rivals = e(r["other_banks_seen"]) or '<span class="muted">None seen</span>'
        cards.append(f"""
<article class="brand" data-f="{cls}">
  <header><h3>{e(r["brand"])}</h3><span class="tag {cls}">{label}</span></header>
  <p class="cat">{e(r["category"])} · checked {e(r["last_checked"])}</p>
  <dl>
    <dt>Homepage or offers page</dt><dd>{e(r["homepage_or_offers_page"])}</dd>
    <dt>Product page</dt><dd>{product}</dd>
    <dt>Other banks seen</dt><dd>{rivals}</dd>
  </dl>
  {f'<div class="thumbs">{thumbs}</div>' if thumbs else '<p class="muted small">Text scan only, no screenshot</p>'}
</article>""")

    slide_imgs = "".join(
        f'<a href="slides/{p.name}" data-cap="Slide {i}"><img src="slides/{p.name}" alt="Slide {i}" loading="lazy"></a>'
        for i, p in enumerate(slides, 1))

    log_html = md_to_html((ROOT / "activity-log.md").read_text())

    page = TEMPLATE.format(
        date=AUDIT_DATE, stats=stats, filters=filters, cards="".join(cards),
        gallery="".join(gallery), slides=slide_imgs, log=log_html,
        logo_count=counts["Logo shown"], total=len(rows),
        n_shots=len(gallery))
    (SITE / "audit.html").write_text(page)
    build_tracker()
    (SITE / "netlify.toml").write_text(NETLIFY_TOML)
    (SITE / "robots.txt").write_text("User-agent: *\nDisallow: /\n")
    print(f"Built {SITE} ({len(rows)} brands, {len(gallery)} screenshots, {len(slides)} slides)")


NETLIFY_TOML = """[build]
  publish = "."

[[headers]]
  for = "/*"
  [headers.values]
    X-Robots-Tag = "noindex, nofollow"
    X-Content-Type-Options = "nosniff"
    Referrer-Policy = "no-referrer"
"""

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="noindex, nofollow">
<title>ICICI Logo Visibility Audit</title>
<link rel="icon" href="assets/icici-iman.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Mulish:wght@500;600;700;800;900&display=swap">
<style>
:root {{
  --orange:#E77817; --maroon:#97291E; --navy:#053C6D; --beige:#D1CFBB;
  --gold:#FDB92A; --grey:#525252; --bg:#FFFFFF; --soft:#F6F5F0; --line:#E4E2D6;
}}
* {{ box-sizing:border-box; }}
html {{ scroll-behavior:smooth; }}
body {{ margin:0; font-family:'Mulish',Arial,sans-serif; font-weight:600; color:var(--grey); background:var(--bg); line-height:1.5; }}
a {{ color:var(--navy); }}
.wrap {{ max-width:1180px; margin:0 auto; padding:0 16px; }}
nav.top {{ position:sticky; top:0; z-index:10; background:#fff; border-bottom:1px solid var(--line); }}
nav.top .wrap {{ display:flex; align-items:center; gap:24px; height:64px; }}
nav.top img {{ height:34px; }}
nav.top ul {{ display:flex; gap:20px; list-style:none; margin:0 0 0 auto; padding:0; overflow-x:auto; }}
nav.top a {{ text-decoration:none; font-weight:700; white-space:nowrap; }}
nav.top a:hover {{ color:var(--orange); }}
.hero {{ background:var(--orange); color:#fff; padding:56px 0 48px; }}
.hero h1 {{ font-size:clamp(2rem,5vw,3.25rem); font-weight:900; margin:0 0 8px; line-height:1.15; }}
.hero p {{ font-size:clamp(1.05rem,2.2vw,1.35rem); margin:0; max-width:760px; }}
.hero .date {{ margin-top:16px; font-weight:700; opacity:.9; }}
.stats {{ display:grid; grid-template-columns:repeat(4,1fr); gap:16px; margin-top:-28px; }}
.stat {{ background:#fff; border-radius:12px; padding:20px; box-shadow:0 4px 18px rgba(0,0,0,.08); border-top:6px solid; }}
.stat .num {{ display:block; font-size:clamp(2.2rem,5vw,3.25rem); font-weight:900; line-height:1; }}
.stat .lbl {{ font-weight:700; }}
.stat.logo {{ border-color:var(--orange); }} .stat.logo .num {{ color:var(--orange); }}
.stat.text {{ border-color:var(--gold); }} .stat.text .num {{ color:#B07A0A; }}
.stat.rival {{ border-color:var(--maroon); }} .stat.rival .num {{ color:var(--maroon); }}
.stat.none {{ border-color:var(--beige); }} .stat.none .num {{ color:var(--navy); }}
section {{ padding:56px 0 8px; scroll-margin-top:64px; }}
h2 {{ color:var(--maroon); font-weight:800; font-size:clamp(1.6rem,3.5vw,2.2rem); margin:0 0 4px; }}
.sub {{ color:var(--navy); font-weight:800; font-size:1.15rem; margin:0 0 24px; }}
.chips {{ display:flex; flex-wrap:wrap; gap:8px; margin-bottom:20px; }}
.chip {{ font:inherit; font-weight:700; border:2px solid var(--navy); color:var(--navy); background:#fff; border-radius:999px; padding:6px 14px; cursor:pointer; }}
.chip.on {{ background:var(--navy); color:#fff; }}
.grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(340px,1fr)); gap:16px; }}
.brand {{ border:1px solid var(--line); border-radius:12px; padding:18px; background:#fff; }}
.brand header {{ display:flex; justify-content:space-between; align-items:center; gap:8px; }}
.brand h3 {{ margin:0; color:var(--navy); font-weight:800; font-size:1.25rem; }}
.cat {{ margin:2px 0 10px; font-size:.9rem; }}
.tag {{ font-size:.8rem; font-weight:800; padding:4px 10px; border-radius:999px; white-space:nowrap; }}
.tag.logo {{ background:var(--orange); color:#fff; }}
.tag.text {{ background:var(--gold); color:var(--navy); }}
.tag.rival {{ background:var(--maroon); color:#fff; }}
.tag.none {{ background:var(--beige); color:var(--navy); }}
dl {{ margin:0; }}
dt {{ font-weight:800; color:var(--navy); font-size:.85rem; margin-top:8px; }}
dd {{ margin:0; }}
.muted {{ color:#7a7a7a; font-weight:500; }}
.small {{ font-size:.9rem; margin:12px 0 0; }}
.thumbs {{ display:flex; gap:8px; margin-top:12px; flex-wrap:wrap; }}
.thumb img {{ width:96px; height:64px; object-fit:cover; object-position:top; border-radius:6px; border:1px solid var(--line); }}
.gallery {{ columns:3 300px; column-gap:16px; }}
.shot {{ break-inside:avoid; margin:0 0 16px; background:var(--soft); border-radius:10px; padding:8px; }}
.shot img {{ width:100%; display:block; border-radius:6px; }}
.shot figcaption {{ font-size:.85rem; padding:6px 2px 0; word-break:break-all; }}
.shot strong {{ color:var(--navy); margin-right:4px; }}
.deck-actions {{ display:flex; flex-wrap:wrap; gap:12px; margin-bottom:20px; }}
.btn {{ display:inline-block; background:var(--orange); color:#fff; text-decoration:none; font-weight:800; padding:12px 20px; border-radius:8px; }}
.btn.alt {{ background:#fff; color:var(--navy); border:2px solid var(--navy); }}
.slides {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(260px,1fr)); gap:12px; }}
.slides img {{ width:100%; display:block; border-radius:8px; border:1px solid var(--line); }}
.method {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; }}
.panel {{ background:var(--soft); border-radius:12px; padding:20px 24px; }}
.panel h3 {{ margin-top:0; color:var(--navy); font-weight:800; }}
.log {{ background:var(--soft); border-radius:12px; padding:8px 24px 16px; }}
.log h3 {{ color:var(--maroon); font-weight:800; margin:20px 0 4px; }}
.log h4 {{ color:var(--navy); font-weight:800; margin:16px 0 4px; }}
.log code {{ background:#fff; padding:1px 5px; border-radius:4px; font-size:.9em; }}
.log a {{ word-break:break-all; }}
footer {{ margin-top:56px; border-top:1px solid var(--line); padding:24px 0 40px; }}
footer .wrap {{ display:flex; align-items:center; gap:12px; }}
footer img {{ height:40px; }}
#lb {{ position:fixed; inset:0; background:rgba(0,0,0,.85); display:none; align-items:center; justify-content:center; flex-direction:column; z-index:50; padding:16px; }}
#lb.open {{ display:flex; }}
#lb img {{ max-width:100%; max-height:85vh; border-radius:6px; background:#fff; }}
#lb p {{ color:#fff; margin:10px 0 0; text-align:center; word-break:break-all; }}
#lb button {{ position:absolute; top:12px; right:16px; font:inherit; font-size:2rem; background:none; border:0; color:#fff; cursor:pointer; }}
[hidden] {{ display:none !important; }}
@media (max-width:760px) {{
  .stats {{ grid-template-columns:repeat(2,1fr); }}
  .method {{ grid-template-columns:1fr; }}
  .grid {{ grid-template-columns:1fr; }}
  nav.top ul {{ gap:14px; font-size:.9rem; }}
  nav.top img {{ height:26px; }}
}}
</style>
</head>
<body>
<nav class="top"><div class="wrap">
  <img src="assets/icici-logo.png" alt="ICICI Bank">
  <ul>
    <li><a href="index.html">Daily tracker</a></li>
    <li><a href="#brands">Brands</a></li>
    <li><a href="#evidence">Evidence</a></li>
    <li><a href="#deck">Deck</a></li>
    <li><a href="#method">Method</a></li>
    <li><a href="#log">Activity log</a></li>
  </ul>
</div></nav>

<header class="hero"><div class="wrap">
  <h1>Only {logo_count} of {total} brands show our logo</h1>
  <p>ICICI Bank logo visibility audit across the top {total} Festive Bonanza partner brands with live credit card offers.</p>
  <p class="date">Last checked {date}</p>
</div></header>

<div class="wrap"><div class="stats">{stats}</div></div>

<main class="wrap">
<section id="brands">
  <h2>All {total} brands at a glance</h2>
  <p class="sub">Homepage, offers page and one product page checked for each brand</p>
  <div class="chips" id="filters">{filters}</div>
  <div class="grid">{cards}</div>
</section>

<section id="evidence">
  <h2>Evidence</h2>
  <p class="sub">{n_shots} screenshots from brand websites. Click any image to enlarge.</p>
  <div class="gallery">{gallery}</div>
</section>

<section id="deck">
  <h2>Presentation</h2>
  <p class="sub">Nine-slide deck for the alliances team</p>
  <div class="deck-actions">
    <a class="btn" href="deck.html" target="_blank" rel="noopener">Open the deck</a>
    <a class="btn alt" href="files/icici-logo-visibility-audit.pptx" download>Download PPTX</a>
    <a class="btn alt" href="files/icici-logo-visibility-audit.pdf" target="_blank" rel="noopener">Open PDF</a>
    <a class="btn alt" href="files/audit-findings.csv" download>Download findings CSV</a>
  </div>
  <div class="slides">{slides}</div>
</section>

<section id="method">
  <h2>How the audit was done</h2>
  <p class="sub">What was checked, and what was not</p>
  <div class="method">
    <div class="panel">
      <h3>Covered</h3>
      <ul>
        <li>Top 20 partner brands from the ICICI Bank Festive Bonanza page</li>
        <li>Each brand's homepage or offers page on desktop web</li>
        <li>One product, buy, restaurant or hotel page per brand</li>
        <li>Page-code scans for "icici" in image names, alt text and page text, plus screenshots</li>
      </ul>
    </div>
    <div class="panel">
      <h3>Not covered</h3>
      <ul>
        <li>Checkout and payment pages, which need a sign-in or a booking</li>
        <li>Brand mobile apps</li>
        <li>Tata CLiQ and Reliance Digital product pages have text scans only, no screenshots</li>
      </ul>
    </div>
  </div>
</section>

<section id="log">
  <h2>Activity log</h2>
  <p class="sub">Dated record of every step on this project</p>
  <div class="log">{log}</div>
</section>
</main>

<footer><div class="wrap">
  <img src="assets/icici-iman.png" alt="">
  <span>ICICI Bank logo visibility audit · Last checked {date}</span>
</div></footer>

<div id="lb" role="dialog" aria-modal="true" aria-label="Image preview">
  <button type="button" aria-label="Close">&times;</button>
  <img alt=""><p></p>
</div>

<script>
const chips = document.querySelectorAll('#filters .chip');
chips.forEach(c => c.addEventListener('click', () => {{
  chips.forEach(x => x.classList.toggle('on', x === c));
  const f = c.dataset.f;
  document.querySelectorAll('.brand, .shot').forEach(el => {{
    el.hidden = f !== 'all' && el.dataset.f !== f;
  }});
}}));
const lb = document.getElementById('lb');
const lbImg = lb.querySelector('img'), lbCap = lb.querySelector('p');
document.addEventListener('click', ev => {{
  const a = ev.target.closest('a[data-cap]');
  if (!a) return;
  ev.preventDefault();
  lbImg.src = a.getAttribute('href'); lbCap.textContent = a.dataset.cap;
  lb.classList.add('open');
}});
lb.addEventListener('click', ev => {{ if (ev.target !== lbImg) lb.classList.remove('open'); }});
document.addEventListener('keydown', ev => {{ if (ev.key === 'Escape') lb.classList.remove('open'); }});
</script>
</body>
</html>
"""

from tracker_page import build_tracker  # noqa: E402

def make_zip():
    """Zip site/ for drag-and-drop upload at https://app.netlify.com/drop."""
    out = ROOT / "deliverables/icici-logo-tracker-site.zip"
    out.unlink(missing_ok=True)
    shutil.make_archive(str(out.with_suffix("")), "zip", SITE)
    print(f"Zip: {out.relative_to(ROOT)} ({out.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    build()
    make_zip()
