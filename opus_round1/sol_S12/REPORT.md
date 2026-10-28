# S12 Lazy accumulator updates + why Job A's ON path was slow — DONE (report and evidence tool; follow-up: Sol's null-edge alias ported, default OFF)

`SOL_LEFTOVERS_FOR_CLAUDE.md`, section 2. Branch `opus-sol-S12` = `d4f4312` (AL1 lock tree and baseline evidence) +
`0d99f02` cherry-picked (`316ab352`) + `35469022` (this job's tool and logs) + this report. No engine file changes,
so no CI run (`[skip ci]`). No timed run was made (machine exclusive: no). No Elo or speed claim.
**Follow-up (2026-10-27, section 6):** Sol's null-edge accumulator alias is now ported (`1d4052d2`), behind the build
switch `FORGE_NNUE_LAZY_ACC` and the UCI option `NnueLazyAcc`, both default off; the default build is the lock binary.

## Coverage decision (section 1 rule: skip covered work and say so)
| part of the S12 spec | status | evidence |
|---|---|---|
| OFF-default lazy accumulator update "from the nearest computed ancestor" | **already in AL1; not repeated here.** opus-O2 REPORT §1 documents it ("Lazy updates (already in AL1, unchanged)") | `git show d4f4312:src/search.cpp`. `static_evaluate` 599-620 walks back to the nearest valid accumulator and replays the stored `DirtyPieces` (611-612), or refreshes (607). `record_move` 623-629 only stores `DirtyPieces` and marks the child invalid. `record_null_move` 632-636 does the same with zero changes. An option for it would duplicate existing behaviour, so none is added. |
| "first explain, with counts, why Job A's ON path ran at 0.976/0.930" | **DONE here** | sections 1-4 |
| Sol's extra refinement: reuse the parent accumulator on null-move edges instead of copying it | not covered by O2 (O2 kept null moves as copy-then-apply); **ported in the follow-up**, default off, node-exact | section 6 |
| Sol's prepared tools (bench-counter helper, ON-framing/qualify scripts, alias model tests) | his native regression test now runs as a CTest target (v2, one substitution); the bench-counter helper and ON-framing scripts are not shipped (our `alias_stats.py` reads the patch's own stats lines) | sections 5, 6 |

## 1. Refresh is not the cause (counts)
Sol's 20 raw counter logs
(`17aa0cae:validation/forge_sol_jobACD_20261025/forge_sol_a_{lock,buffix}_checks_20261025/forge_sol_{off,on}_bench_d*_20261025.stdout`)
are identical for the lock and buffix bases and for OFF and ON. Every log has the exact bench nodes, and ON runs
every construction in int32:

| depth | refreshes | incremental updates | NNUE evaluations | refresh/(refresh+update) |
|---:|---:|---:|---:|---:|
| 11 | 8 | 238,992 | 194,803 | 0.003347280% |
| 13 | 8 | 571,275 | 468,251 | 0.001400357% |
| 16 | 8 | 1,862,090 | 1,529,986 | 0.000429623% |
| 20 | 8 | 9,547,266 | 8,129,843 | 0.000083794% |
| 22 | 8 | 23,231,031 | 19,748,055 | 0.000034437% |

- **One refresh per root.** In AL1 the only refresh calls are `search.cpp:1367` (the root, once per search) and
  `:607`. Line 607 only runs when no ancestor accumulator is valid, which cannot happen once the root has been
  refreshed.
- **O2's callgrind of AL1** (`bench 13`, CI run 40410897098,
  `origin/opus-O2:opus_round1/O2/logs/ci_perf_edcf163/profile_self_lock.txt`):
  - total: 5,009,901,526 instructions;
  - `nnue::update`: 414,046,564 (8.26%);
  - `nnue::evaluate`: 205,304,330 + 54,925,574 (4.10% + 1.10%);
  - `nnue::refresh`: not listed. The smallest listed line is 0.98%, and O2's REPORT §3 puts refresh below 0.1%.
- So no refresh speed-up or refresh cache can move NPS on this architecture.

## 2. With the option OFF, the feature build costs nothing measurable
These are QA's raw box ABBA arrays (lock archive `7_history/rejected_and_shelved/int32_exact_h256e12_20261025/qa_evidence/`,
sha256 `7782c9df…`, `80a07688…`), recomputed. All stored medians reproduce. Intervals are 95% block-bootstrap
intervals of the median (resampling whole ABBA blocks, seed 20261027, 10,000 resamples).

| comparison | d13 median [95%] (ratios < 1) | d16 median [95%] (ratios < 1) |
|---|---|---|
| C1: switch-ON build, option ON, vs plain lock | 0.9534 [0.9375, 0.9695] (19/20) | 0.9580 [0.9483, 0.9820] (16/20) |
| C2: same binary, option ON vs OFF | 0.9570 [0.9461, 0.9644] (19/20) | 0.9539 [0.9449, 0.9618] (16/20) |
| C4: buffix + switch-ON build, option ON, vs buffix | 0.9558 [0.9413, 0.9649] (17/20) | 0.9612 [0.9505, 0.9845] (16/20) |
| C3: switch-OFF build vs lock, 20-block rerun | 0.9943 [0.9788, 1.0091] (24/40) | 1.0049 [0.9915, 1.0133] (15/40) |

- C3's intervals include 1.0, so the build with the switch OFF costs nothing measurable.
- C1 ≈ C2. So the switch-ON build with the option OFF runs like the lock: the 2080 → 4128-byte Accumulator, the
  always-on thread-local counters and the mode branches do not explain the loss.
- QA's guess that "accumulator copy work doubled" is also not supported. With the option ON, only the int32 half
  of the accumulator is written; with it OFF, only the float half.

## 3. The cost is the ON path's per-node arithmetic (machine code of the timed exe)
Sol saved the disassembly of the timed candidate B (exe `aaf0f890`; file
`…/forge_sol_a_lock_checks_20261025/forge_sol_nnue_disassembly_20261025.txt`, sha256 `f768bc90…`). He also saved
the build with the switch compiled out (exe `f4365f19`, sha256 `bba81094…`). Both are GCC 14.2, `-march=znver5`.

**(a) Accumulator update.** The float path, which the same exe uses with the option OFF, has a fused kernel per
move type. It is fully unrolled, has no branches, and uses 512-bit `zmm` registers (16 lanes).
- Quiet move: load, `vsubps`, `vaddps`, store per 16 lanes, 65 instructions per perspective (range
  `0x41bed3..0x41c092`).
- Capture: 83 instructions per perspective (`0x41c9ee..0x41cc22`).

The int32 path (`update_exact`, inlined into `update`, `0x41c4a0..0x41c540`) is one generic loop over the change
list, inside the 256-bit `ymm` vector loop (8 lanes). On every 8 lanes it re-reads `dirty.count` and each change's
add flag and branches on them. One iteration was traced by hand; the tool checks the trace is a valid control-flow
path:
- quiet move: 21 instructions per 8 lanes, including 6 branches;
- capture: 30, including 9 branches.

Per update (512 lanes):

| move | float (OFF) | int32 (ON) | ratio |
|---|---:|---:|---:|
| quiet | 130 | 1,344 | 10.3x |
| capture | 166 | 1,920 | 11.6x |

The int32 path's one advantage, reading int16 weight columns (half the bytes of float columns), did not make up
for this.

**(b) Evaluation.** Every ON evaluation first converts both perspectives' 512 int32 lanes to float and scales them
by 1/4096 into 2 KiB of stack temporaries. That is a 9-instruction loop run 32 times, 288 instructions per call
(`0x41cf00..0x41cf28`). It then calls the output layer `evaluate_values` out of line (76 instructions). In the
compiled-out build that layer is inlined in an 84-instruction `evaluate`.

**Instructions are not cycles.** A static model gives about 0.83-1.14 billion extra instructions at d13:
(1,344 − 130) to (1,920 − 166) per update × 571,275 updates, plus 288 × 468,251 evaluations. That is far more than
the measured ~4.5% time cost, so most of the extra integer work overlaps with the memory-bound parts. The model
explains the direction of the loss, not its size.

QA's box builds were AVX2, where the float kernels are 256-bit too, and QA still measured 4-5%. So the 512-bit
versus 256-bit gap is not needed to explain the loss; it can only add to it on AVX-512 targets such as Sol's znver5
build.

## 4. Sol's 0.976 / 0.930 are noisy
The 80 raw advisory logs are in Sol's branch:
`validation/forge_sol_jobACD_20261025/forge_sol_a_advisory_abba_20261025/forge_sol_d{13,16}_block{00..09}_{0_A,1_B,2_B,3_A}_20261025.stdout`.
His recon thought they were missing. They reproduce all 20 controller ratios per depth exactly.

| depth | median B/A | 95% interval | ratio range | ratios below 1 | sign test p | A run time |
|---|---:|---|---|---:|---:|---|
| d13 | 0.9760 | [0.9320, **1.0091**] | 0.505..2.856 | 12/20 | 0.503 | 805..4581 ms (median 898) |
| d16 | 0.9298 | [0.9105, 0.9807] | 0.643..1.184 | 15/20 | 0.041 | 2431..3461 ms |

The d13 interval includes 1.0, so d13 does not establish a slowdown at all. The d13-versus-d16 difference is
noise, not a depth effect: QA's tighter arrays put the ON cost at 4-5% at both depths.

**Written cause.** Job A's ON path was slower because every node pays more. Its int32 update kernel is a generic,
branchy, 8-lane loop (10-12× the instructions of the fused float kernels), and every evaluation adds a 512-lane
int32 → float conversion plus an out-of-line output layer. Refresh had nothing to do with it (8 per bench). The
layout, counters and dispatch of the feature build cost nothing measurable with the option OFF. The specific
numbers 0.976 and 0.930 come from a noisy shared machine; the reliable estimate is QA's 4-5%. If int32 is
revisited (shelf README conditions), the idea would be: one int32 kernel per move type with no branch inside the
vector loop, full vector width, and the conversion fused into the output layer's first load. That is an idea
only, not a claim.

## 5. Not done (original run; the alias was ported later, section 6)
- **Null-move alias not ported.** Sol's zero-dirty null-edge alias
  (`…/forge_sol_S12_source_prepared_20261026/forge_sol_S12_lazyacc_h256e12_reviewv2_20261026.patch`, sha256
  `66efe4c9…`, made for his dev base, never compiled) is not covered by O2 and not ported. It adds a branch to
  `static_evaluate`, an `accumulator_owner` field to `SearchStack` and a compile-time switch, so it changes hot
  code. A gateable version (the PC recipe has fixed flags) needs a codegen diff and an NPS A/B.
  - **Bound (model):** O2's microbenchmark puts a null-move update at about 24.8 ns on the PC. AL1 d20 is 12.39M
    nodes in about 6.2 s, so saving 1% would need about 2.5M evaluated null-move children, about 20% of all nodes.
  - **Resume steps:** port the patch as a runtime option to the lock tree; check with
    `opus_round1/O3/codegen_compare.sh`; bench all 5 depths OFF and ON exact; ASan/TSan on CI; count null edges;
    NPS A/B using the `opus-c1-nps.yml` pattern.
- **Sol's tools not shipped.** His bench-counter helper and ON-bench parsers need that patch's counters.

## 6. Follow-up (2026-10-27): Sol's null-edge accumulator alias, ported (default OFF)
Main session, commit `1d4052d2` (+ this evidence commit). Folder `followup_nullalias/` (README, patch.diff vs the
lock, tools, logs). Machine exclusive: no; speed is quoted only from quiet GitHub runners. No Elo claim.

**What it is.** After a null move the pieces do not change, so the null child's accumulator equals its parent's;
AL1 still copies it (`nnue::update` with zero dirty pieces copies both 256-float halves, 2 KiB). Sol's patch lets the
null child borrow the nearest valid physical ancestor's accumulator and runtime PSQT through
`SearchStack::accumulator_owner`, so the copy is skipped. Values and search trees do not change.
- Build switch `FORGE_NNUE_LAZY_ACC` (CMake option, default OFF); with it, the UCI option `NnueLazyAcc` (check,
  default false). When on, each search prints `info string NnueLazyAcc active` once and a stats line per search.
- Sol's patch `66efe4c9` (`…/forge_sol_S12_source_prepared_20261026/…reviewv2_20261026.patch`, never compiled by
  him): its 17 code hunks apply to AL1 with GNU `patch -p1 -F0` without fuzz or offset and are unchanged. His
  README/IDEA_SOURCE hunks belong to his h256_e12 tree and are not applied.

| check | result | evidence |
|---|---|---|
| default build = lock | **PASS**: the PC box build without the switch differs from the lock exe `5d4df7f1…` only in the 6 PE timestamp/checksum bytes; FMA 0, 0 warnings. Linux CI (g++-14, CMake Release): the default build is the lock binary byte for byte and in disassembly (sha256 `6635d4d1…`). | `logs/step0_builds.log`; `logs/ci_40528476124/release/identity_default_vs_lock.log` |
| node-exact | **PASS**: `uci_check --full` (bench d11-d22, perft5, kiwipete) ALL OK for the switch-OFF build and for the switch-ON build with `NnueLazyAcc` false and true (PC); the same on Linux CI (`--full`, option off and on), and under ASan+UBSan (d11/13/16 + perft, off and on) | `logs/step1_identity.log`; `logs/ci_40528476124/{release,asan}/identity_*` |
| the alias is active | copies avoided per bench (the null edges that borrowed instead of copying): d11 2,696, d13 9,612, d16 41,488, d20 183,232, d22 507,093 = 1.4-2.7% of evaluations; nodes = AL1 pins; same d13 counts under ASan on Linux | `logs/step2_alias_stats.log`; `logs/ci_40528476124/{asan,release}/alias_stats_*.log` |
| Sol's regression test | **PASS 143/143** (v2: one substitution, AL1's PSQT oracle replaces a private call), asserts on. Control against the base (switch off): exactly the 17 alias-specific checks fail, the 126 parity checks pass | `logs/step4_sol_regression_v2_on.log`, `logs/step4b_sol_regression_v2_base_control.log` |
| extra tests (ours) | **PASS 9/9**: a reused null-null chain must not leave a stale alias; an owner pointer that is not a lower, valid, physical frame is ignored | `logs/step5_extra_tests_on.log` |
| planted bugs | **7/7 caught**. Sol's test alone caught 5/7; the two it missed (a missing owner reset in `record_null_move`, an unvalidated owner pointer) are caught by the extra tests. Six mutants are caught by the CTest programs, the seventh (option not wired into the search) by `alias_stats.py` | `logs/step3_mutants.log`, `logs/step3b_mutants_with_extra_tests.log` |
| CTest with the switch | `forge_s12_lazyacc_tests` and `forge_s12_lazyacc_extra_tests` pass in release, ASan+UBSan and TSan; otherwise only the 4 known forge_tests lines; 0 sanitizer reports | `logs/ci_40528476124/*/known_*`, `*/ctest_*` |
| threads | TSan: Threads 2 and 4 sessions with `NnueLazyAcc` on, bestmove returned, 0 reports | `logs/ci_40528476124/tsan/tsan_sessions.log` |
| default build in opus-ci (run 40528475941) | release identity ALL OK (forge sha256 `6635d4d1…` = the lock build), FMA 0; ASan and TSan known-only, 0 reports | `logs/ci_40528475941/` |
| NPS (quiet runner) | no measurable effect. Run 40528476124, Intel Xeon Platinum 8370C, ABBA, 10 runs per side, nodes identical; CPU NPS d16 / d20 (95% CI of the difference): lock vs switch-on, option off +0.11% [−0.23, +0.46] / +0.17% [+0.00, +0.33]; switch-on, option off → on −0.16% [−0.38, +0.06] / −0.12% [−0.37, +0.13]; lock vs switch-on, option on −0.06% [−0.25, +0.12] / −0.07% [−0.25, +0.12] | `logs/ci_40528476124/release/nps_*.log` |

**Size of the effect.** O2's microbenchmark puts a null-edge copy at about 24.8 ns on the PC. At d20 the alias
avoids 183,232 copies: about 4.5 ms of a bench that takes about 6.2 s on the PC, about 0.07%. Section 5's bound
said a 1% gain would need about 2.5M null children; the real count is 14 times smaller. The quiet-runner A/B agrees: option on vs off and lock vs alias-on stay within ±0.4% with every CI including 0 (the lock vs switch-on figure with the option off touches 0 at d20, +0.17% [+0.00, +0.33]). The alias works and is node-exact, but it does not pay for itself as a speed change.

**Code size (Linux, `nm -S`, bytes; `release/hot_function_sizes.log`).** Switch-on vs lock: `static_evaluate` 625 → 726, new `static_evaluate_lazy` 1,020, `record_move` 159 → 170, `record_null_move` 29 → 40, `qsearch` 4,233 → 4,265, recursive `search` 12,737 → 12,762; the NNUE kernels are unchanged.

**Findings**
- The two planted bugs that only our extra tests catch are equivalent in today's engine. Search never makes two
  null moves in a row (`search.cpp` null-move condition: `!(ss - 1)->current_move.is_none()`), so a null child's
  owner is always its parent and a stale pointer would name the right frame. They guard the null-null chains that
  Sol's design and test allow.
- With the switch on, the patch counts every evaluation, refresh and update in both paths (the stats line). That
  counter cost is part of what the switch-on build measures.

**Left / UNVERIFIED**
- No gate. Not proposed for a gate as a speed change: the measured effect is zero within ±0.4% and the counted saving is about 0.07%. Kept as a correct, tested, default-off option.
- MSVC build of the switch not tested.

## Evidence and reproduction
```
cd opus_round1/sol_S12
python -I jobA_cause.py --repo <git dir with 17aa0cae, d4f4312, origin/opus-O2> \
  --qa-dir <lock archive>/7_history/rejected_and_shelved/int32_exact_h256e12_20261025 --json logs/jobA_cause.json
python -I test_jobA_cause.py
python -I mutation_check.py <scratch dir>
```
- Step 1, the real-file run (`logs/step1_jobA_cause_run.log`): all inputs parse and cross-check, exit 0.
- Step 2, unit tests (`logs/step2_unit_tests.log`): 11/11 OK.
- Step 3, planted bugs (`logs/step3_mutation_check.log`): all 4 mutants caught (wrong ABBA pairing, jmp allowed to
  fall through, one-sided sign test, zmm counted as ymm).
- Input revisions: Sol `17aa0cae1d36…`, lock `d4f43124dde1…`, O2 `82282b09f606…`.
- Main-session spot check (2026-10-27): the cited lock-tree lines (`search.cpp` 599-636, 607, 1367) match
  `git show d4f4312:src/search.cpp`.

## UNVERIFIED
- That the extra instructions translate into time in the proportions given (static model only).
- The int32 loop structure in QA's x86-64-v3 binaries: same source, but that disassembly was not saved.
- The null-move alias's benefit: measured in section 6 (counts on the PC, NPS on a quiet runner).
- Windows timings (none made).

## Files
`REPORT.md`, `jobA_cause.py`, `test_jobA_cause.py`, `mutation_check.py`, `logs/step1_jobA_cause_run.log`,
`logs/jobA_cause.json`, `logs/step2_unit_tests.log`, `logs/step3_mutation_check.log`, `FILES.txt`, `SHA256SUMS`.
No .tar.gz archives (each step wrote one log).
Follow-up: `IDEA_SOURCE.md` (added), `followup_nullalias/` (README, patch.diff, tools, logs); engine and tests
outside the folder: `CMakeLists.txt`, `include/forge/search.hpp`, `src/search.cpp`, `src/uci.cpp`,
`tests/forge_sol_S12_lazyacc_native_regression_v2_20261027.cpp`, `tests/s12_lazyacc_extra_tests.cpp`,
`.github/workflows/opus-sol-s12-alias.yml`.
