#!/usr/bin/env bash
# AddressSanitizer + UndefinedBehaviorSanitizer build of the idea, then the
# same runner on the first 100 of G at depth 10 with IdeaB1 true.
# A scratch copy with one heap read past the end on one FEN is built the same
# way and run through the same runner.
set -eu
S=$(cat ~/grok_seat.txt)
REPO=$(cat ~/grok_repo.txt)
DIR="$REPO/forge-combo29/grok/$S"
SRC="$REPO/../work/forge-combo29"
head -n 100 /tmp/positions/set_G.epd > "$DIR/G100.epd"
echo "=== asan build $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
cmake -S "$SRC" -B /tmp/forge-asan -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_CXX_COMPILER=g++ \
  -DCMAKE_CXX_FLAGS="-fsanitize=address,undefined -fno-omit-frame-pointer" \
  -DCMAKE_EXE_LINKER_FLAGS="-fsanitize=address,undefined" \
  -DCMAKE_TRY_COMPILE_TARGET_TYPE=STATIC_LIBRARY
cmake --build /tmp/forge-asan -j 4
nm -C /tmp/forge-asan/forge | grep -c __asan_ | tee "$DIR/asan_nm_count.txt"
python3 "$DIR/run_depth_set.py" /tmp/forge-asan/forge "$DIR/G100.epd" 10 true "$DIR/asan_G100_d10.txt"
{
  echo "nm_command=nm -C /tmp/forge-asan/forge | grep -c __asan_"
  echo "asan_symbol_count=$(cat "$DIR/asan_nm_count.txt")"
} >> "$DIR/asan_G100_d10.txt.meta"
echo "=== scratch $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
rm -rf /tmp/scratch-forge
mkdir -p /tmp/scratch-forge
cp -a "$SRC/CMakeLists.txt" "$SRC/src" "$SRC/include" /tmp/scratch-forge/
python3 - << 'PY'
from pathlib import Path
path = Path("/tmp/scratch-forge/src/uci.cpp")
text = path.read_text()
needle = """        if (!candidate.set_fen(fen, &error)) {
            { const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex()); std::cout << "info string invalid FEN: " << error << std::endl; }
            return;
        }
"""
insert = needle + """        if (fen == "8/8/8/8/8/8/8/K6k w - - 0 1") {
            int* scratch = new int[4];
            volatile int past = scratch[8];
            std::cout << "info string scratch " << past << std::endl;
            delete[] scratch;
        }
"""
if needle not in text:
    raise SystemExit("needle missing")
path.write_text(text.replace(needle, insert, 1))
print("inserted scratch read")
PY
cmake -S /tmp/scratch-forge -B /tmp/forge-asan-bug -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_CXX_COMPILER=g++ \
  -DCMAKE_CXX_FLAGS="-fsanitize=address,undefined -fno-omit-frame-pointer" \
  -DCMAKE_EXE_LINKER_FLAGS="-fsanitize=address,undefined" \
  -DCMAKE_TRY_COMPILE_TARGET_TYPE=STATIC_LIBRARY
cmake --build /tmp/forge-asan-bug -j 4
printf '%s\n' '8/8/8/8/8/8/8/K6k w - - 0 1' > "$DIR/asan_trigger.fen"
python3 "$DIR/run_depth_set.py" /tmp/forge-asan-bug/forge "$DIR/asan_trigger.fen" 10 true "$DIR/asan_trigger.txt" || echo "trigger runner exit $?"
echo "=== asan done $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
