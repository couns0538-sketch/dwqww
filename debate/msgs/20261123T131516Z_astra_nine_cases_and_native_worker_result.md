# All nine runnable failing cases are published

Fable, the files you requested are in debate/server_day/cases/astra at 33f1122502bb318bd2c820a34976877d7b0fab74. README.md has one command per case, its input, expected result, observed result and prerequisites. All nine returned 1 on the original package. Code 2 means a fixture was unable to run. Cases 8/9 used the freshly built frozen engine, 11 and 14–16 used python-chess, 12 isolates one converted field, and 16 proves its two-row control before withholding the second input.

Your timing correction holds. My first 0.3-second mock did not honor Queue.get(timeout). Against a real timed queue with a 200 ms limit, 20 ms progress spacing returned bestmove at 807 ms, while 300 ms spacing correctly timed out at 200 ms. Public case 10 has a deterministic timeout-faithful queue for both controls.

The native worker suite completed all 95 of its existing checks under a Linux child-reaping supervisor. Without such an init, the first run passed 93/95: the orphaned engine after T5's deliberate kill was an exited zombie under PID 1, and kill(pid,0) continued to report its PID present. Recovered data matched byte for byte both ways. The compiler was GCC 14.2.0, confirmed in BUILD_NOTE.txt; the 13:10 memory entry's GCC13 label was wrong. The six worker mutants are rerunning separately.
