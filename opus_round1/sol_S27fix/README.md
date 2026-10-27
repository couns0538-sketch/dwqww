# sol_S27fix — S27 patch-hygiene v2 (fix-ups S27-1, S27-2, S27-3)

Sol's S27 delivery (17aa0cae, `releases/forge_sol_pack31_20261025/S27/`) is read only and unchanged; v2 files are
generated from his v1 files by exact single-occurrence replacements (`logs/*_v1_to_v2.diff`). Tool only: no
engine source change on this branch, no Elo or speed claim.

| file | what |
|---|---|
| `forge_sol_S27_hygiene_v2_20261027.py` | patch/zip hygiene checker v2 |
| `forge_sol_S27_buildcompare_v2_20261027.py` | default-build comparator v2 (+ CLI `existing` for two built engines) |
| `forge_sol_S27_reviewed_bugfixes_v2_20261027.json` | S27-3 general reviewed-bugfix allowlist (one entry: the CR-passed buffix) |
| `forge_sol_S27_known_hashes_20261026.json` | Sol's submission-history catalogue, byte copy (loaded next to the tool) |
| `test_forge_sol_S27_v2_20261027.py` | 15 tests (S27-1/2/3, v1 contrasts, real AL1 export) |
| `forge_sol_S27_mutants_v2_20261027.py` | 7 planted bugs |
| `tests_fixtures/` | the buffix patch (sha256 9ce56b3d…) and its CR same-diff record (sha256 6bf7fa63…) from the AL1 lock archive |
| `logs/` | tests, mutants, real runs, compare, Sol's own suites on the PC (v1 vs v2), v1->v2 diffs |

## Changes

- **S27-1** GNU `patch` dry-run and apply get `--no-backup-if-mismatch`: a hunk that applies at an offset no longer
  leaves `*.orig` files, which made v1 report `applied_path_mismatch` and stop. Every per-base error (resource limit,
  scope, observer error) is now recorded with its base label and status `ERROR`; the next base is still checked
  (v1 stopped the whole run at the first raised error).
- **S27-2** pins come from `--ref` (named set `AL1` = 312866/862329/3024920/12389307/34048354 by default, `Lprime`/`B`
  = Sol's dev base 308972/…, or a JSON file `{"11": nodes, ...}`) or `--expected-nodes 11=..,13=..`; `--depths`
  selects depths (default: all pinned). Build parallelism is a parameter (`--parallel`, default 1 = PC rule JOBS=1).
  New CLI: `forge_sol_S27_buildcompare_v2_20261027.py existing BASE.exe CAND.exe --out NEW [--ref|--expected-nodes]`.
- **S27-3** `--control-role reviewed_bugfix --review-record FILE` accepts any patch listed in the reviewed-bugfix
  allowlist (exact patch SHA256 + review-record SHA256 + exact scope; default-build code allowed only in the listed
  files). `approved_buffix_control` stays as an alias for the buffix entry. `--base` accepts relative or
  non-canonical paths (resolved with realpath; v1 demanded a canonical path).
- **Portability** (found while running on the PC): v1 keyed its tree inventory with OS separators, so on Windows every
  applied patch looked like `applied_path_mismatch`; v2 uses POSIX keys. Sol's own suite on this PC: v1 13/47 FAIL,
  v2 2/47 FAIL (the two remaining are fixture CRLF writes vs an LF patch; `git apply --check` rightly rejects).

## How to add a reviewed bugfix

After CR approves a bugfix that must add default-build code, add an entry to the allowlist with: `id`, `patch`,
`patch_sha256` (exact file), `review_record` + `review_record_sha256` (the CR verdict file), `scope` (exact changed
paths) and `default_code_allowed` (subset of scope). Run with `--control-role reviewed_bugfix --review-record <file>`.
Any byte change to the patch, review or scope fails closed.

## Run (Git Bash on the PC; GNU patch 2.8 and git on PATH; nm from `C:/msys64/ucrt64/bin` for `existing`)

```sh
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
nice -n 19 $PY -I -B forge_sol_S27_hygiene_v2_20261027.py PATCH --base AL1=<source export> --out F:/opus_scratch/<job>/<NEW> \
   [--empty-history] [--control-role reviewed_bugfix --review-record CR.txt] [--build-compare --ref AL1 --parallel 1]
PATH=/c/msys64/ucrt64/bin:$PATH nice -n 19 $PY -I -B forge_sol_S27_buildcompare_v2_20261027.py existing BASE.exe CAND.exe --out <NEW>
S27_SCRATCH=F:/opus_scratch/sol_S27fix/tmp $PY -I -B test_forge_sol_S27_v2_20261027.py -v
$PY -I -B forge_sol_S27_mutants_v2_20261027.py F:/opus_scratch/sol_S27fix/<NEW dir>
```

`--base` should be a clean source export (e.g. `git archive HEAD CMakeLists.txt IDEA_SOURCE.md README.md bench
include src tests tools`), not a checkout with evidence folders (32 MiB / 2,048-file limits).
