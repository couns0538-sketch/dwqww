#!/usr/bin/env bash
# For each r3 merge commit: (a) the manual resolution = diff between the recomputed automatic merge (git merge-tree)
# and the committed merge, excluding the mechanical removal of src/search.cpp / include/forge/search.hpp;
# (b) the merged branch's own engine diff against the AL1 base, for comparison. One file per merge.
set -u
cd /f/opus_scratch/worktrees/fable_review || exit 1
OUT=/f/opus_scratch/fable_review/deep/r3; mkdir -p "$OUT"
for m in "$@"; do
  p1=$(git rev-parse "$m^1"); p2=$(git rev-parse "$m^2")
  t=$(git merge-tree --write-tree "$p1" "$p2" 2>/dev/null | head -1)
  f="$OUT/$m.txt"
  { echo "# merge $m: $(git log -1 --format=%s "$m" | cut -c1-120)"
    echo "# parent2 $(git rev-parse --short "$p2") ; auto-merge tree $t ; conflicts: $(git merge-tree --write-tree "$p1" "$p2" 2>/dev/null | grep -c '^CONFLICT')"
    echo "## (a) manual resolution vs the automatic merge (src include tests CMakeLists.txt, without search.cpp/search.hpp)"
    git diff "$t" "$m" -- src include tests CMakeLists.txt ':!src/search.cpp' ':!include/forge/search.hpp' | grep -v '^index '
    echo "## (b) the merged branch's own engine diff vs d4f4312 (src include, +/- lines only)"
    git diff d4f4312 "$p2" -- src include | grep -E '^(diff --git|@@|[-+])' | grep -v -E '^(\+\+\+|---)'
  } > "$f" 2>&1
  echo "$m $(git log -1 --format=%s "$m" | cut -c1-60): $(grep -c '' "$f") lines, resolution $(sed -n '/^## (a)/,/^## (b)/p' "$f" | grep -c '^[-+]') +/- lines, branch diff $(sed -n '/^## (b)/,$p' "$f" | grep -c '^[-+]') +/- lines"
done
