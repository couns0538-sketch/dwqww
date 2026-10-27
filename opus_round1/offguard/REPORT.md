# offguard — OFF-path cost of the new default-OFF options on a quiet runner (A1 HistRework, S-A2 NnueInt16, S41 NetScale) — DONE (advisory)

**Branch.** `opus-offguard` = `d4f4312` + `0d99f02` cherry-picked (`9c5aaf46`) + `9e96c23a` (workflow, script, README)
+ this evidence commit. Measurement only: no engine change on this branch; the three engines are built from their own
branch commits, pinned in `ci_offguard.sh`. Main session's own follow-up (not a queue item); machine exclusive: no.

**Why.** All three options are default OFF and bench-identical to the AL1 lock with the option off, but their OFF
builds are not the lock binary, and their NPS was measured only on the loaded PC (A1: not at all). This job measures
the OFF builds against the lock on a quiet GitHub runner, the way S29 and S-IT were measured.

## Setup
- Workflow `opus-offguard-ci`, run 40520714508 on `9e96c23a`, success (job 14:23:57Z-14:45:43Z); logs in
  `logs/ci_40520714508/`.
- Runner: ubuntu-24.04, Intel Xeon Platinum 8370C @ 2.80 GHz. g++-14, CMake Release, Ninja, the box flags
  (`-march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256`). Every build log shows
  the same 6 known `-Wconversion` warnings as the lock.
- Builds (`builds.log`): lock `294dbed3` (sha256 `6635d4d1…`, the same binary as the S49 Linux box lock build), A1
  `a8b63aae` (`da73c5e6…`), S-A2 `d2301c51` (`6becec13…`), S41 `5a197863` (`171c7560…`).
- NPS: `nps_ab.py` (from opus-sol-S29): ABBA order, fresh process per run, 10 runs per side, bench d16 and d20, nodes
  must match (they did in every run). A = lock, B = the option's OFF build.

## Results
| option (OFF build) | identity, option off | d16 CPU NPS B/A (95% CI of the difference) | d20 CPU NPS B/A (95% CI) | reading |
|---|---|---|---|---|
| A1 `HistRework` | ALL OK (bench d11-d22, perft5, kiwipete) | 0.9919: −0.81% (−1.35 .. −0.27) | 0.9902: −0.98% (−1.22 .. −0.73) | **small real cost**: both CIs exclude 0 |
| S-A2 `NnueInt16` | ALL OK | 0.9960: −0.40% (−0.61 .. −0.19) | 0.9954: −0.46% (−0.62 .. −0.30) | **small real cost**: both CIs exclude 0 |
| S41 `NetScale` | ALL OK | 0.9984: −0.16% (−0.46 .. +0.15) | 0.9988: −0.12% (−0.35 .. +0.10) | no measurable cost |

Wall-clock NPS gives the same picture (A1 −0.82% / −0.98%, S-A2 −0.42% / −0.46%, S41 −0.11% / −0.13%;
`nps_lock_vs_*.log`). The A1 d16 lock arm has one slow run (1,262,149 CPU NPS, run 19); the d20 result does not depend
on it.

**Hot-function sizes** (`nm -S`, bytes; `hot_function_sizes.log`):

| function | lock | A1 | S-A2 | S41 |
|---|---|---|---|---|
| `Worker::search` (recursive) | 12,737 | 13,337 (+600) | 12,737 | 12,737 |
| `Worker::qsearch` | 4,233 | 4,812 (+579) | 4,233 | 4,233 |
| `Worker::static_evaluate` | 625 | 641 (+16) | 625 | 779 (+154) |
| `nnue::update` | 2,266 | 2,266 | 2,342 (+76) | 2,266 |
| `nnue::refresh` | 589 | 589 | 691 (+102) | 589 |
| `nnue::evaluate` | 431 | 431 | 447 (+16) | 431 |

## Findings
- **A1 HistRework costs about 1% NPS with the option off.** Its OFF path runs the extra mode checks in search and
  qsearch (both grew by about 600 bytes), and every thread carries the table of about 200 KiB even when OFF. Which of
  the two costs more was not isolated. This matters only if A1 is merged with the option off by default. The gate plan
  tests HistRework=2 against the lock; any measured gain there must cover this 1% when it is switched on. A
  compile-time switch (as S13 did with `FORGE_S13_TT_CHILD_PREFETCH`) would make the default build the lock binary.
- **S-A2 NnueInt16 costs about 0.4-0.5% with the option off.** The accumulator stack entries double (2 → 4 KiB) and the
  NNUE kernels grew slightly. The S-A2 report's PC figure (−1.1% / −1.2%, CIs −7.5 .. +5.2 / −3.8 .. +1.5, "within
  noise") is now resolved: the cost is real but smaller.
- **S41 NetScale has no measurable OFF cost.** It adds one branch in `static_evaluate`; the CIs include 0 at both
  depths.
- All three OFF builds stay bench-identical to the lock (the rule "OFF = lock nodes" holds); this job is only about
  speed. No Elo claim; NPS figures are advisory.

## Left / UNVERIFIED
- The A1 OFF cost is not split into its parts (branches vs per-thread table vs layout).
- One runner and one run per option. The CIs are tight (10 ABBA runs per side), but a second run would confirm the
  0.4% S-A2 figure.
- Option-ON speed is not measured here; it is in the S-A2 and S-C4 reports (PC, advisory).

## Files
- `README.md` (what and why), `ci_offguard.sh` (CI driver), `nps_ab.py` (copy from opus-sol-S29), `IDEA_SOURCE.md`,
  `REPORT.md`, `FILES.txt`, `SHA256SUMS`.
- `logs/ci_40520714508/`: builds, configure/build logs, identity per option, hot-function sizes, NPS A/B per option.
- `.github/workflows/opus-offguard-ci.yml`.
