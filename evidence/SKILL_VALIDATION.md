# Packaged skill validation

Installed skills on C: were read only. R13 adds a scoped relabel-data-qc package
and extends a copied npt-data-holdout-check package under D:/a13/.agents/skills.
No global installation or agent configuration changes were made.

Observed workflow gaps motivating the additions:
- R14-B labels use inferred game groups despite a zero game_overlap counter.
- R13 sealed shards retain intermediate file names; rejecting all .part files is wrong.
- Reconstructed FEN labels cannot be repaired by attaching original state afterward.
- Comparing new cohort row ordinals to unrelated old cohort ordinals is invalid.

Validation is direct, with no subagents per user instruction. Regression tests
exercise these data semantics and the command examples use the reviewed launcher.
Package structure/link checks and final test receipts are recorded at finalization.
This is not a claim of agent pressure-scenario evaluation or global installation.

Final direct validation: PASS, evidence/skill_receipt.json. Both package frontmatters,
all Markdown local links and six named code/test examples resolve. The copied
legacy audit_exports.py is byte-identical to the installed helper and was not run.
The full inherited + R13 suite passes 603 tests and 60 subtests. This validates the
implemented semantics; it is not an agent pressure-scenario evaluation.
