#!/usr/bin/env bash
# kit_build_r14.sh <scratch repo> <tag> [checkopt ...] - R13's kit_build.sh (opus-r13-p1-nearmiss-ports opus_r13/tools) with
# the R14 scratch rule: work dir D:\o14a\w, clean exports under D:\o14a\src, disk gate on D: (>= 50 GB + 1). QA's LTO+PGO
# kit v2.3 (-Expose) per side (KIT_SIDES, default "pc1 pc2"), CPUs 2-3 (0xC) BelowNormal, OFF pins + perft pins, one
# -CheckOpt per argument; binding check for two sides: pc1 exe sha256 == pc2 exe sha256.
set -uo pipefail
repo="$1"; tag="$2"; shift 2
T=/d/grok-pc-data/dwqww/.claude/worktrees/o13-p1/opus_r13/tools
KIT='C:\Users\Administrator\grok-pc\forge_push\qa_ltopgo_al1_stage\kit_v23\build_ltopgo.ps1'
PY='C:\Users\Administrator\grok-pc\nnue\.venv\Scripts\python.exe'
opts=""; for o in "$@"; do opts="$opts${opts:+,}'$o'"; done
sides="${KIT_SIDES:-pc1 pc2}"
mkdir -p /d/o14a/w /d/o14a/src
for side in $sides; do
  # load gate: wait in 60 s steps (up to 60 min); CPUs 2-3 <= 60 % busy, total <= 95 %, RAM >= 6 GB, D: >= 51 GB
  ok=0; for i in $(seq 1 60); do
    if powershell -NoProfile -ExecutionPolicy Bypass -File "$(cygpath -w "$T/pc_gate.ps1")" -Drive D -NeedGB 1 -MaxCpu 95 -Cpus 2,3 -MaxMyCpu 60; then ok=1; break; fi
    sleep 60
  done
  [ $ok = 1 ] || { echo "pc_gate not OK for 60 min, stop"; exit 75; }
  src=/d/o14a/src/${tag}_$side; bash "$T/export_src.sh" "$repo" "$src" >/dev/null || exit 2
  cmd="& '$KIT' -SrcDir '$(cygpath -w "$src")' -Tag '${tag}_$side' -Work 'D:\o14a\w' -Affinity 0xC -Python '$PY' -Expose"
  cmd="$cmd -Pins 'd11=312866,d13=862329,d16=3024920,d20=12389307,d22=34048354' -PerftPins 'startpos=4865609,kiwipete=193690690'"
  [ -n "$opts" ] && cmd="$cmd -CheckOpt $opts"
  echo "$(date '+%F %T') kit $tag $side: $cmd"
  powershell -NoProfile -ExecutionPolicy Bypass -Command "$cmd; exit \$LASTEXITCODE" > /d/o14a/w/${tag}_$side.out 2>&1
  rc=$?; echo "$(date '+%F %T') $side exit $rc: $(grep -a 'RESULT' /d/o14a/w/${tag}_$side.out | tail -1)"
  [ $rc = 0 ] || exit $rc
done
for side in $sides; do echo "$side $(sha256sum /d/o14a/w/${tag}_$side/src_copy/forge_ltopgo_${tag}_$side.exe | cut -c1-64)"; done
if [ "$sides" = "pc1 pc2" ]; then
  a=$(sha256sum /d/o14a/w/${tag}_pc1/src_copy/forge_ltopgo_${tag}_pc1.exe | cut -c1-64)
  b=$(sha256sum /d/o14a/w/${tag}_pc2/src_copy/forge_ltopgo_${tag}_pc2.exe | cut -c1-64)
  [ "$a" = "$b" ] && echo "PC1 = PC2: PASS" || { echo "PC1 != PC2: FAIL"; exit 4; }
fi
