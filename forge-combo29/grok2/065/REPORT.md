# grok2 seat 065

Arm 5, id S10. Source seat 081, branch for-fable-and-opus/grok-081, commit b3cd11a46a7c966ed3a87fcbf1fca67f76ce09fa. Switch IdeaS10. Model Grok 4.7.

## Patch

sha256 of ~/arm.patch, from forge-combo29/grok2/065/build_note.txt:

```
196a7d108427fdf4a3456ba5587ec89207fa0365f39ac52806b7e30831c4e368  /home/ubuntu/arm.patch
```

That is the arm table sha256. `git apply --check` then `git apply` on the work tree at 6b98f2170a3210e71beed04bbd2553972c253ed7. The same file's diff stat:

```
 forge-combo29/include/forge/eval.hpp   |   3 +
 forge-combo29/include/forge/search.hpp |  10 ++
 forge-combo29/src/eval.cpp             |  26 ++++++
 forge-combo29/src/search.cpp           | 163 +++++++++++++++++++++++++++++++--
 forge-combo29/src/uci.cpp              |  13 ++-
 5 files changed, 208 insertions(+), 7 deletions(-)
```

Release builds used g++ 13.3.0, CMake Release, FORGE_PORTABLE left off, FORGE_MARCH left x86-64-v4. /proc/cpuinfo has avx512 and bmi2, so the portable flags were not added. Exe paths and sha256 are in build_note.txt and the .meta files. id name: Chess Engine Forge 6.4.24 candidate.

## Honesty

Pasted from forge-combo29/grok2/065/table_step2.txt, which is the stdout of table.py reading the raw honesty transcripts:

```
honesty
  B bench11 312866 expected 312866 ok
  B bench13 862329 expected 862329 ok
  B bench16 3024920 expected 3024920 ok
  B goperft5 4865609 expected 4865609 ok
  P bench11 312866 expected 312866 ok
  P bench13 862329 expected 862329 ok
  P bench16 3024920 expected 3024920 ok
  P goperft5 4865609 expected 4865609 ok
honesty_all ok
```

Each line is a fresh process. The measured command was the first thing sent. No setoption before it.

## Three O runs

Same table_step2.txt, against the arm table (B sum 9,500,069 and first three 41,311 / 24,872 / 28,574; S10 on sum 9,542,904, same first three, 10 positions differ):

```
B positions 200 sum 9500069 first 41311 / 24872 / 28574
Poff positions 200 sum 9500069 first 41311 / 24872 / 28574
Pon positions 200 sum 9542904 first 41311 / 24872 / 28574
Poff_vs_B equal 200 differ 0
Pon_vs_B differ 10
B_known yes
off_identical yes
on_ok yes expected_sum 9542904 expected_differ 10
```

S14, Threads 1 and Hash 16 were sent, then IdeaS10 false or true on exe P only. Rows, raw transcripts and .meta files are in this folder. first200.fens sha256 ca2f576bb1632e46aa6143707de831d4d9ce361c5c6a9c7e7bc3fe913c8068b8, 200 lines.

## Book

Pasted from forge-combo29/grok2/065/book_check.txt:

```
zip 4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07  /home/ubuntu/uho.zip
epd_lines 2632036
epd 7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a  /home/ubuntu/uho.epd
mine_lines 29245
seat 065
```

Both sha256 values match the brief. Seat 065 takes every 90th line starting at line 65. The last 300 of mine.epd were held for the controls and were not used in the chunks.

## C-ARRIVE and C-HALF

arrive_check.txt: grep_true 20, grep_bad 0. The engine log shows `ON <--- setoption name IdeaS10 value true`. No unknown option, invalid value, or No such option.

C-HALF, pasted from half_pool.txt (stdout of games_tsv.py pool FULL on half.tsv):

```
side FULL: games 400 W-L-D 218-37-145 pairs 200 (openings not in exactly 2 games: 0)
ptnml [0, 11, 46, 94, 49] Elo +169.49 95% [+145.17, +195.46]
```

FULL's Elo is above +20. Pass. 400 games, 200 pairs.

## POOL

21 chunks, each 500 games, 10500 games. No FAILED line in ~/play.log. play.sh stopped with `minute 95: no new chunk` after chunk 21. Chunk 21 finished at 2026-11-20T15:00:52Z, before minute 103, and was not killed.

Pasted from POOL.txt (stdout of games_tsv.py pool ON on chunk_*.tsv):

```
side ON: games 10500 W-L-D 2763-2865-4872 pairs 5250 (openings not in exactly 2 games: 0)
ptnml [176, 1037, 2899, 989, 149] Elo -3.38 95% [-7.12, +0.36]
```

## suspicions, not proven

The ON side is 3.38 Elo behind OFF. The 95% interval is [-7.12, +0.36], so this sample does not separate a small loss from no change. I do not claim a proven loss or a proven gain.

Short matches produced many mates. match.sh and half.sh pass no -draw, -resign, -maxmoves, or tablebase flags. The untracked fastchess config.json left in the repo root has resign, draw, maxmoves, and tb_adjudication enabled set to false. I have not proved why so many games mate at 20000 nodes.

## what I did NOT do

I did not open a pull request. I did not commit engine source, binaries, nets, or PGNs. I did not send the IdeaS10 spin options (Margin, Flat, Look, Shrink, Depth). I did not add FORGE_PORTABLE. I did not play the reserved 300 openings. I did not repeat an opening. I did not find a FABLE_TO_grok2 file on the handoff branch at any push. I did not commit config.json. I did not kill fastchess.

## what I am NOT sure about

I am not sure of the exact UCI line fastchess uses for nodes=20000. C-HALF shows the larger node budget won by +169.49 Elo and that the side named FULL is the one the pool script scored, which is the check the brief asked for.

On each honesty process I sent `uci` only after the bench or perft line, to record id name in that same process. The node lines match the known numbers.

The Elo and interval are the script's formula, copied from its stdout, not recomputed another way.

## times: see stamps.txt

The first stamp is 2026-11-20T13:23:07Z STEP 1. Later lines are in stamps.txt.

## git status --short

```
 M forge-combo29/grok2/065/stamps.txt
?? config.json
?? forge-combo29/grok2/065/POOL.txt
?? forge-combo29/grok2/065/REPORT.md
?? forge-combo29/grok2/065/RESULT.txt
?? forge-combo29/grok2/065/chunk_21.out
?? forge-combo29/grok2/065/chunk_21.tsv
```

## ls -la forge-combo29/grok2/065

```
total 3480
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 15:02 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:22 ..
-rw-r--r-- 1 ubuntu ubuntu   2087 Nov 20 13:31 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu    226 Nov 20 13:34 book_check.txt
-rw-r--r-- 1 ubuntu ubuntu    892 Nov 20 13:29 build_note.txt
-rw-r--r-- 1 ubuntu ubuntu  56418 Nov 20 14:15 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51346 Nov 20 14:15 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  56347 Nov 20 14:19 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51455 Nov 20 14:19 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  56045 Nov 20 14:24 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51459 Nov 20 14:24 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  56297 Nov 20 14:28 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu  51612 Nov 20 14:28 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu  56608 Nov 20 14:32 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu  51614 Nov 20 14:32 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu  56328 Nov 20 14:36 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu  51503 Nov 20 14:36 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu  56764 Nov 20 14:40 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu  51624 Nov 20 14:40 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu  56140 Nov 20 14:44 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu  51544 Nov 20 14:44 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu  56264 Nov 20 14:48 chunk_18.out
-rw-r--r-- 1 ubuntu ubuntu  51501 Nov 20 14:48 chunk_18.tsv
-rw-r--r-- 1 ubuntu ubuntu  56224 Nov 20 14:52 chunk_19.out
-rw-r--r-- 1 ubuntu ubuntu  51496 Nov 20 14:52 chunk_19.tsv
-rw-r--r-- 1 ubuntu ubuntu  56191 Nov 20 13:39 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  51162 Nov 20 13:39 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  56054 Nov 20 14:56 chunk_20.out
-rw-r--r-- 1 ubuntu ubuntu  51374 Nov 20 14:56 chunk_20.tsv
-rw-r--r-- 1 ubuntu ubuntu  56181 Nov 20 15:00 chunk_21.out
-rw-r--r-- 1 ubuntu ubuntu  51559 Nov 20 15:00 chunk_21.tsv
-rw-r--r-- 1 ubuntu ubuntu  56008 Nov 20 13:43 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51126 Nov 20 13:43 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  56509 Nov 20 13:47 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51411 Nov 20 13:47 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  56095 Nov 20 13:51 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51217 Nov 20 13:51 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  56567 Nov 20 13:55 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51484 Nov 20 13:55 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  56891 Nov 20 13:59 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51481 Nov 20 13:59 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  56301 Nov 20 14:03 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51527 Nov 20 14:03 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  56381 Nov 20 14:07 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51396 Nov 20 14:07 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  55944 Nov 20 14:11 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51458 Nov 20 14:11 chunk_9.tsv
-rw-r--r-- 1 ubuntu ubuntu   2779 Nov 20 13:31 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  46952 Nov 20 13:34 half.out
-rw-r--r-- 1 ubuntu ubuntu    146 Nov 20 13:34 half_pool.txt
-rw-r--r-- 1 ubuntu ubuntu   1037 Nov 20 13:31 half.sh
-rw-r--r-- 1 ubuntu ubuntu  42342 Nov 20 13:34 half.tsv
-rw-r--r-- 1 ubuntu ubuntu     46 Nov 20 13:34 half_tsv_count.txt
-rw-r--r-- 1 ubuntu ubuntu    201 Nov 20 13:27 honesty_B_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu   4994 Nov 20 13:27 honesty_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    201 Nov 20 13:27 honesty_B_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu   4994 Nov 20 13:27 honesty_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    201 Nov 20 13:27 honesty_B_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu   4996 Nov 20 13:27 honesty_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    203 Nov 20 13:27 honesty_B_goperft5.meta
-rw-r--r-- 1 ubuntu ubuntu   5207 Nov 20 13:27 honesty_B_goperft5.txt
-rw-r--r-- 1 ubuntu ubuntu    201 Nov 20 13:27 honesty_P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu   5342 Nov 20 13:27 honesty_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    201 Nov 20 13:27 honesty_P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu   5342 Nov 20 13:27 honesty_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    201 Nov 20 13:27 honesty_P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu   5344 Nov 20 13:27 honesty_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    203 Nov 20 13:27 honesty_P_goperft5.meta
-rw-r--r-- 1 ubuntu ubuntu   5555 Nov 20 13:27 honesty_P_goperft5.txt
-rw-r--r-- 1 ubuntu ubuntu   3577 Nov 20 13:26 honesty.py
-rw-r--r-- 1 ubuntu ubuntu   1020 Nov 20 13:31 match.sh
-rw-r--r-- 1 ubuntu ubuntu    906 Nov 20 13:27 orun_B.meta
-rw-r--r-- 1 ubuntu ubuntu  31950 Nov 20 13:27 orun_B.rows
-rw-r--r-- 1 ubuntu ubuntu 282034 Nov 20 13:27 orun_B.txt
-rw-r--r-- 1 ubuntu ubuntu    941 Nov 20 13:27 orun_Poff.meta
-rw-r--r-- 1 ubuntu ubuntu  31950 Nov 20 13:27 orun_Poff.rows
-rw-r--r-- 1 ubuntu ubuntu 282410 Nov 20 13:27 orun_Poff.txt
-rw-r--r-- 1 ubuntu ubuntu    940 Nov 20 13:27 orun_Pon.meta
-rw-r--r-- 1 ubuntu ubuntu  31948 Nov 20 13:27 orun_Pon.rows
-rw-r--r-- 1 ubuntu ubuntu 282413 Nov 20 13:27 orun_Pon.txt
-rw-r--r-- 1 ubuntu ubuntu   6456 Nov 20 13:27 orun.py
-rw-r--r-- 1 ubuntu ubuntu   1154 Nov 20 13:31 play.sh
-rw-r--r-- 1 ubuntu ubuntu    153 Nov 20 15:01 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu   5704 Nov 20 15:02 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    225 Nov 20 15:02 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     77 Nov 20 13:22 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu    754 Nov 20 15:02 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu   3210 Nov 20 13:27 table.py
-rw-r--r-- 1 ubuntu ubuntu    638 Nov 20 13:29 table_step2.txt
```
