# seat 20 — job 72: seat 30's 30-F59 (PC20 pick a 200+ cp worse move until depth 18) — NOT REPRODUCED on my build

I tried to confirm 30-C56 / 30-F59 independently. **I could not reproduce it**, and I am recording that as
*unreproduced*, **not** as a refutation — because their run does not state its exe identity, so a build difference
cannot be excluded.

## What they claim
On position 29 (`rnb3nr/3kb2p/1p2p3/p1p2pP1/1PP1p1P1/P3PQ1R/1B1P1P2/RN2KB2 w Q - 0 18`), PC20 plays `f3g3`, which is
**200+ cp worse** than S14's `f3g2`, from depth 10 through 16, and only switches at depth 18.

## What I measured (PC r15 build, Threads 1)

| depth | S14 move / score | PC20 move / score |
|---|---|---|
| 10 | f3g2 / cp 1744 | **f3g2** / cp 1770 |
| 12 | f3g2 / cp 1838 | **f3g2** / cp 1790 |
| 14 | f3g2 / cp 1905 | **f3g2** / cp 1940 |
| 16 | f3g2 / cp 1985 | **f3g2** / cp 2019 |
| 18 | f3g2 / cp 2053 | f3g2 / cp 2031 |
| 20 | f3g2 / cp 2113 | f3g2 / cp 2187 |

**PC20 plays `f3g2` at every depth on my build**, and the two arms' scores agree to within ~50 cp throughout. Their
reported `f3g3 / cp 1627` at depth 12 does not appear in any configuration I tried.

## What I ruled out before concluding "unreproduced"
- **Option ordering / Hash:** their `settle_pos29.py` S14 list carries no `Hash` or `Threads`, so I tried all four
  combinations (S14 and PC20 each with the default Hash 32, and with Hash 16) at depths 12/14/16 — **`f3g2` in all
  twelve cells**, scores within a few cp of each other.
- **The FEN:** their raw JSON's FEN is valid (37 legal moves). (Their *FINDINGS line* misquotes it as `RN2KB1` with
  unequal rank lengths — I used the raw file's `RN2KB2`, which is the right thing to do and is worth their correcting.)

## Why I stop at "unreproduced"
Their `check17/run.log` and `prediction.txt` **do not record the exe's sha256 or `id name`**, so I cannot show their
build is the same as mine. My PC r15 build is
sha256 `068f0927768d30be60e8…`, `id name Chess Engine Forge 6.4.24 candidate`, and it reproduces all four honesty pins.
Given that, the honest verdict is:

> **NOT REPRODUCED (not refuted).** On my build PC20 and S14 agree at every depth. Their result may depend on a build or
> option detail their files do not record — which is itself the actionable note: **a claimed 200 cp behaviour needs the
> executable identity in the file.**

This is exactly the failure mode my S-F44 regime triple exists to prevent, one level down: not just *which settings*,
but *which binary*.

## What would settle it
1. Their exe's sha256 and `id name`.
2. The exact option list they sent, in order, with Hash and Threads included.
Then a re-run of the same six depths on their build — if it still shows `f3g3`, the difference is in the build, not in
the measurement method.

## Limits
- One position, depths 10–20, my build only, Threads 1, built-in net.
- I did not run their `A_isolated` (per-move `searchmoves`) arm; a difference could in principle appear there, but that
  would not explain the *unrestricted* disagreement, which is the claim.
