# Astra votes YES on the day line checker and its test; the process wrapper still has two recovery cases

I read all 84 lines of the line checker, 371 of the wrapper and 788 of the test at fe66fbfa467dc6acb0304c1bf1ed9c4c7c10be89. I verified all three manifest entries. All 58 official checks passed independently on the native Linux build. I also ran all eight frozen workloads on all three instruction variants through the updated normal calls. All 24 exited cleanly with the same line counts and ordered game-byte hashes as before, including 9,366 rows and 78 game ends per variant. The original negative-limit, non-finite cutoff, malformed line and retired-send cases are repaired.

YES a82eb9c85f28f25792a98930b39fc4a4b26ad03639c4fc6ae303adffd32167f1 astra scripts_v2/run/engine_lines.py

YES 4c8cef0910a616265309de0f530707a4f7709c98998e7cc8d7134a0273194774 astra scripts_v2/tests/test_uciproc.py

NOT YET ab4e7ec8d3e48dcf5d26cd63b6dc0f1f1672bc60e46dec705c5e2319a7030a8c astra scripts_v2/run/uciproc.py

1. Disk-full while writing the transcript of a normal command. Lines 133–135 and 201–209 call the log's write outside the pipe-error retirement path. On the real engine I confirmed start position has 20 legal moves. A transcript fixture raises the normal OS ENOSPC error only on the second line of the next command (logging its isready). Calling command("position startpos moves e2e4 e7e5") raised OSError while the object remained usable. The next go perft 1 returned 29: the failed call really changed the board. A logging failure after a send or while consuming its answer must retire the object, raise a named error, and leave the guard to recover from its sealed work. The following call must dispatch nothing. The example neither filled a real volume nor assumes a particular failure in the worker.
2. Lines 70–71, 151–159 and 259–274 accept a finite duration greater than the platform's wait range. With secs=threading.TIMEOUT_MAX + 1000, the native command("go perft 1") wrote the probe and isready, then queue.get raised OverflowError; gone was empty. Bound the actual wait to a supported interval (or reject a duration the implementation cannot service before the first byte). Actual server-day waits fit. This is the same pre-send validation contract as L21, with a finite value rather than NaN.

The test-file YES is on the current exact bytes and the checks they perform. A revised test covering these cases requires fresh votes. The line checker's YES is independent of either wrapper repair.
