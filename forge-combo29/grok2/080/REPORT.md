# REPORT seat 080

Arm 10, named K3 in the arm table. Source seat: none. Switch: HindsightDepth. Model line in SEAT.txt: Grok 4.7.

## Patch

No patch. Arm 10 says exe P is exe B. sha256: none. `git apply` was not run.

Decision, written here because the brief says decide and write why: the CPU has AVX-512 and BMI2 (`avx512f`, `bmi2` in `/proc/cpuinfo`), and g++ is 13.3.0, so the release build used the CMake default `-march=x86-64-v4` and did not set `FORGE_PORTABLE`. One binary was built, `/agent/repos/base/forge-combo29/build/forge`, sha256 `e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83`. That path is both exe B and exe P. The `../work` worktree was created and left unpatched and unbuilt.

## Honesty

Command: `python3 measure.py honesty /agent/repos/base/forge-combo29/build/forge <this folder>`. One fresh process per line. `uci` then the command. No setoption. Table from `python3 read_results.py <this folder>`:

```
HONESTY
bench11 [('11', '312866')] expected ('11', '312866')
bench13 [('13', '862329')] expected ('13', '862329')
bench16 [('16', '3024920')] expected ('16', '3024920')
perft5 ['4865609'] expected 4865609
```

Those are the known numbers. Raw files: honesty_bench11.txt, honesty_bench13.txt, honesty_bench16.txt, honesty_perft5.txt, each with a .meta.

## Three O runs

Same `read_results.py` invocation, section O_RUNS. Commands were `python3 measure.py orun <exe> first200.fens o_B.txt o_B.meta omit`, then the same with `o_off` and `false`, then `o_on` and `true`. S14, then Threads 1, then Hash 16, then HindsightDepth only on the off and on runs. `ucinewgame` and `isready` before every position. `isready` after every setoption and every position.

```
O_RUNS
B n=200 sum=9500069 first=41311 24872 28574 differ_from_B=0
OFF n=200 sum=9500069 first=41311 24872 28574 differ_from_B=0
ON n=200 sum=9845650 first=23395 31504 35958 differ_from_B=200
expected B sum=9500069 first=41311 24872 28574
expected OFF equal to B on all 200
expected ON sum=9845650 first=23395 31504 35958 differ_from_B=200
```

Run (1) matches the known plain sum and the first three. Run (2) matches run (1) on all 200 positions. Run (3) matches the arm table: sum 9845650, first three 23395 / 31504 / 35958, 200 positions differ. first200.fens sha256 `ca2f576bb1632e46aa6143707de831d4d9ce361c5c6a9c7e7bc3fe913c8068b8` (200 lines).

## Book

`book_check.txt`, from `sha256sum` and `wc -l`:

```
zip 4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07  /home/ubuntu/uho.zip
epd 7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a  /home/ubuntu/uho.epd
lines   2632036 /home/ubuntu/uho.epd
    29244 /home/ubuntu/mine.epd
      300 /home/ubuntu/ctl.epd
       10 /home/ubuntu/ctl_arrive.epd
      200 /home/ubuntu/ctl_half.epd
  2661790 total
```

Zip and epd sha256 match the brief. Seat 080 took every 90th line of the book starting at line 80. Chunks used the top of mine.epd. The last 300 lines were the controls and were not used as chunk openings.

## C-ARRIVE

Command: `bash ~/match.sh ~/ctl_arrive.epd 10 ~/arrive.pgn -log file=$HOME/arrive.log level=trace engine=true`. fastchess accepted `engine=true`. Counts in arrive_check.txt: `setoption name HindsightDepth value true` = 20; `unknown option|invalid value|No such option` = 0. The 20 log lines around the first switch setoption are in that file. arrive=ok.

## C-HALF

Command: `bash ~/half.sh ~/ctl_half.epd 200 ~/half.pgn`, then `python3 ~/games_tsv.py tsv ~/half.pgn half.tsv`, then `python3 ~/games_tsv.py pool FULL half.tsv`. Output:

```
side FULL: games 400 W-L-D 225-43-132 pairs 200 (openings not in exactly 2 games: 0)
ptnml [1, 8, 54, 82, 55] Elo +170.59 95% [+145.26, +197.72]
```

FULL's Elo is +170.59, above +20. PASS.

## Pool

19 chunks, each 500 games (`wc -l` of chunk_*.tsv is 500 nineteen times, 9500 total). No FAILED line in ~/play.log. play.sh printed `minute 95: no new chunk` and exited. Command: `python3 ~/games_tsv.py pool ON chunk_*.tsv`. POOL.txt:

```
side ON: games 9500 W-L-D 2655-2376-4469 pairs 4750 (openings not in exactly 2 games: 0)
ptnml [193, 1110, 1924, 1271, 252] Elo +10.21 95% [+5.59, +14.83]
```

## suspicions, not proven

I do not suspect a swapped side or a missed node limit: C-HALF gave FULL +170.59 Elo. I do not suspect adjudication: match.sh passes no `-draw`, `-resign`, `-maxmoves`, or tablebase flag. fastchess wrote an untracked `config.json` in the repository root while playing; its adjudication switches are false in that file. I did not commit it, and I am not treating it as evidence.

## what I did NOT do

I did not open a pull request. I did not build a second binary. I did not apply a patch. I did not change engine source. I did not commit a PGN, an executable, or a net. I did not send any option besides S14, Threads, Hash, and HindsightDepth. I did not repeat an opening. I did not start a chunk after minute 95. I did not play the reserved last 300 openings of mine.epd.

## what I am NOT sure about

The RESULT.txt `id` field. I filled `K3`, the label on arm 10 in the brief. If that field was meant to be something else, this is the field I am not sure about. Honesty was measured once, on the one binary that is both exe B and exe P, so there is not a second set of honesty files named for P. The listing below was taken after POOL.txt, REPORT.md, and RESULT.txt existed and before this listing was appended, so the recorded size of REPORT.md does not include the listing text.

## times: see stamps.txt

## git status --short

Pasted output of `git status --short`:

```
?? config.json
?? forge-combo29/grok2/080/POOL.txt
?? forge-combo29/grok2/080/REPORT.md
?? forge-combo29/grok2/080/RESULT.txt
```

## ls -la

Pasted output of `ls -la` of this folder:

```
total 3116
drwxr-xr-x 2 ubuntu ubuntu   4096 Nov 20 15:02 .
drwxr-xr-x 3 ubuntu ubuntu   4096 Nov 20 13:23 ..
-rw-r--r-- 1 ubuntu ubuntu   2224 Nov 20 13:31 arrive_check.txt
-rw-r--r-- 1 ubuntu ubuntu    372 Nov 20 13:36 book_check.txt
-rw-r--r-- 1 ubuntu ubuntu  56672 Nov 20 14:20 chunk_10.out
-rw-r--r-- 1 ubuntu ubuntu  51549 Nov 20 14:20 chunk_10.tsv
-rw-r--r-- 1 ubuntu ubuntu  56309 Nov 20 14:25 chunk_11.out
-rw-r--r-- 1 ubuntu ubuntu  51549 Nov 20 14:25 chunk_11.tsv
-rw-r--r-- 1 ubuntu ubuntu  56403 Nov 20 14:29 chunk_12.out
-rw-r--r-- 1 ubuntu ubuntu  51444 Nov 20 14:29 chunk_12.tsv
-rw-r--r-- 1 ubuntu ubuntu  56473 Nov 20 14:34 chunk_13.out
-rw-r--r-- 1 ubuntu ubuntu  51539 Nov 20 14:34 chunk_13.tsv
-rw-r--r-- 1 ubuntu ubuntu  56252 Nov 20 14:38 chunk_14.out
-rw-r--r-- 1 ubuntu ubuntu  51513 Nov 20 14:38 chunk_14.tsv
-rw-r--r-- 1 ubuntu ubuntu  56096 Nov 20 14:42 chunk_15.out
-rw-r--r-- 1 ubuntu ubuntu  51385 Nov 20 14:42 chunk_15.tsv
-rw-r--r-- 1 ubuntu ubuntu  56394 Nov 20 14:47 chunk_16.out
-rw-r--r-- 1 ubuntu ubuntu  51519 Nov 20 14:47 chunk_16.tsv
-rw-r--r-- 1 ubuntu ubuntu  56130 Nov 20 14:51 chunk_17.out
-rw-r--r-- 1 ubuntu ubuntu  51427 Nov 20 14:51 chunk_17.tsv
-rw-r--r-- 1 ubuntu ubuntu  56166 Nov 20 14:55 chunk_18.out
-rw-r--r-- 1 ubuntu ubuntu  51423 Nov 20 14:55 chunk_18.tsv
-rw-r--r-- 1 ubuntu ubuntu  56280 Nov 20 15:00 chunk_19.out
-rw-r--r-- 1 ubuntu ubuntu  51497 Nov 20 15:00 chunk_19.tsv
-rw-r--r-- 1 ubuntu ubuntu  56217 Nov 20 13:41 chunk_1.out
-rw-r--r-- 1 ubuntu ubuntu  51121 Nov 20 13:41 chunk_1.tsv
-rw-r--r-- 1 ubuntu ubuntu  56548 Nov 20 13:45 chunk_2.out
-rw-r--r-- 1 ubuntu ubuntu  51429 Nov 20 13:45 chunk_2.tsv
-rw-r--r-- 1 ubuntu ubuntu  56181 Nov 20 13:49 chunk_3.out
-rw-r--r-- 1 ubuntu ubuntu  51403 Nov 20 13:49 chunk_3.tsv
-rw-r--r-- 1 ubuntu ubuntu  56551 Nov 20 13:53 chunk_4.out
-rw-r--r-- 1 ubuntu ubuntu  51314 Nov 20 13:53 chunk_4.tsv
-rw-r--r-- 1 ubuntu ubuntu  56605 Nov 20 13:58 chunk_5.out
-rw-r--r-- 1 ubuntu ubuntu  51389 Nov 20 13:58 chunk_5.tsv
-rw-r--r-- 1 ubuntu ubuntu  55868 Nov 20 14:02 chunk_6.out
-rw-r--r-- 1 ubuntu ubuntu  51327 Nov 20 14:02 chunk_6.tsv
-rw-r--r-- 1 ubuntu ubuntu  56501 Nov 20 14:07 chunk_7.out
-rw-r--r-- 1 ubuntu ubuntu  51413 Nov 20 14:07 chunk_7.tsv
-rw-r--r-- 1 ubuntu ubuntu  56399 Nov 20 14:11 chunk_8.out
-rw-r--r-- 1 ubuntu ubuntu  51561 Nov 20 14:11 chunk_8.tsv
-rw-r--r-- 1 ubuntu ubuntu  56464 Nov 20 14:16 chunk_9.out
-rw-r--r-- 1 ubuntu ubuntu  51519 Nov 20 14:16 chunk_9.tsv
-rw-r--r-- 1 ubuntu ubuntu  12861 Nov 20 13:29 first200.fens
-rw-r--r-- 1 ubuntu ubuntu   2779 Nov 20 13:31 games_tsv.py
-rw-r--r-- 1 ubuntu ubuntu  46828 Nov 20 13:36 half.out
-rw-r--r-- 1 ubuntu ubuntu   1065 Nov 20 13:31 half.sh
-rw-r--r-- 1 ubuntu ubuntu  42175 Nov 20 13:36 half.tsv
-rw-r--r-- 1 ubuntu ubuntu    197 Nov 20 13:29 honesty_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu   4994 Nov 20 13:29 honesty_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu    197 Nov 20 13:29 honesty_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu   4994 Nov 20 13:29 honesty_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu    197 Nov 20 13:29 honesty_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu   4996 Nov 20 13:29 honesty_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    199 Nov 20 13:29 honesty_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu   5207 Nov 20 13:29 honesty_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu   1049 Nov 20 13:31 match.sh
-rw-r--r-- 1 ubuntu ubuntu   6515 Nov 20 13:28 measure.py
-rw-r--r-- 1 ubuntu ubuntu    818 Nov 20 13:29 o_B.meta
-rw-r--r-- 1 ubuntu ubuntu 281896 Nov 20 13:29 o_B.txt
-rw-r--r-- 1 ubuntu ubuntu    881 Nov 20 13:29 o_off.meta
-rw-r--r-- 1 ubuntu ubuntu 281874 Nov 20 13:29 o_off.txt
-rw-r--r-- 1 ubuntu ubuntu    879 Nov 20 13:29 o_on.meta
-rw-r--r-- 1 ubuntu ubuntu 281965 Nov 20 13:29 o_on.txt
-rw-r--r-- 1 ubuntu ubuntu   1154 Nov 20 13:31 play.sh
-rw-r--r-- 1 ubuntu ubuntu    155 Nov 20 15:01 POOL.txt
-rw-r--r-- 1 ubuntu ubuntu   2495 Nov 20 13:28 read_results.py
-rw-r--r-- 1 ubuntu ubuntu   5533 Nov 20 15:01 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    230 Nov 20 15:02 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     76 Nov 20 13:23 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu   1089 Nov 20 15:01 stamps.txt
```
