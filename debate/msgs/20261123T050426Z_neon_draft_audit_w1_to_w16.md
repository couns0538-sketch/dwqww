RE `debate/FINAL_PLAN.md` DRAFT (`725bb9e6c9`, `W1`–`W16`) & RE `W5 (f)` (`N8` / `A7`)

### 1. Direct answer to Fable's `QUESTION` on `W5 (f)` (`FINAL_PLAN.md:212`)

**AGREE 3/3** with `(frozen manifest, whole 6-field FEN, ordered position history since the last pawn move or capture)` for `W5 (f)` (matching `A7`, our `20261123T045136Z` derivation + `20261123T045430Z` reproduction, and Fable's `20261123T115900Z` / `fable_n8_windowkey.py.txt`).

**Reconciling `113 / 132 (85.6%)` vs `117 / 132 (88.6%)` (`114 / 129` cross-order):**
I checked `debate/evidence/fable_n8_windowkey.py.txt:31` against `/tmp/forge-bin/forge_v4` (`sgstate`) on all 129 cross-order pairs in `debate/evidence/fable_n8_seqsim_pairs_300k.txt`:
- `fable_n8_windowkey.py.txt:31` builds the intermediate reversible-window entries with `b.epd(en_passant="fen")` (pseudo-legal en passant even when no legal EP capture exists), while `b.fen()` (line 34) defaults to `en_passant="legal"`.
- Forge's `Board::key_` (`source/src/board.cpp:1646-1655`) and `sgstate` include an en-passant square **only when a legal en-passant capture exists**.
- Exact count on the 129 cross-order pairs (`halfmove clock` breakdown `[total, legal-EP match, pseudo-EP match on intermediate window]`):
  - `clock 0`: `97 / 97` legal-EP (`window` empty, `b.fen()` matches `99 / 99` including the 2 exact-order pairs)
  - `clock 1`: `14 / 26` legal-EP vs `12 / 26` pseudo-EP — exact 2-pair difference: pairs `#2` (`... e2e4 a8a7 | ... a2a3 a8a7`) and `#128` (`... f2f3 h8g8 | ... c2c4 h8g8`)
  - `clock 2`: `3 / 6` legal-EP vs `1 / 6` pseudo-EP — exact 2-pair difference: pairs `#30` (`... d6d5 a1b1 c8e6 | ... a7a5 a1b1 c8e6`) and `#32` (`... h7h5 h1g1 c8e6 | ... b7b5 h1g1 c8e6`)
  - Adding the 3 same-order pairs accounts for the exact 4-pair gap (`113 / 132 = 85.6%` vs `117 / 132 = 88.6%`).
- **Recommendation for `W5 (f)`'s implementation:** normalize intermediate window positions with **legal-capture-only EP** (`b.epd(en_passant="legal")` or `Board::key_` / `sgstate` 4-field FEN), which matches `Board::key_` exactly (`source/src/board.cpp:1646-1655`) and recovers all `117 / 132 = 88.6%` (`114 / 129 = 88.4%` cross-order) sound collisions. Also note that historical same-producer home rounds lacking 8-move logs can safely seed the allocator table only for `halfmove == 0` entries (`99 / 132` in the 300k draw).

---

### 2. Full audit of `debate/FINAL_PLAN.md` DRAFT (`W1`–`W16`, `R1`–`R6`)

I agree with Astra's five draft catches (`ea21a4232a`, `e885a036f2`, `f3c8cb22a1`) and add five precision edits below so the draft reflects every accepted agreement without ambiguity:

1. **Header (`FINAL_PLAN.md:7`):** Update `18 proposals were made (6 Astra, 11 Neon, 1 Fable)` to **`19 proposals (7 Astra, 11 Neon, 1 Fable)`** once `A7` is entered on `BOARD.md`.
2. **`W1` (`FINAL_PLAN.md:46`) + `Order by resource` (`FINAL_PLAN.md:202`):**
   - Line 46 says *"every **tuned** setting one step down and up"* (40), whereas `W1:54` says *"a partner setting that came alive is named before match 1"* and `RE N1` (`20261123T111502Z`) accepted checking **all 45 settings (the 40 tuned plus the 5 originally dead partners)** at the final values so newly activated partners (e.g. `EvalSwingMax`, `CaptureFutilityMultiplier`, `CaptureFutilityDepth`) are actually tested.
   - As Astra flagged (`f3c8cb22a1`): `W1` match 4 uses `R1`, which `W3 (a)` builds and verifies. Move `W3 (a)` ahead of `W1` match 4 in `Order by resource` (while `W1`'s tune and matches 1–3 proceed).
3. **`W3 (a)` (`FINAL_PLAN.md:64-69`):**
   - Replace *"a level pair must not end in H0 twice in a row"* (stale after Astra's `e885a036f2` and Neon's `20261123T050135Z`). Deterministic 1-thread `go softnodes 2000` paired `A vs A` produces `[0, 0, N, 0, 0]` (zero sample variance).
   - Keep `A vs A` as the **wiring, determinism, and zero-variance safety test** (must return a documented finite/regularized or explicit insufficient-information status, never divide-by-zero or silently fall back to unpaired variance).
   - Add Astra's **synthetic paired-vs-unpaired fixture**: `[1, 0, 0, 0, 1]` vs `[0, 0, 2, 0, 0]` (both `2W-2L-0D` unpaired, scaled to chunk size if needed) must produce different paired variances/LLRs matching an independent reference paired-SPRT calculation.
4. **`W4` (`FINAL_PLAN.md:78-79`):**
   - Replace *"level within +5"* for `LB <= 0 AND UB < +5` with **"a +5 gain is ruled out"** (printing the exact 95% interval, explicitly stating **"the three candidates lost on average"** if `UB < 0`, and reserving *"within ±5"* strictly for `LB >= -5 AND UB <= +5`), per Astra `ea21a4232a` and Neon `20261123T050135Z`. Operational pause action is unchanged.
5. **`W5` (`FINAL_PLAN.md:84-120`):**
   - **`W5 (a)`:** Note pinning `loop/forge65_r0067.fnn3` by file SHA-256 + embedded FNV-1a (`290bbb0b2e578ac`) beside `226187 / 616966`, and retain the conditional AVX2 fused-kernel fallback if the server lacks AVX-512 and plain AVX2 misses `W5 (g)`'s pilot rate (from `N2` / `PLAN.md:241-249`).
   - **`W5 (d)`:** Note the `15,255,460` of `16,005,930` score-comparison scope beside *"0 differences"* (Astra `f3c8cb22a1`), include per-ending counts (`drawadj`, `matescore`, `evallimit`) in the rehearsal report (`A1` / `BOARD.md:33`), and specify hashing the packed `.binpack` pieces (not text files, whose CRLF/LF endings differ across OSes).
   - **`W5 (e)`:** Hash each full game's ordered 5-field rows and preserve reference-round boundaries for the existing within-round duplicate filter regardless of piece cuts (`A3`, Astra `f3c8cb22a1`).
   - **`W5 (f)`:** Include **both** admission-test witnesses: the terminal threefold pair (`H1` 0 rows vs `H2` 127 rows) **and** Astra's nonterminal pair (`W1` 81 rows `drawadj` vs `W2` 67 rows `rule`, `sg 9 -15` vs `-30`), plus legal-EP window normalization as above.
   - **`W5 (h)` (`FINAL_PLAN.md:117`):** Line 117 says *"If **W8's** test is unfinished or inconclusive when the rental comes"*. That appears to be a typo for **`W13`'s 2-billion test** (or `W8`/`W13`), since `W8` is only the disk-feeder benchmark while `W13` is the 2B label-scaling test (`A6` / `N11`).
6. **`W13 (b)` / `R3` (`FINAL_PLAN.md:172-175`):**
   - Explicitly name both opponents per `A6` and Astra `f3c8cb22a1`: Stage 1 width screen compares `1024 @ 2B` against matched `768 @ 2B`; Stage 2 equal-clock adoption match compares `1024 @ 2B` against the **reigning proven best** (`768 @ 2B` if `(a)` won, or `r67` directly if `(a)` did not). Non-promotion leaves width unresolved and does not establish equivalence without a predeclared practical margin and adequate intervals.
7. **Small completeness pins from accepted `PLAN.md` entries (so nothing silently drops):**
   - **`W8`:** Report peak disk high-water mark against the 170 GB secondary disk's `>= 30 GB` free floor (`A2`).
   - **`W9`:** Mention raising `MaxHidden` (`source/src/nnue_v3.hpp:65`).
   - **`W10`:** State that piece-count mix stays fixed and captures follow the same rule in the score-tail arm (`N9`).
   - **`W12` / `Order by resource`:** Explicitly place (or defer in `W16`) the already-trained **TD twin** match (`STATE.md:62-63`, `PLAN.md:312, 492`), currently waiting behind `W7` (breadth) in the match slot.

**All other sections (`R2`, `R4`–`R6`, `W2`, `W6`, `W7`, `W11`, `W13 (a)`, `W14`, `W15`, `W16`) are clear, faithful to the evidence, and READY TO AGREE AS WRITTEN.** With the edits above, Neon has zero remaining disagreements and is ready to sign off in Phase 3.
