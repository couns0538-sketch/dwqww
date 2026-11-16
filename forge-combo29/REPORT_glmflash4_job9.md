# glmflash4, job 9 report (2026-11-15/16) — the session's last job

**What the two losing switches add on top of the bundle: nothing.**
**W1 — LmrLateParentRelief over the seven-switch bundle: −1.95 with a 95 %
pair interval of [−14.09, +10.18]** (1,600 games); **W2 — EvasionOrdering
over the bundle: −5.86 [−17.86, +6.12]** (1,600 games). Both lean the same
way their solo readings did (−5.6 ± 12.1 and −4.2 ± 12.5 from the earlier
helper) — neither adds anything; EvasionOrdering leans negative twice now.
**Nothing was cut**: both W-matches ran their full agreed 1,600 games
(see the cut note below); every game ended by mate or a draw rule; illegal
moves, disconnects and time losses are 0 everywhere.

**One deviation, said first:** the job's bundle names **eight** switches, but
the eighth — `MateAlphaGuard` — **does not exist in commit 6b98f217** (no
`uci` line among the tree's 82 options, and a `setoption` for it is silently
ignored: bench 13 with only that switch set prints the base 862,329 —
`step0/seven_bundle_benches.txt`). The bundle as playable on this tree is the
SEVEN declared switches, and everything below uses that. The cross-helper
check also did not reproduce: the other helper's "eight on" number 868,694
differs from my seven-on 876,772 (order-independent — reversed order and
MAG-first both give 876,772); with MateAlphaGuard provably absent, their
number must come from a different tree or setup than this job's base — I
could not reproduce it and did not chase it further.

## Step 0 (unpatched build; fresh runs in this job's folder)

Build: `cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++ -DCMAKE_CXX_FLAGS="-DFORGE_NNUE_HIDDEN=256" && cmake --build build --target forge -j4` (the same flags as my jobs 4/7).

| line | expected | printed | file |
|---|---|---|---|
| bench 11 | 312866 | 312866 | step0/unpatched_bench11.txt |
| bench 13 | 862329 | 862329 | step0/unpatched_bench13.txt |
| bench 16 | 3024920 | 3024920 | step0/unpatched_bench16.txt |
| go perft 5 | 4865609 | 4865609 | step0/unpatched_perft5.txt |
| the eight on | 868694 (cross-helper) | **876772 — MISMATCH, cause above** | step0/seven_bundle_benches.txt |
| the bundle + LmrLateParentRelief | new, ≠ the others | **851826** | step0/seven_bundle_benches.txt |
| the bundle + EvasionOrdering | new, ≠ the others | **825419** | step0/seven_bundle_benches.txt |

The two candidate benches differ from each other and from the bundle's —
both switches act; both matches were played. My first three step-0 runs were
DISCARDED and are not the numbers above: a multi-line shell variable passed
to my UCI feeder exploded into one-word lines the engine silently ignored
(the "eight" bench printed the base number; the two "+X" runs measured the
extra switches ALONE). The committed `step0/seven_bundle_benches.txt` carries
the corrected runs; the feeder's per-argument-is-one-line contract is now
documented in `scripts/`.

The ten `uci` lines: the nine existing ones are quoted in
`step0/uci_reply.txt` (LmrDeeperShallower, ThreatHistory, NullThreatVerify,
NullSeeVeto, ContHist4PlyRead, AspCappedReopen, NonPawnCorrection,
LmrLateParentRelief, EvasionOrdering — all `type check default false`);
**the tenth (MateAlphaGuard) has no line — it does not exist in this tree.**

## The probes

A 2-game logged match before every match (`probes/probeC.txt`,
`probeW1.txt`, `probeW2.txt`; the raw logs stay on this machine at
`/tmp/matches/j9_probe*/probe.log`): zero warnings; the candidate side
receives the seven bundle lines AND its extra switch, the base side the
bundle only — the counted setoption lines in the probe files show exactly
that pattern (bundle lines ×8 = 2 games × both sides; the extra switch ×4 =
2 games × candidate only).

## The matches

Form: one exe both sides, `proto=uci nodes=20000 option.Threads=1
option.Hash=16 option.OwnBook=false` under `-each`, UHO openings
`order=random` with `-srand`, each opening twice with colours reversed, no
adjudication, `-concurrency 4`. **Game-count decision, said plainly:** at
the control's measured pace, two 2,000-game matches would have landed exactly
on the minute-50 line, so per the job's own rule BOTH were played at the same
smaller even number, **1,600 games each** (800 rounds).

| match | cand | base | seed | games | W-L-D (cand) | pair counts | fastchess Elo ± err | my Elo [95 % pair interval] | faults (illegal/disconnect/time) |
|---|---|---|---|---|---|---|---|---|---|
| C | nodes 20000 | nodes 10000 | 8300 | 300 | 176-29-95 | [0, 10, 33, 57, 50] | +186.25 ± 33.29 | +186.25 [+154.41, +221.23] | 0 |
| W1 | bundle+LmrLateParentRelief | bundle | 8301 | 1600 | 453-462-685 | [46, 210, 313, 169, 62] | −1.95 ± 12.12 | −1.95 [−14.09, +10.18] | 0 |
| W2 | bundle+EvasionOrdering | bundle | 8302 | 1600 | 456-483-661 | [62, 177, 334, 180, 47] | −5.86 ± 11.99 | −5.86 [−17.86, +6.12] | 0 |

**How the games ended** (from the per-game files' ending column; every game
accounted for, none by fault):

| match | White mates | Black mates | 3-fold | 50-move | insufficient material | stalemate |
|---|---|---|---|---|---|---|
| C | 113 | 92 | 67 | 11 | 17 | 0 |
| W1 | 460 | 455 | 472 | 98 | 111 | 4 |
| W2 | 502 | 437 | 454 | 93 | 112 | 2 |

Per-game files (ONE line per game, `round|white|black|result|how it
ended|opening FEN`): `matches/C_games.txt`, `matches/W1_games.txt`,
`matches/W2_games.txt` — produced by `scripts/extract_games9.py` (the ending
comes from the PGN's final move comment; the extractor's ending tally was
cross-checked against fastchess's own stdout reasons on the job-8 M3 data
before use: identical counts).

## Files of the repository I opened

- `handoff/...`: `FABLE_TO_glmflash4_9.md`.
- Commit `6b98f217` (the unpatched tree, built fresh in this job's own build
  directory): its `uci` reply (82 options, read for the ten-option check) and
  its four bench numbers; no source line was read this time beyond what the
  earlier jobs had already opened.

## Stamps (date -u / recorded)

- ~23:47:30 job file 9 fetched and read (budget start)
- ~23:49-23:52 step 0 first runs (the discarded variable-form runs are
  superseded by the corrected ones; the story is in the report above)
- ~23:53-23:55 the MateAlphaGuard absence proven; the corrected seven-bundle
  benches (reproduced twice: 876772/876772); order-independence check
- 23:57-00:00 the three probes
- 00:01:07-00:03:04 C (match stamps.txt)
- 00:03:11-00:14:47 W1 (1,600 games, exit 0)
- 00:14:50-00:25:44 W2 (1,600 games, exit 0)
- 00:26-00:33 extraction, tallies, this report, commit, push

## What I did not do

- I did not chase the other helper's 868,694 beyond the MateAlphaGuard
  finding and the order-independence check (their setup may differ in ways
  this tree cannot express).
- I did not test the two candidates against EACH OTHER, nor three-way
  combinations with more of the bundle's members dropped.
- The bundle's own strength was not re-measured here (both W-sides carry it;
  the comparison does not need it) — its +9.5 [-4.0, +23.1] unconfirmed
  reading stays unconfirmed by me.
- No PR; nothing outside my own branch was pushed or changed.

## What I am not sure about

- 1,600 games per match gives intervals of about ±12 Elo: a true add-on of
  +5 for either switch would not have been visible. What IS established is
  that neither switch shows the kind of lean that would justify more games:
  both point the same (negative) way their solo readings did.
- The bundle's composition: with MateAlphaGuard absent I cannot know whether
  the other helper's 868,694 (and the +9.5 unconfirmed reading) included it
  under a different spelling or came from a different tree.
- My uci_feed contract bug (the discarded step-0 runs) is fixed and
  documented, but it is a reminder that a silently-ignored setoption looks
  EXACTLY like a switch that does nothing; the bench tripwire in this job's
  step 0 is what caught it, and I would not have seen it in a match.

## A better way

- The job's step-0 tripwire ("if one equals the base, the switch never
  acted") caught my feeder bug before any match was played — it is the
  single most valuable line in the job text; keep it, and add its mirror:
  quote the raw `setoption` echo or use a `uci` reply delta so a silently
  ignored option is distinguishable from an acting one without a bench run.
- The ending column (round|white|black|result|how it ended|FEN) costs one
  regex over the PGN and closes the runner-fault hole in the owner's warning;
  my extractor's ending tally matched fastchess's own stdout counting on
  independent data — make it the standard per-game format.
- The session's biggest repeats of wasted work came from MEASURING BEFORE
  CHECKING THE MACHINE (job 6's blocked table host; this job's feeder bug).
  The cheap habit that would have caught both: one smoke run of the exact
  pipeline on ONE case before any batch.

## Model

I am glmflash4. The model behind this agent is GLM, trained by Z.ai; the
runtime presents it as GLM 5.3 Flash. I cannot verify a precise version
string from inside the run. This was the session's last job; after pushing
this report I end my run as the job file instructs.
