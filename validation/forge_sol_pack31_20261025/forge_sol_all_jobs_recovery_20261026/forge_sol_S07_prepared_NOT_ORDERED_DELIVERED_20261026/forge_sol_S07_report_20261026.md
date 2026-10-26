# S07 preparation report — 2026-10-26

Status: tool and synthetic subprocess validation prepared; native acceptance pending root execution. No native engine, bench, compiler, match or native WAC process was launched by this task. Git/network/publication was left to the root.

The exact S7 spec and its 10:30 rework were read from lines 322ff of `HANDOFF_PROMPT_FULL_20261025_1435.md`. The importer reads the actual P23b `artifacts/bench.log` and supplied `19_screen_ref_p23b/README_p23b_lock_table.md`. Raw artifact OFF rows reproduce 308972/745494/2460422/11901452/31111774; raw expose and release primary ON rows reproduce 311855/745052/2594099/10785772/22307140. The 12-setting table imports separately as supplied documentary evidence: individual raw logs for every tunable combination are unavailable here. Original artifact hashes are retained in the import JSON.

The current absolute deep guard flags m1 r4 (+22.9% at d22), m1 r5 (−28.3%), and m4 r6 (−22.4%). The historical README accepted some reductions, and additionally marked smaller changes at other depths as failures. Its original label is retained verbatim; current guard results are computed without forcing agreement. m4 r6 automatically selects PC precheck d16: OFF 2460422, ON 2460426.

Actual WAC source verification: SHA256 `9bfb7b42cf5bbc7f3d60ff767ca3be460e0ae4d9110ef9a71ddf0bd7071d4d46`, 22,862 bytes, 300 unique exact WAC.001..WAC.300 IDs, all boards valid, all bm/am moves legal, zero parser exceptions, 37 positions with multiple accepted bm moves. Verification used existing chess 1.11.2 and the original EPD, without an engine. WAC.274 accepts g6b6/g6g5 and excludes g6d6; set membership is used, so bm ordering does not affect scoring.

Tests were written before the implementation. `forge_sol_S07_initial_RED_20261026.log` records the missing implementation. The first GREEN had 16 tests; independent source review found runtime trailing-summary and descendant cleanup edges, then five added RED cases. `forge_sol_S07_review_edges_RED_20261026.log` retains those actual failures, including an unrelated short-timeout failure under concurrent load. Runtime synthetic fixture timeout was raised to 2 seconds except the intentional timeout case. The corrected 21-test suite passed; the final 24-test suite passed in 24.710 seconds, adding live-option, explicit release-tunable declaration and raw-byte/hash checks. All subprocesses in these tests are explicitly synthetic Python doubles; their node numbers and move outputs are fixtures, not native engine observations.

Independent review findings were addressed: full captured bench output is revalidated; process groups with pipe-holding descendants are cleaned; silent unknown names fail absent an explicit caller allowlist; bounded capture overflow remains a failure even after the last awaited reply; deleted input still produces a failed result with process receipts. Timeout, nonzero exit, unknown option, illegal bestmove and existing-output cases are exercised. Native performance, NPS and strength were not inferred from these tests.

Native fields for root completion:

| Field | Status |
|---|---|
| Frozen canonical executable provenance independently rechecked by S07 | UNVERIFIED |
| Fresh native L or accepted canonical ELF five-depth OFF sweep | UNVERIFIED |
| Native candidate OFF/ON five-depth sweep and option-live evidence | UNVERIFIED |
| Native current absolute deep-node guard acceptance | UNVERIFIED |
| Native WAC300 fixed-time OFF score | UNVERIFIED |
| Native WAC300 fixed-time ON score | UNVERIFIED |
| Native engine illegal moves/process exceptions | UNVERIFIED |
| Native resource lease/CPU isolation checks | UNVERIFIED; root owned |
| Publication/integration | UNVERIFIED; root owned |

The delivered offline import PASS describes successful artifact parsing, and corpus validation PASS describes original-data parsing. Neither means a native engine screen or strength acceptance passed. See the README for CLI usage, dependency locations and the root-provided L/L′/B controls.
