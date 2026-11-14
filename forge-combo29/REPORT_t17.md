# t17: move generation and game-rule suite

This section is the account of the branch. The command logs below it are the evidence. Nothing in those logs was edited to fit a result.

## What changed

Two commits on `grok47/t17-rules-suite`, based on `lock/combo29-20261110`.

`4bdb9e95184199b8fa9344b515aa5359738f715f` added the suite and the only engine edit. `3438c19e92b3f3919b1cd089b2e7e3162bbeee45` extended the suite. The second commit did not touch engine source.

Files:

- `forge-combo29/include/forge/board.hpp`: three lines inside the private section of `Board`.

```cpp
    // Test probe: compares every field, including ones with no public accessor.
    friend struct BoardStateProbe;
```

- `forge-combo29/tests_t17/rules_suite.cpp`: the C++ suite. It links `bitboard.cpp`, `board.cpp`, `eval.cpp`, `eval_params.cpp`, `nnue.cpp`, and `search.cpp`. It does not link `uci.cpp` (that file has `main`) or `book.cpp`.
- `forge-combo29/REPORT_t17.md`: this file.

The friend lets the test compare `plies_from_null_` and the king-line cache (`valid`, `pinned`, `discoverers`, `check_squares`). Those fields have no public accessor. The declaration does not change move generation, hashing, or search. After it was added, the lock was run again: bench 11 = 312866, bench 13 = 862329, perft 5 from the start = 4865609. The same three numbers came back from an address-sanitizer and undefined-behavior-sanitizer build of the engine binary.

## What I found

Move generation and the draw rules the search uses already match the cases the task named. No engine rule was changed, because no case failed for a reason that was the engine's.

Published perft, checked against the Chess Programming Wiki, Wasserpuncher/chess-perft, and GoBit `perft_tests.txt` before the suite was written. The three tables agree with each other and with this engine. No expected count was edited.

| Position | Depth | Engine | Published |
| --- | ---: | ---: | ---: |
| start | 5 | 4865609 | 4865609 |
| `r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq -` | 4 | 4085603 | 4085603 |
| `8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - -` | 5 | 674624 | 674624 |
| `r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1` | 4 | 422333 | 422333 |
| `rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8` | 4 | 2103487 | 2103487 |
| `r4rk1/1pp1qppp/p1np1n2/2b1p1B1/2B1P1b1/P1NP1N2/1PP1QPPP/R4RK1 w - - 0 10` | 4 | 3894594 | 3894594 |

After each of those perfts, and again after a depth-3 walk of every node, the board matches the board from before the walk. Depth-3 position counts were start 9323, Kiwipete 99950, position 3 3018, position 4 9738, position 5 63910, position 6 92016, with 0 key mismatches. At every node, `key`, `pawn_key`, and `checkers` equal a from-scratch recompute.

The search draw rules, at Hash 16 and one thread:

- One repetition cycle is twofold. The root search does not adjudicate it (`score=370 nodes=131 best=h1h8`). Asking `is_draw` while pretending that root is an earlier occurrence returns a draw. A second cycle is threefold and the root search adjudicates it (`score=0 nodes=0 best=h1f1`).
- Half-move 99 is not an immediate draw. Depth 2 of a quiet position returns `score=0 nodes=32` because every child has reached 100. Half-move 100 with a legal move is an immediate draw (`score=0 nodes=0`).
- Mate on the move that reaches 100 wins. From `k7/8/1QK5/8/8/8/8/8 w - - 99 1`, `b6b7` scores `31999`. The position after that mate has half-move 100, is checkmate, `is_draw` is false, and the side to move scores `-32000`. The same position with the clock already at 100, before the mate, is a draw even though `b6b7` is still legal (`score=0 nodes=0 best=b6b1`).
- Stalemate `7k/5Q2/6K1/8/8/8/8/8 b - - 0 1` is `score=0 nodes=0`. The parent move `g5g6` into that stalemate scores `0` with `nodes=2`.
- Bare kings, king and knight versus king, and king and bishop versus king are immediate draws. King and rook versus king is not (`score=434 nodes=53`).
- A pawn push or a capture at half-move 99 resets the clock. `a1a8` in `n7/8/8/8/8/7k/8/R3K3 w - - 99 1` leaves a depth-2 search of `score=-381 nodes=37 best=h3g2`. Black is to move after the capture, so the negative score is Black to move in a lost king-and-rook ending. It is not a 50-move adjudication (`nodes` is not 0).
- A null move flips the side, clears en passant, increments the half-move clock, and matches a recomputed key. Unmake restores every field. Two null moves after one repetition cycle leave the search draw flag false, because a null move sets `plies_from_null_` to 0 and the search repetition scan does not look through it. Game-level `is_repetition()` does not use that cursor. After the null moves are taken back, the game is still twofold.
- Two workers still return the mate `b6b7` at score 31999, and from the start at depth 3 they return the legal move `e2e4` at score 18.

All 40 malformed FENs are rejected or clamped. A rejection leaves the previous board unchanged. Address and undefined-behavior sanitizers printed nothing, and the sanitizer suite output matched the release suite line for line. The sanitizer engine binary reproduced bench 11 = 312866, bench 13 = 862329, and perft 5 = 4865609, including the same per-move split.

## What was wrong

Three different things were wrong. They are separated below. The move generator and the draw rules were not among them.

### 1. The first queenside positions were illegal, and the suite hid that

The first follow-up run failed 12 checks, all from five white queenside FENs. Each one ended with `7k/R3K2R`, so the black king stood on `h2` and a white rook stood on `h1`. The rook attacks `h2`. White is to move, so the side that just moved (Black) left its king in check.

`set_fen` rejected every one of those FENs with `side that moved left its king in check`. That message is the same check as malformed FEN 32. The rejection was correct.

What was wrong was the test, and then the way a failed load continued. `load` prints the failure and returns the board it already had. The board constructor is the start position, and `set_fen` does not modify the board when parsing fails. The later checks therefore ran on the start position:

- `e1c1` is illegal in the start position because `b1`, `c1`, and `d1` are occupied, so "cannot castle queenside through check" passed for that reason.
- A hand-built queen-castle move is not pseudo-legal in the start position for the same reason, so that check passed too.
- "d1 attacked, king safe", "a1 rook is attacked", and "queenside castle with the rook attacked is legal" failed, because the start position is not that position.

The black king was moved off the h-file and off the file the test needs clear. Through check, out of check, the attacked `a1` rook, and `b1` attacked use the king on `c7`. Into check uses the king on `b7`, because a king on `c7` would block the c-file and `c1` would not be attacked. After that change the same checks passed for the positions they name: `e1c1` is illegal through `d1`, illegal into `c1`, illegal out of check, legal when only `a1` is attacked, and legal when only `b1` is attacked. The king lands on `c1`, the rook on `d1`, the key matches a recompute, and unmake restores every field.

### 2. Two assertions were too weak to catch the regression they described

The first suite printed the right facts and then checked something smaller.

Double check. `d7f6` in `4k3/3N2q1/8/8/B7/8/8/4K3 w - - 0 1` leaves the black king in check from the knight and the bishop. The suite printed `e8e7 e8f7 e8d8 e8f8` and then asserted only that the list was non-empty, that every reply moved the black king, and that `g7f6` was absent. Dropping three of the four legal replies would still pass. Adding an illegal king move onto an attacked square would still pass as long as the mover was the king. The check now requires that set and no other move: `e8e7`, `e8f7`, `e8d8`, `e8f8`. The engine already produced exactly that set. The assertion was what was wrong.

Oversized clocks. FENs 33 to 36 were marked `FenKind::Any`, so acceptance and rejection both counted as success. The log line showed `halfmove=65535`, but nothing asserted it. A parser that wrapped `1000000` or `LLONG_MAX` to some other `uint16_t` value would still pass. FENs 37 and 38, which overflow `long long`, were also `Any`, so accepting a truncated value would have passed. The suite now requires:

- half-move `1000000` and half-move `9223372036854775807` are accepted and stored as half-move 65535, full-move 1
- full-move `1000000` and full-move `9223372036854775807` are accepted and stored as half-move 0, full-move 65535
- a half-move or full-move that does not fit in `long long` is rejected

That is what the engine already did. `set_fen` clamps with `std::min(value, 65535)` into a `uint16_t` when extraction succeeds. When extraction fails, the six-field read fails and the error is `FEN must contain six fields`. The wording of that overflow error is easy to misread: the input has six fields, and the failure is that one of them is not a `long long`. The board is left unchanged. No crash.

### 3. `board.hpp` no longer matches the published source snapshot

`windows_build/SOURCE_INPUTS.sha256` is the hash list for the locked sources. After the friend was added:

```
sha256sum -c windows_build/SOURCE_INPUTS.sha256
```

exits 1. `include/forge/board.hpp` is `FAILED`. The other 19 files are `OK`. Expected hash `ced3835a829cfe766281a19827f3b919c80fdf418314c63b0f7cd55eacd0e724` is the file without the friend.

What is wrong here is the snapshot check, not a chess rule. The header is one of the files that hash is supposed to identify as the source of the published lock binary. A three-line friend changes that identity even though bench 11, bench 13, and perft 5 stay on the lock numbers. The friend was left in place because the task asked for every field after make and unmake, and `plies_from_null_` and the king-line cache cannot be read from outside the class. Removing the friend would make the hash match and would drop those fields from the comparison.

### Parser results that look like the wrong error, and are the parser's real order

These were not changed. They are recorded so a later reader does not "fix" them.

- Nine pawns on rank 8, and `4p4` on rank 8, are rejected as `pawn on promotion rank`. The file-count check never runs, because the first pawn is already on rank 8. The message is not `invalid FEN placement`, which is what a digit `9` and an `8p` rank produce.
- A double push records the en-passant square in the FEN even when no enemy pawn can capture. `a2a4` in `8/8/8/8/8/7k/P7/4K3 w - - 99 1` sets ep `a3`, resets the clock to 0, and leaves `a3` out of the hash. The key includes an en-passant file only when a legal capture of that pawn exists. The incremental key matched a from-scratch key.
- `is_legal` for a castling move checks the king's destination. `is_pseudo_legal` checks that the king is not in check and that every square the king crosses is safe. Generated castles are only emitted when the path is empty and safe. A hand-built castle through check fails `is_pseudo_legal`, which is the gate the transposition table uses. Search then runs `is_legal` on moves it generated. Widening `is_legal` was not done: the suite did not find a search that could play the illegal castle, and a change there can change the lock node counts.
- Opposite-coloured bishops are not called insufficient material. King and knight versus king, and king and bishop versus king, are. King and rook versus king is not. Two knights versus a lone king is not. The task asked for bare kings and king plus minor versus king. Changing the opposite-bishop case would change bench nodes.
- The king-line cache is filled lazily by `is_legal` and `gives_check`, which are const. A cold board compared with the board after perft differs in `king_lines_.valid`. The suite fills the cache before the snapshot. Unmake restores the cache that was saved in the undo record. A mismatch on a cold board is the lazy cache, not a failed unmake.
- A two-thread search shares the transposition table. One pair of runs, before the node count was removed from the printed line, showed 215 nodes at `-O3` and 274 nodes under the sanitizers for the same start-position search, the same score 18, and the same move `e2e4`. The count is not a signature. The mate line stayed `b6b7` at 31999.

### The build, which failed before any chess code ran

`/usr/bin/c++` on this machine is Clang 18.1.3. The first CMake configure failed in the compiler test with `cannot find -lstdc++`. `g++` and `libstdc++-13-dev` were installed. The lock numbers and the suite were measured with `g++` 13.3.0, `-O3 -ffp-contract=off -fno-fast-math -march=x86-64-v3`, and the portable defines from `CMakeLists.txt` (`FORGE_PORTABLE=ON`, `FORGE_MARCH=x86-64-v3`).

After that install, a bare `clang++` command still fails with `fatal error: 'array' file not found`. Clang does not search `/usr/include/c++/13` on its own. The suite was rebuilt with `-stdlib=libstdc++ -isystem /usr/include/c++/13 -isystem /usr/include/x86_64-linux-gnu/c++/13 -L/usr/lib/gcc/x86_64-linux-gnu/13`. That binary's output matched the `g++` suite line for line, exit 0.

No second chess engine was executed in this environment. The six perft counts were compared with the three published tables, which agree.

## What I found, in the form the suite first reported it

No rule fault. The engine already matches the six published perft counts, restores every board field on unmake, and keeps the incremental hash equal to a from-scratch key. The special-move cases and the draw rules the search actually uses also match. All 40 malformed FENs are rejected or clamped, with no crash under address and undefined-behavior sanitizers.

The six expected counts were checked against a second and a third published source before the suite was written. They agree with each other and with this engine. Nothing was edited to fit the engine.

| Position | Depth | Task / engine | Chess Programming Wiki | Wasserpuncher/chess-perft and GoBit `perft_tests.txt` |
| --- | ---: | ---: | ---: | ---: |
| start | 5 | 4865609 | 4865609 | 4865609 |
| `r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq -` | 4 | 4085603 | 4085603 | 4085603 |
| `8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - -` | 5 | 674624 | 674624 | 674624 |
| `r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1` | 4 | 422333 | 422333 | 422333 |
| `rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8` | 4 | 2103487 | 2103487 | 2103487 |
| `r4rk1/1pp1qppp/p1np1n2/2b1p1B1/2B1P1b1/P1NP1N2/1PP1QPPP/R4RK1 w - - 0 10` | 4 | 3894594 | 3894594 | 3894594 |

Sources: https://chessprogramming.org/Perft_Results , https://github.com/Wasserpuncher/chess-perft , https://github.com/carokanns/GoBit/blob/master/perft_tests.txt . Disagreements: none.

Make/unmake: after each of those perfts, and again after a depth-3 walk, every board field matches the board from before the walk. The fields are the piece array, piece and colour bitboards, king squares, side to move, castling, en passant, both clocks, position key, pawn key, checkers, plies since a null move, the key history, and the king-line cache (`valid`, `pinned`, `discoverers`, `check_squares`). The cache is filled before the snapshot, because `is_legal` fills it lazily; unmake then restores that filled cache. At every position of the depth-3 walk (root through the leaves), `key`, `pawn_key`, and `checkers` equal `compute_key()`, `compute_pawn_key()`, and `compute_checkers()`.

Special moves:

- `8/8/8/8/k2Pp2Q/8/8/3K4 b - d3 0 1`: `e4d3` is generated as a pseudo-legal en passant and is illegal. `parse_uci` rejects it.
- Castling through check (`f1` attacked, king not in check): `e1g1` illegal.
- Castling out of check: `e1g1` illegal.
- Castling into check (`g1` attacked, `f1` not): `e1g1` illegal.
- Castling with the rook on `h1` attacked and `e1-f1-g1` safe: `e1g1` legal. After the move the king is on `g1` and the rook on `f1`. Unmake restores the board.
- Underpromotion: `a7a8n`, `a7a8b`, `a7a8r`, and `a7a8q` are legal and leave the named piece.
- Promotion with capture: `a7b8n`, `a7b8b`, `a7b8r`, and `a7b8q` are legal captures, leave the named piece on `b8`, and remove the pawn.
- Double check: `d7f6` in `4k3/3N2q1/8/8/B7/8/8/4K3 w - - 0 1` gives check from the knight and the bishop (`popcount(checkers()) == 2`). Legal replies are only `e8e7`, `e8f7`, `e8d8`, `e8f8`. The black queen cannot take the knight.

Draw rules, both through `Worker::is_draw` (the predicate search calls off the root) and through `Searcher::search` at Hash 16 and one thread:

- Threefold: after one rook-and-king cycle the position has occurred twice. That is not a root draw (`score=370 nodes=131`). Repeating a position that occurred at the search root is a draw inside `is_draw`. After the second cycle the position has occurred three times and the search adjudicates it (`score=0 nodes=0`).
- Fifty-move rule: at 99 half-moves the search is not an immediate draw; depth 2 returns `score=0 nodes=32` because every child has reached 100. At 100 half-moves the search adjudicates a draw without searching (`score=0 nodes=0`).
- Mate on the move that reaches 100: from `k7/8/1QK5/8/8/8/8/8 w - - 99 1`, `b6b7` is mate and the search score is `31999`. The resulting position has half-move 100, is checkmate, `is_draw` is false, and the side to move scores `-32000`. The same position with the clock already at 100, before that move, is a draw even though `b6b7` is still legal (`score=0 nodes=0`).
- Stalemate: `7k/5Q2/6K1/8/8/8/8/8 b - - 0 1` is an immediate draw (`score=0 nodes=0`). Restricting the parent to `g5g6` scores the move into stalemate as `0` with `nodes=2`.
- Insufficient material: bare kings, king and knight versus king, and king and bishop versus king are immediate draws. King and rook versus king is not (`score=434 nodes=53`).

FEN reader, 40 cases. A rejection leaves the previous board unchanged. An acceptance was then exercised with `legal_moves`, `perft(1)`, `key()`, and `fen()`.

| # | Result | Engine message or stored clocks | Case |
| ---: | --- | --- | --- |
| 1 | reject | FEN must contain six fields | empty |
| 2 | reject | FEN must contain six fields | placement only |
| 3 | reject | FEN must contain six fields | missing castling, ep, clocks |
| 4 | reject | FEN must contain six fields | missing ep and clocks |
| 5 | reject | FEN must contain six fields | missing both clocks |
| 6 | reject | FEN must contain six fields | missing fullmove |
| 7 | reject | FEN must contain exactly six fields | seventh field |
| 8 | reject | FEN must contain six fields | side token missing |
| 9 | reject | invalid FEN placement | digit 9 |
| 10 | reject | invalid FEN placement | `8p` (nine squares) |
| 11 | reject | pawn on promotion rank | nine pawns; the first pawn is already on rank 8, so the file-count error is not reached |
| 12 | reject | pawn on promotion rank | `4p4` on rank 8; same reason |
| 13 | reject | invalid FEN fields | two white kings |
| 14 | reject | invalid FEN fields | two black kings |
| 15 | reject | invalid FEN fields | no black king |
| 16 | reject | invalid FEN fields | no white king |
| 17 | reject | invalid FEN fields | no kings |
| 18 | reject | pawn on promotion rank | white pawn on rank 1 |
| 19 | reject | pawn on promotion rank | white pawn on rank 8 |
| 20 | reject | pawn on promotion rank | black pawn on rank 1 |
| 21 | reject | pawn on promotion rank | black pawn on rank 8 |
| 22 | reject | invalid en-passant square | ep on rank 4 |
| 23 | reject | invalid en-passant square | ep on rank 1 |
| 24 | reject | invalid en-passant square | ep file `i` |
| 25 | reject | inconsistent en-passant square | ep `e6` and no pawn |
| 26 | reject | inconsistent en-passant square | ep `e6` with a white pawn on `e4` |
| 27 | reject | inconsistent en-passant square | ep square occupied |
| 28 | reject | inconsistent en-passant square | ep origin occupied |
| 29 | reject | inconsistent en-passant square | ep `e3` and no white pawn |
| 30 | reject | inconsistent en-passant square | white to move, ep on rank 3 |
| 31 | reject | side that moved left its king in check | white king in check, black to move |
| 32 | reject | side that moved left its king in check | black king in check, white to move |
| 33 | accept | halfmove clamped to 65535 | half-move 1000000 |
| 34 | accept | fullmove clamped to 65535 | full-move 1000000 |
| 35 | accept | halfmove clamped to 65535 | half-move `LLONG_MAX` |
| 36 | accept | fullmove clamped to 65535 | full-move `LLONG_MAX` |
| 37 | reject | FEN must contain six fields | half-move does not fit in `long long` |
| 38 | reject | FEN must contain six fields | full-move does not fit in `long long` |
| 39 | reject | invalid FEN fields | negative half-move |
| 40 | reject | invalid FEN fields | full-move 0 |

## The change

No rule fault was found, so move generation and search were left as they are. The only engine edit is a `friend struct BoardStateProbe` on `Board`, so the suite can compare fields that have no accessor (the null-move cursor and the king-line cache) after every perft. That declaration does not change the lock counts. A follow-up added more rule cases to the suite and did not edit engine source again.

## Files changed

- `forge-combo29/include/forge/board.hpp` (3 lines added)
- `forge-combo29/tests_t17/rules_suite.cpp` (new)
- `forge-combo29/REPORT_t17.md` (this file)

Engine source changed: 3 lines. The suite links `bitboard.cpp`, `board.cpp`, `eval.cpp`, `eval_params.cpp`, `nnue.cpp`, and `search.cpp`. It does not link `uci.cpp` or `book.cpp`.

## Commands and output

The machine has AVX-512. The Start command was still run with `-DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3`. `/usr/bin/c++` is Clang 18 and the first configure failed in the compiler test (`cannot find -lstdc++`). `g++` and `libstdc++-13-dev` were installed (`sudo apt-get update -qq && sudo apt-get install -y -qq g++ libstdc++-13-dev`, exit 0). The measured builds use `g++` 13.3.0.

### Start command, before any source edit (configure failed)

```
git fetch origin
git checkout -b grok47/t17-rules-suite origin/lock/combo29-20261110
lscpu | rg -i "avx|model name|flags"
cmake -S forge-combo29 -B build -DCMAKE_BUILD_TYPE=Release -DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3
```

```
From https://github.com/couns0538-sketch/dwqww
 * [new branch]        cursor/draw-rules-history-tt-cb8e -> origin/cursor/draw-rules-history-tt-cb8e
 * [new branch]        cursor/forge-audit-f132 -> origin/cursor/forge-audit-f132
 * [new branch]        cursor/forge-branch-inventory-automation -> origin/cursor/forge-branch-inventory-automation
 * [new branch]        cursor/forge-concurrency-audit-8d98 -> origin/cursor/forge-concurrency-audit-8d98
 * [new branch]        cursor/forge-correctness-20261113-e6b6 -> origin/cursor/forge-correctness-20261113-e6b6
 * [new branch]        cursor/forge-history-index-20261113-712a -> origin/cursor/forge-history-index-20261113-712a
 * [new branch]        cursor/forge-nnue-eval-20261113-22cc -> origin/cursor/forge-nnue-eval-20261113-22cc
 * [new branch]        cursor/forge-qsearch-audit-60ce -> origin/cursor/forge-qsearch-audit-60ce
 * [new branch]        cursor/forge-search-strength-20261113-9558 -> origin/cursor/forge-search-strength-20261113-9558
 * [new branch]        cursor/forge-time-audit-770f -> origin/cursor/forge-time-audit-770f
 * [new branch]        cursor/move-legality-82b6 -> origin/cursor/move-legality-82b6
 * [new branch]        cursor/search-bound-audit-9cd5 -> origin/cursor/search-bound-audit-9cd5
 * [new branch]        cursor/search-bounds-audit-e6d7 -> origin/cursor/search-bounds-audit-e6d7
 * [new branch]        cursor/tt-audit-bounds-4ffa -> origin/cursor/tt-audit-bounds-4ffa
 * [new branch]        grok47/t1-capture-overflow -> origin/grok47/t1-capture-overflow
 * [new branch]        grok47/t10-multipv      -> origin/grok47/t10-multipv
 * [new branch]        grok47/t3-clock-parse   -> origin/grok47/t3-clock-parse
 * [new branch]        grok47/t4-clock-parse   -> origin/grok47/t4-clock-parse
 * [new branch]        grok47/t5-krk-mate      -> origin/grok47/t5-krk-mate
 * [new branch]        grok47/t6-fixed-node-score -> origin/grok47/t6-fixed-node-score
 * [new branch]        grok47/t8-nnue-file     -> origin/grok47/t8-nnue-file
Switched to a new branch 'grok47/t17-rules-suite'
branch 'grok47/t17-rules-suite' set up to track 'origin/lock/combo29-20261110'.
Model name:                              Intel(R) Xeon(R) Processor
Flags:                                   fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush dts mmx fxsr sse sse2 ss ht syscall nx pdpe1gb rdtscp lm constant_tsc pebs bts rep_good nopl xtopology nonstop_tsc cpuid tsc_known_freq pni pclmulqdq dtes64 vmx ssse3 fma cx16 pcid sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand hypervisor lahf_lm abm 3dnowprefetch cpuid_fault ssbd ibrs ibpb stibp ibrs_enhanced tpr_shadow flexpriority ept vpid ept_ad fsgsbase tsc_adjust bmi1 avx2 smep bmi2 erms invpcid avx512f avx512dq rdseed adx smap avx512ifma clflushopt clwb avx512cd sha_ni avx512bw avx512vl xsaveopt xsavec xgetbv1 xsaves avx_vnni avx512_bf16 wbnoinvd arat vnmi avx512vbmi umip pku ospke avx512_vbmi2 gfni vaes vpclmulqdq avx512_vnni avx512_bitalg avx512_vpopcntdq rdpid bus_lock_detect cldemote movdiri movdir64b fsrm md_clear serialize tsxldtrk amx_bf16 avx512_fp16 amx_tile amx_int8 flush_l1d arch_capabilities
-- The CXX compiler identification is Clang 18.1.3
-- Detecting CXX compiler ABI info
-- Detecting CXX compiler ABI info - failed
-- Check for working CXX compiler: /usr/bin/c++
-- Check for working CXX compiler: /usr/bin/c++ - broken
-- Configuring incomplete, errors occurred!
CMake Error at /usr/share/cmake-3.28/Modules/CMakeTestCXXCompiler.cmake:60 (message):
  The C++ compiler

    "/usr/bin/c++"

  is not able to compile a simple test program.

  It fails with the following output:

    Change Dir: '/agent/repos/dwqww/build/CMakeFiles/CMakeScratch/TryCompile-JQAF6b'

    Run Build Command(s): /usr/bin/cmake -E env VERBOSE=1 /usr/bin/gmake -f Makefile cmTC_947df/fast
    /usr/bin/gmake  -f CMakeFiles/cmTC_947df.dir/build.make CMakeFiles/cmTC_947df.dir/build
    gmake[1]: Entering directory '/agent/repos/dwqww/build/CMakeFiles/CMakeScratch/TryCompile-JQAF6b'
    Building CXX object CMakeFiles/cmTC_947df.dir/testCXXCompiler.cxx.o
    /usr/bin/c++    -MD -MT CMakeFiles/cmTC_947df.dir/testCXXCompiler.cxx.o -MF CMakeFiles/cmTC_947df.dir/testCXXCompiler.cxx.o.d -o CMakeFiles/cmTC_947df.dir/testCXXCompiler.cxx.o -c /agent/repos/dwqww/build/CMakeFiles/CMakeScratch/TryCompile-JQAF6b/testCXXCompiler.cxx
    Linking CXX executable cmTC_947df
    /usr/bin/cmake -E cmake_link_script CMakeFiles/cmTC_947df.dir/link.txt --verbose=1
    /usr/bin/c++ CMakeFiles/cmTC_947df.dir/testCXXCompiler.cxx.o -o cmTC_947df
    /usr/bin/ld: cannot find -lstdc++: No such file or directory
    c++: error: linker command failed with exit code 1 (use -v to see invocation)
    gmake[1]: *** [CMakeFiles/cmTC_947df.dir/build.make:100: cmTC_947df] Error 1
    gmake[1]: Leaving directory '/agent/repos/dwqww/build/CMakeFiles/CMakeScratch/TryCompile-JQAF6b'
    gmake: *** [Makefile:127: cmTC_947df/fast] Error 2
```

### Reference numbers before the edit

```
rm -rf build && CXX=g++ cmake -S forge-combo29 -B build -DCMAKE_BUILD_TYPE=Release -DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3 && cmake --build build -j && printf 'setoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nbench 11\nbench 13\nposition startpos\ngo perft 5\nquit\n' | ./build/forge
```

```
-- The CXX compiler identification is GNU 13.3.0
-- Detecting CXX compiler ABI info
-- Detecting CXX compiler ABI info - done
-- Check for working CXX compiler: /usr/bin/g++ - skipped
-- Detecting CXX compile features
-- Detecting CXX compile features - done
-- Performing Test CMAKE_HAVE_LIBC_PTHREAD
-- Performing Test CMAKE_HAVE_LIBC_PTHREAD - Success
-- Found Threads: TRUE
-- Configuring done (0.5s)
-- Generating done (0.0s)
-- Build files have been written to: /agent/repos/dwqww/build
[ 11%] Building CXX object CMakeFiles/forge.dir/src/bitboard.cpp.o
[ 22%] Building CXX object CMakeFiles/forge.dir/src/board.cpp.o
[ 33%] Building CXX object CMakeFiles/forge.dir/src/book.cpp.o
[ 55%] Building CXX object CMakeFiles/forge.dir/src/eval_params.cpp.o
[ 55%] Building CXX object CMakeFiles/forge.dir/src/eval.cpp.o
[ 66%] Building CXX object CMakeFiles/forge.dir/src/nnue.cpp.o
[ 77%] Building CXX object CMakeFiles/forge.dir/src/uci.cpp.o
[ 88%] Building CXX object CMakeFiles/forge.dir/src/search.cpp.o
[100%] Linking CXX executable forge
[100%] Built target forge
info string bench depth 11 nodes 312866 time 171 nps 1829625
info string bench depth 13 nodes 862329 time 447 nps 1929147
a2a3: 181046
b2b3: 215255
c2c3: 222861
d2d3: 328511
e2e3: 402988
f2f3: 178889
g2g3: 217210
h2h3: 181044
a2a4: 217832
b2b4: 216145
c2c4: 240082
d2d4: 361790
e2e4: 405385
f2f4: 198473
g2g4: 214048
h2h4: 218829
b1a3: 198572
b1c3: 234656
g1f3: 233491
g1h3: 198502
nodes 4865609
```

Rule 7 before the edit: bench 11 = 312866, bench 13 = 862329, perft 5 = 4865609.

### Suite, release flags

```
g++ -std=c++20 -O3 -ffp-contract=off -fno-fast-math -march=x86-64-v3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1 -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=0 -DFORGE_SPD_NNUE_ZMM=0 -I forge-combo29/include -pthread forge-combo29/tests_t17/rules_suite.cpp forge-combo29/src/bitboard.cpp forge-combo29/src/board.cpp forge-combo29/src/eval.cpp forge-combo29/src/eval_params.cpp forge-combo29/src/nnue.cpp forge-combo29/src/search.cpp -o /tmp/t17_rules
/tmp/t17_rules
```

Compile exited 0 with no diagnostics. Program output:

```
t17 rules suite
SOURCE chessprogramming.org/Perft_Results and github.com/Wasserpuncher/chess-perft and github.com/carokanns/GoBit perft_tests.txt agree; disagreements=none
PASS PERFT start depth 5 engine 4865609 expected 4865609
PASS STATE after perft start
PASS HASH start depth 3 positions 9323 mismatches 0
PASS STATE after hash walk start
PASS PERFT kiwipete depth 4 engine 4085603 expected 4085603
PASS STATE after perft kiwipete
PASS HASH kiwipete depth 3 positions 99950 mismatches 0
PASS STATE after hash walk kiwipete
PASS PERFT pos3 depth 5 engine 674624 expected 674624
PASS STATE after perft pos3
PASS HASH pos3 depth 3 positions 3018 mismatches 0
PASS STATE after hash walk pos3
PASS PERFT pos4 depth 4 engine 422333 expected 422333
PASS STATE after perft pos4
PASS HASH pos4 depth 3 positions 9738 mismatches 0
PASS STATE after hash walk pos4
PASS PERFT pos5 depth 4 engine 2103487 expected 2103487
PASS STATE after perft pos5
PASS HASH pos5 depth 3 positions 63910 mismatches 0
PASS STATE after hash walk pos5
PASS PERFT pos6 depth 4 engine 3894594 expected 3894594
PASS STATE after perft pos6
PASS HASH pos6 depth 3 positions 92016 mismatches 0
PASS STATE after hash walk pos6
PASS ep pin fen keeps d3
PASS ep capture e4d3 is pseudo-legal
PASS ep capture e4d3 is illegal
PASS parse_uci rejects illegal ep e4d3
PASS castle through: king is not in check
PASS castle through: f1 is attacked
PASS castle through: g1 is not attacked
PASS cannot castle through check
PASS castle out: king is in check
PASS cannot castle out of check
PASS castle into: king is not in check
PASS castle into: f1 is not attacked
PASS castle into: g1 is attacked
PASS cannot castle into check
PASS rook on h1 is attacked
PASS king path e1-f1-g1 is safe
PASS castling with the rook attacked is legal
PASS O-O lands king g1 rook f1
PASS O-O vacates e1 and h1
PASS STATE after attacked-rook castle unmake
PASS underpromotion legal a7a8n
PASS promotion piece a7a8n
PASS STATE unmake a7a8n
PASS underpromotion legal a7a8b
PASS promotion piece a7a8b
PASS STATE unmake a7a8b
PASS underpromotion legal a7a8r
PASS promotion piece a7a8r
PASS STATE unmake a7a8r
PASS underpromotion legal a7a8q
PASS promotion piece a7a8q
PASS STATE unmake a7a8q
PASS promotion capture legal a7b8n
PASS promotion capture result a7b8n
PASS STATE unmake a7b8n
PASS promotion capture legal a7b8b
PASS promotion capture result a7b8b
PASS STATE unmake a7b8b
PASS promotion capture legal a7b8r
PASS promotion capture result a7b8r
PASS STATE unmake a7b8r
PASS promotion capture legal a7b8q
PASS promotion capture result a7b8q
PASS STATE unmake a7b8q
PASS double-check move d7f6 is legal
PASS d7f6 gives check
PASS double check has 2 checkers (got 2)
PASS checkers are the knight and the bishop
double-check legal: e8e7 e8f7 e8d8 e8f8
PASS double check allows only king moves
PASS queen cannot take one checker while the other remains
PASS STATE after double-check unmake
PASS play one repetition cycle
PASS second occurrence is not game threefold
PASS search draw is false on twofold at the root
PASS search draw is true when the line repeats the root
DRAW twofold-root score=370 nodes=131 best=h1h8
PASS search does not adjudicate twofold at the root
PASS play the second repetition cycle
PASS third occurrence is game threefold
PASS search draw is true on threefold at the root
DRAW threefold-root score=0 nodes=0 best=h1f1
PASS search adjudicates threefold as a draw
PASS clock 99 quiet position has no mating move
PASS search draw is false at 99 half-moves
DRAW halfmove99 score=0 nodes=32 best=a1a3
PASS at 99 the search looks and the next ply is drawn
PASS search draw is true at 100 half-moves
DRAW halfmove100 score=0 nodes=0 best=a1b1
PASS search adjudicates 100 half-moves as a draw
PASS quiet mate b6b7 is legal at half-move 99
DRAW mate-on-100 score=31999 nodes=73 best=b6b7
PASS mating move that reaches half-move 100 wins
PASS mate still exists once the clock is already 100
PASS clock already 100 is a draw before the move
DRAW already-100-with-mate score=0 nodes=0 best=b6b1
PASS search does not play a mate after the clock has reached 100
PASS parse mating move
PASS mating move lands on half-move 100
PASS opponent is checkmated
PASS checkmate on half-move 100 is not a draw
DRAW mated-at-100 score=-32000 nodes=0 best=none
PASS side to move loses the mate on half-move 100
PASS stalemate has no legal move
PASS search draw is true in stalemate
DRAW stalemate-root score=0 nodes=0 best=none
PASS search adjudicates stalemate as a draw
PASS g5g6 leads to stalemate
DRAW stalemate-child score=0 nodes=2 best=g5g6
PASS search scores a move into stalemate as a draw
DRAW material bare-kings flag=1 score=0 nodes=0 best=a1b1
PASS insufficient-material bare-kings
PASS search draw flag bare-kings
PASS search adjudication bare-kings
DRAW material bare-kings-black flag=1 score=0 nodes=0 best=h1g1
PASS insufficient-material bare-kings-black
PASS search draw flag bare-kings-black
PASS search adjudication bare-kings-black
DRAW material knight-king flag=1 score=0 nodes=0 best=b1d2
PASS insufficient-material knight-king
PASS search draw flag knight-king
PASS search adjudication knight-king
DRAW material bishop-king flag=1 score=0 nodes=0 best=b1a2
PASS insufficient-material bishop-king
PASS search draw flag bishop-king
PASS search adjudication bishop-king
DRAW material bishop-king-black flag=1 score=0 nodes=0 best=a1b1
PASS insufficient-material bishop-king-black
PASS search draw flag bishop-king-black
PASS search adjudication bishop-king-black
DRAW material rook-king flag=0 score=434 nodes=53 best=b1b5
PASS insufficient-material rook-king
PASS search draw flag rook-king
PASS search adjudication rook-king
FEN 1 REJECT missing all fields | FEN must contain six fields
PASS FEN 1 reject leaves the board unchanged
PASS FEN 1 rejected as required
FEN 2 REJECT missing side, castling, ep, clocks | FEN must contain six fields
PASS FEN 2 reject leaves the board unchanged
PASS FEN 2 rejected as required
FEN 3 REJECT missing castling, ep, clocks | FEN must contain six fields
PASS FEN 3 reject leaves the board unchanged
PASS FEN 3 rejected as required
FEN 4 REJECT missing ep and clocks | FEN must contain six fields
PASS FEN 4 reject leaves the board unchanged
PASS FEN 4 rejected as required
FEN 5 REJECT missing both clocks | FEN must contain six fields
PASS FEN 5 reject leaves the board unchanged
PASS FEN 5 rejected as required
FEN 6 REJECT missing fullmove | FEN must contain six fields
PASS FEN 6 reject leaves the board unchanged
PASS FEN 6 rejected as required
FEN 7 REJECT extra seventh field | FEN must contain exactly six fields
PASS FEN 7 reject leaves the board unchanged
PASS FEN 7 rejected as required
FEN 8 REJECT missing side token | FEN must contain six fields
PASS FEN 8 reject leaves the board unchanged
PASS FEN 8 rejected as required
FEN 9 REJECT digit 9 in a rank | invalid FEN placement
PASS FEN 9 reject leaves the board unchanged
PASS FEN 9 rejected as required
FEN 10 REJECT eight empties plus a pawn | invalid FEN placement
PASS FEN 10 reject leaves the board unchanged
PASS FEN 10 rejected as required
FEN 11 REJECT nine pawns on a rank | pawn on promotion rank
PASS FEN 11 reject leaves the board unchanged
PASS FEN 11 rejected as required
FEN 12 REJECT 4+pawn+4 squares | pawn on promotion rank
PASS FEN 12 reject leaves the board unchanged
PASS FEN 12 rejected as required
FEN 13 REJECT two white kings | invalid FEN fields
PASS FEN 13 reject leaves the board unchanged
PASS FEN 13 rejected as required
FEN 14 REJECT two black kings | invalid FEN fields
PASS FEN 14 reject leaves the board unchanged
PASS FEN 14 rejected as required
FEN 15 REJECT no black king | invalid FEN fields
PASS FEN 15 reject leaves the board unchanged
PASS FEN 15 rejected as required
FEN 16 REJECT no white king | invalid FEN fields
PASS FEN 16 reject leaves the board unchanged
PASS FEN 16 rejected as required
FEN 17 REJECT no kings | invalid FEN fields
PASS FEN 17 reject leaves the board unchanged
PASS FEN 17 rejected as required
FEN 18 REJECT white pawn on rank 1 | pawn on promotion rank
PASS FEN 18 reject leaves the board unchanged
PASS FEN 18 rejected as required
FEN 19 REJECT white pawn on rank 8 | pawn on promotion rank
PASS FEN 19 reject leaves the board unchanged
PASS FEN 19 rejected as required
FEN 20 REJECT black pawn on rank 1 | pawn on promotion rank
PASS FEN 20 reject leaves the board unchanged
PASS FEN 20 rejected as required
FEN 21 REJECT black pawn on rank 8 | pawn on promotion rank
PASS FEN 21 reject leaves the board unchanged
PASS FEN 21 rejected as required
FEN 22 REJECT ep square on rank 4 | invalid en-passant square
PASS FEN 22 reject leaves the board unchanged
PASS FEN 22 rejected as required
FEN 23 REJECT ep square on rank 1 | invalid en-passant square
PASS FEN 23 reject leaves the board unchanged
PASS FEN 23 rejected as required
FEN 24 REJECT ep file off the board | invalid en-passant square
PASS FEN 24 reject leaves the board unchanged
PASS FEN 24 rejected as required
FEN 25 REJECT ep e6 with no pawn | inconsistent en-passant square
PASS FEN 25 reject leaves the board unchanged
PASS FEN 25 rejected as required
FEN 26 REJECT ep e6 with a white pawn on e4 | inconsistent en-passant square
PASS FEN 26 reject leaves the board unchanged
PASS FEN 26 rejected as required
FEN 27 REJECT ep square occupied | inconsistent en-passant square
PASS FEN 27 reject leaves the board unchanged
PASS FEN 27 rejected as required
FEN 28 REJECT ep origin e7 occupied | inconsistent en-passant square
PASS FEN 28 reject leaves the board unchanged
PASS FEN 28 rejected as required
FEN 29 REJECT ep e3 with no white pawn | inconsistent en-passant square
PASS FEN 29 reject leaves the board unchanged
PASS FEN 29 rejected as required
FEN 30 REJECT white to move but ep on rank 3 | inconsistent en-passant square
PASS FEN 30 reject leaves the board unchanged
PASS FEN 30 rejected as required
FEN 31 REJECT side not to move (white) is in check | side that moved left its king in check
PASS FEN 31 reject leaves the board unchanged
PASS FEN 31 rejected as required
FEN 32 REJECT side not to move (black) is in check | side that moved left its king in check
PASS FEN 32 reject leaves the board unchanged
PASS FEN 32 rejected as required
FEN 33 ACCEPT halfmove=65535 fullmove=1 fen=4k3/8/8/8/8/8/8/4K3 w - - 65535 1 | half-move 1000000
PASS FEN 33 handled by acceptance
FEN 34 ACCEPT halfmove=0 fullmove=65535 fen=4k3/8/8/8/8/8/8/4K3 w - - 0 65535 | full-move 1000000
PASS FEN 34 handled by acceptance
FEN 35 ACCEPT halfmove=65535 fullmove=1 fen=4k3/8/8/8/8/8/8/4K3 w - - 65535 1 | half-move LLONG_MAX
PASS FEN 35 handled by acceptance
FEN 36 ACCEPT halfmove=0 fullmove=65535 fen=4k3/8/8/8/8/8/8/4K3 w - - 0 65535 | full-move LLONG_MAX
PASS FEN 36 handled by acceptance
FEN 37 REJECT half-move overflows long long | FEN must contain six fields
PASS FEN 37 reject leaves the board unchanged
PASS FEN 37 handled by rejection
FEN 38 REJECT full-move overflows long long | FEN must contain six fields
PASS FEN 38 reject leaves the board unchanged
PASS FEN 38 handled by rejection
FEN 39 REJECT negative half-move | invalid FEN fields
PASS FEN 39 reject leaves the board unchanged
PASS FEN 39 rejected as required
FEN 40 REJECT full-move 0 | invalid FEN fields
PASS FEN 40 reject leaves the board unchanged
PASS FEN 40 rejected as required
RESULT PASS fails=0
```

Exit code 0.

### Suite built with `-fsanitize=address,undefined`

```
g++ -std=c++20 -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer -ffp-contract=off -fno-fast-math -march=x86-64-v3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1 -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=0 -DFORGE_SPD_NNUE_ZMM=0 -I forge-combo29/include -pthread forge-combo29/tests_t17/rules_suite.cpp forge-combo29/src/bitboard.cpp forge-combo29/src/board.cpp forge-combo29/src/eval.cpp forge-combo29/src/eval_params.cpp forge-combo29/src/nnue.cpp forge-combo29/src/search.cpp -o /tmp/t17_rules_asan
ASAN_OPTIONS=detect_leaks=1:halt_on_error=1 UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1 /tmp/t17_rules_asan
```

Compile exited 0 with no diagnostics. The sanitizers printed no errors. Program output was the same as the release run, line for line, ending in `RESULT PASS fails=0`. Exit code 0.

### Rule 7 after the edit

```
cmake --build build -j && printf 'setoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nbench 11\nbench 13\nposition startpos\ngo perft 5\nquit\n' | ./build/forge
```

```
[ 11%] Building CXX object CMakeFiles/forge.dir/src/board.cpp.o
[ 22%] Building CXX object CMakeFiles/forge.dir/src/eval.cpp.o
[ 33%] Building CXX object CMakeFiles/forge.dir/src/book.cpp.o
[ 44%] Building CXX object CMakeFiles/forge.dir/src/eval_params.cpp.o
[ 55%] Building CXX object CMakeFiles/forge.dir/src/nnue.cpp.o
[ 66%] Building CXX object CMakeFiles/forge.dir/src/search.cpp.o
[ 77%] Building CXX object CMakeFiles/forge.dir/src/uci.cpp.o
[ 88%] Linking CXX executable forge
[100%] Built target forge
info string bench depth 11 nodes 312866 time 167 nps 1873449
info string bench depth 13 nodes 862329 time 441 nps 1955394
a2a3: 181046
b2b3: 215255
c2c3: 222861
d2d3: 328511
e2e3: 402988
f2f3: 178889
g2g3: 217210
h2h3: 181044
a2a4: 217832
b2b4: 216145
c2c4: 240082
d2d4: 361790
e2e4: 405385
f2f4: 198473
g2g4: 214048
h2h4: 218829
b1a3: 198572
b1c3: 234656
g1f3: 233491
g1h3: 198502
nodes 4865609
```

Rule 7 after the edit: bench 11 = 312866, bench 13 = 862329, perft 5 = 4865609. The per-move perft 5 split is unchanged. Wall-clock times differ between the two runs; the node counts do not.

## What I could not verify

The follow-up below covers queenside castling, null-move make and unmake, a two-thread search, a Clang build of the suite, and the lock bench under address and undefined-behavior sanitizers.

Still open: no second chess engine was executed in this environment. The six counts were compared with the three published tables above, which agree. They were not recomputed by another program here.

## Follow-up

The suite grew. Engine headers and sources did not. The new cases passed, so nothing in move generation or search was changed.

Queenside castling, white, queen-side rights only:

- Through check, `3r4/2k5/8/8/8/8/8/R3K2R w Q - 0 1` (`d1` attacked, king safe): `e1c1` is illegal. A hand-built queen-castle move is not pseudo-legal. Search drops a transposition-table move that fails that check.
- Into check, `2r5/1k6/8/8/8/8/8/R3K2R w Q - 0 1` (`c1` attacked, `d1` safe): `e1c1` is illegal.
- Out of check, `4r3/2k5/8/8/8/8/8/R3K2R w Q - 0 1`: `e1c1` is illegal.
- Rook on `a1` attacked and `c1`/`d1` safe, `r7/2k5/8/8/8/8/8/R3K2R w Q - 0 1`: `e1c1` is legal. The king lands on `c1`, the rook on `d1`, and `a1` and `e1` are empty. The key matches a recompute. Unmake restores every field.
- Only `b1` attacked, `1r6/2k5/8/8/8/8/8/R3K2R w Q - 0 1`: `e1c1` is legal, the key matches, and unmake restores the board.

Black, same ideas: kingside through `f8`, into `g8`, and out of check; kingside with the `h8` rook attacked (`e8g8` legal); queenside with only `b8` attacked (`r3k3/8/8/8/8/8/8/1R2K3 b q - 0 1`, `e8c8` legal).

Other edges:

- File pin on en passant. `3r4/8/8/3Pp3/8/8/8/3K3k w - e6 0 1`: `d5e6` is pseudo-legal and illegal. With the rook on `a8` instead, `d5e6` is legal, the key matches, and unmake restores the board. `4k3/8/8/8/3Pp3/8/8/4R2K b - d3 0 1`: `e4d3` is illegal because it opens the e-file.
- Pinned knight, `4r3/8/8/8/8/8/4N3/4K2k w - - 0 1`: `e2d4` and `e2c3` are pseudo-legal and illegal, and the knight has no legal move.
- Discovered check, `4k3/8/8/8/8/8/4N3/4RK2 w - - 0 1`: `e2d4` gives check from the rook alone.
- Checking castle, `3k4/8/8/8/8/8/8/R3K3 w Q - 0 1`: `e1c1` gives check, the checker is the rook on `d1`, and the key matches a recompute.
- Null move on `r7/8/8/3Pp3/8/8/8/3K3k w - e6 0 1`: the side flips, en passant is cleared, the half-move clock becomes 1, the key matches a recompute, and unmake restores every field.
- After one rook-and-king repetition cycle, two null moves leave `is_draw` false. Unmaking them leaves a twofold repetition, not a threefold.
- Clock 99 with a pawn, `8/8/8/8/8/7k/P7/4K3 w - - 99 1`: `a2a3` resets the clock and is not a draw; `e1e2` lands on 100 and is a draw; `a2a4` sets en passant on `a3` with no capturer, resets the clock, leaves that dead square out of the key, and the FEN still records `a3`.
- Capture at 99, `n7/8/8/8/8/7k/8/R3K3 w - - 99 1`: `a1a8` resets the clock. Depth 2 is not an adjudicated draw (`score=-381 nodes=37 best=h3g2`, black to move).
- Two workers, 16 MB hash. Mate in one still returns `b6b7` at score 31999. From the start, depth 3 returns the legal move `e2e4` at score 18. The helper's node count is not printed. One earlier pair of runs, before that print was removed, showed 215 nodes at `-O3` and 274 under the sanitizers for the same move and the same score. The shared table makes that count unstable.

The first queenside positions put the black king on `h2`, in check from the rook on `h1`. `set_fen` rejected them with "side that moved left its king in check", which is the same check as FEN 32. Those positions were replaced with the king on `c7` or `b7`. That was a bad test position, not an engine fault.

Two checks that used to accept a weaker condition now require the exact result. Double check must produce exactly `e8e7`, `e8f7`, `e8d8`, and `e8f8`. Half-move `1000000` and `LLONG_MAX` must be stored as 65535 with full-move 1. Full-move `1000000` and `LLONG_MAX` must be stored as 65535 with half-move 0. A clock that does not fit in `long long` must be rejected.

`sha256sum -c windows_build/SOURCE_INPUTS.sha256`, run from `forge-combo29`, exits 1. The mismatch is the three-line `friend struct BoardStateProbe` from the first commit. Those fields (`plies_from_null_` and the king-line cache) have no accessor, and the state compare needs them. The friend stays. The node lock is unchanged.

```
sha256sum -c windows_build/SOURCE_INPUTS.sha256
```

```
include/forge/bitboard.hpp: OK
include/forge/board.hpp: FAILED
include/forge/book.hpp: OK
include/forge/eval.hpp: OK
include/forge/eval_params.hpp: OK
include/forge/nnue.hpp: OK
include/forge/search.hpp: OK
include/forge/uci_output.hpp: OK
src/bitboard.cpp: OK
src/board.cpp: OK
src/book.cpp: OK
src/book_data.inc: OK
src/eval.cpp: OK
src/eval_params.cpp: OK
src/eval_params_table.inc: OK
src/nnue.cpp: OK
src/nnue_weights.inc: OK
src/polyglot_keys.inc: OK
src/search.cpp: OK
src/uci.cpp: OK
sha256sum: WARNING: 1 computed checksum did NOT match
```

Exit code 1.

### Release suite after the follow-up

```
g++ -std=c++20 -O3 -ffp-contract=off -fno-fast-math -march=x86-64-v3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1 -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=0 -DFORGE_SPD_NNUE_ZMM=0 -I forge-combo29/include -pthread forge-combo29/tests_t17/rules_suite.cpp forge-combo29/src/bitboard.cpp forge-combo29/src/board.cpp forge-combo29/src/eval.cpp forge-combo29/src/eval_params.cpp forge-combo29/src/nnue.cpp forge-combo29/src/search.cpp -o /tmp/t17_rules
/tmp/t17_rules
```

Compile exited 0. Program exit code 0. Output:

```
t17 rules suite
SOURCE chessprogramming.org/Perft_Results and github.com/Wasserpuncher/chess-perft and github.com/carokanns/GoBit perft_tests.txt agree; disagreements=none
PASS PERFT start depth 5 engine 4865609 expected 4865609
PASS STATE after perft start
PASS HASH start depth 3 positions 9323 mismatches 0
PASS STATE after hash walk start
PASS PERFT kiwipete depth 4 engine 4085603 expected 4085603
PASS STATE after perft kiwipete
PASS HASH kiwipete depth 3 positions 99950 mismatches 0
PASS STATE after hash walk kiwipete
PASS PERFT pos3 depth 5 engine 674624 expected 674624
PASS STATE after perft pos3
PASS HASH pos3 depth 3 positions 3018 mismatches 0
PASS STATE after hash walk pos3
PASS PERFT pos4 depth 4 engine 422333 expected 422333
PASS STATE after perft pos4
PASS HASH pos4 depth 3 positions 9738 mismatches 0
PASS STATE after hash walk pos4
PASS PERFT pos5 depth 4 engine 2103487 expected 2103487
PASS STATE after perft pos5
PASS HASH pos5 depth 3 positions 63910 mismatches 0
PASS STATE after hash walk pos5
PASS PERFT pos6 depth 4 engine 3894594 expected 3894594
PASS STATE after perft pos6
PASS HASH pos6 depth 3 positions 92016 mismatches 0
PASS STATE after hash walk pos6
PASS ep pin fen keeps d3
PASS ep capture e4d3 is pseudo-legal
PASS ep capture e4d3 is illegal
PASS parse_uci rejects illegal ep e4d3
PASS castle through: king is not in check
PASS castle through: f1 is attacked
PASS castle through: g1 is not attacked
PASS cannot castle through check
PASS castle out: king is in check
PASS cannot castle out of check
PASS castle into: king is not in check
PASS castle into: f1 is not attacked
PASS castle into: g1 is attacked
PASS cannot castle into check
PASS rook on h1 is attacked
PASS king path e1-f1-g1 is safe
PASS castling with the rook attacked is legal
PASS O-O lands king g1 rook f1
PASS O-O vacates e1 and h1
PASS STATE after attacked-rook castle unmake
PASS underpromotion legal a7a8n
PASS promotion piece a7a8n
PASS STATE unmake a7a8n
PASS underpromotion legal a7a8b
PASS promotion piece a7a8b
PASS STATE unmake a7a8b
PASS underpromotion legal a7a8r
PASS promotion piece a7a8r
PASS STATE unmake a7a8r
PASS underpromotion legal a7a8q
PASS promotion piece a7a8q
PASS STATE unmake a7a8q
PASS promotion capture legal a7b8n
PASS promotion capture result a7b8n
PASS STATE unmake a7b8n
PASS promotion capture legal a7b8b
PASS promotion capture result a7b8b
PASS STATE unmake a7b8b
PASS promotion capture legal a7b8r
PASS promotion capture result a7b8r
PASS STATE unmake a7b8r
PASS promotion capture legal a7b8q
PASS promotion capture result a7b8q
PASS STATE unmake a7b8q
PASS double-check move d7f6 is legal
PASS d7f6 gives check
PASS double check has 2 checkers (got 2)
PASS checkers are the knight and the bishop
double-check legal: e8e7 e8f7 e8d8 e8f8
PASS double check replies are exactly e8e7 e8f7 e8d8 e8f8
PASS STATE after double-check unmake
PASS queenside through: d1 attacked, king safe
PASS cannot castle queenside through check
PASS crafted queenside castle through check is not pseudo-legal
PASS queenside into: c1 attacked, d1 safe
PASS cannot castle queenside into check
PASS queenside out: king is in check
PASS cannot castle queenside out of check
PASS a1 rook is attacked
PASS queenside king path c1-d1 is safe
PASS queenside castle with the rook attacked is legal
PASS O-O-O lands king c1 rook d1
PASS O-O-O vacates a1 and e1
PASS key after O-O-O rook attacked
PASS STATE unmake O-O-O rook attacked
PASS b1 is attacked
PASS c1 and d1 are safe
PASS queenside castle is legal when only b1 is attacked
PASS key after O-O-O b1 attacked
PASS STATE unmake O-O-O b1 attacked
PASS black kingside through: f8 attacked
PASS black cannot castle through check
PASS black kingside into: g8 attacked
PASS black cannot castle into check
PASS black cannot castle out of check
PASS black castle with h8 rook attacked is legal
PASS black queenside castle is legal when only b8 is attacked
PASS file-pin ep square is e6
PASS file-pin ep d5e6 is pseudo-legal
PASS file-pin ep d5e6 is illegal
PASS ep d5e6 is legal when the king is not on the opened file
PASS key after legal ep d5e6
PASS STATE unmake legal ep d5e6
PASS black ep e4d3 is illegal when it opens the e-file
PASS pinned knight e2d4 is illegal
PASS pinned knight e2c3 is illegal
PASS pinned knight has no legal move
PASS e2d4 is a pure discovered check
PASS discovered check is the rook alone
PASS O-O-O gives check along the d-file
PASS rook on d1 is the checker
PASS key after checking castle
PASS null move passes the turn
PASS null move clears en passant
PASS null move increments the half-move clock
PASS key after null move matches a recompute
PASS STATE after null-move unmake
PASS cycle once before the null-move chain
PASS twofold before the null moves is not a draw
PASS two null moves restore the side to move
PASS a null move breaks the repetition chain the search uses
PASS unmaking the null moves restores twofold, not threefold
PASS clock 99 has a pawn push and a quiet king move
PASS a pawn move resets the half-move clock
PASS the position after the pawn move is not a 50-move draw
PASS key after the pawn reset
PASS a quiet move from 99 lands on 100
PASS the quiet reply at 100 is a draw
PASS a2a4 double push is legal
PASS double push sets ep a3 even with no capturer
PASS double push resets the clock
PASS dead ep square is not hashed
PASS fen still records the dead ep square
PASS a1a8 captures the knight at clock 99
PASS capture resets the clock and leaves the rook
DRAW capture-resets-99 score=-381 nodes=37 best=h3g2
PASS a capture on ply 99 is not a 50-move draw
PASS play one repetition cycle
PASS second occurrence is not game threefold
PASS search draw is false on twofold at the root
PASS search draw is true when the line repeats the root
DRAW twofold-root score=370 nodes=131 best=h1h8
PASS search does not adjudicate twofold at the root
PASS play the second repetition cycle
PASS third occurrence is game threefold
PASS search draw is true on threefold at the root
DRAW threefold-root score=0 nodes=0 best=h1f1
PASS search adjudicates threefold as a draw
PASS clock 99 quiet position has no mating move
PASS search draw is false at 99 half-moves
DRAW halfmove99 score=0 nodes=32 best=a1a3
PASS at 99 the search looks and the next ply is drawn
PASS search draw is true at 100 half-moves
DRAW halfmove100 score=0 nodes=0 best=a1b1
PASS search adjudicates 100 half-moves as a draw
PASS quiet mate b6b7 is legal at half-move 99
DRAW mate-on-100 score=31999 nodes=73 best=b6b7
PASS mating move that reaches half-move 100 wins
PASS mate still exists once the clock is already 100
PASS clock already 100 is a draw before the move
DRAW already-100-with-mate score=0 nodes=0 best=b6b1
PASS search does not play a mate after the clock has reached 100
PASS parse mating move
PASS mating move lands on half-move 100
PASS opponent is checkmated
PASS checkmate on half-move 100 is not a draw
DRAW mated-at-100 score=-32000 nodes=0 best=none
PASS side to move loses the mate on half-move 100
PASS stalemate has no legal move
PASS search draw is true in stalemate
DRAW stalemate-root score=0 nodes=0 best=none
PASS search adjudicates stalemate as a draw
PASS g5g6 leads to stalemate
DRAW stalemate-child score=0 nodes=2 best=g5g6
PASS search scores a move into stalemate as a draw
DRAW material bare-kings flag=1 score=0 nodes=0 best=a1b1
PASS insufficient-material bare-kings
PASS search draw flag bare-kings
PASS search adjudication bare-kings
DRAW material bare-kings-black flag=1 score=0 nodes=0 best=h1g1
PASS insufficient-material bare-kings-black
PASS search draw flag bare-kings-black
PASS search adjudication bare-kings-black
DRAW material knight-king flag=1 score=0 nodes=0 best=b1d2
PASS insufficient-material knight-king
PASS search draw flag knight-king
PASS search adjudication knight-king
DRAW material bishop-king flag=1 score=0 nodes=0 best=b1a2
PASS insufficient-material bishop-king
PASS search draw flag bishop-king
PASS search adjudication bishop-king
DRAW material bishop-king-black flag=1 score=0 nodes=0 best=a1b1
PASS insufficient-material bishop-king-black
PASS search draw flag bishop-king-black
PASS search adjudication bishop-king-black
DRAW material rook-king flag=0 score=434 nodes=53 best=b1b5
PASS insufficient-material rook-king
PASS search draw flag rook-king
PASS search adjudication rook-king
MULTI-THREAD
PASS searcher keeps two workers
THREADS mate depth2 score=31999 best=b6b7
PASS two-thread mate search returns a legal move
PASS two threads still find the mate in one
THREADS start depth3 score=18 best=e2e4
PASS two-thread start search visits nodes
PASS two-thread start search returns a legal move
FEN 1 REJECT missing all fields | FEN must contain six fields
PASS FEN 1 reject leaves the board unchanged
PASS FEN 1 rejected as required
FEN 2 REJECT missing side, castling, ep, clocks | FEN must contain six fields
PASS FEN 2 reject leaves the board unchanged
PASS FEN 2 rejected as required
FEN 3 REJECT missing castling, ep, clocks | FEN must contain six fields
PASS FEN 3 reject leaves the board unchanged
PASS FEN 3 rejected as required
FEN 4 REJECT missing ep and clocks | FEN must contain six fields
PASS FEN 4 reject leaves the board unchanged
PASS FEN 4 rejected as required
FEN 5 REJECT missing both clocks | FEN must contain six fields
PASS FEN 5 reject leaves the board unchanged
PASS FEN 5 rejected as required
FEN 6 REJECT missing fullmove | FEN must contain six fields
PASS FEN 6 reject leaves the board unchanged
PASS FEN 6 rejected as required
FEN 7 REJECT extra seventh field | FEN must contain exactly six fields
PASS FEN 7 reject leaves the board unchanged
PASS FEN 7 rejected as required
FEN 8 REJECT missing side token | FEN must contain six fields
PASS FEN 8 reject leaves the board unchanged
PASS FEN 8 rejected as required
FEN 9 REJECT digit 9 in a rank | invalid FEN placement
PASS FEN 9 reject leaves the board unchanged
PASS FEN 9 rejected as required
FEN 10 REJECT eight empties plus a pawn | invalid FEN placement
PASS FEN 10 reject leaves the board unchanged
PASS FEN 10 rejected as required
FEN 11 REJECT nine pawns on a rank | pawn on promotion rank
PASS FEN 11 reject leaves the board unchanged
PASS FEN 11 rejected as required
FEN 12 REJECT 4+pawn+4 squares | pawn on promotion rank
PASS FEN 12 reject leaves the board unchanged
PASS FEN 12 rejected as required
FEN 13 REJECT two white kings | invalid FEN fields
PASS FEN 13 reject leaves the board unchanged
PASS FEN 13 rejected as required
FEN 14 REJECT two black kings | invalid FEN fields
PASS FEN 14 reject leaves the board unchanged
PASS FEN 14 rejected as required
FEN 15 REJECT no black king | invalid FEN fields
PASS FEN 15 reject leaves the board unchanged
PASS FEN 15 rejected as required
FEN 16 REJECT no white king | invalid FEN fields
PASS FEN 16 reject leaves the board unchanged
PASS FEN 16 rejected as required
FEN 17 REJECT no kings | invalid FEN fields
PASS FEN 17 reject leaves the board unchanged
PASS FEN 17 rejected as required
FEN 18 REJECT white pawn on rank 1 | pawn on promotion rank
PASS FEN 18 reject leaves the board unchanged
PASS FEN 18 rejected as required
FEN 19 REJECT white pawn on rank 8 | pawn on promotion rank
PASS FEN 19 reject leaves the board unchanged
PASS FEN 19 rejected as required
FEN 20 REJECT black pawn on rank 1 | pawn on promotion rank
PASS FEN 20 reject leaves the board unchanged
PASS FEN 20 rejected as required
FEN 21 REJECT black pawn on rank 8 | pawn on promotion rank
PASS FEN 21 reject leaves the board unchanged
PASS FEN 21 rejected as required
FEN 22 REJECT ep square on rank 4 | invalid en-passant square
PASS FEN 22 reject leaves the board unchanged
PASS FEN 22 rejected as required
FEN 23 REJECT ep square on rank 1 | invalid en-passant square
PASS FEN 23 reject leaves the board unchanged
PASS FEN 23 rejected as required
FEN 24 REJECT ep file off the board | invalid en-passant square
PASS FEN 24 reject leaves the board unchanged
PASS FEN 24 rejected as required
FEN 25 REJECT ep e6 with no pawn | inconsistent en-passant square
PASS FEN 25 reject leaves the board unchanged
PASS FEN 25 rejected as required
FEN 26 REJECT ep e6 with a white pawn on e4 | inconsistent en-passant square
PASS FEN 26 reject leaves the board unchanged
PASS FEN 26 rejected as required
FEN 27 REJECT ep square occupied | inconsistent en-passant square
PASS FEN 27 reject leaves the board unchanged
PASS FEN 27 rejected as required
FEN 28 REJECT ep origin e7 occupied | inconsistent en-passant square
PASS FEN 28 reject leaves the board unchanged
PASS FEN 28 rejected as required
FEN 29 REJECT ep e3 with no white pawn | inconsistent en-passant square
PASS FEN 29 reject leaves the board unchanged
PASS FEN 29 rejected as required
FEN 30 REJECT white to move but ep on rank 3 | inconsistent en-passant square
PASS FEN 30 reject leaves the board unchanged
PASS FEN 30 rejected as required
FEN 31 REJECT side not to move (white) is in check | side that moved left its king in check
PASS FEN 31 reject leaves the board unchanged
PASS FEN 31 rejected as required
FEN 32 REJECT side not to move (black) is in check | side that moved left its king in check
PASS FEN 32 reject leaves the board unchanged
PASS FEN 32 rejected as required
FEN 33 ACCEPT halfmove=65535 fullmove=1 fen=4k3/8/8/8/8/8/8/4K3 w - - 65535 1 | half-move 1000000
PASS FEN 33 clamps the half-move clock to 65535
FEN 34 ACCEPT halfmove=0 fullmove=65535 fen=4k3/8/8/8/8/8/8/4K3 w - - 0 65535 | full-move 1000000
PASS FEN 34 clamps the full-move number to 65535
FEN 35 ACCEPT halfmove=65535 fullmove=1 fen=4k3/8/8/8/8/8/8/4K3 w - - 65535 1 | half-move LLONG_MAX
PASS FEN 35 clamps the half-move clock to 65535
FEN 36 ACCEPT halfmove=0 fullmove=65535 fen=4k3/8/8/8/8/8/8/4K3 w - - 0 65535 | full-move LLONG_MAX
PASS FEN 36 clamps the full-move number to 65535
FEN 37 REJECT half-move overflows long long | FEN must contain six fields
PASS FEN 37 reject leaves the board unchanged
PASS FEN 37 rejected as required
FEN 38 REJECT full-move overflows long long | FEN must contain six fields
PASS FEN 38 reject leaves the board unchanged
PASS FEN 38 rejected as required
FEN 39 REJECT negative half-move | invalid FEN fields
PASS FEN 39 reject leaves the board unchanged
PASS FEN 39 rejected as required
FEN 40 REJECT full-move 0 | invalid FEN fields
PASS FEN 40 reject leaves the board unchanged
PASS FEN 40 rejected as required
RESULT PASS fails=0
```

### Same suite under `-fsanitize=address,undefined`

```
g++ -std=c++20 -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer -ffp-contract=off -fno-fast-math -march=x86-64-v3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1 -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=0 -DFORGE_SPD_NNUE_ZMM=0 -I forge-combo29/include -pthread forge-combo29/tests_t17/rules_suite.cpp forge-combo29/src/bitboard.cpp forge-combo29/src/board.cpp forge-combo29/src/eval.cpp forge-combo29/src/eval_params.cpp forge-combo29/src/nnue.cpp forge-combo29/src/search.cpp -o /tmp/t17_rules_asan
ASAN_OPTIONS=detect_leaks=1:halt_on_error=1 UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1 /tmp/t17_rules_asan
```

Compile exited 0 with no diagnostics. The sanitizers printed no errors. Program output was the same as the release suite above, line for line. Exit code 0.

### Clang 18.1.3

`clang++` with no extra include path still fails: `fatal error: 'array' file not found`. `libstdc++-13-dev` is installed, and Clang does not search `/usr/include/c++/13` on its own. The suite was rebuilt with those headers named explicitly:

```
clang++ -std=c++20 -stdlib=libstdc++ -isystem /usr/include/c++/13 -isystem /usr/include/x86_64-linux-gnu/c++/13 -L/usr/lib/gcc/x86_64-linux-gnu/13 -O3 -ffp-contract=off -fno-fast-math -march=x86-64-v3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1 -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=0 -DFORGE_SPD_NNUE_ZMM=0 -I forge-combo29/include -pthread forge-combo29/tests_t17/rules_suite.cpp forge-combo29/src/bitboard.cpp forge-combo29/src/board.cpp forge-combo29/src/eval.cpp forge-combo29/src/eval_params.cpp forge-combo29/src/nnue.cpp forge-combo29/src/search.cpp -o /tmp/t17_rules_clang
/tmp/t17_rules_clang
```

Compile exited 0. Program exit code 0. Output matched the g++ release suite, line for line.

### Lock numbers again, g++ binary, engine sources unchanged

```
printf 'setoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nbench 11\nbench 13\nposition startpos\ngo perft 5\nquit\n' | ./build/forge
```

```
info string bench depth 11 nodes 312866 time 167 nps 1873449
info string bench depth 13 nodes 862329 time 440 nps 1959838
a2a3: 181046
b2b3: 215255
c2c3: 222861
d2d3: 328511
e2e3: 402988
f2f3: 178889
g2g3: 217210
h2h3: 181044
a2a4: 217832
b2b4: 216145
c2c4: 240082
d2d4: 361790
e2e4: 405385
f2f4: 198473
g2g4: 214048
h2h4: 218829
b1a3: 198572
b1c3: 234656
g1f3: 233491
g1h3: 198502
nodes 4865609
```

Exit code 0. bench 11 = 312866, bench 13 = 862329, perft 5 = 4865609.

### Lock numbers under `-fsanitize=address,undefined`

The engine binary, including `uci.cpp` and `book.cpp`, rebuilt at `-O1` with the same defines. OwnBook stayed false, so the book file was not opened.

```
g++ -std=c++20 -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer -ffp-contract=off -fno-fast-math -march=x86-64-v3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1 -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=0 -DFORGE_SPD_NNUE_ZMM=0 -I forge-combo29/include -pthread forge-combo29/src/bitboard.cpp forge-combo29/src/board.cpp forge-combo29/src/eval.cpp forge-combo29/src/eval_params.cpp forge-combo29/src/nnue.cpp forge-combo29/src/search.cpp forge-combo29/src/book.cpp forge-combo29/src/uci.cpp -o /tmp/forge_asan
ASAN_OPTIONS=detect_leaks=1:halt_on_error=1 UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1 /tmp/forge_asan
```

Input was the same Threads 1, Hash 16, OwnBook false, `bench 11`, `bench 13`, `go perft 5` sequence. Compile exited 0. The sanitizers printed no errors. Program exit code 0. Output:

```
info string bench depth 11 nodes 312866 time 2191 nps 142795
info string bench depth 13 nodes 862329 time 5972 nps 144395
a2a3: 181046
b2b3: 215255
c2c3: 222861
d2d3: 328511
e2e3: 402988
f2f3: 178889
g2g3: 217210
h2h3: 181044
a2a4: 217832
b2b4: 216145
c2c4: 240082
d2d4: 361790
e2e4: 405385
f2f4: 198473
g2g4: 214048
h2h4: 218829
b1a3: 198572
b1c3: 234656
g1f3: 233491
g1h3: 198502
nodes 4865609
```

The node counts match the g++ binary. The per-move perft 5 split is unchanged.

