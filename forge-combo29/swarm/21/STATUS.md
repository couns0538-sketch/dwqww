## 2026-11-16T21:40Z — CHECKPOINT (owner's 30-minute push)
seat 21, area 1 (FEN INPUT under ASan + UBSan), branch for-fable-and-opus/swarm-21, seed 2101

**Engine + honesty**: Release build of 6b98f217, honesty 4/4 exact (312866 / 862329 /
3024920 / 4865609) — `HONESTY.txt`. ASan+UBSan build with BOTH mandated proofs.

**Harness integrity (this checkpoint's work)**
- Audited every harness against seat 19's 19-F12 notice: `go depth` + immediate `quit`
  fabricates `bestmove a2a3` with no `info` line. My job1/job2/job3/job4 harnesses used
  `go perft` (synchronous, safe) and `go depth` only in `sticky.py`, `sticky_gui.py`,
  `extreme.py`, `f1_8902.py`. All search-based numbers were RE-RUN with a new driver
  (`job6/safe_engine.py`: reads to `bestmove` before the next command, refuses to send
  while a search is outstanding, never closes stdin mid-search).
- Re-run results: job7 `out/summary.md` (fullmove 0 → refused, stale perft 20 vs true 15),
  job4 prefixes (20/400, 26/726, 22/100 — unchanged), F2 controlled (`job6/out/f2_safe`).
- Measurement-integrity audit of my own 21-C1: parser now asserts the `nodes N` line was
  FOUND and fails loudly; two plants (empty answer, impossible comparison) both correctly
  rejected — `job6/out/audit_c1`. 21-C1 still CONFIRMS 30-F6.

**Findings so far**: 21-F1..F10, 21-C1 (CONFIRMS 30-F6), 21-C2 — `FINDINGS.md`.

**Next**: re-run the 20,000-FEN job1 measurement under the safe driver to publish a
corrected table, then area 1 job 1 with SEED 2111.
Next command: `cd forge-combo29/swarm/21 && python3 job6/fen_rerun.py ~/b/asan/forge out6`
