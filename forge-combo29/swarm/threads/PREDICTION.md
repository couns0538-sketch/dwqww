# Predictions, committed before the measuring runs

Written before `determinism.py`, `pins_by_threads.py` and the wall-time run.
Each prediction has the range that kills it. Never edited afterwards.

## P1 — `go depth N` determinism at Threads > 1

Prediction: at Threads 2, 4 and 8, **every one of 40 positions differs in node count
across 3 repeats** (40/40 differ), and **at least 30 of 40 also differ in score**.
Bestmove differs on **at least 3 of 40** at Threads 8.

Killed if: fewer than 30/40 differ in node count at Threads 4, or fewer than 2/40
differ in bestmove at Threads 8. That would mean the search is far more stable than
a work-stealing SMP search of this design usually is.

## P2 — `go depth N` determinism at Threads 1

Prediction: **0 of 40** differ in nodes, score or bestmove, on 3 repeats each.

Killed if: any single position differs. This is the inherited claim's one half that
the audit already believes; a failure here would mean even the Threads-1 baseline is
not reproducible and every number in the report is suspect.

## P3 — the nodes/score/bestmove ordering

Prediction: **bestmove is far more stable than the score**. Specifically, at Threads
4 I expect the score to differ on more positions than the bestmove does, by at least
a factor of 3.

Killed if: bestmove differs on more positions than score does. That would suggest the
instability is in move selection rather than in leaf evaluation.

## P4 — drawn-root bail under threading

Prediction: the bail still fires at Threads 2/4/8 — the root-drawn branch is taken
**before** any helper is spawned and returns `nodes 0` with `pv` empty — so a drawn
root returns the same score (cp 0) and the same move on **40/40** repeats at every
thread count.

Killed if: any drawn root at Threads > 1 reports a nonzero node count or a
nonempty pv.

## P5 — book behaviour

Prediction: book moves are decided in the UCI loop **before** the searcher is called,
so `Threads` cannot change whether the book fires or what it returns. Expect
**0 of N** differences between Threads 1 and Threads 8 on `go wtime` book positions.

Killed if: any book position answers differently at Threads 8, or fails to book.

## P6 — the four honesty pins

Prediction: `bench 11/13/16` are **bit-identical at every thread count** (because
bench builds its own `Searcher(16)` and never reads the Threads option), and
`perft 5` likewise (single-threaded UCI path). All four reproducible on 3 repeats
at Threads 1/2/4/8.

Killed if: any bench value moves with Threads, or fails to reproduce on a repeat.
If a threaded bench value differs, the pins are NOT a Threads-N identity and every
Threads-N row must say so.

## P7 — wall-time scaling on 4 cores

Prediction: Threads 4 wall time is **1.5x–3.0x faster** than Threads 1 on depth-13
searches of real positions (median over 20 positions).

Killed if: Threads 4 is slower than Threads 1, or faster by more than 3.5x (which
would mean the Threads-1 baseline was not using the machine).

Threads 8 is reported but not predicted as faster: **the box has 4 cores**, so 8
threads is 2x oversubscribed and may be slower than Threads 4.
