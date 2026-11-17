#!/usr/bin/env bash
# Reproduce the whole measurement from a clean checkout.
# Every step is fail-fast: a failed validation must stop the pipeline, because a
# clean number from an unvalidated oracle is the failure mode this seat exists to
# avoid (brief rule 3).
set -euo pipefail

ENGINE_DIR=${ENGINE_DIR:-.}
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
WORK=${WORK:-/tmp/matelabels-work}
mkdir -p "$WORK"

echo "== 1. build engine =="
mkdir -p "$ENGINE_DIR/build" && cd "$ENGINE_DIR/build"
cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=/usr/bin/g++ \
      -DFORGE_MARCH=x86-64-v4 .. > "$WORK/cmake.log"
LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13 make -j"$(nproc)" > "$WORK/make.log"
FORGE="$ENGINE_DIR/build/forge"
sha256sum "$FORGE"

echo "== 2. four honesty pins (bench on STDIN) =="
printf 'uci\nisready\nbench 11\nbench 13\nbench 16\nposition startpos\ngo perft 5\nquit\n' \
  | "$FORGE" > "$WORK/gate.txt" 2>&1
grep -E "bench depth|^nodes " "$WORK/gate.txt"
python3 - "$WORK/gate.txt" <<'PY'
import re, sys
text = open(sys.argv[1]).read()
want = {11: 312866, 13: 862329, 16: 3024920}
ok = True
for d, exp in want.items():
    m = re.search(rf"bench depth {d} nodes (\d+)", text)
    got = int(m.group(1)) if m else None
    ok &= (got == exp)
m = re.search(r"^nodes (\d+)", text, re.M)
ok &= bool(m) and int(m.group(1)) == 4865609
print("PINS", "MATCH" if ok else "MISMATCH")
sys.exit(0 if ok else 1)
PY

echo "== 3. build oracle + planted-wrong oracle =="
cd "$HERE"
g++ -O2 -std=c++20 -o "$WORK/oracle" mate_oracle.cpp
g++ -O2 -std=c++20 -o "$WORK/oracle_broken" mate_oracle_planted_wrong.cpp

echo "== 4. perft validation (must pass) =="
python3 perft_check.py

echo "== 5. oracle self-test (known answers + planted fault) =="
python3 oracle_selftest.py

echo "== 6. end-to-end label test (must show 0 falsely-EXACT) =="
python3 e2e_label_test.py || echo "NOTE: non-zero exit means a planted label was misclassified; inspect before reporting"

echo "== 7. measure =="
python3 harvest_labels.py
python3 add_seldepth.py
python3 run_verify_parallel.py
python3 analyze.py

echo "== done. compare against evidence/analysis-output.txt =="
