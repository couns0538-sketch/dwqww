# Frozen source and package checks

Run from `/workspace/dwqww`. These commands do not build or execute engines,
commit, push, or launch jobs. The protocol currently remains`PENDING_REVIEW`.

Frozen candidate6.4.11:`c5cbf97a7291a3bd960c71dcd77a29bf7c95ad8e`.
Frozen baseline6.4.9:`4edda780c68a742f20565d4e6a54a0c99a2c88a6`.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B validation/nnue-strength-20261019/test_hosted_nnue_strength.py
PYTHONDONTWRITEBYTECODE=1 python3 -B validation/nnue-strength-20261019/test_archive_results.py -v
PYTHONDONTWRITEBYTECODE=1 /workspace/.cloud-setup/venv/bin/python -B validation/nnue-strength-20261019/check_frozen_openings.py --out validation/nnue-strength-20261019/root-final-opening-check.json
PYTHONDONTWRITEBYTECODE=1 python3 -B validation/nnue-strength-20261019/check_prelaunch.py --out validation/nnue-strength-20261019/root-final-static-check.json
sha256sum -c .github/hosted-nnue-strength/PACKAGE-SHA256SUMS
```

The opening check uses the existing setup virtualenv withpython-chess1.11.2;
it rereads the original34700PGNs, exact frozen42historical registries and
explicit164confirmation cohort. It checks the existing pools and separately
frozen seed20261021 runtime order without changing/reselecting them. The
static checker uses systemPython withPyYAML and verifies both exact source
commits against every original source-inventory SHA, package/workflow SHA,
review gate, trigger and shell syntax. Default mode can pass preparation with
`launch_authorized=false`; it never enables the gate.

After root has passing ASan/Windows results and final independent review,
record those actual evidence paths/hashes inprotocol, update source-gate
narrative/README, and change protocolstatus to
`PREREGISTERED_REVIEWED_READY_FOR_SINGLE_PUSH`. Then refresh package hashes and
run the final check with the explicit ready requirement:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B validation/nnue-strength-20261019/refresh_package_inventory.py
PYTHONDONTWRITEBYTECODE=1 python3 -B validation/nnue-strength-20261019/check_prelaunch.py --require-ready --out validation/nnue-strength-20261019/root-final-ready-check.json
sha256sum -c .github/hosted-nnue-strength/PACKAGE-SHA256SUMS
```

Inventory sources:

- `.github/hosted-nnue-strength/PACKAGE-SHA256SUMS`: all21package files excluding
  itself, plus the separate workflow (22SHA entries), using repository-relative
  paths. The refresher enumerates current files; it rejects unexpected bytecode.
- `source-inputs-SHA256.json`: every frozen build-input file from both Git source
  objects under`CMakeLists.txt src include tests bench tools`, with both source
  SHA256s and unchanged flags. Added driver files have no baseline SHA.
- `source-scope-audit.json`: exact scope assertions; `source-runtime.diff` keeps
  the original Git diff for runtime/version files, and
  `source-build-input-changes.txt` records the only5changed export paths.
- `source-all-path-changes.txt`: every changed branch path, including preserved
  documentation, workflow, validation and release evidence. These additional
  repository differences are distinct from compiled engine changes.

Removing the44added fusion lines makes the entire candidate`nnue.cpp`
byte-identical to6.4.9, including fallback, refresh, evaluation and weights.
The two other modified build inputs change only CMake/UCIversionlabels.
Alltests/opening/bookmetadata are unchanged. The2newdriver tools are absent
from CMake target changes and do not alter engine execution.

Original pre-source-freeze metadata/inventory and earlier test attempts are
preserved alongside the fresh`root-ready-*` check outputs. No launch occurred.
