# TT package verification and final source gate

Preparation performs no engines, builds, timing trials, games, Git mutations or
launches. Reuse the existing isolated checkout and virtualenv; do not create a
worktree. The active NNUE package/job and all historical evidence stay frozen.

```sh
cd /workspace/dwqww
PYTHONDONTWRITEBYTECODE=1 python3 -B validation/tt-strength-20261020/test_hosted_tt_strength.py
PYTHONDONTWRITEBYTECODE=1 python3 -B validation/tt-strength-20261020/test_archive_results.py -v
PYTHONDONTWRITEBYTECODE=1 /workspace/.cloud-setup/venv/bin/python -B validation/tt-strength-20261020/check_frozen_openings.py --out validation/tt-strength-20261020/root-opening-check.json
PYTHONDONTWRITEBYTECODE=1 python3 -B validation/tt-strength-20261020/check_prelaunch.py --out validation/tt-strength-20261020/root-static-check.json
```

The opening checker uses installed python-chess 1.11.2 and never selects or
replaces frozen inputs. Its exclusion universe is the original frozen 42
registries, explicit 164 confirmation cohort and all 1028 reserved active NNUE
positions, including unused tails. `prepare_frozen_openings.py` was used once;
its marker rejects re-reservation. Do not rerun it to replace inputs.

Candidate source is frozen to 8865666cc0ab4961cd507bae40ff6ce44e9319df;
baseline is c5cbf97a7291a3bd960c71dcd77a29bf7c95ad8e. Source-export input hashes
for both commits are recorded in source-inputs-SHA256.json. The exact original
runtime diff and all-path/build-input path lists remain in this directory.

Before launch root must finish all actual-engine correctness gates and
independent review, record their exact proof-file SHA256 in protocol under
correctness_evidence_sha256, set source_gates_status=PASSED, and only then set
status=PREREGISTERED_REVIEWED_READY_FOR_SINGLE_PUSH. Pending review rejects
before affinity, compiler setup, engine or subprocess execution. Update the
README/status with actual evidence and retain every failed attempt.

After reviewed metadata changes:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B validation/tt-strength-20261020/refresh_package_inventory.py
PYTHONDONTWRITEBYTECODE=1 python3 -B validation/tt-strength-20261020/check_prelaunch.py --require-ready --out validation/tt-strength-20261020/root-ready-check.json
```

`--require-ready` must fail while source_gates_status or review is pending.
The tests use mocked Python subprocesses only. Launch is outside this package
preparation task; no speed or Elo claim follows from these checks.
