STATE: IN PROGRESS

# b2_slider_pext: FORGE_SPD_SLIDER_PEXT mode 1 (spec S2: PEXT index on the lock's slider-table layout)

Worker b2mg (fable), job B part 2, branch opus-speed-20261105. Source edits 09:41-09:44 PC clock (`date`); built only after
changes 1-4 (task order: "only if time remains").
Patch: `F:/ospd/wt/opus_speed/patches/b2_slider_pext.patch` (89 lines; files bitboard.hpp, bitboard.cpp; applies with `patch -p1`
to a fresh lock copy and reproduces `F:/ospd/src/b2_slider_pext`: apply test in `F:/ospd/src/b2_applytest_slider_pext`). One
switch line `#define FORGE_SPD_SLIDER_PEXT 0` in bitboard.hpp (top of the file, before the conditional `<immintrin.h>`).

## Design (own words)
Mode 1 of spec S2 only: the per-square record becomes {mask, table*} (16 B instead of 32 B) and `index(occ) =
_pext_u64(occ, mask)`; `init_magics` fills `table[pext(s, mask)] = sliding_attack(sq, s)` for every subset s of the mask
(carry-rippler enumeration, no random magic search, so start-up is shorter and seed-free). Every subset has its own index
in [0, 2^popcount(mask)), and the lock's tables are exactly sum over squares of 2^popcount(mask) entries (0x19000 rook,
0x1480 bishop), so the tables keep their sizes; only the entry order changes. `bishop()`, `rook()`, `queen()` and all 37
call sites are untouched (they go through `m.index()` and `m.table`). Modes 2-3 (16-bit PDEP entries, compile-time tables)
are not built. BMI2 is required: `#error` without `__BMI2__` (znver5 defines it; a Zen 1 / 2 or generic side cannot enable
the switch).

## Lines touched (lock numbering)
- include/forge/bitboard.hpp: after the includes (:5) the switch block + conditional `<immintrin.h>` (+ `#error`); :143-152
  `struct Magic` PEXT form under `#if`, the lock struct verbatim under `#else`.
- src/bitboard.cpp: :63-108 `init_magics` PEXT fill under `#if`, the lock function verbatim under `#else`.
- Switch 0: `g++ -E -P` of all eight .cpp files is byte-identical to the lock's (`F:/ospd/jobb/b2/slider_pext/pp/`).

## Why node-identical
Both index functions return the same attack set for every (square, occupancy) (every bit outside the mask is ignored by
PEXT as by the lock's `& mask`), proven exhaustively (below); the move generator, SEE, gives_check and the HCE read only
those attack sets, so every node is the same.

## Checks
PENDING (chain D): exhaustive test `F:/ospd/jobb/b2/tools/b2_slider_test.cpp` (every square x every subset of its relevant mask
= 102,400 rook + 5,248 bishop cases, + 64 empty-board cases, + 1,000,000 random occupancies with bits outside the mask,
against an own ray walk; run for the switch at 1 and at 0), (a) switch-0 exe cmp, (b) lp_check net on / off, pext count.

## Risks
- Expected gain for mode 1 alone is 0 to +1 % (spec, UNPROVEN): the and-imul-shr chain becomes one pext (latency 3 on Zen 5).
- Start-up table fill order differs from the lock (no behavioural effect; the tables are read-only after init()).
