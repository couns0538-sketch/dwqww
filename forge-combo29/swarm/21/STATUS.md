## 2026-11-16T23:01:56Z (from `date -u`)
seat 21. Working **the PC's match path** (handoff file 6 items 3 and 4). **Threads 1 in every run**,
Hash 16, PC20 on the PC build.

**The node budget, fully characterised**
- **21-F16**: `go nodes N` never reaches N — mean −27.1 % / −28.0 % / −20.4 % at N=20k / 50k / 250k;
  worst **−51.9 %**; 0 of 30 pairs over budget; deterministic 30/30.
- **21-F17**: stops at the last COMPLETED depth; mean depth 10.1 / 11.9 / 12.8 / 15.4 / 17.2 at
  20k / 50k / 80k / 200k / 400k; effective budget a steady 72–80 % of N.
- **21-F18**: the undershoot does NOT change the move — same bestmove on 8/8 tactical positions and
  9/10 middlegame ones, over a ~7-ply depth gap. **Real, not urgent.**

**21-F15**: `go softnodes N` is deterministic (40/40) and stops at a depth boundary but OVERSHOOTS by
up to **+58.9 %** — the opposite direction from `go nodes`.

**21-C13**: the clock is safe at the end of a game — 60 simulated moves at 6s+0.06 give **0 forfeits**,
peak 42 % of remaining time, think time shrinking as the clock falls; 12 forced low clocks down to
`wtime 0` all answer legally within 37 ms.

**Withdrawn under file 6** (3 of my claims): 21-F9, 21-F13, 21-F11.

**Still standing, ranked below the PC path**: 21-F8 (`fullmove 0` refused), 21-F2 (refused FEN →
`readyok` → old board). **Unfinished**: job28 (15-F3 KNN v K), killed mid-run.

**Next**: `go softnodes 2000` under a full self-play game clock — the owner's self-play uses
softnodes alone, and I have only measured it cold. Then a determinism check of softnodes across
DIFFERENT move orders reaching the same position (transposition), which would show whether the TT
makes self-play results order-dependent.
