#!/usr/bin/env bash
# S41 bench evidence (sequential, nice 19, one engine/compiler process at a time). Writes only under $OUT.
#   1. patched AL1 exe: OFF identity is step5 (uci_check --full); here ON at NetScale 99 (proposal for s198) and 90
#      (the idea-board NetScalePct=90 value, sensitivity), 5 depths each; UCI option list.
#   2. e48f006 base (AL1 code tree + e48f006 net): unpatched build -> bench == 328459/945640/3024381/9162399/20421972;
#      patched build OFF -> same refs + perft; patched ON at NetScale 99 (proposal for e48f006).
# usage: run_s41_benches.sh <worktree> <build_dir> <out_dir> <lock_exe>
set -uo pipefail
W=$1; B=$2; OUT=$3; LOCK=$4
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
T=$W/opus_round1/sol_S41/tools
BUILD=/d/grok-pc-data/dwqww/.claude/worktrees/b/tools/build_pc.sh
AL1_REF=312866,862329,3024920,12389307,34048354
F006_REF=328459,945640,3024381,9162399,20421972
mkdir -p "$OUT"
free_gb() { powershell -NoProfile -Command "[math]::Round((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1MB,1)"; }
need_ram() { local f; f=$(free_gb); echo "free RAM ${f} GB before: $1"; awk -v f="$f" 'BEGIN{exit !(f>=6.0)}' || { echo "free RAM below 6 GB, stop"; exit 3; }; }
echo "# S41 benches $(date); machine exclusive: no (gate + self-play + training running); nice 19"
need_ram "UCI option lists"
nice -n 19 $PY -I -B $T/bench_ref.py "$LOCK" --depths 11 --label lock_exe_uci --uci-out "$OUT/uci_options_lock.txt" > "$OUT/b0_lock_uci.log" 2>&1
nice -n 19 $PY -I -B $T/bench_ref.py "$B/forge_s41_al1.exe" --depths 11 --label s41_uci --uci-out "$OUT/uci_options_s41.txt" > "$OUT/b0_s41_uci.log" 2>&1
diff "$OUT/uci_options_lock.txt" "$OUT/uci_options_s41.txt" > "$OUT/uci_options_diff.txt"; echo "uci option diff rc=$? (1 = differs, expected: one NetScale line)"
for pct in 99 90; do
  need_ram "AL1 NetScale=$pct bench"
  nice -n 19 $PY -I -B $T/bench_ref.py "$B/forge_s41_al1.exe" --ref $AL1_REF --opt NetScale=$pct --label "AL1 patched ON NetScale=$pct" --json "$OUT/al1_on_$pct.json" 2>&1 | tee "$OUT/b1_al1_on_$pct.log"
done
need_ram "build e48f006 base (unpatched)"
nice -n 19 bash $BUILD "$B/src_e48f006_base" "$B/forge_e48f006_base.exe" > "$OUT/b2_build_e48f006_base.log" 2>&1; cat "$OUT/b2_build_e48f006_base.log"
need_ram "e48f006 base bench"
nice -n 19 $PY -I -B $T/bench_ref.py "$B/forge_e48f006_base.exe" --ref $F006_REF --perft --label "e48f006 base (unpatched)" --json "$OUT/e48f006_base.json" 2>&1 | tee "$OUT/b3_e48f006_base.log"
need_ram "build e48f006 patched"
nice -n 19 bash $BUILD "$B/src_e48f006_patched" "$B/forge_s41_e48f006.exe" > "$OUT/b4_build_e48f006_patched.log" 2>&1; cat "$OUT/b4_build_e48f006_patched.log"
need_ram "e48f006 patched OFF bench"
nice -n 19 $PY -I -B $T/bench_ref.py "$B/forge_s41_e48f006.exe" --ref $F006_REF --perft --label "e48f006 patched OFF (NetScale default)" --json "$OUT/e48f006_patched_off.json" 2>&1 | tee "$OUT/b5_e48f006_patched_off.log"
need_ram "e48f006 patched ON bench"
nice -n 19 $PY -I -B $T/bench_ref.py "$B/forge_s41_e48f006.exe" --ref $F006_REF --opt NetScale=99 --label "e48f006 patched ON NetScale=99" --json "$OUT/e48f006_on_99.json" 2>&1 | tee "$OUT/b6_e48f006_on_99.log"
echo "# done $(date)"
