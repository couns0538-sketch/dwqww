#!/usr/bin/env bash
# fit_bg.sh <run name> <cpu mask> [o30_fit.py train arguments ...] - start one o30_fit.py run at Idle on <cpu mask>
# with forward-slash Windows paths (no backslash quoting traps): run dir D:/o30/runs/<name>, logs
# D:/o30/logs/<name>.out / .err (lowrun refuses existing files). Blocks until the trainer exits; prints its exit code.
set -uo pipefail
name="$1"; mask="$2"; shift 2
A=$(cd "$(dirname "$0")" && pwd)
line="-I -B D:/o30/wt/opus_30h/a/o30_fit.py train --out D:/o30/runs/$name $*"
powershell -NoProfile -ExecutionPolicy Bypass -File "$(cygpath -w "$A/../tools/lowrun.ps1")" -Mask "$mask" -Priority Idle \
  -Exe 'C:\Users\Administrator\grok-pc\nnue\.venv\Scripts\python.exe' -ArgLine "$line" \
  -Out "D:/o30/logs/$name.out" -Err "D:/o30/logs/$name.err"
echo "fit_bg $name exit $?"
