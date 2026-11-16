# deepseek6 long 34 — PREDICTION (written before the first extreme-value run)

Item (file 8, long 34): **EXTREME VALUES under ASan + UBSan.** Every spin option of the plain build's `uci` list
set to its minimum, then to its maximum (one option at a time, the rest S14), `go depth 8` on the first 20
positions of O. Per option: sanitizer lines, crash or not, every bestmove legal (python-chess). One planted fault
must be reported.

Model: DeepSeek V4.1 Flash 1017. Time: `stamps.txt`, first line.

## Fixed now

- Build: `-fsanitize=address,undefined -fno-omit-frame-pointer -g -O1`, RelWithDebInfo, plain 6b98f217,
  sha256 `41e592fa…` — the four pins are already met on it (312,866 / 862,329 / 3,024,920 / 4,865,609, zero
  sanitizer lines).
- **61 spin options** in `spin_opts.tsv`, parsed from the build's own `uci` list (name, default, min, max).
  Two runs per option (min, max) = **122 runs**, each `go depth 8` over the first 20 positions of O = 2,440
  searches. `Threads` is forced to 1 in every run (the item says Threads 1) even when the option under test is
  `Threads` itself — that case is then **not a true extreme** and will be marked so, not silently reported.
- `Hash`'s min (1) and max (2048) are both tested; 2048 MB is above this VM's free memory, so that run may be
  killed by the OS — that is a finding, recorded as such, not a crash I attribute to the engine.
- Bestmove legality is checked with python-chess (`pip install chess`); illegal or missing `bestmove` is a row.
- One planted fault: a deliberately invalid option value sent to the plain SANITIZER build (a value outside
  min..max) must be REFUSED by the engine with `invalid value`; and, separately, a planted C++ fault in a copy
  (an out-of-bounds write in the search entry) must be reported by ASan with a nonzero exit.

## Predictions, each with the range that kills it

**P1 — no genuine sanitizer finding.** Prediction: **0 AddressSanitizer errors and 0 UBSan runtime errors** across
all 122 runs, apart from the planted fault. Kill range: any real report → that is the item's headline finding.

**P2 — no crashes.** Prediction: **at most 2 runs** die by signal, and both are `Hash` at 2048 (memory), not an
engine fault. Kill range: 3 or more signal deaths, or a signal death on any option other than `Hash`.

**P3 — every bestmove is legal**, all 2,440 searches. Kill range: any illegal or missing bestmove (a real bug).

**P4 — the extremes that visibly slow the search are the ones that disable a pruning path**: `RfpMargin` max (300),
`RazorBase` max, `FutilityBase` max, `SeeQuietMultiplier` max, `LmrCutoffThreshold` max. I predict those five are
the slowest runs (largest total nodes over the 20 positions), each at least **1.3×** the S14 baseline at depth 8.
Kill range: none of them reaching 1.3×, or a 6th option exceeding all five.

**P5 — the inert options stay inert**: `QsSeeMargin`, `CaptureFutilityMultiplier`, `CaptureFutilityDepth` at both
ends equal the S14 baseline node-for-node (my job 1 found all three inert under S14). Prediction: 6 identity runs.
Kill range: any of the six differing.

**P6 — the whole sweep finishes inside the item's 60-minute budget** with runs in parallel (4 at a time). An
extreme setting can make depth 8 take far longer than the 1–2 s a normal setting needs, so I predict the slowest
single run is under 300 s. Kill range: a run exceeding 900 s gets killed and reported as "timeout", not "clean".

## What would make me report "not done"
A build that fails the pins, a sanitizer finding I cannot attribute, or a sweep that does not finish: then the
report says which options were covered and which were not, with the counts.
