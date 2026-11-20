#!/usr/bin/env bash
# Scratch engine: one deliberate heap read past the end, on one FEN, same runner.
set -euo pipefail
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
DIR="forge-combo29/grok/$S"
SRC=/tmp/scratch-forge
rm -rf "$SRC"
mkdir -p "$SRC"
# Sources only. Build trees stay out of the scratch copy.
tar -C /agent/repos/work/forge-combo29 --exclude build-release --exclude build-asan -cf - . | tar -C "$SRC" -xf -
python3 - "$SRC/src/uci.cpp" << 'PY'
import sys
path = sys.argv[1]
text = open(path).read()
old = '''        if (!candidate.set_fen(fen, &error)) {
            { const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex()); std::cout << "info string invalid FEN: " << error << std::endl; }
            return;
        }
'''
new = '''        if (!candidate.set_fen(fen, &error)) {
            { const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex()); std::cout << "info string invalid FEN: " << error << std::endl; }
            return;
        }
        if (fen == "4k3/8/8/8/8/8/8/4K3 w - - 0 1") {
            int* heap = new int[4];
            volatile int sink = heap[8];
            (void)sink;
            delete[] heap;
        }
'''
if old not in text:
    raise SystemExit("anchor not found")
open(path, "w").write(text.replace(old, new, 1))
PY
cmake -S "$SRC" -B "$SRC/build-asan" -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++ \
  -DCMAKE_CXX_FLAGS="-fsanitize=address,undefined -fno-omit-frame-pointer" \
  -DCMAKE_EXE_LINKER_FLAGS="-fsanitize=address,undefined"
cmake --build "$SRC/build-asan" -j 4
EXE="$SRC/build-asan/forge"
nm -C "$EXE" | grep -c __asan_ > "$DIR/asan_scratch_nm_count.txt"
echo "4k3/8/8/8/8/8/8/4K3 w - - 0 1" > "$DIR/asan_scratch.fen"
set +e
python3 "$DIR/harness_depth.py" "$EXE" "$DIR/asan_scratch.fen" 4 asan_scratch "$DIR" IdeaK9 true
code=$?
set -e
echo "runner_exit=$code" > "$DIR/asan_scratch_result.txt"
grep -n -E 'AddressSanitizer|UndefinedBehaviorSanitizer|runtime error:' "$DIR/asan_scratch.raw.txt" >> "$DIR/asan_scratch_result.txt" || true
echo "----- scratch result -----"
cat "$DIR/asan_scratch_result.txt"
