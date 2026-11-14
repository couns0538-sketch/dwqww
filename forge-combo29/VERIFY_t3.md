# VERIFY t3

Branch `grok47/t3-clock-parse` at `5e7fda216e1c03981ede2955f9cf14866f6c992a`.
Base `16833ecc03b425586f91f4c8834dea8807bf4c22`.
Verdict: **PASS**. t4 is the better clock fix.

## Rule check

Files: `include/forge/search.hpp`, `include/forge/uci_clock.hpp`, `src/uci.cpp`, `tests_t3/clock_commands.txt`, `tests_t3/clock_parse_test.cpp`, `REPORT_t3.md`. All mode 100644. No executable, archive, script, workflow, or Python. Engine source: 60 insertions, 8 deletions. `depth`, `nodes`, `mate`, and `movestogo` stay on the old 32-bit reader.

## Safety

`parse_clock_ms` is a pure `std::from_chars` helper. No network, process start, registry, environment access, obfuscation, or file write. The test includes only `forge/uci_clock.hpp`.

## Build

Clang configure failed (`cannot find -lstdc++`). g++ Release and ASan/UBSan both `Built target forge`.

## Pins

```
info string bench depth 11 nodes 312866 time 165 nps 1896157
info string bench depth 13 nodes 862329 time 438 nps 1968787
nodes 4865609
```

## Task test

```
g++ -std=c++20 -O3 -ffp-contract=off -fno-fast-math -march=x86-64-v4 -fsanitize=address,undefined -fno-omit-frame-pointer -g -I include tests_t3/clock_parse_test.cpp
```

Branch: `clock_parse_test passed`, exit 0.
Lock include path: `fatal error: forge/uci_clock.hpp: No such file or directory`, so the test does not build there.

Release engine, one command, reader stopped at the stated wait:

- Lock `go wtime 3000000000`: within 0.4s the last line was `info depth 5 seldepth 9 score cp 6 nodes 1001 ...`. An earlier sanitizer probe got `bestmove a2a3` within 200ms.
- This branch `go wtime 3000000000`: still searching at 0.44s, last line `info depth 17 ... nodes 600227 ... time 317`.
- This branch `go movetime +80`: `bestmove e2e4` at wall 91.8ms, with info lines up to depth 12.
- This branch `go movetime -5` and `go movetime 0`: `bestmove a2a3` in about 35ms and no info line. That is the 1ms budget the report describes for a clamped or zero clock, not the 3000000000 bug.
- `go depth +8` on this branch: only `info depth 1 ... nodes 26`. The leading plus is still rejected. t4 prints the depth-8 line for the same command.

## Report claims

Reproduced: the unit test, the lock's huge `wtime` collapsing, this commit keeping that clock alive, and `movetime +80` taking a real slice of time. Not reproduced from the report's stored transcript: the exact info text of `python3 /tmp/t3_measure.py`, which is not in the branch. No Elo or speed claim was checked.

## Pair

t4 is better. It fixes the same 3000000000 clock and also `go depth +8`, which this branch still treats as depth 1.
