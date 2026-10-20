# Baseline time-forfeit causal replay

One preregistered cold→warm diagnostic completed in3.856seconds after compiler,
engine and archive work ended. This is not a match: historical clocks and all260
original baseline commands were fixed diagnostic inputs; no PGN was reconstructed.
Both captures completed, all51bestmoves were legal, owned process groups/readers
were cleaned up, and all frozen source/binary/protocol/input hashes stayed equal.

| Final-position case | Go to observed bestmove | Reported result | Bestmove |
|---|---:|---:|---|
| Cold |24.888ms|24ms|f7e7|
| Warm, search50|32.140ms|31ms|e6f6|

Both final requests had63ms remaining and the original31ms hard budget. The
hosted forfeit took108.696ms. Its stall did not recur in this single local run.
Cold and warm final moves differ from the original e6e1;10of50warm choices
changed. The next original positions were forced as preregistered. This proves
neither identical internal TT/history state nor an explanation of the hosted
failure. Different host, timed search work and telemetry can affect the path.

The final warm worker interval was31.893ms wall /30.205ms threadCPU. Its output
flush bracket was1.021ms wall /0.022ms threadCPU; controller observation can
precede the post-flush event when pipe bytes are already readable. Wall-minus-CPU
is non-CPU elapsed time, not uniquely proof of preemption. Full timestamps,
same-thread comparisons, polls and raw byte capture remain in phase-analysis.json
and the original event logs. No local phase value is projected onto the hosted
run, and its last completed info24ms remains insufficient to locate that stall.

The diagnostic engine is built from frozen6.4.11 c5cbf97 with telemetry only.
Source-v2 corrected a misplaced observer event caught by syntax checking; original
RED remains. Independent runner checks repaired owned-group cleanup after leader
exit and preregistered input binding, with all original failing tests retained.
READY and PROTOCOL bind the source/core/engine and original exchange before this
single execution. There was no retry, filtering, changed tolerance or new game.

Decision: preserve the negative reproduction and original failure. The hosted
forfeit cause remains unresolved. No stronger-play, NPS, clock reliability,
native Ryzen or Stockfish conclusion is accepted. Further timed matches require
a fresh justified protocol and operational conditions; never rescue the invalid
TT run or pool this diagnostic with its games.
