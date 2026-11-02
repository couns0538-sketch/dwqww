#!/usr/bin/env bash
# R14 Main 2: advisory palindromic ABBA, lock FD3A5190 (A0) vs FORGE_SEARCH_SPEED2 ON de20653c (A1), 10 pairs + 3 A/A
# pairs per exe (byte copies), bench depths 16 and 20, every run a fresh process at BelowNormal pinned to CPU 2
# (r12_speed.py; --ignore-idle: the Idle trainer on 0xF does not block, any non-Idle gate / own build does).
set -u
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
R=/d/grok-pc-data/dwqww/.claude/worktrees/o13-p2/opus_r13/p2/speed2/r12_speed.py
D=/d/o14a/p2/abba
[ -e $D/run1 ] && { echo "exists: $D/run1 - refusing"; exit 2; }
mkdir -p $D
for x in A0 A0aa; do cp /c/Users/Administrator/grok-pc/forge_push/bin/forge_ltopgo_x_al1s198_v23.exe $D/$x.exe; done
for x in A1 A1aa; do cp /d/o14a/w/s2on_pc1/src_copy/forge_ltopgo_s2on_pc1.exe $D/$x.exe; done
sha256sum $D/*.exe | sed 's#/d/o14a/p2/abba/##'
date '+start %F %T'
"$PY" -I -B $R --out 'D:\o14a\p2\abba\run1' --cpu 2 --ignore-idle --exe 'A0=D:\o14a\p2\abba\A0.exe' --exe 'A1=D:\o14a\p2\abba\A1.exe' \
  --ref A0 --aa 'A0=D:\o14a\p2\abba\A0aa.exe' --aa 'A1=D:\o14a\p2\abba\A1aa.exe' --pairs 10 --aa-pairs 3 --depths 16 20
echo "abba exit $?"
date '+end %F %T'
