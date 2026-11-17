#!/usr/bin/env bash
# Build the ThreadSanitizer engine and run every race case at Threads 4.
#
#   build_and_run.sh <forge-combo29 tree> [build-dir] [evidence-dir]
#
# This script measures NO TIME. TSan slows execution 5-20x and serialises some
# operations, so every wall-clock number from it is a property of the
# instrument. Only race reports are collected.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="${1:?usage: build_and_run.sh <forge-combo29 tree> [build-dir] [evidence-dir]}"
WORK="${2:-$(mktemp -d)}"
OUT="${3:-$HERE/../evidence}"

GXX=/usr/bin/g++
GCC_LIB=/usr/lib/gcc/x86_64-linux-gnu/13
# -g embeds the source AND build directory into the binary, so without the two
# prefix maps the sha256 changes with the checkout path and cannot be quoted as
# a property of the source. With them the build is byte-reproducible.
SAN="-fsanitize=thread -fno-omit-frame-pointer -g"
TSAN_ENV='halt_on_error=0 history_size=4'

build_tsan() {   # build_tsan <source tree> <build dir>
  local s=$1 b=$2
  mkdir -p "$b"
  cmake -S "$s" -B "$b" \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_CXX_COMPILER="$GXX" \
    -DFORGE_MARCH=x86-64-v4 \
    -DCMAKE_CXX_FLAGS="$SAN -ffile-prefix-map=$s=/src -ffile-prefix-map=$b=/build" \
    -DCMAKE_EXE_LINKER_FLAGS="-fsanitize=thread" >/dev/null
  LIBRARY_PATH="$GCC_LIB" cmake --build "$b" -j"$(nproc)" >/dev/null
}

echo "== compiler =="
"$GXX" --version | head -1
cmake --version | head -1
python3 -V

ENGINE_BUILD="$WORK/build-engine"
echo "== configure + build (TSan) =="
build_tsan "$SRC" "$ENGINE_BUILD"

echo "== exact flag line =="
grep -m1 '^CXX_FLAGS' "$ENGINE_BUILD/CMakeFiles/forge.dir/flags.make"
cat "$ENGINE_BUILD/CMakeFiles/forge.dir/link.txt"

echo "== proof the binary is instrumented =="
ldd "$ENGINE_BUILD/forge" | grep -i tsan || { echo "NOT LINKED AGAINST libtsan" >&2; exit 1; }
echo "undefined __tsan symbols: $(nm -u "$ENGINE_BUILD/forge" | grep -c tsan)"

echo "== binary sha256 =="
sha256sum "$ENGINE_BUILD/forge"

echo "== honesty pins under TSan (node counts are unaffected by the sanitizer) =="
for n in 11 13 16; do printf 'bench %s\nquit\n' "$n" | "$ENGINE_BUILD/forge" | grep 'bench depth'; done
printf 'position startpos\ngo perft 5\nquit\n' | "$ENGINE_BUILD/forge" | tail -1

mkdir -p "$OUT"

# The scripts refuse to write outside an allowed root. The build workspace is a
# temp dir the caller chose, so it is granted explicitly rather than by turning
# the check off. Anything not listed here is still refused.
export FORGE_AUDIT_ROOT="$HERE/..:$WORK"

echo "== path-guard self-test (must pass before any path is used) =="
python3 "$HERE/pathsafe.py" | tee "$OUT/pathsafe_selftest.log" | tail -1

echo "== driver self-tests (both must pass before the run is trusted) =="
python3 "$HERE/drain_selftest.py" | tee "$OUT/drain_selftest.log"
FORGE_EXE="$ENGINE_BUILD/forge" python3 "$HERE/exit_observation.py" "$OUT/exit_observation.json" \
  | tee "$OUT/exit_observation.log"

echo "== corpus =="
python3 "$HERE/build_corpus.py" "$ENGINE_BUILD/forge" "$WORK/corpus40.json" "$SRC/soak_all/search_corpus.txt"

echo "== planted-race self-test: build and confirm a race IS reported =="
python3 "$HERE/plant_selftest.py" "$SRC" "$WORK/planted-b" B
build_tsan "$WORK/planted-b" "$WORK/build-planted-b"
sha256sum "$WORK/build-planted-b/forge"
TSAN_OPTIONS="$TSAN_ENV" python3 - "$WORK/build-planted-b/forge" <<'PY' | tee "$OUT/planted_b_check.log"
import sys
sys.path.insert(0, __import__("os").environ["HERE"])
from tsan_driver import Engine, races
e = Engine(sys.argv[1])
e.cmd("setoption name Threads value 4"); e.sync()
e.cmd("ucinewgame"); e.cmd("position startpos")
bm, info = e.go("go depth 12", 600)
log = e.close()
r = races(log)
print("planted build: bestmove %s, race reports %d, exit %s, drained %s"
      % (bm, len(r), getattr(e, "exit_code", None), getattr(e, "drained_to_eof", None)))
if not r:
    print("PLANT_NOT_DETECTED -- the clean run below would be worthless")
    sys.exit(1)
for x in r[:1]:
    print(x["summary"])
print("PLANT_DETECTED")
PY

echo "== the run =="
TSAN_OPTIONS="$TSAN_ENV" python3 "$HERE/tsan_run.py" "$ENGINE_BUILD/forge" \
  --corpus "$WORK/corpus40.json" \
  --out "$OUT/tsan_run.json" --cases ABCDEFGH --timeout 900

echo "== done =="
python3 - "$OUT/tsan_run.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
runs = sum(len(c["runs"]) for c in d["cases"])
print("cases %d | searches %d | race reports %d"
      % (len(d["cases"]), runs, d["race_count"]))
PY
