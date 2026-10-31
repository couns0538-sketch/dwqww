#!/usr/bin/env bash
# export_src.sh <scratch repo> <out dir> - clean LF export of the working tree's tracked files (no .git, no build leftovers)
# for the LTO+PGO kit (it refuses trees with .o/.gcda/.exe/obj_*/pgo_*). Commits nothing; uses `git stash create` -free path:
# it copies `git ls-files` from the working tree, so uncommitted edits ARE included.
set -euo pipefail
src="$1"; out="$2"
[ -e "$out" ] && { echo "refusing: $out exists" >&2; exit 2; }
mkdir -p "$out"
cd "$src" && git ls-files -z | xargs -0 -I{} cp --parents {} "$out/"
echo "exported $(find "$out" -type f | wc -l) files to $out"
