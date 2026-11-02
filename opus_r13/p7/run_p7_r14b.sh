#!/usr/bin/env bash
# R14 A3 part 2: the gate PGNs grew after R13 (13,795 games now vs 11,888), so the R14 extraction is a new data set:
# raw lock evals with the R13 raw_eval.exe (ebd27774, built on d4f4312), then fit_e3 at the default and the wide bounds.
set -u
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
P7=/d/grok-pc-data/dwqww/.claude/worktrees/o13-p7/opus_r13/p7
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
O=/d/o14a/p7
for x in $O/al1gates_r14.evals $O/fit_e3_r14data_default.json $O/fit_e3_r14data_wide.json; do
  if [ -e "$x" ]; then echo "exists: $x - refusing"; exit 2; fi
done
date '+start %F %T'
echo "raw_eval sha256 $(sha256sum /c/o13/p7/raw_eval.exe | cut -c1-64)"
/c/o13/p7/raw_eval.exe D:/o14a/p7/al1gates_r14.fens > $O/al1gates_r14.evals 2> $O/raw_eval_r14.err
echo "raw_eval exit $? lines $(wc -l < $O/al1gates_r14.evals) stderr lines $(wc -l < $O/raw_eval_r14.err)"
"$PY" -I -B $P7/fit_e3.py D:/o14a/p7/al1gates_r14 D:/o14a/p7/al1gates_r14.evals D:/o14a/p7/fit_e3_r14data_default.json; echo "fit default exit $?"
"$PY" -I -B $P7/fit_e3.py D:/o14a/p7/al1gates_r14 D:/o14a/p7/al1gates_r14.evals D:/o14a/p7/fit_e3_r14data_wide.json --bounds 50,400,100; echo "fit wide exit $?"
for p in $(sed -n 's#^[0-9a-f]* \*F:/#/f/#p' $O/pgn_inputs.sha256); do sha256sum "$p" | sed "s# \*\?/f/forge_push/# *F:/forge_push/#"; done > $O/pgn_inputs_end.sha256
cmp -s $O/pgn_inputs.sha256 $O/pgn_inputs_end.sha256 && echo "PGNs unchanged during the R14 runs" || echo "PGNs CHANGED during the R14 runs"
date '+end %F %T'
