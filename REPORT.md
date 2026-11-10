# Forge combo29 review

Reviewed lock: `16833ecc03b425586f91f4c8834dea8807bf4c22`, verified on `lock/combo29-20261110` before work. All writes are confined to `dot/review-20261110`. Checkpoint updated 2026-11-10 UTC. Original code, constants, embedded net and datasets remain unchanged when new default-0 experiment switches are off. No GPL/AGPL implementation was copied.

**UNPROVEN is the acceptance/performance status of every patch and idea.** Several defects are reproduced, but that does not establish speed or strength gains. No Elo or speed claim is made. Native tester-PC 12k bit-exact, quiet ABBA and 10+0.1 SPRT gates remain outstanding.

## Findings, confidence and patches

Patch files were exported from sequential review commits and can have context dependencies; use the branch or apply in documented commit order. All line references in this section refer to the original locked source under `forge-combo29/`, unless explicitly stated. Patch files live under `forge-combo29/patches/dot-review/` and preserve original behavior when disabled.

### F1 HIGH: stale helper node counters
Confidence **high, deterministically reproduced**. `src/search.cpp:1509-1510,1804-1809` resets published counters inside worker execution. Main sums every helper at 881-886, so a helper held before entry contributes its preceding search's nodes. Known issue confirmed, not claimed as a new discovery.

Minimal fix: reset every published counter synchronously before any worker starts. Patch `F1-smp-reset.patch`, switch `FORGE_FIX_SMP_NODE_RESET=1`. Test `tests/run_smp_nodes.sh`: old main=0/returned=1000000 under a fresh 100-node budget; fixed main=100/returned=100. Test uses an actual held helper, no timing guesses. Status **UNPROVEN** pending full acceptance.

### F2 MED: returned total omits helper tail
Confidence **high, deterministically reproduced with injected scheduling**. `src/search.cpp:1734-1735,1812-1815`: result.nodes is sampled before helpers stop/join. Minimal fix: sum final published counters after joins. Patch `F2-final-nodes.patch`, switch `FORGE_FIX_SMP_FINAL_NODES=1`.

Test `SMP_NODES_FINAL=1` with `tests/run_smp_nodes.sh`: old returned 21/final 42, fixed 42. The harness deliberately re-enables a held helper at join to model late real depth-one work; it is an injected schedule, not an ordinary-run measurement. SMP node budgets remain approximate due to helper publication/check cadence. Status **UNPROVEN**.

### F3 MED: concurrent external stop can be lost
Confidence **high, deterministically reproduced; direct API impact**. `src/search.cpp:1811-1814` snapshots stop then restores that stale snapshot after joining helpers. A stop() during the join can be overwritten. Current UCI also has stop_requested, so this is not evidence of a CLI hang.

Patch `F3-stop-latch.patch`, switch `FORGE_FIX_SMP_STOP_LATCH=1`, separates internal shutdown from latched external cancellation. Only explicit reset_stop clears external stop. Test `SMP_STOP_JOIN=1`: original searches 21 nodes after an intervening stop without reset; fixed 0, then resumes after reset. All three SMP regressions passed 20 repetitions together. Status **UNPROVEN**.

### F4 MED: exception during helper creation terminates process
Confidence **high, reproduced exceptional resource-failure path**. `src/search.cpp:1803-1809` unwinds a vector containing joinable threads after a later pthread creation failure. Main-search exceptions have the same cleanup concern; uncaught helper exceptions also terminate.

`tests/thread_exception*` inject EAGAIN on second helper creation with Threads 3: child receives SIGABRT 6 with 'terminate called without an active exception'. First-helper failure is catchable std::system_error 11; uninjected control succeeds. Minimal fix: stop/join on exceptional exits and transport helper exceptions after joins. Patch `F4-exception-cleanup.patch`, switch `FORGE_FIX_SMP_EXCEPTIONS=1`, now joins all started helpers before propagating exceptions. Startup failure, injected main/helper bad_alloc and repeated successful searches pass with F4 alone and with F3. Internal shutdown never overwrites external stop. The initial patch covered library cleanup only. The requested review follow-up adds guarded UCI-worker and bench catches, an error diagnostic and deterministic legal fallback, while retaining the infinite/ponder wait. This does not promise recovery from every process-wide resource failure outside the guarded search calls. See `tests/thread_exception_REVIEW.md`. Status **UNPROVEN**.

### F5 LOW: first-use attack initialization races
Confidence **high, reproduced with ThreadSanitizer and unsanitized scheduling**. `src/bitboard.cpp:136-139` uses a plain static bool and publishes true before tables are constructed. Simultaneous first calls can read incomplete tables.

Patch `F5-init-once.patch`, switch `FORGE_FIX_ATTACKS_INIT_ONCE=1`, wraps unchanged initialization in std::call_once. See `tests/ATTACKS_INIT_REVIEW.md` and `tests/attacks_init_concurrent.cpp`: baseline TSan exits 66 with data race; enabled exits 0 without diagnostics; unsanitized baseline premature-return failure reproduced and enabled passed 10 fresh-process repeats. Normal UCI constructs its first Board before launching workers, so normal CLI reachability is not established. Status **UNPROVEN**.

### F6 LOW: UCI option names are case-sensitive
Confidence **high, reproduced**. `src/uci.cpp:205,219-280` compares option names exactly, ignoring alternate casing despite UCI's case-insensitive option-name rule. `setoption name usennue value false` leaves bench 11 at 312866; canonical UseNNUE disables net and produces 375354.

Patch `F6-uci-case.patch`, switch `FORGE_FIX_UCI_OPTION_CASE=1`, compares option names with ASCII case folding and preserves values/file paths. Regression `tests/uci_option_case.py BASELINE CANDIDATE` passes both NNUE cases plus mixed-case multiword names, tunables, Hash and Threads. Clear Hash dispatch is source-reviewed; its side effect is not directly tested. Status **UNPROVEN**.

## No defect established in these checks

No TT race established under documented quiescent lifecycle contract. Later extreme-depth API testing did establish the overflow documented as F7 below; ordinary bounded-depth TT checks passed. No legal-position move-generation defect found in source review and tests. This is not a proof of absence.

Board-only ASan+UBSan: 17401 positions and 499310 legal moves over 100 seeded random games plus corners, no diagnostics. Checks generated pseudo-legality, gives_check versus resulting in_check, reconstructed FEN/full/pawn keys/checkers, exact make/unmake and legal-move-existence agreement. This compares invariants within this engine, not an independent chess implementation. Default header switches were used for this harness. Full source and commands: `tests/book_board_audit.cpp`, `tests/book_REVIEW.md`.

Corner FENs verified:
- Illegal horizontal EP excluded g5f6: `8/8/8/r4pPK/8/8/8/4k3 w - f6 0 1`.
- EP check evasion includes e5d6: `4k3/8/8/3pP3/4K3/8/8/8 w - d6 0 1`.
- Both white castles: `r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1`.
- Four a7a8 promotions: `4k3/P7/8/8/8/8/7p/4K3 w - - 0 1`.
- Double-check evasions exactly e1d1/e1f1/e1f2: `4r2k/8/8/8/1b6/8/8/4K3 w - - 0 1`.

## Cloud build and baseline measurements

Linux g++ 14.2, C++20, strict `-ffp-contract=off -fno-fast-math`, x86-64-v4, all combo29 CMake definitions. Clang and CMake are absent, so built directly with g++. No claim of a Clang build. Embedded net verified SHA256 `a7ebcf3a319675f347e6e8e3f2539901d38d8036cb9b5935f31dd43d084c9638`; Windows exe not fetched.

Baseline and default-off review build both match all documented pins at depths 11/13/16/20/22:
- NNUE on: 312866 /862329 /3024920 /12389307 /34048354.
- NNUE off: 375354 /907205 /2448617 /13573040 /24506465.
- Startpos perft 5: 4865609.
- Baseline Kiwipete perft 4:4085603.

Baseline CLI checks passed nodes 0, nodes 1, movetime 0, movetime 30, restricted e2e4, infinite withholding bestmove until stop, ponder withholding until ponderhit, and isready during search. Evidence under `tests/review_evidence/`. These are this cloud machine's results, not the tester PC. Raw logs may include timing/NPS as engine output; no speed conclusion is drawn. The seven-switch combined candidate also passed all ten pins, perft 5, Kiwipete perft 4 and the UCI smoke checks. The final corrected eight-switch candidate including F4 exception cleanup and the final default-off build both passed all ten pins, perft 5, the UCI smoke suite and mixed-case option regression. Reproduce both default and all-enabled builds with `bash forge-combo29/tests/review_build.sh /tmp/forge-review-build`.

## Final fresh-FEN equivalence screen

**PASS, high confidence for the tested scope:** 128 FENs (16 corner positions plus 112 seeded legal playout samples), NNUE on and off, 256 comparisons and 512 sequential searches. Threads 1, Hash 16, OwnBook false, depth 7, cold TT for every search. Zero mismatches in final nodes, depth, score, bestmove or PV. Fresh FEN reloads do not preserve full preceding game history. This is not the tester-PC 12k gate and does not validate deterministic SMP equivalence.

Full generator, fixture, test driver, receipt and compared results: `forge-combo29/tests/equivalence_*`.

- Locked-source cloud baseline binary SHA256: `1371770e2ad61aa2fe3c038acc7da3912da5d64c9cb1dcc5e4668221fb3226f6`.
- Final default-off binary SHA256: `eb9dfc03aba50d5875300ea378cbb1b06c361f11ed2a330e7da6d740cbca2275`.
- Final all-eight-enabled binary SHA256: `21d64ae060cf54614a8a0761b9711b776dc91278f8e8bdab4fa6ecdc62fb9d74`.

Independent static review found no introduced defect in UCI/book/NNUE/node-reset patches and identified the preliminary F4 standalone latch regression. That regression was corrected before remote publication and covered with repeated-search tests. Source/header and embedded-net Git blob IDs were independently compared between published branch and tested local source and match. This is source-content verification, not a Windows executable identity claim.

## Implemented bit-exact speed candidates

Both are **UNPROVEN** optimizations, disabled by default. Confidence in tested equivalence is high; confidence of a real speed gain is undetermined.

1. `S1-book-reuse.patch`, `FORGE_BOOK_LEGAL_REUSE=1`, `src/book.cpp` candidates loop. Reuse one legal list for all book entries at a matching key. Preserve decoder/order/duplicate saturation/probe semantics; misses avoid movegen. Both modes passed ASan+UBSan candidate/reference checks on 509 positions, including all 65536 encodings on 9 corner FENs. This optimizes book lookup, not a demonstrated main-search hotspot. See `tests/book_REVIEW.md`.
2. `S2-nnue-castling.patch`, `FORGE_SPD_NNUE_CASTLE_FUSE=1`, `src/nnue.cpp` generic dirty-update fallback. Fuse castling's four passes while retaining per-lane subtract/add/subtract/add order. 12972 exact-bit cases pass default-off, enabled, native, non-vectorized and ASan+UBSan builds; all castle directions, random finite floats, signed zero, aliasing and fallback patterns included. Leak detection disabled due to ptrace environment. See `tests/nnue_CASTLING_REVIEW.md`.

Other source-grounded profiling candidates, not measured bottlenecks: cache material correction index (search.cpp805-812,855-872), add exact nonterminal witnesses while retaining pre-pruning draw detection (914-923; board.cpp696-712), directly generate check evasions preserving surviving move order (748-769), profile picker selection/sort and equal-score ordering (645-659), precompute root effort slots (1409-1412). Locations here refer to local review snapshot b6e896f.

## Ranked search/evaluation ideas

All **UNPROVEN**. Idea 1 now has an isolated default-off experiment, documented below; the other ideas remain unimplemented. Search changes must be independently default-off behind UCI control. Locations refer to review snapshot b6e896f. Ranking is experiment priority, not predicted Elo.

1. Read four-ply continuation in quiet scoring (search.cpp184-190,926-953). Updates include 1/2/4 but scoring reads 1/2. Test a separate weight; beware correlated signals and shared-context effects.
2. Existing capture futility is disabled by CaptureFutilityBase=0 (74-76,1343-1350). Isolated experiment only; tactical sacrifice/promotion risk.
3. Existing fail-low continuation bonus is disabled (77,1485-1489). May improve parent ordering; risk rewarding shallow misleading fail-lows.
4. Add non-pawn-placement correction context (855-872; search.hpp287-290). Current keys are pawn position and material counts; risks memory traffic/collisions/overfitting.
5. Adapt reduced-search re-search depth narrowly by returned score (1417-1436). Many LMR conditions already exist; risk tactical instability.
6. Use recent root-score variability for initial aspiration width (1663-1685), instead of fixed initial AspirationDelta. Risk extra re-search or wasted wide windows.
7. Diversify helper schedules (1663-1675,1828-1832), after SMP correctness fixes. Same current depth sequence/limits; risk lost useful shared work and reproducibility.
8. Bounded quiet checks in quiescence (436-438,519-529,999-1119). Currently captures/promotions outside check. Lower priority due to expansion/TT semantics risk.

Already present, not suggested as missing: PVS, aspiration, LMR/LMP, razoring/reverse futility, verified high-depth null move, ProbCut, singular/double/negative extensions, SEE pruning, capture/continuation history, countermoves, pawn/material correction and root-effort time management.

## Published commit ledger

Connector author was explicitly authorized after authenticated git push was unavailable. Local Dot commits and remote connector commits have different identities; below are published remote commits, all only on dot/review-20261110.

- 3d50f368: initial report checkpoint.
- 789c1dcb: UCI option case fix/test.
- 71fbfbe3: book list reuse/test.
- fdd3f3a0: synchronous SMP counter reset/test.
- 09b70765: castling NNUE fusion/test.
- 75c01af2: expanded UCI tests.
- 12816dd0: post-join SMP final nodes/test.
- cd8ed985: NNUE sanitizer/reproduction notes.
- 4f9aa66e, bf43a459: synchronized init/test and repeat evidence.
- fcb491cb: latched external stop fix/test.
- 43b5e076: thread-creation failure reproducer.
- 29e8c5a0: complete findings/evidence checkpoint.
- 39f69079: corrected exception-safe cleanup and regression tests.
- 15e8f115: reproduction recipe and seven-switch validation evidence.
- bb1b8fbd: final eight-switch pin/UCI summary and executable test script metadata.
- 80b4f4ba: full 128-FEN equivalence artifact bundle.
- 60e6a8c2: complete equivalence JSON transfer, verified to exact local Git blob.

This final report checkpoint follows verified publication of all eight opt-in changes, patch exports, reproductions and evidence. A transfer-integrity check caught a partial large evidence JSON; a non-rewriting follow-up commit restored the exact local blob. All 64 compared source/header/test/patch/report entries now match their tested local content and modes. Remaining: native 12k bit-exact, quiet ABBA, 10+0.1 SPRT and Windows/Clang validation. Cloud work completed to the coverage documented here; no claim of exhaustive verification. No branch rewrite, force push, deletion, merge or locked-branch change performed.


## Continued audit checkpoint: additional coverage and third speed candidate

No additional production correctness defect established in this phase.

- Full-engine GCC ThreadSanitizer: default-off and all-eight-enabled builds each completed 72 UCI searches with no sanitizer warnings or initialization failures. Covers all Threads 2/4 × NNUE on/off combinations, node limits, stop, pondering, movetime, hash resize/clear and newgame. Source tested through the exception-cleanup correction, before material caching. Finite race coverage does not negate the previously reproduced atomic semantic defects. Full logs and recipe: `tests/smp_tsan_*`.
- Ten additional UCI edge cases passed on original baseline and the eight-switch candidate: mate overrides rule-50 draw, stalemate, legal rule-50 draw, twofold versus threefold knight cycles with history, empty searchmoves, invalid-FEN/illegal-move atomicity, castling through attack, and quiet/capture underpromotions. Driver `tests/uci_edgecases.py`; logs `tests/review_evidence/uci-edge-*`.
- Third default-off speed candidate: `FORGE_SPD_MATERIAL_CORRECTION_CACHE=1`, patch `S3-material-cache.patch`. Lazily reuse the material-correction index within one SearchStack frame. Every main/qsearch entry invalidates it, including early returns and same-ply re-entry; weight-zero stays lazy and NNUE is independent. Original hash, mask and correction arithmetic retained. Independent static review found no new defect. Focused tests plus isolated off/on 256 comparisons passed. **UNPROVEN speed/strength**, high confidence only in tested equivalence. Files `tests/material_cache_*`.
- All NINE switches combined also pass all ten bench pins, startpos perft 5, the terminal/history/atomicity UCI edge suite, and a new 256-comparison baseline screen at depth 7 with both NNUE modes: zero mismatches in nodes/depth/score/PV/bestmove. Evidence `tests/review_evidence/nine-switch-*`. The general build recipe now enables all nine candidates.

Published continuation commits: `214f7401` TSan lifecycle stress; `9edcfe92` UCI/history edge tests; `04cc2f87` material-correction cache and isolated equivalence evidence. This checkpoint adds combined nine-switch evidence and the third patch export. Native tester-PC gates remain unchanged and outstanding.


## Further audit: seventh finding and isolated search experiment

### F7: LOW, high confidence, extreme TT API depth overflows before clamping

`TranspositionTable::store` previously evaluated `depth + 4` before its later depth clamp. An occupied matching-key non-exact entry and `depth=INT_MAX` reproducibly trigger UBSan signed-overflow diagnostics in both NOTLS implementations. Ordinary engine search depths are bounded, so this is a public-API robustness edge, not a demonstrated normal-gameplay bug. Default-off `FORGE_FIX_TT_DEPTH_OVERFLOW` uses the equivalent safe comparison `depth > int(entry->depth) - 4`. Both variants pass the formerly failing UBSan case and ordinary concurrent TT contract checks under TSan. Reproducer, original failures, corrected logs and hashes: `tests/tt_contract_*`; patch `patches/dot-review/F7-tt-depth.patch`.

### Additional negative findings and coverage

- Fast `key_after` audit: 17,470 positions and 490,569 legal moves; all 470,876 successful fast paths match the fully made board hash, with 19,693 safe fallbacks. Both king-line configurations pass ASan+UBSan.
- SEE: 134,088 moves screened against an independent target-square minimax oracle. All 18 differences were subsequently explained by Forge's greedy least-valuable-attacker policy and match an independent legal greedy oracle. These are not established correctness defects. Both SEE configurations agree; threshold properties and sanitizer checks pass. Exact classifications and reproduction sources are retained in the test files.
- Ten focused move-generation corners cover pinned promotions, en-passant double check, and captured corner-rook castling rights. Both king-line builds pass ASan+UBSan. No new move-generation defect established.
- Incremental evaluation: 121,960 release checks and 48,336 transitions match fresh accumulator bits/output and uncached HCE/PSQT; sanitizer run passes 39,954 checks.
- Actual Worker lazy-stack evaluation: 45,787 checks across three seeds, including absent ancestors, cache hits, 1/2/7/31/96-ply replay, root invalid/valid, deferred sibling reuse, null descendants and special moves. Every accumulator float bit and fresh residual score match. ASan+UBSan passes 15,288 checks. Leak checks remain unavailable under ptrace. Details: `tests/eval_incremental_*` and `tests/eval_lazy_*`.

Confidence is high for these observed finite tests, not proof over all positions. No speed or strength gain is inferred.

### E1: four-ply continuation history changes ordering, LMR and pruning; UNPROVEN

`FORGE_EXPERIMENT_CONTINUATION4` defaults to zero. Enabling it exposes `Continuation4Weight`, default zero, range 0–100 percent. Nonzero weight adds four-ply history to quiet scoring, affecting ordering, quiet-history pruning and LMR. Both slow and SPEED2 scoring paths are covered; null/sentinel predecessors are skipped. Existing continuation update rules and locked evaluation constants are unchanged. Patch: `patches/dot-review/E1-continuation4.patch`.

The implementation is an experiment, not a recommendation to enable a particular weight. Native fixed-time matches and SPRT are required before any strength claim. Default-zero equivalence and legal PV checks cannot establish strength or absence of all tactical regressions.

Published additional checkpoints: `d554d6cb` incremental evaluation tests, `506dea84` SEE classifier evidence, `d5fa47ed` focused move-generation corners, `f51ab0f7` TT contracts, `d732c84a` isolated four-ply source, `21fc5f78` lazy-stack evidence, and `fd80dee9` default-off TT overflow fix. All remain on the authorized new branch only.

E1 validation (`tests/continuation4_*`): four complete lock-pin suites passed across SPEED2 on/off and experiment compiled on/off. 512 default-zero comparisons match depth/nodes/score/PV/bestmove exactly. At positive weight, 256 searches and 128 cross-path comparisons passed, including 1,382 verified legal PV plies. 170 searches changed, proving activation only.

Combined phase-three build: all ten opt-in fixes/speed candidates plus the compiled E1 option at its default zero weight pass all ten official bench pins, startpos perft5=4,865,609, basic UCI lifecycle and option-case tests. A further 128-position × both NNUE modes baseline screen passed all 256 comparisons with zero depth/nodes/score/PV/bestmove differences. Results and binary hashes are under `tests/review_evidence/ten-switch-*`; recipe `tests/review_build.sh`. This does not replace the native 12k, ABBA, Windows/Clang or SPRT gates.


Independent static review of the E1 and F7 source deltas found no concrete introduced defect. It checked the four-entry stack prefix, null/sentinel eligibility, persistent history pointers, both scoring paths, default-zero behavior and bounded weight arithmetic. The TT subtraction comparison was checked for equivalence over formerly non-overflowing inputs and safety at INT_MIN/INT_MAX in both implementations. This was a source review, not a rerun of tests.

Patch delivery audit: all eleven exported patches applied in documented sequence to a fresh archive of the locked source. The replayed source/header trees exactly match the tested candidate. Exact order is recorded in `forge-combo29/patches/dot-review/README.md`; exports are sequential, not necessarily independently applicable.

Latest combined ThreadSanitizer screen: all ten switches plus E1 at explicitly verified weight 50 completed 72 searches across eight lifecycle rounds (Threads 2/4 × NNUE on/off twice), with no sanitizer warnings or startup failures. Portable x86-64-v3 paths were used (PEXT=0, NNUE_ZMM=0), so this is not sanitizer coverage of the AVX-512 kernel. Search/stop/ponder/hash/newgame cases, exact flags and binary hash are preserved in `tests/smp_tsan_combined50_*`, published as `4cfd716e`. Finite race coverage does not prove all interleavings or strength.

## Bounded follow-up: input robustness and exploratory material-cache timings

No new correctness defect was established. ASan+UBSan FEN audit passed 3,007 valid roundtrips, 23 explicit malformed cases and 20,000 deterministic byte mutations: 234 accepted inputs canonicalized consistently, while 19,766 were rejected without changing prior state. The actual production UCI position handler passed 17 rejection rollback cases and three valid commits. Permissive numeric signs, equivalent rank digit runs, castling-order normalization and saturated counters are documented behavior rather than automatically classified as bugs. Tests and receipts: `tests/fen_audit_*`. Confidence is high in these recorded finite checks, not exhaustive parser safety.

Isolated material-cache exploratory profile used hash-verified off/on binaries, one pinned CPU, three ABBA cycles per NNUE mode and a coordinated pause of our other CPU jobs. All 24 measured runs and four warmups preserved the official depth-16 node signatures. Median process wall time was 1.907s baseline vs 1.925s candidate with NNUE on, and 1.340s vs 1.370s with NNUE off. Paired candidate/baseline ratios were 1.008, 0.984, 1.024 (on) and 1.014, 1.049, 1.018 (off). These observations provide no basis to promote the candidate as a speed improvement. Shared host contention/frequency and small sample remain uncontrolled; this is not native ABBA acceptance, nor a statistically established slowdown. Candidate remains disabled and UNPROVEN. Raw complete and interrupted preliminary receipts, executable hashes and reproducible driver are retained in `tests/material_cache_profile*`, published at `0f633981`.

## S4: bounded exact legal-move witnesses

`FORGE_SPD_LEGAL_WITNESSES` defaults to zero. After the existing single pawn witness fails, the candidate tests at most one knight destination and one king destination before using the unchanged complete move-generation fallback. Attack geometry excludes friendly occupancy and the opposing king, capture flags match occupancy, and existing exact king-safety filtering decides legality. The purpose is to avoid a full list when one legal move proves a position nonterminal; no search/draw-rule change is intended. Candidate source was checkpointed at `64659e74` and remains **UNPROVEN** for speed/strength.

Independent static review found no concrete defect, including both KING_LINES paths and king captures. The four-way ASan+UBSan matrix (witness off/on × KING_LINES off/on) passed 17,755 positions against complete legal-list existence. Explicit cases cover pinned pawn followed by legal knight witness, illegal first knight and king requiring the full fallback, king capture/x-ray, check, mate and stalemate. Corpus path counts were 15,575 existing pawn hits, 862 additional knight hits, 789 additional king hits and 529 full fallbacks, including 146 added capture witnesses. These counts characterize that corpus, not engine hotspot frequency or performance.

Combined eleven-switch validation (seven fixes plus four speed candidates, E1 compiled at weight zero) passed all ten official pins, startpos perft5, UCI lifecycle/option checks and all 256 baseline comparisons over 128 FENs with both NNUE modes. Receipt and hashes: `tests/review_evidence/eleven-switch-*`. The updated build recipe enables this set. All twelve source patches replay from the lock to exactly reproduce candidate source/header trees; the README lists their order. Native acceptance remains outstanding.

Isolated S4 off/on binaries also passed all ten canonical pins, perft5 and 256 exact fixed-depth comparisons; full evidence published at `4ab27e9d`. The subsequent hash-verified, CPU-pinned three-cycle cloud ABBA screen preserved exact nodes in every run. Median wall time was 1.875s baseline vs 1.864s candidate with NNUE on, and 1.307s vs 1.357s with NNUE off. Cycle candidate/baseline ratios were 1.001, 0.971, 1.036 (on) and 1.044, 1.022, 1.033 (off). Mixed/noisy on-results and consistently slower off-observations do not support promotion. This is descriptive shared-cloud data, not a statistically established gain or slowdown; native acceptance remains open. Candidate stays default-off and UNPROVEN. Full driver, validation provenance, raw receipts and limitations are in `tests/legal_witness_profile*`.


## User-requested review blockers

S3 signature gating: the original cache patch unnecessarily changed helper signatures even when its switch was disabled. The review correction puts both declarations, definitions and every SearchStack argument behind FORGE_SPD_MATERIAL_CORRECTION_CACHE. The isolated pre-S3 and corrected-S3-off binaries are byte-identical under the same compiler/path/command, and the enabled binary retains its previous hash with 256 exact comparisons passing. Full lock identity is separately checked rather than inferred from this narrower result.

E1 option contract: Continuation4Weight is appended to the parameter table and is the final advertised UCI option, after Clear Hash. Every legacy option retains its prior position. Options are resolved by name, never by positional index. Both scorer builds pass 52 name-based tunable change/restore checks, helper tests and depth-11 NNUE-on/off pins. Its experiment card explicitly states that it changes ordering, LMR and pruning; strength remains UNPROVEN.

F4 recovery: the actual UCI worker now catches propagated search exceptions, prints `info string search error`, selects the first legal move admitted by an explicit searchmoves restriction (or `0000` if none), and retains the existing infinite/ponder wait before bestmove. Bench also catches search failures and emits the diagnostic/fallback without publishing a misleading partial benchmark total. All 15 injected CLI cases pass, including standard/nonstandard exceptions, main/helper allocation failures, terminal positions, stop/ponderhit waits, restricted/empty fallback and subsequent commands/searches. Original failures and F4-off behavior are retained in `tests/f4_uci_*`. Outer UCI thread creation, startup and bench construction remain outside these guarded search calls; this is not blanket resource-failure immunity.

Full default-off identity: exact same GCC 14 compiler/command/build path now produces byte-identical immutable-lock and final-reviewed binaries, SHA256 `1371770e2ad61aa2fe3c038acc7da3912da5d64c9cb1dcc5e4668221fb3226f6`. Diagnosis found that F6's prior default-off wrapper still changed UCI object code; all seven other translation units matched. A minimal compile-time guard now restores original std::string comparisons when F6 is disabled, while the enabled ASCII-name protocol tests still pass. Reproduction and before/after evidence: `tests/default_lock_identity_*`, `tests/material_cache_lock_identity.sh`. This is an exact result for the recorded GCC build, not a claim about untested compilers/platforms.

Independent static review found no remaining blocker in S3 gating, E1 ordering/name lookup, F4 recovery/restricted fallback, or F6 default-off restoration. Final combined enabled build, with E1 runtime weight zero, passes every official pin, startpos perft5, UCI lifecycle checks and all 256 baseline search comparisons. Final receipts: `tests/review_evidence/blocker-fixes-*`. All seventeen source patch exports replay from the lock to exactly match final source/header trees. The five C-series follow-up patches in the replay README correct review blockers without rewriting prior history. Native performance/strength gates and UNPROVEN acceptance status remain unchanged.

## Follow-up capacity audit

The fixed 256-entry MoveList release path was tested against adversarial, parser-accepted promoted inventories rather than ordinary game playouts alone. A bounded search examined 468,000 proposals across 78 configurations, with 304,602 accepted. Safe counting used a test-only 1024-capacity header and an independent geometric counter; production capacity was unchanged. The largest observed position had 209 pseudo-legal moves but only 3 legal moves, illustrating why legal-move counts alone cannot justify this buffer. No overflow was found; observed 47-slot headroom is not a universal bound.

All 156 per-configuration maxima and color mirrors passed real-capacity 256 replay with assertions disabled under ASan+UBSan across eight witness/king-lines/move-list configurations. Quiet/noisy partitioning, pseudo-legality, legal existence and impossible-inventory rejection checks passed. Corpus, commands and limitations are in `tests/move_capacity_*`, published at `daff4141`. No production change or capacity reduction follows from this finite audit.


## Locked-source hotspot attribution

A bounded GCC 14/gprof diagnostic build of the immutable lock preserved exact node signatures at depths 16 and 18 in both NNUE modes. At depth 18 with NNUE enabled, the largest observed self-sample shares were residual HCE evaluation 18.75%, NNUE update 11.68%, main search 11.14% and MovePicker 10.87%. This network is residual, so NNUE-on still performs HCE. The run contained only 368 histogram ticks; instrumentation, inlining, setup and shared-host effects prevent precise production-cost or speed claims. NNUE-off HCE was also largest at 23.40% of 265 ticks.

Stock gprof mislabeled some introsort entries as a parameter-vector destructor. Raw address ranges and disassembly resolved that attribution; corrected rankings do not identify destructor work as a hotspot. Complete decoded nonzero bins/arcs and original reports are preserved in `tests/hotspot_profile_*`, published at `b4c4addc`. Candidate ideas in measured regions are TT replacement-score reuse and avoiding MovePicker self-swaps, but their branch frequencies and actual generated-code costs require separate examination before proposing changes. No production patch or gain is claimed from this profile.

Two targeted follow-ups refine those hypotheses without adding production patches. MovePicker self-swaps occur in 37.53–39.20% of first-four selections across depth 16/18 and NNUE on/off; every node signature matched. This is frequent enough to measure, but replacing stores with a branch can lose time. Full counts, ordinal distributions and instrumentation are in `tests/pick_swap_profile_*` (`2ceb496a`).

TT disassembly confirms that GCC does not carry the selected replacement score through every later comparison, but measured exposure is narrow: depth-18 redundant recomputations average only 0.0739 per probe with NNUE on and 0.0878 off. Hits account for 35.77%/37.59%, empty-slot misses for 62.30%/59.96%, and full replacements for 1.94%/2.44%. All four depth/mode node signatures match the lock. Counts and pristine assembly are in `tests/tt_probe_profile_*` (`e6109b8a`). These results limit the likely opportunity rather than justify an unmeasured speed claim.

A proposed first-empty TT hit-scan exit was rejected after a concrete API counterexample. BoundNone can create an empty slot before a later occupied slot; both current TT implementations correctly preserve the later hit. The modeled shortcut misses it. The executed regression passes under TSan in both NOTLS modes, including refill and the existing concurrent contract suite. This is a disproved optimization premise, not a new engine bug. Evidence: `tests/tt_contract_boundnone_*` and the updated TT contract suite, published at `d61982f1`.

## S5: compact pawn-cache layout

Existing HCE histogram addresses were mapped through optimized DWARF and checked against disassembly, without additional benchmark runs. Piece evaluation and then king evaluation account for substantial HCE samples; the most recurrent individual HCE bin includes pawn-cache validity checking. Counts are too small and optimized line tables too coarse for precise line-level cost claims. An apparent repeated queen-ray calculation was rejected as a candidate because GCC already eliminates it. Full attribution: `tests/hce_profile_lines_*` (`6da66521`).

The new default-off `FORGE_SPD_COMPACT_PAWN_CACHE` moves PawnEntry.valid into existing padding. On the tested x86-64 GCC build, entries shrink from 40 to 32 bytes; 32,768 entries therefore use 1 MiB instead of 1.25 MiB, a verified 256 KiB element-payload reduction per worker. This is not a process-RSS or speed measurement. Key/index semantics, scores, passed-pawn data and validity behavior are unchanged. The disabled declaration is the original struct verbatim, and its complete default-off binary remains byte-identical to the immutable lock. Source checkpoint: `5655398d`.

Opting in changes public struct ABI and aggregate-initializer order. Every consuming translation unit/library must use the same setting; external positional/designated initializers or serialized layouts may need adjustment. Independent review found only member-name access and value initialization in this repository, with no raw serialization or positional initializer dependence.

Isolated off/on builds pass all ten pins, perft5 and 256 exact comparisons. Both layout/cache units pass 4,105 checks, including hit/miss/collision, zero key and invalidation; enabled ASan+UBSan passes the same 4,105 checks, with LeakSanitizer disabled. The combined twelve-switch build (E1 compiled at zero weight) also passes all pins, perft, UCI lifecycle and 256 comparisons; receipts are under `tests/review_evidence/compact-combined-*`. All eighteen source patches replay to exactly match source/header trees. Speed/strength acceptance remains UNPROVEN; the measured payload reduction does not establish a speed gain.

Compact-cache exploratory ABBA: all 24 measured runs and four warmups retained exact depth-16 nodes and unchanged hashes. Median wall time was 1.888s baseline versus 1.896s candidate with NNUE on, and 1.406s versus 1.421s with NNUE off. Cycle ratios crossed parity in both modes (on: 1.048, 1.020, 0.971; off: 1.104, 0.967, 0.961). The small, shared-host sample does not establish a speed gain or slowdown. The separately verified cache-payload reduction remains valid. Full receipts and caveats: `tests/compact_pawn_cache_profile_*`.

## Continued small-gain candidates: S6–S8

All remain default-off and UNPROVEN for native performance/strength. Default-off builds at these source checkpoints are byte-identical to the immutable lock.

- **S6, TT replacement-score cache:** `FORGE_SPD_TT_REPLACE_CACHE` caches the selected score during both replacement loops, retaining the complete hit scan, first-empty selection, BoundNone holes and earliest strict-less tie behavior. Four NOTLS/cache variants pass TSan contracts and 4,096 selected-slot oracle cases each; full pins/perft and 256 engine comparisons pass. Generated code retains scores but adds register saves. Three-cycle diagnostic wall ratios were mixed with NNUE on (aggregate 0.98735, cycles crossing parity) and slower in every off block (aggregate 1.02689). No promotion is supported. Source/evidence: `fa748141`, `2071c38a`, `tests/tt_replace_cache_*`. Temporary packed-priority, dedicated-empty-pass and outlined-helper refinements were investigated separately; the latter shapes burdened common paths with saves/spills and were not adopted. Their source-only diagnostic artifacts remain under `tests/tt_*prototype*` and associated review files.
- **S7, MovePicker self-swap guard:** `FORGE_SPD_PICKER_SELF_SWAP_GUARD` skips only a swap whose source and destination are the same slot. Four configurations pass 36,474 fixtures and 1,060,531 selections each, including tie orders, full 256-entry boundaries and sorted tails. Both scorer paths pass 256 exact engine comparisons; full pins/perft and sanitizer checks pass. Three diagnostic NNUE-on wall ratios were 0.98953/0.97501/0.98187; off ratios were mixed at 1.05051/0.97033/1.00889. This is a limited cloud signal, not accepted speed evidence. Source/evidence: `24654935`, `6866d435`, `tests/picker_self_swap_*`.
- **S8, WeakQueen mask simplification:** `FORGE_SPD_WEAK_QUEEN_MASK` removes redundant queen terms using the invariant that valid Board bishop/rook/queen bitboards are disjoint. Full occupancy remains unchanged in both ray queries, so all blockers still work identically. Independent review and exact truth-table proof support the change; 37,412-board cached/uncached/full-trace checks, adversarial blocker fixtures and deliberate mutation failures validate it. Both sanitizer modes, full pins/UCI and 256 comparisons pass. GCC 14 eval-object text is 192 bytes smaller; this is a code-size observation, not a runtime-speed claim. Source/evidence: `9004c527`, `ac4cbbd6`, `tests/weak_queen_*`.

S8 used a predeclared depth-18 protocol with four balanced ABBA/BAAB blocks per NNUE mode, fresh processes and child user/system CPU accounting alongside wall time. All 36 runs preserved nodes/hashes. Median block CPU ratios were 0.98784 with NNUE on and 0.99462 off; wall ratios were 0.98782 and 0.99454. The on blocks drifted toward parity, and off included a regression block. This supports native follow-up, not a general speed or Elo claim. Complete fixed protocol and receipts: `tests/weak_queen_profile_*` (`a144c7f5`).

Combined validation through source `9b67829` enables all fifteen correctness/speed switches with E1 runtime weight zero: every official pin, perft5, UCI lifecycle and all 256 baseline comparisons pass. Receipts: `tests/review_evidence/fifteen-switch-*`. The reproduction recipe and sequential patch README now include S6–S8; twenty-one exports reproduce that source. No speculative TT refinement was promoted into production.
