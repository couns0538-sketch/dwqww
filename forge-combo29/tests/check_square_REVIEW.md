# Check-square ray-query hypothesis: static contract and locked-source counts

Scope: immutable lock `16833ecc03b425586f91f4c8834dea8807bf4c22`. Diagnostic files only; no production change, timing experiment, games, export or lock update.

## Exact proposed transformation

In `MovePicker::init_check_squares`, compute the bishop ray only if `board_.pieces(us, Bishop) | board_.pieces(us, Queen)` is nonzero, otherwise assign **zero** to the Bishop slot. Likewise compute the rook ray only if `pieces(us, Rook) | pieces(us, Queen)` is nonzero, otherwise assign zero to the Rook slot. Assign Queen to the OR of the two resulting slots, and retain Pawn, Knight and King initialization. Occupancy and enemy king square remain exactly unchanged when a query is executed.

This preserves slots for all actually scored piece types; it need not preserve a slot for a piece type absent from the current moving side. Initializing skipped slots to zero is required: NO_ZERO_MOVELISTS can leave storage uninitialized, and Queen initialization reads both component slots even when no queen exists. Merely omitting the assignment is not safe.

## Proof under the existing Board / MovePicker contract

1. Board's square array and colored piece bitboards agree. Generated moves originate from the moving side's pieces. `Board::moved_piece(move)` is exactly `piece_at(move.from)`; it is not the promotion result.
2. SPEED2=0 `direct_check` and SPEED2=1 `QuietScorer::score` both index by this same original piece type. They do not infer a slider type from destination, capture victim, promotion field or castling rook.
3. If a scored piece is Bishop, that side's Bishop bitboard is nonzero, so its Bishop query is retained verbatim. The Rook case is identical. If a scored piece is Queen, the Queen bitboard makes **both** predicates true, so its OR is unchanged. Pawn, Knight and King slots are always unchanged. This proof permits multiple/promoted sliders and unreachable but internally consistent parser-accepted boards.
4. `generate_captures` never initializes or reads check squares. Both capture scorer implementations use capture value/history and promotion bonuses only.
5. For NO_ZERO_MOVELISTS < 2, quiet generation explicitly skips all captures and promotions before either scorer. For >= 2, `GenMode::Quiets` excludes the entire promotion/capture/en-passant block, selects only empty destinations for pieces, and emits ordinary pawn pushes plus castling. Pawn promotion pushes are specifically excluded despite not having Capture set.
6. Evasions generate the full pseudo-legal list, but every capture **or promotion** takes its dedicated material-score branch before either quiet scorer. En passant carries Capture. Thus a promotion cannot require a newly promoted slider's slot; even if a future scorer did read the original pawn slot, that slot remains unchanged.
7. Castling quiet score reads King and receives the same zero direct-check bonus. This shortcut preserves the existing approximate direct-check heuristic, including its existing treatment of discovered checks and rook checks from castling; it does not improve or redefine check detection.
8. The picker and its referenced board are used for one node's position. Recursive search restores the board before obtaining another move; existing cached check squares already rely on that invariant. Quiet/evasion initialization stages are mutually exclusive and reached at most once per picker. TT/killer/counter stages do not read check-square slots.

Counterexamples to overly broad shortcuts: testing Bishop alone or Rook alone would corrupt Queen scoring on queen-only material; skipping uninitialized slot writes would read indeterminate values when forming Queen; using the opponent's inventory would be incorrect. Presence of only pinned sliders still requires retaining the query because scoring precedes full legality filtering.

## Measurement scope

`check_square_calls.py` explicitly extracts only src/include files from the immutable commit into a temporary build tree. It records per-file hashes, compiler/flags, binary hashes, commands and raw stdout/stderr. Baseline and instrumented builds cover SPEED2=0/1 with the lock's NO_ZERO_MOVELISTS=2. Each runs depth 16, Threads 1, OwnBook false, NNUE on/off. Process-local counters separate quiet generation from evasion generation and count absent Bishop|Queen, absent Rook|Queen, and both absent. Fresh processes avoid accumulated counters. No source in the repository is altered.

Counters are not speed measurements. They add work and alter compiler layout. Existing reported bench times in raw output must not be used to estimate gains. Runtime configurations NO_ZERO_MOVELISTS=0/1 are covered by the static contract, not by this count run. No full candidate equivalence or sanitizer claim is made here.

## Completed immutable-lock count results

Both SPEED2 paths produced identical counts. All eight baseline/instrumented depth-16 runs retained exact nodes: 3,024,920 NNUE-on; 2,448,617 NNUE-off.

- NNUE-on: 447,038 initializations (296,865 quiet, 150,173 evasion). Absent B|Q: 189,918; absent R|Q: 87,170. Together 277,088 of 894,076 original ray queries could be omitted (30.99%). Both absent in 87,017 calls.
- NNUE-off: 349,061 initializations (219,875 quiet, 129,186 evasion). Absent B|Q: 92,287; absent R|Q: 39,572. Together 131,859 of 698,122 ray queries could be omitted (18.89%). Both absent in 39,281 calls.

Pristine GCC 14 PEXT code inlines both ray queries directly into each quiet/evasion arm of `MovePicker::next(bool)`. In SPEED2=1 the two pairs of PEXT instructions appear at offsets 0x1a0/0x1c1 and 0x768/0x789; SPEED2=0 pairs are 0x1a2/0x1c3 and 0x7ea/0x80b. Each uses the corresponding magic-mask and table-pointer loads with no piece-presence guard. The opportunity is therefore not already eliminated in this inspected compiler configuration.

## Temporary default-off prototype codegen screen

`check_square_codegen.py` creates a temporary candidate from the same verified source-only snapshot. Its only proposed edit is retained in `check_square_prototype.patch`; production remains untouched. The macro `FORGE_SPD_CHECK_SQUARE_PRESENCE` defaults to zero and keeps the original two assignments verbatim under `#else`.

Both SPEED2=0 and SPEED2=1 complete search objects are byte-identical between pristine lock and prototype-off, under identical compiler/path/command. This is object identity, not yet a full production-binary gate. Prototype-on emits real branches around the PEXT/magic-mask, table-pointer and result loads. It pays for moving-side index selection, three inventory loads, two OR predicates and two conditional skips per initialization. GCC adds a color branch for the three piece indices rather than deriving all indices branchlessly. The same six callee-saved registers and stack reservations remain at the MovePicker prologue (SPEED2=1 remains 0x38 bytes); no new function calls are introduced by the predicates.

MovePicker::next text grows from 7,546 to 7,738 bytes (+192) with SPEED2=0, and 6,681 to 6,841 (+160) with SPEED2=1. Static PEXT instruction count stays four: the change is dynamic avoidance, not deletion of the instructions from the binary. Side-selection/branch costs, cache behavior and extra code footprint can erase the count-based opportunity. No runtime speed conclusion follows.

Recommendation: the exactness argument and confirmed dynamic query opportunity justify testing this small default-off prototype further, not promoting it. Before production adoption, require independent review, guarded/original score and move-order equivalence across scorer and quiet-generation modes, sanitizer checks with absent sliders/queen-only/promotion/castling/pinned fixtures, default-off full-binary identity and standard exact search gates. Timing must be separately preregistered/coordinated and cannot be inferred from these runs. Native speed and Elo remain UNPROVEN.

## S11 source freeze and validation design

Following the diagnostic-only phase, the exact default-off prototype was authorized for production validation and frozen as source commit `1e6c398dec7717868a740f5d322cf7434336345f`, after evidence checkpoint `2da946c`. No other production source changed. Its acceptance status remains disabled and UNPROVEN for speed/strength.

`check_square_unit.cpp` exercises the real implementation-local MovePicker, not a standalone mask imitation. For every board it calls production quiet/evasion/capture generation, verifies the complete generated move/score list against original unconditional-ray scoring, and then compares every actual `pick_best` output to the locked first-four-selection/sorted-tail ordering policy. Main history is seeded with nonzero signed values. Check-square storage is poisoned before initialization; absent B/R slots must become zero. This catches a missing write even though the absent slot itself cannot affect a valid moved-piece score.

The corpus starts with 16 targeted positions (both-color queen-only or single-slider inventories, neither slider, pinned bishop/rook/queen, both castling sides, capture and quiet promotions, check/evasions and en passant), plus all 128 frozen search fixtures. Deterministic 24-ply continuations expand this to 3,310 board visits. Each configuration compares 178,822 generated scores and selected moves, with 328 promotion occurrences, 138 castling occurrences, 1,007 absent-B|Q boards, 751 absent-R|Q boards and 56 queen-only boards. The nonking-illegal counter includes pinned moves and other nonking illegal pseudo moves; it is not a pure pinned-slider count. No strength inference follows from these fixture counts.

The validator uses explicit source/header snapshots and one build path for lock/off identity. Unit matrix: SPEED2=0/1 crossed with NO_ZERO_MOVELISTS=0/1/2, all under ASan+UBSan (LeakSanitizer disabled, portable slider/NNUE paths). Each configuration compiles its generation-mode dependencies consistently. It does not exercise AVX-512 under sanitizers. Three scratch-only mutations remove queen participation from either presence predicate or poison a skipped slot; expected failures must be explicit test assertions, not crashes accepted as evidence.

Completed outcome: all six sanitizer matrix entries pass with identical fixture/score/selection counts and no sanitizer diagnostics. All three deliberate mutations fail the intended assertions (queen omissions: generation score at board 1; poisoned absent slot: board 2). Enabled full ten official bench pins and startpos perft5 pass. All 256 depth-7 search comparisons match nodes, score, PV and best move. Immutable-lock and S11-off complete executable SHA256 are both `1371770e2ad61aa2fe3c038acc7da3912da5d64c9cb1dcc5e4668221fb3226f6`; S11-on is `6c8b321ff302cf736d278d315a3a7f426a8d3c85b8db60c7e68c2e5ffe984ad4`. All three binary hashes were rechecked after the run. Receipt, raw pin output, equivalence report and complete commands are `check_square_validation.json`, `check_square_pins_raw.log`, `check_square_equivalence.json` and `check_square_validation.log`.

These are finite semantic/sanitizer gates, not proof of all runtime states, performance acceptance or Elo. No timing experiment has yet been run.

## Subsequent fixed diagnostic

The separately preregistered four-cycle depth18 diagnostic completed once, preserving 32 measured samples plus four warmups with exact nodes and unchanged binaries. Median paired-block candidate/baseline child-CPU duration ratios were 1.001718 NNUE-on and 1.008900 off; wall ratios 1.001775 and 1.008544. Blocks crossed parity in both modes. These noisy near-neutral-to-slower observations do not support promotion and do not establish a native regression. No favorable-result rerun was performed. Complete protocol, ratios and raw evidence are in `check_square_profile_*`. Correctness evidence remains valid; default-off and native speed/Elo UNPROVEN status are unchanged.
