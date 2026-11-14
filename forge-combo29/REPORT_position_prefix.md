# Position command: what was wrong, what the run found, what changed

Lock source is `lock/combo29-20261110` at `16833ecc`. The session board lives in `main` in `forge-combo29/src/uci.cpp`. `position` calls `apply_position`. `go`, including `go perft`, reads that same board. If `apply_position` returns without assigning, the next `go` searches the previous game.

## What was wrong

`apply_position` copied the session board into a local `candidate` and edited only that copy. The session board was replaced at the bottom of the function, after every move token had been accepted. Two returns in the lock skipped that assignment, so a command that had already been parsed was thrown away.

The lock function, from the `startpos` / `fen` setup through the move loop, was:

```cpp
if (!(input >> token)) {
    board = candidate;
    return;
}
if (token != "moves") return;
while (input >> token) {
    const auto move = candidate.parse_uci(token);
    if (!move.has_value()) {
        std::cout << "info string illegal move " << token << std::endl;
        return;
    }
    forge::Undo undo;
    (void)candidate.make_move(*move, undo);
}
board = candidate;
```

`board = candidate` is the only write to the session board on this path. The early `return` on `token != "moves"` and the early `return` on a rejected move both leave `board` as it was when the command started.

`parse_uci` accepts a token only when it is 4 or 5 characters and equals the UCI form of one move in `legal_moves()`. Anything else, including `NOTAMOVE`, is `nullopt`. The engine then prints `info string illegal move ...` and, on the lock, returns. The message says the move was rejected. The assignment that would have kept the position never runs.

That is the whole defect. The new position is built. The illegal token is reported. The built position is discarded.

Three commands hit it:

- `position startpos extra`. `startpos` loads the standard position into `candidate`. The next token is `extra`, not `moves`, so the function returns at `if (token != "moves") return`. The session board stays on the previous game.
- `position startpos moves NOTAMOVE`. `startpos` loads. The token `moves` is accepted. `NOTAMOVE` fails `parse_uci`. The function prints the illegal-move line and returns. `candidate` is the start position and is not copied back.
- `position startpos moves e2e4 NOTAMOVE`. `e2e4` is legal, so `make_move` has already changed `candidate`. `NOTAMOVE` then fails. The return drops `candidate`, including the `e2e4` that was already played. The session board is again the previous game, not the position after `e2e4`.

Paths that already assigned, and that this change does not alter:

- `position` with no token returns before any setup. The session board stays.
- A first token other than `startpos` or `fen` returns before any setup.
- `position startpos` and `position fen <six valid fields>` with nothing after them hit `if (!(input >> token)) { board = candidate; return; }`.
- A full legal move list reaches `board = candidate` at the bottom.
- An invalid FEN prints `info string invalid FEN: ...` and returns before the move loop. The previous game stays. That return is still there.

## What the run found

The previous game was the checkmate `7k/6Q1/5K2/8/8/8/8/8 b - - 0 1`. Black is to move. The black king is on h8, the white king on f6, the white queen on g7. The queen attacks h8, and it also attacks the three flights g8, h7, and the square g7 it stands on. `go perft 1` from that position printed `nodes 0`. `go perft 2` is also 0, because there is no legal move to expand. A later perft total of 0 means the session board is still that mate.

The start position has 20 legal moves, so `go perft 1` is 20 and `go perft 2` is 400. After `e2e4`, `go perft 2` is 600. Those three totals are how the transcript tells the three positions apart.

The lock `uci.cpp` (the release binary built for the capture-list branch; that branch does not change `uci.cpp`) was given the mate, then each broken command. Output, in order:

- mate, `go perft 1`: `nodes 0`
- `position startpos moves NOTAMOVE`, then `go perft 1`: `info string illegal move NOTAMOVE`, then `nodes 0`
- `position startpos moves e2e4 NOTAMOVE`, then `go perft 2`: `info string illegal move NOTAMOVE`, then `nodes 0`
- `position startpos extra`, then `go perft 2`: `nodes 0`
- `position startpos moves e2e4`, then `go perft 2`: `nodes 600`
- `position fen 8/8/8/8/8/8/8/8 w - - 0 1`, then `go perft 1`: `info string invalid FEN: invalid FEN fields`, then `nodes 20`

The last two lines are the control. A fully legal `e2e4` does replace the mate, and the perft total becomes 600. The invalid FEN does not replace that `e2e4` position: the following `perft 1` is 20, which is black to move after `e2e4`, not a new empty board and not the mate. So the lock already kept a good position and already refused a bad FEN. It only dropped the candidate when a later token was unexpected or illegal.

## What changed

After a valid `startpos` or FEN, tokens are read until the line ends or the token is `moves`. If the line ends first, the new position is assigned. If `moves` appears, every following token that `parse_uci` accepts is played. The first token it rejects still prints `info string illegal move ...`, and then the candidate is assigned. That candidate holds the new position plus every move accepted before the bad token.

`position startpos foo moves e2e4` therefore plays `e2e4`. The lock ignored the whole command because `foo` was not `moves`. The fixed parser skips `foo`, sees `moves`, and plays the list.

The invalid-FEN return is the same return as on the lock. A bad FEN still does not replace the current game.

The search, the move generator, and `parse_uci` are unchanged. Bench and start-position perft were re-run because the binary was rebuilt.

## Files

- `forge-combo29/src/uci.cpp` — the two early returns now assign `candidate` first. Unexpected tokens before `moves` are skipped instead of aborting the command.
- `forge-combo29/tests_position/commands.txt` — the UCI transcript.
- `forge-combo29/tests_position/expected.txt` — the perft totals the fixed binary printed.
- `forge-combo29/REPORT_position_prefix.md` — this file.

## Commands and output

`/usr/bin/c++` on this machine is Clang 18.1.3 and cannot link a CMake probe (`cannot find -lstdc++`). The release build uses `/usr/bin/g++` (GCC 13.3.0). The machine has AVX-512, so `FORGE_PORTABLE` was left off.

```
cmake -S /agent/repos/dwqww/forge-combo29 -B /tmp/forge-pos/release -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++ && cmake --build /tmp/forge-pos/release -j
```

The build finished and wrote `/tmp/forge-pos/release/forge`.

### Lock parser

```
printf '%s\n' 'uci' 'setoption name OwnBook value false' 'isready' 'position fen 7k/6Q1/5K2/8/8/8/8/8 b - - 0 1' 'go perft 1' 'position startpos moves NOTAMOVE' 'go perft 1' 'position startpos moves e2e4 NOTAMOVE' 'go perft 2' 'position startpos extra' 'go perft 2' 'position startpos moves e2e4' 'go perft 2' 'position fen 8/8/8/8/8/8/8/8 w - - 0 1' 'go perft 1' 'quit' | /tmp/forge-t1/release/forge
```

Perft totals, in order: `nodes 0`, then after `illegal move NOTAMOVE` still `nodes 0`, then after `e2e4 NOTAMOVE` still `nodes 0`, then after `startpos extra` still `nodes 0`, then a real `e2e4` is `nodes 600`, then the invalid FEN is rejected and the following `perft 1` is `nodes 20`.

### Fixed parser

```
/tmp/forge-pos/release/forge < /agent/repos/dwqww/forge-combo29/tests_position/commands.txt
```

Perft totals, in order:

- mate: `nodes 0`
- `startpos moves NOTAMOVE`: `info string illegal move NOTAMOVE`, then `nodes 20`
- reset to the mate, then `startpos moves e2e4 NOTAMOVE`: `info string illegal move NOTAMOVE`, then `nodes 600`
- reset to the mate, then `startpos extra`: `nodes 400`
- reset to the mate, then `startpos foo moves e2e4`: `nodes 600`
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

`bench 11` is 312866. `bench 13` is 862329. Start-position `go perft 5` is 4865609.

## Not verified

- No AddressSanitizer build of this parser. The change is which board is kept, not a buffer.
- No Elo or speed comparison. The `nps` figures are this run's own timing.
- `go nodes` was not changed.
