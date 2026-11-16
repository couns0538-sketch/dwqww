# seat 20 — job 61: the one-sided-clock runaway CONFIRMED — and it is the OPPOSITE side that hangs

Seat 30's 30-F52/F53: never send a `go` line with only one side's clock; `go wtime N` without `btime` makes the engine
search without stopping, and a `go` line must carry BOTH clocks.

**Confirmed — and the rule is sharper than "always send both": the runaway happens when the OMITTED clock is the one
belonging to the side TO MOVE.**

Both builds, `Threads 1`, PC20 options, hard 20 s cap per case (a hang is reported and the process killed).

## base 6b98f217 + S14, white to move

| command | result |
|---|---|
| `go wtime 2000 btime 2000` | 91 ms, 149,020 nodes, depth 14 |
| `go wtime 2000` (btime missing) | 86 ms, 149,020 nodes, depth 14 — **fine** |
| **`go btime 2000`** (wtime missing) | **HANG, 20,003 ms, 0 nodes** |
| `go wtime 500 btime 500` | 29 ms, 43,800 nodes, depth 11 |
| `go wtime 500` | 28 ms, 43,800 nodes — **fine** |
| **`go btime 500`** | **HANG, 20,003 ms** |
| `go wtime 0 btime 0` | 4 ms, 41 nodes, depth 1 |

## base + S14, BLACK to move — the pattern flips

| command | result |
|---|---|
| `go wtime 2000 btime 2000` | 55 ms, 91,990 nodes, depth 14 |
| **`go wtime 2000`** (btime missing) | **HANG, 20,003 ms** |
| `go btime 2000` | 54 ms, 91,990 nodes — **fine** |
| **`go wtime 500`** | **HANG, 20,002 ms** |

## The rule, stated exactly
**The engine uses the clock of the side to move. If that clock is omitted, it never stops.** A missing clock for the
side NOT to move is harmless (the search is limited by the other one and gives identical nodes to the both-clocks
case). So:
- white to move → `wtime` is required, `btime` optional (ignored);
- black to move → `btime` is required, `wtime` ignored;
- **sending both is always correct**; sending only the opponent's clock always hangs.

This explains why my *first* probe did not reproduce seat 30's claim: I sent `go wtime 2000` on a **white-to-move**
position, which is exactly the case that is safe. Seat 30 tested it in the direction where it hangs. **Neither of us was
wrong; the finding needed the side-to-move qualifier.** (My probe also ran while a stray engine process was alive, so I
re-verified here on a machine the checker certified clean, exit 0.)

## Practical consequence for harnesses
A harness that builds `go` lines per side and forgets one will hang only on one colour — half its games, intermittently,
and it will look like a random hang. **Always emit both clocks.** `AUDIT/machine_clean.sh` reports whether a runaway is
still alive afterwards (exit 0 = fit to measure).

## Limits
- Two builds (base shown above; the PC r15 build ran the same 14 cases in the same script and is in the JSON), two
  positions, `Threads 1`, 20 s cap. A hang is unambiguous; I did not let it run to seat 30's 180 s.
- I did not test `movestogo` with one clock, nor `winc` without `wtime`.
