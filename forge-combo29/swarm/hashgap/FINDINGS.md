# Hash 16 vs Hash 64: replacing the guess with a measurement

Owner-audit seat. Engine `forge-combo29`, base commit `6b98f217`, branch
`swarm/hashgap`. Build: `/usr/bin/g++`, C++20, `-O3`, `LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13`.

Honesty pins on every build used here — **312,866 / 862,329 / 3,024,920 / perft 5
4,865,609**. The default build (instrument compiled out) and the instrumented
build report all four identically, so nothing below can be an artifact of the
instrument changing the search.

---

## The answer in one paragraph

**"Fewer collisions" is not the mechanism, and neither is it nothing — the
divergence has two separable parts, and the report collapsed them into one
wrong guess.** Measured on one position set at `go nodes 2000000`, 24 positions,
all against `Hash 64`:

* **A baseline that has nothing to do with collisions.** `Hash 64` and `Hash 65`
  differ by one megabyte, both sit at essentially the same load factor (0.270 vs
  0.265), and they still disagree on **11 of 24** positions. The reason is
  structural and now measured: this table indexes by multiply-high
  (`(key * cluster_count) >> 64`), so **≥99.996% of keys move to a different
  cluster for any change in table size**, including this 1.02× one. Collision
  pressure is *identical* in the two tables (37.8% of keys share a cluster with
  another key in both). A size change therefore reshuffles the table rather than
  relieving pressure.
* **An increment that does track load.** `Hash 16` disagrees on **23 of 24**
  (Fisher p = 0.00026 against the 65 baseline) and loses **16,117** real entries
  per position against 162 for `Hash 65`. So real evictions do add on top of the
  baseline.

`Hash 32` (23/24) and `Hash 16` (23/24) are indistinguishable, and `Hash 96`
(15/24) and `Hash 256` (14/24) are indistinguishable from each other. **The
sequence is not monotone in size, and a pressure-only account predicts that it
would be** — less table should mean steadily fewer disagreements. **The practical
consequence is real and narrow: the best move rarely changes — 1 of 40 ordinary
game positions at 750k nodes, 3 of 40 at 1.5M — while the reported score changes
constantly above ~750k nodes.**

---

## What is established, and by what

### 1. The divergence has a load-independent baseline plus a load-tracking increment (established)

The cleanest measurement, one position set, 24 positions, `go nodes 2000000`, all
against `Hash 64`:

| size | disagree | 95% CI (Wilson) | mean real (depth≥1) evictions | vs 64/65 baseline |
|---|---|---|---|---|
| 16 | **23/24** | [80%, 99%] | 16,117 | Fisher p = **0.00026** |
| 32 | **23/24** | [80%, 99%] | 1,909 | Fisher p = **0.00026** |
| **65** | **11/24** | [28%, 65%] | 162 | **baseline** |
| 96 | 15/24 | [43%, 79%] | 39 | p = 0.39 |
| 256 | 14/24 | [39%, 76%] | 1 | p = 0.56 |

Two readings of this table are both wrong, and the table is here so neither can
be told:

* **"It is fewer collisions."** `Hash 65` and `Hash 64` sit at essentially the
  same load and lose almost the same number of real entries (162 against 178 per
  position), yet they disagree on 11 of 24. A pressure-only account cannot produce
  11/24 with equal pressure. That baseline is the part of the old explanation that
  is simply false.
* **"Collisions have nothing to do with it."** `Hash 16` and `Hash 32` disagree
  on 23/24 — significantly more than the 11/24 baseline, p = 0.00026 — and lose
  100× more real entries. Real evictions do add.

What the data will not support is a clean monotone story: 32 and 16 tie at 23/24,
and 96 and 256 tie at 15 and 14. Size is not a single axis here, which is exactly
what you get when one component depends on geometry and another on load.

### 2. A 1.02× size change remaps essentially every key (established, measured)
`cluster = (key * cluster_count) >> 64`, computed from the engine's own occupied
keys at `go nodes 2000000`, 8 positions:

| size pair | keys whose cluster changes | keys sharing a cluster with another key |
|---|---|---|
| 64 vs 65 | **≥99.996%** (8 positions; min 99.996%, max 99.998%) | **37.8%** |
| 64 vs 256 | **100.000%** (all 8 positions) | **37.8%** |

The 1.02× step remaps essentially every key while collision pressure stays
identical (37.8% both ways), which is why `Hash 64` and `Hash 65` diverge at all.
This is the mechanism that replaces the guess for the load-independent part: **the
index is a continuous function of the multiplier, so size is not only a dial from
"crowded" to "roomy" — it is also a dial that reshuffles every entry.** The
handful of keys that keep their cluster at 64-vs-65 are near the top of the key
space, where the fractional product is stable; they are not enough to preserve
the search.

### 3. Not caused by TT cutoffs, and not by TT move ordering (established)

Three arms on the instrumented build, `go nodes 1000000`, Threads 1 — the three
engine arms over 24 positions, the null control over 16:

| arm | n | Hash 1 | Hash 16 | Hash 256 |
|---|---|---|---|---|
| shipped search | 24 | 19/24 | 16/24 | 1/24 |
| no TT cutoff (stores and ordering kept) | 24 | 19/24 | 10/24 | 1/24 |
| no `tt_move` supplied (stores and cutoffs kept) | 24 | 20/24 | 17/24 | 0/24 |
| **null control: no probe result read at all** | 16 | **0/16** | **0/16** | **0/16** |

The null control is the important row. With every probe result discarded, the
answer is identical at all four sizes — **0/16 at 500k, 1M and 2M**. That proves
the harness measures the transposition table and nothing else, and it means the
other rows are attributable to the table's read path. Both partial arms stay
size-dependent, so neither cutoffs alone nor move ordering alone carries it; the
table's reads perturb the tree through several channels at once.

### 4. Not an artifact of stopping mid-iteration (established)

An obvious alternative was that equal-node searches simply stop at different
points in the tree. Refuted by repeating at equal *depth* (16 positions, so the
denominator here is 16, not 24):

| stopping rule | Hash 1 | Hash 16 | Hash 256 |
|---|---|---|---|
| `go nodes 1000000` | 16/16 | 14/16 | 2/16 |
| `go depth 18` (mean 1.17M nodes at Hash 16) | 16/16 | 11/16 | 3/16 |
| `go depth 20` (mean 2.44M nodes at Hash 16) | 16/16 | 14/16 | 9/16 |

At equal completed depth the divergence persists. So it is not a truncation
artifact; a size change genuinely alters the tree.

### 5. No false hits (established — and this is a clean bill, not a defect)

The entry stores only **32 bits** of a 64-bit key (`verification_key` is
`static_cast<std::uint32_t>(key)`). A different position sharing those 32 bits is
accepted as a hit, which would be a correctness defect. The instrument carries a
parallel full-key shadow array and compares on every hit:

**0 false hits in 480 grid cells**, across four sizes and five budgets, over
**330,895,390** probes in total. That is a clean bill for these sizes, and it is
also a bounded one: a false hit needs two keys landing in the same 4-slot cluster
with identical low 32 bits, so the exposure that would find one is far larger than
3.3×10⁸. **"No false hit observed" is the claim; "no false hit is possible" is
not.**

### 6. `hashfull` is a sample, and my first reading of it was wrong (corrected)

I predicted `hashfull()` was incomparable across sizes and that the earlier
report's reasoning on it was unsound. **Half right, and I am recording the half I
got wrong.** `hashfull()` samples `min(1000, cluster_count)` clusters — 6.1% of
`Hash 1` but 0.024% of `Hash 256`. That is a real sampling difference. But the
number it returns tracks true load closely:

| size | true load | hashfull (permille) | share sampled |
|---|---|---|---|
| 1 | 0.8031 | 803 | 6.104% |
| 16 | 0.2889 | 288 | 0.381% |
| 64 | 0.0821 | 81 | 0.095% |
| 256 | 0.0206 | 20 | 0.024% |

So `hashfull` is a *usable* proxy for load at these sizes. What it cannot do is
tell you whether load is the *cause*: it measures pressure, and pressure turns out
to be only one of two components. My prediction that the number was unusable was
wrong; I am recording that rather than deleting it.

---

## The practical question: is `Hash 16` unsafe in play?

**Node budgets that matter.** Measured on this machine, `bench nps` ≈ **1.6M**.

| wall time | nodes | Hash 16 vs 64: best move differs |
|---|---|---|
| 0.25 s | ~400k | 0/40 |
| 0.5 s | ~800k | **1/40** |
| 1.0 s | ~1.6M | **3/40** |
| 2.0 s | ~3.2M | **2/40** |
| 5.0 s | ~8M | **3/40** |

40 ordinary positions walked from real games, Threads 1, cold process per cell.

**Move differences start at roughly 750k–1M nodes, i.e. about half a second per
move on this machine** — not an absurd budget. But they stay rare: **1/40, 3/40,
2/40, 3/40** across 0.5 s to 5 s. So `Hash 16` is not *unsafe* in the sense of
playing a different move; it plays the same move 92–98% of the time at budgets
where a game would notice.

**Scores, however, diverge early and widely.**

| budget | identical | 1–4 cp | 5–19 cp | 20–49 cp | ≥50 cp | median \|Δ\| | worst |
|---|---|---|---|---|---|---|---|
| 200k | 39/40 | 0 | 0 | 1 | 0 | 0 | 21 |
| 500k | 33/40 | 2 | 2 | 2 | 1 | 0 | 88 |
| **750k** | **12/40** | 8 | 15 | 5 | 0 | **5** | 46 |
| 1.0M | 8/40 | 7 | 20 | 5 | 0 | 7 | 36 |
| 2.0M | 2/40 | 9 | 20 | 7 | 2 | 9 | 63 |
| 4.0M | 2/40 | 4 | 19 | 13 | 2 | 11 | 80 |

**The threshold is 750k nodes.** Below 500k the answers are near-identical; at
750k two thirds of cells disagree on score, and by 2M nearly all do. What a game
would notice — a different move — remains rare even at 4M.

**Recommendation.** For fixed-node harness work, **Hash 64 is the minimum above
500k nodes**; the earlier seat's "practical floor at 500k nodes is ~64 MB" is
consistent with this and I get the same ordering. For play at 0.5–5 s per move,
`Hash 16` is *not* a correctness risk: it changes 1–3 moves in 40. What it does
do is make **reported scores unreproducible** across Hash settings above ~750k,
which matters for any pipeline that reads the score (training labels, eval
tuning, SPRT on scores) and not for one that reads only the move.

**What I will not claim.** I have no game results. "2 of 40 moves differ at 2M
nodes" is a statement about answers, not about strength, and a 5% move-difference
rate at high budget is not evidence of an Elo gap in either direction.

---

## Prediction scorecard

Registered in `PREDICTIONS.md` before the instrument existed.

| # | Prediction | Outcome |
|---|---|---|
| 1 | Evictions at `Hash 1`/50k are non-zero | **CONFIRMED.** 10,803 displacements over 24 cells (median 488.5, max 907) |
| 2 | False hits zero or near-zero everywhere | **CONFIRMED.** 0 in 480 grid cells and 0 in all 144 two-effects cells |
| 3 | `hit_shallower` does not track divergence | **CONFIRMED.** Separates in only 4 of 10 comparable rows |
| 4 | `Hash 16` at 500k loses no real (depth ≥ 1) entries | **PARTLY REFUTED.** 792 depth≥1 evictions over 24 cells — small but not zero. My "no real entries lost at 500k" reasoning was too strong; the count is small, which is why only 2/24 cells differ |
| 5 | `hashfull` is not comparable across sizes | **REFUTED.** It tracks load closely; the sampling defect is real but does not distort the reading |

The most important correction is **not** on that list, because I did not predict
it: I expected a single mechanism and there are two. I predicted that collisions
would be the cause and wrote the 64-vs-65 control to test the *assignment's*
framing, not my own. It refuted the pure-pressure story, and the follow-up showed
real evictions still add a significant increment. The honest summary is that the
old one-line guess was wrong in both directions at once — it attributed a
load-independent baseline to load, and it gave no account of the part that is
genuinely load.

On the framing I volunteered against: I argued `Hash 1` being dirty at 50k is the
*signature* of collision pressure rather than its refutation, because load is
inversely proportional to size. **Prediction 1 supports that** — evictions are
plentiful at `Hash 1`/50k. That narrower point stands. The broader conclusion I
was moving toward, that collisions are *the* explanation, does not.

---

## What could not be established

* **Which specific probe changes which specific move.** I can show cutoffs and
  move ordering each carry part of it (both arms stay size-dependent) and that the
  cluster remap is total, but I cannot name the single probe that flips a given
  cell. That requires a divergence-point replay across two binaries, which is a
  larger instrument than this one.
* **Whether the amplification is chaotic or deterministic-but-sensitive.** The
  same-cell control is exactly reproducible (0/16), so it is deterministic. I did
  not measure a Lyapunov-style exponent, so "sensitive dependence" is the accurate
  phrase, not "chaos".
* **Strength.** No games were played. See above.
* **Threads > 1 and wall-clock searches.** Out of scope; every cell is Threads 1.
* **Sizes above 256 MB or below 1 MB.**
* **The earlier report's exact 24 positions**, which were not recorded. My counts
  are on my own 23-, 24-, 16- and 40-position sets and are not a re-derivation of
  their 178 cells. The shapes agree; the denominators are mine.
* **How the two components combine per position.** I can separate them across a
  position set (baseline 11/24, load-tracking increment significant at
  p = 0.00026) but not attribute a single position's flip to one or the other.

---

## Files

| path | what it is |
|---|---|
| `FINDINGS.md` | this document |
| `STATUS.md` | what ran, what is trustworthy, what is left |
| `PREDICTIONS.md` | pre-registered predictions, unedited |
| `patches-instrument.diff` | the instrumented build's patch |
| `scripts/ucih.py` | UCI driver; one fresh process per cell by construction |
| `scripts/grid.py` | the 480-cell size × budget × position grid |
| `scripts/analyze.py` | divergence table, counter separation, eviction depths |
| `scripts/verify.py` | the five pre-registered predictions, judged |
| `scripts/governor.py` | load factor vs evictions, correlated |
| `scripts/mechanism.py` | cutoff and move-ordering arms |
| `scripts/nullcontrol.py` | the `no_read` null control |
| `scripts/geometry.py` | the 64-vs-65 control that split the question in two |
| `scripts/two_effects.py` | separates the load-independent baseline from the load-tracking increment, with Wilson CIs and Fisher p |
| `scripts/cluster_remap.py` | remap measurement on real keys |
| `scripts/depth_vs_nodes.py` | equal-depth vs equal-node |
| `scripts/threshold.py` | practical thresholds on real game positions |
| `scripts/score_size.py` | score-delta distribution and wall-clock mapping |
| `scripts/controls.py` | same-cell reproducibility, second position set |
| `evidence/` | raw jsonl per run plus `analysis/` text output |
