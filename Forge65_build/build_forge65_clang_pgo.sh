#!/usr/bin/env bash
# forge6.5, the PLAY exe (Fable, 2026-11-23; teamwork/OWNER_ORDER_2311.md, forge/r65/R65_NOTE.txt): source forge/r65
# (= forge/r15dsg + the compile switch FORGE65: the net inside the exe, the loop's settings applied at the start),
# built exactly as build_forge_v3r15dsg_sp_clang_pgo.sh builds the loop's exe (same compiler, flags, profile work:
# bench 11 / 13 / 16 with the net and 60 self-play games through pgo_selfgame.py), with -DFORGE65=1 added.
# That chain's build_forge_v3_clang_pgo.sh sets FORGE_DEFINES itself, so this script calls the base script directly
# with the chain's own values.
#
#   build_forge65_clang_pgo.sh <out_exe> <net.fnn3 for the profile step>
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
export FORGE_SRC="${FORGE_SRC:-/c/nnue-lab/forge/r65}"
export FORGE_DEFINES="-DFORGE_MATE_ALPHA_GUARD=1 -DFORGE_NNUE_V3=1 -DFORGE65=1"
export FORGE_PROFILE_OPTIONS="${FORGE_PROFILE_OPTIONS:-CuckooRep=true,HistRework=2,TtPruneV2=true,CorrHistV2=true}"
export FORGE_V3_NET="$(cygpath -u "$2")"
export PGOSP_GAMES="${PGOSP_GAMES:-60}"
export PGOSP_PY="${PGOSP_PY:-C:/nnue-lab/venv101/Scripts/python.exe}"
export PGOSP_DRIVER="$(cygpath -m "$HERE/pgo_selfgame.py")"
export PGOSP_CFG="${PGOSP_CFG:-C:/nnue-lab/pipeline/config.forge.toml}"
export PGOSP_EPD="$(cygpath -m "$HERE/pgo_selfplay_books.epd")"
# The net inside the exe must be the net named for the profile step, or the exe would be profiled with another one.
cmp "$FORGE_SRC/src/forge65_net.fnn3" "$FORGE_V3_NET" || { echo "STOP: $FORGE_SRC/src/forge65_net.fnn3 is not $2"; exit 1; }
exec bash "$HERE/build_forge_clang_pgo.sh" "$1"
