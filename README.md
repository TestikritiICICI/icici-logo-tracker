# ICICI Bank logo visibility audit

Checks whether partner brands with live ICICI Bank Festive Bonanza credit card offers show the ICICI Bank logo on their own websites. Runs as a daily tracker across every Bonanza brand, with a calendar website.

**Live site:** https://icici-logo-tracker.onrender.com · updated every day from 10:00 AM IST by GitHub Actions (backup start times until 1:07 PM, because GitHub often starts late) (`.github/workflows/daily-check.yml`), hosted on Render from the `site` branch.

When the Mac is on, `scripts/mac_fill_gaps.sh` (scheduled for about 10:30 AM IST) checks every brand again from India and replaces GitHub's results for the day: some Indian sites block GitHub's servers, and the Mac's text recognition reads logos inside banners more reliably.

| Folder / file | What's in it |
|---|---|
| `activity-log.md` | Dated log of every activity on this project |
| `deliverables/` | Final outputs: deck as HTML, PPTX and PDF |
| `data/audit-findings.csv` | Baseline 20-brand findings (October 28, 2026) |
| `data/brands.json` | Every Bonanza brand and its website, used by the daily check |
| `data/daily/<date>/` | Each day's results (`results.json`) and screenshots |
| `screenshots/evidence/` | Screenshots from brand websites backing the findings |
| `screenshots/deck-preview/` | Rendered slides from the PPTX |
| `scripts/` | `daily_check.py` runs the daily check; `mac_fill_gaps.sh` runs the Mac follow-up check and publishes; `build_site.py` builds the website and zip; `build_deck.py` regenerates the deck; `ocr.swift` reads text inside images |
| `downloads/` | Any files downloaded for this project |
| `site/` | Website built by `scripts/build_site.py` (daily tracker calendar plus baseline audit); published to the `site` branch |
| `.github/workflows/` | Daily run on GitHub Actions from 10:00 AM IST (backup start times to 1:07 PM) |
| `render.yaml` | Render static site settings (serves the `site` branch) |
| `assets/` | ICICI Bank logo and i-Man mark used by the website |
