#!/usr/bin/env bash
# plant_build.sh — builds a SCRATCH COPY of the engine with one planted fault behind input I control.
# Nothing from this copy is committed and the base worktree is untouched.
#
# The fault: an unlocked global counter written by every search thread (a real data race for TSAN), and,
# on a FEN of my choosing, a one-past-the-end heap read (for ASan) + a signed overflow (for UBSan),
# all behind the literal marker "plantfault" in the position's move list so no real input can trigger it.
set -u
SRC=/agent/repos/base/forge-combo29
DST=/agent/repos/scratch-planted
rm -rf "$DST"; mkdir -p "$DST"
cp -r "$SRC"/CMakeLists.txt "$SRC"/include "$SRC"/src "$DST"/
python3 - "$DST" <<'PY'
import sys, re
dst = sys.argv[1]
p = f"{dst}/src/uci.cpp"
s = open(p).read()
# hook: right after the "position" command is dispatched, check for the marker and fire the faults
anchor = '        } else if (command == "position") {'
assert anchor in s, "anchor not found"
hook = '''
        } else if (command == "plantfault") {
            // PLANTED FAULT (scratch copy only): heap over-read + signed overflow on demand.
            int* heap = new int[4];
            volatile int sink = heap[4];        // ASan: heap-buffer-overflow
            volatile int ovf = 2147483647;
            ovf = ovf + (int)sink;               // UBSan: signed integer overflow
            static int shared_counter = 0;      // TSAN: unsynchronised write from every thread
            shared_counter++;                    // no lock on purpose
            (void)ovf;
            delete[] heap;
            { const std::lock_guard<std::mutex> lk(forge::uci_output_mutex());
              std::cout << "info string planted fault" << std::endl; }
            continue;
'''
s = s.replace(anchor, hook + anchor, 1)
open(p, "w").write(s)
print("planted into", p)
PY
CXX=g++ CC=gcc cmake -S "$DST" -B "$DST/build" -DCMAKE_BUILD_TYPE=RelWithDebInfo -DCMAKE_CXX_COMPILER=g++ \
  -DCMAKE_CXX_FLAGS="-fsanitize=address,undefined -fno-omit-frame-pointer -g" \
  -DCMAKE_EXE_LINKER_FLAGS="-fsanitize=address,undefined" > "$DST/cmake.log" 2>&1
cmake --build "$DST/build" -j4 > "$DST/build.log" 2>&1
echo "build exit=$?"
ls -la "$DST/build/forge"
echo "asan syms: $(nm -C "$DST/build/forge" | grep -c __asan_)"
