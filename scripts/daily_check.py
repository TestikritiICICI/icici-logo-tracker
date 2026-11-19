"""Daily ICICI Bank logo check across every Festive Bonanza brand.

1. Reads the live Festive Bonanza page to get today's brands and offers.
2. Opens each brand's website (plus any extra pages in data/brands.json) in
   Google Chrome (Chromium on servers), scrolls it, and looks for the ICICI Bank logo, ICICI text
   mentions and other banks' names or logos.
3. Saves a screenshot per brand and writes data/daily/<YYYY-MM-DD>/results.json.

Run: python3 scripts/daily_check.py            (today, IST)
     python3 scripts/daily_check.py --only Amazon,Croma   (quick test, saved separately)
     python3 scripts/daily_check.py --only Apple --recheck (redo brands in today's results)
"""
import argparse
import asyncio
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from PIL import Image
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent.parent
BONANZA_URL = "https://www.icici.bank.in/campaigns/bonanza/index"
IST = timezone(timedelta(hours=5, minutes=30))
CONCURRENCY = 4
SCALE = 2                 # capture at 2x so OCR can read small logo text
MAX_CAPTURE = 5000        # CSS px of page height captured for OCR
OCR_BIN = ROOT / "scripts/bin/ocr"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36")

# Other banks: (display name, regex for page text, tokens for image names/alt text)
RIVALS = [
    ("HDFC", r"\bHDFC\b", ["hdfc"]),
    ("SBI", r"\bSBI\b", ["sbi", "sbicard"]),
    ("Axis", r"(?i)\baxis bank\b", ["axis", "axisbank"]),
    ("Kotak", r"(?i)\bkotak\b", ["kotak"]),
    ("HSBC", r"\bHSBC\b", ["hsbc"]),
    ("RBL", r"\bRBL\b", ["rbl", "rblbank"]),
    ("IDFC FIRST", r"\bIDFC\b", ["idfc", "idfcfirst"]),
    ("Yes Bank", r"(?i)\byes bank\b", ["yesbank"]),
    ("IndusInd", r"(?i)\bindusind\b", ["indusind"]),
    ("AU", r"\bAU (?:Small Finance )?Bank\b", ["aubank"]),
    ("Bank of Baroda", r"(?i)\bbank of baroda\b|\bBOBCARD\b|\bBOB Card\b", ["bankofbaroda", "bobcard"]),
    ("Federal", r"(?i)\bfederal bank\b", ["federal", "federalbank"]),
    ("PNB", r"\bPNB\b|(?i:punjab national bank)", ["pnb"]),
    ("DBS", r"\bDBS\b", ["dbs"]),
    ("Amex", r"(?i)\bamerican express\b|\bAmex\b", ["amex", "americanexpress"]),
    ("Standard Chartered", r"(?i)\bstandard chartered\b", ["standardchartered"]),
    ("OneCard", r"(?i)\bonecard\b", ["onecard"]),
    ("IDBI", r"\bIDBI\b", ["idbi"]),
    ("Citi", r"\bCiti(?:bank)?\b", ["citi", "citibank"]),
]

# ICICI group companies that are not ICICI Bank; their logos and names do not count
ICICI_GROUP_RE = re.compile(r"(?i)icici[\s_-]*(?:lombard|prudential|pru\b|securities|direct|sec\b)")

BLOCK_RE = re.compile(r"access denied|attention required|are you a robot|captcha|forbidden|"
                      r"request blocked|not available in your|pardon our interruption", re.I)

COLLECT_JS = r"""
() => {
  const out = [];
  const add = (el, kind, s) => { if (s && !s.startsWith('data:')) out.push({kind, s: s.slice(0, 400), i: out.length, el}); };
  document.querySelectorAll('img').forEach(im => {
    add(im, 'img', [im.currentSrc, im.getAttribute('src'), im.getAttribute('srcset'), im.getAttribute('data-src'),
                    im.alt, im.title].filter(Boolean).join(' '));
  });
  document.querySelectorAll('source[srcset]').forEach(s => add(s.parentElement, 'img', s.getAttribute('srcset')));
  document.querySelectorAll('[aria-label],[title]').forEach(el => {
    if (el.tagName !== 'IMG') add(el, 'label', (el.getAttribute('aria-label') || '') + ' ' + (el.getAttribute('title') || ''));
  });
  const all = document.querySelectorAll('body *');
  if (all.length < 8000) all.forEach(el => {
    const bg = getComputedStyle(el).backgroundImage;
    if (bg && bg !== 'none' && bg.includes('url(')) add(el, 'img', bg);
  });
  let marked = false;
  for (const o of out) {
    if (!marked && o.kind === 'img' && /icici/i.test(o.s)) {
      const r = o.el.getBoundingClientRect();
      if (r.width > 8 && r.height > 8) { marked = r.top + scrollY; }
    }
    delete o.el;
  }
  return {items: out, text: (document.body ? document.body.innerText : '').slice(0, 200000),
          title: document.title, marked: marked !== false, hit_y: marked === false ? null : marked};
}
"""

ICICI_TEXT_RECTS_JS = r"""
() => {
  const rects = [], w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  let n;
  while ((n = w.nextNode()) && rects.length < 500) {
    if (!/icici/i.test(n.nodeValue)) continue;
    const r = document.createRange(); r.selectNodeContents(n);
    for (const b of r.getClientRects()) rects.push([b.left + scrollX, b.top + scrollY, b.width, b.height]);
  }
  return rects;
}
"""

BONANZA_JS = r"""
() => [...document.querySelectorAll('.offerbox')].map(b => {
  const sec = b.closest('.tabs');
  return {
    logo: (b.querySelector('.offerlogo img') || b.querySelector('img') || {}).alt || '',
    section: sec ? sec.className.replace(/fullfloat|tabs|specialoffer/g, '').trim() : 'top',
    text: (b.querySelector('.offertext') || b).innerText.replace(/\s+/g, ' ').trim()
  };
})
"""


def norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def tokens(s):
    return set(t for t in re.split(r"[^a-z0-9]+", s.lower()) if t)


async def scroll_through(page):
    try:
        height = await page.evaluate("document.body ? document.body.scrollHeight : 0")
        y = 0
        while y < min(height, 14000):
            y += 900
            await page.evaluate(f"window.scrollTo(0, {y})")
            await page.wait_for_timeout(250)
        await page.wait_for_timeout(1500)
        await page.evaluate("window.scrollTo(0, 0)")
        await page.wait_for_timeout(500)
    except Exception:
        pass


def is_icici_bank(s):
    """True if s mentions ICICI other than as a non-bank group company (ICICI Lombard, Prudential, Securities)."""
    return bool(re.search(r"icici", re.sub(ICICI_GROUP_RE, " ", s)))


def classify_page(data):
    icici_logos, rivals = [], set()
    for it in data["items"]:
        low = it["s"].lower()
        if it["kind"] == "img" and is_icici_bank(low):
            icici_logos.append(it["s"][:160])
        toks = tokens(low)
        for name, _, keys in RIVALS:
            if any(k in toks or any(t.startswith(k) for t in toks if len(k) >= 5) for k in keys):
                rivals.add(name)
    text = data["text"]
    m = re.search(r".{0,70}\bICICI\b.{0,70}", re.sub(ICICI_GROUP_RE, " ", text), re.I)
    icici_text = re.sub(r"\s+", " ", m.group(0)).strip() if m else ""
    for name, rx, _ in RIVALS:
        if re.search(rx, text):
            rivals.add(name)
    return icici_logos, icici_text, rivals


async def run_ocr(png_path):
    """Read text inside the page capture. Uses macOS Vision on a Mac, Tesseract elsewhere (GitHub Actions)."""
    if sys.platform != "darwin":
        return await run_tesseract(png_path)
    proc = await asyncio.create_subprocess_exec(str(OCR_BIN), str(png_path),
                                                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL)
    out, _ = await asyncio.wait_for(proc.communicate(), timeout=120)
    rows = []
    for line in out.decode("utf-8", "ignore").splitlines():
        try:
            r = json.loads(line)
        except ValueError:
            continue
        rows.append({k: (v / SCALE if k != "t" else v) for k, v in r.items()})
    return rows


async def run_tesseract(png_path):
    """Tesseract word boxes grouped into lines, in the same shape as the Vision output."""
    proc = await asyncio.create_subprocess_exec("tesseract", str(png_path), "stdout", "--psm", "11", "tsv",
                                                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL)
    out, _ = await asyncio.wait_for(proc.communicate(), timeout=180)
    lines = {}
    for row in out.decode("utf-8", "ignore").splitlines()[1:]:
        f = row.split("\t")
        if len(f) < 12 or not f[11].strip():
            continue
        key = (f[2], f[3], f[4])  # block, paragraph, line
        x, y, w, h = (int(v) for v in f[6:10])
        ln = lines.setdefault(key, {"t": [], "x0": x, "y0": y, "x1": x + w, "y1": y + h})
        ln["t"].append(f[11])
        ln["x0"], ln["y0"] = min(ln["x0"], x), min(ln["y0"], y)
        ln["x1"], ln["y1"] = max(ln["x1"], x + w), max(ln["y1"], y + h)
    return [{"t": " ".join(ln["t"]), "x": ln["x0"] / SCALE, "y": ln["y0"] / SCALE,
             "w": (ln["x1"] - ln["x0"]) / SCALE, "h": (ln["y1"] - ln["y0"]) / SCALE} for ln in lines.values()]


def overlaps(box, rects, pad=12):
    x, y, w, h = box
    return any(x < rx + rw + pad and rx - pad < x + w and y < ry + rh + pad and ry - pad < y + h
               for rx, ry, rw, rh in rects)


def save_evidence(png_path, shot_path, focus_y):
    """Crop a 1366 x 900 view from the full-page capture, centred on focus_y (CSS px)."""
    with Image.open(png_path) as im:
        top = max(0, int((focus_y - 300) * SCALE)) if focus_y is not None else 0
        top = min(top, max(0, im.height - int(900 * SCALE)))
        crop = im.crop((0, top, im.width, min(im.height, top + int(900 * SCALE)))).convert("RGB")
        crop = crop.resize((crop.width // SCALE, crop.height // SCALE))
        crop.save(shot_path, "JPEG", quality=55)


async def check_url(context, url, shot_path):
    page = await context.new_page()
    res = {"url": url, "ok": False}
    png_path = shot_path.with_suffix(".full.png")
    try:
        resp = await page.goto(url, wait_until="domcontentloaded", timeout=45000)
        await page.wait_for_timeout(3500)
        await scroll_through(page)
        try:
            await page.wait_for_load_state("networkidle", timeout=8000)
        except Exception:
            pass
        await page.wait_for_timeout(1000)
        data = await page.evaluate(COLLECT_JS)
        res["final_url"] = page.url
        res["title"] = data["title"][:120]
        status = resp.status if resp else 0
        page_h = await page.evaluate("document.documentElement.scrollHeight")
        await page.screenshot(path=str(png_path), full_page=True, timeout=30000,
                              clip={"x": 0, "y": 0, "width": 1366, "height": min(max(page_h, 900), MAX_CAPTURE)})
        if status >= 400 or len(data["text"]) < 150 or BLOCK_RE.search(data["title"] + " " + data["text"][:600]):
            res["error"] = f"Page blocked or did not load (HTTP {status})"
            save_evidence(png_path, shot_path, None)
        else:
            res["ok"] = True
            logos, icici_text, rivals = classify_page(data)
            ocr = await run_ocr(png_path)
            text_rects = await page.evaluate(ICICI_TEXT_RECTS_JS)
            # ICICI read from pixels where the page has no ICICI text = ICICI inside an image (logo or banner)
            image_hits = [r for r in ocr if is_icici_bank(r["t"].lower())
                          and not overlaps((r["x"], r["y"], r["w"], r["h"]), text_rects)]
            logos += [f"In image (read by OCR): {r['t']}" for r in image_hits]
            ocr_text = " ".join(r["t"] for r in ocr)
            for name, rx, _ in RIVALS:
                if re.search(rx, ocr_text):
                    rivals.add(name)
            res["icici_logos"], res["icici_text"], res["rivals"] = logos, icici_text, sorted(rivals)
            focus = image_hits[0]["y"] if image_hits else (data.get("hit_y") if data.get("marked") else None)
            if focus is None and icici_text and text_rects:
                focus = text_rects[0][1]
            save_evidence(png_path, shot_path, focus)
        res["screenshot"] = shot_path.name
    except Exception as ex:
        res["error"] = f"Could not open page: {type(ex).__name__}: {str(ex).splitlines()[0][:120]}"
    finally:
        await page.close()
        png_path.unlink(missing_ok=True)
    return res


def overall_status(pages):
    good = [p for p in pages if p.get("ok")]
    if not good:
        return "error"
    if any(p["icici_logos"] for p in good):
        return "logo"
    if any(p["icici_text"] for p in good):
        return "text"
    if any(p["rivals"] for p in good):
        return "rival"
    return "none"


async def check_brand(context, sem, brand, shots_dir):
    async with sem:
        urls = [brand["url"]] + brand.get("extra_urls", [])
        pages = []
        for i, u in enumerate(urls):
            slug = norm(brand["name"]) + (f"-{i}" if i else "")
            pages.append(await check_url(context, u, shots_dir / f"{slug}.jpg"))
        status = overall_status(pages)
        best = next((p for p in pages if p.get("icici_logos")), None) or next((p for p in pages if p.get("ok")), pages[0])
        print(f"  {brand['name']:<24} {status}", flush=True)
        return {
            "status": status,
            "url": brand["url"],
            "final_url": best.get("final_url"),
            "page_title": best.get("title"),
            "icici_logo": (best.get("icici_logos") or [""])[0],
            "icici_logo_count": sum(len(p.get("icici_logos", [])) for p in pages),
            "icici_text": next((p["icici_text"] for p in pages if p.get("icici_text")), ""),
            "rivals": sorted(set(r for p in pages for r in p.get("rivals", []))),
            "screenshot": best.get("screenshot"),
            "error": "; ".join(p["error"] for p in pages if p.get("error")),
            "pages_checked": [p["url"] for p in pages],
        }


async def read_bonanza(context):
    page = await context.new_page()
    try:
        await page.goto(BONANZA_URL, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(4000)
        await scroll_through(page)
        return await page.evaluate(BONANZA_JS)
    finally:
        await page.close()


async def main(only=None, recheck=False):
    now = datetime.now(IST)
    day = now.strftime("%Y-%m-%d")
    out_dir = ROOT / "data/daily" / day
    shots_dir = out_dir / "shots"
    shots_dir.mkdir(parents=True, exist_ok=True)
    cfg = json.loads((ROOT / "data/brands.json").read_text())
    by_alias = {}
    for b in cfg["brands"]:
        for a in b["aliases"] + [b["name"]]:
            by_alias[norm(a)] = b
    ignore = {norm(x) for x in cfg["ignore"]}

    async with async_playwright() as pw:
        # Google Chrome on a Mac; Playwright's bundled Chromium on servers
        browser = await pw.chromium.launch(channel="chrome" if sys.platform == "darwin" else None, headless=True,
                                           args=["--disable-blink-features=AutomationControlled"])
        context = await browser.new_context(user_agent=UA, locale="en-IN", timezone_id="Asia/Kolkata",
                                            viewport={"width": 1366, "height": 900},
                                            device_scale_factor=SCALE)
        await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        print("Reading Festive Bonanza page...", flush=True)
        try:
            offers = await read_bonanza(context)
            bonanza_ok = len(offers) > 20
        except Exception as ex:
            print(f"  Bonanza page failed: {ex}", flush=True)
            offers, bonanza_ok = [], False

        live, new_brands = {}, []
        for o in offers:
            key = norm(o["logo"])
            if not key or key in ignore:
                continue
            b = by_alias.get(key)
            if not b:
                if o["logo"].strip() not in new_brands:
                    new_brands.append(o["logo"].strip())
                continue
            entry = live.setdefault(b["name"], {"brand": b, "offers": []})
            if o["text"] not in entry["offers"]:
                entry["offers"].append(o["text"])
        if not bonanza_ok:
            live = {b["name"]: {"brand": b, "offers": []} for b in cfg["brands"]}
        if only:
            live = {k: v for k, v in live.items() if k.lower() in only}

        print(f"Checking {len(live)} brands...", flush=True)
        sem = asyncio.Semaphore(CONCURRENCY)
        names = sorted(live)
        todo = [n for n in names if live[n]["brand"].get("url")]
        results = await asyncio.gather(*(check_brand(context, sem, live[n]["brand"], shots_dir) for n in todo))
        checked = dict(zip(todo, results))
        # Pages often fail only because several load at once; retry those one at a time.
        retry = [n for n in todo if checked[n]["status"] == "error" and "blocked" not in checked[n]["error"]]
        if retry:
            print(f"Retrying {len(retry)} brands one at a time...", flush=True)
            one = asyncio.Semaphore(1)
            for n in retry:
                checked[n] = await check_brand(context, one, live[n]["brand"], shots_dir)
        await browser.close()

    brands = []
    for n in names:
        b = live[n]["brand"]
        r = checked.get(n) or {"status": "nourl", "url": None, "rivals": [], "error": "Website not set in data/brands.json"}
        brands.append({"name": n, "category": b["category"], "offers": live[n]["offers"], **r})
    for nb in new_brands:
        brands.append({"name": nb, "category": "New on Bonanza page", "offers": [o["text"] for o in offers if o["logo"].strip() == nb],
                       "status": "nourl", "url": None, "rivals": [], "error": "New brand: add its website to data/brands.json"})

    counts = {}
    for b in brands:
        counts[b["status"]] = counts.get(b["status"], 0) + 1
    result = {
        "date": day,
        "checked_at": now.strftime("%B %-d, %Y, %-I:%M %p IST"),
        "bonanza_page_read": bonanza_ok,
        "offers_on_bonanza": len(offers),
        "counts": counts,
        "new_brands": new_brands,
        "brands": brands,
    }
    out_path = out_dir / "results.json"
    if only and recheck and out_path.exists():
        # Merge the rechecked brands into today's full results
        full = json.loads(out_path.read_text())
        fresh = {b["name"]: b for b in brands}
        full["brands"] = [fresh.get(b["name"], b) for b in full["brands"]]
        full["counts"] = {}
        for b in full["brands"]:
            full["counts"][b["status"]] = full["counts"].get(b["status"], 0) + 1
        result, counts = full, full["counts"]
    elif only:
        out_path = out_dir / "results-test.json"
    out_path.write_text(json.dumps(result, indent=1, ensure_ascii=False))
    print(f"Saved {out_path.relative_to(ROOT)}: {counts}", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="Comma-separated brand names for a quick test run")
    ap.add_argument("--recheck", action="store_true",
                    help="With --only: merge the rechecked brands into today's results.json")
    args = ap.parse_args()
    only = {s.strip().lower() for s in args.only.split(",")} if args.only else None
    asyncio.run(main(only, args.recheck))
    sys.exit(0)
