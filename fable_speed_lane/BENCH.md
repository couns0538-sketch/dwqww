# BENCH: identity evidence and indicative timing

Generated 2026-11-10 11:46 Vienna by `tools/collect_evidence.py` from the files under `evidence/` (copied from `D:\forge_jobs_20261109\fable2\out\id`). All runs: CPU 3 only (mask 0x08), Idle priority, one process at a time, while the crew's gates ran on other cores. Lock = combo29 exe `e1284f7f...8802e`.

## 1. Lock reference rows

| Item | Result | File |
|---|---|---|
| 12 pins on the lock copy | 12/12 | `evidence/lock/pins.json` |
| Cold rows net on | not run | |
| Cold rows net off | not run | |
| Warm transcript | sha256 `30d5e06484abb5a3c962f4aade7a4d94b5a1bedfcd3c5b080d82d5d9fd10ad52` | `evidence/lock/warm.txt` |
| Perft set | PASS | `evidence/lock/perftset.json` |

## 2. Identity ladder

Switch 0 = the patch applied, switch left at its default. `89 / 0` = 89 differing bytes inside the debug record (PDB hash and path), 0 differing bytes anywhere else: code and data bytes identical to the lock; sha256 identity UNRESOLVED (debug record only), see STATUS.md.

| Check | WITNESS_NOPIN | EVADE_LEGAL | PAWN_CAPMASK | CHECKERS_KL | KING_PAWN_CACHE | BUNDLE4 | BUNDLE |
|---|---|---|---|---|---|---|---|
| Status | LISTED-UNBUILT | LISTED-UNBUILT | UNLISTED | LISTED-UNBUILT | not new (built before, DUPCHECK.md); extra | the four new candidates | BUNDLE4 + KING_PAWN_CACHE; extra |
| Patch md5 | `ccfa6ce5...` | `b5aaa89f...` | `2a680e14...` | `c8f080ba...` | `a51e1b69...` | `4cfedef4...` | `953ee65a...` |
| Switch 0 vs lock, bytes (debug / other) | 89 / 0 | 89 / 0 | 89 / 0 | 89 / 0 | 89 / 0 | 89 / 0 | 89 / 0 |
| Switch 1, 12 pins | 12/12 | 12/12 | 12/12 | 12/12 | 12/12 | 12/12 | 12/12 |
| Harness, 12,000 FENs, switch 1 | PASS: 12000 FENs, transcript equal to base True, 0 self-check failures | PASS: 12000 FENs, transcript equal to base True, 0 self-check failures | PASS: 12000 FENs, transcript equal to base True, 0 self-check failures | PASS: 12000 FENs, transcript equal to base True, 0 self-check failures | PASS: 12000 FENs, transcript equal to base True, 0 self-check failures | PASS: 12000 FENs, transcript equal to base True, 0 self-check failures | PASS: 12000 FENs, transcript equal to base True, 0 self-check failures |
| Harness, 12,000 FENs, verify build (=2) | PASS: 12000 FENs, exit 0 (no abort), transcript equal True | PASS: 12000 FENs, exit 0 (no abort), transcript equal True | not run | PASS: 12000 FENs, exit 0 (no abort), transcript equal True | not run | PASS: 12000 FENs, exit 0 (no abort), transcript equal True | PASS: 12000 FENs, exit 0 (no abort), transcript equal True |
| Harness, targeted positions, switch 1 | PASS: 24 FENs, transcript equal to base True, 0 self-check failures | PASS: 24 FENs, transcript equal to base True, 0 self-check failures | PASS: 24 FENs, transcript equal to base True, 0 self-check failures | PASS: 24 FENs, transcript equal to base True, 0 self-check failures | PASS: 24 FENs, transcript equal to base True, 0 self-check failures | PASS: 24 FENs, transcript equal to base True, 0 self-check failures | PASS: 24 FENs, transcript equal to base True, 0 self-check failures |
| Harness, targeted positions, verify build (=2) | PASS: 24 FENs, exit 0 (no abort), transcript equal True | PASS: 24 FENs, exit 0 (no abort), transcript equal True | not run | PASS: 24 FENs, exit 0 (no abort), transcript equal True | not run | PASS: 24 FENs, exit 0 (no abort), transcript equal True | PASS: 24 FENs, exit 0 (no abort), transcript equal True |
| Verify engine, 12 pins | PASS: 12/12 | PASS: 12/12 | not run | PASS: 12/12 | not run | PASS: 12/12 | PASS: 12/12 |
| Verify engine, cold 12,000 net on | not run | not run | not run | not run | not run | not run | not run |
| Cold 12,000, depth 13, net on | not run | not run | not run | not run | not run | not run | not run |
| Cold 12,000, depth 13, net off | not run | not run | not run | not run | not run | not run | not run |
| Warm session transcript | PASS: transcript equal True, 1004 searches, bench 13 = 862329 | PASS: transcript equal True, 1004 searches, bench 13 = 862329 | PASS: transcript equal True, 1004 searches, bench 13 = 862329 | PASS: transcript equal True, 1004 searches, bench 13 = 862329 | PASS: transcript equal True, 1004 searches, bench 13 = 862329 | PASS: transcript equal True, 1004 searches, bench 13 = 862329 | PASS: transcript equal True, 1004 searches, bench 13 = 862329 |
| Threads 2-4 soak | PASS: 60/60 legal, T1 tail 50/50 | PASS: 60/60 legal, T1 tail 50/50 | PASS: 60/60 legal, T1 tail 50/50 | PASS: 60/60 legal, T1 tail 50/50 | PASS: 60/60 legal, T1 tail 50/50 | PASS: 60/60 legal, T1 tail 50/50 | PASS: 60/60 legal, T1 tail 50/50 |
| Perft set (6 positions) | PASS: 6/6 | PASS: 6/6 | PASS: 6/6 | PASS: 6/6 | PASS: 6/6 | PASS: 6/6 | PASS: 6/6 |

"not run" in a verify row of `PAWN_CAPMASK` or `KING_PAWN_CACHE` means the patch has no verify mode. The verify engine was run over the cold set for the bundles only (all verify modes on at once). A verify build of `WITNESS_NOPIN` still asks the legality test it would skip, which builds the king lines; verify builds therefore take the `CHECKERS_KL` shortcut in a superset of the shipped mode's cases.

Base harness transcript (lock source, 12,000 FENs): sha256 `b7e28032cd6646459417c2aecc0c3435663fff4b6ae59240f3eb04cb70570059`.

## 3. INDICATIVE timing (not the ABBA)

Lock exe (A) against the switch-1 exe (B), Threads 1, Hash 16, fresh engine per arm, warm `bench 13`, timed `bench 20`, ABBA blocks (count per row), ratio per block = sqrt(B1*B2 / (A1*A2)). **Wall** = nodes per wall second. **Cycles** = nodes per CPU cycle of the engine process (QueryProcessCycleTime), which preemption by other jobs does not inflate. Positive = B faster. These numbers come from one shared CPU at Idle priority; they cannot prove a gain under 1 % and they are not QA's quiet ABBA. Section 5 gives exact, load-independent counters of the work each switch removes.

| Pair | Net | Wall median | Wall IQR | Wall min .. max | Cycles median | Cycles IQR | Cycles min .. max | Blocks | Folder |
|---|---|---|---|---|---|---|---|---|---|
| A/A (lock vs lock) | on | +1.41 % | -2.79 .. +4.52 | -5.59 .. +7.00 | +0.25 % | -0.71 .. +1.55 | -1.99 .. +2.33 | 10 | `evidence/AA_lock_vs_lock/abba_d20_on_013918` |
| A/A (lock vs lock) | off | not run | | | | | | | |
| BUNDLE4 | on | not run | | | | | | | |
| BUNDLE4 | off | not run | | | | | | | |
| BUNDLE | on | not run | | | | | | | |
| BUNDLE | off | not run | | | | | | | |
| WITNESS_NOPIN | on | not run | | | | | | | |
| WITNESS_NOPIN | off | not run | | | | | | | |
| EVADE_LEGAL | on | not run | | | | | | | |
| EVADE_LEGAL | off | not run | | | | | | | |
| PAWN_CAPMASK | on | not run | | | | | | | |
| PAWN_CAPMASK | off | not run | | | | | | | |
| CHECKERS_KL | on | not run | | | | | | | |
| CHECKERS_KL | off | not run | | | | | | | |
| KING_PAWN_CACHE | on | not run | | | | | | | |
| KING_PAWN_CACHE | off | not run | | | | | | | |

## 4. Mutants: would the harness notice a wrong patch?

`tests/mutants.ps1` plants one wrong change per run, builds the harness on it and runs the targeted positions and the first 300 FENs. CAUGHT = transcript differs, a self-check fails, or a verify build aborts. Each tree is first run unchanged with the same switches (control) and must be clean.

| Tree | Mutant | Planted change | Verdict | Where |
|---|---|---|---|---|
| (MUTANTS.log) | not run | | | |
| (MUTANTS_BUNDLE4.log) | not run | | | |
| (MUTANTS_BUNDLE.log) | not run | | | |

Controls (the unchanged tree with the same switches):

| Tree | Switches | Result | Sets |
|---|---|---|---|

Evidence: `evidence/mutants/`.

## 5. Exact work counters: what each switch removes

Not a timing. Every lock-recipe build has an instrumented first stage that runs the frozen workload (bench 11, 13 and 16; 4,200,115 nodes in every build, since all builds are node-identical). Its profile holds an exact counter per source function and per source region. The table compares those counters between the control rebuild of the lock source and each switch-1 build (`tools/work_counters.py`). "same" = equal to the lock's count. Counters measure work removed, not time gained: they say nothing about cache or code-layout effects, but they are exact and repeatable, which the timing above is not.

| Counter over the frozen workload (bench 11, 13, 16) | lock (control rebuild) | WITNESS_NOPIN | EVADE_LEGAL | PAWN_CAPMASK | CHECKERS_KL | KING_PAWN_CACHE | BUNDLE4 | BUNDLE |
|---|---|---|---|---|---|---|---|---|
| Searches entered (`Worker::search`), unchanged by design | 3,375,062 | same | same | same | same | same | same | same |
| Quiescence searches entered (`Worker::qsearch`), unchanged by design | 1,718,471 | same | same | same | same | same | same | same |
| `make_move` calls, unchanged by design | 4,006,631 | same | same | same | same | same | same | same |
| King-line builds (`refresh_king_lines`) | 3,923,435 | 2,445,618 (-37.7 %) | 3,987,628 (+1.6 %) | same | same | same | 2,509,811 (-36.0 %) | 2,509,811 (-36.0 %) |
| `is_legal` calls | 12,237,149 | 9,585,558 (-21.7 %) | same | same | same | same | 9,585,558 (-21.7 %) | 9,585,558 (-21.7 %) |
| Full king-attack tests (`square_attacked_with_occupancy`) | 3,957,588 | same | 1,416,789 (-64.2 %) | same | same | same | 1,416,789 (-64.2 %) | 1,416,789 (-64.2 %) |
| `attackers_to` calls | 7,069,190 | same | same | same | 4,086,335 (-42.2 %) | same | 3,994,640 (-43.5 %) | 3,994,640 (-43.5 %) |
| Pawn-capture loop iterations (generator, region 7) | 9,726,549 | same | same | 650,564 (-93.3 %) | same | same | 650,564 (-93.3 %) | 650,564 (-93.3 %) |
| Pawn captures emitted (generator, region 8), unchanged by design | 677,570 | same | same | same | same | same | same | same |
| Shelter, storm and open-file terms added (`evaluate_king` lambda, both colours) | 18,019,932 | same | same | same | same | 5,504,949 (-69.5 %) | same | 5,504,949 (-69.5 %) |

Evidence: `evidence/work_counters.tsv`; the profiles are `out\build\<tag>\m2gen\m2.profdata` on the PC.
