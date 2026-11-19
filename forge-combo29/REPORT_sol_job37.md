# Sol — Job 37 full-load self-play throughput

## Step 0. Unchanged build and machine pins

All ten fresh processes matched. On each unchanged Job 34 binary, default bench 11 was 312866, bench 13 was 862329 and perft 5 was 4865609. With PC20 and synthetic net768, bench 11 was 882074 and bench 13 was 4275906. Both reported `NNUE v3 active` with checksum `30ab43b4ba5db5f3`. The native GCC 14.2.0 binaries were r15d `9068653cd638639a602b7c72dafe741e395598d0178f14fa31d530767f982671` and kF `c9ab02f9e15cc0a293b849116aa56d45ca3c521fa1209ed27386734dbb62d0eb`. [r15d raw pins](sol/job37/pin-evidence/r15d.raw.txt) · [kF raw pins](sol/job37/pin-evidence/kF.raw.txt) · [Build commands](sol/job34/build-evidence/build-all.txt)

The cloud reported AMD EPYC 9V74 80-Core Processor, `nproc` 5, and cgroup `cpu.max` `400000 100000`. I used W = 5, with one driver and one single-threaded engine per worker. The quota allowed four CPU-equivalents, so the five workers shared that limit. [lscpu](sol/job37/pin-evidence/lscpu.txt) · [CPU quota](sol/job37/pin-evidence/cpu-max.txt)

## C37. Sensitivity control

**PASS.** r15d at 3,000 softnodes over the same r15d at 2,000 softnodes had pooled wall B/A 1.409777 over 4 of 4 blocks. The declared gate required all four blocks and a ratio above 1.10. Both arms used PC20, active net768, Threads 1 and Hash 16. [C37 raw runs](sol/job37/C37.runs.tsv) · [C37 statistics](sol/job37/C37.stats.json)

## Prediction and grade

I froze the prediction in `cfecfe2` after C37 and before W0. I expected the kF stack to improve elapsed time and the same-binary check to center near one. [Frozen prediction](sol/job37/prediction.json) · [UTC stamps](sol/job37/stamps.txt)

| Quantity | Forecast | Observed | Grade |
| --- | --- | --- | --- |
| T1 pooled wall B/A | [0.940000, 1.010000] | 0.935939 | missed |
| T1 wall reading | PAYS | PAYS | met |
| P1 pooled wall B/A | [0.980000, 1.020000] | 1.037214 | missed |
| P1 wall reading | NOT SEEN | NOT SEEN | met |


## T1 and P1. Wall and engine CPU ratios

Both comparisons used PC20, synthetic net768, Threads 1, Hash 16 and `go softnodes 2000`. A was r15d. B was kF for T1 and r15d for P1. Each run assigned 25 games to each worker. The table uses B divided by A. A smaller wall ratio means more positions per second for the same searches.

| Comparison | Metric | Eligible / planned blocks | Median | Pooled | Mean | 95% t interval | df | Blocks below 1 |
| --- | --- | ---: | ---: | ---: | ---: | --- | ---: | ---: |
| T1 | Wall | 16/16 | 0.917347 | 0.935939 | 0.938649 | [0.904375, 0.972924] | 15 | 13 |
| T1 | Engine CPU | 16/16 | 0.916973 | 0.931819 | 0.934922 | [0.901556, 0.968288] | 15 | 13 |
| P1 | Wall | 8/8 | 1.053785 | 1.037214 | 1.037216 | [0.989011, 1.085421] | 7 | 3 |
| P1 | Engine CPU | 8/8 | 1.029096 | 1.026301 | 1.026336 | [0.980962, 1.071711] | 7 | 3 |


**T1 PAYS. P1 NOT SEEN.** The P1 wall interval covered 1, so 1 was the reference for T1. An interval wholly below the reference reads PAYS, wholly above reads COSTS, and overlap reads NOT SEEN. Engine CPU is descriptive.

Across those T1 blocks, each build searched 229,707 positions and 952,949,268 last-info nodes. r15d produced 1,106.25 positions/s and kF produced 1,181.97 positions/s over 207.645 and 194.343 measured wall seconds respectively. [One line per raw run](sol/job37/analysis.runs.tsv)

### T1 record identity and block ratios

| Block | Base | Order | Record identity | A / B rows | Wall B/A | Engine CPU B/A |
| --- | ---: | --- | --- | --- | ---: | ---: |
| 1 | 201000 | AB | identical | 15,426 / 15,426 | 0.963981 | 0.959202 |
| 2 | 202000 | BA | identical | 14,824 / 14,824 | 0.907333 | 0.905841 |
| 3 | 203000 | BA | identical | 15,387 / 15,387 | 0.858689 | 0.853294 |
| 4 | 204000 | AB | identical | 14,495 / 14,495 | 1.026318 | 1.032097 |
| 5 | 205000 | AB | identical | 13,821 / 13,821 | 0.867731 | 0.870642 |
| 6 | 206000 | BA | identical | 14,341 / 14,341 | 0.914497 | 0.903838 |
| 7 | 207000 | BA | identical | 13,555 / 13,555 | 0.908883 | 0.889785 |
| 8 | 208000 | AB | identical | 14,182 / 14,182 | 0.862993 | 0.860419 |
| 9 | 209000 | AB | identical | 13,260 / 13,260 | 0.967584 | 0.974545 |
| 10 | 210000 | BA | identical | 14,823 / 14,823 | 0.995900 | 0.974192 |
| 11 | 211000 | BA | identical | 15,169 / 15,169 | 0.920197 | 0.912907 |
| 12 | 212000 | AB | identical | 14,060 / 14,060 | 1.030495 | 1.013393 |
| 13 | 213000 | AB | identical | 14,872 / 14,872 | 0.865305 | 0.865368 |
| 14 | 214000 | BA | identical | 14,320 / 14,320 | 1.055419 | 1.044223 |
| 15 | 215000 | BA | identical | 13,458 / 13,458 | 0.903215 | 0.921038 |
| 16 | 216000 | AB | identical | 13,714 / 13,714 | 0.969848 | 0.977964 |


P1 block-by-block wall and engine CPU ratios are in the JSON, together with both runs and their record hashes. [P1 block ratios](sol/job37/P1.stats.json) · [P1 cmp receipt](sol/job37/P1.cmp.tsv)

[T1 cmp receipt](sol/job37/T1.cmp.tsv) · [T1 block ratios and receipts](sol/job37/T1.stats.json)

## Facts

W0 used base 199000. Its two run records were identical. Both stayed outside the timing comparison. [W0 raw runs](sol/job37/W0.runs.tsv)

Each timed interval began after all engines sent `readyok` and ended when the parent received the last worker completion. I sampled summed user and system engine ticks from `/proc` while all engines were still alive, so CPU includes engine initialization. Each driver took the seeded random plies from Job 35 and reset the engine once per game, including terminal openings that required zero searches. The two runs shared the same base. I numbered blocks from 1 within each comparison, so their early bases recur. The two-run orders repeat AB, BA, BA, AB, giving the requested ABBA and BAAB sequence. [Runner](sol/job37/run_one37.py) · [Raw worker receipts](sol/job37/raw)

## Suspicions

Because five workers shared a four-CPU quota, the wall outcome can include scheduler contention and the time for the slowest worker to finish. The engine CPU ratios show only the engine work recorded in the worker processes.

## What this check cannot see

The PC's engine build (clang 23 for Windows, its profile), its processor (8 cores, 16 hardware threads), its trained
net (net768 is made up), the PC's own driver (python under Windows), other loads beside self-play.

## What I did not do

I reused the pinned cloud artifacts. I ran no trials on the owner’s PC and made no engine source changes.

## What I am not sure about

The timing includes cloud scheduling and Python driver work. It does not show how much of the observed elapsed-time difference would transfer to the PC.

## Reproduction

The analysis records the arithmetic mean and Student t interval of block ratios, and computes the pooled ratio from total B seconds divided by total A seconds. [Primary analyzer](sol/job37/analyze37.py) · [Independent readback](sol/job37/independent.json) · [UTC stamps](sol/job37/stamps.txt) · [Precommit tree](sol/job37/precommit-readback.txt)
