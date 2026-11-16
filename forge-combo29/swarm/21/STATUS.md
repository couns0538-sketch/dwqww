## 2026-11-16T22:26Z
seat 21, area 1 (FEN INPUT under ASan + UBSan), branch for-fable-and-opus/swarm-21

**New since 22:18**
- job10: CHECK of seat 08's 08-F5 (reserve-empty clock branch) → **CONFIRMS**, with its two
  discriminating numbers reproduced exactly: `wtime 1` answer equals `go depth 1` in 8 of 8
  of my positions, equals the first legal move in 1 of 8; `wtime 10 winc 10` == `winc 0` in
  8 of 8; median wall 0.10–0.46 ms, max 0.64 ms; 0 illegal bestmoves. `job10/out/summary.md`
  via `job10/check_08f5.py`. → `21-C4`.
- Earlier this window: job9 CONFIRMS 30-F7 (`21-C3`), job8 (seed-2111 extremes + the
  mate-at-100 control) strengthening 21-F9.

**Findings total**: 21-F1..F10 (10 findings), 21-C1..C4 (4 checks: 30-F6, 30-F7, 08-F5
confirmed; 21-C2 confirms the brief's prefix rule).

**State**: every job has its own REPORT_jobN.md, its scripts, its raw files and stamps.txt
under `forge-combo29/swarm/21/`. `ADDENDUM_harness.md` records the 19-F12 re-runs.

**Next**: area 1 job 3 again with a seed-2111 game, then the next unchecked finding.
Next command: `cd forge-combo29/swarm/21 && python3 job4/long_moves.py ~/b/asan/forge job11/out 1000`
