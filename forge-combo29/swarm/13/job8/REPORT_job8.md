# REPORT_job8 — the PC's clock mode (6 s + 0.06 s), PC r15 under PC20, Threads 1

## What was asked
The remaining PC-path item from FABLE file 6 and the coordinator's direction: the owner's match clock
is 6 s + 0.06 s. Jobs 5 and 7 covered `go softnodes` and `go nodes`; the clock is a different limit
type and is the one path where a search can **lose on time**.

## The answer
**No overruns and no illegal moves in 80 clocked moves, but the engine uses only ~4 % of its clock.**

| property | result |
|---|---|
| moves measured | 80 (4 games × 20 plies, real clock state carried move to move) |
| overruns (time spent > time available) | **0** |
| illegal moves | **0** |
| wall time min / median / p99 / max | 98.5 / **207.5** / 1,306.1 / 1,306.1 ms |
| engine clock utilisation, median | **4.1 %** (min 2.5 %, max 23.2 %) |
| depths reached | 16 to 25, **median 19** |
| throughput | ~1.84 M nodes/s |

So on a 6-second clock the engine typically spends about **0.2 s** a move and reaches depth ~19. It is
not running out of time; it finishes the depths it can and stops well short of its allowance.

## Mechanism, tested rather than guessed
Allocation scales with the clock, so the small fraction is a design choice and not a stall:

| command | wall time |
|---|---|
| `go wtime 6000 btime 6000 winc 60 binc 60` | 363 ms |
| `go wtime 6000 btime 6000` (no increment) | 361 ms |
| `go wtime 6000 btime 6000 movestogo 40` | 88 ms |
| `go wtime 30000 btime 30000 winc 60 binc 60` | 1,283 ms |

Time scales roughly with remaining clock (6 s → ~0.36 s, 30 s → ~1.28 s, `movestogo 40` cuts it to
88 ms), and the 0.06 s increment changes nothing measurable at this clock. That is consistent with the
engine dividing the remaining time by a large move estimate.

## Determinism in this mode
Five identical `go wtime 6000 btime 6000 winc 60 binc 60` on startpos, fresh process each:
**365 / 366 / 365 / 367 / 366 ms, depth 19 every time, nodes 650,246 every time, `e2e4` every time.**
So the *search* is deterministic (same nodes, same depth, same move) and only wall time moves by ±2 ms.
The engine is completing depth 19 and stopping, not being cut off mid-depth — otherwise the node count
would vary.

## How sure
High for the zeros in the table (overrun, illegal move): each move's wall time is measured with a
monotonic clock around the `go`/`bestmove` pair, and the clock state is carried forward exactly as a
match would carry it (elapsed subtracted, increment added), which is the only way an overrun could
actually be provoked. Caveats under "not sure".

## Settings and build
PC r15 sha256 `068f0927...`, built `-DFORGE_MATE_ALPHA_GUARD=1`; **PC20** in full (Threads 1, Hash 16,
S14 + the six), every option name validated against the exe's `uci` list, `isready`/`readyok` after
every `setoption`, fresh process per game.

## Findings
- S-F10: on the PC's clock path (PC r15, PC20, Threads 1, Hash 16, 6 s + 0.06 s) the engine produced
  **0 overruns and 0 illegal moves in 80 clocked moves**, but used only **4.1 % of its clock** (median
  207 ms of 6,000 ms) reaching median depth 19; allocation scales with the clock (6 s → ~0.36 s,
  30 s → ~1.28 s, `movestogo 40` → 88 ms) and the search is deterministic in nodes/depth/move
  (650,246 nodes, depth 19, `e2e4` five times). Reproduce:
  `cd forge-combo29/swarm/13/job8 && python3 clockpath.py ~/b/pc/forge clock4.fens /tmp/cp 20 6000 60`.

## Suspicions, not proven
- **The engine may be leaving strength on the table in clock games.** Using 4 % of a 6-second clock at
  depth ~19, when it could search deeper, is the kind of thing a strength match would settle and I have
  not run one. I am flagging it as a question, *not* a defect: it may be deliberate (stability, or a
  safety margin on a slow PC), and the owner's PC may be slower than this VM, which would raise
  utilisation on his machine without any code difference.

## What I did NOT do
- No strength match (would need many games; not my area).
- Only 4 games × 20 plies: enough to see overrun behaviour, not enough for a time-management
  distribution at p99.9.
- The owner's own match positions (**my standing limit**: 4 of the 12 G positions, not his games).
- Low-clock stress (`wtime 100`, `wtime 10`, `wtime 1`, `wtime 0`): another seat's area, and the
  file-6 priority is the 6 s clock.

## What I am NOT sure about
- Wall time includes process-independent python overhead between `go` and reading the line, which is
  small (~1 ms) relative to the 200 ms medians but is not zero.
- 80 moves is a small sample for the p99 column; the single 1.3 s maximum is one move, not a trend.
- This VM has 4 cores and is idle; the owner's PC is doing other work, so **his** utilisation will be
  higher than 4 % for the same code.

## Times
See `stamps.txt`.

## Last command output

```
$ ls
clock4.fens
clockpath.py
out
realgame12.fens
REPORT_job8.md
stamps.txt
```
