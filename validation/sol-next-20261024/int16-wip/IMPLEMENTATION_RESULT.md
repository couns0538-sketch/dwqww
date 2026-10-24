# H256 runtime integer inference: verified numerical checkpoint

Checkpoint recorded at15:52UTC. Subsequent clocked evidence is recorded separately in `RESPONSIVENESS_OBSERVATIONS.md`: the first same-binary full WAC trial failed/incomplete at a watchdog, and its bounded three-case diagnostic did not reproduce the delay. Those later observations do not change the numerical results below.

Actual source equals the frozen scratch implementation; root's Release engine SHA256 is `61f3753f8f66ec5b9ee2d43d0f3156b3bc1fedf32fc7da46582354a04c49e509`. The all-OFF d11 precondition passed at308972 in `../int16-release-off-qa/precondition-d11/RESULT.json` before the tool ran. Root owns all production/index/publication changes.

The actual candidate core (`build-int16-release/libforge_core.a`, SHA256 `118fd17d5a84c29b71677eb3cabf6c8dd62a6477962020fc4686febd2bc9c430`) was linked with the original parity driver using the root core's H256/strict-FP/znver5 settings. CPU2 was exclusive to the compile/run for numerical correctness. Both actual exits were0; compiler and runtime stderr were empty. The run closed at2026-10-24T15:49:54.978523Z. These elapsed times are not an NPS result.

| Measured quantity | Result |
| --- | ---: |
| Unique four-field FENs | 100,000 |
| Mean absolute integer-cp difference | 0.0147 |
| Maximum / p99 difference | 1 / 1 cp |
| Nonzero differences | 1,470 |
| Raw-net / full-static strict sign flips | 0 / 0 |
| Raw-net / full-static zero-vs-nonzero | 13 / 3 |
| Full state checks / transitions | 101,504 / 101,295 |
| Fresh / incremental lane mismatches | 0 / 0 |
| Independent int64 output-oracle mismatches | 0 |
| Tag / parent / in-place mismatches | 0 / 0 / 0 |
| Castles / EP / quiet promotions / capture promotions / nulls | 42 / 12 / 822 / 87 / 12 |
| Observed integer lane min / max | -73,948 / 16,714 |

**PASS against fixed mean<=2cp and max<=30cp gates, with all state/oracle/coverage gates passed.** The int32 lane decision is also supported by the observed minimum below int16 range. Native AVX2 integer arithmetic was compared to an independent scalar int64 output oracle; a separately compiled scalar-fallback engine has not been run by this agent.

Original stdout, stderr, exact compile/run argv, source/core/engine/tool hashes and actual exits are retained under `parity-100k/`. The exact100,000-FEN stream is `parity-100k/corpus.fen`, SHA256 `e8a35483ced1a41e607fc5c277cdd800449eea1d55833de38ab10c216af7b842`; seed20261024. This is a deterministic correctness corpus from legal walks/special fixtures, not a playing-strength sample.

The separate buffer-only WAC run completed900positions cleanly at15:46:08Z: lock276/300, buffer265/300, lock279/300; all legal, watchdogs satisfied, three engine exits0 and no stderr. This timed tactical result is retained honestly; the lower middle count is unresolved between candidate timing effects and shared-host variation. It is not an Elo result.

At this numerical checkpoint, the int16 WAC run had not started. Later runs and their authorization are recorded separately; the original failed trial remains failed and unpooled. Root still owns the full bench/perft/CTest/sanitizer/FMA/SIMD/search-bestmove/tactical/performance evidence, invalid-representability fallback exercise, final cumulative `-p1` patch againstf4911f2, source ZIP and CR handoff. The added2048bytes per accumulator (~272KiB per worker) remains an explicit memory/performance tradeoff even OFF. No speed, Elo or candidate-acceptance claim is made here.
