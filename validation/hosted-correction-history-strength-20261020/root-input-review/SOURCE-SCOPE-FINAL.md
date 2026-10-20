# Exact independent18 source scope

**Source scope PASS:** `b5908f0fe9db227158d39e156652f2467252e68a` → `fc51e43c26f735cbc1ffabf0fcf64f48a4592c0b` changes one production search arithmetic line and the UCI version string. All 20 src/include files were hashed from exact Git blobs; all other production files are identical.

NNUE implementation/header/embedded weights are byte-identical: `include/forge/nnue.hpp`, `src/nnue.cpp`, `src/nnue_weights.inc`. No network change or retraining is present.

The code/build/test difference is exactly4files,149insertions/3deletions: CMake version/test registration, `src/search.cpp`, UCI version text and the new permanent correction-history test. The full Git tree also adds `validation/correction-history-residual-20261020/PRODUCTION-PREPARATION.json`. The correction update changes decaying EMA to clamped residual increment; all surrounding guards, clamps and material coupling are unchanged. This is a selectivity hypothesis, not a demonstrated bug or gain.

Package inventory observation: **PASS**, 24 listed files, 0 hash mismatches, 0 unlisted files. Validation inventory observation: **NEEDS_REFRESH_OR_REVIEW**, 618 listed files, 1 mismatches, 1 unlisted files. Exact per-file hashes and discrepancy paths are in JSON. Root/Astra report additions and root proof binding require a new final inventory; this read-only review does not alter it.

Draft-only checks that must not be misapplied after READY: `check_preparation.py`; `test_actual_draft_keeps_proofs_and_workflow_pending_after_signature_freeze`; and `test_actual_source18_signature_does_not_waive_other_gates` when it assumes pending fields from the actual config. Preserve their historical results; future ready-state validation should construct explicit missing-gate controls. Remaining parser, evidence, process, archive and explicit gate-negative tests remain useful.

No engine/build/test execution, Git/index writes, protocol/workflow edits, inventory mutation or launch occurred. These review files are excluded from their own pre-write observation to avoid hash cycles.
