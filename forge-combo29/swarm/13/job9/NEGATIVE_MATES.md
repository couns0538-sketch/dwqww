# Job 9b — NEGATIVE mate scores: the gap is now CLOSED (and how I nearly got it wrong)

Job 9's report stated that `mate < 0` had **no coverage**. This file closes that gap. It also records
a mistake I made in the process, because the mistake is instructive.

## The result
**4 negative mate claims, all 4 correct.** Real lost positions taken from the G set (16 positions
where the side to move is down ≥ 700 centipawns of material), searched at the PC's match budgets under
PC20, Threads 1, Hash 16.

| FEN | claim | plies it allows | opponent forces mate within that? | engine's own PV mates at ply | verdict |
|---|---|---|---|---|---|
| `8/8/5pp1/4p2p/7P/1b2k1K1/3R4/1q5r w - - 0 1` | `mate -3` | 6 | yes | 6 | **CORRECT** (at 20,000 and again at 250,000) |
| `8/4K1pk/8/4p3/2pq3P/5p2/8/8 w - - 0 1` | `mate -4` | 8 | yes | 8 | **CORRECT** |
| `8/8/7K/5p2/5k2/8/8/6q1 w - - 0 1` | `mate -3` | 6 | yes | 6 | **CORRECT** |

12 runs total (6 positions × 2 budgets): 4 produced a negative mate score, 8 produced a large negative
`cp` (range −245 to −3669), and **no run produced a positive or zero score in a lost position** — which
is the other half of what "the sign convention works" means.

## The mistake I made, and why it is worth recording
My first verification pass reported all four as **WRONG**, saying "opponent should force mate within 6
plies: False". That conclusion was **my error, not the engine's**: I had asked the wrong question. I
reused the checker from the positive case, which asks *"can the side to move force mate within N
plies?"* — correct for `mate +M`, but for `mate −M` the mate is forced **by the opponent**, so the
right question is *"after the side to move makes any move, can the opponent force mate within
2|M|−1 plies?"*.

With the correct predicate the answer is True for all four, and the engine's PV mates at exactly the
predicted ply every time. Had I trusted my first checker I would have filed a false engine bug of
exactly the kind I have spent this run warning others about — a fabricated finding from a broken test.

**The lesson, stated for the next reader:** a negative mate score is not a positive one with a minus
sign. The two need *different* verification predicates, and reusing one for the other produces a
confident false failure. This is the mirror image of the stale-shard fault: there the tool invented
*engine differences*; here it invented *engine defects*. Same root cause — a checker that could not
distinguish "the engine is wrong" from "my check is wrong".

## What this now covers, and what it still does not
**Covered:** positive mate claims (S-F11, 57/57 exact) and negative mate claims (this file, 4/4 exact),
across the three match budgets, with the engine's own PV verified against an exhaustive python-chess
search.

**Still not covered, and I am not going to dress it up:**
- **Sample size.** 4 negative claims is small. It shows the sign convention and the PV arithmetic work
  on these, not that they work everywhere.
- **Mate distance depth.** Claims here are mates in 3 and 4 (6 and 8 plies). Deeper negative mates are
  untested because the exhaustive reference becomes expensive.
- **Positions.** All from the G set's tail of lopsided positions, not middlegame mates.

## Evidence
- `out/lost_positions.json` — the 12 runs, with PVs.
- `lost_candidates.json` — the 16 candidate positions and the material filter that chose them.
- `NEGATIVE_MATE_ATTEMPT.md` — the three construction attempts that **failed** before I took the
  real-games route. Kept deliberately: they document why constructed endings do not produce negative
  mates (a defender with material has counterplay, so no forced mate exists).

Reproduce:
```
cd forge-combo29/swarm/13/job9
python3 negative_mates.py        # filters G for lost positions, searches both budgets, verifies
```
