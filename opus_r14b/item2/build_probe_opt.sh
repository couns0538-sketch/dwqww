#!/usr/bin/env bash
# build_probe_opt.sh OUT_DIR TRAIN_REQUESTS - Opus R14-B item 2 improvement: build the R13 relabel probe
# (opus_r13/p5/forge_data_probe.cpp on the lock source d4f4312, copy in C:\o13\p5\lock) with link-time optimisation
# and profile-guided optimisation. Same source and the same flags as R13's plain build (-O3 -march=znver5
# -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256 -static), plus:
#   OUT_DIR/lto/forge_data_probe.exe   -flto
#   OUT_DIR/pgo/forge_data_probe.exe   -flto + -fprofile-use (profile from the instrumented build running TRAIN_REQUESTS)
# GCC names the .gcda files after the OUTPUT file when a command compiles and links sources directly, so the
# instrumented and the optimised build both link to the same work path OUT_DIR/w/fdp.exe (moved away after each
# build), and missing-profile warnings stay on and are counted (a silent non-PGO build is the trap).
# The search is deterministic (fixed nodes, state cleared per position), so the labels must stay bit-identical:
# probe_bench.py checks that before any speed number is used. BelowNormal on CPU 2 (item 1's tools/lowrun.ps1);
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
mkdir -p "$out/w"
work=$(cygpath -w "$out/w/fdp.exe")
build() {  # build NAME "extra flags": link to the work path, then move the exe to OUT_DIR/NAME/
  mkdir -p "$out/$1"
  (cd "$lock" && powershell -NoProfile -File "$lowrun" -Mask 0x4 -Priority BelowNormal -Exe "$gxx" \
     -ArgLine "$base $2 $files -o $work" -Out "$(cygpath -w "$out/$1/build.log")" -Err "$(cygpath -w "$out/$1/build.err")")
  test -s "$out/w/fdp.exe" || { echo "build $1 failed" >&2; tail -20 "$out/$1/build.err" >&2; exit 1; }
  mv "$out/w/fdp.exe" "$out/$1/forge_data_probe.exe"
  echo "$1 $(sha256sum "$out/$1/forge_data_probe.exe" | cut -c1-64) missing-profile warnings: $(grep -c -i 'profile' "$out/$1/build.err" || true)"
}
build lto "-flto"
prof=$(cygpath -w "$out/prof")
mkdir -p "$out/prof"
build pgo_gen "-flto -fprofile-generate -fprofile-update=single -fprofile-dir=$prof"
# Training run: the same kind of work as the relabel (20k nodes, Hash 1 MB, one position after the other).
powershell -NoProfile -File "$lowrun" -Mask 0x4 -Priority BelowNormal -Exe "$(cygpath -w "$out/pgo_gen/forge_data_probe.exe")" \
  -ArgLine "--nodes 20000 --hash-mb 1" -In "$(cygpath -w "$train")" -Out "$(cygpath -w "$out/pgo_gen/train_out.jsonl")" \
  -Err "$(cygpath -w "$out/pgo_gen/train.err")" || true
echo "training answers: $(wc -l < "$out/pgo_gen/train_out.jsonl"), profile files: $(find "$out/prof" -name '*.gcda' | wc -l)"
build pgo "-flto -fprofile-use -fprofile-dir=$prof"
