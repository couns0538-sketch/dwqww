# Castling accumulator fusion review

Status: **UNPROVEN** for speed or Elo. Disabled by default. No network or evaluation constants changed. GCC 14 results below establish tested arithmetic equivalence, not equivalence on every compiler or target.

Run from the repository root (the directory containing `forge-combo29`). Output directory used for this review: `/workspace/shared/forge-build`.

## Bit-exact regression

```sh
mkdir -p /workspace/shared/forge-build
for mode in off on on-native on-scalar; do
  flags=''
  case "$mode" in
    on) flags='-DFORGE_SPD_NNUE_CASTLE_FUSE=1';;
    on-native) flags='-DFORGE_SPD_NNUE_CASTLE_FUSE=1 -march=native';;
    on-scalar) flags='-DFORGE_SPD_NNUE_CASTLE_FUSE=1 -fno-tree-vectorize';;
  esac
  g++-14 -std=c++20 -O3 -ffp-contract=off -fno-fast-math \
    -DFORGE_NNUE_HIDDEN=256 $flags -Iforge-combo29/include \
    forge-combo29/tests/nnue_castling_fusion.cpp \
    forge-combo29/src/board.cpp forge-combo29/src/bitboard.cpp \
    -o /workspace/shared/forge-build/nnue-castle-$mode
  /workspace/shared/forge-build/nnue-castle-$mode
done
```

Each configuration passed **12,972 cases**, comparing every accumulator float's raw bits against a generic, sequential updater with the shipped weights. Cases cover both perspectives, all four castling directions from three legal board fixtures, realistic refreshed accumulators, random finite IEEE-754 inputs, signed zeros, all four-change add/remove patterns, counts zero through four, and both distinct and aliased input/output accumulators. The default-off configuration leaves the original fallback intact. Quiet/capture fusion remains unchanged.

## AddressSanitizer and UndefinedBehaviorSanitizer

```sh
g++-14 -std=c++20 -O1 -g -fsanitize=address,undefined \
  -fno-omit-frame-pointer -ffp-contract=off -fno-fast-math \
  -DFORGE_NNUE_HIDDEN=256 -DFORGE_SPD_NNUE_CASTLE_FUSE=1 \
  -Iforge-combo29/include forge-combo29/tests/nnue_castling_fusion.cpp \
  forge-combo29/src/board.cpp forge-combo29/src/bitboard.cpp \
  -o /workspace/shared/forge-build/nnue-castle-sanitize
ASAN_OPTIONS=detect_leaks=0 /workspace/shared/forge-build/nnue-castle-sanitize
```

Result: **PASS: 12972 cases**, with no ASan or UBSan diagnostics. The first run with default sanitizer settings could not complete LeakSanitizer: it reported that LeakSanitizer does not work under ptrace. Disabling leak detection allowed the address/undefined-behavior checks above to complete. Leak checking remains unverified.

## Full-engine compilation

Both switch values compiled successfully with this portable strict-FP recipe. Other concurrently reviewed patches were present in the workspace; these compilation checks do not establish an isolated performance comparison.

```sh
for mode in 0 1; do
  g++-14 -std=c++20 -O3 -ffp-contract=off -fno-fast-math \
    -march=x86-64-v3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 \
    -DFORGE_EXPOSE_TUNABLES=1 -DFORGE_SPD_TT_NOTLS=1 \
    -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1 \
    -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=0 \
    -DFORGE_SPD_NNUE_ZMM=0 -DFORGE_SPD_NNUE_CASTLE_FUSE=$mode \
    -Iforge-combo29/include forge-combo29/src/*.cpp -pthread \
    -o /workspace/shared/forge-build/nnue-castle-engine-$mode
done
```

No speed, search-node, playing-strength, or Windows/Clang result is claimed here.
