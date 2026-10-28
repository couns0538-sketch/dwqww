#!/usr/bin/env bash
# Build the pick-order oracle twice from one source tree (switch off = the AL1 lock picker, switch on =
# FORGE_NOZERO_MOVE_BUFFERS=1), run each build with every storage pre-fill pattern, and require that all runs
# print the same per-root digests as the reference run (switch off, first pattern; zero by default).
# usage: run_picker_oracle.sh <src_root> <out_dir> [roots.epd] [children_roots]
#   env CXX (default g++), ARCH_FLAGS (default "-march=x86-64-v3 -mtune=znver5"), EXTRA_FLAGS (e.g. sanitizers),
#   LINK_FLAGS (e.g. -static on Windows), PATTERNS (default "zero a5 01 ff random heap"), RUNNER (e.g. a valgrind
#   command line put in front of each oracle run).
# Exit 0 only if every run succeeds and matches the reference.
set -uo pipefail
# pwd -W gives D:/... paths in Git Bash, which native Windows compilers accept; plain pwd elsewhere.
SRC=$(cd "$1" && (pwd -W 2>/dev/null || pwd)); OUT=$2
mkdir -p "$OUT"; OUT=$(cd "$OUT" && (pwd -W 2>/dev/null || pwd))
ROOTS=${3:-$SRC/tools/openings/forge-10000.epd}
CHILDREN=${4:-2000}
CXX=${CXX:-g++}
ARCH_FLAGS=${ARCH_FLAGS:--march=x86-64-v3 -mtune=znver5}
PATTERNS=${PATTERNS:-zero a5 01 ff random heap}
ORACLE="$SRC/opus_round1/sol_S14/followup_zerofill/picker_order_oracle.cpp"
# Assertions stay on (no -DNDEBUG). The oracle includes ../../../src/search.cpp relative to its own directory.
# LIFETIME_FLAG: GCC drops stores made before a constructor runs unless -fno-lifetime-dse (clang: pass LIFETIME_FLAG="").
LIFETIME_FLAG=${LIFETIME_FLAG--fno-lifetime-dse}
FLAGS="-std=c++20 -O3 -g -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math $LIFETIME_FLAG $ARCH_FLAGS ${EXTRA_FLAGS:-}"
CORE="$SRC/src/bitboard.cpp $SRC/src/board.cpp $SRC/src/book.cpp $SRC/src/eval.cpp $SRC/src/eval_params.cpp $SRC/src/nnue.cpp"
status=0
for sw in 0 1; do
  exe="$OUT/picker_oracle_sw$sw"
  # shellcheck disable=SC2086
  if ! $CXX $FLAGS -DFORGE_NOZERO_MOVE_BUFFERS=$sw -I"$SRC/include" \
       "$ORACLE" $CORE -pthread ${LINK_FLAGS:-} -o "$exe" > "$OUT/build_oracle_sw$sw.log" 2>&1; then
    echo "oracle build sw=$sw FAILED"; tail -30 "$OUT/build_oracle_sw$sw.log"; exit 1
  fi
  echo "built $exe ($(grep -ci warning "$OUT/build_oracle_sw$sw.log") warning lines)"
done
# Reference: switch off with the first pattern (zero by default).
ref="$OUT/oracle_sw0_${PATTERNS%% *}.txt"
for sw in 0 1; do
  for p in $PATTERNS; do
    f="$OUT/oracle_sw${sw}_$p.txt"
    start=$(date +%s)
    # shellcheck disable=SC2086
    ${RUNNER:-} "$OUT/picker_oracle_sw$sw" "$ROOTS" "$p" --children "$CHILDREN" > "$f" 2> "$OUT/oracle_sw${sw}_$p.err"
    rc=$?
    echo "sw=$sw pattern=$p exit=$rc $(( $(date +%s) - start ))s $(grep '^TOTAL' "$f")"
    [ $rc -eq 0 ] || { status=1; cat "$OUT/oracle_sw${sw}_$p.err"; }
  done
done
for sw in 0 1; do
  for p in $PATTERNS; do
    f="$OUT/oracle_sw${sw}_$p.txt"
    [ "$f" = "$ref" ] && continue
    if cmp -s <(grep -v '^PICKER_ORACLE' "$ref") <(grep -v '^PICKER_ORACLE' "$f"); then
      echo "MATCH sw=$sw pattern=$p"
    else
      echo "DIFFER sw=$sw pattern=$p: first differing lines:"; diff <(grep -v '^PICKER_ORACLE' "$ref") <(grep -v '^PICKER_ORACLE' "$f") | head -6
      status=1
    fi
  done
done
echo "reference: $(grep '^TOTAL' "$ref")"
echo "run_picker_oracle status=$status"
exit $status
