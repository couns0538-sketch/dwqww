# O4 [test plan G-A5] Pure NNUE, no hand-crafted evaluation (UCI PureNnue, default 0) — DONE

Branch `opus-O4` (from `origin/opus-C4` d9a73ab3; C4's later commits touch only its report). Code commit 61d6314e,
head 42d2e4e6. `patch.diff` = `git diff 294dbed HEAD`, so it contains O3 + C4 + O4 as the brief prescribes;
`patch_vs_C4.diff` = O4 alone. UNPROVEN until gated; no Elo claim.

## What was built
| part | where | what |
|---|---|---|
| UCI `PureNnue` (spin 0-1, default 0; `true`/`false` accepted) | `src/uci.cpp`, `include/forge/search_options.hpp`, `src/search/options.inc` | 1 = the evaluation is the network alone. It needs a stand-alone v2 net (header flag residual = 0) in `NNUEFile`. With `NNUEKingBuckets 0` that net must have one bucket (the lock's input layer); with `NNUEKingBuckets N` it must have exactly N |
| selection and the fail-loud rule | `src/search/evaluation_v2.inc` (`apply_nnue_v2`, `nnue_v2_problem`, both cold) | The header flag and PureNnue must agree both ways. PureNnue 1 with a residual net, and PureNnue 0 with a stand-alone net, are C4-style errors: `info string ERROR NNUE v2: …` at once, then exit 2 at the next isready/go/bench. PureNnue 1 counts as a v2 request on its own. UseNNUE false still wins |
| evaluation path | C4's code, unchanged | C4's `static_evaluate_v2` already returns the network alone for a stand-alone net and never builds the HCE PSQT accumulator. The rule above makes that happen exactly when PureNnue is 1. There is no new hot code: all 23 functions checked by `codegen_compare.sh` are identical to C4's, at the same addresses mod 64 |
| trainer `--pure` | `tools/nnue/train_resid_v3b.py` | `logit = net(x)` with no HCE term; the target blend is unchanged. Every epoch also writes `.fnn2` (residual flag 0). `--hce-dir` becomes optional: it only feeds the HCE-alone baseline report; without it the HCE column is zeros, also with `--mmap-data`. The option refuses `--residual` and `--init-check`. Without `--pure` every output is byte-identical to C4's trainer |
| engine-level evaluator | `tools/nnue/nnue_engine_eval.cpp` (target `forge_nnue_engine_eval`) | Evaluates a FEN list through the real `Worker::static_evaluate` with UCI-style options, next to the network alone and HCE + network. `--walk` is an evaluation-cost benchmark on one identical make/unmake walk |
| tests | `tests/pure_nnue_tests.cpp` (ctest `forge_pure_nnue_tests`, 62 checks) | the rules; network-only evaluation over 4 × 12,000-ply walks, with every accumulator equal to a full refresh; the HCE PSQT is never built; a residual-twin control; search determinism; UCI checks |
| scripts and CI | `opus_round1/O4/` and `.github/workflows/opus-o4-nnue.yml` | `local_cpu_checks.sh`, `local_nps.sh`, `mutation_check.sh`, `ci_o4.sh`, `mkdata_material.py`, `standalone_copy.py`, `opus_nnue_smoke_run1t.py` |

**Behaviour change vs C4 (this branch only):** a stand-alone v2 net with PureNnue 0 is now an error. C4 evaluated
such a net without HCE because of its header flag. No C4 net or test used a stand-alone net.

**Option type:** PureNnue is a spin 0-1 (true/false still accepted) so that `PureNnue=1` as written in the prompt works.

## Acceptance
| # | line | result | command → output |
|---|---|---|---|
| 1 | OFF → bench exact; lock net unchanged | **PASS** | `python <archive>/2_build/uci_check.py forge_o4_v3.exe --full` (PC recipe build) → d11/13/16/20/22 = 312866/862329/3024920/12389307/34048354, perft5 4865609, kiwipete 193690690, ALL OK; FMA 0 (`logs/identity_off_pc_recipe.log`). CI identity also ALL OK. `src/nnue_weights.inc` is untouched. C4's replicas r1/rm8 through UCI: 10/10 benches equal the pins (`logs/ci/replica_bench.log`). `codegen_compare.sh`: 0 differing instructions vs C4; vs the lock only C4's 3 known changes (MovePicker::next padding, the static_evaluate dispatch, Worker::search(Board,)). OFF NPS on a quiet runner, lock vs O4: d16 −0.04% (95% CI −1.75 .. +1.66), d20 +0.06% (−0.76 .. +0.88) |
| 2 | trainer CPU smoke on 5_nnue/sample_data converges | **PASS** | `bash opus_round1/O4/local_cpu_checks.sh /f/opus_scratch/o4/r4 <build>` (copy named `opus_nnue_smoke.py`, CPU torch 2.4.1, 1 thread, nice 19). `--pure --hce-dir`: training MSE 0.0736 → 0.0596 → 0.0521 over 3 epochs, no divergence. The holdout stays at about 0.084 because the sample's scores are board-independent noise (its HCE column is 0.7·score + noise, which is why HCE-alone scores 0.0219); this is a pipeline check only. `--pure --mmap-data` without `.hce` also runs. `--pure --residual` and a missing `--hce-dir` are refused. Learnability check on material-labelled synthetic data (`mkdata_material.py`, no `.hce`): holdout teacher MSE 0.001142 → 0.000831 → 0.000778 → 0.000658, against 0.136 for predicting the mean. The default paths give byte-identical outputs to C4's trainer in 4 configurations, locally and in CI |
| 3 | export parity PyTorch vs C++ 10000/10000 | **PASS** | `forge_nnue_v2_tool eval <net> parity_positions.fen <p>` + `v2_parity.py <pt> <net> <fen> <p>` for the sample net and the material net: export integers OK; keys, accumulators and output 10000/10000; forward truncation 10000/10000 (local and CI). Engine level: `forge_nnue_engine_eval <fen> <tsv> NNUEFile=<net> PureNnue=1` → engine == network alone 10000/10000 (engine == clamp(HCE + network) only 339/10000, so the HCE really is skipped). Planted trainer bug (pure net exported with the residual flag): parity export MISMATCH → FAIL, and the engine refuses that net with exit 2 |
| 4 | NPS ON vs OFF at d16/d20 | **reported** | see NPS below |
| 5 | exact GPU training recipe | **delivered** | see GPU recipe below |
| §3 | ctest, ASan+UBSan, TSan; planted bugs | **PASS** | CI 40476602161: release/asan/tsan ctest show only the 4 known `forge_tests` lines (check PASS); `forge_pure_nnue_tests` passes under all three. Locally 62/62; C4 suites 101/101 and 17/17. Planted engine bugs: 6/6 caught (`logs/mutation_check_part*.log`) |

CI runs: opus-ci 40476602161, opus-o4-nnue 40476602414 (both success).

## NPS (Threads 1, Hash 16)
- **Evaluation cost on one identical walk** (`forge_nnue_engine_eval --walk 3000000`): lock weights + HCE (replica r1)
  against the same weights flagged stand-alone with PureNnue. Locally 759 vs 526 ns per ply, so the HCE costs about
  233 ns (31%). In CI 976 vs 655 ns, about 321 ns (33%).
- **Bench, PureNnue + material-trained pure smoke net vs options off** (a different evaluation searches a different tree):
  - local, 10 runs ABBA, machine exclusive: no — d16 +16.9% wall / +19.8% CPU (3.02M → 5.67M nodes); d20 +16.1% / +15.9% (12.39M → 27.28M nodes)
  - CI quiet runner — d16 +21.3% / +22.0%; d20 +16.3% / +16.9%
- QA should record d16/d20 NPS with the GPU-trained pure net.

## ON bench pins (node counts depend on the net; `logs/on_bench_pins_local.log`)
| net (fnv1a) | d11 | d13 | d16 | d20 |
|---|---|---|---|---|
| material-trained pure smoke net 1544ea643b9cd9a7 | 450072 | 1280779 | 5669969 | 27276967 |
| sample-data pure smoke net a553bca768cf3e93 (learned noise, so trees explode) | 4288758 | 36574413 | 88714337 | 828941759 |

## GPU recipe (QA runs it on the PC; same width and same data as the lock net f003rec_s198)
1. Copy this branch's `tools/nnue/train_resid_v3b.py` to `F:\forge_nnue_train\tools\train_resid_v3b_o4.py`, with
   `tools/nnue/forge_nnue_v2.py` next to it (the `.fnn2` writer). Do not overwrite the live trainer.
2. Run the lock run's `cmd.txt`, with `--residual --init-check` replaced by `--pure` and a new run folder:
   `python -u train_resid_v3b_o4.py --guard-tag train_resid_v2.py --pure --train D:\grok-pc-data\forge_push\nnue_data\pos\forge_selfplay_{001..012,015..023}.pos --holdout D:\grok-pc-data\forge_push\nnue_data\pos\forge_selfplay_013.pos D:\grok-pc-data\forge_push\nnue_data\pos\forge_selfplay_014.pos --hce-dir D:\grok-pc-data\forge_push\nnue_data\hce --final-full-val --log-every 60 --shape 256 --epochs 32 --lr 9.898e-4 --blend-end 0.6 --seed 198 --batch-size 8192 --warmup-steps 300 --val-positions 1000000 --run-dir F:\forge_nnue_train\runs\pure_h256_e32_f003rec_s198_b06`
   - 21 files and 151,913,894 positions, as for the lock run. Seed 198 reproduces the lock run's data order; QA may
     choose another seed. `--hce-dir` only feeds the baseline lines. DirectML uses the same ops as the existing
     stand-alone model.
3. The supervisor queue cannot run this as-is: `Build-Args` appends `--residual --init-check`, which the trainer
   refuses with `--pure`, and `Train-Files` adds newer data files. Launch the command by hand (the supervisor adopts
   it), or change `Build-Args` — QA's decision.
4. The gate artifact is `epoch032-step000593408.fnn2`. Before the gate, `v2_parity.py` must print PASS,
   `forge_nnue_engine_eval … PureNnue=1` must print PASS, and NPS at d16/d20 must be recorded.

## Proposed gate G-A5 (one option: PureNnue; the net file is its payload)
- Candidate: an opus-O4 build (PC recipe) with `NNUEFile=<pure ep32 .fnn2>` and `PureNnue=1`. The engine log must
  show `info string NNUE v2: active: <file> king buckets 1 output buckets 1 hidden 256 unmirrored stand-alone fnv1a <x>`.
- Opponent: AL1 s198. SPRT [0,10] at 10+0.1, with the srand from the test plan's G-A5 row (QA's choice).
- EVAL rule: if H1, confirm at 40+0.4.

## Merge notes
- O4 conflicts with O6/O7 in `search_options.hpp`, `options.inc`, `uci.cpp` and the two rule functions in
  `evaluation_v2.inc`; the merged rules must cover PureNnue, NNUEThreats and NNUEPawnPairs together. Conflicts with C5
  (output buckets) are likely in `nnue_v2.hpp` and the loader.

## Open issues
- The pure net drops the HCE's endgame scale factors. The research report suggests keeping cheap drawish scaling on
  top of the net; that would be its own option and gate.
- The queue/`Build-Args` interaction described in the GPU recipe.
- NPS with a real pure net is unmeasured.
- The first complete local run (r2) used non-compliant script names (`opus_nnue_c4ref.py`, `opus_nnue_bug.py`,
  `opus_parity_check.py`, `opus_run1t.py`) before the `opus_nnue_smoke*` naming rule reached the sub-agent. It was not
  adopted by the supervisor, and r4 repeated it with compliant names and identical results.
- Early O4 builds remain on D: (`worktrees\b\o4_build`, `o4_cm`, `o4_run`), made before the F:-only rule; left in
  place (no deletes). The worktree has an untracked `tools/nnue/__pycache__` (never committed).
- Supervisor: no "adopted running job" line at any check; nothing under `F:\forge_nnue_train` was written.
