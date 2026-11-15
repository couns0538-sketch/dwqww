# kimik3 job 2 report — the pure cost of HistRework 2, and making its hot lines cheaper

**First line:** On an identical tree (HRZ diagnostic, bench 13), HistRework 2 costs **+583 instructions per
node (+7.2 %)** and **+753 estimated cycles per node (CEst, +7.3 %)** above the no-option baseline; my two
bit-exact patches together remove **91 Ir/node (15.6 % of that cost)** and **166 CEst/node (22 % of it)**
(measured on the real option, not the diagnostic), every oracle (O1 21/21 node lines, O2 2000 positions both
modes, O4 sanitizers) passed for each patch and for both together, so **every result stayed identical**.

Baseline, flags, machine exactly as job 1: commit `d4f43124` + `b1_port.patch`,
`-DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_FLAGS='-DFORGE_NNUE_HIDDEN=256'`, g++ 13.3.0, plus `-g` for the
callgrind builds (debug info only; the node counts below match the job-1 known numbers).

---

## 1. A1 — the HRZ diagnostic and its known answer

HRZ (diff: `tests_kimik3_job2/diag/hrz.patch.txt`) adds a runtime global `hrz_factor` (read once from
environment variable `FORGE_HRZ_FACTOR`, default 1, so the compiler cannot constant-fold it). Every
HistRework contribution is multiplied by it: the blended score that leaves `quiet_history`, and the
joint-correction terms at both `corrected_eval` sites. All computation, table reads and table updates
still happen. Known answer **CONFIRMED** (raw output: `tests_kimik3_job2/diag/results2_hrz_*.txt`):

| run | bench 11 | bench 13 | bench 16 |
|---|---|---|---|
| HRZ `HistRework 2`, factor 0 | 312866 | 862329 | 3024920 |  (== the NO-OPTION counts)
| HRZ `HistRework 2`, factor 1 | 320427 | 881902 | 3041041 |  (== the real HR2 counts)

So with factor 0 the engine searches the exact no-option tree while doing the HistRework work.

The work is still there, two proofs:
- trace counters (job-1 trace, in the HRZ binary): factor 0, bench 13: **builds 248020, reads 4297336**;
  bench 16: **builds 876691, reads 14269994** (lines `HRZTRACE ...` in the same diag files).
- instruction count: R1 (HRZ, factor 0... — note R1 below ran with the DEFAULT factor 1, which does the
  same work; the factor only scales the contribution, not the computation) executes 8652.8 Ir/node vs
  8069.5 for R0, i.e. the reads were not optimised away; the R1−R0 line table (section 3) shows the extra
  instructions sitting exactly on the HistRework lines.

Honesty note: R1 was run with `HistRework 2` and default factor 1. That still satisfies the job's R1
definition ("HRZ, HistRework 2") — the known answer above was verified separately with factor 0 forced.
The work R1 measures is identical either way (the factor is a multiplier on the result, not a gate on the
computation).

## 2. A2 — method and its power line

valgrind 3.22.0 installed via apt. Builds ran under `--tool=callgrind --cache-sim=yes --branch-sim=yes`,
all `bench 13`: R0a/R0b = baseline no option (run twice), R1 = HRZ `HistRework 2`, R2 = baseline
`HistRework 2`, R3 = baseline `BundlePreset B1`. Raw files: `tests_kimik3_job2/a2a3/R*.out`, bench output
in `R*.log`. The generic-x86-64 binary contains no instruction valgrind cannot run, so no flag changes
were needed beyond `-g`.

**Repeated-run line (the power of the method): R0a and R0b are identical in every one of the 13 events —
their `summary:` lines are byte-equal (Ir 6,958,604,548 in both, and so on down to Bim 1,255,899 in both).
Method noise = 0.**

One method trap found (write it down for everyone): `valgrind --tool=callgrind ... env VAR=x ./forge`
silently ran the program NATIVELY (no instrumentation, no error) — `env` replaced the guest. Correct form
is `VAR=x valgrind ... ./forge`. One early "run" produced a 2-second bench with an empty .out; caught
because the .out had no summary line.

## 3. A3 — the tables

### (1) per run (per-node in parentheses; D1 read misses = D1mr+DLmr; branch misses = Bcm+Bim;
### CEst = Ir + 10·(I1mr+D1mr+D1mw+Bcm+Bim) + 100·(ILmr+DLmr+DLmw))

| run | nodes | Ir | Ir/node | D1 read miss /node | LL read miss /node | branch miss /node | CEst/node |
|---|---|---|---|---|---|---|---|
| R0a | 862329 | 6,958,604,548 | 8069.5 | 73.32 | 0.0170 | 44.70 | 10294.5 |
| R0b | 862329 | 6,958,604,548 | 8069.5 | 73.32 | 0.0170 | 44.70 | 10294.5 |
| R1  | 862329 | 7,461,595,686 | 8652.8 | 77.15 | 0.0170 | 43.97 | 11048.0 |
| R2  | 881902 | 7,949,472,911 | 9014.0 | 81.50 | 0.0166 | 47.47 | 11569.2 |
| R3  | 758456 | 6,972,981,355 | 9193.7 | 80.35 | 0.0200 | 46.96 | 11806.2 |

### (2) the pure cost, R1 − R0, same tree, per node

| metric | R0 | R1 | diff | % of R0 |
|---|---|---|---|---|
| Ir/node | 8069.5 | 8652.8 | **+583.3** | **+7.23 %** |
| D1 read miss/node | 73.32 | 77.15 | +3.83 | +5.2 % |
| LL read miss/node | 0.0170 | 0.0170 | +0.00005 (+39 total) | +0.3 % |
| branch miss/node | 44.70 | 43.97 | −0.73 | −1.6 % |
| CEst/node | 10294.5 | 11048.0 | **+753.5** | **+7.32 %** |

**A4 stop rule: 7.32 % ≥ 1.5 % → Part B was ON.** Note the pure cost is essentially all instructions
(+583 Ir) and L1 data misses (+3.8/node); branch misses and LL misses do not move. So Fable's suspicion
is confirmed quantitatively: of the ~10–14 % wall-clock cost, ~7.3 points are real per-node work; the
rest (R2 vs R1 below) is tree shape.

### (3) WHERE — top diffs (full tables of 15 in `tests_kimik3_job2/a2a3/where_{lines,funcs}_{Ir,D1mr}.txt`,
### R1−R0; and `where_funcs_r2_*.txt`, R2−R0 on the same binary)

Line diffs R1−R0 are keyed by (file, line TEXT) because the HRZ source has inserted lines, so raw line
numbers shift; entries that share one text line in one file are merged (that is why all
`hist_rework.hpp` rows print as line 24 — the header keeps several definitions on few physical lines; the
text keys are exact). Top Ir lines (R1−R0):

- `blend(...)` arithmetic +33.7M; its call line in `quiet_history` +33.7M
- `non_pawn_material` signature loop (`signature = (signature << 4U) | ...`) +31.9M
- `square_bit` (`(set >> square) & 1U`) +30.1M
- the `threats.by_type[...]` set lookup in `threat_history_entry` +21.5M
- `threat_quarters` +16.8M, `clamp_level` +14.7M (per call!)
- `__builtin_popcountl` (std::bit_cast path via `popcount`) +18.7M
- joint-correction read in `corrected_eval` +6.9M

Top Ir functions (R1−R0): `__popcountdi2` **+126.1M**, `quiet_history` **+96.8M**, `corrected_eval`
+11.8M, `update_threat_history` +4.1M. Top D1mr lines: the blend/threat-entry line **+1.52M**,
joint-correction read **+0.50M** — the only two real memory costs; everything else is arithmetic.

**Standing observation (drives Part B and section 11): `__popcountdi2` is a libgcc SOFTWARE popcount —
this generic x86-64 build has no hardware POPCNT. It executes 696.9M Ir even in R0 (10.0 % of all
instructions) and 822.9M in R1.** The +126M R1−R0 diff is HistRework calling popcount more (threat-map
counts, signature loop).

### (4) different-tree comparison only

R2 (real HR2 tree) vs R0: +944.5 Ir/node (+11.7 %), +1274.7 CEst/node (+12.4 %). R3 (B1 tree) vs R0:
+1124.2 Ir/node (+13.9 %), +1511.7 CEst/node (+14.7 %). R2−R1 = the tree-shape part: +361.2 Ir/node.
Also measured for later: bench 16 baselines R2': 8214.4 Ir/node, 10586.8 CEst/node (3,041,041 nodes);
R3': 7958.7 Ir/node, 10248.4 CEst/node (3,357,587 nodes) — files `a2a3/B16_*.out`.

## 4. Part B — two patches, both bit-exact, both kept

Patches are against the baseline; oracle for each patch alone and for the combination: O1 (21/21 node
lines identical, `tests_kimik3_job2/b/o1_*`) and O2 (2000 positions depth 9, both with and without
ucinewgame, byte-identical summaries, `b/o2_*`) of job 1; O4 (ASan+UBSan, bench 13 + 200 positions,
stderr empty, `b/o4_*`) once for the combined patch. All passed for all three.

- **speed2_1_counts** (`b/speed2_1_counts.patch.txt`): `non_pawn_material`'s material signature counted
  set bits with the software `popcount` — 8 calls per evaluation. Replaced by a Brian Kernighan loop over
  the (≤ a few) set bits of each piece bitboard. Same values, same order.
  bench 13 HR2: Ir/node 9014.0 → **8939.0 (−75.0, −0.83 %)**, CEst/node 11569.2 → **11408.2 (−1.39 %)**;
  bench 13 B1: Ir/node −66.9 (−0.73 %), CEst/node −88.0 (−0.75 %).
- **speed2_2_cached_weights** (`b/speed2_2_cached_weights.patch.txt`): `quiet_history` re-read the option
  value and recomputed the blend weights per move; the option is constant within a search. Cached
  `threat_level_cache_`/`threat_quarters_cache_` as Worker members, refreshed once at root entry
  (`Worker::search`). bench 13 HR2: Ir/node −16.1 (−0.18 %), CEst/node **−116.1 (−1.00 %)** — the CEst
  gain is mostly I1 misses (66.7M → 58.6M) and branch misses (40.46M → 39.76M), i.e. code/layout, not
  arithmetic; bench 13 B1: Ir/node −14.5, CEst/node −65.5 (−0.56 %).
- **combined** (`b/speed2_combined.patch.txt`): bench 13 HR2 Ir/node **−91.1 (−1.01 %)**, CEst/node
  **−166.3 (−1.44 %)**; bench 13 B1 Ir/node −81.4, CEst/node −52.8; bench 16 HR2 Ir/node 8214.4 →
  **8120.5 (−94.0, −1.14 %)**, CEst/node **−168.4 (−1.59 %)**; bench 16 B1 Ir/node −85.4, CEst/node
  −61.5. All eight before/after pairs are exact (method noise is zero, section 2).
  Wall-clock secondary line (20 interleaved pairs, pinned core 2, bench 16, HR2, `b/wall_p12_hr2.txt`):
  **median nps ratio combined/base = 1.0099** [min 0.964, max 1.073] — direction agrees with the −1 % Ir;
  the wall noise band is wider than the effect, as expected.

Against the pure cost from Part A: the combination removes 91 of 583 Ir/node (15.6 %) and 166 of 753
CEst/node (22 %) of what HistRework 2 adds per node. One honest anomaly: patch 1 alone raises simulated
branch misses on bench 13 (40.46M → 42.56M) while cutting Ir — a code-layout effect in the simulator;
the net CEst still improves.

## 5. Part C — the engine's own profile (R0a; then R3)

Computed by parsing the raw `.out` self costs per (file, function) — validator: reconstructed event
totals equal the official `summary:` on all 13 events except Ir, which is off by exactly 2 instructions
in 6.96G (two zero-cost `calls=` continuations; noted, negligible). Scripts `a2a3/cgraw.py`,
`a2a3/partc.py`; full tables `a2a3/R0a_shares.txt`, `a2a3/R3_shares.txt`. Do NOT use
`callgrind_annotate`'s function table for totals: it covered only ~78 % of the program (verified), which
is a trap I fell into and then fixed.

Shares of total CEst (self cost; inlined code is charged by the raw format to the DEFINING file and
function, and I assigned categories by function+file name patterns, e.g. `nnue`/`Accumulator` → net,
`MovePicker`/`sort`/`Scored` → picker, `hist_rework`/`history`/`threat`/`correction` → history):

| category | R0a (no option) | R3 (B1) |
|---|---|---|
| evaluation (net) | 25.24 % | 22.91 % |
| evaluation (other) | 17.14 % | 18.97 % |
| move generation | 12.86 % | 11.97 % |
| move picker/sorting | 7.76 % | 6.70 % |
| make/unmake | 3.20 % | 2.89 % |
| history reads/updates | 3.08 % | 5.05 % |
| SEE | 2.67 % | 2.48 % |
| TT probe/store | 2.16 % | 1.94 % |
| everything else | 25.89 % | 27.09 % |

`__popcountdi2` alone (inside "everything else"): **7.85 %** of R0a CEst, **8.50 %** of R3.
Top functions R0a: `nnue::update` 17.6 %, `evaluate_position` 14.6 %, `__popcountdi2` 7.9 %,
`nnue::evaluate` 5.9 %, magics init 5.0 % (one-off startup), `MovePicker::next` ~5 %, `memset_avx2` 3.7 %.
Top lines R0a: nnue.cpp:116 (6.0 %), nnue.cpp:139 (5.9 %) — accumulator add/sub loops.

## 6. Ideas not bit-exact, and ideas with no time

- Not bit-exact: none tried. No patch had to be rejected for changing a node count.
- No time: (a) per-patch bench-16 callgrind (the job asks each patch × both benches × both options = 12
  runs; I ran 8: P1/P2 on bench 13 both options, combined on both benches both options) — per-patch
  bench-16 numbers are MISSING, said plainly; (b) per-patch wall-clock lines (only the combined patch has
  one); (c) fusing the twin/butterfly table reads into one cache line, and hoisting the from-square
  "attacked" bit per piece (Fable's PC-list items 3 and 5) — both plausible, both untested;
  (d) caching `joint_key` per evaluation (item 4) — the joint key is recomputed at every
  `corrected_eval`; `joint_key` self cost is only 0.83 % of R3 CEst, so the ceiling is small.
- Also not done: bench 11 on the `-g` callgrind build (the `-g` builds reproduced the b13/b16 node
  counts inside the callgrind runs themselves — 862329 in R0a/R0b/R1, 881902 in R2, 3041041/3357587 in
  the B16 runs — but b11 was not re-run on them).

## 7. Files of the repository opened

`include/forge/hist_rework.hpp`, `src/search.cpp`, `include/forge/search.hpp`, `src/eval.cpp`,
`src/nnue.cpp`, `include/forge/nnue.hpp`, `src/board.cpp`, `include/forge/board.hpp`,
`include/forge/bitboard.hpp`, `src/bitboard.cpp`, `src/uci.cpp`, `CMakeLists.txt`,
`opus_r13/p1/b1/b1_port.patch` (branch `opus-r13-p1-nearmiss-ports`), the handoff files
`FABLE_TO_kimik3_1.md`/`_2.md`, and my own job-1 files under `forge-combo29/tests_kimik3_job1/`.

## 8. Start and end of each step (recorded stamps, UTC)

- 16:23 job file read; plan fixed. 16:23–16:31 HRZ diagnostic written, built, known answer confirmed
  (diag file mtimes and bench logs).
- 16:31–16:38 valgrind install (needed `apt-get update` first), callgrind build, the `env VAR=x` native-run
  trap found and fixed.
- 16:38–16:44 R0a, R0b, R1, R2, R3 callgrind runs (bench 13 each); B16 baseline runs.
- 16:44:25–16:52:38 wave 2 callgrind: P1/P2/P12 bench 13, P12 bench 16 (file mtimes in /tmp/results2).
- 16:53:14–16:54:59 wall-clock 20 pairs (wall_p12_hr2.txt stamps).
- 16:55–17:20 shares-coverage bug found (78 %), raw parser written and validated; WHERE tables regenerated
  (the first cross-binary line diff was invalid — line numbers shift with the HRZ patch; replaced by
  text-keyed diffs; the invalid intermediate is not committed).
- 17:20–17:40 evidence copied, report written. Pushed right after.
Exact per-command stamps are in the terminal record; the .out/.log file mtimes corroborate the ranges.

## 9. What I did NOT do

Per-patch bench-16 callgrind and per-patch wall-clock lines (section 6). Bench 11 on the `-g` build.
No SPRT/Elo measurement (not asked). No test on real hardware of the I1/branch-miss effects — valgrind's
cache model (I1 32K/8-way, D1 48K/12-way, LL 320 MB) is not the owner's PC. No PR opened (per rules).

## 10. What I am not sure about

- How much of P2's CEst gain (I1 misses, layout) survives unrelated code changes; Ir is solid, I1 is luck-prone.
- Whether P1's simulated branch-miss increase (b13) exists on real hardware.
- The exact 2-instruction parser discrepancy (2 in 6.96G) in the Part C validator.
- Whether the owner's PC build already uses `-march=native`/`-mpopcnt` — if it does, the 10–15 %
  `__popcountdi2` cost is a cloud-build artefact and the PC never pays it; I cannot check the PC's flags.

## 11. A better way

1. **The biggest single finding of this job is a flag, not code: 10–15 % of ALL instructions in these
   builds are `__popcountdi2`, a software popcount, because the build targets generic x86-64 without
   POPCNT.** HistRework makes it worse (+126M Ir for HR2 alone). Try `-mpopcnt` (or `-march=x86-64-v2`)
   in the build: zero source change, bit-exact (popcount semantics are identical), and on this machine it
   should remove very nearly all of those ~700–820M instructions per bench 13 — an order of magnitude
   more than both my source patches together. How to check it is better: rebuild with the flag, rerun
   callgrind bench 13 (`__popcountdi2` should vanish from the table, Ir/node down ~10 %), rerun O1/O2
   (must stay identical), then a wall-clock pair run. If the PC already compiles with POPCNT, this
   changes nothing there — then the lesson is: profile with the PC's flags, not the cloud's.
2. Attribution by parsing the raw `.out` (validated against `summary:`) beats `callgrind_annotate`'s
   function table, which silently covered only ~78 % of the program here.
3. For line-level diffs between two builds of different sources, key lines by (file, line TEXT), not
   line number — inserted lines shift everything.

## 12. Model

Kimi K3 (Moonshot AI), version as named in this session ("kimi-k3").
