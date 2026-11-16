# seat 20 — job 24: the 10.0 % vs 28.6 % question is RESOLVED — seat 06 is right, my sample was unrepresentative

## Answer first

I ran **seat 06's own 353 G positions** with **their own stated settings**. I reproduce their numbers **exactly, to
the unit**: **101/353 bestmove-asymmetric (28.6 %)** and **334/353 score-asymmetric (94.6 %)**. My job19 figure of
2/20 (10.0 %) was a property of my 20-position sample, not a disagreement with their measurement. There is **no
conflict**, and nothing of theirs needs defending.

## The exact conditions of my original measurement (job19) — for the record, since it was put to them

| condition | job19 (my 10.0 %) | seat 06 (their 28.6 %) |
|---|---|---|
| position set | **my own** seeded walk, `Random(2001)`, one position every 5 plies | **G_353.fens**, 353 positions from games |
| size | **20** | 353 |
| depth | 10 | 10 |
| options | S14 (14 setoptions), OwnBook false | S14 (14 setoptions), OwnBook false |
| `Threads` / `Hash` | **defaults: Threads 1, Hash 32** | **Threads 1, Hash 16** |
| process discipline | **fresh process per search** | one process, `ucinewgame` + `isready` before every `go` |
| comparison | mirror(bestmove P) vs bestmove M; score P vs score M | same two rules (`analyse_search.py`: `expect = mirror_uci(bm_s)`, `a != b`) |
| result | 2/20 = 10.0 % (Wilson 95 % CI ≈ 1–32 %) | 101/353 = 28.6 % (Wilson 95 % CI 24.1–33.5 %) |

Note the Hash difference (32 vs 16) and the set size. My 2/20 has a confidence interval so wide (roughly 1–32 %)
that it **overlaps 28.6 % comfortably** — it was never evidence against their rate, and I should have said so in
job19 instead of offering a "rate not reproduced" reading.

## The reproduction (job24), on their data, their settings

Settings applied exactly as their report states: depth 10, S14 (14 options), `Threads 1`, `Hash 16`, `OwnBook
false`. Two process-discipline arms, to test whether that mattered:

| arm | bestmove asymmetric | score asymmetric |
|---|---|---|
| **fresh process per search** (my job19 discipline) | **101/353 = 28.6 %** (CI 24.1–33.5 %) | **334/353 = 94.6 %** |
| **one process, `ucinewgame` before each `go`** (their reported discipline) | **101/353 = 28.6 %** (CI 24.1–33.5 %) | **334/353 = 94.6 %** |

The two arms agree **row by row**: 0 of 353 positions differ between them in bestmove or in symmetry verdict. So
process discipline is irrelevant here (consistent with my S-F25), and Hash 32 vs 16 does not change their set's
rate either at this depth.

Raw: `repro_s06f6_fresh.json`, `repro_s06f6_shared.json` (every row, both arms). Script: `repro_s06f6.py`.
`G_353.fens` copied byte-for-byte from `for-fable-and-opus/swarm-06:forge-combo29/swarm/06/job3/G_353.fens`.

## What I withdraw

The **"rate NOT reproduced"** reading of my S-C13 line. What stands from job19 is only this: on my own 20-position
sample the rate was 10.0 %, which is compatible with 28.6 % given n=20, and seat 06's claim is correct on the set
they named, reproduced by an independent harness. I will add a correction line rather than edit the original, since
FINDINGS is only ever added to.

## What this does NOT change
- `eval` remains exactly colour-symmetric (my S-C6, 360/360 pairs, 0 difference) — so the asymmetry enters through
  the search, exactly as seat 06's S-F7/S-F8 argue.
- Their two mate observations (S-F9 → closed by their own S-F11) are untouched by this.
- Nothing here bears on my S-F22/S-F18 (mate distance and S14 sensitivity): those are single-position proofs.
