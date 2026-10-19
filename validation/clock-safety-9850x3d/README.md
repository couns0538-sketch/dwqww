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
whether any legal move existed. A regression and a narrowly scoped terminal
check will be validated separately from clock accounting and Elo.
