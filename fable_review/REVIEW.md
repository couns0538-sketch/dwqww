# fable-review-buffix — bounds fix for the move picker's deferred-capture buffer

Base: `d4f4312` (AL1 s198 lock) + the CI workflow file of `fable-nnue-arch` (trigger on `fable-*`, report/log
paths ignored, job cap 60 min, which is ample for this branch's 1.5-minute runs; the R3 stack's runs take 25-30 min). Found during the Fable review of the Opus jobs
(`FABLE_REVIEW_OPUS.md` on branch `fable-review-summary`).

## The mistake

`MovePicker::bad_captures_` is `std::array<Move, 64>` and is written at `src/search.cpp:361`
(`bad_captures_[bad_count_++] = move;`) without a bounds check: every generated noisy move whose static exchange
evaluation fails the picker's threshold (`see_ge(move, -move_score_threshold(move))`) is deferred into it. Capture-promotions count four times each (Q/R/B/N), so a constructed position
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

## Independent check (2026-10-28)

A second reviewer rebuilt the branch from a fresh worktree (FMA 0, identity ALL OK, test 5/5) and confirmed the
three hunks are byte-identical to the archived patch. Remark kept for the next model: the archived regression
test's stress positions reach at most 50 SEE-losing noisy moves, below the old limit of 64, so the test does not by
itself demonstrate the overflow; a position with more than 64 SEE-losing noisy moves (many queens taking defended
minor pieces) would. The fix is correct independently of that: every generated noisy move (at most
`MoveList::Capacity`) can be deferred once, so `Capacity` is exactly the right size.

## Overflow demonstrated (2026-10-28, deep pass)

The remark above is resolved: `tests/bad_capture_tests.cpp` now carries a sixth fixture, `many-losing`
(`3r4/Pn1Q1p2/1Q1n1QpN/1p1Q1pRB/1Qbp1QpN/2bQ1pRB/3r1QpK/2k2q2 w - - 0 1`, a legal position the engine's own FEN
parser accepts: 16 white pieces, king, eight queens of which seven are promoted, two rooks, two bishops, two knights
and one pawn on a7, whose four promotions are the four promotion moves of the census; 16 black pieces), whose
engine census is 69 pseudo-legal noisy moves, 68 of them SEE-losing (`see_ge(move, 0)` false, which is exactly what
the picker defers), 68 legal, 4 promotions, not in check. The fixture asserts `losing >= 65` with the other counts.

- Fixed engine (this branch, `std::array<Move, MoveList::Capacity>`), built with `-D_GLIBCXX_ASSERTIONS` so every
  `std::array::operator[]` is bounds-checked: all 6 fixtures pass, depth-3 search completes
  (`fable_review/logs/overflow_proof_fixed.log`).
- Unfixed engine (the same tree with `std::array<Move, 64> bad_captures_`, the AL1 lock's declaration, built the
  same way): the test aborts in the picker with
  `std::array<forge::Move, 64>::operator[]: Assertion '__n < this->size()' failed`
  (`fable_review/logs/overflow_proof_mutant.log`), i.e. the 65th deferred capture is written past the buffer.

How the position was found: an annealing search over piece placements (python-chess for legality, the engine's own
census over a pipe as the objective, `fable_review/tools/fable_nnue_losing_search2.py` + `fable_census.cpp`); the
inventory rule of `Board::set_fen` (promoted pieces at most 8 minus pawns, 16 pieces, kings apart) is the binding
constraint, and a python-only SEE overestimated the engine's count by 4-5, so the engine had to be the judge.
Tools and logs: `fable_review/tools/`, `fable_review/logs/overflow_proof_*.log`, `fable_review/logs/prove.log`.
