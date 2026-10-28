# C4 [Engine NNUE] King-bucketed input layer: trainer + C++ inference (UCI NNUEKingBuckets, default 0) — DONE

Branch `opus-C4` (on `opus-O3`), commits `[C4] ...`. `patch.diff` = `git diff 294dbed HEAD` (engine tree vs the
lock, as the brief prescribes; it therefore also contains O3's refactor); `patch_vs_O3.diff` = C4 alone
(`git diff 0d99f02 HEAD`, same exclusions). UNPROVEN until gated, no Elo claim. Gate spec G-C1 below.

## Review fixes (2026-10-27; code commits 9470419, e1028d4, 8fb1383; evidence d9a73ab, 1cc708a)

The code review asked for three changes; all are done, with tests that fail on the old behaviour.

1. **Fail loudly instead of falling back to the compiled-in net.** Before, a failed `NNUEFile` load kept the
   previous net and `NNUEKingBuckets=N` without a matching net evaluated with the compiled-in net plus an
   `info string`, so a gate run could silently play the lock net against itself. Now the rule is
   (`include/forge/search_options.hpp`, `options::nnue_v2_problem`, `src/uci.cpp`):
   - The user **requests** a v2 net with a non-empty `NNUEFile` or `NNUEKingBuckets` > 0.
   - A request that cannot be used is an **error**: file missing or unreadable, wrong size, bad header or
     checksum, `NNUEKingBuckets` different from the net's king buckets (including 0 while a file is loaded),
     `NNUEKingBuckets` > 0 without a loaded file. The engine prints `info string ERROR NNUE v2: <reason>` at once
     (after the `setoption` that caused it). If the request is still unsatisfied at the next `isready`, `go`
     (any `go`, also `go perft`) or `bench`, it prints the error again and **exits with status 2** without
     answering (no `readyok`, no `bestmove`, no bench line). A GUI or fastchess sees an engine that died at
     start-up.
   - Not errors: `UseNNUE false` (every network off on purpose; hand-crafted eval only; a v2 request is
     ignored while it lasts and is checked again when `UseNNUE` becomes true) and `NNUEFile <empty>` (the
     advertised default; clears the file part of the request and unloads the net).
   - A failed load leaves **no** net loaded (the previously loaded net is unloaded first), so a stale net can
     never be used.
   - Option order does not matter: a half-set request (`NNUEFile` before `NNUEKingBuckets`, or the reverse) is
     reported at once as the rule asks and is resolved by the next option; only the state at `isready` / `go` /
     `bench` decides whether the engine exits.
   - Defaults (no NNUE option set): nothing new is printed, the engine is the lock (identity below).
2. **File size checked before reading.** `nnue::v2::load()` seeks to the end for the size, rejects a file
   shorter than a header (< 168 bytes) or larger than the largest valid v2 file (32 king buckets: 12,584,618
   bytes) before reading anything, reads only the 160 header bytes, validates them, and rejects a file whose
   size differs from the size the header implies (`file_bytes(king_buckets, output_buckets)`) before the weight
   blocks are allocated or read. `last_load_bytes_read()` lets the tests check this (160 bytes for every
   size-mismatch case, 0 for too short / too large).
3. **Shown to be active.** While a v2 net is in use the engine prints
   `info string NNUE v2: active: <file> king buckets <N> output buckets <M> hidden <H> mirrored|unmirrored
   residual|stand-alone fnv1a <checksum>` once when it becomes active and before every `readyok`.

All new engine code is cold (`[[gnu::cold]]` loader and rule) or in uci.cpp (linked last); the hot code is
instruction-identical to the previous C4 build and the v2 evaluation function too (below), so the earlier
NPS, parity and incremental-update evidence still describes this code.

### Review-fix acceptance

| # | requirement | result |
|---|---|---|
| R1 | unusable request: ERROR at once, again at isready / go, then nonzero exit; UseNNUE false and `<empty>` are not errors; defaults unchanged | **PASS**: `forge_nnue_v2_uci_tests` 17/17 on the PC-recipe exe (`logs/uci_tests.log`), CI release / ASan+UBSan / TSan and the nnue job (`logs/ci/`); transcripts of every case in `logs/failloud_transcripts.log` (script `failloud_transcripts.sh`) |
| R2 | size checked before reading; truncated file rejected without reading the body; too short / too large rejected | **PASS**: `forge_nnue_v2_tests` 101/101 (`logs/unit_tests.log`): truncated by 2 bytes, cut in half, 2 extra bytes, header claiming 32 buckets on a 4-bucket file: "does not match ... the weights were not read" after reading 160 bytes; 8-byte and 167-byte files "too short", a file 1 byte above the maximum "too large", 0 bytes read; every failed load leaves no net |
| R3 | active line + bench with a really bucketed net (node counts differ from OFF) next to the OFF bench at the lock pins | **PASS**: `logs/active_bench_smoke_kb4.log` (below) |
| R4 | tests fail on the old behaviour; planted bugs | **PASS**: the UCI test against the previous C4 engine: 3/17 (`logs/uci_tests_old_engine.log`); 13/13 planted bugs in the new code caught (`logs/mutation_check_failloud.log`) |
| R5 | OFF identity and OFF codegen as in the C4 report | **PASS**: bench x5 / perft / kiwipete exact, FMA 0 (`logs/identity_off_pc_recipe.log`); hot functions vs the lock exactly as before, vs the previous C4 exe 0 differing instructions in every hot function, same address mod 64 (`logs/codegen_off.log`, `logs/layout_diff_vs_previous_c4.log`) |

Raw output (excerpts):

```
$ forge_nnue_v2_uci_tests forge_c4fix.exe          (logs/uci_tests.log)
PASS defaults: exit 0, readyok, bestmove, no NNUE v2 line
PASS missing_file_isready: exit status 2 at isready, 3 ERROR lines, no answer: info string ERROR NNUE v2: cannot load NNUEFile nnue_v2_uci_missing.fnn2: cannot open nnue_v2_uci_missing.fnn2
PASS missing_file_go: exit status 2 at go depth 1, 3 ERROR lines, no answer: ...
PASS missing_file_bench: exit status 2 at bench 2, 3 ERROR lines, no answer: ...
PASS truncated_file: exit status 2 at isready, 3 ERROR lines, no answer: info string ERROR NNUE v2: cannot load NNUEFile nnue_v2_uci_truncated.fnn2: file size 788136 bytes does not match the 788138 bytes implied by its header (2 king buckets, 1 output buckets, hidden 256); the weights were not read
PASS damaged_file: exit status 2 at isready, 3 ERROR lines, no answer: ... checksum mismatch (file damaged)
PASS wrong_bucket_count: exit status 2 at isready, 3 ERROR lines, no answer: info string ERROR NNUE v2: NNUEKingBuckets 4 does not match NNUEFile nnue_v2_uci_valid.fnn2 (2 king buckets)
PASS buckets_without_file: exit status 2 at go depth 1, 2 ERROR lines, no answer: info string ERROR NNUE v2: NNUEKingBuckets 2 is set but no v2 net is loaded (NNUEFile is empty)
PASS file_with_buckets_0: exit status 2 at isready, 2 ERROR lines, no answer: ... is loaded (2 king buckets) but NNUEKingBuckets is 0; set NNUEKingBuckets 2 to use it
PASS failed_reload_after_good_net: exit status 2 at isready, 3 ERROR lines, no answer: ... cannot open nnue_v2_uci_missing.fnn2
PASS usennue_true_again: exit status 2 at isready, 2 ERROR lines, no answer: ...
PASS valid net: exit 0, "info string NNUE v2: active: nnue_v2_uci_valid.fnn2 king buckets 2 output buckets 1 hidden 256 ..." printed 3 times (activation + 2 isready), readyok, bestmove
PASS valid net: NNUEFile before NNUEKingBuckets reports the half-set request once (...), resolved by NNUEKingBuckets 2
PASS NNUEKingBuckets before NNUEFile: active, readyok, exit 0
PASS valid net: bench runs, exit 0
PASS UseNNUE false with a v2 request: not an error (exit 0, readyok, bestmove)
PASS NNUEKingBuckets 0 + NNUEFile <empty>: request cleared, compiled-in net, exit 0
17/17 checks passed

$ forge_nnue_v2_uci_tests forge_c4.exe             (previous C4 engine; logs/uci_tests_old_engine.log)
FAIL missing_file_isready: exit status 0 at isready, 0 ERROR lines, ANSWERED (readyok / bestmove / bench): (no ERROR line)
... (13 more FAIL lines: every unusable request answered with exit 0)
3/17 checks passed

$ python tools/nnue/bench_options.py forge_c4fix.exe 11,13,16,20,22 --expect <lock pins>      (OFF; logs/active_bench_smoke_kb4.log)
bench d11 nodes 312866 time_ms 170 nps 1840388 OK
bench d13 nodes 862329 time_ms 469 nps 1838654 OK
bench d16 nodes 3024920 time_ms 1558 nps 1941540 OK
bench d20 nodes 12389307 time_ms 6356 nps 1949230 OK
bench d22 nodes 34048354 time_ms 16449 nps 2069934 OK

$ python tools/nnue/bench_options.py forge_c4fix.exe 11,13,16,20,22 --set NNUEFile=smoke_kb4.fnn2 --set NNUEKingBuckets=4
info string NNUE v2: loaded .../smoke_kb4.fnn2 king buckets 4 output buckets 1 hidden 256 mirrored residual fnv1a 971f7ad982fc3b3f
info string ERROR NNUE v2: NNUEFile .../smoke_kb4.fnn2 is loaded (4 mirrored king buckets) but NNUEKingBuckets is 0; set NNUEKingBuckets 4 to use it
info string NNUE v2: active: .../smoke_kb4.fnn2 king buckets 4 output buckets 1 hidden 256 mirrored residual fnv1a 971f7ad982fc3b3f
info string NNUE v2: active: .../smoke_kb4.fnn2 king buckets 4 output buckets 1 hidden 256 mirrored residual fnv1a 971f7ad982fc3b3f
bench d11 nodes 449096 time_ms 268 nps 1675731
bench d13 nodes 1244609 time_ms 746 nps 1668376
bench d16 nodes 4057897 time_ms 2448 nps 1657637
bench d20 nodes 24478226 time_ms 14816 nps 1652148
bench d22 nodes 35855314 time_ms 22431 nps 1598471
```
(The smoke net is the C4 job's CPU-smoke-trained 4-king-bucket mirrored net, `epoch003` of
`logs/smoke_train_kb4.log`, sha256 692adca9...; d11-d20 equal the C4 ON pins in `logs/bench_on_smoke_nets.log`,
d11-d16 repeated identically. The ERROR line after `NNUEFile` is the half-set request, resolved by
`NNUEKingBuckets 4`; the second active line is the one printed at `isready`.)

```
$ bash opus_round1/C4/mutation_check_failloud.sh <scratch>     (logs/mutation_check_failloud.log)
unmutated: unit 101/101 checks passed | uci 17/17 checks passed
MUTATION keep_previous_net_on_failure -> caught: 24 failing checks
MUTATION weights_read_before_size_check -> caught: 5 failing checks
MUTATION no_too_large_check -> caught: 1 failing checks
MUTATION usennue_false_is_an_error -> caught: 2 failing checks
MUTATION file_with_buckets_0_is_fine -> caught: 3 failing checks
MUTATION silent_fallback_on_mismatch -> caught: 2 failing checks
MUTATION failed_load_is_fine -> caught: 8 failing checks
MUTATION isready_no_exit -> caught: 7 failing checks
MUTATION go_no_exit -> caught: 2 failing checks
MUTATION bench_no_exit -> caught: 1 failing checks
MUTATION exit_status_0 -> caught: 10 failing checks
MUTATION no_active_line_at_isready -> caught: 2 failing checks
MUTATION no_error_at_once -> caught: 11 failing checks
mutation_check_failloud status=0
```

## What was built

| part | where | what |
|---|---|---|
| v2 file format `FORGENN2` | spec in `include/forge/nnue_v2.hpp`; reader/writer `tools/nnue/forge_nnue_v2.py` | 160-byte header (version, hidden, king buckets 1-32, output buckets, flags residual/mirror, scales 4096/4096/2.25, 64-entry king-bucket map, 33-entry output-bucket map reserved for C5), int16 `w1[KB][768][H]`, `b1[H]`, `w2[OB][2H]`, `b2[OB]`, FNV-1a 64 trailer |
| feature set | `nnue_v2.hpp` | per perspective: `bucket = map[own king square]` (perspective frame, before mirroring), `flip = 7` when the own king is on files e-h of a mirrored net, `index = bucket*768 + (rel*6+type)*64 + (r^flip)`; bucket 0 without flip is exactly the lock's `feature_index` |
| loader / selection | `src/nnue.cpp` (all cold) | file size by seeking first (too short / too large / not the size the header implies: rejected before the weights are allocated or read), then magic, version, sizes, hidden == FORGE_NNUE_HIDDEN, scales, map ranges, reserved bytes, checksum; the previous net is unloaded first, so a failed load leaves no net |
| inference | `nnue_v2.hpp` (inline kernels), `src/search/evaluation_v2.inc` (`Worker::static_evaluate_v2`, section `.text.forge_v2`) | lazy accumulators in the existing `SearchStack::accumulator` with the lock's walk-back; per-perspective incremental update while the own king keeps its (bucket, flip); on a king-key change that perspective is refreshed through the refresh cache. For an unevaluated intermediate ply the piece placement is rebuilt by taking back the later plies' recorded piece changes, so every replayed ply becomes valid (a first version left those plies invalid and replayed 1.9x more plies: 4.2M vs 2.2M at bench 16) |
| refresh cache | `nnue_v2.hpp` `RefreshCache`, one per worker id, owned by the loaded net | per (perspective, bucket, flip): accumulator + 12 piece bitboards of the placement it holds; a refresh applies only the difference (5.8-6.4 weight columns on average, in chunks of 64 floats); used only on king-key changes and when a ply has no valid ancestor |
| options | `include/forge/search_options.hpp`, `src/search/options.inc`, `src/search/evaluation_v2.inc`, `src/uci.cpp` | `NNUEFile` (string, default `<empty>`) loads a v2 file; `NNUEKingBuckets` (spin 0-32, default 0): N > 0 evaluates with the loaded net if it has exactly N king buckets; fail-loud rule above (`options::nnue_v2_problem`; ERROR at once, exit status 2 at isready / go / bench); active line at activation and every isready; `UseNNUE false` disables every net; each change clears the hash (stored static evals belong to the old net). Nothing new is printed with the defaults |
| search hook | `src/search/evaluation.inc`, `src/search/iterative.inc` | one `if (options::nnue_v2) [[unlikely]]` tail call at the top of `Worker::static_evaluate` (with a 32-byte nop pad in that cold branch, see Layout); the once-per-search driver marks the root accumulator invalid when v2 is active |
| trainer | `tools/nnue/train_resid_v3b.py` (copy of the lock archive's v3b, md5 b6758004, committed verbatim first) | `--king-buckets N` (standard mirrored layouts 1/2/4/6/8/16/32), `--king-map` (any 32/64-entry map), `--king-mirror`, `--king-factor` (shared factoriser block during training, folded on export), `--export-v2`; QAT on q(bucket + factor) and the export writes exactly those integers. Without the new options the trainer is unchanged (outputs byte-identical, acceptance 3) |
| parity tools | `tools/nnue/nnue_v2_tool.cpp` (CMake target `forge_nnue_v2_tool`), `tools/nnue/v2_parity.py` | deterministic positions generator (every piece count 2..32 equally often) and engine-side evaluator; PyTorch-side comparison (acceptance 3) |
| bench helper | `tools/nnue/bench_options.py` | bench through UCI with options; exits 1 when the engine exits early or returns fewer bench lines than depths (an unusable v2 request) |
| tests | `tests/nnue_v2_tests.cpp` (ctest `forge_nnue_v2_tests`), `tests/nnue_v2_uci_tests.cpp` (ctest `forge_nnue_v2_uci_tests`, runs the `forge` executable) | 101 checks (acceptance 4 and 6, loader size checks, request rule) and 17 UCI-level checks (fail-loud rule) |
| copied unchanged from the lock archive | `tools/nnue/qa_adam_dml.py` (trainer dependency), `tools/nnue/mkdata_data32_synthetic.py` (generator of 5_nnue/sample_data, used by CI) | |

Standard layouts (`forge_nnue_v2.py half_layout`; half board after mirroring, files a-d, ranks 1..8):
4 buckets `0011 0011 2222 2222 3333 3333 3333 3333`; 8 buckets `0123 4455 6666 7777 7777 7777 7777 7777`.

## Acceptance

| # | acceptance line | result |
|---|---|---|
| 1 | OFF -> bench exact | **PASS**: bench d11/13/16/20/22 = 312866/862329/3024920/12389307/34048354, perft5 4865609, kiwipete 193690690, FMA 0 (PC recipe, review-fix commit 8fb1383, `logs/identity_off_pc_recipe.log`) |
| 2 | the lock net loads unchanged | **PASS**: `src/nnue_weights.inc` untouched (md5 22b4b9e2...); the lock net converted to v2 (`forge_nnue_v2.py from-inc`, replica r1) and loaded through `NNUEFile` gives the lock's bench at all 5 depths, and so do 4 more replicas (4 buckets; 2/8/16 mirrored buckets): 25/25 benches equal the pins (`logs/replica_bench_x5.log`; on the review-fix code in CI, `logs/ci/nnue/replica_bench.log`: 25/25 OK and every replica printed the active line) |
| 3 | export parity 10000/10000 PyTorch vs C++ (CPU-smoke-trained net on 5_nnue/sample_data) | **PASS** for a 4-bucket and an 8-bucket mirrored net: file integers == quantised checkpoint; king bucket/flip of both perspectives 10000/10000; accumulators of both perspectives, float32 bits, 10000/10000; network output float32 bits + centipawns 10000/10000; the training-time model forward truncates to the engine's centipawns 10000/10000 (max diff 0.99998 cp = truncation) (`logs/parity_kb4.log`, `logs/parity_kb8.log`; on the review-fix code in CI: `logs/ci/nnue/parity_kb4.log`, `parity_kb8.log`, PASS). Every bucket/flip and every piece count 2..32 is covered. A planted trainer bug (mirroring from file d) drops it to 8078/10000, FAIL (`logs/parity_planted_trainer_bug.log`). Trainer default path: byte-identical outputs to the original v3b (`logs/trainer_default_identity.log`) |
| 4 | ON incremental == full refresh bit-exact on 100k random make/unmake plies | **PASS**: 102,000 plies (3 random nets x 34,000: 8 mirrored, 32 mirrored, 4 unmirrored buckets) driven through the real `Worker::static_evaluate`; each of the 64,625 accumulators the engine computed was compared bit for bit with a from-scratch refresh, and every evaluation with the oracle: 0 mismatches; 21,435 king-key changes; replays up to 10 plies (`logs/unit_tests.log`). In search: the 5 lock replicas reproduce the lock's node counts (acceptance 2) |
| 5 | ON NPS loss <= 12% vs AL1 at Threads=1 Hash=16 | **PASS on the same tree** (table below): refresh pattern of a mirrored 4-bucket net -5.3% (d16) / -4.1% (d20), of a mirrored 8-bucket net -8.9% / -6.7%. The CPU-smoke nets (synthetic data) measure -12.2% / -13.6% (4 buckets) and -13.3% / -19.9% (8 buckets), but they search different, larger trees with 13-15% more evaluations per node; see the analysis. The loaded PC makes all numbers noisy. Measured before the review fix; the review fix leaves `Worker::static_evaluate_v2` instruction-identical (2495 instructions, 0 differing, address 0 mod 64 in both builds, `logs/codegen_off.log`) |
| 6 | unit tests for the bucket map and mirroring | **PASS**: `forge_nnue_v2_tests` 101/101 (78 original + 23 for the review fix); 10/10 planted bugs caught (`logs/mutation_check.log`), 13/13 for the review fix (`logs/mutation_check_failloud.log`) |
| §3 | ctest only the 4 known lines; ASan+UBSan; TSan | **PASS**: CI release/asan/tsan ctest (19 tests) only the 4 known `forge_tests` lines, 0 ASan/UBSan/TSan reports, `forge_nnue_v2_tests` and `forge_nnue_v2_uci_tests` passed in all three, TSan hook with 2-4 search threads on a v2 net clean; local 18/18 (all but `forge_tests`, which starts a 4-thread search and is left to CI per the brief), only the 6 pre-existing compiler warnings (`logs/ctest_local_release.log`) |
| §5 | layout: OFF hot code identical and at the same address mod 64 | **PASS with one stated change**: every hot function in `codegen_compare.sh` is instruction-identical and at its lock address mod 64 except `Worker::static_evaluate` (same address; +12 instructions = the dispatch, pad and block order). The review fix changed no hot function (0 differing instructions vs the previous C4 exe in every hot function; only cold loader / rule functions and uci.cpp code moved, `logs/layout_diff_vs_previous_c4.log`). OFF NPS A/B: no slowdown (+1.4% d16, +0.3% d20) |

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

## Layout (OFF build; `logs/codegen_off.log`, `logs/layout_diff_vs_o3.log`, `logs/layout_diff_vs_previous_c4.log`)

- All new engine code is outside `.text`: loader/selection/request rule cold (`.text.unlikely`), kernels and
  `static_evaluate_v2` in `.text.forge_v2`, inline helpers as COMDATs. The PE linker places those after every
  object's `.text`, so nnue.cpp's and search.cpp's `.text` are unchanged except the two functions below.
- `Worker::static_evaluate` gains the dispatch. GCC emits a caller after its callees, so `evaluation_v2.inc`
  is included before `evaluation.inc` (otherwise GCC emitted static_evaluate later and 16 hot functions moved).
  The dispatch grew the function by 32 bytes; a 32-byte `.nops` pad in its cold branch makes the growth exactly
  64 bytes, so every function after it keeps its address mod 64 (`FORGE_LAYOUT_PAD`, MinGW g++ only; a no-op
  elsewhere). Measured: no OFF slowdown.
- `Worker::search(Board, ...)` (once per iteration): +1 statement; the three functions after it
  (`Searcher::search` and its thread lambda) moved (not hot). uci.cpp code moved (not hot; uci.cpp is the last
  object of the PC recipe, so its growth from the review fix moves nothing else).

## Proposed gate G-C1 (one option: NNUEKingBuckets; the net file is its payload)

- Build: `opus-C4` with the PC recipe. Candidate options: `NNUEFile=<net>.fnn2`, `NNUEKingBuckets=<buckets of
  that net>`; the engine prints `info string NNUE v2: active: <net> king buckets <N> ...` before every `readyok`
  (check one game log). An engine that cannot use the requested net exits with status 2 at the first `isready`,
  so a wrong path or bucket count shows up as an engine failure at start-up, never as a lock-vs-lock match.
  Opponent AL1 s198. SPRT [0,10] at 10+0.1, srand from the test plan's G-C1 row (QA); confirm at 40+0.4 if H1
  (EVAL rule).
- Net (test plan: gate only on the A1 data): `tools/nnue/train_resid_v3b.py` with the lock recipe (f003rec:
  H256, 32 epochs, bs 8192, lr 9.898e-4, warmup 300, blend-end 0.6, residual) plus `--king-buckets 4` (mirror and
  factoriser are the defaults), new seed, holdout 013+014 as for the lock. Each epoch writes `epochNNN.fnn2`.
  Before the gate: `forge_nnue_v2_tool positions p.fen 10000 <seed>`, `forge_nnue_v2_tool eval epochNNN.fnn2
  p.fen cpp`, `python tools/nnue/v2_parity.py epochNNN.pt epochNNN.fnn2 p.fen cpp` must print PASS; then NPS
  d16/d20 with `opus_round1/C4/nps_ab_options.py`.
- DirectML: the bucketed model uses the standard model's ops plus permute/reshape, tensor indexing and argmax;
  verified on CPU only. Run a few hundred steps on the GPU first.

## CI

GitHub Actions on the review-fix code commit 8fb1383, logs in `logs/ci/` (`RUN.txt` has the URLs; the later
evidence commits d9a73ab and 1cc708a are `[skip ci]`):

| run | job | result |
|---|---|---|
| opus-ci 40468116077 | release (ubuntu-24.04, g++-14.2, box recipe) | bench x5 / perft / kiwipete ALL OK, FMA 0; ctest 18/19, only `forge_tests` with exactly the 4 known lines; `forge_nnue_v2_tests` and `forge_nnue_v2_uci_tests` passed |
| | asan (ASan + UBSan, no recover) | ctest: only the 4 known lines, 0 sanitizer reports (`forge_nnue_v2_tests` 6.2 s, `forge_nnue_v2_uci_tests` 2.3 s, passed) |
| | tsan | ctest: only the 4 known lines, 0 TSan reports; C4 hook `tsan_extra.sh`: v2 replica net active, Threads 4 / 4 / 2 to depth 15 / 10 / 14, bestmove each, 0 reports |
| opus-c4-nnue 40468116040 | Linux evidence (`ci_c4.sh`) | `forge_nnue_v2_tests` 101/101 (102k plies, 0 mismatches); `forge_nnue_v2_uci_tests` 17/17; options off ALL OK; lock replicas via UCI 25/25 benches equal the pins, each replica active; CPU torch 2.4.1 smoke training (4 and 8 mirrored buckets, synthetic data32 records from the archive's generator) + parity on 10000 positions: PASS 10000/10000 on every exact check for both |

Before the review fix (code 98f479a): opus-ci 40462318709 and opus-c4-nnue 40462318800, both success.

## Open issues / notes
- A half-set request prints one `info string ERROR NNUE v2:` line during configuration (e.g. `NNUEFile` sent
  before `NNUEKingBuckets`, as fastchess does for `option.NNUEFile=... option.NNUEKingBuckets=...`), because the
  rule asks for the error at once; the next option resolves it and the engine then prints the active line. If QA
  prefers a quieter log, that one line (`nnue_v2_changed` in uci.cpp) can print a non-ERROR note instead; the
  exit at isready / go / bench would stay.
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
`mutation_check_failloud.sh`, `failloud_transcripts.sh`, `nps_ab_options.py`, `layout_diff.py`,
`instrument_refresh_stats.py`, `run1t.py` (1-thread torch wrapper for local smoke runs), `uci_go.py`,
`tsan_extra.sh`, `ci_c4.sh`; data `parity_positions.fen` (10000 positions, sha256 f6b14e48...); `logs/` (review
fix: `uci_tests.log`, `uci_tests_old_engine.log`, `failloud_transcripts.log`, `active_bench_smoke_kb4.log`,
`mutation_check_failloud.log`, `layout_diff_vs_previous_c4.log`, and re-made `identity_off_pc_recipe.log`,
`codegen_off.log`, `unit_tests.log`, `ctest_local_release.log`, `ci/`).

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
