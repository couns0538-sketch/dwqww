#!/usr/bin/env bash
# S24 check from scratch: lock tree + Sol's shelved exact-int32 patch (e661a145) + this follow-up; box-recipe builds;
# UCI option list and bench output (time/nps masked) vs the lock exe; Std pass of the guarded OFF build.
# usage: verify_s24.sh <repo> <shelf patch> <lock exe> <build_pc.sh> <uci_check.py> <python> <new scratch dir>
set -euo pipefail
REPO=$1; SHELF=$2; LOCK=$3; BUILD=$4; CHECK=$5; PY=$6; OUT=$7
HERE=$(cd "$(dirname "$0")" && pwd)
[ -e "$OUT" ] && { echo "scratch dir exists: $OUT"; exit 2; }
mkdir -p "$OUT/tree"
echo "shelf patch sha256 $(sha256sum "$SHELF" | cut -d' ' -f1) (expected e661a145...)"
git -C "$REPO" -c core.autocrlf=false archive d4f4312 | tar -x -m -C "$OUT/tree"
(cd "$OUT/tree" && git apply -p1 "$SHELF" && git apply -p1 "$HERE/forge_sol_S24_int32guards_20261027.patch")
nice -n 19 bash "$BUILD" "$OUT/tree" "$OUT/forge_guarded_off.exe"
uci() { printf 'uci\nquit\n' | "$1" | grep -E '^(id|option) '; }
bench() { (printf 'uci\nsetoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nisready\nbench 13\n'; sleep 25; printf 'quit\n') \
  | "$1" | grep -v -E '^(id|option) |^uciok|^readyok' | sed -E 's/ time [0-9]+/ time T/; s/ nps [0-9]+/ nps N/'; }
diff <(uci "$LOCK") <(uci "$OUT/forge_guarded_off.exe") && echo "uci list: IDENTICAL to the lock"
diff <(bench "$LOCK") <(bench "$OUT/forge_guarded_off.exe") && echo "bench 13 output (time/nps masked): IDENTICAL to the lock"
nice -n 19 "$PY" -I -B "$CHECK" "$OUT/forge_guarded_off.exe" --full
