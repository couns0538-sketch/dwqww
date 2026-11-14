# Move legality — 2026-11-13

Branch `cursor/move-legality-82b6`, based on `fable/standalone-h512-20261111`.
Standard chess only. One board bug was wrong. Castling, en passant,
promotions, checks, pins, and make/unmake of the pieces matched python-chess
1.11.2. `LOCK.md` was not edited.

## What was wrong

The fullmove number in a FEN is the move number of the game. It stays the
same when White moves, and it increases by one when Black moves. That is
true of a pass as well as of a real move: a null ply is still a ply.

`Board::make_move` already did this. It saves `fullmove_` in `Undo`, and
before it flips the side it does:

```cpp
if (us == Black) fullmove_ = static_cast<std::uint16_t>(std::min<int>(fullmove_ + 1, 65535));
```

`Board::make_null_move` did the rest of a ply and skipped that line.

What the null path already did, and still does:

- save the en-passant square, the Zobrist key, the halfmove clock, the
  checker bitboard, and the king-line cache
- remove the en-passant file from the key when a legal capture existed, then
  clear the square
- flip the side to move and flip the side bit in the key
- add one to the halfmove clock, stopping at 65535
- set `plies_from_null_` to 0 and `checkers_` to 0
- push the new key onto the repetition history
- mark the king-line cache stale

What it did not do: if Black was the side to move, add one to `fullmove_`.
`NullUndo` had no field for that counter, so `unmake_null_move` could not
have restored a change that was never made.

python-chess 1.11.2, in `Board.push`, does the clocks first and then, for a
null move, swaps the turn and clears en passant:

```python
self.halfmove_clock += 1
if self.turn == BLACK:
    self.fullmove_number += 1
self.turn = not self.turn
self.ep_square = None
return
```

Measured on `r3k2r/8/8/8/8/8/8/R3K2R b KQkq - 0 1` (Black to move, move 1,
halfmove 0). After one null ply:

| | halfmove | side | fullmove | FEN tail |
| --- | ---: | --- | ---: | --- |
| python-chess | 1 | White | 2 | `w KQkq - 1 2` |
| Forge before the fix | 1 | White | 1 | `w KQkq - 1 1` |
| Forge after the fix | 1 | White | 2 | `w KQkq - 1 2` |

The same position with White to move stayed on fullmove 1 for both programs,
because White's ply does not advance the move number. The halfmove clock
became 1 for both. Pieces, castling rights, and the en-passant square agreed.
Only the last FEN field was wrong, and only while Black was the side that
had just passed.

Why the number has to become 2: the position started as Black's turn in
move 1. After Black passes, it is White's turn in move 2. Leaving the
counter at 1 says "White to move in move 1", which is an earlier point in
the game. The side had already been flipped, so the FEN described a position
that had not occurred.

The same one-low fullmove showed up wherever the null ply was Black's: the
en-passant pin positions, the stalemate `7k/5Q2/6K1/8/8/8/8/8 b - - 0 1`,
and any start-position line after one White move. The first comparison
against python-chess stopped after 30 failing positions (428 matched, 31
failed, 63 error lines). Every error was this field. Legal-move lists,
check, mate, stalemate, `gives_check`, move flags, promotion pieces, checker
squares, castling, en passant, and the FEN after a real move were already
the same.

Why the engine's own test missed it: after the null, the probe printed
Forge's FEN and loaded that FEN back with `set_fen`. `set_fen` stores the
fullmove number it is given. A counter that is wrong in the same way on both
sides of that round trip compares equal. `unmake_null_move` then returned to
the parent, whose counter had never been changed, so the parent snapshot
matched too. The bug is visible only to something that knows the right
move number from outside Forge.

Where it matters: `fullmove_number()` and `Board::fen()` were wrong for the
whole time a Black null move was on the board. Search calls
`make_null_move` only from null-move pruning, and only when the side to move
is not in check (`src/search.cpp`, the block that requires `!in_check`).
Search does not read the counter. It unmakes the null before the next real
move, so a finished search does not leave the bad number behind. The one
reader in the program is `game_ply` in `src/uci.cpp`:

```cpp
return 2 * (board.fullmove_number() - 1) + (board.side_to_move() == Black ? 1 : 0);
```

That is used at the root, before search, to decide whether the opening book
still applies. A null move inside the search does not reach it. A FEN copied
out while a Black null was in effect would carry the low move number from
then on. The fix is unconditional. A switch would leave that FEN wrong.

## What changed

Engine, three lines of behaviour and one saved field:

- [include/forge/board.hpp](../include/forge/board.hpp): `NullUndo` gained `fullmove`, default 1, next to the halfmove it already saved.
- [src/board.cpp](../src/board.cpp): `make_null_move` stores `undo.fullmove = fullmove_` and, while `side_` is still the mover, increments the counter for Black with the same 65535 cap as `make_move`. `unmake_null_move` writes `fullmove_ = undo.fullmove`.

Nothing else in make/unmake, move generation, or the evaluation was edited.
`LOCK.md`, `windows_build/SOURCE_INPUTS.sha256`, the build receipts, and the
published executable were left as they are.

Tests and the write-up added on this branch:

- [tools/legality_probe.cpp](../tools/legality_probe.cpp) checks the board against itself: mailbox against bitboards, generated moves against `is_legal` and `gives_check`, make/unmake back to the same FEN and key, and the published perft totals.
- [tools/legality_oracle.py](../tools/legality_oracle.py) is the comparison with python-chess, including the null-move FEN. That comparison is what catches this bug. The probe compiles into a private temporary directory.
- [tools/nnue_delta_probe.cpp](../tools/nnue_delta_probe.cpp) checks that the incremental network update matches a full refresh.
- This file.

## What the tests found, besides the clock

These were checked and matched. They are not further bugs.

- Castling both sides, including through an attacked square, into check, and
  out of check. Queenside castling stays legal when b1 is attacked. It is
  illegal when d1 is attacked. Kingside castling is illegal when f1 or g1 is
  attacked.
- En passant: a legal capture, a pin on the rank, a pin on the file, a
  capture that gives check, a discovered check, captures from both sides, a
  capture that gets out of check, and a recorded square with no capturer.
- Promotions to knight, bishop, rook, and queen, including captures and
  checks. A promoting pawn that discovers a rook was included.
- Pins of a queen, knight, rook, and pawn, and a rook pinned on the rank.
- Check, double check, checkmate, and stalemate.
- Make and unmake of those moves, on the king-line fast path and on the
  full occupancy test. Perft totals through the published depths matched,
  including start depth 6 at 119060324 and the lock's start depth 5 at
  4865609.
- The compiled-in network: 525 legal moves (13 castles, 6 en-passant
  captures, 41 promotions) and 36 null moves. The incremental accumulator
  matched a refresh from the board with difference 0, and unmake restored it.
- A g++ 13.3 release build reproduced all ten bench pins (net on
  312866 / 862329 / 3024920 / 12389307 / 34048354, net off
  375354 / 907205 / 2448617 / 13573040 / 24506465) and perft 5.

Two things found in the test harness and the lock record, not in the rules:

- The first oracle wrote its probe binaries to the fixed names
  `/tmp/legality_kl1` and `/tmp/legality_kl0`. SonarCloud rated that security
  D, because another user can replace a file at a fixed name under `/tmp`
  before it is executed. The probes now compile inside
  `tempfile.TemporaryDirectory` (mode 0700). The quality gate then passed
  with no new issues.
- `sha256sum -c windows_build/SOURCE_INPUTS.sha256` matched `board.hpp` and
  `board.cpp` on the parent commit `efb2ff96` and does not match them after
  this fix. Five other files already failed on that parent and were not
  edited here: `include/forge/nnue.hpp`, `include/forge/search.hpp`,
  `src/nnue.cpp`, `src/search.cpp`, and `src/uci.cpp`. The manifest still
  names the source of the published E1284F7F binary. It was not rewritten.

## The fix in the source

`NullUndo` now stores `fullmove`. `make_null_move` saves it and, while
`side_` is still the mover, increments it for Black, saturating at 65535,
the same cap `make_move` uses. `unmake_null_move` writes it back with the
other saved fields. Search calls `make_null_move` only when not in check.
The Linux release build above reproduced the lock bench pins.

## Tests

From the repository root:

```
python3 forge-combo29/tools/legality_oracle.py
```

The script compiles two probes into a private temporary directory (`tempfile.TemporaryDirectory`, mode 0700), compares both with python-chess, and deletes the directory when the probes exit. The binaries are not written to a fixed name under `/tmp`, because that path can be replaced before they are executed.

| probe | flags |
| --- | --- |
| king-line (`legality_kl1`) | `FORGE_SPD_KING_LINES=1`, `FORGE_SPD_NO_ZERO_MOVELISTS=2`, `FORGE_SPD_PREFETCH_EARLY=1` |
| reference (`legality_kl0`) | `FORGE_SPD_KING_LINES=0`, `FORGE_SPD_NO_ZERO_MOVELISTS=0`, `FORGE_SPD_PREFETCH_EARLY=0` |

Both use `-std=c++20 -O2 -DNDEBUG` and link `board.cpp` plus `bitboard.cpp`.
The king-line flags are the lock-style board settings. CMake does not
override `FORGE_SPD_KING_LINES`, and the header default is 1.

After the clock fix, on 2026-11-13, that command exited 0 in about 52 seconds. The same command was run again after the probes moved into the private temporary directory, with the same result:

```
positions 7891
perft start d6 119060324
perft kiwipete d5 193690690
perft pos3 d6 11030083
perft pos4 d5 15833292
perft pos6 d4 3894594
ok 7891 bad 0 errors 0
```

The 7,891 positions are the 33 crafted diagrams, every distinct position
within two plies of the seven perft roots, and random games from seed
`20261113` (12 games of 40 plies from the start, 6 of 25 from kiwipete, 6
of 20 from the promotion position). For each position the oracle checks the
FEN round-trip (`Board.fen(en_passant="fen")`), check, mate, stalemate,
whether any legal move exists, the en-passant square, both clocks, the
checker squares, the legal UCI set, `gives_check`, move flags and promotion
piece, the child FEN, and the null-move FEN when the side to move is not in
check. Every Forge pseudo-legal move must be pseudo-legal in python-chess.

Deep perft and `selftest` run on the king-line probe only after that
comparison is clean. Perft does not make null moves, so the clock fix does
not change those counts. The reference probe is still included in the
7,891-position comparison, including the null FENs. A direct probe check
after the fix:

```
r3k2r/8/8/8/8/8/8/R3K2R b KQkq - 0 1
  null -> r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 1 2
r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1
  null -> r3k2r/8/8/8/8/8/8/R3K2R b KQkq - 1 1
```

Both the king-line probe and the reference probe printed the Black result.

Sanitizer self-test, king-line flags, `-O1 -fsanitize=address,undefined`:

```
g++ -std=c++20 -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer \
  -DNDEBUG -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SPD_PREFETCH_EARLY=1 \
  -DFORGE_SPD_KING_LINES=1 -I forge-combo29/include -o /tmp/legality_asan \
  forge-combo29/tools/legality_probe.cpp forge-combo29/src/board.cpp \
  forge-combo29/src/bitboard.cpp
/tmp/legality_asan selftest
```

Exit 0. `SUMMARY fails 0`. `TOTAL fails 0`. The sanitizer log was empty.
The self-test walks make/unmake, including null moves about one ply in
seven, for 200 plies on six roots and 1,500 plies from the start, then
unmakes back to the root snapshot. The promotion root ended the walk at 130
plies because the game reached a terminal position.

### Perft the self-test checks

| position | depths | nodes |
| --- | ---: | --- |
| start | 1–5 | 20, 400, 8902, 197281, 4865609 |
| kiwipete | 1–4 | 48, 2039, 97862, 4085603 |
| pos3 `8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - -` | 1–5 | 14, 191, 2812, 43238, 674624 |
| pos4 `r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq -` | 1–4 | 6, 264, 9467, 422333 |
| pos5 `rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8` | 1–4 | 44, 1486, 62379, 2103487 |
| pos6 | 1–3 | 46, 2079, 89890 |
| `n1n5/PPPk4/8/8/8/8/4Kppp/5N1N b - -` | 1–4 | 24, 496, 9483, 182838 |

The deeper king-line totals are the five lines in the oracle output above.
Start depth 5 is the lock's perft pin, 4865609.

### Crafted diagrams in the corpus

Castling: both sides, castling while in check, the f1/b1/d1/g1 transit
squares attacked, queenside castle that gives check, kingside castle that
does not, and a blocked h-file so kingside castle does not check along that
file. b1 attacked still allows queenside castling. d1 attacked allows only
kingside. g1 attacked allows only queenside.

Pins: queen, knight, rook, and pawn on a file, plus a rook pinned on the
rank.

En passant: a legal capture, a pin on the rank, a pin on the file, a capture
that gives check, a discovered check, captures from both sides, a capture
that escapes check, and a recorded en-passant square with no capturer.

Promotions and checks: file check by queen or rook promotion, queen and rook
promotion on the e-file, discovery through a promoting pawn, knight
discovery, bishop discovery, double check, and a pawn that captures a rook
and promotes while castling rights are still present. Also the scholar's
mate and the `7k/5Q2/6K1` stalemate.

### Positions Forge rejects

These are expected rejections, and the oracle requires the reason text:

| FEN | reason contains |
| --- | --- |
| `4k3/8/8/8/8/8/8/4R1K1 w - - 0 1` | side that moved left its king in check |
| `7k/8/8/8/8/8/8/4K2R w K - 0 1` | side that moved left its king in check |
| `8/8/8/8/8/8/8/2kK4 w - - 0 1` | kings may not be adjacent |
| `P7/8/8/8/8/8/8/k3K3 w - - 0 1` | pawn on promotion rank |
| `4k3/8/8/8/8/8/8/R3K1N1 w K - 0 1` | castling right without king and rook |
| `r3k2r/8/8/8/8/8/8/R3K2R w KQkqK - 0 1` | duplicate castling right |
| `8/8/8/8/8/8/8/k3K3 w - e3 0 1` | en-passant |
| `8/8/8/3P4/8/8/8/k3K3 b - d4 0 1` | en-passant |
| `8/PPPPPPPP/8/8/8/8/k6P/4K3 w - - 0 1` | impossible piece inventory |
| `8/8/8/8/8/8/8/k3K3 w KQkq - 0 1` | castling right without king and rook |

The nine-pawn position is stricter than `python-chess` `Board.is_valid()`.
Forge also rejects an inventory where extra queens, rooks, bishops, or
knights exceed `8 - pawns`. That rule was already in `set_fen` and was left
as it is.

## Paths that were compared and did not fail

`is_legal` with king lines uses the pin test only when the side to move is
not in check, the move is not en passant, and the mover is not the king.
The contract in `board.hpp` says that answer is exact for a move that is
already pseudo-legal. `gives_check` with king lines uses the check-square
and discoverer sets for ordinary moves, including king moves and double
pawn pushes. En passant, castling, and promotions use the occupancy path.
The header comment groups king moves with the slow cases; that grouping
matches `is_legal`. A non-castling king move still takes the fast
`gives_check` path. Both builds agreed with python-chess on this corpus.

Ideas that were tried against legal positions and did not produce a
mismatch: a slider retreating off a check (that position is already illegal,
and `set_fen` rejects the side that moved), a castling rook "seeing" the
enemy king through the vacated corner (the landing squares occupy the first
rank, or the diagram was already opposite check), a pin test that treats a
move on the far side of the king as aligned (a pseudo-legal slider cannot
pass its own king), and a capture that opens a line (the capturer occupies
the target; en passant is the exception and uses the slow path).

## Bench and the network update

`cmake -S forge-combo29 -B /tmp/forge-build -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++`
then `cmake --build /tmp/forge-build -j4`. The default `c++` driver is Clang
18.1.3 and its link failed for lack of `libstdc++`, so the build used g++
13.3.0. CMake's lock definitions and `-march=x86-64-v4` were left as written
in `CMakeLists.txt`. This is not the Windows clang ThinLTO+PGO executable.

The UCI commands are the ones in `scripts/check_pins.sh` (that script was
read, then the same commands were sent to `/tmp/forge-build/forge`, with the
transcript kept outside the tree). `bench` builds its own one-thread searcher
with a 16 MB hash, which is the pin setting.

| mode | depths 11, 13, 16, 20, 22 |
| --- | --- |
| net on | 312866, 862329, 3024920, 12389307, 34048354 |
| net off | 375354, 907205, 2448617, 13573040, 24506465 |

`position startpos` then `go perft 5` printed `nodes 4865609`. Those are the
ten bench pins and the perft pin in `LOCK.md`.

`tools/nnue_delta_probe.cpp` refreshes the compiled-in network, applies
`dirty_pieces` with `nnue::update`, makes the move, and refreshes again.
Compiled with the same hidden size 256, king-line, movelist, prefetch, PEXT,
and AVX-512 output settings as the lock, plus `-ffp-contract=off
-fno-fast-math`. On 17 diagrams and three random walks it checked 525 legal
moves: 13 castles, 6 en-passant captures, 41 promotions, and 36 null moves.
Every incremental accumulator matched the refresh bit for bit (`max_abs 0`),
every evaluated score matched, and unmake restored the refreshed accumulator.
A null move changes no pieces, so the refresh before and after it matched as
well.

## Limitations

- Castling is the standard e1/e8 form with rooks on a1/h1/a8/h8. There is no Chess960 path in `is_pseudo_legal`.
- `fen()` prints the stored en-passant square. The Zobrist key includes that file only when a legal en-passant capture exists. The halfmove clock is stored and printed, and it is not part of the key.
- `make_null_move` does not itself refuse a side that is in check. Search only calls it when `!in_check`. A null in check would clear `checkers_`.
- The MovePicker direct-check bonus orders moves. The oracle checks `gives_check` on generated moves, and it does not score that bonus.
- Diagrams with three checkers, or other impossible check geometry that `set_fen` already rejects, were not a separate suite.
- Fullmove and halfmove saturate at 65535.
- The internal probe cannot catch a clock that `set_fen` will happily reload. `legality_oracle.py` is the regression for the null fullmove bug.
- The measured binary is a Linux g++ release build. It is not the published clang PGO executable, and its NPS is not a speed result. Root book depth remains the only UCI use of `fullmove_`.
- This branch does not change the speed lock and should not be merged from this run. `LOCK.md`, `windows_build/SOURCE_INPUTS.sha256`, the receipts, and the published E1284F7F executable are unchanged. Rewriting those hashes to follow this edit would describe a binary that was not rebuilt.
- On the parent `efb2ff96`, `sha256sum -c windows_build/SOURCE_INPUTS.sha256` (run from `forge-combo29/`) already failed for five files this branch does not touch: `include/forge/nnue.hpp`, `include/forge/search.hpp`, `src/nnue.cpp`, `src/search.cpp`, and `src/uci.cpp`. `include/forge/board.hpp` and `src/board.cpp` matched there. After this fix they do not. The other 13 files still match. The sentence in `LOCK.md` that all 20 files pass was already false on the parent.
