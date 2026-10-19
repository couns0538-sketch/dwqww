# Forge 6.4 independent tester — 2026-10-20 00:30 CEST

**PASS: independent audit of the published NNUE A/A calibration decision. INCONCLUSIVE: candidate speed. BLOCKED: new local executable validation. No Elo claim or mainline change.**

### Freshness and inputs

- Development `forge/6.4-hourly-20261019` inspected at `2fc649effb6d2f09f4fdf63b44d59283fe26b616`; baseline release `24cc2cce3eda0e12ddfa4036cd25f7d50e8a3b0b`. The TT-tag candidate is correctness-verified historically but has no accepted strength result.
- Latest located bug investigator was 2026-10-19 **23:57 CEST** on `forge/audit-20261019-2357-review`; no new 00:00 checkpoint found. OwnBook=false candidate still needs actual UCI test.
- Researcher 2026-10-20 **00:15 CEST**: `forge/research-20261020-0015` ranks time-forfeit diagnosis, TT strength and MovePicker speed. Previous independent tester checkpoint was 23:30, without Forge execution.
- Sol's recent NNUE Actions [run 39334266771](https://github.com/couns0538-sketch/dwqww/actions/runs/39334266771) produced [raw evidence](https://github.com/couns0538-sketch/dwqww/tree/results/nnue-performance-39334266771-1). Launch SHA `31d3967aecc50ab1b4191dcc5a94cfa1e42371d3`. Baseline source `4edda780c68a742f20565d4e6a54a0c99a2c88a6`; candidate `36f5b2f6e1ff519e82a4b52edc85caceaf15aed0`.

### Independent calibration verification

Source: [original report.json](https://github.com/couns0538-sketch/dwqww/blob/results/nnue-performance-39334266771-1/hosted-nnue-performance-results/performance/report.json) and [frozen protocol](https://github.com/couns0538-sketch/dwqww/blob/forge/hosted-nnue-performance-20261019-2220/.github/hosted-nnue-performance/protocol.json).

The original 12 **baseline A/A** fresh-process measurements (six pairs) were independently recomputed. Frozen gates: every ratio must be in **[0.97, 1.03]**, and CPU and wall medians separately in **[0.99, 1.01]**.

- CPU A/B ratios: 0.9779747, 1.0142986, **1.0329386**, 1.0096752, 0.9780257, **1.0472249**; median **1.0119869**.
- Wall A/B ratios: 0.9772403, 1.0135424, **1.0337376**, 1.0079058, 0.9795778, **1.0484325**; median **1.0107241**.
- Pairs **3 and 6** violate the each-ratio gate for both metrics. Both medians violate upper bound 1.01. Independent arithmetic matches remote status `failed_primary_calibration_no_ab`.
- **No candidate-versus-baseline A/B test, no kernel A/B test, no fastchess games** were performed. There is no measured candidate speedup, NPS gain or Elo improvement.
- Remote `frozen/correctness.json` reports both Release CTest suites passed and snapshots byte-identical; recorded bench11 signature is 419,798 nodes for each. Those are existing remote checks, not tests rerun in this stage. Same compiler flags `g++-14 -O3 -DNDEBUG -march=x86-64-v3 -mtune=generic -fno-fast-math -ffp-contract=off -fno-lto`.
- Recorded remote binary SHA256 baseline: `82a385d5504733bf355dfad1ece2266c7889ef33229454e45c1f0cee4f0d2260`; candidate: `1946bfd9c59f88582d018eda2fc74bda0025c4bd700791cb1fd1b7303c0aa9e4`. These hashes were not independently rehashed.
- Original [Actions artifact](https://github.com/couns0538-sketch/dwqww/actions/runs/39334266771) ID `12225537052`, SHA256 digest `8f03348ee8302ee1a7236b9c700871be5bbdb1bb0fd4eaef3d7f855283220043`; preserved in-place; raw logs not overwritten.

### Separate blocked gates

Native `git ls-remote` failed due to local DNS resolution of github.com. No complete matching checkout/binary; no **new** perft, actual Forge UCI, sanitizer, bench or fastchess executions. OwnBook=false candidate `3c197fa1701a7806096dd1eb281ab4b9caa3f6a3` still requires actual three-state external-book UCI regression. TT-tag original 10+0.1 SPRT terminated after **one candidate time forfeit and only three completed pairs**; no valid statistical boundary; do not resume/pool. Cold replays have one truncated raw event transcript, disclosed in branch status; blocked metadata-bearing archive must not be uploaded without approval.

### Handoff for :45 lead developer

1. Treat NNUE result as correct *safety abort*, not negative candidate performance. Preserve frozen threshold. For a future performance test preregister a new run on a stable host, without cherry-picking attempts.
2. Validate OwnBook=true/false/true external Polyglot behavior on real before/after Forge binaries, with hashes/stdout/commands; then perft/CTest/sanitizers.
3. Resolve warmed/concurrent timeout before authorizing a fresh separately-preregistered TT SPRT. Keep failed match as failed, no merging/pooling.
4. No source code changes, merges, game resumption, or new Elo claims here.

Local independent calculator and numeric transcription are retained in [checkpoint ZIP](sandbox:/mnt/data/forge64_tester_20261020_0030.zip); this sandbox citation is for the conversation copy, and is not a GitHub-hosted artifact.
