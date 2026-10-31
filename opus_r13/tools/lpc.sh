#!/usr/bin/env bash
# lpc.sh <exe> <out.json> <cpu mask hex> [lp_check run args...] - QA's kit lp_check.py `run` under run_low (BelowNormal, mask).
set -euo pipefail
exe="$1"; out="$2"; mask="$3"; shift 3; T=$(dirname "$0")
PY='C:\Users\Administrator\grok-pc\nnue\.venv\Scripts\python.exe'
LP='C:\Users\Administrator\grok-pc\forge_push\qa_ltopgo_al1_stage\kit_v23\tools\lp_check.py'
powershell -NoProfile -ExecutionPolicy Bypass -File "$(cygpath -w "$T/run_low.ps1")" -Mask "$mask" -Prio BelowNormal -Exe "$PY" \
  -ArgLine "-I -B $LP run $(cygpath -w "$exe") $(cygpath -w "$out") $*"
