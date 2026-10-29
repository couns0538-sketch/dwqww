# B6 evidence — 2026-10-29

Base b7c177222038e9332965a95ec53ea3b94e90dbc9, branch astra2-bench-tool.
No engine code changes. Parser reused unchanged from same-repo A3 commit605e5a1c23e00a1fb787090bf8929b8b7b7a1fbe,
SHA25665e4c4d051da5f11aa3abad8bfc940dc56cb03191782905be5d065390bf9ad5b.

`tool_absent_red.log`: two integration success tests fail before the new tool exists. This proves the new runner
was absent, not an old engine bug. `unit_green_attempt1.log`: initial6methodsPASS; `unit_green_attempt2.log`:
expanded7methodsPASS, including correct types for controlled options and a writer thread for bounded stdin I/O.
Tests use a fake UCI executable only. Native engine matrix and full repository CTest remain with parent.

Commands and JSON schema: docs/bench_matrix.md. Exact native command:
```
python3 tools/bench_matrix.py /tmp/forge-astra2-build-base/forge --sets tools/bench_matrix_sets.example.json --out-dir astra2_evidence/B6/native_matrix
```

IDEA_SOURCE: user B6 specification, Forge UCI behavior and reviewed same-repo A3 parser. No Elo or speed claim.
