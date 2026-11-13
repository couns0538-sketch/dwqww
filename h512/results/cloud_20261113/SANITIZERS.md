# Sanitizers on the NNUE v3 tests

Date: 2026-11-13. g++ 13.3.0, `-std=c++20 -O1 -g -march=x86-64-v4 -ffp-contract=off -fno-fast-math -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -DFORGE_NNUE_V3=1`. The walk is the same 100000-ply seed as `h512/results/step3/nnue_v3_tests_combo29.log`, plus the far-cache and near-bound checks added with the bias rebuild.

Undefined-behavior sanitizer, `-fsanitize=undefined -fno-sanitize-recover=undefined`:

```
walk total: plies 100000 evaluations 64987 mismatches 0 ... kernel_mismatches 0
far-cache H1024 one bucket: comparisons 20 refreshes 40 columns 592
nnue_v3_tests: 95960 checks, 0 failures
```

Exit status 0. No sanitizer diagnostic.

Address sanitizer and undefined-behavior sanitizer together, `-fsanitize=address,undefined -fno-sanitize-recover=undefined`, same test command under `/tmp/forge-nnue-asan`:

```
nnue_v3_tests: 95960 checks, 0 failures
```

Exit status 0. The four walk lines matched the earlier log, including H128 45000 plies / 29316 evaluations / 0 mismatches. The H1024 output-sum loop in that run uses weights of ±127 and accumulators at the int16 extremes (the existing kernel section, 1200 sums). No report does not extend to the search, to threads above one, or to a real network.
