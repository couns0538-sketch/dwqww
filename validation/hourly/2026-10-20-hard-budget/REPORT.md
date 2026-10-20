# Forge 6.4 — classify engine hard-budget overruns (20 October 2026)

Starting work head: `d2d8dfe4fe9df20697f993bf44dea0f65e57ba39`. Saved lease was inactive and no Forge/fastchess process was visible in this execution environment. The current source-grounded work remains the TT verification-tag candidate; the first native strength experiment terminated after **6 games / 3 pairs** on **1 Candidate timeout**. No native H0 or H1 SPRT decision and **no new native games** this cycle.

## Finding
The separate cold/warm UCI probe had a **2.0-second harness watchdog**. This is not the engine's internal time budget. With the frozen failing command `go wtime 401 btime 596 winc 100 binc 100`, Move Overhead 10, and original Forge search constants TmSoftDivisor=22, TmIncrementPercent=75, TmHardPercent=60, TmHardSoftMultiple=5, the frozen engine computes **soft=101 ms** and **hard=351 ms**. Previously, a `bestmove` at 650 ms was classified as clean because it arrived before the 2-second harness timeout. That can hide precisely the kind of 1.4-second delay we are investigating.

## Correction
The diagnostic now records `hard_limit_ms=351`, `hard_limit_overrun_ms`, and `hard_limit_violated`. Responses beyond 351 ms but before the 2-second watchdog remain fully journaled; they are not classified as clean. The two timeouts are kept separate. Wall-clock overrun does **not** prove engine causality: host descheduling, stdout buffering, and runner scheduling remain possible contributors. This computation is specific to frozen binaries, settings, and clock—not universal across Forge versions.

## Reproduction and verification
Two new regressions failed against the prior diagnostic (missing constant and missing overrun classification). After the isolated fix **14/14 unit tests passed**; Python byte-compilation passed. Eight ordinary synthetic cold/warm trials produced **8/8 clean**, while four additional deliberately delayed 650-ms trials produced **4/4 correctly identified hard-budget overruns** and **0 clean reports**, without any diagnostic-watchdog expiration. The archive preserves original/corrected source, old and new tests, raw synthetic UCI journals, summaries, stdout/stderr, commands, hashes, and the unmodified prior cycle-4 ZIP.

Full local archive: `forge64_cycle5_hard_budget_evidence_20261020.zip`, SHA-256 `1e5fdb8d0cc1bc1d21f8e3aa53f0e851f5912c81a6d7274e0eb773e4d795d3e3`. The archive is a conversation artifact, **not** uploaded to GitHub; this GitHub commit contains a report and an applicable patch against the previously delivered stage-4 source. Corrected probe SHA-256: `071eaa9b8c56e3f73ed9668795f0c76003b0c160d5a405261e0bac0a6fa5ed2d`, tests SHA-256: `17f2340c053939b883b8983d65b7c60da2c0b232862ef2f7b8e78262dc3e61e8`.

No original metadata-bearing TT-match archive was uploaded or retried. The earlier explicit-approval restriction remains in force.

**Next:** recover the hash-frozen native Linux binaries in an authorized environment and reproduce warmed-state timing under controlled single-lane and load conditions without overlapping workers. Preserve the terminal failed SPRT unchanged; any prospective strength match must be separately frozen/preregistered and pass the native H1 boundary. No speed or Elo claim is made here.
