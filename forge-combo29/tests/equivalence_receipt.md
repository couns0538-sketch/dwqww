# Deterministic cloud equivalence screen, 2026-11-10

Result: **256 comparisons passed, zero mismatches**. This is 128 unique fresh
FENs, each searched with NNUE on and off, against both binaries (512 searches).
Compared final reported depth, node count, score type/value, bestmove and full
PV. Complete compared records are retained in `equivalence_results.json`.

## Inputs and settings

- Baseline binary: `/workspace/shared/forge-build/baseline`
- Baseline SHA-256: `1371770e2ad61aa2fe3c038acc7da3912da5d64c9cb1dcc5e4668221fb3226f6`
- Enabled binary: `/workspace/shared/forge-build/final-validation/enabled`
- Enabled SHA-256: `21d64ae060cf54614a8a0761b9711b776dc91278f8e8bdab4fa6ecdc62fb9d74`
- Fixture SHA-256: `6538341dbe9393fa1933633b2446505140b4c809c0f13af066fbef54207dd723`
- UCI: Threads 1, Hash 16 MB, OwnBook false, depth 7; UseNNUE true then false.
- `ucinewgame` and `isready` before every FEN reset histories and hash; each
  position is reloaded from FEN, without previous playout repetition history.
- All searches are sequential, with no concurrent engine searches in this test.
- Binary hashes were checked again after completion and were unchanged.
- Baseline NNUE-on/off results differ for 117 of 128 fixtures, providing a
  sanity check that the two modes were not accidentally identical.

The enabled binary was built by the parent validation job from engine source
through `dd1d783`, using the recipe retained in `tests/review_build.sh`:
GCC 14, C++20, O3, NDEBUG, strict FP (`-ffp-contract=off -fno-fast-math`),
x86-64-v4, pthread; NNUE hidden 256, exposed tunables, TT_NOTLS=1,
NO_ZERO_MOVELISTS=2, SEARCH_SPEED2=1, PREFETCH_EARLY=1, SLIDER_PEXT=1,
NNUE_ZMM=1. The eight enabled switches are SMP_NODE_RESET, SMP_FINAL_NODES,
SMP_STOP_LATCH, UCI_OPTION_CASE, BOOK_LEGAL_REUSE, NNUE_CASTLE_FUSE,
ATTACKS_INIT_ONCE and SMP_EXCEPTIONS, with their full `FORGE_*` spellings in
that recipe. The binary hashes identify the tested executables definitively.

## Fixture generation and reproduction

`equivalence_positions.cpp` uses SplitMix64 seed `0x464F524745202611` and
Board::legal_moves/make_move. It emits 16 explicit corners plus 112 unique
playout positions. Length targets cycle through 4, 12, 32, 64, 96, 160 and 240
plies plus 0–7 plies; terminal/100-halfmove positions stop early. Corners cover
castling, en passant, promotions, check, checkmate, stalemate, insufficient
material and the 99/100-halfmove boundary. A second generator run reproduced
the fixture byte for byte.

From `forge-combo29`:

```sh
g++-14 -std=c++20 -O2 -pthread -Iinclude tests/equivalence_positions.cpp \
  src/board.cpp src/bitboard.cpp -o /tmp/forge-equivalence-generator
/tmp/forge-equivalence-generator > /tmp/equivalence_positions.fen
cmp tests/equivalence_positions.fen /tmp/equivalence_positions.fen
python3 tests/equivalence_screen.py BASELINE_BINARY ENABLED_BINARY \
  --output /tmp/equivalence_results.json
```

## Limits

This is a small, shallow T1 cloud screen, not the native PC 12,000-position
comparison, long-search validation, an SMP determinism claim, or an Elo/speed
result. Move generation uses Forge itself, not an independent legality oracle.
Fixture play is random rather than game-strength play. Fresh FENs deliberately
omit repetition histories. Timings, NPS and hashfull were not compared.
