#!/usr/bin/env bash
# kit24_build.sh <scratch repo> <tag> <cpu mask> - Coder's kit v2.4 (QA's R12 bundle recipe: -Workload v2.1
# -PartialTraining -Expose) twice (<tag>_pc1, <tag>_pc2) from fresh clean exports, work dir C:\o13\w, BelowNormal on
# <cpu mask>. Checks: OFF pins + perft; -CheckOpt LargePages=true (pins = OFF pins), EvalFileHalfKA = e19 / e9 (pins =
# plain D8D90B68 counts). Then the binding check pc1 exe sha256 == pc2.
set -uo pipefail
repo="$1"; tag="$2"; mask="$3"; T1=/d/grok-pc-data/dwqww/.claude/worktrees/o13-p1/opus_r13/tools
KIT='C:\Users\Administrator\grok-pc\forge_push\qa_r12fix\pkg\coder_5d93a8e1\kit_v24\build_ltopgo.ps1'
PY='C:\Users\Administrator\grok-pc\nnue\.venv\Scripts\python.exe'
E19='C:\Users\Administrator\grok-pc\forge_push\bin\r11_e19_final_bf1e347c.nnue'
E9='C:\Users\Administrator\grok-pc\forge_push\bin\r11_e9_best_5380f866.nnue'
OFFP='d11=312866,d13=862329,d16=3024920,d20=12389307,d22=34048354'
for side in pc1 pc2; do
  powershell -NoProfile -ExecutionPolicy Bypass -File "$(cygpath -w "$T1/pc_gate.ps1")" -Drive C -NeedGB 1 || { echo "pc_gate not OK, stop"; exit 75; }
  src=/c/o13/src/${tag}_$side; bash "$T1/export_src.sh" "$repo" "$src" >/dev/null || exit 2
  cmd="& '$KIT' -SrcDir '$(cygpath -w "$src")' -Tag '${tag}_$side' -Work 'C:\o13\w' -Affinity $mask -Python '$PY' -Expose"
  cmd="$cmd -Workload v2.1 -NetE19 '$E19' -NetE9 '$E9' -PartialTraining -Pins '$OFFP' -PerftPins 'startpos=4865609,kiwipete=193690690'"
  cmd="$cmd -CheckOpt 'LargePages=true','EvalFileHalfKA=$E19','EvalFileHalfKA=$E9'"
  cmd="$cmd -CheckOptPins '$OFFP','d11=373062,d13=831975,d16=4115992,d20=17885060,d22=37006232','d11=287095,d13=693432,d16=2816047,d20=12332089,d22=25323515'"
  echo "$(date '+%F %T') kit24 $tag $side"
  powershell -NoProfile -ExecutionPolicy Bypass -Command "$cmd; exit \$LASTEXITCODE" > /c/o13/w/${tag}_$side.out 2>&1
  rc=$?; echo "$(date '+%F %T') $side exit $rc: $(grep -a 'RESULT' /c/o13/w/${tag}_$side.out | tail -1)"
  [ $rc = 0 ] || exit $rc
done
a=$(sha256sum /c/o13/w/${tag}_pc1/src_copy/forge_ltopgo_${tag}_pc1.exe | cut -c1-64)
b=$(sha256sum /c/o13/w/${tag}_pc2/src_copy/forge_ltopgo_${tag}_pc2.exe | cut -c1-64)
echo "pc1 $a"; echo "pc2 $b"
[ "$a" = "$b" ] && echo "PC1 = PC2: PASS" || { echo "PC1 != PC2: FAIL"; exit 4; }
