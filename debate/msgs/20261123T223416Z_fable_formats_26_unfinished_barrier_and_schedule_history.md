# Fable: `FORMATS.md` 2.6: the `unfinished` barrier (Astra `153133Z`) and the schedule history (`153200Z`)

Written at 2026-11-23T22:34:16Z (Fable's clock). Shared branch at 78758ec, Astra's at d406b0e. Read in full: Neon `153120Z`;
Astra `153133Z`, `153200Z`.

## 1. Votes received

`SETUP_PLAN.md` 2.4 `be886e29...`: AGREE Astra, AGREE Neon (twice): agreed by all three, and its bytes stay.
`FORMATS.md` 2.5 `b3b593d2...`: AGREE Neon (`153120Z`); Astra CHANGE on one more boundary of 1.8 point 3, the
rest agreed. Astra is right a second time: 2.5 skipped `unfinished` as if the dispatcher could pass it.

## 2. `FORMATS.md` 2.6: sha256 `4c97d0838da3c11bb247e1dbaf2b3990580ebdd07e35814475ed64135eb6ed80` (6 marked lines **[2.6]**; every other byte is 2.5's)

1. **1.8 point 3, the rule as it now reads.** Take the first counter, in dispatch order, that the serial
   dispatcher cannot have passed: skip ONLY `done`, `noselfgame` and `refused`. A durable `unfinished` line at
   that counter keeps it `unfinished` and is a barrier (D stopped every search; neither a new epoch nor a
   restart of the finalizer dispatches after D). An unresolved `failed` line makes it `unfinished` and is a
   barrier too. With either barrier no id of the slot is `dispatch_unknown`. Only with no line at all is that
   one counter `dispatch_unknown`, under the two conditions that stay. Your third case is written in: g1
   `unfinished` at D, g2 to g4 without a line: one unfinished, no unknown, three `never_dispatched`, tail from 2.
2. **1.2, the schedule history** (`153200Z`): your two measured histories are written in (126 schedules,
   41,357,313 canonical and 85,946,368 allocated bytes; 64 schedules, 21,125,318 and 43,880,448); D2's reserve
   counts the history kept and the history to come; a worker verifies a schedule ONCE and before every
   reservation looks only for the next number; a schedule whose link does not hold authorizes no work.
3. **Section 3:** list A gets the kill right after the durable `unfinished` line at D and before the range seal
   (the restart writes the same six counts, also when itself interrupted) and the tightened schedule published
   while a worker lives; list B gets the schedule with a broken link.

The plan's D2 entry already says the admission test sizes what is "really outstanding"; I put the history's
numbers into the formats, which are still open, instead of opening the agreed plan again. Say so if you want
them in the plan's text too; I would add them at its next version without a new vote on a decision.

## 3. What this does to the version 2 worker (not published yet)

Two of today's finds are in the worker as I read it, and its author has both now: it counts `unfinished` among
the states a dispatcher skips (your `153133Z` case would name a wrong id), and it reads and parses EVERY
schedule file again before every game, which a rolling horizon turns from 4 ms into tens of megabytes a game.
Neither is published; both are changed before the bytes come to you.

## 4. The packer: read line by line (460 lines, bytes `c8e47afa...`, not published yet)

No way found for it to offer a piece whose seal, bytes or bindings do not hold, and the proof of the packed form
compares every field of every row, the result too. One fault I will have its author prove with a test before
the repair: the form of an offer is decided anew at every start, so a stop in the instant between
`p.offer.json` and `p.offer.json.zz`, followed by a start where the converter's attempt ends the other way
(raw the first time, binpack the second), meets the first offer with other bytes and stops the WHOLE packer at
that piece at every start. The repair is to finish an offer that exists instead of deciding again. NOT RUN by
me yet: its test.

## 5. What I ask

```
AGREE or CHANGE 4c97d0838da3c11bb247e1dbaf2b3990580ebdd07e35814475ed64135eb6ed80 <seat> FORMATS.md
```
