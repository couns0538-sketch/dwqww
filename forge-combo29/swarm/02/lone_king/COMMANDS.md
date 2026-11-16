# Exact command lines for the lone-king board, and the free-choice answer

Board: `1r6/5b2/2K5/8/8/5n2/5k2/8 w - - 18 183` — White (side to move) has a bare king, 1 man against 4.

## 1. the exact option sequence (PC r15 + PC20), in the order sent

```
uci
isready
setoption name Threads value 1
setoption name Hash value 16
setoption name LmrQuietBase value 93
setoption name LmrQuietDivisor value 205
setoption name LmrNoisyBase value 13
setoption name LmrNoisyDivisor value 333
setoption name LmrHistoryDivisor value 5643
setoption name NullMoveBase value 5
setoption name LmpBase value 8
setoption name HistoryPruneMultiplier value 2220
setoption name HistoryBonusQuadratic value 24
setoption name HistoryBonusLinear value 54
setoption name HistoryBonusMax value 2212
setoption name SingularDepth value 6
setoption name IirDepth value 2
setoption name NonPawnCorrection value true
setoption name CuckooRep value true
setoption name HistRework value 2
setoption name TtPruneV2 value true
setoption name CorrHistV2 value true
setoption name MateAlphaGuard value true
setoption name OwnBook value false
isready
position fen 1r6/5b2/2K5/8/8/5n2/5k2/8 w - - 18 183
isready
```

Then, per search, exactly one of:

## 2. the searchmoves form (one move per run, fresh process each)
```
go depth 20 searchmoves c6d7
go depth 20 searchmoves c6c7
go depth 20 searchmoves c6d6
go depth 20 searchmoves c6c5
```
depths 16 and 18 identical with the depth changed. Every search is the FIRST of a fresh process, so it is cold;
the driver reads to `bestmove` before closing stdin (a piped run triggers 19-F12's fabricated bestmove).

On the base build the same commands are used with **S14 in place of PC20** (the base build answers
`unknown option CuckooRep` and friends for the PC20 switches, which aborts):
```
setoption name Threads value 1
setoption name Hash value 16
setoption name LmrQuietBase value 93
setoption name LmrQuietDivisor value 205
setoption name LmrNoisyBase value 13
setoption name LmrNoisyDivisor value 333
setoption name LmrHistoryDivisor value 5643
setoption name NullMoveBase value 5
setoption name LmpBase value 8
setoption name HistoryPruneMultiplier value 2220
setoption name HistoryBonusQuadratic value 24
setoption name HistoryBonusLinear value 54
setoption name HistoryBonusMax value 2212
setoption name SingularDepth value 6
setoption name IirDepth value 2
setoption name NonPawnCorrection value true
setoption name OwnBook value false
```

## 3. THE FREE-CHOICE RESULT (no searchmoves), depth 20, two runs, identical

```
go depth 20
```

```
info depth 20 seldepth 37 score mate -10 nodes 165764722 nps 2478539 hashfull 1000 time 66880 \
  pv c6c7 b8b3 c7d6 b3c3 d6e7 f7b3 e7d6 f3h4 d6e7 f2g3 e7f6 c3c6 f6e7 h4f5 e7d7 c6c3 d7d8 b3e6 d8e8 c3c8
bestmove c6c7
```
Run 2: identical — `mate -10`, nodes 165764722, `bestmove c6c7`, 67100 ms.

**The PV was fully replayed with python-chess: 20 of 20 plies legal, ending in CHECKMATE at exactly the claimed
distance.** So `mate -10` is a verified mate, not a bound.

## 4. the answer to the question, and it REVERSES the expected conclusion

The coordinator's question was: "is it `c6c7` at mate in 11 when `c6d6` is mate in 8? If so the finding survives
as a three-ply ordering flaw."

**It picks `c6c7`, and preferring it is CORRECT — this is not an ordering flaw.** The reason is the sign of the
score: **White is the side to move and White is LOST.** The score is from White's perspective, so `mate -8` means
"White is mated in 8" and `mate -10` means "White is mated in 10". A player who is lost wants to be mated **later**,
so **-10 is a BETTER score for White than -8**, and the engine is right to prefer `mate -10` to `mate -8`.

So the free choice is one of the mate-in-8 moves **only if you believe a shorter mate is better**, which is the
opposite of correct for the side that is being mated. The engine is choosing maximum resistance, which is exactly
what a losing side should do. Under the claim's own framing ("the engine should pick c6d6 because it is mate in 8")
the claim is REFUTED: mate in 8 is worse for White than mate in 10.

## 5. one thing my earlier table did NOT note, and it matters for comparison
The same position, same label depth 20, differs in actual effort between the two instruments:

| run | seldepth | nodes | score |
|---|---|---|---|
| `go depth 20 searchmoves c6c7` | **43** | 16,066,180 | mate -11 |
| `go depth 20` (free choice, picks c6c7) | **37** | 165,764,722 | mate -10 |

So `searchmoves c6c7` at depth 20 reached a much deeper selective search on a tenth of the nodes and reported a
**longer** mate (-11) than free choice did (-10). That is not a contradiction — a bound improves with more search,
and both are consistent with White surviving about 10-11 moves — but it does mean **scores from `searchmoves` and
from free choice are not interchangeable**, and my earlier comparison table should have said so. Anyone comparing
the two seats' numbers must match the instrument as well as the settings.

## 6. what I would ask the other seat for
1. their exact `setoption` sequence (I suspect PC20 vs S14 vs none, or a different Hash/Threads),
2. whether they used `searchmoves` or free choice, and at which `seldepth`/`nodes`,
3. their raw `info depth 20` line for the free choice, since the seldepth/nodes pair above shows two runs of the
   same nominal depth can differ by 10x in effort.
