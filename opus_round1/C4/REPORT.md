# C4 [Engine NNUE] King-bucketed input layer: trainer + C++ inference (UCI NNUEKingBuckets, default 0) — DONE

Branch `opus-C4` (on `opus-O3`), commits `[C4] ...`. `patch.diff` = `git diff 294dbed HEAD` (engine tree vs the
lock, as the brief prescribes; it therefore also contains O3's refactor); `patch_vs_O3.diff` = C4 alone
(`git diff 0d99f02 HEAD`, same exclusions). UNPROVEN until gated, no Elo claim. Gate spec G-C1 below.

## What was built

| part | where | what |
|---|---|---|
| v2 file format `FORGENN2` | spec in `include/forge/nnue_v2.hpp`; reader/writer `tools/nnue/forge_nnue_v2.py` | 160-byte header (version, hidden, king buckets 1-32, output buckets, flags residual/mirror, scales 4096/4096/2.25, 64-entry king-bucket map, 33-entry output-bucket map reserved for C5), int16 `w1[KB][768][H]`, `b1[H]`, `w2[OB][2H]`, `b2[OB]`, FNV-1a 64 trailer |
| feature set | `nnue_v2.hpp` | per perspective: `bucket = map[own king square]` (perspective frame, before mirroring), `flip = 7` when the own king is on files e-h of a mirrored net, `index = bucket*768 + (rel*6+type)*64 + (r^flip)`; bucket 0 without flip is exactly the lock's `feature_index` |
| loader / selection | `src/nnue.cpp` (all cold) | validates magic, version, sizes, hidden == FORGE_NNUE_HIDDEN, scales, map ranges, reserved bytes, exact file size, checksum; a failed load keeps the previously loaded net |
| inference | `nnue_v2.hpp` (inline kernels), `src/search/evaluation_v2.inc` (`Worker::static_evaluate_v2`, section `.text.forge_v2`) | lazy accumulators in the existing `SearchStack::accumulator` with the lock's walk-back; per-perspective incremental update while the own king keeps its (bucket, flip); on a king-key change that perspective is refreshed through the refresh cache. For an unevaluated intermediate ply the piece placement is rebuilt by taking back the later plies' recorded piece changes, so every replayed ply becomes valid (a first version left those plies invalid and replayed 1.9x more plies: 4.2M vs 2.2M at bench 16) |
| refresh cache | `nnue_v2.hpp` `RefreshCache`, one per worker id, owned by the loaded net | per (perspective, bucket, flip): accumulator + 12 piece bitboards of the placement it holds; a refresh applies only the difference (5.8-6.4 weight columns on average, in chunks of 64 floats); used only on king-key changes and when a ply has no valid ancestor |
| options | `include/forge/search_options.hpp`, `src/search/options.inc`, `src/uci.cpp` | `NNUEFile` (string, default `<empty>`) loads a v2 file; `NNUEKingBuckets` (spin 0-32, default 0): N > 0 evaluates with the loaded net if it has exactly N king buckets, otherwise the compiled-in net with an `info string` saying why; `UseNNUE false` disables every net; each change clears the hash (stored static evals belong to the old net). Nothing new is printed with the defaults |
| search hook | `src/search/evaluation.inc`, `src/search/iterative.inc` | one `if (options::nnue_v2) [[unlikely]]` tail call at the top of `Worker::static_evaluate` (with a 32-byte nop pad in that cold branch, see Layout); the once-per-search driver marks the root accumulator invalid when v2 is active |
| trainer | `tools/nnue/train_resid_v3b.py` (copy of the lock archive's v3b, md5 b6758004, committed verbatim first) | `--king-buckets N` (standard mirrored layouts 1/2/4/6/8/16/32), `--king-map` (any 32/64-entry map), `--king-mirror`, `--king-factor` (shared factoriser block during training, folded on export), `--export-v2`; QAT on q(bucket + factor) and the export writes exactly those integers. Without the new options the trainer is unchanged (outputs byte-identical, acceptance 3) |
| parity tools | `tools/nnue/nnue_v2_tool.cpp` (CMake target `forge_nnue_v2_tool`), `tools/nnue/v2_parity.py` | deterministic positions generator (every piece count 2..32 equally often) and engine-side evaluator; PyTorch-side comparison (acceptance 3) |
| tests | `tests/nnue_v2_tests.cpp` (ctest `forge_nnue_v2_tests`) | 78 checks (acceptance 4 and 6) |
| copied unchanged from the lock archive | `tools/nnue/qa_adam_dml.py` (trainer dependency), `tools/nnue/mkdata_data32_synthetic.py` (generator of 5_nnue/sample_data, used by CI) | |

Standard layouts (`forge_nnue_v2.py half_layout`; half board after mirroring, files a-d, ranks 1..8):
4 buckets `0011 0011 2222 2222 3333 3333 3333 3333`; 8 buckets `0123 4455 6666 7777 7777 7777 7777 7777`.

## Acceptance

| # | acceptance line | result |
|---|---|---|
| 1 | OFF -> bench exact | **PASS**: bench d11/13/16/20/22 = 312866/862329/3024920/12389307/34048354, perft5 4865609, kiwipete 193690690, FMA 0 (PC recipe, `logs/identity_off_pc_recipe.log`) |
| 2 | the lock net loads unchanged | **PASS**: `src/nnue_weights.inc` untouched (md5 22b4b9e2...); the lock net converted to v2 (`forge_nnue_v2.py from-inc`, replica r1) and loaded through `NNUEFile` gives the lock's bench at all 5 depths, and so do 4 more replicas (4 buckets; 2/8/16 mirrored buckets): 25/25 benches equal the pins (`logs/replica_bench_x5.log`) |
| 3 | export parity 10000/10000 PyTorch vs C++ (CPU-smoke-trained net on 5_nnue/sample_data) | **PASS** for a 4-bucket and an 8-bucket mirrored net: file integers == quantised checkpoint; king bucket/flip of both perspectives 10000/10000; accumulators of both perspectives, float32 bits, 10000/10000; network output float32 bits + centipawns 10000/10000; the training-time model forward truncates to the engine's centipawns 10000/10000 (max diff 0.99998 cp = truncation) (`logs/parity_kb4.log`, `logs/parity_kb8.log`). Every bucket/flip and every piece count 2..32 is covered. A planted trainer bug (mirroring from file d) drops it to 8078/10000, FAIL (`logs/parity_planted_trainer_bug.log`). Trainer default path: byte-identical outputs to the original v3b (`logs/trainer_default_identity.log`) |
| 4 | ON incremental == full refresh bit-exact on 100k random make/unmake plies | **PASS**: 102,000 plies (3 random nets x 34,000: 8 mirrored, 32 mirrored, 4 unmirrored buckets) driven through the real `Worker::static_evaluate`; each of the 64,625 accumulators the engine computed was compared bit for bit with a from-scratch refresh, and every evaluation with the oracle: 0 mismatches; 21,435 king-key changes; replays up to 10 plies (`logs/unit_tests.log`). In search: the 5 lock replicas reproduce the lock's node counts (acceptance 2) |
| 5 | ON NPS loss <= 12% vs AL1 at Threads=1 Hash=16 | **PASS on the same tree** (table below): refresh pattern of a mirrored 4-bucket net -5.3% (d16) / -4.1% (d20), of a mirrored 8-bucket net -8.9% / -6.7%. The CPU-smoke nets (synthetic data) measure -12.2% / -13.6% (4 buckets) and -13.3% / -19.9% (8 buckets), but they search different, larger trees with 13-15% more evaluations per node; see the analysis. The loaded PC makes all numbers noisy |
| 6 | unit tests for the bucket map and mirroring | **PASS**: `forge_nnue_v2_tests` 78/78; 10/10 planted bugs caught (`logs/mutation_check.log`) |
| §3 | ctest only the 4 known lines; ASan+UBSan; TSan | **PASS**: CI release/asan/tsan ctest only the 4 known `forge_tests` lines, 0 ASan/UBSan/TSan reports, TSan hook with 2-4 search threads on a v2 net clean; local 17/17 (all but `forge_tests`, which starts a 4-thread search and is left to CI per the brief), only the 6 pre-existing compiler warnings (`logs/ctest_local_release.log`) |
| §5 | layout: OFF hot code identical and at the same address mod 64 | **PASS with one stated change**: every hot function in `codegen_compare.sh` is instruction-identical and at its lock address mod 64 except `Worker::static_evaluate` (same address; +12 instructions = the dispatch, pad and block order). OFF NPS A/B: no slowdown (+1.4% d16, +0.3% d20) |

### 5. NPS (`nps_ab_options.py` = O3's nps_ab.py + per-side options; 10 runs per build per depth, ABBA, fresh processes; cpu = nodes / process CPU seconds, wall = engine nps; shared PC with gate games, self-play and training running, nice 19)

| B (A = AL1 s198 lock exe) | tree | d16 cpu B/A (95% CI) | d20 cpu B/A (95% CI) | d16 / d20 wall |
|---|---|---|---|---|
| C4 exe, options off | same | +1.43% (+0.11 .. +2.76) | +0.33% (-2.81 .. +3.46) | +1.54% / -0.00% |
| v2 path, lock replica r1 (1 bucket, no refreshes) | same | -1.31% (-2.84 .. +0.22) | -1.60% (-4.93 .. +1.74) | -1.17% / -1.46% |
| lock replica rm8 (= refreshes of a mirrored 4-bucket net) | same | **-5.33%** (-6.60 .. -4.07) | **-4.13%** (-6.77 .. -1.48) | -4.80% / -4.02% |
| lock replica rm16 (= refreshes of a mirrored 8-bucket net) | same | **-8.94%** (-10.00 .. -7.88) | **-6.65%** (-9.51 .. -3.78) | -7.93% / -5.99% |
| smoke-trained 4-bucket mirrored net | 4.06M / 24.5M nodes | -12.17% (-13.90 .. -10.44) | -13.58% (-15.52 .. -11.64) | -11.97% / -13.93% |
| smoke-trained 8-bucket mirrored net | 3.34M / 20.1M nodes | -13.34% (-14.10 .. -12.59) | -19.92% (-21.71 .. -18.13) | -12.96% / -20.11% |

Lock replicas evaluate exactly like the lock net, so A and B search the identical tree (node counts equal, checked
on every run) and the difference is the engine cost of king buckets: the rm8/rm16 maps put files e-h in their own
buckets holding the file-flipped lock weights, so a refresh happens exactly where a mirrored 4-/8-bucket net
refreshes. Bench-16 statistics (instrumented copy, `logs/refresh_stats_d16.log`):

| net | evaluations per node | king-key changes per evaluation | weight columns per refresh |
|---|---|---|---|
| lock replica rm8 | 0.596 | 11.3% | 5.79 |
| lock replica rm16 | 0.596 | 16.9% | 5.97 |
| smoke 4-bucket | 0.683 | 8.7% | 6.36 |
| smoke 8-bucket | 0.672 | 14.3% | 6.44 |

The smoke nets (trained on random synthetic boards) refresh no more often than the replicas, but their trees need
13-15% more evaluations per node; that, not the bucket machinery, is most of their extra NPS loss. A net trained on
real games should search lock-like trees; QA should still record NPS d16/d20 with the real net on the PC (test-plan
rule for every net change).

## Layout (OFF build; `logs/codegen_off.log`, `logs/layout_diff_vs_o3.log`)

- All new engine code is outside `.text`: loader/selection cold (`.text.unlikely`), kernels and
  `static_evaluate_v2` in `.text.forge_v2`, inline helpers as COMDATs. The PE linker places those after every
  object's `.text`, so nnue.cpp's and search.cpp's `.text` are unchanged except the two functions below.
- `Worker::static_evaluate` gains the dispatch. GCC emits a caller after its callees, so `evaluation_v2.inc`
  is included before `evaluation.inc` (otherwise GCC emitted static_evaluate later and 16 hot functions moved).
  The dispatch grew the function by 32 bytes; a 32-byte `.nops` pad in its cold branch makes the growth exactly
  64 bytes, so every function after it keeps its address mod 64 (`FORGE_LAYOUT_PAD`, MinGW g++ only; a no-op
  elsewhere). Measured: no OFF slowdown.
- `Worker::search(Board, ...)` (once per iteration): +1 statement; the three functions after it
  (`Searcher::search` and its thread lambda) moved (not hot). uci.cpp code moved (not hot).

## Proposed gate G-C1 (one option: NNUEKingBuckets; the net file is its payload)

- Build: `opus-C4` with the PC recipe. Candidate options: `NNUEFile=<net>.fnn2`, `NNUEKingBuckets=<buckets of
  that net>`; the engine log must show `info string NNUE v2: active ...`. Opponent AL1 s198. SPRT [0,10] at
  10+0.1, srand from the test plan's G-C1 row (QA); confirm at 40+0.4 if H1 (EVAL rule).
- Net (test plan: gate only on the A1 data): `tools/nnue/train_resid_v3b.py` with the lock recipe (f003rec:
  H256, 32 epochs, bs 8192, lr 9.898e-4, warmup 300, blend-end 0.6, residual) plus `--king-buckets 4` (mirror and
  factoriser are the defaults), new seed, holdout 013+014 as for the lock. Each epoch writes `epochNNN.fnn2`.
  Before the gate: `forge_nnue_v2_tool positions p.fen 10000 <seed>`, `forge_nnue_v2_tool eval epochNNN.fnn2
  p.fen cpp`, `python tools/nnue/v2_parity.py epochNNN.pt epochNNN.fnn2 p.fen cpp` must print PASS; then NPS
  d16/d20 with `opus_round1/C4/nps_ab_options.py`.
- DirectML: the bucketed model uses the standard model's ops plus permute/reshape, tensor indexing and argmax;
  verified on CPU only. Run a few hundred steps on the GPU first.

## CI

GitHub Actions on commit 7f6ab7f (code identical to the final branch head; later commits add only this folder's
evidence), logs in `logs/ci/` (`RUN.txt` has the URLs):

| run | job | result |
|---|---|---|
| opus-ci 40410933308 | release (ubuntu-24.04, g++-14.2, box recipe) | bench x5 / perft / kiwipete ALL OK, FMA 0; ctest 17/18, only `forge_tests` with exactly the 4 known lines; `forge_nnue_v2_tests` passed |
| | asan (ASan + UBSan, no recover) | ctest: only the 4 known lines, 0 sanitizer reports (`forge_nnue_v2_tests` 7.5 s, passed) |
| | tsan | ctest: only the 4 known lines, 0 TSan reports; C4 hook `tsan_extra.sh`: v2 replica net active, Threads 4 / 4 / 2 to depth 15 / 10 / 14, bestmove each, 0 reports |
| opus-c4-nnue 40410933298 | Linux evidence (`ci_c4.sh`) | `forge_nnue_v2_tests` 78/78 (102k plies, 0 mismatches); options off ALL OK; lock replicas via UCI 25/25 benches equal the pins; CPU torch 2.4.1 smoke training (4 and 8 mirrored buckets, synthetic data32 records from the archive's generator) + parity on 10000 positions: PASS 10000/10000 on every exact check for both |

## Open issues / notes
- NPS with nets trained on real data is unmeasured (only lock replicas and synthetic-data nets exist here).
- `FORGE_LAYOUT_PAD(32)` is tied to MinGW g++ 15.2 code generation; re-run `codegen_compare.sh` after any
  toolchain change.
- Refresh caches are per worker id and owned by the loaded net: two Searchers must not search at the same time
  with a v2 net active (the engine never does; bench and game searches are sequential).
- `forge_tests` was not run locally (4-thread search); CI runs it.
- A stray object file `C:/Program Files/Git/tmp_nnue.o` (446 KB) was created by a mistyped `-o` path during this
  job; removing it was blocked by the shell safety check. Please delete it.

## Files
`REPORT.md`, `IDEA_SOURCE.md`, `patch.diff`, `patch_vs_O3.diff`, `SHA256SUMS`; scripts `mutation_check.sh`,
`nps_ab_options.py`, `layout_diff.py`, `instrument_refresh_stats.py`, `run1t.py` (1-thread torch wrapper for local
smoke runs), `uci_go.py`, `tsan_extra.sh`, `ci_c4.sh`; data `parity_positions.fen` (10000 positions, sha256
086a11d3...); `logs/`.
