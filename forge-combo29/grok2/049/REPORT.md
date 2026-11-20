# grok2 seat 049

Arm 9, id S13, source seat 016, commit cdde64371237fe7778c713655c0c4b5c957a5fe2, switch IdeaS13. exe P is /tmp/forge-work-build/forge. exe B is /tmp/forge-base-build/forge. Both are GCC 13.3.0 Release builds of forge-combo29 (default -march=x86-64-v4, PEXT and AVX-512 on; this machine has AVX-512 and BMI2).

## Patch

sha256 of ~/arm.patch, which is forge-combo29/grok/016/idea.patch.txt from for-fable-and-opus/grok-016:

```
f96367fc5831e1c956c88ce3554632630fd857daf9c580dd190fa4463b74acc4  /home/ubuntu/arm.patch
```

That is the arm table sha256. git apply --check and git apply in the work tree succeeded. git diff --stat there:

```
 forge-combo29/include/forge/search.hpp | 14 ++++++++++
 forge-combo29/src/search.cpp           | 47 ++++++++++++++++++++++++++++++++++
 forge-combo29/src/uci.cpp              |  4 ++-
 3 files changed, 64 insertions(+), 1 deletion(-)
```

IdeaS13_Lookback and IdeaS13_ReduceDivisor were left at the patch defaults. They were never sent.

## Honesty

Fresh process, no setoption. Expected bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609.

```
honesty_B_bench11.txt:info string bench depth 11 nodes 312866 time 164 nps 1907719
honesty_B_bench13.txt:info string bench depth 13 nodes 862329 time 431 nps 2000763
honesty_B_bench16.txt:info string bench depth 16 nodes 3024920 time 1441 nps 2099181
honesty_B_perft5.txt:nodes 4865609
honesty_P_bench11.txt:info string bench depth 11 nodes 312866 time 172 nps 1818988
honesty_P_bench13.txt:info string bench depth 13 nodes 862329 time 440 nps 1959838
honesty_P_bench16.txt:info string bench depth 16 nodes 3024920 time 1428 nps 2118291
honesty_P_perft5.txt:nodes 4865609
```

Both builds match. honesty=ok.

## Three O runs

FENs: for-fable-and-opus/kimi5-work, forge-combo29/tests_kimi5_job3/first200.fens, 200 lines, sha256 ca2f576bb1632e46aa6143707de831d4d9ce361c5c6a9c7e7bc3fe913c8068b8. S14, then Threads 1, then Hash 16. Run 2 also set IdeaS13 false. Run 3 also set IdeaS13 true. Output of o_table.py on o1.raw o2.raw o3.raw:

```
B n=200 sum=9500069 first=41311 24872 28574
Poff n=200 sum=9500069 first=41311 24872 28574
Pon n=200 sum=9722445 first=19900 22525 42778
off_identical 200 of 200
on_differ 200 of 200
table_B MATCH
table_off MATCH
table_on MATCH
```

Arm table for S13: on sum 9,722,445; first three 19,900 / 22,525 / 42,778; 200 differ. Run 1 matches 9,500,069 and 41,311 / 24,872 / 28,574. off_identical=yes. on_sum=9722445. on_ok=yes.

## Book

```
4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07  /home/ubuntu/uho.zip
7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a  /home/ubuntu/uho.epd
2632036 /home/ubuntu/uho.epd
```

Both hashes match the brief. book=ok. Seat 049 takes every 90th line of uho.epd starting at line 49. The last 300 of those lines were held out for the controls.

## C-ARRIVE and C-HALF

arrive_check.txt counts: setoption name IdeaS13 value true = 20; unknown option|invalid value|No such option = 0. arrive=ok.

python3 games_tsv.py pool FULL half.tsv:

```
side FULL: games 400 W-L-D 221-33-146 pairs 200 (openings not in exactly 2 games: 0)
ptnml [0, 11, 44, 91, 54] Elo +177.22 95% [+152.08, +204.19]
```

FULL Elo +177.22 is above +20. half_elo=+177.22.

## Pool

12 chunks, each 500 games, 6000 games. No FAILED line in play.log. play.out ends with "minute 95: no new chunk". python3 games_tsv.py pool ON chunk_*.tsv, which is POOL.txt:

```
side ON: games 6000 W-L-D 1559-1655-2786 pairs 3000 (openings not in exactly 2 games: 0)
ptnml [160, 774, 1215, 704, 147] Elo -5.56 95% [-11.46, +0.34]
```

## suspicions, not proven

The watcher log jumps from 14:14 (chunk 10 pushed) to 15:03 (chunk 11 pushed). Chunks 11 and 12 still have Finished match, 500 tsv rows each, and every opening in the pool is in exactly two games. I did not prove a cause for the log gap.

Every tsv Termination field is the word normal. The chunk out files record mates, 3-fold repetition, and the fifty-move rule. I did not prove that the header "normal" means anything other than "fastchess finished the game".

## what I did NOT do

No pull request. No engine source committed and no engine source edited by me; the given patch was applied only in the work tree. No adjudication flags. No repeated openings. No arm 10 fallback. IdeaS13_Lookback and IdeaS13_ReduceDivisor were not sent. No FABLE_TO_grok2 file was on the handoff branch at any fetch, including the last one. PGN files, the exe, the net, and config.json were not committed.

## what I am NOT sure about

The 95% interval is -11.46 to +0.34. It contains 0, so I am not sure the -5.56 Elo is a real loss rather than noise. I am not sure why the watcher wrote nothing between 14:14 and 15:03.

times: see stamps.txt

## git status --short and ls -la

```
$ git status --short
 M forge-combo29/grok2/049/stamps.txt
?? config.json
?? forge-combo29/grok2/049/POOL.txt
?? forge-combo29/grok2/049/REPORT.md
?? forge-combo29/grok2/049/RESULT.txt

$ ls -la forge-combo29/grok2/049
total 2324
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 15:07 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:22 ..
-rw-r--r-- 1 ubuntu ubuntu   2272 Nov 20 13:28 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu  56476 Nov 20 14:11 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51492 Nov 20 14:11 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  56521 Nov 20 14:15 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51509 Nov 20 14:15 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  56302 Nov 20 15:04 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51454 Nov 20 15:04 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  55947 Nov 20 13:35 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  51049 Nov 20 13:35 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  56331 Nov 20 13:39 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51255 Nov 20 13:39 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  55815 Nov 20 13:43 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51314 Nov 20 13:43 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  56740 Nov 20 13:47 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51342 Nov 20 13:47 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  56427 Nov 20 13:51 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51425 Nov 20 13:51 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  56354 Nov 20 13:55 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51403 Nov 20 13:55 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  56110 Nov 20 13:59 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51355 Nov 20 13:59 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  56491 Nov 20 14:03 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51555 Nov 20 14:03 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  56395 Nov 20 14:07 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51329 Nov 20 14:07 chunk_9.tsv
-rw-r--r-- 1 ubuntu ubuntu   2779 Nov 20 13:27 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  47391 Nov 20 13:30 half.out
-rwxr-xr-x 1 ubuntu ubuntu   1025 Nov 20 13:31 half.sh
-rw-r--r-- 1 ubuntu ubuntu  42249 Nov 20 13:30 half.tsv
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:24 honesty_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:24 honesty_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:24 honesty_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:24 honesty_B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:24 honesty_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:24 honesty_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:24 honesty_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:24 honesty_P_perft5.txt
-rwxr-xr-x 1 ubuntu ubuntu    589 Nov 20 13:24 honesty.sh
-rwxr-xr-x 1 ubuntu ubuntu   1026 Nov 20 13:27 match.sh
-rw-r--r-- 1 ubuntu ubuntu    876 Nov 20 13:26 o1.meta
-rw-r--r-- 1 ubuntu ubuntu 281810 Nov 20 13:26 o1.raw
-rw-r--r-- 1 ubuntu ubuntu    911 Nov 20 13:26 o2.meta
-rw-r--r-- 1 ubuntu ubuntu 281935 Nov 20 13:26 o2.raw
-rw-r--r-- 1 ubuntu ubuntu    910 Nov 20 13:26 o3.meta
-rw-r--r-- 1 ubuntu ubuntu 282096 Nov 20 13:26 o3.raw
-rwxr-xr-x 1 ubuntu ubuntu   4016 Nov 20 13:26 o_harness.py
-rwxr-xr-x 1 ubuntu ubuntu   1942 Nov 20 13:26 o_table.py
-rwxr-xr-x 1 ubuntu ubuntu   1154 Nov 20 13:27 play.sh
-rw-r--r-- 1 ubuntu ubuntu    152 Nov 20 15:06 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu   5029 Nov 20 15:07 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    224 Nov 20 15:07 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     76 Nov 20 13:22 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu    523 Nov 20 15:07 stamps.txt
```
