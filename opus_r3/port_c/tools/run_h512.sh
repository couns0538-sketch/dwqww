#!/usr/bin/env bash
# R3 port C: SA4's H512 recipe on the stack (PC box recipe + -UFORGE_NNUE_HIDDEN -DFORGE_NNUE_HIDDEN=512
# -DFORGE_NNUE_WEIGHTS=<net>), with FORGE_NNUE_INT16 (SA4's ON checks) in both FORGE_NNUE_O2 states, one float-only
# build, SA4's bench pins, and the v2 code at H512 (replica of the split net; an H256 v2 net must be refused).
T=/d/grok-pc-data/dwqww/.claude/worktrees/b/tools
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
W=/f/opus_scratch/worktrees/opus_r3_port_c
WW=F:/opus_scratch/worktrees/opus_r3_port_c
B=/f/opus_scratch/build/r3_port_c
L=/f/opus_scratch/r3/port_c/logs
N=F:/opus_scratch/r3/port_c/nets
SPLIT=F:/opus_scratch/sol_SA4/nets/h512_widened_lock_split.inc
SMOKE=F:/opus_scratch/sol_SA4/nets/h512_smoke_e2.inc
H="-UFORGE_NNUE_HIDDEN -DFORGE_NNUE_HIDDEN=512"
nice -n 19 bash $T/build_pc.sh "$W" $B/h512_split_int16.exe $H "-DFORGE_NNUE_WEIGHTS=\"$SPLIT\"" -DFORGE_NNUE_INT16=1 > $L/build_h512.log 2>&1
nice -n 19 bash $T/build_pc.sh "$W" $B/h512_split_int16_o2.exe $H "-DFORGE_NNUE_WEIGHTS=\"$SPLIT\"" -DFORGE_NNUE_INT16=1 -DFORGE_NNUE_O2=1 >> $L/build_h512.log 2>&1
nice -n 19 bash $T/build_pc.sh "$W" $B/h512_smoke_int16.exe $H "-DFORGE_NNUE_WEIGHTS=\"$SMOKE\"" -DFORGE_NNUE_INT16=1 >> $L/build_h512.log 2>&1
nice -n 19 bash $T/build_pc.sh "$W" $B/h512_smoke_int16_o2.exe $H "-DFORGE_NNUE_WEIGHTS=\"$SMOKE\"" -DFORGE_NNUE_INT16=1 -DFORGE_NNUE_O2=1 >> $L/build_h512.log 2>&1
nice -n 19 bash $T/build_pc.sh "$W" $B/h512_split_float.exe $H "-DFORGE_NNUE_WEIGHTS=\"$SPLIT\"" >> $L/build_h512.log 2>&1
X="nice -n 19 $PY -I -B $WW/opus_r3/port_c/bench_expect.py"
SPLIT_OFF=11=312866,13=862329,16=3043192,20=13215819
SPLIT_ON=11=330610,13=858175,16=2760596,20=9564588
SMOKE_OFF=11=343099,13=834267,16=2755018,20=11577336
SMOKE_ON=11=359658,13=890711,16=3140646,20=10867508
{
for x in h512_split_int16 h512_split_int16_o2; do
  echo "## $x float (NnueInt16 off)"; $X $B/$x.exe --expect $SPLIT_OFF
  echo "## $x NnueInt16 on"; $X $B/$x.exe --opt NnueInt16=true --expect $SPLIT_ON --need "NnueInt16 active"
done
for x in h512_smoke_int16 h512_smoke_int16_o2; do
  echo "## $x float (NnueInt16 off)"; $X $B/$x.exe --expect $SMOKE_OFF
  echo "## $x NnueInt16 on"; $X $B/$x.exe --opt NnueInt16=true --expect $SMOKE_ON --need "NnueInt16 active"
done
echo "## h512_split_float (no FORGE_NNUE_INT16)"; $X $B/h512_split_float.exe --expect $SPLIT_OFF
} > $L/bench_h512.log 2>&1
{
for x in h512_split_int16 h512_split_int16_o2 h512_split_float; do
  echo "## $x + v2 replica r1 of the split net (NNUEKingBuckets 1): the H512 float tree"
  $X $B/$x.exe --opt NNUEFile=$N/h512_split_r1.fnn2 --opt NNUEKingBuckets=1 --expect 11=312866,13=862329,16=3043192 --need "NNUE v2: active"
done
for x in h512_split_int16 h512_split_int16_o2; do
  echo "## $x + v2 replica + NnueInt16 on: still the v2 float tree"
  $X $B/$x.exe --opt NNUEFile=$N/h512_split_r1.fnn2 --opt NNUEKingBuckets=1 --opt NnueInt16=true --expect 11=312866,13=862329,16=3043192 --need "NNUE v2: active" --need "NnueInt16 active"
done
echo "## h512_split_int16 + an H256 v2 net: must be refused (hidden size in the header)"
printf 'uci\nsetoption name NNUEFile value %s\nsetoption name NNUEKingBuckets value 1\nisready\nquit\n' "$N/lock_h256_r1.fnn2" | nice -n 19 $B/h512_split_int16.exe | grep -E "NNUE v2|ERROR"
echo "exit status ${PIPESTATUS[1]}"
} > $L/v2_h512.log 2>&1
cat $L/build_h512.log; grep -c "ALL OK" $L/bench_h512.log $L/v2_h512.log; grep -E "MISMATCH|FAILED|MISSING" $L/bench_h512.log $L/v2_h512.log
echo h512 done
