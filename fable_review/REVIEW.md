# fable-review-buffix — bounds fix for the move picker's deferred-capture buffer

Base: `d4f4312` (AL1 s198 lock) + the `fable-*` CI trigger. Found during the Fable review of the Opus jobs
(`FABLE_REVIEW_OPUS.md` on branch `fable-review-summary`).

## The mistake

`MovePicker::bad_captures_` is `std::array<Move, 64>` and is written at `src/search.cpp:361`
(`bad_captures_[bad_count_++] = move;`) without a bounds check: every generated noisy move that fails
`see_ge(move, 0)` is deferred into it. Capture-promotions count four times each (Q/R/B/N), so a constructed position
can exceed 64 deferred moves and the write runs past the array (undefined behaviour, a stack overwrite in the lock
engine). Opus job S14 documented this ("bad_captures_[64] unguarded, buffix not in AL1") but did not fix it; the
CR-passed, node-identical fix was already in the lock archive
(`7_history/strength_packs/buffix_node_identical/fc_sol_buffix_h256e12_vs_lock.patch`, "applies to AL1") and was
never applied.

## The correction

The archived patch applied verbatim (`patch -p1 -F0`): the buffer becomes `std::array<Move, MoveList::Capacity>`
(256, the generator's own capacity, so every noisy move can be deferred once) with a `static_assert`, plus
`tests/bad_capture_tests.cpp` (ctest `forge_bad_capture_tests`: SEE census of stress positions, a deferred losing
capture surviving a root restriction, depth-3 searches with legal PVs). No search logic changes: the fix is
node-identical by construction (only the array capacity changes).

## Evidence (logs in `fable_review/logs/`)

- `build_pc.log`: box recipe, FMA 0, 0 warnings.
- `identity.log`: bench d11/13/16/20/22 and perft5 / kiwipete against the AL1 pins (must be `ALL OK`).
- `bad_capture_tests.log`: the new regression test.
- CI: opus-ci on this branch (release identity, ASan+UBSan, TSan).
