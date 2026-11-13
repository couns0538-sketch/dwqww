# Repetition, 50-move rule, and insufficient material

Checked on 13 November 2026 against `efb2ff96` (`fable/standalone-h512-20261111`).
The fixes are commit `7639e548930ed3b4b68dc4679adfb63f97bc6b12` on `cursor/draw-rules-history-tt-cb8e`.
This note is a later commit on the same branch. Nothing here was merged.

## What was wrong

Game adjudication at the root already used threefold repetition, a 50-move clock of 100 or more (checkmate still wins when the side to move has no legal move), and insufficient material. Inside the search, three interactions were wrong.

- Search repetition treated the root occurrence as an immediate draw. Returning to the root is only the second occurrence. A draw needs a repeat strictly after the root, or two earlier occurrences (threefold).
- A null move incremented the 50-move clock. A null move is not a game ply. On the unmodified search, that extra ply is what made queen versus king at clock 92 report a draw at depth 8. After the clock stopped advancing, the same search reported `cp 695` at depth 8 (87k nodes): the leaf one ply short of the limit stood pat on the material evaluation.
- A mate score in the transposition table was adjusted for ply and then trusted even when the mate distance ran past the moves left before the 50-move draw. The stored score also does not carry the repetition path. Entries were reusable across clocks whenever both clocks were below 90, including when one search could reach the draw and the stored search could not.

Quiescence at clock 99 now scores a legal quiet non-pawn move as a draw. Captures and pawn moves still reset the clock and are searched. A proven mate score is left alone. If every quiet move is a pawn move or is illegal, the static evaluation stands, because a capture is forced.

## Tests

Unit test, from `forge-combo29`, compiler `/usr/bin/g++`, `FORGE_PORTABLE=ON`, `FORGE_MARCH=x86-64-v3`, `Release`:

```text
cmake --build /tmp/forge-draw --target draw_rules_test
/tmp/forge-draw/draw_rules_test
```

Result: `draw_rules_test passed`. It covers twofold versus threefold, a repeat strictly after the root, the null-move clock and the repetition barrier, insufficient material (including same-color bishops, opposite-color bishops, and king and two knights versus king), and the mate-horizon and table-usability predicates.

Engine tests used `/tmp/forge-draw/forge` with `Threads 1`, `OwnBook false`, `UseNNUE false`. The adjudication rows used `Hash 32`. The queen-versus-king node counts used `Hash 16`. The unmodified binary was built from `efb2ff96` with the same flags and `Hash 16` for that position.

| Case | Patched result |
| --- | --- |
| Twofold knight shuttle, `go depth 4` | `cp 13`, 235 nodes, `bestmove d2d4` (search continues) |
| Threefold knight shuttle, `go depth 3` | `cp 0`, 0 nodes |
| King versus king | `cp 0`, 0 nodes |
| Same-color bishops | `cp 0`, 0 nodes |
| Opposite-color bishops, `go depth 3` | `cp 2`, 122 nodes (not adjudicated) |
| King and two knights versus king, `go depth 3` | `cp 493`, 319 nodes (not adjudicated) |
| Rook versus king, clock 100 | `cp 0`, 0 nodes |
| Rook versus king, clock 99, `go depth 4` | `cp 0`, 76 nodes |
| Mate in 1 at clock 0, `go depth 4` | `mate 1`, `a1a8`, 64 nodes |
| Same position then clock 99, same process, `go depth 3` | `mate 1`, `a1a8`, 48 nodes |
| Mate in 1 at clock 100 | `cp 0`, 0 nodes |
| `r7/8/8/8/4k3/8/8/R3K3 w - - 99 80`, `go depth 3` | `cp 415`, `a1a8` (the capture resets the clock) |
| Queen versus king, clock 96, `go depth 6` | `cp 0` from depth 3 onward |
| Queen versus king, clock 92, `go depth 10` | depth 8 `cp 0`, 90783 nodes; depth 10 `cp 0`, 341655 nodes |
| `go perft 4` from the start position | `197281` |

Unmodified `efb2ff96` on queen versus king at clock 92: depth 8 `cp 0`, 87721 nodes. Depths 1 through 7 were material scores (`cp 696` at depth 7). After the null-move clock change and before the quiescence correction, depth 8 was `cp 695` at 86842 nodes. The correction restores the draw at a similar node count (90783).

`bench` (default network settings, same flags) matches `efb2ff96`:

| Depth | Nodes |
| --- | --- |
| 8 | 67223 |
| 10 | 172081 |

## Limitations

- A search that stops before clock 99 still prints a material score. On queen versus king at clock 92, depth 6 was `cp 704` and depth 7 was `cp 722`. Depth 5 printed `cp 0` because extensions reached the draw, then depth 6 went back to a material score. The stable draw starts at depth 8.
- The transposition table still does not store the repetition path. Cutoffs are refused at clock 90 and above. Below that, a score from another history can still be used. That is the same boundary the main search already used.
- A position set by FEN has no history before that FEN. Repetition from earlier in the game is visible only when the UCI `moves` list is sent.
- King and two knights versus king is not adjudicated. A mate exists if the lone king cooperates, so this is not insufficient material. King and bishop versus king, king and knight versus king, king versus king, and bishops all on one color are adjudicated.
- When every move draws, the chosen move is whichever line the search keeps. A warm table changed queen versus king at clock 92 from one drawing move to another; the score stayed `cp 0`.
- No strength match was played. `bench` at halfmove 0 is unchanged through depth 10, which does not reach this horizon.
