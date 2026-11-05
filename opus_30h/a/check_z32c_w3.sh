#!/usr/bin/env bash
# check_z32c_w3.sh - Opus 30-h job, window 3: the Forge play checks of the packed soup Z32c on CPU 0, as for the other
# soups (cpu6_final.sh): smoke 300 s (games through the engine's own legality check, Threads 2, Hash 16) and the UCI
# conformance script (22 checks, the net must report "EvalFileV2 loaded"). Exit codes on their own lines (BH-2).
set -u
T=/d/o30/wt/opus_30h/tools; PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
EXE='D:\o30\w\v2p4_pc1\src_copy\forge_ltopgo_v2p4_pc1.exe'
. "$T/idle.sh"; o30_pin_self 0x1 || { echo "cannot pin to Idle / CPU 0"; exit 78; }
name=o30_gpu_soupZ32c_w3; o=/d/o30/checks_gpu_w2/$name; mkdir -p "$o"
net="D:/o30/nets/$name/$name.nnue2"
echo "$(date '+%F %T') smoke 300 s $name"
"$PY" -I -B "$T/smoke2m.py" "$EXE" --line "EvalFileV2=$net" --seconds 300 --threads 2 --hash 16 --mask 0x1 --idle \
    --out "$(cygpath -w "$o/smoke_300s")" > "$o/smoke_300s.txt" 2>&1
rc=$?
echo "   exit $rc: $(tail -1 "$o/smoke_300s.txt" | cut -c1-200)"
"$PY" -I -B "$T/uci_conformance_o30.py" "$EXE" --opt "EvalFileV2=$net" --expect-info "EvalFileV2 loaded" --threads 2 \
    --mask 0x1 --json "$(cygpath -w "$o/uci_conformance.json")" > "$o/uci_conformance.txt" 2>&1
rc=$?
echo "   conformance exit $rc: $(tail -1 "$o/uci_conformance.txt" | cut -c1-200)"
echo "$(date '+%F %T') done"
