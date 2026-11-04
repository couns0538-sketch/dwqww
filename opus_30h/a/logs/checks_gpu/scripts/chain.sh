#!/usr/bin/env bash
# chain.sh <name> <net .nnue2> <control .nnue2> [tag] - checks of the GPU-trained v2 nets (2026-11-04): the three checks
# of one net, each through step.sh (Idle, CPU 0 only, trainer check, deadline): 1. smoke2m.py 300 s (Threads 2, Hash 16,
# the gate path, as net_final_checks.sh step 1), 2. uci_conformance_o30.py with the net loaded, 3. depth_probe_ab.py:
# the net (B) vs its control (A) on the same exe, 200 game positions, movetime 200, 2 rounds. With a tag only the probe
# runs (a repeat for run-to-run noise). Outputs: D:/o30/checks_gpu/<name>/. Paths given to the engine use forward slashes.
set -u
[ $# -ge 3 ] || { echo "usage: chain.sh <name> <net> <control> [tag]" >&2; exit 2; }
name="$1"; net="$2"; control="$3"; tag="${4:-}"
S=D:/o30/checks_gpu/scripts
O=D:/o30/checks_gpu/$name
EXE=D:/o30/w/v2p4_pc1/src_copy/forge_ltopgo_v2p4_pc1.exe
VPY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
T=D:/o30/wt/opus_30h/tools
PGN=D:/o30/control/lockkb4_v2p4/lockkb4_v2p4.pgn
mkdir -p "$O"
echo "chain $name start $(date '+%Y-%m-%d %H:%M:%S'), net $net, control $control, tag '${tag}'"
if [ -z "$tag" ]; then
  bash "$S/step.sh" "$O/probe_dryrun.txt" 20 -- "$VPY" -I -B "$S/depth_probe_ab.py" "$PGN" "$EXE" "$EXE" --n 200 --mask 0x1 --dry-run
  unset START_AT
  bash "$S/step.sh" "$O/smoke_300s.txt" 330 -- "$VPY" -I -B "$T/smoke2m.py" "$EXE" --line "EvalFileV2=$net" \
    --seconds 300 --threads 2 --hash 16 --mask 0x1 --idle --out "$O/smoke_300s"
  bash "$S/step.sh" "$O/uci_conformance.txt" 150 -- "$VPY" -I -B "$T/uci_conformance_o30.py" "$EXE" \
    --opt "EvalFileV2=$net" --expect-info "EvalFileV2 loaded" --threads 2 --mask 0x1 --json "$O/uci_conformance.json"
  bash "$S/step.sh" "$O/depth_probe.txt" 300 -- "$VPY" -I -B "$S/depth_probe_ab.py" "$PGN" "$EXE" "$EXE" \
    --opt-a "EvalFileV2=$control" --opt-b "EvalFileV2=$net" --n 200 --movetime 200 --rounds 2 --mask 0x1 \
    --json "$O/depth_probe.json"
else
  bash "$S/step.sh" "$O/depth_probe_$tag.txt" 300 -- "$VPY" -I -B "$S/depth_probe_ab.py" "$PGN" "$EXE" "$EXE" \
    --opt-a "EvalFileV2=$control" --opt-b "EvalFileV2=$net" --n 200 --movetime 200 --rounds 2 --mask 0x1 \
    --json "$O/depth_probe_$tag.json"
fi
echo "chain $name end $(date '+%Y-%m-%d %H:%M:%S')"
