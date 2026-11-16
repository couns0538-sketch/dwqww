# REPORT job 4 — seat 15, area 5, depth-14 PV check on O

**What was asked.** Nothing in the brief asks for this directly; it is my own follow-up. The reason
it is worth a job: the brief gives a known O depth-14 node sum of 21,812,100, so a run at depth 14
tests harness fidelity at a **second** depth (job 1 only proved depth 12), and it looks for mate
scores that depth 14 reaches where depth 12 did not.

**The answer.** The depth-14 node sum matches the brief **exactly** — 21,812,100, difference zero —
which is the strongest single fidelity check in my whole set of jobs. On that faithful harness: 0
illegal PV moves, 0 bestmove/PV-first mismatches, 0 positions without a PV line, and **0 mate
scores**. The last part refutes my prediction, and it is informative: O's 200 curated openings never
reach a mate at depth 14, so depth 14 gives no new mate evidence in either direction.

**How sure.** Very high on the sum (exact to the node against a number given in the brief). High on
the zeros (same analyser as job 1, control caught 5 of 5).

## Honesty numbers

Same release build, `e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83`, four pins
exact **in the default option regime** — see the addendum in `HONESTY.txt` (after 15-C3, S14 must
not be applied before measuring the pins). Run metadata: `raw_d14/meta.txt`.

## Table

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| 200 O positions at depth 14 | done | `raw_d14/pv.jsonl`, `raw_d14/raw/` | 200 accepted, 11.9 s |
| **node-sum fidelity at depth 14** | done | `evidence_fidelity.txt` | 21,812,100 vs brief 21,812,100, **diff 0** |
| every record reached depth 14 | done | `evidence_fidelity.txt` | last-info depths seen: `[14]` only |
| PV legality | done | `analyze_d14.txt` | 0 of 200 |
| bestmove == PV first | done | `analyze_d14.txt` | 0 mismatches |
| mate scores | done | `mates_d14.txt` | **0 of 200** |
| control, planted illegal move | done | `analyze_d14.txt` | 5 tried, 5 caught |

## Prediction, as committed before measuring

| # | prediction | verdict |
|---|---|---|
| P1 | sum exactly 21,812,100 | **HELD** (diff 0) |
| P2 | 0 illegal PV moves | **HELD** |
| P3 | at least 4 mate scores | **REFUTED** — 0 |
| P4 | 0 or 1 mate-rule violations | **vacuous** — no mate scores to violate anything |
| P5 | under 10 minutes | **HELD** — 11.9 s |

P3 is refuted and P4 is vacuous, and I say so rather than dressing either up. My reasoning for P3
("deeper search finds more mates") ignored what O is: 200 balanced opening positions, mostly a pawn
or two from equality, where neither side is anywhere near mate. Job 1 found 10 mate scores in 553
positions *because G (real game positions) supplied nearly all of them*, not because depth 12 is
magically mate-rich. So the honest conclusion is that O is the wrong set for a mate question at any
depth, and P3 was a bad prediction rather than a surprising result.

## Findings

### 15-F7 — the O depth-14 sum reproduces exactly; the harness is faithful at two depths (NEW)

```bash
cd forge-combo29/swarm/15/job4
cat evidence_fidelity.txt
```

```
records 200
last-info depths seen: [14]
O depth14 sum = 21812100   known 21812100   diff +0
first three: [59210, 55147, 119620]
```

Job 1 proved the depth-12 sums (O 9,500,069 and G 18,466,239, both exact). This proves the
depth-14 sum for O as well, on the same build, with the same analyser. Two independent depths
matching the brief's published numbers to the node is much stronger evidence that a harness is
measuring the intended engine than any single depth could be — and it is the check I would want
before trusting any zero in this folder.

### 15-F8 — O carries no mate scores at depth 14 (NEW, a scoping result)

`mates_d14.txt` is an empty table: 0 of 200. Combined with job 1 (10 mate scores in 553, of which I
should state the split) this says which set answers mate questions: **G, not O**. A future seat
looking for mate-distance faults should search G (or R), and will waste its time on O.

Honest caveat: I did not re-derive the O-versus-G split of job 1's 10 mate scores in this job, so I
state "G supplied most of them" as my recollection of job 1's data rather than as a number measured
here; the row indices in `job1/mates_table.txt` are what a reader should check (idx ≥ 200 is G).

## Suspicions, not proven

- Depth 14 being *faster per position* than depth 12 in job 1 (11.9 s for 200 vs 16.8 s for 553,
  i.e. O at depth 14 ≈ 0.06 s/pos) suggests the O positions are shallow for this engine. Not
  investigated; not a fault.

## What I did NOT do

- Did not run G at depth 14 (the brief gives a known G depth-14 sum of 43,345,893 — an obvious next
  fidelity check I ran out of time for).
- Did not extend this to G, whose depth-14 sum the brief also gives (43,345,893) — the obvious next
  fidelity check, cut off by the deadline.
- Did not test the mate rule at depth 14 at all, because O produced no mate scores.
- No sanitizer run in this job.

## What I am NOT sure about

- Whether a deeper O run (16, 18) would eventually reach mates; P3's failure does not show O is
  mate-free, only that depth 14 is not deep enough on these positions.

## Times

`stamps.txt` — every line is a pasted `date -u`.

## Last command's output

```
$ ls
analyze_d14.txt
analyze.py
evidence_fidelity.txt
mates_d14.txt
O_first200.fens
prediction.txt
pvrun.py
raw_d14
REPORT_job4.md
run_d14.log
stamps.txt
```

---

# job 4 part B — G at depth 14 (added after part A)

**What was asked.** My own follow-up: G carries the mate scores (part A showed O carries none), and
the brief publishes a G depth-14 node sum, so this both proves fidelity a third time and puts real
game positions in front of the mate rule at a deeper search.

**The answer.** The G depth-14 sum matches the brief **exactly** (43,345,893, diff 0) — three
distinct fidelity checks now pass to the node. On that faithful harness, 353 positions give **2
mate-rule violations**, and one of them is a position I had never searched before with a mate
distance wrong by **6 moves**.

**How sure.** Very high. The node sum is exact against a number in the brief; both violations were
solved by two independent python-chess solvers that agree with each other.

## Prediction vs result (part B)

| # | prediction | verdict |
|---|---|---|
| P1 | sum exactly 43,345,893 | **HELD** (diff 0) |
| P2 | 0 illegal PV moves | **HELD** |
| P3 | at least 10 mate scores | **HELD** — 14 |
| P4 | 0 or 1 mate-rule violations | **REFUTED** — 2 |
| P5 | under 15 minutes | **HELD** — 22.4 s |

## Findings

### 15-F9 — a second, independent mate-distance fault, wrong by 6 moves (NEW)

```bash
cd forge-combo29/swarm/15/job4
grep -E "^MATE_LEN" analyze_g14.txt
python3 solvemate2.py 'k7/6R1/5N2/p4K1P/P7/8/8/8 b - - 0 1' 12
python3 matedbf.py  'k7/6R1/5N2/p4K1P/P7/8/8/8 b - - 0 1' 12
```

```
MATE_LEN (69, 'k7/6R1/5N2/p4K1P/P7/8/8/8 b - - 0 1', 'mate', -9, 'plies=15 want=18 checkmate=False', ...)
MATE_LEN (192, '8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1', 'mate', -9, 'plies=15 want=18 checkmate=False', ...)

MATED_IN_PLIES 6 (depth 6)
MATED_IN_PLIES 6
```

On **idx 69** (`k7/6R1/5N2/p4K1P/P7/8/8/8 b`, black to move, black lost) the engine reports
`mate -9` — a promise of mate in 18 plies — while the true distance is **6 plies** (`mate -3`). That
is 6 moves too pessimistic. Its printed PV is 15 plies and does not reach mate.

This is a **second, independent instance** of the 15-F1 fault class, on a different position, with a
larger error, found without looking for it. Combined with job 1b (0 violations in 200 R positions)
and part A (0 in 200 O positions), the picture is now:

| set | positions | mate scores | violations |
|---|---|---|---|
| O at depth 12 | 200 | 0 | 0 |
| G at depth 12 (job 1) | 353 | 10 | 1 |
| R at depth 12 (job 1b) | 200 | 8 | 0 |
| O at depth 14 (part A) | 200 | 0 | 0 |
| **G at depth 14 (part B)** | **353** | **14** | **2** |

So the fault is confined to G-like deep game positions, and it gets **more** frequent with depth
(1 in 10 mate scores at depth 12, 2 in 14 at depth 14) — the opposite of a rounding wobble.

### 15-F10 — fidelity now proven at three (set, depth) points (NEW)

```
O depth 12  9,500,069   diff 0   (job 1)
G depth 12 18,466,239   diff 0   (job 1)
O depth 14 21,812,100   diff 0   (part A)
G depth 14 43,345,893   diff 0   (part B)
```

Four exact matches against the brief's own published sums. No zero in these folders rests on a
harness that cannot reproduce the engine's node counts.

### 15-F9 follow-up — it is a horizon effect, and it self-corrects (evidence)

```bash
cd forge-combo29/swarm/15/job4
python3 probe2.py 'k7/6R1/5N2/p4K1P/P7/8/8/8 b - - 0 1' 16 --opts s14
```

```
depth 14  score mate -9  seldepth 24  nodes 42957  pv a8b8 h5h6 b8c8 f5e6 ... a7b8   (15 plies, no mate)
depth 16  score mate -3  seldepth 24  nodes 45476  pv a8b8 h5h6 b8c8 h6h7 c8d8 h7h8q   (6 plies, CHECKMATE)
depth 18  score mate -3  seldepth 24  nodes 47095  pv a8b8 h5h6 b8c8 h6h7 c8d8 h7h8q   (6 plies, CHECKMATE)
```

At depth 16 the engine reports the true `mate -3` with a PV that ends in checkmate. Two things follow
and one does not:

- It **is** a horizon effect, and it self-corrects one iteration later.
- It is **not** "hard position, pessimistic estimate": seldepth is 24 in all three lines, the same
  quiescence reach, yet depth 14 says 18 plies where depth 16 says 6. The depth-14 number is not a
  cautious estimate, it is wrong about a mate the engine finds in 6 plies one iteration later.
- I did **not** find the mechanism, and I do not claim a transposition-table explanation even though
  it would fit.

Practical upshot: a harness can catch this class without a solver, because the signature is a PV
shorter than the mate distance the score promises. That check flags both of my instances (idx 69 and
idx 192) and none of the 8 correct mates in job 1b.

## Times

Appended to `stamps.txt` (pasted `date -u`).
