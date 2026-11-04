#!/usr/bin/env bash
# probe_extra.sh <name> <net> <control> <tag> <n> <movetime> [rounds=2] - checks of the GPU-trained v2 nets (2026-11-04):
# one more depth_probe_ab.py run (net B vs control A, same exe) with other probe parameters, through step.sh
# (Idle, CPU 0, trainer check, deadline). Outputs D:/o30/checks_gpu/<name>/depth_probe_<tag>.{txt,json}.
set -u
[ $# -ge 6 ] || { echo "usage: probe_extra.sh <name> <net> <control> <tag> <n> <movetime> [rounds]" >&2; exit 2; }
name="$1"; net="$2"; control="$3"; tag="$4"; n="$5"; mt="$6"; rounds="${7:-2}"
S=D:/o30/checks_gpu/scripts
O=D:/o30/checks_gpu/$name
EXE=D:/o30/w/v2p4_pc1/src_copy/forge_ltopgo_v2p4_pc1.exe
VPY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
PGN=D:/o30/control/lockkb4_v2p4/lockkb4_v2p4.pgn
expected=$(( n * (mt + 60) * 2 * rounds / 1000 + 20 ))
echo "probe_extra $name $tag start $(date '+%Y-%m-%d %H:%M:%S'): n $n, movetime $mt, rounds $rounds, expected ${expected} s"
bash "$S/step.sh" "$O/depth_probe_$tag.txt" "$expected" -- "$VPY" -I -B "$S/depth_probe_ab.py" "$PGN" "$EXE" "$EXE" \
  --opt-a "EvalFileV2=$control" --opt-b "EvalFileV2=$net" --n "$n" --movetime "$mt" --rounds "$rounds" --mask 0x1 \
  --json "$O/depth_probe_$tag.json"
echo "probe_extra $name $tag end $(date '+%Y-%m-%d %H:%M:%S') rc=$?"
