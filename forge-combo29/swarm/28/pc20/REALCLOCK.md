# At the OWNER'S control (6 s + 0.06/move): the tail reaches 26 % of the clock in one move

Re-run of my tail and stop-fraction work at the control FABLE_TO_swarm_6 names as the only one that matters
for strength: PC build under PC20, Threads 1, Hash 16, `go wtime 6000 btime 6000 winc 60 binc 60`.

Plan from the engine's own advertised constants (identical on both builds per S-F27):
`available = 5990`, `soft = 5990/22 + 60*75/100 = 272 + 45 = 317 ms`,
`hard = min(5990*60/100, 317*5) = min(3594, 1585) = 1585 ms`.

## The table — 60 positions per build, Threads 1, `realclock.log`

| build | n | median | p99 | max | p99/median | stop fraction (median/soft) | last-iter/soft | median last depth | over soft | over hard | over clock | legal |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| base | 60 | 246.1 | 1409.8 | 1585.3 | 5.73 | 0.78 | 0.77 | 19 | 20 | 1 | 0 | 60/60 |
| PC20 | 60 | 226.3 | 1499.3 | 1585.3 | 6.63 | 0.71 | 0.71 | 18 | 17 | 1 | 0 | 60/60 |

Run twice with the same shape (first run: base 252.5 / PC20 224.4), so these are stable.

## The finding that matters: one search in twenty spends a quarter of the clock

The distribution is not a smooth tail. It is bimodal:

| build | <100 | 100-200 | 200-317 (under soft) | 317-500 | 500-1000 | >1000 ms |
|---|---|---|---|---|---|---|
| base | 1 | 22 | 16 | 13 | 5 | **3** |
| PC20 | 1 | 20 | 22 | 10 | 5 | **2** |

Five of 120 searches spend **1.2 to 1.59 seconds** of a 6-second clock on one move. On a 6 s + 0.06 control
that is 20-26 % of the whole game's initial time for a single move.

### The worst case, reproduced three times on the base build

Position `8/5p2/8/pp1pkpKp/7P/2P3P1/1P6/8 w - - 0 1`:

```
run1: wall 1585 ms, 19 info lines, last: depth 19 ... nodes 2929125 ... time 1019 pv g5h5
run2: wall 1585 ms, 19 info lines, last: depth 19 ... nodes 2929125 ... time 997  pv g5h5
run3: wall 1585 ms, 19 info lines, last: depth 19 ... nodes 2929125 ... time 1069 pv g5h5
```

Three things to read from that:
1. **It is deterministic** — the same wall time, the same node count, the same move each run.
2. **It stops exactly at the 1585 ms hard plan**, so the hard limit is doing its job.
3. **The last COMPLETED iteration ended at ~1020 ms.** The search then ran another ~565 ms and completed
   nothing. So the overspend is not a long iteration finishing — it is a search that kept going past its
   own last finished iteration and was cut by the hard limit.

That third point is the actionable one: on this position the engine had a perfectly good depth-19 answer at
1.02 s and spent a further 0.57 s to produce nothing new.

## What this changes, and what it does not
- **It does not contradict S-F27.** The stop fractions here (base 0.78, PC20 0.71) match the 10 s picture:
  PC20 stops earlier relative to soft.
- **It does change the priority of my tail work.** p99/median of 5.7-6.6x at the owner's control is much
  worse than the 2.2-4.4x I measured on `go wtime` without an increment (S-F20). My prediction Y6 said
  2-5x and is **killed**. The increment is not obviously the cause; the bimodality is.
- **Two of the five big searches are in pawn endgames** (`8/5p2/8/pp1pkpKp/...` and
  `8/p7/5pk1/7p/r2NKP2/...`) and one is a queen ending — positions where search is least likely to find
  anything new. That is a pattern worth naming, not a proof.

## A data defect I found and fixed
My first run wrote the TSV rows BEFORE recording which FEN each row came from, so the position column was
empty in 60 of 60 rows and no outlier could be attributed to a board. Fixed by recording the FEN inside the
search loop, and the whole job was re-run from scratch — every number above is from the corrected run, and
`awk` confirms zero empty FEN fields.

## Prediction score
Y1 (PC20 stop fraction 0.55-0.75): 0.71 SURVIVES. Y2 (median depth 13-16): 18 — **KILLED** (I
underestimated depth at this control). Y3 (base higher than PC20): 0.78 > 0.71 SURVIVES. Y4 (over the
clock): 0 SURVIVES. Y5 (over soft, 10-45 %): base 33 %, PC20 28 % SURVIVES. Y6 (p99/median 2-5x): 5.73
and 6.63 — **KILLED**. Y7 (plan 317): exact SURVIVES.

## Reproduce
```
cd forge-combo29/swarm/28/pc20
python3 realclock.py ~/build/base-release/forge ~/build/r15-pc/forge /tmp/real 60
```
Raw: `out_real/realclock_{base,PC20}.tsv` + `.meta` (exe sha256, every option, the `go` line).
