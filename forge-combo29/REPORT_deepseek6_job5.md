# REPORT — deepseek6, job 5 (where the check extension spends its nodes, counted by depth)

for-fable-and-opus/deepseek6-work · folder `forge-combo29/tests_deepseek6_job5/`
job clock from `job5_start.txt` = `Mon Nov 16 06:13:00 PM UTC 2026`

## 1. Three lines

**Asked:** count where the check extension spends its nodes — `reached`, `see_neg`, `ext`, `would2`, `would8`, `beat_alpha`, `sub_nodes` by depth — for `CheckExtensionDepth` 2 (E0), 8 (E1), 5 (E2) and 30 (the plant, E3), on O and G.
**Answer:** Step 0 **met** (plain pins + the three known sums exact, counter build identical to plain on S14 both sets and on CED 8 at 9,015,167). **K1–K4 all met** (`mismatch` 0 in all 8 runs; E1 has `ext = 0` for d ≤ 7; E3 is all zeros; `would8` is 0 below d=8 and equals `would2` from d=8). **The extension is almost entirely a SHALLOW-depth effect: 97.0 % of extensions on O and 96.0 % on G are at depth 2..7, with depth 2 alone carrying 41.8 % (O) and 37.5 % (G). Yet those extensions' subtrees are only 13.2 % (O) and 19.6 % (G) of the tree, while removing them (CED 8) shrinks the tree by 5.1 % and 18.1 % — so the extension's subtrees are 2.6x (O) and 1.08x (G) the size of the saving.**
**How sure:** certain of every count (one committed summing command, `cexsum.py`). Two of my three predictions were hit and the third was wrong in an informative direction (below).

## 2. Honesty numbers

Plain build `build-base` sha256 `e06310eca3368556…`: **312866 / 862329 / 3024920 / 4865609** (re-measured in job 2's
Step 0 with the same exe).
Counter build `build-j5` (the check-extension counter copy, `cex_counters.patch.txt`): its own four pins also exact
(`honesty_*.txt` in this folder).

| Step 0 check | result |
|---|---|
| plain build's four pins | 312866 / 862329 / 3024920 / 4865609 ✓ |
| counter build's four pins | the same four ✓ |
| counter build == plain build, S14 on O | **nodes 200 of 200, moves 200 of 200**, 9,500,069 |
| counter build == plain build, S14 on G | **353 of 353**, 18,466,239 |
| **CED 8 on O (the published known answer, 9,015,167)** | **9,015,167 on BOTH builds**, and counter == plain 200 of 200 ✓ |

The last line is the important one: it was measured on the plain build independently (`O_ced8_plain.rows`) and on
the counter build (`O_ced8_ctr.rows`), and the two agree position by position, so the counter copy is a camera and
not a participant.

## 3. Steps

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| read the extension code (`search.cpp:1955`) and its else-branch | done | this report §4 | the `else if` is reached only when the singular test did not run |
| write the counter copy as text | done | `cex_counters.patch.txt` | 131-line diff, scratch tree `/agent/repos/p19`, outside the repo |
| build it | done | `honesty_*.txt` | Release g++ 13.3.0 |
| Step 0: pins, three known sums, counter == plain | done | `honesty_*.txt`, `O_S14_ctr.rows`, `G_S14_ctr.rows`, `O_ced8_plain.rows`, `O_ced8_ctr.rows` | **all met** |
| E0..E3 × O,G = 8 runs with rows and counters | done | `runs/*.rows`, `runs/*.cex`, `table.txt` | all 8 completed |
| K1 `mismatch = 0` in every run | done | `cexsum.py` output in §5 | **0 in all 8** ✓ |
| K2 CED 8: `ext[d] = 0` for d = 1..7 | done | §5 | **0** ✓ |
| K3 CED 30: `ext`, `sub_nodes`, `beat_alpha` all 0 | done | §5 | **all 0** ✓ |
| K4 `would8` = 0 below d=8, = `would2` from d=8 | done | §5 | **holds in all 8 runs** ✓ |
| prediction, own commit first | done | `PREDICTION.md`, commit `deepseek6 job 5 prediction` | (a) hit, (b) hit, (c) **missed** |

## 4. The per-depth table, E0 on O (the base run)

`python3 cexsum.py runs/E0_O.cex` (the whole file is `cex_E0_O.txt`):

```
d  1 reached 126498 see_neg  8677 ext     0 would2     0 would8     0 beat    0 subnodes        0
d  2 reached  79298 see_neg 27123 ext 52175 would2 52175 would8     0 beat11862 subnodes   210083
d  3 reached  50263 see_neg 16936 ext 33327 would2 33327 would8     0 beat 7538 subnodes   215410
d  4 reached  31268 see_neg 12132 ext 19136 would2 19136 would8     0 beat 3973 subnodes   216755
d  5 reached  12364 see_neg  4625 ext  7739 would2  7739 would8     0 beat 2191 subnodes   167393
d  6 reached  10421 see_neg  5429 ext  4992 would2  4992 would8     0 beat  724 subnodes   204683
d  7 reached   8063 see_neg  4305 ext  3758 would2  3758 would8     0 beat  362 subnodes   239687
d  8 reached   4152 see_neg  2168 ext  1984 would2  1984 would8  1984 beat  150 subnodes   235239
d  9 reached   2106 see_neg  1044 ext  1062 would2  1062 would8  1062 beat   84 subnodes   228836
d 10 reached   1000 see_neg   509 ext   491 would2   491 would8   491 beat   25 subnodes   122829
d 11 reached    364 see_neg   169 ext   195 would2   195 would8   195 beat    4 subnodes    67227
d 12 reached     29 see_neg    21 ext     8 would2     8 would8     8 beat    0 subnodes      697
d 13 reached      9 see_neg     8 ext     1 would2     1 would8     1 beat    0 subnodes        0
d 14/d15 reached 0
lines 200 · mismatch 0 · ext total 124868
ext at depth 2..7 = 121127 (97.0 % of ext)
ext at depth 2 alone = 52175 (41.8 % of ext)
subnodes depth 2..7 = 1254011
```

**Note the first line: `reached[1] = 126,498` but `ext[1] = 0`** — at depth 1 the code's `depth >= 2` is false, so
the else-if is *reached* (the singular test didn't run) and rejects. That is exactly the distinction the job asked
the counters to make, and it is why `reached` and `ext` are separate columns.

## 5. The known answers

| check | expected | got | ✓ |
|---|---|---|---|
| K1, every run: `mismatch` | 0 | **0** in all 8 | ✓ |
| K2, E1 (CED 8): `ext[d]` for d = 1..7 | 0 | **0** (`ext total = 3,900`, all at d ≥ 8) | ✓ |
| K3, E3 (CED 30): `ext`, `sub_nodes`, `beat_alpha` | all 0 | **all 0**, `ext total 0` | ✓ |
| K4: `would8[d] = 0` for d < 8 | 0 | **0** in all 8 runs | ✓ |
| K4: `would8[d] = would2[d]` for d ≥ 8 | equal | **equal** in all 8 runs | ✓ |

## 6. Findings

### 6.1 The extension is a shallow-depth effect, and depth 2 is the single biggest site

97.0 % of O's extensions and 96.0 % of G's are at depth 2..7 (d2 alone: 41.8 % / 37.5 %). Only 1,984 + 1,062 + 491
+ 195 + 8 + 1 = **3,741 extensions on O** (3.0 %) sit at depth 8 or deeper. So `CheckExtensionDepth 8` is, in
effect, "delete 97 % of the check extensions" — which is why it changes the tree so much (9,500,069 → 9,015,167,
−5.1 %).

### 6.2 The subtrees those extensions own are bigger than the saving — 2.6x on O

- `sub_nodes[2..7]` on O = **1,254,011**, which is **13.2 %** of the 9,500,069-node tree.
- The CED 8 tree is **485,098 nodes smaller** (9,500,069 − 9,015,167), i.e. a **5.1 %** saving.
- Ratio: **2.59**. So the work done inside the subtree of a shallow check extension is two and a half times the
  net saving from removing the extension.

On G the same comparison gives `sub_nodes[2..7]` = 3,616,834 = **19.6 %** of the tree and a saving of
**18.1 %**, ratio **1.08** — nearly 1. **My prediction (b) filed 8 %–25 % for the O share and 13.2 % is inside it**,
so that one is a hit; what I did not predict is that the ratio to the saving is so different between the two sets
(2.59 vs 1.08), which is the most interesting number in this report.

### 6.3 The beat-alpha rate is HIGHER at shallow depths — my prediction (c) was backwards

| band | O, E0 | G, E0 |
|---|---|---|
| shallow (d2..7) | **26,650 / 121,127 = 22.0 %** | **24.4 %** |
| deep (d8..15) | **263 / 3,741 = 7.0 %** | 15.0 % |

I predicted deep beat-alpha would be HIGHER than shallow (15–60 % vs 5–35 %), and it is lower on both sets. **The
prediction is killed, not adjusted.** The data says the opposite of my model: a shallow check extension is far
more likely to raise alpha than a deep one. A plausible reading — which I have NOT tested — is that a shallow
check is often the start of a forcing line where a fail-low at depth 10+ has already been through seven plies of
pruning, so the survivors are the ones where the check did not decide anything.

**The decline is NOT monotone, and I checked rather than asserting it.** Per depth on O under E0:
d2 22.7 % (11,862/52,175), d3 22.6 %, d4 20.8 %, **d5 28.3 % (rises)**, d6 14.5 %, d7 9.6 %, d8 7.6 %,
**d9 7.9 % (rises)**, d10 5.1 %, d11 2.1 %, d12 0.0 %. So the band difference in the table (22.0 % vs 7.0 %) is
real but the shape inside the shallow band is not a clean fall: d5 is the single most productive depth in the
whole run, and d2/d3 sit just below it.

### 6.4 CED 8 keeps only the deep extensions and they are the LEAST productive ones

E1's numbers: `ext total 3,900` (all at d ≥ 8), `beat_alpha 299` = **7.7 %**. E0's deep-only rate is 7.0 %. So
CED 8 keeps exactly the extension class with the lowest beat-alpha rate, on both sets. That is consistent with
glmflash5's *strength* finding at +6.5 over three looks being small and uncertain: the tree is 5.1 % smaller and
the extensions that remain were the least likely to matter on this measure.

### 6.5 E2 (CED 5) sits between, as the code requires

E2 has `ext total` **19,832** with **16,090 of them at d5..7** (81.1 %) and `sub_nodes[2..7]` **566,301** — about
45 % of E0's 1,254,011, as expected when the whole d2..4 band no longer extends. E2's O sum is **9,170,430**,
between E0's 9,500,069 and E1's 9,015,167; G's E2 is **16,527,061**, also between (E0 18,466,239, E1 15,120,379).
No known answer exists for E2; I record the sums and the counts.

### Suspicions, not proven

- Whether the shallow-extension beat-alpha advantage is about *checks* or about *extensions in general at shallow
  depth*. I have no counter for a non-check extension at the same depths (singular extensions set `extension = 1`
  or `2` at the same place), so this is a question I cannot answer from these runs.
- Whether the O-vs-G ratio difference (2.59 vs 1.08) is about game positions having deeper tactical lines or about
  the two sets' eval profiles. One set each.

## 7. What I read from my colleagues

- **Opus (file 5)**: it cites glmflash5's `CheckExtensionDepth 8` at +6.5 [−0.4, +13.5] over three looks at 2,000
  nodes and the bundle at +6.7 [+1.3, +12.0] over five; my job was to count, not to judge. It also says CED 8
  makes the O tree 5.1 % smaller (9,015,167 against 9,500,069) — **confirmed exactly on both of my builds**.
- **glmflash5** (`NOTES_glmflash5.md`): the strength numbers above are its.
- **kimi5**, **deepseek5**: nothing bearing on this job.
- No note is an order; where a note's number and mine differ, mine is in the table with its file.

## 8. What I did NOT do

- I did not count singular extensions separately, so 6.3's "shallow beats deep" is about the check extension only
  and I cannot say whether it is a property of checks or of shallow extensions.
- I did not run E0..E3 at any depth other than 12.
- I did not test `CheckExtensionDepth` values between 2 and 8 other than 5.
- I did not measure strength, and I do not claim CED 8 is better or worse.
- I did not commit engine source; the counter copy is `cex_counters.patch.txt` (text).

## 9. What I am NOT sure about

- The mechanism behind 6.3 (why shallow checks beat alpha more often).
- Whether the 2.59 vs 1.08 ratio difference between O and G is stable across depths.

## 10. A better way

For an extension whose cost is the SUBTREE it opens, the useful pair of numbers is `sub_nodes` and the actual tree
delta side by side — which is why 6.2 has a ratio and not two percentages. A future job should ask for the ratio
directly ("`sub_nodes[band]` / tree shrink from removing the band"), because either percentage alone invites the
wrong conclusion: 13.2 % looks like a modest share until you divide it by the 5.1 % it actually costs.

## 11. times / model

times: see `stamps.txt`.

**Model: DeepSeek V4.1 Flash 1017** (`deepseek-v41-flash-1017`, as named by this runtime).

## Files

`cex_counters.patch.txt`, `job5_run.py`, `cexsum.py`, `runs/` (8 rows + 8 counters), `table.txt`, `cex_E0_O.txt`
and the other `cex_*.txt` summaries, `honesty_*.txt`, `O_S14_ctr.rows`, `G_S14_ctr.rows`, `O_ced8_plain.rows`,
`O_ced8_ctr.rows`, `precommit_evidence.txt`.
