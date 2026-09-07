#!/bin/bash
#
# Commits today's work and pushes it to GitHub.
#
# HOW TO RUN: double-click this file in Finder. A Terminal window opens and
# runs it. If macOS refuses to open it, right-click it and choose Open, then
# confirm — that only needs doing once.
#
# It is safe to run more than once. If there is nothing new to commit it
# will say so and stop.

set -e
cd "$(dirname "$0")"

echo "==============================================="
echo " ESG dashboard — commit and push"
echo "==============================================="
echo

# A previous git command was interrupted and left a lock file behind. It is
# empty and nothing is using it, but git refuses to run while it exists.
if [ -f .git/index.lock ]; then
  echo "Clearing a leftover git lock file..."
  rm -f .git/index.lock
fi

# Tidy the stray temporary files git could not clean up itself. Harmless
# either way, but it keeps the repository tidy.
find .git/objects -name 'tmp_obj_*' -delete 2>/dev/null || true

echo "Files that will be committed:"
echo
git add -A
git status --short
echo

read -r -p "Commit and push these? (y/n) " reply
if [ "$reply" != "y" ] && [ "$reply" != "Y" ]; then
  echo "Stopped. Nothing was committed."
  exit 0
fi

git commit -m "add framework mapping, trend charts and framework grouping

Converter
- tools/brsr_indicators.py holds two transcriptions with their sources: BRSR
  indicator codes from SEBI's format (Annexure I, circular 2021/562), and GRI
  disclosures per indicator from the GRI-SEBI BRSR linkage document (GRI with
  BSE, 2022). All 149 BRSR rows are coded; 114 get indicator-level GRI, 35
  keep a principle-level fallback.
- IFC is derived by alignment through GRI rather than sourced, so it is
  marked unverified and rendered differently. Deliberately narrow at 49 rows:
  GRI 200-series, GRI 2 and 3, and principle-level GRI answers are excluded
  because each produced results that read as nonsense.
- Builds year-over-year trend series from metric labels and flags any series
  jumping threefold or more between years.

Page
- Framework filter (BRSR, BRSR Core, GRI, IFC) alongside theme and keyword.
- Selecting IFC regroups the table under Performance Standards PS1-PS8.
- Trend charts as hand-drawn SVG, zero baseline, exact values printed, with
  a visible caption where the reporting basis appears to have changed.
- Indicator codes and GRI disclosure numbers shown on the page rather than
  in tooltips.

Docs
- product-spec.md revised to revision 11; README and CLAUDE.md updated.
- Adds the framework mapping worksheet and the platform PRD.

The shipped page still has zero dependencies."

echo
echo "Pushing to GitHub..."
git push origin main

echo
echo "==============================================="
echo " Done. View it at:"
echo " https://github.com/deb3002/esg-dashboard"
echo "==============================================="
echo
read -r -p "Press Return to close this window. " _
