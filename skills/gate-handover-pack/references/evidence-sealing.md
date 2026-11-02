# R10 evidence-only sealing — UNPROVEN

`seal_evidence.py MANIFEST.json --purpose incomplete-engine|incomplete-data|data-tool --out NEW_DIRECTORY --threads 1`

This separate utility leaves `make_gate_pack.py` unchanged. It creates only a new,
self-contained evidence copy; it never queues, runs, or accepts a gate or training
job. Exit 0 means the selected evidence-copy contract was consistent; exit 2 means
BLOCKED. Existing or partial attempts are retained and cannot be reused.

The manifest has schema 1, `source_root` (absolute directory beneath D:\a10),
`artifacts` (nonempty list of `{role,path,sha256}`), and `blockers` (list of strings).
Each path is relative to source_root and uses forward slashes. SHA256 is lowercase
and binds the source bytes. Inputs, outputs and manifest must all be under D:\a10.
Traversal, drive paths in artifacts, streams, duplicate Windows case aliases,
reserved device names, symlinks and NTFS reparse points are refused. All artifacts
are copied explicitly under `artifacts/`, preserving their relative paths.

`incomplete-engine` requires at least one nonempty blocker. Its status is
`SEALED_INCOMPLETE`; it must never be presented as a completed strict gate pack.
It requires no invented binaries, passing proof, gate settings or seed inventory.

`incomplete-data` requires nonempty blockers and exactly one artifact of each role
`tool`, `sample`, `training_command`, `audit_report`, `replay_report`. The two
reports must be schema1 JSON objects with explicit status PASS, FAIL, UNVERIFIED
or BLOCKED. Their declared status/scope are recorded without promoting them to
qualification. Missing evidence or tests must be named in blockers; include the
original records that are available. This route always emits SEALED_INCOMPLETE,
UNPROVEN, and `training_clearance:"BLOCKED"`, even if both supplied reports say
PASS. A guarded training command must refuse execution while clearance is
missing. It is an evidence handoff, never training readiness. The strict
`data-tool` checks below are unchanged and still reject missing IDs or non-PASS
actual-adapter reports.

`data-tool` requires no blockers and exactly one artifact of each role `tool`,
`sample`, `training_command`, `audit_report`, `replay_report`. Additional artifacts
include the original audit, execution logs, configs, replay files and dependencies.
The reports below are explicit adapter envelopes, not replacements for raw logs.
Keep the original audit/replay output unchanged and reference it as evidence.

Both envelopes must contain `schema:1`, `status:"PASS"`,
`evidence_scope:"actual-adapter"`, and a nonempty `evidence` list of `{path,sha256}`
references to files included in artifacts, relative to source_root. Fixture scope
is refused. These declarations cannot prove native execution by themselves:
independent review must inspect original commands, input identities and logs.

The audit envelope additionally requires positive integer `source_rows` and
`training_rows`, and integer zero for `position_overlap_rows`, `game_overlap_rows`,
`state_mismatch_rows`, `unknown_game_id_rows`. `holdouts` must have exactly keys
`013` and `014`, each containing positive `rows`, lowercase `sha256`, and
`trusted_complete:true` from the verified original shard/export manifest. Include
that original manifest and authoritative adapter receipts among evidence. The
complete private datasets need not be duplicated into a small handover pack.

The replay envelope additionally requires `output_roles`, the complete unique
list of sealed adapter output roles (including FEN/game-ID sidecars), and `faults`
with exactly `before_publish`, `after_publish_before_checkpoint`, `after_checkpoint`.
Each fault has `status:"PASS"` and `outputs` with exactly one entry per output role.
An output is `{role,uninterrupted:{path,sha256,md5},resumed:{path,sha256,md5}}`.
Both files must be shipped, separately stored, and actually match both hashes.
Each fault must reference its own independent resumed files. Include original
fault-injection/exit/checkpoint logs in evidence; equal hashes alone do not prove
that an interruption occurred.

The pack contains REQUEST.json, REPORT.json, README.md, artifacts/, MD5SUMS and
SHA256SUMS. Hash manifests cover all other regular files, excluding themselves.
REPORT binds the request and sealer source hashes and always states UNPROVEN.
`SEALED_DATA_TOOL` means artifact consistency only, never training clearance.
The incomplete-data purpose additionally records input audit/replay statuses and
an explicit blocked training-clearance field. Never rewrite an original report
to obtain a stronger pack status.

Before creation, the utility checks C: >=30 GiB, D: >=50 GiB plus the planned
write reservation, and total retained D:\a10 bytes plus reservation <=15 GB
(15,000,000,000 bytes). It scans all retained files conservatively and refuses
reparse points. Copies are bounded to the preflight file size, use exclusive
creation and fsync, and are rehashed against inputs. Drive floors are rechecked
between files and each 64 MiB. The safety launcher and reviewed bounded adapters
remain required; this utility is neither a security sandbox nor an OS disk quota.
