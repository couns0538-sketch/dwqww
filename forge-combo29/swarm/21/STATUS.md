## 2026-11-16T21:36Z
seat 21, area 1 (FEN INPUT under ASan + UBSan), branch for-fable-and-opus/swarm-21, seed 2101

**Done**
- STEP 2: Release build of 6b98f217 (g++ 13.3.0, no FORGE_PORTABLE); honesty 4/4 exact
  (312866 / 862329 / 3024920 / 4865609) — HONESTY.txt.
- ASan+UBSan build (`__asan_` 35, `__ubsan_` 15) plus the two mandated proofs: planted
  heap over-read and planted signed overflow counted by the SAME runner (2 crashes,
  2 sanitizer lines), real build 0/0.
- Rule 1 planted cases for the harness: fake `bestmove a1a8` engine counted (3 illegal),
  fake never-`readyok` engine counted (startup failure 1).
- job1 (area 1 job 1): 20,000 mutated FENs from G + R (SEED 2101), ASan+UBSan:
  18,775 refused, 1,225 accepted, 1,186 python-valid, 39 python-invalid (31 adjacent
  digits, 8 seven-field), 0 crashes, 0 hangs, 0 sanitizer lines, 0 real illegal bestmoves.
  3,000-char control refused cleanly. REPORT_job1.md.
- job2: CHECK of 30-F6 → **CONFIRMS** (ucinewgame resets the board), and found that
  30-F6's own evidence line cannot show it (20 vs 20). REPORT_job2.md.
- job3 (area 1 job 2): 24 extreme-field cases → 0 crashes, 0 sanitizer lines, 0 perft
  disagreements; `fullmove 0` refused while python-chess accepts it; halfmove ≥ 100
  (up to 2^31) collapses the search to 0 nodes with `cp 0`; all 6,073 real positions
  accepted. REPORT_job3.md.

**Findings**: 21-F1..F10, 21-C1 (CONFIRMS 30-F6) — see FINDINGS.md.
21-F1 is already confirmed by seats 19 and 10 independently.

**Next (THE CYCLE, item 2b)**: area 1 job 3 — `position startpos moves` with 1,000 legal
plies of a random game, then one illegal move at ply 1, 10 and 500, comparing the answer
lines and the kept position (`go perft 1`).
Exact next command: `cd forge-combo29/swarm/21 && mkdir -p job4 && python3 job4/long_moves.py ~/b/asan/forge out`
