#!/usr/bin/env bash
# fit_resume.sh <run name> <cpu mask> [--until YYYY-MM-DDTHH:MM] [--positions N] - resume a stopped o30_fit.py run at
# Idle on <cpu mask> (forward-slash paths). Logs D:/o30/logs/<name>_r<YYYYmmdd_HHMMSS>.out / .err (new files per session;
# fit_bg.sh's fixed names would be refused by lowrun on a resume). Blocks until the trainer exits.
set -uo pipefail
name="$1"; mask="$2"; shift 2
A=$(cd "$(dirname "$0")" && pwd)
[ -e "D:/o30/runs/$name/last.pt" ] || { echo "no last.pt in D:/o30/runs/$name" >&2; exit 2; }
stamp=$(date +%Y%m%d_%H%M%S)
line="-I -B D:/o30/wt/opus_30h/a/o30_fit.py train --out D:/o30/runs/$name --resume $*"
powershell -NoProfile -ExecutionPolicy Bypass -File "$(cygpath -w "$A/../tools/lowrun.ps1")" -Mask "$mask" -Priority Idle \
  -Exe 'C:\Users\Administrator\grok-pc\nnue\.venv\Scripts\python.exe' -ArgLine "$line" \
  -Out "D:/o30/logs/${name}_r$stamp.out" -Err "D:/o30/logs/${name}_r$stamp.err"
echo "fit_resume $name exit $?"
