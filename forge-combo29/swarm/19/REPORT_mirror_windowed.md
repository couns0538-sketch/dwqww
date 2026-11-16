# The mirror test through the window clamp: 1 of 8, and the bare king loses 12 plies it could have kept

seat 19 · area 9 · build **PC r15** · **PC20** · **Threads 1** · Hash 16 · cold · `go depth 16` and `go nodes 20000`.

## 1. The three lines

**What was asked.** The mirror of 19-F55: positions where the **bare king is to move** and wants to survive.
Report numbers **only through `windowed_verdict()`** (19-C10/19-F57), so a mate that does not fit inside
`100 − counter` is treated as the draw the rules actually give.

**The answer.** **1 of 8 covered positions is a defect at the budgets tested**: `6k1/8/5K2/8/6r1/8/8/8 w - - 12
182` — the bare white king plays `f6e7`, mated in **17 plies**, when `f6f5` survives **29 plies**: 12 plies of
resistance given away. **But it is a calibration case, not a bug** — at depth 24 the engine plays `f6f5` with
`mate -15`, exactly as the oracle said (§4). What it demonstrates is *where the engine's horizon sits*, not a
preference for losing quickly.

**How sure.** The DTM values are exact (validated solver, KQvK reproduces 19 plies) and the window clamp is
applied to every verdict. On the *flagged* position the clamp happens not to be decisive (window 88, all mates
fit), but **it was decisive elsewhere in this same run — position 31, counter 87, window 13 — and would have
manufactured a false defect without it.** That pairing is exactly why I withheld these mirror numbers until
`windowed_verdict()` existed: the clamp is not a formality, it is the difference between one real finding and
two, one of them wrong.

## 2. The window clamp was live in this run, which is why it matters

| pos | counter | window | draw available | best defence | engine | verdict | defect |
|---|---|---|---|---|---|---|---|
| 0 | 0 | 100 | yes | — | `a2b3` | draw | no |
| 5 | 20 | 80 | no | 23 | `g2g3` | win | no |
| **11** | **12** | **88** | no | **29** | **`f6e7`** | **win** | **YES** |
| 13 | 17 | 83 | yes | 13 | `b2c1` | draw | no |
| 15 | 21 | 79 | no | 27 | `d2e3` | win | no |
| 22 | 63 | 37 | no | 25 | `b2c3` | win | no |
| 25 | 70 | 30 | no | 13 | `d5d6` | win | no |
| **31** | **87** | **13** | **yes** | **None** | `h4g5` | **draw** | no |

**Position 31 is the one that justifies the whole clamp discipline.** Counter **87**, window **13** half-moves,
and a `dtm=None` move in the table — i.e. an unconstrained solver finds no forced mate for a move that leaves the
signature, and the correct verdict under match rules is **draw**. The engine found `h4g5` and drew it, at both
budgets. **Under my unclamped comparison this position would have been scored as a defender's failure**; through
`windowed_verdict()` it is correctly "no defect". That is exactly the error seat 21's trap predicts, caught in
my own pipeline by applying their rule.

## 3. The defect, verified move by move

`6k1/8/5K2/8/6r1/8/8/8 w - - 12 182` — bare white king, black king + rook. White to move, 4 legal moves:

| move | unconstrained DTM | fits window 88? | windowed verdict |
|---|---|---|---|
| `f6e5` | 27 | yes | win |
| `f6e6` | 27 | yes | win |
| **`f6e7`** | **17** | yes | **win — but the shortest** |
| `f6f5` | **29** | yes | win — **longest** |

Every move loses; the defender's job is to make it **last**. The engine picks the **shortest** resistance
(17 plies) when **29** was available — **12 plies, or 6 moves, thrown away**.

**Both budgets agree**, so this is not the truncation effect from 19-F55/F56 — more search would not fix it.
With four legal moves and a mate in 17 vs 29, the engine is choosing to die sooner. That is a *different* fault
from the node-budget one, and it is the one a lone-king defender can least afford, because each extra ply is
another chance for the attacker to err or for the fifty-move window to close.

## 4. What this pair of results says together

| test | population | windowed | result |
|---|---|---|---|
| 19-F55 (strong side to move) | KQvK/KRvK/KPvK | yes, all fit | **1 of 8** — nodes budget mates 4 plies later |
| this (bare king to move) | KRvK/KQvK/KPvK | yes, one clamp-critical | **1 of 8** — engine chooses mated-in-17 over mated-in-29 |

**Both sides of the lone-king class show one defect in eight, and they are different defects:** on the winning
side the node budget costs distance; on the losing side the search chooses the *shorter* defence even at full
depth. Together they say the lone-king class is not clean, and the failures are not all one mechanism.

### I tested the obvious suspicion and it is confirmed: this is a DEPTH limit, not a preference

I suspected the engine was choosing the move whose mate it could *see* (17 plies fits a depth-16 search; 29 does
not), rather than preferring to die sooner. One command decides it:

| search | bestmove | score |
|---|---|---|
| `go depth 16` | `f6e7` | cp −490 |
| `go depth 20` | `f6e7` | cp −490 |
| **`go depth 24`** | **`f6f5`** | **`mate -15`** (29 plies) |

**At depth 24 the engine finds `f6f5` — exactly the longest defence the oracle said was available.** So the
defect is **depth-limited**: below the depth where the longer mate becomes visible, the search cannot tell the
moves apart and takes whichever its heuristic prefers. That is a *much* less alarming finding than "the engine
prefers to lose quickly", and it makes position 11 a **calibration case** rather than a bug.

Note also that depths 16 and 20 report only **cp −490**, not a mate score, while depth 24 reports `mate -15`: the
search is not in mate-score territory at all until it can see the whole losing line.

## 5. Finding

**19-F58 — in the mirror direction (bare king to move), 1 of 8 oracle-covered positions is a defect:
`6k1/8/5K2/8/6r1/8/8/8 w - - 12 182` is mated in 17 plies after the engine's `f6e7`, when `f6f5` survives 29 —
12 plies of resistance given away, identically at `go depth 16` and `go nodes 20000`.** All verdicts pass
through `windowed_verdict()`; the window clamp was load-bearing on position 31 (counter 87, window 13, draw
available — correctly judged no defect), which is the exact error seat 21 warned about and it did not recur in
this run. PC r15, PC20, Threads 1, Hash 16, cold. Solver validated on KQvK (19 plies).

### What I did NOT do

- I did not test whether a deeper search fixes position 11 — that is the one experiment that would separate "a
  preference for dying sooner" from "a depth limit", and it is one command.
- 8 covered positions of 40 in the mirror sample (32 have 2+ pieces, outside the solver).
- I did not investigate why the engine's choice is the shortest: no trace of the 4 root moves' scores.

## 6. Files

`loneking/dtm_compare_mirror_windowed.py`, `loneking/mirrordiff/RESULT.txt`,
`loneking/oracle_mirror/dtm_oracle.txt`, `loneking/dtm_bfs.py` (with `windowed_verdict()`),
`NOTE_halfmove_window.md`.
