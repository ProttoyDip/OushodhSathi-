#!/usr/bin/env sh
# The synthetic benchmark: both evals on eval/synthetic/ (computer-drawn images), written next to the
# set as eval/synthetic/results_<prompt>.json and bp_results_<prompt>.json. Never touches real results.
#   sh eval/run_synthetic.sh                 # the vision chain, as the app runs it
#   sh eval/run_synthetic.sh --per-provider  # also each vision provider alone (strip eval)
# Needs a vision provider key in backend/.env. These numbers are NOT real-photo accuracy.
set -e
cd "$(dirname "$0")/.."
PY="backend/.venv/bin/python"
[ -x "$PY" ] || PY="backend/.venv/Scripts/python"
"$PY" eval/run_eval.py --kind synthetic --labels eval/synthetic/labels.csv "$@"
"$PY" eval/run_bp_eval.py --kind synthetic --labels eval/synthetic/bp_labels.csv
