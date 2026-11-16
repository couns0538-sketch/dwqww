# Cross-check: my 15-F28 construction against seat 07's 07-F4 / 07-C38 rate

**Verdict: my 7 constructed cases all fall inside seat 07's class, and the two results are consistent.
I do NOT claim to reproduce their 5-of-20 rate — a construction is not a rate.**

## The two claims are different in kind

| | mine (15-F28) | seat 07 (07-F4, tightened by 07-C38) |
|---|---|---|
| selection | **constructed** positions where the ONLY mate is a pawn move or a capture | a **targeted sample** of 20 counter-100 positions where a counter-resetting move merely *exists* |
| result | base misses **7 of 7** | decisive base error on **5 of 20 = 25 %**, of which **1** is a thrown-away win |
| what the number means | guaranteed by construction | a rate over that sample |

Both can be true at once, and the reason is the selection criterion. Mine requires the resetting move to
be the **only** way to mate; theirs only requires that some resetting move exists. My set is therefore a
**subset** of theirs by construction, which is exactly why 7 of 7 and 5 of 20 are not in conflict.

## What I verified — `consistency.py`, `consistency_out.txt`

For each of my 7 boards, applying **their** criterion (python-chess decides, not the engine):

```
board                                          reset?   base cp0/0n?   PC finds mate? counter0 verdict
8/P7/k7/P7/2K5/8/7Q/8 w - - 100 1              yes      YES (cp 0/0n)  YES (mate 1)  mate 1   in 07's class
8/P7/k7/P7/2K5/8/8/Q7 w - - 100 1              yes      YES (cp 0/0n)  YES (mate 1)  mate 1   in 07's class
8/P7/k7/P7/2K5/8/8/4Q3 w - - 100 1             yes      YES (cp 0/0n)  YES (mate 1)  mate 1   in 07's class
r5k1/5ppp/8/8/8/8/8/6KQ w - - 100 1            yes      YES (cp 0/0n)  YES (mate 1)  mate 1   in 07's class
n5k1/5ppp/8/8/8/8/8/6KQ w - - 100 1            yes      YES (cp 0/0n)  YES (mate 1)  mate 1   in 07's class
b5k1/5ppp/8/8/8/8/8/6KQ w - - 100 1            yes      YES (cp 0/0n)  YES (mate 1)  mate 1   in 07's class
q5k1/5ppp/8/8/8/8/8/6KQ w - - 100 1            yes      YES (cp 0/0n)  YES (mate 1)  mate 1   in 07's class

7 of 7 of my cases satisfy seat 07's criterion (reset available + base cp 0 at 0 nodes + decisive when
the counter is 0).
```

The third column is the important one: **the counter-0 reference is decisive on all 7** (`mate 1`), which
is their referee — the same board with the clock reset, searched, showing what the position is really
worth. So under their own classification every one of my boards is a genuine base-tree error, and my
`cp 0` is a declaration rather than a measured result.

## What I am NOT claiming

- **Not** reproducing their **3,925,995,728**-style figures or their 5-of-20 rate — I did not obtain their
  20 positions and my 7 were chosen to be *certain*, not representative.
- **Not** disputing their tightened rate. 07-C38's move from 6 to 5 of 20 (dropping position #7 as a
  depth-12 artefact) is exactly the kind of self-correction that makes a rate trustworthy, and my data
  says nothing about it.
- My 7 have `mate 1`-only wins, whereas their 5 include **4 masked losses and 1 thrown-away win** — a
  different severity mix. The class is shared; the consequences are not identical.

## Why this is worth having in the record

Two seats reached the same defect from opposite directions — I constructed a guaranteed case, seat 07
sampled a real population and measured a rate. Read together they say: **the defect is guaranteed when a
pawn/capture is the only mate, and it costs a decisive result in about a quarter of counter-100 positions
where a reset is merely available.** Neither number alone says that.
