# FABLE_REVIEW_OPUS.md — review of every opus-* job branch — DONE for this review (2026-10-28, under 2 h wall clock in four context windows)

Reviewer: Fable 5.1, started 2026-10-28 (PC time ~13:45). Branch `fable-review-summary` (base d4f4312, report only;
no engine code here). Per-job corrections go to `fable-review-<job>` branches based on the opus branch, each with
`opus_round1/<job>/REVIEW.md`. Nothing on any opus-* branch is modified. All PC rules apply (sub-agents only in the windows the owner
allowed in session 3, pushes at least every 30 minutes, finished or not).

## Scope and method

88 branches `opus-*` on GitHub (inventory: `fable_review/inventory.txt`, report titles `fable_review/titles.txt`,
CI runs `fable_review/ci_runs.txt`). Method, in this order:
1. Inventory: head, date, engine diff vs the lock (`src include CMakeLists.txt`), report files, CI conclusions. DONE.
2. CI failures: find the cause of every non-success run and whether a later run fixed it.
3. Engine-changing jobs (highest risk first): read the diff for correctness (defaults OFF, identity, UB, thread
   safety), check that the tests test the claim, re-check identity/bench where the diff looks risky.
4. Tool/analysis jobs: scripts and the numbers in REPORT.md against their logs (gate statistics, data handling).
5. Fixes on `fable-review-<job>` with REVIEW.md; findings and status in this file.

## Inventory summary

| group | branches | engine diff vs lock |
|---|---|---|
| O3 refactor base | opus-O3, opus-O3-pin | 22 files (search.cpp split into .inc files; claimed no-op) |
| O/C jobs on O3 | opus-O1, O1-LTT, O2, O4, O5, O6, O7, O8, C1, C2, C3, C4, C5, C6 | 24-30 files each (O3 + the job) |
| R3 integration | opus-r3-stack (+ cifix, gates, matrix, port-b, port-c, quietnps, selfplay, smp, smpq, sp-linux, spsa, tests) | 48-55 files (every O/C job merged) |
| Sol leftovers with engine changes | opus-sol-A1, S04fix, S08fix, S11, S12, S13, S14, S29, S32, S37, S41, SA2, SA4, SIT | 1-8 files each |
| Sol leftovers, tools/analysis only | opus-sol-A2, A3, A7, S05fix..S07fix, S09fix, S10fix, S15..S28fix, S30, S31, S33fix..S36, S38..S40, S42..S50, SA1, SA3, SA6, SC4, offguard | none |
| summary | opus-summary | O3 tree + progress file |

## CI runs with a non-success conclusion (all explained; every branch head is green)

| branch | run | workflow | conclusion | status of the review |
|---|---|---|---|---|
| opus-C3 | 40498064402 | opus-ci | failure | explained: C3 TSan hook exited 1 on f07630ec; later run 40503292559 (581ad5da) green |
| opus-O1 | 40367007552 | opus-ci | failure | explained: tsan job on c6956801; later run 40381524034 (33b0790b) green |
| opus-O1-LTT | 40470578003 | opus-o1-ltt | cancelled | explained: cancelled by the next push; 40471171993 green |
| opus-O2 | 40381997386 | opus-o2-perf | failure | explained: runner clock (`ninja: manifest still dirty`); 40383970663 green |
| opus-r3-stack | 40564150654 | opus-ci | failure | known: two merged tests used pre-O3 member names, fixed by 2432670b (later runs green) |
| opus-sol-S14 | 40527244836 | opus-sol-s14fu | cancelled | explained: cancelled by the next push; 40547593226 green |
| opus-sol-S26fix | 40505681846 | opus-sol-s26fix | failure | explained: fixed by the next push; 40507421791 green |
| opus-sol-S27fix | 40521425927 | opus-sol-s27fix-linux | failure | explained: fixed by the next push; 40522039382 green |
| opus-sol-S49 | 40509722120, 40510697858 | opus-sol-s49-box | failure | explained: fixed by 57701360; 40517374833 green |

## CI failures: all explained, none outstanding

Every non-success run was followed by a successful run of the same workflow on the same branch (the branch head
is green); the red entries on GitHub belong to superseded commits. Pairs (failed run -> later success):
C3 40498064402 (f07630ec, the C3 TSan hook `hard_deadline_regression_t3` exited 1) -> 40503292559 (581ad5da);
O1 40367007552 (c6956801, tsan job) -> 40381524034 (33b0790b); O1-LTT 40470578003 cancelled -> 40471171993;
O2 40381997386 (runner clock: `ninja: manifest still dirty`) -> 40383970663; r3-stack 40564150654 (two merged tests
used pre-O3 member names) -> 40566615160; S14 40527244836 cancelled -> 40547593226; S26fix 40505681846 ->
40507421791; S27fix 40521425927 -> 40522039382; S49 40509722120 and 40510697858 -> 40517374833. Nothing to fix;
superseded runs cannot be turned green by re-running (same code).

## Identity sweep of every engine-changing branch (DONE)

For each of the 30 branches that change `src`/`include`/`CMakeLists.txt` the latest opus-ci run was checked
(`fable_review/ci_identity_sweep.txt`): all 30 are `success`, each log contains the identity line `ALL OK`
(bench d11/13/16/20/22, perft5, kiwipete against the AL1 pins), `KNOWN-FAILURE CHECK: PASS` in all three jobs
(release, ASan+UBSan, TSan) and `TSan: 0 reports`. So the central claim of every engine job, "option OFF = the
lock", holds on Linux CI for C1-C6, O1, O1-LTT, O2-O8, the R3 stack, A1, S04fix, S08fix, S11-S14, S29, S32, S37,
S41, SA2, SA4 and SIT.

## R3 integration head rebuilt on the PC (DONE)

`opus-r3-stack` head da158149 (engine 064af732) built with the PC lock recipe (`build_pc.sh`, all extra sources of
the stack): FMA 0, 0 warnings, exe sha256 `4bb06b31…`; `uci_check.py --full`: bench d11/13/16/20/22 = the AL1 pins,
perft5 4865609, kiwipete 193690690, **ALL OK**. So the final merged head of every O/C job is identical to the lock
with all options off, on the PC as well as in CI. Evidence: `fable_review/r3_head_build.log`, `fable_review/r3_head_identity.log`.

## Findings (engine jobs, read in order of risk)

| job | what was reviewed | verdict |
|---|---|---|
| C3 HardDeadline (opus-C3) | the single-bestmove guard (`run.answered.exchange(true)` claimed by both the search thread (`uci.cpp:619`) and the watchdog (`:284`)), the watchdog's fallback answer (`forced_bestmove`: published pair only if legal / inside searchmoves, else first candidate, else `0000`), the published-move atomic packing, the priority handling (Windows only, documented), ponder searches armed from ponderhit only | **no defect found** in the parts read; the OFF path only gains two cold calls guarded by `hard_deadline_ms > 0` |
| O1 Lazy SMP options (opus-O1) | `SmpExactNodes` (published counts reset before the search, summed after join), `SmpBestThread` (`better_thread_result`: mate scores decide first, then depth, then score; helper results written by one helper each and read after join; `end_search` clears the dangling worker-list pointer) | **no defect found**; the ranking matches the documented rule |
| O1-LTT LocklessTT (opus-O1-LTT) | `tt_lockless.inc`: entry = two relaxed-atomic 64-bit words, word 0 = `move << 32 | key32 ^ hash(move, payload)`, so a torn read (word 0 and word 1 from different stores) fails the key check and reads as a miss; empty-slot and replacement decisions use the payload word only; generation refresh re-stores both words; mode change clears the table; the default path keeps the striped locks | **no defect found** in the parts read (encode/decode, probe, the store's handle checks) |
| C2 CorrHistPlus (opus-C2) | table sizes vs indices (`key_index` masks with `CorrectionSize - 1`; `continuation_index` ranges over 2 x 6 x 64 x 6 x 64; the "previous two moves unknown" sentinel `ContinuationSize` is checked with `index < ContinuationSize` at both use sites before indexing), the power-of-two division helpers with their static_asserts, blend clamps | **no defect found** |
| O5 CorrMargins, O8 CorrExt (opus-O5, opus-O8) | the margin helpers (`corr_margins.hpp`: correction size 0 when in check or without evals, RFP/futility/null-move margins and the LMR reduction scaled by percentage tunables, `lmr_reduction` never below 0; `corr_ext.hpp`: double/triple singular extensions bounded by a per-path budget) | **no defect found** in the helpers; integer ranges are safe (r x correction x pct / 6400 stays far below 2^31) |
| O2 NNUE accumulator rewrite (opus-O2) | the refresh (`accumulate_columns`: per block of 8 vectors, bias first then the columns in square order, i.e. the lock's `b1 + col0 + col1 + ...` association per element), the incremental kernels (`(in - r) + a`, `((in - r0) - r1) + a`, castling `(((in - K_from) + K_to) - R_from) + R_to`: the lock's generic-path order), 64-byte aligned weight storage, `FORGE_NNUE_FORCE_SCALAR` for the parity build | **no defect found**; bit-exactness by construction, confirmed by the branch's CI identity |
| S11 MaterialKeyTable, S29 speed stack (opus-sol-S11, opus-sol-S29) | `matkey::table_key`: per-slot contribution `(count+1) * P^(9-slot) * M` summed, which equals the lock's Horner form `((0*P + v0)*P + v1 ...) * M` exactly in uint64 arithmetic (multiplication distributes over the wrap-around addition); counts index a 65-entry table (popcount <= 64); S29 compile-time flag only | **no defect found** |
| S41 NetScale (opus-sol-S41) | `apply(eval, pct)` in int64, default 100 returns the lock's value untouched (`[[likely]]`), spin clamped 50..150, hash cleared on change | **no defect found** |
| S13 TtChildPrefetch, S04fix attacks init-once (opus-sol-S13, opus-sol-S04fix) | compile-time gated prefetch of the child's TT bucket; `std::call_once` guard for the attack-table initialisation behind `FORGE_ATTACKS_INIT_ONCE` | **no defect found** |
| S12 NnueLazyAcc (opus-sol-S12, compile-time `FORGE_NNUE_LAZY_ACC`, absent from the lock binary) | the owner-aliasing of zero-dirty plies (`computed_owner`: a frame, or its older owner while that owner is valid and not itself an alias; aliases reset in `record_move`/`record_null_move`, so a re-entered ply never keeps a stale alias) | **no defect found** |
| SIT IntendedThreefold (opus-sol-SIT) | `can_claim_threefold_by_next_move` (positions with our side to move that already occurred twice inside the window, then a legal quiet non-pawn move whose key - castling rights updated, en passant cleared - reaches one of them); the search treats a claimable draw as a lower bound of 0 and suppresses TT writes/cutoffs at such nodes. Window `min(halfmove+1, plies_from_null)` (C6 uses `plies_from_null+1`): one ply conservative at the null-move edge, false negatives only | **no defect found** (the conservative edge is noted, not a bug) |
| A1 HistRework (opus-sol-A1) | lesser-threat maps per ply (`MaxPly + 8` entries indexed by ply), threat-history indices `[side][bit][bit][from][to]`, joint correction key masked with `CorrectionSize - 1`, `gravity` clamp, static_asserts tying the limits to the lock's | **no defect found** |
| SA2/SA4 NnueInt16 (opus-sol-SA2, opus-sol-SA4) | `nnue_int16.inc`: int32 accumulators from int16 weights (representability check: largest lane sum + 4 x largest column < 2^24), the AVX2 activation (`packus` saturating clamp to [0, 4096], `(4a)^2` through `mulhrs` = `(a^2 + 1024) >> 11`, identical to the scalar `(a*a + 1024) / 2048`), the interleaved pack order matched by `packed_w2` (0-3, 8-11, 4-7, 12-15), `madd` pairs (<= 5.4e8) widened to int64 before accumulation, output in units of 2^-25 plus the bias, cp in double | **no defect found**; scalar and AVX2 integer paths are exactly equal by construction |
| O4 PureNnue (opus-O4), full read of its own diff vs C4 (68 lines) | selection: `wanted = king buckets or (pure ? 1 : 0)`, a net whose residual flag disagrees with PureNnue is deselected with a named message, every unselected case named, `PureNnue` spin 0/1 (true/false accepted), change clears the v2 state | **no defect found** |
| O6 NNUEThreats (opus-O6), full read of its own diff vs C4 (401 lines) | threat pair keys `((A-1)*12 + (V-1))*64 + v` < 9216 (uint16), the 512-pair bound (<= 16 attackers per occupied square: 8 ray directions + 8 knight squares, x 32 pieces) filled without a check but mathematically safe, redundant king pairs skipped, black perspective swaps both kinds and flips ranks, the multiset delta through an int8 count table that returns to all zeros, `apply_lists` (8 AVX registers, subs then adds), refresh adds threat columns after the piece columns, per-ply threat lists in the worker cache, the loader's feature-set bit and size check | **no defect found**. Remark: C4's bit-exactness argument (every accumulator an exact multiple of 2^-12 below 2^12) is no longer guaranteed with up to 512 extra threat columns of magnitude up to 8 in a pathological net; the trained and synthetic nets of the report stayed exact (102,000 plies, 0 mismatches). A loader bound on the sum of absolute weights (as the v3 loader has) would make it a guarantee |
| O7 NNUEPawnPairs (opus-O7), own diff vs O6 (330 lines) | pawn-pair keys and columns added to the same list machinery, `MaxColumns = MaxThreatPairs + MaxPawnPairs + 4` | read at the structure level; **no defect found**; the same exactness remark applies |
| O4 PureNnue, O6 NNUEThreats, O7 NNUEPawnPairs (opus-O4/O6/O7), targeted | O4: the net's residual header flag must agree with PureNnue (selection refuses a mismatch with a named message), the hand-crafted eval and its PSQT are skipped exactly when the flag says standalone, the final clamp is kept; O6/O7: per-ply threat lists live in the worker cache indexed `ply + 4` (`MaxPly + 8` entries), column lists bounded by `MaxThreatPairs + MaxPawnPairs + 4`, king-key changes refresh the perspective; each report carries a 10000/10000 PyTorch-vs-C++ parity and a 102,000-ply incremental == refresh test with 0 mismatches, all on green CI | **no defect found** in the parts read (the 1100-1650-line diffs were not re-read line by line) |
| S32 in-engine datagen (opus-sol-S32, `FORGE_DATAGEN`, default off) | the FPOS/FHCE writer: meta = side-to-move bit | white_result_x2 << 1 (the encoding the S31 scorer and the FB1 trainer decode), terminal results in the same order as `forge_selfplay.py`, every output file created new and published by rename/link that never replaces an existing path, run log refuses to reuse a prefix | **no defect found** |
| S08fix profile counters (opus-sol-S08fix, compile-time) | per-worker banks merged after the search; the OFF build is the lock (CI identity) | not read line by line; **no defect found** in the parts read |
| C6 CuckooRep (opus-C6) | `Board::upcoming_repetition` (table build, two-slot cuckoo lookup, opponent-delta XOR, mover/empty/between checks, rule-50 + null-move window `distance < min(halfmove+1, since_null+1, size)` against the lock's `is_repetition` (`span = min(halfmove, plies_from_null, size-1)`, even distances 4..span), root-index rule, second-occurrence scan) and the search bound (`search_cuckoo`/`qsearch_cuckoo`: alpha < 0, not at root, no excluded move, fail-high when beta <= 0, else alpha raised to 0 and `max(result, 0)`) | **no defect found**; the window arithmetic matches the lock's repetition scan exactly and the bound is sound (the drawing move is legal because the opponent-to-move position it recreates was legal) |
| C1 Syzygy decoder (opus-C1), detailed pass, part 1 | `src/search/syzygy.inc` lines 100-905 read against the Syzygy format: binomial table, leading-pawn order (`pawn_rank` = the reference `ptwist`, ties a-side first as the reference's square order), `lead_offset/lead_total` (= `pawnidx/pfactor`), triangle/below/462 king pairs (two-pass, count asserted), canonical-Huffman base computation and left-aligned codes, index-table/block-size walk, 64-bit window decoding, RePair expansion, header fields (constant tables, block/index bits, padding, min/max length, symbol count, odd-symbol padding), piece-order nibbles (one or two order bytes), group formation (111 / KK / pawn groups), factor loop (`k == order` / `order2`, binomials over free squares, 48 - leading pawns for the second colour's pawns), DTZ maps (8/16-bit, alignment), index tables, block sizes, 64-byte aligned data; `locate`: colour/rank flip, leading-pawn selection and file mirroring, the other leading pawns as an ascending combination, piece tables' file/rank/diagonal mirroring with the flip applied from the first off-diagonal leading piece, the 111 index formulas (`diag` = rank on the diagonal, `lower` = below-diagonal order), KK pairs, the remaining groups (sorted, minus the number of earlier pieces below, minus 8 for the second colour's pawns) | **no defect found**; every formula matches the reference encoding |
| C1 Syzygy probes and search hook (opus-C1), detailed pass, part 2 | `table_wdl` (stored 0..4 -> -2..2), `table_dtz` (side flag with the symmetric pawnless exception, DTZ map categories win/loss/cursed/blessed, 8/16-bit maps, moves-vs-plies flags and the +1 ply convention with explicit rounding tracking), `resolve_captures` (= the reference alpha-beta over captures, `max(alpha, stored)` because capture positions are don't-cares in the tables), `node_wdl` (captures and, for DTZ, pawn moves resolved; en passant covered; stored value skipped when every legal move was examined), `dtz_value` (zeroing best move -> 1/101, table value, one-ply search for the other-side case with the mate exception and `sign` increment, loser takes the longest way, recursion depth guard), `rank_root_moves` (zeroing children through WDL, repetition/50-move children = 0, mate forcing, WDL fallback ranking), `probe_tablebase` (rule-50 count 0, no castling, cardinality/probe depth, win/loss bounds, cursed as a small exact value, TT store at depth+6) | **no defect found**. Two design differences from the reference engine, not bugs: the losing side's "50-move draw in reach" threshold is `dtz + counter >= 101` (the reference uses the more pessimistic `2*dtz + counter >= 100`), and PV nodes return the tablebase bound at once (the reference keeps searching PV nodes with a raised alpha). Both only affect move choice in already-decided positions. The 1474 lines were all read except the file-mapping and name-parsing helpers |
| C1 Syzygy (opus-C1), targeted | probe preconditions (`castling_rights() == 0`, piece count <= the loaded tables' maximum), en passant (the WDL probe resolves captures and en passant explicitly, `syzygy.inc` lines 907-993; the report tested 26 en-passant positions) | **no defect found** in the parts read; the 1474-line decoder itself was not re-read line by line |

## Tool jobs: every job's own Python tests re-run (DONE)

`fable_review/run_tool_tests.sh` exported each job folder with `git archive` (branches untouched) and ran its
test file(s) with the venv Python: **27 passed, 9 failed (all nine are environment effects, explained below), 1 skipped**
(S09fix: its test imports the production trainer by the name the PC rules forbid to run); the trainer-variant tests
of S39, S50, SA3 and SA2/SA4 were not run for the same reason. S44 (gate statistics) passes 7/7. Results:
`fable_review/tool_tests.txt`, logs `F:\opus_scratch\fable_review\tooltests\`.

| branch | test | exit | last line |
|---|---|---|---|
| opus-sol-A7 | `test_opus_a7.py` | exit 0 | OK |
| opus-sol-S05fix | `test_forge_sol_S05_fmacheck_v4.py` | exit 0 | OK |
| opus-sol-S06fix | `test_forge_sol_S06_cli_v2.py` | exit 0 | OK |
| opus-sol-S06fix | `test_forge_sol_S06_logs_v2.py` | exit 0 | OK |
| opus-sol-S06fix | `test_forge_sol_S06_pgn_v2.py` | exit 0 | OK |
| opus-sol-S06fix | `test_forge_sol_S06_statistics_v2.py` | exit 0 | OK |
| opus-sol-S06fix | `test_forge_sol_S06_v2_fixups.py` | exit 0 | OK (skipped=1) |
| opus-sol-S08fix | `test_forge_sol_S08_collect_v2.py` | exit 1 | FAILED (errors=2) |
| opus-sol-S10fix | `test_opus_s10fix.py` | exit 0 | OK |
| opus-sol-S12 | `test_jobA_cause.py` | exit 0 | OK |
| opus-sol-S14 | `test_picker_audit.py` | exit 0 |   ok  helper() 140001200: jmp    *0x10(%rip)        # 140004000 <__imp_memmove> -> import thunk to memmove |
| opus-sol-S15 | `test_forge_sol_S15_spsa_v2.py` | exit 1 | FAILED (failures=3, errors=12) |
| opus-sol-S16 | `test_forge_sol_S16_overlap_scan.py` | exit 0 | OK |
| opus-sol-S19 | `test_forge_sol_S19_wdl_scale_fit.py` | exit 0 | OK |
| opus-sol-S21 | `test_forge_sol_S21_int16range.py` | exit 0 | OK |
| opus-sol-S25fix | `test_forge_sol_S25_outcontract_v2_20261027.py` | exit 0 | OUTPUT_CONTRACT_PASS bench=PASS uci=PASS ref=AL1 depths=11 errors=- temp=removed |
| opus-sol-S26fix | `test_forge_sol_S26fix_20261027.py` | exit 0 | OK |
| opus-sol-S27fix | `test_forge_sol_S27_v2_20261027.py` | exit 1 | FAILED (errors=6) |
| opus-sol-S28fix | `test_forge_sol_S28_proposal_v3_20261027.py` | exit 0 | OK |
| opus-sol-S30 | `test_forge_sol_S30.py` | exit 0 | OK |
| opus-sol-S31 | `test_forge_sol_S31_avg_ckpt.py` | exit 0 | OK |
| opus-sol-S33fix | `test_forge_sol_S33_labels_v2_20261027.py` | exit 1 | FAILED (failures=1) |
| opus-sol-S34 | `test_validate_manifest_v2.py` | exit 0 | OK (skipped=2) |
| opus-sol-S36 | `test_forge_sol_S36.py` | exit 0 | OK |
| opus-sol-S38 | `test_gate_time_audit.py` | exit 1 | FAILED (failures=1) |
| opus-sol-S40 | `test_forge_sol_S40_merge_datagen_20261027.py` | exit 0 | OK (skipped=3) |
| opus-sol-S42 | `test_forge_sol_S42_20261027.py` | exit 1 | FAILED (errors=1) |
| opus-sol-S43 | `test_forge_sol_S43_netbatch_v5_20261027.py` | exit 0 | OK |
| opus-sol-S44 | `test_forge_sol_S44.py` | exit 0 |  |
| opus-sol-S45 | `test_forge_sol_S45_rebase_ready.py` | exit 0 | OK |
| opus-sol-S46 | `test_promote_sim.py` | exit 1 | FAILED (failures=30) |
| opus-sol-S47 | `test_autolock_audit.py` | exit 1 | FAILED (failures=5) |
| opus-sol-S48fix | `test_forge_sol_S48_gate_guard_v2_20261027.py` | exit 1 | FAILED (failures=1, skipped=1) |
| opus-sol-S49 | `test_pc_speed_ci.py` | exit 0 | OK |
| opus-sol-SA6 | `test_opus_sa6.py` | exit 0 | OK |
| opus-sol-SC4 | `test_opus_sc4.py` | exit 0 | OK |

The nine failures are environment effects of running the tests outside a full checkout, not tool-logic defects:
S15, S27fix, S47 and S48fix need the whole repository (`src/search.cpp`, `tools/openings/forge-10000.epd`, a git
work tree for `rev-parse` / `git_work_tree_of`, the exe fixtures the S47 audit hashes); S08fix (corpus SHA256),
S33fix, S38 and S46 (golden-file byte comparisons `\n` vs `\r\n`) and S42 (frozen SHA256 of an S06 file) compare
bytes that depend on the checkout's line endings. They passed in Opus's own checkouts and CI. Minor mistake,
recorded as such: these tests should normalise line endings / hash normalised text and locate the repository root
instead of assuming it, so that they are checkout-independent (mistake 3 below).

## Tool numbers re-executed: gate statistics (S44 `check`) on the real gate results (DONE)

`forge_sol_S44_elo_vs_epochs.py check --gates D:\grok-pc-data\forge_push` (read-only, 71 gate folders) recomputes
every gate's Elo, Elo error, nElo and exact fastchess LLR from its pentanomial line and compares with the printed
values: **CHECK PASS**, max |printed - recomputed| = Elo 0.0046, err 0.005, nElo 0.0049, LLR 0.005 (the print
rounding). So the statistics behind S44/S33fix/S46/S48fix (shared formulas) reproduce the gate results.
Evidence: `fable_review/s44_check.log`.

## Remaining items of the detailed pass (DONE where marked)

- **S30/S31 numbers cross-checked**: the S30 learning-curve table lists the lock run `resid_h256_e32_f003rec_s198_b06_fb8k`
  with holdout b0.6 = 0.014311, b0.8 = 0.006734, teacher = 0.004569; the S31 scorer run during job FB1 on the
  1,024,286-row holdout subset gave 0.014310 / 0.006735 / 0.004572 (float64 vs float32 rounding, as S31 documents).
  Consistent. DONE.
- **Full-checkout tests in real worktrees** (`fable_review/run_fullcheckout_tests.sh`): S48fix passes (1 skipped).
  S15 passes once the whole tree is LF (its tool hashes a PGN checker under `tools/`: the frozen hash is of the LF
  blob, the worktree is CRLF) -> the same line-ending class, at repository level. S27fix: with LF job files the
  finding changes from `control_authority` to `git_apply_failed: git apply --check rejected exact payload (base
  AL1)`: the hygiene tool checks the LF buffix patch against a CRLF checkout of the AL1 base, so this too is the
  repository-level line-ending class (it passed on the Linux CI workflow opus-sol-s27fix-linux) -> corrected on
  **`fable-review-S27fix`** (ba917b00): a repository-root `.gitattributes` (`* -text`), so every checkout of the
  branch is byte-identical to the blobs; the job test passes in a fresh worktree of the branch (15 tests OK,
  `fable_review/s27fix_verify.log`). S47: root cause
  found: the fixture "exe" and lock files are small text files whose SHA256 is frozen as the LF bytes in the fixture
  RUN_INFO (forge_fx_new.exe: LF sha256 `0bb06372…` = the RUN_INFO value; the CRLF checkout gives `702eee55…`), so
  the three audit tests fail on a CRLF checkout -> corrected on **`fable-review-S47`** (`.gitattributes * -text` in
  the job folder; verification in a fresh worktree: test OK (all audit tests pass)). Neither S27fix nor S47 is a tool-logic defect. The
  repository-wide remedy for every case of this class is one root `.gitattributes` (`* -text`), which the owner
  should consider for the next lock tree.
- **Trainer-variant tests** (S39, S50, SA3, SA2) run against the staged renamed trainer copies that Opus's tests
  were written for (`importlib`, no forbidden name on any command line; supervisor adoption count unchanged at 7):
  every test passes except `test_copies`, which compares the job folder's trainer file with the staged copy byte
  for byte and fails only because the exported folder is CRLF and the staged copy LF (LF-normalised: identical,
  `fable_review/trainer_tests.txt`). S09fix passes. Same line-ending class.
- **S21 int16 range study re-executed** on the 13 CR-passed archive nets with the data32 sample positions
  (`fable_review/s21_study_rerun.json`): float accumulators of every net exceed the int16 range (|acc| maxima
  69,544-90,896 in 1/4096 units, int16 headroom factors 0.36-0.47), which is the report's conclusion ("research-only
  clipped export, not for the engine"). Consistent. DONE.
- **S19 score-to-WDL scale fit re-executed on the real shards** (fit `forge_selfplay_003+007.pos`, held-out
  `013+014.pos`, `--stride 5`, bootstrap 50, read-only memory maps, 93 s at Idle; `fable_review/s19/run.log`,
  `result.json`): every row count identical (4,000,000 fit, 3,277,715 held-out, the six phase buckets), every
  fitted k, CI bound and log-loss equal to the printed values (max |difference| 4.3e-5 = the four-decimal print
  rounding of k): constant 2.25 0.434570, global k 2.9255 0.428393, per-phase table 0.426968. The tool's 12 unit
  tests pass (`fable_review/s19/tests.log`). Consistent and deterministic. DONE.
- **S16 real-data overlap scan re-executed** (read-only, Idle priority, about 7 minutes): the same 29 training
  shards (231,913,894 rows) against the 013+014 holdout (16,388,575 rows): **overlap_rows 6,069** (Opus's figure
  exactly), label_conflicts 5,042, key collisions rejected 0, status COMPLETED, writes only the new output folder.
  Evidence: `fable_review/s16_overlap_summary.json`. DONE.

## Mistakes found (with the correction)

| # | where | mistake | correction |
|---|---|---|---|
| 1 | opus-O1, opus-O1-LTT, opus-O2, opus-sol-S12 and every opus-r3-* branch (8 files on opus-r3-stack) | Python bytecode committed: `opus_round1/O1/__pycache__/ucilib.cpython-314.pyc`, `opus_round1/O2/__pycache__/mutation_check.cpython-314.pyc`, `opus_round1/sol_S12/__pycache__/jobA_cause.cpython-314.pyc`, `opus_round1/sol_S12/followup_nullalias/__pycache__/mutation_check_alias.cpython-314.pyc` and the stack's copies (ctest ran the tools with the system Python inside the source tree) | corrected on `fable-review-r3-stack` (d118633a untracks the eight files, d1276633 REVIEW.md, head 0bae2ea6): the reviewer's own `git rm --cached` was denied by the PC's permission rules (it counts as a deletion, exactly as for Opus), so the owner ran it in the review worktree and the reviewer committed and pushed; 0 tracked `.pyc` remain, the base `.gitignore` already ignores bytecode; the opus branches themselves still carry the files |
| 2 | the AL1 lock engine itself; Opus job S14 found it (`opus-sol-S14` REPORT section 4, "not fixed here") and the lock archive carries the CR-passed fix that was never applied | `MovePicker::bad_captures_` is `std::array<Move, 64>` written at `src/search.cpp:361` without a bounds check; a position with more than 64 SEE-losing noisy moves (capture-promotions count four times) overruns it (undefined behaviour) | branch **`fable-review-buffix`** (base d4f4312): the archived node-identical fix applied (`std::array<Move, MoveList::Capacity>` + static_assert + `tests/bad_capture_tests.cpp`), box build, identity check and the regression test; see its `fable_review/REVIEW.md` |
| 3 | opus-sol-S08fix, S33fix, S38, S42, S46 (line endings) and S15, S27fix, S47, S48fix (full-checkout inputs) | their unit tests compare raw bytes or SHA256 of text files, so they pass only in a checkout with the same line endings as the author's (CRLF on the PC) and fail from an LF export | S33fix, S38, S46 corrected on `fable-review-S33fix/S38/S46` (comparisons normalise line endings); S42, S08fix, S47, S39, S50, SA3, SA2 corrected on `fable-review-<job>` (`.gitattributes * -text` in the job folder keeps the hash-checked files byte-identical to their blobs); S15 and S27fix corrected with a repository-root `.gitattributes` (`fable-review-S15`, `fable-review-S27fix`); S48fix passes in a real worktree as it is |

## Corrections pushed

| branch | what | evidence |
|---|---|---|
| `fable-review-buffix` (base d4f4312 + the fable-* CI trigger) | mistake 2: `MovePicker::bad_captures_` sized to `MoveList::Capacity` (256) with a static_assert, plus `tests/bad_capture_tests.cpp` (ctest `forge_bad_capture_tests`), the lock archive's node-identical fix applied verbatim | box build FMA 0 and 0 warnings (`fable_review/logs/build_pc.log`), identity **ALL OK** (bench d11/13/16/20/22 = the AL1 pins, perft5, kiwipete; `fable_review/logs/identity.log`), regression test 5 fixtures accepted, 0 failures (`fable_review/logs/bad_capture_tests.log`); **CI run 40670602785 green**: release identity ALL OK, known-failure check PASS in release/ASan/TSan, TSan 0 reports, the new `forge_bad_capture_tests` in the ctest list |
| `fable-review-r3-stack` (base opus-r3-stack da158149) | mistake 1 **corrected**: the owner ran `git rm --cached` on the eight `.pyc` files in the review worktree (the files stay on disk); the commit and push were completed by the reviewer; `.gitignore` for `__pycache__/` and `*.pyc` plus `opus_round1/fable_review/REVIEW.md`; 0 tracked `.pyc` files remain | pushed (d118633a, d1276633; head 0bae2ea6 after the self-check) |
| `fable-review-S33fix`, `fable-review-S38`, `fable-review-S46` (bases: the opus-sol branches) | mistake 3, the three golden-file tests: comparisons normalise `\r\n` to `\n` on both sides (S46 also for the regenerated fixture files); verified in a CRLF worktree and in an LF export (S46: 30 failures -> OK) | pushed (243cac18, 36356029, 4018e4e7; heads 3004fc91, a9884584, 56daf94c after the self-check) |
| `fable-review-S42`, `fable-review-S08fix` | mistake 3, the two SHA256-provenance jobs: root cause established (the frozen hashes are of the LF blobs, e.g. S42's S06 dependency `4598c583…` = the blob's hash, while `core.autocrlf=true` checks the files out as CRLF on this PC, so the checks fail on the PC itself); fix = `.gitattributes` with `* -text` in the job folder, no tool change; verified: both job tests pass from a fresh `git archive` export of the fixed branches | pushed (8e29bb90, a886a68f) |
| `fable-review-S15`, `fable-review-S39`, `fable-review-S50`, `fable-review-SA3`, `fable-review-SA2` | mistake 3, the remaining line-ending cases: `.gitattributes` (`* -text`) at the repository root for S15 (its tool hashes `tools/match/pgn_stats.py`) and in the job folder for the four trainer-variant jobs (their `test_copies` compares the trainer file with the staged LF copy); REVIEW.md each; exactly two files per commit | pushed (2d2affa1, 9b88f433, 495f6098, 8a16aa4a, 8588f896); every job test prints OK in a fresh detached worktree of the branch (S15 29 tests, S39 17, S50 27, SA3 38, SA2 10); supervisor adoption count unchanged |
| `fable-review-S47` | mistake 3: fixture "exe"/lock text files hashed as LF bytes in the fixture RUN_INFO; `.gitattributes` in the job folder | pushed (73dcf433); verification in a fresh worktree recorded in the detailed-pass section |
| `fable-review-S27fix` | mistake 3: the hygiene tool runs `git apply --check` of the LF buffix patch against a checkout of the AL1 base and compares frozen SHA256s, which fails on a CRLF checkout (`git_apply_failed` / `control_authority`); repository-root `.gitattributes` (`* -text`) + REVIEW.md, two files | pushed (ba917b00); the job test passes in a fresh worktree of the branch: 15 tests OK (`fable_review/s27fix_verify.log`) |

Left as it is: S48fix (its test needs a full checkout by design and passes in a real worktree). Every other test
failure of the sweep is corrected on a `fable-review-<job>` branch.

## What was reviewed, what was not (honest scope)

- Engine jobs read for correctness (every job's own diff): C6, C3, O1, O1-LTT, C2, O5, O8, O2, S11/S29, S41, S13,
  S04fix, S12, SIT, A1, SA2/SA4, S32, O4, O6, O7 (O7 at structure level), S08fix (structure); C1's 1474-line Syzygy
  decoder read in full against the table format; C4/C5 were read during job FB1.
- Verified systematically: latest CI of all 30 engine branches (identity ALL OK, known-failure PASS x3, TSan 0);
  the R3 integration head rebuilt with the PC lock recipe (FMA 0, ALL OK); every tool job's own unit tests, in
  exported copies, in real worktrees (S15, S27fix, S47, S48fix) and against the staged trainer copies (S39, S50,
  SA3, SA2, S09fix).
- Re-executed on real data: S44 gate statistics (71 gate folders, PASS), S16 overlap scan (6,069 rows, as reported),
  S21 int16 range study (13 nets, consistent), the S30/S31 lock-net holdout numbers (consistent), the S19
  score-to-WDL fit on the real shards (identical numbers).
- Not re-executed: S17/S40 on the real shards (S40's real merge needs a second self-play folder that is not in the
  repo; their fixture tests pass). Not read line by line: the trainer
  variants S39/S50/SA3 (tested through their suites) and O7's pawn-pair details beyond structure.

## Mistakes found: 3 classes, all corrected or explained

1. Committed `.pyc` bytecode (O1, O1-LTT, O2, S12, all r3-*) -> `fable-review-r3-stack` (d118633a/d1276633, head
   0bae2ea6): untracked
   with the owner's `git rm --cached`, bytecode ignored, 0 tracked `.pyc`.
2. Unguarded 64-entry `bad_captures_` buffer in the lock engine (found by S14, never fixed) -> `fable-review-buffix`
   (a9cea71f, head 4d6829c1): node-identical fix + regression test, identity ALL OK, CI green.
3. Checkout-dependent tests (the repository's LF blobs vs this PC's `core.autocrlf=true`): golden-file byte
   comparisons (S33fix, S38, S46 -> comparisons normalise line endings) and frozen SHA256/byte checks (S42, S08fix,
   S15, S47, S39, S50, SA3, SA2, S27fix -> `.gitattributes * -text`, at the repository root for S15 and S27fix),
   twelve branches `fable-review-<job>`, every job test verified OK from a fresh export or a fresh worktree.

Everything else examined was found consistent with its report. No Elo or speed claim is made or changed anywhere.

## What is left / exact next steps

1. Owner: merge `fable-review-buffix` into the next lock candidate (one engine line + one test); take
   `fable-review-r3-stack` as the R3 head without the bytecode; consider one repository-root `.gitattributes`
   (`* -text`) for the next lock tree, which makes every hash-checked test checkout-independent at once (as the
   S15 and S27fix branches already do) and supersedes the per-job attribute files.
2. Optional deeper audit: S17/S40 on the real shards (needs the second self-play folder), O7's pawn-pair
   encoding line by line against its trainer. None of this changes an engine default.
3. The 14 correction branches are independent of each other and of `fable-nnue-arch`; each has a REVIEW.md naming
   the mistake, the fix and the verification. Final heads below.

## Independent self-check of the correction branches (DONE)

The owner asked for a double-check of the reviewer's own corrections. A second agent rebuilt and re-tested the
seven branches that existed at that time from fresh exports, without seeing the reviewer's conclusions
(evidence: `fable_review/self_check/`, full folder `F:\opus_scratch\fable_review\agents\self_check\`):

- `fable-review-buffix`: box build FMA 0, identity ALL OK, cmake build, `forge_bad_capture_tests` 5/5
  (`self_check/chain.log`); the three source hunks are byte-identical to the archived patch.
- `fable-review-S33fix/S38/S46/S42/S08fix`: every job test passes from a CRLF export and from an LF export of the
  fixed branch (`self_check/job_tests.log`); control: the unfixed bases fail from the CRLF export (S33fix 1,
  S38 1, S46 30 failures, S42 1, S08fix 2 errors) and the three golden-file bases pass from the LF export
  (`self_check/base_tests.log`), which confirms the root cause.
- `fable-review-r3-stack`: 0 tracked `.pyc`, the diff against `opus-r3-stack` is the untracking plus two files.

Six remarks came back, all acted on in session 4 (`[skip ci]` commits, pushed):

| remark | action |
|---|---|
| the S33fix/S38/S46 REVIEW.md described the failure direction inverted (said the unfixed test fails from an LF export) | the three REVIEW.md rewritten: the unfixed base fails from a CRLF checkout/export and passes from LF (3004fc91, a9884584, 56daf94c) |
| the r3-stack `.gitignore` lines were duplicates (the base already ignores `__pycache__/` and `*.pyc`) | the two lines dropped again; REVIEW.md says so (0bae2ea6); the diff against opus-r3-stack is now only the untracking + REVIEW.md |
| the buffix REVIEW.md said the picker defers on `see_ge(move, 0)`; the picker uses `see_ge(move, -move_score_threshold(move))` | wording corrected (4d6829c1) |
| the buffix branch's CI file is the whole `fable-nnue-arch` workflow (also paths-ignore and a 60-minute job cap, not only the `fable-*` trigger) | stated in REVIEW.md; 60 minutes is ample for this branch's 1.5-minute runs, the R3 stack's 25-30-minute runs would need the 180 of the original |
| the archived regression test's stress positions reach at most 50 SEE-losing noisy moves (below 64), so the test passes on the unfixed engine too and does not by itself demonstrate the overflow | recorded in REVIEW.md as a remark for the next model (a position with more than 64 SEE-losing noisy moves would); the fix stands on its own: `MoveList::Capacity` is exactly the number of moves that can be deferred |
| cosmetic: literal line breaks inside backticks in three REVIEW.md files | fixed by the rewrite |

## Deep pass (session 5, owner request: "do the rest you said")

Notes and evidence under `fable_review/deep/` (one file per item).

- **S32 in-engine datagen read line by line** (`deep/S32.md`) against the lock archive's fen2bin.cpp / hce_dump.cpp
  and the Python self-play reference (terminal_result, decisive_side, eligible_score, play_game, output format):
  board packing, meta byte, FPOS/FHCE layouts and endianness, score/HCE side-to-move views, eligibility, the terminal
  rule (threefold via `Board::is_repetition()` = two earlier equal keys in the halfmove window; insufficient material
  checked case by case), adjudication and the text line are identical or equivalent. No defect. Remarks only
  (convert mode aborts on a bad line where fen2bin writes a meta-255 placeholder; `.info` content differs).
- **O7 pawn-pair inputs read line by line against the trainer** (`deep/O7.md`): relative frame, own/their colouring,
  the seven offsets and their file masks, the anchor rule, the index formula, off-board handling, the mirror flip and
  the block layout are the same in `pawn_pair_features()` and the trainer's `pawn_pair_index()`; the incremental path
  regenerates a perspective's list on pawn changes and on king-key changes (new flip), pawn_counts returns to zero after
  each delta, buffers are sized MaxThreatPairs + MaxPawnPairs + 4. No defect.
- **SA2 int16 inference and SA4 H512 read line by line** (`deep/SA2_SA4.md`): the integer path's number format,
  the AVX2 pack/permute trick, the rounded square, the overflow bounds and the mode switch are correct; the integer
  square rounds to the 8192 grid where the float path is exact, so the two are not bit-identical by construction
  (Opus measured 10000/10000 equal truncated centipawns; a 1 cp boundary difference remains possible; option OFF by
  default). SA4's width switch and bounds hold for H512. No defect.
- **r3 merge resolutions read against the merged branches** (`deep/r3_merges.md`, per-merge diffs `deep/r3/`):
  every merge's automatic 3-way result was recomputed with `git merge-tree` and diffed against the committed merge, so
  exactly R3-1's manual edits were read; of 37 merges 16 were clean and 21 conflicted (the merged branches patched
  src/search.cpp, which the stack had split into src/search/*.inc, or added option blocks at the same place). S14,
  S29, S11, S13, S41, SIT, S12 are hunk-for-hunk the branch's code; A1, O2, C6, C1, C2, C3, O4, O5, O8, C5 and the
  O7 combo are marker removals, moved option handlers and R3's documented unifications (instance selection, v2 option
  rules), all cross-checked ON against their branches by R3-1 except HardDeadline, whose statement order was
  verified by hand; S08fix is entirely under `#ifdef FORGE_PROF` with `#else` keeping the lock code. No logic change by any
  resolution. Owner item: the stack's `bad_captures_` is still 64 entries in both `#if` branches of movepicker.hpp;
  the fable-review-buffix change belongs there too.
- **Planted-bug (mutant) checks re-run on the PC** (`deep/mutants/<job>.log`, runner `deep/fable_nnue_mutants.sh`,
  `deep/fable_nnue_mutants_py.sh`): each job's own mutation script run from a fresh LF export of the branch head
  (Idle priority, two build jobs). Shell-style jobs, mutants caught / not caught, re-run vs Opus's committed log:
  O3 8/0 = 8/0, C2 14/0 = 14/0, C4 10/0 = 10/0, C4 fail-loud 13/0 = 13/0, C5 8/0 = 8/0 (the committed folder also
  holds an older pre-merge log with 6 more), O4 6/0 = 6/0, O5 20/0 = 20/0, O6 8/0 = 8/0, O7 7/0 = 7/0, O8 19/0 =
  19/0. Every planted bug is still caught. The Python-style checks (A1, SA2, SA4, S12 + alias, S41, C6, R3-4, R3-5,
  R3-6, port_c with/without -O2, O2, S14 + zero-fill, S08fix, SIT) are running at the time of this commit; their
  results follow in the next commit. Not re-run: C1 (its 290-file 3-5 man tablebase folder, 939 MiB, was stored
  outside the repository at a location the report does not record), S11 (the mutation evidence is a tarball of
  logs, no script), and the jobs that never had a scripted mutation check (C3, O1, O1-LTT, S04fix, S13, S29, S32,
  S37: their REPORTs describe hand-made planted bugs or none).
- **Buffix test strength**: a position with more than 64 SEE-losing noisy moves is being constructed (search driven by
  the engine's own census); result and the unfixed-engine overflow proof follow in the next commit.
- **S17 real-window re-run** (shards 010 last 200k rows + 011 + 012, read-only inputs): running; result follows.

## Final state of the correction branches (remote heads, 2026-10-28)

| branch | head | base | content |
|---|---|---|---|
| `fable-review-summary` | this commit | d4f4312 | this report + `fable_review/` evidence |
| `fable-review-buffix` | 4d6829c1 | d4f4312 + CI workflow | mistake 2: engine fix + test (a9cea71f), REVIEW.md |
| `fable-review-r3-stack` | 0bae2ea6 | opus-r3-stack da158149 | mistake 1: eight `.pyc` untracked, REVIEW.md |
| `fable-review-S33fix` | 3004fc91 | opus-sol-S33fix | mistake 3: comparison normalises line endings |
| `fable-review-S38` | a9884584 | opus-sol-S38 | mistake 3: comparison normalises line endings |
| `fable-review-S46` | 56daf94c | opus-sol-S46 | mistake 3: comparisons normalise line endings |
| `fable-review-S42` | 8e29bb90 | opus-sol-S42 | mistake 3: job-folder `.gitattributes` |
| `fable-review-S08fix` | a886a68f | opus-sol-S08fix | mistake 3: job-folder `.gitattributes` |
| `fable-review-S15` | 2d2affa1 | opus-sol-S15 | mistake 3: repository-root `.gitattributes` |
| `fable-review-S47` | 73dcf433 | opus-sol-S47 | mistake 3: job-folder `.gitattributes` |
| `fable-review-S39` | 9b88f433 | opus-sol-S39 | mistake 3: job-folder `.gitattributes` |
| `fable-review-S50` | 495f6098 | opus-sol-S50 | mistake 3: job-folder `.gitattributes` |
| `fable-review-SA3` | 8a16aa4a | opus-sol-SA3 | mistake 3: job-folder `.gitattributes` |
| `fable-review-SA2` | 8588f896 | opus-sol-SA2 | mistake 3: job-folder `.gitattributes` |
| `fable-review-S27fix` | ba917b00 | opus-sol-S27fix | mistake 3: repository-root `.gitattributes` |

## Time spent (measured from the commit timestamps, PC clock, 2026-10-28)

The upfront estimate was 12-16 h. The measured span is under 2 h: the FB1 branch's last commit is at 11:53:35, the
first review commit (the inventory) at 12:05:22, the last (this version) at 13:52:51; 58 commits on 15 branches in
between, in four context windows. The per-"session" hour figures that stood here before (adding up to about 6.5 h)
were estimates written without a clock and were wrong; the "sessions" are context windows, not hours. Sub-agents
ran in parallel for about 40 minutes of the span.

Why so much less than estimated: the CI logs already held the identity, ASan/UBSan and TSan results of all 30
engine branches, so the engine sweep was log reading instead of 30 rebuilds; every tool job ships its own test
suite, which runs in seconds from an export; the test failures collapsed into one class with one fix pattern; the
real-data re-executions (S44, S16, S21, S19) take seconds to minutes; and reading a diff is fast.

What the short time did not buy is in the honest-scope section: engine jobs were read at diff level, O7 at
structure level, the trainer variants only through their suites, S17/S40 not re-executed, no engine branch rebuilt
on the PC except the R3 head and buffix. If the owner wants the original estimate spent, the next 8-10 h would be:
a line-by-line read of the large engine diffs (O7, SA2/SA4, S32, the r3 merges) against their specs, the
planted-bug (mutant) checks of every engine job re-run on the PC, a buffix test position with more than 64
SEE-losing noisy moves, and S17/S40 on the real shards once the second self-play folder is available.
