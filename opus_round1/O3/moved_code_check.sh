#!/usr/bin/env bash
# Review aid for the O3 split: compare the lock's src/search.cpp with the new search modules as a
# multiset of normalised source lines (comments, blank lines, includes, namespace braces dropped).
# Lines that appear on only one side are exactly the non-verbatim edits of the refactor.
# usage (from the repository root): opus_round1/O3/moved_code_check.sh [base_commit]
set -euo pipefail
BASE=${1:-294dbed}
TMP=$(mktemp -d)
git show "$BASE:src/search.cpp" > "$TMP/old.cpp"
cat include/forge/history.hpp > "$TMP/new.cpp"   # history_bonus, apply_history, HistoryMax moved here
for m in tune scores uci_info tt; do cat "src/search/$m.inc"; done >> "$TMP/new.cpp"
cat src/search/movepicker.hpp >> "$TMP/new.cpp"
for m in worker evaluation; do cat "src/search/$m.inc" >> "$TMP/new.cpp"; done
cat src/search/timeman.hpp >> "$TMP/new.cpp"
for m in checks history qsearch alphabeta iterative searcher; do cat "src/search/$m.inc" >> "$TMP/new.cpp"; done
norm() {
  sed -E 's#^\s*//.*$##; s#\s+# #g; s#^ ##; s# $##' "$1" |
    grep -vE '^$|^namespace |^} // namespace|^#include|^#pragma|^\{$|^}$' | sort
}
norm "$TMP/old.cpp" > "$TMP/old.sorted"
norm "$TMP/new.cpp" > "$TMP/new.sorted"
echo "== lines only in the lock search.cpp ($BASE), normalised:"
comm -23 "$TMP/old.sorted" "$TMP/new.sorted"
echo
echo "== lines only in the new src/search/ modules, normalised:"
comm -13 "$TMP/old.sorted" "$TMP/new.sorted"
echo
echo "== counts: lock lines $(wc -l < "$TMP/old.sorted"), new lines $(wc -l < "$TMP/new.sorted"), common $(comm -12 "$TMP/old.sorted" "$TMP/new.sorted" | wc -l)"
