# Dot job 9: UCI parser and worker hand-off

## 1. Step 0
PASS: unchanged r15d bb37ed7c50e1716c5fc38f1b2fb92293c18e98f6131bf2be2b13d668603b4fc6 and kF 340f78f4e4834a5bf1e6dc2d73eca3caa62b7a45d05011b5c1c092ace6e5e5ea. Each command used a fresh process, uci/isready, NO setoption and NO loaded net. Both: bench 11 =312866 nodes; bench 13 =862329 nodes; go perft 5 =4865609 nodes. Six complete raw transcripts are committed in dot/job9/{r15d,kf}_{bench_11,bench_13,go_perft_5}.raw.txt.
Builds preserved from prior jobs: GCC14.2.0, libstdc++.so.6.0.33, glibc2.41, C++20 Release O3/NDEBUG strictFP marchx86-64-v4. No rebuild or source edit in job9. Claim2026-11-18T17:13:15Z; cutoff18:03:15Z, deadline18:13:15Z. No source patch proposed.

## 2. Part A
All26 cases run in the exact supplied order in one process per build. Case input SHA256 prefix b14f885f verified by harness. Complete transcripts A_r15d.raw.txt and A_kf.raw.txt include uci/isready startup and every output to readyok for each case. Full engine-output sequences are IDENTICAL:789 lines each, including startup. Harness UTC/build labels are excluded, no output normalization used.

Important known-answer counting clarification: the job calls its second number a count of per-move lines. Each supplied number is actually per-move lines PLUS the aggregate nodes line (startpos has20 legal moves, not21). Every supplied inclusive count, node total and exact diagnostic matches r15d. This was treated as a count-label error, not an engine gate failure, and declared in the immutable prediction before running kF. The literal per-move counts are shown separately rather than silently altered.

|Case|r15d nodes|kF nodes|actual move lines each|supplied inclusive count each|other output (apart from readyok)|
|---|---:|---:|---:|---:|---|
|1|400|400|20|21|none|
|2|400|400|20|21|none|
|3|835|835|29|30|none|
|4|835|835|29|30|none|
|5|779|779|29|30|none|
|6|753|753|30|31|none|
|7|560|560|20|21|none|
|8|835|835|29|30|info string illegal move e2e4|
|9|600|600|20|21|info string illegal move xyz|
|10|600|600|20|21|info string illegal move 0000|
|11|400|400|20|21|info string illegal move E2E4|
|12|2039|2039|48|49|none|
|13|2059|2059|43|44|none|
|14|1962|1962|48|49|none|
|15|2059|2059|43|44|none|
|16|46|46|2|3|none|
|17|19|19|7|8|info string illegal move a7a8Q|
|18|15|15|3|4|none|
|19|15|15|3|4|info string invalid FEN: FEN must contain six fields|
|20|15|15|3|4|info string invalid FEN: FEN must contain six fields|
|21|1000|1000|31|32|none|
|22|1000|1000|31|32|info string invalid FEN: invalid FEN fields|
|23|1000|1000|31|32|info string invalid FEN: FEN must contain six fields|
|24|1000|1000|31|32|none|
|25|600|600|20|21|none|
|26|400|400|20|21|none|

## 3. Prediction graded
Own immutable commit a1c9760c0eb37f60de3e4fdc79c6a814aa739584, after r15d Part A and before kF Part A: zero differing cases; none expected among supplied input classes. PASS: zero differing cases. Numeric parsing, token overflow, unusual whitespace and malformed sequences were named suspects for subsequent reading/testing, not asserted bugs. The prediction has no timestamp in its content. Claim commit54f172e81fe3901bc98c9e1a400ebbf7703c81a0; r15d A commit0d7b36fd, kF A7a070ee5. Actual r15d execution precedes prediction even though raw publication follows it; raw transcripts carry execution UTC.

## 4. Part B
### Paths for all26 sequential cases
Job9 exact26-case sequential position/cache path table
Read UTC Wed Nov18 17:15:38 UTC2026 (date -u). Inputs opened /tmp/forge-dot-job9-cases.py. Reading-only: no engine executed. This table assumes all26 position commands run IN ORDER in one process with no intervening ucinewgame/position mutation; searches/display do not modify controller board/cache. Initial cache invalid. If harness resets percase, cache-path claims must be adjusted.

Source path legend (r15d versus kF src/uci.cpp):
Rroot r15d79-83: same root + vector-prefix reuse; Rreset84-100: reset startpos or validate candidate FEN and clear cache; Rmove102-111: append only legal moves, retain legalprefix on error106-107.
Kroot kF97-109: same root by startpos/FEN token fields; Kempty115-117: emptycanonical prefix reuse; Kraw118-122: raw canonicalprefix reuse with whitespace/end boundary; Ktoken124-137: tokenwise fallback; Kreset141-168: reset/validate candidate then clear cache; Kmove170-182: legalappend/error176-177.
InvalidFEN is transactional: r15d88-94/kF151-157 leave both prior board and cache unchanged on failure. Missing position argument returns r15d52/kF69. Token skipping before literal moves: r15d67-75/kF85-95.
Board move parsing: r15dsrc/board.cpp1318-1354, kF1378-1414; files a-h strictly lowercase (kF1380-1382), promotion only n/b/r/q lowercase (1388-1395), legal/pseudolegal guard1413. FEN requires six parseable fields (r15dboard212ff,kF213-223); king inventory validation kF268-271.
Abbreviations: START=standardstartposition; K=KIWI constant; P=PROMO constant; E=EP constant from cases.py. Cache root + [moves] is retained textual legal move prefix, not resulting FEN. Rows1-based matching CASES order.

01 position startpos
 r15d Rreset: initialinvalidcache, setSTART, cache startpos[]. kF Kreset same. After=START; no moves.
02 position startpos moves
 r15d Rroot reuse(emptyvector); kF Kempty reuse. Cache startpos[] unchanged. After=START.
03 position startpos moves e2e4 e7e5
 r15d Rroot reuseempty thenRmove append2; kF Kempty thenKmove append2. Cache startpos[e2e4 e7e5]; afterSTART+2plies, Whiteturn.
04 same two moves with spaces/tabs
 r15d tokens normalized, Rroot reuses2, noappend. kF rawprefix fails because incoming intermove whitespace differs; Ktoken consumes two equal tokens, tail empty, noappend. Cache unchanged2; sameboardas03.
05 add g1f3
 r15d Rroot reuses2 thenappend1. kF Kraw reusescanonical2 thenappend1. Cache startpos[e2e4 e7e5 g1f3]; Blackturn.
06 extend to e2e4 e7e5 g1f3 b8c6 f1b5 a7a6 b5a4 g8f6 e1g1
 r15d Rroot reuses3/appends6; kF Kraw reuses3/appends6. Whitecastle lastmove. Cache entire9moves; Blackturn. No rootreset.
07 position startpos moves d2d4
 r15d cachelength9>incoming1, RresetSTART thenappendd2d4. kF Kraw fails andKtoken mismatchfirsttoken, KresetSTART thenappendd2d4. Cache startpos[d2d4]; Blackturn.
08 position startpos moves e2e4 e7e5 e2e4
 r15d cachedfirstd2d4 !=e2e4 soRreset; kF Kraw/Ktoken fail soKreset. Both append e2e4,e7e5 then reject third e2e4 (e2nowempty); emit illegalmovee2e4. Cache startpos[e2e4 e7e5] ONLY; afterSTART+2plies, Whiteturn. Do not retain prior d4 or resetagain aftererror.
09 position startpos moves e2e4 xyz e7e5
 r15d firsttokenmatches butcachedseconde7e5 !=xyz, RresetSTART. kF rawfails andtokenfallback mismatchsecondtoken, KresetSTART. Both append e2e4, rejectxyz, neverapplysuffixe7e5. Cache startpos[e2e4] ONLY; Blackturn.
10 position startpos moves e2e4 0000
 r15d Rroot reuses1; kF Kraw reuses1; both reject0000. Cache startpos[e2e4] unchanged; Blackturn. No rootreset.
11 position startpos moves E2E4
 r15d prefixmismatch,RresetSTART; kF raw/tokenmismatch,KresetSTART. Both reject uppercasefiles E2E4. Cache startpos[]; afterSTART, Whiteturn. NOT the e4board retained from10.
12 position fen K
 r15d rootkind changes(startpos->fen),Rreset validatesK; kF rootkindchanges,Kreset. Cache fenK[]; boardK, Whiteturn.
13 position fen K moves e1g1
 r15d Rroot empty-prefixreuse thenappendwhitecastle; kF Kempty thenappend. Cache fenK[e1g1]; Blackturn.
14 position fen K moves e1g1 e8c8
 r15d Rroot reuseswhitecastle thenappendblackqueensidecastle; kF Kraw same. Cache fenK[e1g1 e8c8]; Whiteturn. Both castle moves are expected legal by board geometry; this row is a source-path expectation, not runtime proof.
15 position fen K moves e1g1 plus trailing spaces/CR
 r15d incominglist1<cached2 ->RresetK,reapplywhitecastle. kF rawprefix fails(shorter), Ktoken finds missingsecondtoken ->KresetK,reapplywhitecastle. Cache fenK[e1g1]; Blackturn. TrailingCR is whitespace, not movecontent.
16 position fen P moves a7a8q
 Both rootFENchanges K->P ->resetP, applyqueenpromotion. Cache fenP[a7a8q]; Blackturn.
17 position fen P moves a7a8Q
 Both sameFEN but move-text differs fromcachedlowercaseq ->resetP. Both reject uppercasepromotionQ, leaving unpromotedP. Cache fenP[]; Whiteturn. NOT queenpromotedboard retained from16.
18 position fen P moves a7a8n
 Both sameFEN and emptycachedprefixreuse; appendknightpromotion. Cache fenP[a7a8n]; Blackturn.
19 position fen 8/P7/8/8/8/8/8/k6K w - -
 Both collect4FENfields, notsamecached6fields; attemptcandidateFEN then failmissingnumericfields. Priorboard/cache retained: fenP[a7a8n], knightpromoted, Blackturn. No movesreplayed.
20 position fen 8/P7/8/8/8/8/8/k6K w - - moves a7a8r
 Both blindlycollectfirst6tokens asFEN: placement,w,-,-,moves,a7a8r. Thus literalmoves is fifthFENfield, NOT move-listdelimiter. CandidateFEN numericparsefails; no rookpromotion. Priorboard/cache retained: fenP[a7a8n], Blackturn.
21 position fen E moves d4e3
 Both newvalidFENroot E ->resetE, applyblackEPcapture d4e3 removingwhitee4pawn. Cache fenE[d4e3]; Whiteturn. Root E has Blackturn, e3EPtarget.
22 position fen 8/8/8/8/8/8/8/8 w - - 0 1
 Both newcandidateFEN structurally6fields butkingless ->invalidFEN. RetainpriorEPresult and cache fenE[d4e3], Whiteturn.
23 position fen
 r15d tokenfen thennoFENfields; kF fen_n0; bothcandidateemptyFENfails6fieldread. RetainpriorEPresult/cachefenE[d4e3], Whiteturn.
24 position
 Noargument: r15d52/kF69 return before root/cache logic. RetainpriorEPresult/cachefenE[d4e3], Whiteturn; noinvalidFENmessage fromthiscommand.
25 position fen standardSTARTFEN moves e2e4
 Both rootFENchanges E->standardSTARTFEN ->validate/resetSTART thenappende2e4. Cache fen(standardSTARTFEN)[e2e4] (rootkindfen, notstartpos); Blackturn.
26 position startpos fen K
 Both firsttokenstartpos fixesrootkindstartpos; remaining 'fen' plusKfields are skipped while looking forliteral'moves' and nonefound. Incomingmovelistempty. Rootkinddiffers from25, soresetSTART, cache startpos[]. AfterSTART, Whiteturn. K FEN is ignored, not parsed or validated.

Conclusions: all26 paths expected sameboard/cache effect across builds, with kF04 using fallbacktokenprefix instead of r15dvectorprefix. Cases08,09,10,11,17 distinguish reset-before-error from retain-legalprefix; cases19,20,22,23 preserve preceding state transactionally. Invalid positions are intentionally parser cases, not claimed python-chess-valid setups. No runtime result, bestmove, node count, or parser diagnostic exacttext was invented here.

### Input-class audit
Job9 PartB read-only parser/cache audit
UTC read: Wed Nov18 17:13:45 UTC2026 (date -u); no engine execution, prediction-independent source review only.
Sources actually opened: r15d src/uci.cpp:43-285,410-415; kF src/uci.cpp:43-368,495-498 and command dispatch references823/860.

Finding: no demonstrated semantic difference in the inspected enabled FORGE_FIX_GO_PARSE branches. The changes are token storage and position-prefix representations. Potentially distinguishing input classes below are boundary-focused tests, not asserted bugs.

Position representation:
- r15d43-48 stores canonicalized six-field FEN string + vector<string> move tokens; kF43-49 stores FEN count/six field strings + one canonical_moves string.
- r15d58-61 and kF76-80 both consume at most6 FEN tokens, even malformed/incomplete input. r15d67-75 and kF85-95 both skip arbitrary intervening tokens until literal 'moves', then parse every remaining token as a move.
- r15d79-83 reuses only exact root plus cached move-token prefix. kF97-109 compares exact per-field root and count,113-122 uses a raw canonical prefix only with whitespace/end boundary at120. If whitespace differs,124-137 token-compares entire cached prefix. Shorter incoming sequence or a changed token resets root at141ff, same as r15d84ff. An empty cached prefix is accepted by both.
- On invalid FEN, r15d88-94/kF151-157 validate a separate candidate then leave existing board/cache untouched on error. On illegal move, both keep root + legal prefix already applied: r15d102-111/kF170-182. Cache appends only after successful make_move, so repeated invalid suffix cannot be mistaken for cached success.
- r15d stringstream extracts whitespace under the stream locale; kF51-64 explicitly recognizes six ASCII whitespace bytes (space/tab/newline/CR/VT/FF). In ordinary C locale these agree. A custom imbued C++ locale with non-ASCII whitespace would not necessarily agree, but no UCI command in inspected code installs such a locale. This is a library-integration caveat, not a demonstrated executable-input defect.

Go representation:
- r15d124-126 materializes arbitrary token vector; kF195-211 keeps first32 views on stack then copies all32 into heap when token33 arrives, appending subsequent tokens and incrementing token_count. The switch condition is strictly '< stack_tokens.size()'. No token lost or duplicated is evident; input string remains live for whole synchronous parse (kF495-498,860).
- Keyword lists r15d115-119/kF186-190 match. take_integer refuses to consume another recognized keyword (r15d144-147/kF229-232), consumes malformed nonkeyword values identically. Saturating int and unsigned node logic matches (r15d149-188/kF234-273); plus/minus grammar matches (r15d132-139/kF217-224).
- Missing/malformed lone limit gives movetime0 in both r15d232-234/kF317-319. Recognized usable later limit suppresses this fallback. Opponent clock/increment semantics match. Searchmoves stops at any keyword and ignores unparseable moves identically (r15d224-229/kF309-314).
- Repeated softnodes followed by nodes leaves soft_nodes=true in BOTH (r15d187/kF272): shared behavior, not a new kF difference. Cases must not mislabel this as parsing divergence.

Proposed14 bounded focused cases (all expected equal from reading; actual outputs not predicted here as facts). Start each independent case fresh or explicitly ucinewgame. For each position command, use isready then board display if available plus go depth1/2; do not use timing-dependent limits as primary equality oracle. Literal \t/\v/\f/\r below means corresponding byte, not backslash letters. A trailing newline ends each command.
B01 Canonical cache extension: position startpos moves e2e4 e7e5; then position startpos moves e2e4 e7e5 g1f3; go depth2. Exercises kF raw prefix path119-122.
B02 Noncanonical whitespace cached-prefix fallback: first same two moves; then 'position\tstartpos\tmoves\te2e4\v e7e5\f g1f3\r'; go depth2. Exercises fallback124-137 and ASCII whitespace51-64.
B03 Shortened move list: establish e2e4 e7e5 g1f3; then position startpos moves e2e4; go depth2. Must reset, not reuse current board.
B04 Changed earlier move: establish e2e4 e7e5; then position startpos moves d2d4 d7d5; go depth2. Must reject cached prefix.
B05 Prefix-byte false match guard: establish e2e4; then position startpos moves e2e4x e7e5; go depth2. Boundary fails and root resets; first token illegal, board should remain startpos, not e4 board.
B06 Illegal suffix and continuation: position startpos moves e2e4 e7e5 INVALID; repeat identical line; then position startpos moves e2e4 e7e5 g1f3; go depth2. Both emit illegal suffix twice and retain only legal cached prefix.
B07 Root type switch and canonical FEN whitespace: position startpos moves e2e4; then position fen rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1 moves e2e4; same FEN fields with multiple spaces/tabs then e2e4 e7e5; go depth2. Root textual token equality, not full byte-string equality.
B08 Invalid/incomplete FEN retains prior board: establish position startpos moves e2e4; then position fen INVALID w - - 0 1; then position fen 8/8/8/8/8/8/8/8 w; go depth2. Compare diagnostics and retained board. No handmade valid-FEN assumption: these are intentionally invalid-parser cases.
B09 Garbage before moves and empty suffix: position startpos nonsense moves e2e4; then position startpos nonsense moves; go depth2. Both skip unknown tokens before moves then reset when incoming list shorter/empty.
B10 Exactly32 go tokens: position startpos; go followed by30 literal 'junk' tokens then 'depth 1' (32tokens aftergo). Both bounded depth1, stack boundary control.
B11 Exactly33 go tokens: position startpos; go followed by31 literal 'junk' tokens then 'depth 1' (33tokens aftergo). Numeric value crosses stack-to-heap boundary.
B12 >32 searchmoves: position startpos; go searchmoves followed by40 copies of 'e2e4' then depth 1 (43tokens aftergo). Exercises view migration while preserving legal searchmoves + stop-at-keyword. Duplicate-move behavior is shared, compare not assume deduplication.
B13 Missing value followed by valid keyword: position startpos; go depth nodes 100. take_integer must not consume nodes; bounded hard-node request dominates unusabledepth. Also append unknown token after100 only if needed to observe harmless junk; do not combine independent expectations invisibly.
B14 Signed/overflow/repeated limits with final bound: position startpos; go nodes +184467440737095516160 depth -999999999999999999999 softnodes -1 nodes +0. Unsigned saturation, int saturation/clamp, negative count0, stickysoftnodes; explicit zero makes bounded response. Compare full outputs, no asserted bug if both zero.

Scope: up to14 tests proposed, none executed. No PartA kF run. A passing sample does not establish equivalence for custom locales, all byte sequences, allocation failure, arbitrary direct C++ callers or uninspected disabled preprocessor branches.

### Actual additional cases and runs
The following Python list literal is the exact executed list of14 cases; each inner list groups consecutive command lines. SHA256 of repr(list).encode(): fcbdecafb3123ad53712509ae4ee18009a9f8e810a35f008b080d292370b1226. This is report evidence, not a standalone dataset file. The prose suggestions above were adapted to this actual sequential list, which controls any discrepancy.
Each build used a fresh process with default options, replayed ALL26 PartA cases first (complete outputs in B raw), then ran B1..B14 in order without resets except position commands shown. B1..B9 append go perft2 and isready. B10..B14 wait through bestmove before sending isready; this avoids mistaking readyok for search completion. Each case records every output through readyok. No timing limit used.

```python
[['position startpos moves e2e4 e7e5', 'position startpos moves e2e4 e7e5 g1f3'], ['position startpos moves e2e4 e7e5', 'position\tstartpos\tmoves\te2e4\x0b e7e5\x0c g1f3\r'], ['position startpos moves e2e4'], ['position startpos moves d2d4 d7d5'], ['position startpos moves e2e4', 'position startpos moves e2e4x e7e5'], ['position startpos moves e2e4 e7e5 INVALID', 'position startpos moves e2e4 e7e5 INVALID', 'position startpos moves e2e4 e7e5 g1f3'], ['position startpos moves e2e4', 'position fen rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1 moves e2e4', 'position fen rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR   w\tKQkq - 0 1 moves e2e4 e7e5'], ['position startpos moves e2e4', 'position fen INVALID w - - 0 1', 'position fen 8/8/8/8/8/8/8/8 w'], ['position startpos nonsense moves e2e4', 'position startpos nonsense moves'], ['position startpos', 'go junk junk junk junk junk junk junk junk junk junk junk junk junk junk junk junk junk junk junk junk junk junk junk junk junk junk junk junk junk junk depth 1'], ['position startpos', 'go junk junk junk junk junk junk junk junk junk junk junk junk junk junk junk junk junk junk junk junk junk junk junk junk junk junk junk junk junk junk junk depth 1'], ['position startpos', 'go searchmoves e2e4 e2e4 e2e4 e2e4 e2e4 e2e4 e2e4 e2e4 e2e4 e2e4 e2e4 e2e4 e2e4 e2e4 e2e4 e2e4 e2e4 e2e4 e2e4 e2e4 e2e4 e2e4 e2e4 e2e4 e2e4 e2e4 e2e4 e2e4 e2e4 e2e4 e2e4 e2e4 e2e4 e2e4 e2e4 e2e4 e2e4 e2e4 e2e4 e2e4 depth 1'], ['position startpos', 'go depth nodes 100'], ['position startpos', 'go nodes +184467440737095516160 depth -999999999999999999999 softnodes -1 nodes +0']]
```

Results: full B engine-output streams1050 lines each including replay and startup, EXACTLY identical. All14 case arrays identical; normalization unnecessary. The >32 paths use32,33 and43 tokens AFTER go in B10/11/12. No lost or duplicated token behavior observed.

|Bcase|nodes line or final search output|diagnostic lines|
|---|---|---|
|1|nodes 779|none|
|2|nodes 779|none|
|3|nodes 600|none|
|4|nodes 728|none|
|5|nodes 400|info string illegal move e2e4x|
|6|nodes 779|info string illegal move INVALID / info string illegal move INVALID|
|7|nodes 835|none|
|8|nodes 600|info string invalid FEN: invalid FEN placement / info string invalid FEN: FEN must contain six fields|
|9|nodes 400|none|
|10|info depth 1 seldepth 1 score cp 1 nodes 26 nps 0 hashfull 0 time 0 pv d2d4 / bestmove d2d4|none|
|11|info depth 1 seldepth 1 score cp 1 nodes 21 nps 0 hashfull 0 time 0 pv d2d4 / bestmove d2d4|none|
|12|info depth 1 seldepth 1 score cp -11 nodes 2 nps 0 hashfull 0 time 0 pv e2e4 / bestmove e2e4|none|
|13|info depth 1 seldepth 1 score cp 1 nodes 21 nps 0 hashfull 0 time 0 pv d2d4 / info depth 2 seldepth 2 score cp 49 nodes 49 nps 0 hashfull 0 time 0 pv d2d4 d7d6 / bestmove d2d4|none|
|14|bestmove a2a3|none|

## 5. Part C: shared objects and ordering
2026-11-18T17:15:24Z
Part C: read-only UCI worker/task synchronization audit, r15d versus kF.
All short references below are src/uci.cpp unless otherwise named; R=r15d, K=kF. No execution, edits to source, or remote writes. No changed-path data race or stale-task field found under serialized uci_loop use. This is a source argument, not a stress-test result or a proof for arbitrary concurrent public C++ clients.

1. Actual change and required ownership invariant
R335-346 creates SearchTask task inside every loop iteration, then under stop_mutex executes `task = std::move(pending_task);`, then calls searcher.search(std::move(task.board), task.limits,...).
K418-431 creates SearchTask task once outside the loop. Under the same mutex it assigns all three declared fields: `task.board = pending_task.board;` (425), `task.limits = std::move(pending_task.limits);` (426), `task.ponder_enabled = pending_task.ponder_enabled;` (427), then clears has_task. SearchTask has exactly Board, SearchLimits, bool (K402-406; R319-323), so no stale field survives a later task. K431 passes task.board by copy to Searcher::search, whose signature takes Board by value (K search.hpp758 and search.cpp3794; R search.cpp3289). K therefore retains pending/task Board allocations instead of moving them away; retention is not shared storage.
Board's owned members are arrays/scalars plus std::vector<uint64_t> key_history_ (K board.hpp280-298), with no borrowed pointer to input text or another Board. Default copy assignment deep-copies history; mutable KingLines is copied by value, too. Searcher's by-value Board, helper-by-value captures, and main thread Board are distinct. Board history/counters/cached legality metadata travel together, preserving repetition state. SearchLimits has owning move vectors, not parser string_views. Task reused limits are overwritten by move assignment before every search; moved-from pending limits are not read by worker again before main assigns a fresh limits object. This assumes no new SearchTask field is later added without updating the explicit three-field copy.

2. Shared task and queue-state inventory (all non-atomic fields protected by stop_mutex)
- pending_task (R333, K416): main writes Board/limits/ponder bool at R812-814/K893-895 inside lock R809/K890; worker reads/copies/moves R342/K425-427 under R339/K422. Previous worker cannot retain a reference into pending_task because Board is deep copied and SearchLimits move transfers ownership. Next main write happens only after stop_search has observed worker_busy false.
- has_task (R330/K413): main sets true R815/K896 under mutex; worker work_cv predicate reads R340/K423; worker clears false R343/K428 under mutex. No task coalescing/overwrite: each go begins stop_search (R740/K825), which waits for prior busy task. Busy is set before enqueue lock releases, even if worker has not awakened yet.
- worker_busy (R331/K414): main sets true R816/K897 under lock; stop_search reads R377,387/K462,472 under lock; worker clears false R368/K453 only AFTER search return, deferred wait, and bestmove output. done_cv notification R370/K455 follows the unlock. Thus stop_search returning means no worker use of old task/search configuration remains, not just that a stop flag was sent.
- stop_requested (R328/K411): initialized before thread starts; reset false at R810/K891 with new-task mutex; set true by stop_search R381/K466 under mutex; read in deferred infinite/ponder predicate R350/K435 while holding same mutex. Non-atomic is sufficient here.
- ponder_hit_received (R329/K412): initialized before start/reset false R811/K892; set true in ponderhit R885/K969 under R884/K968 lock; read by deferred predicate R350/K435 under lock. No lost wake: predicate is stateful and reads already-true flag even if notification preceded waiting.
- worker_quit (R332/K415): read under work mutex R340-341/K423-424; written true by shutdown guard R401-402/K486-487 under that mutex. Guard first invokes stop_search, then sets quit, notifies work_cv, joins R405/K490. Shared state outlives the join because guard destroys before earlier-declared state.
- stop_mutex R324/K407 serializes all above publications and completion. Unlock/lock provides happens-before for payload and non-atomic flags; CV notify alone is not the payload synchronization.
- work_cv R326/K409 waits predicate has_task||worker_quit, main notifies R818/K899 and guard notifies R404/K489; notify may precede wait without losing task because predicate remains true.
- stop_cv R325/K408 waits stop_requested||(task.limits.ponder&&ponder_hit_received) R347-351/K432-436. stop_search notifies R384/K469; ponderhit R887/K971. Wait releases stop_mutex while asleep, so producer can set predicate.
- done_cv R327/K410 wait predicate !worker_busy R387/K472; worker notifies after publication R370/K455. Spurious wakeups harmless through predicate.
- worker std::thread object R335/K418 is main-owned except execution represented by the thread; only guard joins. Worker lambda captures surrounding state by reference but only uses searcher/queue/CVs/output as above. task, result and output prediction are worker-local. Retaining task across iterations does not make it main-shared.

3. Shared Searcher and global engine configuration
searcher R302/K385 is invoked from worker R345-346/K430-431. Main may call stop(), reset_stop(), ponderhit() concurrently only through designed atomic paths:
K search.hpp760 stop stores shared_.stop true relaxed; reset_stop761-764 stores stop false and ponder_hit_ns0; ponderhit765-769 uses compare_exchange_strong on the atomic timestamp (default sequential consistency). R637-646 same behavior. Fields are atomic at K search.hpp545,547 / R463,465. Worker reads relaxed atomic flags/time at K search.cpp2009,2028,2044,2048,2069 (R1519,1538,1554,1558,1579). These flags carry only their own state/time, not task payload; queue mutex carries the payload ordering.
reset_stop occurs R807/K888 only AFTER prior stop_search at go entry and BEFORE task publication. Searcher::search does not reset away a newly requested stop at entry (K3794-3817/R3289-3312 inspected). Thus immediate go->stop before worker pickup still leaves stop_requested and atomic stop set for that admitted task.
Non-atomic Searcher mutation (clear, clear_hash, resize_hash, set_threads) and tunable/net/global-eval changes happen after the common setoption stop_search gate R499/K583. ucinewgame gate R491/K575 precedes clear and Board reset. Bench gate R842/K923 precedes separate bench Searcher. Position gate R737/K822 and go gate R740/K825 likewise quiesce. Threads helper joins occur inside Searcher::search before return: K search.cpp3860/R3353, so busy=false also covers helper completion. Main doesn't resize histories/TT/net while helpers are active.
Globals nnue::enabled/requested/loaded-net state and tune::* are shared reads during search, but only main UCI thread mutates them after stop_search; the next enqueue mutex orders new values before worker begins. uci/isready/eval may read configuration while a search runs, but do not replace it. eval uses main-owned Board and fresh/local evaluator/reference state (K901-918); it doesn't touch Worker search caches. This last statement is confined to the visible eval dispatch, not an audit of all future library implementation changes.

4. Main-only state, output and command ownership
Main Board (R301/K384), PositionCache (R315/K398), current input line/parser views (R409 onward/K494 onward), book/book_rng/book settings, move_overhead_ms, multipv, ponder_enabled and ponder_search_active (R303-318/K386-400) are main-thread owned. Worker does not access them directly: each relevant field enters SearchTask/SearchLimits by value. In particular ponder_search_active is not a data race despite lacking mutex: only main writes/reads it in go, stop_search and ponderhit. Worker instead reads task.limits.ponder/task.ponder_enabled and protected ponder_hit_received.
std::cout is shared: worker bestmove output holds uci_output_mutex R363/K448; command-thread outputs such as readyok hold it R489/K573; search info output holds it (K search.cpp3222). uci_output.hpp7-10 defines one function-local static mutex. Stop mutex is NOT held during bestmove output, then separately acquired to clear busy, so output-lock and stop-lock are not held in the inverse nested order there. stop_search releases stop_mutex before searcher.stop and before CV notification, then waits with CV releasing it. No deadlock cycle found in this worker lifecycle.
Output locking guarantees complete lines/groups, not a fixed order between concurrent info and readyok. isready K557-573/R473-489 normally does not stop or wait for the active search; readyok is not a completion barrier. Tests must not infer bestmove completed merely from readyok. Invalid-v3 readiness error is the explicit stopping exception K566-570/R482-486.

5. Modes and guarantees, and limits
- Back-to-back go, position, setoption, hash resize, Threads changes and ucinewgame: previous task quiesces before main reuses pending_task or mutates configuration. Queue depth effectively one, not an unbounded asynchronous queue.
- infinite/ponder whose search reaches its depth limit remains worker_busy and waits for stop/ponderhit, so next go's stop_search releases it before overwrite. Ponderhit uses both searcher atomic timestamp and the protected completion flag, covering either still-searching or already-waiting worker states.
- EOF/quit: explicit stop_search and destructor guard's idempotent extra stop ensure join before state destruction.
- Long position strings: parser views never cross dispatch into worker; Board owns history and task limits own Moves. Changing copy/move policy preserves content, including long repetition history, but does not promise success under allocation failure.
- MultiPV and Threads>1 do not change UCI handoff: their nested workers finish before outer search return; each Board/Worker-local state remains distinct. Shared TT synchronization is its own subsystem, not established solely by this UCI mutex audit.
- Unexpected exceptions in the worker, failing allocation, concurrent independent callers invoking Searcher mutators directly, or multiple uci_loop instances sharing process globals are not covered. No new handling for them was added by persistent SearchTask/copyBoard. No dynamic race detector or TSAN was run in this read-only assignment.

Conclusion: the persistent-task and copyBoard change relies on complete three-field reassignment, deep owning Board/limits values, one admitted task at a time, and stop_search's completion barrier. Each is visible at cited lines in both versions; no changed-path race or stale value identified. A stress test should assess liveness/one-bestmove-per-go and legal outputs, not impose equal timing-dependent nodes across infinite/stop scheduling.

## Facts, suspicions and limits
Facts: all requested gates passed under the explicit inclusive-count interpretation; all26 A and14 B outputs matched exactly; source audit found no changed-path divergence or race under described UCI assumptions. Native workload was finished before17:17:34Z, comfortably before cutoff. All ten raw transcripts individually created and full-body read back successfully, no bulk tree write. Every numerical runtime claim above comes from these raw transcripts. Report/source tables are reading evidence, not dynamic instrumentation of cache paths.
Suspicions: custom stream locales could change whitespace classification outside current executable setup; additions to SearchTask require all fields to be copied; global process state or allocation failures remain outside this audit. Shared softnodes-sticky behavior is not a kF regression. None establishes a bug. No repair patch is justified by these results.
What I did not do: no sanitizer/race-detector runs, no strength/speed claims, no additional positions dataset publication, no other branch/source changes, no tests of arbitrary command scheduling. No shadow NNUE, PC20, loaded syntheticnet, or multithread-option changes in this job. The generated harness scripts remain outside repository.
What I am not sure about: equivalence across all byte strings, custom locales, memory exhaustion, direct concurrent library clients, or other compiler/PC environments. Exact model identity is not exposed and is not guessed.

### What this check cannot see (verbatim)
Command orders other than these (each case runs after the case before it); commands other than position and go;
the PC's build; more than one search thread (sol3's job 22 runs that).

## FOR FABLE AND OPUS
Please confirm the PartA second-count label should read perft output lines including nodes, not per-move lines. All supplied numeric/error answers match under that interpretation. No kF/r15d parser discrepancy found; no changed worker-state ownership defect identified. Job7/8 count correction acknowledged:1000 W1 entries represent990 distinct positions; S2 starts1 and14 duplicate. Job9 PartA intentionally contains repeated/equivalent state commands rather than a unique-position sample.
After verified report, poll FABLE_TO_dot_10.md every2minutes for30minutes. CLI fetch review timeout in prior boundary did not establish absence; connector reads were used and found Job9. Use fresh success/404 at final boundary, never a stale FETCH_HEAD.

Auxiliary workflow note: investigate-chess-bugs skill was read; its scripts/audit_finding.py resource returned 'failed to read skill resource'. The auxiliary record auditor was NOT run. Local checkpoint records this limitation; native assertions and remote full-body comparisons are separate and completed.

## Last shell command before report commit
`git status --short; ls -R forge-combo29/dot/job9`
Local checkout deliberately preserves untracked prior evidence; connector commits are not reflected by these local index entries. Only ten raw transcripts plus claim/prediction/checkpoint and this report are asserted remote, not all listed local files.
```
 M forge-combo29/dot/job2/stamps.txt
?? forge-combo29/REPORT_dot_job6.md
?? forge-combo29/REPORT_dot_job7.md
?? forge-combo29/REPORT_dot_job8.md
?? forge-combo29/REPORT_dot_job9.md
?? forge-combo29/dot/job2/K1_base_count_search_extract.txt
?? forge-combo29/dot/job2/K1_base_diagnostic_gate.raw.txt
?? forge-combo29/dot/job2/K1_base_plain_search_extract.txt
?? forge-combo29/dot/job2/K1_matrix.py.txt
?? forge-combo29/dot/job2/K1_matrix_console.txt
?? forge-combo29/dot/job2/K1_pc_count_search_extract.txt
?? forge-combo29/dot/job2/K1_pc_diagnostic_gate.raw.txt
?? forge-combo29/dot/job2/K1_pc_plain_search_extract.txt
?? forge-combo29/dot/job2/K1_summary.json.txt
?? forge-combo29/dot/job2/K2_analysis.txt
?? forge-combo29/dot/job2/K2_base_raw.txt
?? forge-combo29/dot/job2/K2_base_search_extract.txt
?? forge-combo29/dot/job2/K2_cap.py.txt
?? forge-combo29/dot/job2/K2_console.txt
?? forge-combo29/dot/job2/K2_fault_replay.py.txt
?? forge-combo29/dot/job2/K2_fault_result.txt
?? forge-combo29/dot/job2/K2_pc_raw.txt
?? forge-combo29/dot/job2/K2_pc_search_extract.txt
?? forge-combo29/dot/job2/K2_replay_count.raw.txt
?? forge-combo29/dot/job2/K2_replay_fault.raw.txt
?? forge-combo29/dot/job2/K2_replay_plain.raw.txt
?? forge-combo29/dot/job2/K2_summary.json.txt
?? forge-combo29/dot/job2/base_count_go_nodes_250000_fen0.raw.txt
?? forge-combo29/dot/job2/base_count_go_nodes_250000_fen1.raw.txt
?? forge-combo29/dot/job2/base_count_go_nodes_250000_fen2.raw.txt
?? forge-combo29/dot/job2/base_count_go_nodes_250000_fen3.raw.txt
?? forge-combo29/dot/job2/base_count_go_nodes_250000_fen4.raw.txt
?? forge-combo29/dot/job2/base_count_go_nodes_250000_fen5.raw.txt
?? forge-combo29/dot/job2/base_count_go_nodes_250000_fen6.raw.txt
?? forge-combo29/dot/job2/base_count_go_nodes_250000_fen7.raw.txt
?? forge-combo29/dot/job2/base_count_go_nodes_50000_fen0.raw.txt
?? forge-combo29/dot/job2/base_count_go_nodes_50000_fen1.raw.txt
?? forge-combo29/dot/job2/base_count_go_nodes_50000_fen2.raw.txt
?? forge-combo29/dot/job2/base_count_go_nodes_50000_fen3.raw.txt
?? forge-combo29/dot/job2/base_count_go_nodes_50000_fen4.raw.txt
?? forge-combo29/dot/job2/base_count_go_nodes_50000_fen5.raw.txt
?? forge-combo29/dot/job2/base_count_go_nodes_50000_fen6.raw.txt
?? forge-combo29/dot/job2/base_count_go_nodes_50000_fen7.raw.txt
?? forge-combo29/dot/job2/base_count_go_softnodes_2000_fen0.raw.txt
?? forge-combo29/dot/job2/base_count_go_softnodes_2000_fen1.raw.txt
?? forge-combo29/dot/job2/base_count_go_softnodes_2000_fen2.raw.txt
?? forge-combo29/dot/job2/base_count_go_softnodes_2000_fen3.raw.txt
?? forge-combo29/dot/job2/base_count_go_softnodes_2000_fen4.raw.txt
?? forge-combo29/dot/job2/base_count_go_softnodes_2000_fen5.raw.txt
?? forge-combo29/dot/job2/base_count_go_softnodes_2000_fen6.raw.txt
?? forge-combo29/dot/job2/base_count_go_softnodes_2000_fen7.raw.txt
?? forge-combo29/dot/job2/base_count_only.patch.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_250000_fen0.raw.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_250000_fen1.raw.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_250000_fen2.raw.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_250000_fen3.raw.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_250000_fen4.raw.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_250000_fen5.raw.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_250000_fen6.raw.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_250000_fen7.raw.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_50000_fen0.raw.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_50000_fen1.raw.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_50000_fen2.raw.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_50000_fen3.raw.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_50000_fen4.raw.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_50000_fen5.raw.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_50000_fen6.raw.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_50000_fen7.raw.txt
?? forge-combo29/dot/job2/base_plain_go_softnodes_2000_fen0.raw.txt
?? forge-combo29/dot/job2/base_plain_go_softnodes_2000_fen1.raw.txt
?? forge-combo29/dot/job2/base_plain_go_softnodes_2000_fen2.raw.txt
?? forge-combo29/dot/job2/base_plain_go_softnodes_2000_fen3.raw.txt
?? forge-combo29/dot/job2/base_plain_go_softnodes_2000_fen4.raw.txt
?? forge-combo29/dot/job2/base_plain_go_softnodes_2000_fen5.raw.txt
?? forge-combo29/dot/job2/base_plain_go_softnodes_2000_fen6.raw.txt
?? forge-combo29/dot/job2/base_plain_go_softnodes_2000_fen7.raw.txt
?? forge-combo29/dot/job2/manifest.sha256.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_250000_fen0.raw.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_250000_fen1.raw.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_250000_fen2.raw.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_250000_fen3.raw.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_250000_fen4.raw.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_250000_fen5.raw.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_250000_fen6.raw.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_250000_fen7.raw.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_50000_fen0.raw.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_50000_fen1.raw.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_50000_fen2.raw.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_50000_fen3.raw.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_50000_fen4.raw.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_50000_fen5.raw.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_50000_fen6.raw.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_50000_fen7.raw.txt
?? forge-combo29/dot/job2/pc_count_go_softnodes_2000_fen0.raw.txt
?? forge-combo29/dot/job2/pc_count_go_softnodes_2000_fen1.raw.txt
?? forge-combo29/dot/job2/pc_count_go_softnodes_2000_fen2.raw.txt
?? forge-combo29/dot/job2/pc_count_go_softnodes_2000_fen3.raw.txt
?? forge-combo29/dot/job2/pc_count_go_softnodes_2000_fen4.raw.txt
?? forge-combo29/dot/job2/pc_count_go_softnodes_2000_fen5.raw.txt
?? forge-combo29/dot/job2/pc_count_go_softnodes_2000_fen6.raw.txt
?? forge-combo29/dot/job2/pc_count_go_softnodes_2000_fen7.raw.txt
?? forge-combo29/dot/job2/pc_count_only.patch.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_250000_fen0.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_250000_fen1.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_250000_fen2.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_250000_fen3.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_250000_fen4.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_250000_fen5.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_250000_fen6.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_250000_fen7.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_50000_fen0.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_50000_fen1.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_50000_fen2.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_50000_fen3.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_50000_fen4.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_50000_fen5.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_50000_fen6.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_50000_fen7.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_softnodes_2000_fen0.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_softnodes_2000_fen1.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_softnodes_2000_fen2.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_softnodes_2000_fen3.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_softnodes_2000_fen4.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_softnodes_2000_fen5.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_softnodes_2000_fen6.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_softnodes_2000_fen7.raw.txt
?? forge-combo29/dot/job2/pc_planted_overrun.patch.txt
?? forge-combo29/dot/job3/
?? forge-combo29/dot/job4/
?? forge-combo29/dot/job5/
?? forge-combo29/dot/job6/
?? forge-combo29/dot/job7/
?? forge-combo29/dot/job8/
?? forge-combo29/dot/job9/
forge-combo29/dot/job9:
A_comparison.txt
A_kf.raw.txt
A_kf_summary.txt
A_r15d.raw.txt
A_r15d_summary.txt
B_comparison.txt
B_kf.raw.txt
B_kf_summary.txt
B_r15d.raw.txt
B_r15d_summary.txt
gate_summary.txt
kf_bench_11.raw.txt
kf_bench_13.raw.txt
kf_go_perft_5.raw.txt
local_finding_record.json.txt
r15d_bench_11.raw.txt
r15d_bench_13.raw.txt
r15d_go_perft_5.raw.txt
```
