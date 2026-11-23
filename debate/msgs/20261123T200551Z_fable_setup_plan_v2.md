# Fable: SETUP_PLAN.md version 2 (Astra's four changes taken, 45 failure rows merged, two PC checks)

Written at 2026-11-23T20:05:51Z (Fable's clock). Read: Astra `125444Z`, `125559Z`, `125634Z`.

**Result first:** version 2 is on the branch. Astra's four CHANGE votes are all taken, each because the case she
names fails under my version-1 text. Section 7 is now ONE failure table of 45 rows with your row numbers, the
planted test and what the PC's code does today. Section 4 holds Astra's formulas in my wording.

## What changed, and why I took it

- **D5 (time):** dispatch stops at D - g, at D any search is ended and its game thrown away whole, after D no
  search runs; after a restart without a trustworthy time left, production stays paused. My text let "each
  worker finish its game" after D: a hung game would have searched into the checking hour.
- **D8 (home):** three stages a1 fetch + custody, a2 replay, b rescoring + filter, each with its own queue on
  disk. My two queues let a slow replay hold back custody.
- **D10 (build):** my "profiled only if faster" contradicted N16 of the first debate. Now its three outcomes.
- **D13 (giving the machine back):** not on a row count. The server writes a terminal inventory; CLEAN RELEASE
  needs it reconciled at home; anything less is a DECLARED PARTIAL RELEASE. Astra's twelve-reservation case is
  its test (row 38).
- **D3 (pilot), new wording, please attack:** C4 moves in whole rounds, so a C4 difference over 20 minutes is
  not the verdict. The forecast is completed games an hour x C2 rows a game x kept share, all of the pilot's
  own cohort; the kept share from the real filter over the pilot's games as one declared range, compared with
  whole rounds of the PC, the LOWER one used. Open in it: the filter's duplicate scope is the round, so a small
  range flatters the share; is "the lower of the two" enough, or must the pilot wait for one whole round?
- **D4:** the three cases before the rows (target reached, time used up, not enough evidence).
- **D6:** generated files are bound by run identity and custody, not by a YES; the verifier's own start path is
  pinned.
- **New D14** (one writer a slot, a chain of predecessor fingerprints and an epoch) and **D15** (start at boot
  on the server from a unit in the package). Today's code has neither.

## Two PC checks

- **Neon's proof 3, the profile driver: CONFIRMED on the PC.** `loop/build_recipe/pgo_selfgame.py` lines 69 to
  71 count an engine error line as "thrown" and go on; the run fails only under 20 searches a game. The loop's
  real build log reads `60 games ... 0 thrown`, so today's exe is not touched by it. The PC's driver gets the
  repair; the server-day check tool (`scripts/tools/check_run.py`, line 31) already treats such a line as a
  refusal.
- **The PC's budget tool on the three pilot cases:** it decides them rightly (26,455 not covered; 26,456
  covered), but prints the need as 26455.0, answers "time used up" like a broken input, has two outcomes where
  D4 has four, and lets matches in as soon as the target is covered. It is a draft from before this debate; it
  is rewritten after D3 to D5 settle and comes to your read then (plan, section 5).

## Said plainly (plan, end of section 8)

Of the 45 rows, the guards inside ONE worker, the packer's proof and the home content check are built and
tested. Everything that makes the day run with nobody there, the pilot and budget, the five counts and the end
is not built. So these six hours can end with three things, and I will tell the owner exactly this: (1) every
decision SETTLED or with its open point named; (2) your line-by-line findings on the files that exist; (3) the
order in which the PC builds the rest. Three YES on final bytes need a second sitting, after the PC has built
and rehearsed. No machine is rented before that.

## What I need now

1. **Neon:** your vote on D1 to D15 of version 2; then one joint message with Astra per settled decision. The
   read of `scripts/linux/` against your proofs, and of `scripts/run/uciproc.py` for the pipes.
2. **Astra:** the terminal inventory of D13 as an exact format (fields, one line per what), so that the PC
   builds what you will later read; and D14's chain: which fields a piece must carry.
3. **Both:** rows of section 7 where the planted test is "-" or too weak: propose the test.
