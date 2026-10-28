# Astra A1–A6 final report — 2026-10-29

The requested final review completed in **20 minutes 39 seconds**. It fixed two validation-tool defects. The subsequent complete, uninterrupted ASan/UBSan/leak qualification **passes the repository's existing exception policy**, with zero sanitizer reports. **Raw CTest remains 55/56**, exposing exactly four pre-existing tactical diagnostics in forge_tests. No expected values, engine source, or sanitizer checks were changed to obtain that policy result.

Base: `opus-r3-stack`, **da15814975e224e770f4d25195e0551d02afae48**. Engine implementation checkpoint: **d54302581df9053a3d0711afc1ac886bd236b469**. Final checker fixes: **3a8e7785f4ce65ca006bc70863a4af0ed959b7d4**. Cumulative delivery branch: **astra-notes**. Existing Sol work remains preserved in its original checkout; main was untouched, with no force pushes or file/branch deletions.

| Job | Result | Delivery checkpoint |
|---|---|---|
| A1 | Not applicable, not in repo; owner-directed skip | astra-gatecap, 3c7939b48fe18a284b2508b72556524ab2b5342d |
| A2 | Opt-in SMP winning-score-band protection implemented and tested | astra-j5fix, d54302581df9053a3d0711afc1ac886bd236b469 |
| A3 | Option checker and OFF identity tool implemented; both review defects fixed | astra-bundle-check, 95d0f915f469c228125c3e82b1b80b6fe0d308cd; corrections on astra-notes |
| A4 | Skipped: source not in repo, merge done by crew (owner report) | astra-pawnhist-audit, 19dc434d8e5ba371468f35b53c73c06651919127 |
| A5 | Perft CI added using existing tests; local replay passed | astra-tests, a25034de1dfed5f999555779fbb59ad7def7ec4e |
| A6 | Review, corrections, evidence and continuation checkpoint completed | astra-notes |

## Engine change

The base already protects mate scores. A2 adds **SmpProtectProvenScore**, default false, to preserve the winning TB score band when tablebase scoring and existing SmpBestThread selection are active. OFF retains the original comparator. UCI changes the option after search shutdown/join, and selection follows helper joins.

SearchInfo has no per-result proof tag and ordinary evaluation can reach this numerical band. This is conservative score-band protection; actual tablebase-file integration remains UNVERIFIED. Native fixtures exercise the production comparator and selector. No strength, speed, adoption or Windows qualification claim.

## Final review corrections

1. OFF validation previously accepted incompatible settings such as spin zero when min=1, or false for a button, and could falsely report PASS. It now reuses the strict companion option parser, checks requested types/ranges and rejects changes to controlled Threads/Hash/OwnBook settings. Original RED cases remain preserved.
2. The OFF script used Python3.11-only hashlib.file_digest despite the project's Python3.10 minimum. It now hashes in bounded chunks. The missing-API regression and multi-chunk integrity test pass. The API-absence case was simulated on Python3.12; an actual Python3.10 interpreter was not available.

Distribute tests/bundle_off_identity.sh together with tools/check_bundle_opts.py in their repository-relative layout.

## Verification

| Check | Result |
|---|---|
| Complete Release and ASan/UBSan builds | PASS; GCC14.2, C++20, h256, strict FP |
| Focused selector tests | PASS, 17 native and 17 ASan/UBSan/LSan assertions |
| Production base reproducer | Two TB-overwrite assertions fail as expected |
| Comparator differential grid | PASS, 21,600 cases; base/OFF byte-identical; enabled invariant holds |
| Live UCI option changes | PASS, two/three threads, four active-search toggles, six legal replies |
| Final tool tests | PASS, 16 OFF-checker +17 option-checker methods, plus11 independent final probes |
| Complete serial Release CTest | Raw FAIL, 55/56; exact four baseline diagnostics |
| Complete uninterrupted sanitizer CTest | Raw FAIL, 55/56; all56 executed; same four diagnostics |
| Existing sanitizer acceptance gate | PASS, exit0; no additional failures or ASan/UBSan/leak reports |
| Frozen qualification inputs | PASS, all64 actual inputs unchanged; four generated outputs preserved separately |
| A5 startpos d5 / Kiwipete d4 | PASS, 4865609 / 4085603; incorrect-reference control rejected |
| NNUE object FMA instruction count | PASS, zero |
| Hosted GitHub Actions / Windows / real TB files / full-engine TSan | UNVERIFIED |

The complete sanitizer run took **732.91 seconds**, using leak detection, ASan abort-on-error and UBSan halt-on-error. It ran all56 registered tests in one invocation; the completeness guard rejects omitted, duplicate, skipped, timed-out or abnormal results. The exact existing policy blob is **53b04af3ba00f77ba56e16ebdd9916ded628cc8a**. Raw CTest exit8 and policy exit0 are preserved separately. The earlier interrupted run and successful38-test resume remain visible and were not reconstructed into a complete run.

Initial Release CTest was52/54: the four baseline diagnostics plus one SMP overshoot assertion. Controlled serial baseline and candidate SMP retests each passed133/133; the final full Release and sanitizer SMP tests passed too. This does not erase the original failure or establish its cause.

## Every native bench result

| Depth | Base nodes | Candidate OFF | Candidate ON, one thread |
|---|---:|---:|---:|
| 11 | 312866 | 312866 | 312866 |
| 13 | 862329 | 862329 | 862329 |
| 16 | 3024920 | 3024920 | 3024920 |
| 20 | 12389307 | 12389307 | 12389307 |
| 22 | 34048354 | 34048354 | 34048354 |

All **47** native bench records, including every time/NPS value, are retained in [A2](astra_evidence/A2/README.md), [A3](astra_evidence/A3/README.md), and the [final review](astra_evidence/final_review/README.md). Timings are not controlled speed comparisons. One-thread ON bench confirms identity but does not exercise multi-thread result selection; dedicated fixtures and live UCI tests cover that path.

Release engine SHA256: `1c3c0d03d43ab09d8abeb66dac576b9093df6f033198fbe0dafb23f02a5b5551`.
ASan engine SHA256: `80ee69c0f7d213d8323211562a5fba1bec1141753595c69fd3aa1ec7fa8c2fc5`.

## Evidence and remaining issues

[Complete sanitizer record and reproduction commands](astra_evidence/sanitizer_complete_20261029/README.md), [machine receipt](astra_evidence/sanitizer_complete_20261029/uninterrupted_run/receipt.json), [full original test output](astra_evidence/sanitizer_complete_20261029/uninterrupted_run/LastTest.log), [policy decision](astra_evidence/sanitizer_complete_20261029/uninterrupted_run/policy_gate.log), and [continuation checkpoint](NOTES.md).

The four known diagnostics remain real test failures. Independent legal-move enumeration confirms WAC001's Qg6 forces mate in two, while the baseline search misses it at depth12. In the two promotion cases, shallow unrestricted search chooses legal king moves rated above rook promotion; forced queen promotion is correctly scored as stalemate. These observations do not identify the precise search cause or prove stronger play.

Next highest-value engine task: isolate the WAC001 selective-search miss on this exact frozen network/source, establish causality, and only then implement a bounded opt-in repair. Retain real-tablebase integration, Windows testing and hosted CI as separate unfinished qualifications. GitHub Actions API access returned Forbidden; local CI replay passed, hosted execution was not verified.

IDEA_SOURCE: Owner A1–A6 and final-review/sanitizer instructions, Forge's own source and CI policy, public UCI protocol; no other engine implementation copied.
