#!/usr/bin/env bash
# R8 measurement chain after the first "after" run (each step <= 2 busy threads, nothing on CPUs 12-15).
# usage: r8_chain.sh   (writes F:/opus_scratch/r8/chain/*; prints one line per step)
set -uo pipefail
R=D:/grok-pc-data/dwqww/.claude/worktrees/opus-r8-datagen
S=F:/opus_scratch/r8
C=$S/chain
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
RP=$R/r8/tools/run_pinned.py
ENG='F:\opus_scratch\r8\engine\forge_live_copy.exe'
mkdir -p $C
step() { echo "== $(date '+%H:%M:%S') $*"; }
step "1 build v3"
$PY -I -B $RP --mask 0x00FF -- $R/r8/tools/build_driver.py $R $S/driver/forge_selfplay_fast_v3.exe 2>&1 | grep -E "error|warning|built"
D3=$S/driver/forge_selfplay_fast_v3.exe
step "2 v3 equivalence on the 60 fixed openings (vs the live play_game reference)"
mkdir -p $C/eq_v3
nice -n 10 $D3 --engine "$ENG" --out 'F:\opus_scratch\r8\chain\eq_v3' --workers 1 --cpus 8-9 --openings 'F:\opus_scratch\r8\eq1\openings60.txt' --no-dedup --prefix eq --priority belownormal --progress-seconds 600 | tail -2
cmp $C/eq_v3/eq_001.txt $S/eq1/ref.txt && echo "v3 == reference: IDENTICAL" || echo "v3 DIFFERS from the reference"
for h in 8 4; do
  step "3 hash $h on the 60 fixed openings"
  mkdir -p $C/hash$h
  s=$(date +%s%N)
  nice -n 10 $D3 --engine "$ENG" --out "F:\\opus_scratch\\r8\\chain\\hash$h" --workers 1 --cpus 8-9 --openings 'F:\opus_scratch\r8\eq1\openings60.txt' --no-dedup --prefix h$h --hash $h --priority belownormal --progress-seconds 600 | tail -2
  echo "hash $h wall $(( ($(date +%s%N) - s) / 1000000 )) ms; records $(wc -l < $C/hash$h/h${h}_001.txt); same as hash 16: $(cmp -s $C/hash$h/h${h}_001.txt $S/eq1/ref.txt && echo yes || echo no)"
done
step "4 SMT: 2 workers on CPUs 8-9 (one logical CPU each), 4 minutes, random openings (only if the PC leaves room)"
busy=$(powershell -NoProfile -Command "\$s=0; 1..5 | ForEach-Object { \$s += (Get-CimInstance Win32_PerfFormattedData_PerfOS_Processor -Filter \"Name='_Total'\").PercentProcessorTime; Start-Sleep 2 }; [math]::Round(\$s/5)")
echo "system busy before the SMT test: ${busy}% (2 busy engines add ~12.5%; the job limit is 70%)"
if [ "${busy:-99}" -le 57 ]; then
  mkdir -p $C/smt2
  nice -n 10 $D3 --engine "$ENG" --out 'F:\opus_scratch\r8\chain\smt2' --workers 2 --cpus 8-9 --max-minutes 4 --seed 7 --priority idle --progress-seconds 60 | tail -3
else
  echo "SMT test skipped: it would push the PC over 70%"
fi
step "5 baseline segment 2 (live script, 1 worker, CPUs 8-9, 1300 games)"
mkdir -p $C/base2
(cd $C/base2 && nice -n 10 $PY -B 'C:\Users\Administrator\grok-pc\nnue\forge-nnue-tools\forge_selfplay.py' --engine "$ENG" --workers 1 --cpus 8-9 --nodes 5000 --engine-timeout 180 --out 'F:\opus_scratch\r8\chain\base2\out' --progress-seconds 60 --games-per-worker 1300 --seed 11 2>&1 | grep -E "TOTAL|Stopped|error" | tail -2)
step "6 after segment 2 (v3, 1 worker, CPUs 8-9, 10 minutes)"
mkdir -p $C/after2
nice -n 10 $D3 --engine "$ENG" --out 'F:\opus_scratch\r8\chain\after2' --workers 1 --cpus 8-9 --max-minutes 10 --seed 12 --pos --priority idle --progress-seconds 60 | tail -3
step "chain done"
