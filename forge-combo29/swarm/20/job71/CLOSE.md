# CLOSE — all four variants fail; the tolerance question is MOOT

This closes the MultiPV / alternate-table thread that ran from S-C27 to S-C45.

## The four variants, and where each fails

| variant | depth at large Hash | alternate lines | verdict |
|---|---|---|---|
| **repaired, alt table = main** (seat 30's patch only) | **collapses to depth 1 at Hash 2048** | faithful | **fails** — does not restore depth |
| **fixed 64 MB cap** (S-C42/S-F56) | 14 ✓ | move by up to **775 cp**, both directions | **fails** — unpredictable |
| **share one table** (S-F57) | 11–15 ✓ | move by up to **~900 cp** | **fails** — bounds from a different root restriction |
| **own 8 MB table** (S-C43/S-C44) | 14 ✓ | 0 cp median, 73 cp max on **shallow** positions | **fails** — **p90 112 cp at depth 23** (S-C45) |

**All four fail.** None satisfies S-F56's requirement (*restore main-line depth at large Hash without moving the
alternate lines' scores*).

## The tolerance question is therefore MOOT
I put a tolerance question to the owner (is 0 cp median / 18 cp p90 / 73 cp max acceptable, or must it be
bit-identical?). **Withdraw that question** — it was asked about the 8 MB candidate, and that candidate fails on deep
positions regardless of which tolerance is chosen (112 cp p90 against my own 100 cp limit). There is no point pricing
a tolerance for a variant that does not work in the regime that matters.

**If the owner answered "accept the tolerance", the answer would not rescue it** — the failure is at depth, not at
tolerance.

## The recommendation is unchanged
**MultiPV 1 at any Hash, or Hash 16 MB with multiple lines.** That advice never depended on any variant; it comes from
S-C27/S-C33 (the measured collapse) and remains the only guidance that is safe under every test I ran.

## What would actually be needed
Nothing I tried works, and the reason is now understood: **the alternate line needs a large table for deep searches
(because a smaller one evicts) and the engine cannot afford to allocate one (because it allocates a second full-size
table synchronously, which eats the clock).** A real fix must attack **the cost of allocating**, not the size — e.g.
lazy zeroing of a large table, a smaller cluster format, or reusing one allocation across lines with disjoint
generations. **All of those are search-engine design work, not measurement**, and I have built none of them.

## Honest state
Five variants' worth of evidence, four failed experiments, and one clear recommendation. That is a negative result
stated as a negative result — the useful thing it gives the owner is that **"use MultiPV 1 with a big Hash" is not a
workaround for a bug, it is the correct configuration**, and that any future fix has to be about allocation cost.
