# SPEC_REVIEW: adversarial review of SPEC_SEARCH2 and SPEC_SEARCH3 against the lock source

Started 04:39 PC clock (`date`), written by 04:52, planned stop 05:04. Status: COMPLETE (ten specs checked; no card
and no spec file edited). Reviewer: fable SPECREV (board slot S3). Read-only lock source FD3A5190 = AL1 s198:
`C:/Users/Administrator/grok-pc/forge_push/qa_ltopgo_al1_stage/src_al1s198_clean` (`src/search.cpp` 1,531 lines,
`include/forge/{board,search,eval}.hpp`, `src/uci.cpp`). Nothing here edits the engine; every Forge-side number is
UNPROVEN. No web read; no source of any other engine opened.

Questions per spec: (a) anchors exist and say what the spec claims; (b) OFF path node-identical (no reordering, no
changed history writes, no changed TT stores); (c) ON path vs mate scores, stalemate, 50-move, repetition, TT bound
semantics, history ranges; (d) start values are own values with a range; (e) interactions and gate order.
Verdicts: OK | FIX (exact fix in words; none of them blocks a build or a gate) | BLOCKER (none found).

## Reading record (lock, read-only, 04:41-04:45)
- search.cpp :13-103 (tune ints and parameters() rows), :107 HistoryMax, :109-123 score_to_tt / mated_in, :153-160
  history_bonus / apply_history, :162-166 capture_value, :286-296 TT store (:293 move kept), :319-333 MovePicker
  constructor (:325 `is_pseudo_legal` test of the TT move, :331-333 stage choice), :413-423 evasion stage, :538-555
  generate_evasions, :692-702 is_draw, :704-767 history helpers, :771-870 qsearch, :875-1220 search, :1238-1243
  counter reset, :1388-1392 root call (`false`).
- board.hpp :16-22 (Piece, PieceType), :163-167 (moved_piece, captured_piece), :196-201 (piece_type, color_of);
  eval.hpp :32 SeePieceValue; search.hpp :55-62 (MaxPly 128, Infinite 32001, MateValue 32000, MateInMaxPly,
  ValueNone, is_mate_score), :252-256 history types; uci.cpp :383-392 bench FENs; board.cpp :932-946 see_ge head.
- T04P-01 port tree `.../cands/caissa_c123/forge_caissa_c123_al1s198_src`: search.cpp :34-42, :86-90, :926-940,
  :970-982; search.hpp :215-219; record `qa_v22_checks/xchk_caissa_c123_TtCutExtraMargin.json` (1,547 bytes, Oct 30
  17:41); sha256 of `forge_push/bin/forge_ltopgo_x_caissa_c123_al1_8924099a.exe` starts 8924099ad4c42f45 (04:44).
- notes/SPEC_SEARCH.md :14 pins (d11 312866, d13 862329, d16 3024920, d20 12389307, d22 34048354, perft 5 4865609);
  `tools/tried_gates.py --grep 'HistMalus|QsEvasion'`: gate 67 and P27R-AL1 rows.
- Sanity FENs S1-S5 hand-checked by the reviewer: S1 d1d8 mate; S2 no legal move, no check (stalemate); S3 e6e8 /
  e6c8 mate, e6f7 and e6g6 stalemate; S4 no mate in 1, every move reaches half-move 100 (is_draw :694-696 -> 0);
  S5 a1a8 mate on the hundredth half-move (in check, no legal move: not a draw). All five as the spec states.

## Common parts (both notes)
- Pins, ON-live rule, box FENs F1-F5 (uci.cpp :384 / :385 / :387 / :389 / :391), S1 = white twin of :390: OK.
- FIX (wording, both notes): "every `tune::parameters()` row admits 0" is not what the specs build. The secondary
  rows QuietMalusStart {100,150} default 100, NoisySeeHistCap {50,400} default 150 and TtCutNodeForm {1,2} default 1
  do not admit 0 and need not: they are read only while their master option is > 0. Write the rule as "every master
  row admits 0 and defaults to 0; a secondary row admits its own default and is dead at master 0". The OFF proof is
  unchanged (all masters 0 = the lock path).
- Cost arithmetic 3,000 / 502 = 6.0 h, 3,000 / 430 = 7.0 h; 5 lines 30-35 h, 7 lines 42-49 h; crew-hour sums 10.5
  and 8: all correct.

## SPEC_SEARCH2

### T04E-03 QuietMalusDecay - OK
- (a) All anchors hold: update_quiet_stats :729-750, bonus :731 = history_bonus :153-155 (min(2048, 20 d^2 + 48 d
  - 32)), +bonus :742-743, update_continuation :720-727 (ply 4 half, :725), malus loop :744-749, caller :1196-1199
  with depth + (best_score > beta + 100) at :1198, quiets_tried :1034 (128), append :1186 after the cutoff `break`
  :1181, pruned moves `continue` at :1068 / :1070 / :1071 / :1079 / :1083 before the append. So the cutoff move is
  never in the list and the skip :746 is dead on this path: k = i, as claimed. Verified detail the spec does not
  say: the lock calls update_quiet_stats inside singular verification frames too (:1196 has no `excluded` test),
  so the ON rule also acts there; OFF is untouched.
- (b) Step 0 runs the lock loop with its literal -bonus: node-identical; no TT store or ordering change.
- (c) History only. malus <= 2048 x 150 / 100 = 3072, inside apply_history's +-16384 clamp; the gravity form keeps
  int16 entries inside +-16384. No score path touched.
- (d) 8 / 100 / 40 with ranges 0-20 / 100-150 / 0-100 are the card's own values; the source rule is stated unknown.
- (e) FIX (wording): the motivation line "the tried gate 67 HistMalusPct=125 went the other way" should say what
  the tried-gates row says: gate67_omnis_s12b_vs_h256e12, 1,500 games, -7.41 (-15.55 .. -2.54), cap with no
  decision, on another base and opponent, not the lock. Keep it as colour, not as evidence. Order and coupling
  with T04B-01 (capture tables untouched by this form) are right.

### T04E-02 NmpTtCaptureMin / NmpTtCaptureSee - FIX
- (a) Anchors hold: tt_move :913, tt_capture :918, NMP condition :965-968 (all seven terms as listed), null_tries_
  :969, null_cutoffs_ :985 / :995, reset :1241-1242, captured_piece board.hpp :164-167, color_of(Empty) = White
  :200. The claim "tt_move is not validated before :965" is true: the lock validates a TT move only inside the
  MovePicker (`is_pseudo_legal`, :325), which runs after NMP.
- (b) Both masters 0: the appended term is constant true and reads nothing. Node-identical.
- (c) Blocking a null search cannot create a score, a TT store or a draw-rule change. FIX: replace the hand-made
  plausibility test (victim != Empty, mover colour, victim colour, victim <= Queen) by the lock's own test
  `board.is_pseudo_legal(tt_move)` (as :325), evaluated after the `> 0` tests. Reason: see_ge (board.cpp :932)
  reads from / to squares and the en-passant capture square straight from the move; the lock only ever calls it on
  generated or pseudo-legal-checked moves, and a colliding TT move with a stale EnPassant flag passes the
  hand-made test but not the lock's. Same cost class, one call, only when ON.
- (d) 4 (rook or queen) and 300 cp are own values with ranges 0-5 / 0-900; the sources' thresholds are stated
  unknown. En passant = Pawn (type 1): correct.
- (e) A then B; interaction with T04N-02 / T04-03 in the same condition is handled in SPEC_SEARCH3. OK.

### T04B-01 NoisySeeHistDiv / NoisySeeHistCap - OK
- (a) Anchors hold: `history` :1058 (quiet sum / capture_history_value :714-718), guard :1061, quiet branch
  :1064-1071, else branch :1072-1084 (captures, promotions, quiet checks), capture futility :1075-1080 with history
  / 8, threshold :1081 (SeeNoisyMultiplier 150 at :35), shortcut :1082 only when the picker flag is set AND the
  threshold <= 0, see_ge :1083. The one-sided capture-slot-0 argument for non-capture promotions is right:
  piece_type(Empty) = 0 (board.hpp :199), bonus :754 needs `best.is_capture()`, every tried non-quiet move
  (:1187) gets -bonus at :759-765. CaptureHistory [13][64][7] int16 (search.hpp :255).
- (b) Divisor 0 -> no shift, lock threshold: node-identical.
- (c) Shift clamped to +-Cap; +-16384 / 96 = +-170 -> +-150. A positive threshold skips the shortcut and calls
  see_ge: as the lock already does. No score path, no TT store touched.
- (d) 96 and 150 with ranges {0,512} (tuning 16-512) and 50-400 are own values; no source formula read.
- (e) Alone first, then with T04B-02; before T04E-03's capture-history variant; T04E-04 at qsearch :838 is another
  site. OK.

### T04D-01 CutNoTtLmr - OK (one note)
- (a) Anchors hold: tt_move :913, TT store keeps an older move :293, IIR :1031, LMR :1137-1158 (cut_node +2 :1141,
  clamp :1147, reduced search :1148, re-search :1149-1153, boost :1154-1157). In a verification frame tt_move is
  the excluded move (non-none), so the term is dead there: correct.
- (b) 0 -> no term: node-identical.
- (c) Only r changes; :1147 keeps reduced_depth >= 1; re-search intact. No score, TT or draw-rule effect.
- (d) 1 with range 0-2, own.
- (e) Note (no fix needed): at depth >= 4 a cut node without a TT move already lost one ply to IIR (:1031); the new
  term stacks a second ply on each late move there. The spec's "IIR kept" should say this stacking is intended, so
  the box test "share clamped at reduced_depth 1" is read with it in mind. Order OK.

### T04D-02 TtCutNodeDepth / TtCutNodeForm - OK
- (a) Anchors hold: :875 cut_node, :876 pv_node, cutoff :921-926 with the six terms listed, IIR after it. The
  null-window claim is right: pv_node is computed at :876 from the caller's window; mate-distance pruning :896-898
  can only narrow it or return, so at :921 a non-PV node has alpha = beta - 1 and `tt_score <= alpha` equals
  `tt_score < beta`; an Exact score lies on one side too.
- (b) `TtCutNodeDepth == 0` first in the appended term: node-identical, no reordering (all terms pure).
- (c) Refusing a cutoff only re-searches a node; bounds are read, never rewritten; mate scores pass through
  unchanged; more repetition detection, not less. Form 1 / form 2 match the spec's own description.
- (d) 6 with range 0-14, form 1-2: own values; the source's limit is stated unknown.
- (e) Form 1 then form 2; joint build with T04P-01 ANDs the terms (both only remove cutoffs). OK.

## SPEC_SEARCH3

### T04C-02 SingularTtPvMargin - OK (one note)
- (a) Anchors hold: gate :1089-1090 (seven terms), singular_beta :1091 (SingularMargin 2 at :37), depth :1092,
  tt_pv save / restore :1093 / :1096 (the verification's probe rewrites :919 in the same frame), verification
  :1095, outcomes :1100-1111 as listed, tt_pv :919, IIR dead when a TT move exists.
- (b) 0 -> no term: node-identical.
- (c) Lower singular_beta: fewer +1 / +2, multicut needs tt_score >= beta + the whole margin and returns a lower
  value still >= beta, more chain entries. No TT store is changed (verification frames store nothing, :1213).
  Note: "no crossing into the mate range" holds because |tt_score| of a non-mate entry is a centipawn value far
  below MateInMaxPly - 8 x depth; the lock's own 2 x depth term rests on the same fact. Fine as written.
- (d) 32 / 16 = 2 cp per ply, range 0-96: own value.
- (e) Before T04N-01 and T04-06 in the singular queue; T04-01 changes the verification flag, not :1109. OK.

### T04F-01 QsEvasionLimit - OK
- (a) Anchors hold: in check best_score = -Infinite :804, no stand pat; legality :829, move_count :830, prune block
  :831-839 out of check only, score block :851-863 (beta break :860, alpha :861), mated :865, bound :867, store
  :868 at depth 0 with eval ValueNone in check; EvasionTT :331; generate_evasions :538-555 (:546-548 captures and
  promotions, :550 quiets with +12000 for a direct check). The two lock facts added by the spec are right: :880
  enters qsearch in check at depth <= 0 (check extension :1112 needs depth >= 2), and :1016 is a qsearch after a
  ProbCut capture.
- (b) 0 -> the first term is false, no break: node-identical.
- (c) Mate safety holds: a mated node has best_score <= -MateInMaxPly, so the break never fires before every
  evasion is searched; a winning score at a non-PV node already breaks at :860. Stalemate cannot occur in check.
  After the break best_move is none (no score > alpha), bound Upper, depth 0: the main search's cutoff (:921 needs
  tt_depth >= depth >= 1), the singular gate (:1089 excludes Upper) and ProbCut's guard (:1003) never use it; only
  qsearch re-visits (:794-798) and the eval adjustment (:938-941) do, as for the lock's own pruned upper bounds.
  Accepted as the spec says.
- (d) 1 with range 0-4, the card's own; value 2 as a second line.
- (e) Tried P27R-AL1 QsEvasionSeeNonPv=1 (+4.63 after 3,000, cap with no decision) prunes the same node class:
  gate apart, as the spec says. WAC fixed-node check before the gate: right for this class. OK.

### T04N-01 NegExtTtAlpha - OK (one note)
- (a) Anchors hold: chain :1100-1111, :1089 excludes Upper, MainTT first :333, alpha moves only at :896 and :1183,
  :1116 counts extension == 2, :1117 new_depth. Verified detail: the TT move is move 1 and the pruning guard :1061
  needs best_score > -MateInMaxPly, which is false at move 1, so the TT move always reaches the extension block
  with the entry alpha. new_depth >= 4 at depth >= 7 and extension -2.
- (b) 0 -> the appended `else if` is false, the lock's extension stands: node-identical.
- (c) Depth only; no score, TT or draw-rule effect.
- (d) 1 with range 0-2, own.
- (e) Note (design, not a fix): the spec correctly derives that at non-PV nodes the branch fires at every non-cut
  node that reaches the chain end (tt_score < beta there means tt_score <= alpha). The gate therefore tests
  "non-singular TT move at an expected all-node loses one ply", not an alpha test; the box test split PV / non-PV
  will show it. Order (alone vs the lock, then on top of T04C-02 if adopted) OK.

### T04N-02 NmpCutOnly - OK
- (a) Anchors hold: :952 block terms, :965-968, :969, :970-971, :979 `!cut_node`, :986 (depth < 14), :989-990
  verification with `false`; cut_node map :1148 true, :1151 / :1160 `!cut_node`, :1163 false, :1391 false, :1018
  `!cut_node`, :1095 inherits.
- (b) Constant-true term appended last, all terms pure: node-identical.
- (c) Fewer null searches only; RFP :960, razoring :954, ProbCut :1000 still run. No score or TT effect.
- (d) 0-1, nothing copied.
- (e) Before any T04E-02 / T04-03 combination; re-check their ON-live on top if adopted. OK.

### T04P-01 TtCutExtraMargin - OK (one note)
- (a) Port tree verified: `int TtCutExtraMargin = 0` :41, row {0,200} :89, extern search.hpp :217, condition
  :931-937 (comment :931, `if` :932, depth test :933) = the lock's :921-926 plus `+ (TtCutExtraMargin > 0 &&
  tt_score >= beta && tt_score < beta + TtCutExtraMargin)`; C1 :38 / :973-978, C2 :40 / :979, both default 0.
  Record verified: 65 options, advertised, OFF = the five lock pins + perft 5 4865609 / kiwipete 193690690, ON at
  80 = 342592 / 879873 / 2333863 / 12556911 / 39261538 = expected, smoke Threads 1 / 4 legal, ALL_OK; the bin
  exe's sha256 starts 8924099ad4c42f45. Shape at 80 vs OFF: +9.5 / +2.0 / -22.8 / +1.4 / +15.3 %: correct.
- (b) OFF proven by the record (all options 0); re-run `pin_check -Full` before the gate as the spec says.
- (c) Only removes equal-depth cutoffs for a fail high inside [beta, beta + M); an Upper entry that cuts has
  tt_score <= alpha < beta and is untouched; beta + 200 fits int; mate scores pass through.
- (d) 72 (one RfpMargin step, :23) is an own value, not the port's 80; range 24-200 for SPSA. Note: the port's
  comment :34-37 carries the source engine's name, a personal copyright line and its constants (80, 75, 28, 22):
  no effect on the exe; the spec already says strip or notice before any merge. Add: the review file and INDEX
  line should quote 72 only, never the comment.
- (e) First in the queue (no build), form A (200) only at LTC after B; joint with T04D-02 needs a one-line re-port.
  OK.

## Table
| spec | option(s) | (a) anchors | (b) OFF identical | (c) ON safety | (d) own values | (e) order | verdict |
|---|---|---|---|---|---|---|---|
| T04E-03 | QuietMalusDecay/Start/Floor | yes | yes | yes (history <= 3072) | yes | yes; gate-67 wording | OK + FIX wording |
| T04E-02 | NmpTtCaptureMin/See | yes | yes | yes; see_ge on raw TT move | yes | yes | FIX: use is_pseudo_legal |
| T04B-01 | NoisySeeHistDiv/Cap | yes | yes | yes | yes | yes | OK |
| T04D-01 | CutNoTtLmr | yes | yes | yes | yes | yes; IIR stacking note | OK |
| T04D-02 | TtCutNodeDepth/Form | yes | yes | yes | yes | yes | OK |
| T04C-02 | SingularTtPvMargin | yes | yes | yes (cp range) | yes | yes | OK |
| T04F-01 | QsEvasionLimit | yes | yes | yes (mate-safe) | yes | yes | OK |
| T04N-01 | NegExtTtAlpha | yes | yes | yes | yes | yes; all-node coverage note | OK |
| T04N-02 | NmpCutOnly | yes | yes | yes | yes | yes | OK |
| T04P-01 | TtCutExtraMargin (built) | yes (tree + record) | yes (record) | yes | yes (72) | yes | OK |
| common | row rule | - | - | - | - | - | FIX wording (secondary rows) |

Blockers: none. Fixes: three wording fixes (secondary-row rule in both notes; gate-67 line in SPEC_SEARCH2; nothing
in SPEC_SEARCH3) and one code-level fix (T04E-02: validate the TT move with `board.is_pseudo_legal` before reading
its victim or calling see_ge). Everything else checked line by line against the lock as written.
