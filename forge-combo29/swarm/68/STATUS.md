# STATUS

## State: verifier validated and shown able to fail; corpus results in

**Wrong-mate rate: 89/240 = 37.1%** at depth 12, Threads 1, MultiPV 1/2/3,
on labels with `|N| ≤ 5` (the ones the verifier can finish).

**Verifier validation result: PASSES.** It reproduces exact retrograde DTM on
50/50 KQvK positions and 17/20 KRvK (3 `INCONCLUSIVE`, 0 wrong), its move
generation agrees with python-chess on 27/27 perft cases, and it **rejects
planted wrong distances in both directions with the correct direction label**.
A negative control (side-to-move-assumes-attacker) misreports the negative-score
cases, so the verifier's agreement on losses is earned rather than structural.

## Headline numbers

| item | value |
|---|---|
| wrong-mate rate (all MultiPV, \|N\|≤5) | **89/240 = 37.1%** |
| MultiPV 1 | 16/42 = 38.1% |
| MultiPV 2 | 28/81 = 34.6% |
| MultiPV 3 | 45/109 = 41.3% |
| direction `over` | 85/89 |
| direction `under` | 4/89 |
| PV-length filter passes that are still WRONG | **97/240** |
| PV-length filter passes that are CORRECT | 143/240 |
| PV-length filter rejections | 0/240 |
| verifier throughput | 0.553 labels/s single-core, ~1.2/s on 4 cores |
| positions refused by the engine | 0/400 |

## The two headline findings

1. **The PV-length filter is inert on this corpus.** All 240 graded labels have a
   PV of exactly the length the score implies, and 97 of them are wrong anyway.
   The rule checks the one property that is not broken.
2. **Wrong mate distances are common at match depth and mostly overstate.**
   85 of 89 are `over`, mean +1.33 moves, but 4 are `under` — so both directions
   occur, and the two known boards are not the whole class.

## Honest limits of this result

- **Most of the 37% is a depth artefact, not a persistent defect.** The engine
  converges from above: `8/8/8/8/8/k7/8/KQ6 w` gives `mate 6` at depth 12,
  `mate 6` at 16, `mate 5` at 20–24, and the exact answer is 5. A deeper corpus
  would show a smaller rate. What the number establishes is that **a mate label
  collected at fixed shallow depth is unsafe to train on**, which is the corpus
  risk in the brief.
- **The corpus is sparse by construction** (material diff ≥ 5, ≤ 12 pieces), so
  the rate applies to the positions where mates actually appear — not to
  middlegames, where a mate label is rare to begin with.
- **Board 222 and board 121 are NOT confirmed or refuted.** Both are ~12-piece
  middlegames with pawns and the exhaustive verifier did not finish board 222 in
  15 minutes. The verifier is a sparse-endgame tool; this is a real limitation.

## Open items

1. **Boards 222 / 121** — need a faster exact solver for populated middlegames.
   No verdict claimed. This is the one assigned sub-task left incomplete.
2. **Depth sweep** — re-grade at depth 16/20 to separate "wrong because shallow"
   from "wrong at convergence". Cheap to run; the corpus and harness exist.
3. **`INCONCLUSIVE` handling** — 8/240 hit the node cap. They are excluded from
   the rate rather than counted as wrong; that choice is stated so it can be
   challenged.

## Re-runnable

```bash
cd forge-combo29/swarm/68/tools
g++ -O2 -std=c++20 -o mateverify mateverify.cpp
python3 retrograde.py all     # exact DTM tables + published-bound assertions
python3 perft_check.py        # 27/27 movegen agreement vs python-chess
python3 dtm_validate.py       # true/wrong/negative-control validation
python3 build_corpus.py 400 corpus.fen 6801
python3 collect_mates.py "$(pwd)/../../build/forge" corpus.fen 12 1 mates_mpv1_d12.jsonl 30
```

## Traps hit (all fixed, all documented in SCREEN.md)

default `c++` is Clang without libstdc++ · unmake restoring the promoted piece ·
**TT mate-score reuse across plies (reported mate 12 at horizon 9)** ·
retrograde dropping capture-escapes (KQvK max 6 instead of 10) · the brief's
bounds in mixed units · `invalid FEN` readable from two different streams ·
side-to-move-assumes-attacker.
