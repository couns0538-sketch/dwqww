# REPORT_check_20F14 — CONFIRMS seat 20's S-F14 (area 10), seat 16

**What was asked:** check seat 20's S-F14, a convention claim that touches my own area: "`eval` is
SIDE-TO-MOVE relative, so a colour mirror must read the SAME number, not the negation —
`4k3/8/8/8/8/8/8/QQQQK3 w` reads hce 4211 and the mirrored `qqqqk3/.../4K3 b` also reads 4211, while the same
board with black to move reads -4182."

**The answer:** CONFIRMED, digit for digit.

```
4k3/8/8/8/8/8/8/QQQQK3 w   ->  hce 4211  nnue 228  total 4439
qqqqk3/8/8/8/8/8/8/4K3 b   ->  hce 4211  nnue 228  total 4439     (the colour mirror: SAME)
4k3/8/8/8/8/8/8/QQQQK3 b   ->  hce -4182 nnue 662  total -3520    (same board, other side to move)
qqqqk3/8/8/8/8/8/8/4K3 w   ->  hce -4182 nnue 662  total -3520
```

A negation-based checker would report a **8422 cp** "difference" per position. That is the trap.

**How sure:** high. All three of the finding's numbers reproduce exactly on my own build, and python-chess
confirms that the second FEN is the colour mirror of the first.

**What this means for MY job 1:** it was correct. Job 1 required the mirror to read the SAME number, which is
exactly what S-F14 says is right; that is why it returned 0 differences instead of 853. If I had written the
negation comparison, my job 1 would have reported 853 false asymmetries. Worth saying plainly, because a
reader could otherwise take S-F14 as a correction of my work when it is a confirmation of it.

## Honesty numbers

```
exe     /home/ubuntu/builds/bld-release/forge
sha256  e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83
bench 11 312866  bench 13 862329  bench 16 3024920  go perft 5 4865609   (all equal)
```

## Table

| step | done-partly-not done | evidence file | result |
|---|---|---|---|
| the finding's board, white to move | done | `raw_check.txt` | hce 4211 nnue 228 total 4439 |
| its colour mirror, black to move | done | `raw_check.txt` | identical: hce 4211 nnue 228 total 4439 |
| same board, black to move | done | `raw_check.txt` | hce −4182 nnue 662 total −3520 |
| the mirror with white to move | done | `raw_check.txt` | hce −4182 nnue 662 total −3520 |
| is the second FEN really the colour mirror (python-chess) | done | `raw_check.txt` | True |
| a negation checker's false verdict, quantified | done | `raw_check.txt` | 8422 cp "difference" per position |
| check my own job 1 against this convention | done | `../REPORT_job1.md`, `../job1/raw/G.tsv` | my job 1 already required EQUALITY → unaffected |

## Findings

`S-C5 | CONFIRMS S-F14 | check_20F14/raw_check.txt (again: `python3 check_20F14/conv_check.py ~/builds/bld-release/forge /tmp/o.txt`) | eval is side-to-move relative: the colour mirror of `4k3/.../QQQQK3 w` reads the SAME hce 4211 nnue 228 total 4439, while the same board with black to move reads hce -4182 nnue 662 total -3520; a negation-based symmetry checker would report a false 8422 cp difference per position, and my job 1 did not fall into it (it required equality) |`

## Suspicions, not proven

- Whether any seat in the swarm has actually published a negation-based symmetry result. I only checked my
  own job 1; auditing other seats' symmetry harnesses is not this seat's job.

## What I did NOT do

- Did not read seat 20's scripts (reproduced from the finding text alone, as required).
- Did not test the convention at other material counts — the finding's example is a decisive single case.

## What I am NOT sure about

- Whether the nnue component's different values between the two sides-to-move (228 vs 662) is expected. It is
  consistent with the net being side-to-move-aware, but I did not investigate.

## Times

`stamps.txt`, every line a `date -u`.

## Last command output

(pasted into `last_cmd.txt` at commit time)

## Last command output

```
$ git status --short
 M check_20F14/stamps.txt
?? REPORT_check_20F14.md
?? check_20F14/conv_check.py
?? check_20F14/last_cmd.txt
?? check_20F14/raw_check.txt
$ ls
check_20F14
check_S-F1
check_S-F2
check_S-F3
check_S-F5
FINDINGS.md
honesty.sh
HONESTY.txt
job0_honesty
job1
job2
job3
ownbook_check
REPORT_check_20F14.md
REPORT_check_S-F1.md
REPORT_check_S-F2.md
REPORT_check_S-F3.md
REPORT_check_S-F5.md
REPORT_job1.md
REPORT_job2.md
REPORT_job3.md
REPORT_ownbook_check.md
SEAT.txt
STATUS.md
$ ls check_20F14
conv_check.py
last_cmd.txt
prediction.txt
raw_check.txt
stamps.txt
```
