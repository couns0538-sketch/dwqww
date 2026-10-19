# Quiescence stalemate audit

Date: 2026-10-19 18:00 CEST. Base: 9108d012.

Root FEN: 7k/8/5K2/6Q1/8/8/8/8 w - - 0 1. White g5g6 stalemates black; score must be zero.

`src/search.cpp` does not check stalemate in `Worker::qsearch`: non-check leaf scores with stand-pat static evaluation. Use the two Python regression scripts in this audit branch. Local geometric oracle passed. Mock UCI success/failure checks passed. Actual Forge execution was not possible because local GitHub clone failed DNS. This is source-confirmed but not runtime-confirmed.

Next: tester run UCI regression on baseline, save raw logs; researcher design efficient qsearch check; developer validate isolated repair. Previous SMP TT race is a distinct finding.
