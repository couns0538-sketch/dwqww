#!/usr/bin/env bash
# The engine for FORGENN3 nets ("v3": king-bucketed, loaded from a file with the options NNUEArchFile and NNUEArch):
# source forge/r7, the v3 path compiled in, built by build_forge_clang_pgo.sh with the profile step run on the
# given v3 net. ONE exe serves every v3 net (the net is an option, not compiled in); the compiled-in net is the
# lock's and is not used while a v3 net is active.
#
#   build_forge_v3_clang_pgo.sh <out_exe> <net.fnn3 for the profile step>
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
export FORGE_SRC="${FORGE_SRC:-/c/nnue-lab/forge/r7}"
export FORGE_DEFINES="-DFORGE_MATE_ALPHA_GUARD=1 -DFORGE_NNUE_V3=1"
export FORGE_V3_NET="$(cygpath -u "$2")"
exec bash "$HERE/build_forge_clang_pgo.sh" "$1"
