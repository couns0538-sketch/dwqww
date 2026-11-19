# kimi5 job 33 — Step 1: K1, K2, K3 read on my chain (committed before Step 2)

Chain: 6b98f217 + pc_r15 (sha256 d6bd72c5…) + history_age + count27 + age_split (the job-30 split
build; step0/exe.sha256 = 7a956e98… = job 30's split build hash, bit-identical). Compiled with
FORGE_SEARCH_SPEED2=1 (CMakeLists.txt:34), FORGE_PAWN_HISTORY=0 (search.hpp:403-404 default, not
set), -DFORGE_MATE_ALPHA_GUARD=1. All line numbers are from this tree (/tmp/j33/split).

## K1 — the test compares h with t; h = blend(M, W, 3) + C1 + C2. CONFIRMED, formula identical.

- The test: src/search.cpp:2169
  `if (lmr_depth <= tune::HistoryPruneDepth && history < history_prune_threshold) {`
  (`history` is h, `history_prune_threshold` is t). r15d names 2235 and 2294; my chain's matching
  pair is 2110 (h computed) and 2169 (the test) — the same 59-line apart layout.
- h is computed at src/search.cpp:2110:
  `const int history = quiet ? quiet_history(board, ss, move) : capture_history_value(board, move);`
- Worker::quiet_history, src/search.cpp:1474-1502. With FORGE_SEARCH_SPEED2=1 the compiled branch is
  1477-1487: quiet_history_sum(main row, cont1, cont2, cont4, piece, move) + threat_quiet_bonus
  + rework; the pawn term is compiled out.
  - M: quiet_history_sum (src/search.cpp:351-360) starts with `main[move.from][move.to]`, the row
    `(*main_history_)[side_to_move]` passed at 1478. ButterflyHistory = [2][64][64] int16
    (include/forge/search.hpp:395).
  - C1: `(ss-1)->continuation` passed at 1479, added at 356 when not null: `(*cont1)[piece][to]`.
  - C2: `(ss-2)->continuation` passed at 1480, added at 357 when not null.
  - No 4-ply term under PC20: cont4 = nullptr (1481-1482: `tune::ContHist4PlyRead && … ? (ss-4)->continuation
    : nullptr`; ContHist4PlyRead default false, src/search.cpp:165, not set by pc20.opt).
  - No threat bonus under PC20: threat_quiet_bonus returns 0 when !tune::ThreatHistory
    (src/search.cpp:1532-1536; ThreatHistory default false, src/search.cpp:169, not set by pc20.opt).
  - No pawn history: FORGE_PAWN_HISTORY=0.
  - W and the blend: the rework term at 1476 calls rework_quiet_delta (src/search.cpp:1517-1520) =
    `b4::blend(plain, rework_entry(board, ss, move), b4::threat_quarters(tune::HistRework)) - plain`
    with plain = M (1518). rework_entry (src/search.cpp:1507-1513) =
    `(*rework_history_)[side][b4::square_bit(set, from)][b4::square_bit(set, to)][from][to]` where
    set = threat_maps_[ss->ply].by_type[piece_type(moved piece)] — the lesser-threat bits of this
    node (LesserThreatHistory = [2][2][2][64][64] int16, include/forge/b4.hpp:105-106).
  - b4::threat_quarters(level) = clamp_level(level)+1 (b4.hpp:28); HistRework=2 under PC20
    (pc20.opt line 16; default 0 at src/search.cpp:184) → quarters = 3.
  - b4::blend(plain, threat, 3) = (plain*1 + threat*3)/4, C++ int division truncated toward zero
    (b4.hpp:65-67).
  - So under PC20: h = M + C1 + C2 + (blend(M, W, 3) − M) = blend(M, W, 3) + C1 + C2 exactly (int
    arithmetic; |values| ≤ 2·16384 so no overflow). MATCHES K1 as written.
- Consequence for the counter: the check `h == B + C1 + C2` with B = blend(M, W, 3) must hold at
  every eligible test under every PC20-derived options file of this job (all have HistRework=2,
  ThreatHistory off, ContHist4PlyRead off, no pawn history). The counter recomputes M, W, C1, C2
  from the same entries between 2110 and 2169; no history write happens inside the move loop, so
  the entries cannot change between the engine's read and the counter's read.

## K2 — t = −HistoryPruneMultiplier·depth·3/4 (TtPruneV2 on, not improving) else −HPM·depth. CONFIRMED.

- src/search.cpp:2154-2156:
  `const int history_prune_threshold = tt_prune_v2_ && !improving
       ? -tune::HistoryPruneMultiplier * depth * 3 / 4
       : -tune::HistoryPruneMultiplier * depth;`
- tt_prune_v2_ = tune::TtPruneV2, one snapshot per search (src/search.cpp:2510); TtPruneV2=true
  under PC20 (pc20.opt line 17). HistoryPruneMultiplier=2220 under PC20 (default 2048 at
  src/search.cpp:117). depth is the node's depth (the search function's parameter).
- Int arithmetic left-to-right: (−2220·d)·3/4 = −6660d/4 = −1665d exactly; the else arm −2220d.
  MATCHES K2's "−1,665 × depth or −2,220 × depth".

## K3 — reachability. CONFIRMED on my chain, element by element.

- The shallow-pruning block opens at src/search.cpp:2122-2123:
  `if (!sound_mate_case && mate_moves_ == 0 && board.halfmove_clock() + depth < 100 && !root_node &&
       best_score > -MateInMaxPly && has_material && !bare_king_mode)`
  - sound_mate_case at 2118-2121 (SoundArmPv&&pv_node || SoundArmInCheck&&in_check ||
    SoundArmMateAlpha&&is_mate_score(alpha)).
  - mate_moves_ == 0: not a `go mate` search.
  - has_material = board.has_non_pawn_material(board.side_to_move()) (src/search.cpp:2083): the
    side to move has non-pawn material.
  - best_score > -MateInMaxPly: best score above the mated range.
- The move must be quiet, give no check, and be prunable: `if (quiet && !gives_check && prunable)`
  at src/search.cpp:2157; prunable = !tt_prune_v2_ || move != tt_move (2152) — with TtPruneV2 on,
  the TT move never reaches the test.
- The quiet futility test above (2158-2167: `!in_check && lmr_depth <= FutilityDepth &&
  MateAlphaGuard-arm && static_eval + FutilityBase + futility_improving + FutilityMultiplier·lmr_depth
  <= alpha`) must not have pruned it (its `continue` skips the history test). The futility test
  needs not-in-check; the history test at 2169 has no in_check condition. MATCHES K3.
- The test prunes only when lmr_depth <= HistoryPruneDepth; HistoryPruneDepth default 3
  (src/search.cpp:116), not set by pc20.opt → 3. lmr_depth = max(0, depth − reduction(…)) at 2147.
- ELIGIBLE for the counter = control reaches src/search.cpp:2169 with
  lmr_depth <= tune::HistoryPruneDepth (the counter hooks exactly there, before the h<t half of
  the condition).
