# REPORT seat 078 arm 8

Arm 8, id K4b, source seat 043, commit 2f38a63656ec17062b581c933fcc77d961b946f1, switch IdeaK4.
exe P is the base engine plus that patch. exe B is the base commit 6b98f2170a3210e71beed04bbd2553972c253ed7.

## Patch sha256 and git apply
```
zip 4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07  /home/ubuntu/uho.zip
epd_lines 2632036
epd 7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a  /home/ubuntu/uho.epd
patch b325e8c17842f9dc4d70213aef8ab14897c733f609860807ea85e930d902dc81  /home/ubuntu/arm.patch
```
git apply --check and git apply both succeeded on ../work before the build. Recorded build commands:
```
g++: Ubuntu 13.3.0
cpu: AVX-512 and BMI2 present, so FORGE_PORTABLE was left OFF and FORGE_MARCH stayed the CMake default x86-64-v4
base: cmake -S /agent/repos/base/forge-combo29 -B /agent/repos/base/forge-combo29/build -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++
base: cmake --build /agent/repos/base/forge-combo29/build -j4
work: cmake -S /agent/repos/work/forge-combo29 -B /agent/repos/work/forge-combo29/build -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++
work: cmake --build /agent/repos/work/forge-combo29/build -j4
patch: git show 2f38a63656ec17062b581c933fcc77d961b946f1:forge-combo29/grok/043/idea.patch.txt applied in ../work
patch_sha256: b325e8c17842f9dc4d70213aef8ab14897c733f609860807ea85e930d902dc81
git_apply: check and apply both succeeded
decision: S14 options are sent in the listed order, then Threads 1, then Hash 16, then IdeaK4 true or false on exe P. IdeaK4_Shrink is never sent.
```
The patch sha256 matches the arm table (b325e8c17842f9dc4d70213aef8ab14897c733f609860807ea85e930d902dc81).

## Honesty
Fresh process per line, no setoption. Expected bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609, on both exe B and exe P.
```
honesty
B_bench11 312866 expected 312866 ok
B_bench13 862329 expected 862329 ok
B_bench16 3024920 expected 3024920 ok
B_perft5 4865609 expected 4865609 ok
P_bench11 312866 expected 312866 ok
P_bench13 862329 expected 862329 ok
P_bench16 3024920 expected 3024920 ok
P_perft5 4865609 expected 4865609 ok
```

## Three O runs
S14 in the listed order, then Threads 1, then Hash 16. IdeaK4 omitted on exe B, false on run 2, true on run 3. IdeaK4_Shrink was not sent. go depth 12, ucinewgame and isready before every position.
Table targets: run 1 sum 9500069, first 41311 / 24872 / 28574. Run 2 equal to run 1 on all 200. Run 3 sum 8983632, first 23741 / 21846 / 35911, 200 differ.
```
B positions 200 unparsed 0 sum 9500069 first [41311, 24872, 28574]
P_off positions 200 unparsed 0 sum 9500069 first [41311, 24872, 28574]
P_on positions 200 unparsed 0 sum 8983632 first [23741, 21846, 35911]
off_vs_B compared 200 differ 0
on_vs_B compared 200 differ 200
```
Per-position rows are the `rows` sections of o_summary.txt, produced by summarize.py from the raw transcripts.

## Book
Official file matched: zip 4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07, 2632036 lines, epd 7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a.
Seat 078 takes every 90th line starting at line 78. The last 300 of those lines were held out for the controls and were not used as match openings.

## C-ARRIVE and C-HALF
C-ARRIVE: setoption name IdeaK4 value true count and the refusal count, then 20 log lines around the first switch setoption.
```
grep_true 20
grep_bad 0
first_line 394
----- 20 log lines around the first setoption -----
```
C-HALF is FULL at 20000 nodes against HALF at 10000 nodes, both with IdeaK4 false. Pass requires FULL Elo above +20. games_tsv.py pool FULL printed:
```
side FULL: games 400 W-L-D 240-21-139 pairs 200 (openings not in exactly 2 games: 0)
ptnml [0, 4, 35, 99, 62] Elo +213.60 95% [+188.92, +240.37]
```

## Pool
Chunks counted: 20.
```
side ON: games 10000 W-L-D 2616-2689-4695 pairs 5000 (openings not in exactly 2 games: 0)
ptnml [239, 1276, 2039, 1211, 235] Elo -2.54 95% [-7.05, +1.97]
```

## suspicions, not proven
fastchess wrote an untracked config.json in the repository root while the controls ran from that directory. Its resign, draw, maxmoves, and tablebase switches are all disabled. Match commands passed no -draw, -resign, -maxmoves, or tablebase flags. Sample games ended by mate, threefold repetition, fifty-move rule, and insufficient material. That is consistent with no adjudication; it is not a line-by-line audit of every game.

## what I did NOT do
No pull request. No engine source edit and no commit of an exe, object file, net, or PGN. IdeaK4_Shrink was left at its default and was never sent. The last 300 openings of this seat's book slice were not used in the chunks. Openings were not repeated to add games. No adjudication options were enabled.

## what I am NOT sure about
The pool interval is the one games_tsv.py prints from the tsv files. I did not recompute it with fastchess over the concatenated PGNs, because those PGNs are not part of the commit. On C-HALF the same script and fastchess both printed Elo +213.60. I am not sure whether any two selected book lines are the same FEN; the pool line 'openings not in exactly 2 games' is the check I have.
No FABLE_TO_grok2 file was present on the handoff branch at the fetches recorded in the committer log.

## times
times: see stamps.txt

## git status --short
```
A  forge-combo29/grok2/078/POOL.txt
A  forge-combo29/grok2/078/REPORT.md
A  forge-combo29/grok2/078/RESULT.txt
A  forge-combo29/grok2/078/book_patch_sha.txt
M  forge-combo29/grok2/078/stamps.txt
?? config.json
```

## ls -la
```
total 3244
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 15:00 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:23 ..
-rw-r--r-- 1 ubuntu ubuntu   2177 Nov 20 13:35 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu    295 Nov 20 15:00 book_patch_sha.txt
-rw-r--r-- 1 ubuntu ubuntu    918 Nov 20 13:33 build.txt
-rw-r--r-- 1 ubuntu ubuntu  56464 Nov 20 14:18 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51381 Nov 20 14:18 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  56810 Nov 20 14:22 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51397 Nov 20 14:22 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  56177 Nov 20 14:26 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51472 Nov 20 14:26 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  56250 Nov 20 14:30 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu  51474 Nov 20 14:30 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu  56279 Nov 20 14:34 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu  51391 Nov 20 14:34 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu  56583 Nov 20 14:38 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu  51370 Nov 20 14:38 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu  56373 Nov 20 14:43 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu  51315 Nov 20 14:43 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu  56635 Nov 20 14:47 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu  51528 Nov 20 14:47 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu  56400 Nov 20 14:51 chunk_18.out
-rw-r--r-- 1 ubuntu ubuntu  51481 Nov 20 14:51 chunk_18.tsv
-rw-r--r-- 1 ubuntu ubuntu  56042 Nov 20 14:55 chunk_19.out
-rw-r--r-- 1 ubuntu ubuntu  51595 Nov 20 14:55 chunk_19.tsv
-rw-r--r-- 1 ubuntu ubuntu  57001 Nov 20 13:42 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  51386 Nov 20 13:42 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  56714 Nov 20 14:59 chunk_20.out
-rw-r--r-- 1 ubuntu ubuntu  51565 Nov 20 14:59 chunk_20.tsv
-rw-r--r-- 1 ubuntu ubuntu  56731 Nov 20 13:46 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51325 Nov 20 13:46 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  56441 Nov 20 13:50 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51232 Nov 20 13:50 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  56179 Nov 20 13:54 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51476 Nov 20 13:54 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  56296 Nov 20 13:57 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51299 Nov 20 13:57 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  56196 Nov 20 14:01 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51411 Nov 20 14:01 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  56031 Nov 20 14:05 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51510 Nov 20 14:05 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  56271 Nov 20 14:09 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51404 Nov 20 14:09 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  56292 Nov 20 14:14 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51217 Nov 20 14:14 chunk_9.tsv
-rw-r--r-- 1 ubuntu ubuntu   2779 Nov 20 13:34 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  46938 Nov 20 13:37 half.out
-rw-r--r-- 1 ubuntu ubuntu    145 Nov 20 13:37 half_pool.txt
-rw-r--r-- 1 ubuntu ubuntu   1057 Nov 20 13:34 half.sh
-rw-r--r-- 1 ubuntu ubuntu  42225 Nov 20 13:37 half.tsv
-rw-r--r-- 1 ubuntu ubuntu    339 Nov 20 13:27 honesty_B_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:27 honesty_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    339 Nov 20 13:27 honesty_B_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:27 honesty_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    339 Nov 20 13:27 honesty_B_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:27 honesty_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    341 Nov 20 13:27 honesty_B_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:27 honesty_B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    339 Nov 20 13:27 honesty_P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:27 honesty_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    339 Nov 20 13:27 honesty_P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:27 honesty_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    339 Nov 20 13:27 honesty_P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:27 honesty_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    341 Nov 20 13:27 honesty_P_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:27 honesty_P_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu   1096 Nov 20 13:27 honesty.sh
-rw-r--r-- 1 ubuntu ubuntu   1041 Nov 20 13:34 match.sh
-rw-r--r-- 1 ubuntu ubuntu   1081 Nov 20 13:32 o_B.meta
-rw-r--r-- 1 ubuntu ubuntu 281682 Nov 20 13:32 o_B.raw
-rw-r--r-- 1 ubuntu ubuntu   1116 Nov 20 13:32 o_off.meta
-rw-r--r-- 1 ubuntu ubuntu 281767 Nov 20 13:32 o_off.raw
-rw-r--r-- 1 ubuntu ubuntu   1114 Nov 20 13:32 o_on.meta
-rw-r--r-- 1 ubuntu ubuntu 280639 Nov 20 13:32 o_on.raw
-rw-r--r-- 1 ubuntu ubuntu   5901 Nov 20 13:32 o_run.py
-rw-r--r-- 1 ubuntu ubuntu   6287 Nov 20 15:00 o_summary.txt
-rw-r--r-- 1 ubuntu ubuntu   1154 Nov 20 13:34 play.sh
-rw-r--r-- 1 ubuntu ubuntu    154 Nov 20 15:00 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu   5339 Nov 20 15:00 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    226 Nov 20 15:00 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     75 Nov 20 13:23 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu    726 Nov 20 15:00 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu   3024 Nov 20 13:33 summarize.py
```
