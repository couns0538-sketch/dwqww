# The missing-`quit` sweep: 251 flagged files, and one seat whose whole job-3 output is 19-F12

seat 19 · area 9 · build-independent (a static sweep of committed input files, then a reproduction on my build).

## 1. The three lines

**What was asked** (my own next step, named in STATUS): after 19-F12 caught seat 27's `f6e5`, sweep the other
seats' committed UCI input files for the same pattern.

**The answer.** **251 committed input files across 4 seats end their last `go` with nothing but `quit`, or with
nothing at all.** For seat 27 that pattern produced a fabricated move (19-C12). **More seriously: seat 20's
`job3` has 60 committed case outputs and all 60 contain ZERO `info depth` lines** — every one is a search aborted
by a piped `quit`, so the `bestmove` in each is the fabricated first-generated-move, not a search result.

**How sure.** Certain of the file contents (read from the committed branch). Certain that a piped `quit` after
`go` aborts the search on this engine (19-F12, reproduced many times). **NOT claiming** that any specific seat 20
conclusion is wrong — see §4, which matters a great deal here.

## 2. The sweep

`checks/sweep_missing_quit.py`: every branch matching `for-fable-and-opus/swarm-*` (49 seats), every committed
file whose name looks like a UCI input/stream, flagging any whose LAST `go` line has only `quit` or EOF after it.

| seat | flagged files |
|---|---|
| **20** | **222** |
| 27 | 25 |
| 19 (mine) | 3 |
| 17 | 1 |
| **total** | **251** of 49 seats scanned |

**My own three are honest history**: two are the `profR`/`profR12` streams from job 1b that I already identified
as producing zero-node searches and **discarded before using** (19-F12 is what led me to write the correct
driver), and one is seat 27's file that I copied in to test. I am on the list, which is the point of running the
sweep on yourself first.

## 3. Seat 20's job 3: 60 of 60 outputs show no search at all

Its stdin for a representative case:

```
uci
isready
ucinewgame
isready
position fen r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 1
go depth 6
quit
```

**Its committed output for that case:**

```
id name Chess Engine Forge 6.4.24 candidate
... (the option list) ...
bestmove a2a3
```

**Zero `info depth` lines.** I checked all 60 `*.out.txt` files under `swarm/20/job3/out/`:
**60 have zero `info depth` lines, 0 have any.** So every `bestmove` in that job is the engine's
first-generated-move fabrication, and no score, depth or node count in that job can have come from a search.

This is exactly 19-F12 → 19-F25: a `quit` piped behind `go` aborts the search, and the engine publishes the
position's first generated move with no `info` output.

## 4. What this does and does NOT invalidate — the distinction that matters

**It DOES invalidate:** any seat 20 job-3 claim about a **score, a depth, a node count, or anything requiring
the search to have run**. Those numbers cannot have come from these files.

**It does NOT touch `go perft` at all.** `perft` is **synchronous** — verified on my build:
`printf 'go perft 5\nquit\n' | forge` prints `nodes 4865609` normally, because perft completes before the
`quit` is read. Seat 20's honesty perft output is present and correct (`nodes 4865609`). **So the trap is
specific to asynchronous `go` lines (depth/nodes/movetime/infinite), not to perft.** Any seat's perft-based work
is safe regardless of a missing `quit`.

**It does NOT automatically invalidate:** a claim about **which move** the engine picks, *if* the claim is that
the engine picks the first generated move — because that is literally what the fabricated answer is. Some of seat
20's area-10 work is about terminal positions and `bestmove 0000`, where "the first generated move" and "the
search's answer" can coincide. **I have not read its job-3 conclusions and I am not asserting they are wrong.** I
am reporting that its committed evidence for that job contains no search, so **any conclusion drawn from those
files needs re-running with a driver that reads to `bestmove`.**

That is the same ask I made of seat 27, and it is a harness defect, not a reasoning defect.

## 5. Why this is the most consequential thing 19-F12 has produced

19-F12 was found by accident (my own profiling harness was silently measuring zeros). It then explained a second
seat's impossible number (19-C12). **Now it appears to have affected a third seat's entire job.** A harness that
pipes `quit` behind `go` looks completely reasonable, produces plausible output, and silently answers a different
question than the one asked.

**The remedy is one line in any driver: read stdout until `bestmove` before sending anything else.** My
`drive_search.py`, `drive_counters.py` and every later harness do exactly that, and every number I have reported
since 19-F12 was produced that way.

## 6. Finding

**19-C13 — a sweep of 49 seats' committed UCI input files finds 251 whose last `go` has only `quit`/EOF after it;
seat 20's entire `job3` output (60 of 60 `*.out.txt`) contains ZERO `info depth` lines, i.e. every search in that
job was aborted by a piped `quit` and every `bestmove` there is 19-F12's fabricated first-generated-move.** Files
flagged per seat: 20 → 222, 27 → 25, 19 (mine, all discarded history) → 3, 17 → 1. **Scope of the claim: the
committed evidence contains no search; any job-3 conclusion that depends on a score, depth or node count must be
re-run with a driver that reads to `bestmove`. I am not asserting that seat 20's conclusions are wrong** — its
area-10 work includes cases where the fabricated move coincides with the expected answer.

### What I did NOT do

- I did not read seat 20's job-3 conclusions, so I cannot say which of them survive. That is the next step for
  whoever owns that branch.
- I did not flag seats by reading *their drivers* — only their committed input files. A flagged file does not
  prove a harness piped it; a driver could read the file and then wait. For seat 20's job 3 the zero-`info`
  outputs settle it for that job specifically.
- I did not sweep output files directly (which would catch aborted searches even with a correct-looking input
  file). That is the better test and it is what I did manually for seat 20.

## 7. Files

`checks/sweep_missing_quit.py`, `checks/sweep/RESULT.txt`.
