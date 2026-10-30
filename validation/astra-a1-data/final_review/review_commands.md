# Independent final-review commands

Working directory: `/tmp/forge-astra-a1-data`. Started 2026-10-30T04:16:47Z.
The commands below were actually executed during this review. Shell reads of individual source/test/docs files used `cat`, `nl -ba`, `sed -n`, and `rg`; their purpose was manual inspection, not a new runtime qualification.

- `git status --short`; `git branch --show-current`; `git log -1 --format='%H %s'`
- `git diff --name-only e0d76ce8a6450573b503852aeca12b929bf4a17a -- src include CMakeLists.txt tools/nnue` — empty.
- `python3 validation/astra-a1-data/final_review/repro_package_casefold_boundary.py` — exited 1 because the former packager returned PASS for the reproduced collision. Original stdout/stderr and archive remain.
- `PYTHONDONTWRITEBYTECODE=1 python3 validation/astra-a1-data/final_review/replay_saved_evidence.py` — passed; reads 1,024 saved native request/response records and paired records, four sealed bundles, original selected source rows, standard opening metadata, and saved OFF benchmark outputs. No native child.
- `PYTHONDONTWRITEBYTECODE=1 python3 validation/astra-a1-data/final_review/replay_opening_generation.py` — passed; 5,998 archived requests/responses replayed into a new output folder. No native child.
- Python `difflib.unified_diff` over each of `filter_positions.py`, `forge_pos.py`, `forge_probe.py`, `forge_data_probe.cpp`, comparing `validation/astra-a1-data/filter_full10m_v2_protocol` with `tools/data`. Results are the four `.frozen-current.diff` files plus `frozen_current_identity.json`.
- Python import of the fixed packager; `package([{'sourcepath': original_fixture_source, 'archiveprefix': 'evidence', 'kind': 'auxiliary'}], NEW_result_fixed_archive)` — rejected the original unchanged fixture before creating archive or partial. `package_casefold_boundary/fixed_recheck.json` retains the result and implementation hash.

The first attempted bulk `wc` command returned 1 because `__pycache__` is a directory, so its following `cat` was rerun separately. A guessed `protocol.json`/`launch.json` read returned missing-file errors; the actual `launch_progress.json` was then read. The initial shell `diff` stopped at its expected difference exit code; all four comparisons were rerun independently in Python. These are review navigation outcomes, not program failures.

Child review commands and hashes are recorded separately in `windows_resource/review.json`. No full10M process was signaled, stopped, changed, rehashed, or independently searched. No engine build, benchmark, trainer run, Git commit/push, or network publication was performed by this reviewer.
