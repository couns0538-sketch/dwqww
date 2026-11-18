# sol3 — Job 1 Forge lock pins

Case A. Codex Cloud on Linux x86_64. Model GPT-6 (Codex).

## Build and test identity

- Source `for-fable-and-opus/astra-0017-v3-path` at `6b98f2170a3210e71beed04bbd2553972c253ed7`. Clean tracked source at configure and before recording results. CMake 4.2.3, Unix Makefiles, Release, GCC C++ 14.2.0 (Debian 14.2.0-19), libstdc++ `libstdc++.so.6.0.33` (Debian 14.2.0-19), glibc 2.41 (Debian `2.41-12+deb13u4`). Default `x86-64-v4`, PEXT and ZMM enabled, strict floating point, v3 compile path off.
- Linux binary SHA-256 `2f545495d4e3e2b59af49fbb18212ec2ed8ae297d801e58647cfea37cd18e785`. The build matches the SHA-256 in Sol’s separate Job 1 report.
- Embedded AL1 s198, 256 hidden units per side, weights-source SHA-256 `a7ebcf3a319675f347e6e8e3f2539901d38d8036cb9b5935f31dd43d084c9638`. No external net.
- Each command used a fresh engine process and explicitly set Threads 1, Hash 16 MiB, MultiPV 1, OwnBook false and UseNNUE true. Other options at defaults. `bench` creates and resets its own 16 MiB searcher per test position (`src/uci.cpp:599–619`). Perft uses startpos.
- Commands ran from `2026-11-18T06:36:47Z` to `2026-11-18T06:36:49Z` using the shell clock.

```sh
cmake -S forge-combo29 -B /workspace/work/build-sol3 -DCMAKE_BUILD_TYPE=Release
cmake --build /workspace/work/build-sol3 --parallel 4
```

Each process received these commands first. It then received its command below and `quit`.

```text
setoption name Threads value 1
setoption name Hash value 16
setoption name MultiPV value 1
setoption name OwnBook value false
setoption name UseNNUE value true
isready
```

## Facts

| Command | Lock expectation | Observed nodes |
| --- | ---: | ---: |
| `bench 11` | 312866 | 312866 |
| `bench 13` | 862329 | 862329 |
| `position startpos` then `go perft 5` | 4865609 | 4865609 |

All pins match `LOCK.md`. I summed the perft root rows independently and got 4865609. All three processes exited with empty stderr. Timing fields are raw measurements from this Linux session.

## Raw stdout

### `bench 11`

```text
readyok
info string bench depth 11 nodes 312866 time 469 nps 667091
```

### `bench 13`

```text
readyok
info string bench depth 13 nodes 862329 time 1204 nps 716220
```

### `position startpos` then `go perft 5`

```text
readyok
a2a3: 181046
b2b3: 215255
c2c3: 222861
d2d3: 328511
e2e3: 402988
f2f3: 178889
g2g3: 217210
h2h3: 181044
a2a4: 217832
b2b4: 216145
c2c4: 240082
d2d4: 361790
e2e4: 405385
f2f4: 198473
g2g4: 214048
h2h4: 218829
b1a3: 198572
b1c3: 234656
g1f3: 233491
g1h3: 198502
nodes 4865609
```

[First note, source observations and deciding tests](NOTES_sol3.md)

## Follow-up — Sol Job 12 independent readback and IirDepth replay

The new IirDepth 1 versus 2 result was **−5.70 Elo [−18.30, +6.91]** on 610 complete color-swapped pairs from a disjoint opening sample at 20,000 nodes per move per side. The earlier 1,000-pair result was −3.30 [−13.85, +7.25]. Both estimates are slightly negative and both intervals include zero. Conditioning on each run’s measured half-node control, only the Stockfish judge estimate falls inside either uncertainty interval.

### Facts

I downloaded Sol’s original Job 12 PGNs from `d1004bfdab19a4d21a23e26b511e8439b002b2a8` and parsed their moves and headers with my own code. Grouping by the PGN Round tag and checking FEN and colors reproduced all four game and pair counts. The original K move lists matched in 100/100 pairs. The original E lower endpoint computed with unrounded inputs is +0.02519. Sol printed +0.02 after subtracting fastchess’s rounded halfwidth `9.71` from its rounded point estimate `9.73`. The sign agrees. [Sol’s original report](https://github.com/couns0538-sketch/dwqww/blob/d1004bfdab19a4d21a23e26b511e8439b002b2a8/forge-combo29/REPORT_sol_job12.md)

| Original, from A’s perspective | Node budgets A/B | Seed | Pairs | W–L–D | Pentanomial | Elo [95% interval] |
| --- | --- | ---: | ---: | --- | --- | --- |
| K, identical | 20000/20000 | 7101 | 100 | 49–49–102 | 0,0,100,0,0 | 0.00 [0.00, 0.00] |
| C, half-node | 10000/20000 | 7102 | 200 | 37–222–141 | 57,86,43,13,1 | −173.89 [−201.36, −146.41] |
| E, EvalSwingMult 3 vs 0 | 20000/20000 | 7103 | 1000 | 555–499–946 | 35,234,411,280,40 | +9.73 [+0.03, +19.44] |
| I, IirDepth 1 vs 2 | 20000/20000 | 7104 | 1000 | 544–563–893 | 57,261,383,242,57 | −3.30 [−13.85, +7.25] |

All rows above reference the PC20 binary/net/options below and the original runner identified by Sol. I also compared Sol2’s later lock report with my own plain build above. Our binary hashes, both bench totals, and all 20 perft rows and the total agree across the Intel and AMD cloud hosts. [Sol2 report](https://github.com/couns0538-sketch/dwqww/blob/9ea5be9c33e959f998f44734aff89e2e8e5cecf9/forge-combo29/REPORT_sol2_job1.md)

| Independent replay, from A’s perspective | Node budgets A/B | Seed | Pairs | W–L–D | Pentanomial | Elo [95% interval] |
| --- | --- | ---: | ---: | --- | --- | --- |
| K, identical | 20000/20000 | 73031 | 100 | 61–61–78 | 0,0,100,0,0 | 0.00 [0.00, 0.00] |
| C, half-node | 10000/20000 | 73032 | 200 | 44–231–125 | 52,85,61,2,0 | −176.10 [−200.05, −152.16] |
| I, IirDepth 1 vs 2 | 20000/20000 | 73034 | 610 | 310–330–580 | 31,152,253,154,20 | −5.70 [−18.30, +6.91] |

K played the exact same ordered moves in both games of every opening pair. C cleared the predeclared gate of Elo ≤ −30 with the 95% upper endpoint below zero. I stopped at the pre-set `2026-11-18T07:26:00Z` cloud clock cutoff. The 610 scored pairs are rounds 1–610, with no partial round in the saved PGN. Its only adjudication was a draw. I normalized its interval by `abs(−176.1034)`, yielding −0.03235 [−0.10393, +0.03924]. Sol’s listed Stockfish S value −0.0196 is inside and Forge R value −0.5396 is outside.

### Suspicions

The agreement is consistent with a small effect around zero. The wider cutoff interval leaves modest effects in either direction plausible. One setting comparison cannot decide which judge transfers to other settings or networks.

### What I did not do

I ran IirDepth instead of duplicating Sol’s ongoing EvalSwingMult replay. I did not start the separate EvalSwingMult job described in Opus’s reply. All historical source reconstruction was in scratch. The Forge branch contains the note and reports as text. I made no owner-PC, training, tuning or engine source change.

### What I am not sure about

The live check covered only the first 610 pairs of the seeded 1,000-pair fixture at the chosen cutoff. The judge calculation treats the measured half-node Elo as a fixed denominator. The result does not estimate transfer to the owner’s net, timed searches or other search budgets.

### Replay clock and evidence

The scratch workspace `/workspace/work/sol3-replay` contains `independent_replay.py`, the full fixture files, original PGNs, replay PGNs, raw engine pins and runner output. Its retained hashes bind the table above to the raw files.

| Arm | Start UTC | End UTC | Opening fixture SHA-256 | Replay PGN SHA-256 | Raw runner output SHA-256 |
| --- | --- | --- | --- | --- | --- |
| K | `2026-11-18T06:44:10+00:00` | `2026-11-18T06:49:42+00:00` | `84d52e8d18904622e0f434f921b877fd387db04d0130555791f4c2afd5d57ab6` | `7b80ab3bd7f05fe9e761579bc08d872071cd9e85547b178db1e661bc8b216955` | `5de47228b05469f436417c1f702d9aa0137a052f4bc3b81d80c97d1b7d80b088` |
| C | `2026-11-18T06:49:44+00:00` | `2026-11-18T06:57:27+00:00` | `ae4814a99bed1b2e7690960a5c54c7ecdf2c7a114823c93e35a33a7413c4de26` | `a9649265bc21ba13e09336f36ed954f49c2e028d5131095829fc18c43a044fbd` | `a95524aa606e7b131c1ea04ca9ff204b4b2fc024431356931ef7b445202efecd` |
| I | `2026-11-18T06:57:29+00:00` | `2026-11-18T07:26:00+00:00` | `31cc5de9481e698a886d7a3cf1308bcb0bf6e2a0f1f62b7f73bc09a13b312b47` | `aa0f17332689d997129d69e2923edca70be5211329e624f72bdabe7c31a330bb` | `82350c826af5593a9436a08ae9c4f3f82da84aaa52e2faa14875ac258d4efa70` |
## Build and protocol

- The build starts at `6b98f2170a3210e71beed04bbd2553972c253ed7`. I reconstructed the already published PC r15 counting source in a disposable directory, applying the PC r15, counter and buttons diffs in that order with zero fuzz. Their SHA-256 values are `d6bd72c531f785f40421be1cc542743922a944fb0973d05831788440309c1a1a`, `ff3c25aa634966aa62cd9ce75326a6c148d03b2c24eb36d279a00d68b7a75488`, and `fb219e959e7e988cbc10ae1c235ce1894c226a06c57c61cde3669dfc0f4d9183`. The first is lines 56–2374 in the pinned handoff file. The following two are the pinned Sol text patches. [PC r15](https://github.com/couns0538-sketch/dwqww/blob/cea646630ab27e64dfee92c1bb334277c717c79d/forge-combo29/soak_all/FABLE_TO_swarm_5.md#L56) · [Counters](https://github.com/couns0538-sketch/dwqww/blob/d1004bfdab19a4d21a23e26b511e8439b002b2a8/forge-combo29/sol/job2/count.patch.txt) · [Buttons](https://github.com/couns0538-sketch/dwqww/blob/d1004bfdab19a4d21a23e26b511e8439b002b2a8/forge-combo29/sol/job4/buttons.patch.txt)
- Count build command `cmake -S counting-source -B counting-build -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_FLAGS=-DFORGE_MATE_ALPHA_GUARD=1`, then `cmake --build counting-build --parallel 2`. CMake 4.2.3, GCC 14.2.0, libstdc++ 6.0.33, glibc 2.41, x86-64-v4. Forge SHA-256 `63356d12c5505ab657e71ddd020e3ca27c8e8c6b4b1632bae343c57deef33333` exactly matches Sol’s Job 12 counting binary. Its embedded AL1 s198 weights-source SHA-256 is `a7ebcf3a319675f347e6e8e3f2539901d38d8036cb9b5935f31dd43d084c9638`.
- Fresh-process default pins were `312866`, `862329`, and `3024920` at bench 11/13/16, and `4865609` at startpos perft 5. S14 gave `242796`, `656517` at bench 11/13. PC20 gave `278024`, `587276` at bench 11/13. All used Threads 1, Hash 16 MiB, MultiPV 1, OwnBook false, UseNNUE true, the binary and embedded net above, and the applicable options below.
- Official fastchess `v1.8.3-alpha`, `d7b47e8dec6b564aaf4cbb2922ab37e6c6761e75`, `make -j2`, version `fastchess alpha 1.8.3 20261107-d7b47e8`. My runner binary SHA-256 is `cea635d07255a707df705ddced578d8af843a3547cb8f2b230a8a43bf82ed1b9`. It used four workers on `cpu.max = 400000 100000`. [Official source](https://github.com/Disservin/fastchess/tree/d7b47e8dec6b564aaf4cbb2922ab37e6c6761e75)
- Official `UHO_Lichess_4852_v1.epd` had 2,632,036 lines and SHA-256 `7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a`. Its archive SHA-256 is `4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07`. Sampling used Python 3.12.14. For each K, C, I arm in order, I drew `2 * pairs + 64` zero-based line indices with `random.Random(seed).sample(range(2632036), 2 * pairs + 64)`. I kept the first `pairs` indices whose opening’s first four FEN fields were absent from original I and all openings already accepted in this run. Fastchess played each resulting fixture in order with colors swapped. [Official archive](https://raw.githubusercontent.com/official-stockfish/books/37751b08db745aa02babfa74056dd1168b9da803/UHO_Lichess_4852_v1.epd.zip)
- The driver used `-each proto=uci -openings file=ARM.epd format=epd order=sequential -srand SEED -rounds PAIRS -games 2 -repeat -concurrency 4 -maxmoves 300 -pgnout file=ARM.pgn -ratinginterval 20`. Both engine clauses named the same build, used their own `nodes=N` budget as shown above, and used this option set. A's one `IirDepth` in I was 1. Every other `IirDepth` was 2. There were no extra draw or resign adjudication settings.

```text
Threads=1 Hash=16 MultiPV=1 OwnBook=false UseNNUE=true
S14: LmrQuietBase=93 LmrQuietDivisor=205 LmrNoisyBase=13 LmrNoisyDivisor=333
     LmrHistoryDivisor=5643 NullMoveBase=5 LmpBase=8 HistoryPruneMultiplier=2220
     HistoryBonusQuadratic=24 HistoryBonusLinear=54 HistoryBonusMax=2212
     SingularDepth=6 IirDepth=2 NonPawnCorrection=true
PC20 adds: CuckooRep=true HistRework=2 TtPruneV2=true CorrHistV2=true MateAlphaGuard=true
```

I parsed PGNs using python-chess 1.11.2. I scored a round only when both legal games used its selected opening and had A and B in opposite colors. The K control additionally required the same ordered UCI moves in both legs and split points. Elo is `400 log10(p/(1-p))` where `p` is mean points per game. The 95% pentanomial interval uses the population variance of the paired scores divided by the number of pairs, with score endpoints transformed to Elo to obtain the symmetric Elo halfwidth. Judge coverage conditions the normalization on the C point estimate. [Fastchess paired interval method](https://github.com/Disservin/fastchess/blob/d7b47e8dec6b564aaf4cbb2922ab37e6c6761e75/app/src/matchmaking/elo/elo_pentanomial.cpp#L9-L49)
