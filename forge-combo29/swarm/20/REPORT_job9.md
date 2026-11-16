# REPORT job9 — seat 20, area 10 job 1 (fifth check): seat 06's S-F1

**what was asked** — Reproduce an unconfirmed NEW finding: seat 06's S-F1, that `eval` is exactly
colour-symmetric (0 differences in hce/nnue/total).

**the answer** — **CONFIRMS.** 120 positions x 3 configurations = 360 pairs, **0 asymmetric, max absolute
difference 0 in hce, nnue and total**, with two controls proving the harness can see a change. But the check only
means something after a convention correction: `eval` is side-to-move relative, so a colour mirror must read the
SAME number, not its negation. My first script asserted negation and "found" 120 asymmetries — all my error, kept
on record as `out_check_WRONG_convention.txt` and reported as finding S-F14.

**how sure** — certain about the numbers (deterministic `eval` calls, every pair committed as JSON); the claim
"exactly symmetric" is supported on 360 pairs, not proved for every position, and I say so.

## Honesty numbers
`/agent/repos/build-base/forge` sha256 `e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83`,
4/4 pins (`../HONESTY.txt`). `eval` is a static, deterministic command: no search, no timing, no sanitizer claim
made here, so no planted-fault proof is involved in this job's numbers.

## Step table
| step | done-partly-not done | evidence file | result |
|---|---|---|---|
| prediction, alone | done | `PREDICTION.txt` (commit before any run) | 5 predictions |
| convention probe FIRST | done | `convention.txt` | eval is side-to-move relative; mirror must be EQUAL |
| first run (wrong convention) | done, kept | `out_check_WRONG_convention.txt` | 120 false asymmetries — my error |
| corrected run, 60 own positions | done | `check_s06f1b.json` | 0 asymmetries |
| corrected run, +60 O positions, 3 configs | done | `out_symmetry.txt` | 360/360 symmetric |
| controls | done | `out_symmetry.txt` controls | same twice equal; different position differs |

## Findings
1. **S-C6 = CONFIRMS seat 06's S-F1.** Show it again:
   `python3 check_s06f1b.py /agent/repos/build-base/forge /tmp/o O_first60.fens`
2. **S-F14: the sign convention trap.** `4k3/8/8/8/8/8/8/QQQQK3 w` -> hce 4211; `qqqqk3/8/8/8/8/8/8/4K3 b` ->
   hce 4211; the same board with black to move -> hce −4182. Any checker negating the mirror invents a fault.
3. The symmetry holds in all three configurations, including `DeadMaterial true`, so it is not an artifact of the
   net being switched off.

### Suspicions, not proven
- Whether the equality survives a position where one side is in check (vacuous for a true mirror, but I did not
  construct the case deliberately).

## What I did NOT do
- I did not reproduce seat 06's exact position set (8,103 pairs) or their fourth configuration ("dead-material set"
  position list); I used my own 60 + 60 from O with `DeadMaterial true` over them.
- I did not stratify by in-check status.
- I did not test the left-right axis here (seat 06's S-F3/S-F4 — a different finding, and their own).

## What I am NOT sure about
- Whether "exactly symmetric" holds for every possible position. 360 pairs with a zero maximum is strong, but it
  is a sample.

## Times: see `stamps.txt`
## The last command's output
```
$ ls forge-combo29/swarm/20/job9/
CHECK_s06F1.md  PREDICTION.txt  O_first60.fens  check_s06f1b.json  check_s06f1b.py
convention.txt  out_check_WRONG_convention.txt  out_symmetry.txt  stamps.txt
```
