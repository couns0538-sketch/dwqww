#!/usr/bin/env bash
# Build the repetition-ablated engine used by the Q5 A/B comparison.
#
# The patch forces Board::is_repetition() to false so that in-tree repetition
# detection is disabled while everything else (rule-50, insufficient material,
# search) is untouched. The result is written to /tmp/abtest/forge_norep and is
# NOT part of the shipped tree.
#
# Verified to be a real ablation: a root threefold then scores cp+589 instead
# of cp 0.
set -euo pipefail

root="$(cd "$(dirname "$0")/../.." && pwd)"
dest=/tmp/abtest
rm -rf "$dest"
mkdir -p "$dest"
cp -r "$root/src" "$root/include" "$dest/"

python3 - "$dest/src/board.cpp" <<'PY'
import sys

path = sys.argv[1]
source = open(path).read()
old = """bool Board::is_repetition() const {
    if (key_history_.size() < 5) return false;"""
new = """bool Board::is_repetition() const {
    if (true) return false;  // ABLATION: repetition detection disabled
    if (key_history_.size() < 5) return false;"""
if old not in source:
    raise SystemExit("ablation anchor not found in %s" % path)
open(path, "w").write(source.replace(old, new, 1))
print("patched %s" % path)
PY

g++ -std=c++20 -O2 -I"$dest/include" \
    "$dest/src/uci.cpp" "$dest/src/board.cpp" "$dest/src/search.cpp" \
    -o "$dest/forge_norep" -pthread
echo "built $dest/forge_norep"
