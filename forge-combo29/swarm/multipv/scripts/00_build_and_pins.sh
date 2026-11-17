#!/usr/bin/env bash
# Build forge-combo29 at the audit base commit and check the four honesty pins.
#   build: /usr/bin/c++ on this image is clang 18 with a broken header path, so the compiler
#          is pinned to /usr/bin/g++; LIBRARY_PATH is required or the link finds no libstdc++.
set -uo pipefail
root="${1:-.}"
cd "$root" || exit 2
pin_ok=1

cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=/usr/bin/g++ >/tmp/mp_cfg.log 2>&1 \
  || { echo "CONFIGURE FAILED"; tail -20 /tmp/mp_cfg.log; exit 2; }
LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13 cmake --build build -j"$(nproc)" >/tmp/mp_build.log 2>&1 \
  || { echo "BUILD FAILED"; tail -30 /tmp/mp_build.log; exit 2; }
echo "build ok: $(ls -l build/forge | awk '{print $5}') bytes  md5 $(md5sum build/forge | cut -d' ' -f1)"

bench() {  # depth -> nodes, fresh process, Threads 1, Hash 16
  printf 'uci\nsetoption name Threads value 1\nsetoption name Hash value 16\nsetoption name UseNNUE value %s\nbench %s\nquit\n' "$2" "$1" \
    | ./build/forge | awk '/info string bench depth/{for(i=1;i<=NF;i++) if($i=="nodes") printf "%s", $(i+1)}'
}

pins=0
for pair in "11:312866" "13:862329" "16:3024920"; do
  d="${pair%%:*}"; want="${pair##*:}"
  got=$(bench "$d" true)
  if [ "$got" = "$want" ]; then echo "PIN bench $d = $got  OK"; pins=$((pins+1));
  else echo "PIN bench $d = $got  WANT $want  MISMATCH"; pin_ok=0; fi
done

perft=$(printf 'uci\nsetoption name Threads value 1\nsetoption name Hash value 16\nposition startpos\ngo perft 5\n' | ./build/forge | awk '/^nodes /{print $2}' | tail -1)
if [ "$perft" = "4865609" ]; then echo "PIN perft 5 = $perft  OK"; pins=$((pins+1));
else echo "PIN perft 5 = $perft  WANT 4865609  MISMATCH"; pin_ok=0; fi

echo "pins: $pins/4"
[ "$pin_ok" = 1 ] && echo "PINS MATCH" || echo "PINS FAILED"
exit $((1-pin_ok))
