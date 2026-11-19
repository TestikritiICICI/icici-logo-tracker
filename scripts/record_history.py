"""Append today's counts to data/daily/run-history.csv (once per date)."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HISTORY = ROOT / "data/daily/run-history.csv"
FIELDS = ["date", "logo", "text", "rival", "none", "error", "nourl"]

latest = sorted((ROOT / "data/daily").glob("*/results.json"))[-1]
day = json.loads(latest.read_text())
rows = list(csv.DictReader(HISTORY.open())) if HISTORY.exists() else []
rows = [r for r in rows if r["date"] != day["date"]]
rows.append({"date": day["date"], **{k: day["counts"].get(k, 0) for k in FIELDS[1:]}})
with HISTORY.open("w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=FIELDS)
    w.writeheader()
    w.writerows(sorted(rows, key=lambda r: r["date"]))
print(f"History: {day['date']} {day['counts']}")
