#!/usr/bin/env bash
# R14 A3: P7 - PGN sha256, re-extraction with the CR 129d440e PGN-error skip (must equal R13's output to reuse the evals),
# fit_e3 regression at the default bounds (must equal R13's fit), one refit with wider bounds 50,400,100.
set -u
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
P7=/d/grok-pc-data/dwqww/.claude/worktrees/o13-p7/opus_r13/p7
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
F=/f/forge_push
O=/d/o14a/p7
for x in $O/al1gates_r14.fens $O/fit_e3_default_r14.json $O/fit_e3_wide.json; do
  if [ -e "$x" ]; then echo "exists: $x - refusing"; exit 2; fi
done
PGNS="$F/gateR11H2H_B_winner_vs_AL1plain833c/gateR11H2H_B_winner_vs_AL1plain833c.pgn
$F/gate_sf26bundle14_vs_AL1/gate_sf26bundle14_vs_AL1.pgn
$F/uhoR12_bundle_w21pt_7d50_vs_AL1lp/uhoR12_bundle_w21pt_7d50_vs_AL1lp.pgn
$F/uhoR5A1_corrhistplus4_lp442f_vs_AL1lp/uhoR5A1_corrhistplus4_lp442f_vs_AL1lp.pgn
$F/uhoR5A2_corrext1_lp442f_vs_AL1lp/uhoR5A2_corrext1_lp442f_vs_AL1lp.pgn
$F/uhoSF26bit1_razor_e417_vs_AL1lp/uhoSF26bit1_razor_e417_vs_AL1lp.pgn"
date '+start %F %T'
for p in $PGNS; do sha256sum "$p" | sed "s# \*\?/f/forge_push/# *F:/forge_push/#"; done > $O/pgn_inputs.sha256
cat $O/pgn_inputs.sha256
"$PY" -I -B $P7/extract_positions.py D:/o14a/p7/al1gates_r14 $PGNS; echo "extract exit $?"
for e in fens tsv; do
  a=$(sha256sum /c/o13/p7/al1gates.$e | cut -c1-64); b=$(sha256sum $O/al1gates_r14.$e | cut -c1-64)
  [ "$a" = "$b" ] && echo "al1gates.$e: R14 re-extraction IDENTICAL to R13 ($a)" || echo "al1gates.$e: DIFFERS R13 $a R14 $b"
done
"$PY" -I -B $P7/fit_e3.py C:/o13/p7/al1gates C:/o13/p7/al1gates.evals D:/o14a/p7/fit_e3_default_r14.json; echo "fit default exit $?"
date '+default fit done %F %T'
"$PY" -I -B $P7/fit_e3.py C:/o13/p7/al1gates C:/o13/p7/al1gates.evals D:/o14a/p7/fit_e3_wide.json --bounds 50,400,100; echo "fit wide exit $?"
date '+end %F %T'
