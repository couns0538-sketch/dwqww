# OPUS R3 report (job pack R3, Forge AL1 s198) — IN PROGRESS

Branch `opus-r3-stack` (base `d4f4312`). Machine exclusive: no (gates, self-play and NNUE training ran
throughout; my work at nice 19). No Elo claims: no gate was run.

## Status

| job | state | where |
|---|---|---|
| R3-1 integration stack | all O/C branches and every opus-sol engine feature merged (S32/S37/S04fix via `opus-r3-port-b`, S-A2/S-A4 via `opus-r3-port-c`); HardDeadline defect found by the self-play checker fixed; 500-game self-play on `330237f`: 8 of 36 configs done (all-ON variants, HardDeadline, four switches), 4000 games, 0 errors; the rest running (`opus-r3-selfplay`); a Linux copy of the checker on GitHub runners is being set up (`opus-r3-sp-linux`) to re-check the final head | `opus-r3-stack`, `opus_r3/R3-1/`, `opus_r3/R3-1_selfplay/` |
| R3-2 interaction matrix | DONE, merged (`7e0660a`): no conflicts; two silent cancels; build layout ±5% on the PC; quiet-runner repeat of the switch rows running (`opus-r3-quietnps`) | `opus_r3/R3-2/REPORT.md` |
| R3-3 gate proposals | DONE, merged | `opus_r3/R3-3/`, `F:\opus_scratch\r3\GATE_PROPOSALS.md` |
| R3-4 SPSA tool | DONE, merged (`064af73`): 20 search constants as UCI spins (identical defaults), `tools/spsa/opus_spsa*.py`, dry run with restart; no tuning session | `opus_r3/R3-4/REPORT.md`, `tools/spsa/README.md` |
| R3-5 regression test suite | DONE, merged (`7e0660a`): six new CTest entries, 12/12 planted bugs caught | `opus_r3/R3-5/REPORT.md` |
| R3-6 Lazy SMP scaling | PARTIAL (1 of 3 repetitions), merged (`1f354cc`, evidence `1f2b4fd`): one scaling bug found and fixed behind UCI `SmpHelpersPastDepth` (default off) | `opus_r3/R3-6/REPORT.md` |

## CI (GitHub `opus-ci`: release, ASan+UBSan, TSan)
| run | head | result |
|---|---|---|
| 40561969912 | `c82ccbd` (all O/C merges) | success (release 3m34s, TSan 19m13s, ASan 4m27s) |
| 40564150654 | `467a59b` (+ S14, S13, S11, S29, S41, A1, S-IT) | **failure**: two tests (S-IT, A1) still used the pre-O3 member names; caught only by the CMake build, which I had not run locally |
| 40565363595 | `2432670` (`opus-r3-cifix`: the fix on top of `467a59b`) | success (11m38s) |
| 40566615160 | `7b431d4` (+ S12, the fix, a CMake endif fix) | success (20m13s) |
| 40568162589 | `2047348` (+ S08fix, evidence) | success (19m29s) |
| 40568260400 | `opus-r3-port-b` `a06b00d` (S32, S37, S04fix on `2432670`) | success |
| 40570018288 | `opus-r3-port-c` (S-A2 behind FORGE_NNUE_INT16, S-A4 on `2432670`) | success |
| 40573865157 | `330237f` (port-b + port-c merged, HardDeadline fix) | success |
| 40578094641 | `287aa15` (+ docs, R3-3, CI hook) | success |
| 40578094685 | `287aa15`, new workflow `opus-r3-switches` (every build switch ON) | success |
| 40581146563 | `7e0660a` (+ R3-5 tests, R3-2 matrix) | running |
| 40581146586 | `7e0660a`, `opus-r3-switches` | running |
| 40583093802 / 40583093751 | `1f354cc` (+ R3-6 SmpHelpersPastDepth), opus-ci / opus-r3-switches | running |
| 40584552130 / 40584552107 | `064af73` (+ R3-4 tunables and SPSA tool; final engine head), opus-ci / opus-r3-switches | running |
Since the failure every push is preceded by a full local CMake build of all targets and the full CTest list (only
the 4 known `forge_tests` lines may fail; `check_known_failures.py` PASS), and every run is followed to green.
`opus-r3-switches` (new in R3) runs the same release/ASan/TSan evidence with every build switch ON (O2, NOZERO,
TT prefetch, SPEEDSTACK, LAZY_ACC, PROF, INT16, DATAGEN, ATTACKS_INIT_ONCE); before it went live the same
configuration passed locally (CMake all targets, uci_check --full ALL OK, CTest 49 tests, known-failure check PASS).
The failed run cannot be re-run usefully (it would rebuild the same broken commit) and runs cannot be deleted here;
every later run of the branch is green.

## R3-1 so far (logs: `opus_r3/R3-1/logs/`, scratch `F:\opus_scratch\r3\logs`)
- Base: `d4f4312` fast-forwarded to `opus-O3` (`c7eb247`: the no-op module split every O/C branch is built on,
  plus the CI baseline `0d99f02`). Then one merge commit per branch: O1-LTT (contains O1), C1, C2, C3, O7 (contains
  C4 and O6), C5, O4, O5, O8, C6, O2, the evidence-only heads of O1 and O6, then the opus-sol features S14, S13,
  S11, S29, S41, A1, S-IT, S12, S08fix (ported from the single-file search.cpp onto the module layout:
  `opus_r3/R3-1/tools/port_search_hunks.py` places each hunk whose exact context exists in one module file, the
  rest by hand; every merge commit message lists what went where).
- After every merge: PC-recipe build (0 warnings, FMA 0) and bench d11/13/16 + perft5 + kiwipete = lock: ALL OK;
  for every build switch the switch-off exe is byte-identical to the previous stack exe (PE timestamp aside).
- Each feature's ON behaviour was checked against its branch where the branch recorded numbers:
  CorrMargins d11 343365 d13 858019 d16 2522546 d20 12894582; CorrExt 312961 / 838790 / 2891507 / 12313394;
  CuckooRep 324211 / 790682 / 3148570; HistRework=1 373261 / 1043893 / 3399770, =2 320427 / 881902 / 3041041;
  node-exact features stay at the lock pins when ON (MaterialKeyTable, FORGE_SPEEDSTACK to d22, TtChildPrefetch,
  NnueLazyAcc to d20, FORGE_PROF to d22, FORGE_NNUE_O2, FORGE_NOZERO_MOVE_BUFFERS); NNUE smoke nets of C5, O6, O7, O4
  reproduce their branches' ON pins (5/5); options without recorded pins equal their own branch exe (CorrHistPlus
  1/2/4/7, NetScale 90/110, HistRework 3, Syzygy, LocklessTT: 9/9); NnueInt16 (FORGE_NNUE_INT16) reproduces S-A2's
  pins. Every build switch at once compiles with 0 warnings, FMA 0, ALL OK.
- **HardDeadline defect found and fixed** (`5792074`): after a watchdog answer the stopped search could print a late
  `info depth` line (33 in ~140 all-ON self-play games); now the watchdog closes the search output under the output
  mutex before its bestmove. The extended `hard_deadline_regression` fails on the old engine and passes on the new
  one; the self-play repro shows 0 late lines in 1100 rounds (480 watchdog answers) on the final head.
- Gate executables built from `330237f` in `F:\opus_scratch\r3\exe\` (`EXES.txt`: name, flags, sha256, ALL OK).
- Semantic merges: (1) one selection / fail-loud rule for the five NNUE v2 options (C4, C5, O4, O6, O7; each
  branch's test phrases kept); (2) one search instance per combination of CorrMargins x CorrExt x CuckooRep (8
  alpha-beta + 2 quiescence instances; a single option runs its branch's code); (3) O2 behind the new build switch
  `FORGE_NNUE_O2` (off: token-identical preprocessed nnue.cpp and byte-identical exe vs. the pre-O2 stack);
  (4) A1's joint correction also in C2's cold CorrHistPlus path, so the two combine.

## R3-3 gate proposals (agent; `opus_r3/R3-3/REPORT.md`)
- One entry per feature vs the all-OFF engine (`forge_r3_base.exe`), exes from `330237f` in `F:\opus_scratch\r3\exe\`,
  SPRT [0,5] a=b=0.05 normalized, 1500-game cap, 10+0.1, the PC book and concurrency, a new srand each;
  `GATE_ENTRIES.json` holds the 29 manifest objects ready to append (nothing was written to the queue).
- Ranked: A node-exact speed (O2, NOZERO, S13, SPEEDSTACK, LazyAcc, MaterialKeyTable), B search/eval changes,
  C SMP (the r7 runner hard-codes Threads=1: needs a runner change), D trained-net features (no net exists).
- **Owner decision needed:** by an approximate GSPRT model, [0,5] with a 1500-game cap ends "cap, no decision" for
  practically every realistic effect size (H1 needs about +50 nElo observed; a true −20 nElo regression ends H0 in
  0.4% of runs vs 62% at [0,10]). §7 of GATE_PROPOSALS.md lists the alternatives.

## R3-2 interaction matrix (agent; `opus_r3/R3-2/REPORT.md`)
- 71 configurations (every runtime option and build switch alone, TT / correction / NNUE pairs, the final-head
  features), 1152 NPS runs and 130 node-count processes, all clean. Bench nodes: identical across processes; every
  node-exact part and combination stays at the lock pins; every branch ON pin reproduces on the stack.
- **Conflicts: none. Silent cancels: two** (by design): NetScale and NnueInt16 act only on the compiled-in net, so
  with any v2 net they do nothing, without a warning (NnueInt16 even prints `NnueInt16 active`). Same for O2 and
  NnueLazyAcc (not flagged: no own tree effect).
- NPS (advisory, PC ~98% loaded, cycle-timed CPU NPS, paired ABBA, A/A control +0.06% [-0.66, +0.77]): TT pairs
  additive; correction combinations strongly sub-additive but on new trees (tree-confounded, not a code conflict);
  Threats + PawnPairs share machinery (-48.5% together vs -53.2% predicted); output buckets nearly free.
- **Build layout moves NPS by up to about ±5% on this PC** (the final head's OFF exe runs 4.6% slower than the
  first-pass OFF exe; FORGE_NOZERO_MOVE_BUFFERS -4.2%, O2 0 / +3%): switch-level NPS effects below that size are not
  attributable here. A quiet-runner repeat of the switch rows is running (`opus-r3-quietnps`).
- Tool finding: `bench` always searches with its own one-thread Searcher, so Threads options never reach bench.

## R3-4 SPSA tool (agent; `opus_r3/R3-4/REPORT.md`)
- **20 constants advertised as UCI spin options in every build**, default = the AL1 s198 value: LMR 6
  (LmrQuietBase, LmrQuietDivisor, LmrNoisyBase, LmrNoisyDivisor, LmrHistoryDivisor, LmrCutoffThreshold), null move 5
  (NullMoveBase, NullMoveDepthDivisor, NullMoveEvalDivisor, and the former literals 24 / 180 of the null-move
  static-eval margin as NullMoveMarginDepth / NullMoveMarginBase), RFP 3, futility 3, SEE 2, AspirationDelta. The
  other tunables stay unlisted (setoption accepts them; FORGE_EXPOSE_TUNABLES lists all 64).
- Defaults keep the lock: uci_check --full ALL OK on the branch and on the stack; on the pre-merged stack all 20 set
  explicitly to their defaults give the lock pins, and non-default values change the tree (e.g. NullMoveMarginBase
  150: d11 339997; with CorrMargins the default margin still gives CorrMargins' pin 343365;
  `F:\opus_scratch\r3\logs\premerge_spsa_*`). Codegen: the default `Worker::search` keeps its address and size; 12
  normalised lines differ (the two immediates became loads).
- Tool `tools/spsa/opus_spsa.py` (+ `_core`, `_fastchess`, `_uci`): Spall gains, fishtest-style update, integer
  rounding, clamping, fastchess mini-matches with W/L/D and pentanomial cross-checks, resumable state + CSV per
  iteration, Idle priority in a Windows job object. 30 unit tests in CTest (`opus_spsa_tests`,
  `opus_spsa_engine_options`), 16/16 planted bugs caught. Dry run at 0.5+0.005, concurrency 2, 3 params: stopped
  after 2 iterations and resumed at iteration 2/3. No real tuning session (by the spec).
- Findings: QsSeeMargin cannot be tuned in small steps (SEE balances are multiples of 100: margins 0-99 search the
  same tree), so LmrCutoffThreshold took its slot; fastchess `-strict` ends a whole run at the first time forfeit,
  so the tool runs without it and verifies every tuned option is applied; CaptureFutilityMultiplier is dead (0 node
  change). README estimate for a real session: 40,000 games at 8+0.08, about 32 h on 8 slots (pilot 4,000 games).

## R3-5 regression test suite (agent; `opus_r3/R3-5/REPORT.md`)
- Six new CTest entries: `forge_perft_cpw`, `forge_perft_edge` (20 positions at depth 5-7 with published counts,
  cross-checked with python-chess: 0 mismatches), `forge_draw_rules_tests` (repetition / threefold incl. GitHub
  issue #7 with IntendedThreefold off and on, 50-move rule incl. mate on the 100th half-move),
  `forge_tt_mate_tb_tests` (mate scores through the TT, TB scores with the PC tables; SKIP without tables, as on CI),
  `uci_options_regression` (data-driven over `uci`, ready for the SPSA spins), `smp_uci_regression` (Threads 2/3:
  stop, ponder/ponderhit, node/depth limits, new go/position/setoption/quit during a search).
- 12 planted one-line bugs: every one caught (14/14 guarded runs fail). opus-ci 40576759596 green on the branch.
- Findings (no engine change): an SMP search can settle on a longer (real) mate and a warm TT keeps it; UCI option
  names are case-sensitive in the engine (the protocol says they are not; GUIs send the advertised spelling).
- Merged into the stack (`2afd0365`); local CMake + full CTest on `7e0660a`: default 51 tests, all-switch 55 tests,
  only the known lines fail (plus `forge_prof_tests` at Idle priority, see below).

## R3-6 Lazy SMP scaling (agent; `opus_r3/R3-6/REPORT.md`) — PARTIAL
- 30 positions (10 opening, 12 middlegame, 8 endgame) at fixed depth 20-32 (Threads=1 2.2-7.6 s), Threads 1/2/3,
  Hash 64, fresh process per run at Idle, configs off / on (SmpExactNodes + SmpBestThread + LocklessTT) / on2 (on +
  CorrHistPlus 7, CorrMargins, CorrExt, CuckooRep, HistRework 2, MaterialKeyTable) / offP / onP (+ the fix), on the
  final engine head `330237f`. 464 runs: one full repetition plus 74 runs of a second, not the 3 asked for
  (deadline; about 8 s per run on the loaded PC). All wall numbers advisory (the engine got 0.8 / 1.4 / 2.1 CPUs).
- Stack OFF: suite time-to-depth speedup 0.95x (T2) and 1.14x (T3), node inflation 1.71x / 2.03x, NPS scaling
  1.86x / 2.43x. Helpers duplicate the main thread (same depth sequence in lockstep); at T2 the main thread still
  needs 0.80x of its single-thread nodes. Stack ON is not significantly different (wall on/off 0.84 [0.67..1.04]
  at T2, 0.97 [0.80..1.15] at T3). on2 scales better at fixed depth (1.47x / 1.94x) but its T1 search is 1.68x
  slower.
- **Bug found:** in a `go depth N` search every helper returned after completing iteration N and its core idled
  until the main thread finished N (trace build: 6.6% / 9.2% of helper time idle; 53% / 43% of helpers returned by
  themselves). **Fix:** UCI `SmpHelpersPastDepth` (default off; only Threads > 1 with `go depth`): helpers keep
  deepening until stopped and still report their depth-N result. Idle time drops to 0%, NPS +6.5% / +10.6%; a
  time-to-depth gain is not measurable on this PC (offP/off 0.99 [0.80..1.21] at T2). Option off: lock pins; on:
  bench pins, hot code instruction-identical. CTest checks + planted bugs (M1 5/5, M2 5/5, M3 4/5); CI green.
- Checked without finding a bug: stop/join latency (median 0.1-1.2 ms), reported nodes (= per-worker sum), T3 vs T2,
  TT pressure, locked vs lockless TT on Windows. Proposed follow-up: depth diversification for helpers (needs an
  SMP gate). Not done: Threads > 3 (PC rule), larger Hash, the remaining 2 repetitions.

## Notes for the owner
- Load-sensitive tests on this PC (pass on the CI runners): `forge_smp_tests` (SmpExactNodes overshoot bound; port-b
  agent: 7/20 failures at nice 19) and `forge_prof_tests` (FORGE_PROF builds only: each of 4 workers must count >0
  nodes in a depth-9 search; 7/10 failures at nice 19 on the saturated PC, 3/3 passes at normal priority; on
  `7e0660a` 4/5 failures at Idle and 8/8 passes at BelowNormal, `F:\opus_scratch\r3\logs\prof_tests_priority_7e0660a5.txt`).
  Not regressions of the stack; not changed.
- Silent cancels (R3-2): setting NetScale or NnueInt16 while a v2 net is loaded has no effect and no warning. A
  one-line `info string` warning would be the natural fix; not done here (it changes UCI output).
- Sol leftovers: all done in earlier rounds (`SOL_LEFTOVERS_PROGRESS.md` on `opus-summary`) except the S09fix
  DirectML optimizer check (S09-5), still UNVERIFIED: the read-only venv now has `torch_directml` 0.2.5.dev240914 and
  the PC has an RX 7900 XT, but the GPU runs production NNUE training, so I did not run anything on it. The check is
  5 in-memory optimizer steps; its CPU proxy (PASS) is in `forge_sol_S09_holdout_validate_v2.py` on `opus-sol-S09fix`
  (`opus_round1/sol_S09fix/`). Run it on the GPU when the GPU is free.
- Rule slip by the R3-4 agent: one stray 3.6 KB test-output copy on C:
  (`C:\Users\Administrator\AppData\Local\Temp\r35.out`, from a `cp` to `/tmp`); left in place (no deletions).
- Four Python bytecode files entered the stack with the S08fix merge commit `9588a10` (CTest runs the tools with the
  system Python, which writes `__pycache__` into the tree): `tools/__pycache__/uci_regression.cpython-314.pyc`,
  `tools/match/__pycache__/{pgn_stats,run_match,windows_validate}.cpython-314.pyc`. Untracking them was not permitted
  here (no deletions); a `.gitignore` now keeps new ones out. Please `git rm --cached` them when convenient.

## Left
- R3-1: the 500-game self-play evidence on `330237f` (28 of 36 configurations still running, ETA about 00:20); the
  Linux re-check of the final head on GitHub runners (`opus-r3-sp-linux`).
- R3-4 (SPSA) and R3-6 (SMP scaling, fix `SmpHelpersPastDepth`): agents finishing; then merge, full local CMake +
  CTest, push, CI green.
- R3-2 follow-up: quiet-runner NPS of the switch rows (`opus-r3-quietnps`).
