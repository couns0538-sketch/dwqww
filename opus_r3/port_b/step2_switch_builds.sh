#!/usr/bin/env bash
# port_b step 2: switch-ON PC builds (box recipe) + lock identity + each branch's own acceptance runs.
# Sequential (one heavy step at a time), nice 19, free RAM >= 6 GB before every heavy step.
set -u
W=/f/opus_scratch/worktrees/opus_r3_port_b
T=/d/grok-pc-data/dwqww/.claude/worktrees/b/tools
B=/f/opus_scratch/build/r3_port_b
L=/f/opus_scratch/r3/port_b
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
LA=D:/grok-pc-data/dwqww/.claude/worktrees/b/pkg/forge_LOCK_AL1_s198_FULL_20261026_1039
ram() { powershell -NoProfile -Command "[math]::Floor((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1MB)"; }
waitram() { while :; do r=$(ram | tr -d '\r'); [ "${r:-0}" -ge 6 ] && { echo "free RAM ${r} GB"; break; }; echo "free RAM ${r} GB < 6, waiting"; sleep 60; done; }
step() { echo "== $(date '+%F %T') $*"; }

cd "$W"
echo "head $(git rev-parse HEAD)"

# --- S32 FORGE_DATAGEN ------------------------------------------------------------------------------------
step "build head_datagen.exe (FORGE_EXTRA_SRCS=src/datagen.cpp, -DFORGE_DATAGEN=1)"; waitram
FORGE_EXTRA_SRCS=src/datagen.cpp nice -n 19 bash $T/build_pc.sh "$W" $B/head_datagen.exe -DFORGE_DATAGEN=1 > $L/build_head_datagen.log 2>&1
echo "rc=$? warnings=$(grep -ci warning $L/build_head_datagen.log)"; cat $L/build_head_datagen.log
step "uci_check --full head_datagen.exe"; waitram
nice -n 19 $PY -I -B $LA/2_build/uci_check.py F:/opus_scratch/build/r3_port_b/head_datagen.exe --full > $L/uci_check_full_head_datagen.log 2>&1
echo "rc=$?"; tail -1 $L/uci_check_full_head_datagen.log
step "datagen smoke = S32's determinism run (25 games, 5000 nodes, seed 20261027, --text), twice"
mkdir -p $L/datagen_smoke/det_a $L/datagen_smoke/det_b
for r in det_a det_b; do
  waitram
  nice -n 19 $B/head_datagen.exe datagen --out F:/opus_scratch/r3/port_b/datagen_smoke/$r/g --games 25 --seed 20261027 --text > $L/datagen_smoke_$r.log 2>&1
  echo "$r rc=$?"; cat $L/datagen_smoke_$r.log
done
(cd $L/datagen_smoke && sha256sum det_a/g.games det_a/g_000.hce det_a/g_000.info det_a/g_000.pos det_a/g_000.txt \
   det_b/g.games det_b/g_000.hce det_b/g_000.info det_b/g_000.pos det_b/g_000.txt) > $L/datagen_smoke.sha256
ls -l $L/datagen_smoke/det_a
# S32's recorded sha256 of the same run (opus_round1/sol_S32/logs/run_outputs.sha256, det_a lines)
grep ' det_a/' "$W/opus_round1/sol_S32/logs/run_outputs.sha256" > $L/datagen_smoke_s32_reference.sha256
if diff <(grep ' det_a/' $L/datagen_smoke.sha256) $L/datagen_smoke_s32_reference.sha256 > /dev/null \
   && diff <(grep ' det_a/' $L/datagen_smoke.sha256 | cut -d' ' -f1) <(grep ' det_b/' $L/datagen_smoke.sha256 | cut -d' ' -f1) > /dev/null; then
  echo "DATAGEN SMOKE: det_a == det_b == S32 reference (5 files): PASS"
else
  echo "DATAGEN SMOKE: MISMATCH"; diff <(grep ' det_a/' $L/datagen_smoke.sha256) $L/datagen_smoke_s32_reference.sha256
fi

# --- S04fix FORGE_ATTACKS_INIT_ONCE -------------------------------------------------------------------------
step "build head_initonce.exe (-DFORGE_ATTACKS_INIT_ONCE=1)"; waitram
nice -n 19 bash $T/build_pc.sh "$W" $B/head_initonce.exe -DFORGE_ATTACKS_INIT_ONCE=1 > $L/build_head_initonce.log 2>&1
echo "rc=$? warnings=$(grep -ci warning $L/build_head_initonce.log)"; cat $L/build_head_initonce.log
step "uci_check --full head_initonce.exe"; waitram
nice -n 19 $PY -I -B $LA/2_build/uci_check.py F:/opus_scratch/build/r3_port_b/head_initonce.exe --full > $L/uci_check_full_head_initonce.log 2>&1
echo "rc=$?"; tail -1 $L/uci_check_full_head_initonce.log

# --- S37 microbench (tool target, PC lock recipe via the job's own script) ---------------------------------
step "build mb_avx2.exe (opus_round1/sol_S37/build_microbench_pc.sh avx2)"; waitram
nice -n 19 bash "$W/opus_round1/sol_S37/build_microbench_pc.sh" "$W" $B/mb_avx2.exe avx2 > $L/build_microbench_avx2.log 2>&1
echo "rc=$? warnings=$(grep -ci warning $L/build_microbench_avx2.log)"; cat $L/build_microbench_avx2.log
WAC=F:/opus_scratch/worktrees/opus_r3_port_b/tools/nnue_microbench_wac300.epd
step "microbench --check-only --positions 2000 (= the CTest; S37 check_quick.log reference)"; waitram
nice -n 19 $B/mb_avx2.exe --check-only --positions 2000 --wac $WAC > $L/microbench_check2000.log 2>&1
echo "rc=$?"; cat $L/microbench_check2000.log
step "microbench --check-only --positions 10000 (S37 lock checksums 116176/-65898/50278)"; waitram
nice -n 19 $B/mb_avx2.exe --check-only --positions 10000 --wac $WAC > $L/microbench_check10000.log 2>&1
echo "rc=$?"; cat $L/microbench_check10000.log
step "microbench timed run (10000 positions, 5 passes; advisory, machine exclusive: no)"; waitram
nice -n 19 $B/mb_avx2.exe --positions 10000 --repeats 5 --call-repeats 1 --wac $WAC --label stack_port_b_avx2 \
  --dump-fens F:/opus_scratch/r3/port_b/microbench_fens10000.txt --json F:/opus_scratch/r3/port_b/microbench_timed.json > $L/microbench_timed.log 2>&1
echo "rc=$?"; tail -30 $L/microbench_timed.log
sha256sum $L/microbench_fens10000.txt
step "STEP2 DONE"
