#!/usr/bin/env bash
# The loop's engine WITH the game loop inside (Opus, 2026-11-20; tmp/opus_scratch/selfgame_pc/PLACE_PLAN.txt, step 2):
# forge/r15dsg = forge/r15d + carbon2's selfgame patch v3 (forge/r15dsg/R15DSG_NOTE.txt), built exactly as
# build_forge_v3r15d_sp_clang_pgo.sh builds r15d, except that the 60 self-play games of the profile step are played
# the way the loop will play them: ONE `selfgame` line a game (pgo_selfgame.py), never `go`. Without that command the
# exe searches as r15d does.
# BUILD IT BY HAND, with PGOSP_CFG naming a config whose own exe exists (pgo_selfgame.py refuses otherwise: it asks
# engine_for_net for the loop's options, and engine_for_net builds a missing exe, which inside this build would start
# the same build again). Copied to forge/tools at step 2, beside pgo_selfgame.py.
#
#   build_forge_v3r15dsg_sp_clang_pgo.sh <out_exe> <net.fnn3 for the profile step>
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
export FORGE_SRC="${FORGE_SRC:-/c/nnue-lab/forge/r15dsg}"
export PGOSP_GAMES="${PGOSP_GAMES:-60}"
export PGOSP_PY="${PGOSP_PY:-C:/nnue-lab/venv101/Scripts/python.exe}"
export PGOSP_DRIVER="$(cygpath -m "$HERE/pgo_selfgame.py")"
export PGOSP_CFG="${PGOSP_CFG:-C:/nnue-lab/pipeline/config.forge.toml}"
export PGOSP_EPD="$(cygpath -m "$HERE/pgo_selfplay_books.epd")"
exec bash "$HERE/build_forge_v3r15d_clang_pgo.sh" "$1" "$2"
