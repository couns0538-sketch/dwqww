# Resume proof01 — PASS for stated scope; UNPROVEN

Native Windows run finished `2026-11-02T07:49:03Z`, launcher exit 0, Idle,
one worker on CPU2, no capture errors or disk-floor breach. The prelaunch sample
was CPU2/3 26%, host 89%. No engine, GPU or training process was started.

Evidence: `D:/a10/job3/resume-proof01/RESTART_PROOF.json`, SHA256
`91dc7c653cab30c16044fd3cbec3a1d5d88d7f40e4d89f00ef94ce54f2f734e7`.
Launcher receipt: `proof01-launch/result.json`, SHA256
`fc0cfa60dc36477c0530b2ccad6a8810e7d8dfd3c3576e27477a70c4324baa7c`.

Reviewed implementation: `adapter_proof.py`
`30ee29216043b36c5f758ddcc382157e639a90d50d444fa40ced3a430beb5f31`;
`data2/convert_dataset.py`
`5e51245ff0f444da0bc1e87f54430f4d4b462fe1a067d3a10e0e9cb29182c77e`.
Independent reviewer `proof_contract` found missing verification that resume
preserves abandoned output. The fix binds fault-marker output/paths and rehashes
all retained shard files and prior commit receipts after both resumes. Its
focused recheck found no remaining blocker in the inspected scope.

Inputs are three actual `relabel_positions.run` output rows from retained
`tool/green01/test_actual_relabel_roundtrip_and_ids`, using **FixtureProbePool**
responses. Their old source/probe receipt is pinned in `input-provenance01.json`.
This run does not qualify native teacher labels or attribute those outputs to
the later GREEN02 state implementation. The positions include KQkq castling,
noncapturable e3 EP and capturable d6 EP. Authentic game-ID clearance is absent.

| Check | Result |
| --- | --- |
| Frozen d8982bc0 versus modified default payload bytes | PASS |
| Before-publication interruption and two resumes | PASS; owned child exit 1 |
| After publication/before checkpoint and two resumes | PASS; owned child exit 1 |
| After-checkpoint interruption and two resumes | PASS; owned child exit 1 |
| Retained staging/orphan payloads and prior receipts | PASS after each resume |
| Corrupted committed shard, verify and resume | DETECTED: sealed chunk hash mismatch |
| Same-path changed source FEN, resume | DETECTED: config/source/tool identity mismatch |
| Timeouts | 0 |

Every committed output role was compared per chunk and as stored bytes
concatenated in receipt order. All three interruption runs match these baseline
digests:

| Role | Bytes | MD5 | SHA256 |
| --- | ---: | --- | --- |
| rows.bullet | 96 | 9bf99a59cde8ae3f2c9a02200fe1ffc1 | 36c2dcc3b8eaba50ac81d7899f5419766a1c76c5e8c7cfe7943bd8b619b95039 |
| rows.txt | 140 | a63e0b99a4d6c88af66e6c7433955a5c | 67c58fa9b4457e85fe5a3ab2cc57dc3687e9f37c6b6a58e458c6651fcc5e06ca |
| provenance.tsv | 9 | 8eb1fa474a84dec7804fc16f6b9026d0 | 213f88ed4bea9d73f4d93ddcc6e7eb901148d767932af91954f83699326d7576 |

UUID path strings, operational reports and disposable indexes are preserved but
excluded from payload identity. This converter has no HCE output role. Full
native relabel replay, the 73-test suite and the full real-data holdout audit
remain separate evidence obligations; this small proof does not fill them.
