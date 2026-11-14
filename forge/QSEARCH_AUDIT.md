# Quiescence search audit

This note is the record of the audit on `cursor/forge-qsearch-audit-60ce`. It says what was wrong in Forge 5.31.0, what the search found around that bug, and what this branch changes. The branch is not merged. The version string is still 5.31.0. No strength claim is made.

## What was wrong

`Searcher::quiescence` is the search used when the main depth reaches 0. Its job is tactical: captures, en passant, and promotions. A quiet move is anything else, including castling and a double pawn push. Stand-pat means "decline the capture and take the static evaluation." That is a legal choice only when the side to move has a quiet legal move it could play instead.

Forge 5.31.0 treated stand-pat as legal on every node that was not in check. The old function did this in two places, both before it would allow a bad tactical move to lower the score:

1. Before generating moves, if the side was not in check and `stand_pat >= beta && beta <= 0`, it returned `beta`.
2. After `legal_moves(true)` (captures and promotions only), if `stand_pat >= beta`, it returned `beta`, except when that list was empty and the position was stalemate. Otherwise it set `alpha = max(alpha, stand_pat)` and then searched the tactical moves.

`legal_moves(true)` being non-empty was treated as proof that stand-pat was optional. A non-empty list only proves that a capture or promotion exists. It does not prove the side can decline it. When every legal move is a capture or a promotion, the side must play one of them. The static evaluation is then a score the position cannot choose.

The damage shows up in two ways.

**The floor.** On a wide window the old code still generated the tactical moves, but it had already raised `alpha` to the static evaluation. The search loop only replaces `alpha` when a move scores strictly above it. A forced loss below the static evaluation was computed and then discarded. The function returned the static evaluation.

**The false fail-high.** On a zero window whose upper bound was the static evaluation, `stand_pat >= beta` returned `beta` immediately. The tactical moves were not searched. The caller was told the score was at least `beta`. The true score was below `beta`.

Depth 1 of the same positions was already right. The root of `alpha_beta` generates every legal move and does not stand-pat. The wrong score appeared at the quiescence horizon, and in any cutoff that trusted stand-pat.

### White is forced to promote

FEN: `8/P7/8/8/8/8/6q1/K1k5 w - - 0 1`

White has a pawn on a7, the king on a1, the black king on c1, and a black queen on g2. White is not in check. The only legal moves are `a7a8q`, `a7a8r`, `a7a8b`, and `a7a8n`. There is no quiet move. The static evaluation is -720, which is the material of a queen against a pawn. That number does not see that every promotion loses.

After `a7a8q`, Black is not in check. Both `g2a8` (capture of the new queen) and `g2b2` (a quiet move) are mate. Quiescence sees the capturing mate, so this example does not depend on searching quiet checks. The mate is delivered at ply 2. Mate score is 30000, so the score from White's point of view is `-30000 + 2 = -29998`.

Unmodified 5.31.0 quiescence returned -720. A fresh depth-1 search returned -29998 and played `a7a8q`. The same bug on the black mirror `5K1k/1Q6/8/8/8/8/7p/8 b - - 0 1` returned -720 instead of -29998 for `h2h1q`.

The window `[-800, -720)` made the second failure mode visible. 5.31.0 returned -720 without searching. That is a claim that the score is at least -720. The true score, -29998, is below -720. This branch returns -800, the fail-low bound.

### The bishop must capture, and the result is a draw

FEN: `8/8/8/8/8/1k6/1p6/BK6 w - - 0 1`

White's only legal move is `a1b2`, capturing the pawn. The static evaluation is +1. After the capture the position is bishop and king against king, which the engine scores as a draw, 0. Depth 1 already returned 0. Unmodified quiescence returned +1, because +1 had been installed as `alpha` and the capture's 0 did not beat it.

The window `[0, 1)` returned 1 on 5.31.0. That claims the score is at least 1. The true score is 0. This branch returns 0. The black mirror `6kb/6P1/6K1/8/8/8/8/8 b - - 0 1` has the same shape: 5.31.0 quiescence returned +1 for `h8g7`, and depth 1 returned 0.

## What the audit found

The bug above is the one that was wrong. The surrounding quiescence rules were checked on the same probes and on 150,594 positions. These cases already matched the contract on 5.31.0, and they still match after the correction.

**Checks and evasions.** In check, the old code generated every legal move and did not stand-pat. `4r2k/8/8/8/8/8/8/4K3 w - - 0 1` is check, with four king moves and none of them mate. The static evaluation is -530. Both builds return -541 on the wide window and on `[-610, -530)`. Immediate mate `7k/6Q1/6K1/8/8/8/8/8 b - - 0 1` scores -30000 on both builds.

**Stalemate.** `5k1K/7P/8/8/8/8/8/8 w - - 0 1` has static evaluation +288 and no legal move. Both builds return 0 inside `[0, 388)`. `7k/5Q2/6K1/8/8/8/8/8 b - - 0 1` has static evaluation -1010 and returns 0. The 5.21.0 fix for a favorable quiet stalemate is intact. A window that cannot contain 0 still returns the ordinary alpha-beta bound. That is a fail-low, not an exact draw score.

**Tactical moves when a quiet move also exists.** Stand-pat is the correct floor there, because the side can decline the capture. `4k3/8/8/2q5/8/8/8/2R1K3 w - - 0 1` scores 562 against a static evaluation of -470. En passant is available in `4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 2`, and the score is 218 against a static evaluation of 45. On `7k/8/8/8/8/7K/p7/1rR5 w - - 0 1` the capture `c1b1` is answered by -969. The root stays at the static evaluation, -249, on both builds, because 17 other legal moves are quiet.

**A quiet mate is a different horizon.** `k7/8/1K6/8/8/8/8/6Q1 w - - 0 1` is mate in one by the quiet move `g1g8`. Depth 1 scores 29999. Quiescence returns the static evaluation, 1019, because all 25 legal moves are quiet and this search does not examine quiet checks. Forge 1.1.0 rejected a checking-quiescence experiment after a W11 L10 D11 screen because it cost about 9.3% more nodes. This audit leaves that decision in place. No test locks the score 1019.

**The wide sample.** `forge/tools/qsearch_audit.cpp` compares the engine with an independent search of the same rules: evasions in check, draw on stalemate, tactical moves searched, stand-pat only when a quiet legal move exists. It shares move generation, check detection, evaluation, and the draw rules with the engine, so agreement shows that quiescence follows those rules. It does not prove the shared pieces. The existing perft and legality tests still pass.

The sample is 12 named positions, a structured placement of both kings plus either a white pawn on the seventh rank or a rim knight and a black pawn, and a 30-game walk of 24 plies. It keeps checks, positions with no legal move, positions whose moves are all tactical, and a thin slice of positions that have both a quiet move and a capture. The walk also keeps every fourth ply. Across 150,594 comparisons there were 0 mismatches and 0 rejected FENs.

One walk position exceeded the contract's 200,000-node cap because that contract had no transposition table: `r2qk1nr/3n1ppp/1pp2b2/p2pp3/1PP3bP/P4N2/2QPPPPR/RNB1KB2 w Qkq - 2 11`. It is not in check. It has 28 quiet moves and 4 tactical moves, and its static evaluation is -26. The engine returns -26 after 563 nodes. The same rules, given a transposition table, searched 1,353,971 nodes and also returned -26. Stand-pat is legal here, and no tactical line beat it.

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

| Position | FEN | Stand-pat | 5.31.0 qsearch | Depth 1 | This branch |
| --- | --- | --- | --- | --- | --- |
| White must promote | `8/P7/8/8/8/8/6q1/K1k5 w - - 0 1` | -720 | -720 | -29998 `a7a8q` | -29998 |
| Black must promote | `5K1k/1Q6/8/8/8/8/7p/8 b - - 0 1` | -720 | -720 | -29998 `h2h1q` | -29998 |
| White bishop must capture | `8/8/8/8/8/1k6/1p6/BK6 w - - 0 1` | +1 | +1 | 0 `a1b2` | 0 |
| Black bishop must capture | `6kb/6P1/6K1/8/8/8/8/8 b - - 0 1` | +1 | +1 | 0 `h8g7` | 0 |

| Window | 5.31.0 | This branch |
| --- | --- | --- |
| Promotion, `[-800, -720)` | -720 | -800 |
| Bishop capture, `[0, 1)` | 1 | 0 |
| Favorable stalemate `5k1K/7P/8/8/8/8/8/8 w - - 0 1`, `[0, 388)` | 0 | 0 |
| Evasion `4r2k/8/8/8/8/8/8/4K3 w - - 0 1`, `[-610, -530)` | -541 | -541 |

## What changed

The engine change is the stand-pat gate in `Searcher::quiescence`. Stand-pat is applied only when one of these is true:

- There is no capture or promotion to search. The existing stalemate probe still runs, and a favorable stalemate still returns 0 when that 0 can change the window.
- `stand_pat <= alpha`, so raising `alpha` to it, or cutting off on it, would not change the bound. The tactical moves are searched anyway.
- A legal quiet move exists.

`Board::has_legal_quiet_move()` walks pseudo-legal moves, skips captures and promotions (en passant counts as a capture), and returns on the first move that leaves the king safe. That walk runs only in the third case. In-check nodes still call `legal_moves(false)` and never stand-pat. Transposition-table stores are unchanged: depth-0 entries, mate scores shifted by ply, and a deeper entry is not overwritten.

The files are:

- `forge/src/search.cpp`: the gate around stand-pat.
- `forge/include/forge/board.hpp` and `forge/src/board.cpp`: `has_legal_quiet_move()`.
- `forge/tests/tests.cpp`: `check_quiescence_forced_tactics`, covering both colors, the fail-high windows, a repeated transposition-table probe, the evasion, and the winning rook capture. Each forced-tactical fixture must be out of check, have a legal move, and have no quiet move. Mate fixtures must match a fresh depth-1 search, score below -29000, and fail low on `[stand-pat - 80, stand-pat)`. Draw fixtures must score 0 at quiescence and at depth 1, and `[0, 1)` must return 0.
- `forge/tools/qsearch_audit.cpp`: the differential checker. It is not linked into the engine.
- `forge/CMakeLists.txt`: builds `qsearch_audit`. `FORGE_BUILD_VALIDATION_TOOLS` adds `forge_openings` only when `tools/generate_openings.cpp` is present. In this tree the source is absent, so configuring with the option on prints a skip and finishes. The earlier CMake error was `Cannot find source file: tools/generate_openings.cpp`.

Negative static-exchange pruning and hard delta pruning stay removed, as they have since 5.17.0 through 5.19.0. This change does not put them back.

Verification used g++ 13.3.0, C++20, `-Wall -Wextra -Wpedantic -Wconversion -Wshadow`. The default `c++` on the machine is Clang 18.1.3 and its link failed with `cannot find -lstdc++`, so the builds named g++ explicitly.

- Release `ctest` target `forge_tests`: passed in 8.02 seconds.
- `forge_tests` rebuilt with `-O1 -fsanitize=address,undefined -fno-omit-frame-pointer`: `All tests passed`.
- `qsearch_audit`: 150,594 positions, 0 mismatches.

`has_legal_quiet_move()` walks the pseudo-legal list when a tactical move exists and stand-pat is above `alpha`. The node counter does not include that walk. The existing node ceilings stayed green. No nodes-per-second claim is made.

## Limits

The structured sample is seventh-rank pawns and rim knights plus a short random walk, not every chess position. Quiet checking moves are outside the contract on purpose. The Python match, ponder, and UCI scripts, the opening book, and the validation corpora from the 5.31.0 archive are not in this tree. `ctest` registers those Python tests only when `tools/uci_regression.py` is present.

Nothing on this branch was merged or promoted.
