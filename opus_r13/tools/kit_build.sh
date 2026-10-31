#!/usr/bin/env bash
# kit_build.sh <scratch repo> <tag> [checkopt ...] - QA's LTO+PGO kit v2.3 (-Expose) twice (tags <tag>_pc1, <tag>_pc2),
# each from a fresh clean export, work dir C:\o13\w (short paths), CPUs 2-3 (0xC) BelowNormal, OFF pins + perft pins +
# one -CheckOpt per argument ('N=V' or 'N1=V1;N2=V2'). Then the binding check: pc1 exe sha256 == pc2 exe sha256.
set -uo pipefail
repo="$1"; tag="$2"; shift 2; T=$(dirname "$0")
KIT='C:\Users\Administrator\grok-pc\forge_push\qa_ltopgo_al1_stage\kit_v23\build_ltopgo.ps1'
PY='C:\Users\Administrator\grok-pc\nnue\.venv\Scripts\python.exe'
opts=""; for o in "$@"; do opts="$opts${opts:+,}'$o'"; done
for side in pc1 pc2; do
  powershell -NoProfile -ExecutionPolicy Bypass -File "$(cygpath -w "$T/pc_gate.ps1")" -Drive C -NeedGB 1 || { echo "pc_gate not OK, stop"; exit 75; }
  src=/c/o13/src/${tag}_$side; bash "$T/export_src.sh" "$repo" "$src" >/dev/null || exit 2
  cmd="& '$KIT' -SrcDir '$(cygpath -w "$src")' -Tag '${tag}_$side' -Work 'C:\o13\w' -Affinity 0xC -Python '$PY' -Expose"
  cmd="$cmd -Pins 'd11=312866,d13=862329,d16=3024920,d20=12389307,d22=34048354' -PerftPins 'startpos=4865609,kiwipete=193690690'"
  [ -n "$opts" ] && cmd="$cmd -CheckOpt $opts"
  echo "$(date '+%F %T') kit $tag $side: $cmd"
  powershell -NoProfile -ExecutionPolicy Bypass -Command "$cmd; exit \$LASTEXITCODE" > /c/o13/w/${tag}_$side.out 2>&1
  rc=$?; echo "$(date '+%F %T') $side exit $rc: $(grep -a 'RESULT' /c/o13/w/${tag}_$side.out | tail -1)"
  [ $rc = 0 ] || exit $rc
done
a=$(sha256sum /c/o13/w/${tag}_pc1/src_copy/forge_ltopgo_${tag}_pc1.exe | cut -c1-64)
b=$(sha256sum /c/o13/w/${tag}_pc2/src_copy/forge_ltopgo_${tag}_pc2.exe | cut -c1-64)
echo "pc1 $a"; echo "pc2 $b"
[ "$a" = "$b" ] && echo "PC1 = PC2: PASS" || { echo "PC1 != PC2: FAIL"; exit 4; }
