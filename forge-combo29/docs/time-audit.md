# Forge time-management audit

Audited the combo29 UCI clock on commit `16833ecc` (`lock/combo29-20261110`). Two defects were confirmed on a release build and fixed. The soft and hard allocation formulas were left as they are.

## How time is applied

`go` reads only the side to move. `wtime`/`btime` and `winc`/`binc` for the other side are ignored. `moves_to_go == 0` is sudden death. The default move overhead is 10 ms; the tests set it to 0 except for the overhead case.

In `Worker::search`:

- `movetime` wins over the clock. The hard limit is `max(1, movetime - overhead)`.
- Otherwise `available = max(1, time - overhead)`.
- With `movestogo`: `soft = available / (min(mtg, 50) + 1) + increment * 3 / 4`, and `hard = min(available * 4 / 5, soft * 4)`.
- Sudden death uses the tune defaults `TmSoftDivisor=22`, `TmIncrementPercent=75`, `TmHardPercent=60`, `TmHardSoftMultiple=5`.
- Both limits are then clamped to `[1, available]`. The hard limit does not exceed the clock minus overhead, except for the 1 ms floor when the clock is already inside the overhead.

The main worker samples the clock every 1024 local nodes and between iterations. `stop` is the same atomic. A ponder budget stays at 0 until `ponderhit`; `elapsed_ms()` then counts from that timestamp.

## Confirmed defects

**A clock above the 32-bit range was played as a forfeit.** `std::from_chars` into `int` returns `result_out_of_range` for `3000000000` and `2147483648` and leaves the out-parameter at 0. `read_int` treated every failure as 0, and 0 is the explicit flagged clock, so the search returned the first legal move immediately. Before the fix, `go wtime 3000000000 btime 3000000000` (OwnBook off) came back at depth 0 with `bestmove a2a3` in 5.2 ms. The same parse turned `movestogo 3000000000` into `movestogo 1` (`max(1, 0)`), which spends about 80% of the clock, and it dropped an overflowing increment.

A full token that is out of range now clamps to `INT_MAX` or `INT_MIN`. Existing `max(0, …)` clamps then keep a negative clock at 0 and turn a huge positive clock into a long control. A token with trailing junk (`3000000000abc`) is still 0, because the whole token was not a number. A leading `+` is still 0: `from_chars` rejects it.

**`go perft` ignored `stop` and blocked the command thread.** Perft ran synchronously on the UCI thread. `go perft 6`, then `stop` about 80 ms later, still printed `nodes 119060324` at 643 ms, and `isready` was not answered until that line. Perft now runs on the search worker. The walk polls the stop flag at depth 2 and above. On cancel it prints `info string perft stopped` and does not print a `nodes` total. Move lines already emitted stay. Completed counts are unchanged: startpos perft 1/2/4/5/6 are 20, 400, 197281, 4865609, and 119060324.

## Evidence after the fix

Release build with `g++` (`-O3`, `FORGE_MARCH=x86-64-v4`) at `/tmp/forge-build/forge`. Reader is a daemon thread over stdout. `select` plus a text-mode `readline` was not used: the text wrapper buffers ahead and that pattern reports false hangs.

```text
python3 forge-combo29/tools/uci_time_audit.py /tmp/forge-build/forge
ctest --test-dir /tmp/forge-build --output-on-failure
```

`ctest` passed `uci_time_audit` in 3.86 s on the final suite. An earlier run of the same script passed in 3.93 s, and a shorter predecessor passed twice before the overflow-budget cases were added. OwnBook off, Threads 1, Hash 16, overhead 0 unless noted.

| Case | Result |
| --- | --- |
| movetime 40 / 100 | 40.6 ms / 100.4 ms |
| movetime 100, overhead 40 | 60.8 ms |
| movetime 70 with wtime 4000 | 70.8 ms |
| white wtime 70, black clock 8000 | 5.0 ms |
| black btime 70 after e2e4 | 2.8 ms, `bestmove e7e5` |
| wtime 100, winc 9000, movestogo 1 | 80.9 ms (under the 100 ms clock) |
| wtime 160, winc 8000, sudden death | 97.2 ms (60% hard cap) |
| wtime 2000, movestogo 1 vs 25 | 1425 ms vs 110 ms, both under 2000 |
| wtime 200, winc 3000000000 | 120.6 ms |
| wtime 1000, movestogo 3000000000 | 12.1 ms (capped at 50 moves, not 1) |
| wtime 0 and wtime -3000000000 | 1.6 ms and 1.4 ms, with a move |
| wtime 3000000000 | still searching at 250 ms; stop 0.8 ms |
| black btime 3000000000, white wtime 20 | still searching; not the opponent clock |
| white wtime 60, black btime 3000000000 | 2.8 ms |
| wtime 3000000000abc | 1.6 ms (junk stays zero) |
| stop during movetime 4000 / infinite | 0.3 ms / 0.6 ms, one bestmove |
| ponder movetime 120 | no bestmove before ponderhit; 120.9 ms after |
| stop while pondering | 0.8 ms |
| depth 24 plus wtime 80 | 5.4 ms |
| four plies from a 180 ms clock | finished at 151 ms, no forfeit |
| perft 6, then isready, then stop | readyok 0.6 ms; `info string perft stopped` 0.5 ms; no `nodes 119060324` |

A separate transcript of the two fixes, after `uciok`:

```text
go wtime 3000000000 btime 3000000000
info depth 1 seldepth 1 score cp 1 nodes 26 nps 0 hashfull 0 time 0 pv d2d4
stop
bestmove c2c4
```

```text
go perft 6
b2b3: 5310358
readyok
info string perft stopped
```

## What was checked and not changed

The allocation formulas, the 1024-node poll, movetime-over-clock precedence, and the 1 ms floor on an explicit zero clock all behaved as written. On this host the movetime overshoot was about 0.4–0.9 ms. Increment is added into the soft budget and then capped by the current clock, so a large increment is not spent before it arrives. A missing own-side clock leaves the search unlimited, which matches “only the side to move is clocked.”

## Limitations

- `bench` runs on the command thread with its own `Searcher`. `stop` does not interrupt it.
- `wtime +10` is still 0, because `from_chars` does not accept a leading `+`.
- `info time` during ponder is wall time from search start, so it includes time before `ponderhit`. The budget does not. The ponderhit case above is the budget measurement.
- `go perft 0` still prints `nodes 1` on the command thread. A stopped perft can leave per-move lines that were already printed.
- The committed suite is one thread on this machine. A much slower host can overshoot by more than a millisecond between 1024-node samples. That gap was not large enough here to lose on time.
- Book probes return immediately. The suite turns OwnBook off.
