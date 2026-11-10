#!/usr/bin/env bash
set -euo pipefail
repo=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
out=${1:-/tmp/forge-default-lock-objects}
mkdir -p "$out"
out=$(cd "$out" && pwd)
export FORGE_OBJECT_DIAGNOSTIC_DIR="$out"
flags=(-std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1 -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_NNUE_ZMM=1 -ffp-contract=off -fno-fast-math -march=x86-64-v4 -pthread -Iinclude)
for entry in 'lock 16833ec' 'reviewed 31c5d202e6662c159976a70de5803d220acee2e1'; do
 read -r label rev <<<"$entry"
 rm -rf "$out/source"
 mkdir -p "$out/source" "$out/$label-objects"
 git -C "$repo" archive "$rev" -- forge-combo29/src forge-combo29/include | tar -x -C "$out/source"
 (cd "$out/source/forge-combo29"; /usr/bin/g++-14 "${flags[@]}" -c src/*.cpp)
 cp "$out/source/forge-combo29/"*.o "$out/$label-objects/"
done
python3 - <<'PY'
import pathlib,hashlib,json
import os
p=pathlib.Path(os.environ['FORGE_OBJECT_DIAGNOSTIC_DIR']);rows=[]
for a in sorted((p/'lock-objects').glob('*.o')):
 b=p/'reviewed-objects'/a.name
 h=lambda x:hashlib.sha256(x.read_bytes()).hexdigest()
 rows.append({'object':a.name,'lock_sha256':h(a),'reviewed_sha256':h(b),'identical':a.read_bytes()==b.read_bytes()})
(p/'object-comparison.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows,indent=2))
PY
