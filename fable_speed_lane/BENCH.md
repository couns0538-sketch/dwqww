# BENCH: identity evidence and indicative timing

Generated 2026-11-10 16:59 Vienna by `tools/collect_evidence.py` from the files under `evidence/` (copied from `D:\forge_jobs_20261109\fable2\out\id`). All runs: CPU 3 only (mask 0x08), Idle priority, one process at a time, while the crew's gates ran on other cores. Lock = combo29 exe `e1284f7f...8802e`.

## 1. Lock reference rows

| Item | Result | File |
|---|---|---|
| 12 pins on the lock copy | 12/12 | `evidence/lock/pins.json` |
| Cold rows net on | 12000 rows, sha256 `c366cf20b40db7c3e94808f2338d4421d5d30951ff3539c9d3c55581c9ce305e` | `evidence/lock/cold_on_all.tsv` |
| ... against QA's cached lock rows, net on | 12000 QA rows, 0 rows differ (QA file sha256 `c366cf20b40db7c3e94808f2338d4421d5d30951ff3539c9d3c55581c9ce305e`) | `C:\Users\Administrator\grok-pc\forge_push\overnight_timing_20261108\checks2\combo29_on\fens_n12000_d13.tsv` (read only) |
| Cold rows net off | 12000 rows, sha256 `a6e52a5d316fd6071aa2e3fe753fa2d249cc995bd40d16b573563263309e7393` | `evidence/lock/cold_off_all.tsv` |
| ... against QA's cached lock rows, net off | 12000 QA rows, 0 rows differ (QA file sha256 `a6e52a5d316fd6071aa2e3fe753fa2d249cc995bd40d16b573563263309e7393`) | `C:\Users\Administrator\grok-pc\forge_push\overnight_timing_20261108\checks2\combo29_off\fens_n12000_d13.tsv` (read only) |
| Warm transcript | sha256 `30d5e06484abb5a3c962f4aade7a4d94b5a1bedfcd3c5b080d82d5d9fd10ad52` | `evidence/lock/warm.txt` |
| Perft set | PASS | `evidence/lock/perftset.json` |

## 2. Identity ladder

Switch 0 = the patch applied, switch left at its default. `89 / 0` = 89 differing bytes inside the debug record (PDB hash and path), 0 differing bytes anywhere else: code and data bytes identical to the lock; sha256 identity UNRESOLVED (debug record only), see STATUS.md.

| Check | WITNESS_NOPIN | EVADE_LEGAL | PAWN_CAPMASK | CHECKERS_KL | KING_PAWN_CACHE | BUNDLE4 | BUNDLE3 | BUNDLE |
|---|---|---|---|---|---|---|---|---|
| Status | LISTED-UNBUILT | LISTED-UNBUILT | UNLISTED | LISTED-UNBUILT | not new (built before, DUPCHECK.md); extra | the four new candidates | three new candidates: EVADE_LEGAL, PAWN_CAPMASK, CHECKERS_KL | BUNDLE4 + KING_PAWN_CACHE; extra |
| Patch md5 | `ccfa6ce5...` | `b5aaa89f...` | `2a680e14...` | `c8f080ba...` | `a51e1b69...` | `4cfedef4...` | `ba2fcf2e...` | `953ee65a...` |
| Switch 0 vs lock, bytes (debug / other) | 89 / 0 | 89 / 0 | 89 / 0 | 89 / 0 | 89 / 0 | 89 / 0 | 89 / 0 | 89 / 0 |
| Switch 1, 12 pins | 12/12 | 12/12 | 12/12 | 12/12 | 12/12 | 12/12 | 12/12 | 12/12 |
| Harness, 12,000 FENs, switch 1 | PASS: 12000 FENs, transcript equal to base True, 0 self-check failures | PASS: 12000 FENs, transcript equal to base True, 0 self-check failures | PASS: 12000 FENs, transcript equal to base True, 0 self-check failures | PASS: 12000 FENs, transcript equal to base True, 0 self-check failures | PASS: 12000 FENs, transcript equal to base True, 0 self-check failures | PASS: 12000 FENs, transcript equal to base True, 0 self-check failures | PASS: 12000 FENs, transcript equal to base True, 0 self-check failures | PASS: 12000 FENs, transcript equal to base True, 0 self-check failures |
| Harness, 12,000 FENs, verify build (=2) | PASS: 12000 FENs, exit 0 (no abort), transcript equal True | PASS: 12000 FENs, exit 0 (no abort), transcript equal True | not run | PASS: 12000 FENs, exit 0 (no abort), transcript equal True | not run | PASS: 12000 FENs, exit 0 (no abort), transcript equal True | PASS: 12000 FENs, exit 0 (no abort), transcript equal True | PASS: 12000 FENs, exit 0 (no abort), transcript equal True |
| Harness, targeted positions, switch 1 | PASS: 24 FENs, transcript equal to base True, 0 self-check failures | PASS: 24 FENs, transcript equal to base True, 0 self-check failures | PASS: 24 FENs, transcript equal to base True, 0 self-check failures | PASS: 24 FENs, transcript equal to base True, 0 self-check failures | PASS: 24 FENs, transcript equal to base True, 0 self-check failures | PASS: 24 FENs, transcript equal to base True, 0 self-check failures | PASS: 24 FENs, transcript equal to base True, 0 self-check failures | PASS: 24 FENs, transcript equal to base True, 0 self-check failures |
| Harness, targeted positions, verify build (=2) | PASS: 24 FENs, exit 0 (no abort), transcript equal True | PASS: 24 FENs, exit 0 (no abort), transcript equal True | not run | PASS: 24 FENs, exit 0 (no abort), transcript equal True | not run | PASS: 24 FENs, exit 0 (no abort), transcript equal True | PASS: 24 FENs, exit 0 (no abort), transcript equal True | PASS: 24 FENs, exit 0 (no abort), transcript equal True |
| Verify engine, 12 pins | PASS: 12/12 | PASS: 12/12 | not run | PASS: 12/12 | not run | PASS: 12/12 | PASS: 12/12 | PASS: 12/12 |
| Verify engine, cold 12,000 net on | not run | not run | not run | not run | not run | PASS: 0 rows differ | INCOMPLETE: 1501 of 12000 rows, all equal the lock's | INCOMPLETE: stopped at the start (1 of 12000 rows) |
| Cold 12,000, depth 13, net on | INCOMPLETE: 3501 of 12000 rows, all equal the lock's | INCOMPLETE: 3501 of 12000 rows, all equal the lock's | INCOMPLETE: 1501 of 12000 rows, all equal the lock's | INCOMPLETE: 5001 of 12000 rows, all equal the lock's | INCOMPLETE: stopped at the start (1 of 12000 rows) | INCOMPLETE: 7501 of 12000 rows, all equal the lock's | INCOMPLETE: 3501 of 12000 rows, all equal the lock's | INCOMPLETE: stopped at the start (1 of 12000 rows) |
| Cold 12,000, depth 13, net off | INCOMPLETE: 2501 of 12000 rows, all equal the lock's | INCOMPLETE: 2501 of 12000 rows, all equal the lock's | INCOMPLETE: 2501 of 12000 rows, all equal the lock's | INCOMPLETE: 2501 of 12000 rows, all equal the lock's | INCOMPLETE: stopped at the start (1 of 12000 rows) | INCOMPLETE: 1501 of 12000 rows, all equal the lock's | INCOMPLETE: 3501 of 12000 rows, all equal the lock's | INCOMPLETE: stopped at the start (1 of 12000 rows) |
| Warm session transcript | PASS: transcript equal True, 1004 searches, bench 13 = 862329 | PASS: transcript equal True, 1004 searches, bench 13 = 862329 | PASS: transcript equal True, 1004 searches, bench 13 = 862329 | PASS: transcript equal True, 1004 searches, bench 13 = 862329 | PASS: transcript equal True, 1004 searches, bench 13 = 862329 | PASS: transcript equal True, 1004 searches, bench 13 = 862329 | PASS: transcript equal True, 1004 searches, bench 13 = 862329 | PASS: transcript equal True, 1004 searches, bench 13 = 862329 |
| Threads 2-4 soak | PASS: 60/60 legal, T1 tail 50/50 | PASS: 60/60 legal, T1 tail 50/50 | PASS: 60/60 legal, T1 tail 50/50 | PASS: 60/60 legal, T1 tail 50/50 | PASS: 60/60 legal, T1 tail 50/50 | PASS: 60/60 legal, T1 tail 50/50 | PASS: 60/60 legal, T1 tail 50/50 | PASS: 60/60 legal, T1 tail 50/50 |
| Perft set (6 positions) | PASS: 6/6 | PASS: 6/6 | PASS: 6/6 | PASS: 6/6 | PASS: 6/6 | PASS: 6/6 | PASS: 6/6 | PASS: 6/6 |

"not run" in a verify row of `PAWN_CAPMASK` or `KING_PAWN_CACHE` means the patch has no verify mode. The verify engine was run over the cold set for the bundles only (all verify modes on at once). A verify build of `WITNESS_NOPIN` still asks the legality test it would skip, which builds the king lines; verify builds therefore take the `CHECKERS_KL` shortcut in a superset of the shipped mode's cases.

Base harness transcript (lock source, 12,000 FENs): sha256 `b7e28032cd6646459417c2aecc0c3435663fff4b6ae59240f3eb04cb70570059`.

## 3. INDICATIVE timing (not the ABBA)

All of it: lock exe (A) against a switch-1 exe (B), Threads 1, Hash 16, fresh engine per arm, warm `bench 13`, then a timed bench; blocks of four arms; ratio per block = sqrt(B*B / (A*A)) of nodes per unit; positive = B faster. **Cycles** = CPU cycles of the engine process over the timed bench (QueryProcessCycleTime), which preemption by other jobs does not inflate; **wall** = wall-clock time, which it does. One shared CPU (3) at Idle priority while the crew's gates ran and, for most of it, while this job's own cold runs shared the same CPU. None of this is QA's quiet ABBA.

### 3.1 The same exe is not equally fast from two files

Found while checking why `BUNDLE4` first timed 3.7 % slower than the lock and, two hours later, 0.3 % faster on the same two files. Lock against lock, by cycles:

| Lock against lock | Timed | Blocks | Median | SD of block ratios | IQR | min .. max | Evidence |
|---|---|---|---|---|---|---|---|
| one file for all arms (first timing step) | bench 20, net on | 10 | +0.25 % | 1.36 % | -0.71 .. +1.55 | -1.99 .. +2.33 | `evidence/AA_lock_vs_lock/abba_d20_on_013918` |
| one file for all arms (first timing step) | bench 20, net off | 10 | +0.25 % | 0.86 % | -0.09 .. +0.35 | -0.70 .. +2.57 | `evidence/AA_lock_vs_lock/abba_d20_off_033555` |
| two byte-identical copies made anew for every block | bench 20, net on | 12 | +0.10 % | 2.80 % | -0.81 .. +1.45 | -5.70 .. +6.12 | `evidence/regime/AA_recopy/rc16_d20_on_044034` |
| a new copy for every arm | bench 16, net on | 24 | +0.45 % | 2.76 % | -1.00 .. +3.20 | -3.91 .. +8.02 | `evidence/regime/AA_recopy/rc16_d16_on_045134` |
| a new copy for every arm, load address fixed at 0x140000000 | bench 16, net on | 24 | +0.28 % | 2.48 % | -0.43 .. +2.65 | -5.70 .. +6.08 | `evidence/regime/AA_fixedbase/fb16_d16_on_045614` |
| a new copy for every arm, order alternating (section 3.2) | bench 16, net on | 40 | -0.02 % | 1.42 % | -0.37 .. +0.50 | -2.06 .. +5.54 | `evidence/AA_lock_vs_lock/abbarc_d16_on_050437` |

In the per-block run each block holds two launches of one copy and two of another. Two launches of the same file differ by 0.61 % (median of 24 pairs); the two files of a block differ by 1.19 % (median of 12 blocks, largest 6.04 %). The copies are byte-identical.

The copy test (`tools/file_effect.py`), which separates a copy's own offset from the drift of the machine: 14:17: 6 copies of the lock, 8 launches each in rotating order (bench 16, net on): SD between copies 0.26 %, SD of one launch 1.15 %, permutation p 0.25 (`evidence/regime/FILE_EFFECT/fe_d16_on_051703/FILE_EFFECT.json`).

Reading, with its limits. At 11:43 one fixed pair of files gave -3.65 % with a spread of a few tenths of a percent over 30 blocks (section 3.3); the five-bundle, which holds the same four switches, gave +0.43 % in the next quarter of an hour; the same two files gave about +0.3 % two hours later; and with a new copy per arm the four-bundle reads -0.70 % (section 3.2). Between 13:40 and 14:01 byte-identical copies of the lock differed by up to 6 % in single blocks, while two launches of one copy agreed far better. From 14:04 on the extra spread was gone, and the copy test at 14:17 found no offset that belongs to a copy. So at times an exe file carried its own offset of several percent for many minutes, and at other times it did not. The load address is not the cause (copies forced to one address scattered as much). What else it is, I could not establish; where Windows put the file's code and constant pages in physical memory is a candidate, not a finding. Consequences that do not depend on the cause: (1) a timing of two fixed files can be off by several percent while looking tight; (2) lock against lock with one file cannot show that; (3) a new copy of the exe for every arm turns such an offset into visible spread. Whether a quiet machine shows any of this is for QA to measure (QA_ABBA_PROTOCOL.md).

### 3.2 Timing with a new copy of the exe for every arm

`tools/timing2.ps1`: every arm runs from a copy made for that arm, odd blocks run B A A B, timed bench 16 (the ABBA's own timed bench). The per-file effect is then part of the spread of the block ratios instead of a bias. The interval is a bootstrap 95 % interval of the median over blocks. A candidate's row is to be read against the lock-against-lock row, which shows what the method gives when there is nothing to find.

| Pair | Net | Blocks | Cycles median | 95 % interval | Cycles mean +/- SE | SD of blocks | min .. max | Wall median | Evidence |
|---|---|---|---|---|---|---|---|---|---|
| lock against lock | on | 40 | -0.02 % | -0.27 .. +0.24 | +0.32 +/- 0.22 | 1.42 % | -2.06 .. +5.54 | -4.16 % | `evidence/AA_lock_vs_lock/abbarc_d16_on_050437` |
| lock against lock, **INCOMPLETE** (run stopped at 16:56) | on | 36 | -0.00 % | -0.58 .. +0.75 | +0.10 +/- 0.50 | 2.98 % | -8.68 .. +11.15 | -1.84 % | `evidence/AA_lock_vs_lock/abbarc_d16_on_062604.txt` (log only) |
| BUNDLE4 | on | 100 | -0.70 % | -0.99 .. -0.39 | -0.75 +/- 0.14 | 1.37 % | -4.15 .. +3.68 | +0.17 % | `evidence/BUNDLE4/abbarc_d16_on_051448` |
| BUNDLE3, **INCOMPLETE** (run stopped at 16:56) | on | 34 | -0.22 % | -0.90 .. +0.47 | -0.40 +/- 0.61 | 3.56 % | -11.75 .. +7.64 | -0.52 % | `evidence/BUNDLE3/abbarc_d16_on_063123.txt` (log only) |
| BUNDLE, **INCOMPLETE** (run stopped at 16:56) | on | 4 | +0.94 % | -1.40 .. +3.55 | +1.01 +/- 0.98 | 1.97 % | -1.40 .. +3.55 | +2.96 % | `evidence/BUNDLE/abbarc_d16_on_074532.txt` (log only) |
| WITNESS_NOPIN | on | 60 | -1.02 % | -1.25 .. -0.86 | -1.02 +/- 0.22 | 1.73 % | -6.13 .. +5.17 | -0.70 % | `evidence/WITNESS_NOPIN/abbarc_d16_on_055224` |
| EVADE_LEGAL, **INCOMPLETE** (run stopped at 16:56) | on | 34 | -0.63 % | -0.99 .. +0.37 | -0.75 +/- 0.47 | 2.76 % | -10.73 .. +4.05 | -1.05 % | `evidence/EVADE_LEGAL/abbarc_d16_on_063121.txt` (log only) |
| PAWN_CAPMASK, **INCOMPLETE** (run stopped at 16:56) | on | 34 | -0.39 % | -1.14 .. +0.46 | -0.64 +/- 0.66 | 3.88 % | -15.93 .. +6.42 | -0.88 % | `evidence/PAWN_CAPMASK/abbarc_d16_on_063125.txt` (log only) |
| CHECKERS_KL, **INCOMPLETE** (run stopped at 16:56) | on | 34 | -0.59 % | -0.95 .. +0.48 | -0.64 +/- 0.50 | 2.90 % | -9.76 .. +4.70 | +0.00 % | `evidence/CHECKERS_KL/abbarc_d16_on_063124.txt` (log only) |
| KING_PAWN_CACHE, **INCOMPLETE** (run stopped at 16:56) | on | 5 | +0.09 % | -2.33 .. +4.57 | +0.58 +/- 1.02 | 2.28 % | -2.33 .. +4.57 | -0.57 % | `evidence/KING_PAWN_CACHE/abbarc_d16_on_074532.txt` (log only) |

Finished runs of the same pair are pooled; the evidence column names each run. Rows marked INCOMPLETE are runs that were stopped at 16:56 on the owner's instruction to wrap up: the blocks they had finished are shown as they are, with fewer blocks than planned (100 for `BUNDLE3`, 40 for the singles and for the second lock-against-lock round, 60 and 40 for the two extras) and therefore wider intervals. From 15:11 on about forty of this job's own runs shared the CPU with the timing arms (every arm of a pair alike); all INCOMPLETE rows were taken in that crowd, the second lock-against-lock row with them. No net-off timing was taken in this step.

### 3.3 First timing step: one fixed file per exe (superseded by 3.2)

Kept for the record, not as results: each row is the patch plus whatever offset its two files carried at that time. The last rows repeat `BUNDLE4` on the same two files two hours later.

| Pair | Net | Timed | When (Vienna) | Wall median | Cycles median | Cycles IQR | Cycles min .. max | Blocks | Evidence |
|---|---|---|---|---|---|---|---|---|---|
| lock against lock | on | bench 20 | 10:39 to 10:44 | +1.41 % | +0.25 % | -0.71 .. +1.55 | -1.99 .. +2.33 | 10 | `evidence/AA_lock_vs_lock/abba_d20_on_013918` |
| lock against lock | off | bench 20 | 12:35 to 12:40 | +1.41 % | +0.25 % | -0.09 .. +0.35 | -0.70 .. +2.57 | 10 | `evidence/AA_lock_vs_lock/abba_d20_off_033555` |
| BUNDLE4 | on | bench 20 | 11:43 to 11:57 | -4.39 % | -3.65 % | -3.73 .. -3.43 | -4.25 .. -1.26 | 30 | `evidence/BUNDLE4/abba_d20_on_024331` |
| BUNDLE4 | off | bench 20 | 12:40 to 12:44 | +1.05 % | -0.89 % | -1.25 .. -0.63 | -1.50 .. -0.28 | 10 | `evidence/BUNDLE4/abba_d20_off_034020` |
| BUNDLE3 | on | bench 20 | not run | | | | | | |
| BUNDLE3 | off | bench 20 | not run | | | | | | |
| BUNDLE | on | bench 20 | 11:57 to 12:11 | +0.66 % | +0.43 % | -0.05 .. +0.84 | -1.71 .. +1.43 | 30 | `evidence/BUNDLE/abba_d20_on_025748` |
| BUNDLE | off | bench 20 | 12:44 to 12:49 | +0.97 % | +0.79 % | +0.27 .. +1.15 | -1.64 .. +1.18 | 10 | `evidence/BUNDLE/abba_d20_off_034451` |
| WITNESS_NOPIN | on | bench 20 | 12:11 to 12:16 | -1.17 % | -1.06 % | -1.46 .. -0.76 | -2.01 .. +1.45 | 10 | `evidence/WITNESS_NOPIN/abba_d20_on_031149` |
| WITNESS_NOPIN | off | bench 20 | 12:49 to 12:53 | +0.36 % | -1.17 % | -1.52 .. -0.95 | -3.79 .. +0.27 | 10 | `evidence/WITNESS_NOPIN/abba_d20_off_034912` |
| EVADE_LEGAL | on | bench 20 | 12:16 to 12:21 | -1.49 % | -0.64 % | -1.19 .. -0.59 | -2.56 .. +0.66 | 10 | `evidence/EVADE_LEGAL/abba_d20_on_031633` |
| EVADE_LEGAL | off | bench 20 | 12:53 to 12:58 | -0.07 % | -0.02 % | -0.10 .. +0.04 | -0.40 .. +0.39 | 10 | `evidence/EVADE_LEGAL/abba_d20_off_035336` |
| PAWN_CAPMASK | on | bench 20 | 12:21 to 12:26 | +1.66 % | +0.51 % | +0.04 .. +0.75 | -1.54 .. +0.91 | 10 | `evidence/PAWN_CAPMASK/abba_d20_on_032113` |
| PAWN_CAPMASK | off | bench 20 | 12:58 to 13:02 | +1.36 % | +0.54 % | +0.48 .. +0.70 | +0.20 .. +2.31 | 10 | `evidence/PAWN_CAPMASK/abba_d20_off_035815` |
| CHECKERS_KL | on | bench 20 | 12:26 to 12:31 | +1.41 % | +0.38 % | +0.12 .. +0.68 | -0.06 .. +1.56 | 10 | `evidence/CHECKERS_KL/abba_d20_on_032628` |
| CHECKERS_KL | off | bench 20 | 13:02 to 13:07 | +1.05 % | -0.36 % | -0.70 .. -0.14 | -1.96 .. +0.24 | 10 | `evidence/CHECKERS_KL/abba_d20_off_040244` |
| KING_PAWN_CACHE | on | bench 20 | 12:31 to 12:35 | +2.37 % | +0.76 % | +0.58 .. +0.89 | +0.09 .. +3.62 | 10 | `evidence/KING_PAWN_CACHE/abba_d20_on_033117` |
| KING_PAWN_CACHE | off | bench 20 | 13:07 to 13:12 | -2.83 % | -2.46 % | -3.22 .. -2.28 | -4.30 .. +1.00 | 10 | `evidence/KING_PAWN_CACHE/abba_d20_off_040720` |
| BUNDLE4 (repeat) | on | bench 16 | 13:25 to 13:27 | -9.44 % | -0.32 % | -0.61 .. +0.02 | -0.98 .. +0.52 | 6 | `evidence/regime/BUNDLE4/h1_d16_on_042535` |
| BUNDLE4 (repeat) | on | bench 16 | 13:27 to 13:28 | -7.02 % | +0.44 % | +0.18 .. +0.72 | -0.20 .. +2.21 | 6 | `evidence/regime/BUNDLE4/h16_d16_on_042709` |
| BUNDLE4 (repeat) | on | bench 16 | 13:28 to 13:30 | +2.75 % | +0.45 % | +0.19 .. +0.86 | -0.67 .. +1.44 | 6 | `evidence/regime/BUNDLE4/h256_d16_on_042835` |
| BUNDLE4 (repeat) | on | bench 20 | 13:34 to 13:38 | +2.69 % | +0.30 % | +0.14 .. +0.40 | +0.10 .. +2.90 | 5 | `evidence/regime/BUNDLE4/h16_d20_on_043446` |

The repeats named `h1_`, `h16_` and `h256_` were meant to vary the hash size; `bench` builds its own 16 MB table and ignores the option, so they are three plain repeats.

`go depth 20` on the eight bench positions one by one (`tools/pos_cycles.py`, 2 blocks, fixed files, same tree as bench 20: 12389307 nodes): BUNDLE4 +0.18 % by cycles; per position from -0.38 % to +1.06 % (`evidence/regime/BUNDLE4/pos_d20_on_h16/POS_CYCLES.json`).

### 3.4 Does the size of the transposition table matter? (`go`, Hash 1 / 16 / 256 MB)

`bench` cannot answer this: it builds its own 16 MB table. `tools/regime_pos.ps1` runs `go` on the eight bench positions with the Hash option set, a new copy of the exe for every arm, odd blocks B A A B. The three sizes ran at the same time on the same CPU, together with many other runs of this job, so each block is noisy. Node counts differ between sizes (another table, another tree) and are equal for lock and candidate at each size.

| Candidate | Table | Search | Nodes (last info lines) | Blocks | Cycles median | 95 % interval | Cycles mean +/- SE | Evidence |
|---|---|---|---|---|---|---|---|---|
| WITNESS_NOPIN | 1 MB | depth 16 | 2882111 | 16 | -0.85 % | -1.42 .. +0.06 | -0.36 +/- 0.80 | `evidence/regime/WITNESS_NOPIN/pos_d16_on_h1/POS_CYCLES.json` |
| WITNESS_NOPIN | 16 MB | depth 16 | 3024920 | 16 | -0.61 % | -1.56 .. +0.47 | -0.24 +/- 0.73 | `evidence/regime/WITNESS_NOPIN/pos_d16_on_h16/POS_CYCLES.json` |
| WITNESS_NOPIN | 256 MB | depth 16 | 3019577 | 16 | -1.56 % | -2.88 .. -0.50 | -1.13 +/- 0.73 | `evidence/regime/WITNESS_NOPIN/pos_d16_on_h256/POS_CYCLES.json` |

Exact counters for this (frozen workload, 4,200,115 nodes; `evidence/witness_counters.txt`): `has_legal_move` is called 3,902,622 times. The lock builds the king lines 3,923,435 times. `WITNESS_NOPIN` accepts the witness without the legality test, and so without the build, 2,651,591 times. 1,477,817 builds disappear; the other 1,173,774 are made later in the node, after the table probe.

What the question is: the search prefetches the child's table entry before `make_move` and reads it at the top of the child, after the stalemate test that calls `has_legal_move`. In the lock that call builds the king lines while the entry is on its way. `WITNESS_NOPIN` skips the build there; at a node that goes on, the build then happens after the probe at full cost, and at a node that ends at the probe nothing is saved while the entry has not arrived. If that is why `WITNESS_NOPIN` times slower under load, it should lose more with a large table than with one that stays in cache. The rows above are the test; read them with their intervals.

## 4. Mutants: would the harness notice a wrong patch?

`tests/mutants.ps1` plants one wrong change per run, builds the harness on it and runs the targeted positions and the first 300 FENs. CAUGHT = transcript differs, a self-check fails, or a verify build aborts. Each tree is first run unchanged with the same switches (control) and must be clean.

| Tree | Mutant | Planted change | Verdict | Where |
|---|---|---|---|---|
| KING_PAWN_CACHE | `kpc_anyking` | record used for any king square | CAUGHT | targeted: 472 self-check failures, transcript differs; first300: 16438 self-check failures, transcript differs |
| KING_PAWN_CACHE | `kpc_keepother` | other colour's record kept when the pawns changed | CAUGHT | targeted: clean; first300: 1232 self-check failures, transcript differs |
| KING_PAWN_CACHE | `kpc_shelter0` | shelter sum for king danger not restored on a hit | CAUGHT | targeted: 608 self-check failures, transcript differs; first300: 24239 self-check failures, transcript differs |
| WITNESS_NOPIN | `wit_pinned_plain` | witness accepted without the line test, plain build (shows only where the pinned push is the last hope: targeted row 10) | CAUGHT | targeted: 1 self-check failures, transcript differs; first300: clean |
| WITNESS_NOPIN | `wit_pinned_verify` | witness accepted without the line test, verify build | CAUGHT | targeted: verify abort inside the engine; first300: verify abort inside the engine |
| WITNESS_NOPIN | `wit_incheck` | witness accepted while in check (shows only at a checkmate with a free pawn push: targeted row 9) | CAUGHT | targeted: 1 self-check failures, transcript differs; first300: clean |
| EVADE_LEGAL | `evd_nopin` | pin rule dropped for check evasions | CAUGHT | targeted: 15 self-check failures, transcript differs; first300: 1 self-check failures, transcript differs |
| EVADE_LEGAL | `evd_double` | double check treated like single check | CAUGHT | targeted: 1 self-check failures, transcript differs; first300: clean |
| EVADE_LEGAL | `evd_nocapture` | capturing the checker no longer counts as an evasion | CAUGHT | targeted: 15 self-check failures, transcript differs; first300: 200 self-check failures, transcript differs |
| PAWN_CAPMASK | `cap_wrongside` | capturer mask built with the wrong pawn direction | CAUGHT | targeted: transcript differs; first300: transcript differs |
| CHECKERS_KL | `chk_nodisc` | discovered checks ignored | CAUGHT | targeted: 359 self-check failures, transcript differs; first300: 211 self-check failures, transcript differs |
| CHECKERS_KL | `chk_promo` | promotions taken through the shortcut (targeted row 4) | CAUGHT | targeted: 460 self-check failures, transcript differs; first300: 249 self-check failures, transcript differs |
| CHECKERS_KL | `chk_ep` | en passant taken through the shortcut (targeted row 23) | CAUGHT | targeted: 3 self-check failures, transcript differs; first300: clean |
| CHECKERS_KL | `chk_kingmoves` | king moves taken through the shortcut (differs only for an illegal king step next to the enemy king) | CAUGHT | targeted: 6 self-check failures, transcript differs; first300: 1025 self-check failures |
| CHECKERS_KL | `chk_wrongking` | discoverer line tested against the wrong king (targeted row 24) | CAUGHT | targeted: 40 self-check failures, transcript differs; first300: clean |
| BUNDLE4 | `wit_pinned_plain` | witness accepted without the line test, plain build (shows only where the pinned push is the last hope: targeted row 10) | CAUGHT | targeted: 1 self-check failures, transcript differs; first300: clean |
| BUNDLE4 | `wit_pinned_verify` | witness accepted without the line test, verify build | CAUGHT | targeted: verify abort inside the engine; first300: verify abort inside the engine |
| BUNDLE4 | `wit_incheck` | witness accepted while in check (shows only at a checkmate with a free pawn push: targeted row 9) | CAUGHT | targeted: 1 self-check failures, transcript differs; first300: clean |
| BUNDLE4 | `evd_nopin` | pin rule dropped for check evasions | CAUGHT | targeted: 140 self-check failures, transcript differs; first300: 2 self-check failures, transcript differs |
| BUNDLE4 | `evd_double` | double check treated like single check | CAUGHT | targeted: 1 self-check failures, transcript differs; first300: clean |
| BUNDLE4 | `evd_nocapture` | capturing the checker no longer counts as an evasion | CAUGHT | targeted: 15 self-check failures, transcript differs; first300: 200 self-check failures, transcript differs |
| BUNDLE4 | `cap_wrongside` | capturer mask built with the wrong pawn direction | CAUGHT | targeted: transcript differs; first300: transcript differs |
| BUNDLE4 | `chk_nodisc` | discovered checks ignored | CAUGHT | targeted: 359 self-check failures, transcript differs; first300: 211 self-check failures, transcript differs |
| BUNDLE4 | `chk_promo` | promotions taken through the shortcut (targeted row 4) | CAUGHT | targeted: 460 self-check failures, transcript differs; first300: 249 self-check failures, transcript differs |
| BUNDLE4 | `chk_ep` | en passant taken through the shortcut (targeted row 23) | CAUGHT | targeted: 3 self-check failures, transcript differs; first300: clean |
| BUNDLE4 | `chk_kingmoves` | king moves taken through the shortcut (differs only for an illegal king step next to the enemy king) | CAUGHT | targeted: 6 self-check failures, transcript differs; first300: 1025 self-check failures |
| BUNDLE4 | `chk_wrongking` | discoverer line tested against the wrong king (targeted row 24) | CAUGHT | targeted: 40 self-check failures, transcript differs; first300: clean |
| (MUTANTS_BUNDLE3.log) | pass **INCOMPLETE**: stopped at 16:56 on the owner's instruction to wrap up, after the control and 0 mutants | | | |
| BUNDLE | `kpc_anyking` | record used for any king square | CAUGHT | targeted: 472 self-check failures, transcript differs; first300: 16438 self-check failures, transcript differs |
| BUNDLE | `kpc_keepother` | other colour's record kept when the pawns changed | CAUGHT | targeted: clean; first300: 1232 self-check failures, transcript differs |
| BUNDLE | `kpc_shelter0` | shelter sum for king danger not restored on a hit | ERROR in the log (one set refused by the disk guard); caught on the set that ran | targeted: exit 95 without a harness verdict; first300: 24239 self-check failures, transcript differs |

"exit 95" in a row is the launcher's refusal to start a run while D: was under this job's 30.3 GiB guard: that set was not run for that mutant. The script of that day counted any such exit as ERROR; the verdict column says what the set that did run showed.

Controls (the unchanged tree with the same switches):

| Tree | Switches | Result | Sets |
|---|---|---|---|
| KING_PAWN_CACHE | `FORGE_SPD_KING_PAWN_CACHE=1` | clean | targeted: clean; first300: clean |
| WITNESS_NOPIN | `FORGE_SPD_WITNESS_NOPIN=1` | clean | targeted: clean; first300: clean |
| WITNESS_NOPIN | `FORGE_SPD_WITNESS_NOPIN=2` | clean | targeted: clean; first300: clean |
| EVADE_LEGAL | `FORGE_SPD_EVADE_LEGAL=1` | clean | targeted: clean; first300: clean |
| PAWN_CAPMASK | `FORGE_SPD_PAWN_CAPMASK=1` | clean | targeted: clean; first300: clean |
| CHECKERS_KL | `FORGE_SPD_CHECKERS_KL=1` | clean | targeted: clean; first300: clean |
| BUNDLE4 | `FORGE_SPD_WITNESS_NOPIN=1,FORGE_SPD_EVADE_LEGAL=1,FORGE_SPD_PAWN_CAPMASK=1,FORGE_SPD_CHECKERS_KL=1` | clean | targeted: clean; first300: clean |
| BUNDLE4 | `FORGE_SPD_WITNESS_NOPIN=2,FORGE_SPD_EVADE_LEGAL=1,FORGE_SPD_PAWN_CAPMASK=1,FORGE_SPD_CHECKERS_KL=1` | clean | targeted: clean; first300: clean |
| BUNDLE3 | `FORGE_SPD_EVADE_LEGAL=1,FORGE_SPD_PAWN_CAPMASK=1,FORGE_SPD_CHECKERS_KL=1` | clean | targeted: clean; first300: clean |
| BUNDLE | `FORGE_SPD_WITNESS_NOPIN=1,FORGE_SPD_EVADE_LEGAL=1,FORGE_SPD_PAWN_CAPMASK=1,FORGE_SPD_CHECKERS_KL=1,FORGE_SPD_KING_PAWN_CACHE=1` | clean | targeted: clean; first300: clean |

Evidence: `evidence/mutants/`.

## 5. Exact work counters: what each switch removes

Not a timing. Every lock-recipe build has an instrumented first stage that runs the frozen workload (bench 11, 13 and 16; 4,200,115 nodes in every build, since all builds are node-identical). Its profile holds an exact counter per source function and per source region. The table compares those counters between the control rebuild of the lock source and each switch-1 build (`tools/work_counters.py`). "same" = equal to the lock's count. Counters measure work removed, not time gained: they say nothing about cache or code-layout effects, but they are exact and repeatable, which the timing above is not.

| Counter over the frozen workload (bench 11, 13, 16) | lock (control rebuild) | WITNESS_NOPIN | EVADE_LEGAL | PAWN_CAPMASK | CHECKERS_KL | KING_PAWN_CACHE | BUNDLE4 | BUNDLE3 | BUNDLE |
|---|---|---|---|---|---|---|---|---|---|
| Searches entered (`Worker::search`), unchanged by design | 3,375,062 | same | same | same | same | same | same | same | same |
| Quiescence searches entered (`Worker::qsearch`), unchanged by design | 1,718,471 | same | same | same | same | same | same | same | same |
| `make_move` calls, unchanged by design | 4,006,631 | same | same | same | same | same | same | same | same |
| King-line builds (`refresh_king_lines`) | 3,923,435 | 2,445,618 (-37.7 %) | 3,987,628 (+1.6 %) | same | same | same | 2,509,811 (-36.0 %) | 3,987,628 (+1.6 %) | 2,509,811 (-36.0 %) |
| `is_legal` calls | 12,237,149 | 9,585,558 (-21.7 %) | same | same | same | same | 9,585,558 (-21.7 %) | same | 9,585,558 (-21.7 %) |
| Full king-attack tests (`square_attacked_with_occupancy`) | 3,957,588 | same | 1,416,789 (-64.2 %) | same | same | same | 1,416,789 (-64.2 %) | 1,416,789 (-64.2 %) | 1,416,789 (-64.2 %) |
| `attackers_to` calls | 7,069,190 | same | same | same | 4,086,335 (-42.2 %) | same | 3,994,640 (-43.5 %) | 3,994,640 (-43.5 %) | 3,994,640 (-43.5 %) |
| Pawn-capture loop iterations (generator, region 7) | 9,726,549 | same | same | 650,564 (-93.3 %) | same | same | 650,564 (-93.3 %) | 650,564 (-93.3 %) | 650,564 (-93.3 %) |
| Pawn captures emitted (generator, region 8), unchanged by design | 677,570 | same | same | same | same | same | same | same | same |
| Shelter, storm and open-file terms added (`evaluate_king` lambda, both colours) | 18,019,932 | same | same | same | same | 5,504,949 (-69.5 %) | same | same | 5,504,949 (-69.5 %) |

Evidence: `evidence/work_counters.tsv`; the profiles are `out\build\<tag>\m2gen\m2.profdata` on the PC.
