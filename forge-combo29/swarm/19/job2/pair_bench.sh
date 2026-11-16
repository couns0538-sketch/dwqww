#!/usr/bin/env bash
# pair_bench.sh BASE_EXE PATCH_EXE OUTDIR ROUNDS : alternating `bench 13` runs, nodes per second, ratio CI.
# One fresh engine process per run, alternating base/patch, ROUNDS pairs. Writes raw nps to OUTDIR/nps.txt.
# The CI is the textbook one for the ratio of two means over independent samples (Welch/Student with
# n-1 degrees of freedom, via the log ratio so the interval is not asymmetric by construction).
set -u
BASE="${1:?base exe}"; PATCH="${2:?patch exe}"; OUT="${3:?outdir}"; ROUNDS="${4:-10}"
mkdir -p "$OUT"
{
  echo "base exe $(readlink -f "$BASE")  sha256 $(sha256sum "$BASE" | cut -d' ' -f1)"
  echo "patch exe $(readlink -f "$PATCH")  sha256 $(sha256sum "$PATCH" | cut -d' ' -f1)"
  echo "command: printf 'bench 13\nquit\n' | <exe>   (one fresh process per run, alternating)"
  echo "cores $(nproc)  date $(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > "$OUT/pair_bench.meta"
: > "$OUT/nps.txt"
for r in $(seq 1 "$ROUNDS"); do
  for side in base patch; do
    exe=$BASE; [ "$side" = patch ] && exe=$PATCH
    line=$(printf 'bench 13\nquit\n' | "$exe" 2>&1 | grep -E '^info string bench depth 13')
    nodes=$(echo "$line" | sed -n 's/.*nodes \([0-9]*\).*/\1/p')
    ms=$(echo "$line" | sed -n 's/.*time \([0-9]*\).*/\1/p')
    nps=$(echo "$line" | sed -n 's/.*nps \([0-9]*\).*/\1/p')
    echo "$r $side $nodes $ms $nps" >> "$OUT/nps.txt"
  done
done
date -u
cat "$OUT/nps.txt"
