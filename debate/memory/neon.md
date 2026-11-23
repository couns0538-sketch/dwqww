# Neon's debate memory

Last updated: 2026-11-23T07:17:01Z (Neon's clock)
Phase: 4 POST-CLOSE ADDENDUM & LATER-PLAN RESEARCH (6-hour window through ~12:35-12:40Z; Fable checks ~every 30 min)

## Current Status
- Shared branch HEAD (before this push): `816c6277cd`; Astra branch HEAD: `a540f1bb90`.
- **Agreed & filed Addendum entries (waiting on Fable's ~07:18Z check):**
  - *Changes to the items above:* `A16` (`064956Z`), `A17` (`065016Z`), `N17` (`065155Z`), `A18` (`071114Z`).
  - *For later, once the engine is stronger:* `A19` (Fable #1 deeper self-play labels, `071136Z` — incorporates Neon's `warm2k = 98.00 cp` vs `cold2k = 124.72 cp` vs `cold8k = 97.21 cp` finding; Astra running full matched warm replay `070804Z`).
- **New Neon later-plan proposals posted (`071700Z`, `071701Z`):**
  - `N18` (Fable #4 — Multi-threaded search / `Threads > 1` before match play): unifies Astra's `065443Z` `softnodes` overshoot with Neon's TSan (`NNUEArch=true`, 0 reports), 20-FEN 1/2/4T TTD scaling (`1.21x–1.37x` TTD for `3.09x–3.16x` NPS), isolated `lock_stripe` / `stripes_dirty_` ablation, unused `id_` / missing voting, `bare_king_mode` (`11.7x` node / `4.3x` time divergence at 2T), and `search.cpp:3350-3354` async-stop clobber.
  - `N19` (Fable #6 — Clock time management): live-reproduced `3,656 ms` / `13.6M` nodes burned on single legal move `SINGLE_Kxg2` (`60+0.6`), flat `TmSoftDivisor=22` (`3.1x–6.1x` mv1/mv40 ratio), unclamped `TmFinishIteration` deadline `soft_basis * factor > hard_limit_ms_` (`search.cpp:3215`), and `TmFinishIteration`/`TmNodeShare` live comparison.

## Ready Next (waiting one cycle so proposals stay cleanly paced, one batch at a time)
- **Fable #5 (`N21` Next NNUE shape beyond 1024 wide):** ALL live proofs already collected!
  - Exact `int32` overflow reproduced in `nnue_v3.cpp:125`: AVX2 wraps at `H = 1056` (`-16,918,472,768` vs `+17,441,265,600`), `1536`, `2048` while AVX-512 stays exact up to `H = 2048` (silent cross-ISA divergence!). Widening `sum0`/`sum1` before adding (`avx2_wide`) fixes AVX2 up to `H = 2048` with 0 extra loop instructions.
  - Zero-confounded real-engine NPS (`bench 15`, bit-identical `1,667,608` nodes via zero-padded `r67` `768 -> 1024`): `-4.32%` on AVX-512 (`2.36M -> 2.25M`), `-8.84%` on AVX2 (`2.19M -> 1.99M`).
  - Live kernel microbenchmark (`2M` iters): `768 1L = 55.9 ns`, `1024 1L = 72.8 ns`, `1536 1L = 106.2 ns`, `2048 1L = 140.9 ns` (`1,152 KiB` worker cache > 1 MiB L2!), `2L VNNI (H->16->32->1)` = `163.4 / 214.3 / 326.3 / 430.4 ns`.
- **Fable #2 & #3 (`N20` Measuring Stronger Engine + Reference Ladder):** Incorporating Astra's verified `065443Z` draw-rate pair-shape operating curves + anchor-overlap bridge math + `PLAN §2` SF10/SF11/SF19-3100 baseline.
- Also awaiting Astra's full 384-opening matched warm replay (`070804Z`) to cross-check its raw numbers!
