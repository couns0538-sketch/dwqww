# REPORT_depthgap — does the colour-mirror score gap shrink with depth?

**What was asked (my own follow-up to S-F22):** the mirror score gap was ~16–19 cp at depth 10. File 6 uses
"a spread that does not shrink with depth" as its test for a defect in multi-thread scores. Is the colour gap a
shallow-search artefact that washes out, or a persistent property?

**The answer: the gap is FLAT from depth 6 to depth 12. My prediction that it would shrink (P1) was REFUTED.**

```
depth | n  | score_equal | median |gap| | p90 | move_mismatch
    6 | 60 |          9 |      14 cp   |  45 |           24
    8 | 60 |          1 |      17 cp   |  76 |           24
   10 | 60 |          3 |      11 cp   |  85 |           22
   12 | 60 |          6 |      20 cp   |  60 |           19
```

The medians wander between 11 and 20 cp with no trend, and with ~50 cp-only pairs the approximate standard
error of each median is 6–12 cp, so the four 95 % intervals overlap heavily — **the medians are not
distinguishable from one another.** The gap is a persistent property of the engine, not an artefact of a shallow
search.

**P2 confirmed** (the gap never reaches 0: smallest median 11 cp). **P3 confirmed** (score-equal pairs stay at
1–9 of 60 — never a third). **P4 confirmed** (move mismatch falls only from 24 to 19 over six plies — essentially
flat, consistent with the depth-independent generation-order cause of S-F11/S-F12/S-F21).

**What this means.** The colour gap is not something a deeper search fixes, and it is not the same phenomenon as
the multi-thread spread file 6 describes (which does shrink with depth). A ~15 cp median disagreement between a
position and its colour mirror is a property of the search, and per S-F21 it is inherited from the generation
order, which no depth removes.

**How sure:** high on "flat, not shrinking" — four depths, 480 searches, intervals overlapping. NOT sure whether
a much greater depth (20+) would change it; the trend from 6 to 12 gives no reason to expect so, but I did not
go further.

## Honesty numbers

```
exe     /home/ubuntu/builds/bld-pc/forge  PC r15, sha256 068f0927768d30be60e8cce6c9f29620dec330565397357dccc9e0fe361e32f4
        none 312866 / S14 242796 / PC20 278024   (all match file 5)
settings PC20 + Threads 1 + Hash 16, cold discipline (fresh process + ucinewgame) per search
```

## Table

| step | done-partly-not done | evidence file | result |
|---|---|---|---|
| gap at depths 6/8/10/12, 60 positions | done | `raw/depthgap.txt`, `run.log` | median 14/17/11/20 cp, flat |
| score-equal counts per depth | done | same | 9/1/3/6 of 60 |
| move mismatch per depth | done | same | 24/24/22/19 of 60 |
| test whether the medians differ at all | done | this report | approximate SE 6–12 cp, CIs overlap — not distinguishable |
| depth 20+ | NOT done | — | time; the 6–12 trend gives no reason to expect a change |

## Findings

`S-F23 | 6 | the colour-mirror score gap does NOT shrink with depth: on the PC build under PC20 at Threads 1 the median |gap| is 14 / 17 / 11 / 20 cp at depths 6 / 8 / 10 / 12 over 60 positions, with overlapping 95% intervals (approx SE 6-12 cp) so the medians are indistinguishable, while score-equal pairs stay at 1-9 of 60 and move mismatches fall only 24 -> 19 — so the gap is a persistent search property, not a shallow-depth artefact, and unlike the multi-thread spread in file 6 it does not wash out | depthgap/raw/depthgap.txt depthgap/run.log (again: `python3 depthgap/depthgap.py ~/builds/bld-pc/forge /tmp/o`) | NEW |`

## Suspicions, not proven

- That an extremely deep search would still show it. My 6–12 trend is flat but the engine is not playing at
  depth 20+ in any match.
- That the gap's magnitude is dominated by the tuned asymmetric PSQT (my S-F3/S-C3 result) rather than by order
  dependence. Untested on the PC build.

## What I did not do

- Did not go beyond depth 12 (each depth doubles the cost).
- Did not separate the PSQT contribution from the order contribution on the PC build (the PSQT symmetrisation
  patch exists for the base tree only).

## Times

`depthgap/stamps.txt`, every line a `date -u`.
