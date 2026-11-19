# The synthetic benchmark: both evals on eval/synthetic/ (computer-drawn images), written next to the
# set as eval/synthetic/results_<prompt>.json and bp_results_<prompt>.json. Never touches real results.
#   powershell -File eval/run_synthetic.ps1                 # the vision chain, as the app runs it
#   powershell -File eval/run_synthetic.ps1 -PerProvider    # also each vision provider alone (strip eval)
# Needs a vision provider key in backend/.env. These numbers are NOT real-photo accuracy.
param([switch]$PerProvider)
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
$py = "backend/.venv/Scripts/python.exe"
if (-not (Test-Path $py)) { $py = "backend/.venv/bin/python" }
$extra = @()
if ($PerProvider) { $extra += "--per-provider" }
& $py eval/run_eval.py --kind synthetic --labels eval/synthetic/labels.csv @extra
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $py eval/run_bp_eval.py --kind synthetic --labels eval/synthetic/bp_labels.csv
exit $LASTEXITCODE
