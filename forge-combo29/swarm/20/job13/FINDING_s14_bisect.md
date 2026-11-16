# seat 20 — job 13: which S14 option causes the mate-distance error?

Answer: **none alone, and not one pair either — it is an interaction between the search-shape options
(`NullMoveBase`, `LmpBase`, `IirDepth`), and the effect is non-monotone.** The all-S14 answer (`mate -12`, 18 plies)
is not reproduced by any single option, by any pair, or even by the triple `NullMoveBase=5 + LmpBase=8 + IirDepth=2`
(which gives `mate -9`, 15 plies). So the mate-distance error is a property of the *whole* S14 move-ordering /
pruning configuration, not of one knob.

Raw: `out_bisect.txt`, `out_pairwise.txt`, `bisect_s14.json`, `pairwise_s14.json`. Scripts: `bisect_s14.py`,
`pairwise_s14.py`. Build `/agent/repos/build-base/forge` sha256 `e06310ec…` (4/4 pins).
Board `8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1`, `go depth 12`, python-chess replayed every PV.

## Single options (all others default)

| option applied alone | score | PV | verdict |
|---|---|---|---|
| **DEFAULT, run 1** | mate −7 | 14 | CONSISTENT (mate in exactly 14) |
| **DEFAULT, run 2** | mate −7 | 14 | CONSISTENT (deterministic) |
| LmrQuietBase=93 | mate −7 | 14 | consistent |
| LmrQuietDivisor=205 | mate −7 | 14 | consistent |
| LmrNoisyBase=13 | mate −7 | 14 | consistent |
| LmrNoisyDivisor=333 | mate −7 | 14 | consistent |
| LmrHistoryDivisor=5643 | mate −7 | 14 | consistent |
| **NullMoveBase=5** (default 3) | **mate −9** | 17 | TRUNCATED 17/18 |
| **LmpBase=8** (default 4) | **cp −3114** | 20 | mate lost entirely |
| HistoryPruneMultiplier=2220 | mate −7 | 14 | consistent |
| HistoryBonusQuadratic=24 | mate −6 | 12 | consistent (12 plies, verified) |
| HistoryBonusLinear=54 | mate −7 | 14 | consistent |
| HistoryBonusMax=2212 | mate −7 | 14 | consistent |
| SingularDepth=6 | mate −7 | 14 | consistent |
| **IirDepth=2** (default 4) | **mate −8** | 15 | TRUNCATED 15/16 |
| NonPawnCorrection=true | mate −7 | 14 | consistent |
| **ALL S14** | **mate −12** | 18 | TRUNCATED 18/24 |

Three single options break the mate answer: `NullMoveBase=5`, `LmpBase=8` (which loses the mate score completely),
`IirDepth=2`. **Ten of the fourteen options are inert on this position.**

## Pairs of the three culprits

| options | score | PV | verdict |
|---|---|---|---|
| NullMoveBase=5 | mate −9 | 17 | truncated 17/18 |
| LmpBase=8 | cp −3114 | 20 | mate lost |
| IirDepth=2 | mate −8 | 15 | truncated 15/16 |
| NullMoveBase=5 + LmpBase=8 | mate −8 | 15 | truncated 15/16 |
| **NullMoveBase=5 + IirDepth=2** | **mate −15** | 16 | truncated 16/30 |
| **LmpBase=8 + IirDepth=2** | **mate −13** | 17 | truncated 17/26 |
| NullMoveBase=5 + LmpBase=8 + IirDepth=2 | mate −9 | 15 | truncated 15/18 |
| DEFAULT | mate −7 | 14 | **consistent** |

Non-monotone: the triple is *better* (mate −9) than two of the pairs (mate −15, mate −13). More aggressive pruning
in a different combination produces a *longer* claimed mate, not a shorter one. The pair `NullMoveBase=5 +
IirDepth=2` claims 30 plies of mate in a 16-ply line — the worst line I produced.

## What this means for the PC
1. The mate score itself is intact: with defaults every PV verifies as a real checkmate in exactly the claimed
   number of plies, so "mate detection is broken" is the wrong conclusion.
2. What breaks under S14 is the **reported distance** (and under `LmpBase=8` alone, the mate score entirely,
   replaced by `cp −3114`). That is a search-shape effect: pruning changes which defensive resource the engine
   sees first, so `mate N` at a fixed depth is not stable.
3. The honest conclusion for anyone testing mate distances: **pin the tuning** and state it. A `mate N` value at
   depth D is a statement about that configuration, not about the engine.

### Suspicions, not proven
- That `LmpBase=8` losing the mate entirely is the most serious of the three, because it is a wrong *evaluation*,
  not only a wrong distance. I did not chase it further (one position, one depth).
- That the non-monotonicity comes from different move orderings at the root between combinations. Plausible, not
  demonstrated — proving it needs per-move ordering dumps.

## What I did NOT do
- I did not bisect the remaining 11 options in combination, nor test pairs among the ten inert ones.
- I did not test other positions or depths; every row here is one board at depth 12.
- `LmpBase=8` losing the mate deserves its own job and did not get one.

## What I am NOT sure about
- Whether the true mate distance on this board is 14 plies (the default's verified answer) or shorter. A
  verified PV proves "at most", never "exactly".

## Commands that show it again
```
python3 bisect_s14.py /agent/repos/build-base/forge /tmp/o      # the 14 single options
python3 pairwise_s14.py /agent/repos/build-base/forge /tmp/o    # the pairs
```
