# Neon's 10 runnable failing cases (`N1`–`N10`) for `debate/server_day/scripts/`

All 10 cases run with Python 3 standard library + Bash only (no `python-chess`, no compiled engine required; `N2` uses `loop/source` and `loop/forge65_r0067.fnn3` from this repo with a 5-line fake `CXX` shim so the whole suite runs in under 6 seconds).

## One command to run all 10 cases

```bash
python3 -I -B debate/server_day/cases/neon/run_all.py debate/server_day/scripts /tmp/neon_cases_run
```

To run a single case (for example `N9`):

```bash
python3 -I -B debate/server_day/cases/neon/run_all.py debate/server_day/scripts /tmp/neon_n9 only=N9
```

- On today's v1 package (`MANIFEST.sha256` member digest `9705a787bf51f71f8adee7b155d5fccd73f8616a520f39beaaad45c55a91c864`), **all 10 cases return `FAIL` (exit code `1`)**.
- On version 2, **all 10 cases must return `PASS` (exit code `0`)**.

## Case index

| ID | Target file & exact v1 SHA-256 (first 12) | Line(s) | Fixture / input | Observed on v1 (`FAIL`) | Required on v2 (`PASS`) |
|---|---|---|---|---|---|
| `N1` | `linux/cpu_check.sh` (`95f3aa0db7d7`) | 25 | `noflags.cpuinfo` (no `flags` line) | Silent `rc=1` (`set -e` aborts on `grep` before line 26) | `rc=2` with diagnostic naming missing flags |
| `N2` | `linux/build_forge.sh` (`e46c92f25eb1`) | 78, 89, 94, 125 | `$WORK` = `<work>/dir with space` + fake `CXX` arg logger | Unquoted `$extra` splits flag into `.../dir`, `with`, `space/prof` | Single intact `-fprofile-generate=.../dir with space/prof` arg |
| `N3` | `run/uciproc.py` (`ebd26c42342b`) | 62–74 | `spam_engine.py` (`info` every `20 ms` for `2.0 s`), `secs=0.3` | Returns `OK` after `~2.0 s` instead of timing out at `0.3 s` | Raises `EngineError` timeout in `<= 0.8 s` |
| `N4` | `tools/drive.py` (`d7319a8488d0`) | 62–76 | `spam_engine.py` + `spam.uci`, step limit `0.3 s` | Exits `0` after `~2.05 s` | Exits `3` (timeout) in `<= 1.2 s` |
| `N5` | `tools/drive.py` (`d7319a8488d0`) | 43 | Non-existent `<engine exe>` | Raw `FileNotFoundError` traceback (`rc=1`) | Clean error message, `rc=2`, no traceback |
| `N6` | `run/record.py` (`093e3e59bf65`) | 44–48, 108–112 | `openingend` record with line-1 opening mutated, unchanged `bind` | `record.faults(g, reserved=None)` returns `[]` | Returns non-empty bind-digest fault (`opening` hashed in `bind()`) |
| `N7` | `run/packer.py` (`23a01d67f561`) | 114, 199–203 | `w001/closed/p000000.raw` + 0-byte `p000000.sha256` | Uncaught `IndexError` traceback (`rc=1`) | Clean refusal `rc=3`, no traceback |
| `N8` | `tools/check_run.py` (`3a2d88d3c1cd`) | 31 | `error_path_and_bare_sgerror.transcript` | Clean `NNUE v3 active` path `/tmp/TEST_ERROR_DIR/...` flagged as refusal; bare `sgerror` missed | Bare `sgerror` flagged as refusal; clean path NOT flagged |
| `N9` | `tools/hash_tree.py` (`ae469583a62d`) | 17–26 | Dir with dangling symlink `sub/dangling`; overlapping `sub sub/a.txt` | Dangling symlink exits `0` silently; `sub/a.txt` emitted twice | Symlink rejected (`rc != 0`); no duplicate entries on overlapping args |
| `N10` | `tools/make_workloads.py` (`5a9ede134acc`) | 65 | Invoked with 0 arguments | Uncaught `ValueError` traceback (`rc=1`) | Prints usage and exits `2`, no traceback |
