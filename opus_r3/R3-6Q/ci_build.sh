#!/usr/bin/env bash
# R3-6Q: release build of the forge target with the box recipe of opus_round1/ci/run_ci.sh (g++-14, CMake
# Release, Ninja, x86-64-v3, no FMA contraction), identity record, uci_check quick (must print ALL OK) and
# the four SMP options in the `uci` option list.
# usage: ci_build.sh <build_dir> <log_dir>
set -euo pipefail
BD=$1; LOG=$2
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
CXX=${CXX:-$(command -v g++-14 || command -v g++)}
FLAGS="-march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256"
mkdir -p "$LOG"
cmake -S "$ROOT" -B "$BD" -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER="$CXX" \
  "-DCMAKE_CXX_FLAGS=$FLAGS" > "$LOG/configure.log" 2>&1
cmake --build "$BD" --target forge -j"$(nproc)" > "$LOG/build.log" 2>&1 || { tail -50 "$LOG/build.log"; exit 1; }
{
  echo "commit: $(git -C "$ROOT" rev-parse HEAD 2>/dev/null || echo unknown)"
  echo "compiler: $($CXX --version | head -1)"
  echo "CMAKE_CXX_FLAGS: $FLAGS"
  echo "forge sha256: $(sha256sum "$BD/forge" | cut -d' ' -f1)"
  echo "FMA instructions (must be 0): $(objdump -d "$BD/forge" | grep -cE 'vfn?m(add|sub)' || true)"
} | tee "$LOG/identity.log"
python3 "$ROOT/opus_round1/ci/uci_check.py" "$BD/forge" | tee -a "$LOG/identity.log"
grep -q '^ALL OK' "$LOG/identity.log"
(printf 'uci\n'; sleep 1; printf 'quit\n') | "$BD/forge" > "$LOG/uci_options.txt"
n=$(grep -cE 'option name (SmpHelpersPastDepth|SmpExactNodes|SmpBestThread|LocklessTT) ' "$LOG/uci_options.txt" || true)
echo "SMP options listed by uci: $n of 4" | tee -a "$LOG/identity.log"
[ "$n" -eq 4 ]
