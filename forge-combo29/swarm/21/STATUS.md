## 2026-11-16T22:58:02Z (from `date -u`)
seat 21. Now working **the PC's match path** (handoff file 6 items 3 and 4). **Threads 1 in every
run**, Hash 16, PC20 on the PC build unless stated.

**The story on the node budget, complete**
- **21-F16**: `go nodes N` never reaches N — mean −27.1 % at N=20000, −28.0 % at 50000, −20.4 % at
  250000; worst **−51.9 %**; 0 of 30 pairs over budget; fully deterministic (30/30).
- **21-F17**: it stops at the last COMPLETED depth, and that costs depth — mean 10.1 / 11.9 / 12.8 /
  15.4 / 17.2 plies at 20k / 50k / 80k / 200k / 400k nodes, effective budget a steady 72–80 % of N.
- **21-F18 (settles it)**: the undershoot does NOT change the move. 8 tactical positions: same
  bestmove at 20k and 400k on all 8; with job32's 9-of-10 that is **1 change in 18 positions** over
  a ~7-ply gap. **So 21-F16 is real but not urgent** — the owner gets a shallower search than asked
  for, and the same move.

**Also new this session**: 21-F15 (`go softnodes N` deterministic, depth-boundary stop, but
OVERSHOOTS by up to +58.9 % — the opposite direction from `go nodes`). **21-C12** the 6 s clock path
is healthy (slowest 599.5 ms of 30 searches, all moves legal).

**Withdrawn under file 6** (3 of my claims): 21-F9, 21-F13, 21-F11 — each caught by a rule I had not
applied before, all recorded with the measurement that refuted them.

**Still standing, ranked below the PC path**: 21-F8 (`fullmove 0` refused), 21-F2 (refused FEN →
`readyok` → old board).

**Unfinished**: job28 (seat 15's 15-F3, KNN v K) — killed mid-run, no output.

**Next**: the clock path under stress — `movestogo`, the last moves of a 6s+0.06 game, and whether
the engine leaves enough time to answer (an overrun in the last moves would be a real match defect).
