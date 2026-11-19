# ICICI Bank logo visibility audit

Checks whether partner brands with live ICICI Bank Festive Bonanza credit card offers show the ICICI Bank logo on their own websites. Runs as a daily tracker across every Bonanza brand, with a calendar website.

| Folder / file | What's in it |
|---|---|
| `activity-log.md` | Dated log of every activity on this project |
| `deliverables/` | Final outputs: deck as HTML, PPTX and PDF |
| `data/audit-findings.csv` | Baseline 20-brand findings (October 28, 2026) |
| `data/brands.json` | Every Bonanza brand and its website, used by the daily check |
| `data/daily/<date>/` | Each day's results (`results.json`) and screenshots |
| `screenshots/evidence/` | Screenshots from brand websites backing the findings |
| `screenshots/deck-preview/` | Rendered slides from the PPTX |
| `scripts/` | `daily_check.py` runs the daily check; `build_site.py` builds the website and zip; `build_deck.py` regenerates the deck; `ocr.swift` reads text inside images |
| `downloads/` | Any files downloaded for this project |
| `site/` | Website built by `scripts/build_site.py` (daily tracker calendar plus baseline audit) |
