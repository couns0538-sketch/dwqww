# B6 evidence — 2026-10-29

Base b7c177222038e9332965a95ec53ea3b94e90dbc9, branch astra2-bench-tool.
No engine code changes. Parser reused unchanged from same-repo A3 commit 605e5a1c23e00a1fb787090bf8929b8b7b7a1fbe,
SHA256 65e4c4d051da5f11aa3abad8bfc940dc56cb03191782905be5d065390bf9ad5b.

`tool_absent_red.log`: two integration success tests fail before the new tool exists. This proves the new runner
was absent, not an old engine bug. `unit_green_attempt1.log`: initial 6 methodsPASS; `unit_green_attempt2.log`:
expanded 7 methodsPASS, including correct types for controlled options and a writer thread for bounded stdin I/O.
Tests use a fake UCI executable only. Native engine matrix and full repository CTest remain with parent.

Commands and JSON schema: docs/bench_matrix.md. Exact native command:
```
python3 tools/bench_matrix.py /tmp/forge-astra2-build-base/forge --sets tools/bench_matrix_sets.example.json --out-dir astra2_evidence/B6/native_matrix
```

IDEA_SOURCE: user B6 specification, Forge UCI behavior and reviewed same-repo A3 parser. No Elo or speed claim.

`unit_green_final.log`: 8 methods PASS, including a child that stops reading stdin while the runner queues a
128 KiB string; the cell deadline still terminates its own child. Results checkpoints are atomically replaced.

## Runner revision qualification

The complete native OFF/B1/B2 matrix uses commit `01d57eb` and runner SHA256
`16496dd665db4961499ed8eff01025d5d5fa5a05aa0ab6e6c7b2c4ee6cfb3338`, as its own `results.json` records.
The subsequent save-only delta adds atomic checkpoint replacement (no changes to engine invocation, option
validation, bench parsing or timing). Its runner SHA256 is
`04b143662adeecaf6e4b0c2fc8f7a0bf84a58be74d59dfecf8eecfe9624761ab`.
The final fake suite adds injected persistent `os.replace` failures after one completed cell: the prior valid
ledger remains byte-identical, and the next cell's raw evidence remains available. A persistent filesystem write
failure propagates nonzero; it does not fabricate a completed matrix. Native qualification of the final save-only
revision is reported separately by the parent. Do not attribute the earlier native matrix to the later script hash.
