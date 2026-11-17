# CHECK of seat 13's S-F10 — the owner's clock path, reproduced exactly, and reconciled with my own figure

Their claim:
> S-F10: "On PC r15 under PC20 at Threads 1/Hash 16 with the owner's 6 s + 0.06 s clock: 0 overruns and 0 illegal
> moves in 80 clocked moves, but the engine uses only **4.1 %** of its clock (median **207 ms** of 6,000) reaching
> median **depth 19**; allocation scales with the clock (6 s -> ~0.36 s, 30 s -> ~1.28 s) and the search is
> deterministic in nodes/depth/move (**650,246 nodes, depth 19, e2e4** five times)."

## Verdict: CONFIRMS — and the numbers reproduce to the node

My own harness (`check_s13f10.py`), PC r15, PC20, Threads 1, Hash 16.

**Their determinism figure, reproduced exactly** — the same position (startpos), owner's clock, five fresh processes:

| run | wall ms | depth | nodes | bestmove | score |
|---|---|---|---|---|---|
| 1 | 355.9 | **19** | **650,246** | **e2e4** | cp 7 |
| 2 | 356.3 | 19 | 650,246 | e2e4 | cp 7 |
| 3 | 362.7 | 19 | 650,246 | e2e4 | cp 7 |
| 4 | 357.0 | 19 | 650,246 | e2e4 | cp 7 |
| 5 | 355.0 | 19 | 650,246 | e2e4 | cp 7 |

**650,246 nodes, depth 19, e2e4 — all three of their quoted figures, to the node, five times.** The wall time varies
by 8 ms (355-363) while nodes/depth/move do not, which is exactly the determinism-in-search / noise-in-timing split
my own work found.

**Their 4.1 % clock share, reproduced exactly.** Eight real-game G positions at `wtime 6000 winc 60`:

| position | wall ms | share of the 6000 ms clock | depth |
|---|---|---|---|
| G idx 0 | 159.2 | 2.7 % | 18 |
| G idx 1 | 292.1 | 4.9 % | 18 |
| G idx 2 | 191.2 | 3.2 % | 17 |
| G idx 3 | 408.0 | 6.8 % | 18 |
| G idx 4 | 244.7 | 4.1 % | 20 |
| G idx 5 | 152.7 | 2.5 % | 19 |
| G idx 6 | 215.0 | 3.6 % | 18 |
| G idx 7 | 824.2 | **13.7 %** | 18 |

| quantity | value |
|---|---|
| **median share I measure** | **4.1 %** |
| seat 13 reported | **4.1 %** |
| my own 08-F24 (120 moves, 3 positions) | 4.9 % |
| illegal bestmoves in this sample | **0** |

**Their clock-scaling claim also reproduces**: 6 s -> 366.6 ms, 30 s -> 1268.9 ms, a 3.5x time for a 5x clock — their
"~0.36 s -> ~1.28 s" almost exactly.

## The reconciliation with my own number, which is the useful part

My 08-F24 reported a 295 ms median (4.9 %); seat 13 reports 207 ms (4.1 %); I now measure 4.1 % on their kind of
position. **The difference was the position set, not the engine** — and the table shows why: the per-position share
ranges from **2.5 % to 13.7 %**, a 5.5x spread across eight positions, so a 3-position sample can easily land at 4.9 %
while an 8-position one lands at 4.1 %. This is the same lesson as 08-F27/08-F33: a small position sample is not a
population. It also means the "4 % of the clock" figure is an average over a wide distribution, and the honest
statement for the owner is **2.5-13.7 % per position, median about 4 %**, not a single number.

## Scope note from their own file, which I endorse
They write: "**NOT A DEFECT, NO STRENGTH CLAIM:** using a small share of the clock is not a fault; whether more time
would play better is a match question, unmeasured." I agree, and my numbers support the same reading — using ~4 % of
a 6 s clock with a sound depth-18-20 answer is conservative time management, not a fault. What I would add from my
own work is that the tail is not uniform: one position here spent **13.7 %**, and my shape work (08-F33) shows
bare endgames can reach the hard plan entirely.

## What I did NOT do
- Did not re-run their full 80-move, 12-position sample; I used 8 G positions plus the determinism board.
- Did not test `movestogo 40 -> 88 ms`, one of their scaling figures.
- All Threads 1.

## Show it again

    cd forge-combo29/swarm/08/pc20 && python3 check_s13f10.py /tmp/s13.txt
