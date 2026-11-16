## 2026-11-16T22:29:58Z
seat 21, area 1 (FEN INPUT). **Threads 1 in every run.** Builds: base 6b98f217, PC r15.

**job21 done — no new fault, and two near-misses avoided**
- The PC patch's `go` handling answers AT ONCE (`a2a3`, 0 nodes) for `go depth`,
  `go wtime btime 50`, `go nodes abc`, `go movetime` — documented as intended by the patch
  ("when a limit was named but unusable ... the answer comes at once"). I first wrote three of
  those as predictions of failure; the predictions were wrong, not the engine.
- A bare `go` / `go banana` searches for ever on BOTH builds. I first recorded that as a hang;
  it is a legal infinite search. I nearly filed a REFUTES of seat 30's 30-F1 on it — withdrawn
  before filing, because 30-F1's claim needs a `stop` to test properly and I did not send one.
- The five new options exist only on the PC build and their ranges are enforced there
  (HistRework 4 / −1 → `invalid value`). **Warning for other seats**: sending PC20 to the BASE
  build yields five `unknown option` lines; stop on them.

**My area's state on the PC build**: 21-F9 repaired; 21-F8 and 21-F2 still open; 21-F10 confirmed
identical; 21-F11 withdrawn by me (mate 0 is correct).

**Next**: implement 30-F1 properly (go + stop, count bestmoves) since I now have the exact
question, and test `go wtime btime 50` with the parse instrumented.
