#!/usr/bin/env bash
# R14 A5: P3 combined line on the handoff exe 029d58e8 with QA's kit v2.3 checker (lp_check.py, frozen bench_fens):
# OFF (pins), Sf26Bundle=14 and the three singles together; the combined line must equal Sf26Bundle=14 in every number.
set -u
K='C:\Users\Administrator\grok-pc\forge_push\qa_ltopgo_al1_stage\kit_v23'
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
EXE='C:\o13\handoff\p3_sf26\forge_ltopgo_sfs.exe'
O=/d/o14a/p3
for x in $O/off.json $O/b14.json $O/comb.json; do [ -e "$x" ] && { echo "exists: $x - refusing"; exit 2; }; done
echo "exe sha256 $(sha256sum /c/o13/handoff/p3_sf26/forge_ltopgo_sfs.exe | cut -c1-64)"
date '+start %F %T'
"$PY" -I -B "$K\\tools\\lp_check.py" run "$EXE" 'D:\o14a\p3\off.json' --fens "$K\\workload\\bench_fens.txt" > $O/off.txt 2>&1; echo "run off exit $?"
"$PY" -I -B "$K\\tools\\lp_check.py" run "$EXE" 'D:\o14a\p3\b14.json' --opt Sf26Bundle=14 --fens "$K\\workload\\bench_fens.txt" > $O/b14.txt 2>&1; echo "run b14 exit $?"
"$PY" -I -B "$K\\tools\\lp_check.py" run "$EXE" 'D:\o14a\p3\comb.json' --opt Sf26NmpPrior=1 --opt Sf26LmrGap=1 --opt Sf26MulticutCorr=1 --fens "$K\\workload\\bench_fens.txt" > $O/comb.txt 2>&1; echo "run comb exit $?"
echo "== OFF vs lock pins (OFF run compared with itself + pins)"
"$PY" -I -B "$K\\tools\\lp_check.py" compare 'D:\o14a\p3\off.json' 'D:\o14a\p3\off.json' --pins d11=312866,d13=862329,d16=3024920,d20=12389307,d22=34048354 --perft-pins startpos=4865609,kiwipete=193690690; echo "off pins exit $?"
echo "== combined line vs Sf26Bundle=14 (every bench / perft / FEN number and bestmove)"
"$PY" -I -B "$K\\tools\\lp_check.py" compare 'D:\o14a\p3\b14.json' 'D:\o14a\p3\comb.json' --off 'D:\o14a\p3\off.json'; echo "comb = b14 exit $?"
date '+end %F %T'
