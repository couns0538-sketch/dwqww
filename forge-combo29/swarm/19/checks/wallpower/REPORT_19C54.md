# 19-C54 — seat 15 is right that I published a pooled ratio, and wrong that the penalty is tail-driven. It is a tight unimodal shift.

## The three questions, answered directly

### 1. What kind of ratio was 1.0693?
**A POOLED ratio**: (total PC20 ms / total PC20 nodes) ÷ (total S14 ms / total S14 nodes). Seat 15's instinct
was exactly right — a pooled ratio is the wrong summary if the distribution has a heavy tail, because the tail's
big pairs dominate both sums.

**Recomputed from the saved run** (`distribution_result.txt`, n = 180, fixed `go nodes 50000`):

| summary | per-node ratio |
|---|---|
| **pooled** (what 19-C53 published) | **1.0643** |
| arithmetic mean | 1.077 |
| geometric mean | 1.074 |
| **median** | **1.071** |

**All four agree to within 1.3 %.** The pooled figure is not being dragged — mean, median, geometric mean and
pooled all sit at 1.064–1.077. **That is the first sign the distribution is not tail-dominated.**

### 2. The distribution (the thing I should have published)

**Per-node ratio, PC20/S14, n = 180:**

| min | Q1 | **median** | Q3 | max |
|---|---|---|---|---|
| 0.751 | **1.044** | **1.071** | **1.110** | 1.837 |

- **IQR = 0.065**, sd = 0.090
- **90.0 % of pairs (162 of 180) are above 1.0**
- histogram: a single peak at **1.05–1.10** (117 of 180 pairs), with 4 low outliers and **one** high outlier at 1.84

**Compare against the NODE ratio in the same pairs:** min 0.336, Q1 0.809, median 0.997, Q3 1.208, **max 2.731**,
**IQR 0.400**. The node ratio is wild; **the per-node ratio's IQR is 6.1× tighter.**

**And the two are statistically independent: r = 0.044.** A pair where PC20 used 2.73× the nodes had a per-node
ratio of 1.099; the pair at 2.06× had 0.770. **Node-ratio extremity says nothing about per-node cost.**

### 3. Is it bimodal? No — and here the correction runs the other way
Seat 15's concern was that a bimodal distribution makes "~7 % per-node penalty" wrong and replaces it with
"a penalty concentrated in a minority of positions, with a heavy tail". **On my data that is not what the per-node
ratio does:**

- **The BIMODALITY IS IN THE NODE RATIO, not in the per-node ratio.** Median node ratio 0.997 with Q1 0.809 and
  Q3 1.208 is a wide, two-sided spread — exactly what seat 15 and I both see, including its 18.4× pair.
- **The per-node ratio is tight, unimodal, and shifted.** 90 % above 1.0, peak at 1.05–1.10, IQR 0.065.

**So the heavy tail in node counts and times is real, and it is a different quantity from the per-node penalty.**
Conflating them would have produced seat 15's proposed statement, which **my data does not support**: a penalty
concentrated in a minority would show a *bimodal* per-node ratio with a large mass at 1.0 and a separate high
cluster. Instead there is a single narrow peak above 1.0.

### Tail-leverage test, done directly
Removing the **top 5 % of pairs by node ratio** (9 pairs, node ratios 2.73 down to 1.83):
- pooled per-node **with** them: **1.0643**
- pooled per-node **without** them: **1.0665**

**The tail contributes −0.2 %, i.e. nothing.** It cannot be dragging my figure, which settles the question
quantitatively rather than by argument.

### The cleanest confirmation: node-matched pairs
Restricting to pairs where the two engines' node counts agree within 2 % — so the **time ratio IS the per-node
ratio**, with no node contamination at all (n = 16, 9 % of the sample):
- per-node ratio **median 1.074**, IQR 0.076
- time ratio median 1.073 — **identical, as it must be**

**This is the measurement with no modelling assumptions**, and it lands on the same 1.07.

## Corrected statement for the FINAL
**PC20 costs ~7 % more per node on real positions (median 1.071, IQR [1.044, 1.110], 90 % of 180 pairs above
1.0), and ~1.2 % more per node on `bench`.** It is **not** a minority-of-positions effect — it is a tight,
unimodal shift present in nine pairs out of ten. **The heavy tail seat 15 found is in the NODE and TIME ratios,
where it is real and large (max 2.7× nodes, 3.0× time), and it is independent of the per-node cost (r = 0.044).**

**For the owner this changes nothing about the advice, and everything about the mechanism:** at matched nodes PC20
spends ~7 % more time **everywhere, not occasionally** — so it is a uniform tax on the search rate, not a set of
pathological positions to be avoided. **Both tails matter differently:** the node-ratio tail means an equal-node
match has high-variance individual positions (some 2.7× apart), while the per-node penalty is a steady 7 %.

## Credit and what I got wrong
- **19-C53 published a pooled ratio without the distribution.** Seat 15's question was the right one, and asking
  it is what produced the tight-IQR finding. I should have reported quartiles unprompted — I had the data.
- **The specific hypothesis (tail-dragged mean) is refuted** by the leverage test and by mean/median/geometric
  agreement. Refuting it is more useful than confirming it: it tells the owner the penalty is uniform.
- **Seat 15's replication at n = 116 with median wall 0.983 / median node 0.926 and mean 1.214 / 1.318** is
  consistent with my node-ratio distribution here (median 0.997, mean 1.043, sd 0.381) — its mean-vs-median gap
  is the same tail, in the same place. **We agree on the distribution; we differ only on which quantity it
  describes.**
