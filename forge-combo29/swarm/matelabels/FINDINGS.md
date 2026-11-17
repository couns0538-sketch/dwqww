# FINDINGS — the measured mate-label error rate

**Result first.** Over 300 engine-emitted `mate N` labels, drawn by uniform random
sample from the repo's own search corpus at one fixed recorded configuration:

| | count |
|---|---|
| labels harvested | **300** |
| verified (both halves decided) | **238** |
| — exact | **176** |
| — **wrong** | **62** |
| — wrong in the *under* direction | **0** |
| — move wrong, distance plausible | **0** |
| unverifiable (deadline-bounded, reason recorded per row) | **62** |

**Wrong rate among verified labels: 62/238 = 26.1%.**
**Unverifiable rate: 62/300 = 20.7%.**

**Every single error is an over-statement.** Not one label claimed a mate shorter
than the true distance, and not one claimed a distance it could not reach at all.
The engine, at depth 12, systematically reports mates as **longer** than they are.

**35 of the 48 independently confirmed errors are off by exactly one move.**

And the PV-length filter from findings §4 would have caught **9 of the 62** —
**14.5%**. It passes 53 wrong labels untouched. §4's claim that a length-passing
PV is "not rejected, never verified" is now a measured number, on a random sample,
with a denominator.

---

## 1. What the labels are, and why this population

The population is **mate scores the engine itself emits**. That is the only
population a length filter is ever applied to: a filter that discards
short-PV claims acts on labels the engine produced, so the risk it is meant to
manage is the risk in *those* labels.

Sampling frame: `forge-combo29/soak_all/search_corpus.txt` (199,020 FENs — the
repo's own soak corpus, itself an interleaved reservoir sample of 100,000 UHO
book positions and 99,020 fixed-seed playout FENs). 5,473 positions were scanned
to collect 300 mate labels, a harvest rate of **5.48%**. Selection was
`random.Random(20261117).shuffle` over the corpus, then in-order scan — a uniform
random sample, not a search for disagreements.

**This matters, and §4 already warned about the opposite.** The two bad boards in
§4 were found by *searching for disagreements*, so they could not supply a base
rate. This corpus was not selected on disagreement; it was selected on *being a
mate label*. That is what makes 26.1% a rate rather than an anecdote.

One configuration only:

```
engine      Chess Engine Forge 6.4.24 candidate
base commit 6b98f2170a3210e71beed04bbd2553972c253ed7
binary      sha256 e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83
options     Hash 32, Threads 1, MultiPV 1, OwnBook false, UseNNUE true, Ponder false
search      go depth 12
```

All four honesty pins matched before recording: `bench 11` = 312,866,
`bench 13` = 862,329, `bench 16` = 3,024,920, `go perft 5` = 4,865,609
(`evidence/gate.md`).

All 300 labels reproduced **bit-for-bit** on a second pass at the same
build/settings/depth (`scripts/add_seldepth.py`, `0 did not reproduce`). So the
labels are deterministic outputs of a stated build, not one-off noise.

---

## 2. The oracle, and why you should believe it

The brief's rule 4 says validate every fixture; rule 3 says prove every checker
fires on a planted fault. Both were done, and the second one caught two of my own
fixture errors before they reached a number.

### 2.1 The oracle is not the engine, and not python-chess

`scripts/mate_oracle.cpp` is an **independent implementation**: its own mailbox
board, its own move generator, its own attack detection, its own negamax mate
search. It shares no source with `forge`. It is the "AND/OR search that does not
call the engine" standard.

`python-chess` is used for **fixture validity and as a second opinion**, never as
the primary oracle, because the brief records two ways it is not neutral: its
`Board.fen()` silently drops the ep square when no legal ep capture exists, and
its repetition logic can be stricter than the engine's.

### 2.2 Move generator validated against published perft

Perft pins castling, en passant, promotion and pin handling at once. **25/25
cases match published values *and* python-chess**, including Kiwipete (4,085,603
at depth 4) and the four standard CPW positions. `evidence/oracle-perft.json`,
reproduce with `scripts/perft_check.py`.

The oracle is slower than python-chess and agrees with it on every perft case,
which is the intended relationship: two independent implementations, one used to
check the other.

### 2.3 Known-answer self-test, with expectations *computed* not recalled

`scripts/oracle_selftest.py` passes **7/7**, including a negative control (the
start position must yield "no mate"). Crucially, the expected distances are
**computed by a second solver** (`scripts/pysolve_independent.py`, a memoised
negamax on python-chess) rather than written down from memory.

That discipline paid immediately. My first fixture set contained a hand-remembered
"scholar's mate, mate in 1" that is **only a check** (`Qxf7+`, not `Qxf7#`), and a
"wAC mate in 3" that is **mate in 2**. The oracle was right and my fixtures were
wrong. A recalled expectation is a hypothesis, which is exactly how eight
fixtures got labelled mate-in-2/3/4 by eye and turned out to be mate in 1.

### 2.4 Planted-wrong oracle must fail

`scripts/mate_oracle_planted_wrong.cpp` returns the requested depth as the "exact"
distance as soon as *any* mate exists — never proving the shorter distance
impossible. That fault was chosen because it is the one that would **fake a clean
result**: it can never report an over-statement, so it would make a bad corpus
look perfect.

The suite catches it on **6/6** positive cases. A clean run from the real oracle
therefore means something.

### 2.5 End-to-end test of the *verifier*, both directions

`scripts/e2e_label_test.py` plants synthetic labels on positions whose true
distance pysolve confirmed: honest, overstated (+1), wild (+3), and understated
(−1).

**21 synthetic labels: 20/21 classified correctly, and the safety property is
clean:**

* **wrong labels falsely called EXACT: 0**
* **honest labels falsely called WRONG: 0**

The one miss (`wAC-WILD`) returned **UNVERIFIABLE on a deadline**, not a wrong
verdict. It fails in the safe direction.

Both directions were planted deliberately, because §4 records that the two
known-bad boards failed in **opposite** directions. A checker that only ever
reports one direction is not measuring the class — and a checker tuned to this
corpus would have missed an under-statement entirely. This one does not: it
correctly flagged all 3 planted under-statements.

### 2.6 One bug found in my own code, and it is the interesting one

My first cross-check reported **10 of 62 wrong labels as "disputed"** — my oracle
said overstated, python-chess said the claim was correct. Ten disagreements in one
run is a signal about the measurement, not about the engine.

The cause was **mine**: a loss distance lives on **even** plies (the defender
moves first and is mated on the opponent's move), and my cross-check loop stepped
`k` by 2 from 1 — odd only — so it never tested the true even distance and
reported it one move too long. Fixed; the cross-check then returned
**48 confirmed, 0 disputed**.

This is recorded because the failure was invisible except for the disagreement
count. Had the corpus contained only wins, that bug would have produced a
plausible, wrong number and nothing would have flagged it. The 62 loss labels in
the sample are what exposed it.

---

## 3. The verification method, and the cost asymmetry

A `mate N` claim in UCI means the **shortest** forced mate is exactly N moves
(moves, not plies: `format_score` at `src/search.cpp:272` computes
`distance = MateValue - |score|` then `mate = (distance+1)/2`). So "exactly N"
splits into two halves:

* **(A)** some legal move forces mate within the claimed budget
* **(B)** **no** legal move forces mate within one move less

| | win labels (N > 0) | loss labels (N < 0) |
|---|---|---|
| (A) | mate within **2N−1** plies, **pinned to the engine's move** | mated within **2N** plies, full search |
| (B) | no mate within **2N−3** plies | not mated within **2N−2** plies |

The four cells are disjoint and exhaustive over {A,B}, so **no separate
full-distance search is needed** — which is the §4 affordability result.

### The cost asymmetry is real, measured, and one-sided in a way §4 did not state

§4 says the pinned half (A) is cheap. On this corpus the opposite holds for
anything past mate-in-3:

| claimed \|N\| | half A (A) median | A max | half B median | B max |
|---|---|---|---|---|
| 1 | 0.00 s | 0.00 s | 0.00 s | 0.00 s |
| 2 | 0.00 s | 0.03 s | 0.00 s | 0.01 s |
| 3 | 0.01 s | 1.64 s | 0.01 s | 0.04 s |
| 4 | 0.16 s | 46.96 s | 0.12 s | 1.18 s |
| 5 | 3.17 s | 240.77 s | 1.18 s | 7.96 s |
| 6 | 32.75 s | 241.84 s | 1.42 s | 109.25 s |

**Half (B) — the "expensive" half — is consistently cheaper than the pinned half
(A).** The reason is structural: half (B) asks a *negative* question at a *lower*
budget, and a negative answer is established by the first refutation found, so it
exits early. Half (A) must prove a positive over a pinned subtree, and cannot exit
until every defence is closed.

So §4's "the asymmetry is the usable result" holds, but the sign depends on
direction. For a **defence** (half B is the cheap one, by up to 40×). For an
**attack** the pinned subtree is the expensive object. **A budget planned as "B is
the expensive half" would under-fund A on exactly the hard boards.**

### Loss labels cannot be pinned at all

Half (A) for a loss label is a full search, not a pinned one: the engine's
`bestmove` is the **defender's** move, and proving the opponent mates requires
every defence, so pinning pins the wrong side. This is exactly §4's warning that
"a checker that assumes the side to move is the attacker is backwards for any
negative mate score". It is recorded per row (`pinned: false`), not glossed.

### Deadline policy

Per-claim deadlines from the §4 ceiling evidence: |N| ≤ 3 → 60 s per half,
|N| = 4 → 240 s, |N| ≥ 5 → 180–240 s. Every query is a **fresh process**, so the
§4 state-leak bug (recursion unwound without popping, only on the timeout path)
cannot occur here by construction — the process dies instead.

---

## 4. Which claims could not be verified, and why

**62 of 300 (20.7%) are unverifiable.** This is part of the result, not a gap
around it. Reasons, all deadline-bound:

| count | reason |
|---|---|
| 29 | half A pinned **timeout** (a win label's positive proof did not close) |
| 27 | half A loss **timeout** (full search, cannot be pinned) |
| 6 | half B **timeout** |

The distribution is entirely a **distance** effect, and it is sharp:

| claimed \|N\| | n | exact | wrong | unverifiable |
|---|---|---|---|---|
| 1 | 44 | 44 | 0 | 0 |
| 2 | 49 | 49 | 0 | 0 |
| 3 | 33 | 33 | 0 | 0 |
| 4 | 41 | 31 | 10 | 0 |
| 5 | 35 | 15 | 17 | 3 |
| 6 | 30 | 4 | 15 | 11 |
| 7 | 22 | 0 | 6 | 16 |
| 8 | 14 | 0 | 5 | 9 |
| 9 | 8 | 0 | 4 | 4 |
| 10 | 4 | 0 | 1 | 3 |
| 11 | 6 | 0 | 1 | 5 |
| 12 | 1 | 0 | 1 | 0 |
| 14 | 4 | 0 | 1 | 3 |
| 15–19 | 8 | 0 | 0 | 8 |
| 20 | 1 | 0 | 1 | 0 |

**Up to mate-in-3, the labels are perfect: 126/126 exact.** The measured ceiling
in §4 was 4 and "not safe there"; this corpus agrees precisely — mate-in-4 is the
first distance with any errors (10 of 41), and it is also the first with any cost
(one half-A query took 47 s).

Above mate-in-14 the sample thins to 8 rows (15–19) and all of them were
unverifiable, **but not everything large is undecided**: H0081 (claimed 20) and
H0294 (claimed 14) both settled as over-statements, because half (A) closed on the
pinned move and half (B) found a shorter mate early. Unverifiability tracks the
*position*, not the number — a large claim on a forced position closes fast, and a
modest claim on a wide position does not.

**One honest asymmetry in the denominator.** Rows that were *wrong* were cheap to
settle (half B exited early with a refutation), so the wrong rate is computed over
238 verified rows that are **biased toward the decidable**. The unverifiable rows
are concentrated at large |N|, which is exactly where errors are most frequent in
the decidable part. So **26.1% is a floor on the verified population, and the true
rate over all 300 is plausibly higher** — but I cannot measure it, and I am not
going to estimate it.

---

## 5. Direction of every error

**All 62 wrong labels are over-statements. Zero under-statements. Zero wrong
moves.**

Cross-checked independently by pysolve on all 62 (`evidence/crosscheck-wrong-labels.json`):
**48 confirmed, 0 disputed, 14 undecided** (pysolve could not settle them at its
9-ply cap; those 14 keep the oracle's verdict and are flagged as cross-check-undecided).

Magnitude, over the 48 confirmed:

| off by (moves) | count |
|---|---|
| 1 | **35** |
| 2 | 5 |
| 3 | 4 |
| 4 | 2 |
| 6 | 1 |
| 7 | 1 |

### This reproduces the "true mate 5 reported as mate 6" defect, and sizes it

You reported 6 hits in 1,200 requests for that specific defect. **This corpus
contains 8 rows that are exactly that class** — claimed mate 6, true mate 5:

| row | claimed | true | seldepth | depth | pv_len |
|---|---|---|---|---|---|
| H0124 | 6 | 5 | 17 | 12 | 11 |
| H0149 | 6 | 5 | 18 | 12 | 11 |
| H0161 | 6 | 5 | 18 | 12 | 11 |
| H0172 | 6 | 5 | 15 | 12 | 11 |
| H0208 | 6 | 5 | 32 | 12 | 11 |
| H0221 | 6 | 5 | 28 | 12 | 11 |
| H0261 | 6 | 5 | 18 | 12 | 11 |
| H0275 | 6 | 5 | 20 | 12 | 11 |

8/300 = **2.7%** at depth 12, against your 6/1,200 = 0.5% pooled over mixed
requests. The two are not the same population (this is one configuration, depth
12, MultiPV 1, mate labels only, not all requests), so they are **not** a
disagreement and I am not presenting them as one — but this corpus puts the defect
at a measurable rate in a fixed setting, and shows it is **the modal error shape**,
not an exotic one.

### Every wrong label's `seldepth`, as required

Quoted beside every row above and in `evidence/analysis-output.txt`, one block per
error with seldepth, depth, nodes, pv_len, the filter's verdict, the PV and the
FEN. Range across the 62 wrong labels: **seldepth 12 to 38**.

**seldepth does not separate wrong from right — and the deepest search in the
whole corpus is a wrong one.** The three highest-seldepth rows in the corpus are
all wrong: H0294 (claimed 14, seldepth 38), H0298 (claimed −8, seldepth 38) and
H0265 (claimed −7, seldepth 38). Meanwhile correct labels include seldepth 12.
A deeper selective search **does not** protect the distance, and at the top of the
seldepth range it is associated with the largest over-statements. That is worth
recording as a negative result: "it searched to seldepth 38" is not a defence of a
mate distance.

---

## 6. What the PV-length filter would have caught — its measured value

The rule from §4: valid iff PV length is **2|N|−1** for a win and **2|N|** for a
loss.

| | count |
|---|---|
| labels **passing** the filter | 268/300 (89.3%) |
| labels **rejected** by it | 32/300 |
| of the rejected, actually wrong | 9/32 (28%) |
| of the passing, actually wrong | **53/268 (19.8%)** |
| **wrong labels the filter would have caught** | **9/62 = 14.5%** |
| **wrong labels it would NOT have caught** | **53/62 = 85.5%** |

**The filter's measured value on wrong labels is 14.5%.** It catches the short-PV
shapes it was designed for and is blind to the rest.

And the 53 it misses are **precisely the class §4 named**: right-length,
wrong-mate. Every one of them has `pv_len` exactly equal to the wanted value:

```
H0001 claimed 4 pv_len 7 wanted 7 seldepth 20
H0113 claimed -4 pv_len 8 wanted 8 seldepth 19
H0022 claimed 5 pv_len 9 wanted 9 seldepth 19
H0126 claimed -5 pv_len 10 wanted 10 seldepth 33
H0124 claimed 6 pv_len 11 wanted 11 seldepth 17
H0098 claimed 7 pv_len 13 wanted 13 seldepth 20
```

These PVs replay legal and end in checkmate — they simply prove a **shorter** mate
than the score claims. The filter cannot see that, because it only compares the
PV's length against the *claimed* distance, and the claimed distance is the thing
that is wrong. **A filter keyed on the claim cannot validate the claim.**

So §4's sentence — a length-passing PV is "not rejected, never verified" — is now
a number: on this corpus **268 labels pass the filter and 53 of them are wrong**,
for a filter efficacy of 14.5%, with the residual 85.5% sitting exactly in the
right-length-wrong-mate cell that motivated this measurement.

**Practical consequence:** the filter is worth keeping (it removes 9 wrong labels
for free, and 32 rejections is cheap) but it **cannot** be used as evidence that a
corpus is clean. A mate-labelled training set filtered only by PV length carries an
expected ~20% wrong labels among the survivors, all of them biased toward
reporting mates **later** than they occur.

---

## 7. What I had to withdraw, and what is left untested

### Withdrawn

1. **My first fixture set.** A "scholar's mate, mate in 1" that is only a check,
   and a "wAC mate in 3" that is mate in 2. Both were recalled rather than computed;
   the oracle was right. Replaced with pysolve-computed expectations.
2. **My first cross-check result.** It reported 10 of 62 wrong labels as disputed.
   The bug was a parity error in my own loss-distance loop, not an oracle fault.
   Corrected: 48 confirmed, 0 disputed.
3. **My first end-to-end test.** It reported 16/18 misclassified, which looked like
   a verifier failure and was a fixture failure — synthetic rows carried no mating
   move, so half (A) could not pin. Same shape as §4's "a refused FEN manufactures a
   pass": the fixture, not the checker, was broken.

### Not tested, and why

* **Only one configuration.** Depth 12, MultiPV 1, Threads 1, Hash 32. §4 records
  the error as configuration-specific, and a decreasing `mate N` differs between
  builds — so **this rate does not transfer to another depth or to MultiPV > 1**.
  Notably §4's board R5 222 failed at MultiPV 3, and no MultiPV-3 sample was taken
  here. That is the most obvious follow-up.
* **`go mate N` was not exercised.** You note it is a different search (1,140 of
  1,600 cells differ). Every label here came from `go depth`.
* **Nothing above mate-in-19 was decided** (the single claimed-20 row H0081 *was*
  decided, as an over-statement); the 8 rows in the 15–19 band had no decidable
  cell at all.
* **The 14 cross-check-undecided rows** keep the oracle's verdict on the strength
  of the oracle alone. They are 23% of the wrong set and are flagged in the
  evidence, not folded in silently.
* **No engine-code root cause was investigated.** §4 and your note already date
  `search.cpp:1434`; this seat measured the rate, not the mechanism.
* **The corpus is 300, not more, because the sample was fixed at 300** by the
  assignment. The 26.1% figure has a 95% Wilson interval of roughly
  **[20.9%, 32.0%]** — but that interval assumes the verified 238 are a random
  sample of all 300, and they are not (they are the decidable ones). The point
  estimate is honest; the interval should not be read as covering the true
  population rate.

### One thing I want to state plainly

The 20.7% unverifiable rate is **not** a defect in the method and **not** a
reason to distrust the 26.1%. It is the honest shape of the problem: the claims
that are hardest to check are the longest ones, and those are also the ones most
likely to be wrong. A seat that reported only the verified rows without this
paragraph would be quoting a number that looks cleaner than the situation is.
