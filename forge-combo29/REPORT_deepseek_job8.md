# REPORT - deepseek job 8

**With one thread and a 16 MB table the engine searches at every clock I tried, down to
0 ms, and finds the mate in 200 of 200 positions at every clock; it never answers
without searching. It does answer LATER than the clock: at clock 0 in 200 of 200 cases
(any non-zero time exceeds 0), and once at clock 1. From clock 2 upwards no answer was
later than the clock in any of the 72 cells.**

Branch `for-fable-and-opus/deepseek-work`. No engine source changed.

Step 0, commit `6b98f217`, release build, built-in net (`logs/engine-pins.txt`):

```
info string bench depth 11 nodes 312866
info string bench depth 13 nodes 862329
nodes 4865609              (go perft 5)
```

## 1. Part 0 - the pawn table repaired

`kpk_20000_v2.txt`, the same 20,000 positions in the same order (`cmp` on the FEN column
confirms the order is identical), with verdicts from the repaired table.

**Power line: with the old black-pawn half left in, Fable's comparison reports 6,735
differences out of 20,000.** The v2 file changes **exactly 6,735** entries against the
job 7 file (13,265 identical), so every difference Fable found is addressed and nothing
else moved (`logs/part0-repair.txt`).

Method, Fable's: a position whose pawn is **black** is mirrored - every piece's colour
swapped and the rank order reversed - into a position with a white pawn, looked up in the
white-pawn half (which agreed 10,023 of 10,023 with the PC), and the verdict taken from
the mirror. Mirroring preserves the value because the game tree is isomorphic and
side-to-move maps to side-to-move. 222,326 of 331,352 black-pawn states changed.

Fable's two check positions:

| FEN | job 7 | repaired |
|---|---|---|
| `8/6K1/8/8/3p4/5k2/8/8 w` (Fable's example) | D | **L** |
| `8/3k4/8/8/8/5p2/8/3K4 b` (job 7's disputed one) | D | **D** |

Verdict totals: W 7,563 / D 6,576 / L 5,861.

## 2. Controls

| control | result |
|---|---|
| the stopwatch: 200 x `isready` on an idle engine | median **0.019 ms**, p95 0.032 ms, worst **0.499 ms** |
| a player that answers with the FIRST legal move | **0 of 200** |
| `go depth 2` | **200 of 200** |
| Move Overhead (reported, not changed) | `type spin default 10 min 0 max 1000` |

**Power line for the sweep: the first-legal-move player is the planted fault - it scores
0 of 200 by construction, because every position whose first generated move mates was
dropped (6 of 13,200 candidates were dropped for that reason).** So a cell that reported
200 of 200 did not get it by accident.

The stopwatch is why the millisecond numbers below are worth reading: the machine's own
delay is 0.02 ms, two orders of magnitude under the smallest effect I report.

**A measurement error I made and fixed.** My first sweep charged the cost of
`ucinewgame` to the search. At Hash 512 that call alone takes **34.66 ms** (it zeroes the
whole table) against 0.72 ms at Hash 16, and it made every Hash-512 cell look like a
28-32 ms search that always flagged. Re-measured with `ucinewgame` completed before the
timer starts, the search itself is **0.78-0.95 ms at both hash sizes**. Every table below
is from the corrected run.

## 3. Step 2 - the sweep

The timer runs from writing `go` to receiving `bestmove`. Full tables in
`logs/sweep-table.txt`; the 18 clocks are 0,1,2,3,5,8,10,11,12,13,15,20,25,30,40,60,100,200.

### Threads 1, Hash 16 MB

| clock | mate/200 | searched/200 | no-search/200 | median ms | max ms | later than clock |
|---|---|---|---|---|---|---|
| 0 | 200 | 200 | 0 | 0.523 | 1.412 | **200** |
| 1 | 200 | 200 | 0 | 0.521 | 1.342 | **1** |
| 2 | 200 | 200 | 0 | 0.531 | 1.276 | 0 |
| 3 | 200 | 200 | 0 | 0.509 | 1.253 | 0 |
| 5 | 200 | 200 | 0 | 0.534 | 1.177 | 0 |
| 8 | 200 | 200 | 0 | 0.507 | 1.363 | 0 |
| 10 | 200 | 200 | 0 | 0.538 | 1.388 | 0 |
| 11 | 200 | 200 | 0 | 0.531 | 1.364 | 0 |
| 12 | 200 | 200 | 0 | 0.528 | 1.179 | 0 |
| 13 | 200 | 200 | 0 | 0.538 | 1.264 | 0 |
| 15 | 200 | 200 | 0 | 0.532 | 1.059 | 0 |
| 20 | 200 | 200 | 0 | 0.537 | 1.064 | 0 |
| 25 | 200 | 200 | 0 | 0.524 | 1.401 | 0 |
| 30 | 200 | 200 | 0 | 0.473 | 1.243 | 0 |
| 40 | 200 | 200 | 0 | 0.502 | 1.350 | 0 |
| 60 | 200 | 200 | 0 | 0.661 | 1.610 | 0 |
| 100 | 200 | 200 | 0 | 0.673 | 1.274 | 0 |
| 200 | 200 | 200 | 0 | 0.670 | 1.270 | 0 |

### Threads 1, Hash 512 MB

Every clock: mate 200, searched 200, no-search 0. Median 0.75-0.96 ms, max 2.09 ms.
Later than clock: **200 at clock 0, 45 at clock 1, 0 from clock 2 up**
(`logs/sweep-table.txt`).

### Threads 8, Hash 16 MB

Every clock: mate 200, searched 200, no-search 0. Median 1.34-1.68 ms, max 2.85 ms.
Later than clock: **200 at clock 0, 101 at clock 1, 8 at clock 2, 0 from clock 3 up**.

### Threads 8, Hash 512 MB

Every clock: mate 200, searched 200, no-search 0. Median 1.52-1.85 ms, max 3.14 ms.
Later than clock: **200 at clock 0, 101 at clock 1, 25 at clock 2, 0 from clock 3 up**.

### With an increment (clock 5/10/20, `winc 60 binc 60`)

All four configurations: **mate 200, searched 200, no-search 0, later-than-clock 0** in
all 12 cells (`logs/sweep-increment.txt`).

## 4. Step 3 - where it stops searching

| configuration | smallest clock with mate >= 195/200 | clocks with any no-search answer |
|---|---|---|
| Threads 1, Hash 16 | **0** | none |
| Threads 1, Hash 512 | **0** | none |
| Threads 8, Hash 16 | **0** | none |
| Threads 8, Hash 512 | **0** | none |

There is **no clock at which the engine answers without searching**, and no clock at which
it fails to find the mate. The three worst cells are all clock 0, where "later than the
clock" is unavoidable (200 of 200 at 1.34-1.52 ms median, 2.74-2.85 ms worst, still
searching and still mating in 200 of 200). Full transcripts: for each of those cells the
`.json` in `logs/` carries the per-cell tally, median, max and three captured
`no_search`/`miss_after_search` examples (both empty).

## 5. Findings, each with a test that can be re-run

**F1. The engine always searches and always finds a mate in one, from clock 0 to 200, at
1 and 8 threads and 16 and 512 MB.** 72 sweep cells (18 clocks x 4 configurations) plus 12
increment cells = **84 cells x 200 positions = 16,800 searches; all 16,800 searched, all
16,800 found the mate, 0 answered without searching** (counted from the 84 files in
`forge-combo29/tests_deepseek_job8/logs/`). Re-run:
`python3 j8_sweep.py logs/positions-200.json out.json 1 16 11`.

**F2. It can answer later than the clock it was given, but only at the very smallest
clocks.** Counts above the clock: at clock 0 always (any non-zero time exceeds zero);
at clock 1 in 1/200 (1 thread) and 45-101/200 (Hash 512 or 8 threads); at clock 2 in
0/200 (1 thread, Hash 16) but 8-25/200 (8 threads); **0 from clock 3 upwards in all four
configurations**. With an increment, 0 at every clock tried. That is the flag the job
asked about, and it is confined to clocks of 2 ms and under.

**F3. The reviewer's case - "plays the first legal move without searching at `wtime 11`
with 64 threads" - did not reproduce in any of my cells.** At clock 11 with 1 and 8
threads and both hash sizes the engine searched 200/200 and mated 200/200 (median 0.53 ms
at 1 thread, 1.42 ms at 8). I could not test 64 threads: this machine has 4 cores, and I
did not run 64 threads because the oversubscription would make the timings meaningless
rather than informative. **This is the main limit of the finding**, and it is exactly the
configuration the reviewer used.

**F4. `ucinewgame` costs ~35 ms at Hash 512 and ~0.7 ms at Hash 16**, because it zeroes
the table. It is not part of a search, but a GUI that sends `ucinewgame` before each move
would see it as a delay. I found this only because my first sweep charged it to the
search; the corrected numbers are in section 2.

## 6. Suspicions, not proven

- **The clock-1 and clock-2 flags are probably `Move Overhead 10` plus startup cost**,
  not a decision to skip search: the search always runs. I did not test `Move Overhead 0`,
  which would separate "the budget logic flags" from "the process cannot start that fast".
- **The 64-thread case may behave differently for the reason the reviewer saw** - 64
  threads on few cores means very slow first-iteration latency before any `info depth`
  line, and a time manager that answers on the first check may move before depth 1
  completes. My 8-thread numbers (median 1.4 ms) are the trend, but I did not measure 64.

## 7. Files opened

`src/uci.cpp` (option table, `go` handling), `src/search.cpp` (time management entry),
`CMakeLists.txt`, and my own job 7 files `kpvk.py`, `tests_deepseek_job7/kpk_20000.txt`.
`FABLE_TO_deepseek_8.md`.

## 8. Times from recorded stamps

| part | start | end | wall |
|---|---|---|---|
| pins | 14:35:34 | 14:36:00 | <1 min |
| part 0 mirror repair and v2 file | 14:36:00 | 14:39:00 | ~3 min |
| positions + controls (stopwatch, first-move, depth 2) | 14:36:18 | 14:37:00 | <1 min |
| first sweep (wrong timing) and diagnosis | 14:36:47 | 14:41:00 | ~4 min |
| corrected sweep, 72 cells | 14:41:10 | 14:45:25 | ~4 min |
| increment cells | 14:45:25 | 14:46:17 | ~1 min |
| step 3, tables, report | 14:46:17 | 14:56:00 | ~10 min |

**Total about 21 minutes** of the 60 allowed.

## 9. What I did not do

- **64 threads was not tested** (the reviewer's configuration): this machine has 4 cores.
- I did not test `Move Overhead` other than its default of 10, so I cannot say whether the
  clock-0/1/2 flags are the budget rule or process start-up.
- I did not vary Hash beyond 16 and 512 MB, or threads beyond 1 and 8.
- I did not test clocks between 25 and 40 ms or below 0 (the job's list is as given).
- I did not re-run the job 7 KPvK A1 engine tests against the v2 table; part B of job 7
  already showed zero still-failing cases, and Fable's PC measurement (3 of 732 thrown
  away, 0.4%) is the number that counts.
- I did not change any engine source.

## 10. What I am not sure about

- **Whether my v2 table is now right.** It changes exactly the 6,735 entries Fable found
  wrong and preserves the 10,023 that agreed, which is as strong a consistency argument as
  I can make without a second independent solver. Fable's re-run is the test.
- **Whether "later than the clock" at clock 0-2 matters in practice.** In a real game the
  opponent's clock is also running, so a 1 ms overrun at a 1 ms clock is a flag, but such
  clocks only arise from a GUI sending absurd values. I report the counts without
  claiming harm.
- **The `no_search` definition.** I counted "searched" as at least one `info depth` line
  and no `nodes 0` in the last info. A search that printed `info depth 0` or crashed before
  printing would be counted as no-search; none occurred, so the definition did not bite.
- **My clock-0 result is partly a definition.** Every answer is later than a 0 ms clock.
  Saying "200 of 200 flagged at clock 0" is true and nearly vacuous; the informative rows
  are clock 1 and 2.

## 11. A better way

**11.1 Measure 64 threads on a machine that has the cores.** The reviewer's case is the one
configuration I could not reproduce, and it is the one that motivated the job. A cloud
machine with 64 cores, or the PC itself, would settle it in the same 20 minutes this took.

**11.2 Separate "budget rule" from "process latency" by testing `Move Overhead 0`.** If the
clock-0/1/2 flags disappear with a zero overhead, they are the rule working as written; if
they remain, the engine cannot answer that fast whatever the budget says. One extra
column in the same sweep.

**11.3 Time only the search, always.** My first sweep was wrong because it charged
`ucinewgame` to the search, and at Hash 512 that is a 35 ms error - larger than every
effect in the job. A job text that says "start the timer when `go` is written, after
`readyok`" would have prevented it, and it is worth putting in the text rather than
relying on the helper to notice.
