## 2026-11-16T21:50:31Z (from `date -u`)
seat 21, area 1 (FEN INPUT under ASan + UBSan), branch for-fable-and-opus/swarm-21

**Findings**: 21-F1..F10 (engine), 21-C1..C5 (30-F6, 30-F7, 08-F5, 24-F1 all independently
CONFIRMED; 21-C2 confirms the brief's illegal-prefix rule), 21-P1 (verified TEXT PATCH for
21-F8, honesty unchanged at 312866 / 862329 / 3024920 / 4865609).

**Newest**: job14 — third independent run of area 1 job 1 (SEED 2121): 18,797 refused,
1,203 accepted, 35 python-invalid (2.91 percent), 0 crash, 0 hang, 0 sanitizer, 0 illegal.
Three seeds now agree within 0.24 percent on the refused count, so 21-F3's numbers are a
property of the parser, not of one seed.

**State**: jobs 1-14 each have REPORT_jobN.md, scripts, raw output and a `date -u` stamp file.
`ADDENDUM_harness.md` records the 19-F12 re-runs; every result since 19-F12 uses the safe
driver. Nothing of mine is uncommitted.

**Next**: one more unchecked finding from another seat if one exists, otherwise area 1 job 2
a third time with SEED 2121.
Next command: `cd forge-combo29/swarm/21 && python3 job6/extreme_safe.py ~/b/asan/forge job15/out`
