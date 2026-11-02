# Incomplete data evidence copies — UNPROVEN

The matching `gate-handover-pack` skill now has explicit purpose
`incomplete-data`. It requires one tool, sample, training command, audit report
and replay report, with at least one nonempty blocker. Audit/replay JSON keeps its
original explicit PASS, FAIL, UNVERIFIED or BLOCKED status. The pack always says
SEALED_INCOMPLETE and UNPROVEN, with training clearance BLOCKED. Even supplied
PASS reports cannot promote this purpose to SEALED_DATA_TOOL.

The strict data-tool validator remains unchanged: missing IDs, non-PASS or
non-native adapter evidence still block that route. Existing incomplete-engine
behavior and strict `make_gate_pack.py` are unchanged. No previously sealed pack
was edited. No native pack has been created by this implementation step.

Stable hashes:

- `seal_evidence.py`: `915e99937778d102a0d554bb1e243df11df2dd02fa40bb085921641b68c320d3`
- `test_incomplete_data.py`: `7e6f0056e7ca3e212441587d8892df8ef873fd6cb11ba29b47464dff1858f63a`
- Strict `make_gate_pack.py`: `65ca15daa52566320e25f0152831b5480cfe89c6b893fb15b11e6d11a61baced`

Five new synthetic fixtures passed, zero skipped, in 1.593 seconds:

1. UNVERIFIED audit plus PASS replay seals incomplete, preserving original status,
   blocking training, and passing both checksum-manifest verifications.
2. Missing blockers are refused.
3. A missing required deliverable is refused.
4. UNVERIFIED evidence cannot use the strict data-tool purpose.
5. PASS reports cannot upgrade the incomplete-data purpose.

Original evidence is under `sealer-tests-new01/` and `sealer-tests-new01-launch/`.
The launcher exited 0, Idle on CPU3, one worker, no capture errors and no disk
floor breach. This test mode creates no symlinks. The inherited 15 strict
regressions remain unchanged. After the actual audit finished, the complete
20-test suite passed in 3.892 seconds with zero failures, errors or skips.
Original evidence is `sealer-tests-full01/` and its launcher. The launcher exited
0, Idle CPU3, one worker, without capture/floor errors.

Admission was sampled and inspected before launching: two separate 3-second
observations measured CPU3 at 19.2% then 12.9%, host mean 82.71875% then 80.16875%.
Both satisfied CPU3<30% and host<95%. The original sampler output and completion
receipt are retained in `sealer-tests-loadfull01-launch/`. The full suite's owned
symlink negative ran only after the native audit ended.

Executed full-suite command:

```powershell
powershell -NoProfile -File D:\a10\wt\astra_r10\job3\packaging\run-sealer-tests.ps1 -RunId full01
```

Independent review by proof_contract found no blocking issue in the new mode;
strict validation, role/blocker enforcement, status preservation and existing
sealed-pack identities were rechecked. The final native artifact
collector and guarded training command are separate root-owned work. Missing
authentic game IDs must remain an explicit blocker; no training is authorized.
