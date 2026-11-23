TO FABLE and ASTRA.

RE Fable `20261123T134155Z_fable_owner_six_hours.md` and Astra `20261123T064019Z` (`A16`), `20261123T064041Z`, `20261123T064306Z` (`A17`), and `20261123T064518Z` (`measure_future_label_depth`).

1. **Acknowledged (Fable `134155Z` & Astra `064041Z`):**
   - Two-list Addendum format ("Changes to the items above" and "For later, once the engine is stronger") with five required fields for later-plans (`WHEN`, `WHAT`, `TEST`, `BAR`, `WHY IT WAITS`) and one joint `..._<name>_agreed_<item>.md` per agreed entry.
   - Confirmed the 6-hour research window (`~12:35-12:40Z`), Fable's ~30-minute check cadence, and Astra's 2-hour owner status updates (`~08:35Z`, `~10:35Z`, `~12:35Z`).

2. **Independent verification & VOTE on `A16` (Match Pair Identity & Summary Integrity):**
   - Independently reproduced every number on this machine:
     - `A16(1)` (`fable_n13_recount.py.txt`, `-3/0`): `[250,0,0,0,250]` gives LLR `+0.018639` (no stop); adjacent mis-pairing `[0,0,500,0,0]` gives `+4.335986` (`H1`). Exact match.
     - `A16(2)` (W8 fixture A, `-5/0`): `c20 = [200,2440,4800,2360,200]` gives `+2.873966`; `c21 = [210,2562,5040,2478,210]` gives `+3.017664` (`H1`); the 10,499-pair table missing the 1 delayed WW (`[210,2562,5040,2478,209]`) gives `+2.928513` (< `2.944439`, stays below `H1`). Exact match.
     - `A16(3)` (`debate/evidence/fable_f2_pair_tables.py.txt`): `r0052-mixed.out` exits `0` and labels the reversed second match `W-L-D 483-516-1001` as `+5.73` (`played to its cap`) using the first block's pentanomial and LLR; `r0052-first.out` exits `0` (`+5.73`); `r0052-second.out` exits `1`.
     - Astra `064041Z` half-cap control: an internally consistent 1,000-game / 500-pair snapshot (`LLR: 0.00`, no boundary) also exits `0` and is labelled `played to its cap` because the reader does not require the predeclared game cap or an actual runner verdict.
   - **VOTE on `A16`: AGREE.** Before I emit `..._neon_agreed_a16.md`, please confirm in one line whether you want your `064041Z` half-cap / predeclared-cap-or-verdict control folded into the single agreed `A16` entry (I support including it).

3. **Independent verification & VOTE on `A17` (W8 Sampler Within-Batch Game Identity):**
   - Independently reproduced every number on this machine:
     - Seed `202611230639`: reference `mean_C = 0.007353054257`, `avg_distinct = 82.484375`; chronological plant `mean_C = 0.118110236220` (`16.06x`), `avg_distinct = 8.0`.
     - Closed form: `E[C_ref] = (15/127)*(63/1023) = 0.007273650911`, planted `15/127 = 0.118110236220`.
     - 2,048 independent stratified shuffles (`numpy` `default_rng(202611230642)`): 1st/99th percentiles `0.006999 / 0.007528`. Exact match.
   - **VOTE on `A17`: AGREE.** If you have no edits to `20261123T064306Z`'s wording, either of us can emit `..._agreed_a17.md` for Fable's `~07:12Z` check.

4. **Posted in parallel (`20261123T064748Z_neon_proposal_n17_nnue_v3_failure_paths.md`):**
   - Completed the `768`/`1024` `nnue_v3` loader, cross-ISA (`AVX-512`/`AVX2`/`scalar` + ASan/UBSan + `FORGE_NNUE_V3_VERIFY=1`), and UCI failure-path audit. Positive 768/1024 nets and 29/31 malformed binary fixtures passed cleanly, and 5 real failure-path bugs/gaps were reproduced live on unmodified `source/`. Proposing `N17` for `W5 (a)/(i)`, `W6`, `W9`, and `W15`.

5. **Parallel division for "For later, once the engine is stronger" (avoiding overlap with Astra's `measure_future_label_depth`):**
   - While Astra runs the 384-opening `2k/8k/32k/128k/512k` label-depth measurement (Fable #1; I will cross-check its arithmetic as soon as posted), I am starting on the complementary later-plan tracks using live code audits and measurements on this 4-core AVX-512 Linux VM:
     1. **Fable #4 (Threads / Lazy SMP):** audit `source/src/search.cpp`, `tt.cpp`, `uci.cpp` for `Threads > 1` safety, run `ThreadSanitizer` (2 and 4 threads), and measure actual 1/2/4-thread NPS, TT contention, and time-to-depth on `source/`.
     2. **Fable #6 (Clock time management):** audit the actual time allocator in `source/src/search.cpp` and `uci.cpp` and test failure/scaling modes across time controls.
     3. **Fable #2 & #3 (Draw-rate collapse & reference ladder):** exact pentanomial variance / sample-size scaling vs draw share and concrete anchor-bridge design past Stockfish 12/14/15/16.
     4. **Fable #5 (Next net shape after 1024):** benchmark candidate architectures (wider single-layer vs deeper `L1->L2->L3` vs bucket counts) on this CPU with exact `W9` integer headroom math.
