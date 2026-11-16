# REPORT_nodebudget — the PC's match node budgets on real-game positions

**What was asked (my own priority from file 6):** the PC's matches use `go nodes 20000 / 50000 / 250000`. Does the
MOVE change between them, and is any move at a real budget demonstrably wrong?

**The answer: no illegal move anywhere (0 of 120 searches), the move is stable at all three budgets on 31 of 40
positions, and the 8 moves that change as the budget rises change for ordinary depth reasons — including one that
IMPROVES by 125 cp and one that WORSENS by 70 cp.**

```
positions measured                 40 of 40
same move at all three budgets     31
same move at 20000 and 250000      32
illegal moves                       0
moves that changed 20000 -> 250000  8
  idx  6: c8c3 (7)   -> d6e6 (37)    delta  +30 cp
  idx 10: e8d8 (22)  -> e8e6 (-40)   delta  -62 cp
  idx 12: e5e4 (239) -> b6c6 (364)   delta +125 cp
  idx 17: g7g6 (-122)-> d5f6 (-56)   delta  +66 cp
  idx 20: e4d2 (9)   -> e6d6 (37)    delta  +28 cp
  idx 21: f4g3 (15)  -> e5e6 (0)     delta  -15 cp
  idx 23: d1f3 (100) -> g7e6 (152)   delta  +52 cp
  idx 37: h8h1 (-497)-> h8g8 (-567)  delta  -70 cp
```

**The two that matter, in context:**

```
idx 12  rn2r1k1/pp3pp1/1q3f2/2bpp3/6bR/1BPP1N2/PP1NQP2/R1B1K3 b Q - 0 1
  20000   e5e4   cp 239  depth  9  nodes   8,717
  50000   b6e6   cp 222  depth 10  nodes  24,553
  250000  b6c6   cp 364  depth 13  nodes 214,451     <- +125 cp over the 20k choice

idx 37  7r/2k2p2/2p3P1/2Ppn3/PP2p1b1/4P3/4BK2/R6R b - - 0 1
  20000   h8h1   cp -497 depth 11  nodes  18,811
  50000   h8h1   cp -527 depth 13  nodes  44,797
  250000  h8g8   cp -567 depth 16  nodes 185,044     <- -70 cp, i.e. the deeper search rates its own choice WORSE
```

**Neither is a defect, and both are worth stating precisely.**

- idx 12: the 20k budget plays a move the deeper search rates 125 cp worse. That is a strength cost of the
  LOWEST match budget, not a wrong move — the engine is consistent at each budget and simply has less depth.
- idx 37: the deeper search picks a move it scores LOWER than the shallower search's preference. That is normal
  in a losing position: at depth 16 the engine sees the refutation, so its own score drops. It is the expected
  sign of seeing more of a bad position, not an error.

**P1 confirmed** (31/40 same at all three, far above my "at least half" bar). **P2 confirmed** (0 illegal).
**P3 confirmed** (24 of the 32 unchanged-move positions are within 30 cp; the score drifts down as depth exposes
the position). **P4 REFUTED as stated** — I predicted no replacement would improve by more than 100 cp, and idx 12
improves by 125 cp. **P5 confirmed** (depth differs between the budgets: 9-11 at 20k, 10-13 at 50k, 13-16 at 250k).

**How sure:** high. 120 searches, Threads 1, PC20, every move legality-checked against python-chess, raw rows
committed.

## Honesty numbers

```
exe     /home/ubuntu/builds/bld-pc/forge  PC r15, sha256 068f0927768d30be60e8cce6c9f29620dec330565397357dccc9e0fe361e32f4
        none 312866 / S14 242796 / PC20 278024   (all match file 5)
settings PC20 + Threads 1 + Hash 16; go nodes 20000/50000/250000; 40 G positions; cold per search
```

## Table

| step | done-partly-not done | evidence file | result |
|---|---|---|---|
| 40 positions x 3 budgets | done | `raw/nodebudget.tsv` (121 lines incl. header) | 120 measurements |
| legality of every move | done | same, `legal` column | 0 illegal |
| move stability across budgets | done | `raw/summary.txt` | 31/40 identical at all three; 8 changed 20k→250k |
| find a blunder at a real budget | NOT found | — | the worst case is +125 cp from the lowest budget, which is less depth, not a blunder |
| determinism of `go nodes` | done earlier (S-F16) | `../softnodes/run.log` | 1 distinct result over 5 reps |

## Findings

`S-F24 | 6 | on the PC's own match budgets (PC build, PC20, Threads 1, `go nodes 20000/50000/250000`, 40 real-game positions) no search produced an illegal move (0 of 120) and the move is identical at all three budgets on 31 of 40 positions; of the 8 moves that change, the largest is a +125 cp improvement from the 20,000 budget to the 250,000 one (idx 12, rn2r1k1/pp3pp1/1bq3n2/2bpp3/6bR/1BPP1N2/PP1NQP2/R1B1K3 b) and one is a -70 cp self-assessment drop in a lost position (idx 37), both ordinary depth effects rather than faults | nodebudget/raw/nodebudget.tsv nodebudget/raw/summary.txt (again: `python3 nodebudget/nodebudget.py ~/builds/bld-pc/forge /tmp/o`) | NEW |`

## Suspicions, not proven

- That idx 12's +125 cp gap is what a 20,000-node match budget costs in strength overall. One position is not a
  strength estimate; I would need a game-level comparison to claim that.
- That idx 37's -70 cp is purely "seeing the refutation". Plausible from the depth sequence, not proven.

## What I did NOT do

- Did not play games at the two budgets to measure the strength difference (that is a match, not a search test).
- Did not check whether 20,000 is ever TOO FEW nodes to reach a stable move on tactical positions (idx 12 hints
  it can be, but 1 of 40 is not a rate).

## Times

`nodebudget/stamps.txt`, every line a `date -u`.
