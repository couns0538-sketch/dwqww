#!/usr/bin/env bash
# Kit builds of the final candidate e011a3e (= 89cddf7 + three comment lines): OFF must be 4181a589, GATE must be
# 2940fb05 (the exes qualified in BENCH 11). Fresh tags m0c / m1c (k0c / k1c failed before compiling: a quoting slip in
# an inline command left the literal '$src' in the source path; their folders keep the kit's FAILED marker).
set -u
cd /d/forge_jobs_20261107/opus2/out || exit 1
T='D:\forge_jobs_20261107\opus2\repo\opus_smp_layout\tools'
ps1() { MSYS_NO_PATHCONV=1 powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$@"; }
ps1 "$T\\kit_build.ps1" -SrcDir 'D:\forge_jobs_20261107\opus2\out\src\k0' -Tag m0c > logs/kit_m0c.log 2>&1
echo "kit m0c exit=$? | $(grep -o 'RESULT [A-Z]*' logs/kit_m0c.log | tail -1) | $(grep -o 'NODE IDENTITY: [A-Z ]*' logs/kit_m0c.log | tail -1) | $(sha256sum k/m0c/src_copy/forge_ltopgo_m0c.exe | cut -c1-64)"
ps1 "$T\\kit_build.ps1" -SrcDir 'D:\forge_jobs_20261107\opus2\out\src\k1' -Tag m1c -CheckOpt 'TtLockless=true' > logs/kit_m1c.log 2>&1
echo "kit m1c exit=$? | $(grep -o 'RESULT [A-Z]*' logs/kit_m1c.log | tail -1) | $(grep -o 'NODE IDENTITY: [A-Z ]*' logs/kit_m1c.log | tail -1) | $(sha256sum k/m1c/src_copy/forge_ltopgo_m1c.exe | cut -c1-64)"
echo KIT_FINAL_DONE
