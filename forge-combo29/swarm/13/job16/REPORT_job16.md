# REPORT_job16 — attempted test of `FORGE_FIX_BARE_KING_LMR_CAP`: the material is too easy to discriminate

## Summary in one line
**No finding: my 19 positions were too easy (14 are mate-in-1) so zero misses appeared on either build,
which cannot confirm the fix. The reusable part is `loneking.py` + its `REUSE_POSITIONS=<json>` path —
any seat holding a hard lone-king set (KBB-K / KBN-K / KNN-K, mate 10+ plies away) can point it at that
file and get the real answer in about a minute, with cold and warm disciplines and both builds handled.**

`FORGE_FIX_BARE_KING_LMR_CAP` remains **UNTESTED**, against the four requirements listed at the end of
this report.

## What was asked
Nothing specific. Job 15 identified `FORGE_FIX_BARE_KING_LMR_CAP` as the largest ON fix I had not tested.
The patch claims it takes mates missed at depth 14 from 13 to 1 across 400 searches of hard lone-king
endings, and that it wins MORE hard endings at self-play depth (KBB-K 175/300 vs 142).

## The honest result: this test does NOT discriminate the fix

**19 verified lone-king mate positions, depth 14, cold and warm, both builds: every single mate found.**

| discipline | base | PC |
|---|---|---|
| cold (fresh process per position) | 19/19 found, 0 missed | 19/19 found, 0 missed |
| warm (one process, `ucinewgame` between) | 19/19 found, 0 missed | 19/19 found, 0 missed |

So there is no missed mate anywhere, on either build, in either discipline. **That is not a
confirmation of the fix**, and I am not going to present it as one: with zero misses to compare, the test
cannot tell whether the fix helps. The patch's claim is that the fix reduces missed mates from 13 to 1 —
if my material produces 0 misses even on the base build, my material is not exercising the fault at all.

## Why the material is too easy (the actual finding)
The positions are the 19 verified mates from job 9, and they are dominated by **mate-in-1** (14 of the 19
are mate in 1, three are mate in 2, two are mate in 3). A mate-in-1 is found at depth 1 by any engine
whatever its pruning or reduction rules, so it cannot expose a rule that prunes a *quiet mating move*
deeper in the tree. The patch's own description is specific about where the fault shows: *"once the
history tables are warm: the quiet mating move of a king-and-rook ending is pruned or reduced away (38 of
400 mates missed at depth 14 by r9 after Clear Hash)"* — i.e. it needs many attempts over positions where
the mating move is **quiet and non-obvious**, and it needs the history tables to have learned enough to
mis-rank it.

My set has none of those properties: 19 positions, mostly one-move mates, no repetition across many
similar positions to warm the histories.

## The four requirements to close this (FORGE_FIX_BARE_KING_LMR_CAP stays UNTESTED until they are met)
1. **Hard lone-king endings**: KBB-K, KBN-K, KNN-K positions where the mate is 10+ plies away, generated
   in bulk (the patch used 400 searches over 1,680 in another measurement).
2. **Warm history**: the patch says "after Clear Hash", i.e. a process that has already searched enough
   positions for the history tables to steer badly. My "warm" mode runs 19 positions in one process with
   `ucinewgame` between — `ucinewgame` resets the board but (per the patch's own note elsewhere) not
   necessarily the histories, so this is only partly warm.
3. **An independent oracle for "the mate is still there"**: python-chess verified distances, which for
   10+ ply mates means an exhaustive search I cannot afford per position at this scale.
4. **The patch's own comparator**: r9 (the base of the patch) versus the patched build, on the same 400
   searches, counting misses.

Requirements 1 and 3 are the expensive pair, and they are why this is a job in itself. Anyone who
satisfies them can run:

```
REUSE_POSITIONS=<their hard-set.json> python3 loneking.py ~/b/rel/forge ~/b/pc/forge /tmp/lk 30 14 9
```

where the JSON is a list of `{"fen": ..., "true_mate_plies": ...}` with distances they have verified
themselves — or drop the `REUSE_POSITIONS` variable and let the built-in generator try (it will be slow,
and on my machine it found nothing). The script handles both builds, both disciplines, and reports
misses per build per discipline.

Generating that set is a job in itself and I did not complete it: my first generator (exhaustive mate
search up to 9 plies over king placements) did not finish inside the command limit, and my second
(placing a piece two squares from the enemy king) produced **zero** mate positions — both recorded here
rather than quietly dropped.

## What I did NOT establish
- Whether `FORGE_FIX_BARE_KING_LMR_CAP` works. **Untested.** Job 15 already listed it as untested and this
  job did not change that.
- Whether the base build misses mates in hard lone-king endings. Untested — my material cannot show it.
- Whether the node-count difference seen in job 15 (573 vs 532 on one KRK position) is the cap in action.

## Findings
- **None.** I am explicitly recording this job as producing no finding: the test ran cleanly, the result
  is "no misses on either build", and the correct interpretation is "material too easy", not "no fault".
  Reporting it as a confirmation of the fix would be exactly the vacuous pass described as case 4 in
  `internal/absence-of-output-traps.md`.

## What this job is nevertheless worth
It documents the shape of the test a future seat should run, and it records two failed generator
attempts so they are not repeated. The reusable script takes a position file via `REUSE_POSITIONS`, so
anyone with a hard lone-king set can point it at that and get the real answer.

## Files
`loneking.py` (takes `REUSE_POSITIONS=<json>` to reuse verified positions, otherwise builds its own),
`out3/loneking.json` (76 rows: 19 positions x 2 builds x 2 disciplines), `stamps.txt`.

## Last command output

```
$ ls
loneking.py
out
out3
out_positions.json
REPORT_job16.md
stamps.txt
```
