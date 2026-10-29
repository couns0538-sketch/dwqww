# Forge option bench matrix — Astra R2 B6

Run from the repository (Python 3.10 or later, standard library only):

```sh
python3 tools/bench_matrix.py /absolute/path/to/forge --sets tools/bench_matrix_sets.example.json --out-dir /new/path/to/matrix
```

Windows uses the same command with `python` and an `.exe` path. Windows execution is unverified here.
Each cell has a complete180-second deadline by default (`--timeout` changes it). A new child engine is launched
for every row/depth. The runner controls Threads1, Hash16 and OwnBookfalse, waits for actual `uciok` and `readyok`,
then sends bench11/13/16/20/22 separately. The table reports node counts and the engine-reported NPS.
Do not compare NPS from loaded machines or treat this output as a speed/Elo result.

The auto-generated `OFF` row means fresh engine defaults plus those three controlled settings and
`BundlePreset OFF` when advertised. It is always checked against312866/862329/3024920/12389307/34048354.
Users cannot supply another OFF-labelled row or override the controlled settings. Other rows are requested
configurations, not strength acceptance: the tool checks advertisement and refusal diagnostics but cannot prove
that an engine with silently broken option handling actually used each requested feature.

`--sets` contains an array of objects with exactly `name` and `options`. Each options list is an ordered list
of `[option name, value]` pairs. This preserves preset-before-override semantics, including deliberately repeated
options. Values may be strings, integers or booleans; use `null` for buttons. Example:

```json
[{"name":"B1 plus nonpawn","options":[["BundlePreset","B1"],["CorrHistPlus",4]]}]
```

Before applying a row, every requested/control option must be advertised with an appropriate type/range/variant.
Unknown, refused and invalid diagnostics; missing handshakes; malformed, duplicated or wrong-depth bench output;
OFF node mismatch; timeout; nonzero process exit; changed executable; or capture overflow all produce nonzero exit.
The capture cap is8MiB per stream per cell. A cap failure is explicitly labelled truncated; no completeness claim
is made for that failed stream. Only owned child processes are terminated on failure or timeout.

The output directory must not exist. Each cell preserves `.stdin`, `.stdout`, `.stderr` bytes and their hashes;
`results.json` is updated after each completed cell, so interrupted runs preserve completed work. It records
normalized ordered settings, fixed references, invocation, executable before/after SHA256s, and runner/parser/config
source hashes. A failure stops the matrix; rerun into a different directory, retaining the original failure.
The source scripts and the original JSON file should accompany results when moving them to another machine.

Parser reuse: `tools/check_bundle_opts.py` is byte-identical to this same repository at
`605e5a1c23e00a1fb787090bf8929b8b7b7a1fbe` (`astra-notes`, A3), SHA256
`65e4c4d051da5f11aa3abad8bfc940dc56cb03191782905be5d065390bf9ad5b`.
No code from another engine was used. No engine source, evaluation or search behavior is changed by B6.

Tests:
```sh
python3 tests/test_bench_matrix.py
ctest --test-dir BUILD -R bench_matrix_tool_tests --output-on-failure
```
The fake executable is a protocol fixture, not chess evidence. Native full-depth OFF/B1/B2 runs are separately
recorded in `astra2_evidence/B6` when completed.
