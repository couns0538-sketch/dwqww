# S09fix — QA fix-ups S09-1..5 for Sol's S09 (8 piece-count output buckets)

Branch `opus-sol-S09fix`, folder `opus_round1/sol_S09fix/`. Tool/evidence job: no engine source change, no net
trained, no gate. Sol's delivered files (commit `17aa0cae`) are read only; fixes ship as new `_v2` files.

## Files
| file | what |
|---|---|
| `forge_sol_S09_trainer_buckets_v2.py` | S09-2: Sol's S09 trainer with the v3b CLI defaults restored (`--shape 128`, no `--residual`, `--epochs 8`, `--batch-size 4096`, `--lr 1e-3`, `--seed 1`, no `--final-full-val`); `--buckets 1|8` kept (default 1); `output_buckets` is written to the config only for 8 heads. |
| `forge_sol_S09_f006_recipe_args_v2.txt`, `forge_sol_S09_f006_recipe_v2.json` | S09-2: the f006 recipe as explicit arguments, copied from the production f006 command line. |
| `forge_sol_S09_trainer_v2_vs_current_v3b.diff`, `forge_sol_S09_trainer_v2_vs_sol_S09.diff` | review diffs: v2 against the current production trainer (only the bucket code + header) and against Sol's file (only the restored defaults + config). |
| `forge_sol_S09_export_identity_v2.py` | S09-1: `roundtrip` (net .inc -> both trainers' models -> both exports, bytes compared) and `compare-runs` (two training run folders, every artifact byte for byte). |
| `opus_s09_identity_runs.sh` | S09-1: CPU smoke runs of the current trainer and v2 (renamed copies) with identical arguments on a data32 split. |
| `forge_sol_S09_holdout_validate_v2.py` | S09-5: real 013/014 holdout validation of the 8-head path (occupancy, MSE per net and head, 1-head vs replicated-8 parity, bias-shift head-selection control, CPU optimizer check). |
| `forge_sol_S09_holdout_validation_v2.md` | the S09-5 result table. |
| `opus_s09_patch_one_file.py` | rebuilds the trained 8-head net (b8ep8, md5 `09227945…`) from the lock archive's research patch (no copy from the training folder). |
| `opus_s09_split_pos.py` | writes a row range of a .pos/.hce pair (used for the data32 train/holdout split). |
| `opus_s09_package_sol_packet.py`, `sol_S09_v2_packet/archives/` | S09-4: Sol's 902-file packet as 35 per-step archives (the files index is part of `FILES.txt`). |
| `test_forge_sol_S09_v2.py`, `opus_s09_mutants.py` | 11 unit tests; 8 planted bugs, all must make the tests fail. |
| `IDEA_SOURCE.md` | S09-3: idea sources of the 8 output buckets. |
| `logs/step*.tar.gz` | one archive per step (stdout, result JSON). |
| `FILES.txt` (the one index), `SHA256SUMS`, `REPORT.md` | |

## How to run (PC rules: Idle priority, one thread, scratch only, renamed trainer copies)
```
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 TMP=F:\\opus_scratch\\sol_S09fix\\tmp TEMP=$TMP
# trainer copies must be named opus_nnue_smoke_*.py (never run a train_resid* file); qa_adam_dml.py beside them
S09_CURRENT_TRAINER=F:/opus_scratch/sol_S09fix/opus_nnue_smoke_s09_current.py nice -n 19 $PY -I -B test_forge_sol_S09_v2.py
nice -n 19 $PY -I -B opus_s09_mutants.py --work F:/opus_scratch/sol_S09fix/mutants_runN
nice -n 19 $PY -I -B forge_sol_S09_export_identity_v2.py roundtrip --current <current copy> --v2 <v2 copy> --out <new dir> --net L=<net.inc> ...
bash opus_s09_identity_runs.sh F:/opus_scratch/sol_S09fix <this folder>
nice -n 19 $PY -I -B forge_sol_S09_holdout_validate_v2.py --trainer <v2 copy> --pos <holdout.pos> --hce-dir <dir> --net e12=<inc> --rep8 e12 --out <new dir>
nice -n 19 $PY -I -B opus_s09_package_sol_packet.py --repo <dwqww clone> --commit 17aa0cae --out <new dir>
```
Train with the v2 trainer and the f006 recipe: `python -u <copy>.py $(cat forge_sol_S09_f006_recipe_args_v2.txt) --train ... --holdout ... --hce-dir ... --run-dir ...`
(add `--buckets 8` only after a CR review and a crew vote; never queue it on the GPU from this job).
