#!/usr/bin/env bash
# job2 part C: run all 2,000 sequences of deepseek6's own generator through MY runner on MY ASan+UBSan build.
set -u
HERE=/agent/repos/dwqww/forge-combo29/swarm/30/job2
cd "$HERE" || exit 1
date -u
echo "\$ cp /tmp/uci56_seqs.txt seqs56_generated.txt ; wc -l"
cp /tmp/uci56_seqs.txt seqs56_generated.txt
wc -l seqs56_generated.txt
date -u
echo "\$ nice -n 5 python3 runner.py /home/ubuntu/b/asan/forge seqs56_generated.txt out_full 4"
nice -n 5 python3 runner.py /home/ubuntu/b/asan/forge seqs56_generated.txt out_full 4
date -u
echo "--- summary.json"
cat out_full/summary.json
echo "--- bad_sequences.txt size"
wc -l out_full/bad_sequences.txt
