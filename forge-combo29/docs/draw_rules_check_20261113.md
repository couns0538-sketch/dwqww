# Repetition, the 50-move rule, and the transposition table

Branch `cursor/draw-rules-history-tt-cb8e`, compared with `efb2ff96` (`fable/standalone-h512-20261111`).
Nothing on this branch has been merged.

The root of a finished game was already adjudicated correctly: threefold repetition, a 50-move clock of 100 or more (checkmate still wins when the side to move has no legal move), and insufficient material. The mistakes were inside the search. A line could be called a draw before it was one, a draw could be missed and replaced by a material score, and a score saved in the transposition table could be replayed in a position where that score was no longer true.

## 1. Returning to the root was called a draw

`Board::is_repetition(root_index)` walks the position keys of the reversible moves. The old test was `i >= root_index`: any earlier copy of the current position at or after the root returned a draw immediately.

The copy at `root_index` is the position the search started from. Seeing it again is the second occurrence. Under the threefold rule that is not yet a draw. It becomes a draw only when the same position has occurred twice before this visit, or when the repeat is a position that was reached strictly after the root (the line has cycled and can be repeated forever).

The comparison is now `i > root_index`. A hit at the root itself only increments the earlier-occurrence count, and the function returns a draw when that count reaches two.

What that looked like in the engine, `Threads 1`, `OwnBook false`, `UseNNUE false`:

- Twofold knight shuttle (`g1f3 g8f6 f3g1 f6g8` once), `go depth 4`: the search continues, `cp 13`, 235 nodes, `bestmove d2d4`.
- The same shuttle twice, so the start position has occurred three times, `go depth 3`: `cp 0`, 0 nodes. The root adjudicates before any node is searched.
- One repeat of a position that was first reached after the root is a search draw. `draw_rules_test` plays `g1f3 b8c6 f3g1 c6b8` and checks that returning to the root is not a draw, then plays `g1f3` again and checks that the repeat of the post-root position is a draw.

A pawn move still clears the clock and the repetition window. `draw_rules_test` checks `e2e4` after a shuttle: the clock is 0 and neither the game test nor the search test reports a repetition.

## 2. A null move was counted as a 50-move ply

`Board::make_null_move` passed the turn without moving a piece, then did `halfmove_ + 1`. A null move is a search device, not a game ply. It must not move the 50-move clock. The undo record already stored the old clock, so unmake was restoring a value the make had changed for no game reason.

On queen versus king at clock 92, that extra ply was enough for the unmodified search (`efb2ff96`) to report a draw at depth 8: `cp 0`, 87721 nodes. Depths 1 through 7 were material scores (`cp 696` at depth 7). The draw was an artifact of the null-move clock, not a proof that every real line had reached 100.

After the increment was removed, and before the quiescence change below, the same search reported `cp 695` at depth 8 (86842 nodes). The leaf one ply short of the limit stood pat on the material evaluation. The null-move child was no longer a false draw, and the real draw was not seen either.

`plies_from_null_ = 0` was already set, and the repetition walk stops at that barrier, so a null move still cannot be looked through for a repetition. `draw_rules_test` checks that the clock is unchanged across make and unmake, and that a cycle played after the null is still a search draw.

## 3. Quiescence at clock 99 kept the material score

At clock 99 the side to move can play a legal quiet non-pawn move. The child has clock 100. `Worker::is_draw` then returns a draw unless that move is checkmate: checkmate on the hundredth half-move still wins, and every other position at clock 100 is a draw. The side to move can therefore choose a draw, unless every quiet non-pawn move is illegal and the only tries are captures or pawn moves, which reset the clock.

Quiescence does not search quiet moves. It stood pat on the static evaluation. Queen versus king was scored as a win of several hundred centipawns at the exact ply where any queen move that did not mate was a draw. The losing side had the same bug in the other direction: a king-only position was scored as a loss even though any king move drew.

The quiescence stand-pat is now 0 when clock is at least 99, the evaluation is not a mate score, and at least one legal quiet non-pawn, non-promotion move exists. Captures and pawn moves are still generated and searched, so a capture that resets the clock can still raise the score above 0. If no such quiet move exists, the static evaluation is left alone, because a capture is forced. A mate score is not replaced by 0.

Measured after this correction, before the horizon guard in section 6:

- Rook versus king, clock 99, `go depth 4`: `cp 0`, 76 nodes.
- `r7/8/8/8/4k3/8/8/R3K3 w - - 99 80`, `go depth 3`: `cp 415`, `a1a8`. The capture resets the clock, so the score stays a win.
- Queen versus king, clock 92: the draw returned at depth 8, `cp 0`, 90783 nodes. Depth 10 was `cp 0`, 341655 nodes. The 13 November note recorded depth 6 as `cp 704` and depth 7 as `cp 722` on that search.

## 4. A mate in the table was trusted past the 50-move horizon

Before a score is stored, a mate is converted to plies-to-mate from the node that produced it. On the way out, the old `score_from_tt(score, ply)` only subtracted or added `ply`. It did not ask whether that many plies still exist before the 50-move draw.

At clock 80, twenty plies remain before clock 100. A stored mate in 20 fits. A stored mate in 21 does not: the game would be drawn before that mate, unless an unrecorded capture or pawn move resets the clock. The table entry does not prove that such a move is in the line, so the score is not proof. The old function returned it anyway, and the search treated it as a cutoff.

`score_from_tt(score, ply, halfmove)` now refuses the mate when `MateValue - score` (or `MateValue + score` for a loss) is greater than `100 - clock`. The caller then searches again. A non-mate score is not a horizon decision. Mate in 1 at clock 99 is one ply and is kept; mate in 1 at clock 100 is refused because the move is no longer playable. `draw_rules_test` checks those boundaries.

The engine check used `6k1/8/6K1/8/8/8/8/R7`. `Ra8` is mate. At clock 0 and at clock 99, `go depth 3` is `mate 1`, `a1a8`. At clock 100 the root is adjudicated: `cp 0`, 0 nodes.

## 5. A stored score from a short clock answered a search that could reach the draw

The position hash does not include the 50-move clock or the repetition path. The old `score_usable` accepted an entry when both clocks were below 90, or when the clocks were equal. A depth-20 search stored at clock 0 could therefore answer a search at clock 89. The stored search finished at clock 20 and never saw the draw. The new search, at clock 89 and depth 20, reaches clock 109. The stored score is a material or mate result from a different rule.

The rule is now:

- If this search can reach clock 100 and the stored search could not, the entry is refused.
- If neither search can reach clock 100, the entry is usable. Both are inside the same rule.
- If both can reach it, the clocks must be equal. A draw proved at one clock is not a draw proved at another.

`use_depth` is the depth the caller is about to trust. The test takes the greater of that depth and the stored depth, so a deep entry cannot be laundered by asking about it from a shallow call. `draw_rules_test` checks clock 0 depth 20 against clock 89, a short search at clock 89 against a longer one at the same clock, and two different clocks that both cross the horizon.

Cutoffs in both `search` and `qsearch` are also refused when the clock is 90 or more. At that clock the same hash still covers different repetition histories, and the stored score does not carry the path. The mate-horizon test above has already dropped mates the 50-move rule can falsify; the clock-90 test is the repetition boundary. Below 90, a score from another history can still be used. That is the same boundary the main search already had, and this branch does not add the repetition path to the hash.

A direct check of that boundary: a threefold knight shuttle returns `cp 0` at 0 nodes because the root adjudicates. The same piece placement sent as a FEN, with no move list, has no earlier history. It searched as a normal opening, `cp 13`, 235 nodes at depth 4, both in the process that had just seen the threefold draw and in a fresh process. The table did not reuse the adjudicated draw for the FEN.

## 6. What the 14 November probes found

Clock 99 at the root, and the interior nodes of the short searches below, were already draws, mates, or captures. These used `/tmp/forge-draw/forge`, `Threads 1`, `Hash 16`, `OwnBook false`, `UseNNUE false`, and `ucinewgame` before each search.

| Case | Result |
| --- | --- |
| `6k1/8/6K1/8/8/8/8/R7 w - - 99 80`, `go depth 3` | `mate 1`, `a1a8`, 60 nodes |
| Same position at clock 0, `go depth 3` | `mate 1`, `a1a8`, 60 nodes |
| Same position at clock 100, `go depth 2` | `cp 0`, 0 nodes |
| `6k1/8/8/8/8/8/7r/Q5K1 w - - 99 80`, `go depth 3` | `cp 838`, `g1h2`, 128 nodes. `Kxh2` captures the rook and resets the clock |
| `4k3/8/8/8/8/8/4P3/4K3 w - - 99 40`, `go depth 3` | `cp 71`, `e2e4`, 66 nodes. The pawn move resets the clock |
| `r7/8/8/8/4k3/8/8/R3K3 w - - 99 80`, `go depth 3` | `cp 415`, `a1a8`, 160 nodes |
| `8/8/8/4k3/8/8/8/3QK3 w - - 99 80`, `go depth 4` | `cp 0`, 88 nodes |
| Same position at clock 98, `go depth 3` | `cp 0`, 144 nodes |
| `4k3/8/8/8/3q4/8/8/4K3 w - - 98 80`, `go depth 4` | `cp 0`, 35 nodes |

The miss was one ply earlier than clock 99. On `8/8/8/4k3/8/8/8/3QK3 w - - 92 80`, a depth-7 search is the first iteration whose quiet leaves stand on clock 99, where quiescence now returns a draw. Before the horizon guard that search still printed a material score:

| Depth | Score before the guard | Nodes |
| --- | --- | --- |
| 5 | `cp 895` | 2889 |
| 6 | `cp 767` | 12937 |
| 7 | `cp 722` | 44921 |
| 8 | `cp 0` | 113125 |

Reverse futility pruning returns the static evaluation when it is far enough above beta, without searching the moves. Null-move pruning searches a reduced depth after passing the turn. Neither looks at the quiet line that walks into the clock-99 draw, so both were cutting off with the material score. The 13 November numbers for depth 8 (90783 nodes) are the earlier queen-versus-king measurement after the quiescence correction. This table is a fresh search of the FEN above, on that same code, immediately before the guard.

Both prunes are now skipped when `halfmove_clock + depth >= 99`. The same position then printed:

| Depth | Score | Nodes |
| --- | --- | --- |
| 5 | `cp 860` | 1876 |
| 6 | `cp 722` | 18650 |
| 7 | `cp 0` | 44478 |
| 8 | `cp 0` | 65779 |

Depth 6 stays a material score. Clock 92 plus 6 plies reaches clock 98, and the clock-99 stand-pat is not in that tree. Depth 5 also moves, from `cp 895` to `cp 860`, because a check extension can make some node inside that iteration satisfy `clock + depth >= 99`. The score is still a material score.

Mate in 1, the rook capture `a1a8` at `cp 415`, the pawn push `e2e4` at `cp 71`, and the hanging-rook capture `g1h2` at `cp 838` were unchanged by the guard.

## What changed

- `forge-combo29/src/board.cpp`: `make_null_move` no longer increments `halfmove_`. `is_repetition(root_index)` uses `i > root_index` for an immediate search draw.
- `forge-combo29/include/forge/board.hpp`: the comment on `is_repetition(root_index)` matches that rule.
- `forge-combo29/include/forge/search.hpp`: `score_from_tt` takes the halfmove clock and refuses a mate past the horizon. `TTEntry::score_usable` takes the depth the caller wants to trust and applies the three cases in section 5.
- `forge-combo29/src/search.cpp`: the old ply-only `score_from_tt` was removed. Search and quiescence pass the clock and the depth into `score_usable`. Cutoffs require clock below 90. Quiescence stand-pat at clock 99 is 0 when a legal quiet non-pawn move exists. Reverse futility and null-move pruning are skipped when `halfmove_clock + depth >= 99`.
- `forge-combo29/tests/draw_rules_test.cpp`: twofold against threefold, a repeat strictly after the root, the null-move clock and the repetition barrier, insufficient material, and the mate-horizon and table-usability predicates.
- `forge-combo29/CMakeLists.txt`: builds `draw_rules_test` from the test, `board.cpp`, and `bitboard.cpp`.

Commits:

- `7639e548930ed3b4b68dc4679adfb63f97bc6b12` — sections 1 through 5, the quiescence stand-pat, and `draw_rules_test`.
- `844cef9a167be65a30c98d8da8f7c85f98cddc0f` — the first version of this note.
- `21996d6ed1b87d254fcf16d3f0ee8bfb656a05f2` — the horizon guard in section 6.

## Checks that stayed the same

Unit test, from `forge-combo29`, compiler `/usr/bin/g++`, `FORGE_PORTABLE=ON`, `FORGE_MARCH=x86-64-v3`, `Release`:

```text
cmake --build /tmp/forge-draw --target draw_rules_test
/tmp/forge-draw/draw_rules_test
```

`draw_rules_test passed`. The same file does not cover the search prunes; those are the engine searches above.

`go perft 4` from the start position: `197281`.

`bench`, fresh process, default network, the eight built-in positions, all of which have clock 0:

| Depth | Nodes |
| --- | --- |
| 8 | 67223 |
| 10 | 172081 |

Both match `efb2ff96`. Clock 0 plus depth 10 does not reach the horizon guard.

Other adjudication, `Hash 32` for these rows:

| Case | Result |
| --- | --- |
| King versus king | `cp 0`, 0 nodes |
| Same-color bishops | `cp 0`, 0 nodes |
| Opposite-color bishops, `go depth 3` | `cp 2`, 122 nodes, not adjudicated |
| King and two knights versus king, `go depth 3` | `cp 493`, 319 nodes, not adjudicated |
| Rook versus king, clock 100 | `cp 0`, 0 nodes |
| Queen versus king, clock 96, `go depth 6` | `cp 0` from depth 3 onward |

## What is still wrong, or deliberately unchanged

- A search that stops before clock 99 still prints a material score. On the queen-versus-king FEN in section 6, depth 6 is `cp 722`, 18650 nodes.
- The transposition table does not store the repetition path. Below clock 90 a score from another history can still be used.
- A FEN has no history before that FEN. Repetition from earlier in the game is visible only when the UCI `moves` list is sent.
- King and two knights versus king is not adjudicated. A mate exists if the lone king cooperates, so this is not insufficient material. King and bishop versus king, king and knight versus king, king versus king, and bishops all on one color are adjudicated.
- When every move draws, the chosen move is whichever line the search keeps. A warm table changed queen versus king at clock 92 from one drawing move to another. The score stayed `cp 0`.
- No strength match was played.
