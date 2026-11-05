# SPEC_SEARCH2: implementation specs for the search cards T04E-03, T04E-02, T04B-01, T04D-01, T04D-02

Started 04:08 PC clock (`date`), planned stop 04:43. Status: COMPLETE (all five specs written by 04:20 `date`; own review only, not independent).
Layout as notes/SPEC_SEARCH.md. Lock FD3A5190 = AL1 s198 source, read-only:
`C:/Users/Administrator/grok-pc/forge_push/qa_ltopgo_al1_stage/src_al1s198_clean` (`search.cpp` = `src/search.cpp`,
`board.hpp` / `search.hpp` / `eval.hpp` under `include/forge/`). Nothing here edits the engine; every Forge-side number
is UNPROVEN. No web read for this note: the mechanisms come from the five cards (their sources are GPL / AGPL /
unlicensed = ideas only, and nothing of theirs was opened here) plus the lock source. No card was edited.

## Reading record (lock, read-only, 04:09-04:14)
- search.cpp :13-20 and :96-103 (tune ints / parameters() rows), :107 HistoryMax 16384, :153-155 history_bonus,
  :157-160 apply_history, :692-699 is_draw, :704-767 (quiet_history, capture_history_value :714-718,
  update_continuation :720-727, update_quiet_stats :729-750, update_capture_stats :752-767), :905-1000 (TT probe and
  cutoff, eval, razor, RFP, NMP), :1030-1088 (IIR, move loop, pruning), :1112-1215 (LMR, cutoff, list appends,
  history calls, TT store); :875 `Worker::search(..., bool cut_node)`.
- board.hpp:16-18 (Piece: Empty = 0, WP = 1 ...), :22 (PieceType: Pawn 1, Knight 2, Bishop 3, Rook 4, Queen 5,
  King 6), :163-167 (moved_piece, captured_piece: en passant -> opponent pawn, else piece on `to`), :200 (color_of
  returns White for Empty); eval.hpp:32 SeePieceValue {0,100,300,300,500,900,0}; search.hpp:252-255 history types.
- uci.cpp:383-392 bench FENs. Option names below grepped in src/ and include/: no hit (no collision).

## Common parts (all five)
- Option recipe, kit `-Expose` build (pc1 = pc2), OFF proof `pin_check -Full` = the lock pins (bench d11-d22 + perft),
  ON-live rule (bench d13 != 862329, else d16 / d20; equal at d20 = not wired), counter build FORGE_SPEC_COUNTERS
  (search increments, never reads; its bench nodes must equal the plain build's): all exactly as in
  notes/SPEC_SEARCH.md "Common parts". Every master row admits 0 and defaults to 0 = the lock path; a secondary row
  (QuietMalusStart {100,150} default 100, NoisySeeHistCap {50,400} default 150, TtCutNodeForm {1,2} default 1) admits
  its own default and is dead at master 0, so the OFF proof (all masters 0) is unchanged (review fix).
- Gate line (crew decision, WORKER_RULES "Numbers"; it replaces SPEC_SEARCH.md's pending-bounds text): candidate vs
  lock FD3A5190, UHO book, Threads=1, SPRT [0,5] normalized Elo, alpha = beta = 0.05, pentanomial, cap 3,000 games.
  A run that hits the cap without a decision = UNPROVEN / no decision (not H0, not a pass); if its Elo is positive it
  gets exactly one extension (its size is not written in WORKER_RULES: the crew sets it). STC first, LTC after an STC
  H1. 8moves_v3 only as a separate confirm, never pooled. Cost at 430-502 games/h: <= 6.0-7.0 h per capped line.
- Box FENs (five named lock bench FENs, fixed depth): F1 uci.cpp:384 start position; F2 :385
  `r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1` (many captures); F3 :387
  `8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1` (rook and pawn ending, zugzwang-prone); F4 :389
  `2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1` (tactical); F5 :391
  `r2q1rk1/ppp2ppp/2n1bn2/2bpp3/3PP3/2N1BN2/PPP1BPPP/R2Q1RK1 w - - 0 9` (quiet middlegame, history-heavy).
  Per FEN: new process or `ucinewgame`, Hash 16, Threads 1, `position fen ...`, `go depth 16`; record nodes, score,
  bestmove. OFF exe = lock exe per FEN (identity). ON: record with the card's expected direction; a per-FEN ON/OFF
  node ratio outside 0.5x-2x = stop and look; bench d22 total ON within 0.7x-1.5x of OFF.
- Sanity FENs (hand-checked by the writer, not engine-run), `go depth 12` OFF and ON, same score class and move class:
  S1 mate in 1 `6k1/5ppp/8/8/8/8/5PPP/3R2K1 w - - 0 1` (white-to-move twin of bench FEN :390): mate 1, d1d8.
  S2 stalemate, no legal move `7k/5Q2/6K1/8/8/8/8/8 b - - 0 1`: the lock's no-move reply, identical OFF / ON.
  S3 stalemate trap `7k/8/4Q2K/8/8/8/8/8 w - - 0 1`: mate 1 by e6e8 or e6c8, never e6f7 / e6g6 (both stalemate).
  S4 50-move draw `8/8/8/4k3/8/8/8/3QK3 w - - 99 200`: cp 0 (every move reaches half-move 100 without mate; is_draw
  :694-696). S5 mate on the hundredth half-move `7k/8/6K1/8/8/8/8/R7 w - - 99 150`: mate 1 by a1a8 (is_draw keeps a
  mate at half-move 100, :695-696). Plus the crew's mate probe set OFF / ON.

## T04E-03 QuietMalusDecay (quiet malus that shrinks with the try index)
Source (card; ideas only, nothing opened here): Reckless PR 1038 (AGPL-3.0; title, branch name, logs): STC 8+0.08
+4.67 +- 2.78 n=15,778 [0,3]; LTC 40+0.4 +5.18 +- 2.88 n=12,682 [0,3]; UHO_Lichess_4852_v1, 1 thread. Same idea
passed in three more engines per the card's evidence pointers (T04D-03, T04G-03, T04C-04). The source's exact rule is
unknown; the form below is the card's own. Card estimate +1 to +3 Elo **UNPROVEN**.
- Lock lines: update_quiet_stats search.cpp:729-750; bonus :731 = history_bonus(depth) :153-155 (min(2048,
  20 d^2 + 48 d - 32)); best move +bonus main :742, continuation :743 via update_continuation :720-727 (plies back 1,
  2, 4; ply 4 gets half, :725); malus loop :744-749 (-bonus main :747, continuation :748). Caller :1196-1199, only on a
  beta cutoff with a quiet best move, at depth + (best_score > beta + 100). List quiets_tried :1034 (128 slots),
  appended at :1186 in search order and only for searched moves (pruned moves `continue` at :1062-1083 first). The
  cutoff `break` :1181 comes before :1186, so the cutoff move is never in the list and the skip :746 never fires on
  this path: try index k = loop index i. Capture malus :759-765 untouched. apply_history :157-160 clamps to +-16384.
- Options (spin): `QuietMalusDecay` (step in % per try index) default 0 = off, range 0-20, own start 8;
  `QuietMalusStart` (% of bonus at k = 0) default 100, range 100-150; `QuietMalusFloor` (%) default 40, range 0-100.
  Start and floor are read only when the step > 0; the ranges keep floor <= 100 <= start. Own values (card).
- Change (own pseudo-steps), in update_quiet_stats after :742-743:
  1. If QuietMalusDecay == 0: run the lock loop :744-749 unchanged (the OFF path keeps its literal -bonus).
  2. Else: k = 0; for each quiet in the list (skip `== move` as the lock): scale = max(Floor, Start - k * Decay);
     malus = bonus * scale / 100; apply_history(main[us][from][to], -malus);
     update_continuation(ss, moved piece of quiet, to, -malus); k = k + 1.
  3. The scaled value goes through update_continuation, so plies 1 and 2 get it and ply 4 its half, as for -bonus now.
  Bounds: bonus <= 2048, scale <= 150 -> <= 307,200 (int). Start 100 / step 8 / floor 40 gives k=0 100 %, k=1 92 %,
  ..., k=7 44 %, k>=8 40 %; k = 0 equals the lock at start 100.
- OFF node-identical: step 0 -> the lock loop -> pins. ON live: `QuietMalusDecay=8` bench d13 != 862329 (every quiet
  cutoff with >= 2 tried quiets differs).
- Box tests (counter build, F1-F5 d16, S1-S5): maluses per k bucket (0, 1-3, 4-7, 8+) per 1M nodes; share of quiet
  cutoffs with >= 2 tried quiets (live share); first-move cutoff rate (cutoffs at move_count 1 / all cutoffs) OFF vs
  ON; history prunes :1070 per 1M nodes OFF vs ON (smaller late maluses = fewer prunes; report). Own expectation,
  unproven: F5 nodes down, first-move rate up.
- SPSA (after an STC H1 or a capped positive run; CSV name,start,min,max,c, a / schedule per skill forge-o30-spsa):
  `QuietMalusDecay,8,1,20,2`; `QuietMalusStart,100,100,150,8`; `QuietMalusFloor,40,0,100,8` (step min 1 keeps it ON).
- Gate line: `setoption name QuietMalusDecay value 8`, `setoption name QuietMalusStart value 100`,
  `setoption name QuietMalusFloor value 40`; crew line (Common parts). The card's capture-history variant is a later,
  separate option (see "Shared code" below).
- Crew hours: 2 (card) + 0.5 counters.

## T04E-02 NmpTtCaptureMin (no null move when the hash move captures a valuable piece)
Source (card; ideas only): Reckless PR 671 (no licence at the merge commit): STC 8+0.08 +3.43 +- 2.31 n=22,374 [0,3],
LTC 40+0.4 +3.67 +- 2.27 n=20,816 [0,3]; Viridithas PR 412 (read as ideas only): LTC 40+0.4 +1.88 +- 1.48 n=49,814
[0,3]; UHO_Lichess_4852_v1, 1 thread. Their thresholds are unknown. Card estimate +1 to +3 Elo **UNPROVEN**.
- Lock lines: tt_move :913, tt_capture :918; NMP condition :965-968 (depth >= NullMoveMinDepth 3, eval >= beta,
  static margin, null_move_allowed, previous move not null, own non-pawn material, TT upper-bound guard :968);
  null_tries_ :969, null_cutoffs_ :985 / :995 (reset :1241). Victim = captured_piece(tt_move) (board.hpp:164-167).
  tt_move is not validated before :965 (a colliding entry can carry another position's move; the lock validates it only
  in the MovePicker, `board_.is_pseudo_legal(tt_move_)` at :326, after NMP), so the guard below runs the lock's own
  test `board.is_pseudo_legal(tt_move)` (board.cpp:600) before it reads the victim or calls see_ge (review fix).
- Options (spin): `NmpTtCaptureMin` default 0 = off, range 0-5, own start 4 (rook or queen; 2 = minor or better, 1 =
  any capture). Variant B `NmpTtCaptureSee` (cp) default 0 = off, range 0-900, own start 300. Both > 0: either blocks.
- Change (own pseudo-steps), one term appended last to :965-968 (so it is evaluated only when NMP would run):
  1. plausible = tt_capture and board.is_pseudo_legal(tt_move) (review fix) (the lock's own test, as at :326, replaces
     a hand-made victim / mover / colour test that a stale EnPassant flag passes; see_ge board.cpp:932 reads from / to
     and the en-passant square straight from the move, and the lock calls it only on generated or checked moves).
     Passing it means a real capture: mover ours (board.cpp:604), target not ours and not a King (:606), en passant
     only on the live ep square with the Capture flag (:641), Capture needs a piece on `to` (:646 / :658); so the
     victim is Pawn..Queen of the other side.
  2. block = (NmpTtCaptureMin > 0 and plausible and piece_type(victim) >= NmpTtCaptureMin) or
     (NmpTtCaptureSee > 0 and plausible and see_ge(tt_move, NmpTtCaptureSee)); plausible (one is_pseudo_legal call)
     is evaluated only after a `> 0` test, and the victim is read only after plausible (review fix).
  3. NMP runs only if not block; else the node goes on to ProbCut :1000 and the move loop (TT move first).
  En passant victims are pawns (type 1): below every start value.
- OFF node-identical: both 0 -> the term is constant true and reads nothing -> pins. ON live: `NmpTtCaptureMin=4`
  bench d13 != 862329 (needs NMP-eligible nodes whose TT move takes a rook / queen; F2 / F4 have them).
- Box tests (counter build, F1-F5 d16, S1-S5): NMP-eligible nodes and the share blocked, by victim type; null_tries_
  and null_cutoffs_ per 1M nodes OFF vs ON (tries must fall: the card's check); at blocked nodes the share that still
  ends >= beta with best move == tt_move (own expectation, unproven: high; low = useful null moves blocked); F3 score
  and move class OFF = ON. Blocking only removes null searches, so no new zugzwang exposure.
- SPSA: none for the type threshold (discrete: 4, then 3 / 2 by hand); variant B if gated: `NmpTtCaptureSee,300,100,900,50`.
- Gate lines: A `setoption name NmpTtCaptureMin value 4`; B only after A ends H0 or capped <= 0:
  `setoption name NmpTtCaptureSee value 300` (A at 0). Crew line.
- Crew hours: 1.5 (card 1-2) + 0.5 counters.

## T04B-01 NoisySeeHistDiv / NoisySeeHistCap (capture history in the noisy SEE pruning threshold)
Source (card; ideas only): Stormphrax PR 269 (GPL-3.0; title and OpenBench result lines): STC 8+0.08 +3.08 +- 2.21
n=28,964 [0,3]; LTC 40+0.4 +6.48 +- 3.34 n=10,130 [0,3]; book DFRC_4852_v1 (double Fischer random, not UHO), 1
thread. No formula or constants were read. Card estimate +1 to +4 Elo **UNPROVEN**.
- Lock lines: `history` :1058 (quiet sum for quiets, capture_history_value :714-718 for the rest; CaptureHistory
  [13][64][7] int16, search.hpp:255, +-16384); pruning guard :1061; quiet non-check branch :1064-1071; else branch
  :1072-1084 = captures, promotions and quiet checks; capture futility :1075-1080 (already uses history / 8);
  threshold :1081 `-SeeNoisyMultiplier * depth` (150, :35); the shortcut :1082 skips SEE only when the picker's
  good-capture flag is set AND threshold <= 0, so a positive threshold already reaches see_ge :1083: no change there
  (the card's debug assert is a check, not a fix).
- Scope (own choice, narrower than the card's `!quiet`): captures only (`move.is_capture()`, incl. capture-promotions
  and en passant). Lock reason: a non-capture promotion reads capture slot victim 0 (piece_type(Empty) = 0, board.hpp:199), which only ever gets maluses (the
  bonus :754 needs `best.is_capture()`; every tried non-quiet move, :1187, gets -bonus :759-765), so its shift would be
  one-sided. Quiet checks keep the lock threshold (their `history` is the quiet sum).
- Options (spin): `NoisySeeHistDiv` default 0 = off, own start 96; its parameters() row must be {0, 512} (the card's
  16-512 is the tuning range and would exclude the default 0; 1-15 are legal and just saturate at the cap).
  `NoisySeeHistCap` (cp) default 150, range 50-400, read only when the divisor > 0.
- Change (own pseudo-steps) at :1081:
  1. threshold = -SeeNoisyMultiplier * depth (lock).
  2. If NoisySeeHistDiv > 0 and capture: shift = clamp(history / NoisySeeHistDiv, -Cap, +Cap); threshold -= shift.
  3. :1082-1083 unchanged.
  Start values: a good record lowers the threshold by up to 150 cp (more losing captures searched), a poor one raises
  it by up to 150 cp (at depth 1 up to 0 = the capture must not lose; with Cap > 150 it can turn positive = must win).
- OFF node-identical: divisor 0 -> no division, lock threshold -> pins. ON live: `NoisySeeHistDiv=96` bench d13 !=
  862329.
- Box tests (counter build, F1-F5 d16 with F2 / F4 capture-rich, S1-S5): see_ge calls at :1083 and prunes there per
  1M nodes OFF vs ON; in the counter build the lock threshold is evaluated beside the ON one (counted only, search
  follows the option) to count prunes added (shift < 0) and removed (shift > 0); share of shifts at the cap; positive
  thresholds (each forces a SEE call the shortcut skipped). Debug asserts: term only for captures; threshold > 0
  never takes the shortcut.
- SPSA (after STC): `NoisySeeHistDiv,96,16,512,24`; `NoisySeeHistCap,150,50,400,25`.
- Gate line: `setoption name NoisySeeHistDiv value 96`, `setoption name NoisySeeHistCap value 150`; crew line. Alone
  first, then with T04B-02 (same site, card). T04E-04 (qsearch SEE :838) is another site and its own gate. The source
  gained more at LTC: LTC after an STC H1.
- Crew hours: 2 (card) + 0.5 counters.

## T04D-01 CutNoTtLmr (one more LMR ply at cut nodes without a TT move)
Source (card; ideas only): Stockfish 9cc15b3 (GPL-3.0; title, message, fishtest records): STC 10+0.1 [0,2] +2.72 +-
1.74 n=42,304 LLR 2.93; LTC 60+0.6 [0.5,2.5] +3.35 +- 1.81 n=32,334 LLR 2.95; UHO_Lichess_4852_v1, 1 thread. The
one-ply amount is the card's own. Card estimate 0 to +3 Elo at STC **UNPROVEN**.
- Lock lines: tt_move :913 (constant per node; none on a miss or when this position's entry never held a move: the
  store keeps an older move for the same position, search.cpp:293); IIR :1031 (depth >= 4, no TT move, PV or cut node: --depth; kept); LMR block :1137-1158: base :1138,
  `cut_node` +2 :1141, clamp :1147 to [1, new_depth], reduced search :1148, re-search :1149-1153, continuation boost
  :1154-1157. Inside the singular verification frame (:1095, excluded = TT move) tt_move is that move, so the new
  term is dead there (no overlap with T04-01 SingularNonCut).
- Option (spin): `CutNoTtLmr` default 0 = off, range 0-2, own start 1 (one whole ply; 2 = the size of the existing
  cut-node term). Not SPSA (two values).
- Change (own pseudo-steps): 1. after :1141: if CutNoTtLmr > 0 and cut_node and tt_move is none: r += CutNoTtLmr.
  2. Nothing else: :1147 keeps reduced_depth in [1, new_depth].
  IIR stays (review fix): at depth >= IirDepth 4 (:38), not in check, such a cut node already lost one ply at :1031,
  so the term stacks a second ply on each late move there. This stacking is intended; read the box test "share
  clamped at reduced_depth 1" with it in mind.
- OFF node-identical: 0 -> no term -> pins. ON live: `CutNoTtLmr=1` bench d13 != 862329.
- Box tests (counter build, F1-F5 d16, S1-S5): LMR searches at cut nodes without a TT move per 1M nodes (live share);
  share clamped at reduced_depth 1 OFF vs ON; re-search rate :1149 at those nodes OFF vs ON (a large rise eats the
  saving); boosts :1156 per 1M nodes; own expectation, unproven: F1-F5 nodes down.
- Gate line: `setoption name CutNoTtLmr value 1`; crew line; LTC after an STC H1 (the source's LTC was not below
  its STC).
- Crew hours: 1 (card) + 0.5 counters.

## T04D-02 TtCutNodeDepth (shallow TT cutoffs only when the stored direction matches the node type)
Source (card; ideas only): Stockfish 43e100a (GPL-3.0; title, message, PR text, fishtest records): STC 10+0.1 [0,2]
+2.72 +- 1.72 n=41,184; LTC 60+0.6 [0.5,2.5] +1.02 +- 0.62 n=270,888; follow-up a4edacb (depth limit only): STC
+1.63 +- 1.23 n=83,648, LTC +1.96 +- 1.25 n=68,160; UHO_Lichess_4852_v1, 1 thread. Depth limits unknown. The commit
text states only the fail-high half; the two-sided rule is the card's reading. Card estimate 0 to +3 Elo **UNPROVEN**.
- Lock lines: :875 `cut_node` parameter, :876 `pv_node = beta - alpha > 1`; TT cutoff :921-926 (non-PV, no excluded move, usable score, tt_depth >=
  depth, halfmove < 90, bound test :923-924). Non-PV nodes are null-window (alpha = beta - 1), so `tt_score <= alpha`
  equals `tt_score < beta` and an Exact score is on one side too: `tt_score >= beta` gives the direction for all three
  bounds. `depth` is the entry depth (IIR :1031 comes later). qsearch's TT cutoff stays.
- Options (spin): `TtCutNodeDepth` default 0 = off, range 0-14, own start 6; `TtCutNodeForm` default 1, range 1-2,
  read only when the depth > 0: 1 = fail-high half (source-stated: a cutoff at >= beta needs cut_node), 2 = both
  halves (card: a cutoff below beta also needs !cut_node).
- Change (own pseudo-steps): append last to :921-924: `TtCutNodeDepth == 0 or depth > TtCutNodeDepth or match`,
  match = Form 1: (tt_score < beta or cut_node); Form 2: ((tt_score >= beta) == cut_node). A refused cutoff searches
  the node normally (eval, NMP, move loop; tt_move still ordered first).
- OFF node-identical: 0 -> short-circuit -> pins. ON live: `TtCutNodeDepth=6` bench d13 != 862329, form 1 and form 2.
- Box tests (counter build, F1-F5 d16, S1-S5): TT cutoffs per 1M nodes by depth bucket (1-2, 3-4, 5-6, 7+) OFF vs
  ON (only <= 6 may change); refused cutoffs by kind (fail high at a non-cut node, fail low at a cut node); agreement
  = share of refused nodes whose search ends on the stored side of beta (near 100 % = the rule only burns nodes);
  F1-F5 nodes (own expectation: ON up); bench d20 ON within 1.5x of OFF.
- SPSA (after a first STC run, card): `TtCutNodeDepth,6,1,14,1` (integer, coarse).
- Gate lines: 1 form 1: `setoption name TtCutNodeDepth value 6`, `setoption name TtCutNodeForm value 1`; 2 form 2
  (`... TtCutNodeForm value 2`) only after line 1 ends H0 or capped <= 0. Crew line.
- Crew hours: 1.5 (card 1 + the form option) + 0.5 counters.

## Shared code, one build, gate order
- Edit sites: T04E-03 :744-749 (update_quiet_stats), T04E-02 :965-968, T04B-01 :1081, T04D-01 :1141, T04D-02
  :921-924. No two specs edit the same line.
- History coupling: T04E-03 writes main and continuation history (read by move ordering, history pruning :1070, LMR
  :1146 and `history` :1058 for quiets); T04B-01 reads capture history (:1058 -> :1081), written only by
  update_capture_stats :752-767, which T04E-03's first form does not touch: different tables, no shared code. The
  card's capture-history variant of T04E-03 would write what T04B-01 reads, so: T04B-01 is gated before that variant;
  if both pass, the variant is gated with T04B-01 ON and NoisySeeHistDiv re-checked (SPSA) on top. T04D-01 also feeds
  LMR (:1141 next to the :1146 history term) and changes how often the boost :1156 fires; no shared line with T04E-03.
- cut_node coupling: T04D-01 (:1141) and T04D-02 (:921) both key on cut_node. A cut node whose fail-low TT cutoff
  form 2 refuses and whose entry holds no move is exactly a T04D-01 node: a joint effect exists only with both ON.
- One build can carry all five: separate tune:: ints, default 0, each behind its own `> 0` test. One kit `-Expose`
  build with all five needs one OFF pin proof (all at 0) plus one ON-live bench per option, and one nps ABBA OFF exe
  vs the lock exe (cold code at five sites, profile trained OFF; expect noise, report; a slowdown beyond the A/A
  spread = build single-option exes instead). Each gate line sets exactly one option family; a combined line only
  after each passes alone, with its own ON-live bench and gate.
- Order (own reading, no Elo claim): 1 T04E-03 (four engines passed the idea; the lock's malus is flat; colour only,
  not lock evidence (review fix): tried gate 67 gate67_omnis_s12b_vs_h256e12, option HistMalusPct=125, on another
  base and opponent, 1,500 games, -7.41 (-15.55 .. -2.54), cap with no decision); 2 T04D-01 (1 h, one line); 3 T04E-02 (A, then B only after A's
  H0 / capped <= 0); 4 T04D-02 (form 1, then form 2 on the same condition); 5 T04B-01 (DFRC-book evidence only;
  before T04E-03's capture variant). Five firm STC lines = 30-35 h worst case at the cap (430-502 games/h), up to
  seven with the two conditional lines (42-49 h), plus extensions and LTC runs after H1.
- Crew hours total: 10.5 summed per spec incl. counters (2.5 + 2 + 2.5 + 1.5 + 2), before any gate time; one build
  carrying all five shares part of the build / pin / counter work (saving not estimated).
