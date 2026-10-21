# Windows 24 auditor adaptation (preparation only)

Derived only `independent-artifact-audit.py` from immutable Windows 23 auditor
`validation/tt-refresh-windows-20261021/independent-artifact-audit.py`.

- Original SHA256: `8cd5c8cdf9220c2e5a435dc0098c706d2bbb74159fd362b2d2ff2446ebd5e8a2`
- New SHA256: `8ad52c7c2a79be491d70b5bfef1ca8f2021bd4c161af09ec59aab663bf60a318`
- Byte diff: 63 added / 36 removed lines; no original file changed.
- Frozen source: `7db08eac6ead99d641834c56ccec06a06600586a`; parent: `1d3ed25bea2c8b781f7ee5a178af0f66061b3984`.
- Exact core source hash checked during preparation: `93c56defd68beb9812b734594f3395b3296bb9aea81ed680ee600c528e94a7b9`. Actual output syntax from tests.cpp404-405 is `SEE threshold contract: assertions 504 failures 0`, matching the anchored unique-summary parser.

Diff scope: Windows 6424/release 6.4.24 namespace and parent23 preservation; mandatory exact root24 source, proof namespace/path and root-published FREEZE proof hash; four source deltas with existing tests/tests.cpp changed and TT/PV tests unchanged; raw SEE504 marker/runtime fields; source getter/nonpositive guard/arithmetic-expression checks; sixth actual core object/source/compile/tested-PE record; pure-proof-reuse/no-evaluation-change/no-speed-or-Elo claims. Source/PE counts stay 74/77, 14 CTests, 13 Wine checks and 11 built/10 shipped PEs.

The first bench value stays unknown in FREEZE and must be a single original positive capture. Only after parsing/freezing that actual evidence does this auditor require equality to parent23 334752. It cannot synthesize the captured value or invoke another engine. Source/stdout/stdin/runtime/settings/PE identities, closed-package and freeze-before-package gates are retained. Parent preservation count comes from actual PROTOCOL data, without reusing 604.

Main-driver schema dependencies: `see_threshold_assertions=504`, runtime `see_threshold_assertions`/`see_threshold_failures`, and `see-threshold-object-provenance.json` fields `object_sha256`, `core_test_source_sha256`, `tested_pe_sha256`, `compile_records`, `assertions`. Package scope flags must identify pure SEE proof reuse, intended exact evaluation/search parity and no new coupled TT policy trial; README must declare `runtime/pawn/nearest/PV metadata/TT/core test objects`.

Validation performed: source-only Python AST parsing, bounded text assertions, immutable template hash check, and core source hash/marker inspection. No imports of prepared helpers, exports, compiler, engine/Wine, artifact audit, Git or network operations occurred. Root proof byte identity was checked against the root-published hash; full native clearance remains pending and this file grants no execution authority. The exact read-only diff is reproducible with `diff -u ../tt-refresh-windows-20261021/independent-artifact-audit.py independent-artifact-audit.py`.

Published root24 source-gate SHA256, pinned exactly in FREEZE and checked as a read-only source identity during preparation: `8be7f3a73111350eca27adbe76bf001e5ab26915c73f1201c3056f881a87afd1`. Source/baseline/77-input schema matches the declared revisions. Parent23 protected-file count remains actual PROTOCOL data (root currently reports 597), without a fixed count in this auditor.
