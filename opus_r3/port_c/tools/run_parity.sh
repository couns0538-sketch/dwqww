#!/usr/bin/env bash
# R3 port C: SA2's parity driver (opus_round1/sol_SA2/nnue_int16_dump.cpp) built on the stack with the switch
# FORGE_NNUE_INT16, FORGE_NNUE_O2 off/on, AVX2 (znver5) and scalar (x86-64) kernels; H256 lock net and SA4's two
# H512 nets; every dump must be byte-identical to the SA2 / SA4 reference dump (which passed sa2_parity.py).
GPP=/c/msys64/ucrt64/bin/g++.exe
export PATH=/c/msys64/ucrt64/bin:$PATH
W=/f/opus_scratch/worktrees/opus_r3_port_c
OUT=/f/opus_scratch/r3/port_c/parity
L=/f/opus_scratch/r3/port_c/logs
F=F:/opus_scratch/sol_SA2/inputs/fens_10k.txt
SPLIT=F:/opus_scratch/sol_SA4/nets/h512_widened_lock_split.inc
SMOKE=F:/opus_scratch/sol_SA4/nets/h512_smoke_e2.inc
REF_H256=ba76ee8134a2d80705d7b044cff976bfdd68173eb42a8239c9da071c2ac5a837
REF_SMOKE=408d7a54d1f023e4328f5f91ff4f8d0c8118e398f7855109ac03b758484146ca
REF_SPLIT=6389c13216857b94242affc96463db582a5244964367fec007959a9e33d8fa8b
cd "$W"
COMMON="-std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -static -Wall -Wextra -Iinclude -DFORGE_NNUE_INT16=1"
SRCS="opus_round1/sol_SA2/nnue_int16_dump.cpp src/nnue.cpp src/bitboard.cpp src/board.cpp src/eval.cpp src/eval_params.cpp"
LOG=$L/parity_dumps.log
echo "# R3 port C parity dumps ($(date -u +%FT%TZ)); FENs $F sha256 $(sha256sum $F | cut -d' ' -f1)" > $LOG
run() {  # name ref extra-flags...
  local name=$1 ref=$2; shift 2
  local start=$(date +%s)
  nice -n 19 $GPP $COMMON "$@" $SRCS -o $OUT/$name.exe > $OUT/$name.build.txt 2>&1
  local brc=$?
  local warn=$(grep -ci warning $OUT/$name.build.txt)
  nice -n 19 $OUT/$name.exe $F > $OUT/$name.tsv 2> $OUT/$name.stderr
  local rrc=$?
  local sha=$(sha256sum $OUT/$name.tsv | cut -d' ' -f1)
  local verdict=MISMATCH; [ "$sha" = "$ref" ] && verdict="IDENTICAL to reference"
  echo "$name: flags [$*] build rc $brc, $warn warnings; run rc $rrc, $(wc -l < $OUT/$name.tsv) lines, stderr '$(cat $OUT/$name.stderr)'; dump sha256 $sha -> $verdict ($(( $(date +%s) - start )) s)" >> $LOG
}
run h256_avx2_o2off   $REF_H256 -march=znver5
run h256_scalar_o2off $REF_H256 -march=x86-64
run h256_avx2_o2on    $REF_H256 -march=znver5 -DFORGE_NNUE_O2=1
run h256_scalar_o2on  $REF_H256 -march=x86-64 -DFORGE_NNUE_O2=1
H="-UFORGE_NNUE_HIDDEN -DFORGE_NNUE_HIDDEN=512"
run h512_smoke_avx2_o2off   $REF_SMOKE -march=znver5 $H "-DFORGE_NNUE_WEIGHTS=\"$SMOKE\""
run h512_smoke_scalar_o2off $REF_SMOKE -march=x86-64 $H "-DFORGE_NNUE_WEIGHTS=\"$SMOKE\""
run h512_smoke_avx2_o2on    $REF_SMOKE -march=znver5 $H "-DFORGE_NNUE_WEIGHTS=\"$SMOKE\"" -DFORGE_NNUE_O2=1
run h512_split_avx2_o2off   $REF_SPLIT -march=znver5 $H "-DFORGE_NNUE_WEIGHTS=\"$SPLIT\""
run h512_split_avx2_o2on    $REF_SPLIT -march=znver5 $H "-DFORGE_NNUE_WEIGHTS=\"$SPLIT\"" -DFORGE_NNUE_O2=1
echo "identical: $(grep -c 'IDENTICAL to reference' $LOG) of 9" >> $LOG
cat $LOG
