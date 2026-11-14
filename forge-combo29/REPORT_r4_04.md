# R4-04 screen: ContHist4PlyRead

Screening only. This is one fixed-node match of the existing UCI check `ContHist4PlyRead` (default false) on one binary, option on versus option off. It is not a strength claim, not an SPRT, and not a replication of another machine.

The owner's PC screen was +3.1 +/- 6.9 over 4000 games. That number is context for this screen. It is not a result from this run.

## Setup

Same binary both sides. Engine source was not modified. Tested tree `e04556ddc3a430b2e751159b0d46111ef56c8b89`. The option was introduced in `b68d49fedcc8e705484d06fb02cf0a417734839f` and is present, default off, in the tested tree.

Owner build: the host has AVX-512F and BMI2, so this is the non-portable lock (`FORGE_SPD_SLIDER_PEXT=1`, `FORGE_SPD_NNUE_ZMM=1`, `-march=x86-64-v4`), not the portable build.

Conditions: `go nodes 50000`, Threads 1, Hash 16, OwnBook false, `ContHist4PlyRead` true versus false. Book `UHO_Lichess_4852_v1.epd` (2632036 lines, sha256 `7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a`), order sequential, chunks of 500 openings, both colors (`-repeat`, 1000 games per full chunk). No resign adjudication and no score draw adjudication. Engines restart each game. Concurrency 2. fastchess alpha 1.8.3.

Match budget: sequential chunks until 6 hours from the first chunk, and not past 9 hours. Chunks already started are allowed to finish inside that outer limit.

## Command

```
/tmp/r4_04/fastchess-linux-x86-64/fastchess \
  -engine cmd=/agent/repos/dwqww/forge-combo29/build/forge name=ContHist4PlyRead-on nodes=50000 proto=uci restart=on \
    option.Threads=1 option.Hash=16 option.OwnBook=false option.ContHist4PlyRead=true \
  -engine cmd=/agent/repos/dwqww/forge-combo29/build/forge name=ContHist4PlyRead-off nodes=50000 proto=uci restart=on \
    option.Threads=1 option.Hash=16 option.OwnBook=false option.ContHist4PlyRead=false \
  -openings file=/tmp/r4_04/UHO_Lichess_4852_v1.epd format=epd order=sequential start=START \
  -rounds 500 -repeat -concurrency 2 -srand 1 \
  -recover -ratinginterval 100 -report penta=true \
  -event "r4-04 ContHist4PlyRead chunk CHUNK" -site "screen" \
  -pgnout file=games.pgn notation=san nodes=true \
  -log file=fastchess.log level=warn
```

`START` is 1, 501, 1001, ... and `CHUNK` is the chunk directory. The command is also in `tests_r4_04/command.txt`.

## Versions and hashes

```
tested_source e04556ddc3a430b2e751159b0d46111ef56c8b89
feature_intro b68d49fedcc8e705484d06fb02cf0a417734839f
engine_id Chess Engine Forge 6.4.24 candidate
compiler g++ (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0
cmake cmake version 3.28.3
fastchess fastchess alpha 1.8.3 compiled for ubuntu-22.04 20261107-d7b47e8 (CI) 
uname Linux 6.12.113+ #1 SMP PREEMPT_DYNAMIC Fri Nov 13 20:22:28 UTC 2026 x86_64
cpu Intel(R) Xeon(R) Processor
flags_avx512f avx512f
flags_bmi2 bmi2
nproc 4
march x86-64-v4
portable OFF
defines -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_NNUE_ZMM=1 -DFORGE_EXPOSE_TUNABLES=1 NDEBUG
cxx_flags -O3 -ffp-contract=off -fno-fast-math -march=x86-64-v4 -std=c++20
sha256_forge 4a624cf990c057c9a5d7847916b2d537a38ab6b95be4339dbec30a187f7ec984
sha256_book 7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a
sha256_book_zip 4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07
sha256_fastchess 091bf93dcf08e15d14b77bc2374d0a423982b32200e8add69f17bace3a34b31f
book_lines 2632036
book_name UHO_Lichess_4852_v1.epd
```

## Pins

Default option state (ContHist4PlyRead false). `scripts/check_pins.sh` on this binary:

```
net-on : 312866 862329 3024920 12389307 34048354
net-off: 375354 907205 2448617 13573040 24506465
perft5 : 4865609
PINS MATCH combo29
```

The three named pins are unchanged: bench 11 = 312866, bench 13 = 862329, perft 5 = 4865609. With the option on, bench 13 nodes move to 989877. That is the same on-value already recorded for this candidate. The screen uses one binary; the option is the only difference.

## bench 13 nps, five alternating runs

Order is off, on, off, on, off, on, off, on, off, on. Nodes stay on the pin when the option is off.

| run | option | nodes | time_ms | nps |
| ---: | --- | ---: | ---: | ---: |
| 1 | off | 862329 | 680 | 1268130 |
| 2 | on | 989877 | 970 | 1020491 |
| 3 | off | 862329 | 724 | 1191062 |
| 4 | on | 989877 | 639 | 1549103 |
| 5 | off | 862329 | 572 | 1507568 |
| 6 | on | 989877 | 686 | 1442969 |
| 7 | off | 862329 | 703 | 1226641 |
| 8 | on | 989877 | 711 | 1392232 |
| 9 | off | 862329 | 660 | 1306559 |
| 10 | on | 989877 | 765 | 1293956 |

Off mean nps 1299992 over 5 runs, nodes [862329]. On mean nps 1339750 over 5 runs, nodes [989877]. These nps figures are from this container. They are not a speed claim.

## Pooled screen

Scores are from the option-on side. W-L-D is wins, losses, draws for option on. Pentanomial bins are pair results over the two colors of one opening: LL, LD (or DL), DD+WL, WD (or DW), WW. Elo and LOS use the fastchess pentanomial model: pair score in game-point units, variance of that score, 95% interval z=1.959963984540054, Elo = -400 log10(1/p - 1), and the printed margin is half the distance between the Elo values of the two score bounds. LOS is the normal probability that the true score is above 0.5.

W-L-D (option on first): 245-247-508

Pentanomial [LL, LD, DD+WL, WD, WW]: 13, 133, 212, 127, 15

Elo 95%: -0.69 +/- 13.14 (-13.84 to 12.44)

LOS: 45.87%

Pairs: 500. Games: 1000. Score: 0.4990.

Pair notes:

- middle bin split DD=124 WL=88

## Chunks

### chunk001

sha256 695faf864f1c28ac47e6ebd674a783a5242b3df032ab0091e76cb207a31de960 bytes 5391805

```
chunk chunk001
meta finished start=1 rounds=500 elapsed_sec=5426
pgn_games 1000 W-L-D 245-247-508 other 0
pentanomial LL LD DD+WL WD WW [13, 133, 212, 127, 15]
openings checked 500 mismatches 0 start 1 rounds 500
middle bin split DD=124 WL=88
independent_pentanomial Elo -0.69 +/- 13.14 (95%) bounds -13.84 .. 12.44 LOS 45.87% score 0.4990 pairs 500
fastchess_tail:
Results of ContHist4PlyRead-on vs ContHist4PlyRead-off (50000 nodes, 1t, 16MB, UHO_Lichess_4852_v1.epd):
Elo: -0.69 +/- 13.14, nElo: -1.14 +/- 21.53
LOS: 45.87 %, DrawRatio: 42.40 %, PairsRatio: 0.97
Games: 1000, Wins: 245, Losses: 247, Draws: 508, Points: 499.0 (49.90 %)
Ptnml(0-2): [13, 133, 212, 127, 15]
```

