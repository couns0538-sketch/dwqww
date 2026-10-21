# Forge 6.4.23 TT-refresh vs 6.4.22: independent original-evidence audit
Date: 2026-10-21 UTC. Audit only; no source modification, match rerun, or acceptance change.

## Result
Completed GitHub Actions run [39537333958](https://github.com/couns0538-sketch/dwqww/actions/runs/39537333958) reported CI success. **CI success is not an SPRT PASS.** Original archived Fastchess SPRT ended at its predeclared 512-pair cap, **INCONCLUSIVE**.

- Frozen baseline source: `ff2e269c6058be84456e3b98344826d17b0056eb` (6.4.22)
- Frozen candidate source: `1d3ed25bea2c8b781f7ee5a178af0f66061b3984` (6.4.23, occupied TT-generation refresh)
- Actual match: logistic Elo0=0 / Elo1=+10, alpha=beta=0.05; equal `1+0.01` time controls, Threads=1, Hash=32, OwnBook=false, serial concurrency=1. Hosted Linux AMD EPYC 7763.
- Independent original PGN recount: **1024 games / 512 same-FEN color-reversed pairs**, **W215 / D569 / L240**, 135,139 plies and 512 unique paired openings. All PGN headers report normal termination.
- Pentanomial `[30,128,217,111,26]`, outcome score 499.5/1024 = 48.7793%.
- Native Fastchess LLR -2.51, boundaries [-2.944439, +2.944439]. Independently recomputed logistic-pentanomial constrained-MLE **LLR -2.5124062624954604**, matching Fastchess and the original runner's preserved independent auditor. Neither boundary reached.
- Native descriptive Elo **-8.48 +/- 14.31**, not acceptance evidence. This does not prove a strength gain and does not establish a true regression.
- The separate A/A operational readiness set had 8 games, W1 D6 L1. It was not pooled with SPRT.

## Original evidence checked
The run's immutable original evidence is preserved at result branch commit [1edc13238c8eb4d55dac9e18da7d900f5357dd41](https://github.com/couns0538-sketch/dwqww/commit/1edc13238c8eb4d55dac9e18da7d900f5357dd41), file `archived-results/tt-refresh-strength-39537333958-1.zip` (64,228,712 bytes; SHA256 `cd4cdf35ab8c32bbb704a474ffaa61594b229c36c7e6b82f3a7452fe078c08d7`).

Independently downloaded the source Actions artifact (SHA256 `811bde927a833df64ffe376edd43b4765560cfccd5993c79f219679b4b1fa98d`), checked its nested original archive SHA256, verified **486/486** original inner manifest payloads and independently **486/486** matching outer Actions-artifact payloads by SHA256. Both ZIP CRC checks passed. Recomputed original PGN WDL/pentanomial/paired FEN, original move-count fields, full outcome state and LLR. Frozen engine and runner binary SHA256 hashes matched their original match summary.

The independently runnable Python auditor and portable approximately 2.4MB checkpoint ZIP with original PGN, original console/state/stats and AA evidence were delivered in the originating ChatGPT run as `forge-6423-strength-1024-independent-audit-20261021.zip`. The original 446MiB UCI log is **not copied into this report**; it is retained in the above immutable 64MiB GitHub result ZIP, with exact source manifest hashes.

## Context and decisions
Forge 6.4.24 `7db08eac6ead99d641834c56ccec06a06600586a` is an isolated SEE bound-reuse candidate. Sol's published branch documents 42 native CTests, 8 active UCI checks, 56 exact comparisons and 13 Wine checks, not independently rerun in this audit. It still lacks accepted calibrated 6.4.23→6.4.24 throughput or equal-time Elo evidence. Accepted integration remains `5101c2529d386b7c3a04ba9156a69ee34df6bb43`.

**Disposition: do not promote Forge 6.4.23 TT refresh on the 0/+10 test and do not interpret the existing successful CI job as an Elo PASS.** Preserve the original source/PGNs/LLR unchanged. Prioritize properly calibrated 6.4.23-vs-6.4.24 equal-settings throughput on a stable host. Chess move legality was not independently replayed, and no Windows/Ryzen native test was performed here.
