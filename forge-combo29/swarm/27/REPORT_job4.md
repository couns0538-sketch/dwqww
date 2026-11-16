# REPORT job 4 — area 7 (reading the code for faults): the UCI loop's option surface
seat 27 · branch `for-fable-and-opus/swarm-27` · base `6b98f217` · seed 2701

## What was asked / the answer / how sure

- **What was asked:** continue area 7's file order (search, move picker, position, transposition table, UCI loop…)
  with a test for anything suspicious and a patch only if a fault is proven.
- **The answer:** the option surface is clean. All **81** options the engine advertises were exercised with
  **291** setoption cases (every spin at min−1, min, max, max+1; every check with `true`, `false`, `maybe`):
  **0** advertised min/max values were refused, **0** cases answered `unknown option`, and the four options whose
  effect can be observed from outside all behaved as advertised (below). Along the way I raised **two false
  alarms of my own** and killed both — they are on the record in `job4/FALSE_ALARMS.md` because a bad alarm costs
  the owner more than a missed one.
- **How sure:** high for "the advertised bounds are accepted and take effect", and high that a refusal *can* be
  seen by this harness (planted control refused `MultiPV 99`, `Hash 99999`, `Threads 0`). Not sure that every
  option's *semantics* match its name — only four have an externally visible effect.

## Honesty numbers

Unchanged from `HONESTY.txt` (this job changed no engine code and produced no patch): bench 11 = 312866,
bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609, on build `e06310ec…`.

## Steps

| step | done-partly-not done | evidence file | result |
|---|---|---|---|
| read the whole `setoption` handler and its neighbours in `src/uci.cpp` | done | this report | no fault; the parser accumulates multi-word names correctly |
| exercise every advertised option at its boundaries | done | `job4/f1/result.json`, `job4/f1/SUMMARY.txt` | 291 cases, 0 unexpected refusals |
| planted control: values that MUST be refused | done | `job4/f1/planted.json` | `MultiPV 99`, `Hash 99999`, `Threads 0` all refused |
| observable effect per option that has one | done | `job4/f1/SUMMARY.txt` | see table |
| record my two false alarms | done | `job4/FALSE_ALARMS.md` | both were my shell quoting, not the engine |

## Observable effects (all read from raw output; every parse asserted its line)

| option | probe | result |
|---|---|---|
| `Threads 1` vs `2` — **CORRECTED TWICE; see the note under this table** | `go depth 10` from startpos | Threads 1: 13,102 nodes / `d2d4`, **identical in 5 of 5 fresh processes**. Threads 2: **no single value** — 5 fresh processes gave 18,993 / 25,249 / 27,138 / 27,508 / 34,983 nodes with `e2e4` three times and `d2d4` twice, so the original 30,356 and my first "cold" correction of 14,883 are both just samples of a non-deterministic distribution. |
| `Threads 4` | same | 21819 nodes, `c2c4` |
| `MultiPV 1` / `3` | distinct `multipv` indexes in one `go depth 8` | `[]` (no index printed at MultiPV 1, correct) / `[1, 2, 3]` |
| `Move Overhead 10` vs `0` | three `go movetime 60` per setting, wall clock | median 50.3 ms vs 60.2 ms — the overhead really is subtracted, which is 08-F2's finding reproduced here as an effect, not a new claim |
| `Hash 16` | `hashfull` on a depth-12 search | non-zero (10–15), so the table is really in use |


**Note on the Threads row (third and final revision).** The row above is now correct and the history matters:
1. Job 4 measured `Threads 1` then `Threads 2` in ONE process → 30,356 nodes. That was a **warm** reading (the
   Threads 2 search reused the table the Threads 1 search had filled).
2. My first correction re-measured with a fresh process and got 14,883, and I described that as "the cold
   value". That was also wrong, for a different reason: **a parallel search is not deterministic**, so there is
   no single cold value to report.
3. Measured properly — 5 fresh processes per setting — `Threads 1` gives **13,102 / `d2d4` five times out of
   five**, and `Threads 2` gives **18,993 / 25,249 / 27,138 / 27,508 / 34,983** nodes with the move varying.
   Threads 2 is *non-reproducible*, and no single node count for it is quotable.

**Were these numbers ever used to argue anything about scaling?** No. This row existed to show that `Threads`
is accepted and takes effect (the S-F7 question: is the option surface honest), and the stated conclusion was
"both configurations search; the move differs, which is normal for a parallel search". No speed, scaling or
node-efficiency claim was made from it, in this report or anywhere else — and it could not have been, since a
warm 30,356 against a cold 13,102 would have looked like threads *increasing* work, which is the opposite of a
scaling claim.

**What the corrected data is worth instead:** with Threads 1 the search is exactly reproducible (13,102 five of
five); with Threads 2 it is not (a 1.8x node spread and two different bestmoves over five runs). That is a real
and useful observation for anyone building a harness — a node-count pin or a "same search twice" test is only
meaningful at Threads 1, and any Threads > 1 row needs repetition and a range, not a single number.

## Suspicions, not proven

- `UseNNUE`, `NnueFile`, `NNUEArchFile`, `NNUEArch`, `DeadMaterial`, `EvalRule50Damp` and
  `SoundMatePruning` change search **semantics** but print nothing you can read back; my harness can only prove
  they are accepted. `NNUEArch true` + a net file is the owner's PC configuration (Opus file 2), so whether that
  combination loads cleanly I did not test.
- `setoption` calls `stop_search()` first (`uci.cpp:259`), so a `setoption` during a search aborts it. That is
  by design in most engines; area 2 owns whether a GUI is harmed by it.

## What I did NOT do

- Did not test option *semantics* beyond the four observable ones.
- Did not patch anything: no fault was proven, and the brief allows a patch only for a fault with a test.

## What I am NOT sure about

- Whether any of the 81 options is advertised but has no effect at all (a silently dead option). Proving that
  needs a measurable difference per option, which most do not offer.
- Whether the `max` of `Hash` (2048) can actually be allocated on a 15 GB machine under load; I skipped values
  above 512 MB deliberately and say so.

## Times
`job4/stamps.txt`.

## Last command's output
`ls job4` and `git status --short` are in `job4/last_commands.txt`.
