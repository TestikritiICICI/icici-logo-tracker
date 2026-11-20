#!/bin/bash
# Mac gap-filler for the daily ICICI logo tracker.
#
# GitHub Actions runs the full check every day at 9:00 AM IST, but many Indian
# sites block GitHub's (non-Indian) servers. This script, run on the Mac on an
# Indian connection, rechecks only the brands GitHub could not check, then
# publishes the corrected results to the live site (Render redeploys from the
# "site" branch). If GitHub has no results for today, it runs the full check.
#
# Run: bash scripts/mac_fill_gaps.sh
set -euo pipefail
cd "$(dirname "$0")/.."

REPO_API="https://api.github.com/repos/TestikritiICICI/icici-logo-tracker/actions/runs?per_page=1"
TODAY=$(TZ=Asia/Kolkata date +%F)

# 1. Wait (up to 60 minutes) for any GitHub run in progress, so the two never push at once
for _ in $(seq 1 40); do
  status=$(curl -s -m 30 "$REPO_API" | python3 -c "import json,sys;r=json.load(sys.stdin)['workflow_runs'];print(r[0]['status'] if r else 'completed')" || echo unknown)
  [ "$status" = "completed" ] && break
  echo "GitHub run is $status; waiting..."
  sleep 90
done

# 2. Get GitHub's latest results and the screenshots already on the live site
git pull -q --rebase origin main
git fetch -q --depth 1 origin site
rm -rf prev && git worktree prune
git worktree add -q --detach prev FETCH_HEAD
for d in prev/shots/*/; do
  [ -d "$d" ] || continue
  day=$(basename "$d")
  mkdir -p "data/daily/$day/shots"
  cp -n "$d"* "data/daily/$day/shots/" 2>/dev/null || true
done
git worktree remove --force prev

# 3. Recheck the brands GitHub could not check (or run everything if GitHub has no results today)
RESULTS="data/daily/$TODAY/results.json"
if [ -f "$RESULTS" ]; then
  BLOCKED=$(python3 -c "
import json
d = json.load(open('$RESULTS'))
print(','.join(b['name'] for b in d['brands'] if b['status'] == 'error'))")
  if [ -n "$BLOCKED" ]; then
    echo "Rechecking from the Mac: $BLOCKED"
    python3 scripts/daily_check.py --only "$BLOCKED" --recheck --from-mac
  else
    echo "GitHub checked every brand today; nothing to fill."
  fi
else
  echo "No GitHub results for $TODAY; running the full check on the Mac."
  python3 scripts/daily_check.py
fi

# 4. Rebuild the website, save results to main, publish the site branch
python3 scripts/record_history.py
python3 scripts/build_site.py
git add data/daily data/brands.json
if ! git diff --cached --quiet; then
  git -c user.name="TestikritiICICI" -c user.email="TestikritiICICI@users.noreply.github.com" \
    commit -q -m "Mac recheck of blocked brands $TODAY"
  git push -q origin HEAD:main
fi
export GIT_INDEX_FILE="$(mktemp -d)/site-index"
git --work-tree=site add -A
tree=$(git write-tree)
commit=$(git -c user.name="TestikritiICICI" -c user.email="TestikritiICICI@users.noreply.github.com" \
  commit-tree "$tree" -m "Website for $TODAY (with Mac recheck)")
git push -q -f origin "${commit}:refs/heads/site"
unset GIT_INDEX_FILE
python3 -c "
import json
d = json.load(open('$RESULTS'))
print('Published', d['date'], d['counts'])"
