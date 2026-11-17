#!/bin/sh
# planted_fault.sh SRC_TREE OUTLOG — proves the ASan+UBSan build really has the
# sanitizer armed on the NEW code. Plants a heap overflow inside has_mating_move
# (the function this patch adds), builds ASan+UBSan, runs the band fixture that
# calls it, and requires a sanitizer report NAMING that function.
set -e
src="$1"; log="$2"
rm -rf "$src.planted"; cp -r "$src" "$src.planted"
python3 - "$src.planted/src/search.cpp" <<'PY'
import sys
p = sys.argv[1]; s = open(p).read()
anchor = "bool Worker::has_mating_move(Board& board) const {"
assert anchor in s, "has_mating_move not found: is the patch applied?"
bait = anchor + "\n    { volatile int* planted = new int[4]; planted[7] = 1; delete[] planted; }"
open(p, "w").write(s.replace(anchor, bait, 1))
print("planted a 4-int heap buffer overflow at index 7 in has_mating_move")
PY
build="$src.planted.build"
LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13 cmake -S "$src.planted" -B "$build" \
  -DCMAKE_BUILD_TYPE=RelWithDebInfo -DCMAKE_CXX_COMPILER=/usr/bin/g++ \
  -DCMAKE_CXX_FLAGS="-fsanitize=address,undefined -fno-omit-frame-pointer" \
  -DCMAKE_EXE_LINKER_FLAGS="-fsanitize=address,undefined" >/dev/null 2>&1
LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13 make -C "$build" -j4 >/dev/null 2>&1
{
  printf 'uci\nisready\nsetoption name Threads value 1\nsetoption name Hash value 16\n'
  printf 'position fen 6k1/8/5PPP/8/8/8/8/R6K b - - 99 40\ngo depth 8\n'
  sleep 2; printf 'quit\n'
} | "$build/forge" 2>&1 | grep -E 'AddressSanitizer|runtime error|ERROR' > "$log" || true
echo "--- sanitizer report ($log):"
cat "$log"
test -s "$log" || { echo "FAIL: no sanitizer report — the sanitizer did not run"; exit 1; }
grep -q 'has_mating_move' "$log" || { echo "FAIL: report does not name has_mating_move"; exit 1; }
echo "PASS: sanitizer fired inside the function this patch adds"
