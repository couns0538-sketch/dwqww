#!/usr/bin/env bash
# run_aa_identical.sh <out folder name> <cpu mask> - bug hunt item 8 (Opus 30-h job): abba.py with the IDENTICAL command
# (the lock exe, bench 16) in both arms. If arm B is still slower, the harness / launch path is biased; if not, the
# earlier A/A (lock file vs a copy, both directions B slower by ~5.5 %) was a per-file effect plus chance of direction.
set -u
name="$1"; mask="$2"
CMD="printf 'bench 16\nquit\n' | /c/Users/Administrator/grok-pc/forge_push/bin/forge_ltopgo_x_al1s198_v23.exe"
C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe -I -B 'D:\o30\wt\opus_30h\tools\abba.py' \
    --out "D:\\o30\\speed\\aa\\$name" --a "$CMD" --b "$CMD" --pairs 10 --warmup 1 \
    --metric 'nps (\d+)' --higher-better --identity 'bench depth 16 nodes (\d+)' --identity-ab --mask "$mask"
