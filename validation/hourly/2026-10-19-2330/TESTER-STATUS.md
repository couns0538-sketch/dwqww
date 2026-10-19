# Forge 6.4 independent test checkpoint — 2026-10-19 23:30 CEST

**Decision: BLOCKED for new executable validation; INCONCLUSIVE for qsearch candidate.**

- Accepted development ref (read-only): `forge/6.4-hourly-20261019` = `9108d012526be80c6d163f7cab684e6acd9abf8d`. Verified 2026-10-19 ~23:34 CEST using GitHub branch API.
- Candidate (not merged): `forge/candidate-qsearch-check-20261019-2245` = `3dddd864d45288787b6e949dca5528e88be9f535`, exactly one source diff in `src/search.cpp` at ~729.
- Latest available research: `forge/research-20261019-2315` at `49a69213166d471716e2202bc2bb8612b34bda02`; H2 requests exact search preservation and bench11 baseline 417491 nodes.
- 23:00 audit branch `forge/audit-perft-uci-responsiveness-20261019-2300` still points to unmodified accepted SHA; its previous user-facing source finding has **no GitHub checkpoint on that branch** as of this audit. Do not interpret that as a test.
- 22:30 tester branch also points to unmodified SHA (no checkpoint); latest published tester result is 21:30 `forge/test-20261019-2130` at `2b4d354ca9992caca738c86a53e9caa43e6c66c8`. That checkpoint was model-only, no engine tests.

## New review in this tester stage

H2 qsearch patch moves the `const bool gives_check = board.gives_check(move)` computation from unconditional inside the legal-move loop into `if (!in_check && best_score > -MateInMaxPly)`; source diff verifies the boolean is only used inside that condition. `Board::gives_check` in `src/board.cpp:567-597` is a `const` function whose inspected implementation performs occupancy/attack queries without writing to board state. **Static plausibility only**, NOT a measured PASS. Exact nodes/PV, speed benefit, and runtime safety remain unverified.

## Execution blockers

The tester workspace cannot resolve `github.com` with native `git ls-remote` (`Could not resolve host: github.com`), so the full source cannot be cloned into the local compilation sandbox. The GitHub connector is read/write, but cannot provide a checked-out filesystem for builds. Attempting to publish a new GitHub Actions workflow to the tester branch was blocked by tool safety checks; no remote job was started. No engine binary was built, no new CTest/perft/UCI/sanitizer/fastchess test ran, and no new raw PGNs/logs exist to attach. The isolated report/checkpoint does not modify accepted sources.

## Existing evidence (historical, not retested now)

- `validation/hourly/2026-10-19-initial/candidate-ctest.log` has 4/4 pass for the earlier **TT-tag** fix (NOT for H2).
- `validation/hourly/2026-10-19-initial/baseline-bench11.log` gives 417491 nodes.
- Earlier sanitizer CTest run failed 3/4 due to an LSAN host `/proc`/ptrace fatal error; rerun without LeakSanitizer `sanitizer-ctest-no-lsan.log` passed 4/4. This does not prove a clean standalone LeakSanitizer run.
- 21:30 tester model run reported TT baseline model flagged 3/3 and TT candidate model passed 3/3; this is not a real engine regression test.

## Required :45 handoff

1. Do not merge H2 on this report: build original sources at both SHAs on identical hardware, run CTest (all 4), canonical perft, UCI/ponder, sanitizer and 20+ paired fixed-depth UCI probes. Require identical bestmove, score, node count, PV for speed-only H2.
2. Run bench11 on both (expected 417491 nodes), then 10–20 interleaved paired A/B and B/A same-core timings, preserve raw logs and binary/source SHA-256; only accept real speed gains exceeding measurement noise.
3. Keep any strength claim **INCONCLUSIVE** until a predeclared equal-time color-reversed fastchess 10+0.1 SPRT (Elo0=0, Elo1=+5, alpha=beta=.05) finishes its native boundary; preserve original PGNs, opening selection and runner state. No games were played this stage.
4. Validate high-halfmove TT provenance separately (research H1): existing model evidence cannot establish a real engine defect.

This is a verified status/patch review and a precise blocked test handoff, not an Elo gain.
