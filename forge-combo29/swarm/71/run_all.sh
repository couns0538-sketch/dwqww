#!/usr/bin/env bash
# swarm/71 — reproduce every net-path correctness claim, in order, writing raw evidence to out/.
# Threads 1, fixed budgets, no `go infinite`. Stops on the first unexpected exit.
set -u
cd "$(dirname "$0")"
EXE=./build/forge
VEXE=./build_verify/forge
NET=test_v3.fnn3
mkdir -p out
fail=0
note() { printf '\n=== %s\n' "$1" | tee -a out/run_all.log; }

: > out/run_all.log

note "build hashes"
sha256sum "$EXE" "$VEXE" "$NET" | tee -a out/run_all.log

note "test net identity (expect bytes 6309096, fnv1a64 fdff70de72e4ca82)"
python3 make_v3_testnet.py out/regen_testnet.fnn3 2>&1 | tee -a out/run_all.log
cmp -s "$NET" out/regen_testnet.fnn3 && echo "IDENTICAL to shipped test net" | tee -a out/run_all.log

note "Q1a incremental vs refresh, 400 sequences x 120 plies, every ply"
./netpath inc "$NET" fixtures/seq_deep.tsv 1 2>&1 | tee -a out/run_all.log || fail=1

note "Q1b incremental vs refresh, 200 sequences x 40 plies, every ply"
./netpath inc "$NET" fixtures/seq_large.tsv 1 2>&1 | tee -a out/run_all.log || fail=1

note "Q1c incremental vs refresh with evaluation gaps (replay_ply rebuild branch)"
./netpath inc "$NET" fixtures/seq_large.tsv 3 2>&1 | tee -a out/run_all.log || fail=1

note "Q1d lone-king walks: 5012 king-key transitions through the rebuild branch"
./netpath inc "$NET" fixtures/kingwalk.tsv 1 2>&1 | tee -a out/run_all.log || fail=1

note "Q1e distinct positions compared (fixtures overlap; this is the honest denominator)"
python3 count_distinct.py fixtures/seq_deep.tsv fixtures/seq_large.tsv fixtures/seq_small.tsv \
  fixtures/kingwalk.tsv 2>&1 | tee -a out/run_all.log || fail=1

note "Q1f kernel equality: scalar == avx2 == avx512 (a kernel diff would masquerade as an accumulator bug)"
g++ -O2 -std=c++20 -march=x86-64-v4 -DFORGE_NNUE_V3=1 -DFORGE_NNUE_HIDDEN=256 -I../../include \
  -o kernprobe kernprobe.cpp ../../src/nnue_v3.cpp ../../src/board.cpp ../../src/bitboard.cpp ../../src/nnue.cpp \
  >> out/run_all.log 2>&1 || fail=1
./kernprobe "$NET" fixtures/deep800.fens 2>&1 | tee -a out/run_all.log || fail=1

note "Q2 colour mirror, 1000 positions"
./netpath mirror "$NET" fixtures/mirror1000.fens 2>&1 | tee -a out/run_all.log || fail=1

note "Q2 colour mirror, 200 committed opening positions"
./netpath mirror "$NET" fixtures/OG200.fens 2>&1 | tee -a out/run_all.log || fail=1

note "Q3 bare kings"
./netpath bare "$NET" 2>&1 | tee -a out/run_all.log || fail=1

note "Q4 damaged nets"
python3 damage.py "$NET" ./netpath damage_out 2>&1 | tee -a out/run_all.log || fail=1

note "Q5 UCI activation / refusal / FEN diagnostic"
python3 uci_checks.py "$EXE" "$NET" damage_out/flip_w1.fnn3 fixtures/OG200.fens 2>&1 | tee -a out/run_all.log || fail=1

note "Q5b fault injection: the incremental check must FAIL when corrupted"
./netpath inc "$NET" fixtures/seq_small.tsv 1 0 1 > out/inject.log 2>&1
if grep -q "acc_mismatched 0 " out/inject.log; then
  echo "INJECTION DID NOT DETECT — harness cannot fail" | tee -a out/run_all.log; fail=1
else
  echo "injection detected: $(grep -o 'acc_mismatched [0-9]*' out/inject.log | head -1)" | tee -a out/run_all.log
fi

note "Q6 identity baseline"
python3 baseline_200.py "$EXE" "$NET" fixtures/OG200.fens 27944084 out/baseline_out.csv 2>&1 | tail -4 | tee -a out/run_all.log

printf '\nrun_all finished fail=%d\n' "$fail" | tee -a out/run_all.log
exit "$fail"
