# S25 v2 — strict bench/UCI output contract, 20261025

The output-contract checker passes on all four current L-prime/B Release and ASan/UBSan profiles, with 66/66 current CTest tests passing and exactly four known outcomes in each CPP suite. The exact prior shelved default-OFF fixture remains a verified negative for both the post-summary bytes and the extra typed UCI option. It was not replayed, rebuilt or adopted. `FORGE_OUTPUT_CONTRACT` remains OFF by default; accepted h256_e12 is unchanged. Speed and Elo remain UNPROVEN. Publication is UNVERIFIED until root's immutable HTTP/SHA/Git-byte readbacks.

The code base is `1ab50b2dd64d9b2f752f7f1285f6968cad2fd792` plus the explicit supplied h256_e12 network overlay SHA256 `74c4009d86b7d3a5ae9e6119d0890e5b923508f4063161bb4bc1539aab275b1b`; the raw commit's net differs. B retains its supplied buffer fix. Current merged `tests/tests.cpp` SHA256 `55334ba94fd508d5f8e8e0e715c86a6996eddc69b20b1c110110a96e46deaa2c` is calculated from the file. Production src/include and all pre-existing tests are preserved.

Patch `forge_sol_S25_outcontract_v2_20261025.patch` SHA256 `32bc590c23f05944fe112bc6691578e9e041a26d5268bbb4b70f6963b3214d49` is private Git full-index/U5 output, 5 files, +208/-0, with three explicit new-file mode100644 headers. Actual old patch Git checks fail `dev/null` on L/L-prime/B while GNU-F0 passes. New Git-check and GNU-F0 dry/apply all pass. The CMake bytes, checker, typed allowlist and parser test file are exactly v1 on each corresponding base. The same additive IDEA paragraph uses a safe common title anchor and preserves all existing notes. Original16-file publication at afb285e2044741e4598b0dea3222390acdb45a8a remains untouched.

## Contract and actual negative

The checked-in allowlist comes from the original source authority, not from candidate output. It defines ten option names with exact types/defaults and spin bounds: Hash, Threads, Move Overhead, Ponder, OwnBook, Book File, Book Depth, Book Variety, UseNNUE and Clear Hash. The first engine invocation is only `bench 11` then `quit`, requiring308972 nodes. One exact LF or CRLF summary terminator is required and zero bytes may follow it. Blank/stat tails, malformed/duplicate summaries, prefixes and missing terminators fail. When the fixed-node precondition holds, a separate `uci`/`quit` process still runs after a tail failure, so both problems are retained. Extra/missing/duplicated/malformed or metadata-changed options fail the typed comparison. Captures wait for EOF and child exit; no caller affinity/host-limit/signal changes are made.

The retained negative ELF SHA256 is `f4365f194f6d781a3ff79b4770495f24f125ef3e65d5ef48bece5183ae993465`, distinct from the QA reference `ba6cc6756cd10cff4924df9c0ac9419e08dde395f798d0367c66b21c1f12bc63`. Its exact source/flags binding records the shelved backend compile switch OFF, no backend define, static linking and `-march=znver5`; it is a separate fixture, not the current dynamic x86-64-v3 canonical build. Both original engine child processes exit0 with EOF observed. The first d11 node gate passes308972, but the checker exits1 with both `bench_post_summary_bytes` (134 original bytes, SHA256 `67f2c884cd33897f009c752ce668c36eaf9866a1647cff83b1b6485051845d30`) and `unexpected_option` (`NnueExactInt32`, check/default false). Original int32 refresh/update counters are zero; no backend activation/adoption is claimed. The checker/allowlist/parser remain byte-identical, so these exact original control bytes are inherited without running or rebuilding the shelved implementation.

|Check|Status|Scope|
|---|---|---|
|Git-check/GNU-F0 all three bases|PASS|Actual old RED/new GREEN;26 source-application streams|
|v1 CMake/checker/allowlist/parser identity|PASS|Exact corresponding applied bytes; no expectation edits|
|Implicit default OFF cache/registration|PASS|Four actual configurations; new targets absent; L-prime14/B15 baseline counts|
|Current ON full CTest|PASS|Four actual suites, 66/66, KNOWN4/PIN0/FAIL0|
|Current parser controls|PASS|12 cases per registered current parser CTest|
|Current native contract|PASS|Each current bench/uci child exits0/EOF; strict summary tail and typed list accepted|
|Exact shelved negative|PASS inherited expected RED|Both independent violations in original byte records; no new execution|
|Release five reference depths/perft5/FMA|PASS inherited only|Exact current production/main/source/flags binding, prior original qualification; no fresh deep sweep|
|Windows runtime/speed/Elo|UNVERIFIED / UNPROVEN|No PC or strength work in S25 v2|

## Native matrix and reuse

|Base|Profile|ON CTest|Implicit OFF target count|Main ELF SHA256|
|---|---|---|---|---|
|B|asan|17/17|15|`1564bd068a03c0293983b666a8fdfb2d56e8d2c2406485e36114bf0af7a9a8e6`|
|B|release|17/17|15|`55fa7e81768452bf62e5c9fa748d88353e37fbec50492077e70d30f14fc7d406`|
|Lp|asan|16/16|14|`61da67f15ebce9edb186d5cf76dac7096a486584d2382e54e7c6eabadcd4e23e`|
|Lp|release|16/16|14|`e3df99cddb609d9f00168d8df3187fdf6943c10812dd5c4f82206895e594367b`|

These are fresh current CMake registrations and actual full-suite executions. The source/flag-bound main/core/ordinary helpers and exact current merged CPP executables are reused from the qualified S05 matrix. No fresh C++ compilation or full-engine all-target rebuild is claimed. Each profile preserves current all-target implicit-OFF/ON flag equality, all seven core archive-member identities and complete LastTest output. The existing current CPP source is still the exact merged55334 version, not a historical four-FAIL executable. Both new Python targets are present only ON. Current Release/ASan direct engine invocations obey the first bare d11 gate. The source patch changes tests/docs/registration only; no evaluation, search, NNUE/backend, network, TT, move-order, runtime UCI option or default-output change.

H256 remains float with C++20, `-march=x86-64-v3 -mtune=znver5 -ffp-contract=off -fno-fast-math`; Release O3 and ASan/UBSan O1/g1 scopes are in the exact per-target records. Fixed d11/13/16/20/22 references remain308972/745494/2460422/11901452/31111774 and perft5 totals4865609/193690690. Release deep refs/perfts and FMA proof are inherited by exact engine/source identity rather than repeated; ASan profiles have their actual first d11/current full suites, without a new deep-ASan sweep claim. Existing ordinary-helper and current CPP passes are retained separately from prior old FAIL-format test history.

Two native-preflight observer attempts failed before engine work while assuming incompatible recorded-blob/native-authority schema fields. A later last-profile low-free-space guard stopped preparation and resumed only its pending gates after verified closed-cache recovery, preserving the first three completed cases. Both original failures and corrected preflight metadata are preserved; they are provenance preparation failures, not engine/sanitizer regressions. The current four-case native matrix records its own actual outcomes and resource-stop history. Existing SIMD patch-format and exact-record-schema guidance already covers the metadata-only lesson; it was reused without creating a duplicate skill; this S25 requalification makes no guide edits and preserves the frozen S04/S05 artifacts. The existing guide's later S05 publication-pointer/blob-schema refresh is additive, recorded separately at validation/forge_sol_pack31_20261025/forge_sol_S05_v2_skill_reference_refresh_20261025.json. No cloud/global skill installation is claimed.

## Evidence and continuation

The flat delivery has the patch, three exact test/allowlist files, source/native review and 115 reversible original-byte records. The index gives each path, byte count and SHA256. All current native commands/full streams, original strict-contract child captures/results, complete LastTest logs, source application, controller/cache/preflight failures and resume audits are preserved. Inherited negative evidence is limited to three metadata files and seven exact raw records; baseline qualification uses the original provided-handoff receipt/script and small S05 source/current-matrix authority. The entire old101-record corpus is not redelivered. No shelved backend patch, engine, network, object, source-tree, cache payload, ZIP, license or agent-instruction export is included. Cache payloads referred to by prior recipes remain local-only.

```sh
sha256sum -c forge_sol_S25_SHA256SUMS_v2_20261025.txt
python3 -B forge_sol_S25_outcontract_20261025.py /path/to/forge --out /path/to/NEW_RESULTS_FOLDER
python3 -B forge_sol_S25_raw_restore_v2_20261025.py --archive forge_sol_S25_raw_evidence_v2_20261025.jsonl.gz --index forge_sol_S25_evidence_index_v2_20261025.json --out NEW_OUTPUT_FOLDER
```

Keep the exact options JSON beside the standalone checker. The reused portable decoder actually restored and byte-compared every record; existing output is rejected. All S25 native jobs/cache leases are closed. Next: final independent report/checkpoint binding, root publication plus actual per-file immutable readbacks, then S27 in the saved order. No engine acceptance, speed gain or Elo claim follows from these tests.
