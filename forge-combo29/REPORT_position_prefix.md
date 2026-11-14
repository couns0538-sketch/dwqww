# Position command keeps a legal prefix

## What was wrong

`apply_position` in `src/uci.cpp` built the requested position on a candidate board and assigned it only after every move token was accepted. Two returns skipped that assignment:

- a token other than `moves` (`position startpos extra`);
- a move token `parse_uci` rejected (`position startpos moves NOTAMOVE`, or a legal move followed by a bad token).

The engine then stayed on the previous game. From the checkmate `7k/6Q1/5K2/8/8/8/8/8 b - - 0 1`, all three of those commands still printed `go perft 1` = 0 or `go perft 2` = 0.

An invalid FEN already returns before the assignment. That path is unchanged: a bad FEN does not replace the current game.

## The fix

After a valid `startpos` or FEN, the parser skips tokens until `moves` or the end of the line, then plays every legal move. On the first illegal move it prints `info string illegal move ...` and keeps the position reached so far. A later `moves` list after an unexpected token is still played.

## Files

- `forge-combo29/src/uci.cpp`
- `forge-combo29/tests_position/commands.txt`
- `forge-combo29/tests_position/expected.txt`
- `forge-combo29/REPORT_position_prefix.md`

## Commands

Release build, because `/usr/bin/c++` is Clang 18.1.3 and cannot link `libstdc++`:

```
cmake -S /agent/repos/dwqww/forge-combo29 -B /tmp/forge-pos/release -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++ && cmake --build /tmp/forge-pos/release -j
```

The build finished and wrote `/tmp/forge-pos/release/forge`.

### Lock parser, same transcript

The binary was the lock `uci.cpp` (the task-1 release build, whose search change does not affect `position`).

```
printf '%s\n' 'uci' 'setoption name OwnBook value false' 'isready' 'position fen 7k/6Q1/5K2/8/8/8/8/8 b - - 0 1' 'go perft 1' 'position startpos moves NOTAMOVE' 'go perft 1' 'position startpos moves e2e4 NOTAMOVE' 'go perft 2' 'position startpos extra' 'go perft 2' 'position startpos moves e2e4' 'go perft 2' 'position fen 8/8/8/8/8/8/8/8 w - - 0 1' 'go perft 1' 'quit' | /tmp/forge-t1/release/forge
```

Perft totals, in order: `nodes 0`, then after `illegal move NOTAMOVE` still `nodes 0`, then after `e2e4 NOTAMOVE` still `nodes 0`, then after `startpos extra` still `nodes 0`, then a real `e2e4` is `nodes 600`, then the invalid FEN is rejected and the following `perft 1` is `nodes 20` (the `e2e4` position, not a new board).

### Fixed parser

```
/tmp/forge-pos/release/forge < /agent/repos/dwqww/forge-combo29/tests_position/commands.txt
```

Perft totals, in order:

- mate: `nodes 0`
- `startpos moves NOTAMOVE`: `info string illegal move NOTAMOVE`, then `nodes 20`
- `startpos moves e2e4 NOTAMOVE`: `info string illegal move NOTAMOVE`, then `nodes 600`
- `startpos extra`: `nodes 400`
- `startpos foo moves e2e4`: `nodes 600`
- invalid FEN: `info string invalid FEN: invalid FEN fields`, then `nodes 600` (the `e2e4` position is kept)
- `position startpos`: `nodes 400`

Those totals match `tests_position/expected.txt`.

### Bench pins

```
printf '%s\n' 'uci' 'setoption name Threads value 1' 'setoption name Hash value 16' 'setoption name OwnBook value false' 'isready' 'bench 11' 'bench 13' 'position startpos' 'go perft 5' 'quit' | /tmp/forge-pos/release/forge
```

```
readyok
info string bench depth 11 nodes 312866 time 163 nps 1919423
info string bench depth 13 nodes 862329 time 427 nps 2019505
nodes 4865609
```

`bench 11` is 312866. `bench 13` is 862329. Start-position `go perft 5` is 4865609. The per-move perft 5 lines match the task-1 run (the same 20 numbers, total 4865609).

## Not verified

- No AddressSanitizer build of this parser. The change is a control-flow assignment, not a buffer.
- No Elo or speed comparison. The `nps` figures are this run's own timing.
- `go nodes` was not changed.
