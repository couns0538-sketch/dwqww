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

`tests/thread_exception*` inject EAGAIN on second helper creation with Threads 3: child receives SIGABRT 6 with 'terminate called without an active exception'. First-helper failure is catchable std::system_error 11; uninjected control succeeds. Minimal fix: stop/join on exceptional exits and transport helper exceptions after joins. Patch `F4-exception-cleanup.patch`, switch `FORGE_FIX_SMP_EXCEPTIONS=1`, now joins all started helpers before propagating exceptions. Startup failure, injected main/helper bad_alloc and repeated successful searches pass with F4 alone and with F3. Internal shutdown never overwrites external stop. This is library exception safety, not end-to-end UCI resource-failure recovery: the outer UCI worker still has no exception handler. See `tests/thread_exception_REVIEW.md`. Status **UNPROVEN**.

### F5 LOW: first-use attack initialization races
Confidence **high, reproduced with ThreadSanitizer and unsanitized scheduling**. `src/bitboard.cpp:136-139` uses a plain static bool and publishes true before tables are constructed. Simultaneous first calls can read incomplete tables.

Patch `F5-init-once.patch`, switch `FORGE_FIX_ATTACKS_INIT_ONCE=1`, wraps unchanged initialization in std::call_once. See `tests/ATTACKS_INIT_REVIEW.md` and `tests/attacks_init_concurrent.cpp`: baseline TSan exits 66 with data race; enabled exits 0 without diagnostics; unsanitized baseline premature-return failure reproduced and enabled passed 10 fresh-process repeats. Normal UCI constructs its first Board before launching workers, so normal CLI reachability is not established. Status **UNPROVEN**.

### F6 LOW: UCI option names are case-sensitive
Confidence **high, reproduced**. `src/uci.cpp:205,219-280` compares option names exactly, ignoring alternate casing despite UCI's case-insensitive option-name rule. `setoption name usennue value false` leaves bench 11 at 312866; canonical UseNNUE disables net and produces 375354.

Patch `F6-uci-case.patch`, switch `FORGE_FIX_UCI_OPTION_CASE=1`, compares option names with ASCII case folding and preserves values/file paths. Regression `tests/uci_option_case.py BASELINE CANDIDATE` passes both NNUE cases plus mixed-case multiword names, tunables, Hash and Threads. Clear Hash dispatch is source-reviewed; its side effect is not directly tested. Status **UNPROVEN**.

## No defect established in these checks

No TT race/UB established under documented quiescent lifecycle contract. No legal-position move-generation defect found in source review and tests. This is not a proof of absence.

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

All **UNPROVEN**, no patches or parameter changes made. Any implementation must be independently default-off behind UCI control. Locations refer to review snapshot b6e896f. Ranking is experiment priority, not predicted Elo.

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
