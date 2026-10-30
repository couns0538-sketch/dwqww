# R11: automated NNUE pipeline (data -> train -> export -> parity -> bench -> package)

Status, numbers and next steps: `../NOTES_R11.md`. Skill: `skills/forge-nnue-pipeline/SKILL.md` (copy of the project
skill). Ideas and sources: `IDEA_SOURCE.md`. Every script runs itself at Idle priority in background mode on at most
3 cores (mask 0x700) and never touches production, gates, queue files, locks or baselines.

## One command
```
PY=F:/nnue_pytorch/venv/Scripts/python.exe          # the R6 trainer venv (numpy, psutil, torch ROCm)
$PY -I -B opus_r11/pipeline/r11_pipeline.py --config opus_r11/pipeline/r11_config.json run --profile smoke
$PY -I -B opus_r11/pipeline/r11_pipeline.py --config opus_r11/pipeline/r11_config.json run --profile full
$PY -I -B opus_r11/pipeline/r11_pipeline.py --config opus_r11/pipeline/r11_config.json run --ckpt <file.ckpt> --l1 1024
$PY -I -B opus_r11/pipeline/r11_pipeline.py --config opus_r11/pipeline/r11_config.json run --net <file.nnue> --l1 1024
$PY -I -B opus_r11/pipeline/r11_pipeline.py --config opus_r11/pipeline/r11_config.json status
$PY -I -B opus_r11/pipeline/r11_pipeline.py --config opus_r11/pipeline/r11_config.json selftest <new folder>
```
Exit 0 = `R11 PIPELINE PASS <package>`, 1 = FAIL, 3 = WAIT (a production trainer holds the GPU, the disk floor, or
incomplete data for a full run): rerun later; every stage resumes from its done markers. Log:
`D:\grok-pc-data\r11_nnue\logs\pipeline.log` (one PASS / FAIL / WAIT line per stage).
Stop: end the process with the PID in `D:\grok-pc-data\r11_nnue\run\pipeline.pid.json`. Hold:
`$PY -I -B opus_r11/pipeline/r11_hold.py hold [--minutes N]` (named event `Local\Forge_R11_Hold`).

## Stages (each also runs on its own)
| stage | script | what it does |
|---|---|---|
| data | `pipeline/r11_data.py --config <cfg> run` | inventory -> registry (013/014 first, full sha256) -> hce for r8v5 -> dedup -> binpacks (.part -> verify -> rename) under the 40 GB D: floor -> MANIFEST, train_files.txt, holdout_files.txt |
| holdout proof | `tests/test_r11_holdout_real.py --config <cfg>` | 013/014 only holdout, no training row with a holdout position, dedup order; writes HOLDOUT_TEST.json (the train gate) |
| train | `pipeline/r11_train.py --config <cfg> --profile smoke\|full` | R6 trainer through `tools/nnue_pytorch_amd/r11/r11_train_entry.py`: yield-only, exact resume, newest 2 + best checkpoints |
| export + check | `pipeline/r11_check.py --config <cfg> --net <nnue> [--ckpt <ckpt>] --l1 N --out <dir>` | AVX2 x86-64-v3 build of 7f79c349, serialize.py export, fens_12k parity, OFF identity, ON bench d11-d22, WAC 300 |
| package | `pipeline/r11_package.py --config <cfg> --check <dir>` | gate_ready/ (or smoke_packages/) folder with GATE_EXE.txt (exe sha256), README, SHA256SUMS; never queued |
| Astra | `pipeline/r11_astra.py download\|verify\|list\|extract` | release astra-a1-data-results-20261030, pinned sha256, staged extract |

## Tests
```
$PY -I -B opus_r11/tests/test_r11_tools.py <new folder>                       # CR rules, tools, GPL boundary
$PY -I -B opus_r11/tests/test_r11_data.py <writer exe> <new folder>           # data stage on synthetic shards
$PY -I -B opus_r11/tests/test_r11_train.py <new folder>                       # the one command end to end (CPU)
$PY -I -B opus_r11/tests/test_r11_holdout_real.py --config <cfg>              # the real-data holdout proof
```
The writer is built by `tools/nnue_pytorch_amd/r11/build_r11_tools.py` (content-addressed name) or automatically
(`data.writer_exe: auto`). Evidence of the runs: `logs/`.
