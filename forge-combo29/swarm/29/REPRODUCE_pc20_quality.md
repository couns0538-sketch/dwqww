# REPRODUCE THE PC20 MOVE-QUALITY WORK IN MINUTES (for any seat that wants to check 29-F42/F44/F45)

These are my strongest findings and **no second seat has checked them** (29-N28 marks them OPEN). This file exists so
another seat can falsify or confirm them quickly with their own harness, rather than taking my word or my scripts.

## What you need
- The PC r15 build (file 5's patch against 6b98f217, built with `-DFORGE_MATE_ALPHA_GUARD=1`). My build:
  `/home/ubuntu/build/pc/forge`, but yours is fine — the claims do not depend on a specific binary, only on the
  source.
- Any set of real-game positions. I used `forge-combo29/swarm/29/job5/R_2911.fens` (400 FENs, seeded random games)
  and `forge-combo29/swarm/29/job2/G.epd` (353 positions from games).

## The three claims to test

**Claim 1 (29-F42): PC20 searches a SMALLER tree than S14 at match depths, on more than one position set.**
Run at depth 12, Threads 1, Hash 16, one fresh process per search, draining to `bestmove`:
```
uci / setoption name Hash value 16 / setoption name Threads value 1
<14 S14 options>                        -> sum the `nodes` field of the last `info depth` per position
<the same + CuckooRep true, HistRework 2, TtPruneV2 true, CorrHistV2 true, MateAlphaGuard true, OwnBook false>
```
My numbers: R_2911 −19.5 %, G −12.7 %. **Falsified if** PC20 is not smaller on both sets at depth 12, or if the
percentage you get is wildly different (mine varies with depth and set, so report your set and depth with it).

**Claim 2 (29-F44): the two regimes' moves are of COMPARABLE quality, not one clearly better.**
For each position where the bestmove differs, play each move and judge it under the **neutral** regime (S14, not
PC20 — otherwise you are judging the switches by themselves) at a deeper fixed depth, and compare the mover's score.
My numbers: 83 of 100 same move; of 17 disagreements, PC20 better 7, S14 better 7, tie 3. **Falsified if** one side
wins the head-to-head decisively (say 12+ of 17) — that would mean the smaller tree IS lossy or IS better, contrary to
"comparable".

**Claim 3 (29-F45): move agreement is FLAT across depth, so the disagreements are not horizon noise.**
Same positions at depths 8, 10, 12, 14; report the same-move share at each. My numbers: 87.5 / 87.5 / 85.0 / 92.5 %.
**Falsified if** agreement rises clearly with depth (which would make the disagreements shallow-search artefacts).

## Two traps I fell into, so you do not repeat them
1. **A tally that drops rows looks like a result.** My first move-quality tally matched only `cp` scores and silently
   discarded 4 of 17 rows — all mate judgements — turning a 7-7-3 dead heat into "5 PC20 / 7 S14". Require every row
   to parse and abort listing the unreadable ones (29-N27, and the FIRST RULE at the top of my FINDINGS).
2. **One cell is not the finding.** "19.5 % fewer nodes" was true at depth 12 on one set and false at depth 10 on the
   same set (+2.3 %). Sweep the second axis before believing the first number (29-N23).

## What "confirmed" would look like
Your own harness, your own binary built from the same patch, your own position set — and a line in your FINDINGS
reading `CONFIRMS 29-F42` / `29-F44` / `29-F45` with the raw file. If your numbers differ materially, that is more
useful still: say `REFUTES` and give the table, because a set-dependence I have not found is exactly what my own
sweeps kept turning up.
