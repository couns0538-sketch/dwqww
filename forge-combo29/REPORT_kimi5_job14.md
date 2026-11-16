# kimi5 job 14 report — RfpGuards: three reverse-futility guards behind options (patch on top of job 12's FailHighBlend)

(1) Step 0 met: bench 11 = 312,866, bench 13 = 862,329, `go perft 5` = 4,865,609, all four options listed with
their ranges, default 0. Identities I1 (O 12,573,318 / G 22,128,265), I2 (O 9,500,069 / G 18,466,239), I3
(O 9,272,824 / G 18,240,994) met per position AND best move against my job-12 rows. Z1, Z2, Z3, Z4 equal Z
(RfpDepth 0) on every position, node count and best move, on O and G.
(2) Step 2 blocked counts over the 200 searches of O under S14, against P of the same run: RfpCorrMul 16 blocks
C = 118,746 of P = 2,073,015 plain-true sites; RfpTtGuard blocks T = 2,413 of P = 2,027,107; RfpNoTtPv blocks
N = 1,703 of P = 2,000,181. All three at once: N 1,699, T 3,279, C 124,909 (P 2,112,187; the per-option sets
overlap, so N+T+C overstates distinct blocked returns). Positive control: the plant that blocks EVERY return
under RfpTtGuard 1 gave T = P = 1,846,146 exactly, and its nodes equal Z's per position.
(3) Step 3 table below. Plain words: asked = three RFP guards as text patch, each default-off, with identities,
counters, tree ratios. Answer = patch written, every identity and wiring check passed, the correction guard is
the big one (+7.3 % tree at 16, +11.2 % at 32 on O) while the two TT guards are nearly free on trees. Surety:
high on the numbers (identities per position, counting build per-position equal to plain, plant fired exactly);
the tree ratios are what they are (bootstrap intervals included), no strength claim made or implied.

## Step 0 (raw output files)
- tests_kimi5_job14/step0_bench11.txt: `info string bench depth 11 nodes 312866 ...` — OK
- tests_kimi5_job14/step0_bench13.txt: `... nodes 862329 ...` — OK
- tests_kimi5_job14/step0_perft5.txt: `nodes 4865609` — OK
- tests_kimi5_job14/step0_uci.txt: `FailHighBlend 0..7 d0`, `RfpNoTtPv 0..1 d0`, `RfpTtGuard 0..1 d0`,
  `RfpCorrMul 0..64 d0` — OK. Built from 6b98f217 + FailHighBlend.patch.txt (sha256 checked
  8083a257c55b2deef9455c9c698fe750b7c3fd9707d8bc75507a6265cfc23e1a before applying) + RfpGuards.patch.txt,
  `patch -p1 -F0`, zero fuzz, g++ 13.3.0, Release, machine has AVX-512+BMI2 (no FORGE_PORTABLE).

## Steps table
| step | done | evidence | result |
|---|---|---|---|
| 0 honesty | done | step0_*.txt | all three known numbers met, options listed |
| answers (a)-(d) | done | below, file+line | written before the build |
| patch + sha256 | done | RfpGuards.patch.txt db6a1dba...; applies after FHB with -F0 | zero fuzz, identical tree verified |
| 1 identities I1-I3 | done | compare_i.txt, rows/*.json(.meta) | per position + best move, all equal |
| 1 wiring Z1-Z4 vs Z | done | compare_i.txt | all equal on O and G (Z: O 15,223,075 / G 28,769,153) |
| 2 counters | done | counter_sums.txt, RfpGuardsCount.patch.txt | counts above; counting build per-position equal to plain build in all 5 states |
| 2 positive control | done | ctrl_plant_t rows, RfpGuardsCountPlant.patch.txt | T = P = 1,846,146; plant nodes = Z per position |
| 3 trees | done | boot_trees.txt, rows/ | table below |
| prediction | done (scored) | prediction.txt | 2 of 6 tree rows alive, nearness right, Step-2 ordering KILLED |

Runs overlapped: up to 3 single-thread depth-12 searches at once (driver 21:06:13-21:07:37Z, counters after;
stamps.txt has every window). Depth-limited searches: node counts unaffected; said here per the job-12 habit.

## Step 3, tree ratios vs I2 (S14), bootstrap 95 % over positions (2000 resamples, seed 12)
| run | O ratio [interval] | O bm changed /200 | G ratio [interval] | G bm changed /353 |
|---|---|---|---|---|
| T_n (RfpNoTtPv 1) | 0.9948 [0.9489, 1.0430] | 41 | 0.9896 [0.9449, 1.0351] | 79 |
| T_t (RfpTtGuard 1) | 1.0125 [0.9695, 1.0595] | 29 | 0.9979 [0.9528, 1.0453] | 78 |
| T_c16 (RfpCorrMul 16) | 1.0727 [1.0186, 1.1313] | 55 | 1.0285 [0.9769, 1.0786] | 81 |
| T_c32 (RfpCorrMul 32) | 1.1116 [1.0548, 1.1723] | 49 | 1.1076 [1.0460, 1.1705] | 81 |
| T_all (three, 16) | 1.1008 [1.0443, 1.1621] | 58 | 1.0702 [1.0173, 1.1335] | 86 |
| T_allF (three + FHB 1) | 1.0292 [0.9719, 1.0908] | 65 | 1.0319 [0.9803, 1.0873] | 80 |
| T_allF vs I3 (FHB 1) | 1.0544 [0.9923, 1.1212] | 63 | 1.0447 [0.9939, 1.0949] | 82 |

T_allF nodes: O 9,777,431 (I2 9,500,069 +277,362; I3 9,272,824 +504,607) — nearer to I2, as predicted.

## Prediction, scored (prediction.txt, committed before Step 1)
- T_n 1.015 [0.995, 1.040]: actual 0.9948 — KILLED (0.0002 under the fence; direction wrong: it SHRANK).
- T_t 1.045 [1.010, 1.080]: actual 1.0125 — alive, at the floor.
- T_c16 1.003 [0.990, 1.015]: actual 1.0727 — KILLED. - T_c32 1.006 [0.990, 1.025]: actual 1.1116 — KILLED.
- T_all 1.055 [1.020, 1.095]: actual 1.1008 — KILLED. - T_allF 1.025 [0.995, 1.060]: actual 1.0292 — alive.
- T_allF nearer I2 than I3: CORRECT. Step 2 most-blocks (predicted T > N > C): KILLED — actual C >> T > N,
  the exact reverse. Cause misjudged: correction differences at frontier nodes are commonly tens of cp, so
  adding |static_eval - raw_eval| to the margin (corr 16 ≈ 1 x diff) flips ~6 % of plain-true tests.

## Answers (a)-(d) from the code (6b98f217 line numbers; verified before the build)
(a) `ss->static_eval - ss->raw_eval` at the RFP test (search.cpp:1689): `raw_eval` is the uncorrected static
eval set at 1653-1655 (the TT entry's stored eval after a `!= ValueNone` check at 1653, the Hindsight-reused
raw of 1620/1654, or a fresh `static_evaluate` at 1655). `static_eval` (1656) is
`rule50_damped_static(corrected_eval(board, raw_eval), halfmove)`: raw + the correction-history term
(corrected_eval, search.cpp:1210-1226 — pawn table plus, when the options are on, material and non-pawn
tables, sum divided by CorrectionGrain 256, result clamped to ±(MateInMaxPly-1) = ±31871), then the rule-50
shrink (search.hpp:351-355, `score*(100-clock)/100`, only when tune::EvalRule50Damp; that bool defaults false
and S14 does not set it, so in these runs the difference is the pure correction term). Neither side can be
ValueNone at 1689: the in-check branch that sets both to ValueNone (1649) is barred by `!in_check` (1680), the
excluded-move branch (1650-1651) by `excluded.is_none()` (1680), and in the taken branch raw comes from the
checked-TT/reused/fresh paths above while static_eval is a clamped int (31,871 < ValueNone 32,002,
search.hpp:75) or its damped-toward-zero value. The TT-score replacement at 1657-1661 rewrites `eval`, not
the two ss fields, so the difference is unaffected by it.
(b) Largest rfp_corr: |static_eval - raw_eval| ≤ 31,871 + max|raw|; even at the formal bound (raw at the
opposite clamp) that is 63,742, so rfp_corr ≤ 64 x 63,742 / 16 = 254,968. Margin ≤ RfpMargin 300 x depth 15 -
0 + 254,968 = 259,468; `eval - margin` ≥ -31,871 - 259,468 ≈ -2.9e5 and `eval < 31,872` — int (±2.1e9) cannot
overflow (search.hpp:71-75 constants; realistic raw within a few thousand cp, same conclusion wider).
(c) `tt_move` is born at 1595 from the TT probe: `tt_hit && (!near50 || tte.rule50_clock ==
board.halfmove_clock()) ? tte.move : Move::none()`, a const. Between 1595 and 1689 nothing can change it:
the Hindsight block (1611-1635) touches `depth` (read by the RFP test — today's behavior, kept), the TT cutoff
(1638-1644) only returns, the eval block (1647-1661) writes ss->raw_eval/static_eval/`eval` only. `tt_capture`
(1601) is fixed with it. Caveat: `tt_capture` reads the move's encoded capture flag from the TT entry; it is
not re-validated against the board (the job's formula uses exactly this value).
(d) `RfpNoTtPv` given `!pv_node` (1680): `ss->tt_pv = pv_node || (tt_hit && !near50 && tte.pv())` (1602), so
at non-PV nodes it is true exactly when a usable (not near-50) TT entry carries the pv flag — an entry stored
by a PV-node search. The option can therefore remove reverse futility only at non-PV "expected-PV" nodes; at
PV nodes the block never runs, and nodes without a hit or with a non-PV entry are untouched. Measured: that
is 1,703 of 2,000,181 plain-true sites (0.085 %) — and the tree SHRANK anyway (O 0.9948): the blocked
fail-high returns cost their prune but change what the TT stores; the net measured effect is slightly fewer
nodes. Mechanism for the shrink is a suspicion, not proven (below).

## The patches and how to apply
1. `git archive 6b98f217` (or a clean checkout of it), then:
2. `patch -p1 -F0 < tests_kimi5_job12/FailHighBlend.patch.txt` (sha256 8083a257c55b2deef9455c9c698fe750b7c3fd9707d8bc75507a6265cfc23e1a)
3. `patch -p1 -F0 < tests_kimi5_job14/RfpGuards.patch.txt` (sha256 db6a1dba024741b7af9b6f10693189caea3a79ead3018d94152f52c16aeb03dc)
   — plain build, the engine of every Step 0/1/3 row (exe sha256 d5043407357127333a4b8dda58646c806b8213bbc8c44f318a9cb1daad8858c7).
4. Counters: then `patch -p1 -F0 < tests_kimi5_job14/RfpGuardsCount.patch.txt` (sha256 94de9b6a...) and build
   with `-DCMAKE_CXX_FLAGS=-DFORGE_RFP_COUNT=1` (exe bd26ef06...). Observe only: per-position equal to the
   plain build in all five option states (counter_sums.txt).
5. Plant (control): `RfpGuardsCountPlant.patch.txt` (sha256 359e1f25...) on the counting tree, same flag
   (exe 62502c53...). Never for play: RfpTtGuard 1 blocks every RFP return there.
RfpGuards.patch.txt logic (names kept from the job file): three ints + table entries
(`RfpNoTtPv 0..1`, `RfpTtGuard 0..1`, `RfpCorrMul 0..64`, all default 0), and at the RFP test
`rfp_ok = !(RfpNoTtPv && ss->tt_pv) && !(RfpTtGuard && !tt_move.is_none() && !tt_capture)`,
`rfp_corr = RfpCorrMul ? RfpCorrMul * abs(ss->static_eval - ss->raw_eval) / 16 : 0`, the test gaining
`rfp_ok &&` in front and `+ rfp_corr` inside the margin's parentheses. No other change.

## Suspicions, not proven
- T_n's shrink (O 0.9948, G 0.9896) despite 1,703 blocked returns: the un-returned nodes' TT entries (stored
  with real bounds instead of a Lower-bound eval) plausibly save more than the prunes cost. Not isolated.
- C's large count says correction magnitudes at frontier non-PV nodes are commonly ≥ 16 cp; distribution not
  measured (only the flip count).
- P moving across option states (2.00 M to 2.11 M) is a tree-shape effect (blocked returns change what is
  reached), consistent with the numbers, not independently proven.

## From my colleagues
- Read: deepseek5 NOTES (stage labels read one late — counters must read state at the event; my note() reads
  ss->tt_pv/tt_move at the RFP line itself, never cached) and their job-30 Killer/Counter rates (not this job).
- Read: glmflash5 NOTES on cursor/glmflash5-work-cb5c (the branch-name correction held; my FailHighBlend
  blends LOSE games at 2k nodes: bit7 -25.9, bit2 -13.4; LmrFine T1 a perfect null). Consequence taken:
  T_allF's FHB part is strength-negative there even while it shrinks trees — trees only here, as ordered.
  Their fabrication lesson applied: every table above is script output pasted, report written around it.
- Read: deepseek6 NOTES (a batch harness without ucinewgame carries a depth-dependent bias of a few %):
  checked my runner's input logs — `ucinewgame` + `isready` before every `go`, e.g.
  rows/i2_s14_O_d12_input.log. Their planned sanitizer cross-check of this patch: patch kept minimal for it.
- Applied: deepseek6's "a prune count does not predict a tree" — T_n confirmed it again (1,703 prunes
  removed, tree shrank). Checked: nothing of theirs re-run this job (trees only, per the file).

## What I did NOT do
- No strength measurement (the file says trees only). bench 16 not in this job's Step 0 (11/13 + perft 5 only).
- Counters on G not run (the file sums over O only). No sanitizer run on this patch (deepseek6's standing
  cross-check covers it). Two driver failures on the first batch (xargs -I word-splitting dropped the
  no-option runs; a backgrounded `VAR=... &&` emptied the exe path once) — both rerun standalone, all rows
  present, nothing overwritten (the runner refuses existing files and stopped as designed).

## What I am NOT sure about
- Whether the TT move's encoded `is_capture()` can ever disagree with the board at that line (not
  re-validated; the job's formula uses this value, so behavior is as specified either way).
- G-side C rate (counters were O-only by the file).
- Whether the two near-1.00 ratios (T_n, T_t on G) hide position-class structure the bootstrap averages away.

## A better way
- Make the plant's side effect a standing check: the RfpTtGuard-plant's nodes equal Z (RfpDepth 0) PER
  POSITION — an unplanned second proof that the plant blocked exactly the RFP returns. Any "blocks every X"
  plant should be required to reproduce the "X switched off" knob's rows; it costs one comparison and catches
  a plant that blocks more than intended.
- Quote blocked shares inside one run (N/P of the same search set), never N across runs: P itself moves with
  the tree (2.00 M - 2.11 M here). Done above; worth making a standing rule.

## Times
times: see stamps.txt (run start first: claim 2026-11-16T21:03:34Z).

## Model
Kimi K3 (as given by this runtime).
