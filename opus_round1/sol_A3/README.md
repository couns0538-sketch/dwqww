# sol_A3 — Astra A3: full-NNUE design, trainer, converter, reference evaluator, smoke net (no engine integration)

Branch `opus-sol-A3` = AL1 lock `d4f4312` + CI baseline `0d99f02` + the `[A3]` commits (job folder only: no file
under `src/`, `include/`, `tests/`, `tools/`, `bench/` or `CMakeLists.txt` changes). Offline / CPU only; nothing is
queued on the GPU; no strength claim. Builds on A2 (`opus-sol-A2`, layout M4).

## Files
| file | what |
|---|---|
| `forge_astra_A3_fullnnue_spec_20261027.md` | the spec: network FN1, file format FORGEFN1, evaluation order, incremental plan, engine integration plan (`UseFullNnue` = 0 keeps the residual net), acceptance evidence |
| `forge_astra_A3_trainer_20261027.py` | the trainer (new file; v3b loader conventions, FPOS data). Run only as a copy named `opus_nnue_smoke_<name>.py` on the PC |
| `forge_astra_A3_converter_20261027.py` | checkpoint `.pt` -> engine file `.fnn` (FORGEFN1); `info` |
| `forge_astra_A3_refeval_20261027.py` | reference evaluator (pure Python + numpy): loader, features, refresh, incremental update, refresh cache, lazy evaluator, engine-order float32 evaluation |
| `a3_parity_1k.py` | acceptance 1: trainer -> converter -> reference evaluator on 1000 synthetic + 1000 real positions |
| `a3_incremental_200k.py` | acceptance 2: incremental == full refresh on 200k positions (python-chess walks) |
| `a3_smoke_train.sh` | acceptance 3: trains the smoke net twice with seed 7 (and once with seed 8 as a control), converts, compares sha256 |
| `a3_mutation_check.py` | planted bugs: each must make its test fail |
| `logs/` | raw output of every run (see the spec's acceptance table); `logs/invalid_empty_trainset_run1/` = a first smoke run whose training glob matched no files (kept for the record; it led to the empty-training-set guard); `logs/mutation_check_first_run_4000pos.log` = the first planted-bug run, whose 4,000-position walk never reached an en-passant capture, so that bug went unseen (the check now walks 20,000 positions) |
| `a3_acceptance.sh` | runs acceptance 1, 2 (with and without the cache), the planted bugs, a CLI sample and the "no engine change" check after `a3_smoke_train.sh`. Its console is `logs/acceptance_console.log`; in that run the last block ran `git diff -- src include ...` from the job folder, where the relative pathspecs match nothing, so it proved nothing. The script now runs the check at the repository root, and `logs/no_engine_change.log` holds that corrected check |
| `smoke_net/` | the smoke net (`a3_smoke_FN1_M4_H256_L16x32_OB8_seed7_epoch003.fnn`, sha256 f5ec8bd5...), its last epoch's metrics and settings |
| `IDEA_SOURCE.md`, `FILES.txt`, `SHA256SUMS` | sources, index, checksums |

## Reproduce (Git Bash on the PC, nice 19, one thread; S = a scratch dir with inputs/ copied in)
```
S=/f/opus_scratch/sol_A3          # holds inputs/data32_sample_50k (copy of LA/5_nnue/sample_data/data32_sample/data32_sample_50k)
                                  # and inputs/fens_10k.txt (copy of F:\opus_scratch\sol_S31\inputs\fens_10k.txt)
bash a3_smoke_train.sh $S logs <new_prefix>                          # ~7 min: smoke net, rerun, control
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
cd $S
$PY -I -B <A3>/a3_parity_1k.py --trainer opus_nnue_smoke_a3trainer.py --ckpt <prefix>_seed7_r1/epoch003-step000000585.pt \
    --net <prefix>_seed7_r1/epoch003.fnn --pos inputs/data32_sample_50k/h000.pos --fens inputs/fens_10k.txt
$PY -I -B <A3>/a3_incremental_200k.py <prefix>_seed7_r1/epoch003.fnn inputs/fens_10k.txt --positions 200000 --seed 1
$PY -I -B <A3>/a3_mutation_check.py --trainer opus_nnue_smoke_a3trainer.py --ckpt ... --net ... --pos ... --fens ... --tmp <new dir>
```
Never run the trainer under a name containing `train_resid`, never use run folders named `runs_*` / `smoke_kb*`,
and check `F:\forge_nnue_train\supervisor.log` for a new "adopted running job" line after each start.
