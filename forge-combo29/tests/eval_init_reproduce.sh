#!/usr/bin/env bash
set -euo pipefail
repo=$(git rev-parse --show-toplevel)
cd "$repo"
lock=16833ecc03b425586f91f4c8834dea8807bf4c22
out=forge-combo29/tests/eval_init_evidence
mkdir -p "$out/include/forge"
git show "$lock:forge-combo29/src/eval.cpp" > "$out/baseline.cpp"
while read -r f; do git show "$lock:$f" > "$out/include/forge/${f##*/}"; done < <(git ls-tree -r --name-only "$lock" forge-combo29/include/forge)
${CXX:-g++} -std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1 -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_NNUE_ZMM=1 -ffp-contract=off -fno-fast-math -march=x86-64-v4 -I "$out/include" -S "$out/baseline.cpp" -o "$out/baseline.s"

python3 forge-combo29/tests/eval_init_generate_variants.py
for variant in conservative selective; do
  ${CXX:-g++}-std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1 -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_NNUE_ZMM=1 -ffp-contract=off -fno-fast-math -march=x86-64-v4 -I "$out/include" -DFORGE_SPD_EVAL_INIT=1 -S "$out/$variant.cpp" -o "$out/$variant.s"
done
