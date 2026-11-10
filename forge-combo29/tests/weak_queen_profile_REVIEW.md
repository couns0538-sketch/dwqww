# WeakQueen child-CPU/wall diagnostic

**Exploratory shared-cloud data only. Native speed and Elo remain UNPROVEN.**
The candidate remains default off. This is not a native acceptance test.

## Fixed protocol

After exact isolated correctness gates, the parent coordinated a quiet window
with other workers idle. The driver was frozen in `38c8f68` before execution.
The tested production source remains `9b67829c86c0ddadcb8334fe92147ffa4a895ced`.

- Depth 18; Threads 1; OwnBook false; bench's Hash 16 MB.
- NNUE on, then off. Four balanced blocks per mode in fixed order:
  ABBA, BAAB, ABBA, BAAB, where A = baseline and B = isolated candidate.
- Fresh engine process for every run. One baseline and candidate warmup per
  mode, excluded from summaries. Exactly 32 measured runs and four warmups.
- Linux process affinity pinned to allowed CPU 0 on an AMD EPYC 9V74. CPU
  affinity is not host reservation or isolation.
- `resource.getrusage(RUSAGE_CHILDREN)` is sampled immediately before and
  after each `subprocess.run`; only that engine child runs in the interval.
  User-time, system-time, and their sum are preserved separately. Wall time
  uses `perf_counter_ns`. Both metrics include process creation/init/exit.
- Binaries are checked against the saved 256-comparison evidence before and
  after the run. Every bench node count must match its baseline warmup.
- Orders and sample count are saved before the first run. There was no
  adaptive stopping, dropped sample, rerun, or post-hoc sample selection.

## Results

All 36 processes exited successfully with empty stderr and unchanged binary
hashes. Exact nodes were 6,066,072 with NNUE on and 6,134,776 with NNUE off.

Below, each block ratio is candidate mean duration / baseline mean duration.
Ratios below 1 mean less duration within that block, not a release claim.

| Mode | Metric | Four block ratios | Median block ratio |
|---|---|---|---:|
| NNUE on | Child CPU | 0.978821, 0.984769, 0.990902, 0.995265 | 0.987836 |
| NNUE on | Wall | 0.978805, 0.984735, 0.990898, 0.995269 | 0.987816 |
| NNUE off | Child CPU | 1.016664, 0.998546, 0.963194, 0.990700 | 0.994623 |
| NNUE off | Wall | 1.016629, 0.998370, 0.963196, 0.990706 | 0.994538 |

CPU and wall ratios agree closely in this window, so descheduling does not
explain most of the observed spread. That does not eliminate CPU frequency,
cache interference, thermal/power state, or other shared-host noise. The
NNUE-on block ratios drift toward 1. The NNUE-off set includes one regression
block and has a wider range. Four blocks on one fixed eight-position bench
do not justify a precise general speed estimate, confidence interval, or
native performance decision.

Decision: retain this small, exact, default-off candidate for a native test.
The diagnostic is mildly encouraging but not acceptance evidence. No Elo
claim is made, and Windows/clang PGO behavior has not been measured.

## Evidence and reproduction

`weak_queen_profile_results.json` preserves the predeclared protocol, all
36 raw stdout/stderr records, timestamps, resource deltas, wall times, load,
node signatures, binary hashes, script hash and summary calculations.
`weak_queen_profile.log` preserves the driver's complete stdout.

```
python3 -B forge-combo29/tests/weak_queen_profile.py \
  --evidence forge-combo29/tests/weak_queen_equivalence.json \
  --output /tmp/weak-queen-new-profile.json --depth 18 --cycles 4
```

The output must not already exist. The exact validated engine paths in the
evidence file must exist and match their hashes; rebuild them with
`weak_queen_check.py` if needed and use its new equivalence manifest. A fresh
run would be a separate diagnostic, not a continuation of this fixed sample.
