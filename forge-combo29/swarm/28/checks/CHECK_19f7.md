# S-C2 — 19-F7, build-to-build spread: the NUMBER holds, the CAUSE does not

Checked by seat 28 (area 8) on my own builds. Seat 19's files were **read only** (I fetched their
branch and read `job2/four_builds_times.txt`); nothing of theirs was written or changed.

## The claim
19-F7 (seat 19, area 9): "On this 4-core VM the build-to-build spread of ONE source is 4.2 % (baseA
median 443 ms vs baseB 425 ms, same source, same flags), not the 1.5 % the brief names; a control pair
of two identical builds gave a 95 % CI of [0.9488, 1.0543]. Any speed claim below ~5 % measured here is
measuring the machine."

## Verdict: **REFUTES the stated cause, CONFIRMS the practical conclusion**
19-F7's number (4.1 % between its two medians) recounts exactly from its own raw file, and its practical
advice ("do not trust a <5 % bench difference on this box") is **right and if anything understated**. But
what it calls **build-to-build** spread is not build-to-build: on this machine two builds of this source
are **byte-identical**, and an alternating A/B run of them differs by **0.45 %** between the two builds
while a single run of either build moves by **8-17 %**. The 4.2 % comes from *sequential blocks of runs
drifting while the machine changes state*, which 19-F7's layout (all of A, then all of B) cannot separate
from a build effect.

## Evidence 1 — two builds of this source are byte-identical

```
A: e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83  /home/ubuntu/rebuild19f7/buildA/forge
B: e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83  /home/ubuntu/rebuild19f7/buildB/forge
binaries byte-identical: True
```

Two independent `cmake` + `make -j4` builds from clean directories, same source (commit 6b98f217), same
flags (`-DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=/usr/bin/g++-13`), same GCC 13.3.0. Command:
`python3 rebuild_pair.py /home/ubuntu/rebuild19f7 12`. A byte-identical pair cannot have a
build-to-build *code* difference; any timing difference between them is machine noise.

## Evidence 2 — alternating A/B of those identical builds: 0.45 % apart, 8-17 % within a build

| quantity | value | what it measures |
|---|---|---|
| rounds | 12 | A and B alternated, fresh process each |
| A times (ms) | [468, 446, 448, 440, 440, 440, 441, 455, 435, 434, 433, 439] | all rounds |
| B times (ms) | [443, 436, 508, 472, 434, 465, 444, 433, 441, 431, 453, 434] | all rounds |
| A median / min / max | 440.0 / 433 / 468 | within-build run-to-run noise |
| B median / min / max | 442.0 / 431 / 508 | within-build run-to-run noise |
| A single-run range as % of its median | 8.0 % | what ONE run can move by |
| B single-run range as % of its median | 17.4 % | what ONE run can move by |
| between-build spread of medians | 0.45 % | the thing 19-F7 calls build-to-build |
| one-run paired ratios B/A | min 0.9466 .. max 1.1339 | a seat that runs each side ONCE sees this |
| full range of one-run ratios as % | 18.7 % | where a 4 % reading comes from |

(pasted output of `python3 variance_parts.py /home/ubuntu/rebuild19f7/ab`; raw runs in
`/home/ubuntu/rebuild19f7/ab/ab_runs.tsv`, summarised in `ab_summary.txt`. Nodes identical in all 24
runs: 862,329 — honesty preserved on both builds, and both also reproduce bench 11 = 312,866,
bench 16 = 3,024,920, perft 5 = 4,865,609.)

## Evidence 3 — seat 19's OWN raw file shows the drift, not a build difference

From `forge-combo29/swarm/19/job2/four_builds_times.txt` (their committed data, recounted by my script):

| block | n | times (ms, in order) | median | min | max |
|---|---|---|---|---|---|
| baseA | 15 | [444, 447, 448, 442, 443, 444, 453, 444, 442, 442, 444, **424, 426, 424, 426**] | 443 | 424 | 453 |
| baseB | 15 | [456, 429, 427, 424, 424, 425, 429, 430, 424, 424, 423, 426, 429, 425, 423] | 425 | 423 | 456 |

19-F7's number: median(baseA) 443, median(baseB) 425, difference 4.1 %

The last four baseA runs are **[424, 426, 424, 426] — the same level as baseB's whole block (median
425)**. In other words baseA does not sit "4.2 % above baseB"; baseA's *first eleven* runs sit at
442-453 ms and then the same build drops to 424-426 ms for its last four. That is a step in the machine's
state inside one block. baseA's within-block drift is 10.0 ms, larger than the 18 ms that separates the
two block medians once the step is accounted for, and baseB begins with the same kind of outlier (456).

Corollary that cannot be explained by a build: **the two blocks' ranges overlap completely**
([424, 453]); baseA has runs at baseB's level and baseB has a run above baseA's median.

## What this does to the guidance
- **19-F7's practical rule stands, and is too weak**: a one-run difference of 4 % is entirely ordinary
  noise on this box (my one-run paired ratios ranged 0.947 to 1.134, i.e. −5 % to +13 %). A 5 % threshold
  is roughly the *minimum* useful, not a safe one; the right rule is *alternate the two sides many times
  and compare medians*, not "ignore anything under 5 %".
- **The label "build-to-build" is wrong**: with this build determinism, a rebuild of unchanged source has
  0.0 % code difference; the variance is run-to-run and machine-state.
- This bears on my own S-F3 (job 1), which said movetime-50 wall time is reproducible to 0.05 ms so a
  >1 % change is measurable. That remains true **for movetime timing** (a clock-bounded quantity, 400
  searches) and is **not** true for `bench` timing (a throughput quantity): the two are different
  measurements and I should have said so. S-F3 is corrected in FINDINGS.md by a later line, not edited.

## How to see it again
```
cd forge-combo29/swarm/28/checks
python3 rebuild_pair.py /home/ubuntu/rebuild19f7 12
python3 variance_parts.py /home/ubuntu/rebuild19f7/ab
# and seat 19's own data (read-only):
#   git show <seat19 branch>:forge-combo29/swarm/19/job2/four_builds_times.txt > /tmp/fbt.txt
python3 analyse_19f7_data.py /tmp/four_builds_times.txt
```

## What I did NOT do
- Did not rebuild seat 19's patched binaries; the question was the spread of ONE source, which needs no
  patch.
- Did not try to reproduce seat 19's exact machine state (other jobs running, thermal, CPU frequency).
  That is precisely why I ran the alternating design instead.
- 12 rounds, not 30: enough to separate 0.45 % from 4 %, not enough to state the true tail.

## What I am NOT sure about
- Why seat 19's baseA block steps down after eleven runs. Candidates: another job on the box finishing,
  CPU frequency scaling, or a NUMA/page-cache effect. I did not instrument it, so it stays a suspicion.
- Whether my 0.45 % would hold on a busier box; seat 19's block layout suggests that under load the drift
  can be much larger than that, which is exactly why alternation is the fix.
