# Seat 055 report

## Arm and source seat

Seat 055, arm 5, id S10. Source seat 081, commit b3cd11a46a7c966ed3a87fcbf1fca67f76ce09fa, SWITCH IdeaS10. Model Grok 4.7. The other IdeaS10_* options were left at their defaults and were never sent.

## Patch sha256 and git apply

The patch was fetched from for-fable-and-opus/grok-081, checked, and applied in /agent/repos/work before the patched build. That session printed FETCH b3cd11a46a7c966ed3a87fcbf1fca67f76ce09fa, sha256 196a7d108427fdf4a3456ba5587ec89207fa0365f39ac52806b7e30831c4e368, and APPLY_OK.

A later re-fetch, saved as patch_fetch.txt:

```
$ git fetch -q --depth 1 origin for-fable-and-opus/grok-081
$ git rev-parse FETCH_HEAD
b3cd11a46a7c966ed3a87fcbf1fca67f76ce09fa
$ git show FETCH_HEAD:forge-combo29/grok/081/idea.patch.txt | sha256sum
196a7d108427fdf4a3456ba5587ec89207fa0365f39ac52806b7e30831c4e368  -
$ sha256sum ~/arm.patch
196a7d108427fdf4a3456ba5587ec89207fa0365f39ac52806b7e30831c4e368  /home/ubuntu/arm.patch
$ cmp ~/arm.patch <(git show FETCH_HEAD:forge-combo29/grok/081/idea.patch.txt) && echo CMP_OK
CMP_OK
```

git apply --check then git apply exited 0. The work tree diff stat after apply was:

```
 forge-combo29/include/forge/eval.hpp   |   3 +
 forge-combo29/include/forge/search.hpp |  10 ++
 forge-combo29/src/eval.cpp             |  26 ++++++
 forge-combo29/src/search.cpp           | 163 +++++++++++++++++++++++++++++++--
 forge-combo29/src/uci.cpp              |  13 ++-
 5 files changed, 208 insertions(+), 7 deletions(-)
```

patch=ok. No engine source was committed.

## Honesty numbers

Both exes, a fresh process per command, no setoption on the measured process. Expected: bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, go perft 5 nodes 4865609.

```
honesty_B_bench11.txt:info string bench depth 11 nodes 312866 time 184 nps 1700358
honesty_B_bench13.txt:info string bench depth 13 nodes 862329 time 474 nps 1819259
honesty_B_bench16.txt:info string bench depth 16 nodes 3024920 time 1577 nps 1918148
honesty_B_perft5.txt:nodes 4865609
honesty_P_bench11.txt:info string bench depth 11 nodes 312866 time 178 nps 1757674
honesty_P_bench13.txt:info string bench depth 13 nodes 862329 time 496 nps 1738566
honesty_P_bench16.txt:info string bench depth 16 nodes 3024920 time 1884 nps 1605583
honesty_P_perft5.txt:nodes 4865609
```

honesty=ok. Exe B is /tmp/builds/base/forge (sha256 e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83). Exe P is /tmp/builds/work/forge (sha256 8430a8b654d504f7e69d11b1dc3daf73854fa5e2c9a477cc893c7eb1dddf80bc). id name on both: Chess Engine Forge 6.4.24 candidate. Release CMake, g++ 13.3.0, FORGE_PORTABLE left off because the machine has AVX-512 and BMI2.

## The three O runs

Known table for arm 5: exe B sum 9500069, first three 41311 / 24872 / 28574; SWITCH false identical on all 200; SWITCH true sum 9542904, first three 41311 / 24872 / 28574, 10 positions differ.

Output of summarize_o.py, which reads o_B.txt, o_Poff.txt and o_Pon.txt (also saved as o_summary.txt):

```
B sum 9500069 first 41311 24872 28574
Poff sum 9500069 first 41311 24872 28574
Pon sum 9542904 first 41311 24872 28574
Poff positions differing from B: 0
Pon positions differing from B: 10
Poff identical to B: yes
```

off_identical=yes. on_sum=9542904. on_ok=yes. S14, Threads 1 and Hash 16 were sent in that order, then IdeaS10 false or true on exe P. Each setoption and each position was followed by isready. No unknown option, invalid value, invalid FEN, or illegal move.

## Book

```
$ sha256sum ~/uho.zip
4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07  /home/ubuntu/uho.zip
$ wc -l ~/uho.epd
2632036 /home/ubuntu/uho.epd
$ sha256sum ~/uho.epd
7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a  /home/ubuntu/uho.epd
```

Both hashes and the line count match the brief. book=ok. Seat 055 took every 90th line of uho.epd starting at line 55 (29245 lines). The last 300 of those were held back as ctl.epd. Chunks used the top of mine.epd and did not reach those 300.

## C-ARRIVE and C-HALF

C-ARRIVE: match.sh on ctl_arrive.epd, 10 rounds, trace log with engine=true. From arrive_check.txt:

```
$ grep -c "setoption name IdeaS10 value true" ~/arrive.log
20
$ grep -c -E "unknown option|invalid value|No such option" ~/arrive.log
0
```

The 20 log lines around the first switch setoption are in arrive_check.txt. The engine ON received `setoption name IdeaS10 value true`. arrive=ok.

C-HALF: half.sh, FULL at 20000 nodes and HALF at 10000, both IdeaS10 false, nodes removed from -each. games_tsv.py pool FULL on half.tsv (half_pool.txt):

```
side FULL: games 400 W-L-D 218-38-144 pairs 200 (openings not in exactly 2 games: 0)
ptnml [2, 9, 49, 87, 53] Elo +168.40 95% [+142.74, +195.89]
```

The last Elo line in half.out is `Elo: 168.40 +/- 26.57`. +168.40 is above +20. PASS. half_elo=+168.40.

## POOL.txt and chunks

18 chunks, each 500 games, 9000 games. play.sh stopped with `minute 95: no new chunk` after chunk 18. No chunk was marked FAILED. Chunk outs contain no adjudication, resign, maxmoves, or tablebase phrases. Chunk 1 endings are mates, 3-fold, fifty-move, insufficient material, and stalemate. Mean plies over 9000 games: 144.957. No game under 10 plies. Unscored results: 0.

POOL.txt, from `python3 ~/games_tsv.py pool ON` on chunk_1.tsv through chunk_18.tsv:

```
side ON: games 9000 W-L-D 2332-2418-4250 pairs 4500 (openings not in exactly 2 games: 0)
ptnml [131, 899, 2499, 867, 104] Elo -3.32 95% [-7.26, +0.61]
```

## suspicions, not proven

patch_check.txt's `git rev-parse FETCH_HEAD` line prints d495aff45ff3354bcb19f5a07650e0857f41eec7. That was a stale FETCH_HEAD left by the later kimi5-work fetch, not the arm commit. The sha256 line in that same file is the real sha256 of ~/arm.patch and matches. patch_fetch.txt is the correction.

fastchess, started with the repository as its working directory, wrote an untracked config.json there (autosave). resign, draw, maxmoves, and tb_adjudication are all `"enabled": false`. The match command did not pass -draw, -resign, -maxmoves, -tb, or -config. I did not commit config.json.

## what I did NOT do

I did not open a pull request. I did not change engine source on this branch, and I did not commit an exe, a net, a PGN, or config.json. I did not send IdeaS10_Margin, IdeaS10_Flat, IdeaS10_Look, IdeaS10_Shrink, or IdeaS10_Depth. I did not fall back to arm 10. I did not repeat an opening. I did not force-push or write any other branch. No FABLE_TO_grok2 file existed on the handoff branch at any push, so nothing there changed the run. I did not build with FORGE_PORTABLE, because AVX-512 and BMI2 are present.

## what I am NOT sure about

The honesty meta files take "id name" from a separate `uci` process of the same exe. The measured process received only `bench` or `go perft`. I am not sure a reader would count that probe as part of the measured run. The node counts still match.

I am not sure whether fastchess would auto-load ./config.json without -config. I did not pass -config. The saved file has adjudication disabled, and the printed game endings are chess endings.

I am not sure the 95% interval in games_tsv.py is the same estimator fastchess prints. On C-HALF both printed 168.40 for the point Elo. The pool interval and fastchess's +/- are different calculations. RESULT.txt uses the games_tsv.py interval.

## times

times: see stamps.txt


## git status --short

```
 M forge-combo29/grok2/055/stamps.txt
?? config.json
?? forge-combo29/grok2/055/POOL.txt
?? forge-combo29/grok2/055/REPORT.md
?? forge-combo29/grok2/055/RESULT.txt
?? forge-combo29/grok2/055/chunk_18.out
?? forge-combo29/grok2/055/chunk_18.tsv
?? forge-combo29/grok2/055/half_pool.txt
```

## ls -la

```
total 3044
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 15:01 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:22 ..
-rw-r--r-- 1 ubuntu ubuntu   2219 Nov 20 13:29 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu    469 Nov 20 13:29 book_check.txt
-rw-r--r-- 1 ubuntu ubuntu  56098 Nov 20 14:20 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51515 Nov 20 14:20 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  56371 Nov 20 14:25 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51479 Nov 20 14:25 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  56035 Nov 20 14:30 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51455 Nov 20 14:30 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  56309 Nov 20 14:34 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu  51457 Nov 20 14:34 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu  56273 Nov 20 14:39 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu  51300 Nov 20 14:39 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu  55759 Nov 20 14:44 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu  51311 Nov 20 14:44 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu  56673 Nov 20 14:49 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu  51526 Nov 20 14:49 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu  56245 Nov 20 14:53 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu  51451 Nov 20 14:53 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu  56134 Nov 20 14:58 chunk_18.out
-rw-r--r-- 1 ubuntu ubuntu  51391 Nov 20 14:58 chunk_18.tsv
-rw-r--r-- 1 ubuntu ubuntu  56006 Nov 20 13:38 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  51170 Nov 20 13:38 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  56583 Nov 20 13:43 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51448 Nov 20 13:43 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  56708 Nov 20 13:48 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51430 Nov 20 13:48 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  56312 Nov 20 13:52 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51415 Nov 20 13:52 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  56552 Nov 20 13:57 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51376 Nov 20 13:57 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  56535 Nov 20 14:02 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51270 Nov 20 14:02 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  56545 Nov 20 14:07 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51690 Nov 20 14:07 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  56198 Nov 20 14:11 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51560 Nov 20 14:11 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  56170 Nov 20 14:16 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51473 Nov 20 14:16 chunk_9.tsv
-rw-r--r-- 1 ubuntu ubuntu  12861 Nov 20 13:26 first200.fens
-rw-r--r-- 1 ubuntu ubuntu   2779 Nov 20 13:29 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  46985 Nov 20 13:33 half.out
-rw-r--r-- 1 ubuntu ubuntu    145 Nov 20 15:01 half_pool.txt
-rw-r--r-- 1 ubuntu ubuntu    945 Nov 20 13:29 half.sh
-rw-r--r-- 1 ubuntu ubuntu  42479 Nov 20 13:32 half.tsv
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:27 honesty_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    278 Nov 20 13:27 honesty_B_bench11.txt.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:27 honesty_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    278 Nov 20 13:27 honesty_B_bench13.txt.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:27 honesty_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    278 Nov 20 13:27 honesty_B_bench16.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:27 honesty_B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    280 Nov 20 13:27 honesty_B_perft5.txt.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:27 honesty_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    278 Nov 20 13:27 honesty_P_bench11.txt.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:27 honesty_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    278 Nov 20 13:27 honesty_P_bench13.txt.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:27 honesty_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    278 Nov 20 13:27 honesty_P_bench16.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:27 honesty_P_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    280 Nov 20 13:27 honesty_P_perft5.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   1021 Nov 20 13:29 match.sh
-rw-r--r-- 1 ubuntu ubuntu 282083 Nov 20 13:27 o_B.txt
-rw-r--r-- 1 ubuntu ubuntu    813 Nov 20 13:27 o_B.txt.meta
-rw-r--r-- 1 ubuntu ubuntu 282557 Nov 20 13:27 o_Poff.txt
-rw-r--r-- 1 ubuntu ubuntu    848 Nov 20 13:27 o_Poff.txt.meta
-rw-r--r-- 1 ubuntu ubuntu 282508 Nov 20 13:27 o_Pon.txt
-rw-r--r-- 1 ubuntu ubuntu    847 Nov 20 13:27 o_Pon.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    214 Nov 20 13:28 o_summary.txt
-rw-r--r-- 1 ubuntu ubuntu    136 Nov 20 13:29 patch_check_note.txt
-rw-r--r-- 1 ubuntu ubuntu    772 Nov 20 13:28 patch_check.txt
-rw-r--r-- 1 ubuntu ubuntu    482 Nov 20 13:29 patch_fetch.txt
-rw-r--r-- 1 ubuntu ubuntu   1154 Nov 20 13:29 play.sh
-rw-r--r-- 1 ubuntu ubuntu    151 Nov 20 15:00 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu   7762 Nov 20 15:01 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    223 Nov 20 15:01 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu   8147 Nov 20 13:27 run_measures.py
-rw-r--r-- 1 ubuntu ubuntu     76 Nov 20 13:22 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu    672 Nov 20 15:01 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu   1464 Nov 20 13:27 summarize_o.py
```
