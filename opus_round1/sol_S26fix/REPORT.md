# S26fix — S26 net-batch fix-ups: v4 re-run on CI, v5 fix, f023 pin root cause, per-net ASan/UBSan, closed-net summaries — DONE

Branch `opus-sol-S26fix` = `d4f4312` + CI baseline (cherry-pick 7578c69b) + 08ec677e (CI scaffolding) + 3f7cc526 (v5 + CI) + 4f1c73ec (evidence).
No engine source change on this branch (the AL1 tree is untouched).
Base B (Sol's forge_h256_e12_buffix_jobC_S01_src) is rebuilt by ci/make_base_B.sh = AL1 source + e12 net + buffix + B pre-merge docs + Job C/S01 merge. It equals Sol's recorded 78-file snapshot byte for byte (PC and every CI job).
Sol's files are unchanged. Machine exclusive: no.

CI runs:
- opus-sol-s26fix 40505681846: conclusion "failure", but only because the job's own first ASan checker mislabelled f023 (finding 3). All v4 receipts were produced.
- opus-sol-s26fix 40507421791: success (v4, v5, ASan).
- opus-ci 40505681678 and 40507421768: success. The ASan log shows ctest ran and the known-failure check passed.

## Acceptance
| line | result | evidence |
|---|---|---|
| S26-1 short summary .md per closed net (verdict + key numbers) next to the f019/f020 JSONs | DONE: closed_nets/<net>/SUMMARY_<net>.md for B_lock, f019..f023, next to Sol's native result JSON (f019/f020 with his closed-folder JSONs, byte copies) and the CI summaries; rendered from the JSONs and byte-verified | forge_sol_S26_closed_net_summaries_20261027.py verify -> PASS |
| S26-v4-1 re-run the six native first attempts under v4 4dbf73e6 and publish receipts | DONE on Linux CI (v4 needs fcntl, /proc, sched_setaffinity; it cannot run on the Windows PC). Runs 40505681846 and 40507421791, plus v5 in 40507421791. Every net: tool sha256 4dbf73e6, g++ 14.2.0, 19 TUs, bench d11..d22 = frozen refs, FMA 0, UCI WAC001/promotion observations = v3, forge_tests diagnostic lines = v3 | evidence/ci/<run>/ (summary, result.json.gz, junit, pin proposals) + ARTIFACT_SHA256SUMS.txt; full artifacts in F:\opus_scratch\sol_S26fix\ci_runs\ |
| v4 defect found in the native re-run | f023: v4 reports "CTest case was not run: forge_tests" because native CTest JUnit writes status="fail" for a test that ran and failed (v4's synthetic fixtures never set status). v5 (new file, one changed check) reports the true reason, identical to v3 | test_forge_sol_S26fix_20261027.py (real CI JUnit as fixtures); v5 f023 summary |
| S26-v4-2 root-cause f023 PIN_MISMATCH (661 documented vs 620 actual) | DONE: 661 is the h256_e12 lock net's own WAC001 observation (B_lock f6h5 661). tests.cpp:176-195 accepts g3g6 mate or exactly f6h5/661/d12. f019-f022 find the mate at d12 (pin never consulted). f023 plays the same horizon move with its own 620 cp in every run (v3, CI v4 ×2, v5, ASan build, UCI Hash 8). Net-specific pin, not a tool, engine or flakiness defect. Expectations not edited; v4/v5 wrote the UNREVIEWED 661->620 proposal | logs/f023_pin_rootcause.json (consistent: true) |
| S26-v4-3 per-net ASan/UBSan (CI) | PASS 6/6 (run 40507421791): 0 sanitizer reports, all 15 tests ran, forge_tests lines = the net's Release lines, ASan-build bench d11 = ref | closed_nets/*/ci_asan_check.json; evidence/ci/40507421791/s26fix-asan-* |
| S26-v4-3 copy the 15k-line index + .jsonl.gz into evidence/ (SHA256 only in the release folder) | DONE: evidence/sol_S26_original/ (be2174ea… 6,590,435 B; 70b2127d… 15,344 lines); RELEASE_FOLDER_SHA256_ONLY.txt; Sol's restore tool: VERIFIED records=958; nothing deleted on Sol's branch | logs/capsule_verify.log |
| tests | 11 OK | logs/tests.log |

## Findings
1. WAC300 at 1000 ms is machine-bound. CI runner: B_lock 284/282/284, f019 283/283/285, f020 283/287/287, f021 289/287/287, f022 285, f023 284 (v4 run 1 / v4 run 2 / v5). Sol's box: 268/260/238/242/226/238.
2. On CI, f019 and f021 now meet their documentary refs (within 3). f020 is 4-8 above its INFO-only 279. Sol's WAC FAILs were a slow or loaded machine, not the nets.
3. The job's first ASan checker had the same status="fail" mistake as v4 (f023 marked "not run"); fixed, so run 40505681846's "failure" conclusion is that artefact.

## Note
The S26 evidence (about 11 MB: Sol's capsule copy, gzipped nets, CI receipts) is now in the shared git object store.

## Left / UNVERIFIED
- v5 is a fix candidate; Sol's portable setup still pins v4's sha256.
- f022/f023 have no measured documentary WAC refs.
- No net adoption, no Elo or speed claim.
- Windows-native v4/v5: not possible (Linux APIs). Per-net TSan: not asked, not run.
