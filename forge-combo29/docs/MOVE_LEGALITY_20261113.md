# Move legality — 2026-11-13

Branch `cursor/move-legality-82b6`, based on `fable/standalone-h512-20261111`.
Standard chess only. This note records one clock bug, the fix, and the tests
that compared Forge with python-chess 1.11.2. `LOCK.md` is unchanged. Bench
pins were left unmeasured.

## Result

Legal move generation, check, pins, castling, en passant, promotions, and
make/unmake matched python-chess on 7,891 positions, on both the king-line
build and the full-occupancy build. Published perft totals matched. Address
and undefined-behavior sanitizers reported nothing on the probe self-test.

One rules bug reproduced: a null move by Black left the fullmove counter
unchanged. A real Black move already advanced it. After the fix, the null
FEN matches python-chess, and unmake restores the previous counter.

## The bug

`Board::make_null_move` cleared the en-passant square, flipped the side to
move, and incremented the halfmove clock. It did not increment `fullmove_`
when Black was the side to move. `make_move` does that before it flips the
side. python-chess 1.11.2 does the same for a null ply: it increments
`halfmove_clock`, increments `fullmove_number` when the side to move is
Black, then swaps the turn and clears en passant (`chess.Board.push`).

The first oracle run, before the fix, stopped after 30 failing positions
(428 matched, 31 failed, 63 error lines). Every error was this clock.
Legality, `gives_check`, move flags, checkers, castling, en passant squares,
and child FENs were not among them. White nulls already matched, because a
White ply does not advance the fullmove counter.

Example, `r3k2r/8/8/8/8/8/8/R3K2R b KQkq - 0 1`:

| side | python-chess after a null ply | Forge before the fix |
| --- | --- | --- |
| Black | `r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 1 2` | `... w KQkq - 1 1` |
| White | `r3k2r/8/8/8/8/8/8/R3K2R b KQkq - 1 1` | already matched |

The halfmove clock was 1 on both sides. Only Black's fullmove was one low.
The same shape showed up on the en-passant pin positions, the stalemate
position, and start positions after one White move (the null was then
Black's ply).

The internal probe missed it. After a null it re-parses Forge's own FEN with
`set_fen`, and `set_fen` keeps whatever fullmove number the FEN contains.

## The fix

`NullUndo` now stores `fullmove`. `make_null_move` saves it and, while
`side_` is still the mover, increments it for Black, saturating at 65535,
the same cap `make_move` uses. `unmake_null_move` writes it back with the
other saved fields.

Search calls `make_null_move` only from the null-move pruning block, which
requires `!in_check`. `fullmove_` is read by UCI only to decide whether the
root is still inside the opening book (`game_ply` in `src/uci.cpp`). Search
does not read it, so this fix is expected to leave node counts unchanged.
That expectation was not re-measured with `bench`. The change is always on:
a switch would leave the clock wrong.

## Tests

From the repository root:

```
python3 forge-combo29/tools/legality_oracle.py
```

The script compiles two probes and compares both with python-chess:

| probe | flags |
| --- | --- |
| `/tmp/legality_kl1` | `FORGE_SPD_KING_LINES=1`, `FORGE_SPD_NO_ZERO_MOVELISTS=2`, `FORGE_SPD_PREFETCH_EARLY=1` |
| `/tmp/legality_kl0` | `FORGE_SPD_KING_LINES=0`, `FORGE_SPD_NO_ZERO_MOVELISTS=0`, `FORGE_SPD_PREFETCH_EARLY=0` |

Both use `-std=c++20 -O2 -DNDEBUG` and link `board.cpp` plus `bitboard.cpp`.
The king-line flags are the lock-style board settings. CMake does not
override `FORGE_SPD_KING_LINES`, and the header default is 1.

After the fix, on 2026-11-13, that command exited 0 in about 52 seconds:

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

## Limitations

- Castling is the standard e1/e8 form with rooks on a1/h1/a8/h8. There is no Chess960 path in `is_pseudo_legal`.
- `fen()` prints the stored en-passant square. The Zobrist key includes that file only when a legal en-passant capture exists. The halfmove clock is stored and printed, and it is not part of the key.
- `make_null_move` does not itself refuse a side that is in check. Search only calls it when `!in_check`. A null in check would clear `checkers_`.
- The MovePicker direct-check bonus orders moves. The oracle checks `gives_check` on generated moves, and it does not score that bonus.
- Diagrams with three checkers, or other impossible check geometry that `set_fen` already rejects, were not a separate suite.
- Fullmove and halfmove saturate at 65535.
- The internal probe cannot catch a clock that `set_fen` will happily reload. `legality_oracle.py` is the regression for the null fullmove bug.
- The full UCI binary was not rebuilt, and `bench` was not run. Search does not read `fullmove_`. Root book depth is the only UCI use, and only before search starts.
- This branch does not change the speed lock and should not be merged from this run.
