# sol_A2 — Astra A2: king-bucket feasibility design (design only)

Branch `opus-sol-A2` = AL1 lock `d4f4312` + CI baseline `0d99f02` + the `[A2]` commits (job folder only: no file
under `src/`, `include/`, `tests/`, `tools/`, `bench/` or `CMakeLists.txt` changes on this branch).

## Files
| file | what |
|---|---|
| `forge_astra_A2_kingbucket_design_20261027.md` | the design document (layouts, refresh plan, footprint, trainer, data, NPS estimate, recommendation, what stays float) |
| `forge_astra_A2_kbstats_microbench_20261027.patch` | the microbench: a patch for the lock source behind the compile flag `FORGE_A2_KBSTATS` (absent = no code) |
| `a2_verify.sh` | applies the patch to fresh copies of the lock source (`git apply --check`, `patch -p1 -F0`), builds the pristine lock, the patched tree with the flag OFF and ON (box recipe), proves OFF = no code (binary and preprocessed-source compare), runs `uci_check.py --full` on OFF and ON, and runs the counters at bench 16 / 20 / 22 |
| `a2_kbstats_run.py` | UCI driver for the ON exe: bench depths, raw output to a log, node pins checked |
| `a2_kbstats_table.py` | raw counter log -> the Markdown tables of the design doc |
| `a2_bucket_occupancy.py` | own-king square distribution of real self-play positions per layout (data needs) |
| `a2_footprint.py` | memory / cache footprint table (arithmetic) |
| `logs/` | every command's raw output (see the design doc for which number comes from which log); `logs/patch_v1_4fb8a637/` = identity of the first patch version (before the `replayed_cols` counter was added), kept for the record |
| `IDEA_SOURCE.md`, `FILES.txt`, `SHA256SUMS` | sources, index, checksums |

## Reproduce (Git Bash on the PC; everything at nice 19, one thread)
```
cd opus_round1/sol_A2
bash a2_verify.sh /f/opus_scratch/build/A2/<new_dir> logs_rerun          # ~5 min
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
$PY -I -B a2_kbstats_table.py logs_rerun/kbstats_raw.log
$PY -I -B a2_bucket_occupancy.py <holdout_013_014_s16.pos>               # F:\opus_scratch\sol_S31\inputs\prod
$PY -I -B a2_footprint.py 256
```
The microbench exe is only for counting; it is never a gate or play candidate.
