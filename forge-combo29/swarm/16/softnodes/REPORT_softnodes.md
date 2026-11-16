# REPORT_softnodes — `go softnodes N` on the PC build under PC20, Threads 1 (the owner's self-play path)

**What was asked (FABLE_TO_swarm_6, new area suggestion):** is `go softnodes N` deterministic run to run, does it
stop at a finished depth, and how far past N does it go? This is the owner's SELF-PLAY path (`go softnodes 2000`),
so it matters more than any UCI edge case.

**The answer: DETERMINISTIC (1 distinct result in 20 runs, every budget, every position — P1 and P2 confirmed),
STOPS AT A FINISHED DEPTH (20/20, 5/5, 5/5 — P2 confirmed), but the OVERSHOOT IS MUCH LARGER THAN I PREDICTED:
up to 2.06x the budget at N=2000 (P3 refuted).**

```
budget   n   overshoot range        median   determinism        finished-depth
  2000   4   1.157x .. 2.061x       1.656x   1/1 result (20 runs) 20/20 every position
 20000   4   1.054x .. 1.589x       1.203x   1/1 result (5 runs)   5/5
 50000   4   1.016x .. 1.584x       1.572x   1/1 result (5 runs)   5/5
```

So at the PC's self-play budget of 2,000 nodes the engine actually searches **between 2,314 and 4,121 nodes** —
up to **twice** the budget. The depth that crosses the budget is always finished (so the answer is clean), but
for a self-play loop that counts on ~2,000 nodes per move the real cost is 1.16x–2.06x.

**P3 was refuted, and P4 too:** I predicted a 10–60 % overshoot at N=2000 (actual 15.7 %–106 %) and predicted the
fraction would not GROW with N (actual: N=50000 has a 58 % overshoot on one position, higher than N=20000's 59 %
maximum but on a different position). The honest statement is: the overshoot depends on how coarse the depth
ladder is at that budget, not on N.

**P5 confirmed:** `go nodes 20000/50000/250000` are also deterministic — 1 distinct result over 5 runs each, all
four positions.

**What this means for the owner's PC.** Self-play at `go softnodes 2000` is REPRODUCIBLE (good: games can be
replayed) but each move costs up to 2x the nominal node budget (a real cost, worth knowing when timing or
counting self-play work). It does not mean a wrong move: the reported bestmove is always the PV's first move of
a completed depth.

## Honesty numbers

```
exe     /home/ubuntu/builds/bld-pc/forge   PC r15, -DFORGE_MATE_ALPHA_GUARD=1
        sha256 068f0927768d30be60e8cce6c9f29620dec330565397357dccc9e0fe361e32f4
        none 312866 / 862329 / 3024920 / 4865609     S14 242796 / 656517     PC20 278024 / 587276  (all match file 5)
settings PC20 (S14 + CuckooRep true, HistRework 2, TtPruneV2 true, CorrHistV2 true, MateAlphaGuard true,
         OwnBook false) + Threads 1 + Hash 16     <- Threads 1 throughout, per the swarm rule
positions: startpos + the first three G positions (real-game positions)
```

## Table

| step | done-partly-not done | evidence file | result |
|---|---|---|---|
| determinism, 20 runs at N=2000, 4 positions | done | `run.log`, `raw/softnodes.txt` | 1 distinct result each — deterministic |
| determinism at N=20000 / 50000, 5 runs | done | same | 1 distinct result each |
| stops at a finished depth | done | same (`finished-depth` column) | 20/20, 5/5, 5/5 — bestmove always the last depth's PV head |
| overshoot measurement (P3) | done — prediction WRONG | same | 1.157x–2.061x at N=2000, far above my predicted 1.1–1.6x |
| `go nodes` at 20000/50000/250000, determinism | done | same | 1 distinct result over 5 runs each |
| the clock path (`go wtime ... winc ...`) | NOT done | — | different limit type; area 8's territory |
| more than 4 positions | NOT done | — | 4 positions × 3 budgets × up to 20 reps was the time budget |

## Findings

`S-F16 | 6 | PC r15, PC20, Threads 1: `go softnodes N` is fully DETERMINISTIC (1 distinct bestmove/score/nodes over 20 runs at N=2000 and 5 runs at 20000/50000, on 4 positions including startpos) and always stops at a FINISHED depth, but it overshoots the budget by up to 2.06x — at the owner's self-play budget of 2000 nodes the search runs 2,314 to 4,121 nodes across four positions (median 1.66x); `go nodes` at 20000/50000/250000 is equally deterministic | softnodes/run.log (again: `python3 softnodes/softnodes_test.py ~/builds/bld-pc/forge /tmp/o`) | NEW |`

## Suspicions, not proven

- That the overshoot is bounded at ~2x for ALL positions at N=2000. Four positions cannot prove a bound; the
  mechanism (finish the crossing depth) implies the bound is set by the cost of one depth step, which varies.
- That the PC's self-play loop does not care. It may have been measured with the overshoot in mind.

## What I did NOT do

- Did not test the clock path (`go wtime/btime/winc`), which is the PC's match path and a different limit type.
- Did not test `go movetime`, `go depth` interaction, or `stop` during a softnodes search.
- Did not vary Hash, since the PC's self-play uses Hash 16.

## What I am NOT sure about

- Whether a deeper ladder position (a quiet position where one depth costs many nodes) could overshoot 2x. My
  four positions top out at 2.061x, which is close to twice, and one more quiet position could exceed it.

## Times

`softnodes/stamps.txt`, every line a `date -u`.
