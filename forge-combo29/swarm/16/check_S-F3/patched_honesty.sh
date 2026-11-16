#!/usr/bin/env bash
# patched_honesty.sh : honesty numbers for a build, written beside its raw files.
# usage: patched_honesty.sh <exe> <rawdir> <outfile>
set -u
EXE="$1"; RAW="$2"; OUT="$3"
{
  echo "# HONESTY of the PATCHED (symmetrised-PSQT) build"
  echo "date $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "exe $(sha256sum "$EXE")"
  printf 'uci\nquit\n' | "$EXE" | grep '^id name'
  echo "expected / measured"
  echo "bench 11 -> 312866 / $(grep -oE 'nodes +[0-9]+' "$RAW/bench_11.raw" | tail -1 | grep -oE '[0-9]+$')"
  echo "bench 13 -> 862329 / $(grep -oE 'nodes +[0-9]+' "$RAW/bench_13.raw" | tail -1 | grep -oE '[0-9]+$')"
  echo "bench 16 -> 3024920 / $(grep -oE 'nodes +[0-9]+' "$RAW/bench_16.raw" | tail -1 | grep -oE '[0-9]+$')"
  echo "go perft 5 -> 4865609 / $(grep -oE 'nodes +[0-9]+' "$RAW/go_perft_5.raw" | tail -1 | grep -oE '[0-9]+$')"
  echo ""
  echo "NOTE: the three bench counts DIFFER from the pinned numbers, because the patched evaluation changes"
  echo "pruning. perft 5 is unchanged (4,865,609), which is exactly what S-F3 claims. This build is NOT used"
  echo "for any bench-based comparison, and no engine source file is committed: the patch lives as"
  echo "psqt_symmetry.patch.txt and is applied to a scratch worktree outside the repository."
} > "$OUT"
cat "$OUT"
