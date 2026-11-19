# Sol — Job 36 kF versus r15d at 6+0.06

## Step 0. Unchanged builds, net and concurrency

I reused the Job 34 native binaries. kF SHA-256 was `c9ab02f9e15cc0a293b849116aa56d45ca3c521fa1209ed27386734dbb62d0eb`, and r15d SHA-256 was `9068653cd638639a602b7c72dafe741e395598d0178f14fa31d530767f982671`. The build used GCC 14.2.0 with the Job 34 PC defines, `-march=native` and the AVX-512 path. [Build commands and hashes](sol/job34/build-evidence/build-all.txt)

Each executable matched all five fresh-process pins. The defaults returned 312866 for `bench 11`, 862329 for `bench 13` and 4865609 for `go perft 5`. PC20 with synthetic net768 returned 882074 and 4275906 for the two benchmarks. Every net-enabled preflight showed `NNUE v3 active` with checksum `30ab43b4ba5db5f3`. Net SHA-256 was `c3d95131d7c1c89ccb5b000b52c7c37ed8665dbf8bb2a0a7a873809c85b9f7c7`. [kF raw pins](sol/job36/pin-evidence/kF.raw.txt) · [r15d raw pins](sol/job36/pin-evidence/r15d.raw.txt) · [Net generator receipt](sol/job34/net-evidence/net768-generation.txt)

`nproc` returned 5. I chose four simultaneous games, the permitted maximum of `nproc − 1`, and one search thread per engine. The cloud cgroup quota was four CPUs. [CPU receipt](sol/job36/pin-evidence/nproc.txt)

## K26. kF versus kF

**PASS.** At 6+0.06 with PC20 and active net768, both kF arms completed all 20 games with zero time losses. 0 of 10 color-reversed pairs repeated every move. A scored 9–10–1 W–L–D with pentanomial `[1, 1, 7, 0, 1]` and -17.39 [-122.32, +87.55] Elo. [PGN](sol/job36/raw/K26.pgn) · [Fastchess output](sol/job36/raw/K26.out) · [Gate](sol/job36/K26.gate.txt)

## Prediction and grade

I froze the prediction in `87c2dcf` after K26 and before Q1. The point estimates rounded the K26 means to 175 ms and allowed a higher maximum in the longer matches. Ranges are graded against observed counts and the paired Elo point estimate. Point forecasts show observed minus forecast in milliseconds. [Frozen prediction](sol/job36/prediction.json) · [UTC stamps](sol/job36/stamps.txt)

| Match | kF flags [0, 2] | r15d flags [0, 2] | kF / r15d mean 175 ms each | kF / r15d max 1,800 ms each | kF Elo [−30, +30] |
| --- | --- | --- | --- | --- | --- |
| Q1 | 0, met | 0, met | +14.5 / +14.5 | -195.0 / -196.0 | 0.00, met |
| Q2 | — | — | — | — | — |

## Q1 and Q2. Move times and time losses

Both timed arms used PC20, active net768, Threads 1, Hash 16, OwnBook false and 6+0.06 with four simultaneous games. A was kF and B was r15d. Fixed-node counts do not apply to these matches.

| Run and seed | Status | Games | Full pairs | A W–L–D | Pentanomial | A Elo [95%] | Reading |
| --- | --- | ---: | ---: | --- | --- | --- | --- |
| Q1, 7361 | Complete | 600 of 600 | 300 | 261–261–78 | `[42, 39, 141, 33, 45]` | 0.00 [-23.29, +23.29] | CLOCK OK |
| Q2, 7362 | Cut at minute 50 | 0 of 400 | 0 | — | — | — | UNAVAILABLE |

| Run | Arm | Moves | Mean ms | p99 ms | Max ms | Moves above 500 ms | PGN flags | Fastchess flags |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| K26 | A kF | 975 | 176.031 | 1,100 | 1,601 | 84 | 0 | 0 |
| K26 | B kF | 976 | 172.851 | 1,030 | 1,601 | 81 | 0 | 0 |
| Q1 | A kF | 25,778 | 189.461 | 1,148 | 1,605 | 2,385 | 0 | 0 |
| Q1 | B r15d | 25,780 | 189.543 | 1,142 | 1,604 | 2,410 | 0 | 0 |

**CLOCK OK** on the recorded timed games. The declared rule requires zero kF time losses in each played comparison and an absolute p99 difference of at most 10% of r15d’s p99. The absolute differences were Q1 0.53%. [Raw games and fastchess output](sol/job36/raw) · [Independent archive readback](sol/job36/readback.txt)

Q2 launched at 2026-11-18T23:59:29Z and received SIGINT at 2026-11-18T23:59:37Z. Fastchess started 4 games and recorded no finishes, so Q2 has no forecast grades.

## Facts

Game results and time losses were read from the PGN and checked against fastchess’s output. The archive readback independently matched the PGN byte hashes, game results, paired scores and timing counts. [Archive readback](sol/job36/readback.txt)

## Suspicions

The slower end of the move-time distribution may include cloud scheduling delays. The observed largest move and Elo estimate are descriptive under Opus’s rule.

## What this check cannot see

The PC's engine build (clang 23 for Windows, its profile), its processor with 16 engines at once, its trained net
(net768 is made up), the PC's own fastchess version, other time controls.

## What I did not do

I reused the verified cloud binaries and synthetic net. I made no tracked engine-source changes and ran no training or tests on the owner's PC.

## What I am not sure about

The PGN times measure elapsed wall time in this fastchess build. They include local scheduling and communication delays, and the comparison cannot isolate those contributions.

## Reproduction

The runs used official fastchess `alpha 1.8.3 20261107-d7b47e8`, the pinned UHO book, seed-specific random order, reversed colors, no adjudication and recovery off. Both sides had PC20, one thread, Hash 16, OwnBook false, active net768 and `tc=6+0.06`. In the measured matches A was kF and B r15d. Each side's move-time tail uses the nearest-rank 99th percentile of fastchess's integer-millisecond PGN comments. The 95% Elo interval uses fastchess's paired score variance and symmetric Elo half-width. [Exact argv and active-net receipts](sol/job36/raw) · [Timing parser](sol/job36/analyze_matches36.py) · [Fastchess Elo formula](https://github.com/Disservin/fastchess/blob/d7b47e8dec6b564aaf4cbb2922ab37e6c6761e75/app/src/matchmaking/elo/elo_pentanomial.cpp)

Each match log records the two UCI preflights. They sent the same option order as fastchess, which moves Threads first and preserves the order of the remaining options, including the net filename before the architecture switch. [Pinned fastchess option setup](https://github.com/Disservin/fastchess/blob/d7b47e8dec6b564aaf4cbb2922ab37e6c6761e75/app/src/engine/uci_engine.cpp#L341-L357)

From the repository root, with chess 1.11.2 on the Python import path, run the readback without launching an engine.

```sh
cd forge-combo29/sol/job36
python3 analyze_matches36.py raw --prediction prediction.json
```

[UTC stamps](sol/job36/stamps.txt) · [Archive readback](sol/job36/readback.txt) · [Precommit tree](sol/job36/precommit-readback.txt)
