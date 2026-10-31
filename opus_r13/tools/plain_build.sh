#!/usr/bin/env bash
# plain_build.sh <scratch repo> <out dir> [extra g++ flags] - clean export + the lock's direct g++ line (kit plain step,
# -DFORGE_EXPOSE_TUNABLES=1 added as in kit -Expose), on CPUs 2-3 at BelowNormal. Prints exe sha256 and vfmadd count.
set -euo pipefail
repo="$1"; out="$2"; shift 2; T=$(dirname "$0")
bash "$T/export_src.sh" "$repo" "$out/src" >/dev/null
cd "$out/src"
units=$(ls src/*.cpp | sort | tr '\n' ' ')
args="-std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -march=znver5 -static -pthread -DFORGE_EXPOSE_TUNABLES=1 $* -Iinclude $units -o ../forge_plain.exe"
powershell -NoProfile -ExecutionPolicy Bypass -File "$(cygpath -w "$T/run_low.ps1")" -Mask 0xC -Prio BelowNormal -Exe 'C:\msys64\ucrt64\bin\g++.exe' -ArgLine "$args" > ../build.log 2>&1 || { tail -20 ../build.log; exit 1; }
cd .. && echo "warnings: $(grep -c 'warning:' build.log || true)" && sha256sum forge_plain.exe && echo "vfmadd: $(/c/msys64/ucrt64/bin/objdump -d forge_plain.exe | grep -c vfmadd || true)"
