# VERIFY t4

Branch `grok47/t4-clock-parse` at `0ccc839bd9c4c2c73070b1fa5048cbd8009e9eb9`.
Base `16833ecc03b425586f91f4c8834dea8807bf4c22`.
Verdict: **PASS**. Better than t3.

## Rule check

Files: `include/forge/go_numbers.hpp`, `include/forge/search.hpp`, `src/uci.cpp`, `tests_t4/check_clock.cpp`, `clock_commands.txt`, `clock_expected.txt`, `go_numbers_test.cpp`, `REPORT_t4.md`. All mode 100644. No executable, archive, script, workflow, or Python. Engine source: 111 insertions, 24 deletions. The new parser is also used for depth, mate, movestogo, and nodes.

## Safety

`parse_i64_token`, `clamp_clock_ms`, and `parse_u64_token` are pure parsers. No network, process start, registry, environment access, obfuscation, or file write. `check_clock.cpp` only reads an expected file and stdin.

## Build

Clang configure failed (`cannot find -lstdc++`). g++ Release and ASan/UBSan both `Built target forge`.

## Pins

```
info string bench depth 11 nodes 312866 time 164 nps 1907719
info string bench depth 13 nodes 862329 time 442 nps 1950970
nodes 4865609
```

## Task test

`go_numbers_test` against this include tree printed `pass`, exit 0. Against the lock include tree: `fatal error: forge/go_numbers.hpp: No such file or directory`.

Release binary, commands sent, then stdout read for up to 3s with no following command:

`go depth +8` printed

```
info depth 8 seldepth 13 score cp 26 nodes 4099 nps 2049500 hashfull 2 time 2 pv d2d4 d7d5 c2c4 c7c6 e2e3 g8f6 h2h3 h7h6 c4d5
```

which is the depth-8 line in `clock_expected.txt`. A byte-at-a-time read also saw `bestmove` immediately after that line. The lock's `go depth +8` printed only `info depth 1 ... nodes 26`.

`go depth 12 wtime 3000000000` printed

```
info depth 12 seldepth 23 score cp 30 nodes 56720 nps 2025714 hashfull 36 time 28 pv e2e4 c7c5 g1f3 b8c6 b1c3 e7e6 d2d4 c5d4 f3d4 g8f6 f1e2 f8e7
```

which is the depth-12 line in `clock_expected.txt`. The engine's own `time` field is 28. The reader was stopped at 3s, after that line.

`go movetime +80` returned `bestmove e2e4` at wall 91.8ms. `go movetime -80` returned `bestmove a2a3` at wall 32.7ms with no info line.

The full `check_clock` transcript was run and exited 1. It is not evidence about the engine: the reader gave up on the first `go` at 60s (`go_ok=False`) and the next commands aborted the later searches, so those lines are depth 2. The isolated commands above are the ones that match the expected file.

## Report claims

Reproduced: `go_numbers_test`; `go depth +8` reaches the stored depth-8 line and the lock does not; `go depth 12 wtime 3000000000` reaches the stored depth-12 line (nodes 56720, `e2e4`); bench and perft pins. Not reproduced: a single passing `check_clock` pass over the whole command file, because this run's driver did not wait out the first search. No Elo or speed claim was checked.

## Pair

t4 is better than t3. t3 fixes wtime/movetime only, and `go depth +8` still ends at depth 1. t4's depth-8 and depth-12 lines match `clock_expected.txt`.
