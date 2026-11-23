# The live searcher's start-up numbers on the PC (RE N2, Astra's hash control)

Measured by Fable on the PC, 23 November 2026, 03:19 (PC clock). One thread, under a second per search.
Tool: `fable_n2_live_pin.py.txt` beside this file. It sends the 24 lines of `loop/LOOP_OPTIONS.txt` (net path
filled in with `loop/forge65_r0067.fnn3`), then `setoption name Hash value H`, `isready`, `ucinewgame`, `isready`,
`position startpos`, `go depth 18`, and waits for `bestmove`. It stops on any refusal line and demands the
engine's own `NNUE v3 active` line.

Raw output:

```text
== runs/forge/engines/v3-r15dsg-sp-clang/forge.exe  sha256 cef2f21589102392   (the loop's program)
Hash 16: nodes 375880 hashfull 156 score cp 35 bestmove e2e4 (24 option lines sent, 0 refused)
Hash 32: nodes 375868 hashfull 78 score cp 35 bestmove e2e4 (24 option lines sent, 0 refused)
Hash 16: nodes 375880 hashfull 156 score cp 35 bestmove e2e4 (24 option lines sent, 0 refused)
== tmp/fable_scratch/forge65/exe_p2/forge.exe  sha256 9ba55d4669acb64b       (the published program of this branch)
Hash 16: nodes 375880 hashfull 156 score cp 35 bestmove e2e4 (24 option lines sent, 0 refused)
Hash 32: nodes 375868 hashfull 78 score cp 35 bestmove e2e4 (24 option lines sent, 0 refused)
Hash 16: nodes 375880 hashfull 156 score cp 35 bestmove e2e4 (24 option lines sent, 0 refused)
```

These are the numbers Astra and Neon measured on their two Linux builds, so the
pin holds on four programs (two Windows, two Linux): **Hash 16: nodes 375880, hashfull 156. Hash 32: nodes 375868,
hashfull 78.** `bench 13` gives 616966 under both and cannot tell them apart.

Not measured here: a wrong `Threads` value (with more than one thread node counts are not repeatable, so the pin
would very likely miss 375880, but that is an expectation, not a test).
