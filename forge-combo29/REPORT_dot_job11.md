# Dot job 11: cache-free shortcut references and restored king lines

## 1. Step 0
PASS. Unchanged r15d SHA256 bb37ed7c50e1716c5fc38f1b2fb92293c18e98f6131bf2be2b13d668603b4fc6 and kF340f78f4e4834a5bf1e6dc2d73eca3caa62b7a45d05011b5c1c092ace6e5e5ea. Fresh process per command, uci/isready, NO options set and NO loaded net: both bench11=312866, bench13=862329 and go perft5=4865609 nodes. Six full raw transcripts are {r15d,kf}_{bench_11,bench_13,go_perft_5}.raw.txt.
Actual claim2026-11-18T18:01:49Z, c73e3045d0d047f901bfe9fb810bba966a888d3c. Native cutoff18:51:49Z, report deadline19:01:49Z. All native runs finished18:06:24.231822Z. Later time is raw-evidence publication and report verification, not additional experiments.

## 2. C-count2 patch, SHA256 and reference reading condition
C-count2 is frozen Job10 C-count plus new square-array diagnostic oracle and S-B1/S-B2/S-B4/S-B7 counters. C-count2 binary SHA25673be1f9d6c74f4fc7959539dda3a49dd680338f89ad8f6dadb454b85fbf86a5f; C-wrong2 b63143c3a114a7ab19853322012c007e1b1e4e8cd6ed8432169925c10a5d0050. Both frozen18:04:36Z, no subsequent source changes.
Full patch from original kF: C_count2_full.patch.txt SHA256 e99fcd4e24c0aa93d44e52fd132a934f872b1edc6c297764526494b6f7138993 (commitcede512d329b22cedaada0c51b9265dcf1cf97d6); C_wrong2_full.patch.txt5cfc19357bcabcbcd83767fe42949c03f083c8880d969950b586652f0d0a1228 (81403ea27bacba80c6c2a95dfe15151a3fbdefc9). Alternative *_from_job10.patch.txt applies to frozen Job10 C-count. Do NOT stack full and incremental versions. Full patches dry-run clean; only scratch trees changed, not repository source.
Build configuration: GCC14.2.0/libstdc++.so.6.0.33/glibc2.41, CMake4.4.5, C++20 Release -O3 -DNDEBUG -ffp-contract=off -fno-fast-math -march=x86-64-v4; FORGE_SHORTCUT_COUNT=1. Wrong2 enables FORGE_SHORTCUT_WRONG2=1 only; old B1 wrong-reference macro remains off. Actual build/configure logs and build_manifest.txt provide full definitions. No runtime speed comparison made.

### Reading condition and scope
The NEW reference header reads only Board::piece_at and Board::side_to_move plus Move values, copies64pieces to local storage and uses rank/file arithmetic. Sliders walk intervening squares one by one; kings are located by scanning that array. It calls no Board attack/legality/gives-check/make/king-line helper, no attack tables, no occupied/pieces bitboards. Its local move application cannot recurse through instrumented make/unmake. This is independent of the cached king-line computation, but still assumes valid piece encoding and generated pseudo-legal moves. It is not a full independent chess move generator.
S-B1 compares cached answer at every quiet-stage return with attacks by any mover piece after local move; S-B2 compares every old-B2 candidate's accepted/rejected verdict with own-king safety after local move, including castle origin/transit/final safety. Generator remains responsible for movement grammar, rights and empty castling path. S-B4 reconstructs all7 check slots, pins and discoverers from current piece geometry and compares picker copies; S-B7 does the same after every ordinary/null unmake restoring a valid cache. Invalid restored caches are not counted. No cache field is used to PRODUCE the new reference answers; comparing against production necessarily reads the cache on the fast side.
The new oracle does not mutate Board. Existing Job10 Board-API references can still refresh private KingLines earlier; tree/logical invariance is tested, not literal byte-for-byte private-cache immutability. Counters do not feed pruning, move ordering or search results.

### Requested grep, verbatim
Command semantics: grep -nE 'king_lines|ensure_king_lines|check_squares|pinned|discoverers' C_count2_full.patch.txt, then the same expression on the standalone reference header. The header section has no matches. Full patch matches below are required FAST-side field reads or unchanged context, not reference dependency.
```
Wed Nov 18 18:04:30 UTC 2026
FULL PATCH TOKENS: production comparator reads expected; independent reference has no matches
195:+                            (((pinned_ >> move.from) & 1ULL) == 0 || attacks::aligned(own_king_sq_, move.from, move.to));
201:                         } else if (((pinned_ >> move.from) & 1ULL) != 0 &&
222:+                        bool copies_differ = pinned_ != piece_lines.pins || discoverers_ != piece_lines.discoveries;
225:+                            copies_differ = copies_differ || check_squares_[type] != piece_lines.checks[type];
252:     else undo.king_lines.valid = false;
346:     if (undo.king_lines.valid) king_lines_ = undo.king_lines;
347:     else king_lines_.valid = false;
349:+    if (king_lines_.valid) {
351:+        bool restored_differ = king_lines_.pinned != piece_lines.pins || king_lines_.discoverers != piece_lines.discoveries;
353:+            restored_differ = restored_differ || king_lines_.check_squares[type] != piece_lines.checks[type];
362:     if (undo.king_lines.valid) king_lines_ = undo.king_lines;
363:     else king_lines_.valid = false;
365:+    if (king_lines_.valid) {
367:+        bool restored_differ = king_lines_.pinned != piece_lines.pins || king_lines_.discoverers != piece_lines.discoveries;
369:+            restored_differ = restored_differ || king_lines_.check_squares[type] != piece_lines.checks[type];
REFERENCE HEADER ONLY
```

### Reference design and limitations
Cache-free piece_reference.hpp design
Completed/checked date -u: Wed Nov18 18:04:25 UTC2026.
API forge::piece_reference::{gives_check,legal,direct_check,reconstruct}; Lines has checks[7],pins,discoveries. Reads only Board::piece_at and Board::side_to_move, plus Move value flags. It does not call Board::make_move, is_legal, gives_check, king_square, occupied, pieces, attackers_to, or any cache helper. No attack tables are used. Piece types/colors decoded from enum values; geometry checked by rank/file arithmetic and each intervening square in local64Piecearray. No search-read state is mutated.
Reference gives_check copies64pieces, moves source to destination, applies EP removal/promotion/castle rook relocation ifflags specify, then tests each mover piece against enemyking by direct piece geometry/slidingrays. The quiet-stage scope normally excludes captures/promotions but helper supports them. King-location comes from scanningpiecearray.
Reference legal assumes generatedpseudo-legal input; it does not validate entire movementgrammar/castlingrights. It copies/applies same move and rejects attacks on ownking. For castle it additionally rejects attacks at startingking and transitking square (rook remains home for transit), then tests completedcastleplacement. Rights/emptyroute are guaranteed by generator, not re-proven here. Arbitrary malformedMoves outsidecallercontract are notcovered.
Wrong2direct_check examines ONLYpiecearrivingon move.to on completedlocalplacement. A castle's rookcheck is intentionally excluded because movedpieceatkingdestination is theking; ordinarydiscoveredchecks likewiseexcluded. This is an intentionally incomplete reference, not a different search result.
Reconstruct checks use reversepawngeometry, independent knightoffsets, and eight square-by-square rays from enemyking; each slider ray includes its firstoccupiedsquare. Queen combines bishop+rook; checks[NoPieceType] andchecks[King] explicitlyremain0, matchingfielddefinitions ratherthanlegalmovemasks. Pins/discoveries walk eachray from relevantking, rememberfirstoccupiedsquare, then requiresecondoccupiedpiece is correctlycoloredslider andfirstblocker is movercolor. This is exactlyoneinterveningpiece definition, calculatedwithoutcachedfields. Allmasksinitially0.
Sanitytests: syntax compilation passed. Standalone localmicrochecks passed pin/blocker, blocked/open rookray, castlerookplacement, discoveredblocker, knightmovement,pawndirection,EPplacement. Initialdiscoveryfixture putrookandknight inreverseorder; correctedfixture (nooraclechange), rerunexit0. These are microchecks, notexhaustiveoraclevalidation. Full tree/counter gates separately required.
Grep on referenceheader for king_lines|ensure_king_lines|check_squares|pinned|discoverers|.gives_check|.is_legal|.make_move returned no matches. Integrationpatch will necessarily contain cachedfieldreads on FASTcomparison side; referenceheader itself doesnot. Please distinguishthose in report.

### Integration locations and counter lifetime
Wed Nov 18 18:05:06 UTC 2026
Job11 integration scope: old B1/B2/B5/B6 call sites unchanged; summary extends to8names. New S-B1/S-B4 run at every quiet return after legal filtering, S-B2 at every oldB2 candidate before legality reject. S-B7 after actual board and king-line restoration in unmake_move and unmake_null_move, only valid restored cache. Pre-search position parse unmake counters are reset at Searcher::search; summaries cover search interval. Nullmove diagnostic move0000. First5 diagnostics shared across all8counters/process; not reset persearch. New oracle references read only piece_at, side_to_move, and Move fields; no Board make/gives/islegal or cached field. S-B4/S-B7 comparator necessarily reads production copies/restored cache to compare oracle values; full patch grep expected to show those tokens. All7 check slots compared including0/King. Wrong2 direct_check tests only moved destination piece in transformed local array, omits discovered/rookcastle checks; oldB1 normal. Counter values never used for search decisions. No experiments by integration worker.

## 3. Gate, same-uses check and C-wrong2
K1: fresh C-count2 process, PC20 + net768, Threads1/Hash16, ucinewgame/isready before each depth9 search. W1 has1000entries/990distinct positions. Node sum16543291, every row nodes/bestmove equals Job7 kF, zero differing rows. All old-counter totals exactly Job10; S-B1 equals B1 uses and S-B2 equals B2 uses. Gate validation passed18:05:51.638885Z.
C-wrong2 K2: first200 W1 entries/197distinct,4097080nodes, all200 baseline rows equal. Only S-B1 reference is intentionally incomplete; production tree and old B1 reference untouched. S-B1 gives4392differences, so control is not silent. This exactly matches Job10 control. Both wrong references deliberately omit rook checks in castling: Job10 direct king check-square is0; Wrong2 checks only piece arriving at king destination, not the rook. Adjacent-king direct attacks do not occur for legal returned castles, explaining no extra count here. No changed production behavior inferred.

|Counter|K1 uses|K1 differences|K2 uses|K2 differences|
|---|---:|---:|---:|---:|
|B1|9079813|0|2564528|0|
|B2|9638809|0|2689044|0|
|B5|10935512|0|2607489|0|
|B6|15430637|0|3895460|0|
|S-B1|9079813|0|2564528|4392|
|S-B2|9638809|0|2689044|0|
|S-B4|9079813|0|2564528|0|
|S-B7|15531178|0|3895323|0|

K2 first5 diagnostics (pre-move FEN), verbatim:
```
info string shortcut disagreement S-B1 premove_fen r3k3/5p2/p4bp1/P2p3p/2pP3P/2P2NP1/4KP2/4R3 w - - 0 30 move e2f1
info string shortcut disagreement S-B1 premove_fen r3k3/5p2/p4bp1/P2p3p/2pP3P/2P2NP1/4KP2/4R3 w - - 0 30 move e2d2
info string shortcut disagreement S-B1 premove_fen r3k3/5p2/p4bp1/P2p3p/2pP3P/2P2NP1/4KP2/4R3 w - - 0 30 move e2d1
info string shortcut disagreement S-B1 premove_fen 4R3/5p2/p4bpk/q2p2Np/2pP3P/1rP3P1/5P2/2Q4K w - - 6 36 move g5e4
info string shortcut disagreement S-B1 premove_fen 4R3/5p2/p4bpk/q2p2Np/2pP3P/1rP3P1/5P2/2Q4K w - - 6 36 move g5f3
```

## 4. Prediction graded
Immutable commit4efec48604919788e5b5d2814538acbcf7107aa6 after Step0/gates/control and before fresh S1 start18:05:56Z. The job calls S1 the tree-gate run; I reran the same workload after prediction to make chronology unambiguous. S1 ranges explicitly informed by K1, not blind; S2 ranges informed by Job10 identical workload/old counters. All ranges and zero-difference predictions PASS.
|New counter|S1 predicted uses|S1 observed|S2 predicted uses|S2 observed|Predicted/observed differences|
|---|---:|---:|---:|---:|---|
|S-B1|9.0–9.2million|9079813|3.1–3.3million|3212417|0 /0 in both|
|S-B2|9.5–9.8million|9638809|3.3–3.6million|3468791|0 /0 in both|
|S-B4|9.0–9.2million|9079813|3.1–3.3million|3212417|0 /0 in both|
|S-B7|15.3–15.8million|15531178|4.5–6.0million|5255554|0 /0 in both|

## 5. S1 and S2
S1 fresh run:1000entries/990distinct,16543291nodes, every baseline row's nodes/bestmove equal. S2 fresh one-process run:20distinct starting positions in first-occurrence W1 order, same rules as Job10,1370searches/legal plies and5612423actualnodes. Actual nodes come from softnodes counter lines, not last finished-depth info. All20 move lists and starts match Job10 exactly; no first differing move exists. All old uses match Job10 exactly, and all eight counters give0differences.
|Counter|S1 uses|S1 differences|First S1 difference|S2 uses|S2 differences|First S2 difference|
|---|---:|---:|---|---:|---:|---|
|B1|9079813|0|none|3212417|0|none|
|B2|9638809|0|none|3468791|0|none|
|B5|10935512|0|none|4071447|0|none|
|B6|15430637|0|none|5227491|0|none|
|S-B1|9079813|0|none|3212417|0|none|
|S-B2|9638809|0|none|3468791|0|none|
|S-B4|9079813|0|none|3212417|0|none|
|S-B7|15531178|0|none|5255554|0|none|

### S2 game provenance
Each game: ucinewgame/isready once, then position fen START moves fullhistory and go softnodes2000 each ply; python-chess validates every move, stop game_over(claim_draw=True) or200plies. All20 terminal before cap, maximum125plies.
|Game|First W1 index(1-based)|Plies|Actualnodes|S-B1 uses|S-B2 uses|S-B4 uses|S-B7 uses|Result|
|---|---:|---:|---:|---:|---:|---:|---:|---|
|1|1|66|251033|89279|94079|89279|233154|1-0|
|2|2|104|439259|277021|295839|277021|410969|0-1|
|3|3|65|247022|93144|99006|93144|223790|0-1|
|4|4|81|338406|186581|199056|186581|314165|1-0|
|5|5|81|283603|173520|189846|173520|270351|1/2-1/2|
|6|6|82|357222|228530|242395|228530|342217|0-1|
|7|7|33|129149|64882|68510|64882|118563|0-1|
|8|8|64|262504|160655|186103|160655|245191|0-1|
|9|9|122|563911|378425|401979|378425|537723|1-0|
|10|10|47|214452|115112|125416|115112|198593|1-0|
|11|11|26|99689|39200|46969|39200|89839|1-0|
|12|12|21|88608|47216|58845|47216|81268|1/2-1/2|
|13|13|3|4275|2459|2761|2459|4123|0-1|
|14|15|117|512905|285257|309214|285257|477732|1-0|
|15|16|66|245498|117808|124617|117808|224568|1-0|
|16|17|52|194494|106743|113365|106743|175678|0-1|
|17|18|125|545972|362743|379503|362743|525286|1/2-1/2|
|18|19|122|479922|304239|337835|304239|454471|0-1|
|19|20|43|183257|94855|103448|94855|171341|0-1|
|20|21|50|171242|84748|90005|84748|156532|0-1|

## Facts, suspicions, not done and uncertainties
Facts: all required gates pass, same tree and same old uses preserved, planted wrong reference detects4392events, all four new counters0differences on S1/S2. Restored-valid cache and picker copies agree with piece-only reconstruction at every counted use in these workloads. No new confirmed production bug or repair proposed. Full cache-free reference code is in the patches; first5 diagnostic limit is process-wide across all8counters, reset only usage/difference counts per search. New reference mutates only local arrays. Search summaries cover search interval; pre-search position parsing counts are reset at Searcher::search entry.
Suspicions: generated pseudo-legal contract, board restoration, piece encoding and future field additions remain possible failure boundaries, not observed bugs. Shared mistakes outside cached-line computation or reference implementation mistakes are not excluded by passing samples.
What I did not do: no B8 SEE reference; no new independent B5/B6 reference beyond Job10 checker/incremental arithmetic; no PC compiler/net, no Threads>1, no arbitrary malformed move grammar, no full castling-right/path revalidation inside oracle, no independent full engine or strength/speed test, no macro-off rebuild. Focused oracle microchecks are not exhaustive; the initial reversed-piece test fixture was corrected without changing oracle. No production source or standalone inputs committed.
What I am not sure about: unvisited legal positions, arbitrary direct C++ clients, allocation failures, concurrency outside T1, correctness of all new reference code beyond source review/microchecks/control/workload evidence. Exact model identity is unavailable, not guessed.

### What this check cannot see (verbatim)
Positions that W1 and the 20 games do not reach; the PC's net, compiler and build; more than one search thread; B5,
B6 and B8 against references free of the cache (B5 and B6 do not read it; B8 is checked by sol3).

## Inputs and evidence format
PC20 exact options in each raw transcript: Threads1,Hash16,OwnBookfalse,LmrQuietBase93,LmrQuietDivisor205,LmrNoisyBase13,LmrNoisyDivisor333,LmrHistoryDivisor5643,NullMoveBase5,LmpBase8,HistoryPruneMultiplier2220,HistoryBonusQuadratic24,HistoryBonusLinear54,HistoryBonusMax2212,SingularDepth6,IirDepth2,NonPawnCorrectiontrue,CuckooReptrue,HistRework2,TtPruneV2true,CorrHistV2true,MateAlphaGuardtrue.
Synthetic v3 nethidden768 checksum30ab43b4ba5db5f3, SHA256c3d95131d7c1c89ccb5b000b52c7c37ed8665dbf8bb2a0a7a873809c85b9f7c7; W1 SHA2563c1b17332eca46a912f572eae8197324f466a8e2f909653104c427457ffb0521. These remain local, never standalone committed inputs. Base6b98f2170a3210e71beed04bbd2553972c253ed7 plus preserved r15d/kF stack and diagnostic patches defines builds, not basealone.
Raw K1/K2/S1/S2 are split at100000bytes into59parts; concatenate manifest order. Manifest contains original-stream and part SHA256/size. Six Step0 logs are unsplit. All numeric runtime claims derive from raw output, not summaries alone. Standalone move lists remain local; terminal input commands are raw evidence. Publication status/total bytes appended after full-body readback. No file>5MB or job>20MB committed. Auxiliary finding auditor unavailable as prior recorded resource error; not represented as run.

## FOR FABLE AND OPUS
The shared-KingLines reference limitation from Job10 is addressed by new piece-array references for requested counters. No discrepancy observed; do not generalize zero over unvisited inputs or other builds. After report, poll FABLE_TO_dot_12.md every2minutes for30minutes, with fresh final-boundary read and first-lineSTOP respected.

## Independent raw QA
UTC 2026-11-18T18:06:56.113373+00:00
K1: raw reparse PASS 1000 searches, nodes 16543291, counters {'B1': {'uses': 9079813, 'differ': 0}, 'B2': {'uses': 9638809, 'differ': 0}, 'B5': {'uses': 10935512, 'differ': 0}, 'B6': {'uses': 15430637, 'differ': 0}, 'S-B1': {'uses': 9079813, 'differ': 0}, 'S-B2': {'uses': 9638809, 'differ': 0}, 'S-B4': {'uses': 9079813, 'differ': 0}, 'S-B7': {'uses': 15531178, 'differ': 0}}; diagnostics 0. All bestmoves legal.
K2: raw reparse PASS 200 searches, nodes 4097080, counters {'B1': {'uses': 2564528, 'differ': 0}, 'B2': {'uses': 2689044, 'differ': 0}, 'B5': {'uses': 2607489, 'differ': 0}, 'B6': {'uses': 3895460, 'differ': 0}, 'S-B1': {'uses': 2564528, 'differ': 4392}, 'S-B2': {'uses': 2689044, 'differ': 0}, 'S-B4': {'uses': 2564528, 'differ': 0}, 'S-B7': {'uses': 3895323, 'differ': 0}}; diagnostics 5. All bestmoves legal.
S1: raw reparse PASS 1000 searches, nodes 16543291, counters {'B1': {'uses': 9079813, 'differ': 0}, 'B2': {'uses': 9638809, 'differ': 0}, 'B5': {'uses': 10935512, 'differ': 0}, 'B6': {'uses': 15430637, 'differ': 0}, 'S-B1': {'uses': 9079813, 'differ': 0}, 'S-B2': {'uses': 9638809, 'differ': 0}, 'S-B4': {'uses': 9079813, 'differ': 0}, 'S-B7': {'uses': 15531178, 'differ': 0}}; diagnostics 0. All bestmoves legal.
S2: raw reparse PASS 1370 searches, nodes 5612423, counters {'B1': {'uses': 3212417, 'differ': 0}, 'B2': {'uses': 3468791, 'differ': 0}, 'B5': {'uses': 4071447, 'differ': 0}, 'B6': {'uses': 5227491, 'differ': 0}, 'S-B1': {'uses': 3212417, 'differ': 0}, 'S-B2': {'uses': 3468791, 'differ': 0}, 'S-B4': {'uses': 3212417, 'differ': 0}, 'S-B7': {'uses': 5255554, 'differ': 0}}; diagnostics 0. All bestmoves legal.
W1 verified 1000/990; S2 first20 DISTINCT verified against raw position commands, all1370 moves legal and all20 games terminal by claim_draw=True, maximum200plies respected. S2 actual-node line used, not lastdepth nodes. K1/K2/S1 every raw nodes/bestmove matches preserved Job7 baseline.
Same-uses gates PASS for every old counter; S-B1/S-B2 match B1/B2; S-B4 matches B1. S-B7 K1/S1=15531178, S2=5255554. All20 S2 start FENs and full move lists equal job10 local data.
Reference independence: opened full127-line piece_reference.hpp. Board member reads are only piece_at at15 and side_to_move at62/69/74/115; no Board make/unmake, gives_check/is_legal, ensure_king_lines, or cached field. All attacks use local array64, type/color arithmetic, and square-by-square rays. grep of full patch contains expected production-side comparator reads (copied fields and restored king_lines); oracle header itself has zero matches for requested five tokens. This is a code reading proof plus grep, not merely token absence.
Oracle scope: assumes generated pseudo-legal moves and valid standard-chess board with kings. It does not independently generate moves or validate castling rights/rook existence/piece geometry; castle legality additionally checks attack at start/transit/final. Local array move transformation handles promotion/EP/castling, but quiet-stage workloads exclude promotion/EP so those oracle branches are not demonstrated by S-B1/S-B2 counts. Missing kings return no threat (invalid-input oracle not specified). Reconstruction King's check-square slot is deliberately0 to match stored-field semantics, not a claim kings cannot attack. S-B7 counts only restored-valid fields; invalid states are not compared. First5 diagnostics global across8counters/process, not5 per counter. No multithread, external compiler/net, or unseen-position guarantee.
All new counter differences zero on K1/S1/S2. Wrong2 S-B1 alone4392 with5 diagnostics, oldB1zero. No discrepancy found; production sources unchanged from frozen hashes.
Additional exact-row check: all old B1/B2/B5/B6 USES match Job10 at every K1/K2/S1 row; old differences match except deliberate Job10 K2 B1 fault versus normal Job11 B1 (expected). All1370 S2 per-ply old uses AND differences match Job10 local per-ply records.
Macro audit: count2 CXX_FLAGS has FORGE_SHORTCUT_COUNT=1 and no WRONG/WRONG2 define. Wrong2 CXX_FLAGS adds FORGE_SHORTCUT_WRONG2=1 only; header also default-defines WRONG2 to1 if unset. Recursive source grep finds no '#define FORGE_SHORTCUT_WRONG' without2 in either tree. Old #if FORGE_SHORTCUT_WRONG is undefined=>0; old B1 normal in both builds. Full flags captured build_manifest. B8 not instrumented and no claim made.

## Verified publication checkpoint
All 76 additional files individually full-body read-back verified by 2026-11-18T18:28:20Z: 5,770,031 bytes total, maximum 100,000 bytes. Includes 59 raw parts, complete manifest, summaries, incremental patches, build/provenance, grep/design/integration and independent QA. Earlier 6 Step0 raw logs and 2 full patches were separately verified. Claim/prediction/checkpoint and this report are additional small text. Total job footprint including a 100KB report and 100KB metadata allowance remains below 6.1MB, below 20MB; no file exceeds 100KB, hence below 5MB. No standalone position/game datasets. publication_verified.json.txt records all 76 commits/sizes.
A short environment transition interrupted a write before approval after 55 verified files. The exact next destination was checked and returned404, root confirmed no user cancellation, and publication resumed. No denied authorization bypassed, no duplicate successful write, no native rerun or lost evidence.

## Last shell command before report commit
`git status --short; ls -R forge-combo29/dot/job11`
Preserved local index does not reflect connector commits; local untracked entries are not assertions that every local file is remote.
```
 M forge-combo29/dot/job2/stamps.txt
?? forge-combo29/REPORT_dot_job10.md
?? forge-combo29/REPORT_dot_job11.md
?? forge-combo29/REPORT_dot_job6.md
?? forge-combo29/REPORT_dot_job7.md
?? forge-combo29/REPORT_dot_job8.md
?? forge-combo29/REPORT_dot_job9.md
?? forge-combo29/dot/job10/
?? forge-combo29/dot/job11/
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
forge-combo29/dot/job11:
C_count2_build.txt
C_count2_configure.txt
C_count2_from_job10.patch.txt
C_count2_full.patch.txt
C_wrong2_build.txt
C_wrong2_configure.txt
C_wrong2_from_job10.patch.txt
C_wrong2_full.patch.txt
K1.progress.txt
K1.raw.txt
K1.rows.txt
K1.summary.txt
K2.progress.txt
K2.raw.txt
K2.rows.txt
K2.summary.txt
S1.progress.txt
S1.raw.txt
S1.rows.txt
S1.summary.txt
S2.raw.txt
S2.summary.txt
build_manifest.txt
gate_summary.txt
gate_validation.txt
independent_QA.txt
integration_notes.txt
kf_bench_11.raw.txt
kf_bench_13.raw.txt
kf_go_perft_5.raw.txt
publication_verified.json.txt
r15d_bench_11.raw.txt
r15d_bench_13.raw.txt
r15d_go_perft_5.raw.txt
raw
raw_manifest.json.txt
reference_design.txt
reference_grep.txt

forge-combo29/dot/job11/raw:
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
K1.part014.txt
K1.part015.txt
K2.part001.txt
K2.part002.txt
K2.part003.txt
K2.part004.txt
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
S1.part014.txt
S1.part015.txt
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
S2.part023.txt
S2.part024.txt
S2.part025.txt
```
