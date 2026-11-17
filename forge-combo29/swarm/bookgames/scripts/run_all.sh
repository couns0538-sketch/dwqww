#!/bin/bash
# Reproduce every number in FINDINGS.md.
#
# Requires: the engine built from 6b98f217 with g++ (see STATUS.md), and the
# two patched builds for the trap-1 and trap-2 comparisons.
#
#   ENGINE_LOCK, ENGINE_TRAP1, ENGINE_TRAP2  paths to the three binaries
#   BOOK                                     path to src/book_data.inc
#
# Every script is safe to run alone; this only fixes the order and the arguments.
set -u
cd "$(dirname "$0")"

ENGINE_LOCK=${ENGINE_LOCK:?set ENGINE_LOCK to the lock binary}
ENGINE_TRAP1=${ENGINE_TRAP1:-}
ENGINE_TRAP2=${ENGINE_TRAP2:-}
BOOK=${BOOK:?set BOOK to forge-combo29/src/book_data.inc}
OUT=${OUT:-out}
mkdir -p "$OUT"

echo "=== 0. honesty pins (must print 312866 / 862329 / 3024920 / 4865609) ==="
printf 'uci\nisready\nbench 11\nbench 13\nbench 16\nquit\n' | "$ENGINE_LOCK" | grep 'bench depth'
printf 'position startpos\ngo perft 5\nquit\n' | "$ENGINE_LOCK" | grep '^nodes'

echo "=== 1. material-judge self-test (must pass before any Q3 number) ==="
python3 test_material_judge.py || exit 1

echo "=== 2. book graph: cycles, depth, leaf ply, controls ==="
python3 book_paths.py "$BOOK" "$OUT/book_graph.json"

echo "=== 3. book RNG: variety 30 vs 0 over 24 processes ==="
python3 q0_rng.py --engine "$ENGINE_LOCK" --out "$OUT/q0-book-rng.json"

echo "=== 4. two-sided games (the long part; ~11s/game at 3000+50) ==="
python3 play_games.py --engine "$ENGINE_LOCK" --games 320 --workers 3 \
  --book-depth 30 --book-variety 30 --wtime 3000 --btime 3000 --winc 50 --binc 50 \
  --out "$OUT/games-default.json" --tag default
python3 analyse_games.py "$OUT/games-default.json" --out "$OUT/games-default-summary.json"

echo "=== 5. exit quality and exit drawn-roots ==="
python3 q1b_exit_quality.py --engine "$ENGINE_LOCK" --games "$OUT/games-default.json" \
  --out "$OUT/q1b-exit-quality.json"
python3 q1c_exit_drawn.py --engine "$ENGINE_LOCK" --games "$OUT/games-default.json" \
  --out "$OUT/q1c-exit-drawn.json"

echo "=== 6. book vs depth 18, then the depth-18 verdict ==="
python3 extract_played.py --games "$OUT/games-default.json" --out "$OUT/played.json"
python3 q3_book_vs_search.py --engine "$ENGINE_LOCK" --positions "$OUT/played.json" \
  --out "$OUT/q3-played.json" --book "$BOOK" --book-variety 30
python3 q3b_depth18_verdict.py --engine "$ENGINE_LOCK" --losses "$OUT/q3-played.json" \
  --out "$OUT/q3-depth18-verdict.json"

echo "=== 7. re-entry structure and the shuffle that reaches a threefold ==="
python3 reentry_drawn.py "$BOOK" "$OUT/reentry_drawn.json" 6 20000
python3 q2b_shuffle.py "$ENGINE_LOCK" "$OUT/q2b-shuffle.json" "$BOOK"

echo "=== 8. clock gate on both builds (variety 0 pins the RNG) ==="
python3 q4_clock_gate.py "$ENGINE_LOCK" "$OUT/q4-clock-lock.json" "$BOOK" 0
if [ -n "$ENGINE_TRAP1" ]; then
  python3 q4_clock_gate.py "$ENGINE_TRAP1" "$OUT/q4-clock-patched.json" "$BOOK" 0
else
  echo "  (skip patched clock gate: ENGINE_TRAP1 not set)"
fi

echo "=== 9. does trap 2 close the threefold route? ==="
if [ -n "$ENGINE_TRAP2" ]; then
  python3 q5_trap2_closes_route.py "$ENGINE_LOCK" "$ENGINE_TRAP2" \
    "$OUT/q5-trap2-closes-route.json"
else
  echo "  (skip trap-2 closure: ENGINE_TRAP2 not set)"
fi

echo
echo "done. compare $OUT against evidence/ in this folder."
