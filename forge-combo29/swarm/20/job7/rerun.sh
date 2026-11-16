#!/usr/bin/env bash
# rerun.sh — every command of job 7, from scratch, in one committed script (so the tables are pasted output).
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
EXE=/agent/repos/build-base/forge
PATCHED=/agent/repos/scratch-patch01/build/forge
date -u +"start %Y-%m-%dT%H:%M:%SZ" >> "$HERE/stamps.txt"
echo "== 1. the base build: fen / second occurrence / third occurrence"
python3 "$HERE/check_s28f4.py" "$EXE" "$HERE" base
date -u +"base done %Y-%m-%dT%H:%M:%SZ" >> "$HERE/stamps.txt"
echo
echo "== 2. seat 01's patch applied to a scratch copy (nothing committed), pins re-checked"
bash "$HERE/patch_copy.sh"
date -u +"patch done %Y-%m-%dT%H:%M:%SZ" >> "$HERE/stamps.txt"
echo
echo "== 3. the same three cases on the PATCHED build"
python3 "$HERE/check_s28f4.py" "$PATCHED" "$HERE" patched
date -u +"patched done %Y-%m-%dT%H:%M:%SZ" >> "$HERE/stamps.txt"
echo
echo "== 4. control: the halfmove door, both builds, through an INTERACTIVE driver"
python3 "$HERE/halfmove_control.py" "$EXE" "$PATCHED"
date -u +"done %Y-%m-%dT%H:%M:%SZ" >> "$HERE/stamps.txt"
