#!/bin/bash
# Auto-publish marginalia: regenerate the site from whatever notebooks are in
# the "Blog" folder on rm2, and if the generated site changed, commit + push
# so GitHub Pages rebuilds. Runs unattended via launchd.
#
# Tolerant of the tablet being unreachable (it sleeps its WiFi) -- such runs
# just skip and try again next interval. The vision analysis is content-hash
# cached, so runs where nothing changed make no API calls and cost nothing.

set -uo pipefail

REPO="/Users/amit/Projects/marginalia"
LOG="$REPO/.cache/publish.log"
mkdir -p "$REPO/.cache"
cd "$REPO" || exit 1

# Skip quietly if the tablet isn't reachable right now.
if ! ssh -o ConnectTimeout=6 -o BatchMode=yes rm2 \
        "test -d .local/share/remarkable/xochitl" 2>/dev/null; then
    echo "$(date): rm2 unreachable, skipping" >> "$LOG"
    exit 0
fi

if ! .venv/bin/python generate.py >> "$LOG" 2>&1; then
    echo "$(date): generate failed" >> "$LOG"
    exit 0
fi

git add docs/
if git diff --cached --quiet; then
    echo "$(date): no changes" >> "$LOG"
    exit 0
fi

git -c user.name="Amit T Subhash" -c user.email="amitsubhashco@gmail.com" \
    commit -m "Publish: update site from Blog folder ($(date +%Y-%m-%d))" \
    >> "$LOG" 2>&1
if git push >> "$LOG" 2>&1; then
    echo "$(date): published" >> "$LOG"
else
    echo "$(date): push failed (commit is local)" >> "$LOG"
fi
