# C6 [Engine Strategist] Upcoming-repetition detection via cuckoo tables (UCI CuckooRep, default false) — DONE

Branch `opus-C6` = `opus-O3` (`0d99f02`) + [C6] commits:
- `2cb0bab`: detector + table
- `147395c`: UCI option + search bound
- `3ce0679`: tests
- `4d14f3c`: halfmove pre-test, the last engine-code change
- `f9b1445`, `70c6257`: evidence only

`patch.diff` = `git diff 294dbed HEAD` (engine tree incl. O3); `patch_c6_only.diff` = C6 on top of `0d99f02`.
Ideas: `IDEA_SOURCE.md` (M. van Kervinck 2013; CPW "Repetitions"; concepts only, own code).
UNPROVEN until gated; no Elo claim.

The implementation was done by a sub-agent and reviewed by the main session. The review rebuilt the engine
with the PC lock recipe and re-ran:
- the default identity at all 5 depths;
- the ON bench pin at d11;
- a perpetual-check position at depth 3 with the option on and off;
- a diff of the hot functions' machine code.

All matched the evidence below.

## Acceptance

| # | acceptance line | result |
|---|---|---|
| 1 | table of all reversible non-pawn moves has exactly 3668 entries; insert/lookup round trip exact | **PASS**: 3668 = 2 x (N 168 + B 280 + R 448 + Q 728 + K 210), 3668 exact round trips, 3668 of 8192 slots, 0 stray hits on 10^6 random keys; also a `static_assert` |
| 2 | brute-force reference agrees on 10,000 random reversible-move sequences + 50 hand-written positions, 0 mismatches | **PASS**: 10,000 sequences (334,860 plies, 14,902 null moves), 669,720 comparisons (121,657 positive) + 51 hand-written positions, 0 mismatches |
| 3 | respects the rule-50 window and the ply-from-null limit (reuse rule50_tests) | **PASS**: board-level edge cases and a node-level probe in the rule50_tests style |
| 4 | ON: draw score in >= 5 known repetition-draw positions where OFF does not | **PASS, 6/6**: forced perpetual checks; depth 3 OFF −719/−637/−719/−637/−933/−925, ON 0; at depth 8 both give 0 |
| 5 | OFF: bench exact | **PASS**: d11/13/16/20/22 = 312866/862329/3024920/12389307/34048354, perft5 4865609, kiwipete 193690690, FMA 0 (PC recipe, re-checked in review; Linux CI g++-14) |
| §3 | ctest only the known failures | **PASS**: 17/18, only `forge_tests` with its 4 known lines (local and all 3 CI jobs) |
| §3 | ASan+UBSan; TSan | **PASS**: 0 reports (CI run 40410916145); TSan hook runs CuckooRep at Threads 2 and 4 |
| — | tests catch planted bugs | **PASS, 15/15** (`mutation_check.py`) |

## How it works

### Board level: `Board::upcoming_repetition(root_index)` (src/board.cpp, include/forge/board.hpp)
- **Meaning (also the test oracle).** True iff some legal move of the side to move leads to a position for
  which Forge's own `Board::is_repetition(root_index)` holds. That is the search's draw rule: one earlier
  occurrence at or after the root, or two before it, inside the window min(halfmove clock, plies since a
  null move, history length).
- **Implementation (no move generation):**
  - scan the key history at odd distances 3, 5, ... inside the child's window;
  - require the opponent's moves since then to cancel (running XOR of the key deltas is 0);
  - look up `key ^ key(then)` in the cuckoo table;
  - require that move to be playable now: the right piece and colour on one square, the other square empty,
    and the path between them empty.

  A target inside the tree counts once; a target before the root needs a second occurrence. Such a move is
  always legal, because it recreates a legal position.
- **Cuckoo table.** `constexpr`, built at compile time. It holds 3668 entries in 8192 slots with two candidate
  slots per key. On Windows it is placed after all other read-only data (`.rdata$zz_forge_cuckoo`), so no
  existing table moves inside its cache line. The new board functions are `[[gnu::cold]]`.

### Search level (src/search.cpp, src/search/{cuckoo,alphabeta,qsearch,iterative,options}.inc)
- **Two compiled instances.** `alphabeta.inc` and `qsearch.inc` are compiled twice.
  - The first instance is the unchanged `Worker::search` / `Worker::qsearch`.
  - The second (`search_cuckoo_body` / `qsearch_cuckoo_body`, at the end of the unit) reaches its children
    through `Worker::search_cuckoo` / `Worker::qsearch_cuckoo` (cuckoo.inc).
- **The bound.** At a non-root node with alpha < 0 and no excluded move, if a repetition is reachable:
  - with beta <= 0 the node fails high at 0;
  - otherwise it is searched with alpha = 0 and the result is kept at >= 0.

  This floor matters. Without it, pruning can still fail the node low below 0 after the drawing move was
  skipped; that version found 5 of the 6 perpetuals no earlier than OFF did. An inline pre-test (halfmove
  clock >= 3) skips the detector right after captures and pawn moves.
- **Option read.** The root reads `options::cuckoo_rep` once per iteration and calls `search_cuckoo` or
  `search`. With the option off, no node tests it.
- **UCI.** `option name CuckooRep type check default false`. The option lives in
  `forge/search_options.hpp` / `src/search/options.inc`, the same files O1 uses.

## Evidence (opus_round1/C6/logs)
- `cuckoo_tests.log`: `forge_cuckoo_tests` covers items 1-4: table, hand-written and random comparisons,
  rule-50 and null-move windows, node-level probes, the 6 search draws. PASS, 312,089 checks.
- `draw_scan_depth1-8.log` (`draw_scan.py`, `draw_positions.txt`): the 6 perpetuals at depths 1-8, OFF vs ON.
- `identity_pc_recipe.log`: the default identity at all 5 depths. CI: `ci/release/identity.log`.
- `mutation_check.log`: the 15 planted bugs, all caught:
  - clock window off by one;
  - null window ignored, and null window off by one;
  - a single pre-root occurrence counted, and the second pre-root occurrence ignored;
  - path check removed;
  - second cuckoo slot not probed;
  - move key without the side key;
  - opponent filter removed;
  - search bound disabled, and qsearch bound disabled;
  - halfmove pre-test off by one;
  - search floor removed, and qsearch floor removed;
  - root dispatch ignores the option.
- `ci/RUN.log`: CI run 40410916145 on `f9b1445` (the same engine code as `4d14f3c`):
  - release: identity ALL OK, FMA 0, ctest 17/18 with only the 4 known lines;
  - asan (ASan+UBSan): same ctest result, no report;
  - tsan: same ctest result, and the CuckooRep hook passes with 0 reports.

### Hot code, data layout and NPS (option off)
- `codegen_lock_vs_c6.log`, from `O3/codegen_compare.sh`, lock exe vs C6 exe:
  - qsearch, static_evaluate, TT probe/store, should_stop, is_draw, the correction and history functions,
    record_move, NNUE update/evaluate/refresh, make/unmake and see_ge are identical at the same address
    mod 64.
  - `MovePicker::next` shows 32 "differing" lines. The review diffed it and found the instructions
    identical. Only the RIP-relative displacements to moved data differ, plus 32 nops of trailing padding.
  - **Alpha-beta `Worker::search(Board&, ...)`: fixed after delivery, now instruction-identical to the lock**
    (0 differing lines, same start mod 64; `logs/codegen_lmp_copy_fix.log`).
  - The delivered version (`4d14f3c`) had 2409 vs 2413 instructions, with 150 normalised lines differing in
    basic-block order. Its start mod 64 and its call multiset were the same, and it never read the option. The
    second instance in the same translation unit flipped the operand order of one comparison inside GCC
    (`gimple_search_one_vs_two_instances.diff`). Six layout experiments gave the same 150 lines
    (`codegen_variants/EXPERIMENTS.txt`); variants that tested the option at every node were worse (324 to 913
    lines).
  - The root cause was found in job O5 (`opus-O5`, `opus_round1/O5/logs/codegen_second_instance_investigation.log`).
    The static helper `lmp_threshold` has one caller in AL1 s198, and the early inliner inlines it. A second
    caller (the second instance) leaves it to the IPA inliner, which shifts the SSA numbering of the default
    search.
  - The fix (`src/search/cuckoo_lmp.inc`, macro `FORGE_LMP_THRESHOLD` in alphabeta.inc): the CuckooRep instance
    calls its own copy, `lmp_threshold_cuckoo`.
  - Re-checked with the fix: bench x5, perft and kiwipete identical, FMA 0; CuckooRep ON pins unchanged (d11
    324211, d13 790682); `forge_cuckoo_tests` passes, 312,089 checks (`logs/lmp_copy_fix_identity.log`,
    `logs/lmp_copy_fix_cuckoo_tests.log`).
- `data_layout_check.log`: hot tables moved by whole pages. `DistanceMasks` keeps mod 64. The cuckoo table
  and the option flag are new.
- `nps_ab_lock_vs_c6_off.log`: `nps_ab.py`, 10 ABBA runs, on the busy PC, node counts equal in every run:
  - d16 wall −0.08% [−1.92, +1.77], CPU −0.03%;
  - d20 wall +0.60% [−2.79, +3.99], CPU +0.72%.

  No measurable change.
- `logs/ci/nps_0994d36/` (workflow `opus-c6-nps.yml`, run 40464096680): the same A/B on a quiet GitHub runner
  (g++-14 box recipe, 10 ABBA runs, node counts equal), added in review because of the alpha-beta block order:
  - O3 → C6 (C6's own share): d16 CPU −0.26% (95% CI −1.01 .. +0.50), d20 CPU +0.05% (−0.64 .. +0.73);
  - lock → C6: d16 CPU +0.88% (−0.48 .. +2.24), d20 CPU +1.70% (+0.69 .. +2.72).

  The block-order change in the default alpha-beta costs nothing measurable.

### With the option on (informational)
- **Bench nodes:** d11 324211 (re-checked in review), d13 790682, d16 3148570, d20 10326301, d22 31204053
  (`on_bench.log`).
- **Per-node cost:** about 1%, measured with tree-identical scratch variants (−0.8% / −1.1%,
  `on_speed_experiments.log`). Bench nps ON/OFF is 0.94-0.96, which includes the different tree.

## Proposed gate (one option)
- **Candidate:** opus-C6 exe (PC lock recipe) with `option.CuckooRep=true`. **Opponent:** the AL1 s198 lock
  exe (833C47F3…22B3).
- **Settings,** per `6_gate/GATE_RULES.md`: fastchess, 10+0.1, Threads 1, Hash 16, OwnBook false, the gate
  openings book, SPRT [0,10].
- **Seed and ID:** a new srand chosen by QA. The test plan has no C6 row yet, so QA assigns the gate ID.
- **Confirmation:** this is a search change, so an H1 result gets the standard confirm gate.

No Elo claim.

## Open issues / notes
- **Default alpha-beta block order:** fixed after delivery (own `lmp_threshold` copy for the CuckooRep
  instance). The default alpha-beta is now instruction-identical to the lock. Even before the fix, NPS showed
  no measurable effect, on the busy PC or on a quiet runner (O3 → C6 −0.26% / +0.05%).
- **Untested guard:** the guard that skips the bound while a move is excluded (singular verification) has no
  dedicated unit test.
- **History dependence:** the draw bound depends on the game history, while TT entries do not. This is the
  usual graph-history issue that repetition draws already have; the bound itself stores nothing extra in the
  TT.
- **Code size:** the second search instance adds about 19 KB of `.text`, placed after the default search
  functions.
- **Merge conflict with O1:** O1 also creates `search_options.hpp` / `options.inc`. Merging means keeping
  both option lines.
- **Housekeeping for the user, not part of the branch:**
  - The sub-agent's mistyped `cp` left a stray file `C:\Program Files\Git\tmp_c6_search.cpp` (2669 bytes). The
    safety rules blocked its deletion; please delete it by hand.
  - Scratch build folders `D:\grok-pc-data\dwqww\.claude\worktrees\b\c6_*` remain, because recursive
    deletion is not allowed in this session.

## Files
- Engine and tests: `src/board.cpp`, `include/forge/board.hpp`, `src/search/cuckoo.inc`,
  `src/search/{alphabeta,qsearch}.inc` (name macros only), `src/search.cpp`, `src/search/iterative.inc`,
  `include/forge/search.hpp`, `include/forge/search_options.hpp`, `src/search/options.inc`, `src/uci.cpp`,
  `tests/cuckoo_tests.cpp`, `CMakeLists.txt`.
- `opus_round1/C6`: `REPORT.md`, `IDEA_SOURCE.md`, `patch.diff`, `patch_c6_only.diff`, `draw_positions.txt`,
  `draw_scan.py`, `on_bench.py`, `data_layout_check.py`, `mutation_check.py`, `cuckoo_smp.py`,
  `tsan_extra.sh`, `logs/`, `SHA256SUMS`.
