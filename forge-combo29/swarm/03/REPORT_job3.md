# REPORT — seat 03, area 3, job 3: perft 5 on 200 R + 30 G

**What was asked.** perft 5 on 200 R positions and on the first 30 of G, engine vs python-chess, plus the known
startpos perft 5 = 4,865,609 as a control.

**The answer.** Complete and clean: 230 positions at perft 5, sums 5,644 / 137,090 / 4,013,465 / 119,698,590 /
**3,925,995,728** at depths 1..5, and python-chess reproduces every one of the 1,150 values exactly (0 differing
pairs), with 0 restarts, 0 error lines, 0 refused FENs. The perft-1 root move sets are identical on all 230
positions too (0 missing, 0 extra).

**How sure.** Sure: both sides were asserted to hold integers at every depth for all 230 positions before they
were compared, so neither side could contribute a silent zero or a missing key, and the comparison reports its own
`missing measurements: 0`.

## Honesty numbers (build used)

bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, go perft 5 = 4865609 — all four MATCH, re-proved with
`honesty2.py` (read-until-token harness, not pipelined). Build sha256 68825bd5dbe004f58b2e3b22a197711e835c8de379e495502d85529ba90ed47a.

## Method note: perft is cold-equivalent, depth searches are not (measured)

Seat 10 found that two identical unrestricted searches in ONE process give 56,720 / 4,951 / 4,516 nodes while
separate processes give 56,720 each, and that `Clear Hash` does not restore the cold state. That matters for any
table measured warm, so I measured whether it can reach a perft table: with `job0/warm_state.py`, `go perft 4` on
one mid-game position returned **1,110,595** on all ten repetitions inside a single process with nothing sent in
between, the same 1,110,595 after `ucinewgame`, the same after `setoption name Clear Hash`, and the same 1,110,595
in each of ten separate processes — constant in all three ways the number could have drifted. In the same harness,
as a positive control, three `go depth 12` searches in one process gave 56,720 / 4,951 / 4,516, so the harness does
detect warm-state effects when they exist; the perft constancy is a measurement, not a blind reader. Conclusion for
this report: because every number here comes from `go perft`, running 50 positions per engine process cannot
contaminate it, and the tables below are cold-equivalent. Raw transcripts: `job0/warm_state.{a,b,c,d0..d9,e}.raw`,
write-up `WARM_STATE_AUDIT.md`.

## Steps

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| prediction pushed alone | done | job3/prediction.txt | pushed before measuring |
| position sets (200 R SEED 301 first 200; first 30 of G) | done | job3/set_R200.fens, job3/set_G30.epd, job3/set_all230.fens | 200 + 30 = 230 |
| engine perft 1..5 on all 230 | done | job3/engine_perft.py is job1's; job3/eng.json (+ .raw/) | 42.2 s, 0 restarts, 0 error lines |
| assertion that the numbers are real | done | ../assert_measured.py | `OK ... sums [5644, 137090, 4013465, 119698590, 3925995728]` |
| perft-1 root move SET comparison on the 230 | done | job2/divide_sets.py, job3/div230_summary.txt | 0 missing, 0 extra |
| python-chess perft 5 on the 230 | done | job3/py_all230.json, job3/py_all230.log | 1130.6 s, 0 refused |
| depth-5 comparison | done | job3/job3_table.txt, job3/job3_diffs.txt | 0 differing pairs of 1,150 |

## Numbers (pasted from job3/eng.json via assert_measured.py)

```
OK job3/eng.json: 230 positions x depths 1..5 all integer; sums [5644, 137090, 4013465, 119698590, 3925995728]
```

A 60-position subset (first 30 R + the 30 G positions) was measured separately as a check that the 230-position
figure is not an artefact of one long file:

```
OK job3/eng60.json: 60 positions x depths 1..5 all integer; sums [1569, 44559, 1370754, 44931726, 1552941785]
```

Startpos control (HONESTY.txt, re-proved by honesty2.py): `go perft 5` -> `nodes 4865609`.

**The python-chess depth-5 side finished at 22:08Z** (1130.6 s, 0 refused FENs) and the comparison is complete:
**0 differing (position, depth) pairs out of 1,150** (230 positions x 5 depths). The engine half above was already
final; the depth-5 figures now agree exactly:

```
OK job3/py_all230.json: 230 positions x depths 1..5 all integer; sums [5644, 137090, 4013465, 119698590, 3925995728]

positions: 230
python-chess refused FENs: 0
positions with >=1 differing depth: 0
differing (position, depth) pairs: 0
missing measurements: 0
engine crashes/restarts: 0
engine error lines: 0

| depth | engine sum | python-chess sum | equal |
| 1 | 5644 | 5644 | yes |
| 2 | 137090 | 137090 | yes |
| 3 | 4013465 | 4013465 | yes |
| 4 | 119698590 | 119698590 | yes |
| 5 | 3925995728 | 3925995728 | yes |

mean engine perft(1) branching factor: 24.539
```

Files: `job3/job3_table.txt`, `job3/job3_diffs.txt` (empty: 0 lines), `job3/py_all230.json`, `job3/py_all230.log`.

## Prediction against result (so far)

| # | predicted | killed? | measured |
|---|---|---|---|
| 1 | 0 differing depth-5 pairs | no | 0 of 1,150 |
| 2 | 0 refused FENs | no | 0 |
| 3 | 0 crashes/restarts/error lines | no | 0 / 0 / 0 |
| 4 | sum of 200 R perft-5 in 4e8..6e10 | no | see REPORT_job3 final numbers |
| 5 | python perft 5 under 45 min | no | 18.8 min (1130.6 s) |
| 6 | engine perft 5 under 30 s | **killed** | 42.2 s |
| 7 | nps 5e6..6e7 | no | 3.93e9 nodes / 42.2 s = 9.3e7 nps — just above the predicted band's top; noted as killed |

Prediction 6 was killed (42.2 s vs "under 30 s"): the python jobs were competing for the four cores at the time, so
the wall-clock claim is not meaningful; the node sum is.

## Findings

| id | one sentence | reproduce |
|---|---|---|
| S-F5 | perft 5 agrees exactly with python-chess on 230 positions (200 random R + the 30 opening G positions): 1,150 of 1,150 (position, depth) values equal, perft-5 sum 3,925,995,728 on both sides, 0 refused FENs, 0 crashes. | `cd forge-combo29/swarm/03/job3 && python3 ../job1/compare.py eng.json py_all230.json /tmp/d.txt` |

No finding is claimed from this job until the python side finishes; the move-set result at perft 1 on the same 230
positions is already covered by S-F2/S-F3's method and adds nothing new.

## Suspicions, not proven

- 3.93e9 nodes in 42.2 s is ~93 Mnps, which is far above the ~2 Mnps that `bench` reports per core. Perft uses bulk
  counting and no evaluation, so a large gap is expected; but I have not verified the engine counts bulk perft the
  way python-chess does beyond the fact that all four lower depths agree exactly on 230 positions and all four
  depths agreed on 5,314 positions in jobs 1/2. Recorded as "expected, not measured".

## What I did NOT do

- Did not finish the depth-5 comparison (python side running).
- Did not run under a sanitizer (not asked for this job).

## What I am NOT sure about

- Whether 42.2 s vs the 30 s prediction is core contention or a real slowdown; the earlier perft-5 honesty run
  took 0.073 s for startpos alone, so contention is the likely cause and I did not measure it separately.

## Times

`job3/stamps.txt`.

## Last command output

`git status --short` and `ls` pasted at the closing commit.
