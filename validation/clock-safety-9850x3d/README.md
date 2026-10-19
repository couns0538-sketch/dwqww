# Forge clock and terminal-search investigation

This branch continues the AVX2 candidate at `5a3a28d2ddbe05691d3a0df85ece5f9a15300275`.
No playing-strength gain or win over full-strength Stockfish has been established.

## Reproduced clock failure

`diagnostics/repro-forge-2` freezes a ten-game diagnostic at 10+0.1,
Threads=1, Hash=32 MiB, OwnBook=false, Move Overhead=100 ms,
concurrency=1, CPU 2. Both engines ran through a timestamping UCI proxy.
Fastchess trace logging was deferred (`realtime=false`). This is diagnostic
evidence, not an Elo experiment: the proxy adds overhead and the run stopped
on a timeout in game 3, after only one complete pair.

The last request in `diagnostics/uci-24182.jsonl` was
`go wtime 465 btime 242 winc 100 binc 100`. Candidate Black replied
`bestmove e7d7` after **270.292 ms** as observed at the proxy. Child CPU
usage increased by five ticks (50 ms at the recorded 100 Hz resolution).
The first depth report, with internal `time 0`, reached the proxy after
199.543 ms. The second reported `time 188` for 24 nodes. Fastchess charged
264 ms and reported a 22 ms forfeit. Different observation boundaries
account for the two wall-time measurements; neither is an engine CPU time.

This establishes substantial latency outside useful search in this attempt.
It does not separate thread dispatch, descheduling, output transport, and
proxy scheduling precisely. A final `info time` also excludes later search
in an unfinished iteration, so a large gap after that report alone does not
prove output blocking. The cgroup resource counters and raw communications
are preserved. Archived earlier forfeits did not retain exact failed plies
and cannot be attributed retrospectively.

Source inspection independently confirms a late clock epoch: the old worker
starts its timer after UCI parsing, board copies, and thread dispatch.
Charging those costs from receipt of `go` is a bounded accounting correction;
it cannot guarantee a deadline if the operating system pauses the process.

## Other diagnostics

`repro-forge-1` completed one game normally (a fifty-move draw, 109 Black
moves). That successful trace does not clear the repeated timeout history.
`repro-stockfish-1` failed because its logging arguments were invalid;
`repro-stockfish-2` timed out during Stockfish startup before Forge launched.
Stockfish prints its banner before substantial initialization. Neither
startup failure is strength evidence. All attempts are retained.

## Confirmed search defect

Before the search correction, the existing candidate returned:

```text
position fen 7k/8/5KQ1/8/8/8/8/8 w - - 0 1
go depth 1 searchmoves g6f7
info depth 1 seldepth 1 score cp 930 nodes 2 ... pv g6f7
bestmove g6f7
```

`g6f7` leaves Black stalemated. Its score must be zero. Non-check
quiescence nodes previously reached stand-pat evaluation without checking
whether any legal move existed. Positive-depth pruning could likewise skip
terminal detection. The shared draw check now identifies stalemate before
either path reaches cached scores or pruning.

## Validated 6.4.1 candidate

- Clock source checkpoint: `9cf37933596c6777870ef6aac626f7e766255f51`.
- Candidate source: `fab979c`; unchanged evaluation weights and AVX2 arithmetic.
- Clock tests: seven expected failures before the fix, passing afterward.
- Stalemate tests: nine expected failures before the fix, passing afterward.
  They cover depth-one search, opposite null windows, positive-depth pruning,
  seeded nonzero TT entries, quiet legal positions, and checkmate.
- All four Linux CTest suites passed. Windows core, UCI and ponder checks
  passed under Wine 10. No native Windows or physical Ryzen test was performed.
- Direct UCI checks against old/new Linux and Windows executables reproduce
  **+930 cp before, 0 cp after** on the stalemate fixture.
- Final Linux and Windows binaries pass the AVX2 instruction check without
  fused arithmetic. `bench 11` records 417491 Linux nodes and 350867 Windows
  nodes. The old Windows candidate had 343022 nodes; this behavioral search
  correction need not preserve the old tree.
- Seven counterbalanced repetitions retained under `search-unoptimized/`
  and `search-cpu/` show substantial shared-VM variation. Even identical perft
  code varies widely. CPU-time medians do not establish a stable engine speedup
  or regression; no physical Ryzen speed claim follows. The CPU driver is
  included with its raw CSVs. No speculative board optimization was added.
- Fixed-node A/A calibration passed four color-swapped pairs, with identical
  move sequences within each pair and all eight normal terminations.

The Windows ZIP is `releases/forge-6.4.1-candidate-windows-zen5.zip`.
Its exact checksums are in `artifact.json`. The delivered executable matches
the runtime-tested build byte-for-byte. This is a correctness candidate;
it is not an accepted Elo release.

## Paired clock pilot

`run-pilot.py` registers eight fresh opening pairs at 10+0.1, Threads=1,
Hash=32 MiB, OwnBook=false, Move Overhead=100 ms, concurrency=1. It uses
the clock-corrected reference `9cf3793`, so both engines charge dispatch time.
Both native engines inherit the permitted CPU set instead of sharing one
explicitly pinned CPU. Owned builds, benchmarks and Wine jobs are stopped
before play. Deferred UCI tracing retains failed positions and clocks.

The pilot requires all sixteen games to terminate normally, complete unique
color-swapped pairs, matching independent/native pentanomial counts, and
unchanged inputs. Any forfeit or interrupted pair invalidates the attempt.
It is an infrastructure pilot, not a superiority test or accepted SPRT.

The 100 ms-reserve pilot failed in game 4 at Black's 59th move, with 308 ms
remaining. It is invalidated in full. The final position, exact history and
clocks are in `diagnostics/timed-pilot-failure-forensics.json`.

## Scheduling isolation and buffered pilot

A direct replay bypassed Fastchess and tested that final position 100 times
per engine. One candidate response took 594.184 ms. Linux task scheduling
counters recorded approximately 121.705 ms of CPU runtime and **465.623 ms
of runnable-queue wait** in the search thread. That is concrete scheduling
starvation in this reproduction; it does not attribute every archived
forfeit. Neither a longer internal search nor the old `info time` alone
would establish this finding.

All 200 trials, thread states, scheduling counters, outputs, protocol and
diagnostic code are retained in `diagnostics/deadline-probe.zip` and adjacent
files. Proc-file samples are not atomic: their timestamp precedes several
reads and those reads can themselves be delayed. Interpret cumulative
counter deltas and complete response times, rather than treating those
timestamps as precise endpoints. These are diagnostics, not games or a
relative reliability comparison between builds.

`run-buffered-pilot.py` registers a separate eight-pair pilot using the same
10+0.1 clocks and a symmetric **1000 ms Move Overhead**. This follows the
measured 465.6 ms scheduling stall. It selects fresh openings and preserves
its own protocol, hashes and results. The earlier failed pilot contributes
no data. The large reserve is a shared-VM test setting, not a measured
optimal setting for a native Ryzen computer.


The buffered pilot also failed: after four normal games the reference
forfeited game 5 by 450 ms. Its final request had 4290 ms remaining and
the response arrived roughly 5.3 seconds after the logged request. The
last completed iteration's 260 ms report excludes the unfinished search.
The entire pilot is invalid; its four completed games contribute no Elo
information. Increasing the reserve again is not a defensible strength test.

## Preregistered fixed-node search-quality comparison

The next protocol compares the current candidate with the **exact original
user-supplied 6.4 ZIP**, not the clock-only reference. `original-baseline/`
records archive CRC validation, the 52 extracted files and their hashes,
matching compiler flags, build logs, all four passing CTest suites, and
UCI smoke checks. The archive SHA256 is
`98d2ff2c523a25931897794bad3c39d40398799b8907d51596dad3e326a2ba9d`.
The Linux baseline binary SHA256 is
`025e836782af559a620ce78dc1a8a66bb2c49ae798f3f7c320175494d9a060e0`.
The production code comparison against the later `9108d01` reference
isolates the known transposition-table tag correction; evaluation and
network data are unchanged.

`run-quality-sprt.py` freezes 10,000 nodes per move, unlimited wall clock,
Threads=1, Hash=32 MiB, OwnBook=false, fresh color-swapped openings and
restarted processes. First run four original-vs-original A/A pairs. If
that passes, run one native Fastchess paired SPRT: H0=0, H1=+20,
alpha=beta=0.05, logistic model, maximum 500 pairs. SPRT uses concurrency=1
because this Fastchess version can abort another pair's return game at an
early boundary with concurrent play. No adjudication or pooling is used.
A cap without native acceptance is inconclusive. H1 acceptance does not
prove the improvement is at least 20 Elo. A/A retains full tracing;
the larger node-only test retains warnings, full PGNs and console statistics.

This measures **search quality at 10,000 nodes per move against original
Forge 6.4**. It cannot establish equal-clock, Windows or Ryzen Elo, isolate
which code change helped, or demonstrate superiority to Stockfish. Clock
failures and earlier A/A games contribute no outcomes. The frozen protocol,
inputs, complete paired normal terminations, independent pentanomial audit
and explicit native acceptance are all required before any quality claim.


Calibration outcome: `matches/quality-aa/` finished all eight games normally
but failed its strict opening audit because Fastchess normalized an unusable
EP target from `a6` to `-`. Its outcomes are excluded. The exact old runner
and diagnosis are retained there. Before A/B play, the protocol was narrowed
to **unchanged original corpus entries whose EP field is `-`**; legal EP
rights are never silently removed. The corrected audit requires the exact
scheduled opening prefix. A separate fresh `matches/quality-aa-v2/` passed:
four deterministic color-swapped pairs, eight normal games, native and
independent pentanomial `[0, 0, 4, 0, 0]`, unchanged hashes. An independent
review also found and fixed final-LLR parsing: a final nonfinite value must
be rejected even if an earlier finite value exists. Audit fixtures are
recorded under `tests/quality-runner-audit-checks.json`.
