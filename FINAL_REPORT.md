# Astra A1–A6 report — 2026-10-29 (review complete; full sanitizer qualification running)

Base: `opus-r3-stack`, `da15814975e224e770f4d25195e0551d02afae48`. Existing Sol checkout preserved; all work isolated on cumulative `astra-*` branches. No main changes, branch deletions or force pushes.

| Job | Delivery | Status |
|---|---|---|
| A1 | astra-gatecap, 3c7939b48fe18a284b2508b72556524ab2b5342d | Not applicable, not in repo; owner-directed skip |
| A2 | astra-j5fix, d54302581df9053a3d0711afc1ac886bd236b469 | Opt-in correctness candidate implemented and tested |
| A3 | astra-bundle-check, 95d0f915f469c228125c3e82b1b80b6fe0d308cd | Implemented; final-review corrections on astra-notes |
| A4 | astra-pawnhist-audit, 19dc434d8e5ba371468f35b53c73c06651919127 | Skipped: source not in repo, merge done by crew (owner report) |
| A5 | astra-tests, a25034de1dfed5f999555779fbb59ad7def7ec4e | Local CI replay passed; hosted run UNVERIFIED |
| A6 | astra-notes | 20-minute review completed; additional full sanitizer qualification running |

## Engine change and scope

The base already protects mate scores. A2 adds `SmpProtectProvenScore`, default false, to preserve the winning TB score band when tablebase scoring and existing `SmpBestThread` selection are active. With it OFF, the original comparator is used. All option writes follow search shutdown/join; selection follows helper joins. No network, search tuning, evaluation, TT or move-ordering changes.

This is score-band protection: SearchInfo lacks per-result TB proof metadata, and ordinary evaluation can reach this numerical band. Actual tablebase files were not available; native fixtures exercise the production comparator and selector. End-to-end TB-file validation is UNVERIFIED. No Windows, speed, adoption or Elo claim.

## Bench and correctness

| Depth | Base nodes | Candidate OFF | Candidate ON (single thread) |
|---|---:|---:|---:|
| 11 | 312866 | 312866 | 312866 |
| 13 | 862329 | 862329 | 862329 |
| 16 | 3024920 | 3024920 | 3024920 |
| 20 | 12389307 | 12389307 | 12389307 |
| 22 | 34048354 | 34048354 | 34048354 |

Every initial bench timing/NPS and repeat is retained in [A2](astra_evidence/A2/README.md) and [A3](astra_evidence/A3/README.md). Single-thread ON bench establishes node identity, not execution of the multi-threaded selection guard. Focused tests exercise that guard. Timings were not controlled performance comparisons.

- Complete Release build passed (GCC14.2, C++20, strict FP, x86-64-v3/znver5 tuning, h256). NNUE object FMA count 0.
- Production base reproducer: 2 failing TB overwrite assertions; candidate focused native and ASan/UBSan/LSan tests: 17/17 PASS.
- Initial full suite: 52/54 PASS, exit8. Four baseline forge_tests diagnostics plus one SMP overshoot assertion failure. Serial base/candidate SMP retests each 133/133 PASS.
- Final serial full suite: **55/56 PASS**, exit8. Only forge_tests fails with those exact four baseline diagnostics; SMP passes. This does not erase the initial failure or prove scheduling caused it.
- A3 initial tests:17 option-checker +10 OFF-comparator methods PASS. Final review found invalid OFF setting false positives; revised suite14 OFF-comparator methods PASS after10 RED subcases. Corrected native all5-depth comparison PASS; hash-only final d11 replay also PASS. Final OFF-validator suite16 methods PASS (including Python3.10 API-absence simulation and multi-chunk hashing).
- A5 exact workflow commands replayed locally: startpos d5 **4865609**, Kiwipete d4 **4085603**; all5 selected cases pass. Deliberately incorrect temporary expectation correctly fails. Hosted Actions API returns Forbidden; hosted run remains UNVERIFIED.

## Remaining work at this checkpoint

The fresh review completed in1239.08seconds and fixed both validator defects. The owner then requested a complete passing sanitizer qualification. All56tests are running again in one uninterrupted invocation, assessed by the unchanged repository policy allowing exactly the four known FAIL lines. Raw CTest and policy results will be reported separately. See astra_evidence/sanitizer_complete_20261029/. Environment outage was recovered without resetting any source. No failed experiment was deleted.

IDEA_SOURCE: Owner A1–A6, Forge source and test contracts, public UCI protocol; no external engine implementation copied.
