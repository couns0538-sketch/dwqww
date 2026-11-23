#!/usr/bin/env bash
# The engine for FORGENN3 nets from source forge/r15d (Opus, 2026-11-17): forge/r15c + the helper carbon2's E1
# step (forge/r15d/R15D_NOTE.txt): the same searches and output as r15c, faster self-play. Built exactly like r15
# (build_forge_v3r15_clang_pgo.sh): the profile step with the four B4 switches on, because the loop plays with them on.
# With every switch off it counts the same nodes as r15 (312866 / 862329 / 4865609 with the built-in net).
#
#   build_forge_v3r15d_clang_pgo.sh <out_exe> <net.fnn3 for the profile step>
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
export FORGE_SRC="${FORGE_SRC:-/c/nnue-lab/forge/r15d}"
export FORGE_PROFILE_OPTIONS="${FORGE_PROFILE_OPTIONS:-CuckooRep=true,HistRework=2,TtPruneV2=true,CorrHistV2=true}"
exec bash "$HERE/build_forge_v3_clang_pgo.sh" "$1" "$2"
