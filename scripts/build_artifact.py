"""Build the claude.ai Artifact version of the daily tracker website.

Reads the built site/ folder (run scripts/build_site.py first) and writes artifact/:
  index.html        the tracker page (document wrapper tags removed; the Artifact host adds them)
  audit.html, deck.html, assets/, evidence/, slides/, files/   copied as-is
  data/days.json, data/days/<date>.json
  shots/<latest date>/   screenshots for the most recent check only (older days keep their
                         results but show no screenshot, to stay within Artifact file limits)

It also writes data/artifact-publish-map.json: the `files` map for the Artifact publish call
(published path -> path under artifact/, or null for a file the last publish had that is now
gone). After a successful publish, run:  python3 scripts/build_artifact.py --mark-published
"""
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
OUT = ROOT / "artifact"
MAP = ROOT / "data/artifact-publish-map.json"
PENDING = ROOT / "data/artifact-manifest-pending.json"
PUBLISHED = ROOT / "data/artifact-manifest.json"


def strip_wrapper(html):
    html = re.sub(r"<!DOCTYPE html>\s*", "", html, flags=re.I)
    html = re.sub(r"</?html[^>]*>\s*", "", html, flags=re.I)
    html = re.sub(r"</?head>\s*", "", html, flags=re.I)
    html = re.sub(r"</?body[^>]*>\s*", "", html, flags=re.I)
    html = re.sub(r'<meta charset="[^"]*">\s*', "", html, flags=re.I)
    html = re.sub(r'<meta name="viewport"[^>]*>\s*', "", html, flags=re.I)
    return html


def build():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    (OUT / "index.html").write_text(strip_wrapper((SITE / "index.html").read_text()))
    for f in ("audit.html", "deck.html"):
        if (SITE / f).exists():
            shutil.copy(SITE / f, OUT / f)
    for d in ("assets", "evidence", "slides", "files"):
        if (SITE / d).exists():
            shutil.copytree(SITE / d, OUT / d)

    index = json.loads((SITE / "data/days.json").read_text())
    latest = index[-1]["date"]
    (OUT / "data/days").mkdir(parents=True)
    shutil.copy(SITE / "data/days.json", OUT / "data/days.json")
    for day in index:
        d = json.loads((SITE / f"data/days/{day['date']}.json").read_text())
        if day["date"] != latest:
            for b in d.get("brands", []):
                b["screenshot"] = None
        (OUT / f"data/days/{day['date']}.json").write_text(json.dumps(d))
    if (SITE / "shots" / latest).exists():
        shutil.copytree(SITE / "shots" / latest, OUT / "shots" / latest)

    paths = sorted(str(p.relative_to(OUT)) for p in OUT.rglob("*") if p.is_file() and p.name != "index.html"
                   and not p.name.startswith("."))
    previous = json.loads(PUBLISHED.read_text()) if PUBLISHED.exists() else []
    files_map = {p: p for p in paths}
    for p in previous:
        if p not in files_map:
            files_map[p] = None
    MAP.write_text(json.dumps(files_map, indent=1))
    PENDING.write_text(json.dumps(paths))
    size = sum(p.stat().st_size for p in OUT.rglob("*") if p.is_file())
    removed = sum(1 for v in files_map.values() if v is None)
    print(f"Built {OUT}: {len(paths) + 1} files, {size / 1e6:.1f} MB, latest day {latest}, "
          f"{removed} old files to remove. Publish map: {MAP.relative_to(ROOT)}")


if __name__ == "__main__":
    if "--mark-published" in sys.argv:
        PENDING.replace(PUBLISHED)
        print("Recorded the published file list.")
    else:
        build()
