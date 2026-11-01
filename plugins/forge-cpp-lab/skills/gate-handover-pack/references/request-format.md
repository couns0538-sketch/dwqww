# Gate request and inventory formats

The helper uses Python 3.10+ and only the standard library. Run through the PC safety skill; the helper alone is not an OS sandbox. It performs no process launch, network call, queue update or source-data deletion. Linux fixture tests are not native Windows qualification.

CLI: `python make_gate_pack.py REQUEST.json --out NEW_DIRECTORY`

Exit 0 produces `READY_FOR_QA_REVIEW`; exit 2 prints `BLOCKED` with the reason. Preflight failures create no output. A copy/write failure may leave an incomplete owned directory; it is preserved, never cleaned or reused automatically. The output parent must exist.

## Request schema 1

| Field | Required value |
|---|---|
| `schema` | Integer 1 |
| `baseline_commit`, `candidate_commit` | Full lowercase 40-hex Git SHA-1s |
| `build` | `compiler` and `flags`, nonempty strings from the actual build |
| `variants` | `OFF` and `ON` objects containing actual UCI option settings |
| `gate` | Object with `name` (letters/digits/underscore/hyphen), `start`, `srand`, `threads`, `hash_mb`, `time_control` |
| `artifacts` | List of objects: `role`, `path`, lowercase SHA-256 `sha256` |
| `snapshots` | Nonempty list of the fresh-copy descriptors below |

Start/srand are nonnegative signed-32-bit integers; thread/hash counts must be positive. The packager does not decide whether a time-control string or SPRT design is suitable; QA uses the actual gate specification.

Each required artifact role occurs exactly once: `baseline_binary`, `candidate_binary`, `net`, `source_manifest`, `build_log`, `bench_log`, `test_log`, `protocol`, `lock_contract`, `proof`. Additional roles/files are allowed. Include all proof evidence files and original native gate exports as artifacts; pack only explicitly nominated inputs. An aggregate log may satisfy a role if it retains the unmodified original output and exit evidence.

All paths are relative forward-slash paths **under the request's parent directory**. Absolute, drive-qualified, parent traversal, symlink paths and protected NPT/queue components are rejected. Stage or nominate a common approved root first; do not relocate a proof without its relative evidence files. Outputs preserve these paths under `artifacts/`, so a packed proof's evidence references remain valid. Snapshots are additionally copied under `snapshots/`.

The `protocol` artifact is a JSON object containing all `gate` fields with exactly the same values. It may also record the runner version, runner executable hash, opening suite/hash, SPRT hypotheses, adjudication, concurrency and other required options. Those additional semantics are reviewed by QA, not guessed by the packager.

## Native proof binding

The proof artifact is schema 1 with:

- `status: "PASS"`, `evidence_scope: "native"`;
- matching `baseline_commit` and `candidate_commit`;
- `baseline_binary_sha256`, `candidate_binary_sha256` and `net_sha256` equal to the actual declared binary/net artifact hashes;
- `tested_options: {off: ..., on: ...}` exactly matching the request's `variants.OFF` and `variants.ON` maps;
- `contract_sha256` equal to the declared `lock_contract` artifact hash;
- nonempty `checks`, each uniquely named and `status: "PASS"`;
- each check has a nonempty `evidence` list of `{path, sha256}` references relative to the proof file's directory. Every referenced file must be included in `artifacts` with the same digest.

Required check names: `build_a`, `build_b`, `reproducible_builds`, `off_pins`, `on_active`, `perft`, `smoke_t1`, `smoke_t4`, `asan_ubsan`. Extra checks must also pass. This format matches `forge-lock-proof-set`; `fixture` scope, missing checks, hash mismatches and revision mismatches are blocked. The packager verifies the supplied declaration and artifact bytes; it cannot detect fabricated logs or independently establish that a compiler/test ran.

## Fresh copied inventory

Each snapshot descriptor requires `path`, `sha256`, exact integer `mtime_ns` of the copied file, timezone-aware ISO `captured_at_utc`, descriptive `source_label` explaining full inventory coverage, and `trusted_copy: true`. This attestation is the crew's provenance declaration, not a cryptographic certification. Capture time must be 0–900 seconds before the scan; future timestamps and older copies are rejected. A truly new export is required for a fresh scan.

The normalized snapshot is JSON with `schema: 1` and a `gates` list. Every row must contain integer `start` and `srand`; a descriptive `name` is recommended. The exporter must include all relevant records, not only finished or non-VOID gates. Native format parsing/exporting is deliberately outside the helper: inspect the real gate schema and preserve the original exported copy. Do not read the live queue through this helper or omit unrecognized records to obtain a PASS.

SCAN.json records capture times, supplied hashes/mtimes, source coverage labels, scan time and row counts. The check rejects exact reuse of the proposed start or srand anywhere in the nominated rows. It proves only uniqueness within those copies, not live queue state or undisclosed inventories. QA must recheck freshness and uniqueness immediately before queueing.

## Output and hashes

The new pack contains `artifacts/`, `snapshots/`, `REQUEST.json`, `SCAN.json`, `README.md`, `GATE.md`, `MD5SUMS` and `SHA256SUMS`. Hash manifests cover every payload file and generated instruction/scan file; they intentionally do not hash themselves or each other. Hash the complete archive externally after sealing it. Files are written exclusively and fsynced through writable descriptors. Keep incomplete attempts; this tool never deletes or overwrites them.

Original-only implementation: user gate-handover requirements and existing Forge evidence conventions. No external engine code or tuned constants.
