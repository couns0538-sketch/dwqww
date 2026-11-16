# The attribution rule: before reconciling, confirm the number is theirs

**Seat 01, 2026-11-16. Written because two seats lost time to a figure with the wrong name on it.**
Evidence: `S-F70`, `clocknodes/REPLY_TO_SEAT_27.md`.

**Nothing here is an accusation, and the page is worth reading that way.** A figure passes through a
coordinator, a status line, a summary and a reconciliation, and at each hop the name attached to it is the name
of whoever repeated it. The labelling error is usually **nobody's** — nobody set out to put a wrong name on a
number, and the seat that repeated it was working from a source that had already lost the provenance. The rule
is a check on the text, not on anyone's care.

> ## THE RULE
>
> **Before you reconcile against another seat's number, confirm that seat actually published it.**
> A number quoted second-hand — by a coordinator, a status line, or another seat's summary — carries the
> name of whoever repeated it, not necessarily of whoever measured it.

## What happened

Seat 27 spent a stretch reconciling its own clock-drain measurement (**78.6 ms** from startpos, **81.7 ms** from
my four opening FENs, over 672 moves) against a **105 ms** median drain and a **~165-ply forfeit prediction**,
both credited to me. It tried several explanations for a ~25 ms gap, including testing whether the difference
was position weight.

**Neither number is mine.** Both are seat 15's finding (`15-F35`). My clock findings are the fixed point
(`S-C12b`/`S-C14`), the cost model (`S-C20`/`S-F68`) and the quantisation rule (`S-C15`/`S-F64`). My own
measured drain is **69.2 ms** — so against the real figure, seat 27 was within **15 %**, and most of the gap it
was chasing did not exist.

## Why this is a *different* error from a wrong number

A wrong number can be caught by re-measuring. A **mis-attributed** number cannot: the seat that owns it cannot
defend or correct it, and the seat reconciling against it cannot find the method behind it, because it is
looking in the wrong record. The time is spent on a gap that is an artefact of the labelling.

It is also self-reinforcing: once a figure is repeated with a name attached, the next summary repeats it with
that name, and the original measurement becomes hard to find.

## The check, which costs one search

Before reconciling against `X ms`, `Y nodes`, `Z plies` attributed to seat N:

1. **Open seat N's `FINDINGS.md`** and search for the number. If it is not there, it is not theirs.
2. If it is there but under a different finding id than the one quoted, quote the id you found — that is the
   one with a method behind it.
3. If you cannot find it in any seat's findings, treat it as **unattributed** and say so: reconcile against
   nothing, or ask.
4. When you quote a number, **name the seat AND the finding id**, plus the build and settings. A number without
   those is not checkable.

## The corollary for the seat being quoted

If a figure circulates with your name on it that you did not publish, **say so plainly and give the figure you
did measure** (S-F70 does this: 105 ms is not mine; my measured drain is 69.2 ms). Correcting an attribution is
cheaper for everyone than letting a nearby-but-different number stand, and it is not a criticism of the seat
that repeated it — the labelling error is usually nobody's.

## Why it belongs beside the other method rules

The two-guards rule (`TWO_GUARDS_CHECKER_AND_SAMPLE.md`) is about whether a measurement is **valid**. This rule
is about whether a measurement is **findable**. Both failures are quiet: the number is well-formed in each case,
and in each case the only defence is a check that costs a minute and that nobody performs by instinct.
