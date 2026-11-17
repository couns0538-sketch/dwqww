#!/usr/bin/env bash
# Re-runs the whole book audit from scratch and writes the raw evidence.
#
# Every claim in FINDINGS.md / BOOK_WIRE.md has a section here that produces it.
# Usage:  bash swarm/65/scripts/run_all.sh [repo_root]
#
# Outputs land in swarm/65/evidence/. Nothing here needs network access.

set -u -o pipefail

ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
cd "$ROOT" || exit 1
SCRIPTS="swarm/65/scripts"
EV="swarm/65/evidence"
BUILD="${BUILD:-/tmp/build65}"
mkdir -p "$EV"

echo "== 0. build engine and probe tools =="
cmake -S . -B "$BUILD" -DCMAKE_BUILD_TYPE=Release -DFORGE_MARCH=native > "$EV/build.log" 2>&1 || {
  echo "cmake failed, see $EV/build.log"; exit 1; }
cmake --build "$BUILD" -j"$(nproc)" >> "$EV/build.log" 2>&1 || { echo "build failed"; exit 1; }
FORGE="$BUILD/forge"

# The probe tools link the engine's own board and book, so they see exactly the
# compiled-in data the engine sees.
CXXFLAGS=(-std=c++20 -O2 -Iinclude -DFORGE_NNUE_HIDDEN=256
          -DFORGE_NNUE_WEIGHTS="\"$ROOT/src/nnue_weights.inc\"")
g++ "${CXXFLAGS[@]}" "$SCRIPTS/probe_book.cpp" src/board.cpp src/bitboard.cpp src/book.cpp \
    src/eval.cpp src/eval_params.cpp src/nnue.cpp -o /tmp/probe_book -lpthread || exit 1
g++ "${CXXFLAGS[@]}" "$SCRIPTS/book_census.cpp" src/board.cpp src/bitboard.cpp src/book.cpp \
    src/eval.cpp src/eval_params.cpp src/nnue.cpp -o /tmp/book_census -lpthread || exit 1
g++ "${CXXFLAGS[@]}" "$SCRIPTS/key_probe.cpp" src/board.cpp src/bitboard.cpp src/book.cpp \
    src/eval.cpp src/eval_params.cpp src/nnue.cpp -o /tmp/key_probe -lpthread || exit 1

echo "== 1. book census =="
/tmp/book_census | tee "$EV/census.txt"

echo "== 2. walk the whole book =="
/tmp/probe_book 40 > /tmp/book_full.txt
head -3 /tmp/book_full.txt
cp /tmp/book_full.txt "$EV/book_walk.tsv"

echo "== 3. coverage: walk vs BookKeys =="
python3 "$SCRIPTS/coverage_check.py" --tsv /tmp/book_full.txt --inc src/book_data.inc \
  | tee "$EV/coverage.txt"

echo "== 4. SEE self-test (must pass before any soundness claim) =="
python3 "$SCRIPTS/see_selftest.py" | tee "$EV/see_selftest.txt" || { echo "SEE SELF-TEST FAILED"; exit 1; }

echo "== 5. soundness: legality, material, key agreement =="
python3 "$SCRIPTS/q7_soundness.py" /tmp/book_full.txt | tee "$EV/soundness.txt"

echo "== 6. engine verification of every SEE-flagged move =="
python3 "$SCRIPTS/q7b_verify.py" /tmp/book_full.txt --binary "$FORGE" --depth 12 \
  | tee "$EV/soundness_verified.txt"

echo "== 7. exhaustive quality gap at depth 10, plus its noise floor =="
python3 "$SCRIPTS/q7d_noise_floor.py" 10 /tmp/book_full.txt | tee "$EV/noise_floor.txt"
python3 "$SCRIPTS/q7c_exhaustive_gap.py" /tmp/book_full.txt --binary "$FORGE" \
  --depth 10 --threshold 100 | tee "$EV/gap_depth10.txt"

echo "== 8. deep re-check of the worst offenders =="
python3 "$SCRIPTS/q7e_deep_check.py" --binary "$FORGE" --depths 10,14,18 \
  | tee "$EV/deep_check.txt"

echo "== 9. polyglot key conformance vs python-chess =="
python3 "$SCRIPTS/key_conformance.py" | tee "$EV/key_conformance.txt"

echo "== 10. go-form matrix =="
python3 "$SCRIPTS/q1_go_matrix.py" --binary "$FORGE" | tee "$EV/go_matrix.txt"

echo "== 11. book cost and the info-depth deadlock =="
python3 "$SCRIPTS/q2_cost_and_deadlock.py" --binary "$FORGE" | tee "$EV/cost_deadlock.txt"

echo "== 12. OwnBook interactions: drawn root, MultiPV, clock, gated forms =="
python3 "$SCRIPTS/q4_interactions.py" --binary "$FORGE" | tee "$EV/interactions.txt"

echo "== 13. gate and RNG behaviour =="
python3 "$SCRIPTS/q4b_gates_and_rng.py" --binary "$FORGE" | tee "$EV/gates_rng.txt"

echo "== 14. book boundary walk =="
python3 "$SCRIPTS/q5_boundary.py" --binary "$FORGE" --plies 24 | tee "$EV/boundary.txt"

echo "== 16. determinism across ten fresh processes =="
python3 "$SCRIPTS/q6_determinism.py" --binary "$FORGE" --variety 0 --runs 10 | tee "$EV/determinism_v0.txt"
python3 "$SCRIPTS/q6_determinism.py" --binary "$FORGE" --variety 30 --runs 10 | tee "$EV/determinism_v30.txt"

echo "== 17. score absence on the book path, with an off-book control =="
python3 "$SCRIPTS/q3_score_absence.py" "$FORGE" | tee "$EV/score_absence.txt" || { echo "SCORE-ABSENCE CHECK FAILED"; exit 1; }

echo "== 18. book pre-empts drawn-root detection =="
python3 "$SCRIPTS/q4c_drawn_root.py" "$FORGE" | tee "$EV/drawn_root.txt" || { echo "DRAWN-ROOT CHECK FAILED"; exit 1; }

echo "== 19. castle wire form round trip =="
python3 "$SCRIPTS/q1b_castles.py" /tmp/book_full.txt "$FORGE" | tee "$EV/castles.txt"

echo "== 20. book path latency distribution =="
python3 "$SCRIPTS/q2b_latency.py" --binary "$FORGE" --runs 200 | tee "$EV/latency.txt"

echo
echo "done. evidence in $EV/"
