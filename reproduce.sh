#!/usr/bin/env bash
# One-command reproduction of every number in README.md, docs/CLAIMS.md and docs/index.html from the raw SCAPS-1D exports in data/.
# Needs: pip install -r requirements.txt   (no SCAPS-1D installation needed; the batch exports are in data/)
set -euo pipefail
cd "$(dirname "$0")"
python scripts/make_figures.py     # figures/*.png and data/scaps_metrics.json from the eleven workbooks
python docs/build_assets.py --no-page        # docs/assets/data.js, SVG figures and the social preview for the live page
echo "Done. Compare the printed values with docs/CLAIMS.md."
# python docs/build_assets.py --snap --qa --lighthouse   # static fallbacks for the 3D body scenes, both-theme screenshots, Lighthouse (needs playwright + lighthouse)
