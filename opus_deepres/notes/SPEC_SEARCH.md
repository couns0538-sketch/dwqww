# SPEC_SEARCH: implementation specs for the lock-direct search cards T04-01, T04-03, T04-05, T04-06, T04-04

Started 00:51 PC clock (`date`), planned stop 01:36. Status: COMPLETE (all five specs written, last edit 01:06 `date`;
own review only, not independent).
Lock FD3A5190 = AL1 s198 source, read-only:
`C:/Users/Administrator/grok-pc/forge_push/qa_ltopgo_al1_stage/src_al1s198_clean` (below: `search.cpp` = `src/search.cpp`,
`search.hpp` = `include/forge/search.hpp`). Nothing here edits the engine; every Forge-side number is UNPROVEN.

## Reading record (lock and own Forge code read for this note, 00:51-00:55)
- search.cpp (1,531 lines) and search.hpp (408 lines) read in full; uci.cpp option code :160-225, bench :377-410.
- Option mechanism: an `int` in `namespace tune` (search.cpp:13-64), a row in `tune::parameters()` (:66-100), an
  `extern` in search.hpp:194-245; uci.cpp accepts any listed name via setoption (:204-215), advertises them only
  under FORGE_EXPOSE_TUNABLES (:174-181, kit -Expose). uci.cpp untouched (skill forge-r15-candidates).
- Pins (lock FD3A5190): bench d11 312866, d13 862329, d16 3024920, d20 12389307, d22 34048354; perft 5 4865609,
  kiwipete 193690690. Bench = 8 FENs (uci.cpp:383-392), Hash 16, clear per FEN, Threads 1, TTAccess Exclusive.
- T04-01: :1095 verification passes cut_node; uses inside the verification frame: :1031 IIR, :1141 LMR +2,
  :1151 / :1160 child flags; :952 block skipped (excluded).
- T04-03: cutoff_count field search.hpp:273; clear (ss+1) :905; LMR read :1145; increment :1180; (ss+2)->killers
  :907 (slot exists); NMP :965-999; null_tries_ / null_cutoffs_ search.hpp:345-346, reset :1241-1242.
- T04-05: corr update gate :1216-1223 (capture skip :1219); see_ge board.cpp:932 (promotion handled :951-953).
- T04-06: singular block :1089-1111; double :1102; budget :1116. Own port source: git fable-fb2-j3
  (1efc0b2c) src/search.cpp:1218 (triple: non-PV, < singular_beta - 80, inherited doubles <= 4, !tt_capture) and
  :1236 (`extension >= 2`).
- T04-04: corrected_eval :638-645, update_correction :647-656, tables search.hpp:322-323, alloc :568-569,
  clear :581-582. Own minor key: F:/opus_scratch/r5/r5b/flake/base_src/include/forge/correction_plus.hpp:51-56
  (avalanche of piece bitboards x own odd multipliers, Board unchanged); CorrMinorWeight default 100 on git
  opus-r5a-singles src/search/tune.inc:39.

## Common parts (all five specs)
- Functions: search.cpp:875-1225 is `Worker::search` (T04-01, T04-03, T04-05, T04-06 edits); :771-870
  `Worker::qsearch`; :638-645 `Worker::corrected_eval` and :647-656 `Worker::update_correction` (T04-04); :561-571
  `Worker::Worker` and :575-584 `Worker::clear` (T04-04 tables); `struct SearchStack` is search.hpp:262-284 (T04-03
  field); options live in `namespace tune` (search.cpp:13-103).
- Option recipe: an `int` in `namespace tune` (search.cpp:13-64), default 0 (= the lock path), one row appended to
  `tune::parameters()` (:66-100), one `extern` next to search.hpp:194-245. Kit v2.3 `-Expose` advertises it (the
  crew's runner checks that). uci.cpp untouched; its `id author` line stays (skill forge-r15-candidates).
- Clean-room: the patch carries no other engine's code, constants, names or comments; source attribution stays in
  this note and the card. Every source cited below is MIT (Caissa, Patricia, Altair; rows in notes/T04/licences.md),
  read as diff / PR text by T04; nothing GPL / AGPL / unlicensed was opened for this note; no web read here.
- OFF proof (each): kit `-Expose` build pc1 = pc2, `pin_check -Full` = the pins above (bench d11-d22 + perft).
  The kit profile is trained with the option OFF, so ON code is cold-optimised: say so in the review.
- ON live (each): `pin_check -Options 'Name=V'` must report LIVE, i.e. bench d13 != 862329 (d16 / d20 if d13 is
  equal by chance; equal at d20 too = the option is not wired).
- Box tests (each): a separate counter build (own macro FORGE_SPEC_COUNTERS, never in the gate exe): per-worker
  `uint64_t` counters that search only increments and never reads, printed as one `info string` line after `bench`.
  Check first that the counter build's bench nodes equal the plain build's at the same options (counters do not
  touch the tree). Positions: the 8 bench FENs at d16 and d20, plus the crew's mate probe set OFF / ON.
- Gate line (each): UHO SPRT at STC, then LTC, vs lock FD3A5190, exact `setoption` strings below; Threads per the
  owner's decision too (worker rules: gates Threads=1; the current *_vs_AL1* gates ran Threads 2 / conc 4); bounds
  per the owner's pending decision (FINAL_REPORT.md section 6 item 2 / card T12-01: [0,10] nElo cap 12k or [0,15]
  nElo cap 6k; the cards' "[0,5]" unit is unresolved - read as logistic Elo it is ~[0,9.5] nElo on UHO). 8moves_v3
  only as a separate confirm, never pooled.
- Gate cost at the measured 430-502 games/h (*_vs_AL1* gates): [0,10] cap 12k = mean ~6.6k games = ~13-15 h per STC
  line; [0,15] cap 6k = mean ~2.95k = ~6-7 h (T12-01 own model, UNVERIFIABLE). The seven STC lines below (T04-01 1,
  T04-03 2, T04-05 1, T04-06 1, T04-04 2; +2 if bundle 68 is adopted) = ~90-105 h at [0,10] or ~42-49 h at [0,15].

## T04-01 SingularNonCut (verification search as a non-cut node)
Source: Caissa 1b7a871 (MIT), 10+0.1, 1 thread, [0,2], n=25,044, +4.20 +- 2.23, LLR 2.94, no LTC. Card estimate
0 to +3 Elo at STC **UNPROVEN**.
- Lock lines: search.cpp:1095 `search(board, ss, singular_depth, singular_beta - 1, singular_beta, cut_node)`. Inside
  that verification frame (same `ss`, `excluded` = the TT move) `cut_node` is read at :1141 (LMR `r += 2`, the main
  effect), :1151 and :1160 (full-depth children get `!cut_node`), :1031 (IIR; rare: the verification re-probes the
  same key at :910, so `tt_move` is normally the excluded move, not none). Not reached there: :952-1028 (skipped,
  `excluded` set; so NMP :979 / ProbCut :1018 flags never see it), :1089 block (no nested singular), :1163 (null
  window, not PV). :1148 passes `true` regardless.
- Live share: only singular nodes that are cut nodes change. PV nodes always run with `cut_node == false` (callers
  :1163, :1391), and non-cut non-PV nodes already pass `false`.
- Option: `SingularNonCut`, spin, default 0, range 0-1, own start 1 (the only ON value).
- Change (own pseudocode):
  `verify_cut = (SingularNonCut > 0) ? false : cut_node` ; `singular_score = search(..., singular_beta, verify_cut)`.
  Nothing to restore: `cut_node` is a by-value parameter, the node's own flag is untouched (the card's "restored
  afterwards" is automatic).
- OFF node-identical: at 0 the argument is `cut_node` bit for bit and nothing else reads the option -> pins.
- ON live: `SingularNonCut=1` bench d13 != 862329.
- Box tests (counter build, 8 FENs d16 / d20): singular tries (entries to :1089), tries with `cut_node` true (= the
  live share), outcomes per try (+1 :1101, +2 :1103, multicut return :1106, -2 :1108, -1 :1110), nodes spent inside
  the verification (`local_nodes_` before / after :1095). The card's own (unproven) reasoning predicts more nodes per
  verification and fewer +1 / +2 ON; a rise means the flipped child flags (:1151 / :1160, all children now cut nodes)
  dominate - report it, it is not a stop. Sanity: d22 ON nodes within 0.7x-1.5x of OFF; mate probe OFF = ON results.
- Gate line: `setoption name SingularNonCut value 1`; route as in Common parts.
- Crew hours: 1 (card: option + pins + ON bench + smoke) + 0.5 for the counter build and box run.

## T04-03 NmpFewCutoffs (null-move margin discount when the child ply produced few cutoffs)
Source: Caissa e53fe6e (MIT): LTC 60+0.6 [0,3] n=10,918 +5.95 +- 3.14 LLR 2.95; STC 10+0.1 [0,2] n=61,474 +2.00 +- 1.41
LLR 2.95 (TC trend suggestive only, intervals overlap). Card estimate 0 to +2 Elo per ON form **UNPROVEN**.
- Lock lines: search.hpp:273 `cutoff_count`; search.cpp:905 clears `(ss + 1)->cutoff_count` at entry, :1145 LMR reads
  it, :1180 `++ss->cutoff_count` on a beta cutoff; :907 already writes `(ss + 2)->killers` (slot exists: `stack_` has
  MaxPly + 8 frames, search.hpp:324, root at `stack_[4]` :1360, and past :894 ply <= MaxPly - 1, so ss + 2 <= frame
  133 of 136); NMP :965-968 (`eval >= beta && ss->static_eval >= beta - 24 * depth + 180 && ...`), reduction
  :970-971, null search :979; `null_tries_` :969, `null_cutoffs_` :985 / :995 (search.hpp:345-346, reset :1241-1242).
- Why a new field: :905 zeroes `(ss + 1)->cutoff_count` at entry and nothing runs at ss + 1 before :965, so that
  counter is always 0 at null-move time; reusing it would also change what LmrCutoffThreshold (:1145) means.
- New field `sibling_cutoffs` (own name) in SearchStack right after `cutoff_count` (search.hpp:273; same cache line
  area as `killers`, which :907 already touches). Rule "clear two plies ahead": at node entry next to :907
  `(ss + 2)->sibling_cutoffs = 0`; next to :1180 `++ss->sibling_cutoffs`. At :965 `(ss + 1)->sibling_cutoffs` = the beta
  cutoffs scored at ply + 1 since the parent started, i.e. by the children of this node's earlier siblings. Frame
  reuse (lock semantics, accepted): a verification search run at the parent's frame (:1095 or :990) clears the count
  again at its entry. Root clears frame ply 2, so ply-1 nodes read a fresh count; no reset needed at :1349-1359.
- Options (all spin): `NmpFewCutoffs` default 0 (= off), range 0-6, own start 3 ("few" = count <= value);
  `NmpFewCutoffsDiscount` default 0, range 0-72, own start 24 cp (one ply of the lock's 24-per-depth NMP slope, :965);
  `NmpFewCutoffsForm` default 1, range 1-2, read only when both others are > 0. Own starts differ from the source's
  (fewer than 2, bonus 19) - not copies.
- Change (own pseudocode) at :965:
  `few = NmpFewCutoffs > 0 and NmpFewCutoffsDiscount > 0 and (ss+1).sibling_cutoffs <= NmpFewCutoffs`
  `eval_ok = eval >= beta` ; `static_ok = static_eval >= beta - 24*depth + 180`
  `if few and Form == 1: eval_ok = eval_ok or (eval >= beta - Discount and raw_eval >= beta)` (source-faithful form:
  the corrected / TT-adjusted eval may sit just below beta while the raw eval (search.hpp:271, set :935-936) is >=
  beta; the lock's static term is kept);
  `if few and Form == 2: static_ok = static_eval >= beta - 24*depth + 180 - Discount` (shallow-term form, live at
  depth 3-7 mainly);
  then the lock's test with `eval_ok and static_ok` in place of its first two terms, the rest of :966-968 unchanged.
- Reduction guard: under form 1 `eval - beta` can be -72..-1, and :971 `(eval - beta) / NullMoveEvalDivisor` truncates
  to 0 for |eval - beta| < divisor (default 200, range min 50), so at the start values the reduction is unchanged; write
  `max(0, min((eval - beta) / NullMoveEvalDivisor, 3))` anyway. OFF identical: on the OFF path `eval >= beta`, so the
  `max(0, ...)` is a no-op.
- OFF node-identical: the new counter is written but never read at the defaults (read behind both values > 0); with
  Discount 0 both forms reduce to the lock's test as well -> pins. The extra store per node and the larger SearchStack
  can only move speed: one nps ABBA OFF exe vs the lock exe (expect noise; report).
- ON live: `NmpFewCutoffs=3 NmpFewCutoffsDiscount=24` (form 1) bench d13 != 862329; same with `NmpFewCutoffsForm=2`.
- Box tests (counter build, 8 FENs d16 / d20): NMP-eligible nodes (reaching :965 with depth >= NullMoveMinDepth),
  share of them where "few" holds (if it holds at most eligible nodes, the start 3 is too loose: move it to 1-2 before
  gating), `null_tries_` / `null_cutoffs_` per 1M nodes OFF vs ON, extra tries that only the discount allowed and their
  cutoff rate (a low rate = wasted null searches). Zugzwang / mate probe: the crew's mate probe set plus a few own
  zugzwang-prone middlegame / minor-piece endgame FENs, best move and score at fixed depth OFF = ON.
- Gate lines: form 1 first `setoption name NmpFewCutoffs value 3` + `setoption name NmpFewCutoffsDiscount value 24`;
  form 2 as the second line (+ `setoption name NmpFewCutoffsForm value 2`). STC = no-loss check; the LTC run decides
  (do not stop after an STC H0 inside +-2 Elo); route and bounds as in Common parts.
- Crew hours: 2 (card: field + clear + increment + three options, OFF identity, ON bench, smoke) + 0.5 counters.

## T04-05 CorrBadCapture (correction update also after a SEE-losing capture best move)
Source: Caissa 54aef4a (MIT), 10+0.1, 1 thread, [0,2], n=44,298, +2.63 +- 1.68, LLR 2.97, no LTC. Card estimate
0 to +2 Elo **UNPROVEN**.
- Lock lines: search.cpp:1216-1223 gate the update; the skip is :1219 `(best_move.is_none() || !best_move.is_capture())`;
  update itself :647-656, called at :1222. At :1219 every move was unmade (:1165), so `board` is the node's own
  position and `board.see_ge(best_move, 0)` (board.cpp:932) is valid. Quiet promotions already update today
  (`is_capture()` false); capture-promotions are skipped as captures.
- Option: `CorrBadCapture`, spin, default 0, range 0-1, own start 1.
- Change (own pseudocode): `skip = best_move is a capture` ; `if CorrBadCapture > 0 and skip and not see_ge(best_move, 0):
  skip = false` ; update when the lock's other terms hold and not skip. SEE threshold 0 is the lock's own good / bad
  capture boundary (MovePicker :360 with `move_score_threshold() == 0`, :479), so no constant is carried over.
  Capture-promotions follow the capture rule (see_ge counts the promotion gain, board.cpp:951-953, so most stay
  skipped); quiet promotions keep the lock's handling (the source also skipped promotions - not taken).
  Optional, result-neutral: test the two bound terms (:1220-1221) before the SEE term so SEE runs only when an update
  would otherwise happen.
- OFF node-identical: `CorrBadCapture > 0 &&` is tested first, so `see_ge` is never called and the condition is the
  lock's -> pins.
- ON live: `CorrBadCapture=1` bench d13 != 862329 (the tables change, so later corrected evals and pruning change).
- Box tests (counter build): update_correction calls per 1M nodes OFF vs ON (ON > OFF expected), the count of
  updates that only the new branch allowed, and the mean |correction| read at :640-643 OFF vs ON (a large rise =
  the losing-capture residuals are noisy; report). Mate probe OFF = ON results.
- Gate line: `setoption name CorrBadCapture value 1`; route as in Common parts.
- Crew hours: 1 (card) + 0.5 counters.

## T04-06 TripleExtMargin (triple singular extension, decided at LTC)
Sources: Patricia PR 147 (MIT) 60+0.6, [0,3], n=24,804, +3.12 +- 2.14, LLR 2.96 (non-captures only); Caissa f2967c1
(MIT) 80+0.8, [0,2.5], n=25,260, +3.36 +- 2.07, LLR 2.97 (a bundle: also dropped its per-path double cap, PV extras).
No STC logged by either. Card estimate 0 to +3 Elo at LTC **UNPROVEN**.
- Lock lines: search.cpp:1100-1104 (single +1, double +2 when non-PV, `singular_score < singular_beta - 24` and
  `inherited_double_extensions <= 6`), :1116 path budget `+ (extension == 2)`, :883-884 inherited budget, :1097
  restore after the verification, :1117 `new_depth = depth - 1 + extension`, :918 `tt_capture`.
- Own port source (Forge code): git fable-fb2-j3 (1efc0b2c) src/search.cpp:1218 (triple: non-PV, below
  `singular_beta - 80`, inherited doubles <= 4, `!tt_capture`) and :1236 (`extension >= 2`). Port these two only -
  not its PV doubles (:1220), multicut or -3 / -2 negative extensions (SingularV2 bundle, never gated).
- Option: `TripleExtMargin`, spin, default 0 (= off), range 0-400, own start 80 (FB2-J3's own value; the T04 TABLE
  row 6 alternative "60 below the double threshold" = 84 is practically the same). Values <= 24 turn every double into
  a triple: keep >= 40 as the lower bound of any later tuning. Budget: own literal 4 (FB2-J3), not an option.
- Change (own pseudocode), after the double step inside `if (singular_score < singular_beta)`:
  `if TripleExtMargin > 0 and not pv_node and not tt_capture and inherited_double_extensions <= 4 and
  singular_score < singular_beta - TripleExtMargin: extension = 3` ; and at :1116
  `double_extensions = inherited + (extension >= 2)` (a triple uses one unit of the path budget, as FB2-J3).
  `!tt_capture` = the extended move (== tt_move here) is not a capture.
- OFF node-identical: at 0 the branch is dead, so `extension` stays in {-2, -1, 0, 1, 2}, where `>= 2` equals `== 2`:
  the :1116 change is unconditional and identical by value domain -> pins.
- ON live: `TripleExtMargin=80` bench d13 != 862329 (triples need depth >= SingularDepth 7 and a very singular TT
  move; if d13 is equal, d16 / d20 must differ).
- Box tests (counter build): triples and doubles per 1M nodes, the largest `double_extensions` seen (must stay <= 7 =
  the lock's path cap 6 inherited + 1), max seldepth per FEN ON vs OFF, nodes per iteration (no explosion: d22 ON within
  1.5x of OFF), returns at the `ply >= MaxPly` guard :894 (0 or as OFF). Mate probe OFF = ON results.
- Gate line: `setoption name TripleExtMargin value 80`; STC only as the no-loss check, the LTC run decides (both
  sources measured only long TC); route and bounds as in Common parts.
- Crew hours: 2 (card: triple step + budget change, one option, proofs) + 0.5 counters.

## T04-04 MinorCorrectionWeight / MajorCorrectionWeight (two more correction-history keys)
Sources: Altair PR 189 minor / PR 188 major (MIT, PR text): 8+0.08, 1 thread, [0,4] with LLR bounds (-2.25, 2.89),
minor +7.74 +- 5.71 n=7,008, major +6.84 +- 5.23 n=8,280; both stopped early (inflated), no LTC. Card estimate
+1 to +4 Elo **UNPROVEN**. Overlap: a non-pawn key (packa NonPawnCorr, bundle 68, CorrHistPlus bit 4) covers part
of both keys.
- Lock lines: search.cpp:638-645 `corrected_eval` (pawn :640, material :641-643 only when MaterialCorrectionWeight > 0),
  :647-656 `update_correction` (same diff :649 / weight :650 / `apply` lambda :651-653 for both tables, material update
  :655 gated the same way); callers :809 (qsearch), :937 (search), :1222 (update); tables search.hpp:322-323
  (`std::unique_ptr<CorrectionHistory>`, 2 x 16,384 int32 = 128 KiB each), alloc :568-569, clear :581-582;
  `material_key` :588-596 is computed on demand (Board unchanged).
- Keys (own Forge code, no Board change): minor key = port of the R3 header
  F:/opus_scratch/r5/r5b/flake/base_src/include/forge/correction_plus.hpp:37-56 (same file in git opus-r5a-singles
  include/forge/correction_plus.hpp, `minor_piece_key` at :52) (avalanche of the WN, WB, BN, BB, WK,
  BK bitboards times own odd multipliers; the finaliser is the public-domain SplitMix64 output step). Major key = the
  same form over WR, WQ, BR, BQ, WK, BK with a fresh own draw of six odd 64-bit multipliers. Index `key & (CorrectionSize
  - 1)` as the pawn table. Only the keys are ported: use the lock's int32 tables and linear `apply` (:651-653), not
  the R3 int16 entries, decay `apply` or 64 cp blend clamp.
- New members: `minor_correction_`, `major_correction_` (same type, pattern of search.hpp:322-323), allocated next to
  :568-569, cleared next to :581-582 (+256 KiB per worker; `Worker::clear()` covers both).
- Options (spin): `MinorCorrectionWeight` default 0 (= off), range 0-300, own start 100; `MajorCorrectionWeight`
  default 0, range 0-300, own start 100 (100 = the pawn table's weight, the lock's own MaterialCorrectionWeight scale
  and the R3 CorrMinorWeight default, git opus-r5a-singles src/search/tune.inc:39). Second value 50 if the total
  correction grows too much (with both at 100 the term can reach +-128 cp vs +-64 cp today).
- Change (own pseudocode):
  `corrected_eval`: after :643 add `if MinorW > 0: c += minor[side][minor_key(board) & mask] * MinorW / 100` and the
  same for Major; the :644 clamp stays. `update_correction`: after :655 add
  `if MinorW > 0: apply(minor[side][minor_key(board) & mask])` and the same for Major. Sum bound: 8,192 + 3 x 24,576
  at max weights = 81,920, far inside int32.
- OFF node-identical: at weight 0 a key is neither computed, read nor updated (the :641 / :655 rule), so evals and
  the tree equal the lock -> pins. The new allocation and clear only move speed / bench time (bench clears per FEN):
  one nps ABBA OFF exe vs the lock exe.
- ON live: `MinorCorrectionWeight=100` bench d13 != 862329; separately `MajorCorrectionWeight=100`.
- Box tests: (1) key test (own CTest): the minor key changes on every knight / bishop / king move (incl. castling,
  captures of those pieces, promotion to knight / bishop) and on nothing else; the major key the same for rook /
  queen / king (castling moves both); both equal a slow reference built from piece lists over a perft-4 walk of the
  bench FENs. (2) Fill rate: distinct indices hit per table over a d16 bench (expect a broad spread). (3) Counter
  build: mean |term| per key ON, share of evals where a new key moves the eval by > 8 cp. (4) nps ABBA ON vs OFF:
  the on-demand keys cost two hashes per node (expected ~1-2 % nps ON; part of the trade, report it).
- Gate lines: A `setoption name MinorCorrectionWeight value 100`; B `setoption name MajorCorrectionWeight value 100`;
  each alone vs the lock, and each on top of bundle 68 if the owner adopts it (overlap with its NonPawnCorr w50);
  route and bounds as in Common parts.
- Crew hours: 4 (card: two keys ~40 lines, two options, OFF pins, ON benches, smoke) + 1 for the key CTest.

## Order for the crew (own reading, no Elo claim)
T04-01 and T04-05 first (one line each, 1 h), then T04-06 (LTC decides), T04-03 (two forms, LTC decides), T04-04
(two lines, overlap with bundle 68 to settle first).
