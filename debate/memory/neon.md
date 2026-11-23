# Neon's debate memory

Last updated: 2026-11-23T06:51:55Z (Neon's clock)
Phase: 4 POST-CLOSE ADDENDUM & LATER-PLAN RESEARCH (6-hour window through ~12:35-12:40Z; Fable checks ~every 30 min)

## Current Status
- Shared branch HEAD (before this push): `693df4d4fa`; Astra branch HEAD: `2a785b0191`.
- **Three Addendum entries (`Changes to the items above`) agreed 2/2 and filed for Fable's next check (~07:18Z):**
  - `A16`: Astra filed `20261123T064956Z_astra_agreed_a16.md` (Astra `064019Z`/`064928Z`, Neon `064747Z`, Fable proof `134816Z`).
  - `A17`: Astra filed `20261123T065016Z_astra_agreed_a17.md` (Astra `064306Z`/`064928Z`, Neon `064747Z`, Fable proof `134816Z`).
  - `N17`: Neon filed `20261123T065155Z_neon_agreed_n17.md` (Neon `064748Z`, Astra `065058Z`).

## Active Later-Plan Research Division ("For later, once the engine is stronger")
- Astra is running:
  - Fable #1: self-play label depth (`2k/8k/32k/128k/512k` on 384 openings + whole-game cost).
  - Fable #2: draw-rate / pair-shape operating curves.
  - Fable #3 (anchor overlap design) and a multithreaded soft-node ceiling issue (Astra asked Neon to prioritize independent verification once posted rather than parallel discovery on those two).
- Neon is actively running live measurements on unmodified `source/` (with `-DFORGE_NNUE_V3=1` + exact `CMakeLists.txt` flags) for the complementary later-plan frontiers:
  1. **Fable #4 (Threads / Lazy SMP architecture & scaling):** audit & measure TT `stripes_dirty_` `seq_cst` ping-pong + `std::mutex` contention at `Threads=1/2/4`, zero helper diversification (`id_` unused), per-move `std::thread` create/join overhead, `Searcher::search:3350-3354` external `stop` clobber race, and `ThreadSanitizer` with `NNUEArch=true`.
  2. **Fable #6 (Clock Time Management):** live measurement of missing single-legal-move early exit, constant `TmSoftDivisor=22` (no ply/phase curve), `TmFinishIteration`/`TmNodeShare` defaults & unclamped `soft_basis*factor` interaction, and cross-move eval-drop / fail-low handling.
  3. **Fable #5 (Next NNUE shape beyond 1024 wide):** SIMD AVX2/AVX-512 kernel latency + cache footprint + `W9` integer headroom for wider single-layer vs deeper `L1->L2->L3` candidates.
