# Neon's debate memory

Last updated: 2026-11-23T06:47:48Z (Neon's clock)
Phase: 4 POST-CLOSE ADDENDUM & LATER-PLAN RESEARCH (6-hour window through ~12:35-12:40Z; Fable checks ~every 30 min)

## Current Status
- Shared branch HEAD (before this push): `281c1a7ba3`; Astra branch HEAD: `c2cbc8aa8c`.
- Phase 3 closed 3/3 AGREE on `R1`–`R6` and `W1`–`W16` (`5ed482d6ad`); Fable opened two Addendum lists in `debate/FINAL_PLAN.md` (`f367231ae2`, `20261123T134155Z_fable_owner_six_hours.md`):
  1. "Changes to the items above"
  2. "For later, once the engine is stronger" (requires `WHEN / WHAT / TEST / BAR / WHY IT WAITS` + proof/reproducible mechanism).
  - Entry rule: one `..._<name>_agreed_<item>.md` with final wording, reproducible proof, and both vote message IDs; Fable verifies and appends to `FINAL_PLAN.md`.
- **Addendum item tracking:**
  - `A16` (Astra `064019Z` + `064041Z` half-cap control): **Neon independently verified all 3 checks + half-cap control and voted AGREE (`064747Z`).** Waiting for Astra's 1-line OK on folding `064041Z` half-cap/verdict check into `..._agreed_a16.md`.
  - `A17` (Astra `064306Z`): **Neon independently verified all numbers (`0.007353054257` vs `0.118110236220`, closed forms, 2,048-shuffle `p1/p99 = 0.006999/0.007528`) and voted AGREE (`064747Z`).** Ready for `..._agreed_a17.md`.
  - `N17` (Neon `064748Z`): Full `768`/`1024` `nnue_v3` loader/cross-ISA/UCI failure-path audit posted with 1-command reproducer. All 7 positive 768/1024 fixtures and 4-build (`AVX-512`/`AVX2`/`scalar`+`VERIFY=1`, `ASan+UBSan`) UCI parity passed cleanly; 5 real failure-path bugs reproduced in `source/src/uci.cpp` & `nnue_v3.cpp` (`eval` silent fallback, `UseNNUE false` silent HCE lie, Linux directory `SIGABRT`, `NNUEArch`-before-`NNUEArchFile` `N15` `ERROR` trap, `load()` accepting `FlagResidual`). Awaiting Astra's independent verification and vote.

## Parallel Later-Plan Research Division
- Astra is running Fable #1 (`measure_future_label_depth.md`: 384 openings, `2k/8k/32k/128k/512k` label depth + online cost).
- Neon is investigating complementary later-plan tracks on this 4-core AVX-512 Linux VM:
  1. Fable #4: Multi-threaded search (`Threads > 1` / Lazy SMP) code audit + ThreadSanitizer (2 and 4 threads) + 1/2/4-thread NPS/TT/time-to-depth benchmarks on unmodified `source/`.
  2. Fable #6: Clock time management audit (`source/src/search.cpp`, `uci.cpp`).
  3. Fable #2 & #3: Draw-rate variance/sample-size collapse curve + reference ladder past SF12/14/15/16.
  4. Fable #5: Next NNUE architecture beyond `1024` wide (SIMD microbenchmarks + `W9` headroom math).
