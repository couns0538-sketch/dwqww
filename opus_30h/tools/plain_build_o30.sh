#!/usr/bin/env bash
# plain_build_r15.sh <scratch repo> <out dir> [extra g++ flags] - clean export + the lock's direct g++ line (the kit's
# plain step, -DFORGE_EXPOSE_TUNABLES=1 as in kit -Expose) on CPUs 0-1 at Idle via lowrun.ps1. Quick node checks only:
# gate exes always come from the kit (kit_build_r15.sh / cand_pack.ps1). Prints warnings, exe sha256, vfmadd count.
# R15 copy of opus-r13-p1-nearmiss-ports:opus_r13/tools/plain_build.sh (mask 0x3, Idle, lowrun.ps1, TMP on D:\o30).
set -euo pipefail
repo="$1"; out="$2"; shift 2; T=$(cd "$(dirname "$0")" && pwd)
[ -e "$out" ] && { echo "refusing: $out exists" >&2; exit 2; }
export TMP='D:\o30\tmp' TEMP='D:\o30\tmp'
# g++ started by an absolute path still needs its own bin folder on PATH (cc1plus / as / ld DLLs): without it it
# exits 1 with no message at all (seen 2026-11-03 11:41).
export PATH="/c/msys64/ucrt64/bin:$PATH"
bash "$T/export_src.sh" "$repo" "$out/src" >/dev/null
cd "$out/src"
units=$(ls src/*.cpp | sort | tr '\n' ' ')
args="-std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -march=znver5 -static -pthread -DFORGE_EXPOSE_TUNABLES=1 $* -Iinclude $units -o ../forge_plain.exe"
powershell -NoProfile -ExecutionPolicy Bypass -File "$(cygpath -w "$T/lowrun.ps1")" -Mask "${PLAIN_MASK:-0x3}" -Priority Idle -Exe 'C:\msys64\ucrt64\bin\g++.exe' -ArgLine "$args" > ../build.log 2>&1 || { tail -20 ../build.log; exit 1; }
cd .. && echo "warnings: $(grep -c 'warning:' build.log || true)" && sha256sum forge_plain.exe && echo "vfmadd: $(/c/msys64/ucrt64/bin/objdump -d forge_plain.exe | grep -c vfmadd || true)"
