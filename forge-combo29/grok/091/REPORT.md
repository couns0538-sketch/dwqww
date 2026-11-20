# Seat 091, idea 41, IdeaK2

IdeaK2 keeps a separate quiet-move history for each of the first four plies from the root and adds it only when those quiet moves are ordered.
The switch is the check option IdeaK2, default false. The spins are IdeaK2_PlyLimit, default 4, and IdeaK2_Scale, default 1024, which adds the stored history at full weight.
With the check false the new table is not read and not written, and the ordering score adds zero. With the check true, a quiet cutoff and a quiet principal-variation move update that ply's from-to row.

EXISTS: no. I read `forge-combo29/src/search.cpp`. ThreatHistory is a cheaper-attacker table and ContHist4PlyRead reads a continuation table four plies back. Neither is a history of the quiet moves played in the first plies from the root.

## Honesty

Plain engine (exe B) and the patched engine with no setoption (exe P). Both from `report_numbers.txt`, which is the output of `report_from_files.py`.

```
HONESTY_B
PASS bench 11 expected 312866 got 312866
PASS bench 13 expected 862329 got 862329
PASS bench 16 expected 3024920 got 3024920
PASS go perft 5 expected 4865609 got 4865609
HONESTY_P
PASS bench 11 expected 312866 got 312866
PASS bench 13 expected 862329 got 862329
PASS bench 16 expected 3024920 got 3024920
PASS go perft 5 expected 4865609 got 4865609
```

Exe B under S14, before any patched measurement: O depth 12 sum 9500069, first three 41311 24872 28574. G depth 12 sum 18466239. Those are the known sums.

## Steps

| step | done / partly / not done | evidence file | result |
| --- | --- | --- | --- |
| 1 seat | done | SEAT.txt, stamps.txt | seat 091, idea 41 |
| 2 honesty and baselines | done | HONESTY_B.txt, B_O_d12.sum.txt, B_G_d12.sum.txt | honesty pass; O 9500069; G 18466239 |
| 3 prediction | done | prediction.txt | O-on 9350000, wrong outside 8000000..11000000; Elo 8, wrong outside -40..50. Not edited after. |
| 3 patch | done | idea.patch.txt, my_apply_check.txt | git apply --check exit 0 on a fresh base |
| 3 proofs | done | report_numbers.txt | off identical; on differs 200 of 200; uci lists the options; sanitizer clean |
| 3 match | done | match_OG.log, match_OG.pgn | Elo -5.65 +/- 10.15, 1106 games |
| 4 partner | done | partner_off_O_vs_B.txt, partner_on_O_vs_claimed.txt, partner_match_R.log | CONFIRMS seat 041 |
| 5 report | done | REPORT.md, RESULT.txt | this file |

## Proofs

(1) Honesty with no setoption, above. Unchanged on exe P.

(2) S14 and IdeaK2 false. From `report_numbers.txt`:

```
OFF_O_VS_B
EQUAL 200
DIFFER 0
OFF_G_VS_B
EQUAL 353
DIFFER 0
```

(3) S14 and IdeaK2 true, O depth 12. From `report_numbers.txt`:

```
P_ON_O
SUM 9752024
FIRST3 30328 23836 34993
ON_O_VS_B
EQUAL 0
DIFFER 200
```

The measured sum 9752024 is inside the prediction band 8000000..11000000. The prediction was 9350000. It was not proved wrong.

(4) `uci` on exe P lists:

```
option name IdeaK2 type check default false
option name IdeaK2_PlyLimit type spin default 4 min 1 max 8
option name IdeaK2_Scale type spin default 1024 min 0 max 4096
```

(5) AddressSanitizer and UndefinedBehaviorSanitizer build of the patched tree. `asan_G100_on.meta` has `nm_asan_count=35` and `sanitizer_lines=0` for the first 100 of G at depth 10 with IdeaK2 true. The same runner on a scratch copy with one planted read past the end of a four-int heap array, on the FEN in `asan_special.fen`, reported:

```
/agent/repos/asan-scratch/forge-combo29/src/uci.cpp:46:26: runtime error: load of address 0x5020000000c0 with insufficient space for an object of type 'int'
```

## Match

Exe P with IdeaK2 true against exe P with IdeaK2 false. S14, Threads 1, Hash 16, 20000 nodes, openings O then G (553), both colours, 1106 games. fastchess, concurrency 3. From `report_numbers.txt`:

```
Results of IdeaK2on vs IdeaK2off (20000 nodes, 1t, 16MB, OG.fens):
Elo: -5.65 +/- 10.15, nElo: -11.41 +/- 20.48
Games: 1106, Wins: 318, Losses: 336, Draws: 452, Points: 544.0 (49.19 %)
fastchess_exit=0
```

The prediction was +8 Elo, proved wrong below -40 or above 50. -5.65 is inside that band. The point is not below -20, and -5.65 minus 10.15 is still above -20 and the upper side is positive, so the whole interval is not below 0. I did not open the code again looking for a mistake.

Whole output: `match_OG.log` and `match_OG.pgn`. No line contains "unknown option".

## Partner

Partner is seat 041. Seats for idea 41 are 041, 091 and 141. 141 has no branch. 041 is the next seat after 091 that has a branch.

Their patch applies to a fresh base: `partner_apply_check.txt`. Honesty of that build passes (`HONESTY_PARTNER.txt`). IdeaK2 false matches exe B on O, 200 equal and 0 differ (`partner_off_O_vs_B.txt`). IdeaK2 true with IdeaK2_Plies 4 matches their own O depth-12 rows, 200 equal and 0 differ (`partner_on_O_vs_claimed.txt`). Their file claims sum 9752024 and 200 positions different from the plain engine. My rebuild got that sum.

Their check is IdeaK2. Their spin is IdeaK2_Plies, default 4. They do not have IdeaK2_Scale. At the default the O depth-12 rows are the same as mine.

Test match of their switch, my 300 R openings, both colours, 600 games:

```
Results of partnerOn vs partnerOff (20000 nodes, 1t, 16MB, R.fens):
Elo: -0.58 +/- 13.39, nElo: -1.20 +/- 27.80
Games: 600, Wins: 246, Losses: 247, Draws: 107, Points: 299.5 (49.92 %)
fastchess_exit=0
```

Verdict: CONFIRMS. The proofs they claim for apply, honesty, switch false, and switch true on O all came out as they claim.

## suspicions, not proven

Seat 041's OG match prints the same Elo line as mine, -5.65 +/- 10.15, with the same win, loss and draw counts. The O depth-12 rows of the two patches match, and a fixed node count with one thread repeats a game. I did not prove the 20000-node games are move for move the same.

## what I did NOT do

I did not read `IDEAS.md`. Idea 41 is one of the ideas 32 to 50, and the brief describes it.
I did not try IdeaK2_PlyLimit or IdeaK2_Scale at any value other than the defaults.
I did not play a second match of my own patch. Seat 041 had a patch, so the second match is theirs, on my R openings.
I did not replay their 1106-game OG match.
At step 1 and again at minute 60 the handoff branch had no `FABLE_TO_grok_<N>.md`.
I did not open a pull request.

## what I am NOT sure about

fastchess prints `Elo: -5.65 +/- 10.15`. I put -5.65 in elo and 10.15 in err. I am not sure whether 10.15 is one standard error or the half-width of a 95 percent interval. The result line is the measurement.
The planted bug's message is a UBSan runtime error. `nm -C` on that executable counts 35 `__asan_` symbols, so AddressSanitizer is in the binary. I did not see a second line that begins with `ERROR: AddressSanitizer`. The same runner reported the sanitizer line, and the clean run reported none.

## times: see stamps.txt

## git status --short and ls -la

The command output follows.
## command output
```
$ git status --short
 M forge-combo29/grok/091/stamps.txt
?? forge-combo29/grok/091/HONESTY_PARTNER.txt
?? forge-combo29/grok/091/REPORT.md
?? forge-combo29/grok/091/RESULT.txt
?? forge-combo29/grok/091/honesty_PARTNER_bench11.meta
?? forge-combo29/grok/091/honesty_PARTNER_bench11.txt
?? forge-combo29/grok/091/honesty_PARTNER_bench13.meta
?? forge-combo29/grok/091/honesty_PARTNER_bench13.txt
?? forge-combo29/grok/091/honesty_PARTNER_bench16.meta
?? forge-combo29/grok/091/honesty_PARTNER_bench16.txt
?? forge-combo29/grok/091/honesty_PARTNER_goperft5.meta
?? forge-combo29/grok/091/honesty_PARTNER_goperft5.txt
?? forge-combo29/grok/091/my_apply_check.txt
?? forge-combo29/grok/091/partner041_O_on_claimed.txt
?? forge-combo29/grok/091/partner_apply_check.txt
?? forge-combo29/grok/091/partner_match_R.log
?? forge-combo29/grok/091/partner_match_R.pgn
?? forge-combo29/grok/091/partner_off_O_d12.meta
?? forge-combo29/grok/091/partner_off_O_d12.stderr
?? forge-combo29/grok/091/partner_off_O_d12.txt
?? forge-combo29/grok/091/partner_off_O_vs_B.txt
?? forge-combo29/grok/091/partner_on_O_d12.meta
?? forge-combo29/grok/091/partner_on_O_d12.stderr
?? forge-combo29/grok/091/partner_on_O_d12.txt
?? forge-combo29/grok/091/partner_on_O_vs_claimed.txt
?? forge-combo29/grok/091/report_from_files.py
?? forge-combo29/grok/091/report_numbers.txt
?? forge-combo29/grok/091/run_partner_match.sh

$ ls -la forge-combo29/grok/091
total 10676
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 09:19 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:55 ..
-rw-r--r-- 1 ubuntu ubuntu     954 Nov 20 08:07 asan_G100_on.meta
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:07 asan_G100_on.stderr
-rw-r--r-- 1 ubuntu ubuntu  119057 Nov 20 08:07 asan_G100_on.txt
-rw-r--r-- 1 ubuntu ubuntu    6837 Nov 20 08:06 asan_run.py
-rw-r--r-- 1 ubuntu ubuntu     967 Nov 20 08:08 asan_scratch.meta
-rw-r--r-- 1 ubuntu ubuntu     317 Nov 20 08:08 asan_scratch.stderr
-rw-r--r-- 1 ubuntu ubuntu    5252 Nov 20 08:08 asan_scratch.txt
-rw-r--r-- 1 ubuntu ubuntu      30 Nov 20 08:07 asan_special.fen
-rw-r--r-- 1 ubuntu ubuntu     954 Nov 20 08:04 B_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:04 B_G_d12.stderr
-rw-r--r-- 1 ubuntu ubuntu    3481 Nov 20 08:04 B_G_d12.sum.txt
-rw-r--r-- 1 ubuntu ubuntu  507986 Nov 20 08:04 B_G_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     955 Nov 20 08:04 B_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:04 B_O_d12.stderr
-rw-r--r-- 1 ubuntu ubuntu    1943 Nov 20 08:04 B_O_d12.sum.txt
-rw-r--r-- 1 ubuntu ubuntu  282215 Nov 20 08:04 B_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     894 Nov 20 08:05 compare_nodes.py
-rw-r--r-- 1 ubuntu ubuntu    1389 Nov 20 08:05 design.txt
-rw-r--r-- 1 ubuntu ubuntu    5009 Nov 20 08:07 G100.epd
-rw-r--r-- 1 ubuntu ubuntu   17691 Nov 20 08:03 G.epd
-rw-r--r-- 1 ubuntu ubuntu     212 Nov 20 08:01 honesty_B_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu    5002 Nov 20 08:01 honesty_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     212 Nov 20 08:01 honesty_B_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu    5002 Nov 20 08:01 honesty_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     212 Nov 20 08:01 honesty_B_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu    5004 Nov 20 08:01 honesty_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     214 Nov 20 08:01 honesty_B_goperft5.meta
-rw-r--r-- 1 ubuntu ubuntu    5215 Nov 20 08:01 honesty_B_goperft5.txt
-rw-r--r-- 1 ubuntu ubuntu   20725 Nov 20 08:01 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu    3012 Nov 20 08:01 honesty_check.py
-rw-r--r-- 1 ubuntu ubuntu     215 Nov 20 09:12 honesty_PARTNER_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu    5103 Nov 20 09:12 honesty_PARTNER_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     215 Nov 20 09:12 honesty_PARTNER_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu    5103 Nov 20 09:12 honesty_PARTNER_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     215 Nov 20 09:12 honesty_PARTNER_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu    5105 Nov 20 09:12 honesty_PARTNER_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     217 Nov 20 09:12 honesty_PARTNER_goperft5.meta
-rw-r--r-- 1 ubuntu ubuntu    5316 Nov 20 09:12 honesty_PARTNER_goperft5.txt
-rw-r--r-- 1 ubuntu ubuntu   21153 Nov 20 09:12 HONESTY_PARTNER.txt
-rw-r--r-- 1 ubuntu ubuntu     212 Nov 20 08:05 honesty_P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu    5169 Nov 20 08:05 honesty_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     212 Nov 20 08:06 honesty_P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu    5169 Nov 20 08:06 honesty_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     212 Nov 20 08:06 honesty_P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu    5171 Nov 20 08:06 honesty_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     214 Nov 20 08:06 honesty_P_goperft5.meta
-rw-r--r-- 1 ubuntu ubuntu    5382 Nov 20 08:06 honesty_P_goperft5.txt
-rw-r--r-- 1 ubuntu ubuntu   21393 Nov 20 08:06 HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu   12104 Nov 20 08:05 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    1924 Nov 20 08:03 make_r.py
-rw-r--r-- 1 ubuntu ubuntu  152264 Nov 20 08:15 match_OG.log
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:09 match_OG.nohup
-rw-r--r-- 1 ubuntu ubuntu 4677513 Nov 20 08:15 match_OG.pgn
-rw-r--r-- 1 ubuntu ubuntu     953 Nov 20 08:09 match_smoke.log
-rw-r--r-- 1 ubuntu ubuntu   21762 Nov 20 08:09 match_smoke.pgn
-rw-r--r-- 1 ubuntu ubuntu      25 Nov 20 09:17 my_apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu     187 Nov 20 08:03 O3.fens
-rw-r--r-- 1 ubuntu ubuntu   12861 Nov 20 08:03 O.fens
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:09 OG.fens
-rw-r--r-- 1 ubuntu ubuntu  282781 Nov 20 09:12 partner041_O_on_claimed.txt
-rw-r--r-- 1 ubuntu ubuntu     146 Nov 20 09:12 partner_apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu   81283 Nov 20 09:16 partner_match_R.log
-rw-r--r-- 1 ubuntu ubuntu 2548532 Nov 20 09:16 partner_match_R.pgn
-rw-r--r-- 1 ubuntu ubuntu     992 Nov 20 09:12 partner_off_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 09:12 partner_off_O_d12.stderr
-rw-r--r-- 1 ubuntu ubuntu  281912 Nov 20 09:12 partner_off_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu      56 Nov 20 09:12 partner_off_O_vs_B.txt
-rw-r--r-- 1 ubuntu ubuntu    1027 Nov 20 09:12 partner_on_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 09:12 partner_on_O_d12.stderr
-rw-r--r-- 1 ubuntu ubuntu  282641 Nov 20 09:12 partner_on_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu      56 Nov 20 09:12 partner_on_O_vs_claimed.txt
-rw-r--r-- 1 ubuntu ubuntu     988 Nov 20 08:06 P_off_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:06 P_off_G_d12.stderr
-rw-r--r-- 1 ubuntu ubuntu    3481 Nov 20 08:06 P_off_G_d12.sum.txt
-rw-r--r-- 1 ubuntu ubuntu  507925 Nov 20 08:06 P_off_G_d12.txt
-rw-r--r-- 1 ubuntu ubuntu      56 Nov 20 08:06 P_off_G_vs_B.txt
-rw-r--r-- 1 ubuntu ubuntu     989 Nov 20 08:06 P_off_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:06 P_off_O_d12.stderr
-rw-r--r-- 1 ubuntu ubuntu    1943 Nov 20 08:06 P_off_O_d12.sum.txt
-rw-r--r-- 1 ubuntu ubuntu  282151 Nov 20 08:06 P_off_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu      56 Nov 20 08:06 P_off_O_vs_B.txt
-rw-r--r-- 1 ubuntu ubuntu     988 Nov 20 08:06 P_on_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:06 P_on_O_d12.stderr
-rw-r--r-- 1 ubuntu ubuntu    1943 Nov 20 08:06 P_on_O_d12.sum.txt
-rw-r--r-- 1 ubuntu ubuntu  282856 Nov 20 08:06 P_on_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     508 Nov 20 08:06 P_on_O_vs_B.txt
-rw-r--r-- 1 ubuntu ubuntu     655 Nov 20 08:04 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu    2712 Nov 20 09:17 report_from_files.py
-rw-r--r-- 1 ubuntu ubuntu    8317 Nov 20 09:19 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    3453 Nov 20 09:17 report_numbers.txt
-rw-r--r-- 1 ubuntu ubuntu     187 Nov 20 09:18 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu   19964 Nov 20 08:04 R.fens
-rwxr-xr-x 1 ubuntu ubuntu    1063 Nov 20 08:09 run_match.sh
-rwxr-xr-x 1 ubuntu ubuntu    1090 Nov 20 09:12 run_partner_match.sh
-rw-r--r-- 1 ubuntu ubuntu    5883 Nov 20 08:03 search_set.py
-rw-r--r-- 1 ubuntu ubuntu      78 Nov 20 07:55 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu     954 Nov 20 08:03 smoke_B_O3.meta
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:03 smoke_B_O3.stderr
-rw-r--r-- 1 ubuntu ubuntu      67 Nov 20 08:04 smoke_B_O3.sum.txt
-rw-r--r-- 1 ubuntu ubuntu    9124 Nov 20 08:03 smoke_B_O3.txt
-rw-r--r-- 1 ubuntu ubuntu     122 Nov 20 08:09 smoke_openings.fens
-rw-r--r-- 1 ubuntu ubuntu     205 Nov 20 09:18 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu    1142 Nov 20 08:03 sum_nodes.py
-rw-r--r-- 1 ubuntu ubuntu    4933 Nov 20 08:07 uci_B.txt
-rw-r--r-- 1 ubuntu ubuntu     484 Nov 20 08:06 uci_dump.py
-rw-r--r-- 1 ubuntu ubuntu    5100 Nov 20 08:07 uci_P.txt
```
