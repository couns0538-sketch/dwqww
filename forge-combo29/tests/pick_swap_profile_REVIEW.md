# First-four selection self-swap frequency

**Observed frequency only. No speed inference, production change, or optimizer implementation.**

A source-only immutable-lock snapshot (`16833ec`) was instrumented immediately before `std::swap(moves_[index_], moves_[best])` in `MovePicker::pick_best`, `src/search.cpp:642–656`. Only the first four selection scans per list are counted. This is not the count of every `MovePicker::next` entry, later sorted-list returns, or all swaps in the engine.

The original swap still executes unchanged. Counters record selections and `best == index_` outcomes by ordinal 1–4; distinct swaps are their difference. The counter build is single-threaded and is not safe for multithreaded profiling. No `-pg` instrumentation or candidate timing was used.

## Results

All four runs matched the byte-verified uninstrumented lock's node count exactly:

| Mode/depth | Nodes | First-four selections | Self-swaps | Distinct swaps | Self-swap fraction |
|---|---:|---:|---:|---:|---:|
| NNUE on, 16 | 3,024,920 | 3,097,163 | 1,196,960 | 1,900,203 | 38.65% |
| NNUE on, 18 | 6,066,072 | 6,224,536 | 2,440,266 | 3,784,270 | 39.20% |
| NNUE off, 16 | 2,448,617 | 2,670,724 | 1,037,781 | 1,632,943 | 38.86% |
| NNUE off, 18 | 6,134,776 | 5,972,392 | 2,241,622 | 3,730,770 | 37.53% |

Self-swap fractions by selection ordinal:

| Mode/depth | First | Second | Third | Fourth |
|---|---:|---:|---:|---:|
| NNUE on, 16 | 40.29% | 38.35% | 38.40% | 34.00% |
| NNUE on, 18 | 41.01% | 39.10% | 38.63% | 33.87% |
| NNUE off, 16 | 39.99% | 38.87% | 39.54% | 33.70% |
| NNUE off, 18 | 40.18% | 37.23% | 36.08% | 30.84% |

Exact per-ordinal selection/self/distinct counts are preserved in `pick_swap_profile_results.json`. Their identities (`self + distinct == selections`) were checked. The reference executable hash remained `1371770e2ad61aa2fe3c038acc7da3912da5d64c9cb1dcc5e4668221fb3226f6`.

## Interpretation and limits

Self-swaps are common in this workload, so a guard is a concrete candidate for further investigation rather than a hypothetical rare-case optimization. **This does not show that a guard saves time.** It adds a branch; current optimized code may already eliminate some no-op operations; self-aliasing loads/stores may be cheap; and instrumentation changes code generation. A source-level self-swap count is not a count of avoidable machine instructions or memory writes.

The counts include selections with only one remaining entry as well as winners already at the front after a nonempty scan. Those subcases were not separately counted. Any proposed guard must preserve exact move order, equal-score behavior and search signatures, then be validated separately without the counters. No guarded prototype or production edit was made in this follow-up. No performance claim is made from engine-reported times retained in raw receipts.

## Reproduction and provenance

The recipe explicitly archives only `forge-combo29/src` and `forge-combo29/include`, verifies all 20 original blobs, then applies the committed profiling-only diff in the scratch snapshot. No Windows executable, bundle or unrelated input is requested.

```sh
python3 forge-combo29/tests/pick_swap_profile_run.py \
  --output /workspace/shared/forge-build/pick-swap-profile-reproduction \
  --baseline /workspace/shared/forge-build/final-lock-identity-fixed/lock
```

Requires GCC 14 and x86-64-v4 support. Compilation retains the locked strict-FP/O3/ISA flags. The supplied baseline must match the expected lock hash; otherwise the script stops. Full compiler command, source blob IDs, instrumentation hash and binary hashes are in the result receipt.

- `pick_swap_profile_run.py`: bounded source-only reproduction.
- `pick_swap_profile_instrumentation.patch`: exact scratch-source instrumentation, not a production patch.
- `pick_swap_profile_results.json`: counts, fractions, node signatures and provenance.
- `pick_swap_profile_raw.json`: original engine stdout/stderr for all reference and instrumented processes.

Candidate status remains **UNPROVEN**; these data justify examining a possible guard, not accepting one.
