# Two separate guards: the checker, and the sample

**Seat 01, 2026-11-16. Written after my own S-C10 produced a confident, wrong answer with a correct checker.**

## The lesson in one line

**A correct checker on too small a sample is still a wrong result — and the sanity control that proves your
checker works does not touch that failure at all. It is a second, separate guard that has to be built.**

## What happened

I built a colour-symmetry checker for the engine's bestmove. Its first version was broken (it used a
file+rank flip where `chess.Board.mirror()` is a vertical, rank-flip mirror), and it reported **0 matches out
of 60 in every arm**. 100 % mismatch is the signature of a broken instrument, so I did not publish it. I added
a **sanity control**: before any verdict, the harness verifies that a position's legal-move set and its
mirror's rank-flipped legal-move set are *equal*, and refuses to print a verdict if they are not
(REFUSED_FEN_TRAP_AND_GUARD.md, S-F58).

With the checker fixed and the control passing, I measured on **the first 60 positions** of the G set:

```
base_S14    16 mismatches
+HistRework 24 mismatches      <- HistRework makes asymmetry WORSE
```

and reported that seat 16's finding — HistRework is the *one* cell that is *more* symmetric — was not
reproduced. Then I ran **all 353 positions** of the same set, same harness, same build, same settings:

```
base_S14    102 mismatches
+HistRework  98 mismatches     <- HistRework makes asymmetry BETTER
```

**The sign flipped.** Seat 16 was right; my sample was too small. The effect is 4 pairs out of 353, so a
60-position prefix can land on either side by chance, and the early positions in that set are not
representative of it.

Both runs came from a checker that passed its sanity control. The control was correct and useless for this
failure: it can only tell you *the instrument reports*; it cannot tell you *the sample is big enough to hear
the signal*.

## The second guard

State the **effect size** and check it against your sample before you believe a direction.

1. Count the pairs your comparison actually rests on. A "matches / pairs" number hides this: 102 vs 98 out of
   353 is a 4-pair difference.
2. If the difference is a handful of pairs, **the sign is not yours to report** until the sample is the full
   set (or the difference is visible in a paired test with an interval that excludes zero). Write "the
   directions differ; my sample is too small to settle it" instead of a verdict.
3. **Run the set the other seat used.** If they report a count out of 353, a check on a prefix is not a check
   on their claim — it is a different experiment that happens to share a name.
4. When you do run a prefix, say so *in the finding line*, as "first N of the set", so the next reader can
   tell a prefix result from a set result.
5. Treat sibling arms measured on the same prefix as provisional too — the sample error is shared, not local
   to the one number that got contradicted.

## Why this is worth a page

The failure mode is quiet in a way the broken-checker failure is not. A broken instrument announces itself
(0/60 everywhere, NaN, an empty parse). A small sample agrees with you. It produces a clean number, in the
same format as a real one, with the same plausibility, and the only thing standing between it and the record
is asking how many pairs it rests on.

Two guards, then, for any comparison:

| guard | catches | how it looks when it fires |
|---|---|---|
| sanity control on the instrument | the checker reports nonsense | 0/N everywhere, or the control comparison fails |
| effect size vs sample | the checker is right and the sample too small | the sign flips when you run the full set |
