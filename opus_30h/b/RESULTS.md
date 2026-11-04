# Item B - SPSA tuner and exposed search constants - RESULTS

No Elo claim: the crew gates (UHO [0,5] SPRT, 8moves_v3 confirm). Own games are tuning only.

## Options (step B.2)
- The lock exe FD3A5190 (kit -Expose) already advertises 41 search constants + 10 time-management constants at the
  lock's own values (`uci_options`, 2026-11-03 15:5x): LmrQuietBase, LmrQuietDivisor, LmrNoisyBase, LmrNoisyDivisor,
  NullMoveMinDepth, NullMoveBase, NullMoveDepthDivisor, NullMoveEvalDivisor, RfpDepth, RfpMargin, RfpImproving,
  RazorDepth, RazorBase, RazorMultiplier, FutilityDepth, FutilityBase, FutilityMultiplier, LmpBase, HistoryPruneDepth,
  HistoryPruneMultiplier, SeeQuietMultiplier, SeeNoisyMultiplier, SingularDepth, SingularMargin, IirDepth, ProbcutDepth,
  ProbcutMargin, QsFutilityMargin, QsSeeMargin, AspirationDelta, HistoryBonusQuadratic, HistoryBonusLinear,
  HistoryBonusMax, LmrHistoryDivisor, CheckExtensionDepth, LmrCutoffThreshold, MaterialCorrectionWeight,
  CaptureFutilityBase, CaptureFutilityMultiplier, CaptureFutilityDepth, FailLowContinuationBonus.
- New: `opus_30h/b/o30_expose.py` exposes 22 more (18 anchored edits in src/search.cpp, the literal sites R9 proved
  identical; no switch: each option's default is the literal it replaces): NmpEvalDepthMargin 24, NmpEvalBase 180,
  NullMoveEvalMax 3, NullMoveVerifyDepth 14, ProbcutImproving 50, ProbcutReduction 4, SingularTtDepth 3,
  SingularDoubleMargin 24, SingularDoubleLimit 6, LmrTtPv / LmrNotImproving / LmrTtCapture / LmrGivesCheck / LmrInCheck /
  LmrCutoffCount 1024 and LmrCutNode 2048 (LMR adjustments in 1/1024 ply), HistoryMalusPercent 100,
  HistoryDepthBonusMargin 100, AspirationMinDepth 4, AspirationGrowPercent 50, AspirationGrowAdd 4, QuietCheckBonus 12000.
  Patch `opus_30h/b/expose22.patch` md5 73cd35917a872d2a00b8ce6219d6f7d7.
| check | result |
|---|---|
| plain build `D:\o30\plain\spsa_1\forge_plain.exe` (sha256 3e8cf18f03506b2c33c688355ad43458bafcf7c534c02bbff96499a871522e5a) | 0 warnings, vfmadd 0 |
| defaults = lock: pin_check -Full | PASS d11 312866 / d13 862329 / d16 3024920 / d20 12389307 / d22 34048354, perft 4865609 / 193690690 |
| each new option moved once (pin_check ON mode, d11/d13/d16 must differ) | 22 / 22 LIVE (LmrNotImproving and LmrInCheck were dead at half-ply values 1536 / 512 - the other LMR terms are whole plies, so a lone half ply rounds away - and LIVE at whole-ply values 2048 / 0) |

## Tuner (tune_spsa.py) - port of R9's r9_spsa.py, what changed and why
- Parameter list from a CSV (name,start,min,max,c,a) instead of the JSON list; c = c_end, a = r_end (R9's names).
- Options go straight to the engine (`option.Name=V`); R9's `R9Tune=true` switch is gone (the exe has no switch).
- CPU control: pin to a CPU list at Idle (children inherit); per batch: wait while a fastchess the tuner did not start
  overlaps its CPUs (a running gate), wait while RAM < 6 GB, then one game slot per CPU at most max_busy_percent busy
  (default 80: the npt trainer keeps CPUs 0-3 at ~50-60 %; a first 50 % threshold starved the tuner), never above
  --threads (<= 8). R9's whole-PC load cap (70-90 %) is gone: the PC sits at ~85 % with the crew's gates alone.
- Stop: --until (date + time), --max-pairs, --total-pairs, or the stop command (named event; no STOP files).
- Same math (checked line by line against R9): c_i = c_end * N^gamma, a_i = r_end * c_end^2 * (A + N)^alpha,
  c_k = c_i / (k+1)^gamma, a_k = a_i / (k+1+A)^alpha, theta += a_k / c_k * (W - L) * delta, clamped; the same
  append-only iterations.jsonl / history.csv and torn-line handling.

### Review R-B1 (structured self-review, NOT independent; 2026-11-03 19:0x)
- Ranges: every CSV range lies inside the engine's advertised option range (LmrQuietBase 0-300, LmrQuietDivisor
  100-500, LmrCutNode 0-6144, HistoryMalusPercent 0-300, NmpEvalBase -200-600, RfpMargin 10-300, SeeQuietMultiplier
  0-200, SingularDoubleMargin 0-200), so the engine never clamps a value the tuner believes it sent.
- c_end >= 5 everywhere, so plus and minus never round to the same integer.
- Found: own sanity matches (fastchess) on the tuner's CPUs make it wait (by design: they look like a gate) - run them on
  CPUs outside the tuner's list (resume with --cpus). Not a bug; recorded in the README's CPU section.

## One switch for the tuned set: O30Tuned (prepared 2026-11-03 20:2x; built with the real values at the end)
- `b/o30_tuned_patch.py --tuned <TUNED_OPTIONS.txt> --params <run params.csv> --repo <expose22 scratch repo>`: three
  anchored edits in src/uci.cpp - a table (name, lock value, tuned value), `option name O30Tuned type check default
  false` next to the tunables, and a setoption handler (true = the tuned values, false = the lock values, each clamped
  to its option range, then tune::refresh()). Refuses a tree that already has it, a name that is not a tune parameter
  of the tree, a value outside the CSV range.
- `b/test_o30tuned.sh <exe> <TUNED_OPTIONS.txt> [mask]`: 1 OFF pins -Full, 2 O30Tuned=true bench == the explicit option
  list's bench (and differs from the lock), 3 true then false = the lock pins, 4 advertised + an invalid value rejected.
- Dry run with a DUMMY set (8 values moved by hand; scratch clone `D:\o30\repos\spsa_tunedtest` 2da9756, plain build
  `D:\o30\plain\tunedtest_1\forge_plain.exe` sha256 14abbbc15fcaa83e51654b5e92dd6166606d5f76da87ebf84ceb163b2297561d,
  0 warnings, vfmadd 0): O30TUNED PASS - 1 PASS; 2 PASS (d11 373948 / d13 1042797 / d16 2580989 both ways); 3 PASS; 4 PASS.

## SPSA pre-flight (2026-11-03 20:4x)
The 8 stc8 options at their start values on the SPSA exe 7bf5dab3: every name advertised with the CSV's range inside
the option range, bench d11 / d13 / d16 = the lock pins (pin_check -Expect PASS) - the tuner's first batch starts from
exactly the lock.

## Inventory of the 41 constants the lock already advertises (plan B.1; `b/option_inventory.py`, lock exe, 20:5x-21:0x)
Every option set explicitly to its default gives the lock pin (41 / 41). Moved by +-25 % (or +-1): 37 change bench d11
at once. The other four: HistoryPruneDepth moves bench d13 (2: 862,381 vs 862,329); CaptureFutilityMultiplier /
CaptureFutilityDepth act only when the feature is on (CaptureFutilityBase 0 = off by default; with Base 50: 312,043,
+ Multiplier 300: 312,256, + Depth 8: 312,038); QsSeeMargin is live only in steps of the exchange values it is compared
with (`see_ge(move, -QsSeeMargin)`, piece-value units): 0 and 40 give the same search, 200 -> 350,185, 1000 -> 429,577
nodes - a tuner with a small c on it would only see noise. Evidence `D:\o30\logs\option_inventory_lock.txt`.
Option lists (`uci`, sorted): gate exe ff856ba8 = the lock's 61 options + EvalFileV2; SPSA exe 7bf5dab3 = the lock's
61 + 22 (none removed); the O30Tuned test build = the SPSA exe's + O30Tuned.

## SPSA simulation test (plan B.3's sim tests; `b/sim/test_spsa_sim.py`, 2026-11-03 21:0x)
The real tuner against a FAKE fastchess (`b/sim/fake_fastchess.bat` -> `fake_fastchess.py`) whose games follow a model
with a known optimum (A = 160 / scale 40, B = 20 / scale 10, Elo = -60 * sum of squared scaled distances; outcomes
seeded by the command line). Start A = 100, B = 60, 10 pairs per batch, 1,000 pairs: A -> 148.0, B -> 21.1 (distances
60 -> 12.0 and 40 -> 1.1); resumed for 200 more pairs: records = history rows (120), k contiguous, batch numbers
0..119, A 152.4, B 21.0. SPSA SIM PASS. This exercises what real short games cannot show through their noise: the sign
of W - L (a win counts for the engine named plus, which plays theta + c * delta), the option values on the command
line, the PGN parsing, the schedule and the resume. Side finding: a first try on CPU 1 waited correctly on the n2e
match's fastchess (the gate-overlap check, live) and was stopped through the stop event.

## Tuned exe for the stc8_main session at 184 pairs (tag tuned184; built 2026-11-04 13:40:43 - 13:44:34, checks to 13:47:31)
No Elo claim, no convergence claim: 184 of 1800 planned pairs (92 batches, 368 games, +88 -77 =203, draw rate 55.2 %),
only SeeQuietMultiplier beyond 2 sigma of the null-gradient noise (24 -> 28, z +2.11; with 8 parameters about 0.4 pass
by chance); report `D:\o30\spsa\report_184pairs\REPORT.md`. The crew gates.
- `build_o30tuned.sh D:\o30\spsa\report_184pairs\TUNED_OPTIONS.txt D:\o30\spsa\stc8_main tuned184` (log
  `D:\o30\logs\build_o30tuned_tuned184.out`): clone of the expose22 repo (deabbd2) -> `D:\o30\repos\tuned184`
  (574b018), patch `b/o30tuned_tuned184.patch` md5 eaa42c9fb3806a884c46a6f635548b93 (cleanroom_lint CLEAN), kit v2.3 -Expose on
  CPUs 0-1 at Idle, pc1 + pc2.
- Exe `D:\o30\w\tuned184_pc1\src_copy\forge_ltopgo_tuned184_pc1.exe` sha256 3b35f5cfa662f4f09916fa9c4b40f6bfc6a6d0d4ce7fa1f1b8f6970daadb66d1 = pc2 (binding);
  kit pc1 / pc2 RESULT PASS (OFF pins d11-d22 + perft, node identity plain = ltopgo ALL OK, real missing-profile / coverage warnings 0, vfmadd 0); `uci` = the SPSA exe 7bf5dab3's option list + O30Tuned.
- The set (O30Tuned=true): LmrQuietBase 85 -> 80, LmrQuietDivisor 220 -> 215, LmrCutNode 2048 -> 2038,
  HistoryMalusPercent 100 -> 99, NmpEvalBase 180 -> 174, RfpMargin 72 -> 65, SeeQuietMultiplier 24 -> 28,
  SingularDoubleMargin 24 -> 25 (false = the lock values; untouched = the expose22 exe).
| check | result |
|---|---|
| kit pc1 / pc2: OFF pins d11-d22 + perft, node identity plain = ltopgo | RESULT PASS / RESULT PASS (sha256 identical) |
| test_o30tuned.sh 1 OFF pins -Full | PASS |
| 2 O30Tuned=true == explicit list, differs from the lock | PASS (d11 330152 / d13 745986 / d16 2436337 both ways; lock 312866 / 862329 / 3024920) |
| 3 true then false = the lock pins | PASS |
| 4 advertised + invalid value rejected | PASS |
| UCI conformance (tools/uci_conformance_o30.py, CPU 1): switch untouched / O30Tuned=true | PASS 18 / 18 / PASS 21 / 21 |
| smoke2m 120 s, O30Tuned=true, Threads 2, Hash 16, tc 2000+20, engine-side legality (CPU 1) | SMOKE2M PASS: 21 games (20 finished), 2450 plies, 0 illegal / crashes / hangs / time losses / overruns / option errors, stderr empty |

Evidence: `D:\o30\checks_itemB\` (prep, waiter, option-list diff, conformance, smoke). Gate line: engine A = the exe
above with `option.O30Tuned=true`; engine B = the lock FD3A5190 (no options); UHO [0,5] SPRT, then the 8moves_v3
confirm. The same set without a new exe: the SPSA exe 7bf5dab3 with the explicit list in
`D:\o30\spsa\report_184pairs\gate_options.txt` (check 2: bench(switch) == bench(list)).
Full report of this step: `opus_30h/b/logs/itemB/ITEM_B_REPORT.md` (copies of the evidence beside it).
