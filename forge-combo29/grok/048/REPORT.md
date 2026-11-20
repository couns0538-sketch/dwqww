# Seat 048 IdeaK9

Idea 48 is the null-move reduction growing with (eval - beta) / a divisor.
The plain engine already adds that term, capped by the literal 3, and the divisor is already the spin NullMoveEvalDivisor.
I added check IdeaK9, default false, and spin IdeaK9_Cap, default 3, range 0 to 6. False keeps the literal 3. True reads the spin.

EXISTS: forge-combo29/src/search.cpp:1701
The statement continues on line 1702 with `std::min((eval - beta) / tune::NullMoveEvalDivisor, 3)`. NullMoveEvalDivisor is already a UCI spin, default 200, range 50 to 1000 (`src/search.cpp` lines 49 and 120). The cap 3 was the remaining literal. S14 sets NullMoveBase to 5 and leaves the divisor at 200.

Honesty, no setoption, exe B and exe P: bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, go perft 5 nodes 4865609.

The table is the `TABLE` section of `NUMBERS.txt`, which is the output of `report_numbers.py` reading the raw files:

```
step | status | evidence | result
STEP 2 honesty B | done | HONESTY_B.txt bench11.raw.txt bench13.raw.txt bench16.raw.txt goperft5.raw.txt | 312866 862329 3024920 4865609
STEP 2 O and G | done | SUMS.txt | O_d12.raw.txt positions 200 sum 9500069 first3 41311 24872 28574 ; G_d12.raw.txt positions 353 sum 18466239 first3 37203 70845 144383
STEP 3 apply | done | idea_apply_check.txt | exit 0
proof 1 honesty P | done | HONESTY_P.txt | 312866 862329 3024920 4865609
proof 2 off O | done | P_off_O_vs_B.txt | a=forge-combo29/grok/048/P_off_O.nodes.txt n=200 sum=9500069 | b=forge-combo29/grok/048/O_d12.nodes.txt n=200 sum=9500069 | compared=200 differ=0 same=200
proof 2 off G | done | P_off_G_vs_B.txt | a=forge-combo29/grok/048/P_off_G.nodes.txt n=353 sum=18466239 | b=forge-combo29/grok/048/G_d12.nodes.txt n=353 sum=18466239 | compared=353 differ=0 same=353
proof 3 on cap 3 | done | P_on_O_vs_B.txt | a=forge-combo29/grok/048/P_on_O.nodes.txt n=200 sum=9500069 | b=forge-combo29/grok/048/O_d12.nodes.txt n=200 sum=9500069 | compared=200 differ=0 same=200
proof 3 cap 0 | done | P_cap0_O_vs_B.txt | a=forge-combo29/grok/048/P_cap0_O.nodes.txt n=200 sum=9518441 | b=forge-combo29/grok/048/O_d12.nodes.txt n=200 sum=9500069 | compared=200 differ=172 same=28
proof 5 clean | done | asan_G100.raw.txt.meta.txt | symbols 35 lines 0
proof 5 bug | done | asan_bug.raw.txt.meta.txt | symbols 35 lines 2
match O+G | done | k9_og_match.log | Elo: -0.00 +/- 0.00, nElo: -nan +/- -nan ; Games: 1106, Wins: 336, Losses: 336, Draws: 434, Points: 553.0 (50.00 %)
match R | done | k9_match.log | Elo: -0.00 +/- 0.00, nElo: -nan +/- -nan ; Games: 600, Wins: 254, Losses: 254, Draws: 92, Points: 300.0 (50.00 %)
partner 098 off | done | partner098_off_vs_B.txt | a=forge-combo29/grok/048/partner098_off_O.nodes.txt n=200 sum=9500069 | b=forge-combo29/grok/048/O_d12.nodes.txt n=200 sum=9500069 | compared=200 differ=0 same=200
partner 098 on | done | partner098_on_vs_theirs.txt | their_file=partner098_their_on_O.raw.txt n=200 sum=9500069 first3 41311 24872 28574 | mine_file=partner098_on_O.nodes.txt n=200 sum=9500069 first3 41311 24872 28574 | compared=200 differ=0
partner 098 match | done | partner098_match.log | Elo: -0.00 +/- 0.00, nElo: -nan +/- -nan ; Games: 600, Wins: 254, Losses: 254, Draws: 92, Points: 300.0 (50.00 %)
partner 098 honesty | done | HONESTY_P098.txt | 312866 862329 3024920 4865609
seat 030 off | done | partner030_off_vs_B.txt | a=forge-combo29/grok/048/partner030_off_O.nodes.txt n=200 sum=9500069 | b=forge-combo29/grok/048/O_d12.nodes.txt n=200 sum=9500069 | compared=200 differ=0 same=200
seat 030 on | done | partner030_on_vs_B.txt | a=forge-combo29/grok/048/partner030_on_O.nodes.txt n=200 sum=10081213 | b=forge-combo29/grok/048/O_d12.nodes.txt n=200 sum=9500069 | compared=200 differ=200 same=0
seat 030 match | done | partner030_match.log | Elo: -0.58 +/- 11.30, nElo: -1.43 +/- 27.80 ; Games: 600, Wins: 253, Losses: 254, Draws: 93, Points: 299.5 (49.92 %)
```

## Proofs

(1) Exe P with no setoption matches the four honesty numbers. `HONESTY_P.txt`.

(2) S14 and IdeaK9 false: O depth 12 differs in 0 of 200 (sum 9,500,069) and G depth 12 differs in 0 of 353 (sum 18,466,239). Both match exe B position by position.

(3) S14 and IdeaK9 true with IdeaK9_Cap at its default 3: O depth 12 differs in 0 of 200, sum 9,500,069. That is the predicted sum. The zero is not a dead option. The same switch with IdeaK9_Cap 0 differs in 172 of 200 (sum 9,518,441). At the default the cap integer is still 3, so the reduction does not change. `uci` lists `option name IdeaK9 type check default false` and `option name IdeaK9_Cap type spin default 3 min 0 max 6`.

(4) See `P_idname.raw.txt`.

(5) AddressSanitizer and UndefinedBehaviorSanitizer build, IdeaK9 true, first 100 of G at depth 10: `nm -C` count of `__asan_` is 35, and the run has 0 sanitizer lines. The same runner on a scratch copy that reads past a 4-int heap array when the FEN is `8/8/8/8/8/8/8/K6k w - - 0 1` reports `ERROR: AddressSanitizer: heap-buffer-overflow`. That scratch copy is not in the patch.

`git apply --check` of `idea.patch.txt` on the base commit exited 0 (`idea_apply_check.txt`).

## Match

Prediction, committed before any patched search: O depth-12 sum 9,500,069, and Elo 0, wrong if the interval excludes 0.

O+G, 553 openings, both colours, 1,106 games, nodes 20000, S14, Threads 1, Hash 16, IdeaK9_Cap 3, true versus false: Elo -0.00 +/- 0.00, 336 wins, 336 losses, 434 draws, 553.0 points. Pentanomial (0-2) was [0, 0, 553, 0, 0]. Fastchess prints nElo as -nan when that paired score has no variance. The points are exactly half the games.

A separate 600-game match on R300 (seed 4801) was the same score shape: Elo -0.00 +/- 0.00, 254 wins, 254 losses, 92 draws.

## Partner

Partner for idea 48 is seat 098. Verdict: CONFIRMS.

Their patch adds the same check IdeaK9, default false, and the spin IdeaK9_Cap bound to a variable defaulting to 3, range 0 to 6. `git apply --check` on the base commit exited 0. Honesty on the rebuilt exe matched all four numbers. Switch false matched exe B on 0 of 200. Switch true matched their published O depth-12 rows on 0 of 200 (sum 9,500,069, first three 41311, 24872, 28574), which is what `proof_o.txt` on their branch claims. The 600-game match of their switch, both cap 3, on my R300, was Elo -0.00 +/- 0.00, 254 wins, 254 losses, 92 draws. They had predicted that true at cap 3 would not change the node sum and that the Elo would be 0.

Seat 030 had a patch before 098 did, so I also ran that protocol. IdeaB1 applies, honesty matches, switch false differs in 0 of 200, switch true differs in 200 of 200 (sum 10,081,213). They had not published switch-on rows. Their prediction interval was 7,500,000 to 12,000,000, and 10,081,213 sits inside it. The 600-game match was Elo -0.58 +/- 11.30, 253 wins, 254 losses, 93 draws. I do not use that as the partner verdict. The partner verdict is the 098 result.

## suspicions, not proven

Fastchess prints nElo -nan when every opening pair is balanced. The game score is still 50 percent exactly, and the Elo line is -0.00 +/- 0.00.

Seat 030's prior adds an enemy-piece count and a king-zone count that can include the same square twice. I did not prove that this double count is unintended. The match interval includes negative and positive values.

## what I did NOT do

I did not make NullMoveEvalDivisor into a new option. It already was one.

I did not play the 1,106-game match at a cap other than 3. The required match is at the option defaults.

I did not review every other seat. I reviewed 098, the idea partner, and 030, the first other patch that was on the remote.

The STEP 1 handoff fetch found no `FABLE_TO_grok_<N>.md`. The minute-60 fetch is the last line of `stamps.txt` if that clock had been reached before the push.

## what I am NOT sure about

I am not sure a tuner wants the cap range wider than 0 to 6. I chose 0 because a zero cap drops the added term (eval is at least beta when the null move is tried) and 6 because today's literal is 3 and the added piece is a small integer.

I am not sure a reader will treat on_differs of 0 as "the option never runs". At cap 3 it must be 0. At cap 0, 172 of 200 positions change.

## times: see stamps.txt

The pasted `git status --short` and `ls -la` of this folder follow.

## git status --short

```
 M forge-combo29/grok/048/stamps.txt
?? forge-combo29/grok/048/G100.epd
?? forge-combo29/grok/048/HONESTY_P.txt
?? forge-combo29/grok/048/HONESTY_P098.txt
?? forge-combo29/grok/048/NUMBERS.txt
?? forge-combo29/grok/048/OG.fens
?? forge-combo29/grok/048/P098_bench11.meta.txt
?? forge-combo29/grok/048/P098_bench11.raw.txt
?? forge-combo29/grok/048/P098_bench13.meta.txt
?? forge-combo29/grok/048/P098_bench13.raw.txt
?? forge-combo29/grok/048/P098_bench16.meta.txt
?? forge-combo29/grok/048/P098_bench16.raw.txt
?? forge-combo29/grok/048/P098_goperft5.meta.txt
?? forge-combo29/grok/048/P098_goperft5.raw.txt
?? forge-combo29/grok/048/P098_idname.raw.txt
?? forge-combo29/grok/048/P_bench11.meta.txt
?? forge-combo29/grok/048/P_bench11.raw.txt
?? forge-combo29/grok/048/P_bench13.meta.txt
?? forge-combo29/grok/048/P_bench13.raw.txt
?? forge-combo29/grok/048/P_bench16.meta.txt
?? forge-combo29/grok/048/P_bench16.raw.txt
?? forge-combo29/grok/048/P_cap0_O.nodes.txt
?? forge-combo29/grok/048/P_cap0_O.raw.txt
?? forge-combo29/grok/048/P_cap0_O.raw.txt.meta.txt
?? forge-combo29/grok/048/P_cap0_O_vs_B.txt
?? forge-combo29/grok/048/P_goperft5.meta.txt
?? forge-combo29/grok/048/P_goperft5.raw.txt
?? forge-combo29/grok/048/P_idname.raw.txt
?? forge-combo29/grok/048/P_off_G.nodes.txt
?? forge-combo29/grok/048/P_off_G.raw.txt
?? forge-combo29/grok/048/P_off_G.raw.txt.meta.txt
?? forge-combo29/grok/048/P_off_G_vs_B.txt
?? forge-combo29/grok/048/P_off_O.nodes.txt
?? forge-combo29/grok/048/P_off_O.raw.txt
?? forge-combo29/grok/048/P_off_O.raw.txt.meta.txt
?? forge-combo29/grok/048/P_off_O_vs_B.txt
?? forge-combo29/grok/048/P_on_O.nodes.txt
?? forge-combo29/grok/048/P_on_O.raw.txt
?? forge-combo29/grok/048/P_on_O.raw.txt.meta.txt
?? forge-combo29/grok/048/P_on_O_vs_B.txt
?? forge-combo29/grok/048/REPORT.md
?? forge-combo29/grok/048/RESULT.txt
?? forge-combo29/grok/048/asan_G100.raw.txt
?? forge-combo29/grok/048/asan_G100.raw.txt.meta.txt
?? forge-combo29/grok/048/asan_bug.raw.txt
?? forge-combo29/grok/048/asan_bug.raw.txt.meta.txt
?? forge-combo29/grok/048/bug.fen
?? forge-combo29/grok/048/idea.patch.txt
?? forge-combo29/grok/048/idea_apply_check.txt
?? forge-combo29/grok/048/insert_asan_bug.py
?? forge-combo29/grok/048/k9_match.log
?? forge-combo29/grok/048/k9_match.meta.txt
?? forge-combo29/grok/048/k9_match.pgn
?? forge-combo29/grok/048/k9_og_fastchess_config.json
?? forge-combo29/grok/048/k9_og_match.log
?? forge-combo29/grok/048/k9_og_match.meta.txt
?? forge-combo29/grok/048/k9_og_match.pgn
?? forge-combo29/grok/048/partner098.patch.txt
?? forge-combo29/grok/048/partner098_apply_check.txt
?? forge-combo29/grok/048/partner098_match.log
?? forge-combo29/grok/048/partner098_match.meta.txt
?? forge-combo29/grok/048/partner098_match.pgn
?? forge-combo29/grok/048/partner098_off_O.nodes.txt
?? forge-combo29/grok/048/partner098_off_O.raw.txt
?? forge-combo29/grok/048/partner098_off_O.raw.txt.meta.txt
?? forge-combo29/grok/048/partner098_off_vs_B.txt
?? forge-combo29/grok/048/partner098_on_O.nodes.txt
?? forge-combo29/grok/048/partner098_on_O.raw.txt
?? forge-combo29/grok/048/partner098_on_O.raw.txt.meta.txt
?? forge-combo29/grok/048/partner098_on_vs_theirs.txt
?? forge-combo29/grok/048/partner098_their_on_O.raw.txt
?? forge-combo29/grok/048/partner098_their_on_sums.txt
?? forge-combo29/grok/048/report_numbers.py
?? forge-combo29/grok/048/run_k9_match.sh
?? forge-combo29/grok/048/run_k9_og_match.sh
?? forge-combo29/grok/048/run_partner098_match.sh
?? forge-combo29/grok/048/sanitizer_run.py
```

## ls -la

```
total 13844
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 08:55 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:53 ..
-rw-r--r-- 1 ubuntu ubuntu    9948 Nov 20 08:17 asan_bug.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    1103 Nov 20 08:17 asan_bug.raw.txt.meta.txt
-rw-r--r-- 1 ubuntu ubuntu  130344 Nov 20 08:17 asan_G100.raw.txt
-rw-r--r-- 1 ubuntu ubuntu   11210 Nov 20 08:17 asan_G100.raw.txt.meta.txt
-rw-r--r-- 1 ubuntu ubuntu     284 Nov 20 07:59 bench11.meta.txt
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 07:59 bench11.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     284 Nov 20 07:59 bench13.meta.txt
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 07:59 bench13.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     286 Nov 20 07:59 bench16.meta.txt
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 07:59 bench16.raw.txt
-rw-r--r-- 1 ubuntu ubuntu      28 Nov 20 08:16 bug.fen
-rw-r--r-- 1 ubuntu ubuntu     787 Nov 20 08:06 compare_rows.py
-rw-r--r-- 1 ubuntu ubuntu    1099 Nov 20 08:13 DECISION.txt
-rw-r--r-- 1 ubuntu ubuntu   12861 Nov 20 07:59 first200.fens
-rw-r--r-- 1 ubuntu ubuntu    5009 Nov 20 08:16 G100.epd
-rw-r--r-- 1 ubuntu ubuntu   21123 Nov 20 08:00 G_d12.nodes.txt
-rw-r--r-- 1 ubuntu ubuntu  544904 Nov 20 08:00 G_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu   36977 Nov 20 08:00 G_d12.raw.txt.meta.txt
-rw-r--r-- 1 ubuntu ubuntu     288 Nov 20 07:59 goperft5.meta.txt
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 07:59 goperft5.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    2821 Nov 20 07:59 honesty_b.py
-rw-r--r-- 1 ubuntu ubuntu     657 Nov 20 07:59 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu    2634 Nov 20 08:05 honesty_exe.py
-rw-r--r-- 1 ubuntu ubuntu     657 Nov 20 08:06 HONESTY_P030.txt
-rw-r--r-- 1 ubuntu ubuntu     657 Nov 20 08:22 HONESTY_P098.txt
-rw-r--r-- 1 ubuntu ubuntu     657 Nov 20 08:14 HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu      70 Nov 20 08:14 idea_apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu    5457 Nov 20 08:14 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    4933 Nov 20 07:59 idname.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    1120 Nov 20 08:16 insert_asan_bug.py
-rw-r--r-- 1 ubuntu ubuntu   80945 Nov 20 08:21 k9_match.log
-rw-r--r-- 1 ubuntu ubuntu     359 Nov 20 08:21 k9_match.meta.txt
-rw-r--r-- 1 ubuntu ubuntu 1732304 Nov 20 08:21 k9_match.pgn
-rw-r--r-- 1 ubuntu ubuntu    7127 Nov 20 08:33 k9_og_fastchess_config.json
-rw-r--r-- 1 ubuntu ubuntu  156028 Nov 20 08:33 k9_og_match.log
-rw-r--r-- 1 ubuntu ubuntu     359 Nov 20 08:33 k9_og_match.meta.txt
-rw-r--r-- 1 ubuntu ubuntu 3496768 Nov 20 08:33 k9_og_match.pgn
-rw-r--r-- 1 ubuntu ubuntu    1553 Nov 20 08:04 make_r.py
-rw-r--r-- 1 ubuntu ubuntu    7131 Nov 20 08:04 measure_set.py
-rw-r--r-- 1 ubuntu ubuntu    5308 Nov 20 08:37 NUMBERS.txt
-rw-r--r-- 1 ubuntu ubuntu   14757 Nov 20 08:00 O_d12.nodes.txt
-rw-r--r-- 1 ubuntu ubuntu  306247 Nov 20 08:00 O_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu   24191 Nov 20 08:00 O_d12.raw.txt.meta.txt
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:23 OG.fens
-rw-r--r-- 1 ubuntu ubuntu     287 Nov 20 08:06 P030_bench11.meta.txt
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:06 P030_bench11.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     287 Nov 20 08:06 P030_bench13.meta.txt
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:06 P030_bench13.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     289 Nov 20 08:06 P030_bench16.meta.txt
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:06 P030_bench16.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     291 Nov 20 08:06 P030_goperft5.meta.txt
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:06 P030_goperft5.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    5094 Nov 20 08:06 P030_idname.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     284 Nov 20 08:22 P098_bench11.meta.txt
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:22 P098_bench11.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     284 Nov 20 08:22 P098_bench13.meta.txt
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:22 P098_bench13.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     286 Nov 20 08:22 P098_bench16.meta.txt
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:22 P098_bench16.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     288 Nov 20 08:22 P098_goperft5.meta.txt
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:22 P098_goperft5.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    5032 Nov 20 08:22 P098_idname.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     118 Nov 20 08:13 partner030_apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu   81138 Nov 20 08:11 partner030_match.log
-rw-r--r-- 1 ubuntu ubuntu     365 Nov 20 08:11 partner030_match.meta.txt
-rw-r--r-- 1 ubuntu ubuntu 1793656 Nov 20 08:11 partner030_match.pgn
-rw-r--r-- 1 ubuntu ubuntu   14757 Nov 20 08:06 partner030_off_O.nodes.txt
-rw-r--r-- 1 ubuntu ubuntu  306311 Nov 20 08:06 partner030_off_O.raw.txt
-rw-r--r-- 1 ubuntu ubuntu   24236 Nov 20 08:06 partner030_off_O.raw.txt.meta.txt
-rw-r--r-- 1 ubuntu ubuntu     160 Nov 20 08:06 partner030_off_vs_B.txt
-rw-r--r-- 1 ubuntu ubuntu   14759 Nov 20 08:06 partner030_on_O.nodes.txt
-rw-r--r-- 1 ubuntu ubuntu  307274 Nov 20 08:06 partner030_on_O.raw.txt
-rw-r--r-- 1 ubuntu ubuntu   24235 Nov 20 08:06 partner030_on_O.raw.txt.meta.txt
-rw-r--r-- 1 ubuntu ubuntu     160 Nov 20 08:06 partner030_on_vs_B.txt
-rw-r--r-- 1 ubuntu ubuntu    9073 Nov 20 08:03 partner030.patch.txt
-rw-r--r-- 1 ubuntu ubuntu      75 Nov 20 08:22 partner098_apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu   80945 Nov 20 08:26 partner098_match.log
-rw-r--r-- 1 ubuntu ubuntu     359 Nov 20 08:26 partner098_match.meta.txt
-rw-r--r-- 1 ubuntu ubuntu 1732304 Nov 20 08:26 partner098_match.pgn
-rw-r--r-- 1 ubuntu ubuntu   14757 Nov 20 08:22 partner098_off_O.nodes.txt
-rw-r--r-- 1 ubuntu ubuntu  306512 Nov 20 08:22 partner098_off_O.raw.txt
-rw-r--r-- 1 ubuntu ubuntu   24233 Nov 20 08:22 partner098_off_O.raw.txt.meta.txt
-rw-r--r-- 1 ubuntu ubuntu     160 Nov 20 08:22 partner098_off_vs_B.txt
-rw-r--r-- 1 ubuntu ubuntu   14757 Nov 20 08:22 partner098_on_O.nodes.txt
-rw-r--r-- 1 ubuntu ubuntu  306655 Nov 20 08:22 partner098_on_O.raw.txt
-rw-r--r-- 1 ubuntu ubuntu   24274 Nov 20 08:22 partner098_on_O.raw.txt.meta.txt
-rw-r--r-- 1 ubuntu ubuntu     185 Nov 20 08:23 partner098_on_vs_theirs.txt
-rw-r--r-- 1 ubuntu ubuntu    5123 Nov 20 08:21 partner098.patch.txt
-rw-r--r-- 1 ubuntu ubuntu  310752 Nov 20 08:23 partner098_their_on_O.raw.txt
-rw-r--r-- 1 ubuntu ubuntu      75 Nov 20 08:22 partner098_their_on_sums.txt
-rw-r--r-- 1 ubuntu ubuntu     284 Nov 20 08:14 P_bench11.meta.txt
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:14 P_bench11.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     284 Nov 20 08:14 P_bench13.meta.txt
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:14 P_bench13.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     286 Nov 20 08:14 P_bench16.meta.txt
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:14 P_bench16.raw.txt
-rw-r--r-- 1 ubuntu ubuntu   14757 Nov 20 08:15 P_cap0_O.nodes.txt
-rw-r--r-- 1 ubuntu ubuntu  306761 Nov 20 08:15 P_cap0_O.raw.txt
-rw-r--r-- 1 ubuntu ubuntu   24274 Nov 20 08:15 P_cap0_O.raw.txt.meta.txt
-rw-r--r-- 1 ubuntu ubuntu     153 Nov 20 08:15 P_cap0_O_vs_B.txt
-rw-r--r-- 1 ubuntu ubuntu     288 Nov 20 08:14 P_goperft5.meta.txt
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:14 P_goperft5.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    5032 Nov 20 08:14 P_idname.raw.txt
-rw-r--r-- 1 ubuntu ubuntu   21123 Nov 20 08:14 P_off_G.nodes.txt
-rw-r--r-- 1 ubuntu ubuntu  545701 Nov 20 08:14 P_off_G.raw.txt
-rw-r--r-- 1 ubuntu ubuntu   37019 Nov 20 08:14 P_off_G.raw.txt.meta.txt
-rw-r--r-- 1 ubuntu ubuntu     153 Nov 20 08:15 P_off_G_vs_B.txt
-rw-r--r-- 1 ubuntu ubuntu   14757 Nov 20 08:14 P_off_O.nodes.txt
-rw-r--r-- 1 ubuntu ubuntu  306482 Nov 20 08:14 P_off_O.raw.txt
-rw-r--r-- 1 ubuntu ubuntu   24233 Nov 20 08:14 P_off_O.raw.txt.meta.txt
-rw-r--r-- 1 ubuntu ubuntu     151 Nov 20 08:15 P_off_O_vs_B.txt
-rw-r--r-- 1 ubuntu ubuntu   14757 Nov 20 08:15 P_on_O.nodes.txt
-rw-r--r-- 1 ubuntu ubuntu  306760 Nov 20 08:15 P_on_O.raw.txt
-rw-r--r-- 1 ubuntu ubuntu   24232 Nov 20 08:15 P_on_O.raw.txt.meta.txt
-rw-r--r-- 1 ubuntu ubuntu     150 Nov 20 08:15 P_on_O_vs_B.txt
-rw-r--r-- 1 ubuntu ubuntu     404 Nov 20 08:13 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu   19823 Nov 20 08:05 R300.fens
-rw-r--r-- 1 ubuntu ubuntu     157 Nov 20 08:05 R300.meta.txt
-rw-r--r-- 1 ubuntu ubuntu    1244 Nov 20 08:01 read_sums.py
-rw-r--r-- 1 ubuntu ubuntu    8297 Nov 20 08:55 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    6063 Nov 20 08:37 report_numbers.py
-rw-r--r-- 1 ubuntu ubuntu     212 Nov 20 08:37 RESULT.txt
-rwxr-xr-x 1 ubuntu ubuntu    1353 Nov 20 08:17 run_k9_match.sh
-rwxr-xr-x 1 ubuntu ubuntu    1366 Nov 20 08:23 run_k9_og_match.sh
-rwxr-xr-x 1 ubuntu ubuntu    1359 Nov 20 08:07 run_partner030_match.sh
-rwxr-xr-x 1 ubuntu ubuntu    1382 Nov 20 08:23 run_partner098_match.sh
-rw-r--r-- 1 ubuntu ubuntu    6151 Nov 20 08:15 sanitizer_run.py
-rw-r--r-- 1 ubuntu ubuntu      79 Nov 20 07:53 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu   17691 Nov 20 07:59 set_G.epd
-rw-r--r-- 1 ubuntu ubuntu     173 Nov 20 08:54 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu     132 Nov 20 08:01 SUMS.txt
```
