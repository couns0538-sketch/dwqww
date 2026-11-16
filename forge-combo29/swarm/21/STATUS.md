## 2026-11-16T21:56Z — checkpoint
seat 21, area 1 (FEN INPUT under ASan + UBSan), branch for-fable-and-opus/swarm-21, seed 2101

**Since the last checkpoint**
- Re-ran the 20,000-FEN job1 measurement under the 19-F12-safe driver: per-FEN verdicts
  identical on all 20,000 (refused 18,775 / accepted 1,225 / py-invalid 39 / 0 crash /
  0 hang / 0 san). Only the `illegal_best 1` → `0` classifier correction changed.
- `ADDENDUM_harness.md`: which harnesses were exposed to 19-F12, what was re-run, what
  changed and what did not; 21-F2's quoted move corrected to the controlled run.
- `job6/audit_c1.py`: measurement-integrity audit of my own 21-C1 — parser now RAISES if the
  `nodes N` line is absent; two plants (empty answer, impossible comparison) both rejected.
  21-C1 still CONFIRMS 30-F6.
- `REPORT_job7.md`: area 1 job 1 again with SEED 2111 (5,471-position R2, weighted mutation
  mix). 18,820 refused / 1,180 accepted / 35 python-invalid (2.97 %) / 0 crash / 0 hang /
  0 san / 0 illegal. Honesty 4/4 again. One prediction (P4, that the invalid share would
  RISE) FAILED and is recorded as failed.

**Findings**: 21-F1..F10, 21-C1 (CONFIRMS 30-F6), 21-C2 — `FINDINGS.md`.

**Next**: area 1 job 2 again under the safe driver with the seed-2111 inputs (the cycle's
2(c) continuation), then re-check the newest unconfirmed finding from another seat.
Next command: `cd forge-combo29/swarm/21 && python3 job6/extreme_safe.py ~/b/asan/forge job8/out`
