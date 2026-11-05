#!/usr/bin/env bash
# cpu6_final.sh - Opus 30-h job, last hour of window 2 on CPU 6 (mask 0x40, Idle):
#  0. wait until the R14 agent's suite (D:\a14\evidence\test_logs\r14\full-suite-r14cont03\exit.txt) has run on CPU 6
#     and no python / fastchess / engine is pinned to CPU 6 (or 18:20, whichever first, then still only a free CPU 6)
#  1. Forge play checks of the final candidates (the gate exe v2p4 with EvalFileV2=<net>): smoke2m.py 300 s (Threads 2,
#     Hash 16, tc 2000+20, engine-side legality) and uci_conformance_o30.py with the net loaded -> D:\o30\checks_gpu_w2\<net>\
#  2. two more layout speed probes each for KB8 / KB16 / KB32 vs KB4 (identity nets) for 3-run figures
#  Nothing starts after 19:00 (the window ends ~19:06). Paths built from variables (no backslash literals).
set -u
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
T=/d/o30/wt/opus_30h/tools
EXE=D:/o30/w/v2p4_pc1/src_copy/forge_ltopgo_v2p4_pc1.exe
OUT=/d/o30/checks_gpu_w2
busy6() {   # processes pinned to exactly CPU 6 (mask 64): the P16 match, the R14 suite
    powershell -NoProfile -Command "Get-Process python,fastchess,forge_ltopgo* -ErrorAction SilentlyContinue | Where-Object { [int64]\$_.ProcessorAffinity -eq 64 } | Measure-Object | Select-Object -ExpandProperty Count" | tr -d '\r'
}
late() { [ "$(date +%H%M)" -ge "$1" ]; }
# wait UNPINNED (polling must not land on CPU 6 while the agent's timing-sensitive suite runs there)
until { [ -f /d/a14/evidence/test_logs/r14/full-suite-r14cont03/exit.txt ] || late 1820; } && [ "$(busy6)" = "0" ]; do sleep 20; done
. "$T/idle.sh"; o30_pin_self 0x40 || { echo "cpu6_final: cannot pin to Idle / CPU 6"; exit 78; }
echo "$(date '+%F %T') CPU 6: suite marker $( [ -f /d/a14/evidence/test_logs/r14/full-suite-r14cont03/exit.txt ] && echo present || echo absent)"
# the P16 match (16:02-~18:00) wrote into the literal folder D:\o30\nets$name\sanity (an escaped $ in the starting
# command); it has ended now (CPU 6 free): move it to the net's own folder (a move, nothing deleted)
src='/d/o30/nets$name/sanity'; dst=/d/o30/nets/o30_gpu_soupP16_r3r5r7r11r12/sanity
if [ -d "$src" ] && [ ! -e "$dst" ]; then
    mv "$src" "$dst" && echo "$(date '+%F %T') moved the P16 sanity folder to $dst (the empty folder 'D:\\o30\\nets\$name' stays)"
fi
for name in o30_gpu_soupZ32_r3r5r7r8r12 o30_gpu_soupU8r3r5r10r12r14 o30_gpu_soupV16_r3r5r7r11r12r13; do
    late 1900 && { echo "$(date '+%T') 19:00 reached: stop"; exit 0; }
    o="$OUT/$name"; mkdir -p "$o"
    net="D:/o30/nets/$name/$name.nnue2"
    echo "$(date '+%F %T') smoke 300 s $name"
    "$PY" -I -B "$T/smoke2m.py" "$EXE" --line "EvalFileV2=$net" --seconds 300 --threads 2 --hash 16 --mask 0x40 --idle \
        --out "$(cygpath -w "$o/smoke_300s")" > "$o/smoke_300s.txt" 2>&1
    echo "   exit $?: $(tail -1 "$o/smoke_300s.txt" | cut -c1-200)"
    "$PY" -I -B "$T/uci_conformance_o30.py" "$EXE" --opt "EvalFileV2=$net" --expect-info "EvalFileV2 loaded" --threads 2 \
        --mask 0x40 --json "$(cygpath -w "$o/uci_conformance.json")" > "$o/uci_conformance.txt" 2>&1
    echo "   conformance exit $?: $(tail -1 "$o/uci_conformance.txt" | cut -c1-200)"
done
for rep in rep2 rep3; do
    for k in rank4x2 rank4x4 rank4x8; do
        late 1900 && { echo "$(date '+%T') 19:00 reached: stop"; exit 0; }
        t="$OUT/layout_${k}_vs_kb4_$rep"
        [ -e "$t.txt" ] && t="${t}b"
        "$PY" -I -B 'D:\o30\checks_gpu\scripts\depth_probe_ab.py' 'D:\o30\control\lockkb4_v2p4\lockkb4_v2p4.pgn' "$EXE" "$EXE" \
            --opt-a 'EvalFileV2=D:/o30/nets/lockv2/lock_kbrank4_ob8.nnue2' --opt-b "EvalFileV2=D:/o30/nets/lockv2/lock_kb${k}_ob8.nnue2" \
            --mask 0x40 --json "$(cygpath -w "$t.json")" > "$t.txt" 2>&1
        echo "$(date '+%T') $(basename "$t") exit $?: $(grep 'nps B / A' "$t.txt" | cut -c1-110)"
    done
done
echo "$(date '+%F %T') cpu6_final done"
