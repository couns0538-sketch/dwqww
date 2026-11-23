# Neon's debate memory

Last updated: 2026-11-23T07:09:59Z (Neon's clock)
Phase: 4 POST-CLOSE ADDENDUM & LATER-PLAN RESEARCH (6-hour window through ~12:35-12:40Z; Fable checks ~every 30 min)

## Current Status
- Shared branch HEAD (before this push): `afb1b052fd`; Astra branch HEAD: `7c813fd516`.
- **Addendum items — "Changes to the items above":**
  - `A16`: agreed & filed (`20261123T064956Z_astra_agreed_a16.md`).
  - `A17`: agreed & filed (`20261123T065016Z_astra_agreed_a17.md`).
  - `N17`: agreed & filed (`20261123T065155Z_neon_agreed_n17.md`).
  - `A18` (cold position activity for `W1` & `W14`, Astra `065145Z`): **Neon independently verified every number bit-for-bit (`59/56/15` vs `0/0/0`, `60/60` vs `0/0/0`) and voted AGREE (`070959Z`).** Ready for `agreed_a18.md`.
- **Addendum items — "For later, once the engine is stronger":**
  - `A19` (Fable #1 deeper self-play labels, Astra `070539Z`): **Neon verified SHA-256 `9b8e833f...`, all 12,639 search and 1,536 game stats, WDL sigmoid sensitivity (~26% drop unsaturated), and discovered that production `warm2k` (`98.00 cp`, WDL `0.02592`) ALREADY closes 97.1% of the `cold2k -> cold8k` CP MAE gap (`124.72 -> 97.21 cp`, `warm_closer = 1,901 vs 1,050`, `corr = +0.6092`). Voted AGREE (`070959Z`) with a 1-sentence warm-vs-cold diagnostic sharpening.**
  - Verified Astra `065443Z` (draw-rate LLRs & sims, anchor Elo diffs, and `Threads=4` `softnodes 16` hard-cap overshoot `7/12 > 64`, max `148` + exact `search.cpp:2657, 3230-3247, 3352-3353` root cause).

## Active Neon Later-Plan Research
1. **Fable #4 (`N18` Threads / Lazy SMP):** TSan (`NNUEArch=true`, 2 & 4 threads, 5 stress suites) = `0` warnings; initial 5-FEN `go depth 16` showed `Threads=2` `0.89x` SLOWER than 1T and `Threads=4` only `1.28x` TTD despite `3.45x` NPS (`id_` unused in search -> zero helper diversification, `stripes_dirty_` `seq_cst` global cache-line ping-pong + `std::mutex`, per-move `std::thread` create/join, `search.cpp:3350-3354` stop clobber, `bare_king_mode` divergence, plus Astra's `softnodes` overshoot). Next: 20-position scaling + isolated `lock_stripe` ablation -> publish `N18`.
2. **Fable #6 (`N19` Clock Time Management):** Live-reproduced `SINGLE_Kxg2` burning `3,656 ms` / `13,629,020` nodes on a single legal move (`60+0.6`), constant `TmSoftDivisor=22` (`6.1x` move-1 vs move-40 in SD), `TmNodeShare` vs `effort_share_factor` redundancy, and `TmFinishIteration` unclamped `soft_basis*factor > hard_limit_ms_` bug. Next: verify `TmFinishIteration` unclamped-deadline case + check cross-move eval drop -> publish `N19`.
3. **Fable #2 & #3 (`N20` Measuring Stronger Engine + Reference Ladder):** Incorporate Astra's verified `065443Z` pair-shape & anchor-overlap bridge results + `PLAN §2` baseline -> publish `N20`.
4. **Fable #5 (`N21` Next NNUE shape beyond 1024 wide):** Benchmark AVX2/AVX-512 kernel latency + cache footprint + `W9` headroom math -> publish `N21`.
