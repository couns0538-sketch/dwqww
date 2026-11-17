#!/usr/bin/env bash
# Build one engine per planted UB class and confirm the workload's sanitizer
# detector reports each. Also runs the control (unplanted build, same runner).
set -uo pipefail
cd /tmp/forge
FLAGS="-fsanitize=undefined,address -fno-sanitize-recover=all -fno-omit-frame-pointer -g"
export LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13

rm -rf plants && mkdir -p plants
mkdir -p ev/plants

echo "plant,where,built,caught,error_class,sanitizer_line" > ev/plants/summary.csv

for n in 1 2 3 4 5 6 7 8 9 10 11 12; do
  tree="plants/p$n"
  rm -rf "$tree" && mkdir -p "$tree"
  cp -r eng/src eng/include eng/CMakeLists.txt "$tree/"
  python3 inject_plants.py "$tree" "$n" >/dev/null || { echo "$n,?,NO,NO,inject-failed," >> ev/plants/summary.csv; continue; }
  if ! cmake -S "$tree" -B "build-p$n" -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_CXX_COMPILER=/usr/bin/g++ -DFORGE_MARCH=x86-64-v4 \
        -DCMAKE_CXX_FLAGS="$FLAGS" -DCMAKE_EXE_LINKER_FLAGS="-fsanitize=undefined,address" \
        > "ev/plants/cmake-p$n.log" 2>&1 || \
     ! cmake --build "build-p$n" -j4 > "ev/plants/build-p$n.log" 2>&1; then
    echo "$n,?,NO,NO,build-failed," >> ev/plants/summary.csv
    continue
  fi
  nsym=$(nm build-p$n/forge | grep -c __ubsan_)
  timeout 900 python3 workload.py "/tmp/forge/build-p$n/forge" "ev/plants/p$n" --plant-check \
      > "ev/plants/run-p$n.log" 2>&1
  python3 - "$n" "ev/plants/p$n/workload.json" >> ev/plants/summary.csv <<'EOF'
import json, sys
n, path = sys.argv[1], sys.argv[2]
d = json.load(open(path))
lines = d["sanitizer_lines"]
first = lines[0] if lines else ""
cls = ""
if "runtime error: " in first:
    cls = first.split("runtime error: ", 1)[1].split(":")[0]
elif "AddressSanitizer" in first:
    cls = "AddressSanitizer"
print(f"{n},?,YES,{'YES' if lines else 'NO'},{cls},{first}")
EOF
  echo "plant $n done ($nsym ubsan syms)"
done

# control: the unplanted sanitizer build through the identical runner
echo "-- control: unplanted build --"
timeout 900 python3 workload.py /tmp/forge/build-ubsan/forge ev/plants/control --plant-check \
    > ev/plants/run-control.log 2>&1
python3 - >> ev/plants/summary.csv <<'EOF'
import json
d = json.load(open("ev/plants/control/workload.json"))
print(f"0(control),none,YES,{'YES' if d['sanitizer_lines'] else 'NO'},{''},{d['sanitizer_lines'][0] if d['sanitizer_lines'] else ''}")
EOF
cat ev/plants/summary.csv
