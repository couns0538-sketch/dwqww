# Actual converter restart proof — UNPROVEN until executed

This directory contains an owned copy of the existing `tools/data2` production
converter and its six same-project Python modules, with the original notices
preserved. The frozen export under `D:/a10/job3/source` is never modified.

The narrow converter change stages a complete shard in `.partial_data_<uuid>`,
flushes/fsyncs every data file, exclusively renames it to `data_<uuid>` on Windows,
then writes the existing immutable `chunk_N.json` commit receipt. Optional
programmatic fault hooks are disabled by default. Output must resolve inside
`D:/a10`; no overwrite, deletion or cross-volume fallback is used. A resumed
attempt verifies all committed payloads, retains abandoned stages and orphan
publications, and regenerates only uncommitted source ranges.

`adapter_proof.py` consumes actual `.pos` plus full six-field `.fen` files using
the converter's existing `--sidecar-format fen` path. It never transforms input
into artificial digest records. `--no-filters --no-dedupe` qualifies this format
adapter without starting a probe, external binpack tool, trainer or GPU. It
does not qualify teacher labels or native filtering. Inputs must contain 3–256
rows; the default chunk size is one row so at least one committed shard precedes
each interruption. No experimental seed is used.

The proof runs the frozen original converter and the modified default path,
then stops a newly created owned worker at each of the three publication hooks.
The marker is durably published before the worker waits; the parent verifies
the expected filesystem state and terminates only its own live `Popen` handle.
Every attempted argv, spec, exit code, stdout/stderr, marker and abandoned file
remains. Timeouts fail the proof rather than count as interruption. Each resumed
output is compared with the uninterrupted output, then resumed again to check
that a completed replay preserves bytes. After both resumes the harness also
rehashes every recorded interrupted-stage/orphan file and prior commit receipt
at its original path; deleting or rewriting retained evidence fails the proof.

The compared roles are every committed `rows.txt`, `rows.bullet` and
`provenance.tsv`, both individually and as exact stored byte streams concatenated
in receipt/source order. Both MD5 and SHA256 must match. Chunk ranges and counts
must also match. UUID directory names, path-bearing receipts, disposable SQLite
indexes and elapsed-time reports are retained but excluded from byte identity.
No `.hce` output is produced by this converter, so this proof makes no claim
about HCE replay. Missing game IDs remain empty in provenance; the proof does
not invent authentic IDs or grant holdout clearance.

Negative controls alter only named copies under the new proof directory:
one byte in a committed bullet shard must be refused by both verification and
resume; a valid fullmove-counter change at the same input-sidecar path must be
refused when resuming its earlier checkpoint. Originals are rehashed at the end.

## Input provenance contract

Supply a new JSON receipt with this shape, using actual paths and full hashes:

```json
{
  "schema": 1,
  "upstream_scope": "relabel-with-fixture-probe",
  "outputs": {
    "pos": {"path": "D:/a10/.../relabeled.pos", "sha256": "..."},
    "fen": {"path": "D:/a10/.../relabeled.fen", "sha256": "..."}
  },
  "evidence": {"path": "D:/a10/.../summary.json", "sha256": "..."},
  "scope_evidence": {"path": "D:/a10/.../SCOPE.json", "sha256": "..."}
}
```

Allowed scope labels are `native-relabel`, `relabel-with-fixture-probe` and
`frozen-fpos-sidecar`. The reviewer must assess the referenced evidence before
selecting the label; hashing a receipt alone does not prove its assertions.
The harness binds the exact input paths/hashes, scope, provenance receipt and
referenced evidence. Mock-probe output must never be labeled native relabel.

## Reviewed-launch command template

Execute only after source review and the parent's CPU-slot allocation, through
the R10 safe launcher with the full protected-roots list and one worker/Idle.
Use a fresh nonexistent output directory for each attempt. The approved D-local
Python must inherit one approved CPU; all descendants inherit that affinity.

```text
<D-python> -B adapter_proof.py proof --threads 1
  --out D:/a10/job3/resume-proof01
  --pos <actual.pos> --pos-sha256 <sha256>
  --fen <actual.fen> --fen-sha256 <sha256>
  --input-provenance <input-provenance.json> --provenance-sha256 <sha256>
  --upstream-scope <reviewed-scope> --chunk-rows 1
```

`RESTART_PROOF.json` is written only after all checks pass; `FAILURE.json` records
runtime failures. No PASS is claimed before the native run. The original source
and default-path comparison inside this harness is the relevant regression
check; the separate 73-test NPT/datafilter suite remains a separate obligation.
