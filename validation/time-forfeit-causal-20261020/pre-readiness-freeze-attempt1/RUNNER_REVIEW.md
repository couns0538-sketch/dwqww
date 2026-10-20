# Causal diagnostic runner review

Read-only review before the one authorized cold/warm diagnostic. No engine,
compiler, diagnostic, match, Git mutation or network request ran during this
review. Only this review file was written. This is a review of preparation,
not evidence that the original hosted forfeit has been explained.

## Findings to resolve before execution

1. **Cleanup follows the leader, rather than its owned process group.**
   `run_diagnostic.py:98-116` signals the group only when `proc.poll()` says the
   leader remains alive. A leader that exits while a descendant retains a pipe
   skips both signals. Joining readers then reports incomplete capture, but the
   owned descendant remains running. In addition, `finished=True` is set before
   cleanup: if cleanup itself raises, the exception handler's second `close()`
   cannot finish it. Perform group cleanup/checking independently of leader
   state and mark completion after resources are finalized. Retain incomplete
   capture as a failure. An exited-leader/live-descendant control is the useful
   contract test; normal Forge's threads do not themselves create descendants.

2. **A causal input is missing from the final hash comparison.**
   `ORIGINAL` (`forfeit-exchange.json`) supplies the cold FEN, final `go`, and
   original-session expected SHA at line177 and later. `frozen_inputs()` records
   the original stdin and session, but omits this JSON. Add its own SHA to both
   the preregistered inputs and the before/after map. Otherwise an accidental
   change to an actual case-selection input is not detected by final rehash.

The parent separately identified the instrumentation insertion in the
restricted-root block, before `nodes`, `depth` and `elapsed` exist. That compile
issue is outside these two runner findings and must be repaired and recorded
before the source/build manifest is frozen.

## Contracts that look sound on inspection

- The original stdin is hash-bound, must contain260commands/50go requests, and
  is sent in its saved order. The seven-command setup includes `ucinewgame` and
  `isready`. The runner waits for UCI/readiness/bestmove responses, rather than
  immediately sending the historical stop/quit commands into active searches.
- Each requested board is legally reconstructed and each emitted bestmove is
  checked against that board. Subsequent positions remain original even after
  a diagnostic move divergence, which is explicitly recorded. This preserves
  requested inputs without claiming identical warm TT/history contents.
- A separate raw stdout/stderr capture retains exact bytes. Manager `os.read`,
  decoded-line and consumer-dequeue events distinguish observed pipe output
  from Python queue/consumer delay. Write timestamps bracket the actual pipe
  write before the event-log writes occur.
- The engine telemetry uses a separate append-only sink with event IDs;
  short/failed writes abort rather than silently drop data. Contiguous IDs,
  mandatory per-search phases, reader joins, exit code and empty stderr are
  checked. Atomically allocated IDs need not be file-order chronological across
  threads; the runner correctly sorts IDs for its completeness check.
- Root clearance is bound to the protocol hash; execution refuses an existing
  output directory and checks known competing process names. This process-name
  scan is supplementary: it does not identify every possible CPU/I/O consumer,
  so root's explicit quiet-state clearance remains required.
- A56-second active deadline plus bounded cleanup is intended to fit the
  global60-second guard. All ordinary waiting paths use the shared deadline.
  Missing phases, malformed output or a deadline remain failed/incomplete, not
  successful timing evidence.

## Interpretation limits

The diagnostic clocks are sequential samples, not simultaneous wall/CPU
measurements. Thread CPU differences are meaningful only within the same
pid/tid; UCI receipt and Worker entry occur on different threads. A large
wall-minus-CPU interval may include blocking, I/O or scheduling and does not
uniquely prove host preemption. Previous-write metrics include instrumentation
formatting/clock work as well as the syscall, and the final event's own cost has
no later event to report it. Account for this observer effect in analysis.

No new local reproduction can establish what happened inside the original
hosted process. Failure to observe a stall does not explain or invalidate its
108.696ms end-to-end response against63ms remaining. These fixed historical
clock inputs create diagnostics, not newly maintained tournament clocks, new
games, performance measurements or Elo evidence.

## Reviewed input identities

| File | SHA256 |
| --- | --- |
| run_diagnostic.py | `54365b0f88aec15e743393e50d0610e431dc768b8593c2696751ce4cdf20360b` |
| time_diagnostic.hpp | `44212eab699acb5740ef10bdcb1c2294e1ba67afc0e6e7418f8b4558d8726f1b` |
| instrumentation.patch | `d74884a4fae363896b5986574fe7ea200c6ba4cf7ceb21a6c3423c90d85793e6` |
| DESIGN_REVIEW.md | `a8942b8408ba0203c1b003d3151ae4fc09eb0669b9c0c557c1254b5bb3691380` |

These identify the reviewed pre-fix files. Follow-up fixes need their own final
hashes and contract-test evidence; this review does not label them executed.

## Implemented follow-up and bounded fixture evidence

The diagnostic runner now checks its owned process group independently of the
leader state. It sends TERM, escalates to KILL for remaining live members, waits
for the leader, joins readers and closes captured streams before marking the
capture finished. Dead zombies are excluded from the live-group check. An early
cleanup exception leaves the object eligible for a real retry. Remaining waits
and joins share a cleanup deadline capped at active-deadline+4seconds and
close-entry+3seconds; this is intended to fit56active+4cleanup, not a guarantee
against arbitrary host suspension.

`cleanup-regression-attempt1/` preserves real process-group fixtures. One has a
leader that exits while its child ignores TERM and retains the capture pipes.
The other injects only an early leader-wait exception, then uses real signals,
pipes and readers for retry and idempotence. The unchanged two-test contract
fails the original runner with exactly two assertion failures and passes the
corrected runner with both tests passing. Test cleanup independently killed
and drained fixtures even for RED; final live-member scans found none. The
initial relative-path fixture-launch error is retained as invalid harness
evidence and is not counted as RED. No chess engine or causal diagnostic ran.

The shared before/after frozen-input helper now includes the original
`forfeit-exchange.json` SHA. Per-search postcapture checks also require all four
info-output phase counts to agree with actual consumed/raw depth lines, and
balanced timer-poll phases restricted to the target search. These checks are
implemented and syntax-checked; their actual engine-data exercise remains the
later authorized diagnostic's responsibility.

Corrected runner SHA256:
`c8101d5f551be0cdab194b506692c7805952cf70844b572b39ca7d259a25a7ea`.
Cleanup test SHA256:
`29e9616fc0a37eb6b5d11b28db26d884d74cc3b8ea3fd6bfe3238bdf6cde5681`.
Exact commands, return codes, raw outputs, fixture captures and file hashes are
retained in cleanup-regression-attempt1/RESULTS.json and its SHA256.json. The
earlier reviewed hashes above remain historical and unchanged.
