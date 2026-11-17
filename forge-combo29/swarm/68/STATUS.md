# Swarm 68 — label-quality screen for mate scores

**Status: verifier NOT yet cleared to gate anything.** It is validated on move
generation (27/27 perft cases against python-chess) and it demonstrably rejects
wrong `N` in both directions. But it disagrees with an independent retrograde
table on small KQvK endgames (28/40 agreement), so its DTM numbers are not
trustworthy yet. The disagreement is unresolved and is being worked; no
wrong-mate rate will be reported until it is.

## Ground truth established

`retrograde.py` computes exact DTM for **every** legal KQvK and KRvK position by
backward induction, and asserts the published bounds:

| class | states | resolved | max DTM (winner) | published |
|---|---|---|---|---|
| KQvK | 368,452 | 345,404 | 19 plies = 10 moves | 10 moves — ok |
| KRvK | 399,112 | 376,868 | 31 plies = 16 moves | 31 plies — ok |

Note the brief's bounds mix units: KQvK is 10 **moves** (19 plies) and KRvK is
31 **plies** (16 moves). The table asserts both numbers explicitly.

Re-runnable: `python3 retrograde.py all` (writes `kqvk_dtm.json`, `krvk_dtm.json`).

The bound assertion is load-bearing. A first version dropped states where the
strong piece could be captured, silently deleting the weak king's best defence
(take the undefended queen → KvK draw). It reported a KQvK maximum of 6 moves and
**zero** drawn positions, both impossible. The assertion caught it.

## Move generation

`mateverify` is an independent C++ program: own mailbox→bitboard board, own move
generation, own search. It links no engine code.

`python3 perft_check.py` → **27/27** agree with python-chess (7 published perft
positions + 20 hand-picked and random endgames). Two real bugs were found this
way and fixed:

1. **Unmake restored the promoted piece instead of the pawn.** `d7c8=Q` put a
   queen back on `d7` on unmake, corrupting every position after it.
2. A hardcoded expectation of `89879` for position 6 was itself wrong; the
   verifier's `89890` is correct and python-chess agrees. The fixture was the
   fault, not the code — recorded because an expectation typed from memory is a
   fixture that can be wrong.

## What is proven about the verifier

- **It rejects a wrong `N` in both directions.** Fed `mate 8` where the truth is
  `mate 10`: `WRONG / under`. Fed `mate 12` where the truth is `mate 10`:
  `WRONG / over`. So a "correct" verdict is not structurally unreachable.
- The attacker is resolved from the **sign** of the exact score and printed per
  result (`attacker_from: sign_of_exact_score`), so a negative label does not get
  the side-to-move-as-attacker bug.

## What is NOT proven yet

Verifier DTM vs the retrograde table agrees on only **28/40** sampled KQvK
positions with `|DTM| <= 11`; the verifier reports distances 2–6 plies **too
large**. Two independent implementations (the retrograde table, and a plain
python negamax) both say 10 plies for `8/8/7K/8/8/7k/2Q5/8 b - - 0 1`; the
verifier says 12. Perft passing but mate distances being wrong points at the
search, not move generation. This must be closed before any corpus verdict is
reported.

## Not started

- Engine mate-score corpus at a real match budget, Threads 1 (MultiPV 1/2/3).
- The two known boards (R5 222, R6 121).
- Positions/second throughput.
- The cheap cp-near-mate-horizon detector.

## Re-runnable commands

```bash
cd forge-combo29/swarm/68/tools
g++ -O2 -std=c++20 -o mateverify mateverify.cpp
python3 perft_check.py          # 27/27 movegen agreement
python3 retrograde.py all       # exact DTM tables + published-bound assertions
./mateverify --one "<FEN>" <N>  # one verdict
```
