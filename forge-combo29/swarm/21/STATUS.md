## 2026-11-16T22:42:20Z (from `date -u`)
seat 21, area 1 → new area: **`go softnodes` / the PC's self-play path**. Threads 1 in every run.

**Withdrawn this session under handoff file 6** (three claims of mine, each caught by a rule I had
not applied before): **21-F9** (counter-100 `cp 0` is CORRECT — the mate lands at half-move 101;
and in the window where the rule bites, counters 98/99, the base build already finds the mate),
**21-F13** (a node-count shape, not a defect), **21-F11** (`mate 0` is correct UCI).
`job29/out/summary.md` prints the inequality per case.

**NEW: 21-F15 — `go softnodes N` on the PC build under PC20, Threads 1** (file 6's new area):
- **deterministic**: 40/40 (position × N) combinations bit-identical across 5 fresh processes each;
- **stops at a depth boundary**: the reported node count is the last `info depth` line's cumulative
  count and no separate total follows (verified in the raw file);
- **overshoots N by a whole iteration**: +671 at N=2000 (+33.6 %), +11,779 at N=20000 (**+58.9 %**),
  +2,904 at N=50000 (+5.8 %), +38,912 at N=250000 (+15.6 %);
- base and PC builds agree on every (position, N) pair.
This matters for the owner's self-play: a "2000-node" search is really ~2,700 nodes.

**Still standing, low priority per file 6** (UCI edge cases come after the PC path): 21-F8
(`fullmove 0` refused) and 21-F2 (refused FEN → `readyok` → old board). Both on the PC build.

**Next**: the rest of the self-play path — `go nodes` 20000/50000/250000 and the clock 6s + 0.06
on real-game positions, checking for a wrong move or a wrong score, which is what file 6 says
counts most. `job28` (seat 15's 15-F3, KNN v K) is UNFINISHED — it produced no output.
Next command: `cd forge-combo29/swarm/21 && python3 job31/nodes_clock.py job31/out`
