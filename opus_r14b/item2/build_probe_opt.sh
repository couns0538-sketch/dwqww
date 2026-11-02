#!/usr/bin/env bash
# build_probe_opt.sh OUT_DIR TRAIN_REQUESTS - Opus R14-B item 2 improvement: build the R13 relabel probe
# (opus_r13/p5/forge_data_probe.cpp on the lock source d4f4312, copy in C:\o13\p5\lock) with link-time optimisation
# and profile-guided optimisation. Same source and the same flags as R13's plain build (-O3 -march=znver5
# -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256 -static), plus:
#   OUT_DIR/lto/forge_data_probe.exe   -flto
#   OUT_DIR/pgo/forge_data_probe.exe   -flto + -fprofile-use (profile from OUT_DIR/pgo_gen running TRAIN_REQUESTS)
# The search is deterministic (fixed nodes, state cleared per position), so the labels must stay bit-identical:
# probe_bench.py checks that before any speed number is used. BelowNormal on CPU 2 (tools/lowrun.ps1 of item 1);
# never overwrites (OUT_DIR must not exist).
set -euo pipefail
out=${1:?out dir}
train=${2:?training request file (id TAB analyze TAB fen per line)}
[ -e "$out" ] && { echo "refusing existing $out" >&2; exit 2; }
here=$(cd "$(dirname "$0")" && pwd)
src=$(cygpath -w "$here/../../opus_r13/p5/forge_data_probe.cpp")
lowrun=$(cygpath -w "$here/../../../o14b-l1/opus_r14b/item1/tools/lowrun.ps1")
lock=/c/o13/p5/lock
gxx='C:\msys64\ucrt64\bin\g++.exe'
base="-O3 -DNDEBUG -std=gnu++20 -march=znver5 -mtune=znver5 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256"
base="$base -static -frandom-seed=forge_data_probe -Wl,--no-insert-timestamp -Iinclude"
files="$src src/bitboard.cpp src/board.cpp src/book.cpp src/eval.cpp src/eval_params.cpp src/nnue.cpp src/search.cpp"
export PATH=/c/msys64/ucrt64/bin:$PATH
build() {  # build NAME "extra flags"
  mkdir -p "$out/$1"
  (cd "$lock" && powershell -NoProfile -File "$lowrun" -Mask 0x4 -Priority BelowNormal -Exe "$gxx" \
     -ArgLine "$base $2 $files -o $(cygpath -w "$out/$1/forge_data_probe.exe")" \
     -Out "$(cygpath -w "$out/$1/build.log")" -Err "$(cygpath -w "$out/$1/build.err")")
  test -s "$out/$1/forge_data_probe.exe" || { echo "build $1 failed" >&2; cat "$out/$1/build.err" >&2; exit 1; }
  echo "$1 $(sha256sum "$out/$1/forge_data_probe.exe" | cut -c1-64)"
}
build lto "-flto"
gen=$(cygpath -w "$out/pgo_gen/prof")
mkdir -p "$out/pgo_gen/prof"
build pgo_gen "-flto -fprofile-generate -fprofile-update=single -fprofile-dir=$gen"
# Training run: the same kind of work as the relabel (20k nodes, Hash 1 MB, one position after the other).
powershell -NoProfile -File "$lowrun" -Mask 0x4 -Priority BelowNormal -Exe "$(cygpath -w "$out/pgo_gen/forge_data_probe.exe")" \
  -ArgLine "--nodes 20000 --hash-mb 1" -In "$(cygpath -w "$train")" -Out "$(cygpath -w "$out/pgo_gen/train_out.jsonl")" \
  -Err "$(cygpath -w "$out/pgo_gen/train.err")" || true
echo "profile files: $(find "$out/pgo_gen/prof" -name '*.gcda' | wc -l)"
build pgo "-flto -fprofile-use -fprofile-dir=$gen -Wno-missing-profile"
