# T12B-01-bad-captures-overflow: the lock's 64-entry bad-capture buffer overflows on a legal FEN; merge the node-identical fix
Status: COMPLETE

## Source
Own: lock src/search.cpp:361 (unguarded write), :398 (read-out), :453-454 (array, then the counter). Own fix and proof:
branch fable-review-buffix 8632e8ab (fix a9cea71f, fixture commit ab2aa56b, tests/bad_capture_tests.cpp:141), logs
F:/opus_scratch/fable_review/buffix64/prove.log, final_mutant.log, final_fixed.log. Same bug class elsewhere (commit
messages only): https://github.com/official-stockfish/Stockfish/commit/c56bd10cb5 (read past the filled part of a move
list, "really rarely triggered", PR 6235), /commit/ee515ad (root PV longer than MAX_PLY; T04 row 9), Caissa 136d3d0
(overflowed tried-move list; T04 row 8).

## Licence
Lock, fix and fixture: own. Stockfish @c56bd10cb5 GPL-3.0 (row in notes/T12B/licences.md): ideas only, commit
messages read, no source or diff. Caissa MIT (row in notes/T04/licences.md).

## Mechanism
In a main-search node that is not in check, the GoodCaptures stage tests every generated noisy move (pseudo-legal
captures plus all four pieces of every promotion, before the legality test) with SEE >= 0 and appends each loser to
bad_captures_ with no size test. The 65th loser lands at index 64 = the low 4 bytes of bad_count_ (declared directly
after the 256-byte array, no padding), so the counter becomes that move's bytes, at least 2^24 because a noisy move's
flags byte is non-zero. With exactly 65 losers this is benign by luck (read-back gives the 65th move, then a zero word =
none, which ends the loop). From the 66th loser on, writes land 64 MiB or more past the array (wild write, typically an
access violation), and read-back hands a 65th move whose from byte was advanced by the extra count to is_legal
(search.cpp:1051, no pseudo-legality test): undefined behaviour. Reachable: the buffix census (the engine's own board code) found a set_fen-accepted, not-in-check
FEN with 69 noisy and 68 SEE-losing moves (4 promotions): `3r4/Pn1Q1p2/1Q1n1QpN/1p1Q1pRB/1Qbp1QpN/2bQ1pRB/3r1QpK/2k2q2
w - - 0 1`. It needs many promoted queens, so gates and self-play will practically never meet it; any GUI user, fuzz
run or imported FEN can. This corrects T04 row 9 ("likely unreachable").
Fix (already written, a9cea71f): size the array to MoveList::Capacity (256) plus a static_assert. Each generated move is
deferred at most once, so the buffer cannot overflow while the generator list itself holds (TABLE A2). A drop guard
(`if (bad_count_ < 64)`) is rejected: it silently removes legal moves from the search.

## Forge fit
NO in the lock (`forge_has.sh 'bad_captures_|bad_count_'`: search.cpp:361, 398, 453, 454; 64 entries, no guard). The
O30 trees checked (D:/o30/plain/spsa_1, v2port_1, harness/h1) still declare `std::array<Move, 64> bad_captures_` and no
R15 patch touches it (0 grep hits under D:/o15/cands), so every lock-line candidate inherits the bug. Fixed only on
fable-review-buffix and fable-review-r3-stack (b0c3882b, both #if variants). Lock-line owner item since 2026-10-28.

## Expected gain
Source: no Elo number exists for this bug (correctness). Proof numbers: the 64-entry mutant aborts on the 68-fixture
under -D_GLIBCXX_ASSERTIONS (exit 127, final_mutant.log); the fixed engine passes 6/6 fixtures and searches the
68-fixture normally (depth 3, 396 nodes, bestmove d3b1, prove.log); identity bench x5 / perft5 / kiwipete ALL OK.
Forge estimate: 0 Elo, UB removed in > 64-loser nodes, frequency in play unknown (near zero) **UNPROVEN**; nps effect
of the larger zero-filled array (+768 B per picker) unmeasured **UNPROVEN**.

## Effort
Crew 1-1.5 h: cherry-pick a9cea71f + ab2aa56b onto the lock tree / next candidate, pins, CTest, ABBA. CPU ~0.5 h of one
core (ABBA). No SPRT games, no GPU.

## Test plan
1. Pins: bench d11/13/16/20/22 = 312866/862329/3024920/12389307/34048354, perft pins unchanged (node-identical).
2. forge_bad_capture_tests (6 fixtures) in a -D_GLIBCXX_ASSERTIONS build: the 64-entry mutant must abort, the fix pass.
3. Crew check: does the CI ASan+UBSan row flag the mutant? The first bad write stays inside the picker object, which
   ASan does not see; if the row misses it, add -D_GLIBCXX_ASSERTIONS to that row (T12B-02).
4. Gate route: node-identical, so nps ABBA only (stack frame and zero-fill grow); no SPRT. Pair it with T05C-02
   (default-initialised picker arrays), which makes the larger array free.

## OFF-by-default design
No option needed: node-identical. Every node with <= 64 SEE-losing noisy moves stores and reads the same moves in the
same order, so OFF = ON = lock pins; the bench never reaches 65 (identity ALL OK). Only nodes where the lock has
undefined behaviour change.
