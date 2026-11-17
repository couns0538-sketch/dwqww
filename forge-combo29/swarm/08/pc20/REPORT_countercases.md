# The two counter-cases: probed, and they remain UNEXPLAINED — seat 08

The coordinator's suggestion was sharp: if the cap does not fire on the two boards where cap-OFF visits *more* nodes,
they are not counter-examples at all and the rule gets cleaner; if it does fire, there is a second mechanism.

**I probed it. The cap fires everywhere. The counter-cases are not explained.**

## The gate, read from the patch (lines ~1563-1574)

```c
const bool bare_king_rule = multi_worker || root_bare_king_;   // ONE_THREAD=1 adds root_bare_king_
const bool bare_king_mode = bare_king_rule &&
    (board.occupied(White) == board.pieces(White, King) ||
     board.occupied(Black) == board.pieces(Black, King));
const bool bare_king_lmr_cap = !bare_king_mode && root_bare_king_ &&
    (board.occupied(White) == board.pieces(White, King) ||
     board.occupied(Black) == board.pieces(Black, King));
```

So the cap fires at a node only when the **root** has a lone king (all 11 boards do) **and** that node has a side with
only its king.

## The measurement (exact legal tree to depth 4, python-chess)

| board | cap-OFF Δ nodes | lone-king node fraction |
|---|---|---|
| 8/8/2B1k3/8/3PP3/P7/4K3/7R b | −9,980 | **100.0 %** |
| 8/8/2k5/4P3/3P4/P7/4K3/7R w | −9,428 | **100.0 %** |
| **8/2k5/4P3/8/3P4/PR6/3K4/8 b** | **+10,981** | **100.0 %** |
| 8/4k3/8/6R1/8/P7/3K4/8 b | −14,040 | **100.0 %** |
| 1R6/8/k7/8/8/P7/8/2K5 b | −7,526 | **100.0 %** |
| **8/8/8/4R3/2k5/P7/8/2K5 w** | **+621** | **100.0 %** |
| 8/8/8/1R6/1K6/P7/3k4/8 b | −6,547 | **100.0 %** |
| 8/8/P7/8/8/4K3/1k6/8 b | −3,356 | **100.0 %** |
| 6K1/2b5/p1k5/8/8/8/8/b7 b | −9,605 | **100.0 %** |
| 8/2k5/p7/8/8/7K/1b6/b7 w | −13,946 | **100.0 %** |
| 2k5/8/p7/6b1/8/2b4K/8/8 b | −8,191 | **100.0 %** |

| class | boards | median lone-king node fraction |
|---|---|---|
| cap-OFF fewer (predicted) | 9 | **100.0 %** |
| cap-OFF MORE (counter-case) | 2 | **100.0 %** |

## Verdict: the gate explanation does NOT hold

**Every node in every one of the 11 trees satisfies the lone-king condition** — which makes sense: with a king plus
one or two pieces, the lone side stays lone for the first four plies unless a pawn promotes, and none of these have a
promoting pawn within four plies. So the gate is active almost everywhere in all eleven boards and **cannot
distinguish the counter-cases**.

Therefore the counter-cases are **not** explained by "the cap has less to act on there". They arise from something
else — most plausibly an interaction between the clamped reductions and the rest of the pruning cascade, which can go
either way board by board because a changed reduction changes which nodes are visited, and which nodes are visited
changes what the search learns.

**That is a second mechanism, as the coordinator anticipated, and I am not able to characterise it from outside the
engine.** Characterising it would need reduction counters inside the search (a patched build printing `r` per depth),
which is seat 03's or seat 21's territory rather than a clock seat's, and would be a text patch rather than a
measurement.

## What this leaves, precisely stated
- **Established:** `BARE_KING_LMR_CAP` alone causes all 11 move divergences (08-F37, 11 of 11 restored with it off);
  turning it off reduces the node count on 9 of 11 boards (08-F38).
- **Not established:** why 2 boards go the other way. Named as an open second mechanism, not folded into the rule and
  not explained away by a firing-rate difference that the data does not show.
- The **strong tendency** statement in 08-F38 stands unchanged: it is the correct summary precisely because it carries
  the counter-cases rather than excluding them.

## Show it again

    cd forge-combo29/swarm/08/pc20 && python3 countercase_probe.py /tmp/cc.txt
