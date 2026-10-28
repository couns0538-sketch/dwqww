# OPUS R3 report (job pack R3, Forge AL1 s198) — DONE

Branch `opus-r3-stack` (base `d4f4312`). Machine exclusive: no (gates, self-play and NNUE training ran
throughout; my work at nice 19). No Elo claims: no gate was run.

## Summary
- **Stack:** `opus-r3-stack`, final engine head `064af73` (later commits are reports and evidence only). Every
  O/C feature, every opus-sol engine feature and the R3 additions are in, each behind a default-off UCI option or
  build switch (`opus_r3/R3-1/OPTIONS.md`). All off: bench d11/13/16/20/22 = 312866 / 862329 / 3024920 / 12389307 /
  34048354, perft5 4865609, kiwipete 193690690 (ALL OK, also with every build switch compiled in); CTest PASS;
  GitHub CI green for opus-ci and the every-switch workflow on the final head.
- **R3-1 self-play** (500 games per option ON alone and all ON): PC 36/36 configs and Linux 36/36 configs, 0
  crashes, illegal moves or double bestmoves; ASan/TSan self-play clean; the options added on the final head:
  Linux and PC clean (4 x 500 games each on `064af73`).
- **R3-2** no option conflicts; two silent cancels (NetScale / NnueInt16 under a v2 net). Switch-level NPS on the
  PC is dominated by code layout (+-5%); on quiet runners O2's AVX2 kernels (+3%), SPEEDSTACK (+0.5%) and
  NOZERO (+1.6%) are real, the PC's NOZERO -4% / LAZY +4% / INT16 +2% are layout (R3-2Q).
- **R3-3** 29 gate entries ready (nothing queued); [0,5] with a 1500-game cap almost always ends at the cap.
- **R3-4** 20 search constants as UCI spins (defaults identical) + SPSA tool with dry run; no tuning run.
- **R3-5** perft (20 positions), draw rules incl. GitHub issue #7, 50-move, mate/TB in TT, SMP stop/ponder and
  UCI option tests in CTest and CI; 12/12 planted bugs caught.
- **R3-6** scaling measured (PC + 3 quiet-runner repetitions); helpers idle at a `go depth` limit, switchable via
  `SmpHelpersPastDepth`, but that gives no time-to-depth gain (slower with the SMP options), so it stays off.

## Owner decisions / to do
1. Gates: `F:\opus_scratch\r3\GATE_PROPOSALS.md` is ready to queue; decide the SPRT bounds first ([0,5] with
   a 1500-game cap almost never decides; alternatives in its section 7). For the node-exact speed entries, the
   PC exes carry layout shifts (R3-2Q), and O2's kernels are not compiled in the znver5 recipe.
2. `git rm --cached` the 8 tracked `.pyc` files (list under Notes); I may not delete.
3. S09fix DirectML optimizer check when the GPU is free (Notes).
4. Optional small fixes, not done: an `info string` warning when NetScale / NnueInt16 is set under a v2 net;
   case-insensitive UCI option names (R3-5 finding; GUIs send the advertised spelling).
5. SPSA: a real session needs a pilot (about 4,000 games) and then about 40,000 games at 8+0.08 on 8 slots
   (`tools/spsa/README.md`); not started (spec: no real tuning).

## Status

| job | state | where |
|---|---|---|
| R3-1 integration stack | DONE: every O/C branch, every opus-sol engine feature and the R3 jobs merged, each behind its own default-off option or switch; final engine head `064af73`: lock pins ALL OK (default and every switch), CTest PASS, CI green; self-play 500 games per option ON alone and all ON: PC 36/36 configs (18000 games) and Linux 36/36 (18000 games + 1100 under ASan/TSan) with 0 errors; the options added after `330237f` checked on `064af73` (Linux 2000 + 200 TSan games and PC 2000 games, 0 errors) | `opus-r3-stack`, `opus_r3/R3-1/`, `opus_r3/R3-1_selfplay/`, `opus_r3/R3-1L/` |
| R3-2 interaction matrix | DONE, merged (`7e0660a`): no conflicts; two silent cancels; build layout ±5% on the PC, confirmed by the quiet-runner repeat R3-2Q (DONE, merged) | `opus_r3/R3-2/REPORT.md`, `opus_r3/R3-2Q/REPORT.md` |
| R3-3 gate proposals | DONE, merged | `opus_r3/R3-3/`, `F:\opus_scratch\r3\GATE_PROPOSALS.md` |
| R3-4 SPSA tool | DONE, merged (`064af73`): 20 search constants as UCI spins (identical defaults), `tools/spsa/opus_spsa*.py`, dry run with restart; no tuning session | `opus_r3/R3-4/REPORT.md`, `tools/spsa/README.md` |
| R3-5 regression test suite | DONE, merged (`7e0660a`): six new CTest entries, 12/12 planted bugs caught | `opus_r3/R3-5/REPORT.md` |
| R3-6 Lazy SMP scaling | DONE with the quiet-runner repeat R3-6Q (3 repetitions, merged): helpers idling at a `go depth` limit found and switchable via UCI `SmpHelpersPastDepth` (default off), but the switch gives no time-to-depth gain (slower with the SMP options on), so it stays off | `opus_r3/R3-6/REPORT.md`, `opus_r3/R3-6Q/REPORT.md` |

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
| 40581146563 | `7e0660a` (+ R3-5 tests, R3-2 matrix) | success |
| 40581146586 | `7e0660a`, `opus-r3-switches` | success |
| 40583093802 / 40583093751 | `1f354cc` (+ R3-6 SmpHelpersPastDepth), opus-ci / opus-r3-switches | success / success |
| 40584552130 / 40584552107 | `064af73` (+ R3-4 tunables and SPSA tool; **final engine head**), opus-ci / opus-r3-switches | success / success |
Since the failure every push is preceded by a full local CMake build of all targets and the full CTest list (only
the 4 known `forge_tests` lines may fail; `check_known_failures.py` PASS), and every run is followed to green.
`opus-r3-switches` (new in R3) runs the same release/ASan/TSan evidence with every build switch ON (O2, NOZERO,
TT prefetch, SPEEDSTACK, LAZY_ACC, PROF, INT16, DATAGEN, ATTACKS_INIT_ONCE); before it went live the same
configuration passed locally (CMake all targets, uci_check --full ALL OK, CTest 49 tests, known-failure check PASS).
The failed run cannot be re-run usefully (it would rebuild the same broken commit) and runs cannot be deleted here;
every later run of the branch is green.

## R3-1 integration stack (logs: `opus_r3/R3-1/logs/`, scratch `F:\opus_scratch\r3\logs`)
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
- **Self-play acceptance** (no crash, no illegal move, no double bestmove; 500 fast games per config; checker
  `opus_r3/R3-1_selfplay/opus_selfplay_check.py`: python-chess legality of every bestmove / ponder / PV move, an
  isready barrier after every `position`, crash / hang / malformed-output / late-output checks; self-test 20/20
  planted protocol faults reported):
  - PC, engine `330237f` (every runtime option ON alone, every build switch ON alone, 3 all-ON variants): 36/36
    configs, 18000 games, 1869703 plies, 0 errors; 3040 HardDeadline watchdog answers, 0 late lines
    (`opus_r3/R3-1_selfplay/REPORT.md`).
  - Linux on GitHub runners (same checker, CMake g++-14 builds; `opus_r3/R3-1L/REPORT.md`): 36/36 configs,
    18000 games, 0 errors; all-ON under ASan+UBSan (2 x 250 games, 1432 watchdog answers) and every Threads=2
    config under TSan (6 x 100 games): 0 errors, 0 sanitizer reports.
  - Final engine head `064af73`, the options added after `330237f` (SmpHelpersPastDepth alone and in all-ON, the
    20 R3-4 spins at +10% / -10%): Linux 4 x 500 games + TSan 2 x 100, 0 errors (run 40585589600).
  - The same 4 configs on the PC with the final head's PC builds: 4 x 500 games, 201275 plies, 0 errors, 45
    watchdog answers, 0 late lines (`opus_r3/R3-1_selfplay/logs/final_064af732/`).
  - The checker found one real defect on the way (HardDeadline printed search output after the watchdog's
    bestmove: 122 late lines in 500 all-ON games on `2432670`), fixed in `5792074` (see above).
- Semantic merges: (1) one selection / fail-loud rule for the five NNUE v2 options (C4, C5, O4, O6, O7; each
  branch's test phrases kept); (2) one search instance per combination of CorrMargins x CorrExt x CuckooRep (8
  alpha-beta + 2 quiescence instances; a single option runs its branch's code); (3) O2 behind the new build switch
  `FORGE_NNUE_O2` (off: token-identical preprocessed nnue.cpp and byte-identical exe vs. the pre-O2 stack);
  (4) A1's joint correction also in C2's cold CorrHistPlus path, so the two combine.

## R3-3 gate proposals (agent; `opus_r3/R3-3/REPORT.md`)
- One entry per feature vs the all-OFF engine (`forge_r3_base.exe`), exes from `330237f` in `F:\opus_scratch\r3\exe\`,
  SPRT [0,5] a=b=0.05 normalized, 1500-game cap, 10+0.1, the PC book and concurrency, a new srand each;
  `GATE_ENTRIES.json` holds the 29 manifest objects ready to append (nothing was written to the queue).
- The gate exes stay valid for the final head `064af73`: after `330237f` the stack only added default-off
  options (SmpHelpersPastDepth, acts only on `go depth` with Threads > 1) and the 20 spins with unchanged
  defaults (lock pins ALL OK); no merged feature's code changed.
- Caveat for the class-A (node-exact speed) entries from R3-2 / R3-2Q: in the PC lock recipe (znver5, AVX-512)
  O2's AVX2 kernels are compiled out, so an O2 gate on PC exes tests the build without its kernels; and the
  NOZERO / LAZY / INT16 switch exes carry PC code-layout shifts of 2-5% NPS that quiet runners do not show.
  A speed gate on these exes measures the layout of that particular binary as much as the feature.
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

## R3-2Q quiet-runner NPS of the build switches (agent; `opus_r3/R3-2Q/REPORT.md`)
- Paired ABBA CPU-time NPS of every switch vs the OFF build of the same commit on GitHub ubuntu-24.04 runners (CI
  recipe, g++-14, x86-64-v3), 10 pairs at bench 16 and 8 at bench 20, A/A in every job, 2-6 runners per config;
  all node-exact (lock pins) except the NnueInt16=true side. Runs 40582060957, 40583387872, 40583577693,
  40583751865 (all success); opus-ci on the branch green.
- **Real effects** (same sign and size on quiet runners): SPEEDSTACK about +0.5%, profile counting about -1.1%,
  the PROF build about -1 to -1.5% on Linux (the PC's -7% adds MinGW's emulated TLS), NnueInt16 -8 / -13% (other
  tree), O2's AVX2 kernels +3.1% / +3.0% (speed rule met; but the PC lock recipe builds AVX-512 code where the
  kernels are compiled out; one AVX-512 runner still showed +4.1% / +4.0%, likely the 64-byte accumulator
  alignment, not isolated). NOZERO is a real +1.6% / +1.7% (rule not met), as S14 found.
- **PC layout artefacts** (do not reproduce): NOZERO -4.2% on the PC, the LAZY switch +4.4%, the INT16 switch
  +1.8%, and the -4.6% drift between two heads (quiet: 0 ± 1.5%); `nm` of the PC exes shows the hot functions
  moved in exactly those builds. So switch-level NPS on the loaded PC needs a quiet machine before any claim.

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

## R3-6 Lazy SMP scaling (agents; `opus_r3/R3-6/REPORT.md`, `opus_r3/R3-6Q/REPORT.md`)
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
- **Quiet-runner repeat (R3-6Q, run 40586326969):** the same 30 positions and depths on GitHub 4-vCPU runners (2
  cores x 2 SMT), 3 independent repetitions, 900 runs, every thread got its CPU. SmpHelpersPastDepth does **not**
  shorten time-to-depth: offP/off 1.105 [0.948..1.286] (T2), 1.019 [0.893..1.157] (T3); with the SMP options on
  it is slower, onP/on **1.157 [1.034..1.308]** (T2) and **1.168 [1.005..1.366]** (T3), with 17-21% more nodes.
  So the idle helpers are real (R3-6's trace) but filling that time with deeper iterations does not help the
  main thread; the option stays default off and is not a gate candidate. Stack OFF scales 1.28x (T2) / 1.14x (T3)
  per position there; the "on" set costs 2.2% at Threads=1 (identical nodes; LocklessTT's per-node cost on Linux).
- Checked without finding a bug: stop/join latency (median 0.1-1.2 ms), reported nodes (= per-worker sum), T3 vs T2,
  TT pressure, locked vs lockless TT on Windows. Proposed follow-up: depth diversification for helpers (needs an
  SMP gate). Not done: Threads > 3 (PC rule), larger Hash. The 3 repetitions were run on quiet runners (R3-6Q).

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
- Eight Python bytecode files are tracked in the stack (CTest runs the tools with the system Python, which writes
  `__pycache__` into the tree): four entered with the S08fix merge commit `9588a10`
  (`tools/__pycache__/uci_regression.cpython-314.pyc`, `tools/match/__pycache__/{pgn_stats,run_match,
  windows_validate}.cpython-314.pyc`) and four came with the merged feature branches (`opus_round1/O1/__pycache__/
  ucilib`, `opus_round1/O2/__pycache__/mutation_check`, `opus_round1/sol_S12/__pycache__/jobA_cause`,
  `opus_round1/sol_S12/followup_nullalias/__pycache__/mutation_check_alias`, all `.cpython-314.pyc`). Local CTest
  runs rewrite them, so every commit adds files by explicit path. Untracking them was not permitted here (no
  deletions); a `.gitignore` keeps new ones out. Please `git rm --cached` them when convenient.

## Left
- Nothing open from the R3 pack. Not done by design: real SPSA tuning, gates (owner), Threads > 3 (PC rule).
- Branches (all pushed, merged into `opus-r3-stack`): `opus-r3-tests`, `-spsa`, `-selfplay`, `-matrix`, `-smp`,
  `-gates`, `-port-b`, `-port-c`, `-cifix`, `-quietnps`, `-sp-linux`, `-smpq`. Local only: `opus-r3-premerge`
  (scratch pre-merge of SPSA + SMP, never pushed).
