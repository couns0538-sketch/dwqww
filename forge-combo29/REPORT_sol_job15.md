# Sol — Job 15 EvalSwingMult fresh seeds, direct dose and node budgets

## Step 0 and gates

1. **The counting executable passed all eight fresh-process pins.** Defaults gave 312866, 862329 and 3024920 bench nodes, and 4865609 at perft 5. S14 gave 242796 and 656517. PC20 gave 278024 and 587276. Counting SHA-256 `63356d12c5505ab657e71ddd020e3ca27c8e8c6b4b1632bae343c57deef33333`. The official executable printed `fastchess alpha 1.8.3 20261107-d7b47e8`. The official opening EPD SHA-256 was `7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a`. [Step 0 raw output](sol/job15/step0-count.raw.txt) · [Build and opening receipts](sol/job15/build.txt)
2. **K4 passed 50/50.** At 5,000 nodes and plain PC20 on both sides, every color-reversed pair shared its FEN, move list and 1–1 result. A scored 32–32–36 and pentanomial `[0, 0, 50, 0, 0]` in 100 games. [K4 PGN](sol/job15/raw/K4.pgn) · [K4 output](sol/job15/raw/K4.out)
3. **C4 passed.** In 200 games at 10,000 versus 20,000 nodes, otherwise plain PC20, A scored 23–112–65. Pentanomial `[26, 42, 28, 3, 1]`, Elo −166.23 and 95% interval [−202.92, −129.54]. Elo was below −100 and its upper bound was below zero. [C4 PGN](sol/job15/raw/C4.pgn) · [C4 output](sol/job15/raw/C4.out) · [Gate readback](sol/job15/gates-K4C4.txt)

The [prediction](sol/job15/prediction.txt) was committed alone as `dc44e1a3bfdc6bc348b41095eb343cdcf02bdd65` after the two gates and before any candidate game. Slot 1 ran E6k2, E12k2, D12v3 and E6m sequentially. Slot 2 ran E6t. Each used two workers. [UTC stamps](sol/job15/stamps.txt)

## Prediction grades

The observed Elo must have the forecast sign and fall within a factor of 1.5 of its magnitude. A zero forecast requires zero. Replication forecasts use exact yes/no matching.

| Forecast | Guess | Observed | Grade | Evidence status |
|---|---:|---:|---|---|
| E6k2 Elo | +11.00 | +23.49 | KILLED | complete |
| E12k2 Elo | +12.00 | +17.21 | survives | complete |
| D12v3 Elo | +4.00 | +14.08 | KILLED | complete |
| E6m Elo | +12.00 | +7.47 | KILLED | complete |
| E6t Elo | +11.00 | +4.17 | KILLED | complete |
| E6k REPLICATED | yes | yes | survives | complete: interval reconstructed from summed penta counts |
| E12k REPLICATED | yes | yes | survives | complete: interval reconstructed from summed penta counts |

4 KILLED, 3 survive, 0 ungraded.

## Table K. EvalSwingMult paired-game results

W-L-D is from A's perspective. The 95% intervals use the fastchess pentanomial Elo ± halfwidth convention. Each analyzed pair contains both colors.

| Match | Status | Games | W-L-D | Pentanomial | Elo [95%] |
|---|---|---:|---|---|---|
| E6k | complete | 2000 | 728-638-634 | 106, 175, 359, 243, 117 | +15.65 [+3.33, +27.97] |
| E6k2 | complete | 2000 | 758-623-619 | 84, 195, 360, 224, 137 | +23.49 [+11.22, +35.76] |
| E6k + E6k2 pooled | complete: interval reconstructed from summed penta counts | 4000 | 1486-1261-1253 | 190, 370, 719, 467, 254 | +19.56 [+10.87, +28.25] |
| E12k | complete | 2000 | 736-634-630 | 97, 190, 356, 228, 129 | +17.73 [+5.36, +30.10] |
| E12k2 | complete | 2000 | 727-628-645 | 96, 194, 334, 267, 109 | +17.21 [+5.04, +29.38] |
| E12k + E12k2 pooled | complete: interval reconstructed from summed penta counts | 4000 | 1463-1262-1275 | 193, 384, 690, 495, 238 | +17.47 [+8.80, +26.15] |
| D12v3 | complete | 2000 | 726-645-629 | 91, 199, 375, 208, 127 | +14.08 [+1.91, +26.25] |
| E6m | complete | 2000 | 636-593-771 | 63, 238, 373, 245, 81 | +7.47 [-3.61, +18.55] |
| E6t | complete | 2000 | 575-551-874 | 55, 256, 360, 268, 61 | +4.17 [-6.53, +14.87] |

A cell is REPLICATED when its fresh seed alone gives Elo above 0 AND the pool of its two seeds (pentanomial counts added) has a 95 % interval whose lower end is above 0. Cells E6k (job 14 + E6k2) and E12k (job 14 + E12k2) get a verdict; D12v3, E6m and E6t are exploratory: no verdict, a row each.
E6k REPLICATED: yes. Fresh Elo +23.4900, pooled lower 95% bound +10.8746. Evidence complete: interval reconstructed from summed penta counts.
E12k REPLICATED: yes. Fresh Elo +17.2100, pooled lower 95% bound +8.7978. Evidence complete: interval reconstructed from summed penta counts.

## Shared openings

Counts are distinct exact FEN tags shared by two files. Each file contributes one opening per complete color-reversed pair. The inventory shows complete pairs and distinct FEN tags.

| File | Status | Complete pairs | Distinct exact FENs |
|---|---|---:|---:|
| K4 | saved | 50 | 50 |
| C4 | saved | 100 | 100 |
| E6k2 | complete | 1000 | 1000 |
| E12k2 | complete | 1000 | 1000 |
| D12v3 | complete | 1000 | 1000 |
| E6m | complete | 1000 | 1000 |
| E6t | complete | 1000 | 1000 |
| Job 13 E2 | saved | 1000 | 1000 |
| Job 13 E3k | saved | 1000 | 1000 |
| Job 13 E6 | saved | 500 | 500 |
| Job 14 E3k2 | saved | 1000 | 1000 |
| Job 14 E6b | saved | 1000 | 1000 |
| Job 14 E6k | saved | 1000 | 1000 |
| Job 14 E12k | saved | 1000 | 1000 |

| File A | File B | Shared exact FENs |
|---|---|---:|
| K4 | C4 | 0 |
| K4 | E6k2 | 0 |
| K4 | E12k2 | 0 |
| K4 | D12v3 | 0 |
| K4 | E6m | 0 |
| K4 | E6t | 0 |
| C4 | E6k2 | 0 |
| C4 | E12k2 | 0 |
| C4 | D12v3 | 0 |
| C4 | E6m | 0 |
| C4 | E6t | 0 |
| E6k2 | E12k2 | 0 |
| E6k2 | D12v3 | 0 |
| E6k2 | E6m | 1 |
| E6k2 | E6t | 0 |
| E12k2 | D12v3 | 0 |
| E12k2 | E6m | 1 |
| E12k2 | E6t | 0 |
| D12v3 | E6m | 0 |
| D12v3 | E6t | 0 |
| E6m | E6t | 1 |
| K4 | Job 13 E2 | 0 |
| K4 | Job 13 E3k | 0 |
| K4 | Job 13 E6 | 0 |
| K4 | Job 14 E3k2 | 0 |
| K4 | Job 14 E6b | 0 |
| K4 | Job 14 E6k | 0 |
| K4 | Job 14 E12k | 0 |
| C4 | Job 13 E2 | 0 |
| C4 | Job 13 E3k | 0 |
| C4 | Job 13 E6 | 0 |
| C4 | Job 14 E3k2 | 0 |
| C4 | Job 14 E6b | 0 |
| C4 | Job 14 E6k | 0 |
| C4 | Job 14 E12k | 0 |
| E6k2 | Job 13 E2 | 1 |
| E6k2 | Job 13 E3k | 0 |
| E6k2 | Job 13 E6 | 0 |
| E6k2 | Job 14 E3k2 | 0 |
| E6k2 | Job 14 E6b | 0 |
| E6k2 | Job 14 E6k | 1 |
| E6k2 | Job 14 E12k | 0 |
| E12k2 | Job 13 E2 | 1 |
| E12k2 | Job 13 E3k | 0 |
| E12k2 | Job 13 E6 | 0 |
| E12k2 | Job 14 E3k2 | 0 |
| E12k2 | Job 14 E6b | 1 |
| E12k2 | Job 14 E6k | 0 |
| E12k2 | Job 14 E12k | 1 |
| D12v3 | Job 13 E2 | 0 |
| D12v3 | Job 13 E3k | 0 |
| D12v3 | Job 13 E6 | 0 |
| D12v3 | Job 14 E3k2 | 0 |
| D12v3 | Job 14 E6b | 0 |
| D12v3 | Job 14 E6k | 1 |
| D12v3 | Job 14 E12k | 0 |
| E6m | Job 13 E2 | 0 |
| E6m | Job 13 E3k | 0 |
| E6m | Job 13 E6 | 1 |
| E6m | Job 14 E3k2 | 0 |
| E6m | Job 14 E6b | 1 |
| E6m | Job 14 E6k | 0 |
| E6m | Job 14 E12k | 1 |
| E6t | Job 13 E2 | 0 |
| E6t | Job 13 E3k | 1 |
| E6t | Job 13 E6 | 0 |
| E6t | Job 14 E3k2 | 0 |
| E6t | Job 14 E6b | 0 |
| E6t | Job 14 E6k | 0 |
| E6t | Job 14 E12k | 0 |

## Facts

- All seven scheduled matches finished before the cutoff. The 10,300 scored games were all in complete color-reversed pairs. E6k2 and E6t launched at 08:16:29Z. Slot 1 started its next matches at 08:22:53Z, 08:29:18Z and 08:35:47Z. E6m finished last at 08:47:09Z. [Independent counts and slot verification](sol/job15/independent-Job15.txt)
- Both 2,000-node cells met the declared replication rule. Dose 6's fresh seed gave +23.49 Elo [+11.22, +35.76] and its 4,000-game pool gave +19.56 [+10.87, +28.25]. Dose 12's fresh seed gave +17.21 [+5.04, +29.38] and its 4,000-game pool gave +17.47 [+8.80, +26.15].
- In the exploratory 2,000-game arms, dose 12 versus dose 3 at 2,000 nodes gave +14.08 Elo [+1.91, +26.25]. Dose 6 versus zero gave +7.47 [−3.61, +18.55] at 5,000 nodes and +4.17 [−6.53, +14.87] at 10,000.
- There were 13 nonzero comparisons among the 70 file pairs in the shared-opening table. Each shared exactly one FEN. Each replication pool has one shared FEN between its two constituent seeds. The declared sum includes both encounters. [Shared-opening recomputation](sol/job15/readback.txt)
- D12v3 applied dose 3 then dose 12 for A and dose 3 for B. The pinned fastchess parser appends options in order at `app/src/cli/cli.cpp:215–219` and sends their relative order after partitioning Threads at `app/src/engine/uci_engine.cpp:344–351`. Forge's setter binds the spin value at `src/uci.cpp:422–429` in the Job 4 counting tree. [D12v3 settings and acknowledgement](sol/job15/raw/D12v3.meta) · [Pinned fastchess option dispatch](https://github.com/Disservin/fastchess/blob/d7b47e8dec6b564aaf4cbb2922ab37e6c6761e75/app/src/engine/uci_engine.cpp#L341-L351)

## Suspicions

Dose 6's two intermediate-budget point estimates are smaller than the 2,000-node pool. Their intervals leave a broad range of plausible effects. The direct dose-12-versus-3 result gives a separate positive signal at 2,000 nodes on this seed.

## What I did not do

This job used Codex Cloud and the unchanged counting executable. Engine source, weights, training and the owner's running tune were outside the scope of the matches.

## What I am not sure about

Each comparison applies to this embedded net, PC20 settings and the sampled openings. The direct-dose arm compares doses 12 and 3 at 2,000 nodes on one seed. The intermediate-budget arms compare dose 6 with zero at their own fixed budgets and each uses one seed. A transfer to the PC's engine and net remains a separate measurement.

## Reproduction

Both sides used Forge PC r15 at `6b98f2170a3210e71beed04bbd2553972c253ed7` with the Job 2 counters and Job 4 buttons, GCC 14.2.0, CMake 4.2.3 Release, libstdc++ 6.0.33, glibc 2.41, x86-64-v4 and `FORGE_MATE_ALPHA_GUARD=1`. Settings were PC20, one thread, Hash 16 MiB, one PV, OwnBook false and embedded AL1 s198 with weights-source SHA-256 `a7ebcf3a319675f347e6e8e3f2539901d38d8036cb9b5935f31dd43d084c9638`. The pinned official fastchess executable and EPD were rehashed before any match. [Forge build](REPORT_sol_job4.md) · [Build and book receipt](sol/job15/build.txt)

Each sampled opening was played twice with opposite colors at the prescribed hard node budget, with a 300-move limit and no separate resign or draw adjudication flags. Every A preflight ended at `readyok`. In D12v3 the shared setting list gives each engine dose 3, and A's last command applies dose 12. The exact option sequence and its acknowledgement are in the sidecar. All matches respected the four-worker maximum. The play cutoff was 09:02:33Z. [Match PGNs, output and sidecars](sol/job15/raw)

From `forge-combo29/sol/job15`, with Python 3 and python-chess 1.11.2, these commands regenerate the controls, Table K and all shared-opening comparisons.

```sh
python3 analyze_matches15.py gates raw
python3 analyze_matches15.py table raw --job13-raw ../job13/raw --job14-raw ../job14/raw \
  --prediction prediction.txt
```

[Complete readback](sol/job15/readback.txt) · [UTC and slot evidence](sol/job15/stamps.txt) · [Precommit tree readback](sol/job15/precommit-readback.txt)
