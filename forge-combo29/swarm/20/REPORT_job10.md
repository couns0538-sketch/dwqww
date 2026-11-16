# REPORT job10 — seat 20, area 10 job 1 (sixth check): seat 28's S-F1

**what was asked** — Reproduce seat 28's S-F1: `go movetime M` stops at M − Move Overhead, so `go movetime 10`
searches ~1 ms and `go movetime 50` ~40.5 ms.

**the answer** — **CONFIRMS**, independently and to within 0.5 ms. Medians (15 runs/cell, monotonic go→bestmove):
10 → 1.72 ms, 50 → 40.94, 100 → 90.82, 200 → 190.77, 500 → 490.80. The gap is a **constant ≈9.2 ms**, not a
fraction, and vanishes with `setoption name Move Overhead value 0` (10.72 / 51.06 / 101.17 / 200.78 / 500.88). An
overhead sweep on `go movetime 100` is exactly linear: overhead 0/5/10/25/50 → 100.92/95.88/90.85/75.78/50.75 ms.

**how sure** — certain: the effect is 100× the run-to-run spread (max−min under 1 ms in every cell).

## Honesty numbers
`/agent/repos/build-base/forge` sha256 `e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83`, pins
4/4 (`../HONESTY.txt`). 4-core machine (nproc 4) — stated because a timing result is machine-specific. No sanitizer
claim in this job, so the planted-fault proof is not involved.

## Step table
| step | done-partly-not done | evidence file | result |
|---|---|---|---|
| prediction, alone | done | `PREDICTION.txt` | 5 predictions, all held |
| movetime sweep with default overhead | done | `out_check.txt` | constant −9.2 ms |
| same with `Move Overhead 0` | done | `out_check.txt` | ≈ +0.9 ms after the request |
| overhead sweep 0/5/10/25/50 | done | `out_check.txt` | exactly linear |
| source read | done | `CHECK_s28F1.md` | `max(1, movetime - overhead)` |

## Findings
1. **S-C7 = CONFIRMS seat 28's S-F1.** Show it again: `python3 check_s28f1.py <exe> <outdir>`
2. **S-F15: the measurement hazard** — two engines compared at "the same movetime" without pinning Move Overhead
   are compared at different think times; the gap is constant, so any fixed-time comparison inherits it.

### Suspicions, not proven
- That subtracting Move Overhead from an explicit `movetime` is the wrong place for the allowance (it belongs to
  clock play). A design question for the PC; I measured the behaviour, not the intent.

## What I did NOT do
- `go movetime 1` (the `max(1, …)` guard).
- Threads > 1 / large Hash (both change dispatch cost).
- The Windows build.

## What I am NOT sure about
- Whether the ≈+0.9 ms at overhead 0 is dispatch or timer granularity.

## Times: see `stamps.txt`
## The last command's output
```
$ ls forge-combo29/swarm/20/job10/
CHECK_s28F1.md  PREDICTION.txt  check_s28f1.json  check_s28f1.py  out_check.txt  stamps.txt
```
