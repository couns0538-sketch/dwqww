# Astra continuation — 2026-10-29

Base: `opus-r3-stack`, `da15814975e224e770f4d25195e0551d02afae48`.

## A1 — not applicable, not in repo
The exact base tree has no `tools/forge_queue.ps1`. The owner confirmed the script lives only on the gate PC and explicitly instructed skipping A1. No queue code was imported or modified. Continue with A2, then A3–A6.

Previous Sol work remains in `/workspace/dwqww`, branch `forge/sol-pack31-20261025`, head `17aa0cae1d36bc88bf93e873905c058e0de5faac`; its uncommitted checkpoint and unrelated work are preserved. This new checkout is isolated under `/tmp/forge-astra-20261029`.

IDEA_SOURCE: Owner-provided A1–A6 specification and Forge's own source; no external engine code.

## A2 — implementation checkpoint; native qualification running
- Existing base already protects mates. Reproduced the remaining TB-score ranking overwrite in the real `better_thread_result`: 2 failing assertions on the unchanged base.
- Added UCI `SmpProtectProvenScore`, default false; only used by existing `SmpBestThread` selection. Mate behavior is unchanged. The new guard preserves the winning TB score band while tablebase scoring is active.
- Score provenance limit: `SearchInfo` has no proof/bound tag, and the current evaluator can reach that numerical band. This repair conservatively protects the score band; it does not prove every high static score came from a TB probe.
- Release build/full tests pending at this checkpoint. RED reproduction is the production ranking function; actual private selector fixtures are additional candidate tests.
- Base bench d11/13/16/20/22: **312866 / 862329 / 3024920 / 12389307 / 34048354**. These replace old h256_e12 numbers for this explicitly changed base. No speed/Elo claim.
- Recipe: GCC 14.2, Release, C++20, `-march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256`; CMake builds outside checkout.

A2 test development: the first candidate direct run had one fixture failure: ordinary-main and TB-helper accidentally shared the same best move, triggering the existing same-move no-replacement rule. Corrected the fixture to distinct legal moves; the original failing output is retained. No production behavior was changed for that test correction.

A2 completed as an isolated correctness candidate: full Release suite 52/54 initially (four exact baseline forge_tests diagnostics plus one scheduler-sensitive SMP overshoot assertion). Controlled serial base/candidate SMP retests both 133/133 PASS; the initial failure is not erased. Native focused selector and ASan/UBSan/LSan 17/17 PASS. All five OFF/ON bench counts equal base; FMA 0. No Elo/speed claim. Review and raw evidence: astra_evidence/A2/. Proceed to A3.

## A3 — complete
Option checker (17 tests) and OFF identity script (10 tests) implemented, registered in CTest (2/2 PASS), independently reviewed. Final native all-five-depth OFF comparison PASS: 312866 / 862329 / 3024920 / 12389307 / 34048354 for both binaries. Correctly rejected the base when candidate-only option was required. Raw logs/specs/review and all bench timings: astra_evidence/A3/. No speed/Elo claim. Proceed to A4.

## A4 — skipped: source not in repo, merge done by crew
Owner confirmed packe2r lives only on the gate PC and its merge was completed elsewhere; explicitly instructed skipping this job. No merge or engine change performed here. Pack A handoff hash was verified; lookup notes retained in astra_evidence/A4/. Crew merge status is owner-provided, not independently revalidated. Proceed to A5.

## A5 — complete; hosted execution UNVERIFIED
Reused existing perft tests in a dedicated Astra CI workflow. Local replay PASS: startpos d5 4865609, Kiwipete d4 4085603; negative fixture rejected. API access to hosted Actions returned Forbidden. Evidence: astra_evidence/A5/. Proceed to A6 and the owner-requested final 20-minute review.

## A6 — final review resumed after environment outage
The environment disconnected during the first review and recovered on the next user turn. Local review files and completed serial CTest survived: 55/56 PASS, only forge_tests with the exact four baseline diagnostics; SMP passed. Original 52/54 run retained.

Review reproduced an A3 false positive for OFF values incompatible with advertised option types/ranges. Fix now uses the existing strict option parser, validates controlled settings and candidate OFF values, and rejects overrides of Threads/Hash/OwnBook. RED: 10 failing subcases; GREEN: 14 OFF-checker test methods plus 17 option-checker tests. Native all-five comparison and independent re-review running. No new engine source changes.

Fresh 20-minute review clock is in astra_evidence/final_review/resumed_review_clock.json; do not treat IN_PROGRESS as complete. Next: finish native verification, preserve independent reviews, publish final report, verify remote head.
