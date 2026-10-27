# sol_S26fix — S26 net-batch fix-ups (S26-1, S26-v4-1, S26-v4-2, S26-v4-3)

Sol's S26 delivery (17aa0cae, `releases/forge_sol_pack31_20261025/S26/`) is read only and unchanged. Fixes ship as
new files. No engine source change on this branch; no net adopted; no Elo or speed claim.

| path | what |
|---|---|
| `closed_nets/<net>/SUMMARY_<net>.md` | S26-1: one short summary per closed first attempt (verdict + key numbers), next to Sol's native result JSON (f019/f020: his closed-folder JSONs, byte copies) and the CI summaries of the re-runs |
| `forge_sol_S26_closed_net_summaries_20261027.py` | builds/verifies those summaries from the JSONs only (`verify` re-renders and compares bytes) |
| `ci/` + `.github/workflows/opus-sol-s26fix.yml` | S26-v4-1/-v4-3 on GitHub Actions (Linux; v4 needs fcntl, /proc, sched_setaffinity, so it cannot run on the PC) |
| `ci/make_base_B.sh` | rebuilds Sol's base B from this branch's AL1 source + e12 net + buffix + Job C/S01 merge; must equal his recorded 78-file snapshot |
| `ci/run_v4_native.sh` | one first attempt under Sol's v4 (default) or `TOOL=v5` |
| `ci/run_pernet_asan.sh`, `ci/check_pernet_asan.py` | per-net ASan+UBSan ctest and verdict |
| `forge_sol_S26_netbatch_v5_20261027.py` | v5 = Sol's v4 with one check_ctest fix (native JUnit `status="fail"` = ran and failed) |
| `forge_sol_S26_f023_rootcause_20261027.py` -> `logs/f023_pin_rootcause.json` | S26-v4-2 root cause, from committed evidence |
| `evidence/sol_S26_original/` | S26-v4-3: copies of Sol's 15,344-line index + `.jsonl.gz` capsule; `RELEASE_FOLDER_SHA256_ONLY.txt` = what the release folder needs |
| `evidence/ci/<run>/` | compact CI receipts per artifact (summary, result.json.gz, table.md, ctest.xml, pin proposal, ASan check/logs) + `ARTIFACT_SHA256SUMS.txt` of every artifact file |
| `test_forge_sol_S26fix_20261027.py` | 11 tests: v5 vs v4 on the real CI JUnit, ASan checker (+ planted sanitizer report), inputs, summaries |

## Re-run

CI: push a change under `opus_round1/sol_S26fix/ci/` or the workflow (or `workflow_dispatch`); artifacts
`s26fix-{v4,v5,asan}-<net>`. Locally (Git Bash):

```sh
PYTHON=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe bash opus_round1/sol_S26fix/ci/make_base_B.sh . F:/opus_scratch/sol_S26fix/<NEW dir>
cd opus_round1/sol_S26fix
S26_SCRATCH=F:/opus_scratch/sol_S26fix/tmp $PY -I -B test_forge_sol_S26fix_20261027.py -v   # S26_V4 = path of Sol's v4 (default: scratch copy)
$PY -I -B forge_sol_S26_closed_net_summaries_20261027.py verify closed_nets
$PY -I -B forge_sol_S26_f023_rootcause_20261027.py . <B>/tests/tests.cpp
```

Full CI artifacts (24 MB + 48 MB) stay in `F:\opus_scratch\sol_S26fix\ci_runs\<run>\`; their file hashes are in
`evidence/ci/<run>/ARTIFACT_SHA256SUMS.txt`.
