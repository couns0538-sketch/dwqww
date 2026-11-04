---
name: r14-finish-helpers
description: Use when running any R14 computation on grok-pc at Idle on one CPU with the GPU hidden, sealing or re-verifying R14 record files and map folders, regenerating sep\PROD_SEPARATION.json from the scan reports, sweeping scripts for silent error handling, hash-pinning the R14 runtime requirements, keeping TOOLS.md md5s current, or running the R14 test suite in the R14 runtime.
---

# R14 finish helper tools

Own code under D:\a14\tools, standard library only (opus_pypi_hashes.py also uses `packaging`). `PY` =
`D:\a14\runtime\python\python.exe -I -B`; `LOW` = `PY D:\a14\tools\opus_lowrun.py --mask 0x4 -- PY`.
Checked on 2026-11-04: `--help` of every tool, the launcher child probe, verify-seal and verify-report, a suite run.
Commands marked "not run here" were checked by `--help` only.

| tool | purpose | command | verify |
|---|---|---|---|
| opus_lowrun.py | pins itself to Idle priority and the CPU mask (both read back; exit 78 if not confirmed), sets CUDA/HIP_VISIBLE_DEVICES=-1, then starts the program, which inherits all of it; exit code = the program's | `LOW <program> [args]` e.g. `LOW -m pytest ...` | a child printing `psutil.Process().cpu_affinity()`, `nice()` and the two variables shows `[2]`, `64`, `-1`, `-1`; `--mask 0x0` and a missing program are refused (exit 1) |
| opus_seal.py | `verify-report R.json [--dir D]` (every {path, md5[, bytes]} object of a record must match; with --dir the folder must hold exactly those files), `seal <dir> --out <list.json>` (bytes, md5, sha256 of every file; output refused inside <dir>), `verify-seal <list.json> [--root R]` | `LOW D:\a14\tools\opus_seal.py verify-seal D:\a14\sep\segments-production02\MAPS_SEAL.json` | prints `verify-seal PASS: 25 files, 0 problems`; any missing / changed / extra file is FAIL, an empty list is FAIL |
| opus_prod_separation.py | regenerates sep\PROD_SEPARATION.json from overlap-production03 and segments-production02 REPORT.json (md5-pinned, every number read, none typed) | `LOW D:\a14\tools\opus_prod_separation.py` (not run here) - it has no CLI and OVERWRITES the record; run it only when the record is meant to change, then `git diff` it (only `updated_vienna` should move otherwise) | the pins are `assert` lines: never run it with -O |
| opus_silent_sweep.py | lists Python `except` bodies that are only pass / ... / continue and PowerShell empty `catch {}`, `-ErrorAction SilentlyContinue|Ignore`, `trap { continue }`; skips runtime/, evidence/, .git/, tmp/ | `LOW D:\a14\tools\opus_silent_sweep.py --root D:\a14 --changed-list D:\a14\evidence\r14\r14_changed_files_11d38208_7636122b.txt [--json <new file>]` | exit is always 0: read the last line (`scanned N scripts, M findings`); it does not see `contextlib.suppress` or `except: return` |
| opus_pypi_hashes.py | turns `name==version` lines into `--require-hashes` lines from PyPI metadata (wheels matching this interpreter's tags, else the sdist); network access | `LOW D:\a14\tools\opus_pypi_hashes.py --requirements D:\a14\tools\requirements-r14.txt --out <new file>` (not run here: network) | `LOW -m pip download --require-hashes --no-deps -r <file> -d <new folder under D:\a14\tmp>` (not run here); the committed tools\requirements-r14-hashes.txt has 13 lines, each with one sha256 (checked) |
| opus_tools_md.py | prints the TOOLS.md section for these tools with current md5s; `--check` compares TOOLS.md with the files | `LOW D:\a14\tools\opus_tools_md.py --check` | exit 0 + `tools md5 check PASS`; until the section is pasted into D:\a14\TOOLS.md it reports every tool as `TOOLS.md None` |

## Running the R14 tests in the R14 runtime

The prescribed "inherited plus R14" command (`-m pytest D:\a14\astra_r8\datafilter\tests D:\a14\tests`) cannot
collect in one process here: the R14 runtime has no torch (datafilter conftest imports it for every test), and
astra_r8\datafilter\filter_positions.py / test_converter.py collide by module name with tools\data and tests\data2.
Run the R14 scope instead, from a PowerShell file so the log keeps raw bytes:
`cmd /c "LOW -m pytest <every D:\a14\tests\test_*.py> D:\a14\tests\r14_native D:\a14\tests\r14_qualification -q -p no:cacheprovider --basetemp <new folder> > <folder>\output.log 2>&1"`
with `TEMP`/`TMP` = D:\a14\tmp, `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`, `OMP/OPENBLAS/MKL_NUM_THREADS=1` (about 65 s;
2026-11-04: 331 tests, 67 subtests). The inherited launcher tests write receipt folders into
D:\a14\evidence\test_logs\r14\launchers\ and unit fixtures into D:\a14\tmp - expect those side effects.

## Pitfalls seen in this job

- Counting CRLF with grep in Git Bash is unreliable (`\r` handling): count `b'\r\n'` in Python over the bytes.
- `python -c "..."` with Windows backslash paths breaks in Git Bash: write a small .py helper and pass paths as
  arguments or on stdin.
- `tools/opus_*` and `tests/test_opus_*.py` are `-text` in .gitattributes: bytes and md5s stay exactly as committed;
  write them LF (`newline='\n'`).
- pwsh passes `$null` to a .NET string parameter as "": `[Environment]::SetEnvironmentVariable($n,$null,'Process')`
  leaves the variable present and empty. To delete use `[NullString]::Value` or `Remove-Item -LiteralPath Env:$n`
  (after `Test-Path`).
- Tools that write records use mode 'x' or refuse an existing --out: choose a new folder; nothing is deleted.
- opus_lowrun.py only lowers its own process: a program that raises its own priority is not stopped.
- One computation process at a time on CPU 2; read-only elsewhere (D:\a13, D:\grok-pc-data, C:\a14x).
