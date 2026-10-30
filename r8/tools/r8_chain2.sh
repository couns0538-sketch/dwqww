#!/usr/bin/env bash
# R8 final checks with the final driver (v4): build, equivalence, dedup modes, --check-nodes, global duplicate rate
# against the live DB (read only), quality of all four runs. One busy thread at a time, nothing on CPUs 12-15.
set -uo pipefail
R=D:/grok-pc-data/dwqww/.claude/worktrees/opus-r8-datagen
S=F:/opus_scratch/r8
C=$S/chain2
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
RP=$R/r8/tools/run_pinned.py
ENG='F:\opus_scratch\r8\engine\forge_live_copy.exe'
OPN='F:\opus_scratch\r8\eq1\openings60.txt'
mkdir -p $C
step() { echo "== $(date '+%H:%M:%S') $*"; }
step "1 build v4"
$PY -I -B $RP --mask 0x00FF -- $R/r8/tools/build_driver.py $R $S/driver/forge_selfplay_fast_v4.exe 2>&1 | grep -E "error|warning|built"
D4=$S/driver/forge_selfplay_fast_v4.exe
run60() {  # run60 <tag> [extra driver args]
  local tag=$1; shift
  mkdir -p $C/$tag
  nice -n 10 $D4 --engine "$ENG" --out "F:\\opus_scratch\\r8\\chain2\\$tag" --workers 1 --cpus 8-9 --openings "$OPN" --prefix $tag --priority belownormal --progress-seconds 600 "$@" | tail -2
}
step "2 v4 equivalence (no dedup) vs the live play_game reference"
run60 eq --no-dedup
cmp $C/eq/eq_001.txt $S/eq1/ref.txt && echo "v4 == reference: IDENTICAL" || echo "v4 DIFFERS"
step "3 dedup modes on the same games: bounded (default) vs exact"
run60 dedupb
run60 dedupx --dedup exact
cmp $C/dedupb/dedupb_001.txt $C/dedupx/dedupx_001.txt && echo "bounded == exact: IDENTICAL ($(wc -l < $C/dedupx/dedupx_001.txt) lines)" || echo "bounded and exact differ"
for n in 2500 1000; do
  step "4 --check-nodes $n (data change after in-check positions)"
  run60 chk$n --no-dedup --check-nodes $n
done
step "5 global duplicate rate of the after run vs the live hash DB (read only, immutable)"
$PY -I -B $RP --mask 0x0FFF -- $R/r8/tools/dedup_against_db.py 'D:\grok-pc-data\selfplay_out\forge_seen_hashes.sqlite3' $C/unused.txt $S/after1/out/forge_selfplay_fast_001.txt --count-only
step "6 quality of the four runs"
$PY -I -B $R/r8/tools/quality_check.py base1=$S/baseline/out/forge_selfplay_001.txt fast1=$S/after1/out/forge_selfplay_fast_001.txt base2=$(ls $S/chain/base2/out/forge_selfplay_*.txt | head -1) fast2=$(ls $S/chain/after2/forge_selfplay_fast_*.txt | head -1) --json $C/quality4.json
step "chain2 done"
