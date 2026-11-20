# Seat 074 arm 4

Arm 4, B8b. Source seat 028. Switch IdeaB8. Branch for-fable-and-opus/grok2-074.

## Patch

Source commit required: 4bf95fd80adf523e97fa250bb8572c946cf0fc75
Required sha256: f30e90f11db8f3d93e58f1e6ca6f2917deff3da632b8600a16da4bac3a9fc474

```
FETCH_HEAD 4bf95fd80adf523e97fa250bb8572c946cf0fc75
f30e90f11db8f3d93e58f1e6ca6f2917deff3da632b8600a16da4bac3a9fc474  /home/ubuntu/arm.patch
 forge-combo29/include/forge/search.hpp |  26 ++++++
 forge-combo29/src/search.cpp           | 147 ++++++++++++++++++++++++++++++++-
 forge-combo29/src/uci.cpp              |   4 +-
 3 files changed, 173 insertions(+), 4 deletions(-)
```

git apply --check and git apply on the work tree both succeeded (the work tree diff above is that applied patch). No engine file on this branch was edited.

## Honesty

exe B /tmp/build-b/forge sha256 e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83
exe P /tmp/build-p/forge sha256 09ec8eec0a7bfde0ff007bd033e93e53bc9c29c866e80e615d93339856bc4422
id name: Chess Engine Forge 6.4.24 candidate
No setoption before bench or perft. Output of summarize.py (option echoes omitted; they are in the .meta files):

```
honesty
B bench11 312866 expected 312866 ok
B bench13 862329 expected 862329 ok
B bench16 3024920 expected 3024920 ok
B perft5 4865609 expected 4865609 ok
P bench11 312866 expected 312866 ok
P bench13 862329 expected 862329 ok
P bench16 3024920 expected 3024920 ok
P perft5 4865609 expected 4865609 ok
meta
o B n 200 sum 9500069 first 41311 24872 28574
o Poff n 200 sum 9500069 first 41311 24872 28574
o Pon n 200 sum 9718009 first 17283 17878 31115
Poff positions differing from B: 0
Pon positions differing from B: 200
B sum expected 9500069 ok
B first expected 41311 24872 28574 ok
Pon sum expected 9718009 ok
Pon first expected 17283 17878 31115 ok
Pon differ expected 200 ok
Poff identical expected 0 ok
```

Known targets: bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609. Both exes matched.

## O runs

Table targets: (1) sum 9500069, first 41311 / 24872 / 28574. (2) identical to (1) on all 200. (3) sum 9718009, first 17283 / 17878 / 31115, 200 differ.

The same summarize.py output above is the measurement: B and Poff match (1), Pon matches (3), Poff differs on 0 positions, Pon differs on 200.

## Book

```
4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07  /home/ubuntu/uho.zip
7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a  /home/ubuntu/uho.epd
2632036 /home/ubuntu/uho.epd
```

Both digests match the brief. Seat 074 took every 90th line starting at line 74 (29245 lines). Chunks used the top of that file. The last 300 lines were the controls only.

## C-ARRIVE

grep -c of `setoption name IdeaB8 value true` in the trace log: 20
grep -c of unknown option / invalid value / No such option: 0
The 20 surrounding lines are in arrive_check.txt. fastchess did accept engine=true.

## C-HALF

FULL 20000 nodes against HALF 10000 nodes, IdeaB8 false on both. Re-read of half.tsv:

```
side FULL: games 400 W-L-D 234-31-135 pairs 200 (openings not in exactly 2 games: 0)
ptnml [1, 7, 38, 96, 58] Elo +194.34 95% [+168.84, +221.90]
```

PASS: FULL Elo is above +20.

## Pool

Chunks: 20. Each chunk_N.tsv is 500 lines. wc -l of chunk_*.tsv total: 10000.

POOL.txt, from `python3 ~/games_tsv.py pool ON forge-combo29/grok2/074/chunk_*.tsv`:

```
side ON: games 10000 W-L-D 2803-2487-4710 pairs 5000 (openings not in exactly 2 games: 0)
ptnml [184, 1163, 2053, 1353, 247] Elo +10.98 95% [+6.56, +15.41]
```

## suspicions, not proven

The arrive trace shows fastchess sending IdeaB8 before some of the -each options. The engine accepted the switch (20 sends, 0 refusals). I did not prove that send order changes any game.

The Elo interval is above zero in this sample. That is the printed interval, not a claim about the next sample.

## what I did NOT do

No pull request. No engine source committed. IdeaB8_Weight and IdeaB8_Swing were not sent. No adjudication, no resign, no draw cutoff, no maxmoves, no tablebases. Arm 10 was not used. Openings were not repeated. PGN, executables, and the net were not committed. No FABLE_TO_grok2 file was on the handoff branch.

## what I am NOT sure about

I counted IdeaB8 and the refusal strings in the arrive log. I did not count every S14 option across all 10000 match games.

The ls below was captured after this report body, POOL.txt, and RESULT.txt existed, and before the following command output was appended, so the byte size of REPORT.md in that listing is from before this section.

## times: see stamps.txt

```
$ git status --short
 M forge-combo29/grok2/074/stamps.txt
?? config.json
?? forge-combo29/grok2/074/POOL.txt
?? forge-combo29/grok2/074/REPORT.md
?? forge-combo29/grok2/074/RESULT.txt

$ ls -la forge-combo29/grok2/074
total 3260
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 15:05 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:23 ..
-rw-r--r-- 1 ubuntu ubuntu   2114 Nov 20 13:31 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu  56025 Nov 20 14:17 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51290 Nov 20 14:17 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  56862 Nov 20 14:21 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51649 Nov 20 14:21 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  55880 Nov 20 14:26 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51411 Nov 20 14:26 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  56719 Nov 20 14:30 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu  51577 Nov 20 14:30 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu  56578 Nov 20 14:34 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu  51554 Nov 20 14:34 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu  56420 Nov 20 14:38 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu  51525 Nov 20 14:38 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu  56097 Nov 20 14:43 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu  51346 Nov 20 14:43 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu  56643 Nov 20 14:47 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu  51634 Nov 20 14:47 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu  56307 Nov 20 14:51 chunk_18.out
-rw-r--r-- 1 ubuntu ubuntu  51455 Nov 20 14:51 chunk_18.tsv
-rw-r--r-- 1 ubuntu ubuntu  56207 Nov 20 14:55 chunk_19.out
-rw-r--r-- 1 ubuntu ubuntu  51554 Nov 20 14:55 chunk_19.tsv
-rw-r--r-- 1 ubuntu ubuntu  56009 Nov 20 13:39 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  51156 Nov 20 13:39 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  56249 Nov 20 14:59 chunk_20.out
-rw-r--r-- 1 ubuntu ubuntu  51462 Nov 20 14:59 chunk_20.tsv
-rw-r--r-- 1 ubuntu ubuntu  56540 Nov 20 13:43 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51278 Nov 20 13:43 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  56247 Nov 20 13:47 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51420 Nov 20 13:47 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  55907 Nov 20 13:51 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51363 Nov 20 13:51 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  56214 Nov 20 13:55 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51492 Nov 20 13:55 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  56568 Nov 20 13:59 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51644 Nov 20 13:59 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  56088 Nov 20 14:03 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51300 Nov 20 14:03 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  56415 Nov 20 14:08 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51348 Nov 20 14:08 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  56288 Nov 20 14:12 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51322 Nov 20 14:12 chunk_9.tsv
-rwxr-xr-x 1 ubuntu ubuntu   2779 Nov 20 13:31 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  46757 Nov 20 13:34 half.out
-rwxr-xr-x 1 ubuntu ubuntu   1032 Nov 20 13:31 half.sh
-rw-r--r-- 1 ubuntu ubuntu  42252 Nov 20 13:34 half.tsv
-rw-r--r-- 1 ubuntu ubuntu    174 Nov 20 13:28 honesty_B_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu   4994 Nov 20 13:28 honesty_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    174 Nov 20 13:28 honesty_B_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu   4994 Nov 20 13:28 honesty_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    174 Nov 20 13:28 honesty_B_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu   4996 Nov 20 13:28 honesty_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    176 Nov 20 13:28 honesty_B_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu   5207 Nov 20 13:28 honesty_B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    174 Nov 20 13:28 honesty_P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu   5162 Nov 20 13:28 honesty_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    174 Nov 20 13:28 honesty_P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu   5162 Nov 20 13:28 honesty_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    174 Nov 20 13:28 honesty_P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu   5164 Nov 20 13:28 honesty_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    176 Nov 20 13:28 honesty_P_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu   5375 Nov 20 13:28 honesty_P_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu   3339 Nov 20 13:27 honesty.py
-rwxr-xr-x 1 ubuntu ubuntu   1016 Nov 20 13:31 match.sh
-rw-r--r-- 1 ubuntu ubuntu    776 Nov 20 13:28 o_B.meta
-rw-r--r-- 1 ubuntu ubuntu 281902 Nov 20 13:28 o_B.txt
-rw-r--r-- 1 ubuntu ubuntu    810 Nov 20 13:28 o_Poff.meta
-rw-r--r-- 1 ubuntu ubuntu 282397 Nov 20 13:28 o_Poff.txt
-rw-r--r-- 1 ubuntu ubuntu    809 Nov 20 13:28 o_Pon.meta
-rw-r--r-- 1 ubuntu ubuntu 282752 Nov 20 13:28 o_Pon.txt
-rw-r--r-- 1 ubuntu ubuntu   5331 Nov 20 13:28 o_run.py
-rwxr-xr-x 1 ubuntu ubuntu   1154 Nov 20 13:31 play.sh
-rw-r--r-- 1 ubuntu ubuntu    156 Nov 20 15:04 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu   4823 Nov 20 15:05 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    228 Nov 20 15:05 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     76 Nov 20 13:23 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu   1174 Nov 20 15:05 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu   3002 Nov 20 13:29 summarize.py
```
