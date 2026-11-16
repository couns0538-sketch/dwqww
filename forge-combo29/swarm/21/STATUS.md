## 2026-11-16T22:32:41Z (from `date -u`)
seat 21, area 1 (FEN input / protocol edges). **Threads 1 in every run.** Builds: base 6b98f217 and
PC r15 — both built Release and ASan+UBSan; the PC Release build was verified against file 5's
three honesty rows (default / S14 / PC20 all exact).

**Findings since the CONTINUE block** (full list in FINDINGS.md, each line names build + settings)
- **21-F14 NEW** — wide (multi-character) FEN corruption gives ZERO accepted-invalid FENs on
  either build; rank transposition is the only large accept (1,407 of 1,448). Sharpens 21-F3.
- **21-F13 NEW** — on the PC build the halfmove counter still changes how much is searched
  (293 nodes at 100, 155 at 150+), though the mate is found at every counter >= 100.
- **21-F12 NEW** — the PC build's drawn-root repair reaches `searchmoves` (8 nodes at hm100 vs 0
  on the base build).
- **21-C7 CONFIRMS 30-F1** on both builds (seven `go` forms, one legal bestmove each after `stop`).
- **21-C8 CONFIRMS 24-C1** (searchmoves with no legal named move → info line + `0000`).
- **21-C9 CONFIRMS** `position fen ... moves` on both builds (8/160 exact; illegal prefix 26/726).
- **21-F8c** — the PC build repairs ONLY the halfmove door; `fullmove 0`, negative clocks, bad ep,
  two kings, no kings and pawn-on-rank-1 are all still refused there.
- **21-F11 WITHDRAWN by me** — `mate 0` on a checkmated root is correct UCI, not a fault.

**Open on the PC build**: 21-F8 (`fullmove 0`), 21-F2 (stale board after a refused FEN).

**Next**: re-check the newest unconfirmed finding of another seat on the PC build, then area 5's
PV/score checks (my area's edge) with the PC build's repaired root path.

**Two harness errors of mine this session, both recorded**: a bare `go` read as a hang (job21;
30-F1 was right, my probe needed `stop`), and a latency figure that measured my read window
(job22; corrected). Also one truncated STATUS.md from an unquoted heredoc (restored).
