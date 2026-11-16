## 2026-11-16T21:50:04Z (from `date -u`)
seat 21, area 1 (FEN INPUT under ASan + UBSan), branch for-fable-and-opus/swarm-21

**Findings**: 21-F1..F10 (engine), 21-C1..C5 (30-F6, 30-F7, 08-F5, 24-F1 all independently
CONFIRMED; 21-C2 confirms the brief's illegal-prefix rule), 21-P1 (verified TEXT PATCH for
21-F8, honesty unchanged).

**Newest**: job13 CONFIRMS 24-F1 with my own TSan build (21 `__tsan_` symbols) and my own
planted race (12/12 rounds reported vs 0/300 on the real build).

**State**: jobs 1-13 each have REPORT_jobN.md, scripts, raw output and a `date -u` stamp file.
`ADDENDUM_harness.md` records the 19-F12 re-runs. All results since 19-F12 use the safe driver.

**Next**: area 1 job 1 a third time with SEED 2121.
Next command: `cd forge-combo29/swarm/21 && python3 job7/gen2.py job14 && python3 job6/fen_rerun.py ~/b/asan/forge job14/mutations2.tsv job14/out asan14`
