# T05C verify (adversarial check of cards/T05C and notes/T05C)

Verifier window 00:35-00:55 PC clock, 2026-11-05 (`date` at start 00:35). Scratch: F:/odr/work/T05C-verify/ (fetched
files, the uops.info page). Method: every number re-opened at its own source (gh api for GitHub pages, mine_commits.py
--show for test logs, the raw file at the exact sha for MIT repos, curl for uops.info), Elo recomputed from W/L/D,
licence rows re-run with tools/licence_at.py --row, Forge-has greps re-run with tools/forge_has.sh, every cited lock
line read in src_al1s198_clean, the lock-exe listing F:/odr/work/T05C/lock_v23.dis re-grepped, tried gates and all
cards/*/ scanned for duplicates. Verdicts: CONFIRMED / CORRECTED / UNVERIFIABLE / VIOLATION / DUPLICATE.

Verifier note on reading: Stockfish was checked through commit messages and PR bodies only (gh api .commit.message /
.body), never a source file. The two MIT files re-fetched for the table-size and mask-name checks (Caissa
src/backend/Bitboard.cpp 740 lines, chess-library src/movegen.hpp 888 lines, attacks_fwd.hpp 266 lines) were
downloaded whole into the scratch folder and only grep hits were read, the same over-cap fetch the worker reported.

## T05C-01 (one-line card: per-node check info for is_legal, gives_check, has_legal_move, make_move checkers)

| card | claim | verdict | evidence |
|---|---|---|---|
| T05C-01 | Caissa 0dc61c8 +1.31 +- 1.92, 8+0.08, SPRT [-1,2], N=59,368 | CONFIRMED | mine_commits --show 0dc61c8 (2024-02-08) "Use threats info to generate less illegal king moves": Elo 1.31 +- 1.92, 8.0+0.08s Threads=1, LLR 2.95 [-1.00, 2.00], N 59368 W 14119 L 13895 D 31354; recomputed Elo from W/L/D = +1.31; the card correctly calls it a related but different change |
| T05C-01 | chess-library movegen.hpp checkMask / pinMask / seenSquares @430266434a | CONFIRMED | raw file at the sha: checkMask L55, pinMask L104, seenSquares L123 |
| T05C-01 | chess-library PR 229 stops at the first legal move (TABLE row 3, sources W13) | CONFIRMED | PR 229 "IsGameOver(): avoid unnecessarily generating all moves", merged 2026-03-10, merge 3dd41be3; body: break out of generation at the first legal move; no number in the PR |
| T05C-01 | Forge has it: board.cpp:558-575, :577-598, :671-701, :786; search.cpp:692-702, :780, :893 | CONFIRMED | lines read: has_legal_move 558-575 (pawn-push witness, else MoveList + generate_pseudo_legal + is_legal loop); is_legal 577-598 (occupancy edit + square_attacked_with_occupancy for every move); gives_check 671-701 (castle rook lookup, direct lookup by type, two discovered lookups: up to 4 for a queen move); make_move 786 `checkers_ = attackers_to(...)` at every move; is_draw 692-702 runs has_legal_move at every non-check node, called at 780 (qsearch) and 893 (search) |
| T05C-01 | "no pinned cache (forge_has 'pinned' or 'blockers_for': see_ge-local scans only)" | CORRECTED | the grep returns 1 hit, a comment at src/eval.cpp:189, nothing in see_ge; the see_ge pin scan (board.cpp:970-994: pinners from two empty-board lookups, loop per pinner) was found by reading, not by the grep. Card wording amended "(corrected by verify: ...)" |
| T05C-01 | has_legal_move fallback memsets a 1,032-B list | CONFIRMED | listing: Board::has_legal_move at 0x14000aa00, `mov $0x408,%r8d` at 0x14000aaa2 before the memset call |
| T05C-01 | +1 to +3 % nps, more in endgames without a free pawn push | UNVERIFIABLE | static estimate, nothing measured; the card states that no logged number exists for the mechanism; UNPROVEN label present |
| T05C-01 | no other engine's tuned constant proposed | CONFIRMED | the card proposes booleans / bitboards and a build switch only |
| T05C-01 | duplicate check | none found | tried_gates grep (pext, magic, memset, pinned, check info, movelist, legal, slider, bitboard, movegen): 0 of 110 gates; packa / packb / E3 options are search / eval options; no card on legality or check info in cards/*/ (the "pinned" hit in T02-04 is a position note) |
| T05C-01 | source fetch size (W3 movegen.hpp 888 lines fetched whole) | VIOLATION (minor, caps) | self-reported in sources.md ("downloaded whole by mistake, only the grep hits and line windows read"); MIT repo, so no licence rule touched; noted in the card's licence field |

## T05C-02 (full card: move arrays without zero fill; quiets-only generation)

| card | claim | verdict | evidence |
|---|---|---|---|
| T05C-02 | README: Ryzen 9 5950X, kiwipete d5 430 ms = 449.4 Mnps "with movelist preallocation" | CONFIRMED | README @430266434a L37 "Tested on Ryzen 9 5950X", L49 "With movelist preallocation:", L54 depth 5, 430 ms, 449398352 nps, kiwipete FEN |
| T05C-02 | comparison.md: 538 ms = 359.4 Mnps without preallocation, machine not stated | CONFIRMED | comparison/comparison.md @sha L7 "`chess-library` had no movelist preallocation, same as the other libraries", L12 depth 5 time 538 nodes 193690690 nps 359351929; no CPU named in the file; surge 230,036,448 and THC 38,400,216 (sources W1) also match |
| T05C-02 | "not a controlled A/B" | CONFIRMED | two tables, machine of the second not stated; the card and TABLE row 5 say so |
| T05C-02 | lock search.cpp:450 moves_{}, :453 bad_captures_{}, :456 MoveList buffer_, :459 check_squares_{}, :1034-1035 quiets_tried{} / captures_tried{}, :523-536 generate_quiets = full list + filter | CONFIRMED | all lines read; generate_quiets 523-536 = init_check_squares + generate_pseudo_legal(buffer_, false) + skip captures / promotions; generate_evasions 538-555 the same full list |
| T05C-02 | board.hpp:34-39 Move member initialisers, :49-73 MoveList | CONFIRMED | Move = 4 x std::uint8_t each `= 0` (34-39); MoveList Capacity 256 (49-51), size_ at 72 |
| T05C-02 | `Move move;` at search.cpp:827 and :1044 assigned before use | CONFIRMED | 827-828 assigned inside the while condition; 1044 the same pattern |
| T05C-02 | pick_best: selection swaps for the first picks, then an unstable std::sort | CONFIRMED | search.cpp:488-503 (index_ - list_start_ < 4 swap, else std::sort with a > comparator, sorted_ = true) |
| T05C-02 | codegen: two CRT memset calls per picker (0x800, 0x400) in search and qsearch, 19 / 4 zmm zero stores, has_legal_move memset 0x408, perft rep stos 0x102 dwords, 0 pext / 0 pdep / 487 imul | CONFIRMED | listing F:/odr/work/T05C/lock_v23.dis (12,955,263 B, 2026-11-05 00:10): Worker::search at 0x1400edd40 has `mov $0x800,%r8d` at 0x1400ee73f and `mov $0x400,%r8d` at 0x1400ee7b1 (three such pairs in the function = inlined pickers); Worker::qsearch at 0x1400fa980 has 0x800 at 0x1400faf87 + `call 140024b60 <memset>` at 0x1400faffb and 0x400 at 0x1400fb051 (+ a second picker at 0x1400fd370); zmm zero stores by regex: 19 in the search range, 4 in the qsearch range; Board::perft 0x140101786: `mov $0x102,%ecx; rep stos`; grep -c pext 0, pdep 0, imul 487; the lock exe sha256 starts fd3a51903e73dc1f (recomputed) |
| T05C-02 | "~2,200 cycles per node" from 2.24 Mnps | CONFIRMED as a basis | notes/T05/SPEED_LIST.md row 5 (probe nps 2.24M from the 30-h counters); 5 GHz clock is an assumption and is labelled as one |
| T05C-02 | 70-120 cycles per node -> +1 to +3 % search nps; quiets-only +0 to +1 % | UNVERIFIABLE | static count, not measured; UNPROVEN label present; no logged search-nps number for the change (the card says missing) |
| T05C-02 | bench pins d11-d22 312866 / 862329 / 3024920 / 12389307 / 34048354; perft 4,865,609 / 193,690,690 | CONFIRMED | the same pins appear in T04C-01, T04C-02, T04C-05, T12-01; 4,865,609 and 193,690,690 are the standard startpos d5 / kiwipete d5 counts (chess-library README table) |
| T05C-02 | no other engine's tuned constant | CONFIRMED | poison byte and array sizes are own choices |
| T05C-02 | duplicate check | none found | no card on zero fill / move lists in cards/*/; "MovePicker hoist" from the already-done list is a different change (picker placement, not the fill) and is not in notes/T05/SPEED_LIST.md; tried gates 0 |

## T05C-03 (full card: PEXT slider index, 16-bit PDEP entries, compile-time tables)

| card | claim | verdict | evidence |
|---|---|---|---|
| T05C-03 | Stockfish PR 6845: +3.11 % nps (1,136,025 -> 1,171,370, 100 runs), STC [0,2] LLR 2.93, 29,792 games W 7759 L 7465 D 14568, AVX2 build | CONFIRMED | PR body (gh api): "HQ attacks for AVX2"; LLR 2.93 (-2.94,2.94) <0.00,2.00>, Total 29792 W 7759 L 7465 D 14568; 100 runs base 1136025 +/- 2816, test 1171370 +/- 2848, diff +35346 +/- 3275, speedup +0.0311, P(speedup > 0) = 1.0; recomputed Elo +3.43 (the card gives no Elo for this test) |
| T05C-03 | Stockfish e17725f445: STC [0,2] LLR 2.97, 38,400 games W 10057 L 9749 D 18594, ~+2.8 Elo, gain mostly from shared tables, "gains a little outside of fishtest as well" | CONFIRMED | commit message: LLR 2.97 (-2.94,2.94) <0.00,2.00>, Total 38400 W 10057 L 9749 D 18594; "compile time generation leads to sharing tables through the binary, resulting in gain on fishtest"; "Using pdep reduces table size 4x, and gains a little outside of fishtest as well"; "No functional change"; recomputed Elo +2.79 |
| T05C-03 | Stockfish 99489f57dd: pext "slower or equal to parallel-hyperbola attacks", non-regression <-1.75,0.25> avx512icl 81,632 and bmi2 78,112 games | CONFIRMED | commit message: avx512icl LLR 2.96, 81632 games; bmi2 LLR 2.93, 78112 games; quote verbatim; recomputed +0.70 / +0.74 |
| T05C-03 | Stockfish ee72cf49fe (TABLE row 10): 212,800 games W 55208 L 54665, LLR 3.01 | CONFIRMED | commit message "Optimize RankAttacks": LLR 3.01 <0,2>, Total 212800 W 55208 L 54665 D 102927; recomputed +0.89 |
| T05C-03 | Stockfish PR 6706 text (W9): "takes forrrever, and bloats the binary", pdep 4x | CONFIRMED | PR body verbatim |
| T05C-03 | Caissa 7ed119c: +3.01 +- 1.84, 5+0.05 Threads=1, [0,2], LLR 2.95, N=37,274 | CONFIRMED | mine_commits --show 7ed119c (2026-08-25, "No functional change"): N 37274 W 9297 L 8974 D 19003; recomputed Elo +3.01 |
| T05C-03 | Caissa Bitboard.cpp @57cae7ef71: 102,400 + 5,248 entries (PEXT), 84,480 + 4,800 (magic path) | CONFIRMED | L27-28 cRookAttackTableSize 102400 / cBishopAttackTableSize 5248 with ParallelBitsExtract (L311); L195-196 84480 / 4800 |
| T05C-03 | chess-library attacks_fwd.hpp @430266434a: PEXT index behind CHESS_USE_PEXT, tables 0x19000 / 0x1480 | CONFIRMED | L19 #ifdef CHESS_USE_PEXT, L23 _pext_u64, L154-155 RookAttacks[0x19000] / BishopAttacks[0x1480] |
| T05C-03 | uops.info Zen 5 PEXT latency 3, throughput 0.33, 1 uop; Zen 2 latency 18 (mask operand), TP 19.00, microcoded | CONFIRMED | page fetched 2026-11-05: Zen 5 "Latency operand 2 -> 1: 3, operand 3 -> 1: 3, Throughput 0.33, uops 1"; Zen 2 "operand 3 -> 1: 18, Throughput 19.00, uops 7, ucode" |
| T05C-03 | lock bitboard.hpp:143-171 Magic struct + index, bitboard.cpp:23-24 tables 0x19000 + 0x1480, :63-108 runtime magic search, 841 KiB | CONFIRMED | lines read; 0x19000 x 8 B = 800 KiB + 0x1480 x 8 B = 41 KiB |
| T05C-03 | forge_has 'pext|pdep|bmi2': 4 false hits on RfpDepth | CONFIRMED | re-run: search.hpp:202, search.cpp:22, :73, :960, all RfpDepth |
| T05C-03 | 27 slider-lookup call sites in board.cpp, 10 in eval.cpp | CONFIRMED | grep -c 'attacks::(bishop|rook|queen)\(' = 27 / 10 |
| T05C-03 | "786 KiB float w1" in the hot-set sentence | CORRECTED | include/forge/nnue.hpp: InputCount 768, HiddenSize 256 (rules), float = 768 x 256 x 4 B = 786,432 B = 768 KiB (786 kB); card and notes/T05C/BOARD_COST.md amended "(corrected by verify: ...)"; the conclusion (hot set > 1 MiB L2) is unchanged |
| T05C-03 | "~1.55 MiB histories" | UNVERIFIABLE | not re-derived in the window (would need every history array's dimensions in search.hpp) |
| T05C-03 | Forge estimate 0 to +1 % (value 1), +0.5 to +3 % (values 2 / 3) | UNVERIFIABLE | static reasoning; UNPROVEN label present; the card asks for a microbench first |
| T05C-03 | Stockfish read as commit and PR text only; no tuned constant carried over | CONFIRMED | sources.md W7-W10 and licences.md say commit / PR text; nothing in the card or notes quotes a Stockfish source line; the card proposes switch values 0-3 and table layouts, no constants |
| T05C-03 | duplicate check | none found | no PEXT / magic / slider card in cards/*/ or notes/T05/SPEED_LIST.md; tried gates 0 |
| T05C-03 | source fetch size (W5 Bitboard.cpp 740 lines fetched whole) | VIOLATION (minor, caps) | self-reported in sources.md; MIT repo (source reading allowed), so no licence rule touched; noted in the card's Status line |

## T05C-04 (former card: material key kept in Board)

| card | claim | verdict | evidence |
|---|---|---|---|
| T05C-04 | duplicate of T05B-02 variant (b), MERGED into notes/T05C/TABLE.md row 18 | DUPLICATE (confirmed) | cards/T05B/T05B-02-exact-material-key.md title "exact material key without the serial multiply chain (closed form, or incremental in Board)", source search.cpp:588-596 = the same function (forge_has 'material_key' = :588, :642, :655); TABLE row 18 carries the call sites as evidence for T05B-02 |
| T05C-04 | file format | CORRECTED | the one-line pointer had no Status line and failed card_lint (9 findings); rewritten by verify as a ONE-LINE card whose idea field marks DUPLICATE / MERGED (file kept, not deleted; lint 0 findings) |

## Licence rows (tools/licence_at.py --row re-run 2026-11-05)

| repo | sha | result | verdict |
|---|---|---|---|
| Disservin/chess-library | 430266434a | 2026-11-03, LICENSE, MIT, api: MIT | CONFIRMED (identical row) |
| Witek902/Caissa | 57cae7ef71 | 2026-11-04, LICENSE, MIT, api: MIT | CONFIRMED |
| Adam-Kulju/Patricia | 67d83d7056 | 2026-09-12, LICENSE, MIT, api: MIT | CONFIRMED |
| Alex2262/AltairChessEngine | 12ac55a0e2 | 2026-01-21, LICENSE, MIT, api: MIT | CONFIRMED |
| official-stockfish/Stockfish | e17725f445 | 2026-04-26, Copying.txt, GPL-3.0, api: GPL-3.0 | CONFIRMED (ideas only; text sources only) |

## Notes spot checks (TABLE.md, sources.md)

| note | claim | verdict | evidence |
|---|---|---|---|
| TABLE row 19 / W12 | Altair PR 196 "Varied movegen", merge 33292b9, 1,342,447.6 vs 1,365,878.2 nps "-1.705 % +/- 1.249 %", "Q_BN" | CONFIRMED | PR 196 merged 2026-01-03, merge 33292b931212; body "1342447.607 v.s. 1365878.179: -1.705 % +/- 1.249 %", "Max Heap ordering only in Q_BN" |
| TABLE row 21 / W4 | Caissa 5a6f623 codegen-only movegen / threat tuning, no functional change | CONFIRMED | mine_commits --show 5a6f623 (2026-04-03) "Optimize move generation and threat computation codegen" |
| sources.md | web sources W1-W13 (W4b counted with W4) = 13 <= 15; engines read in depth: chess-library, Caissa (+ Altair PR 198 patch) <= 3; forum threads 0 | CONFIRMED | counted from sources.md |
| cards / notes | no vendor or model-company names; no licence headers | CONFIRMED | grep over cards/T05C and notes/T05C: 0 hits |

## Folder checks
- 4 files in cards/T05C (<= 4): T05C-02 and T05C-03 full, T05C-01 one-line, T05C-04 one-line duplicate pointer.
- Crew hours: T05C-01 6-8 h, T05C-02 1-2 h code + 1-2 h proofs, T05C-03 3-4 h (+3-4 h, HQ 6-10 h): present.
- UNPROVEN on every Forge estimate; gate route nps ABBA only on every card; OFF-by-default build switch named on each.
- card_lint after the verify edits: see the last line of this file.

## Counts
- Claims checked: 43 card table rows above (T05C-01 10, T05C-02 13, T05C-03 18, T05C-04 2) plus 5 licence rows and 4 note
  checks = 52 items; 42 CONFIRMED, 3 CORRECTED, 4 UNVERIFIABLE, 2 VIOLATION rows (one minor class), 1 DUPLICATE.
- Corrected: 3 (T05C-03 "786 KiB" -> 768 KiB; T05C-01 forge_has wording; T05C-04 rewritten as a lint-clean ONE-LINE
  duplicate pointer). No source number or link was wrong.
- Unverifiable: 4 (the three Forge nps estimates, all labelled UNPROVEN; "~1.55 MiB histories").
- Violations: 1 class, minor (the ~300-line fetch cap on two MIT files, self-reported by the worker). No licence or
  reading-rule breach found; no tuned constant from another engine proposed.
- Duplicates: 1 (T05C-04 = T05B-02 variant (b); already merged by the worker, now marked in the file).

## Lint and close
- card_lint after the verify edits (00:45 PC clock): T05C-01 0 findings, T05C-02 0, T05C-03 0, T05C-04 0 (both one-liners carry 7 fields after ONE-LINE). Files changed by verify: cards/T05C/T05C-01, -03, -04, notes/T05C/BOARD_COST.md, this file. Nothing committed (the coordinator commits).
- Verify ended 00:45 PC clock.
