# Dot job 10: board and move-picker shortcut audit

## 1. Step 0
PASS on unchanged original binaries, fresh process for each command, no setoption/no loaded net. r15d SHA256 bb37ed7c50e1716c5fc38f1b2fb92293c18e98f6131bf2be2b13d668603b4fc6; kF 340f78f4e4834a5bf1e6dc2d73eca3caa62b7a45d05011b5c1c092ace6e5e5ea. Both give bench11=312866 nodes, bench13=862329 nodes, go perft5=4865609 nodes. Six full raw transcripts named {r15d,kf}_{bench_11,bench_13,go_perft_5}.raw.txt.
Actual claim2026-11-18T17:31:36Z (date-u). First claim file mistakenly rounded to17:32:00; immediately corrected in a9d07bc4870078c1af61eec21e02a9de655aad16. The real native cutoff is18:21:36, deadline18:31:36; no extra time taken from typo. Native work finished17:36:56.109940Z.

## 2. Part A, both unchanged builds
One process per build, uci/isready then all6 position/perft/isready cases in order. A_r15d.raw.txt and A_kf.raw.txt preserve every output and exact position inputs. All supplied totals PASS.
|Case|Position identifier|Depth|r15d nodes|kF nodes|
|---|---|---:|---:|---:|
|1|startpos|5|4865609|4865609|
|2|Kiwipete supplied FEN|4|4085603|4085603|
|3|KP5r /1R3p1k endgame supplied FEN|5|674624|674624|
|4|r3k2r/Pppp1ppp tactical supplied FEN|4|422333|422333|
|5|rnbq1k1r/pp1Pbppp promotion supplied FEN|4|2103487|2103487|
|6|r4rk1/1pp1qppp middlegame supplied FEN|4|3894594|3894594|
Perft calls the default make_move path, not precomputed-key/known-check shortcuts. It exercises board move generation and ordinary make/unmake/king-line restoration, not dynamic coverage of all picker optimizations.

## 3. Part B: shortcut conditions, source locations and input classes
Paths below are src/search.cpp, src/board.cpp or include/forge/board.hpp in the unchanged kF and r15d trees, NOT shifted instrumented-line numbers. Source readers opened the cited files. Full line-level evidence is PartB_reading.txt.

|Shortcut|Equality condition and source|Potential distinguishing classes / coverage|
|---|---|---|
|B1 quiet gives-check|kF search905-910 uses direct check-squares plus discovered-line departure, castle falls back to Board; Board header346-356; r15d search2233/header338-348. Current copies and legal parent required.|Direct/discovered/both, king leaving line, aligned move, rook check from castle. Quiet list excludes captures/EP/promotions; malformed opposite-king-in-check parents outside proof. Board reference shares KingLines helpers.|
|B2 quiet legality|kF search894-903: king Board::is_legal, otherwise unpinned or pin-aligned. Board header334-343 and board901-929; r15d header326-335/board892-920. Quiet stage only Main/not-in-check, not skipped.|King/castle safety, pinned off/on-line, unpinned. Evasions, EP/captures/promotions must not enter quiet stage. Count includes accepted/rejected candidates after duplicate and quiet-tail filters.|
|B3 cached result lifetime|kF search886-914 only QuietMoves return assigns cached answer before914; other stages change stage first; getters960-961, consumer2725 immediately after next2714/legality2720.|Skipped/excluded/restricted-root candidates, TT/killer/counter/BadCaptures/Evasions/Qs. No stale return found; reading after another next or permanent board mutation violates lifetime. r15d computes Board answer at2233.|
|B4 copied king lines|kF search1027-1036 copies ensured fields/kings; quiet init1348/1533/1547. r15d871-883 derives check squares. Parent board restored after recursion (kF make2882/2886, unmake2947).|Board DOES change during child search; equality relies on restoration, not immutability. Singular/probcut subsearch also restores. Stale picker reused on permanently changed board outside contract.|
|B5 known no-check|kF board1283-1295 skips full checker calculation on0; r15d1231-1238 always computes. qsearch2341->2362/2366 and main2725->2882/2886 supply boolean answer for same board/move.|All special/check/discovered/king moves, stale answer or wrong cached move. Every known0 dynamically compared against const compute_checkers after move.|
|B6 supplied child key|kF key_after1141-1164; board1191ff/1253ff versus r15d1120ff/1176-1227. Only qsearch2352->2362 and main2870->2882 pass nonnull when key_after succeeds.|Castling rook/rights/promotion/capture terms; oldEP or EPmove refused; adjacent-enemy-pawn double push refused. Independent incremental dbg_key arithmetic compared at every nonnull use. Not full-board hash reconstruction.|
|B7 conditional Undo king lines|kF board1182-1183,1346-1347 save only valid;1334-1335,1373-1374 restore valid or mark invalid; r15d1173/1288/1277/1314 copy whole cache.|Requires every reader to refresh/guard valid; inspected readers do. Make/unmake/null, castles/EP/promotions invalidate. Invalid payload bytes need not match. Source/perft evidence only, no new B7 counter.|
|B8 SEE early exits|kF board1530 and1554 return true only when no opponent first recapture candidate; r15d1458-1475 full attacker initialization would find none. Superset geometric-ray test then occupied-ray test.|EP origin/capture removal, x-rays, pinned attackers, king recapture, promotion delegate, thresholds. HOIST1 means alternate pawn-cheap-refutation branch1540-1548 is not compiled. Optional B8 reference counter NOT implemented, source reading only.|

### Detailed source evidence
Job10 PartB1-B4, read-only source audit, UTC 2026-11-18T17:34Z.
Paths K=/tmp/forge-dot-kf-src, R=/tmp/forge-dot-r15d-src. Line numbers refer unchanged source, NOT instrumented copies.
B1: K search.cpp905-910 direct_chk = check_squares_[pt]&destination, OR castle full Board::gives_check, otherwise discoverers origin and !aligned(enemyking,origin,destination). K board.hpp346-356 uses exactly these normal-move predicates, routing castle/EP/promotion to full routine. R search.cpp2233 uses Board::gives_check for each surviving move; R board.hpp338-348 has same KingLines fast/full split, R board.cpp1019+ full routine. K board.cpp1032-1040 states legal-position precondition: origin cannot already be checking opposite king. Agreement requires legal reachable parent, pseudo-legal quiet excluding promotions/captures/EP, current king-line copies and king squares. Classes: normal direct check; normal discovered check; both; king vacating discovered line; aligned blocker preserving line; castle rook check (full fallback; direct king table zero). Pseudo-illegal externally constructed moves, stale cached parent, malformed FEN with opposite king already checked are outside proof. Promotion/EP cannot enter quiet list and need full treatment if that invariant changes. K1346-1359 specialized/fallback quiet generation; other compile branches1533-1564 exclude captures/promotions. This is source proof with Board reference, not independent occupancy-only oracle.
B2: K search.cpp894-903 king origin calls Board::is_legal; nonking accepts unless pinned and not aligned. K board.hpp334-343 same pin predicate conditioned checkers0, nonEP, nonking. K board.cpp901-929 full king/castle occupancy test; R board.hpp326-335 and board.cpp892-920 same Board API. R search.cpp2228 checks Board legality after picker. K picker constructor817-828 selects Main for not-in-check, Evasions for in-check, Qs for non-check qsearch. Quiet stage reached Main->captures->killers/counter->GenerateQuiets883-886, only !skip_quiets, after dedup892 and closed-tailcheck893. Thus pinned nonking off-line rejects; aligned accepts; unpinned accepts; king validates destination occupancy; castle is king and invokes full legal API, with generation requiring no check through squares (K1500-1527). Checked parents, EP, captures/promotions must not enter this stage. Quiet stage gets no candidates if skip_quiets. B2 counter observes both accepted and rejected candidates AFTER duplicate/tail filtering, so not every generated quiet move.
B3: K search.cpp886-914 is the sole return move with stage==QuietMoves. It sets last_quiet_gives_check_ before return914 for every accepted move; skips cannot return. Exhaustion switches stage BadCaptures918, so returns there cannot expose cache. Killer1/2/counter change stage before returning (869-879); counter leaves GenerateQuiets, not QuietMoves. TT return advances MainTT->GenerateCaptures etc (840-846), never QuietMoves. Qs/Evasion use separate stages931-948. Cached getters960-961 are valid until next next(); sole consumer search.cpp2725 reads immediately following next2714 and legality2720, before make2882/2886. Excluded/rootrestricted filters may skip current returned move without reading cache; next call overwrites before next eligible return. A caller reading after another next() or after a board mutation violates documented lifetime958.
B4: K search.cpp1027-1036 init copies ensure_king_lines().check_squares,pinned,discoverers and both kings. Invoked quiet generation1348/1533/1547 and evasion1593 (other capture-related invocation does not make QuietMoves stale). R search.cpp871-883 directly derives check_squares from enemy king and occupied. Board can and DOES change during recursive child searches between picker returns: K make2882/2886, child search, unconditional unmake2947 before abort exit2948 or next loop2714. Earlier singular/probcut child operations unmake before continuation (2653-2661). Therefore the correct claim is parent restoration, not 'board never changes'. Each Worker owns its board/search; no concurrent UCI mutation of task board. Quiet caches are value copies, no reference into shared picker scratch. After child unmake same logical parent position, side and king squares return; if abort returns from worker, picker dies. Mutable king-line cache can be invalidated/recomputed but copied logical values remain for same parent. Nonstandard reuse of picker with permanently mutated board would violate invariant.
Instrumentation caveat: both r15d and kF Board APIs already use KingLines when enabled. C-count observes the requested Board::is_legal/gives_check answers, validating picker against Board API, not independently validating King's line derivation for normal moves. B5 compute_checkers and B6 full incremental shadow supply separate board-level checks. All counters diagnostic-only; reset per Searcher::search, first5 disagreement diagnostics across process, summary under output mutex before bestmove. C-wrong B1 reference direct_chk only omits discovered and castle-rook contributions; production last_quiet_gives_check untouched.
Job10 B5-B8 audit and B5/B6 counter design
Source audit completion date -u: Wed Nov 18 17:34:56 UTC 2026. Original reference trees kF/r15d; no original source modified. Counter edits only scratch board.cpp.

B5 | known_gives_check==0 skips checker reconstruction.
Condition for equality: same legal move and unchanged pre-move board used by caller's gives-check calculation; a false result must mean no mover attacks enemyking after move including discovered lines, EP removal, promotion and castling rook movement. kF board.cpp1283-1295 assigns0 ifknown0, else computes mover attacks. r15d board.cpp1231-1238 always computes mover attacks. Full reference compute_checkers kF439-442 calls attackers_to(current sideking,occupied)&opponentoccupied, algebraically same r15d computation after side_ switched to them. It is const and does not write cachedkinglines.
Every nondefault caller: qsearch search.cpp2336-2348 firstlegal-filters; known starts-1 at2339, only becomes0/1 after board.gives_check2341 when mate_moves==0 && !in_check && best_score>-MateInMaxPly. If futility/SEE prunes there is no make; otherwise2362/2366 forwards. Main search2720legalfilters;2725 uses picker cachedanswer when available else Board::gives_check;2880 convertsbool to0/1;2882/2886 forwards. Main includes root/nonroot and restrictedroot paths. If a singular subsearch runs beforemake, it must restore board before this precomputedanswer is used; pairing make/unmake is the contract (B4 audit).
Other actualsrc callers use defaultunknown=-1: search2653 ProbCut; uci180position,852perftroot,877bookreply; board1444recursiveperft. No known0 used by these. r15d qsearch1870/main2388/ProbCut2161 all ordinarymake.
Input classes requiring care: directchecks, discoveredchecks from pinned/discovererorigin, kingmoves, castles, promotions, EP exposingrank/diagonal, in-check evasions, TT/killer/counter/quiet andbadcapture stages, excluded/restrictedroot moves. The fast0 claim can fail if cachedanswer belongs to another move or staleboard, or if a specialmove calculation is wrong; raw malformed externalMove/directAPI callers are not guaranteed.
Counter: at everyknown0branch compute_checkers()!=0 before existing0assignment and recordB5; no checkerfield/referenceanswer is used bysearch. Firstdifference diagnosticFEN is POST-MOVE, paired with incomingmove; not pretended to be pre-moveFEN.

B6 | supplied child key avoids ordinary incremental hash updates.
Condition: pointer refers to correct key_after result for precisely this parent+move, and board does not change between key_after andmake. kF key_after board1141-1164 and r15d1132-1155 implement same closed-form piece/capture/promotion/castle/rights/side XOR. kF1144 refuses ANY existingEPtarget or EPmove.1146-1148 refuses doublepush adjacent to enemypawn (conservative evenifpawnpinned); these paths use ordinarymake incrementally. Castling is NOT refused: rookfrom/to XOR1154-1159; promotiondestination type1153. Legalordinarycapture XOR includes capturedpiece1152. Nonadjacentdoublepush allowed because newEPcannot be legallycaptured and noEPfilehash belongs inkey.
Every nonnull caller is kFsearch2352->2362 qsearch and2870->2882main; pointerpassed only ifkey_after returns true. Stackchild_key remains live through synchronousmake. WhenFORGE_SPD_PREFETCH_EARLY disabled2366/2886 passnullptr. ProbCut/UCIposition/perft/book passdefaults, so noB6 shortcut. r15dsearch1861/2378 computes keyonlyforprefetch then1870/2388make computes fullkey independently.
kFboard1191ff/1253ff debugger already independently accumulates oldEP removal, capturesinclEP, moverorigin,destinationinclpromotion, castlerook, old/newrights, side,newlegalEP. Runtime fastbranch1253-1267 assigns*precomputed_key instead. r15dboard1176-1227 always does those incremental terms.
Counter: compile the existing local dbg_key computation in counterRelease under !NDEBUG || FORGE_SHORTCUT_COUNT; at everynonnullbranch compare assignedkey_ != dbg_key afternewEP term. No keyfield overwrittenbyreference; existingassertstillcompiledawayunderNDEBUG. This reuses debug shadow arithmetic, not key_after, and covers everyB6use. There is no independent fullboard Zobrist reconstruction in this counter. Inputclasses: castlesbothsides, capturedrookrights, rook/kingmovesrights, quiet/capture promotions, oldEPpositions andnewadjacentdoublepush fallback, ordinarycaptures/noncaptures. Arbitraryincorrectpointer or staleparent is outside normalcallcontract and wouldbe detected whenexercised.

B7 | copy Undo kinglines onlywhenvalid.
kFboard1182-1183 ordinarymake and1346-1347 nullmake copywholecacheonlyifvalid elsewriteundo.valid=false; unmake1334-1335/null1373-1374 restorewholecacheonlyifundo.valid elsemarkcurrentinvalid. r15dboard1173/1288 alwayscopies,1277/1314 alwaysrestores. Both invalidatemutatedboard aftermake (kF1299/null1360; r15d1242/null1301). Condition: no readeruses payloadwhenvalidfalse. Readers inspected: kFheader224-226 ensurekinglinesrefreshes;334-343is_legal refreshes at338;346-356gives_check refreshes349; board767-768 and863-864 conditionalvaliduse elsefallback;board908/1037guardrefresh. Thus invalidpayloadbytesneednotmatch r15d; nextuse reconstructs. make/unmake/null, castle/EP/promotion all alterpiece/sidegeometry butinvalidatebeforelaterqueries. A new unguardedpayloadreader or unmatchedundo wouldinvalidatecondition. Counters B5/B6 do not testB7directly; perftmake/unmake stressesit. No assertionthatall externaldirectAPI mutationpaths examined.

B8 | new SEE no-recapture early exits.
Shared existing earlyreturns: kFboard1493castle(0>=threshold),1505promotion_recapture_exchange,1514swap<0false,1516swap<=0true; r15d1432/1445/1454/1456same. New kF1530 returns true if no opponent pawn/knight/king contact and no opponent slider even on empty-board diagonal/orthogonal rays. Geometricray set is supersetofreal sliders, so zero means full r15d initial attacker set contains no opponent. New1554 checks actualbishop/rookattackrays withoccupancy afterorigin/capture removal; if no opponentcontact/slider thenfullr15dloopwouldfirst findnone andkeep result1true. r15d1458-1475 builds fullattackers immediately; its legal/pinfilter cannot add an absentattacker. CurrentkF1560 constructs fullattackers fromsame contact/raycomponents for continuation.
EP capturedsquare andorigin excluded byoccupancy1518/live01520, promotionrankrecapture delegatedbeforethese exits. Threatsbehindblockerscanbe ignoredonlywhen no firstrecapture exists; a slidernewlyexposed by removal is included inactualoccupancy ray. Existingcheck/pinnedopponent matters onlywhenpotentialattackerexists andthencontinuesfullfilter.
kF1540-1548 pawncheaprefutation is inside #else FORGE_SDK_SEE_HOIST; defaultboard14-15definesHOIST1, so it is NOT compiled in currentbuild. Do not claim executedcoverage. Otherhoistedcontact/pinner loop semantics match r15d1464ff.
Inputclasses: EP removingblocker, x-raysbehindcaptured/originpiece, promotionrecapture onbackrank, pinnedpawn orslider, kingrecapturedefendedtarget, zero/nonzero/negativeSEEthreshold, no-opponentcontact butpossibleblockedslider. No r15d-bodycounter implemented forB8; readingonly, optionalpart explicitlynotdone.

## 4. C-count tree gate and C-wrong control
Final frozen C-count SHA256 17964d27c43b5e19f0bc49fc65f3383a11851b70f25f747a45f02a3577007684; C-wrong ef782168e56a18538c3f22393e867c8ab1120d52e593a134537719e90149d40b.
Final patches clean-apply dry-run against unchanged kF: C_count.patch.txt SHA256 ebfffb868c206b12925ce7fcf60d188e313f14d06abb69d7cacffab48e026162; C_wrong.patch.txt a29496bbbb03521ab59bd61b1cf341a86015d78f096209c879f80cbae1478c21. Each is a full patch from kF; do not stack both. No repository engine source changed. C-wrong differs only by enabling reference-only wrong B1; no production return/decision is changed.
GCC14.2.0/libstdc++.so.6.0.33/glibc2.41, CMake4.4.5, C++20 Release -O3 -DNDEBUG -ffp-contract=off -fno-fast-math -march=x86-64-v4. C-count adds -DFORGE_SHORTCUT_COUNT=1; wrong also -DFORGE_SHORTCUT_WRONG=1. Other speed/NNUE flags match preserved kF; actual configure/build logs committed. Both compiled NDEBUG; debug assertions are inactive, independent references are enabled by the counter macro.
Counters reset at Searcher::search entry; first5 disagreement diagnostics process-wide, not reset per search. Summary under UCI output mutex after search before bestmove. B1/B2 diagnostics show pre-move fen; B5/B6 explicitly postmove_fen plus incoming move. B1 and B2 compare requested Board APIs (which share KingLines); B5 full compute_checkers is independent of known answer; B6 extends debug incremental arithmetic independently of precomputed pointer. Extra diagnostic work and cache refreshes may change runtime, not logical tree. Tree equality is tested, not assumed. Counters are diagnostic, not strength/speed evidence.

K1: fresh C-count, PC20 + synthetic net768, T1/H16, ucinewgame+isready before each depth9 search.1000 W1 entries/990distinct positions:16543291 nodes; every row's nodes and bestmove matches Job7 kF. Zero differing rows. K2: C-wrong first200 entries/197distinct:4097080 nodes; all200 row nodes/bestmove match Job7. B1 differences4392, so planted control is NOT silent; other counters zero. The deliberately incomplete B1 reference uses direct-check only, dropping discovered checks and castle-rook contributions; this is not a production defect.

|Run|B1 uses/diff|B2 uses/diff|B5 uses/diff|B6 uses/diff|
|---|---:|---:|---:|---:|
|K1|9079813/0|9638809/0|10935512/0|15430637/0|
|K2|2564528/4392|2689044/0|2607489/0|3895460/0|

K2 process-first5 diagnostics, verbatim:
```
info string shortcut disagreement B1 fen r3k3/5p2/p4bp1/P2p3p/2pP3P/2P2NP1/4KP2/4R3 w - - 0 30 move e2f1
info string shortcut disagreement B1 fen r3k3/5p2/p4bp1/P2p3p/2pP3P/2P2NP1/4KP2/4R3 w - - 0 30 move e2d2
info string shortcut disagreement B1 fen r3k3/5p2/p4bp1/P2p3p/2pP3P/2P2NP1/4KP2/4R3 w - - 0 30 move e2d1
info string shortcut disagreement B1 fen 4R3/5p2/p4bpk/q2p2Np/2pP3P/1rP3P1/5P2/2Q4K w - - 6 36 move g5e4
info string shortcut disagreement B1 fen 4R3/5p2/p4bpk/q2p2Np/2pP3P/1rP3P1/5P2/2Q4K w - - 6 36 move g5f3
```

There was an earlier completed gate/control on identical instrumentation with less-specific diagnostic FEN labels. After changing only B5/B6 label to postmove_fen, BOTH gates were rerun on the final hashes above before prediction. Earlier logs are retained locally outside repository, not substituted for final evidence.

## 5. Prediction graded
Immutable own commit77a6e03f3a916aff53f73e2f2fa0030a1de32e0b after gates/control and PartB, before S1 started17:36:41.333146Z. S1 knowingly informed by identical K1 workload; S2 ranges informed by Job8 but now uses distinct starts. Every range and zero-difference prediction PASS.
|Counter|S1 predicted uses|S1 observed|S2 predicted uses|S2 observed|Predicted/observed differences|
|---|---:|---:|---:|---:|---|
|B1|9.0–9.2million|9079813|2–8million|3212417|0 /0 in both|
|B2|9.5–9.8million|9638809|2–9million|3468791|0 /0 in both|
|B5|10.8–11.1million|10935512|2–9million|4071447|0 /0 in both|
|B6|15.2–15.7million|15430637|3–12million|5227491|0 /0 in both|

## 6. S1 and S2 results
S1 fresh C-count:1000 entries/990distinct positions, depth9,16543291 nodes; every Job7 baseline row nodes/bestmove equal. S2 fresh one-process C-count:20 first DISTINCT W1 positions,20 completed games,1370 legal plies/searches,5612423 actual nodes. Actual nodes are sum of `info string softnodes nodes N`, not last completed-depth info. Each game ucinewgame/isready once; each ply position fen START moves fullhistory then go softnodes2000. python-chess checks validity/legality each ply; stop at game_over(claim_draw=True) or200plies. All20 ended by game_over, none hit cap; maximum125plies. Local standalone move lists retained, not committed.
|Counter|S1 uses|S1 differences|S1 first difference|S2 uses|S2 differences|S2 first difference|
|---|---:|---:|---|---:|---:|---|
|B1|9079813|0|none|3212417|0|none|
|B2|9638809|0|none|3468791|0|none|
|B5|10935512|0|none|4071447|0|none|
|B6|15430637|0|none|5227491|0|none|

### S2 per-game provenance and totals
|Game|First W1 index (1-based)|Plies|Actualnodes|B1uses|B2uses|B5uses|B6uses|Result|
|---|---:|---:|---:|---:|---:|---:|---:|---|
|1|1|66|251033|89279|94079|177845|231697|1-0|
|2|2|104|439259|277021|295839|337272|406628|0-1|
|3|3|65|247022|93144|99006|169659|223046|0-1|
|4|4|81|338406|186581|199056|250032|311979|1-0|
|5|5|81|283603|173520|189846|242105|268410|1/2-1/2|
|6|6|82|357222|228530|242395|265052|340525|0-1|
|7|7|33|129149|64882|68510|86308|117195|0-1|
|8|8|64|262504|160655|186103|177513|245095|0-1|
|9|9|122|563911|378425|401979|381012|542161|1-0|
|10|10|47|214452|115112|125416|139687|198425|1-0|
|11|11|26|99689|39200|46969|61339|91935|1-0|
|12|12|21|88608|47216|58845|64589|80949|1/2-1/2|
|13|13|3|4275|2459|2761|3304|4134|0-1|
|14|15|117|512905|285257|309214|394621|471600|1-0|
|15|16|66|245498|117808|124617|180792|221810|1-0|
|16|17|52|194494|106743|113365|148023|170401|0-1|
|17|18|125|545972|362743|379503|378028|528521|1/2-1/2|
|18|19|122|479922|304239|337835|362571|449360|0-1|
|19|20|43|183257|94855|103448|125001|170158|0-1|
|20|21|50|171242|84748|90005|126694|153462|0-1|

## Facts, suspicions, not done, uncertainties
Facts: all required known-answer/tree/control gates pass;0differences in four exercised counters across S1 and S2; deliberately wrong reference4392differences. One row per shortcut above separates source argument from counted evidence. No new confirmed production bug found; no repair recommended. Board-copy/cached-result contract depends on parent restoration, valid cache guards and correct call-site ownership.
Suspicions: malformed unreachable parent boards, stale picker reuse, future unguarded king-line reads, or new persistent-task fields can violate assumptions. None was demonstrated by these workloads. Absence of discrepancies is not proof of general correctness.
What I did not do: B8 SEE reference counter (optional) not implemented; B3/B4/B7 only reading and indirect workload coverage; no race checker, no additional thread configurations, no PC compiler/net, no full-board hash reconstruction, no independent occupancy oracle for B1/B2, no speed/strength claim. No separate macro-off binary was built. Both diagnostic patches guard code with macro, but only enabled builds were exercised here.
What I am not sure about: inputs outside stated reachable/legal-parent assumptions, arbitrary external API clients, shared-helper bugs in Board reference and picker, concurrency outside T1, allocation failures. Exact model identity is not exposed, not guessed.

### What this check cannot see (verbatim)
Positions that W1 and the 20 games do not reach; the PC's net, compiler and build; more than one search thread
(sol3's job 22 runs that).

## Build / inputs / publication provenance
PC20 full option lines and active synthetic net checksum30ab43b4ba5db5f3 appear in each K/S raw transcript. Net SHA256 c3d95131d7c1c89ccb5b000b52c7c37ed8665dbf8bb2a0a7a873809c85b9f7c7, hidden768; W1 local input SHA2563c1b17332eca46a912f572eae8197324f466a8e2f909653104c427457ffb0521. Neither standalone input is committed. Input commands are preserved as raw terminal evidence. Base source6b98f2170a3210e71beed04bbd2553972c253ed7 plus preserved PCr15/carbon2/E1/finalstack patches defines tested originals, not base alone.
Raw K1/K2/S1/S2 transcripts split into consecutive <=100000byte text parts; concatenate in manifest order. raw_manifest.json.txt carries per-part and full-transcript SHA256/size. Native summaries are derived from those outputs, not substitutes. Eight gate/PartA transcripts are unsplit. No PR, no other branch write, no executable/net/book/standalone data file published.
Publication status will be appended after final independent readback. The auxiliary finding auditor resource remained unavailable in Job9; not represented as run here. Native assertions, source QA and full-body remote readbacks are distinct verification paths.

## FOR FABLE AND OPUS
No shortcut disagreement found in stated workloads. Shared KingLines Board-reference limitation and optional B8 omission are the main remaining coverage limits. Ready for next job; after report poll FABLE_TO_dot_11.md every2minutes for30minutes, respecting a first-lineSTOP and fresh final boundary check.

## Independent raw reparse and invariance QA
UTC 2026-11-18T17:38:10.716671+00:00
K1: raw reparse PASS 1000 searches, nodes 16543291, counters {'B1': {'uses': 9079813, 'differ': 0}, 'B2': {'uses': 9638809, 'differ': 0}, 'B5': {'uses': 10935512, 'differ': 0}, 'B6': {'uses': 15430637, 'differ': 0}}; diagnostics 0. All bestmoves legal.
K2: raw reparse PASS 200 searches, nodes 4097080, counters {'B1': {'uses': 2564528, 'differ': 4392}, 'B2': {'uses': 2689044, 'differ': 0}, 'B5': {'uses': 2607489, 'differ': 0}, 'B6': {'uses': 3895460, 'differ': 0}}; diagnostics 5. All bestmoves legal.
S1: raw reparse PASS 1000 searches, nodes 16543291, counters {'B1': {'uses': 9079813, 'differ': 0}, 'B2': {'uses': 9638809, 'differ': 0}, 'B5': {'uses': 10935512, 'differ': 0}, 'B6': {'uses': 15430637, 'differ': 0}}; diagnostics 0. All bestmoves legal.
S2: raw reparse PASS 1370 searches, nodes 5612423, counters {'B1': {'uses': 3212417, 'differ': 0}, 'B2': {'uses': 3468791, 'differ': 0}, 'B5': {'uses': 4071447, 'differ': 0}, 'B6': {'uses': 5227491, 'differ': 0}}; diagnostics 0. All bestmoves legal.
W1 verified 1000/990; S2 first20 DISTINCT verified against raw position commands, all1370 moves legal and all20 games terminal by claim_draw=True, maximum200plies respected. S2 actual-node line used, not lastdepth nodes. K1/K2/S1 every raw nodes/bestmove matches preserved Job7 baseline.
Patch invariance reviewed: all counter storage separate inline atomics; reset only counter storage; record only counters/output and Board reference queries. B1/B2 observe unchanged picker decisions and return values. B5 does not replace checkers0; B6 shadow XORs do not replace production key. C-wrong changes only B1 reference predicate via macro. No counter value feeds pruning/search/move selection. Diagnostic Board APIs can populate mutable KingLines cache earlier, so this is logical/tree invariance, NOT bit-for-bit untouched private cache/timing. Fixed-depth gates confirm nodes/bestmoves invariance in these workloads; clocks/performance not measured. First5 diagnostic cap is global process total, not per counter/search, and is not reset. Full patches dry-run clean against kF; no source edits after final hashes17964d27/ef782168. B1/B2 Board reference shares KingLines fast logic, so no independent occupancy oracle claimed.

## Verified publication checkpoint
2026-11-18T17:55:28Z: all62 additional files full-body read-back verified, including51 raw parts for4 complete K/S transcripts, full manifest,4 runtime summaries,4 configure/build logs, independentQA and buildmanifest. Earlier8 gate/PartA raw transcripts,2patches,PartB andprediction also individuallyverified. publication_verified.json.txt records62 per-file commits. No denied writes, no bulk-tree call. No claim that local .rows files or unrelated prior-job bulk logs are remote.

## Last shell command before report commit
`git status --short; ls -R forge-combo29/dot/job10`
Preserved local checkout/index does not track connector commits; untracked entries are not claims of remote publication. No cleanup or source reset performed.
```
 M forge-combo29/dot/job2/stamps.txt
?? forge-combo29/REPORT_dot_job10.md
?? forge-combo29/REPORT_dot_job6.md
?? forge-combo29/REPORT_dot_job7.md
?? forge-combo29/REPORT_dot_job8.md
?? forge-combo29/REPORT_dot_job9.md
?? forge-combo29/dot/job10/
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
forge-combo29/dot/job10:
A_kf.raw.txt
A_r15d.raw.txt
A_summary.txt
C_count.patch.txt
C_count_build.txt
C_count_configure.txt
C_wrong.patch.txt
C_wrong_build.txt
C_wrong_configure.txt
K1.progress.txt
K1.raw.txt
K1.rows.txt
K1.summary.txt
K2.progress.txt
K2.raw.txt
K2.rows.txt
K2.summary.txt
PartB_reading.txt
S1.progress.txt
S1.raw.txt
S1.rows.txt
S1.summary.txt
S2.raw.txt
S2.summary.txt
build_manifest.txt
gate_summary.txt
independent_QA.txt
kf_bench_11.raw.txt
kf_bench_13.raw.txt
kf_go_perft_5.raw.txt
local_finding_record.json.txt
publication_verified.json.txt
r15d_bench_11.raw.txt
r15d_bench_13.raw.txt
r15d_go_perft_5.raw.txt
raw
raw_manifest.json.txt

forge-combo29/dot/job10/raw:
K1.part001.txt
K1.part002.txt
K1.part003.txt
K1.part004.txt
K1.part005.txt
K1.part006.txt
K1.part007.txt
K1.part008.txt
K1.part009.txt
K1.part010.txt
K1.part011.txt
K1.part012.txt
K1.part013.txt
K2.part001.txt
K2.part002.txt
K2.part003.txt
S1.part001.txt
S1.part002.txt
S1.part003.txt
S1.part004.txt
S1.part005.txt
S1.part006.txt
S1.part007.txt
S1.part008.txt
S1.part009.txt
S1.part010.txt
S1.part011.txt
S1.part012.txt
S1.part013.txt
S2.part001.txt
S2.part002.txt
S2.part003.txt
S2.part004.txt
S2.part005.txt
S2.part006.txt
S2.part007.txt
S2.part008.txt
S2.part009.txt
S2.part010.txt
S2.part011.txt
S2.part012.txt
S2.part013.txt
S2.part014.txt
S2.part015.txt
S2.part016.txt
S2.part017.txt
S2.part018.txt
S2.part019.txt
S2.part020.txt
S2.part021.txt
S2.part022.txt
```
