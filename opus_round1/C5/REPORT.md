# C5 [Engine NNUE] Output buckets by piece count (UCI NNUEOutputBuckets, default 0) — DONE

Branch `opus-C5` = `opus-C4` (including the 2026-10-27 review fixes, merged in b3a2e30 and 411029b) + the C5
commits `[C5] ...` (eda37b3, 6ef50d4, 959a3e4, 0321350, 3a2f4fa, 2452bc5, evidence 7e4739a). `patch.diff` =
`git diff 294dbed HEAD` (engine tree vs the lock; it also contains O3 and C4); `patch_vs_C4.diff` = C5 alone
(`git diff 1cc708a HEAD`, same exclusions). UNPROVEN until gated, no Elo claim. Gate spec G-C6 below.

## What was built

| part | where | what |
|---|---|---|
| v2 output field | `include/forge/nnue_v2.hpp`, `tools/nnue/forge_nnue_v2.py` | C4's reserved fields: `output_buckets` 1-16 (header offset 32), `output_bucket_map[33]` (offset 116: total piece count 0..32, kings included -> head), head-major `w2[OB][2H]`, `b2[OB]`. Default map `output_layout(N)`: n = pieces - 2 non-king pieces -> min(N - 1, n*N/32); 8 heads: (pieces - 2)/4 (2-5 -> 0, 6-9 -> 1, ..., 30-32 -> 7) |
| inference | `nnue_v2.hpp` `output_bucket()`, `output()` | head = `output_map[min(popcount(occupied), 32)]` of the evaluated position; its `w2` row and `b2` enter the same 16-lane SCReLU float sum as the compiled-in net; accumulators are not touched (heads only change the output layer) |
| option | `include/forge/search_options.hpp`, `src/search/options.inc`, `src/uci.cpp` | `NNUEOutputBuckets` (spin 0-16, default 0). Selection (`nnue::v2::select`): NNUEKingBuckets > 0 needs exactly that many king buckets (0: one unmirrored bucket), NNUEOutputBuckets > 0 exactly that many heads (0: one head), at least one > 0; a net with king and output buckets needs both options |
| fail-loud rule (C4 review fix, extended) | `options::nnue_v2_problem`, `src/uci.cpp` | NNUEOutputBuckets > 0 is a request, like NNUEKingBuckets > 0 or a non-empty NNUEFile; a head count that does not match the net, both counts 0 while a file is loaded, a count without a file: `info string ERROR NNUE v2: <reason>` at once and exit status 2 at the next isready / go / bench; the message names the settings that select the loaded net (e.g. "to use it set NNUEKingBuckets 0, NNUEOutputBuckets 8") |
| trainer | `tools/nnue/train_resid_v3b.py` | `--output-buckets N` (2-16, default map) and `--output-map` (33 entries); output layer `Linear(2H, N)`, each position uses head `output_map[piece count]` (gather), QAT unchanged; with or without `--king-buckets`; exports `.fnn2` with the output field. Without the new options the trainer is byte-identical to the original v3b and to the C4 trainer |
| tools | `forge_nnue_v2.py` (`from-inc --output-buckets N`: lock replicas with N identical heads), `nnue_v2_tool` (output bucket per position), `v2_parity.py` (checks every position's output bucket; PASS needs the training forward within 1 cp) | |
| tests | `tests/nnue_v2_tests.cpp` (141 checks; C5: default maps, output bucket and head at every piece count 2..32, selection rules, lock replicas with 8 identical heads, 34000-ply walk with 8 mirrored king buckets + 8 heads, fail-loud rule with output buckets), `tests/nnue_v2_uci_tests.cpp` (26 checks, 9 for NNUEOutputBuckets) | |
| CI | `opus_round1/C5/ci_c5.sh` (run by `.github/workflows/opus-c4-nnue.yml` after ci_c4.sh) | lock replicas with 8 identical heads through UCI (bench x5 == pins, each replica active), CPU-torch smoke training of an 8-head net and of a 4-king-bucket + 8-head net, parity on 10000 positions |

## Merge of the C4 review fixes (b3a2e30)

`select()` keeps C5's two counts with C4's messages; the fail-loud rule covers NNUEOutputBuckets (above);
`NNUEKingBuckets` / `NNUEOutputBuckets` share one UCI handler that calls the same state update as `NNUEFile` and
`UseNNUE`; the C4 loader (size check before reading, no net after a failed load) is unchanged and its maximum file
size now includes 16 heads. `ci_c5.sh` counted active lines (now also printed at isready) and checks each
replica instead. The merge changed no hot code (codegen below) and left `static_evaluate_v2` identical.

## Acceptance

| # | acceptance line | result |
|---|---|---|
| 1 | OFF -> bench exact | **PASS**: PC recipe, code commit 2452bc5: bench d11/13/16/20/22 = 312866/862329/3024920/12389307/34048354, perft5 4865609, kiwipete 193690690, FMA 0, compiled-in net md5 22b4b9e2 (`logs/identity_off_pc_recipe.log`); CI release ALL OK (`logs/ci/release/identity.log`) |
| 2 | parity 10000/10000 | **PASS** for a CPU-smoke-trained 8-head net and a 4-king-bucket mirrored + 8-head net (local, merged code): export integers == quantised checkpoint, king keys 10000/10000, output bucket 10000/10000, accumulators (float32 bits) 10000/10000, output (float32 bits and cp) 10000/10000, training forward within 1 cp (max 0.999994 / 0.999992), trunc-equal 10000/10000 (`logs/parity_ob8.log`, `logs/parity_kb4ob8.log`); every piece count 2..32 (323 positions each, 31: 310) and every head (0-6: 1292, 7: 956) covered. Same in CI (`logs/ci/nnue_c5/`). A planted trainer bug (head of pieces - 1) FAILs: trunc-equal 7775/10000, max 176 cp (`logs/parity_planted_trainer_bug.log`) |
| 3 | ON NPS loss <= 3% | **PASS on the same tree**: lock vs C5 with lock replica r1 + 8 identical heads (`NNUEOutputBuckets 8`): cpu -0.98% (d16) / -2.20% (d20); same exe 1 head vs 8 identical heads: -0.64% / +0.11% (the head selection itself costs nothing measurable). A smoke-trained 8-head net measures -12.2% / -16.8%, but it searches another tree with 12.7% more evaluations per node (table below) |
| 4 | tests for the bucket index at every piece count 2..32 | **PASS**: `forge_nnue_v2_tests` 141/141 (`logs/unit_tests.log`): "default 8-bucket map: bucket = (pieces - 2) / 4 at every piece count 2..32", "default maps for 1, 2, 4, 5, 8, 16 buckets: non-decreasing, 2 pieces -> 0, 32 pieces -> N-1, every bucket used", "output_bucket() == (pieces - 2) / 4 on real positions with every piece count 2..32", "evaluate() uses that head at every piece count 2..32 (control net: heads differ only in the bias)"; 8/8 planted bugs caught (`logs/mutation_check.log`) |
| §3 | ctest only the 4 known lines; ASan+UBSan; TSan | **PASS**: CI release/asan/tsan (19 tests) only the 4 known `forge_tests` lines, 0 sanitizer reports, TSan hook clean; local 18/18 without `forge_tests` (`logs/ctest_local_release.log`) |
| §3 | lock replicas with identical heads == the lock | **PASS**: r1 + 8 heads (NNUEOutputBuckets 8) and rm8 + 8 heads (NNUEKingBuckets 8 + NNUEOutputBuckets 8) through UCI: 10/10 benches equal the pins, active line printed (`logs/replica_ob_bench_x5.log`, CI `logs/ci/nnue_c5/replica_ob_bench.log`) |
| §3 | trainer default unchanged | **PASS**: without `--output-buckets` the C5 trainer gives the original v3b's md5s (8 files, default mode) and the C4 trainer's sha256s (`--king-buckets 4` smoke run) (`logs/trainer_default_identity.log`) |
| §5 | layout | **PASS**: hot functions vs the lock exactly as C4 (only `Worker::static_evaluate`, the C4 dispatch, differs; `MovePicker::next` = O3 padding), vs the C4 review-fix exe and vs C5 before the merge 0 differing instructions in every hot function at the same address mod 64 (`logs/codegen_off.log`, `logs/layout_diff_vs_c4.log`) |
| C4 rule | fail-loud with NNUEOutputBuckets | **PASS**: `forge_nnue_v2_uci_tests` 26/26 on the PC-recipe exe (`logs/uci_tests.log`); the C5 engine before the merge: 4/26 (`logs/uci_tests_premerge_engine.log`) |

Raw output (excerpts):

```
$ python 2_build/uci_check.py forge_c5.exe --full                        (logs/identity_off_pc_recipe.log)
bench d11 nodes 312866 ref 312866 OK ... bench d22 nodes 34048354 ref 34048354 OK
perft5 startpos 4865609 ref 4865609 OK
perft5 kiwipete 193690690 ref 193690690 OK
ALL OK                         (FMA count: 0; exe sha256 77d35c9b...)

$ python opus_v2_parity.py smoke_ob8/epoch003....pt smoke_ob8/epoch003....fnn2 parity_positions.fen cpp_ob8   (logs/parity_ob8.log)
export (file ints == quantised checkpoint): OK
keys   (bucket, flip both perspectives):    10000/10000
outbkt (output bucket by piece count):      10000/10000
acc    (both perspectives, float32 bits):   10000/10000
output (engine-order float32 bits and cp):  10000/10000
forward (training model, GEMM order): max |cp diff| 0.999994, trunc equal 10000/10000
PASS
(kb4ob8: the same lines, max 0.999992, PASS)

$ forge_nnue_v2_uci_tests forge_c5.exe                                     (logs/uci_tests.log, C5 part)
PASS output_buckets_without_file: exit status 2 at isready, ... NNUEOutputBuckets 8 is set but no v2 net is loaded (NNUEFile is empty)
PASS output_buckets_vs_1_head: exit status 2 at isready, ... does not match NNUEKingBuckets 2, NNUEOutputBuckets 8; to use it set NNUEKingBuckets 2, NNUEOutputBuckets 0
PASS heads_net_counts_0: exit status 2 at go depth 1, ... is loaded (1 king buckets, 8 output buckets) but NNUEKingBuckets is 0 and NNUEOutputBuckets is 0; ...
PASS heads_net_wrong_count / king_and_heads_net_king_option_only / king_and_heads_net_output_option_only: exit status 2
PASS 8-head net with NNUEOutputBuckets 8: "info string NNUE v2: active: ... king buckets 1 output buckets 8 hidden 256 ..." 3 times, readyok, bestmove, exit 0
PASS 2 king buckets + 8 heads with both options (any order): active, readyok, bench, exit 0
PASS UseNNUE false with NNUEOutputBuckets 8: not an error
26/26 checks passed

$ bash opus_round1/C5/mutation_check.sh <scratch>                           (logs/mutation_check.log)
unmutated: 141/141 checks passed
MUTATION bucket_off_by_one -> caught | bias_of_head_0 -> caught | row_half_offset -> caught | rows_ignored -> caught
MUTATION select_ignores_heads -> caught | max_heads_15 -> caught | rule_ignores_output_buckets -> caught | rule_output_count_unchecked -> caught
mutation_check status=0
```

## ON bench pins (Threads 1, Hash 16; `logs/replica_ob_bench_x5.log`, `logs/bench_on_smoke_nets.log`; d11-d16 repeated identically)

| net | options | d11 | d13 | d16 | d20 | d22 |
|---|---|---|---|---|---|---|
| lock replica r1 + 8 identical heads | NNUEOutputBuckets 8 | 312866 | 862329 | 3024920 | 12389307 | 34048354 |
| lock replica rm8 + 8 identical heads | NNUEKingBuckets 8, NNUEOutputBuckets 8 | 312866 | 862329 | 3024920 | 12389307 | 34048354 |
| smoke 8-head net (sha256 9b09df6c...) | NNUEOutputBuckets 8 | 347579 | 1100105 | 2902266 | 14958675 | 26386215 |
| smoke 4-king-bucket + 8-head net (8ae29d8a...) | NNUEKingBuckets 4, NNUEOutputBuckets 8 | 544057 | 1266127 | 3882123 | 17316510 | 34145186 |

Smoke nets: local CPU training of `logs/smoke_train_ob8.log` / `logs/smoke_train_kb4ob8.log` (scratch copy of the
trainer, `F:/opus_scratch/c5/opus_nnue_smoke.py`, torch 2.4.1+cpu, 1 thread, nice 19, 5_nnue sample data, 3
epochs; scripts in `local/`).

## NPS (`opus_round1/C4/nps_ab_options.py`, 10 runs per side per depth, ABBA, fresh processes; shared PC, nice 19)

| comparison | tree | d16 cpu B/A (95% CI) | d20 cpu B/A (95% CI) | d16 / d20 wall |
|---|---|---|---|---|
| A lock, B C5 with lock replica r1 + 8 identical heads (`logs/nps_on_ob8_replica_vs_lock.log`) | same | -0.98% (-3.59 .. +1.64) | -2.20% (-3.85 .. -0.55) | -3.25% / -2.09% |
| same C5 exe, A replica r1 (1 head), B r1 + 8 identical heads (`logs/nps_ob8_vs_1head_same_exe.log`) | same | -0.64% (-4.31 .. +3.03) | +0.11% (-1.23 .. +1.46) | -0.86% / +0.06% |
| A lock, B C5 with the smoke 8-head net (`logs/nps_on_smoke_ob8_vs_lock.log`) | other (2.90M / 14.96M nodes) | -12.20% (-12.75 .. -11.64) | -16.82% (-24.73 .. -8.91) | -12.12% / -16.81% |

Before the merge (same v2 machine code; `logs/premerge_3a2f4fa2/`) the previous measurements were -0.99% / -1.84%
(lock vs r1 + 8 heads) and -1.35% / +1.45% (1 vs 8 heads). Evaluations per node at bench 16 (instrumented copy,
`logs/eval_stats_d16.log`): replica r1 + 8 heads 0.596, smoke 8-head net 0.672 (+12.7%), which matches the smoke
net's d16 gap: its loss comes from its tree (as for the C4 smoke nets), not from the output buckets. The cost of
the v2 path with heads on the lock tree is about 1-2% CPU; QA should record NPS d16/d20 with the real trained net
(test-plan rule).

## Proposed gate G-C6 (one option: NNUEOutputBuckets; the net file is its payload)

- Build: `opus-C5` with the PC recipe. Candidate options: `NNUEFile=<net>.fnn2`, `NNUEOutputBuckets=8`
  (NNUEKingBuckets stays 0: the gate net has one unmirrored king bucket, so C4's king buckets are not part of this
  gate). The engine log must show `info string NNUE v2: active: <net> king buckets 1 output buckets 8 hidden 256
  unmirrored residual ...` before every `readyok`; a wrong path or count makes the engine exit with status 2 at
  start-up. Opponent AL1 s198, SPRT [0,10] at 10+0.1, srand from the test plan's G-C6 row (817455375; QA
  confirms; never reused); EVAL change, so confirm at 40+0.4 if H1.
- Net: `tools/nnue/train_resid_v3b.py` with the lock recipe (f003rec: H256, 32 epochs, bs 8192, lr 9.898e-4,
  warmup 300, blend-end 0.6, residual) plus `--output-buckets 8` (default map), the lock's data and holdout, new
  seed; each epoch writes `epochNNN.fnn2`. Before the gate: `forge_nnue_v2_tool positions p.fen 10000 <seed>`,
  `forge_nnue_v2_tool eval epochNNN.fnn2 p.fen cpp`, `python tools/nnue/v2_parity.py epochNNN.pt epochNNN.fnn2
  p.fen cpp` must print PASS; NPS d16/d20 with `opus_round1/C4/nps_ab_options.py`.
- DirectML: the head selection adds a `gather` per position; verified on CPU only. Run a few hundred steps on the
  GPU first.

## CI

| run | job | result |
|---|---|---|
| opus-ci 40469887232 (code commit 2452bc5) | release | ALL OK, FMA 0; ctest 18/19, only `forge_tests` with the 4 known lines; `forge_nnue_v2_tests` and `forge_nnue_v2_uci_tests` passed |
| | asan | only the 4 known lines, 0 sanitizer reports |
| | tsan | only the 4 known lines, 0 TSan reports, C4 TSan hook clean |
| opus-c4-nnue 40469887209 | `ci_c4.sh` + `ci_c5.sh` | ci_c4 status 0 (unit 141/141, UCI 26/26, identity ALL OK, 25/25 C4 replica benches); ci_c5 status 0 (replicas with 8 heads 10/10 OK and active; CPU torch smoke of the 8-head and 4-king + 8-head nets; parity PASS 10000/10000) |

Before the merge (3a2f4fa): opus-ci 40464412779 and opus-c4-nnue 40464412827 success; ci_c5.sh ran there (status 0:
replicas 10/10, parity PASS for both nets). Logs in `logs/ci/` (`RUN.txt`). Later commits (411029b, 7e4739a)
change no code and are `[skip ci]`.

## Open issues / notes
- As in C4: a half-set request (e.g. NNUEFile before NNUEOutputBuckets) prints one ERROR line during
  configuration, resolved by the next option; only the state at isready / go / bench decides whether the engine
  exits.
- NPS with a net trained on real games is unmeasured; the smoke nets search different trees.
- The previous agent's pre-merge logs are kept in `logs/premerge_3a2f4fa2/` (original CRLF line ends).
- `forge_tests` was not run locally (4-thread search); CI runs it.

## Files
`REPORT.md`, `IDEA_SOURCE.md`, `patch.diff`, `patch_vs_C4.diff`, `SHA256SUMS`; scripts `ci_c5.sh`,
`mutation_check.sh`, `local/run_smoke.sh`, `local/run_parity.sh`, `local/run_identity.sh` (local smoke training,
parity and trainer identity under F:/opus_scratch/c5 with the copied trainer); `logs/` (identity, codegen, layout,
unit and UCI tests, pre-merge engine UCI test, replica benches, smoke training, parity + planted trainer bug,
trainer identity, NPS x3, eval stats, ON pins, mutation check, local ctest, `ci/`, `premerge_3a2f4fa2/`).

## Notes added by the main session (2026-10-27)
- **Review.** The main session rebuilt opus-C5 `7e4739a`, which contains these fixes, with the PC lock
  recipe and checked:
  - the OFF identity: bench x5, perft and kiwipete exact, FMA 0;
  - the fail-loud rule from outside: `NNUEKingBuckets 4` without a file, and a missing `NNUEFile`, each
    print `info string ERROR NNUE v2: ...` and exit with status 2 at `isready`, with no `readyok` and no
    `bestmove`.

  Log: `opus_round1/C5/logs/review_main_session.log` on opus-C5.
- **Incident.** CPU smoke-training runs of earlier C4/C5 sub-agents were adopted by the PC's NNUE training
  supervisor as if they were its own queue jobs:
  - `runs_kb4_test`, `smoke_kb4`, `smoke_kb8` on 26 Oct;
  - `smoke_kb4ob8`, `runs_c5_kb4` on 27 Oct 08:54.

  The supervisor counted them as failed runs and backed off; see the root REPORT.md on branch
  `opus-summary`. Those runs used the trainer under its own name and run folders named `runs_*` /
  `smoke_kb*`. Later runs use the renamed copy `opus_nnue_smoke.py` under `F:\opus_scratch` and were not
  adopted. Nothing was written to `F:\forge_nnue_train`.
