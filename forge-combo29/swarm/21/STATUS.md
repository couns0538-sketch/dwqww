## 2026-11-16T22:31:00Z
seat 21, area 1 (FEN INPUT). **Threads 1 in every run.** Builds: base 6b98f217, PC r15.

**21-C7: CONFIRMS 30-F1 on both builds.** Seven `go` forms including four malformed ones each
give exactly one legal bestmove after `stop`, 0–4 ms after it, on the PC build and the base
build. My job21 "hang" observation was a harness error: a bare `go` is a legal infinite search.
The near-miss REFUTES was never filed; job22 is the right experiment. `job22/out/summary.md`.
(Note: my first latency figure was the read-window length, not the stop latency — corrected, and
the wrong numbers stay in the git history of the folder.)

**Area-1 state on the PC build**: 21-F9 repaired; 21-F8 and 21-F2 still open; 21-F10 confirmed
identical; 21-F11 withdrawn by me.

**Next**: run the area-1 job 1 mutation sweep on the PC build with the six FORGE_FIX switches'
neighbouring paths in mind, plus the `position fen ... moves` form across both builds (job16
found the form works; confirm on the PC build).
