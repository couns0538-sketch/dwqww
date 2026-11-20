#!/usr/bin/env bash
# ASan+UBSan build of ../work, then the same runner on the first 100 of G.
# A scratch copy with one heap read past the end is built the same way and
# run through measure_set.py on one special FEN.
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
OUT="forge-combo29/grok/$S"
SRC=/agent/repos/work/forge-combo29
BUILD=/tmp/forge_asan/build
export ASAN_OPTIONS=detect_leaks=0:halt_on_error=1:abort_on_error=0
export UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1

rm -rf /tmp/forge_asan
cmake -S "$SRC" -B "$BUILD" -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++ \
  -DCMAKE_CXX_FLAGS="-fsanitize=address,undefined -fno-omit-frame-pointer" \
  -DCMAKE_EXE_LINKER_FLAGS="-fsanitize=address,undefined"
cmake --build "$BUILD" -j4
EXE="$BUILD/forge"
NM=$(nm -C "$EXE" | grep -c __asan_ || true)
echo "$NM" > "$OUT/asan_nm_count.txt"
head -n 100 "$OUT/G.epd" > "$OUT/G100.epd"
python3 "$OUT/measure_set.py" "$EXE" "$OUT/G100.epd" 10 "$OUT/P_asan_G100_d10.txt" IdeaA6 true
echo "nm_asan_symbol_count $NM" >> "$OUT/P_asan_G100_d10.txt.meta"
echo "ASAN_OPTIONS $ASAN_OPTIONS" >> "$OUT/P_asan_G100_d10.txt.meta"
echo "clean_asan_lines $(grep -c -E 'ERROR: AddressSanitizer|ERROR: UndefinedBehaviorSanitizer|runtime error:' "$OUT/P_asan_G100_d10.txt" || true)" >> "$OUT/P_asan_G100_d10.txt.meta"

# Scratch: one deliberate read past a heap array, only when the runner sends this FEN.
rm -rf /tmp/forge_scratch
mkdir -p /tmp/forge_scratch
cp -a "$SRC" /tmp/forge_scratch/forge-combo29
rm -rf /tmp/forge_scratch/forge-combo29/build /tmp/forge_scratch/forge-combo29/build-asan
python3 - << 'PY'
from pathlib import Path
path = Path("/tmp/forge_scratch/forge-combo29/src/uci.cpp")
text = path.read_text()
old = '''        if (!candidate.set_fen(fen, &error)) {
            { const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex()); std::cout << "info string invalid FEN: " << error << std::endl; }
            return;
        }'''
new = old + '''
        if (fen == "8/8/8/8/8/8/8/K6k w - - 0 1") {
            int* heap = new int[4];
            volatile int past_end = heap[4];
            (void)past_end;
            delete[] heap;
        }'''
if old not in text:
    raise SystemExit("scratch insertion point missing")
path.write_text(text.replace(old, new, 1))
PY
cmake -S /tmp/forge_scratch/forge-combo29 -B /tmp/forge_scratch/build -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++ \
  -DCMAKE_CXX_FLAGS="-fsanitize=address,undefined -fno-omit-frame-pointer" \
  -DCMAKE_EXE_LINKER_FLAGS="-fsanitize=address,undefined"
cmake --build /tmp/forge_scratch/build -j4
printf '%s\n' "8/8/8/8/8/8/8/K6k w - - 0 1" > "$OUT/special.fen"
set +e
python3 "$OUT/measure_set.py" /tmp/forge_scratch/build/forge "$OUT/special.fen" 10 "$OUT/P_asan_scratch.txt" IdeaA6 true
SCRATCH_EXIT=$?
set -e
echo "scratch_runner_exit $SCRATCH_EXIT" >> "$OUT/P_asan_scratch.txt.meta" 2>/dev/null || true
{
  echo "exe /tmp/forge_scratch/build/forge"
  echo "sha256 $(sha256sum /tmp/forge_scratch/build/forge | awk '{print $1}')"
  echo "nm_asan_symbol_count $(nm -C /tmp/forge_scratch/build/forge | grep -c __asan_ || true)"
  echo "scratch_runner_exit $SCRATCH_EXIT"
  echo "command: measure_set.py special.fen depth 10 IdeaA6 true"
} >> "$OUT/P_asan_scratch.txt.meta"
echo "scratch_asan_lines $(grep -c -E 'ERROR: AddressSanitizer|heap-buffer-overflow' "$OUT/P_asan_scratch.txt" || true)"
