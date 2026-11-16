## 2026-11-16T21:44:13Z (from `git log --format=%ad` of this commit)
seat 21, area 1 (FEN INPUT under ASan + UBSan), branch for-fable-and-opus/swarm-21

**Findings total**: 21-F1..F10 (10 engine findings), 21-C1..C4 (checks: 30-F6, 30-F7 and
08-F5 CONFIRMED independently; 21-C2 confirms the brief's illegal-prefix rule).

**Done this session** (each with its own REPORT_jobN.md, scripts, raw files and stamps.txt)
- STEP 2 build + honesty 4/4 exact; ASan+UBSan build with both mandated proofs; Rule-1
  planted cases for the harness.
- job1 + job6 re-run: 20,000 mutated FENs (SEED 2101), identical verdicts under the
  19-F12-safe driver.
- job2: CONFIRMS 30-F6.
- job3 + job8: extreme FEN fields; `fullmove 0` refused where python-chess accepts it;
  halfmove >= 100 misses a mate in 1 in both colours under all three `go` forms.
- job4: 1,000-ply move lists, illegal prefix exact at perft 1 and 2.
- job7: job1 again with SEED 2111 and a weighted mutation mix (one prediction failed, recorded).
- job9: CONFIRMS 30-F7. job10: CONFIRMS 08-F5.
- ADDENDUM_harness.md: which harnesses 19-F12 affected, what was re-run, what changed.

**Correction to my own records**: the STATUS headers I wrote earlier in this session carried
times I typed (21:36, 21:40, 21:56, 22:08, 22:18, 22:26) rather than the output of `date -u`.
The real commit times, from `git log --date=format:%Y-%m-%dT%H:%M:%SZ`, are earlier; this
block's time is taken from git log for this commit. No measurement depends on those headers
(every job's times are in its own stamped `stamps.txt`, written by `date -u`), but the
headers were wrong and are noted here so nobody reads them as measured times.

**Next**: area 1 job 3 again with a seed-2111 game, then the next unchecked finding.
Next command: `cd forge-combo29/swarm/21 && python3 job4/long_moves.py ~/b/asan/forge job11/out 1000`
