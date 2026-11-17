# The seed-902 replication: the 37 % rate is NOT ESTABLISHED — seat 08

## The strongest actable claim in this line, first

| class | mate-involved targets | boards |
|---|---|---|
| **sparse (≤12 pieces)** | **13** | **56** |
| **full-material / real-game (≥20 pieces)** | **0** | **60** |

Across two independent samples of positions, a self-play target that is a cp evaluation of a position whose deeper
search finds a FORCED MATE occurred **13 times in 56 sparse boards and never in 60 full-material boards.** Both
denominators are the usable boards, both samples, no pooling of rates. That split — not any percentage — is the
result to act on: the risk is confined to the sparse class, and in the full-material class where real games mostly
live it did not appear at all in 60 boards.

## The two samples

| sample | sparse boards | mate appeared | rate | 95 % Wilson interval |
|---|---|---|---|---|
| R seed 801 (the hand-picked shape classes of 08-F28) | 27 | **10** | **37.0 %** | 21.5 % to 55.8 % |
| **R seed 902 (independent, random legal games)** | 29 | **3** | **10.3 %** | 3.6 % to 26.4 % |

| sample | "either" (mate OR ≥200 cp) | rate | 95 % Wilson |
|---|---|---|---|
| R seed 801 | 10 of 27 | 37.0 % | 21.5 % to 55.8 % |
| R seed 902 | 5 of 29 | 17.2 % | 7.6 % to 34.5 % |

| full-material class, both samples | mates | ≥200 cp |
|---|---|---|
| R seed 801 | **0 of 30** | 0 of 30 |
| R seed 902 | **0 of 30** | 0 of 30 |

## What I say, in the terms I fixed in advance

**The rate is NOT ESTABLISHED.** The point estimates differ by 3.6x (37 % against 10.3 %), which is outside the
±15-point window I committed to; I am not averaging them into one figure, not reporting the better-looking one, and
not calling the difference "sampling noise" without the intervals.

Both intervals overlap (21.5–55.8 % and 3.6–26.4 %), so I cannot claim the two samples disagree statistically at
this size — but overlap of two wide intervals is not agreement either, and 27/29 boards cannot resolve a factor of
3.6. What can be said is the thing both samples DO agree on, which is not the rate:

| claim | status |
|---|---|
| the sparse class contains boards where the clocked score is a cp evaluation of a position whose deeper search finds a mate | **DIRECTION, both samples: 10/27 and 3/29** |
| the full-material / real-game class contains no such boards | **0 of 60 across both samples — the strongest single result here** |
| "37 % of sparse self-play targets are wrong in kind" | **NOT ESTABLISHED — withdrawn as a rate** |
| "about 1 in 6 to 1 in 3" (pooled 13 of 56) | **NOT quoted — pooling two samples that differ 3.6x would manufacture precision** |

## Why the difference is plausible rather than mysterious

The two sparse sets are not the same kind of position. Seed 801's boards were selected by me to fill the
"few pieces, few moves" class from R, and several were near-mate endings (two showed `mate 9`-ish lines within four
plies). Seed 902's are whatever random legal games produced with ≤12 pieces — mostly quiet endgames with a rook and
pawns, where four extra plies rarely turns a cp score into a mate. **So the 37 % is best read as a property of
THAT KIND of sparse position (few pieces AND few moves, often already near a mate), not of "sparse" in general.**
That is a guess about the cause, stated as a guess: I did not classify the seed-902 boards by "nearness to mate".

## What the owner can act on, stated without a rate

- If his self-play uses **full-material real-game positions**: both samples found **0 of 60** materially-wrong-in-kind
  targets. That is the strongest and most consistent result of the whole exercise, and it is a rate he can rely on
  to the extent 60 boards allow.
- If it uses **sparse endgames**: such boards CAN produce a target that is a cp score for a position that is
  actually a forced mate — 13 of 56 across two samples did — but how often depends on how near-mate those endgames
  already are, and I could not establish a stable rate. Treat that class as needing spot-checking rather than
  assuming a percentage.
- Either way, the **mate-involved** cases are the ones to look for, not centipawn drift: the cp-only movement was
  median 14-25 cp in both samples, i.e. unremarkable.

## Show it again

    cd forge-combo29/swarm/08/pc20 && VOL_R=./R_seed902.fens python3 volatility_rate.py /tmp/v902.txt 30
    # rows: /tmp/v902.txt.jsonl
