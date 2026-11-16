#!/usr/bin/env bash
# job2 part B: the two sanitizer proofs, then the full 2,000-sequence run with MY runner.
set -u
HERE=/agent/repos/dwqww/forge-combo29/swarm/30/job2
EXE=${1:-/home/ubuntu/b/asan/forge}
date -u
echo "== PROOF 1: the exe really carries ASan + UBSan"
echo "\$ sha256sum $EXE"; sha256sum "$EXE"
echo "\$ nm -C $EXE | grep -c __asan_"; nm -C "$EXE" | grep -c __asan_
echo "\$ nm -C $EXE | grep -c __ubsan_"; nm -C "$EXE" | grep -c __ubsan_
echo "\$ printf 'uci\nisready\nquit\n' | $EXE | grep '^id name'"
printf 'uci\nisready\nquit\n' | "$EXE" | grep '^id name'
echo "\$ env | grep -c 'ASAN_OPTIONS\|UBSAN_OPTIONS\|TSAN_OPTIONS\|LSAN_OPTIONS'"
env | grep -c 'ASAN_OPTIONS\|UBSAN_OPTIONS\|TSAN_OPTIONS\|LSAN_OPTIONS'
echo
echo "options sent: none but uci/isready (no setoption in this job's sequences beyond the generated ones)"
echo
echo "== PROOF 2: ONE planted fault behind input I control, built the same way, run through THE SAME RUNNER"
echo "   planted source: ~/planted_src (scratch copy, never committed; the diff is in planted_fault.patch.txt)"
echo "\$ sha256sum /home/ubuntu/b/planted/forge"; sha256sum /home/ubuntu/b/planted/forge
echo "\$ nm -C /home/ubuntu/b/planted/forge | grep -c __asan_"; nm -C /home/ubuntu/b/planted/forge | grep -c __asan_
echo
echo "\$ FORGE_PLANT_FAULT=1 python3 runner.py ~/b/planted/forge planted_seqs.txt out_planted_on 3"
FORGE_PLANT_FAULT=1 python3 "$HERE/runner.py" /home/ubuntu/b/planted/forge "$HERE/planted_seqs.txt" "$HERE/out_planted_on" 3
echo "\$ python3 runner.py ~/b/planted/forge planted_seqs.txt out_planted_off 3"
python3 "$HERE/runner.py" /home/ubuntu/b/planted/forge "$HERE/planted_seqs.txt" "$HERE/out_planted_off" 3
echo
echo "the sanitizer lines the runner kept (proof it saw them):"
cat "$HERE/out_planted_on/bad_sequences.txt" | head -6
date -u
