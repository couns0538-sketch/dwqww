# CHECK of seat 05's S-F1 — mate score wrong and PV truncated on G/192

**Verdict: CONFIRMS S-F1.** Note on independence: I found this position independently in my own
job 1 (`15-F1`, found by scanning my own 553-position run) before reading seat 05's findings, so
this is two seats reaching the same position by different routes. The harness below is mine
(`probe2.py`, job 1), not a copy of the finder's script, and the truth values come from two solvers
I wrote that share no code path.

The position: `8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1` (white to move, white is lost).

## 1. The claim, on my harness

```bash
cd forge-combo29/swarm/15/job1
python3 probe2.py '8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1' 12 --opts s14
```

```
info depth 12 seldepth 27 score mate -12 nodes 19197 nps 2742428 hashfull 4 time 7 pv c2c3 d2d1q c3b2 e4e3 b2a2 d1c2 a2a1 c2c1 a1a2 c1c4 a2b2 c4d4 b2c1 d4a1 c1c2 a1d1 c2b2 e2d3
bestmove c2c3
```

18-ply PV, does not end in checkmate. Reproduced identically three times, and at Hash 16 / 512 /
2048 with the same node count 19197 (so not transposition-table eviction).

## 2. The truth, from two independent solvers

```bash
cd forge-combo29/swarm/15/job1
python3 matedbf.py '8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1' 12   # full AND/OR tree, no pruning
python3 solvemate2.py '8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1' 10  # alpha-beta mate solver
```

```
MATED_IN_PLIES 8
MATED_IN_PLIES 8
```

Correct score: `mate -4`. Engine: `mate -12`. Wrong by 8 moves.

## 3. What the PV actually reaches

The position after the 18 PV plies is `8/8/1p6/8/p7/3kp3/1K6/3q4 w - - 14 10`, which both solvers
call `MATED_IN_PLIES 4`. So the printed line reaches mate at 22 plies while claiming 24 — the line
it printed contradicts its own score, so this is not merely a short PV.

## 4. Depth behaviour (matches the finding)

`-12` at depths 12 and 13, then `-9`, `-6`, `-5`, `-5`, `-4` as depth grows; the value is still
moving at depth 22. Recorded in `job1/evidence/mate392/verify_safe.txt` and `s14_depth12.txt`.

## Where I differ from the finding's framing

Seat 05's wording ("a mate in 6 plies is provable by hand") describes the *end* of their line. On
my solve the mate from the root is 8 plies, i.e. 4 moves; the -12 claim is 24 plies. I state the
numbers I measured and let the difference in framing stand as a difference, since both agree the
depth-12 score is wrong and reproducible.
