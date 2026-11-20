Arm 8, id K4b, source seat 043, commit 2f38a63656ec17062b581c933fcc77d961b946f1, SWITCH IdeaK4.
Seat file:
seat 008, arm 8, model Grok 4.7, 2026-11-20T13:20:56Z, token 178322159211515

## Patch sha256 and git apply

sha256sum arm.patch
b325e8c17842f9dc4d70213aef8ab14897c733f609860807ea85e930d902dc81  /home/ubuntu/arm.patch
git apply --check and git apply already succeeded; diff --stat of ../work:
 forge-combo29/include/forge/search.hpp |  2 ++
 forge-combo29/src/search.cpp           | 16 ++++++++++++++--
 forge-combo29/src/uci.cpp              |  4 ++++
 3 files changed, 20 insertions(+), 2 deletions(-)

The patch sha256 matches the arm table. git apply --check then git apply on the work tree changed three engine files. Those trees are outside the repository and were not committed.

## Honesty

honesty_B_bench11.txt: info string bench depth 11 nodes 312866 time 167 nps 1873449
honesty_B_bench13.txt: info string bench depth 13 nodes 862329 time 451 nps 1912037
honesty_B_bench16.txt: info string bench depth 16 nodes 3024920 time 1443 nps 2096271
honesty_B_perft5.txt: a2a3: 181046
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
honesty_P_bench11.txt: info string bench depth 11 nodes 312866 time 165 nps 1896157
honesty_P_bench13.txt: info string bench depth 13 nodes 862329 time 510 nps 1690841
honesty_P_bench16.txt: info string bench depth 16 nodes 3024920 time 1453 nps 2081844
honesty_P_perft5.txt: a2a3: 181046
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

Known targets: bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, perft 5 nodes 4865609. Both exes match. honesty=ok.

## Three O runs

Pasted o_table.py output:

B sum 9500069 first 41311 24872 28574
OFF sum 9500069 first 41311 24872 28574
ON sum 8983632 first 23741 21846 35911
OFF positions differing from B: 0
ON positions differing from B: 200
rows /agent/repos/dwqww/forge-combo29/grok2/008/o_rows_B.txt
rows /agent/repos/dwqww/forge-combo29/grok2/008/o_rows_OFF.txt
rows /agent/repos/dwqww/forge-combo29/grok2/008/o_rows_ON.txt

Arm table for K4b, SWITCH IdeaK4 true: sum 8983632; first three 23741 / 21846 / 35911; 200 differ.
Exe B target: sum 9500069; first three 41311 / 24872 / 28574.
OFF identical to B: yes
ON matches the arm table: yes

## Book

sha256sum uho.zip
4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07  /home/ubuntu/uho.zip
wc -l uho.epd
2632036 /home/ubuntu/uho.epd
sha256sum uho.epd
7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a  /home/ubuntu/uho.epd
book=ok

## C-ARRIVE

true_count=20
bad_count=0
first_setoption_line=394 window=384-403
[Engine] [13:27:04.880228] <     139642877765312>  OFF ---> option name CaptureFutilityBase type spin default 0 min 0 max 1000
[Engine] [13:27:04.880230] <     139642877765312>  OFF ---> option name CaptureFutilityMultiplier type spin default 250 min 0 max 1000
[Engine] [13:27:04.880232] <     139642877765312>  OFF ---> option name CaptureFutilityDepth type spin default 6 min 0 max 15
[Engine] [13:27:04.880234] <     139642877765312>  OFF ---> option name FailLowContinuationBonus type spin default 0 min 0 max 300
[Engine] [13:27:04.880236] <     139642877765312>  OFF ---> option name Clear Hash type button
[Engine] [13:27:04.880238] <     139642877765312>  OFF ---> uciok
[TRACE ] [13:27:04.880334] <     139642877765312> fastchess --- Refreshing engine ON
[TRACE ] [13:27:04.880342] <     139642877765312> fastchess --- Sending setoption to engine ON Threads 1
[Engine] [13:27:04.880345] <     139642877765312>  ON <--- setoption name Threads value 1
[TRACE ] [13:27:04.880352] <     139642877765312> fastchess --- Sending setoption to engine ON IdeaK4 true
[Engine] [13:27:04.880356] <     139642877765312>  ON <--- setoption name IdeaK4 value true
[Engine] [13:27:04.880346] <     139642886158016>  ON ---> id name Chess Engine Forge 6.4.24 candidate
[Engine] [13:27:04.880370] <     139642886158016>  ON ---> id author OpenAI
[Engine] [13:27:04.880373] <     139642886158016>  ON ---> option name Hash type spin default 32 min 1 max 2048
[Engine] [13:27:04.880378] <     139642886158016>  ON ---> option name Threads type spin default 1 min 1 max 256
[TRACE ] [13:27:04.880359] <     139642877765312> fastchess --- Sending setoption to engine ON Hash 16
[Engine] [13:27:04.880388] <     139642877765312>  ON <--- setoption name Hash value 16
[Engine] [13:27:04.880380] <     139642886158016>  ON ---> option name MultiPV type spin default 1 min 1 max 8
[TRACE ] [13:27:04.880392] <     139642877765312> fastchess --- Sending setoption to engine ON OwnBook false
[Engine] [13:27:04.880392] <     139642886158016>  ON ---> option name Move Overhead type spin default 10 min 0 max 1000

arrive=ok

## C-HALF

side FULL: games 400 W-L-D 234-35-131 pairs 200 (openings not in exactly 2 games: 0)
ptnml [1, 14, 35, 85, 65] Elo +189.69 95% [+161.73, +220.09]

half_elo=+189.69. PASS requires Elo above +20.

## Pool

chunks=22

side ON: games 11000 W-L-D 2894-3020-5086 pairs 5500 (openings not in exactly 2 games: 0)
ptnml [279, 1397, 2245, 1329, 250] Elo -3.98 95% [-8.29, +0.33]

## How games ended

Pasted tallies of the brace text on Finished game lines in chunk_*.out:

   2576 Black mates
   3445 Draw by 3-fold repetition
    834 Draw by fifty moves rule
    781 Draw by insufficient mating material
     26 Draw by stalemate
   3338 White mates

## suspicions, not proven

Partial pools while the match was still running stayed negative and the interval shrank toward zero from below. That is the same sample growing, not a second experiment.
fastchess wrote an untracked config.json in the repository root. Its adjudication switches are present and set enabled false. The match command does not pass -draw, -resign, or -maxmoves. The endings tally above is the check on how games actually stopped.

## what I did NOT do

Did not open a pull request. Did not commit engine source, the patch, an exe, a net, or a PGN. Did not send IdeaK4_Shrink or any option other than Hash, Threads, the S14 list, and IdeaK4. Did not build with FORGE_PORTABLE: this machine has AVX-512 and BMI2, so the default Release march x86-64-v4 was used. Did not replay an opening. Did not adjudicate. Did not run the morning seat 030 PGN example of games_tsv.py; C-HALF and the chunks are the runs of that script.

## what I am NOT sure about

I am not sure of the exact node count inside each match move, only that C-HALF's 20000-node side beat the 10000-node side by a wide margin and that fastchess logged setoption name IdeaK4 value true. I am not sure a later FABLE_TO_grok2 file appeared in the seconds after the last channel fetch recorded in stamps.txt; the supervisor fetches the channel at every chunk push and again before this report.

## times

times: see stamps.txt

2026-11-20T13:21:08Z STEP 1
2026-11-20T13:25:11Z STEP 2
2026-11-20T13:30:47Z STEP 3
2026-11-20T13:35:33Z chunks 1
2026-11-20T13:40:41Z chunks 2 
2026-11-20T13:45:30Z chunks 3 
2026-11-20T13:50:13Z chunks 4 
2026-11-20T13:54:52Z chunks 5 
2026-11-20T13:59:31Z chunks 6 7 
2026-11-20T14:03:47Z chunks 8
2026-11-20T14:08:19Z chunks 9
2026-11-20T14:12:51Z chunks 10
2026-11-20T14:17:23Z chunks 11
2026-11-20T14:21:55Z chunks 12
2026-11-20T14:26:27Z chunks 13
2026-11-20T14:30:59Z chunks 14
2026-11-20T14:35:31Z chunks 15
2026-11-20T14:40:03Z chunks 16 17
2026-11-20T14:44:35Z chunks 18
2026-11-20T14:49:07Z chunks 19
2026-11-20T14:53:39Z chunks 20
2026-11-20T14:58:11Z chunks 21
2026-11-20T15:02:43Z chunks 22
2026-11-20T15:02:47Z STEP 5

## git status --short

 M forge-combo29/grok2/008/stamps.txt
?? config.json
?? forge-combo29/grok2/008/POOL.txt
?? forge-combo29/grok2/008/REPORT.md
?? forge-combo29/grok2/008/RESULT.txt
?? forge-combo29/grok2/008/endings.txt

## ls -la

total 3544
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 15:02 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:20 ..
-rw-r--r-- 1 ubuntu ubuntu   2161 Nov 20 13:27 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu    253 Nov 20 13:30 book_sha.txt
-rw-r--r-- 1 ubuntu ubuntu  56269 Nov 20 14:11 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51480 Nov 20 14:11 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  56250 Nov 20 14:15 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51651 Nov 20 14:15 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  56352 Nov 20 14:19 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51416 Nov 20 14:19 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  56611 Nov 20 14:23 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu  51474 Nov 20 14:23 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu  56254 Nov 20 14:27 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu  51379 Nov 20 14:27 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu  56288 Nov 20 14:31 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu  51643 Nov 20 14:31 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu  56143 Nov 20 14:35 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu  51516 Nov 20 14:35 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu  56197 Nov 20 14:39 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu  51546 Nov 20 14:39 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu  56489 Nov 20 14:43 chunk_18.out
-rw-r--r-- 1 ubuntu ubuntu  51491 Nov 20 14:43 chunk_18.tsv
-rw-r--r-- 1 ubuntu ubuntu  56295 Nov 20 14:47 chunk_19.out
-rw-r--r-- 1 ubuntu ubuntu  51524 Nov 20 14:47 chunk_19.tsv
-rw-r--r-- 1 ubuntu ubuntu  56316 Nov 20 13:34 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  51223 Nov 20 13:34 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  56085 Nov 20 14:51 chunk_20.out
-rw-r--r-- 1 ubuntu ubuntu  51406 Nov 20 14:51 chunk_20.tsv
-rw-r--r-- 1 ubuntu ubuntu  56372 Nov 20 14:55 chunk_21.out
-rw-r--r-- 1 ubuntu ubuntu  51500 Nov 20 14:55 chunk_21.tsv
-rw-r--r-- 1 ubuntu ubuntu  55674 Nov 20 15:00 chunk_22.out
-rw-r--r-- 1 ubuntu ubuntu  51251 Nov 20 15:00 chunk_22.tsv
-rw-r--r-- 1 ubuntu ubuntu  56208 Nov 20 13:38 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51260 Nov 20 13:38 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  56349 Nov 20 13:42 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51346 Nov 20 13:42 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  56213 Nov 20 13:47 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51238 Nov 20 13:47 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  56214 Nov 20 13:51 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51300 Nov 20 13:51 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  56453 Nov 20 13:55 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51266 Nov 20 13:55 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  56606 Nov 20 13:59 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51396 Nov 20 13:59 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  56389 Nov 20 14:03 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51428 Nov 20 14:03 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  56084 Nov 20 14:07 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51367 Nov 20 14:07 chunk_9.tsv
-rw-r--r-- 1 ubuntu ubuntu    178 Nov 20 15:02 endings.txt
-rw-r--r-- 1 ubuntu ubuntu  12861 Nov 20 13:24 first200.fens
-rwxr-xr-x 1 ubuntu ubuntu   2779 Nov 20 13:27 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  46733 Nov 20 13:30 half.out
-rw-r--r-- 1 ubuntu ubuntu    146 Nov 20 13:30 half_pool.txt
-rwxr-xr-x 1 ubuntu ubuntu   1064 Nov 20 13:27 half.sh
-rw-r--r-- 1 ubuntu ubuntu  42246 Nov 20 13:30 half.tsv
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:22 honesty_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:22 honesty_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:22 honesty_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:22 honesty_B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:22 honesty_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:22 honesty_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:22 honesty_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:22 honesty_P_perft5.txt
-rwxr-xr-x 1 ubuntu ubuntu   1019 Nov 20 13:27 match.sh
-rw-r--r-- 1 ubuntu ubuntu     71 Nov 20 13:24 o_B.harness.log
-rw-r--r-- 1 ubuntu ubuntu    848 Nov 20 13:24 o_B.meta
-rw-r--r-- 1 ubuntu ubuntu 307173 Nov 20 13:24 o_B.raw
-rw-r--r-- 1 ubuntu ubuntu   4441 Nov 20 13:24 o_harness.py
-rw-r--r-- 1 ubuntu ubuntu     74 Nov 20 13:24 o_Poff.harness.log
-rw-r--r-- 1 ubuntu ubuntu    883 Nov 20 13:24 o_Poff.meta
-rw-r--r-- 1 ubuntu ubuntu 308921 Nov 20 13:24 o_Poff.raw
-rw-r--r-- 1 ubuntu ubuntu     73 Nov 20 13:24 o_Pon.harness.log
-rw-r--r-- 1 ubuntu ubuntu    881 Nov 20 13:24 o_Pon.meta
-rw-r--r-- 1 ubuntu ubuntu 307759 Nov 20 13:24 o_Pon.raw
-rw-r--r-- 1 ubuntu ubuntu   1896 Nov 20 13:25 o_rows_B.txt
-rw-r--r-- 1 ubuntu ubuntu   1896 Nov 20 13:25 o_rows_OFF.txt
-rw-r--r-- 1 ubuntu ubuntu   1894 Nov 20 13:25 o_rows_ON.txt
-rw-r--r-- 1 ubuntu ubuntu   2242 Nov 20 13:24 o_table.py
-rw-r--r-- 1 ubuntu ubuntu    372 Nov 20 13:25 o_table.txt
-rw-r--r-- 1 ubuntu ubuntu    395 Nov 20 13:25 patch_apply.txt
-rwxr-xr-x 1 ubuntu ubuntu   1154 Nov 20 13:27 play.sh
-rw-r--r-- 1 ubuntu ubuntu    154 Nov 20 15:02 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu   8171 Nov 20 15:02 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    226 Nov 20 15:02 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     77 Nov 20 13:20 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu    734 Nov 20 15:02 stamps.txt
