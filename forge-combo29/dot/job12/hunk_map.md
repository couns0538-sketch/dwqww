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
