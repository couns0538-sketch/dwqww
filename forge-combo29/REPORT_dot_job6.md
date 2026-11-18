# dot Job 6: carbon2 final speed-stack source audit

1. **Step 0 PASS.** Both Release binaries match all five pins; r15d matches all 29 source hashes; all three patches applied cleanly without fuzz, offset or reject.
2. **Step 1: 35 invariant rows.** Known answers (a), (b), (c) met. No missing guarantee demonstrated within the inspected legal-position UCI/current-build contract; this is not an exhaustive proof of all inputs. Full table below, committed before tests.
3. **Prediction: PASS for all five controls.** Immutable prediction commit `5cf12f7815225cb49ca3c49544e316e45d59a955`; Step1 commit `570a0bae4980da6f98d4fbc530165d283c42cc62`. Predicted zero NOT-guaranteed rows within stated scope and equal final search fields for C1–C5; observed matches. Performance fields excluded as predicted.
4. **Step 2: five guaranteed controls, one run per binary/input.** All complete depth10. C1 has an explicit12000-node ceiling but completes at8569: it tests fast-path eligibility, NOT a cap-boundary stop. Full inputs and last-info/bestmove below.
5. **NOT-guaranteed path list:** no such row established within inspected legal-position UCI paths. Outside the guarantee: arbitrary external C++ concurrent resize/net mutation, forged Move/DirtyPieces/Net objects, locale-modifying host applications, unprovided external-client ABI compatibility, other compilers/ABIs, and unidentified paths. These exclusions are not proven safe and are not disguised as dynamically tested.

## Build and evidence identity
Claim stamp: 2026-11-18T15:19:29Z. Both five-pin sets complete15:21:53Z. Prediction published before Step2 at observed15:30:16Z; Step2 completed by15:30:53Z. All paired raw transcripts, Step1 and Step2 bundle full-body read back and matched by15:33:03Z. No minute50 cutoff reached; no more experiments planned.

r15d: fresh plain PCr15 base6b98f217 plus named speed and E1 patches; 29-file SHA256 check PASS. kF: r15d plus job17 stack SHA256 `3d2ce085a8b76478942d4e29d7a74512eb3ecd2d328d224e27f711a48e46cb30`, nine files. Trees built outside repository; no source edits committed.
GNU C++14.2.0, libstdc++.so.6.0.33, glibc2.41; C++20 Release O3/NDEBUG, strict floating point, -march=x86-64-v4; FORGE_SEARCH_SPEED2=1, FORGE_MATE_ALPHA_GUARD=1, FORGE_NNUE_V3=1, FORGE_EXPOSE_TUNABLES=1. Effective compile commands, clean patch logs, source hash checks, ISA definitions and pin summaries are in [step0_bundle.txt](dot/job6/step0_bundle.txt). Full verbose build logs remain local; relevant exact compile lines are in that committed bundle. No performance conclusion from these short runs.

r15d executable SHA256 `bb37ed7c50e1716c5fc38f1b2fb92293c18e98f6131bf2be2b13d668603b4fc6`.
kF executable SHA256 `340f78f4e4834a5bf1e6dc2d73eca3caa62b7a45d05011b5c1c092ace6e5e5ea`.
Each binary, fresh process per pin: default bench11=312866 nodes; bench13=862329; startpos perft5=4865609. PC20 bench11=278024; bench13=587276. Raw logs: [r15d](dot/job6/r15d_gate.raw.txt), [kF](dot/job6/kf_gate.raw.txt). Harness labels say PCA_default/PCA_PC20 from reuse, but actual binary paths/SHA prove these are r15d/kF, not PCA.

PC20 settings and all handshake/setoption input are preserved verbatim below and in each paired raw file. OwnBook=false; Threads1; Hash16; built-in evaluator, no external net loaded or NNUEArch requested. SIMD macros __AVX512F__, __AVX512BW__, __BMI2__ are defined and processor supports them. V3-specific rows08 and12 remain reading-only: builtin results do not validate loaded-v3 fusion.

## Step 1 full table
# Job 6 Step 1 reading table (before Step 2)

Scope: actual kF source, legal-position UCI paths, loader-accepted nets, current x86/GCC/libstdc++ build. GUARANTEED means an inspected source/caller argument, not exhaustive testing or a universal safety certificate. No demonstrated NOT-guaranteed row in this scope. Unprovided external C++ calls/custom locales/invalid objects/concurrent unsynchronized setters, other ABIs and unknown paths are excluded explicitly rather than silently asserted safe. All requested modes are traced below; not all will be run.

Order inspected/reported: 11,12,13,tidy,01–10. The actual stack uses job14 stop_hot, job15 v3_refresh_fuse, job16 tt_avx512_fast_probe and job17 tidy. Discarded candidate fast_has_legal_move and cuckoo parity patches are NOT this stack.

Effective build defines __AVX512F__=1, __AVX512BW__=1, __BMI2__=1 with -march=x86-64-v4; CPU supports them (step0_bundle.txt). SIMD branches can execute. V3-specific rows12a–e and08.1–3 are nevertheless READING ONLY because Step2 uses built-in evaluation, with no loaded/requested v3 net. Scalar SIMD alternatives are reading-only. Debug shadow-key check and inactive SEE_HOIST #else are not executed.

SHARED PATH / LIFETIME MAP (applies to each row where named; this avoids silently omitting mode variants)
M1 ordinary/main: uci.cpp:893-899 copies Board into pending_task and moves owning SearchLimits, under stop_mutex; :425-431 copies Board/moves limits into worker task and calls Searcher::search. Searcher::search :3854-3856 invokes Worker::search with a by-value Board. Main picker :2684/:2714-2727; qsearch picker :2332-2369; ProbCut picker :2641-2659. Each next() completes synchronous stage generation before caller recurses. SearchStack and per-worker histories/scratch belong to that Worker.
M2 Threads >1: search.cpp:3767-3772 creates distinct unique_ptr<Worker>; :3847-3851 launches one thread per helper with Board captured by value and workers_[i]->search; :3860 joins all helpers before Searcher::search returns. Scratch, maps, v3 state and correction indices are not shared between Workers. Shared TT is separate, outside 01..10's scratch argument. Same deterministic search output is not promised across T>1 schedules.
M3 MultiPV: search.cpp:3844-3847 suppresses helpers when multipv>1; :3451-3460 creates separate alt_shared and alt_worker; :3590-3608 narrows allowed root moves, clears alternate worker, calls its top-level search, which redoes snapshot/initialization. No nested concurrent use of parent scratch. Alternate worker has its own state even though it consults parent budget.
M4 searchmoves: uci.cpp:310-314 (FORGE_FIX_GO_PARSE path) / :358-363 (other path) obtains Board::parse_uci candidates; board.cpp:1412-1414 validates pseudo-legality and legality. search.cpp:3133-3134 snapshots restrictions, :3190-3197 intersects with legal root candidates, :2715-2720 filters candidates before make_move. Does not introduce a separate move maker, cache, or generator. Empty restriction handled by M8.
M5 infinite/stop and ponder: uci.cpp:432-436 waits after search for stop/ponderhit before publishing. stop_search :459-472 signals searcher.stop and waits for worker_busy=false; worker marks that only after search return and output (:451-455). Stop/quit :974-977 and ponderhit :964-972 do not mutate nets/Board/scratch. The Worker unwinds ordinary child make/unmake before its abort return (qsearch :2369-2371, main :2947 and following). New commands changing state call stop_search before mutation. Thus early stops do not leave borrowed parser views or scratch alive for a later command.
M6 hash resize / Threads / net options / ucinewgame: uci.cpp:582-583 stops before all setoption handling, Hash :809 and Threads :812 then mutate. ucinewgame :574-581 stops, searcher.clear(), resets Board and position cache. Searcher::clear :3789-3792 clears TT and every Worker; Worker::clear :1687-1709 resets histories, maps and stack. Resizing itself does not change Board. Public C++ setters are not internally synchronized against arbitrary callers; that is an API precondition, not a reachable concurrent UCI path.
M7 position / long history / specials: uci.cpp:821-823 stops before apply_position_sv; :170-182 parses legal moves and uses make_move with default nullptr/-1 arguments. Key history is copied with Board, grows via board.cpp:1297 and restores via :1305, null :1358/:1365. Long position strings are owning std::string at uci.cpp:494-498, canonical cache owning std::string at :48. Position does not retain string_views beyond the call. EP, promotion and castling cases are described per row.
M8 no legal move: search.cpp:3295-3310 handles root_candidates.empty() before iterative search, returns mate if legal.empty()&&in_check (:3297), and no best move yields "0000" at uci.cpp:438-439. In-check descendant qsearch returns mated_in on no moves (:2386); picker empty-evasion list :1581-1584 sets count=0. No fabricated move passed to make_move. Restricted empty roots use same terminal path. This bypasses stage generation rather than weakening an invariant.


| Row/piece | Relied-on invariant | kF quotes and source guarantees | Reaching paths | Status | Check or no-check reason |
|---|---|---|---|---|---|
| 11a | Single-worker node count and absence of hidden deadlines | search.cpp:3386–3388: "parent_worker_ == nullptr && multipv == 1" plus one-worker, node-limit, no-empty-reserve and hard_limit_ms_<=0 guards. search.cpp:2017–2024 total_nodes is local_nodes plus other worker publications; none exist under guard. search.hpp:735–742 checks shared stop each fast-path node, full should_stop at cap or every1024. search.cpp:2027–2052 contains the skipped predicates. | M1–M8 below. searchmoves filters roots only (search.cpp:3190–3197); no-legal root returns before flag setup. T>1, MultiPV alternates/parents fail guard. Softnodes hardcap is precomputed at3157–3167. | GUARANTEED for inspected UCI paths: node sum equals local and extra_nodes remains zero for MultiPV1. Clocked search is excluded, external stop is retained. | C1 node-capped fixed-depth search; other modes reading-only, not claimed dynamically covered. |
| 11b | Ponderhit cannot introduce an untested clock after flag snapshot | search.cpp:3170–3186 computes clock limits before flag; search.hpp:765–769 ponderhit only stores ponder_hit_ns; should_stop_with2039–2050 consults it without changing limits. | M5 plus M1–M4/M6–M8. Timed ponder already has hard_limit_ms>0 and so uses fallback. Untimed ponder cannot become clocked through ponderhit. Infinite has no clock and explicit cap follows existing semantics. | GUARANTEED by immutable per-search hard limit and timestamp-only ponderhit. | No check: timing/ponder path source-only; C1 tests node path, not timed behavior. |
| 12a | Exactly one king-key unchanged and a valid immediate parent; child is distinct storage. | search.cpp:3884 tests 'index > 4 && ...valid_flags[index - 1] != 0'; 3907 tests '(key0 == parent.keys[0]) != (key1 == parent.keys[1])'; 3909–3911 passes parent and stack[index] to apply_one_refresh_one_and_evaluate. nnue_v3.cpp:912 selects incremental perspective using key0 equality, so the XOR is essential. Same-king and both-unchanged cases use apply_pair; both-changed or non-immediate ancestry uses make_valid (search.cpp:3891–3927). | All reaching callers are enumerated in evidence and shared M1–M8; legal special moves/long position histories and separate helper/MultiPV state included. | GUARANTEED at the sole inspected engine caller. Main search/qsearch/ProbCut all evaluate through static_evaluate -> static_evaluate_v3 (search.cpp:1755–1757); no user command directly calls fused helper. MultiPV, searchmoves, infinite/stop, ponder and helpers do not bypass this guard. No legal move returns from Worker::search before this path (3295ff). | no check: builtin-evaluation scope does not load/request a v3 net, so this function is not executed. A v3 net whose king buckets differ across a king move would be needed for a dynamic check; not performed or claimed. |
| 12b | Dirty changes faithfully encode a single legal move, max four changes; current board equals the frame being evaluated. | search.cpp:1740–1744 lazy dirty_from_move; record_move:1827–1835 records pre-move piece/capture/side and invalidates child's validity flag. Call sites 2359/2362 (qsearch), 2651/2653 (ProbCut), 2878/2882 (main) record before board.make_move; null at2600/2602 calls record_null_move, whose1873–1878 sets 'dirty.count = 0' and invalidates. nnue.cpp:535–550 removes mover, removes capture (EP square corrected at539), adds promoted or original piece, and castle adds two rook changes. Legal castle is noncapture: ordinary2, capture/EP/promotion-capture3, castle4, null0. collect_changes nnue_v3.cpp:198–212 uses columns[4], relying on that contract. | All reaching callers are enumerated in evidence and shared M1–M8; legal special moves/long position histories and separate helper/MultiPV state included. | GUARANTEED for generated/legal engine moves including EP/castle/promotion/null. Searchmoves filters roots, not dirty encoding. Position move lists build the root before search; search.cpp:3423 invalidates state per search. Arbitrary caller-supplied contradictory flags (castle plus capture) are outside inspected UCI path. | no check for fused NNUE path under builtin scope. Builtin EP/castle/promotion controls do NOT validate fused evaluation. |
| 12c | Refresh diff buffers have at most32 entries individually; cached and current placements are each <=32 pieces. | nnue_v3.cpp:927–941 and1046–1060 arrays 'subs[32]'/'adds[32]' append one removed/added occupied square respectively. board.cpp:277–289 sums piece inventory per side and rejects 'total > 16' (also impossible promotions/pawn counts). Thus even accepted FEN is capped at32, not merely assumed reachable from startpos. Legal moves never create an additional piece (promotion replaces pawn). prepare:825–829 initializes each cache entry to empty piece set; fusion:943 and refresh:1062 replace cached bitboards with current placement. | All reaching callers are enumerated in evidence and shared M1–M8; legal special moves/long position histories and separate helper/MultiPV state included. | GUARANTEED for accepted UCI positions and legal descendants. A long legal position moves list cannot increase beyond32. Cache retains a past legal placement, so removed <=32 and added <=32 even when union has up to64. | no NNUE check with builtin evaluation. Invalid >32-piece FEN need not be tested to establish buffer safety because parser explicitly rejects it. |
| 12d | All aligned SIMD loads/stores address64-byte-aligned storage and hidden length a multiple32; arithmetic agrees with unfused scalar formula. | nnue_v3.cpp:520–528 allocates/frees with 'std::align_val_t{64}'; nnue_v3.hpp:120 accumulator and133 cache values are alignas(64); C++20 vector respects element alignment. Column address185–186 is w1 + feature*hidden. Loader nnue_v3.cpp:592–594 enforces hidden32..1024 multiple32, so each int16 column and both perspective halves/each output bucket begin on64-byte boundary. Loop973 steps h+=32. Loader595–630 checks king/output buckets/maps, 662 checks &#124;w2&#124;<=127, 663–664 enforces max&#124;b1&#124;+32*max&#124;w1&#124;<=32767. Fusion1019–1028 clamps to0..255, uses same SCReLU products; largest int16 product255*127=32385. The combined AVX512 int32 lane covers at most128 SCReLU terms across two perspectives at hidden1024; 128*255*255*127 = 1057046400 < 2^31. Reduction nnue_v3.cpp:152–157 converts32-bit halves to64-bit before final reduction. Actually AVX512 has16 int32 lanes, each lane has2 input terms per32-lane chunk and32 chunks perperspective, hence128 terms total across both perspectives; 128*65025*127 < 2^31. The weaker256-term bound is also below2^31. Refresh order subtracts removed then adds new in both r15d and kF. Every intermediate subset has <=32 pieces; fusion reorder is per-hidden lane, not a change in per-lane term order. | All reaching callers are enumerated in evidence and shared M1–M8; legal special moves/long position histories and separate helper/MultiPV state included. | GUARANTEED for loader-accepted nets and caller storage. ISA AVX512 route compiled on this build but builtin scope never reaches it. Scalar #else reading-only. No net speed, alignment stress, or numerical experiment performed. | no check, loaded v3 net unavailable by prescribed builtin scope. |
| 12e | Cache/net generations and thread lifetimes are coherent; top shortcut needs no undo, intermediate refresh must undo later plies. | prepare nnue_v3.cpp:815–834 rebuilds on generation/size change; loader666 increments generation; search3143–3146 snapshots active loaded net and prepares; search3423 invalidates every search. uci.cpp:674 and690 call stop_search before architecture or file load/unload; stop_search459–474 waits '!worker_busy' before returning. Mutation cannot free active net while a worker uses it. Each Worker owns v3_state; MultiPV allocates separate Worker atsearch3457–3459; Threads>1 helpers call their own workers at3848–3850. Newgame/hash resize do not mutate live state due UCI stop serialization (parent shared mode map). nnue_v3.hpp:276–289 uses current board directly only if 'k == top'; otherwise copies bitboards and reverses all dirty changes from top down to k+1. make_valid:298–308 passes index as top consistently. Null has no dirty changes; castle/EP/promotion encoded as12b. | All reaching callers are enumerated in evidence and shared M1–M8; legal special moves/long position histories and separate helper/MultiPV state included. | GUARANTEED for serialized UCI engine call paths. Infinite/stop and ponder only alter stop/timing and do not mutate board during an evaluation. Direct unsynchronized external load/unload calls are not covered by the UCI guarantee. | no check under builtin eval. Reload, NNUE generations and branch reconstruction have not been dynamically checked here. |
| 13a | 64-byte aligned whole-cluster read and correct lane masks | search.hpp:131 "struct alignas(64) TTCluster";134–138 asserts entry16, key offset0, depth12/gen_bound13, cluster64; search.cpp:450 make_unique<TTCluster[]> (C++20 build, aligned new sinceC++17). search.hpp:246 loads aligned512;247–249 masks keys0x1111 and occupied0x8888 with0x300. gen_bound bits0..1 define Bound at90–106; x86 little-endian puts these at bits8..9 of lane3. ctz only on nonzero at250–263. search.cpp:582–587 uses same matcher for store. | All TT probe/store callers via Worker wrappers search.hpp:680–689, both search/qsearch; M1–M8. Castle/EP/promotion only affect keys, not storage alignment. | GUARANTEED on this x86 build: lowest occupied matching slot equals scalar first match; first empty slot equals scalar first empty; full replacement unchanged. Known answer(b) met. | C2 castle/searchmoves exercises ordinary owned TT; no instrumentation proving every collision/lane outcome. |
| 13b | Exclusive cluster lifetime and synchronization | search.hpp:680–681 "tt_owned_ ? ...probe_owned_fast... : ...probe_locked_fast". search.cpp:3821–3836 lease only for workers.size()==1 or MultiPV>1, scoped flag restored.3844–3851 prevents helpers for MultiPV. uci.cpp:459–474 stop_search waits worker completion;575/583 stop before newgame/setoption (Hash resize809). | M1–M8; Threads>1 locks, MultiPV only main owns lease and alternate owns separate TT. Stop/ponder changes atomics only. Long positions mutate main Board only after join. No-legal root releases scoped lease on return. | GUARANTEED for serialized UCI mutation. Arbitrary direct C++ concurrent resize is not internally promised, outside this UCI guarantee. | C5 serialized Hash32->16, Threads2->1 (no active T2 run), ucinewgame and MultiPV2; concurrent T2 behavior reading-only. |
| tidy | Removed data/accessors have no remaining production caller; whitespace has no semantics | kF board.hpp:223–228 retains ensure_king_lines, no cached_king_lines accessor. search.hpp:218–220 retains Worker friendship; src/search.cpp:955–964 retains only used picker caches;1346–1354 no quiet epoch assignment. Whole include/src identifier search finds zero occurrences of removed cached_king_lines, S13TTTestAccess, quiet_hist_epoch_, quiet_gen_epoch_, last_quiet_history_, has_cached_quiet_history, cached_quiet_history. Whitespace-only sites search.cpp:2538,2606,2994 inspected. | All compiled production paths M1–M8 have no caller to deleted items. No external headers/clients supplied. | GUARANTEED runtime deletion of dead storage/accessors for this tree; NOT an ABI/source-compatibility guarantee to unprovided external C++ clients. This is a scope limitation, not a failing UCI row. | No separate run: C1–C5 whole-stack controls include tidy; no external-client ABI test. |
| 01.1 | Worker scratch lifetime | Relied on: search.cpp:1572-1573 "MoveList& buf = searcher_.picker_scratch_;" / "MoveList& non_tt = searcher_.evasion_scratch_;"; fallback :1323-1340 and :1353-1361, :1532-1567. Declared per Worker search.hpp:650-651, not static/thread_local. Guarantee: next :847-849/:882-884/:940-942 finishes generation before returning; generate_evasions copies each selected move+score into picker-owned moves_ (:1616-1623 or :1650-1653). MovePicker retains no buf iterator/reference across return except references local to generation. Child recursion only occurs after next returns (M1). T>1/MultiPV use distinct Workers (M2/M3); M4/M5 merely filter or stop; M6 clears after join. No-legal M8 uses zero count. | M1–M8 and exact per-row callers in evidence column. | GUARANTEED within the stated legal-position UCI/build contract; named caveats in evidence are not claimed proven outside it. | Selected controls only: fixed depth with checks/evasions, MultiPV2 plus T2/T1 transitions; compare deterministic T1 final nodes/PV. No separate scratch oracle run by reviewer. Actual selection C1–C5 below; other suggestions NOT run. |
| 01.2 | Losing-capture prefix | search.cpp:24 "#define FORGE_SDK_BADCAP_PREFIX 1" activates inherited blocks :856-860, :921-924, :999-1006, :1225-1229. GoodCaptures :853 "const Move move = pick_best();" then :858 "moves_[bad_count_++].move = move;". pick_best_scored :1130/:1205 increments index before return. Starting both counts zero, each bad capture corresponds to an already-popped candidate, so bad_count<=index, and write index bad_count_old is strictly below index. Quiet generation starts at quiet_start()==bad_count (:1349-1350), preserving prefix; BadCaptures reads only bad_index<bad_count. The written prefix score is intentionally irrelevant; only .move is read at :922. Applies M1-M8 wherever stage reached, including skip_quiets (preserves prefix; no quiet generation). | M1–M8 and exact per-row callers in evidence column. | GUARANTEED within the stated legal-position UCI/build contract; named caveats in evidence are not claimed proven outside it. | Selected controls only: position with both winning and losing captures plus quiets; full picker sequence oracle would be stronger than a depth result. Guarantee covers prefix non-overwrite, not a new proof that all possible malformed FENs fit fixed 256 slots. Actual selection C1–C5 below; other suggestions NOT run. |
| 01.3 | Evasion tie tagging | search.cpp:1651 "const int sc = score_evasion(move);" then :1652 "... ? move : Move::none();" then :1653 "push_scored(tagged, sc);". :947 skips none after selection; sorting comparator :1201 inspects only score and first four picks :1126; seeded winner :1211-1216 also uses only scores. Thus tagging does not change comparison outcomes or swaps for the same library implementation. Legal_mask from actual non-TT evasions :1641-1643. Promotions sharing from/to are all legal or all illegal with respect to own-king exposure; tagged TT promotion variants still excluded by exact move comparison in :947. M1/M2/M3 check-evasion path; M4/M5 do not change scoring; M8 zero/single paths :1581-1590 bypass sort. | M1–M8 and exact per-row callers in evidence column. | GUARANTEED within the stated legal-position UCI/build contract; named caveats in evidence are not claimed proven outside it. | Selected controls only: in-check position with tied legal quiet evasions and illegal pseudo-legal candidates, including promotion variants. Cannot promise equal unspecified std::sort tie order across different standard-library implementations; comparison is same build/library r15d vs kF. Actual selection C1–C5 below; other suggestions NOT run. |
| 01.extra | AVX512 score layout and leftmost max | search.cpp:1137 "static_assert(sizeof(Scored) == 8"; :1139 odd_idx16 selects score lanes; :1140/:1152 bounds require 16/8 remaining records, :1145/:1161 strict greater and ctz of equality mask preserves lowest index. Scalar remainder :1190-1197 same strict comparison. A cross-compiler layout contract also needs the inspected Scored definition :972-975 (Move then int); size assert alone would not prove offset on arbitrary ABI. Ordinary project x86 ABI expected, but this is a build-specific proof. Parent must label AVX512 read-only if absent from its build. | M1–M8 and exact per-row callers in evidence column. | GUARANTEED within the stated legal-position UCI/build contract; named caveats in evidence are not claimed proven outside it. | Selected controls only: existing all-stage test with long tied capture list; no separate run here. Actual selection C1–C5 below; other suggestions NOT run. |
| 02.1 | Precomputed key exactness | board.cpp:1255-1260 relies on caller pointer, quote "key_ = *precomputed_key;". Search callers only :2351-2363 and :2869-2883, passing "early_key ? &child_key : nullptr" after key_after. board.cpp:1144 excludes an existing EP square and EP moves; :1146-1148 excludes double pushes with adjacent enemy pawn. Otherwise :1152-1162 XORs removed/added/captured/promoted piece terms, castle rook terms, castling masks and side exactly as make_move :1207-1279. No EP-file term needed on admitted path. Special case NOTE README incorrectly suggests king/castling returns false: code handles castling explicitly :1154-1159, ordinary king uses castling mask :1161. ProbCut :2653, UCI position :180, perft :852, book reply :877 call default nullptr and full path. M2/M3 each owns Board/key local; M4/M5 filter/unwind normally; M6 serialized; M7 long history unaffected; M8 no call. | M1–M8 and exact per-row callers in evidence column. | GUARANTEED within the stated legal-position UCI/build contract; named caveats in evidence are not claimed proven outside it. | Selected controls only: fixed-depth legal castle, rook-capture-changing-rights, promotion, double push with and without adjacent enemy pawn, legal/pinned EP cases; direct key oracle can compare pointer and null paths but is outside requested short UCI controls. Actual selection C1–C5 below; other suggestions NOT run. |
| 02.2 | Lazy KingLines Undo | board.cpp:1182-1183 "if (king_lines_.valid) undo.king_lines = king_lines_; else undo.king_lines.valid = false;"; restoration :1334-1335, null :1346-1347/:1373-1374. Field readers search.cpp:1029-1032 use ensure_king_lines (board.hpp:225 refreshes); inline is_legal/gives_check board.hpp:338/:349 refresh; complete counterparts board.cpp:908/:1037 refresh; evasions :767-770 and has_legal_move :863-867 explicitly choose fresh computation if invalid. Writes invalidate after make/null :1299/:1360, set_fen candidate :363; refresh :1070-1088 sets every field before valid=true. No unguarded field read found by entire KingLines identifier search. M1-M8 pass through these accesses. | M1–M8 and exact per-row callers in evidence column. | GUARANTEED within the stated legal-position UCI/build contract; named caveats in evidence are not claimed proven outside it. | Selected controls only: alternate moves that never request lines with moves that request both check and legality; EP/castle/unmake plus ucinewgame; depth result cannot separately expose stale unused fields. README's exact byte count is ABI-dependent, not required for correctness. Actual selection C1–C5 below; other suggestions NOT run. |
| 03.1 | Debug-only shadow Zobrist | board.cpp:1186-1191,1201-1203,1208-1210,1217-1219,1227-1229,1232-1234,1245-1247,1252-1254,1261-1267 all wrapped #ifndef NDEBUG. Last quote :1266 "assert(key_ == dbg_key);". Incremental terms mirror both special and ordinary moves listed 02.1; assertion only when precomputed pointer provided. CMakeLists.txt:27-28 defines NDEBUG (independent of build type), so parent must verify effective -UNDEBUG ordering if wanting this active. M1 ordinary/qsearch admitted pointers; other paths/default pointer don't invoke final assertion. All UCI modes same. | M1–M8 and exact per-row callers in evidence column. | GUARANTEED within the stated legal-position UCI/build contract; named caveats in evidence are not claimed proven outside it. | Selected controls only: No check: release builds compile this verification out; ordinary Release equality tests cannot exercise corruption detection. A debug injected wrong key would require a separate nonproduction harness, not performed. Actual selection C1–C5 below; other suggestions NOT run. |
| 04.1 | Whitespace equivalence | uci.cpp:51-64 "return c == ' ' &#124;&#124; c == '\\t' &#124;&#124; c == '\\n' &#124;&#124; c == '\\r' &#124;&#124; c == '\\v' &#124;&#124; c == '\\f';" and token slices. These are classic C-locale whitespace, which is the relevant default; no setlocale/locale::global calls found in source grep. Command dispatch :497-498 and position/go parsers use this. Outer getline still separates LF commands (same framing, cannot embed literal LF within one command). All M1-M8 command modes admitted identically at token layer. Direct embedding with a custom global C++ locale is NOT guaranteed equivalent, but not a standard UCI-input reachable change. | M1–M8 and exact per-row callers in evidence column. | GUARANTEED within the stated legal-position UCI/build contract; named caveats in evidence are not claimed proven outside it. | Selected controls only: tabs, CR/VT/FF, repeated spaces around startpos/moves/go options. No guarantee advertised for locale-modifying host programs. Actual selection C1–C5 below; other suggestions NOT run. |
| 04.2 | Prefix-cache Board/history | uci.cpp:97-109 same_root checks root form/all FEN tokens; :118-120 matches full canonical prefix with token-boundary condition; :124-137 falls back to token comparison; :141-168 rebuild on mismatch. Each successful parse/make :173-182 appends only applied tokens. Bad move returns after prior legal moves with identical diagnostic :174-177. NOTE invalid FEN :153-155 retains previous Board/cache, rather than literally rebuilding a clean board as README wording may suggest. All command mutations of persistent Board were searched: ucinewgame resets cache :578-581; search tasks copy Board :893/:425; perft makes/unmakes :852-854; book reply uses copy :875-877. Therefore long repeated-prefix histories preserve repetition history, not just FEN. M7 owns cache; M5/M6 stop before mutation; M4 go parsing only reads Board. | M1–M8 and exact per-row callers in evidence column. | GUARANTEED within the stated legal-position UCI/build contract; named caveats in evidence are not claimed proven outside it. | Selected controls only: long reversible move prefix; repeat with tabs; extend; shorten; change root; illegal tail and invalid FEN then a valid extension. A full key_history comparison is stronger than UCI final search output. Actual selection C1–C5 below; other suggestions NOT run. |
| 04.3 | Zero clearing preserves table values | search.cpp:1690-1708 memset only nested primitive integer arrays/maps; types search.hpp:474,477,490-492,497 and b4.hpp:35-36,111-114. Counter moves use fill({}) :1698, SearchStack uses assignment SearchStack{} :1709, not byte-zero pointer-rich stack. PawnHistory compile/time guard :1693-1695 inherited; no selective v1/threat dirty flags. M6 ucinewgame -> Searcher::clear :3791 -> all Worker::clear; new Worker constructor :1682 also clears, alternate MultiPV :3607 clears. Guaranteed for targeted integer representations; no assumption that arbitrary structs may be memset to their default value. | M1–M8 and exact per-row callers in evidence column. | GUARANTEED within the stated legal-position UCI/build contract; named caveats in evidence are not claimed proven outside it. | Selected controls only: dirty histories with search, ucinewgame, repeat same fixed-depth search versus fresh process; T resize creates initialized workers. Actual selection C1–C5 below; other suggestions NOT run. |
| 04.extra | Parser views / reused SearchTask | uci.cpp:195-211 stores <=32 token views on stack, otherwise copies all32 to vector and appends remaining tokens; parse finishes synchronously before line changes. Returned limits contain parsed values/Move objects, not string views. :425-427 copies pending Board, moves limits into task while locked; later commands stop before rewriting pending. Scope M1-M7 including infinite and ponder finished-but-waiting worker (M5). | M1–M8 and exact per-row callers in evidence column. | GUARANTEED within the stated legal-position UCI/build contract; named caveats in evidence are not claimed proven outside it. | Selected controls only: >32-token go line plus searchmoves; position list >2048 characters to exercise owned canonical storage growth. No check for unbounded allocation failure/resource exhaustion. Actual selection C1–C5 below; other suggestions NOT run. |
| 05.1 | Dead-material candidate guard | search.cpp:1751/:1889 "dead_material_enabled && has_dead_material_candidates(board)" before dead_material_score. eval.hpp:54-56 predicate matches eval.cpp:518 "if ((board.pieces(Pawn) &#124; board.pieces(Rook) &#124; board.pieces(Queen)) != 0) return false;". Therefore early false cannot hide a recognized score. All ordinary/qsearch evaluation and corrected-eval callers, all M1-M8; no-legal roots bypass eval. | M1–M8 and exact per-row callers in evidence column. | GUARANTEED within the stated legal-position UCI/build contract; named caveats in evidence are not claimed proven outside it. | Selected controls only: KK, KBK, KNNK, KBNK plus a pawn/rook/queen; fixed-depth result checks selected paths only. No separate test needed to prove duplicate first predicate. Actual selection C1–C5 below; other suggestions NOT run. |
| 05.2 | Cached material correction index | search.cpp:1898-1904 computes when bit8 absent, otherwise trusts corr_mat_idx; :1969-1971 update uses same valid bit/fallback. material_key :1714-1721 hashes ONLY Pawn..Queen counts of each color, not literally all12 counts as README says (kings excluded). record_move :1822 "if (captured != Empty &#124;&#124; move.is_promotion()) keep &= ...(~8U);" else copies index :1823; null :1869-1872 copies unchanged. captured_piece handles EP (board.hpp:271 onward), promotion changes type even on quiet push; castling changes no count. Startup :3419 sets corr_valid=0; clear default search.hpp:537 zero. Calls qsearch :2359, ProbCut :2651, main :2878 and null :2600 before every child. M2/M3 independent stacks; M4/M5 no skipped record; M6 fresh/cleared stack; M7 new top-level snapshot; M8 no read. | M1–M8 and exact per-row callers in evidence column. | GUARANTEED within the stated legal-position UCI/build contract; named caveats in evidence are not claimed proven outside it. | Selected controls only: promotion, EP, ordinary capture, quiet/castle and null-producing depth; MaterialCorrectionWeight>0 needed for consumption. In legal chess no king capture enters, so excluded king counts do not invalidate proof. Actual selection C1–C5 below; other suggestions NOT run. |
| 06.1 | No enemy contact/ray implies no recapture | board.cpp:1518 computes postcapture occupancy, :1520 live0 excludes target, :1524-1529 contact/rays filtered to live enemy; :1530 "if ((them_contact &#124; them_ray_sliders) == 0) return true;". With swap>0 (:1515-1516), opponent's absence of geometric attackers ends same exchange walk. Empty-board slider rays overapproximate occupied-board attacks, so their absence is sufficient even with pins. EP removes captured_square and origin (:1496,:1518); promotion adjusts swap/attacker value :1510-1512 and promotion recapture edge returns earlier :1498-1505; castling returns before optimization :1492. Main GoodCaptures :855, qsearch :2348, ProbCut :2645 and other SEE consumers all use same board routine, across M1-M8. | M1–M8 and exact per-row callers in evidence column. | GUARANTEED within the stated legal-position UCI/build contract; named caveats in evidence are not claimed proven outside it. | Selected controls only: isolated capture, blocked-ray capture, en passant opening a slider, promotion threshold; only populated attacker cases test later loop. No threat-model beyond legal generated moves. Actual selection C1–C5 below; other suggestions NOT run. |
| 06.2 | Unified exact initial attackers | board.cpp:1552-1560 "Bitboard attackers = them_contact &#124; us_contact &#124; b_atk &#124; r_atk;"; :1554 uses exact occupied sliders filtered by them_live to detect no recapture. Old from/captured bits that can remain in us_contact/slider sets are removed by :1564 "attackers &= occupancy;" before per-side selection. Target occupant may appear in occupancy but no nonzero-piece attack function attacks its own target square. This equals old attacker enumeration under current occupancy. Caller/mode coverage same06.1. | M1–M8 and exact per-row callers in evidence column. | GUARANTEED within the stated legal-position UCI/build contract; named caveats in evidence are not claimed proven outside it. | Selected controls only: opposing pinned sliders/knights, x-ray reveal after exchange, contact attack blocked by king safety. The added #else pawn shortcut :1540-1548 is inactive with FORGE_SDK_SEE_HOIST default1; no default-build run can check it (known answer c). No assertion of its dynamic execution. Actual selection C1–C5 below; other suggestions NOT run. |
| 07.1 | Off-ray pawn existence | board.cpp:848 requires checkers_==0; :855-858 computes "safe_pawns = pieces(us, Pawn) & ~k_rays" and tests ordinary push/capture only. A nonking/non-EP move can expose own king only by removing a ray blocker; board.hpp:337-340 and board.cpp:904-910 encode same legal predicate. EP is not the early capture predicate because target is empty and excluded by them_occ; if no early witness, fallback :892-897 generates and tests all moves. A promotion witness is legal exactly as same pawn destination for own-king exposure. M1 descendant has_legal checks/terminal, M7 root legal generation paths, M8 stalemate must return false absent a witness; M2-M6 do not change Board predicate. | M1–M8 and exact per-row callers in evidence column. | GUARANTEED within the stated legal-position UCI/build contract; named caveats in evidence are not claimed proven outside it. | Selected controls only: legal off-ray pawn advance, pinned pawn only, EP-only escape and stalemate. Assumes legal position (no enemy king left in check by side-not-to-move); invalid FENs are not separately proved. Actual selection C1–C5 below; other suggestions NOT run. |
| 07.2 | King-evasion taboo | board.cpp:837-842 "taboo = pawn_attacks_bb(them, pieces(them, Pawn)) &#124; attacks::king(king_square(them));" subtracts guaranteed attacked targets before complete occupancy-based attack check. A pawn attacking to cannot occupy to, hence capturing on to cannot remove that pawn. Enemy king adjacency likewise cannot be legalized by such capture in a legal position. Remaining enemy slider/leaper attack test remains :841. Reach from all in-check MovePicker modes via :1575, and legal-evasion callers; no-legal M8 is a vital negative control. | M1–M8 and exact per-row callers in evidence column. | GUARANTEED within the stated legal-position UCI/build contract; named caveats in evidence are not claimed proven outside it. | Selected controls only: king capture of a pawn defended by a second pawn, adjacent king square, double-check evacuation. No proof for intentionally malformed adjacent-kings FENs. Actual selection C1–C5 below; other suggestions NOT run. |
| 07.3 | known_gives_check correctness/lifetime | board.cpp:1283-1285 "if (known_gives_check == 0) { checkers_ = 0; assert(compute_checkers() == 0); }"; nonzero/-1 recomputes :1287-1294. qsearch initializes -1 :2339, only supplies0/1 after actual Board::gives_check :2341-2342; main :2725 chooses cached QuietMoves or Board call, supplies :2880. TT/killers/counter/evasions do NOT falsely claim cached check (:960). Normal checks use validated KingLines board.hpp:348-356; special EP/castle/promotion use board.cpp:1042-1067, including removing EP pawn and shifting castle rook. ProbCut/UCI/perft default -1 full computation. Quiet fused path proven09.3. M2-M8 preserve local Board and call sequence. | M1–M8 and exact per-row callers in evidence column. | GUARANTEED within the stated legal-position UCI/build contract; named caveats in evidence are not claimed proven outside it. | Selected controls only: discovered quiet, direct quiet, castle rook check, EP discovered check, every promotion type. Release assert inactive; result equality not a direct checkers oracle. Actual selection C1–C5 below; other suggestions NOT run. |
| 08.1 | Per-search net snapshot / prepare | search.cpp:3141-3146 "nnue_active_ = nnue::enabled && nnue::available();" and "v3_active_net_ = ... nnue::v3::loaded() : nullptr;" then prepare. Consumers :1755-1757,:1826-1836,:1877-1879,:3875. UCI guarantee M6: all setoption stops at uci.cpp:583 before net replacement. M2 workers each snapshot stable global config, helpers joined before mutation; M3 alt Worker enters same setup; M4 restrictions no bypass; M5 ponderhit only time/stop state, never changes net; M7 position stops before next search; M8 prepare may occur with no evaluation, harmless. Public C++ net load/unload contract in nnue_v3.hpp:151 explicitly "must not run during a search"; no internal synchronization guarantees misuse. | M1–M8 and exact per-row callers in evidence column. | GUARANTEED within the stated legal-position UCI/build contract; named caveats in evidence are not claimed proven outside it. | Selected controls only: search infinite then setoption UseNNUE false/true (old search stopped first); v3 paths not dynamically covered by built-in-only Step2, so no check there: job intentionally uses built-in evaluation and PC net unavailable. Actual selection C1–C5 below; other suggestions NOT run. |
| 08.2 | Direct king squares / pure key | search.cpp:3889-3895 reads board.king_square; if equal parent.king_sq reuses parent.keys. king_key nnue_v3.hpp:176-181 depends only on net king_map/mirror and perspective/square. Board king move :1238 and unmake :1313 maintain king_squares; dirty_from_move nnue.cpp:535-550 removes/adds moved king, handles promotions and castle rook, EP captured square. record_move before every made child as05.2; null produces dirty.count=0 :1875. Root v3 evaluation :3423-3427 rebuilds after invalidate. MultiPV/newgame/T resize fresh or reset state through M2/M3/M6; M4/M5 retain board/stack consistency. | M1–M8 and exact per-row callers in evidence column. | GUARANTEED within the stated legal-position UCI/build contract; named caveats in evidence are not claimed proven outside it. | Selected controls only: v3 same-bucket king move, bucket crossing, castling, descendant after null. No dynamic check in built-in-only job; source argument, not net-specific evidence. Actual selection C1–C5 below; other suggestions NOT run. |
| 08.3 | Prepare/value initialization | nnue_v3.cpp:816 returns early if generation and stack size match; else :818-824 resizes and clears metadata/valid flags; :825-829 writes each entry bias and zero piece set. search.cpp:3423 "if (v3_state_) v3_state_->invalidate();" handles every later search even when prepare returned early. nnue_v3.hpp:299-308 only reads already-valid ancestors or refreshes entire current accumulator via refresh_cached; :1106-1115 writes both perspectives before valid. Entry values only hidden-width consumed; initialized copy is net.hidden. NOTE README's claim that zero initialization is completely skipped overstates code: new vector elements still have values{} in nnue_v3.hpp:120/:133, but redundant reassignment is avoided for existing payload. M2/M3 separate caches, M6 net generation changes triggers prepare, M8 no read before valid. | M1–M8 and exact per-row callers in evidence column. | GUARANTEED within the stated legal-position UCI/build contract; named caveats in evidence are not claimed proven outside it. | Selected controls only: consecutive v3 searches same net, net512->768->512, Threads resize. No check under built-in-only job; static lifetime/write-before-read reasoning only. Actual selection C1–C5 below; other suggestions NOT run. |
| 09.1 | Lazy lesser-threat lookup by extant moved type | b4.hpp:44-57 always sets Pawn/Knight/Bishop pawn threats, gates Rook on own R&#124;Q and Queen on ownQ; search.hpp:662 returns zero King/NoPiece, :665-669 computes pawn-only fast result or ensures map. Consumers search.cpp:2103,:2124 use board.moved_piece(move); QuietScorer :1089-1096 and fused rows :1406/:1446 use actually generated side-to-move pieces. No current-board R/Q move exists when that type absent; promotion is in captures, not quiet scorer. Invalidation before main picker :2683 and in-check qsearch :2328-2331; quiet-scoring ProbCut absent because noncheck quiescence generates captures only. Every history-update read after move unmake uses parent's same ply map; child writes its different ply. Same-ply singular search returns to same Board, so replacement map describes same position. T/MultiPV separation M2/M3, newgame clearing M6; long positions start new search. | M1–M8 and exact per-row callers in evidence column. | GUARANTEED within the stated legal-position UCI/build contract; named caveats in evidence are not claimed proven outside it. | Selected controls only: noR/noQ, rook-only, queen-only, promotion then next position, HistRework2. Definition b4.hpp:32-34 advertises general by_type semantics but optimized function only equivalent on actual-use types, not arbitrary external lookups for absent pieces. Actual selection C1–C5 below; other suggestions NOT run. |
| 09.2 | Fused move emission/scoring order | search.cpp:1264-1291 emits promotion pushes Q/R/B/N, pawn captures in from/to lsb order, EP; :1303-1320 N/B/R/Q/K captures. Quiets :1401-1436 regular single then double pushes; :1465-1496 N/B/R/Q/K targets; :1498-1527 castles K-side then Q-side. Compare board.cpp:467-518 promotions/pawns and :530-575 pieces/castles. Score capture formulas :1258-1261/:1278-1279/:1298-1300 match fallback :1331-1339. Quiets may fallback when ThreatHistory or PawnHistory compiled-on (:1353-1361), preserving features omitted from fused formula. Caller coverage all picker modes M1-M4; no legal M8 zero count; stop M5 interrupts between search work, not asynchronous mutation of lists. | M1–M8 and exact per-row callers in evidence column. | GUARANTEED within the stated legal-position UCI/build contract; named caveats in evidence are not claimed proven outside it. | Selected controls only: castling+promotions+EP positions, alternate ThreatHistory and HistRework2. Capacity assumptions unchanged (generated moves fit MoveList/256); no general invalid-FEN capacity proof supplied. Actual selection C1–C5 below; other suggestions NOT run. |
| 09.3 | Fused quiet legality/check | constructor search.cpp:826 routes in-check to Evasions, not QuietMoves. Quiet generator :1397-1400 excludes seventh-rank promotion pawns and :1469-1496 masks empty squares; EP only captures :1283-1289. QuietMoves :895-902 tests king via full legality, nonking via cached pins; :905-910 direct/discovered check with castle delegated to Board. init_check_squares :1029-1035 captures exact current board lines; parent Board is restored before picker resumes (M1). Promotions and captures never get cached QuietMoves classification; last_move_known_legal/cached flags :959-961 are stage-limited. Root restrictions skip after return but do not alter stage. M2/M3 isolated; M5 unmake before abort; M6 stops before mutation; M8 no yield. | M1–M8 and exact per-row callers in evidence column. | GUARANTEED within the stated legal-position UCI/build contract; named caveats in evidence are not claimed proven outside it. | Selected controls only: pinned quiet along vs off pin line, discovered check by king/knight/pawn, both castlings. Board::gives_check fast assumptions explicitly depend on legal position board.cpp:1032-1035; arbitrary illegal FEN not proved. Actual selection C1–C5 below; other suggestions NOT run. |
| 10.1 | Direct continuation row arithmetic | search.cpp:1380-1384 "int v = static_cast<int>(c1[to]) + static_cast<int>(c2[to]); if (c4 != nullptr) ... v += static_cast<int>(c4[to]) / 2; ... v += 12000;"; :1390-1393 binds rows using moved Piece and zero row fallback; zero row :1364 constexpr{}. Source QuietScorer :1072-1075 chooses same prior1/2/4 continuation pointers and ContHist4PlyRead/previous-move condition; old scalar quiet_history :2108-2111 same signed /2. Signed 16-bit values widened to int before sum, no signed16 overflow. Negative odd half truncates toward zero; equivalent to old SIMD sign correction, not arithmetic floor. Rows are worker-owned history arrays, used only during synchronous generation, never retained across child updates. No extra per-node array lifetime. M1-M8 same ownership map; root sentinel pointers initialized :3406. | M1–M8 and exact per-row callers in evidence column. | GUARANTEED within the stated legal-position UCI/build contract; named caveats in evidence are not claimed proven outside it. | Selected controls only: exercise negative odd 4-ply values with ContHist4PlyRead true plus HistRework2; simple zero-history depth output does not guarantee this corner reached. Built-in-only evaluation does reach move ordering, unlike v3-only rows. noinline affects call placement, not value contract; no separate semantic test necessary for attribute itself. Actual selection C1–C5 below; other suggestions NOT run. |
## Known answers
(a) MET: row01.2 cites all four activated inherited bad-capture blocks; pick_best pops before bad_count increments, preserving bad_count<=index. (b) MET: row13a alignment is guaranteed, not a defect. (c) MET: kF board.cpp:14–15 defines FORGE_SDK_SEE_HOIST1; added #else at1540–1548 is not compiled by these defaults; no dynamic check.

## Selected Step 2 controls (five guaranteed controls total)
C1 row11a: position startpos; go depth10 nodes12000 (node cap intentionally overrides completion depth).
C2 row13a/02.1: castle FEN r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1; go depth10 searchmoves e1g1 e1c1.
C3 row06.2 with special-move coverage: FEN 4k3/P7/8/3pP3/8/8/7p/4K3 w - d6 0 1; go depth10. EP and promotion branches exist; not a branch-coverage claim.
C4 row01.3: checked FEN r3k2r/ppp2ppp/2n5/8/8/2N5/PPP1rPPP/R3K2R w KQkq - 0 1; go depth10.
C5 row04.2 plus13b: legal long position cycle g1f3 g8f6 f3g1 f6g8 repeated110 times; reissue with tabs; extend e2e4; shorten to startpos moves e2e4; resize Hash32 then16, Threads2 then1; ucinewgame; MultiPV2; position startpos; go depth10 searchmoves e2e4 d2d4. Exact generated UCI input will be committed; no search is run on the long repeated root, only parser work. No active Threads2/infinite/ponder run is included.
All controls PC20, Threads1, Hash16, built-in eval; final last-info+bestmove nodes/score/depth/PV identity is predicted, NOT wall-clock time/NPS equality. One fresh process per binary/control. FENs and each long-list move validated by python-chess before search. No runs have been performed for Step2 at this commit.

## Step 2 observed results

| Input | r15d last-info nodes | kF last-info nodes | Bestmove both | Semantic equality |
|---|---:|---:|---|---|
| C1 | 8569 | 8569 | `bestmove d2d4` | True |
| C2 | 8852 | 8852 | `bestmove e1g1` | True |
| C3 | 13228 | 13228 | `bestmove a7a8q` | True |
| C4 | 33587 | 33587 | `bestmove e1e2` | True |
| C5 | 10511 | 10511 | `bestmove e2e4` | True |

Time/NPS differ and are not equality failures. For MultiPV C5, the last info is PV2, while bestmove is PV1 e2e4; this is reported as emitted, not a mismatch. All emitted lines remain in raw evidence.

### C1
Raw paired transcript: [dot/job6/C1_both.raw.txt](dot/job6/C1_both.raw.txt). Same commands sent separately to each fresh binary; actual tabs in C5 input retained.

```text
uci
setoption name Threads value 1
setoption name Hash value 16
setoption name OwnBook value false
setoption name LmrQuietBase value 93
setoption name LmrQuietDivisor value 205
setoption name LmrNoisyBase value 13
setoption name LmrNoisyDivisor value 333
setoption name LmrHistoryDivisor value 5643
setoption name NullMoveBase value 5
setoption name LmpBase value 8
setoption name HistoryPruneMultiplier value 2220
setoption name HistoryBonusQuadratic value 24
setoption name HistoryBonusLinear value 54
setoption name HistoryBonusMax value 2212
setoption name SingularDepth value 6
setoption name IirDepth value 2
setoption name NonPawnCorrection value true
setoption name CuckooRep value true
setoption name HistRework value 2
setoption name TtPruneV2 value true
setoption name CorrHistV2 value true
setoption name MateAlphaGuard value true
isready
position startpos
isready
go depth 10 nodes 12000
quit
```

r15d:
```text
info depth 10 seldepth 16 score cp 20 nodes 8569 nps 1071125 hashfull 3 time 8 pv d2d4 g8f6 c2c4 e7e6 g1f3 d7d5 e2e3 f8e7 c4d5 e6d5
bestmove d2d4
```

kF:
```text
info depth 10 seldepth 16 score cp 20 nodes 8569 nps 1224142 hashfull 3 time 7 pv d2d4 g8f6 c2c4 e7e6 g1f3 d7d5 e2e3 f8e7 c4d5 e6d5
bestmove d2d4
```

### C2
Raw paired transcript: [dot/job6/C2_both.raw.txt](dot/job6/C2_both.raw.txt). Same commands sent separately to each fresh binary; actual tabs in C5 input retained.

```text
uci
setoption name Threads value 1
setoption name Hash value 16
setoption name OwnBook value false
setoption name LmrQuietBase value 93
setoption name LmrQuietDivisor value 205
setoption name LmrNoisyBase value 13
setoption name LmrNoisyDivisor value 333
setoption name LmrHistoryDivisor value 5643
setoption name NullMoveBase value 5
setoption name LmpBase value 8
setoption name HistoryPruneMultiplier value 2220
setoption name HistoryBonusQuadratic value 24
setoption name HistoryBonusLinear value 54
setoption name HistoryBonusMax value 2212
setoption name SingularDepth value 6
setoption name IirDepth value 2
setoption name NonPawnCorrection value true
setoption name CuckooRep value true
setoption name HistRework value 2
setoption name TtPruneV2 value true
setoption name CorrHistV2 value true
setoption name MateAlphaGuard value true
isready
position fen r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1
isready
go depth 10 searchmoves e1g1 e1c1
quit
```

r15d:
```text
info depth 10 seldepth 16 score cp -9 nodes 8852 nps 1264571 hashfull 2 time 7 pv e1g1 a8a1 f1a1 e8d7 a1a2 d7c6 a2h2 h8e8 g1f2
bestmove e1g1
```

kF:
```text
info depth 10 seldepth 16 score cp -9 nodes 8852 nps 2213000 hashfull 2 time 4 pv e1g1 a8a1 f1a1 e8d7 a1a2 d7c6 a2h2 h8e8 g1f2
bestmove e1g1
```

### C3
Raw paired transcript: [dot/job6/C3_both.raw.txt](dot/job6/C3_both.raw.txt). Same commands sent separately to each fresh binary; actual tabs in C5 input retained.

```text
uci
setoption name Threads value 1
setoption name Hash value 16
setoption name OwnBook value false
setoption name LmrQuietBase value 93
setoption name LmrQuietDivisor value 205
setoption name LmrNoisyBase value 13
setoption name LmrNoisyDivisor value 333
setoption name LmrHistoryDivisor value 5643
setoption name NullMoveBase value 5
setoption name LmpBase value 8
setoption name HistoryPruneMultiplier value 2220
setoption name HistoryBonusQuadratic value 24
setoption name HistoryBonusLinear value 54
setoption name HistoryBonusMax value 2212
setoption name SingularDepth value 6
setoption name IirDepth value 2
setoption name NonPawnCorrection value true
setoption name CuckooRep value true
setoption name HistRework value 2
setoption name TtPruneV2 value true
setoption name CorrHistV2 value true
setoption name MateAlphaGuard value true
isready
position fen 4k3/P7/8/3pP3/8/8/7p/4K3 w - d6 0 1
isready
go depth 10
quit
```

r15d:
```text
info depth 10 seldepth 20 score cp 1624 nodes 13228 nps 1653500 hashfull 1 time 8 pv a7a8q e8e7 a8d5 e7e8 d5g2 e8e7 g2h2 e7e6 h2h5 e6e7 h5h1 e7e6
bestmove a7a8q
```

kF:
```text
info depth 10 seldepth 20 score cp 1624 nodes 13228 nps 2645600 hashfull 1 time 5 pv a7a8q e8e7 a8d5 e7e8 d5g2 e8e7 g2h2 e7e6 h2h5 e6e7 h5h1 e7e6
bestmove a7a8q
```

### C4
Raw paired transcript: [dot/job6/C4_both.raw.txt](dot/job6/C4_both.raw.txt). Same commands sent separately to each fresh binary; actual tabs in C5 input retained.

```text
uci
setoption name Threads value 1
setoption name Hash value 16
setoption name OwnBook value false
setoption name LmrQuietBase value 93
setoption name LmrQuietDivisor value 205
setoption name LmrNoisyBase value 13
setoption name LmrNoisyDivisor value 333
setoption name LmrHistoryDivisor value 5643
setoption name NullMoveBase value 5
setoption name LmpBase value 8
setoption name HistoryPruneMultiplier value 2220
setoption name HistoryBonusQuadratic value 24
setoption name HistoryBonusLinear value 54
setoption name HistoryBonusMax value 2212
setoption name SingularDepth value 6
setoption name IirDepth value 2
setoption name NonPawnCorrection value true
setoption name CuckooRep value true
setoption name HistRework value 2
setoption name TtPruneV2 value true
setoption name CorrHistV2 value true
setoption name MateAlphaGuard value true
isready
position fen r3k2r/ppp2ppp/2n5/8/8/2N5/PPP1rPPP/R3K2R w KQkq - 0 1
isready
go depth 10
quit
```

r15d:
```text
info depth 10 seldepth 23 score cp -135 nodes 33587 nps 1399458 hashfull 13 time 24 pv e1e2 e8c8 a1c1 h8e8 e2f1 d8d2 h2h4 c6d4 h1h3 d2c2 c1c2 d4c2
bestmove e1e2
```

kF:
```text
info depth 10 seldepth 23 score cp -135 nodes 33587 nps 1343480 hashfull 13 time 25 pv e1e2 e8c8 a1c1 h8e8 e2f1 d8d2 h2h4 c6d4 h1h3 d2c2 c1c2 d4c2
bestmove e1e2
```

### C5
Raw paired transcript: [dot/job6/C5_both.raw.txt](dot/job6/C5_both.raw.txt). Same commands sent separately to each fresh binary; actual tabs in C5 input retained.

```text
uci
setoption name Threads value 1
setoption name Hash value 16
setoption name OwnBook value false
setoption name LmrQuietBase value 93
setoption name LmrQuietDivisor value 205
setoption name LmrNoisyBase value 13
setoption name LmrNoisyDivisor value 333
setoption name LmrHistoryDivisor value 5643
setoption name NullMoveBase value 5
setoption name LmpBase value 8
setoption name HistoryPruneMultiplier value 2220
setoption name HistoryBonusQuadratic value 24
setoption name HistoryBonusLinear value 54
setoption name HistoryBonusMax value 2212
setoption name SingularDepth value 6
setoption name IirDepth value 2
setoption name NonPawnCorrection value true
setoption name CuckooRep value true
setoption name HistRework value 2
setoption name TtPruneV2 value true
setoption name CorrHistV2 value true
setoption name MateAlphaGuard value true
isready
position startpos moves g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8
position	startpos	moves	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8	g1f3	g8f6	f3g1	f6g8
position startpos moves g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8 e2e4
position startpos moves e2e4
setoption name Hash value 32
setoption name Hash value 16
setoption name Threads value 2
setoption name Threads value 1
ucinewgame
setoption name MultiPV value 2
position startpos
isready
go depth 10 searchmoves e2e4 d2d4
quit
```

r15d:
```text
info depth 10 multipv 2 score cp 21 seldepth 12 nodes 10511 nps 181224 hashfull 1 time 58 pv d2d4 g8f6 g1f3 e7e6 e2e3 f8e7 c2c4 d7d5 c4d5 e6d5
bestmove e2e4
```

kF:
```text
info depth 10 multipv 2 score cp 21 seldepth 12 nodes 10511 nps 437958 hashfull 1 time 24 pv d2d4 g8f6 g1f3 e7e6 e2e3 f8e7 c2c4 d7d5 c4d5 e6d5
bestmove e2e4
```

## Validation, grading, and limits
All three handmade FENs printed python-chess is_valid=True/status0 before engine runs. Startpos fixtures valid; every move of the440-ply long prefix and its441st-ply extension checked legal and valid (python-chess1.11.2). Exact validation, result JSON and reproducer: [step2_bundle.txt](dot/job6/step2_bundle.txt). No sampled FEN accepted solely on engine output.

C5 exercises long-prefix parsing/extension/shortening without a search at that root, then resets with ucinewgame before fixed-depth search. Therefore its final-output equality establishes liveness plus reset behavior, NOT an oracle for retained history after the long prefix. Threads2 is configured then reset to1 before any search; no active multithreaded equality test is claimed. Infinite/stop, timed ponder, no-legal-root and external-net reload paths were source-reviewed only. C3 contains EP and promotion candidates, but no instrumentation proves a particular SEE or bucket branch ran. The five controls are selected smoke checks, not exhaustive invariants tests.

Facts: clean patch/hash/build gates; concrete cited source guards; five equal final search outputs; zero demonstrated in-scope missing guarantees. Documentation mismatches are real but not demonstrated defects: README02 understates key_after king/castle handling; material_key excludes kings; prepare can early-return on same generation/size but each search invalidates flags; fresh accumulator vector elements still value-initialize despite avoided redundant clearing. No source repair is proposed on this evidence.

Suspicions: no verified behavioral divergence from this stack found. Unknown or excluded callers could violate contracts; no claim that absence in this audit proves none exist.

What I did not do: load the owner's net, run v3 numerical comparisons, performance benchmarking, fuzzing, sanitizers, all invalid-FEN paths, exhaustive move-order/key/checkers oracles, active multithreaded scheduling tests, debug shadow-key assertion tests, inactive SEE_HOIST #else, other architectures/toolchains, external-client ABI tests. Local full build logs are not asserted remotely published; committed Step0 bundle contains relevant raw compile/hash/patch evidence. All five paired Step2 raw transcripts are remotely published and full-body verified.

What I am not sure about: unenumerated paths, owner-machine/compiler/net behavior, pathological legal positions not covered by the source argument and selected inputs. The source table's GUARANTEED labels are conditional on their explicit engine/UCI contract, not universal claims.

The PC's own net, compiler and processor; paths you did not think of; a run is one input, not all inputs.

## Last command before report publication
```text
$ git status --short; ls -R forge-combo29/dot/job6
 M forge-combo29/dot/job2/stamps.txt
?? forge-combo29/REPORT_dot_job6.md
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
forge-combo29/dot/job6:
C1_both.raw.txt
C1_kF.raw.txt
C1_r15d.raw.txt
C2_both.raw.txt
C2_kF.raw.txt
C2_r15d.raw.txt
C3_both.raw.txt
C3_kF.raw.txt
C3_r15d.raw.txt
C4_both.raw.txt
C4_kF.raw.txt
C4_r15d.raw.txt
C5_both.raw.txt
C5_kF.raw.txt
C5_r15d.raw.txt
audit_checkpoint.txt
build_kf.txt
build_r15d.txt
gate.py.txt
isa.txt
kf_gate.raw.txt
kf_gate.summary.txt
kf_patch_gate.txt
patch_gate.txt
prediction.md
r15d_expected.sha256.txt
r15d_gate.raw.txt
r15d_gate.summary.txt
r15d_hash_gate.txt
step0_bundle.txt
step1_table.md
step2.py.txt
step2_bundle.txt
step2_driver.txt
step2_summary.json.txt
validation.txt
```

Local status includes earlier preserved work and connector-published files because this checkout is not fast-forwarded to connector commits. No reset/clean performed. Remote evidence verification, not this local status, establishes publication.
