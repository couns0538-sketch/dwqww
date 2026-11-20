# Seat 022, idea 22, S27

Idea S27 is a veto on quiet history. When the previous-move continuation and the threat-role statistic have opposite signs outside a dead zone, the score keeps only the from-to history.
I added check option IdeaS27, default false, and spin IdeaS27_DeadZone, default 64. While the check is on, the threat-role table is updated, and unless the veto fires its value is added with the continuation terms.
While the check is off, quiet scoring and the threat-table update follow the previous path. The dead-zone choice and the reason the table is live are in decisions.txt.

EXISTS: no. ThreatHistory in search.cpp is the threat-role table. Nothing in the plain engine drops both context terms when their signs disagree.

## Honesty

Exe B and exe P, no setoption. Exe B, S14, Threads 1, Hash 16, also reproduced the known depth-12 sums. The lines below are the output of report_table.py, which reads the raw files.

```
HONESTY_B PASS 312866 862329 3024920 4865609
HONESTY_P PASS 312866 862329 3024920 4865609
```

```
O_B
positions 200
sum 9500069
first3 41311 24872 28574
G_B
positions 353
sum 18466239
first3 37203 70845 144383
```

## Steps

Pasted from report_table.py:

```
step | status | evidence | result
1 seat | done | SEAT.txt stamps.txt | seat 022, idea 22
2 honesty B | done | HONESTY_B.txt | PASS 312866 862329 3024920 4865609
2 O and G | done | proof_compare.txt | see proof_compare.txt sums
3 prediction | done | prediction.txt | file present, not edited after commit
3 patch applies | done | apply_check.txt idea.patch.txt | apply_exit 0
3 proof off | done | proof_compare.txt | see OFF_O and OFF_G blocks
3 proof on | done | proof_compare.txt | see ON_O block
3 uci options | done | uci_p.txt | IdeaS27 and IdeaS27_DeadZone lines in uci_p.txt
3 sanitizer | done | asan_g100_d10.txt.meta scratch_asan.txt | asan_symbol_count 35 scratch yes
3 match | done | match_summary.txt match_og.txt match_og.pgn | Games: 1106, Wins: 338, Losses: 329, Draws: 439, Points: 557.5 (50.41 %)
4 partner | done | partner_072/compare.txt partner_072/on_vs_claimed.txt partner_072/match_summary.txt | off differ 0; on claimed equal True; Games: 600, Wins: 256, Losses: 277, Draws: 67, Points: 289.5 (48.25 %)
```

## Proofs

(1) Honesty, no setoption, exe P: bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609. Same four numbers on exe B. HONESTY_P.txt and HONESTY_B.txt.

(2) S14 and IdeaS27 false. O depth 12 differs from exe B in 0 of 200 (sum 9500069). G depth 12 differs in 0 of 353 (sum 18466239). proof_compare.txt blocks OFF_O and OFF_G.

(3) S14 and IdeaS27 true. O depth 12 differs from exe B in 200 of 200. The sum is 9605430. proof_compare.txt block ON_O. Prediction in prediction.txt was 10450000, wrong below 8000000 or above 13500000. 9605430 is inside that range.

(4) uci_p.txt lists `option name IdeaS27 type check default false` and `option name IdeaS27_DeadZone type spin default 64 min 0 max 8192`.

(5) AddressSanitizer and UndefinedBehaviorSanitizer build, IdeaS27 true, first 100 of G at depth 10: the runner exited 0 and asan_g100_d10.txt has no sanitizer line. asan_g100_d10.txt.meta says asan_symbol_count 35. A scratch copy with one read past the end of a 4-int heap array, on the FEN in scratch.fen, run through search_positions.py, printed `runtime error: load of address ... with insufficient space for an object of type 'int'` at the inserted line. That text is scratch_asan.txt. scratch_nm_count.txt is 35.

idea.patch.txt applies to a fresh checkout of 6b98f2170a3210e71beed04bbd2553972c253ed7. apply_check.txt says apply_exit 0.

## Match

Exe P with IdeaS27 true against exe P with IdeaS27 false. S14, Threads 1, Hash 16, 20000 nodes, openings O then G (553), both colours, 1106 games. fastchess from github.com/Disservin/fastchess, concurrency 3. Output of parse_match.py on match_og.txt:

```
Elo: 2.83 +/- 10.79, nElo: 5.37 +/- 20.48
Games: 1106, Wins: 338, Losses: 329, Draws: 439, Points: 557.5 (50.41 %)
```

Prediction was 3 Elo, wrong below -30 or above 40. 2.83 is inside that range. The point is not below -20, and the interval is not entirely below 0, so I did not go back and change the code.

## Partner

Partner is seat 072. Fetched for-fable-and-opus/grok-072 at 41fd22ce5a0889a66ed368023855d1d4796947bb. idea.patch.txt was present. My harness, not theirs: apply --check exit 0, honesty PASS 312866 862329 3024920 4865609, IdeaS27 false matches exe B on O depth 12 in 0 of 200, IdeaS27 true matches their P_on_O_d12.raw.txt in 0 of 200 (sum 9671966) and differs from exe B in 200 of 200. That is what their REPORT.md claims for the on sum and the differ count. My R match of their switch, 300 openings from r.fens, both colours, 600 games:

```
Elo: -12.17 +/- 10.26, nElo: -32.99 +/- 27.80
Games: 600, Wins: 256, Losses: 277, Draws: 67, Points: 289.5 (48.25 %)
```

Verdict: CONFIRMS.

## Suspicions, not proven

I did not count how often the veto returned the from-to history alone. Turning the option on also adds the threat-role value when the signs do not disagree, so the 200 differing positions are not by themselves a count of vetoes.

The match interval is about -8 to +14. A small loss and a small gain are both inside it.

Seat 072 does not add the threat-role value on the non-veto path when ThreatHistory is off. Their O-on sum is 9671966 and mine is 9605430. Both differ from exe B in 200 of 200. I do not know which reading of "add them as usual" is the one wanted.

Many games ended by threefold repetition, the fifty-move rule, or insufficient material. Those are legal draws.

## What I did NOT do

I did not search G at depth 12 with IdeaS27 true. I did not turn ThreatHistory on in the measured searches. I did not count veto firings. I did not edit prediction.txt after its commit. I did not replay the partner's 1106-game match. I did not remeasure the partner's G off rows. I did not open a pull request.

## What I am NOT sure about

Whether dead zone 64 is a good width. Whether the non-veto path should add the threat-role value when ThreatHistory is off. The built-in net is only a first look. There was no FABLE_TO_grok file on the handoff branch at step 1 or at minute 60.

times: see stamps.txt

## git status and folder listing

```
$ git status --short
 M forge-combo29/grok/022/stamps.txt
?? config.json
?? forge-combo29/grok/022/HONESTY_072.txt
?? forge-combo29/grok/022/REPORT.md
?? forge-combo29/grok/022/RESULT.txt
?? forge-combo29/grok/022/honesty_072_bench11.txt
?? forge-combo29/grok/022/honesty_072_bench11.txt.meta
?? forge-combo29/grok/022/honesty_072_bench13.txt
?? forge-combo29/grok/022/honesty_072_bench13.txt.meta
?? forge-combo29/grok/022/honesty_072_bench16.txt
?? forge-combo29/grok/022/honesty_072_bench16.txt.meta
?? forge-combo29/grok/022/honesty_072_perft5.txt
?? forge-combo29/grok/022/honesty_072_perft5.txt.meta
?? forge-combo29/grok/022/partner_072/
?? forge-combo29/grok/022/partner_072_idea.patch.txt
?? forge-combo29/grok/022/partner_072_o_on_claimed.nodes
?? forge-combo29/grok/022/partner_072_o_on_claimed.raw.txt
?? forge-combo29/grok/022/report_table.py
?? forge-combo29/grok/022/report_table.txt
?? forge-combo29/grok/022/review_partner.sh
?? forge-combo29/grok/022/run_partner_match.sh

$ ls -la forge-combo29/grok/022
total 6240
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 09:15 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:52 ..
-rw-r--r-- 1 ubuntu ubuntu      13 Nov 20 08:07 apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu  119188 Nov 20 08:06 asan_g100_d10.txt
-rw-r--r-- 1 ubuntu ubuntu    1015 Nov 20 08:06 asan_g100_d10.txt.meta
-rw-r--r-- 1 ubuntu ubuntu       3 Nov 20 08:05 asan_nm_count.txt
-rw-r--r-- 1 ubuntu ubuntu     754 Nov 20 08:02 compare_nodes.py
-rw-r--r-- 1 ubuntu ubuntu    1239 Nov 20 08:05 decisions.txt
-rw-r--r-- 1 ubuntu ubuntu    6831 Nov 20 08:12 fastchess_config.json
-rw-r--r-- 1 ubuntu ubuntu    2128 Nov 20 08:01 g_b_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu  507980 Nov 20 08:01 g_b_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     806 Nov 20 08:01 g_b_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    5009 Nov 20 08:05 g_first100.epd
-rw-r--r-- 1 ubuntu ubuntu    2128 Nov 20 08:02 g_p_off_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu  507671 Nov 20 08:02 g_p_off_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     841 Nov 20 08:02 g_p_off_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    5104 Nov 20 09:09 honesty_072_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     210 Nov 20 09:09 honesty_072_bench11.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    5104 Nov 20 09:09 honesty_072_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     210 Nov 20 09:09 honesty_072_bench13.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    5106 Nov 20 09:09 honesty_072_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     212 Nov 20 09:09 honesty_072_bench16.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    5317 Nov 20 09:09 honesty_072_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     214 Nov 20 09:09 honesty_072_perft5.txt.meta
-rw-r--r-- 1 ubuntu ubuntu     301 Nov 20 09:09 HONESTY_072.txt
-rw-r--r-- 1 ubuntu ubuntu    4994 Nov 20 08:01 honesty_b_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     204 Nov 20 08:01 honesty_b_bench11.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    4994 Nov 20 08:01 honesty_b_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     204 Nov 20 08:01 honesty_b_bench13.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    4996 Nov 20 08:01 honesty_b_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     206 Nov 20 08:01 honesty_b_bench16.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    5207 Nov 20 08:01 honesty_b_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     208 Nov 20 08:01 honesty_b_perft5.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    2938 Nov 20 07:58 honesty_b.py
-rw-r--r-- 1 ubuntu ubuntu     295 Nov 20 08:01 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu    2809 Nov 20 08:04 honesty_check.py
-rw-r--r-- 1 ubuntu ubuntu    5104 Nov 20 08:02 honesty_p_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     204 Nov 20 08:02 honesty_p_bench11.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    5104 Nov 20 08:02 honesty_p_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     204 Nov 20 08:02 honesty_p_bench13.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    5106 Nov 20 08:02 honesty_p_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     206 Nov 20 08:02 honesty_p_bench16.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    5317 Nov 20 08:02 honesty_p_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     208 Nov 20 08:02 honesty_p_perft5.txt.meta
-rw-r--r-- 1 ubuntu ubuntu     295 Nov 20 08:02 HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu   10518 Nov 20 08:01 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    1213 Nov 20 08:05 insert_scratch_bug.py
-rw-r--r-- 1 ubuntu ubuntu    1223 Nov 20 08:05 make_r.py
-rw-r--r-- 1 ubuntu ubuntu 3523616 Nov 20 08:12 match_og.pgn
-rw-r--r-- 1 ubuntu ubuntu  125276 Nov 20 08:12 match_og.txt
-rw-r--r-- 1 ubuntu ubuntu     427 Nov 20 08:13 match_summary.txt
-rw-r--r-- 1 ubuntu ubuntu    1204 Nov 20 08:01 o_b_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu  282048 Nov 20 08:00 o_b_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     807 Nov 20 08:00 o_b_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:03 openings_og.epd
-rw-r--r-- 1 ubuntu ubuntu    1204 Nov 20 08:02 o_p_off_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu  282093 Nov 20 08:02 o_p_off_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     842 Nov 20 08:02 o_p_off_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    1202 Nov 20 08:02 o_p_on_d12.nodes
-rw-r--r-- 1 ubuntu ubuntu  282355 Nov 20 08:02 o_p_on_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     841 Nov 20 08:02 o_p_on_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu     543 Nov 20 08:07 parse_match.py
-rw-r--r-- 1 ubuntu ubuntu    1035 Nov 20 08:01 parse_nodes.py
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 09:14 partner_072
-rw-r--r-- 1 ubuntu ubuntu    9647 Nov 20 09:08 partner_072_idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    1204 Nov 20 09:09 partner_072_o_on_claimed.nodes
-rw-r--r-- 1 ubuntu ubuntu  277464 Nov 20 09:09 partner_072_o_on_claimed.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     407 Nov 20 08:00 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu     367 Nov 20 08:06 proof_compare.txt
-rw-r--r-- 1 ubuntu ubuntu    7283 Nov 20 09:15 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    3606 Nov 20 09:15 report_table.py
-rw-r--r-- 1 ubuntu ubuntu    2202 Nov 20 09:15 report_table.txt
-rw-r--r-- 1 ubuntu ubuntu     184 Nov 20 09:15 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu    1873 Nov 20 08:54 review_partner.sh
-rw-r--r-- 1 ubuntu ubuntu   19380 Nov 20 08:05 r.fens
-rw-r--r-- 1 ubuntu ubuntu     823 Nov 20 08:05 run_asan.sh
-rw-r--r-- 1 ubuntu ubuntu    1100 Nov 20 08:05 run_match_og.sh
-rw-r--r-- 1 ubuntu ubuntu    1264 Nov 20 08:54 run_partner_match.sh
-rw-r--r-- 1 ubuntu ubuntu     942 Nov 20 08:07 run_scratch.sh
-rw-r--r-- 1 ubuntu ubuntu    6310 Nov 20 08:07 scratch_asan.txt
-rw-r--r-- 1 ubuntu ubuntu     175 Nov 20 08:07 scratch_asan.txt.meta
-rw-r--r-- 1 ubuntu ubuntu      28 Nov 20 08:06 scratch.fen
-rw-r--r-- 1 ubuntu ubuntu       3 Nov 20 08:07 scratch_nm_count.txt
-rw-r--r-- 1 ubuntu ubuntu    5869 Nov 20 08:04 search_positions.py
-rw-r--r-- 1 ubuntu ubuntu      79 Nov 20 07:52 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu     140 Nov 20 09:15 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu    1003 Nov 20 08:02 uci_options.py
-rw-r--r-- 1 ubuntu ubuntu    5043 Nov 20 08:02 uci_p.txt
-rw-r--r-- 1 ubuntu ubuntu     147 Nov 20 08:02 uci_p.txt.meta
```
