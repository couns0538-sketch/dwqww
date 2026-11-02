# Job3 collector draft — UNPROVEN

The collector has not run. No sample, input hash freeze, final request or native
pack exists from this step. It cannot run from `final_receipt.template.json`.
The root agent must finish all native/admission/regression statuses, close the
focused review, finish job3/HANDOVER.md, and create a new receipt with status
FINAL_INPUTS_FOR_INCOMPLETE_PACK, reviews_closed=true, exact report/launcher
SHA256 values and all unresolved blockers. Final regression paths remain unset
in the draft. Primary replay is admission-valid proof03; proof02 is preserved
with its failed-admission sidecar, and mock-upstream proof01 remains auxiliary.

The collector checks completed launcher exit receipts and their original launch
manifests, then prepares a manifest for `incomplete-data`. It never seals a pack
or starts an engine, training job or GPU work. It creates an exact 1000-row prefix
of the frozen filtered JSONL only after those completion checks and independently
hashes the whole filtered source before/after extraction. Original source001 is
included for the native16 full-state source binding. It generates source patches
against the frozen originals and preserves the originals themselves.

The input list includes small original reports, failure fixtures, logs, launch
receipts, native16 outputs, both old and admitted replay artifacts, current tool
source, matching skill source, original R8/data and tools/data/data2 source,
auxiliary probe binary and exact D-only build-input source files. The O2 probe
is explicitly auxiliary, not an engine candidate. Runtime/compiler identities
are retained; no C: compiler is accessed or copied. The unchanged independent
Job1 checksum verifier is reused with an additional incomplete-data status guard.

The 1.9 GB bulk input set, runtime tree and full actual audit SQLite are not
duplicated. Their retained paths and hashes appear in INPUT_MAP. Small fixture
indexes remain included. Original absolute paths are preserved as provenance;
SOURCE_TO_PACK maps every listed source to its sealed artifact location. Hash
manifests establish the evidence bytes without requiring a trainer installation.

The training-command artifact is an executable guard that always exits2 and
states BLOCKED/UNPROVEN. No authentic IDs, completely qualified training manifest
or fresh seed inventory exists, so the draft makes no ready-training claim and
does not fabricate an argv. Engine NNUE must supply and review those inputs
before preparing a separate authorized command.

After the root agent releases collection and the two inspected load samples pass:

```powershell
powershell -NoProfile -File D:\a10\wt\astra_r10\job3\packaging\run-prepare.ps1 -RunId final01 -FinalReceipt D:\a10\wt\astra_r10\job3\packaging\FINAL_INPUTS.json
```

The collector's request is `packaging/prepare-final01/seal_request.json`. Review
its exact source-to-pack mapping and exclusions before a separately launched
`seal_evidence.py --purpose incomplete-data --out .../job3/pack --threads 1`.
After sealing, launch `verify_job3_pack.py --pack .../job3/pack --threads 1`
through the safety wrapper. Both checksum manifests and complete file coverage
must pass. Never modify an already sealed pack; retain failed preparation and
sealing attempts under their original names.
