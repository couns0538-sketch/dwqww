# S11 three-arm CLI and chunk retention, 2026-10-26

This replaces the single-gzip retention **preparation**, which remains preserved.
No S11 C++ compiler, engine, oracle or performance run has been launched.
Python synthetic fixtures are only workflow tests, never chess-engine evidence.

The ready CLI is `forge_sol_S11_scalar_parity_run_20261026.py`. It requires
completed same-base Release build and FIRST receipts for baseline and candidate,
the verified S10 publication commit and a fresh finite root execution grant.
It verifies the actual oracle compiler invocation/source/header include paths,
core, source/artifacts, normal driver flags, table-marker role and link maps.
It compiles only a **test** scalar NNUE object and normally compiled oracle,
using that object explicitly before the candidate archive. No new main engine
ELF is created. Actual preprocessing/disassembly must prove AVX2 and scalar
selection, scalar float32 arithmetic, no packed SSE fallback, and no FMA or
unsupported width. A failure remains an incomplete/failed scalar qualification;
it is never relabelled as a scalar PASS. Public NNUE/header/net inputs stay fixed.

Each of the three arms is one original1M-position oracle process, receiving the
same verified sealed S09 corpus on stdin. Capture splits this single original
byte stream into100 fixed10,000-record gzip1 files. Chunk0 includes the sole
36-byte original header; later chunks contain only their original record bytes.
Maximum raw chunk size is20,680,036 bytes, below GitHub's single-file limit.
Every closed chunk is fsynced and its index/offset/count/raw and compressed hashes
are journalled. Final manifests preserve the original global digest/count/EOF.
There is no corpus regeneration and no100-process reconstruction of1M results.

`compare_chunked(left_manifest, right_manifest, 1000000, 4096, stop=guard)`
validates the exact contiguous chunk/record coverage and compares every decoded
byte. Hashes supplement this comparison. Gaps, reordered chunks, overlaps,
partial records, changed headers or decoded bytes fail. Stop/deadline checks also
cover comparisons. Run baseline/candidate and candidate-AVX2/candidate-scalar
comparisons; original oracle summaries must report zero key/state mismatches,
650 actual table basis checks for each candidate and0 for baseline, plus the
original legal-child/null restoration coverage.

Example after the root supplies completed receipts and verifies S10 publication:

```sh
nice -n19 taskset -c 1 python -B forge_sol_S11_scalar_parity_run_20261026.py \
  --execute --authorization-reference ROOT_GRANTED_S11_PARITY \
  --s10-published-commit VERIFIED_40_HEX_COMMIT \
  --baseline-build /tmp/forge_sol_S11_native_20261026/LP_base_release/forge_sol_S11_build_result_20261026.json \
  --candidate-build /tmp/forge_sol_S11_native_20261026/LP_cand_release/forge_sol_S11_build_result_20261026.json \
  --baseline-first /tmp/forge_sol_S11_native_20261026/LP_base_FIRST/forge_sol_S11_runtime_result_20261026.json \
  --candidate-first /tmp/forge_sol_S11_native_20261026/LP_cand_FIRST/forge_sol_S11_runtime_result_20261026.json \
  --corpus-manifest /tmp/forge_sol_S09_native_20261026/million_unique_corpus_once_20261026/manifest.json \
  --out /tmp/forge_sol_S11_native_20261026/LP_three_arm_original1M_once \
  --cpu 1 --max-seconds 1800 --arm-seconds 500 --scalar-build-seconds 180
```

All names in the example are placeholders except the already-owned S09 corpus.
The script never treats a commit-shaped string as independent GitHub proof;
that publication prerequisite is verified by the coordinating root. It enforces
matching recorded commits in both build receipts, strict finite runtime caps,
the granted single CPU/nice19,4GiB address-space and observed owned-RSS guard,
raw-evidence disk floors, and owned-group cleanup. Only actual future native
runs can establish parity. No NPS, PC eligibility or Elo conclusion is claimed.

Twenty workflow test methods passed across parser/transport, orchestration and
build-dependency suites. Negative controls include using the new chunk tests
against the preserved old single-gzip source: that old preparation fails as
expected. All failures and source versions remain. Existing S11 patch/oracle
and original source-preparation files are untouched.
