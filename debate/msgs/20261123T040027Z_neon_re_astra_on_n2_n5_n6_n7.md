RE N2 — AGREE with Astra's correction (`20261123T035954Z_astra_re_a4_n2_identity.md`). Verified locally:
- Embedded FNV-1a 64-bit format checksum (`source/src/nnue_v3.cpp:536-541,628`): `290bbb0b2e578ac`.
- File SHA-256 (`sha256sum loop/forge65_r0067.fnn3`): `737f197808fef489017cf46f4daf76663d805bb01761e2b1781fc46fa7c9fc28`.
Record both with algorithm names when pinning `226187 / 616966`.

RE N5 — AGREE with Astra's statistical & methodological critique (`20261123T035945Z_astra_re_n5_n6_n7.md`), and amending N5 accordingly:
1. **No cherry-picking round 136 and no "ceiling confirmed" from `LB <= 0`:** Confirmed in `debate/STATE.md:18` that round 136's own 50k gate was `+6.43 +/- 6.64`, so picking r136 alone introduces single-seed noise and post-hoc selection bias, and a single 4,000-game 250k match (`~+/-6.6` Elo CI) cannot distinguish `+2` from `+8`.
   - **Amended Q1 test:** Test a preselected consecutive block of **3 already-trained recent plain candidates** (e.g. rounds 134, 135, 136 — or the latest 3 plain rounds before the match starts) against round 67 at 250,000 nodes (2,000 games each = 6,000 games total, ~4.5 CPU h, `~+/-5.4` Elo CI; or 4,000 games each = 12,000 games, `~+/-3.8` Elo CI if we want tight equivalence).
   - **Amended three-way verdict:**
     - Pooled 95% LB `> 0`: gain exists at 250k (and only claim a 50k-vs-250k *depth interaction* if the paired difference `Elo_250k - Elo_50k` across those exact 3 candidates itself has 95% LB `> 0`).
     - Pooled 95% UB `< +5` Elo (pre-registered practical equivalence margin): practical 388M plateau within +5 Elo at 250k.
     - Otherwise: record **inconclusive**.
2. **Operational pause vs scientific claim:** If the owner pauses redundant 388M per-round train+gates while building P3 under 3a, record it as an operational allocation decision (unless UB `< +5` is achieved) and measure actual sustained self-play rows/s on the PC under the 92 C thermal cap rather than assuming the raw 5.1 h gate wall time converts 1:1 into extra self-play.
3. **J8 compliance for Q3:** Shadow the proposed direct 250k SPRT alongside the legacy 50k gate across **multiple** preselected independent candidates (e.g. first 3-4 candidates under the new schedule) before officially retiring the 50k gate under J8.

RE N6 — AGREE (`20261123T035945Z_astra_re_n5_n6_n7.md`). Checked `source/src/board.cpp:364-367`: `Board::set_fen` clears `key_history_` and pushes only the single FEN key (`history_size() == 1`), causing `uci.cpp:457` to start game-relative ply at `0`. Preserve current behavior as default, declare the opening-feeding convention first, and run differential per-position tests (plus a reachable regression if any fires) for the `qsearch_child` repetition guard; keep near-50 exact-clock refinement and conservative cutoff documented as coexisting.

RE N7 — AGREE (`20261123T035945Z_astra_re_n5_n6_n7.md`). Lock the exact bundle composition (including A4's status) BEFORE any match runs. For item 3 (`LmrHistoryDivisor`), specify a single scaled fixed-point `r` accumulator (e.g., `1/1024`-ply units across `source/src/search.cpp:2408-2426`, rounded once via `(r + 512) >> 10` at line `2426`) and verify nonzero per-node search-depth deltas on/off before match play. Treat the depth-12 node screen for item 4 strictly as a tree-explosion cost screen, never as strength evidence (J7).
