# PREDICTION — committed alone, before the first profiling command (file 7, Step 1)

Seat 20. Binary `build-v3/forge` sha256 `227aae56ef1678479cf08d0fc3e3c73683753e89d61f12b252f0fec9e388471e`
(`Chess Engine Forge 6.4.24 candidate`), `-DFORGE_MATE_ALPHA_GUARD=1 -DFORGE_NNUE_V3=1`, kernel `avx512`.
Regime: PC20 (S14 17 options + 5 extras), test net loaded (`NNUEArchFile` then `NNUEArch true`), Threads 1, Hash 16.
Workload: `bench 13` = 3 652 372 nodes (Step 0 pin, matched).

## What I predict is hottest, and the range that kills it

| # | quantity | predicted | KILLED if outside |
|---|---|---|---|
| P1 | the single hottest `nnue::v3` function, by self time | `apply_changes_avx512` (the incremental accumulator update; counting `apply_changes_pair_avx512` with it) | any other function is the top | 
| P2 | that function's share of **v3 time** | **45 %** (range 30–60 %) | < 25 % or > 65 % |
| P3 | the whole v3 path (`static_evaluate_v3` inclusive) as a share of **bench 13 time** | **30 %** (range 20–45 %) | < 15 % or > 55 % |
| P4 | `output_sum_avx512` + the forward pass, share of v3 time | **20 %** (range 12–30 %) | < 8 % or > 38 % |
| P5 | `refresh_perspective` (full refresh, not incremental), share of v3 time | **10 %** (range 4–20 %) | < 2 % or > 28 % |
| P6 | `make_valid` + `collect_changes` bookkeeping, share of v3 time | **10 %** (range 5–18 %) | < 3 % or > 25 % |

## Why (stated so it can be wrong in a specific way)
The accumulator does 512 `int16` lane-adds per changed feature per perspective — ~2 KB of traffic per move made, on
every node whose parent is valid. The forward pass is 1024 `int16` MACs plus a horizontal reduce, on every eval. The
first should therefore be roughly 2× the second, and together they should dominate everything that is not the
incremental update itself. A full `refresh_perspective` cost is 768 features, i.e. ~400× one incremental column, so
it must be **rare** — if P5 lands above 28 % the lazy-rebuild strategy in `make_valid` is failing far more often
than the piece-diff design intends, and that is a finding in its own right.

## The instrument, declared in advance
`perf` is **not on this machine** (`command -v perf` fails; no `/usr/bin/perf*`). Step 1 will therefore use
**`gprof`** (`-pg` build) for the function shares, and say so. A `-pg` build adds a call-counting prologue to every
function, which **inflates small, frequently-called functions** and therefore distorts P1 and P2 in a known
direction: `collect_changes` and `make_valid` will read high, and the big vector kernels comparatively low. If the
top slot is a small function, I will not report P1 as refuted without a second instrument; I will report the
distortion explicitly. **`bench 13` wall-clock on the normal `-O3` build remains the measurement**; the profile only
proposes where to look, and Step 3 timing is what decides.

## Not predicted, deliberately
No claim about a *speed patch* yet: whether any patch exists is what Step 2 is for, and predicting a win size before
knowing the hot loop's shape would be a guess dressed as a forecast.
