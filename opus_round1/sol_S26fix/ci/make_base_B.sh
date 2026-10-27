#!/usr/bin/env bash
# Rebuild Sol's S26 base B (forge_h256_e12_buffix_jobC_S01_src) from the AL1 lock source of this branch.
#   B = AL1 source files (identical to 294dbed3, which equals 6.4.24 1ab50b2d except the net)
#       - s198 net + h256_e12 net (74c4009d...)
#       + node-identical buffix (fc_sol_buffix_h256e12_vs_lock.patch, sha256 9ce56b3d...)
#       + B's pre-merge docs (lock archive 7_history/strength_packs/buffix_node_identical)
#       + Job C / S01 tests merge (merge_jobC_S01_base_h256e12_buffix_20261025.diff)
# The result must equal Sol's recorded 78-file snapshot exactly (compare_tree.py, exit 1 otherwise).
# usage: make_base_B.sh <repo_root> <NEW dest dir>
set -euo pipefail
ROOT=$(cd "$1" && pwd)
DEST=$2
HERE=$(cd "$(dirname "$0")" && pwd)
IN="$HERE/inputs"
if [ -e "$DEST" ]; then echo "make_base_B: destination exists: $DEST" >&2; exit 2; fi
mkdir -p "$DEST"
git -C "$ROOT" archive HEAD CMakeLists.txt IDEA_SOURCE.md README.md bench include src tests tools | tar -x -C "$DEST"
gzip -dc "$IN/nets/resid_h256_e12_e_ep12.inc.gz" > "$DEST/src/nnue_weights.inc"
(cd "$DEST" && patch -p1 -F0 --no-backup-if-mismatch -s < "$IN/B_recipe/fc_sol_buffix_h256e12_vs_lock.patch")
cp "$IN/B_recipe/README_h256e12_buffix_merged.md" "$DEST/README.md"
cp "$IN/B_recipe/IDEA_SOURCE_h256e12_buffix_merged.md" "$DEST/IDEA_SOURCE.md"
(cd "$DEST" && patch -p1 -F0 --no-backup-if-mismatch -s < "$IN/B_recipe/merge_jobC_S01_base_h256e12_buffix_20261025.diff")
"${PYTHON:-python3}" -B "$HERE/compare_tree.py" "$IN/B_source_snapshot.json" "$DEST"
