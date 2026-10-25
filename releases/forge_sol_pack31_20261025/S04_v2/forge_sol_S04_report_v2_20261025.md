# S04 v2 — patch format and current-tree qualification, 20261025

Status: optional correctness candidate, OFF by default. All eight current L-prime/B profiles pass, 120/120 CTest tests, exactly four KNOWN_FAILURE lines and zero PIN_MISMATCH/FAIL in each current CPP suite. Performance and Elo remain UNPROVEN. The accepted h256_e12 lock is unchanged. Publication is UNVERIFIED until root performs immutable HTTP/SHA/Git-byte readbacks.

The code base is `1ab50b2dd64d9b2f752f7f1285f6968cad2fd792` plus the supplied h256_e12 network overlay SHA256 `74c4009d86b7d3a5ae9e6119d0890e5b923508f4063161bb4bc1539aab275b1b`. The raw commit's own net differs. B additionally retains the supplied buffer fix SHA256 `9ce56b3d9b5291e450679209ac991c4d560bf40f64aa0281492c53ad37d96a5c`. Current merged test source SHA256 `55334ba94fd508d5f8e8e0e715c86a6996eddc69b20b1c110110a96e46deaa2c` is calculated from the supplied file; no expected engine value or pin was edited here.

Patch `forge_sol_S04_v2_20261025.patch`, SHA256 `b425157e6e9521a544e3612f3c32c3955bb1fd3195735692975d5a6d6d89590b`, was produced by private `git diff --full-index -U5`. Four files, +110/-0. It includes the new test's explicit `new file mode 100644`. Actual original patch `29ee0866e90185a6a50f8389d8792399b890338c4e10f6457459652bbb6c15e7` Git checks fail on all L/L-prime/B with `error: dev/null: No such file or directory`; its GNU-F0 applications pass. The v2 Git checks and GNU-F0 dry/apply all pass. All nine applied C++/CMake/test file pairs exactly match v1. Only the unchanged additive IDEA paragraph moves to a safe shared title anchor; removing it recovers every original document byte on its own base. Existing notes remain intact. Dedicated cold-test source SHA256 `24d2fb04cd1982a592f7ed36cdaa348d3a75cfc7a9ecb00a712265f93881ab88`; patch target path is `tests/forge_sol_S04_tsan_test_20261025.cpp`.

`FORGE_ATTACKS_INIT_ONCE` stays OFF. ON uses the already validated std::call_once publication repair around the existing initialization writes. The original cold API race is reproduced when simultaneous first Board constructors arrive before tables exist. The shipped UCI executable constructs its first Board on the main thread, so this cold-constructor race is not reached by its normal startup flow. This patch adds no search, evaluation, NNUE arithmetic, public-layout, TT, move-order, runtime UCI option, counter or default-output change.

|Check|Status|Evidence scope|
|---|---|---|
|Git-check and GNU-F0, L/L-prime/B|PASS|Actual original RED/new GREEN and per-base resulting source hashes|
|20 production files per current base|PASS|Exact original candidate source/include identity; current merged CPP tests freshly compiled|
|Current Release/ASan OFF/ON full suites|PASS|Eight closed actual current CTests; 120/120; KNOWN4, no PIN_MISMATCH/FAIL|
|First bare d11|PASS|Fresh invocation of each qualified main engine before other runtime checks; 308972|
|All five fixed Release references, OFF and ON|PASS inherited|Exact v1 main ELF + source/flags binding, original closed logs; not five new deep runs|
|Both Release perft5 totals, OFF and ON|PASS inherited|4865609 / 193690690 through the same exact main-identity binding|
|NNUE-scoped FMA0|PASS inherited|Original supplied checker result, same exact binary/source; no new checker claim|
|Four whole-executable FMA counts|PASS fresh|Actual objdump mnemonic count0 with all four original disassembly streams preserved|
|Four ON cold TSan CTest targets|PASS fresh|Each newly built from the three current real TUs; separate TSan link excludes ASan|
|Standalone 1000 cold TSan processes|PASS inherited|Exact historical probe/source/flags/raw1000 identity; not rerun|
|Original baseline cold TSan RED|PASS inherited|Actual exit66 race trace; exact current relevant source/test identity, header evidence separately bound|
|Native Windows/PC, speed, Elo|UNVERIFIED / UNPROVEN|No PC work, timed comparison or strength test in this revision|

## Current matrix and build scope

|Base|Profile|Option|CTest|Main ELF SHA256|
|---|---|---|---|---|
|B|asan|OFF|15/15|`71b251bbb8de879cb6eb6eea9840253bb6f047c8dab4b4a71b1902d31036a96d`|
|B|asan|ON|16/16|`d9ec30b460aa51434b34594f862e3e73aea96cbf85a847ed0b4c6bf8485fd943`|
|B|release|OFF|15/15|`55fa7e81768452bf62e5c9fa748d88353e37fbec50492077e70d30f14fc7d406`|
|B|release|ON|16/16|`3a32f15cf87bf47a831f4bbe41d6e206ea18e79967c10eda65e7630fe93190b6`|
|Lp|asan|OFF|14/14|`1dc9b43f19fc5c0062f65a0742e011a96ec468e083abf9f3bf0d087aed614fef`|
|Lp|asan|ON|15/15|`0e42e3b212efffd5b1325f18660d27d77e2e0a9900be3b6ffdd45f47096e3552`|
|Lp|release|OFF|14/14|`e3df99cddb609d9f00168d8df3187fdf6943c10812dd5c4f82206895e594367b`|
|Lp|release|ON|15/15|`73ae743cac18431750e07c2c89878bf6e4caecc0f9b63b3e87dc76e50dbcdaba`|

These are current merged CPP tests and current CMake registrations against explicitly qualified reused main engines, core archives and ordinary helpers. Each source closure, per-target flags, object-member/archive identity and complete LastTest log is in the evidence. Current tests are compiled fresh; the four ON dedicated cold TSan targets are built fresh. No fresh full-target engine rebuild is claimed. Flags retain C++20, H256 float, `-march=x86-64-v3 -mtune=znver5 -ffp-contract=off -fno-fast-math`, Release O3 or ASan/UBSan O1/g1 with documented per-target scopes. Core's ON macro is PRIVATE; frontend/test flags are recorded separately. The standalone historical TSan probe is distinct from current generated CMake targets. Toolchain/system-header bytes were not directly frozen by the original RED capture; this limitation is retained.

The inherited fixed references are depths11/13/16/20/22 = 308972 / 745494 / 2460422 / 11901452 / 31111774. Kiwipete is `r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1`. Native stdout NPS fields are preserved raw and uninterpreted; historical advisory timing is retained separately without a speed verdict.

## Preserved failures and workflow maintenance

The original patch's Git-header defect, metadata producer's overly strict added-blank-line alignment assertion, first controller diagnostic parser error, incomplete archive-generation lookup, and guessed helper-target name are retained separately from successful retries. The latter lookup/name failures blocked observers, not engine or sanitizer correctness. L-prime ASan OFF resumed only pending gates after its first actual d11/current CPP checks had passed. Reports explicitly identify missing independently saved stderr in older pure-observer assertions; no reconstructed raw logs are presented as originals.

Existing repository-local `validating-chess-simd` guidance was improved for complete archive-generation inventories and deriving names from actual generated CTest/CMake registrations. Two before/after reference-command proofs, two probes and four raw control JSONs are bundled. Final local guide SHA256 `2b8b7c906853ae06dfb14f83b34f4b7f0472f96bc35cea2f175ea384a70d1f69`; the intermediate guide/proof is retained in root's7036d53 checkpoint, while the final additive paragraph is subject to root's separate publication verification. This is local reference validation, not a fresh-agent pressure test or cloud/global skill installation. No duplicate skill was created.

## Evidence and continuation

The flat archive's index lists each of 185 original records with path, byte length and SHA256. Original v1 evidence, all current closed commands/full streams, controller revisions/failures, original1000 cold records, source proofs, reviews and four fresh whole-disassembly gzip streams are reversible base64 records inside `forge_sol_S04_raw_evidence_v2_20261025.jsonl.gz`. No binary, object, network, source-tree, cache gzip payload, ZIP, license or agent-instruction export is included. Cache restore metadata refers to local-only retained payloads. Published v1 remains untouched.

Verify outer hashes from this folder, then verify or restore raw evidence:

```sh
sha256sum -c forge_sol_S04_SHA256SUMS_v2_20261025.txt
python3 -B forge_sol_S04_raw_restore_v2_20261025.py --archive forge_sol_S04_raw_evidence_v2_20261025.jsonl.gz --index forge_sol_S04_evidence_index_v2_20261025.json
python3 -B forge_sol_S04_raw_restore_v2_20261025.py --archive forge_sol_S04_raw_evidence_v2_20261025.jsonl.gz --index forge_sol_S04_evidence_index_v2_20261025.json --out NEW_OUTPUT_FOLDER
```

The builder actually restored and compared all 185 original file bytes; an existing output directory is rejected. All S04 native jobs and cache leases are closed. The final independent native/source review passed all eight profiles. Root performs the final report/checkpoint binding and publication plus per-file immutable download comparison, then S05 fix-ups in the user's saved order. No accepted lock switch or speed/Elo claim follows from this correctness qualification.
