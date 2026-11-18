# Dot job12: complete kF/r15d hunk map and two selected reference counters

## 1. Step 0
PASS: unchanged r15d SHA256bb37ed7c50e1716c5fc38f1b2fb92293c18e98f6131bf2be2b13d668603b4fc6 and kF340f78f4e4834a5bf1e6dc2d73eca3caa62b7a45d05011b5c1c092ace6e5e5ea. Fresh process per command, uci/isready, no setoptions/no loaded net. Both bench11=312866,bench13=862329,go perft5=4865609 nodes. Six full raw transcripts committed and full-body verified.
Claim2026-11-18T18:33:21Z (d33b2d884ec4811c7a95bbceee58468b487c6695); nativecutoff19:23:21Z/reportdeadline19:33:21Z. Native runs finished18:43:00.966876Z. PartA map was completed and published before native counter runs/prediction.

## 2. Complete map
Exact commands, in order; concatenate stdout with no inserted separators (exit1 means differences, not execution failure):
```
diff -ru /tmp/forge-dot-r15d-src/src /tmp/forge-dot-kf-src/src
diff -ru /tmp/forge-dot-r15d-src/include /tmp/forge-dot-kf-src/include
diff -ru /tmp/forge-dot-r15d-src/CMakeLists.txt /tmp/forge-dot-kf-src/CMakeLists.txt
```
Exit codes1,1,0. Concatenated output122872bytes, SHA256c2accc5e40bced1bf635395c663a5355a9a8ea8c709a98ab5357f29594cd5465; committed as diff.part001.txt+diff.part002.txt in that order, exactly100000+22872bytes. diff_provenance.txt records original observed time/commands. Independent QA reran all3commands and obtained exact bytes/digest.86hunks across9changed files,1281added/292removedlines; CMake unchanged; no Only-in files. Every hunk has one row, none omitted. All Job9 UCI hunks and Job10 B1–B8 mechanisms have corresponding original file/range evidence in the map.
Frozen pre-counter map commitac1b7f943830567964956b458535ea44660f5e43. NONE is explicitly a direct-runtime-reference gap for a behavioral facet, not absence of source reading or broad integration evidence. Partial/source evidence is retained. Do not read NONE as 'never tested in any way'. Other helpers are cited only as Opus-reported unless separately verified; I did not reparse sol3/sol2 raw logs in this job. My own earlier Job8 NNUE output-reference evidence is also included rather than discarded because it predatesJob9.

# Job12 complete hunk map (pre-counter coverage)

Exact diff covers unchanged r15d versus kF src/, include/, CMakeLists.txt.86 hunks, all86 rows below; no Only-in files and CMake identical. Original hunk line ranges include context. Source timestamps in raw diff are preserved; digest of concatenated stdout c2accc5e40bced1bf635395c663a5355a9a8ea8c709a98ab5357f29594cd5465 (122872bytes).

Coverage legend: NONE = no existing direct dynamic reference for the changed behavioral mechanism or stated uncovered facet. It does NOT mean no source reading or no broad integration tests. Source-only/partial evidence is retained explicitly; broad same-game/node/perft evidence cannot independently prove each hunk. PARTIAL/DIRECT identifies relevant direct checks with stated limits, not proof across allinputs. NO_BEHAVIOUR identifies header/declaration/comment or compiled-off change. Other helpers results are known through Opus handoffs, not personally re-parsed here; no claim of reading their raw reports. Job8 is also cited where its independently refreshed NNUE reference directly covers an earlier change, even though Job12 examples emphasizeJobs9–11.

|File|Added|Removed|Hunks|
|---|---:|---:|---:|
|src/board.cpp|127|37|12|
|src/nnue_v3.cpp|176|34|4|
|src/search.cpp|630|113|39|
|src/uci.cpp|155|71|15|
|include/forge/b4.hpp|15|9|1|
|include/forge/board.hpp|9|1|3|
|include/forge/eval.hpp|3|0|1|
|include/forge/nnue_v3.hpp|26|10|3|
|include/forge/search.hpp|140|17|8|
|CMakeLists.txt|0|0|0|

Pre-counter NONE count=35. Largest search-read NONE facets by added+removed lines: H28=210, H18=131, H27=95, H82=66, H85=50, H25=39. Ties break by ascending hunk ID. Select H28 quiet generation/scoring and H18 TT operations. NNUEH15(138lines) has Job8 independent eval-output reference evidence, so is not NONE despite branch-reach limits.

|ID|File|kF range|+/-|Change|Coverage/evidence|Active/off and limit|
|---:|---|---|---|---|---|---|
|1|src/board.cpp|2-8|+1/-0|Add assert header|NO_BEHAVIOUR: Header only; runtime assertions disabled by NDEBUG in original Release build.|NDEBUG disables new assertions; Header only; runtime assertions disabled by NDEBUG in original Release build.|
|2|src/board.cpp|834-841|+2/-1|Mask king destinations attacked by enemy pawns/king before expensive safety test|NONE: Job10 B7/perft exercises move generation but no per-use independent early-mask counter; no inspected external report isolates this hunk.|active; Job10 B7/perft exercises move generation but no per-use independent early-mask counter; no inspected external report isolates this hunk.|
|3|src/board.cpp|852-872|+11/-4|has_legal_move fast safe-pawn witness and no-ray pin shortcut|NONE: Job10/11 B2/S-B2 checks quiet picker, not has_legal_move early witnesses; broad node equality is not isolated coverage.|active; Job10/11 B2/S-B2 checks quiet picker, not has_legal_move early witnesses; broad node equality is not isolated coverage.|
|4|src/board.cpp|1165-1171|+1/-1|Extend make_move signature with supplied key/check hint|DIRECT: Job10 B5/B6 counters at every shortcut use; Job11 repeats same old counter uses. Signature itself defines no new algorithm.|active; Job10 B5/B6 counters at every shortcut use; Job11 repeats same old counter uses. Signature itself defines no new algorithm.|
|5|src/board.cpp|1179-1195|+8/-1|Conditional Undo cache save and optional old-EP hash update/debug shadow|DIRECT: Job11 S-B7 recomputes restored fields cache-free; Job10 B6 independent incremental key comparison covers supplied-key uses. NDEBUG shadow off normally.|mixed: runtime path active, debug shadow off; Job11 S-B7 recomputes restored fields cache-free; Job10 B6 independent incremental key comparison covers supplied-key uses. NDEBUG shadow off normally.|
|6|src/board.cpp|1198-1238|+20/-5|Skip capture/mover/promotion hash XORs when precomputed key supplied|DIRECT: Job10 B6 compares every supplied key with incremental reference incl capture/promotion terms; repeated Job11. No per-move-class tally.|runtime active; debug shadow off; Job10 B6 compares every supplied key with incremental reference incl capture/promotion terms; repeated Job11. No per-move-class tally.|
|7|src/board.cpp|1242-1298|+45/-19|Consume precomputed key and known false gives-check; otherwise full paths|DIRECT: Job10 B5 recomputes checkers for every known0; B6 independently accumulates full key. Job11 repeats counts; S-B1 independently verifies quiet gives-check input.|runtime active; NDEBUG assertions off; Job10 B5 recomputes checkers for every known0; B6 independently accumulates full key. Job11 repeats counts; S-B1 independently verifies quiet gives-check input.|
|8|src/board.cpp|1331-1338|+2/-1|Restore Undo fields only if valid else invalidate|DIRECT: Job11 S-B7 validates every restored-valid cache against piece-square oracle; invalid-field payload intentionally unobservable until refresh.|active KING_LINES=1; Job11 S-B7 validates every restored-valid cache against piece-square oracle; invalid-field payload intentionally unobservable until refresh.|
|9|src/board.cpp|1343-1350|+2/-1|Conditional cache save for null move|DIRECT: Job11 S-B7 null-unmake reconstruction validates restored-valid fields; no null-only tally.|active KING_LINES=1; Job11 S-B7 null-unmake reconstruction validates restored-valid fields; no null-only tally.|
|10|src/board.cpp|1370-1377|+2/-1|Conditional cache restoration on null unmake|DIRECT: Job11 S-B7 includes null-unmake at every valid restore, compared with piece-array oracle.|active KING_LINES=1; Job11 S-B7 includes null-unmake at every valid restore, compared with piece-array oracle.|
|11|src/board.cpp|1516-1534|+11/-3|SEE contact/ray-empty early success before full exchange loop|NONE: Job10 B8 was source-read only, no SEE reference counter. External sol3 asserts reported by handoff but exact coverage not inspected here.|active; Job10 B8 was source-read only, no SEE reference counter. External sol3 asserts reported by handoff but exact coverage not inspected here.|
|12|src/board.cpp|1536-1564|+22/-0|SEE actual-ray-empty early success and factored attacker gather; off-branch pawn refutation|NONE: Job10 B8 source proof only; no local independent SEE loop comparison. HOIST0 pawn early-refutation is not in build; other added lines active.|mixed: HOIST1 active; #else pawn refutation off; Job10 B8 source proof only; no local independent SEE loop comparison. HOIST0 pawn early-refutation is not in build; other added lines active.|
|13|src/nnue_v3.cpp|696-701|+0/-8|Remove out-of-line king_key; move identical expression to header h76|NO_BEHAVIOUR: Same orientation/bucket/flip formula inspected old body vs new inline body. Linkage/inlining relocation, not changed answer for valid inputs.|inline replacement active; Same orientation/bucket/flip formula inspected old body vs new inline body. Linkage/inlining relocation, not changed answer for valid inputs.|
|14|src/nnue_v3.cpp|814-828|+9/-3|Resize/reinitialize only metadata instead of value-zeroing accumulator arrays|PARTIAL: Job7 W2 reload/switch lifecycle differential; Job8 every v3 search output independently shadowed against fresh scalar evaluation. No allocation-path count or hidden-size-switch coverage.|active with loaded v3 net; Job7 W2 reload/switch lifecycle differential; Job8 every v3 search output independently shadowed against fresh scalar evaluation. No allocation-path count or hidden-size-switch coverage.|
|15|src/nnue_v3.cpp|899-1042|+138/-0|Add fused one-perspective update plus opposite refresh and output|PARTIAL: Job8 S1/S2 every fast v3 result compared with fresh scalar evaluation; positive incremental-error control. No dedicated XOR-fusion branch hit count, so cannot assert every case/line exercised. Job7 alone only differential, not independent.|AVX512 branch active in main build; scalar fallback exercised by Job8 S3 kernel build; Job8 S1/S2 every fast v3 result compared with fresh scalar evaluation; positive incremental-error control. No dedicated XOR-fusion branch hit count, so cannot assert every case/line exercised. Job7 alone only differential, not independent.|
|16|src/nnue_v3.cpp|1064-1110|+29/-23|Reorder AVX512 refresh by hidden lane, zero-change copy fast path, borrow piece bitboards|PARTIAL: Job8 per-evaluation fresh reference and scalar-kernel differential cover observable outputs on reached calls; no zero-change-path or individual refresh branch counts.|AVX512 active; fallback separately scalar S3; Job8 per-evaluation fresh reference and scalar-kernel differential cover observable outputs on reached calls; no zero-change-path or individual refresh branch counts.|
|17|src/search.cpp|21-27|+1/-1|Default-enable bad-capture prefix reuse instead of separate array|NONE: NONE|Enabled in actual build; No per-use independent mechanism test identified.|
|18|src/search.cpp|525-661|+131/-0|Fast TT locked probe and owned/locked store; factored full-cluster replacement|NONE: NONE|Enabled in actual build; No per-use independent mechanism test identified.|
|19|src/search.cpp|886-916|+22/-1|Quiet legality/check cached at return and consumed by search|PARTIAL_OR_DIRECT: Job10 B1-B4; Job11 S-B1/S-B2/S-B4|Enabled KING_LINES=1; Direct per-use piece-array oracle for quiet legality/check/copies on W1 and20games; not generator completeness or all-position proof|
|20|src/search.cpp|944-950|+1/-2|Mark illegal tied-evasion slots Move::none instead of deferred legality mask|NONE: NONE|Enabled in actual build; No per-use independent mechanism test identified.|
|21|src/search.cpp|955-964|+4/-2|Quiet legality/check cached at return and consumed by search|PARTIAL_OR_DIRECT: Job10 B1-B4; Job11 S-B1/S-B2/S-B4|Enabled KING_LINES=1; Direct per-use piece-array oracle for quiet legality/check/copies on W1 and20games; not generator completeness or all-position proof|
|22|src/search.cpp|1007-1039|+16/-4|MovePicker storage refactor and copied king-line fields; fallback branch closure|PARTIAL_OR_DIRECT: Job10 B4; Job11 S-B4|Enabled copies; #else direct derivation off KING_LINES=1; Direct oracle covers copied masks at every quiet return; buffer removal and evasion mask lifetime lack dedicated reference|
|23|src/search.cpp|1043-1049|+1/-0|MovePicker storage refactor and copied king-line fields; fallback branch closure|PARTIAL_OR_DIRECT: Job10 B4; Job11 S-B4|Enabled copies; #else direct derivation off KING_LINES=1; Direct oracle covers copied masks at every quiet return; buffer removal and evasion mask lifetime lack dedicated reference|
|24|src/search.cpp|1079-1085|+1/-1|Lazily produce/invalidate HistRework threat maps and piece-specific reads|NONE: NONE|Enabled in actual build; No per-use independent mechanism test identified.|
|25|src/search.cpp|1121-1173|+37/-2|AVX512 16/8-lane highest-score selection and Scored-return wrapper|NONE: NONE|Enabled in actual build; No per-use independent mechanism test identified.|
|26|src/search.cpp|1202-1212|+3/-1|AVX512 16/8-lane highest-score selection and Scored-return wrapper|NONE: NONE|Enabled in actual build; No per-use independent mechanism test identified.|
|27|src/search.cpp|1230-1332|+91/-4|Fused capture generation and capture-history scoring|NONE: NONE|Enabled in actual build; No per-use independent mechanism test identified.|
|28|src/search.cpp|1340-1563|+194/-16|Fused quiet generation and per-piece history/continuation scoring|NONE: NONE|Enabled in actual build; Job11 S-B1/B2/B4 independently validates accepted/rejected quiet legality and returned check/copies, NOT list completeness/order or quiet score. Broad equal trees not counted as generator-reference coverage.|
|29|src/search.cpp|1568-1583|+7/-6|Per-worker reusable evasion/picker scratch replacing stack-owned lists|NONE: NONE|Enabled in actual build; No per-use independent mechanism test identified.|
|30|src/search.cpp|1635-1658|+11/-10|Mark illegal tied-evasion slots Move::none instead of deferred legality mask|NONE: NONE|Enabled in actual build; No per-use independent mechanism test identified.|
|31|src/search.cpp|1687-1711|+14/-13|Clear integer history tables with memset and reusable threat readiness|PARTIAL_OR_DIRECT: Job9 ucinewgame command path|Enabled; intended value-preserving implementation; Job9 establishes stop-before-clear and observable protocol path, not direct byte-wise old/new history table comparison|
|32|src/search.cpp|1748-1760|+3/-3|Dead-material cheap guard and per-search NNUE active snapshots|NONE: NONE|Enabled in actual build; Job7/8 backend transition/eval evidence partly applies to snapshots; no independent per-use dead-material guard proof in requested jobs9-11.|
|33|src/search.cpp|1819-1829|+3/-1|Cache material-correction index in stack and invalidate on capture/promotion|NONE: NONE|Enabled in actual build; No per-use independent mechanism test identified.|
|34|src/search.cpp|1831-1838|+2/-2|Snapshot v3 backend, prepare once, direct king-square fast accumulator branch|PARTIAL_OR_DIRECT: Job8 shadow per-eval independent full rebuild (prior additional evidence)|Enabled V3 build; runtime NNUEArch only; Job8 checks every observed v3 result; specific branch counts not separated; unobserved nets/buckets remain uncovered|
|35|src/search.cpp|1867-1881|+3/-2|Propagate material correction index across null and snapshot v3 invalidation|NONE: NONE|Enabled in actual build; Job8 shadow covers resulting observed v3 evaluations, not correction-index identity; retain NONE for mixed material-index mechanism|
|36|src/search.cpp|1883-1909|+13/-2|Cache material-correction index in stack and invalidate on capture/promotion|NONE: NONE|Enabled in actual build; No per-use independent mechanism test identified.|
|37|src/search.cpp|1965-1976|+6/-1|Cache material-correction index in stack and invalidate on capture/promotion|NONE: NONE|Enabled in actual build; No per-use independent mechanism test identified.|
|38|src/search.cpp|2100-2106|+1/-1|Lazily produce/invalidate HistRework threat maps and piece-specific reads|NONE: NONE|Enabled in actual build; No per-use independent mechanism test identified.|
|39|src/search.cpp|2121-2127|+1/-2|Lazily produce/invalidate HistRework threat maps and piece-specific reads|NONE: NONE|Enabled in actual build; No per-use independent mechanism test identified.|
|40|src/search.cpp|2255-2261|+1/-1|Single-worker node-only stop shortcut, and initialize its eligibility|NONE: NONE|Enabled in actual build; Job10/11 S2 trees exercise softnodes and match outcomes, not per-call independent stop-predicate reference; no direct mechanism counter|
|41|src/search.cpp|2277-2283|+1/-1|Worker TT call sites use lightweight probe type|NONE: NONE|Enabled in actual build; No per-use independent mechanism test identified.|
|42|src/search.cpp|2325-2333|+2/-2|Lazily produce/invalidate HistRework threat maps and piece-specific reads|NONE: NONE|Enabled in actual build; No per-use independent mechanism test identified.|
|43|src/search.cpp|2336-2345|+2/-0|Pass already-known givescheck and precomputed childkey to make_move|PARTIAL_OR_DIRECT: Job10 B5/B6 counters; Job11 retained B5/B6|Enabled PREFETCH_EARLY=1; Every used known0 compared compute_checkers and supplied key compared incremental shadow on W1/S2; no independent test of unused hint classes|
|44|src/search.cpp|2358-2369|+2/-1|Pass already-known givescheck and precomputed childkey to make_move|PARTIAL_OR_DIRECT: Job10 B5/B6 counters; Job11 retained B5/B6|Enabled PREFETCH_EARLY=1; Every used known0 compared compute_checkers and supplied key compared incremental shadow on W1/S2; no independent test of unused hint classes|
|45|src/search.cpp|2407-2413|+1/-1|Single-worker node-only stop shortcut, and initialize its eligibility|NONE: NONE|Enabled in actual build; Job10/11 S2 trees exercise softnodes and match outcomes, not per-call independent stop-predicate reference; no direct mechanism counter|
|46|src/search.cpp|2437-2443|+1/-1|Worker TT call sites use lightweight probe type|NONE: NONE|Enabled in actual build; No per-use independent mechanism test identified.|
|47|src/search.cpp|2679-2686|+2/-2|Lazily produce/invalidate HistRework threat maps and piece-specific reads|NONE: NONE|Enabled in actual build; No per-use independent mechanism test identified.|
|48|src/search.cpp|2722-2728|+1/-1|Quiet legality/check cached at return and consumed by search|PARTIAL_OR_DIRECT: Job10 B1-B4; Job11 S-B1/S-B2/S-B4|Enabled KING_LINES=1; Direct per-use piece-array oracle for quiet legality/check/copies on W1 and20games; not generator completeness or all-position proof|
|49|src/search.cpp|2877-2889|+3/-1|Pass already-known givescheck and precomputed childkey to make_move|PARTIAL_OR_DIRECT: Job10 B5/B6 counters; Job11 retained B5/B6|Enabled PREFETCH_EARLY=1; Every used known0 compared compute_checkers and supplied key compared incremental shadow on W1/S2; no independent test of unused hint classes|
|50|src/search.cpp|3138-3151|+8/-0|Snapshot backend active state and prepare v3 state at search entry|PARTIAL_OR_DIRECT: Job9 stop-before-option ordering; Job7/8 backend replay (additional)|Enabled V3; per-search runtime active condition; Source lifetime proof plus transition replay; not all concurrent direct C++ clients|
|51|src/search.cpp|3337-3343|+1/-1|Worker TT call sites use lightweight probe type|NONE: NONE|Enabled in actual build; No per-use independent mechanism test identified.|
|52|src/search.cpp|3383-3394|+4/-1|Single-worker node-only stop shortcut, and initialize its eligibility|NONE: NONE|Enabled in actual build; Job10/11 S2 trees exercise softnodes and match outcomes, not per-call independent stop-predicate reference; no direct mechanism counter|
|53|src/search.cpp|3851-3859|+3/-1|Move root board into main Worker when no helpers|PARTIAL_OR_DIRECT: Job9 copy/worker ownership source audit|Enabled nohelper branch; Source ownership proof; broad tree equality only, not standalone moved-from state assertion|
|54|src/search.cpp|3872-3882|+5/-3|Snapshot v3 backend, prepare once, direct king-square fast accumulator branch|PARTIAL_OR_DIRECT: Job8 shadow per-eval independent full rebuild (prior additional evidence)|Enabled V3 build; runtime NNUEArch only; Job8 checks every observed v3 result; specific branch counts not separated; unobserved nets/buckets remain uncovered|
|55|src/search.cpp|3886-3922|+27/-19|Snapshot v3 backend, prepare once, direct king-square fast accumulator branch|PARTIAL_OR_DIRECT: Job8 shadow per-eval independent full rebuild (prior additional evidence)|Enabled V3 build; runtime NNUEArch only; Job8 checks every observed v3 result; specific branch counts not separated; unobserved nets/buckets remain uncovered|
|56|src/uci.cpp|43-153|+86/-23|Replace PositionCache representation and tokenizer/prefix matching with string_views|DIRECT: Job9 PartA26 sequential parser/cache cases plus PartB own whitespace/prefix/malformed cases compare r15d/kF outputs; includes raw/fallback prefix classes. Finite tests, not arbitrary byte/locale proof.|active; Job9 PartA26 sequential parser/cache cases plus PartB own whitespace/prefix/malformed cases compare r15d/kF outputs; includes raw/fallback prefix classes. Finite tests, not arbitrary byte/locale proof.|
|57|src/uci.cpp|158-220|+34/-12|Canonical move append and stack32/heap token collection for go parsing|DIRECT: Job9 PartB includes32/33-token and >32 searchmoves cases, illegal suffix retention and signed/overflow grammar; source path table.|active; Job9 PartB includes32/33-token and >32 searchmoves cases, illegal suffix retention and signed/overflow grammar; source path table.|
|58|src/uci.cpp|222-239|+5/-5|Use string_view take_integer/int reader and token_count|DIRECT: Job9 PartB malformed/missing keyword value and signed overflowing integer cases, outputs matched r15d.|active GO_PARSE=1; Job9 PartB malformed/missing keyword value and signed overflowing integer cases, outputs matched r15d.|
|59|src/uci.cpp|247-253|+1/-1|Clock token view instead of owning string|PARTIAL: Job9 parser boundary/read-through includes same parse_clock_ms call; fixed-depth/node tests do not independently exhaust clock range/timing.|active GO_PARSE=1; Job9 parser boundary/read-through includes same parse_clock_ms call; fixed-depth/node tests do not independently exhaust clock range/timing.|
|60|src/uci.cpp|258-264|+1/-1|Node/softnode count token view|DIRECT: Job9 PartB signed/overflow/zero/repeated limit cases; r15d and kF compared.|active GO_PARSE=1; Job9 PartB signed/overflow/zero/repeated limit cases; r15d and kF compared.|
|61|src/uci.cpp|308-314|+1/-1|searchmoves loop bounds use token_count|DIRECT: Job9 >32-token searchmoves and keyword termination cases matched r15d.|active GO_PARSE=1; Job9 >32-token searchmoves and keyword termination cases matched r15d.|
|62|src/uci.cpp|318-342|+7/-9|Legacy go parser view/count conversion and remove comment|OFF: Entire changed legacy reader under #else FORGE_FIX_GO_PARSE; original macro defaults1 in both builds, no runtime effect here.|off GO_PARSE=1; Entire changed legacy reader under #else FORGE_FIX_GO_PARSE; original macro defaults1 in both builds, no runtime effect here.|
|63|src/uci.cpp|357-363|+1/-1|Legacy searchmoves loop bound conversion|OFF: Inside legacy #else FORGE_FIX_GO_PARSE, not executed in measured builds.|off GO_PARSE=1; Inside legacy #else FORGE_FIX_GO_PARSE, not executed in measured builds.|
|64|src/uci.cpp|416-434|+5/-3|Reuse persistent task and copy Board/three task fields rather than move whole task|PARTIAL: Job9 PartC source concurrency/lifetime audit and repeated UCI command runs; no independent race/future-field completeness proof. Source assignment exactly3 existing fields.|active; Job9 PartC source concurrency/lifetime audit and repeated UCI command runs; no independent race/future-field completeness proof. Source assignment exactly3 existing fields.|
|65|src/uci.cpp|494-501|+2/-3|Top-level command parse uses string_view tokenizer|DIRECT: Job9 PartA/B command whitespace including tabs/VT/FF/CR, perft/search dispatch outputs compared; custom locales not tested.|active; Job9 PartA/B command whitespace including tabs/VT/FF/CR, perft/search dispatch outputs compared; custom locales not tested.|
|66|src/uci.cpp|577-587|+3/-2|Reset new cache fields and localize setoption stringstream|DIRECT: Job9 ucinewgame/position sequences and option-driven setup exercised; Job7 W2 independently observed ucinewgame resets board. Option parser remainder unchanged.|active; Job9 ucinewgame/position sequences and option-driven setup exercised; Job7 W2 independently observed ucinewgame resets board. Option parser remainder unchanged.|
|67|src/uci.cpp|820-826|+1/-1|Dispatch position to new view parser|DIRECT: Job9 all26 sequential cases plus focused14 compare board/perft/search diagnostics; mapping records post-error retained positions.|active; Job9 all26 sequential cases plus focused14 compare board/perft/search diagnostics; mapping records post-error retained positions.|
|68|src/uci.cpp|830-840|+3/-5|Perft command/depth peek via view instead of stream seek|DIRECT: Job9 PartA perft and malformed/whitespace paths; Job10 six perft known answers. Does not prove all possible invalid depth strings.|active; Job9 PartA perft and malformed/whitespace paths; Job10 six perft known answers. Does not prove all possible invalid depth strings.|
|69|src/uci.cpp|857-863|+1/-3|Dispatch go view parser instead of rewinding stream|DIRECT: Job9 depth/node/searchmoves/missing/overflow/>32 token tests compare outputs.|active; Job9 depth/node/searchmoves/missing/overflow/>32 token tests compare outputs.|
|70|src/uci.cpp|929-938|+4/-1|Bench depth gets its own remainder stringstream|PARTIAL: Repeated defaultbench11/13 known gates exercise valid depths; no exhaustive malformedbench argument test. Formula/stream extraction retained.|active; Repeated defaultbench11/13 known gates exercise valid depths; no exhaustive malformedbench argument test. Formula/stream extraction retained.|
|71|include/forge/b4.hpp|37-62|+15/-9|Skip computing lesser-attack masks for absent friendly rooks/queens|NONE: NONE|Enabled in actual build; No per-use independent mechanism test identified.|
|72|include/forge/board.hpp|208-215|+2/-1|Declare optional make_move key and check arguments/defaults|DIRECT: Job10 B5/B6 at every actual supplied argument use; ordinary perft callers keep defaults. Corresponds implementationh4.|active; Job10 B5/B6 at every actual supplied argument use; ordinary perft callers keep defaults. Corresponds implementationh4.|
|73|include/forge/board.hpp|220-231|+6/-0|Expose ensure_king_lines refreshing accessor|DIRECT: Job11 S-B4 compares copied masks at every returned quiet, S-B7 restored valid fields; independent piece-array reference reads no cache.|active KING_LINES=1; Job11 S-B4 compares copied masks at every returned quiet, S-B7 restored valid fields; independent piece-array reference reads no cache.|
|74|include/forge/board.hpp|249-255|+1/-0|Expose const piece-bitboard array view|PARTIAL: Job8 independent fresh-reference output comparison covers reached NNUE borrowers; source accessor returns existing bitboards unchanged, no independent standalone accessor invariant counter.|active accessor; NNUE use needs loadednet; Job8 independent fresh-reference output comparison covers reached NNUE borrowers; source accessor returns existing bitboards unchanged, no independent standalone accessor invariant counter.|
|75|include/forge/eval.hpp|51-59|+3/-0|Add cheap heavy-piece/pawn prefilter for dead material recognition|NONE: No focused counter of prefilter vs full dead_material_score; original eval.cpp516-518 starts with identical rejection condition. Native default dead_material_enabled=false, but helper may have additional search callers.|conditional caller flags; helper itself compiled; No focused counter of prefilter vs full dead_material_score; original eval.cpp516-518 starts with identical rejection condition. Native default dead_material_enabled=false, but helper may have additional search callers.|
|76|include/forge/nnue_v3.hpp|173-185|+7/-1|Inline king-key orientation/bucket/flip expression|NO_BEHAVIOUR: Equivalent body moved from oldnnue_v3.cpp699-706 (h13); no formula change, valid square/net contract retained.|active; Equivalent body moved from oldnnue_v3.cpp699-706 (h13); no formula change, valid square/net contract retained.|
|77|include/forge/nnue_v3.hpp|217-227|+5/-0|Declare fused one-refresh evaluator|PARTIAL: Declaration for h15; Job8 global v3 shadow outputs, not dedicated fused-branch count.|active whenloadednet+XORbranch; Declaration for h15; Job8 global v3 shadow outputs, not dedicated fused-branch count.|
|78|include/forge/nnue_v3.hpp|272-293|+14/-9|Replay top-ply refresh directly from Board bitboards; reconstruct only older plies|PARTIAL: Job8 all fastv3 outputs checked independently from freshpiecepositions incl selfplay; no separate top/intermediate replay hit counts.|active loadedv3 refresh paths; Job8 all fastv3 outputs checked independently from freshpiecepositions incl selfplay; no separate top/intermediate replay hit counts.|
|79|include/forge/search.hpp|17-25|+3/-0|Include AVX512 intrinsic declarations|PARTIAL_OR_DIRECT: NO_BEHAVIOR|AVX512 enabled by x86-64-v4; Header inclusion itself adds no runtime branch|
|80|include/forge/search.hpp|132-149|+10/-0|Assert TT SIMD layout and add lightweight WorkerTTProbe type|PARTIAL_OR_DIRECT: NO_BEHAVIOR|Layout assertions active at compile; new type used by H18/82/85; Declaration alone no runtime computation; safety of omitted metadata tracked in H18/82/85|
|81|include/forge/search.hpp|206-218|+7/-0|Move TT metadata before stripe array|PARTIAL_OR_DIRECT: NO_BEHAVIOR|Enabled layout-only; No logical output change; cache locality/performance can change clocked timing|
|82|include/forge/search.hpp|226-299|+62/-4|AVX512 owned TT probe and fast declarations; relocate metadata|NONE: NONE|Enabled in actual build; No per-use independent mechanism test identified.|
|83|include/forge/search.hpp|306-322|+6/-3|Factor unchanged cluster-index arithmetic into helper|PARTIAL_OR_DIRECT: NO_BEHAVIOR|Enabled uint128 native; Expression identical algebraically; helper extraction no logical change|
|84|include/forge/search.hpp|533-541|+2/-1|Cache material-correction index in stack and invalidate on capture/promotion|NONE: NONE|Enabled in actual build; No per-use independent mechanism test identified.|
|85|include/forge/search.hpp|645-694|+41/-9|Lazy threat/cache scratch fields, NNUE snapshots, TT-fast Worker dispatch|NONE: NONE|Enabled in actual build; No per-use independent mechanism test identified.|
|86|include/forge/search.hpp|731-745|+9/-0|Single-worker node-only stop shortcut, and initialize its eligibility|NONE: NONE|Enabled in actual build; Job10/11 S2 trees exercise softnodes and match outcomes, not per-call independent stop-predicate reference; no direct mechanism counter|

## Every search-read NONE facet: equality condition and distinguishing class

### H2 src/board.cpp:834-841 (3changedlines)
Condition: Excluded pawn/king attacked squares must always fail full own-king safety even after capture.
Input class: King capture onto pawn-defended square, capture of checking pawn, nearby enemyking; illegal synthetic king adjacency outside accepted-board contract.
Existing partial evidence/limit: Job10 B7/perft exercises move generation but no per-use independent early-mask counter; no inspected external report isolates this hunk.; Job10 B7/perft exercises move generation but no per-use independent early-mask counter; no inspected external report isolates this hunk.

### H3 src/board.cpp:852-872 (15changedlines)
Condition: When not in check, an off-king-ray pawn push/capture cannot expose ownking; no enemy geometric slider ray implies zero absolute pins.
Input class: Stalemate/nearly stalemated sparse position, pinned pawn, promotion push/capture, occupancy opening diagonal or file.
Existing partial evidence/limit: Job10/11 B2/S-B2 checks quiet picker, not has_legal_move early witnesses; broad node equality is not isolated coverage.; Job10/11 B2/S-B2 checks quiet picker, not has_legal_move early witnesses; broad node equality is not isolated coverage.

### H11 src/board.cpp:1516-1534 (14changedlines)
Condition: Contact+empty-board enemy slider-ray absence implies no first legal recapture and fullSEE result true.
Input class: EP removes blocker, origin vacates x-ray, promotionrecapture at backrank, pinned or defended king recapture.
Existing partial evidence/limit: Job10 B8 was source-read only, no SEE reference counter. External sol3 asserts reported by handoff but exact coverage not inspected here.; Job10 B8 was source-read only, no SEE reference counter. External sol3 asserts reported by handoff but exact coverage not inspected here.

### H12 src/board.cpp:1536-1564 (22changedlines)
Condition: Actual no-enemy-attacker gather must equal first r15d loop gather; factored live mask must exclude captured/origin pieces correctly.
Input class: EP/capture x-ray, blocked sliders becoming unblocked, pawn/king/contact-only recaptures; HOIST0 branch not in current build.
Existing partial evidence/limit: Job10 B8 source proof only; no local independent SEE loop comparison. HOIST0 pawn early-refutation is not in build; other added lines active.; Job10 B8 source proof only; no local independent SEE loop comparison. HOIST0 pawn early-refutation is not in build; other added lines active.

### H17 src/search.cpp:21-27 (2changedlines)
Condition: Only overwrites already-consumed prefix; bad_count <= consumed index; preserves bad-capture order
Input class: Capture-rich nodes, many losing captures, equal scoring moves
Existing partial evidence/limit: NONE; No per-use independent mechanism test identified.

### H18 src/search.cpp:525-661 (131changedlines)
Condition: Same first hit/empty/tie replacement, occupied bit layout, generation update, admission and move-preservation; no stale epoch/key misuse
Input class: Full collision clusters, generation wrap, same-key stale probe slot, rejected shallow store; locked multiworker races
Existing partial evidence/limit: NONE; No per-use independent mechanism test identified.

### H20 src/search.cpp:944-950 (3changedlines)
Condition: Preserve full pseudo-legal scored list and tie swaps, discard exactly same moves including promotions sharing from/to
Input class: Equal-score legal/illegal evasions, underpromotions, TT move amid ties
Existing partial evidence/limit: NONE; No per-use independent mechanism test identified.

### H24 src/search.cpp:1079-1085 (2changedlines)
Condition: Ready flag reset at each new node before any read; reused map belongs exact same board; pawn/minor fast subset exact
Input class: Same-ply singular searches, null/recursive return, HistRework on; queens/rooks absent then present
Existing partial evidence/limit: NONE; No per-use independent mechanism test identified.

### H25 src/search.cpp:1121-1173 (39changedlines)
Condition: Scored layout8bytes; lane extraction correct; strict > retains earliest tie; seeded/sorted states same
Input class: Ties at SIMD boundaries, lengths8/16, negative scores, seeded first entry
Existing partial evidence/limit: NONE; No per-use independent mechanism test identified.

### H26 src/search.cpp:1202-1212 (4changedlines)
Condition: Scored layout8bytes; lane extraction correct; strict > retains earliest tie; seeded/sorted states same
Input class: Ties at SIMD boundaries, lengths8/16, negative scores, seeded first entry
Existing partial evidence/limit: NONE; No per-use independent mechanism test identified.

### H27 src/search.cpp:1230-1332 (95changedlines)
Condition: Exact pseudo-legal move order/flags/promotions/EP and score formula match r15d list then score
Input class: Promotion pushes/captures/underpromotions, EP, slider occupancy and negative history
Existing partial evidence/limit: NONE; No per-use independent mechanism test identified.

### H28 src/search.cpp:1340-1563 (210changedlines)
Condition: Exact r15d pseudo-legal quiet list order and score incl HistRework integer rounding, continuation4 half, directcheck bonus, castling; fallback preserves features
Input class: Castling, doublepush, signed/tied history, HistRework2, ContHist4PlyRead, threat/pawn-history fallback
Existing partial evidence/limit: NONE; Job11 S-B1/B2/B4 independently validates accepted/rejected quiet legality and returned check/copies, NOT list completeness/order or quiet score. Broad equal trees not counted as generator-reference coverage.

### H29 src/search.cpp:1568-1583 (13changedlines)
Condition: Generation finishes copying/scoring before recursion can overwrite shared scratch
Input class: Nested evasion search and promotion ties
Existing partial evidence/limit: NONE; No per-use independent mechanism test identified.

### H30 src/search.cpp:1635-1658 (21changedlines)
Condition: Preserve full pseudo-legal scored list and tie swaps, discard exactly same moves including promotions sharing from/to
Input class: Equal-score legal/illegal evasions, underpromotions, TT move amid ties
Existing partial evidence/limit: NONE; No per-use independent mechanism test identified.

### H32 src/search.cpp:1748-1760 (6changedlines)
Condition: Guard supersets all dead-material cases; snapshots stable because option changes stop search
Input class: Unusual recognized endings and backend reload/disable transitions
Existing partial evidence/limit: NONE; Job7/8 backend transition/eval evidence partly applies to snapshots; no independent per-use dead-material guard proof in requested jobs9-11.

### H33 src/search.cpp:1819-1829 (4changedlines)
Condition: Material key unchanged only across noncapture/nonpromotion/null; validity reset correctly; cached index fits uint16
Input class: Pawn captures, EP, promotion and same-ply search reuse; MaterialCorrectionWeight>0 default100
Existing partial evidence/limit: NONE; No per-use independent mechanism test identified.

### H35 src/search.cpp:1867-1881 (5changedlines)
Condition: Null changes no material and backend state prepared before search
Input class: Null nodes with material-index valid/invalid and V3 on
Existing partial evidence/limit: NONE; Job8 shadow covers resulting observed v3 evaluations, not correction-index identity; retain NONE for mixed material-index mechanism

### H36 src/search.cpp:1883-1909 (15changedlines)
Condition: Material key unchanged only across noncapture/nonpromotion/null; validity reset correctly; cached index fits uint16
Input class: Pawn captures, EP, promotion and same-ply search reuse; MaterialCorrectionWeight>0 default100
Existing partial evidence/limit: NONE; No per-use independent mechanism test identified.

### H37 src/search.cpp:1965-1976 (7changedlines)
Condition: Material key unchanged only across noncapture/nonpromotion/null; validity reset correctly; cached index fits uint16
Input class: Pawn captures, EP, promotion and same-ply search reuse; MaterialCorrectionWeight>0 default100
Existing partial evidence/limit: NONE; No per-use independent mechanism test identified.

### H38 src/search.cpp:2100-2106 (2changedlines)
Condition: Ready flag reset at each new node before any read; reused map belongs exact same board; pawn/minor fast subset exact
Input class: Same-ply singular searches, null/recursive return, HistRework on; queens/rooks absent then present
Existing partial evidence/limit: NONE; No per-use independent mechanism test identified.

### H39 src/search.cpp:2121-2127 (3changedlines)
Condition: Ready flag reset at each new node before any read; reused map belongs exact same board; pawn/minor fast subset exact
Input class: Same-ply singular searches, null/recursive return, HistRework on; queens/rooks absent then present
Existing partial evidence/limit: NONE; No per-use independent mechanism test identified.

### H40 src/search.cpp:2255-2261 (2changedlines)
Condition: No helper/MultiPV pending nodes, clock absent, localnodes belowlimit and not cadence boundary: only sharedstop can trigger
Input class: Node budget1/1023/1024/1025, asynchronous stop, ponderhit, toggling clocked/node modes
Existing partial evidence/limit: NONE; Job10/11 S2 trees exercise softnodes and match outcomes, not per-call independent stop-predicate reference; no direct mechanism counter

### H41 src/search.cpp:2277-2283 (2changedlines)
Condition: Worker probe is scoped to same table/key/epoch; returned entry semantics match old probe
Input class: TT collisions, resize/clear boundaries, stale slot interactions
Existing partial evidence/limit: NONE; No per-use independent mechanism test identified.

### H42 src/search.cpp:2325-2333 (4changedlines)
Condition: Ready flag reset at each new node before any read; reused map belongs exact same board; pawn/minor fast subset exact
Input class: Same-ply singular searches, null/recursive return, HistRework on; queens/rooks absent then present
Existing partial evidence/limit: NONE; No per-use independent mechanism test identified.

### H45 src/search.cpp:2407-2413 (2changedlines)
Condition: No helper/MultiPV pending nodes, clock absent, localnodes belowlimit and not cadence boundary: only sharedstop can trigger
Input class: Node budget1/1023/1024/1025, asynchronous stop, ponderhit, toggling clocked/node modes
Existing partial evidence/limit: NONE; Job10/11 S2 trees exercise softnodes and match outcomes, not per-call independent stop-predicate reference; no direct mechanism counter

### H46 src/search.cpp:2437-2443 (2changedlines)
Condition: Worker probe is scoped to same table/key/epoch; returned entry semantics match old probe
Input class: TT collisions, resize/clear boundaries, stale slot interactions
Existing partial evidence/limit: NONE; No per-use independent mechanism test identified.

### H47 src/search.cpp:2679-2686 (4changedlines)
Condition: Ready flag reset at each new node before any read; reused map belongs exact same board; pawn/minor fast subset exact
Input class: Same-ply singular searches, null/recursive return, HistRework on; queens/rooks absent then present
Existing partial evidence/limit: NONE; No per-use independent mechanism test identified.

### H51 src/search.cpp:3337-3343 (2changedlines)
Condition: Worker probe is scoped to same table/key/epoch; returned entry semantics match old probe
Input class: TT collisions, resize/clear boundaries, stale slot interactions
Existing partial evidence/limit: NONE; No per-use independent mechanism test identified.

### H52 src/search.cpp:3383-3394 (5changedlines)
Condition: No helper/MultiPV pending nodes, clock absent, localnodes belowlimit and not cadence boundary: only sharedstop can trigger
Input class: Node budget1/1023/1024/1025, asynchronous stop, ponderhit, toggling clocked/node modes
Existing partial evidence/limit: NONE; Job10/11 S2 trees exercise softnodes and match outcomes, not per-call independent stop-predicate reference; no direct mechanism counter

### H71 include/forge/b4.hpp:37-62 (24changedlines)
Condition: Only read by_type for actually-present mover; no caller requests absent type
Input class: Queen promotion, cached map invalidation, synthetic requests for absent piece mask
Existing partial evidence/limit: NONE; No per-use independent mechanism test identified.

### H75 include/forge/eval.hpp:51-59 (3changedlines)
Condition: Full dead_material_score rejects every position containing pawn/rook/queen before changing score; caller must preserve that same condition.
Input class: Enable dead-material option, promotion/last-heavy-piece capture, mixed minor endings; stale piece bitboards or expanded recognition could break prefilter.
Existing partial evidence/limit: No focused counter of prefilter vs full dead_material_score; original eval.cpp516-518 starts with identical rejection condition. Native default dead_material_enabled=false, but helper may have additional search callers.; No focused counter of prefilter vs full dead_material_score; original eval.cpp516-518 starts with identical rejection condition. Native default dead_material_enabled=false, but helper may have additional search callers.

### H82 include/forge/search.hpp:226-299 (66changedlines)
Condition: Masks identify occupied key lane correctly; preserve earliest hit/empty/full replacement and generation updates
Input class: Full collisions, generationwrap, empty slots, AVX512 lane-layout
Existing partial evidence/limit: NONE; No per-use independent mechanism test identified.

### H84 include/forge/search.hpp:533-541 (3changedlines)
Condition: Material key unchanged only across noncapture/nonpromotion/null; validity reset correctly; cached index fits uint16
Input class: Pawn captures, EP, promotion and same-ply search reuse; MaterialCorrectionWeight>0 default100
Existing partial evidence/limit: NONE; No per-use independent mechanism test identified.

### H85 include/forge/search.hpp:645-694 (50changedlines)
Condition: All readiness resets and ownership proofs of related hunks hold; fast handle consumed before epoch mutation
Input class: Mixed HistRework recursion, reloaded net, owned/locked TT modes
Existing partial evidence/limit: NONE; No per-use independent mechanism test identified.

### H86 include/forge/search.hpp:731-745 (9changedlines)
Condition: No helper/MultiPV pending nodes, clock absent, localnodes belowlimit and not cadence boundary: only sharedstop can trigger
Input class: Node budget1/1023/1024/1025, asynchronous stop, ponderhit, toggling clocked/node modes
Existing partial evidence/limit: NONE; Job10/11 S2 trees exercise softnodes and match outcomes, not per-call independent stop-predicate reference; no direct mechanism counter

## 3. Part B: selected NONE facets, C-count3, gate and controls
All search-read NONE conditions/input classes are listed above. Sorting by added+removed changed lines gives H28=210 then H18=131; next H27=95,H82=66,H85=50. NNUEH15=138 is PARTIAL with direct Job8 fresh-eval reference, not NONE; therefore it does not displaceH18. H28's prior returned-move legality/check evidence does not establish generated-list completeness/order/scoring, so that uncovered facet remains selectable. The frozen map is historical pre-counter coverage; current overlay below adds new evidence without erasing residual gaps or silently rewriting prediction.

### Build and patch identity
C-count3=C-count2 plus H28/H18 observers; SHA2560139a55668552b92ef475b05e824a6430329d6bbe33f55e498cb1d8f385dd527. Wrong3 SHAb2acf7701667ff987c0e8a20e7ae1cf3dff273be29655858f1b5b5d8b3eff4fb; only FORGE_SHORTCUT_WRONG3=1, older wrong flags off. Both frozen before gates; verified build manifest date-u18:41:13Z. Earlier approximate internal messages are not used as clock evidence.
Full patch from originalkF C_count3_full.patch.txt SHA256e7567524617f969c962c2435de90b18405051908620b25cfe7f0e0c2dfaec973 (commit517836ea45277541d95c589b7fe15a65750cc7c0); C_wrong3_full.patch.txte9a4b328bb5dbe25ab215d5abe57e87061be08ccbb5b90d9b3255b79b97bc7c7 (a51110a3c1bf381880c61986a0da0fea5eb908f8). Alternative *_from_job11.patch.txt applies to Job11C-count2; do not stack full+incremental. Both full patches dry-run clean. No repository engine source changed.
GCC14.2.0/libstdc++.so.6.0.33/glibc2.41,CMake4.4.5,C++20Release -O3 -DNDEBUG -ffp-contract=off -fno-fast-math -march=x86-64-v4; FORGE_SHORTCUT_COUNT=1. Full flags/configure/build logs in build_manifest and corresponding logs. No timing/speed claim.

### H28 reference and its limits
At EVERY quiet-generation completion, generate_quiets wrapper compares a private old-path ordered scored list against fused implementation before selection. Reference uses old Board::generate_pseudo_legal(Quiets), copied r15d scalar QuietScorer/history arithmetic, independently rebuilt r15d lesser-threat maps and direct-check masks. It checks every Move (including flags), score, count, index/list-start/sorted flag and earliest-strict-max seed. Production arrays/decisions are not overwritten. One H28 use means one generation, not one returned move. This directly adds evidence for completeness/order/scoring at generation boundary; it does NOT instrument H25 later SIMD selection/tie swaps, all shared attack primitives or every nondefault option branch.
Control adds1 to first local reference quiet score only; with no quiet moves it need not differ. Observed control differs on every counted generation in first200 entries. This is deliberately wrong reference evidence, not an engine defect.

### H18 reference and its limits
All four added H18 functions have observer hooks: full-cluster replacement, locked fast probe, owned fast store, locked fast store. Reference is scalar r15d logic on private cluster snapshots; compares earliest strict-minimum replacement, first hit/empty/probe entry/slot/hit and cluster fields, or complete post-store cluster fields with stale-slot/admission/move-preservation rules. It never changes actual table or sample counters. H18 uses aggregate FUNCTION observations; one operation may invoke replacement plus probe, not a uniform node count. RequiredT1 profile may not reach locked paths; no per-subfunction counts emitted, so aggregate pass does not establish reach of every branch. Owned AVX512 probe is H82 and remains outside direct comparison except shared replacement function.
Original r15d handle owner/epoch/key validation is NOT independently recreated: fast API lacks TTProbe handle and observer assumes valid live worker-call context. Thus stale/foreign lifecycle handles remain a gap, not proven equivalent. sample_gen_counts_/hashfull deltas are also not independently compared. Current-node FEN is read via scoped thread-local BoardContext at root/main/quiescence; pointer restores on return, no dangling root guess. Store passes actual stored move; probe/replacement0000 means no individual move, not a chess nullmove. Calls outside Worker search are not counted. Control flips a bit of local reference selected-entry score, never real TT storage; replacement/probe reference itself unperturbed.

Detailed cross-review evidence:
UTC review stamp: 2026-11-18 18:40:49 UTC (date -u observed).
H18 snapshot oracle design and H28 independent source review

H18 original kF src/search.cpp 531-660 adds full-cluster replacement, locked fast probe, owned fast store, and locked fast store. The scratch implementation adds scalar reference helpers immediately before these functions. Reference algorithms were read from r15d search.cpp463-524 (probe) and533-588 (store). Full cluster replacement executes r15d's scalar earliest-strict-minimum loop. Probe operates on a local cluster copy, scans first occupied matching key, refreshes local generation only, else first empty/lowest replacement; result entry/cluster index/slot/hit and entire post-operation cluster are compared. Stores run original r15d first-matching-key scan and admission/move/payload logic on a local cluster copy, then compare all four entries' key, move, score, eval, depth, gen_bound, rule50_clock and padding. Oracle never writes actual TT, real sample counters or search state. Actual functions retain locking and original operation ordering. All reference code and hooks are guarded FORGE_SHORTCUT_COUNT.

Wrong3 positive control changes only local reference selected entry score with xor1 after reference store; this is an erroneous reference payload, not an unconditional differs flag or a change to search storage. Replacement/probe references are not deliberately faulted; positive control exercises the shared H18 counter through stores.

Diagnostic scope: thread_local BoardContext RAII at root Worker::search plus recursive main/quiescence functions restores previous pointer on exit. Current live node Board is read synchronously; store hook passes its actual move; probe/replacement use0000 because those operations have no move. Replacement passes key0 because this function receives only a cluster/generation; key is currently not printed. Do not interpret replacement/probe0000 as an actual chess move. No guessed root FEN is used.

Limits: sample_gen_counts_ deltas and hashfull values are NOT independently compared. Oracle does not reproduce r15d handle-owner/epoch/key validation because fast worker API has no such handle; valid worker-call contract only. No concurrency theorem: locked probe/store may have zero reach under required T1 tests; actual concurrent overwrite interleavings remain untested. No per-subfunction counters are emitted, H18 aggregates replacement/probe/store uses (so one search action can produce >1 hook). Reference compares legal table field values, not external invalid arguments or lifetime misuse.

H28 independent source audit: read scratch search.cpp1473-1590 and1592-1815, r15d search.cpp891-948 and1055-1097, original r15d include/forge/b4.hpp39-72, scratch push_scored/sort_moves1341-1353. QuietReferenceScorer reproduces r15d arithmetic/history reads and independently rebuilds current lesser-threat maps instead of taking cached threat_maps_. Direct-check squares are recomputed from enemy king/occupancy, with unused/King0. Reference moves come from Board::generate_pseudo_legal(Quiets), the old r15d path, separate from kF fused quiet generation. Comparator checks every initial move+score in order, count/index/list_start/sorted state, and earliest strict-max seed. sort_moves only marks list_start and sorted=false, so observing after it still compares initial generation order, not later selector sorting. No defect found in this comparison on source review. Wrong3 adds1 to first reference quiet score only and hence must change comparison when at least one quiet exists.

H28 limits: ordinary attack-table/generator helpers are shared with the engine, not a fully square-array move generator; this tests fused-generation equivalence to the old path, not absolute chess correctness of all shared primitives. Reference uses existing history tables and standard helper functions, not independently recomputed training history. H25 pick_best SIMD/tie ordering is not directly observed by this H28 hook. Nondefault threat/pawn-history and inactive macro paths need reach evidence, not inferred coverage.

Independent source review of H18 instrumentation: opened original r15d probe_body/store_body and diagnostic helper/hook bodies. Local scalar replacement retains first empty then lowest depth-4age with strict tie order. Locked probe reference compares snapshot entry, hit, slot, cluster and all four post-probe entries. Store reference independently re-finds first same key, applies stale-slot move preservation, admission rule, score/eval/depth/clock clamps and generation/bound flags; compare all logical fields of all four entries. Oracle writes only local TTCluster snapshot. Actual sample counters and table mutation execute unchanged. Full replacement, locked probe, owned store, locked store each add a use; locked full misses can contribute two uses. H82 owned SIMD hit/empty probe not itself instrumented; sample generation count bookkeeping not compared; old opaque-handle owner/epoch/key reject conditions not re-created because Worker fast handle has none, so valid-lifetime assumption remains. No multithread checker here. Current-position FEN comes from RAII Worker BoardContext at root/main/qsearch, safely restored on nested scope exit. For replacement/probe without associated move diagnostic0000; stores report supplied move. Reference control flips only snapshot selected score bit at store, not real table. No discovered mismatch in source review. Native per-use gate still required.

### Gate and controls
K1 fresh C-count3, PC20+net768,T1/H16, ucinewgame/isready before each depth9 search:1000entries/990distinct,16543291nodes, every row nodes/bestmove equalsJob7. All eight Job11 uses exactly preserved; independent QA compares every row, not only totals. K2 wrong3 first200entries/197distinct,4097080nodes, unchanged baseline rows and all old counters; H28 and H18 both detect their deliberate wrong reference. No gate or control stop condition triggered.
|Counter|K1 uses|K1 differences|K2 uses|K2 differences|
|---|---:|---:|---:|---:|
|B1|9079813|0|2564528|0|
|B2|9638809|0|2689044|0|
|B5|10935512|0|2607489|0|
|B6|15430637|0|3895460|0|
|S-B1|9079813|0|2564528|0|
|S-B2|9638809|0|2689044|0|
|S-B4|9079813|0|2564528|0|
|S-B7|15531178|0|3895323|0|
|H28|1376393|0|341487|341487|
|H18|9040060|0|2063485|2063485|

K2 process-first5 diagnostics, both new counters represented:
```
info string shortcut disagreement H18 premove_fen r1bq1rk1/1p2bppp/p3pn2/3pP3/2p2B2/2P1P2P/PP1NBPP1/R2Q1RK1 b - - 0 12 move 0000
info string shortcut disagreement H18 premove_fen r1bq1rk1/1p2bppp/p3pn2/3pB3/2pP4/2P1P2P/PP1NBPP1/R2Q1RK1 b - - 0 12 move 0000
info string shortcut disagreement H18 premove_fen r1bq1rk1/1p2bppp/p3pn2/3pn3/2pP1B2/2P1P2P/PP1NBPP1/R2Q1RK1 w - - 0 12 move 0000
info string shortcut disagreement H28 premove_fen r1bq1rk1/1p1nbppp/p3pn2/3pN3/2pP1B2/2P1P2P/PP1NBPP1/R2Q1RK1 b - - 0 11 move a6a5
info string shortcut disagreement H18 premove_fen r1bq1rk1/1p1nbppp/4pn2/p2pN3/2pP1B2/2P1P2P/PP1NBPP1/R2Q1RK1 w - - 0 12 move 0000
```

## 4. Prediction graded
Immutable commitefa9f176dfa8aa8889c8a7c72df9a1a9da9784cb after PartA and controls, before fresh S1 starts18:42:30Z. Predict35 NONE in unchanged pre-counter map:PASS (already known structural count, not blind). Predict S1 H28uses1.35–1.40million/H18uses8.9–9.2million,0differences; PASS, observed1376393/9040060,0. Predict S2 H28uses0.30–0.60million/H18uses2.5–3.8million,0differences; PASS, observed493901/2638740,0. S1 ranges explicitly K1-informed; S2 ranges from prior workload nodes and K1 ratios, not prior H28/H18 S2 observations. S1 was rerun after prediction although defined as gate workload, making ordering explicit.
Post-run overlay: H28 now has direct old-path ordered scored-list evidence for exercised branches; H18 now has direct snapshot-value evidence under valid worker-call contract. Residual limits above remain, so I do not claim only33 completely uncovered hunks or erase originalNONE35.

## 5. S1 and S2, every counter
S1 fresh1000entries/990distinct,16543291nodes, all baseline rows equal. S2 same20distinct starts and full move lists asJobs10/11:20terminal games,1370legal plies/searches,5612423actualnodes. Actual nodes from softnodes lines, not last finished-depth info. All old8 uses matchJob11 per ply; no first differing game/move. All10counters0differences. python-chess validates eachmove; ucinewgame/isready pergame, fullhistoryposition perply, go softnodes2000, stop game_over(claim_draw=True) or200plies. No game reachescap; max125plies.
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
|H28|1376393|0|none|493901|0|none|
|H18|9040060|0|none|2638740|0|none|

The optional per-game structured table is not published. Requested aggregate results and complete raw terminal transcripts are provided; detailed derived per-game records remain local under the no-dataset restriction.

## Facts, suspicions, not done and uncertainties
Facts:86/86hunks mapped;9changed files,1281additions/292deletions,35pre-counter NONE facets with conditions/classes. Two largest selected by exact changed-line count, not convenience. All required gates/controls/predictions pass; no new production disagreement in sampled workloads. Diagnostic code does not feed search decisions; tree/old-use equality supports logical invariance. First5 diagnostics shared globally across10counters/process; counts reset persearch, sample limit not reset. No source repair proposed.
Suspicions: remaining NONE mechanisms and partial facets listed in map are candidates for further targeted comparison, not confirmed bugs. No claim that broad game equality proves all source changes. Shared helper mistakes can evade old-path comparison; inputs outside valid-worker/generated-move assumptions remain boundaries.
What I did not do: instrument the other33 NONE hunks, H25laterselection, H82ownedprobe directly, H18lifecycle-invalid handles/sample-count bookkeeping/concurrent schedules; no per-subfunction reach counters, no full-independent board generator forH28, noall-option branches, noThreads>1, noPCnet/compiler, no performance/strength test, no macro-off rebuild. Did not independently read/reparse external sol2/sol3 raw reports; those claims remain Opus-reported context. Auxiliary record auditor still unavailable, not represented as run.
What I am not sure about: equivalence outside sampled positions/valid contracts, all reference-code correctness, unvisited branch coverage, concurrency, unrelated directlibraryclients or allocationfailure. Exact model identity unavailable/not guessed.

### What this check cannot see (verbatim)
Positions that W1 and the 20 games do not reach; the PC's net, compiler and build; more than one search thread.

## Inputs and publication provenance
PC20 exact options are in every raw transcript: Threads1,Hash16,OwnBookfalse,LmrQuietBase93,LmrQuietDivisor205,LmrNoisyBase13,LmrNoisyDivisor333,LmrHistoryDivisor5643,NullMoveBase5,LmpBase8,HistoryPruneMultiplier2220,HistoryBonusQuadratic24,HistoryBonusLinear54,HistoryBonusMax2212,SingularDepth6,IirDepth2,NonPawnCorrectiontrue,CuckooReptrue,HistRework2,TtPruneV2true,CorrHistV2true,MateAlphaGuardtrue.
Nethidden768 checksum30ab43b4ba5db5f3, SHA256c3d95131d7c1c89ccb5b000b52c7c37ed8665dbf8bb2a0a7a873809c85b9f7c7; W1 localinput SHA2563c1b17332eca46a912f572eae8197324f466a8e2f909653104c427457ffb0521. Neither standaloneinput committed. Source identity is base6b98f2170a3210e71beed04bbd2553972c253ed7 plus preserved r15d/kF/diagnostic patches, not basealone.
K1/K2/S1/S2 complete raw transcripts split into62consecutive <=100000byte parts, manifest includes whole-stream and per-part SHA256/size. Raw input/output is evidence, not a standalone position/game dataset; local rows/move lists remain local. Six Step0logs and exact source diff/map are separately committed. Publication verification/total size appended after completion. No PR or other branch modification.

## FOR FABLE AND OPUS
Complete map ready for PC line-by-line review. H28/H18 now have conditional direct evidence but residual gaps preserved; no new defect. Next sensible gaps by size include H27capturegeneration,H82ownedprobe,H85lazy/TTcomposite, though next job remains your choice. After report poll FABLE_TO_dot_13.md every2minutes for30minutes, first-lineSTOP and fresh final boundary respected.

## Independent raw and map QA
UTC 2026-11-18T18:43:34.787257+00:00
K1: raw reparse PASS 1000 searches, nodes 16543291, counters {'B1': {'uses': 9079813, 'differ': 0}, 'B2': {'uses': 9638809, 'differ': 0}, 'B5': {'uses': 10935512, 'differ': 0}, 'B6': {'uses': 15430637, 'differ': 0}, 'S-B1': {'uses': 9079813, 'differ': 0}, 'S-B2': {'uses': 9638809, 'differ': 0}, 'S-B4': {'uses': 9079813, 'differ': 0}, 'S-B7': {'uses': 15531178, 'differ': 0}, 'H28': {'uses': 1376393, 'differ': 0}, 'H18': {'uses': 9040060, 'differ': 0}}; diagnostics 0. All bestmoves legal.
K2: raw reparse PASS 200 searches, nodes 4097080, counters {'B1': {'uses': 2564528, 'differ': 0}, 'B2': {'uses': 2689044, 'differ': 0}, 'B5': {'uses': 2607489, 'differ': 0}, 'B6': {'uses': 3895460, 'differ': 0}, 'S-B1': {'uses': 2564528, 'differ': 0}, 'S-B2': {'uses': 2689044, 'differ': 0}, 'S-B4': {'uses': 2564528, 'differ': 0}, 'S-B7': {'uses': 3895323, 'differ': 0}, 'H28': {'uses': 341487, 'differ': 341487}, 'H18': {'uses': 2063485, 'differ': 2063485}}; diagnostics 5. All bestmoves legal.
S1: raw reparse PASS 1000 searches, nodes 16543291, counters {'B1': {'uses': 9079813, 'differ': 0}, 'B2': {'uses': 9638809, 'differ': 0}, 'B5': {'uses': 10935512, 'differ': 0}, 'B6': {'uses': 15430637, 'differ': 0}, 'S-B1': {'uses': 9079813, 'differ': 0}, 'S-B2': {'uses': 9638809, 'differ': 0}, 'S-B4': {'uses': 9079813, 'differ': 0}, 'S-B7': {'uses': 15531178, 'differ': 0}, 'H28': {'uses': 1376393, 'differ': 0}, 'H18': {'uses': 9040060, 'differ': 0}}; diagnostics 0. All bestmoves legal.
S2: raw reparse PASS 1370 searches, nodes 5612423, counters {'B1': {'uses': 3212417, 'differ': 0}, 'B2': {'uses': 3468791, 'differ': 0}, 'B5': {'uses': 4071447, 'differ': 0}, 'B6': {'uses': 5227491, 'differ': 0}, 'S-B1': {'uses': 3212417, 'differ': 0}, 'S-B2': {'uses': 3468791, 'differ': 0}, 'S-B4': {'uses': 3212417, 'differ': 0}, 'S-B7': {'uses': 5255554, 'differ': 0}, 'H28': {'uses': 493901, 'differ': 0}, 'H18': {'uses': 2638740, 'differ': 0}}; diagnostics 0. All bestmoves legal.
W1 verified 1000/990; S2 first20 DISTINCT verified against raw position commands, all1370 moves legal and all20 games terminal by claim_draw=True, maximum200plies respected. S2 actual-node line used, not lastdepth nodes. K1/K2/S1 every raw nodes/bestmove matches preserved Job7 baseline.
All old8 per-row uses match Job11 K1/K2/S1; old differences match except expected removal of Job11 K2 S-B1 fault. S2 full20games/moves plus all old8 per-ply values equal Job11. Both new controls fire with expected counts and both have retained diagnostic samples.
Map QA PASS: exact fresh diff bytes/digest match122872bytes,86hunks. IDs1..86 exactlyonce, allfiles/newranges/changedlinecounts match. File added/removed/hunk totals matchsummary. All86rows have nonemptycondition/inputclass;35NONE under explicit mechanism/facet definition, largestsearch-readNONE H28=210,H18=131. Broad samegames not substituted for mechanismcoverage.
Preserved source coverage gaps: H18 aggregate uses sum replacement, locked probe and owned/locked stores; no per-function reach breakdown. Owned SIMD probe H82 hit/empty is not independently checked, and hashfull sample-generation bookkeeping, omitted old TTProbe lifecycle owner/key/epoch guards, and multithread races remain outside oracle. Active Worker context is required and RAII covers root/main/qsearch. H28 compares ordered generation input and original scalar scores/seed metadata, not H25 SIMD selection/sort. References share original Board generator/attack helpers and histories, not independent chess-law proof. Runtime/compile-time unexercised feature paths remain unproved. New counter coverage does not retroactively change frozen pre-counter35NONE map. Controls are references-only; both H18 and H28 samples actually retained within global5 cap this run.

## Verified publication checkpoint and held optional artifact
2026-11-18T19:05:43Z:78permitted additional files individually full-body verified,6,090,510bytes,max100,000bytes,including all62rawparts. Earlier exactdiff/map/fullpatches/sixgate logs total271,773bytes. Even allowing100KB for finalreport and100KB for additionalmetadata, entirejob stays below6.7MB (limit20MB); largestfile100KB (limit5MB). publication_verified.json.txt records78successful per-file commits.
S2.summary.txt (21,503bytes) contains optional derived per-game records and was withheld under the no-dataset restriction. It was NOT retried, renamed or repackaged for upload. The optional per-game table was removed from this report too. Requested aggregate S1/S2 counter tables, source map and all raw terminal transcripts are published; detailed derived per-game records remain local. All other listed evidence succeeded. Local untracked summaries/row files are not claims of remote publication.

## Last shell command before report commit
`git status --short; ls -R forge-combo29/dot/job12`
Local preserved index does not reflect connector commits. Untracked files include intentionally local-only derived records; no assertion that all listed files are remote.
```
 M forge-combo29/dot/job2/stamps.txt
?? forge-combo29/REPORT_dot_job10.md
?? forge-combo29/REPORT_dot_job11.md
?? forge-combo29/REPORT_dot_job12.md
?? forge-combo29/REPORT_dot_job6.md
?? forge-combo29/REPORT_dot_job7.md
?? forge-combo29/REPORT_dot_job8.md
?? forge-combo29/REPORT_dot_job9.md
?? forge-combo29/dot/job10/
?? forge-combo29/dot/job11/
?? forge-combo29/dot/job12/
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
forge-combo29/dot/job12:
C_count3_build.txt
C_count3_configure.txt
C_count3_from_job11.patch.txt
C_count3_full.patch.txt
C_wrong3_build.txt
C_wrong3_configure.txt
C_wrong3_from_job11.patch.txt
C_wrong3_full.patch.txt
H18_cross_review.txt
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
TT_design_H28_review.txt
build_manifest.txt
diff.part001.txt
diff.part002.txt
diff_provenance.txt
gate_summary.txt
gate_validation.txt
hunk_map.md
independent_QA.txt
kf_bench_11.raw.txt
kf_bench_13.raw.txt
kf_go_perft_5.raw.txt
local_finding_record.json.txt
map_summary.txt
publication_status.txt
publication_verified.json.txt
r15d_bench_11.raw.txt
r15d_bench_13.raw.txt
r15d_go_perft_5.raw.txt
r15d_vs_kF.diff.txt
raw
raw_manifest.json.txt

forge-combo29/dot/job12/raw:
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
K1.part016.txt
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
S1.part016.txt
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
S2.part026.txt
```
