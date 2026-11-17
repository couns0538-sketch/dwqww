#!/usr/bin/env bash
# Re-verification of every finding against commit 6b98f217, the audit's base.
#
# Why this exists: this seat originally measured on `integrate/combo29-all`
# (6020972d3), which is a different tree. The two are NOT disjoint — they share
# ancestor e04556ddc, and 6b98f217 is 277 commits ahead of the other — but
# 6b98f217 differs in uci.cpp (+181 lines) and search.cpp (+923), so every
# behaviour claim had to be re-measured rather than assumed.
#
# Usage:  bash swarm/65/scripts/reverify_6b98f217.sh [repo_root] [commit]
#
# The engine is built in a git worktree at the target commit, so nothing in the
# working tree is touched. Bench 11 must print 312866 or the script aborts before
# recording anything.

set -u -o pipefail

REPO="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
COMMIT="${2:-6b98f217}"

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EV="$HERE/../evidence"
WORKTREE="${WORKTREE:-/tmp/sw65-reverify-$(echo "$COMMIT" | cut -c1-8)}"
BUILD="${BUILD:-/tmp/sw65-reverify-build-$(echo "$COMMIT" | cut -c1-8)}"
PIN=312866

mkdir -p "$EV"
echo "== 0. provenance =="
cd "$REPO" || exit 1
echo "repo            $REPO"
echo "target commit   $(git rev-parse "$COMMIT")"
echo "commit subject  $(git log -1 --format=%s "$COMMIT")"
echo "working tree    $(git rev-parse --abbrev-ref HEAD) at $(git rev-parse --short HEAD)"
echo
echo "history relationship between this seat's original base and the target:"
ORIG=origin/integrate/combo29-all
if git rev-parse --verify -q "$ORIG" >/dev/null; then
  echo "  original base   $(git rev-parse "$ORIG")"
  BASE=$(git merge-base "$ORIG" "$COMMIT" 2>/dev/null || true)
  if [ -n "$BASE" ]; then
    echo "  common ancestor $BASE  (so the branches are NOT disjoint)"
  else
    echo "  common ancestor none"
  fi
  echo "  commits only in target: $(git rev-list --count "$ORIG..$COMMIT")"
  echo "  commits only in original base: $(git rev-list --count "$COMMIT..$ORIG")"
  echo "  book-relevant source diff:"
  git diff --stat "$ORIG" "$COMMIT" -- \
    forge-combo29/src/book.cpp forge-combo29/src/book_data.inc \
    forge-combo29/src/uci.cpp forge-combo29/src/search.cpp | sed 's/^/    /'
else
  echo "  $ORIG not present locally; skipping the comparison"
fi
echo

echo "== 1. build at $COMMIT =="
if [ -d "$WORKTREE" ]; then git worktree remove --force "$WORKTREE" 2>/dev/null || rm -rf "$WORKTREE"; fi
git worktree add --detach "$WORKTREE" "$COMMIT" > "$EV/reverify-worktree.log" 2>&1 || {
  echo "worktree checkout failed, see $EV/reverify-worktree.log"; exit 1; }
# /usr/bin/c++ is a broken clang on this host; force g++ and point the linker at
# the right libstdc++ directory.
export LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13
(
  cd "$WORKTREE/forge-combo29" || exit 1
  cmake -S . -B "$BUILD" -DCMAKE_BUILD_TYPE=Release -DFORGE_MARCH=native \
        -DCMAKE_CXX_COMPILER=/usr/bin/g++ > "$EV/reverify-build.log" 2>&1 &&
  cmake --build "$BUILD" -j"$(nproc)" >> "$EV/reverify-build.log" 2>&1
) || { echo "build failed, see $EV/reverify-build.log"; exit 1; }
FORGE="$BUILD/forge"
echo "binary          $FORGE"

echo
echo "== 2. PIN CHECK: bench 11 must be $PIN =="
BENCH_OUT=$(printf 'uci\nisready\nbench 11\nquit\n' | timeout 600 "$FORGE" 2>&1 | grep "bench depth")
echo "$BENCH_OUT"
GOT=$(echo "$BENCH_OUT" | sed -n 's/.*nodes \([0-9]*\).*/\1/p')
if [ "$GOT" != "$PIN" ]; then
  echo "PIN MISMATCH: expected $PIN, got '${GOT:-nothing}'. Refusing to record anything."
  exit 1
fi
echo "pin OK ($GOT) — recording results"

echo
echo "== 3. the three traps =="
python3 "$HERE/q10_traps_on_base.py" "$FORGE" | tee "$EV/reverify-traps.txt" || {
  echo "TRAP CHECK FAILED"; exit 1; }

echo
echo "== 4. variety nondeterminism and MultiPV =="
python3 "$HERE/q11_variety_multipv_on_base.py" "$FORGE" | tee "$EV/reverify-variety-multipv.txt"

echo
echo "== 5. wire shape and emit-site line numbers =="
python3 "$HERE/q12_wire_on_base.py" "$FORGE" "$WORKTREE/forge-combo29/src/uci.cpp" \
  | tee "$EV/reverify-wire.txt"

echo
echo "== 6. soundness spot check (book data identity + legality) =="
LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13 g++ -std=c++20 -O2 \
  -I"$WORKTREE/forge-combo29/include" -DFORGE_NNUE_HIDDEN=256 \
  -DFORGE_NNUE_WEIGHTS="\"$WORKTREE/forge-combo29/src/nnue_weights.inc\"" \
  "$HERE/probe_book.cpp" \
  "$WORKTREE/forge-combo29/src/board.cpp" "$WORKTREE/forge-combo29/src/bitboard.cpp" \
  "$WORKTREE/forge-combo29/src/book.cpp" "$WORKTREE/forge-combo29/src/eval.cpp" \
  "$WORKTREE/forge-combo29/src/eval_params.cpp" "$WORKTREE/forge-combo29/src/nnue.cpp" \
  "$WORKTREE/forge-combo29/src/nnue_v3.cpp" \
  -o /tmp/probe_book_reverify -lpthread >> "$EV/reverify-build.log" 2>&1 || {
    echo "probe build failed, see $EV/reverify-build.log"; exit 1; }
/tmp/probe_book_reverify 40 > "$EV/reverify-book-walk.tsv"
head -3 "$EV/reverify-book-walk.tsv"
python3 "$HERE/q7_soundness.py" "$EV/reverify-book-walk.tsv" \
  | tee "$EV/reverify-soundness.txt" | grep -E "positions checked|book moves|invalid FEN|key mismatch|illegal"

echo
echo "done. evidence in $EV/reverify-*"
