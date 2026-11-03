#!/usr/bin/env bash
# post_chain.sh - Opus R14-B: the post-proof measurements, one after the other on CPUs 2-3 (one physical core), each
# step logged with the load on CPUs 2-3 before it (private driver; outputs on C:). Steps:
#   1 PGO rebuild into C:/o14b/pgo3 (reproducibility: PGO exe sha256 must equal C:/o14b/pgo2's 08299f9f...)
#   2 measure_rates.sh workers   3 measure_rates.sh nodes   4 measure_rates.sh prepare
#   5 end-to-end: relabel2 with the PGO probe on the proof sample's first ~20k rows -> labels.tsv = the proof's prefix
#   6 item 1: fl_distribution old loader w4 vs fast loader (2,000 batches each), compare
set -u
I2=/d/grok-pc-data/dwqww/.claude/worktrees/o14b-r2/opus_r14b/item2
I1=/d/grok-pc-data/dwqww/.claude/worktrees/o14b-l1/opus_r14b/item1
LOAD=/d/grok-pc-data/dwqww/.claude/worktrees/o14b-status/opus_r14b/tools/cpu_users.ps1
PY=/c/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
SP=/d/grok-pc-data/selfplay_out
load() { echo "--- load before $1"; powershell -NoProfile -File "$LOAD" -Mask 0xC -Seconds 3 | head -6; }
step() { echo; echo "=== $1 start $(date '+%F %T')"; }

step "1 pgo rebuild"; load pgo3
bash $I2/build_probe_opt.sh /c/o14b/pgo3 /d/o14b/r2/pgo_req/train_2k.tsv
echo "pgo2 $(sha256sum < /c/o14b/pgo2/pgo/forge_data_probe.exe | cut -c1-64)"
echo "pgo3 $(sha256sum < /c/o14b/pgo3/pgo/forge_data_probe.exe | cut -c1-64)"

step "2 workers"; load workers
bash $I2/measure_rates.sh workers /c/o14b/r2/meas
step "3 nodes"; load nodes
bash $I2/measure_rates.sh nodes /c/o14b/r2/meas
step "4 prepare"; load prepare
( sleep 44; echo "--- --jobs 2 workers seen during prepare (44 s in):"; powershell -NoProfile -Command \
  "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object { \$_.CommandLine -match 'spawn_main' } | ForEach-Object { \$p = Get-Process -Id \$_.ProcessId -ErrorAction SilentlyContinue; '{0} prio={1} affinity=0x{2:X}' -f \$_.ProcessId, \$p.PriorityClass, [int64]\$p.ProcessorAffinity }" ) &
bash $I2/measure_rates.sh prepare /c/o14b/r2/meas
wait

step "5 pgo end-to-end"; load e2e
J=/c/o14b/r2/pgo_e2e
"$PY" -I -B $I2/relabel2.py prepare --job $J --run-id pgo-e2e --rows 20000 \
  --selfplay $SP/forge_selfplay_001.txt $SP/forge_selfplay_002.txt $SP/forge_selfplay_003.txt $SP/forge_selfplay_004.txt
"$PY" -I -B $I2/relabel2.py run --job $J --run-id pgo-e2e --probe 'C:\o14b\pgo2\pgo\forge_data_probe.exe' --nodes 20000 \
  --workers 2 --mask 0xC
"$PY" -I -B $I2/relabel2.py assemble --job $J --run-id pgo-e2e
n=$(($(wc -l < $J/final/labels.tsv)))
if cmp -s <(head -n "$n" /d/o14b/r2/proof/jobA/final/labels.tsv) $J/final/labels.tsv; then
  echo "PASS pgo probe labels.tsv ($((n - 1)) rows) = the proof's first $((n - 1)) rows (R13 probe)"
else
  echo "FAIL pgo probe labels differ from the proof's prefix"
fi

step "6 fl_distribution"; load fl
mkdir -p /c/o14b/fl_dist
"$PY" -I -B $I1/tools/fl_distribution.py stats --loader old --dll 'D:\o14b\ref\libtraining_data_loader.dll' --workers 4 \
  --batches 2000 --out 'C:\o14b\fl_dist\old_w4.json' --mask 0xC
"$PY" -I -B $I1/tools/fl_distribution.py stats --loader fast --dll 'D:\o14b\fl\b5_install\forge_fastloader.dll' --workers 1 \
  --batches 2000 --out 'C:\o14b\fl_dist\fast_t1.json' --mask 0xC
"$PY" -I -B $I1/tools/fl_distribution.py compare 'C:\o14b\fl_dist\old_w4.json' 'C:\o14b\fl_dist\fast_t1.json'
echo; echo "=== chain end $(date '+%F %T')"
