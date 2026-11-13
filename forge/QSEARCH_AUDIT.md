# Quiescence search audit

Forge 5.31.0 treated stand-pat as legal whenever the side to move was not in check. That is wrong when every legal move is a capture or a promotion. The static evaluation then hid a forced loss and could fail high inside a window that the true score does not reach. The correction searches those forced tactical moves. Checks, evasions, stalemate, and captures that sit beside a quiet move were already bound-correct on the positions below, and they stay that way.

This branch is not merged. The project version is still the extracted 5.31.0 sources plus this correction. No strength claim is made.

## Contract

`Searcher::quiescence` is a capture-and-promotion search with these rules:

- In check, search every legal evasion. Do not stand-pat. No legal move is mate, scored `-30000 + ply`.
- Stalemate scores 0, including when the static evaluation is positive and the window contains that positive value.
- A non-tactical legal move (anything that is not a capture or a promotion, including castling and double pawn pushes) makes stand-pat a legal floor. Only captures and promotions are searched from there. En passant is a capture. A quiet promotion is tactical.
- If every legal move is a capture or a promotion, stand-pat is not a legal choice. Those moves are searched the same way evasions are.
- Repetition, the 100-halfmove rule, and insufficient material still score 0, except that a side with no legal move in check is still mate.

## The bug

In `Searcher::quiescence`, the 5.31.0 code always applied stand-pat on a non-check node. Two paths did it:

- Before move generation, `stand_pat >= beta && beta <= 0` returned `beta`.
- After generating captures and promotions, `stand_pat >= beta` returned `beta` unless the capture list was empty and the position was stalemate. Otherwise `alpha` became `max(alpha, stand_pat)`.

`legal_moves(true)` contains captures and promotions. A non-empty list was treated as proof that stand-pat was optional. It is not optional when the side to move has no other legal move. A forced promotion into mate, or a forced capture that draws a dead position, returned the static evaluation.

Depth-1 search of the same positions was already right, because the root is a full-width node. The bad score appeared at the quiescence horizon and in any zero-window cutoff that trusted stand-pat.

## Reproduced scores

Measured by compiling the same probe against the unmodified 5.31.0 sources and against this branch. Mate score is 30000. `-29998` is mate at ply 2, which is what both a depth-1 search and a corrected quiescence search return for these one-move tactics.

| Position | FEN | Stand-pat | 5.31.0 qsearch | Depth 1 | This branch |
| --- | --- | --- | --- | --- | --- |
| White must promote | `8/P7/8/8/8/8/6q1/K1k5 w - - 0 1` | -720 | -720 | -29998 `a7a8q` | -29998 |
| Black must promote | `5K1k/1Q6/8/8/8/8/7p/8 b - - 0 1` | -720 | -720 | -29998 `h2h1q` | -29998 |
| White bishop must capture | `8/8/8/8/8/1k6/1p6/BK6 w - - 0 1` | +1 | +1 | 0 `a1b2` | 0 |
| Black bishop must capture | `6kb/6P1/6K1/8/8/8/8/8 b - - 0 1` | +1 | +1 | 0 `h8g7` | 0 |

The same probe measured the false fail-high windows on 5.31.0 and the corrected bounds:

| Window | 5.31.0 | This branch |
| --- | --- | --- |
| Promotion, `[-800, -720)` | -720 | -800 |
| Bishop capture, `[0, 1)` | 1 | 0 |
| Favorable stalemate `5k1K/7P/8/8/8/8/8/8 w - - 0 1`, `[0, 388)` | 0 | 0 |
| Evasion `4r2k/8/8/8/8/8/8/4K3 w - - 0 1`, `[-610, -530)` | -541 | -541 |

After `a7a8q`, Black is not in check. Both `g2a8` (capture of the new queen) and `g2b2` (quiet) mate. Quiescence sees the capture, so this fixture does not depend on searching quiet checks.

The favorable stalemate has static evaluation +288 and no legal moves. Both builds return 0 inside `[0, 388)`. The 5.21.0 fix for that case is intact. The in-check evasion has four legal king moves, static evaluation -530, and score -541 on both builds. It is not mate.

## The correction

Stand-pat is applied only when it is a legal choice, or when it cannot change the result:

- There is no capture or promotion to search (the existing stalemate probe still runs).
- `stand_pat <= alpha`, so raising alpha or cutting off on it would not change the returned bound. The tactical moves are searched anyway.
- A legal quiet move exists.

`Board::has_legal_quiet_move()` reports a legal move that is neither a capture nor a promotion. The scan runs only in the third case. In-check nodes still generate every legal move and never stand-pat. Transposition-table stores are unchanged: depth-0 entries, mate scores normalized by ply, and a deeper entry is not overwritten.

## Tests

`forge/tests/tests.cpp` adds `check_quiescence_forced_tactics`. For each forced-tactical fixture it checks that the position is not in check, that a legal move exists, and that none of those moves is quiet. Mate fixtures must match a fresh depth-1 search, score below -29000, score below stand-pat, and fail low on `[stand-pat - 80, stand-pat)`. Draw fixtures must score 0 at quiescence and at depth 1, with stand-pat above 0, and `[0, 1)` must return 0. A second quiescence call on the same searcher must return the same score. The board FEN is restored.

Two guards cover behavior that was already correct: the evasion above must be in check and score below stand-pat without being mate, and `4k3/8/8/2q5/8/8/8/2R1K3 w - - 0 1` must keep a winning rook capture while a quiet move exists.

`forge/tools/qsearch_audit.cpp` is a differential checker, not engine code. Its contract search implements the rules above with the same draw and mate conventions and a 200,000-node cap. A mismatch is an engine score that differs from that contract. A separate one-ply listing is diagnostic only, because a mate score probed at ply 0 can differ by one from the score stored inside the search.

Verification on this branch, g++ 13.3.0, C++20, `-Wall -Wextra -Wpedantic -Wconversion -Wshadow`:

- Release `ctest` target `forge_tests`: passed in 8.02 seconds.
- `forge_tests` rebuilt with `-O1 -fsanitize=address,undefined -fno-omit-frame-pointer`: `All tests passed`.
- `qsearch_audit`: 150,594 positions compared, 0 mismatches, 0 rejected FENs, 1 position skipped because the contract exceeded 200,000 nodes.

The audit set is 12 named positions, a structured sample, and a 30-game random walk of 24 plies. The structured sample places both kings, then either a white pawn on the seventh rank or a rim knight plus a black pawn. It keeps positions that are in check, have no legal move, or have a tactical move and no quiet move, plus a thin sample of positions that have both. The walk keeps checks, terminals, forced tactical positions, and every fourth ply. The named results after the fix:

| Label | Engine | Stand-pat | Legal moves | In check | Quiet move | Tactical move |
| --- | ---: | ---: | ---: | --- | --- | --- |
| Black checkmate | -30000 | -999 | 0 | yes | no | no |
| Black stalemate | 0 | -1010 | 0 | no | no | no |
| Favorable stalemate | 0 | 288 | 0 | no | no | no |
| Evasion, not mate | -541 | -530 | 4 | yes | yes | no |
| Winning rook capture | 562 | -470 | 11 | no | yes | yes |
| En passant available | 218 | 45 | 7 | no | yes | yes |
| Losing back-rank capture | -249 | -249 | 18 | no | yes | yes |
| Quiet mate in one | 1019 | 1019 | 25 | no | yes | no |
| Forced promotions, both colors | -29998 | -720 | 4 | no | no | yes |
| Forced bishop captures, both colors | 0 | 1 | 1 | no | no | yes |

On the losing back-rank position, the capture `c1b1` is answered by a quiescence score of -969. The root correctly stays at stand-pat -249 because quiet moves exist. That score is the same on 5.31.0 and on this branch.

The one skipped FEN is `r2qk1nr/3n1ppp/1pp2b2/p2pp3/1PP3bP/P4N2/2QPPPPR/RNB1KB2 w Qkq - 2 11`. The engine searched it. The independent contract did not finish inside the node cap, so that position is not evidence either way.

The default `c++` on the verification machine is Clang 18.1.3, and its link failed with `cannot find -lstdc++`. The builds above set the compiler to g++.

## What was left unchanged

Quiet checks are still outside quiescence. `k7/8/1K6/8/8/8/8/6Q1 w - - 0 1` is mate in one by `g1g8`. Depth 1 scores 29999. Quiescence returns stand-pat 1019 because all 25 legal moves are quiet. Forge 1.1.0 rejected a checking-quiescence experiment after a W11 L10 D11 screen because it cost about 9.3% more nodes. This audit does not reopen that search, and no test locks the 1019 score in place.

Stalemate that cannot affect the window still returns the normal alpha-beta bound. A fail-low with `alpha >= 0` is not reported as an exact draw.

`has_legal_quiet_move()` walks pseudo-legal moves when a tactical move exists and stand-pat is above alpha. The node counter does not include that walk. Existing node ceilings stayed green. No nodes-per-second claim is made.

Negative static-exchange and hard delta pruning stay removed, as in 5.17.0 through 5.19.0. This change does not put them back.

## Limitations

The contract and the engine share move generation, check detection, evaluation, and the draw rules. Agreement shows that quiescence follows those rules. It does not prove the shared pieces. The existing perft and legality tests still pass.

The structured sample is seventh-rank pawns and rim knights, not the full set of chess positions. One middlegame from the random walk exceeded the contract node cap and was skipped. Quiet checking moves are outside the contract on purpose.

The Python match, ponder, and UCI regression scripts, the opening book, and the validation corpora from the 5.31.0 archive are not in this tree. `ctest` registers those Python tests only when `tools/uci_regression.py` is present. The C++ suite is the verification that was run. `FORGE_BUILD_VALIDATION_TOOLS` still names the opening-corpus generator, and CMake adds that target only when `tools/generate_openings.cpp` is present. In this tree the option configures and skips the target.

Nothing on this branch was merged or promoted.
