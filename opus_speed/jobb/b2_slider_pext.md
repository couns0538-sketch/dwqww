STATE: READY FOR TIMING

# b2_slider_pext: FORGE_SPD_SLIDER_PEXT mode 1 (spec S2: PEXT index on the lock's slider-table layout)

Worker b2mg (fable), job B part 2, branch opus-speed-20261105. Source edits 09:41-09:44 PC clock; test, builds and checks
10:02-10:07 (chain log `F:/ospd/jobb/b2/chain_d.log`); notes finished 10:08 (`date`). Built last (task order: "only if time remains").
Patch: `F:/ospd/wt/opus_speed/patches/b2_slider_pext.patch` (adds 46 lines, removes none; files bitboard.hpp, bitboard.cpp; applies
with `patch -p1` to a fresh lock copy and reproduces `F:/ospd/src/b2_slider_pext`: apply test in `F:/ospd/src/b2_applytest_slider_pext`).
One switch line `#define FORGE_SPD_SLIDER_PEXT 0` in bitboard.hpp (top of the file, before the conditional `<immintrin.h>`, so a
flipped line still pulls the intrinsic header). Deliverable patches of this job: b2_nnue_zmm, b2_no_zero_movelists, b2_matkey_fast,
b2_pickbest, b2_slider_pext.

## Design (own words)
Mode 1 of spec S2 only: the per-square record becomes {mask, table*} (16 B instead of 32 B) and `index(occ) =
_pext_u64(occ, mask)`; `init_magics` fills `table[pext(s, mask)] = sliding_attack(sq, s)` for every subset s of the mask
(carry-rippler enumeration, no random magic search, so start-up is shorter and seed-free). Every subset has its own index
in [0, 2^popcount(mask)), and the lock's tables are exactly sum over squares of 2^popcount(mask) entries (0x19000 rook,
0x1480 bishop), so the tables keep their sizes; only the entry order changes. `bishop()`, `rook()`, `queen()` and every
call site are untouched (they go through `m.index()` and `m.table`). Modes 2-3 (16-bit PDEP entries, compile-time tables)
are not built. BMI2 is required: `#error` without `__BMI2__` (znver5 defines it; a Zen 1 / 2 or generic side cannot enable
the switch, so a wrong machine fails at compile time).

## Lines touched (lock numbering)
- include/forge/bitboard.hpp: after the includes (:5) the switch block + conditional `<immintrin.h>` (+ `#error`); :143-152
  `struct Magic` PEXT form under `#if`, the lock struct verbatim under `#else`.
- src/bitboard.cpp: :63-108 `init_magics` PEXT fill under `#if`, the lock function verbatim under `#else`.
- Switch 0: `g++ -E -P` of all eight .cpp files is byte-identical to the lock's (`F:/ospd/jobb/b2/slider_pext/pp/`).

## Why node-identical
Both index functions return the same attack set for every (square, occupancy): bits outside the mask are ignored by PEXT
as by the lock's `& mask`, and the table holds sliding_attack(sq, subset) at every reachable index (exhaustive test
below). The move generator, SEE, gives_check, checkers and the HCE read only those attack sets, so every node is the same.

## Checks
(c) exhaustive test `F:/ospd/jobb/b2/tools/b2_slider_test.cpp` linked with the copy's src/bitboard.cpp (own ray-walk reference):
    every square x every subset of its relevant mask (102,400 rook + 5,248 bishop = 107,648 subset cases) + 64 empty-board
    cases + 1,000,000 random (square, occupancy) pairs with bits outside the mask, rook / bishop / queen each time:
    switch 1: "107648 subset cases + 1107712 checks total, 0 mismatches: PASS" (`F:/ospd/jobb/b2/slider_pext/b2_slider_test_on.log`);
    switch 0 (the lock magics, same harness): the same counts, 0 mismatches, PASS (`b2_slider_test_off.log`).
(a) switch-0 exe `forge_px_off.exe` (sha256 3b9eec3e...) vs the lock plain exe: `cmp -l` differs only at bytes 137 138 217 218. PASS.
(b) switch-on exe `forge_px_on.exe` (94f22cd1...): net on vs `lock_plain_neton.json` with the pins (bench d11-d22 and perft
    startpos 4865609 / kiwipete 193690690): 24/24 OK, NODE IDENTITY ALL OK (`px_on_neton.compare.log`); net off (UseNNUE=false)
    with the net-off pins: 24/24 OK (`px_on_netoff.compare.log`).
    codegen (`objdump/px_on.dis` vs the lock plain listing): exact `pext` mnemonic 0 -> 105, `imul` 571 -> 476 (the multiply
    magics are gone from the inlined lookups), `pdep` 0 -> 0, `vpextr*` 51 -> 51 (unrelated extract instructions; the chain
    log's raw "pext" count 51 -> 157 includes them). vfmadd 0 in both exes (build logs).
    Not run: the spec's microbench (i)-(iii) and perft nps (no timing by me); the coordinator's ABBA decides.

## Risks
- Expected gain for mode 1 alone is 0 to +1 % (spec, UNPROVEN): the and-imul-shr chain becomes one pext (latency 3 on Zen 5);
  the table footprint is unchanged (841 KiB), so no cache effect. Modes 2-3 are where the spec expects more.
- Start-up table fill order differs from the lock (no behavioural effect; the tables are read-only after init()).
