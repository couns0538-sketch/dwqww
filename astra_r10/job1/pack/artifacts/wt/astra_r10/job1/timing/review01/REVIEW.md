# Independent R10 timing review — UNPROVEN

PASS: original records and statistics agree.

| Population | Blocks | Median % | Q1 % | Q3 % | IQR pp | Min % | Max % |
|---|---:|---:|---:|---:|---:|---:|---:|
| eligible | 10 | 0.361084244 | -0.473842477 | 0.624682811 | 1.098525288 | -1.467115093 | 1.411393858 |
| all_complete | 39 | -1.173411000 | -4.421909460 | 0.716114567 | 5.138024026 | -24.280917443 | 8.671963021 |

The preregistered IQR gate fails; the other calibration gates pass. No candidate ABBA was run. 2273 checks PASS of 2273. All 156 transcript hashes, 312 warmup/timed node pins, block/arm identities and telemetry-based eligibility were checked.

Protocol SHA256 `c83ccb17d428069be129eaf4f1b253dbf299bb6d77ad0353a5667fa82ccb3245`; preregistration commit `bd9f81a77416a68c1b59a7ba87acd4e383c10c03`.

Limitations:

- Raw process CPU-time and per-CPU before/after counters are not retained; eligibility is independently recomputed from recorded derived telemetry, not raw counter deltas.
- Current remote ancestry confirms publication of the prereg commit, and commit time precedes execution. No separate immutable push-time receipt was found; publication-before-start relies additionally on the main agent publication log/history.
- Loaded-host rejection and A/A calibration failure preclude any candidate speed inference; zero candidate ABBA blocks were run.
