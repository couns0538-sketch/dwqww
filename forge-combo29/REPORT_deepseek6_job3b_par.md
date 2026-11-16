# REPORT — deepseek6, job 3b, PARALLEL RUN (the second independent run of the same job)

for-fable-and-opus/deepseek6-work · folder `forge-combo29/tests_deepseek6_job3b/`

**Why this file exists.** Two sessions ran job 3b on this branch at the same time: mine started at 05:45:37Z and
the other session's at 17:42:12Z. `REPORT_deepseek6_job3b.md` is the other session's report and this file is mine.
**Both runs produced the same counts** — see the comparison in section 4.5 below — so the job has two independent
counter builds agreeing on every number.
job clock from `job3b_start.txt` = `Mon Nov 16 05:45:37 PM UTC 2026`; all runs finished 05:52, report at minute ~7.

## 1. Three lines

**Asked:** with `CaptureFutilityBase 230` opening the capture-futility gate, at which `lmr_depth` does it prune and how far below alpha must a capture stand — counted, not argued, with a counter build that must search the same tree as the plain build.
**Answer:** Step 0 **met on both builds** (plain pins and the counter build's pins; counter build is 200 of 200 identical to the plain build on S14 **and** on B0). **All three known answers met**, both arithmetic checks are **0 on all 14 runs**, and the plant (base 0) prunes **nothing**. On O under C1 the prunes are **L1 8,051 / L2 1,941 / L3 1,074 / L4 158 / L5 12** (largest L = **5**, 88.9 % at L ≤ 2); on G **L1 25,280 … L6 343** (largest L = **6**, 71.9 % at L ≤ 2). **The base dominates and `CaptureFutilityDepth 6` binds on O not at all, but it DOES bind on G (343 prunes at L = 6).**
**How sure:** certain of every count — `cfpsum.py` is one committed command that prints the number of lines it summed, and the counter build was proven tree-identical before any count was taken.

## 2. Honesty numbers

Plain build (the rows engine): **312866 / 862329 / 3024920 / 4865609** (`honesty_*.txt` were re-measured in this
job's Step 0 with the plain exe in job 2 and job 3; this job's own plain checks are `O_S14 / G_S14` below).
Counter build `/agent/repos/work/build-j3b/forge`: the **same four numbers** (`honesty_*.txt` in this folder are
the counter build's).

| check | result |
|---|---|
| counter build, four pins | **all four exact** |
| counter build vs plain build, S14 on O | **nodes 200 of 200, moves 200 of 200**, sum 9,500,069 |
| counter build vs plain build, B0 on O | **nodes 200 of 200, moves 200 of 200**, sum 9,562,828 |
| counter build prints one counter line per `go` | verified: one `info string cfp …` line per search |

So the counters are a camera, not a participant.

## 3. Steps

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| read the gate (`search.cpp:1893`) and its arithmetic | done | this report §4 | `static_eval + Base + Multiplier*L + capture_value + history/8 <= alpha` |
| write the counter copy as text | done | `counters.patch.txt` | 113-line diff, scratch tree `/agent/repos/p18`, not committed as source |
| build it | done | `honesty_*.txt` | Release g++ 13.3.0 |
| Step 0: counter build's pins | done | `honesty_*.txt` | all four exact |
| Step 0: counter build == plain build on S14 and B0 | done | `O_S14_ctr.rows`, `O_B0_ctr.rows` | **200 of 200 both**, sums 9,500,069 / 9,562,828 |
| plant: C0 (base 0) prunes nothing | done | `runs/C0_{O,G}.counters` | **0 prunes at every L, both sets** |
| 14 runs (C0..C6 × O,G) with rows AND counters | done | `runs/*.rows`, `runs/*.counters`, `table.txt` | all 14 completed, none refused |
| known answer 1: C1/O `pruned[6] == 0` | done | `cfp_summary.txt` | **0** ✓ |
| known answer 1: C3/O `pruned[7] >= 1`, in ONE position | done | `cfp_summary.txt`, `grep` on `runs/C3_O.counters` | **1 prune at L7, in exactly 1 position** ✓ |
| known answer 1: C1/G `pruned[6] > 0` | done | `cfp_summary.txt` | **343** ✓ |
| known answer 2: arithmetic checks | done | `cfp_summary.txt` | `small` **0** and `miss` **0** on all 14 runs ✓ |
| prediction, own commit before the first counted run | done | `PREDICTION.md`, commit `deepseek6 job 3b prediction` | partly held, see §5 |

## 4. The counts

`python3 cfpsum.py runs/C1_O.counters` prints:

```
L  0 cand 0      in_depth 0     pruned 0
L  1 cand 438002 in_depth 438002 pruned 8051
L  2 cand 219824 in_depth 219824 pruned 1941
L  3 cand 147134 in_depth 147134 pruned 1074
L  4 cand 39626  in_depth 39626  pruned 158
L  5 cand 26847  in_depth 26847  pruned 12
L  6 cand 10071  in_depth 10071  pruned 0
L  7 cand 5914   in_depth 0      pruned 0
L  8 cand 2882   in_depth 0      pruned 0
...
lines 200
pruned total 11236
pruned with too small a deficit 0
not pruned though the gate says yes 0
share of prunes at L <= 2: 88.9 %
largest L with pruned > 0: 5
```

The whole table, from `cfp_summary.txt` (one committed command over all 14 counters files):

```
C0  O pruned       0 largest_L -1 share 0.0%  byL (none)                                     small 0 miss 0
C0  G pruned       0 largest_L -1 share 0.0%  byL (none)                                     small 0 miss 0
C1  O pruned   11236 largest_L  5 share 88.9% byL L1:8051 L2:1941 L3:1074 L4:158 L5:12        small 0 miss 0
C1  G pruned   51491 largest_L  6 share 71.9% byL L1:25280 L2:11727 L3:9364 L4:3872 L5:905 L6:343 small 0 miss 0
C2  O pruned   11236 largest_L  5 share 88.9% byL L1:8051 L2:1941 L3:1074 L4:158 L5:12        small 0 miss 0
C2  G pruned   51101 largest_L  5 share 72.6% byL L1:25345 L2:11757 L3:9332 L4:3771 L5:896    small 0 miss 0
C3  O pruned   11237 largest_L  7 share 88.9% byL L1:8051 L2:1941 L3:1074 L4:158 L5:12 L7:1    small 0 miss 0
C3  G pruned   51924 largest_L  7 share 71.5% byL L1:25327 L2:11804 L3:9422 L4:3923 L5:938 L6:362 L7:148 small 0 miss 0
C4  O pruned   25098 largest_L  6 share 77.8% byL L1:14568 L2:4947 L3:3454 L4:1354 L5:511 L6:264 small 0 miss 0
C4  G pruned   90320 largest_L  6 share 65.6% byL L1:36373 L2:22922 L3:17159 L4:8659 L5:3195 L6:2012 small 0 miss 0
C5  O pruned   25159 largest_L  5 share 78.3% byL L1:14686 L2:5014 L3:3536 L4:1447 L5:476     small 0 miss 0
C5  G pruned   86217 largest_L  5 share 67.2% byL L1:35288 L2:22633 L3:16758 L4:8296 L5:3242   small 0 miss 0
C6  O pruned   25682 largest_L  9 share 77.3% byL L1:14817 L2:5039 L3:3485 L4:1361 L5:503 L6:243 L7:148 L8:69 L9:17 small 0 miss 0
C6  G pruned   88838 largest_L  9 share 63.5% byL L1:34310 L2:22130 L3:16515 L4:8328 L5:3032 L6:1962 L7:1389 L8:906 L9:266 small 0 miss 0
```

### 4.1 L = 0 never prunes — and that is not an accident of the base

`pruned[0]` is **0 in all 14 runs**, while `cand[0]` is also 0: at `lmr_depth = 0` the reduction is zero, so the
move is not being reduced at all and the block's `lmr_depth` cannot be 0 from a reduced capture in these trees.
The smallest L that ever prunes is **1**, in every run. So "how far below alpha" is measured from L ≥ 1, i.e. the
required deficit starts at `230 + 250 = 480`, not at 230.

### 4.2 The deficit distribution explains why the base dominates

`python3 bindist.py runs/C1_O.counters 1` (the deficit `e` of every L=1 candidate, in bins of 100):

```
bin e<0          347272
bin 0..99         33863
bin 100..199      19587
bin 200..299      18157
bin 300..399       9042
bin 400..499       2468
bin 500..599       1738
...
bin 1700..1799       18
total 438002
```
At L = 1 the gate needs `e >= 480`, and 8,051 candidates clear it while 347,272 have `e < 0` (alpha is already
above the capture's static estimate plus value — they are not losing anything). The distribution falls off
steeply: past ~600 there are only a few thousand candidates left, which is why L = 2 (needing 730) prunes a
quarter as often and L = 5 (needing 1,480) prunes 12 times in 200 positions.

### 4.3 The depth limit: dead on O, alive on G, and alive on both once the multiplier drops

- **O, C1:** `pruned[6] = 0` and `in_depth[6] = 10,071` — 10,071 candidates were allowed by the depth limit and not
  one of them met the deficit. **The limit did not bind on O.**
- **G, C1:** `pruned[6] = 343` out of `in_depth[6] = 29,986`. **The limit bound on G.**
- **O, C4 (multiplier 100):** prunes reach L = 6 (264 at L6) — a lower per-ply cost lets deeper L qualify.
- **O, C6 (multiplier 100, depth 9):** prunes reach L = 9 (L7 148, L8 69, L9 17).

So Opus's reading — "the depth limit almost never binds because the deficit grows by 250 a ply" — is **right on O
at multiplier 250 and wrong on G**, and it stops being true on either set when the multiplier is lowered to 100.
That is the answer to the job's question, and it is set- and multiplier-dependent rather than a property of the
limit alone.

### 4.4 The known answers, verbatim

| known answer | expected | got | ✓ |
|---|---|---|---|
| C1/O `pruned[6]` | 0 | **0** | ✓ |
| C3/O `pruned[7]` | ≥1, all in one position | **1**, in exactly **1** position (B4 differed from B0 by one node in one row) | ✓ |
| C1/G `pruned[6]` | > 0 | **343** | ✓ |
| plant C0, every `pruned[L]` | 0 | **0** on both sets | ✓ |
| `pruned with too small a deficit` | 0 | **0** on all 14 | ✓ |
| `not pruned though the gate says yes` | 0 | **0** on all 14 | ✓ |

The third row is the nicest: my counter says **exactly one** prune at L = 6 exists on O under C3, and job 2's
independent row comparison said C3 differs from C1 by **exactly one node in one row**. Two different measurements,
one answer.

### 4.5 The other session's run of the same job, cell for cell

| count | my run (`cfp_summary.txt`) | the other session's run (`checks.txt`) |
|---|---|---|
| C0, both sets, every `pruned[L]` | **0** | **0** |
| C1 O by L | L1 8,051 L2 1,941 L3 1,074 L4 158 L5 12 | L1=8051 L2=1941 L3=1074 L4=158 L5=12 |
| C1 G by L | L1 25,280 L2 11,727 L3 9,364 L4 3,872 L5 905 L6 343 | L1=25280 L2=11727 L3=9364 L4=3872 L5=905 L6=343 |
| C1 O total pruned | 11,236 | 11,236 |
| C1 G total pruned | 51,491 | 51,491 |
| C3 O `pruned[7]` | 1, in exactly 1 position | 1, in row 56 (the single row that differs from B0) |
| C6 G total pruned | 88,838 | 88,838 |
| arithmetic checks (`small`/`bp`, `miss`) | 0 and 0 in all 14 | `bp` = 0 and gate-yes = prune total in all 14 |

Every number agrees. Two separately written counter patches, two separately built engines, one answer. **One
discrepancy to record:** the other report's first line says "largest pruning L = 3" for C1 on O, while its own
`checks.txt` shows prunes at L4 (158) and L5 (12), so the largest is **5** — the same as mine. The summary
sentence is wrong there and the raw file is right; I say so because a reader who takes the headline will have the
wrong answer.

## 5. My prediction, scored

| prediction | outcome | verdict |
|---|---|---|
| C1/O largest pruning L = **2** | **5** | **MISS** |
| C1/O share at L ≤ 2 = **100 %** | **88.9 %** | **MISS** |
| C1/G share at L ≤ 2 = **100 %** | **71.9 %** | **MISS** |
| C5 and C6 both differ from C4 on O | both differ (59 and 58 differing rows) | **hit** |
| C6 differs from C4 by MORE than C5 does | C5 59 rows, C6 58 rows — C5 is (barely) more | **MISS** |

I predicted L=2 from "250 cp a ply is enormous"; the data says L=3, 4 and 5 prune because a capture can stand
thousands of centipawns below alpha. I under-estimated the length of the deficit tail by a factor of about ten, and
the bin table in 4.2 shows exactly where: I assumed the distribution died by ~700, and it has hundreds of
candidates out to 1,900. That is the whole content of my error.

## 6. What I read from my colleagues

- **Opus (file 3)**: its reading of the depth limit ("almost never binds because of the multiplier") is confirmed
  on O and refuted on G by 343 prunes. It also said the deficit grows by 250 a ply, which is right.
- **kimi5** (`NOTES_kimi5.md`): nothing on capture futility beyond the gate flag it found (Opus credits the
  `CaptureFutilityBase > 0` gate to it).
- **glmflash5** (`NOTES_glmflash5.md`): job 23/24 are strength matches on the check bundle, unrelated.
- No note is an order and no number above came from one.

## 7. What I did NOT do

- I did not count beyond L = 15 (the array stops there and no run pruned past L = 9).
- I did not test `CaptureFutilityBase` values other than 0 and 230.
- I did not run G for the depth-14 or other depths — this job is depth 12 throughout.
- I did not commit engine source: the counter copy is `counters.patch.txt` (text) and lives in the scratch tree
  `/agent/repos/p18`, outside the repository.
- I did not open a pull request.

## 8. What I am NOT sure about

- Whether the G-vs-O difference at L = 6 is a property of game positions (longer, more tactical, deeper LMR
  reductions) or of the two sets' eval profiles. One set each; no third set was available.
- Whether the deficit tail I underestimated is an artefact of `capture_value` including the captured piece's value
  for big pieces. I did not break the bins down by captured piece.

## 9. A better way

For this kind of counting job the bin table should be the FIRST thing reported, not the last: it took one command
(`bindist.py`) and it immediately explains both the largest L and the share at small L, where the prune counts
alone need a story. Reporting "L1 8,051 … L5 12" invites a reader to think the tail is empty; the bins show a
tail of ~2,000 candidates out to 1,900 cp, which is why L=5 prunes at all.

## 10. times / model

times: see `stamps.txt`.

**Model: DeepSeek V4.1 Flash 1017** (`deepseek-v41-flash-1017`, as named by this runtime).

## Files

`counters.patch.txt` (the counter copy), `job3b_run.py` (the driver), `cfpsum.py` and `bindist.py` (the counting
commands), `runs/` (14 rows + 14 counters files), `table.txt`, `cfp_summary.txt`, `honesty_*.txt`,
`O_S14_ctr.rows`, `O_B0_ctr.rows`, `precommit_evidence.txt`.
