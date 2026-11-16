# REPORT — seat 25, area 5, job 1 THIRD RUN (seed 2521) + systematic mate-score classification

## What was asked
Cycle step (c) again: job 1 with the next seed (2521) and a new position set R3. Plus, this time, the
question the first two runs left open: when a mate PV is wrong, is the SCORE wrong too, or only the line?

## The answer
250 searches on R3: 0 illegal PVs, 6 mate scores, and **all 6 PVs are correct** (they end in checkmate at
exactly the claimed distance). So the defect is not common — about 1 in 10 mate scores across my three sets.
Applying the classifier to the two sets that DID have a bad PV settles the question: in BOTH cases the score
itself is wrong, and the engine's own deeper search proves it.

| set | records | mate scores | PV correct | SCORE WRONG |
|---|---|---|---|---|
| G (endgames/games) | 353 | 10 | 9 | **1** |
| R2 (seed 2511) | 250 | 12 | 11 | **1** |
| R3 (seed 2521) | 250 | 6 | 6 | 0 |

## How sure
Very sure. For each "SCORE WRONG" the evidence is: the depth-12 PV does not checkmate; the depth-24 search
of the SAME position claims a DIFFERENT mate number; and that deeper PV replays in python-chess to a real
checkmate at exactly the distance it claims. Both cases checked that way.

## The two proven instances
**S-F1** `8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1`: depth 12 says `mate -12` (24 plies), PV 18 plies, not mate.
Depth 24 says `mate -4`, PV 8 plies, verified checkmate. **Wrong by 8 moves.**

**S-F8** `2b2knr/2qpp3/1r2n1pb/p4pP1/4PPQp/3P3P/PP1KB3/1qB3NR w - - 0 22`: depth 12 says `mate -9`
(18 plies), PV 15 plies, not mate. Depth 24 says `mate -7`, PV
`g1f3 f5g4 h1d1 g4f3 d2e1 f3e2 e1e2 c7c1 d1c1 b6b2 c1c2 b1c2 e2f3 c2e2` = 14 plies, verified checkmate.
**Wrong by 2 moves**, on a MIDDLEGAME position (so not an endgame-only artefact).

Shows again:
```bash
python3 forge-combo29/swarm/25/job1c/classify_mates.py forge-combo29/swarm/25/job1b/R2_d12.jsonl /path/to/forge
```

## Predictions, scored
| id | prediction | outcome |
|---|---|---|
| R1 | 250 searches | HELD |
| R2 | 0 illegal PVs | HELD |
| R3 | 5..20 mate scores | HELD (6) |
| R4 | 1..4 bad mate PVs | **KILLED** — 0 bad PVs on R3 |
| R5 | at least half the bad ones are SCORE_WRONG | HELD — 2 of 2 across the other sets |
| R6 | >= 80% of deep mate PVs checkmate at the claimed distance | HELD — 2 of 2 deep PVs verified |

R4 was killed by a lucky/unlucky sample: R3 simply had no bad PV. The rate across all three sets is
2 bad among 28 mate scores (~7%), so predicting 1..4 per 250 positions was optimistic.

## Measurement discipline
- `--expect-records=250` asserted on the checker; it exits 3 on empty input or an unparsed score.
- Every mate score classified; no record left UNRESOLVED.
- The classifier re-searches with `ucinewgame` before the search on a FRESH process, so it is cold
  (`../audit/warm_cold_audit.txt` proves ucinewgame is cold on this build).

## What I did NOT do
- Did not chase the cause in the source (that is area 7's job; I located candidate lines only, as a suspicion).
- Did not test whether the wrong score ever appears at depth 20+ (all my evidence is depth 12 vs 24).
- No sanitizer run here.

## What I am NOT sure about
- The real rate. 2 of 28 is a small sample; the true rate could be 3% or 20%.
- Whether the fault is in the search or in the score-to-`mate N` conversion (a hypothesis with a location,
  src/search.cpp:179-198 and :272-279, but no proof).

## Times
see `stamps.txt`.

## Is the wrong score a state artefact? No — decided in one run (`score_wrong_state.py`)

| case | fresh process, d12 only | d12, ucinewgame, d12 | d24 FIRST, then ucinewgame, d12 |
|---|---|---|---|
| S-F1 | `mate -12`, 18-ply PV | `-12`, `-12` | d24 gives `-4`; then d12 gives **`-12`** |
| S-F8 | `mate -9`, 15-ply PV | `-9`, `-9` | d24 gives `-7`; then d12 gives **`-9`** |

Three things follow, and they matter:
1. The wrong score appears in a FRESH process with no `ucinewgame` and nothing before the search, so it is not
   caused by prior state or by a warm TT.
2. `ucinewgame` restores it exactly (twice), so it is deterministic.
3. **The most telling line:** run depth 24 FIRST — the engine finds the correct `mate -4`/`-7` — then
   `ucinewgame`, then depth 12 — and it goes BACK to the wrong `mate -12`/`-9` in the same process that just
   had the right answer. A correct, deeper result one search earlier does not survive into the shallower one.

Point 3 is why I call this a search/reporting defect rather than a knowledge problem: the engine can find the
truth at depth 24 and still reports the wrong number at depth 12, immediately afterwards, from the same binary.

## Still NOT the cause
I did not patch or bisect the search. The candidate site remains the mate-band arithmetic
(`score_to_tt`/`score_from_tt` against `MateInMaxPly`, src/search.cpp:179-198, and `format_score`,
:272-279). Naming it is a hypothesis; the evidence above is the finding.
