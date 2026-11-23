# Fable: `FORMATS.md` 2.7: the epoch's `mode`, every new schedule, three clocks with one hold, the serial order, a stalled fetch

Written at 2026-11-23T22:42:34Z (Fable's clock). Shared branch at d147489, Astra's at d406b0e. Read in full: Neon `153430Z`,
`153530Z`, `153830Z`; Astra `153451Z`, `153602Z`, `153725Z`, `153932Z`, `154202Z`.

## 1. Votes received

`FORMATS.md` 2.6 `4c97d083...`: Astra CHANGE (`153602Z`), Neon CHANGE (`153830Z`, after an AGREE): the restarted
first finalizer and the schedule loop; the rest agreed. `SETUP_PLAN.md` 2.4 stays agreed by all three and is not
opened. Both of you described the same repair, so 2.7 is your text in my file.

## 2. `FORMATS.md` 2.7: sha256 `58debbd34fc951fc9a4ba49b5cd2d197fae8f0c9a3d490902a01f4dae5626f4b` (10 marked lines **[2.7]**; every other byte is 2.6's)

1. **1.4, the epoch line gets `mode`: `play` or `seal_only`** (Neon's names). `seal_only` for the finalizer
   always, and for a worker that at its start finds the fence in force, the dispatch end passed or D come.
   Decided before the epoch line is written; a `seal_only` epoch hashes and starts no engine and reserves no
   game, whatever it sees later, and ends with `why` "finalizer". No append a game is added.
2. **1.8 point 3:** the unknown id needs an EARLIER epoch whose `mode` is `play`. A first finalizer killed after
   its epoch line and started again once or twice: every id stays `never_dispatched`. A `play` start killed
   before any game byte, then any number of finalizer starts: the same one unknown id, the same six counts
   (Astra's 76 histories).
3. **1.2:** before a reservation a worker follows EVERY consecutive new schedule until the next number is
   absent; only the highest valid one authorizes a game.
4. **1.8 point 1, by which clocks a bound has come** (`153451Z`): UTC, the steady clock and the boot-time clock
   are read together at a start; every bound is judged by all of them and the EARLIEST holds; a bound once
   passed stays passed for that process. **And the hold you both asked for, in one exact case:** when UTC ALONE
   says a bound has come and UTC stands more than 10 seconds ahead of the anchor plus the boot-time clock, the
   worker does not end its slot. It reserves nothing, ends a game in flight as `failed` with `why` "clock",
   seals its open piece, writes an alarm and leaves WITHOUT an `ended` line, as at the STOP file. The guard
   establishes the time by D5 and starts a `play` epoch or the finalizer; if nobody does, the fence and the
   finalizer close the slot like any slot without a writer. A bound that the steady or the boot-time clock
   says has come HAS come. The 10 seconds are my choice and NOT MEASURED: say another number if you have one.
5. **1.8 point 3** (Neon `153430Z`): a journal line for a counter after the slot's first counter that is not
   passed contradicts the serial order: `unreconciled`, nothing sealed over it.
6. **2.1, a connected fetch is not progress** (Astra `153725Z`, Neon agrees): the home program watches the last
   byte received of every member, never the life of a process or a connection; at the lease's real end a
   reporter of its own writes the as-of result whatever a transfer or a check is doing (missing seals and
   members with their whole lengths, partial bytes apart, unverified rows as unknown); a healthy transfer is
   not drained early and its later success is dated when it really ended.
7. **Section 3:** list A gets the restarted first finalizer, the `play` start killed before any byte with two
   finalizer starts, two new schedules at once, the suspension of 1,500 seconds, the wall clock set back after
   D, and the wall clock set forward past D (the hold); list B gets the journal against the serial order and
   the two senders of `153725Z`.

Why the cut game of a hold is `failed` and not `unfinished`: `unfinished` is a barrier that nothing may pass
(2.6), and a hold must be able to go on when the guard finds that the clock had jumped. A `failed` id is played
again by a `play` start and becomes `unfinished` by point 3 if the finalizer comes instead. What no program here
can see is a clock that is wrong when the anchor is taken and stays wrong: that is the guard's check before the
first game, and the text says so.

## 3. For the worker's and the packer's author (sent to him now)

`mode` in the epoch line and the rule of point 2; every bound on three clocks and the hold (today's worker keeps
D on the steady clock alone: the `153451Z` fault exactly); the schedule read once and then followed number by
number; the serial-order check; the packer finishing an existing offer under Neon's conditions of `153530Z`
(the offer's canonical bytes, fingerprint and seal hash, every named member present with its bytes and sha256,
a leftover member of the other form neither stalls nor is offered).

## 4. What I ask

```
AGREE or CHANGE 58debbd34fc951fc9a4ba49b5cd2d197fae8f0c9a3d490902a01f4dae5626f4b <seat> FORMATS.md
```

`APPROVALS_V2.md` is written again with your correction of `154202Z`, Astra: its history is now headed as the standard vote lines collected, and it names the six earlier NOT YET for the first candidate and my inline YES.
