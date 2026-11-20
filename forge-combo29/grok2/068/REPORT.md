# grok2 seat 068 arm 8

Arm 8, K4b. Source seat 043. Switch IdeaK4. Source commit 2f38a63656ec17062b581c933fcc77d961b946f1.

## Patch sha256 and git apply

```
patch_sha256 b325e8c17842f9dc4d70213aef8ab14897c733f609860807ea85e930d902dc81  /home/ubuntu/arm.patch
expected_sha256 b325e8c17842f9dc4d70213aef8ab14897c733f609860807ea85e930d902dc81
src_commit 2f38a63656ec17062b581c933fcc77d961b946f1
fetch_head_was 2f38a63656ec17062b581c933fcc77d961b946f1
git_apply --check then git apply: APPLY_OK
worktree_diff_stat:
 forge-combo29/include/forge/search.hpp |  2 ++
 forge-combo29/src/search.cpp           | 16 ++++++++++++++--
 forge-combo29/src/uci.cpp              |  4 ++++
 3 files changed, 20 insertions(+), 2 deletions(-)
```

The sha256 matches the arm table. `git apply --check` then `git apply` printed APPLY_OK. The patch was applied only in the work tree outside this repository.

## Honesty numbers

Fresh process, no setoption. Expected bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609.

```
HONESTY
B bench11 nodes 312866 expect 312866 match True
B bench13 nodes 862329 expect 862329 match True
B bench16 nodes 3024920 expect 3024920 match True
B perft5 nodes 4865609 expect 4865609 match True
P bench11 nodes 312866 expect 312866 match True
P bench13 nodes 862329 expect 862329 match True
P bench16 nodes 3024920 expect 3024920 match True
P perft5 nodes 4865609 expect 4865609 match True
O RUNS
B positions 200 sum 9500069 first 41311 / 24872 / 28574
B sum_match True
B first_match True
Poff positions 200 sum 9500069 first 41311 / 24872 / 28574
Poff sum_match True
Poff first_match True
Poff_vs_B differ 0 equal True
Pon positions 200 sum 8983632 first 23741 / 21846 / 35911
Pon sum_match True
Pon first_match True
Pon_vs_B differ 200 expect 200 match True
```

## Three O runs

Table for arm 8: off identical to plain; on sum 8983632; first three 23741 / 21846 / 35911; 200 differ.
Plain run (1) table: sum 9500069; first three 41311 / 24872 / 28574.
The block above is the output of `read_numbers.py` on the raw files. All of those comparisons matched.

## Book

```
4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07  /home/ubuntu/uho.zip
7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a  /home/ubuntu/uho.epd
2632036 /home/ubuntu/uho.epd
```

Our copy of the zip is 4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07 and of the epd is 7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a with 2632036 lines. The command output above is what this machine hashed.

## C-ARRIVE and C-HALF

arrive_check.txt begins:

```
grep_c_setoption_true 20
grep_c_unknown_invalid 0
```

true count is 20 (need 1 or more). refusal count is 0. C-ARRIVE passed.

half_pool.txt, from `games_tsv.py pool FULL` on half.tsv:

```
side FULL: games 400 W-L-D 225-39-136 pairs 200 (openings not in exactly 2 games: 0)
ptnml [4, 8, 39, 96, 53] Elo +174.99 95% [+148.52, +203.49]
```

FULL Elo is above +20. C-HALF passed.

## POOL.txt and chunks

Chunks counted: 23. Each counted tsv has 500 lines. Partial tsv left uncounted: none.

```
side ON: games 11500 W-L-D 3034-3057-5409 pairs 5750 (openings not in exactly 2 games: 0)
ptnml [302, 1406, 2345, 1407, 290] Elo -0.69 95% [-4.96, +3.57]
```

## suspicions, not proven

None. One intermediate pool I printed while a tsv was still being written showed 3900 games; that read was incomplete. The committed chunk files used here each have 500 lines, and this POOL.txt was made after those files were finished.

## what I did NOT do

I did not open a pull request. I did not commit an engine source file or a binary. I did not change the patch. I did not send IdeaK4_Shrink; it stayed at the patch default. I did not turn on adjudication. I did not replay an opening. I did not switch to arm 10, because run (3) matched the table. No FABLE_TO_grok2 file was on the channel at the fetches recorded in the finisher log. fastchess wrote config.json in the repository root because the match was started from that directory; resign and draw in it are disabled, and I did not commit that file.

## what I am NOT sure about

I am not sure the morning harness sent Threads and Hash before the S14 options rather than after them. The depth-12 node counts still matched the table on every position, so the searches that were compared are the searches in the raw files. I am not sure a game that was still running at minute 103, if one was killed, would have agreed with a finished game; a killed chunk is not in POOL.txt.

## times: see stamps.txt


## git status --short

```
 M forge-combo29/grok2/068/stamps.txt
?? config.json
?? forge-combo29/grok2/068/POOL.txt
?? forge-combo29/grok2/068/REPORT.md
?? forge-combo29/grok2/068/RESULT.txt
```

## ls -la

```
total 3576
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 15:01 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:23 ..
-rw-r--r-- 1 ubuntu ubuntu   2178 Nov 20 13:30 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu  56498 Nov 20 14:11 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51570 Nov 20 14:11 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  56342 Nov 20 14:15 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51606 Nov 20 14:15 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  56534 Nov 20 14:19 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51391 Nov 20 14:19 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  56589 Nov 20 14:22 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu  51580 Nov 20 14:22 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu  56599 Nov 20 14:26 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu  51517 Nov 20 14:26 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu  56281 Nov 20 14:30 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu  51583 Nov 20 14:30 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu  56304 Nov 20 14:34 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu  51447 Nov 20 14:34 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu  56363 Nov 20 14:38 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu  51540 Nov 20 14:38 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu  56012 Nov 20 14:42 chunk_18.out
-rw-r--r-- 1 ubuntu ubuntu  51306 Nov 20 14:42 chunk_18.tsv
-rw-r--r-- 1 ubuntu ubuntu  56471 Nov 20 14:45 chunk_19.out
-rw-r--r-- 1 ubuntu ubuntu  51565 Nov 20 14:45 chunk_19.tsv
-rw-r--r-- 1 ubuntu ubuntu  56545 Nov 20 13:36 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  51154 Nov 20 13:36 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  56753 Nov 20 14:49 chunk_20.out
-rw-r--r-- 1 ubuntu ubuntu  51540 Nov 20 14:49 chunk_20.tsv
-rw-r--r-- 1 ubuntu ubuntu  56326 Nov 20 14:53 chunk_21.out
-rw-r--r-- 1 ubuntu ubuntu  51562 Nov 20 14:53 chunk_21.tsv
-rw-r--r-- 1 ubuntu ubuntu  55879 Nov 20 14:57 chunk_22.out
-rw-r--r-- 1 ubuntu ubuntu  51522 Nov 20 14:57 chunk_22.tsv
-rw-r--r-- 1 ubuntu ubuntu  56382 Nov 20 15:01 chunk_23.out
-rw-r--r-- 1 ubuntu ubuntu  51511 Nov 20 15:01 chunk_23.tsv
-rw-r--r-- 1 ubuntu ubuntu  56696 Nov 20 13:40 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51406 Nov 20 13:40 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  56505 Nov 20 13:44 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51429 Nov 20 13:44 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  56124 Nov 20 13:48 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51368 Nov 20 13:48 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  57053 Nov 20 13:52 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51572 Nov 20 13:52 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  55962 Nov 20 13:55 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51387 Nov 20 13:55 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  56137 Nov 20 13:59 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51378 Nov 20 13:59 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  56275 Nov 20 14:03 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51389 Nov 20 14:03 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  56013 Nov 20 14:07 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51318 Nov 20 14:07 chunk_9.tsv
-rw-r--r-- 1 ubuntu ubuntu  12861 Nov 20 13:25 first200.fens
-rwxr-xr-x 1 ubuntu ubuntu   2779 Nov 20 13:29 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  46757 Nov 20 13:32 half.out
-rw-r--r-- 1 ubuntu ubuntu    145 Nov 20 13:32 half_pool.txt
-rwxr-xr-x 1 ubuntu ubuntu   1052 Nov 20 13:29 half.sh
-rw-r--r-- 1 ubuntu ubuntu  42296 Nov 20 13:32 half.tsv
-rw-r--r-- 1 ubuntu ubuntu    268 Nov 20 13:27 honesty_B_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:27 honesty_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    268 Nov 20 13:27 honesty_B_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:27 honesty_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    268 Nov 20 13:27 honesty_B_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:27 honesty_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    270 Nov 20 13:27 honesty_B_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:27 honesty_B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    268 Nov 20 13:27 honesty_P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:27 honesty_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    268 Nov 20 13:27 honesty_P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu     61 Nov 20 13:27 honesty_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    268 Nov 20 13:27 honesty_P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu     63 Nov 20 13:27 honesty_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    270 Nov 20 13:27 honesty_P_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    274 Nov 20 13:27 honesty_P_perft5.txt
-rwxr-xr-x 1 ubuntu ubuntu    945 Nov 20 13:26 honesty.sh
-rwxr-xr-x 1 ubuntu ubuntu   1041 Nov 20 13:29 match.sh
-rw-r--r-- 1 ubuntu ubuntu    768 Nov 20 13:28 numbers.txt
-rw-r--r-- 1 ubuntu ubuntu    784 Nov 20 13:27 o_B.meta
-rw-r--r-- 1 ubuntu ubuntu 281741 Nov 20 13:27 o_B.txt
-rw-r--r-- 1 ubuntu ubuntu    818 Nov 20 13:27 o_P_off.meta
-rw-r--r-- 1 ubuntu ubuntu 281870 Nov 20 13:27 o_P_off.txt
-rw-r--r-- 1 ubuntu ubuntu    817 Nov 20 13:28 o_P_on.meta
-rw-r--r-- 1 ubuntu ubuntu 280699 Nov 20 13:28 o_P_on.txt
-rwxr-xr-x 1 ubuntu ubuntu   4293 Nov 20 13:26 orun.py
-rw-r--r-- 1 ubuntu ubuntu    565 Nov 20 13:28 patch_apply.txt
-rwxr-xr-x 1 ubuntu ubuntu   1154 Nov 20 13:29 play.sh
-rw-r--r-- 1 ubuntu ubuntu    154 Nov 20 15:01 POOL.txt
-rwxr-xr-x 1 ubuntu ubuntu   3344 Nov 20 13:27 read_numbers.py
-rw-r--r-- 1 ubuntu ubuntu   4774 Nov 20 15:01 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    226 Nov 20 15:01 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     76 Nov 20 13:23 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu    834 Nov 20 15:01 stamps.txt
```
