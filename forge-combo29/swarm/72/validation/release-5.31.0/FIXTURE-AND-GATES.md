# 5.31.0 depth-9 LMR regression

Immediate frozen baseline ZIP SHA-256: fd2f0d249b78bc353bc3a439464be0c4aec7a01eb1664f2c923f985aef74d0d7

Fixture: `rn1qkb1r/p1p1ppp1/1p1pbn2/7p/3P4/2N1PN2/PPP1BPPP/R1BQK2R w KQkq - 0 1`

Direct interior depth 9, parent null pruning disabled, fresh TT/searcher per call:
- [52,53]: unchanged 5.30=52; full-nominal-depth=no-LMR 53; corrected 5.31=53.
- [53,54]: unchanged 5.30=53; full-nominal-depth=no-LMR 54; corrected 5.31=54.
- [54,55]: unchanged 5.30=54; full-nominal-depth=no-LMR 55; corrected 5.31=55.
- Depth-9 full-window baseline +57, no-LMR +62; this is a differential diagnostic rather than Elo evidence.
- Direct tests assert boundary windows [53,54] and [54,55] plus board/FEN/key/history immutability.
- Baseline with injected tests fails exactly these two assertions; candidate passes.

Strict GCC 14.2, Clang 17, Clang ASan+UBSan: engine, match-tool, UCI, ponder CTest 4/4 each.
Extended UCI + all three perfts each passed 30 validations under GCC/Clang/sanitizers.
Benchmark: seven CPU0 interleaved baseline/candidate pairs, summaries in BENCHMARKS.csv.
Windows: cross-compilation from frozen source with -O3/ThinLTO/znver4 static runtime;
PE verified only, not Windows/Wine/physical Ryzen tested.
