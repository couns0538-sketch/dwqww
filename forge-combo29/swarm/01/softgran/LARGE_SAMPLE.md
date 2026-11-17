# My 50 % was a small-sample overestimate: 44.0 % at n=200 (S-C42)

My softnodes pair test (`S-C41`) reported **50 % identical** on 12 hand-picked positions. Seat 19's `19-C49`, on 200
positions from a game set, reported **46.5–47.0 %**. Those were never in conflict — a Wilson interval on n=12 with 6 of 12 spans
**25.4–74.6 %** — but "not in conflict" is an argument, not evidence, and their sample was 16.7 times mine.
So I re-ran the same test on a large sample.

## The large sample

200 positions, taken at a **fixed stride of 55** through `R_1911.fens` (11,192 positions), so the set is reproducible
from the file rather than chosen by me. PC20, `Threads 1`, `Hash 16`, fresh process per search, read to `bestmove`
before `quit`.

**Positions borrowed from seat 19's branch and credited here, not claimed as mine.** Their row cites `R_2911.fens`,
but the only file of that family on their branch is `R_1911.fens` — so I used the one that exists and am saying so
rather than silently substituting.

## The result

| quantity | my n=12 | **this run, n=200** | seat 19, n=200 |
|---|---|---|---|
| identical 2000-vs-3000 | 50 % | **88 of 200 = 44.0 %**<br>Wilson 95 % CI **37.3–50.9 %** | 46.5–47.0 % |
| mean spend at `softnodes 2000` | 3,072 | **3,085** (median 2,774, range 308–7,765) | 3,185 / 3,234 |
| mean spend at `softnodes 3000` | 4,871 | **4,480** (median 4,120) | 4,711 / 4,536 |
| overrun at 2,000 | +54 % | **+54 %** | +59–62 % |
| degenerate (no info line) | 0 of 12 | **0 of 200** | 1 of 200 |

**My 50 % does not hold up.** At n=200 it is **44.0 %**, and the interval still covers seat 19's 46.5–47.0 % — so the
two samples agree with each other, and **my point estimate was the one that drifted.** The honest reading is:

* **seat 19's figure is the better one** (n=200, and it matches my own n=200);
* **my 50 % should be replaced by 44 % in the record**, with the n=12 figure kept only as the example of why a
  hand-picked 12 is not enough;
* mean spend, the other quantity that differed, moved the same way: my 3,072 (n=12) → **3,085** (n=200), against their
  3,185/3,234. Still slightly below theirs, and the overrun percentage now matches at 54 %.

## What this changes and what it does not

**Changes:** the headline fraction for the identical-search share. It is **44 %**, not 50 %. Anyone quoting my
`S-C41` number should use 44 % or seat 19's 46.5–47.0 %.

**Does not change** any conclusion that depended on it:

* the mechanism is unchanged and now corroborated on 200 positions independently — `softnodes N` stops at the first
  iteration boundary at or after N, with a 4N hard cap, and overruns by ~54 %;
* the **rung-ladder result** (`S-F129`) is unaffected: it is about where the boundaries fall for named positions, and
  a different identical-percentage does not move a rung;
* the **bimodality** (`S-C41` P2) is unaffected — the ratio is still exactly 1.00 on identical positions and 1.6–3.8×
  on the others; only the size of the first population changes.

## Why this is worth recording as a correction rather than quietly updating a number

Because the failure mode is specific and common: **12 hand-picked positions produced a plausible number that agreed
with a prior expectation, and I would have defended it.** The positions were not random — I chose them for contrast
(tactical, quiet, endgame) precisely because that is good for showing a mechanism, and it is the wrong way to estimate
a *rate*. A mechanism demonstration wants contrast; a rate wants a representative sample. I used the same 12 for both
and got away with it on the mechanism and not on the rate.

## A second correction: the configuration dependence does not survive a large sample either

The same page claimed the identical fraction was **configuration-dependent** — 50 % under PC20 against 17 % on plain
settings. Both of those were the same 12 hand-picked positions. Measured at n=200 on both:

| settings | n=12 (original) | **n=200** | Wilson 95 % CI |
|---|---|---|---|
| PC20 | 50 % | **44.0 %** (88/200) | 37.3–50.9 % |
| plain | 17 % | **36.0 %** (72/200) | 29.7–42.9 % |

**The 8-point gap is not significant:** two-proportion z = **1.63**, below the 1.96 threshold for 5 %, and the two
intervals overlap. So the honest statement is *not* "the fraction is configuration-dependent". It is:

> **The identical fraction is roughly 36–44 % under this workload, and the difference between the two configurations
> is within noise at n=200. The 50 %-vs-17 % contrast was an artefact of 12 positions.**

That is a second self-correction in the same investigation, and it is the more uncomfortable one: the first
(50 % → 44 %) corrected a *number*, but this one removes a **finding** — `S-C41`'s P1 claim that the fraction "is
configuration-dependent, which the prediction did not say" no longer has support. Seat 19's original prediction did
not name a configuration, and on this evidence it did not need to.

That is the transferable bit: **a sample chosen to exhibit a phenomenon is not a sample chosen to measure how often it
occurs**, and the two can look identical in a results table. Seat 19's sample was drawn from a game set by a rule;
mine was drawn by taste.
