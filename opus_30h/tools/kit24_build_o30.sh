#!/usr/bin/env bash
# kit24_build_o30.sh <scratch repo> <tag> [checkopt ...] - kit v2.4 (R12) with -Workload v1 (= v2.3 frozen workload) + -PartialTraining.
# Copy of opus-r13-p2-sparse-l1:opus_r13/p2/speed2/kit_build_r14.sh with: work dir D:\o30\w, clean exports under
# D:\o30\src, CPUs 0-1 (kit -Affinity 0x3; the kit sets BelowNormal on itself), TMP/TEMP = D:\o30\tmp, and the FIXED
# pc_gate (R14-B copy: unreadable CPU counters fail the gate). Sides from KIT_SIDES (default "pc1 pc2"); OFF pins +
# perft pins always; one -CheckOpt per extra argument ('Name=Value;Name2=Value2' = one line).
# Binding check for two sides: pc1 exe sha256 == pc2 exe sha256. Exit: 0 ok, 2 export, 4 pc1 != pc2, 75 load gate
# not OK for 60 min, 76 D: or C: below the floor, other = the kit's exit code.
set -uo pipefail
repo="$1"; tag="$2"; shift 2
T=$(cd "$(dirname "$0")" && pwd)
KIT='D:\o30\kit\opus_r12\kit_v24\build_ltopgo.ps1'
PY='C:\Users\Administrator\grok-pc\nnue\.venv\Scripts\python.exe'
export TMP='D:\o30\tmp' TEMP='D:\o30\tmp'
opts=""; for o in "$@"; do opts="$opts${opts:+,}'$o'"; done
sides="${KIT_SIDES:-pc1 pc2}"
mkdir -p /d/o30/w /d/o30/src /d/o30/tmp
for side in $sides; do
  # hard floors first (R15: stop below D: 50 GB / C: 30 GB), then the load gate in 60 s steps (up to 60 min):
  # CPUs 0-1 <= 60 % busy, total <= 97 %, RAM >= 6 GB, D: >= 51 GB
  dfree=$(df -BG /d | awk 'NR==2 {gsub("G","",$4); print $4}'); cfree=$(df -BG /c | awk 'NR==2 {gsub("G","",$4); print $4}')
  if [ "${dfree:-0}" -lt 50 ] || [ "${cfree:-0}" -lt 30 ]; then echo "STOP: D: ${dfree} GB / C: ${cfree} GB below the R15 floor"; exit 76; fi
  ok=0; for i in $(seq 1 60); do
    if powershell -NoProfile -ExecutionPolicy Bypass -File "$(cygpath -w "$T/pc_gate.ps1")" -Drive D -NeedGB 1 -MaxCpu 97 -Cpus 0,1 -MaxMyCpu ${KIT_MAXMYCPU:-60}; then ok=1; break; fi
    sleep 60
  done
  [ $ok = 1 ] || { echo "pc_gate not OK for 60 min, stop"; exit 75; }
  src=/d/o30/src/${tag}_$side; bash "$T/export_src.sh" "$repo" "$src" >/dev/null || exit 2
  cmd="& '$KIT' -SrcDir '$(cygpath -w "$src")' -Tag '${tag}_$side' -Work 'D:\o30\w' -Affinity 0x3 -Python '$PY' -Expose -PartialTraining"
  cmd="$cmd -Pins 'd11=312866,d13=862329,d16=3024920,d20=12389307,d22=34048354' -PerftPins 'startpos=4865609,kiwipete=193690690'"
  [ -n "$opts" ] && cmd="$cmd -CheckOpt $opts"
  echo "$(date '+%F %T') kit $tag $side: $cmd"
  powershell -NoProfile -ExecutionPolicy Bypass -Command "$cmd; exit \$LASTEXITCODE" > /d/o30/w/${tag}_$side.out 2>&1
  rc=$?; echo "$(date '+%F %T') $side exit $rc: $(grep -a 'RESULT' /d/o30/w/${tag}_$side.out | tail -1)"
  [ $rc = 0 ] || exit $rc
done
for side in $sides; do echo "$side $(sha256sum /d/o30/w/${tag}_$side/src_copy/forge_ltopgo_${tag}_$side.exe | cut -c1-64)"; done
if [ "$sides" = "pc1 pc2" ]; then
  a=$(sha256sum /d/o30/w/${tag}_pc1/src_copy/forge_ltopgo_${tag}_pc1.exe | cut -c1-64)
  b=$(sha256sum /d/o30/w/${tag}_pc2/src_copy/forge_ltopgo_${tag}_pc2.exe | cut -c1-64)
  [ "$a" = "$b" ] && echo "PC1 = PC2: PASS" || { echo "PC1 != PC2: FAIL"; exit 4; }
fi
