#!/usr/bin/env bash
# Planted-fault sweep, run through the SAME phased harness as the real sweep
# (workload2.py), so the detector that reports "clean" on the real build is the
# exact detector that reports "dirty" on each planted build.
#
# For each plant class: build, confirm the sanitizer symbols are present, run,
# and record the caught line verbatim. The control is the unplanted build
# through the identical command.
set -uo pipefail
cd /tmp/forge
export LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13
SAN="-fsanitize=undefined,address -fno-sanitize-recover=all -fno-omit-frame-pointer -g"
PHASES="pins,eval,protocol,book"

rm -rf plants2 ev/plants2
mkdir -p plants2 ev/plants2
: > ev/plants2/summary.tsv

for n in $(seq 1 12); do
  tree="plants2/p$n"
  rm -rf "$tree" && mkdir -p "$tree"
  cp -r eng/src eng/include eng/CMakeLists.txt "$tree/"
  python3 inject_plants.py "$tree" "$n" >/dev/null || { printf '%s\tINJECT_FAIL\n' "$n" >> ev/plants2/summary.tsv; continue; }
  if ! cmake -S "$tree" -B "build2-p$n" -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_CXX_COMPILER=/usr/bin/g++ -DFORGE_MARCH=x86-64-v4 \
        -DCMAKE_CXX_FLAGS="$SAN" -DCMAKE_EXE_LINKER_FLAGS="-fsanitize=undefined,address" \
        > "ev/plants2/cmake-p$n.log" 2>&1 || \
     ! cmake --build "build2-p$n" -j3 > "ev/plants2/build-p$n.log" 2>&1; then
    printf '%s\tBUILD_FAIL\n' "$n" >> ev/plants2/summary.tsv
    continue
  fi
  nsym=$(nm "build2-p$n/forge" | grep -c __ubsan_ || true)
  timeout 900 python3 workload2.py "/tmp/forge/build2-p$n/forge" "ev/plants2/p$n" \
      --quick --phases "$PHASES" > "ev/plants2/run-p$n.log" 2>&1
  python3 - "build2-p$n/forge" "ev/plants2/p$n/workload.json" >> ev/plants2/summary.tsv <<'PY'
import json, sys
exe, path = sys.argv[1], sys.argv[2]
d = json.load(open(path))
lines = []
for ph in d.get("phases", {}).values():
    lines += ph.get("sanitizer_lines", [])
    lines += ph.get("close", {}).get("at_exit_san_lines", [])
first = lines[0] if lines else ""
cls = ""
if "runtime error: " in first:
    cls = first.split("runtime error: ", 1)[1]
    if len(cls) > 110:
        cls = cls[:110]
print(f"caught\t{'YES' if lines else 'NO'}\t{first}\t{cls}")
PY
  echo "plant $n: $(grep -c YES ev/plants2/summary.tsv) caught so far / $nsym ubsan syms"
done

# control: unplanted build, identical harness and phase set
timeout 900 python3 workload2.py /tmp/forge/build-ubsan/forge ev/plants2/control \
    --quick --phases "$PHASES" > ev/plants2/run-control.log 2>&1
python3 - >> ev/plants2/summary.tsv <<'PY'
import json
d = json.load(open("ev/plants2/control/workload.json"))
lines = [l for ph in d["phases"].values() for l in ph["sanitizer_lines"]]
print(f"control\t{'YES' if lines else 'NO'}\t{lines[0] if lines else ''}\t")
PY
cat ev/plants2/summary.tsv
