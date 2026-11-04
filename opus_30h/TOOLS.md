# TOOLS - Opus 30-h job (branch opus-30h-20261103; copies under D:\o30\wt\opus_30h)

Every tool is own code. Python = `C:\Users\Administrator\grok-pc\nnue\.venv\Scripts\python.exe -I -B` (numpy, torch
CPU, python-chess, psutil). Own processes run at Idle on CPUs 0-1 (lowrun.ps1 / the tools pin themselves).

## Item A - v2 net path, data, training, packaging (`opus_30h/a/`)
| tool | what it is for | how to verify it |
|---|---|---|
| `v2port.patch` | the engine change: FORGENN2 v2 nets on the lock (UCI EvalFileV2, empty = off) | `pin_check.ps1 -Exe <exe> -Full` = lock pins; lock net as v2 (`o30_v2net.py from-lock`) + `-Expect` lock pins = PASS |
| `o30_v2net.py` | read / write / check FORGENN2 files; `from-lock` writes the lock net as a v2 file (same function); `random` writes test nets | `info <file>` exits 1 on any header / size / checksum problem |
| `v2_eval_o30.cpp` + `build_harness_o30.sh` | engine-side eval printer and accumulator walk (AVX2 / SSE / scalar builds) | `--walk <net> <seed> <games> <plies>` prints 0 mismatches |
| `o30_v2ref.py` + `parity_o30.sh` | independent float32 reference + exact comparison with the three engine builds, planted bug | `parity_o30.sh` prints PARITY PASS and "planted bug caught" |
| `o30_score.cpp` -> `D:\o30\tools_bin\o30_score_v2.exe` | the crew's S31 holdout metric with the engine's own v2 code; `--check-hce` compares the lock's HCE with the FHCE file | lock net as v2 on `holdout_013_014_s16` = b0.6 0.014310027 / b1.0 0.004572428 (the crew's AL1 numbers), hce_differs 0 |
| `o30_data.py` | data audit and training-set preparation (skip lists, jobA overrides, jobA val holdout, evidence JSON) | exit 0 only if jobA aligns 0 mismatches and Astra's mate list = the score rule; AUDIT.json totals |
| `o30_fit.py` | CPU fine-tune of a v2 net (torch, 1 thread): warm start from the lock net, residual target, resumable checkpoints, holdout scores per checkpoint, `stop` via a named event, `selfcheck` | `selfcheck` = the scorer's numbers on the S31 subset |
| `run_fit.sh`, `fit_bg.sh` | launchers (disk / RAM / supervisor checks; Idle + CPU mask; forward-slash paths) | log line with the checks; `fit_bg` prints the trainer's exit code |
| `net_pack.sh` | one step from a trained net to its evidence folder (copy, sha256, parity, holdout scores, OFF / ON pins, RESULT.json) | exit 0 = every check passed |
| `sanity_match.py` | fixed-length match candidate vs lock with fastchess (sanity only) | RUN_INFO.json + `gate_summary.py <dir>` |

## Item B - SPSA (`opus_30h/b/`)
| tool | what it is for | how to verify it |
|---|---|---|
| `o30_expose.py` -> `expose22.patch` | 22 more search constants as tune:: options, defaults = the lock's literals | pin_check -Full = lock pins; each option LIVE |
| `tune_spsa.py` + `tune_spsa.ps1` | the SPSA tuner (params CSV, fastchess pairs, per-iteration CSV, resume, thread cap / CPU mask / gate check, deadline, stop event) | `selftest_10min.ps1 -Out <new dir>` prints SELFTEST PASS |

## Shared (`opus_30h/tools/`, copies of R13-R15 tools with D:\o30 paths)
fresh_lock.sh, export_src.sh, kit_build_o30.sh (kit v2.3), kit24_build_o30.sh (kit v2.4 -PartialTraining; both honour
KIT_MAXMYCPU), plain_build_o30.sh, pin_check.ps1, smoke2m.py, selfplay_smoke.py, cleanroom_lint.py, pc_gate.ps1,
cpu_users.ps1, lowrun.ps1, run_pinned.py, gate_summary.py, abba.py, commit_span.py, doc_lint.py, hash_sweep.py.
