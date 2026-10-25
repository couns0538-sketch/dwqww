# Forge S28v2 — 2026-10-25

Required S28-1/2/3 rework is implemented and current L′/B f006 qualification passes. The accepted h256_e12 lock is unchanged. Optional S28-4 is deferred. No speed or Elo claim.

The new coordinator takes an explicit `--lock`, checksum-bound external references and a source-bound S01 helper. It distinguishes `RECORDED` candidate observations, exact `PIN_MISMATCH` drift and post-proposal `KNOWN_FAILURE` output. It fails on missing, extra or drifting case/score/depth/PV diagnostics. Its terminal checker uses the user's actual eleven-point AUTOLOCK clarification plus additions; the earlier prose-derived checker remains a historical generic source/metadata component. The real checklist consumes evidence and never creates CR approval or invokes PC scripts.

## Source and patches

Base code: `1ab50b2dd64d9b2f752f7f1285f6968cad2fd792`, with explicit lock net SHA256 `74c4009d86b7d3a5ae9e6119d0890e5b923508f4063161bb4bc1539aab275b1b`. The six-profile qualification used the supplied f006 net SHA256 `0fdf9bdb6bdf4c9f1622bcef29921912acb139fdf388e541b017a948118d4661` (MD5 `0fae54a4c0c437432ddb5da85512b5f4`). It did not replace the accepted e12 net. Current L′/B include Job C/S01, tests.cpp SHA256 `55334ba94fd508d5f8e8e0e715c86a6996eddc69b20b1c110110a96e46deaa2c`. B additionally preserves buffix `9ce56b3d9b5291e450679209ac991c4d560bf40f64aa0281492c53ad37d96a5c`.

| Patch | SHA256 | Scope |
|---|---|---|
| forge_sol_S28_v2_timepack4_20261025.patch | 4db4069bbd26bf98a880db5a5ce61cda8dbdb7ccdd709545a033c1ca5070cb73 | Requested IDEA paragraph and Git formatting; C++/CMake target bytes equal v1. Git/GNU-F0 passes L/L′/B. |
| forge_sol_S28_v2_e48f006_pin_proposal_20261025.patch | 7feadcd7212c1106f44559bac641f80eaa39c8289bce9d86e5c1aa65c9d29136 | Explicit isolated test/helper/docs proposal. WAC661→629; original g3g6/31997 and promotion guards retained. Git/GNU-F0 and both patch orders pass L′/B; pure L is intentionally unsupported. |

The diffstats are in `forge_sol_S28_v2_patch_diffstats_20261025.json`. V1 delivery and patches remain immutable. The timepack4 parameter remains default0; no optional minimum/ponder/include changes were made.

## Actual native results

Each new frontend's first invocation was a bare f006 d11=328459 gate. Qualified old cores/helpers were reused with exact archive/source/header/flag records; current merged C++ tests were compiled before/after the explicit pin proposal, and release frontends were compiled fresh. This was not a fresh complete all-target rebuild. Retained source/include hashes, flags and dependency recipes were checked; system dependency hashes are current observations, not invented historical header hashes.

| Tree / variant / flavour | Executable SHA256 | Current CTest |
|---|---|---|
| L′ f006 base / release, reused | 668b8483e349d8c11a36bf0ad95cebdcd657aa24cac5739b09981e50f93066f4 | 14/14 |
| L′ timepack4 / release, fresh frontend | 9386a31f82164b59b969685f12d513db241778f25985dcd5fc01f81aafe2db0b | 15/15 |
| L′ timepack4 / expose ON, reused | b81e3b37a583b404695701f92dc73d63ffc06d89985bf96de2de64d22cf5ab9a | 15/15 |
| B f006 base / release, reused | e8682b8407e1a76d4b927d63273103ec27635148d6f0b1c460b65ef97a2ddd83 | 15/15 |
| B timepack4 / release, fresh frontend | cf3fa9a2ec2ea887a1efdd6778f78089468a1e959f156e298f32800417d92281 | 16/16 |
| B timepack4 / expose ON, reused | 18a53264874875412e02134c698a46a716613472617b9803a221f5c253fb4738 | 16/16 |

All six current profiles exit0 with exactly4 KNOWN_FAILURE, zero unexpected FAIL/PIN_MISMATCH and no diagnostics in complete LastTest logs. Before the explicit proposal, both freshly compiled current test suites actually returned PIN_MISMATCH +2FAIL +2KNOWN, exit1. S01 independently records f6h5/629/d12 and c6d7/c3d2/686/d1; after the proposal its default check returns PASS. The original promotion criterion remains score>100; 642/686 are observations, not silently tightened test thresholds.

New release binaries actually match all five f006 references: 328459 /945640 /3024381 /9162399 /20421972. Their actual perft5 totals are 4865609 and193690690. Whole-executable FMA=0 and the supplied v2 checker pass on both release/expose pairs. All four reused core NNUE members match their original closed object SHA and have FMA=0. Old expose-build runtime-option OFF/ON five-depth and perft evidence is inherited only after exact ELF/stage/closed-manifest identity verification.

## Tool and checklist results

| Check | Result |
|---|---|
| V1 rejects current4KNOWN fixture | PASS, original RED preserved |
| Final current-format parser fixtures | 12 PASS |
| Generic source/metadata integrity fixtures | 43 PASS, including binary/unknown raw hashing and valid source CRLF normalization |
| Exact authoritative AUTOLOCK fixtures | 60 PASS, including RH-Q/CAP-LATE, VOID/options, state/history coupling and external review evidence |
| Final actual CLI dry-runs: f006 first, then s198; L′/B | 4 PASS; Git/GNU-F0, helper/ref binding and terminal checklist invocation |
| Missing real AUTOLOCK packet | UNVERIFIED, eleven points plus three additions reported |
| Fresh standalone coordinator `--execute` all-target path | UNVERIFIED; not run in this resource-limited session |
| Windows, live PC, real AUTOLOCK, new ASan/UBSan matrix | UNVERIFIED; no such acceptance claimed |

Main SHA256: `c0cc4790ab569b7751d6535e684820a6a2c8669119cf6e7aa8426eebbd189547`. Authoritative checker SHA256: `cf49c91e146af083a944b592346e48ada9c8f31702180534817981c86a2012e9`. User authority text SHA256: `56b36813b2fc791d0c8c2676188ca56a31eb59b32c6a269d14f6e084405d3160`. Native component functions match the executed frozen snapshot; final CLI source-only integration was rerun against the delivered modules. Native/source independent reviews report no blockers.

The standalone fresh builder remains available for a suitably provisioned Linux host. The actual cloud qualification used the separately recorded cached native controller; no fake or no-op CMake build is presented as a fresh build.

## Real AUTOLOCK boundary

The real f006 AUTOLOCK must keep the original proposals ATTACHED, NOT APPLIED: original pin proposal SHA256 `692b164b2601cf84411a7ea8c4b7892b255a219b2a07e5bdf7167b2cad77a35e`, MD5 `3aecb403afebae7a5046e9e4bd3f8f97`; companion SHA256 `5685e836373afaecafba0e284f35d62402df478beedda7b0f3f40564ef2ccbca`, MD5 `5a4ed6758d7778e26d2d4c504f3a47bb`. The rebased proposal here is exclusively for isolated post-pin qualification. It is not the actual AUTOLOCK tree or its attachment identity.

The user's accepted script successor is a prefix-only identity until a complete measured artifact is supplied. The tool accepts the user's review authority for that successor without another approval request; it still marks absent/full-hash/snapshot facts UNVERIFIED. External CR_PASS evidence stays external. The checker only emits its own consistency/review-readiness report.

## Evidence and continuation

Original child streams, raw source/flag/dependency records, compilation/link commands, CTest logs, hashes and failure controls are preserved reversibly in the evidence bundle. Failed approaches include the initial archived-helper binding abort (captured controller exception and original child records), the binary normalization false PASS and subsequent metadata/checklist peer controls. The resumed native stage reused closed original pin observations and compiled tests; it did not restart successful work. No PGNs or Elo estimates were generated.

The guide gives exact commands. Existing repository-local skill `validating-chess-simd` was improved at commit `f6273ebe0a0f624de049af93496db2c51e26f7d1`, current SHA256 `33831104021fbe8b56152bc7579fdddae87e94d2ee2318b18e4d847892d825d5`. It covers the actual binary-normalization false PASS, per-TU flag scope, complete derived hashes, and manifest count/format validation. Supporting before/after proof files are `forge_sol_S28_v2_skill_reference_maintenance_20261025.json` and `forge_sol_S28_v2_record_format_skill_proof_20261025.json` under validation/forge_sol_pack31_20261025. No duplicate or global skill installation is claimed. All native leases are released. Next: publish this isolated delivery, verify immutable downloads and resume S04v2 in the user's order. Keep h256_e12 accepted until an independently verified new lock handoff arrives.
