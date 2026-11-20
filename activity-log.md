# Activity log: ICICI Bank logo visibility audit

Dated record of every activity on this project. Newest entries at the bottom.

## October 27, 2026

### 1. Brand list from Festive Bonanza
- Source: https://www.icici.bank.in/campaigns/bonanza/index
- The page has no ranking, so the top 20 = the 5 hero-carousel brands (Amazon, Google Pixel, Reliance Digital, MakeMyTrip, Apple) plus the most prominent brands with live credit card offers across electronics, travel, fashion and food.

### 2. Website audit (homepage and offer pages)
- Checked all 20 brand websites for the ICICI Bank logo using page-code scans (image names, alt text, page text) plus screenshots.
- Result: 4 logo shown (Amazon, Vijay Sales, Cleartrip, MakeMyTrip), 1 text only (Apple), 4 rival banks shown without ICICI (Tata CLiQ, Reliance Digital, Ajio, Goibibo), 11 no bank logos at all.
- Data: `data/audit-findings.csv`. Evidence: `screenshots/evidence/`.
- Limits: desktop web only; no apps, no checkout. Logos baked into banner images were confirmed visually only where screenshotted.

### 3. Product page check (started, paused)
- Reliance Digital product page (Oppo K13 Turbo Pro): Axis, Yes, Federal, PNB, IDFC FIRST, IDBI logos; no ICICI.
- 14 brands still to check. Checkout pages need sign-in, so they are out of scope unless a test account is provided.

### 4. Presentation (presentation-builder skill)
- Audience: alliances team (peers / team leads). Goal: change behavior. Framework: Situation, Complication, Resolution. No agenda slide.
- 9 slides: title, 4 of 20 metric, where we show up, rival banks, silent brands, full table, impact, three asks, thank you.
- Outputs: `deliverables/icici-logo-visibility-audit.html`, `.pptx`, `.pdf`. Rebuild with `python3 scripts/build_deck.py`.
- Verified: HTML in browser; PPTX exported through PowerPoint to PDF and reviewed slide by slide (`screenshots/deck-preview/`).

### 5. Project folder created
- All work for this project is saved in `/Users/user3/Desktop/Ulkrisht/icici-logo-audit/`. Downloaded files go in `downloads/`.

## October 28, 2026

### 6. Product page check (completed)
- Checked one product page (or buy / restaurant / hotel page) for each of the 15 brands that showed no ICICI logo on the homepage. Product used for each is in `data/audit-findings.csv`.
- ICICI logo found: Croma (first card in Super Savings), OnePlus (inside the Instant Discount pop-up, one click deep).
- ICICI in text only: Google Store (Pixel 11 page), Xiaomi (first offer on buy page).
- Other banks shown, no ICICI: Samsung (Axis co-brand card), Sony (Yes, Kotak, BOB), HP (SBI, Axis, HDFC, Kotak, Yes, Amex), Tata CLiQ (DBS), Swiggy (HDFC logo), Zomato (RBL).
- No bank offers on product page: LG (generic cards), Dell, Ajio (low-value item), Goibibo (hotel page before room selection).
- Not done: checkout and payment pages (need sign-in or booking), mobile apps.
- New evidence in `screenshots/evidence/` (14 files). Tata CLiQ and Reliance Digital product-page findings are text-scan only, no screenshot.

### 7. Deck updated
- Overall status now: 6 logo shown, 3 text only, 9 rivals shown, 2 no bank shown.
- Slides changed: 2 (6 of 20), 3 (six wins), 4 (nine rival brands), 5 (three text-only brands, replaces the old "no bank logos" slide), 6 (table), 8 (new asks).
- Fixed HTML layout: card text overflow on slide 3 and table height on slide 6.
- Verified: PPTX exported through PowerPoint and reviewed; HTML checked in browser with every slide's content above the i-Man zone.

### 8. Project folder moved
- Moved the whole project to `/Users/user3/Desktop/Ulkrisht/icici-logo-audit/` at the user's request. Paths in `scripts/build_deck.py` updated to match.

### 9. Website on Netlify
- Built a website from the whole project: summary numbers, all 20 brand cards with filters, evidence gallery, deck (HTML, PPTX, PDF), findings CSV, method and limits, and this activity log.
- Live at https://icici-logo-audit.netlify.app (Netlify project `icici-logo-audit`, site ID 5a322c5a-4063-432f-80ad-e5ce19a5b18e).
- Site is public to anyone with the link, but hidden from search engines (noindex headers and robots.txt). No password set.
- Rebuild with `python3 scripts/build_site.py`, which writes the `site/` folder. Redeploy through Netlify after any change.

### 10. Site packaged for another Netlify account
- Created `deliverables/icici-logo-audit-site.zip` (53 files, 2.7 MB, `index.html` at the top level) for drag-and-drop upload at https://app.netlify.com/drop while signed in to the other account.

### 11. Daily tracker for all Festive Bonanza brands
- Scope widened from the top 20 to every brand on the Festive Bonanza page: 141 offers, 97 brands (card and network offers excluded). Brand websites are listed in `data/brands.json`; 7 brands have no known website yet (Bookmark, Furniselan, Hazel Kitchenware, INSPL, OneSky, Solara Home, Vergo).
- `scripts/daily_check.py` reads the Bonanza page, opens each brand's homepage in Google Chrome, and looks for ICICI in image names and alt text, in page text, and inside images using macOS text recognition (`scripts/ocr.swift`, built to `scripts/bin/ocr`). Saves `data/daily/<date>/results.json` and a screenshot per brand.
- First run, October 28, 2026: 17 ICICI logo shown, 3 named in text only, 16 other banks only, 52 no bank shown, 2 could not be checked (Ajio blocks automated browsers; Nomad did not load), 7 website needed.
- Homepage only. The 20-brand baseline also checked product pages, so some brands differ (for example OnePlus shows the logo only one click deep).
- Website rebuilt: `index.html` is now the daily tracker with a calendar (pick any date to see that day's results and changes from the previous day). The original 20-brand audit moved to `audit.html`.
- `deliverables/icici-logo-tracker-site.zip` is the site for drag-and-drop upload to the user's own Netlify account. Rebuilt by `python3 scripts/build_site.py`.
- Scheduled task "ICICI logo daily tracker" runs every day at about 9:00 AM IST while the Claude app is open. It deploys automatically only once `data/netlify-site.json` holds the target site ID and a Netlify connector for that account is connected.
- Update: the user uploads the zip to their own Netlify account themselves. The daily task no longer deploys; it only runs the check and rebuilds `deliverables/icici-logo-tracker-site.zip`.

## November 6, 2026

### 12. Daily check (one run)
- Run on November 6, 2026 (2:14 PM IST): 144 offers, 104 brands. 14 ICICI logo shown, 3 text only, 16 other banks only, 51 no bank shown, 4 could not be checked, 16 website needed.
- 9 new brands on the Bonanza page with no website set: Blue Star, Daikin, Native, GIVA, PNGS Reva Diamond, Jewelbox, WearKatha, Fitelo, Lifecell. Cleartrip and The Sleep Company were not on the page that day.
- The site and zip were not rebuilt after this run. No other runs happened between October 28 and November 17.

## November 17, 2026

### 13. Scheduled task found missing
- The "ICICI logo daily tracker" scheduled task no longer exists, so the check did not run daily. Not recreated yet; waiting for the user's decision.

### 14. New brand websites added
- Added to `data/brands.json`: Blue Star (bluestarindia.com), Daikin (daikinindia.com), Native by Urban Company (urbancompany.com/native), GIVA (giva.co), PNGS Reva Diamond (revadiamonds.com), Jewelbox (jewelbox.co.in), WearKatha (wearkatha.com), Fitelo (fitelo.co), LifeCell (lifecell.in). Each site was opened and its page title matched the brand.
- New brand today: Origem (in-store jewellery offer). Website not confirmed; added with no URL, shows as "website needed".

### 15. Daily check (November 17, 2026)
- 142 offers, 102 brands. 16 ICICI logo shown, 3 text only, 15 other banks only, 54 no bank shown, 6 could not be checked, 8 website needed.
- Changes since November 6: Amazon and Sleepyhead now show the ICICI logo (were other banks only); HP now shows other banks only (was no bank shown).
- Could not be checked: Ajio and Fitelo (block automated browsers, HTTP 403), WearKatha (page did not load), MakeMyTrip, Goibibo and Nomad (page did not load). Tried disabling HTTP/2 for MakeMyTrip and Goibibo; it did not help, so the change was reverted.
- Site rebuilt; `deliverables/icici-logo-tracker-site.zip` (22.8 MB) now covers October 28, November 6 and November 17. Upload it to Netlify at https://app.netlify.com/drop to update the live site.

## November 19, 2026

### 16. Daily scheduled task recreated
- New scheduled task "ICICI logo daily tracker" (ID `icici-logo-daily-tracker-2`) runs every day at about 9:00 AM IST while the Claude app is open; if the app is closed, it runs on next launch.
- Each run: runs `scripts/daily_check.py`, rebuilds the site and `deliverables/icici-logo-tracker-site.zip`, compares with the previous day, and adds an entry to this log. It does not deploy; the user uploads the zip to Netlify.
- Saved in Bypass permissions mode (runs without asking). A first run was started on November 19, 2026.

### 17. Daily check rerun (November 19, 2026)
- Reran the full check at 2:08 PM IST at the user's request; the 12:37 PM run had 11 brands that could not be checked. 142 offers, 102 brands.
- Result: 14 ICICI logo shown, 2 text only, 16 other banks only, 56 no bank shown, 6 could not be checked, 8 website needed.
- Fixed a false positive: Anvayaa shows an ICICI Lombard client logo, not ICICI Bank. `scripts/daily_check.py` now ignores ICICI Lombard, ICICI Prudential and ICICI Securities/ICICIdirect in images, OCR and text. Earlier days were checked; none were affected.
- Changes since November 17: Akbar Travels (ICICI logo → other banks only), Nilkamal Furniture (ICICI logo → no bank shown), Reliance Digital (text only → no bank shown), HP (other banks only → no bank shown), Anvayaa (no bank shown → other banks only).
- Could not be checked: Ajio and Fitelo (HTTP 403), MakeMyTrip and Goibibo (HTTP/2 error), Nomad and WearKatha (did not load). Same group as November 17.
- Site and `deliverables/icici-logo-tracker-site.zip` rebuilt with October 28, November 6, 17 and 19. Upload to Netlify to update the live site.

### 18. Public website on Render, daily run on GitHub Actions
- Public link: https://icici-logo-tracker.onrender.com (Render free static site `icici-logo-tracker`, workspace iKriti). Hidden from search engines (noindex), but open to anyone with the link.
- Code and data: https://github.com/TestikritiICICI/icici-logo-tracker (public repo).
- `.github/workflows/daily-check.yml` runs every day at 03:30 UTC (9:00 AM IST) on GitHub's servers, with no Mac or person needed. It runs the check with Chromium and Tesseract OCR, saves `results.json` to `main`, rebuilds the website and force-pushes it to the `site` branch. Render redeploys automatically on each push to `site`. A "Run workflow" button on the Actions tab starts a run by hand.
- The workflow file is written as one-line JSON (valid YAML) because it was added through the GitHub web editor; the Mac's saved GitHub login cannot push workflow files.
- Changes for servers: OCR falls back to Tesseract when not on a Mac; Chromium is used instead of Google Chrome; ICICI logos are bundled in `assets/`; screenshots are kept on the site for the last 30 days (results are kept for all days).
- Screenshots are not stored in `main`; each run restores the last 30 days of screenshots from the `site` branch.
- The Mac scheduled task (`icici-logo-daily-tracker-2`) is now a duplicate of the GitHub run.
