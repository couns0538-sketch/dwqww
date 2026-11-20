Idea 29 is B10, depth-normalised effort repayment, under the check option IdeaB10 (default false).
A fail-low node remembers a reduced move whose nodes divided by the depth it was given beat the next such move by 1.5x (IdeaB10_Ratio 384).
The next visit gives that move extra depth, at most IdeaB10_Cap (3) plies along the path from the root.

EXISTS: no. Root node-share (TmNodeShare in search.cpp) splits clock time from raw root nodes. It does not remember a nodes-per-depth move or give depth back.

Honesty, no setoption, from summary.txt (script summarize.py):
bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, go perft 5 nodes 4865609.
Same four numbers for exe B and exe P.

The table below is the pasted output of summarize.py, which reads the raw files.

```
honesty B
info string bench depth 11 nodes 312866 time 180 nps 1738144
info string bench depth 13 nodes 862329 time 576 nps 1497098
info string bench depth 16 nodes 3024920 time 1927 nps 1569756
nodes 4865609
honesty P
info string bench depth 11 nodes 312866 time 165 nps 1896157
info string bench depth 13 nodes 862329 time 449 nps 1920554
info string bench depth 16 nodes 3024920 time 1482 nps 2041106
nodes 4865609
O off vs B n=200/200 equal=True differ=0 sum_left=9500069 sum_right=9500069 first3_left=[41311, 24872, 28574] first3_right=[41311, 24872, 28574]
G off vs B n=353/353 equal=True differ=0 sum_left=18466239 sum_right=18466239 first3_left=[37203, 70845, 144383] first3_right=[37203, 70845, 144383]
O on vs B n=200/200 equal=False differ=197 sum_left=9500069 sum_right=11919607 first3_left=[41311, 24872, 28574] first3_right=[27429, 36528, 40796]
asan_G100 sanitizer_lines=0
asan_scratch sanitizer_lines=1
/tmp/scratch/forge-combo29/src/uci.cpp:499:34: runtime error: load of address 0x502000000090 with insufficient space for an object of type 'int'
asan_G100_d10.txt.meta nm_asan_count: 35
asan_scratch.txt.meta nm_asan_count: 35
option name IdeaB10 type check default false
option name IdeaB10_Ratio type spin default 384 min 257 max 4096
option name IdeaB10_Cap type spin default 3 min 0 max 16
partner off vs B equal=True differ=0 sum=9500069
partner on vs claimed equal=True differ=0 sum=9836323 claimed_sum=9836323 on_vs_B_differ=199
step | status | evidence | result
STEP 1 | done | SEAT.txt stamps.txt | seat 029 idea 29
STEP 2 | done | HONESTY_B.txt B_O_d12.txt B_G_d12.txt | bench/perft match; O 9500069; G 18466239
STEP 3 | done | idea.patch.txt P_on_O_d12.txt match_stdout.txt asan_G100_d10.txt | see proofs above
STEP 4 | done | partner_off_O_d12.txt partner_on_O_d12.txt partner_match_stdout.txt | see partner lines above
STEP 5 | done | REPORT.md RESULT.txt | this report
```

Proofs on exe P:
(1) Honesty with no setoption matches exe B: 312866, 862329, 3024920, 4865609. Files HONESTY_P.txt and HONESTY_B.txt.
(2) S14, IdeaB10 false: O depth 12 and G depth 12 are position-by-position equal to exe B. O sum 9500069, first three 41311 / 24872 / 28574. G sum 18466239.
(3) S14, IdeaB10 true: O depth 12 sum 11919607. 197 of 200 positions differ from exe B.
(4) uci lists IdeaB10 check default false, IdeaB10_Ratio spin default 384, IdeaB10_Cap spin default 3. File uci_options.txt.
(5) AddressSanitizer and UndefinedBehaviorSanitizer build, nm -C | grep -c __asan_ = 35. First 100 of G at depth 10 with the switch on: 0 sanitizer lines (asan_G100_d10.txt). The same runner on a scratch copy that reads past a 4-int heap array when given the FEN in special.fen printed one sanitizer line (asan_scratch.txt). git apply --check of idea.patch.txt on 6b98f2170a3210e71beed04bbd2553972c253ed7 printed APPLY_CHECK_OK.

Match, IdeaB10 on versus off, S14, Threads 1, Hash 16, 20000 nodes, openings OG.epd (553), both colours, 1106 games. From match_stdout.txt: Elo -9.43 +/- 10.50, nElo -18.39 +/- 20.48, Wins 337, Losses 367, Draws 402, Points 538.0 (48.64 %). The interval is not entirely below 0, and the point is not below -20, so the code was not reopened for a mistake hunt. prediction.txt said O sum 10600000 (wrong below 9600000 or above 14000000) and Elo +6 (wrong below -35 or above +40). Measured 11919607 and -9.43 sit inside both ranges.

Partner is seat 079 (same idea, next seat with a branch). git apply --check of their idea.patch.txt printed APPLY_CHECK_OK. My harness, not theirs: honesty matches the known numbers; switch false O depth 12 equals exe B on all 200 positions; switch true O depth 12 equals their P_on_O_d12.nodes on all 200 positions (sum 9836323, 199 differ from exe B, which is what they claim). Verdict: CONFIRMS. A separate match of their switch on my 300 R openings, both colours, 600 games: Elo 8.69 +/- 11.82 (partner_match_stdout.txt). I did not re-run their G off proof, their sanitizer, or their 1106-game match.

suspicions, not proven: the -9 Elo may be the fixed-node cost of searching a few moves deeper, not a functional mistake. Three O positions did not change with the switch on; I did not inspect them.

What I did NOT do: no second match of my own patch on R, because 079 had a patch. No Threads above 1. No retune after the match. The STEP 2 stamp was written late; the honesty files and the known sums were already in the step 3 commit. No pull request.

What I am NOT sure about: whether -9.43 Elo would hold on the owner's net. The printed interval crosses 0. I am not sure the fail-low-only memory misses useful cutoff moves the idea also wanted; scoring every move, including fail-highs, produced zero depth changes on the first three positions (the stored move was never reduced on the next visit). That trial is not in the final patch.

times: see stamps.txt

```
$ git status --short
 M forge-combo29/grok/029/stamps.txt
 M forge-combo29/grok/029/summarize.py
?? forge-combo29/grok/029/HONESTY_079.txt
?? forge-combo29/grok/029/HONESTY_079_bench11.meta
?? forge-combo29/grok/029/HONESTY_079_bench11.txt
?? forge-combo29/grok/029/HONESTY_079_bench13.meta
?? forge-combo29/grok/029/HONESTY_079_bench13.txt
?? forge-combo29/grok/029/HONESTY_079_bench16.meta
?? forge-combo29/grok/029/HONESTY_079_bench16.txt
?? forge-combo29/grok/029/HONESTY_079_perft5.meta
?? forge-combo29/grok/029/HONESTY_079_perft5.txt
?? forge-combo29/grok/029/REPORT.md
?? forge-combo29/grok/029/RESULT.txt
?? forge-combo29/grok/029/partner_claimed_on_O.nodes
?? forge-combo29/grok/029/partner_config.json
?? forge-combo29/grok/029/partner_idea.patch.txt
?? forge-combo29/grok/029/partner_match.pgn
?? forge-combo29/grok/029/partner_match.sh
?? forge-combo29/grok/029/partner_match_stdout.txt
?? forge-combo29/grok/029/partner_off_O_d12.txt
?? forge-combo29/grok/029/partner_off_O_d12.txt.meta
?? forge-combo29/grok/029/partner_on_O_d12.txt
?? forge-combo29/grok/029/partner_on_O_d12.txt.meta
?? forge-combo29/grok/029/partner_uci.txt
?? forge-combo29/grok/029/summary.txt

$ ls -la forge-combo29/grok/029
total 9600
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 09:16 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:52 ..
-rw-r--r-- 1 ubuntu ubuntu  125678 Nov 20 08:16 asan_G100_d10.txt
-rw-r--r-- 1 ubuntu ubuntu   56293 Nov 20 08:16 asan_G100_d10.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    1033 Nov 20 08:16 asan_scratch.txt
-rw-r--r-- 1 ubuntu ubuntu     848 Nov 20 08:16 asan_scratch.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  542174 Nov 20 08:11 B_G_d12.txt
-rw-r--r-- 1 ubuntu ubuntu  197916 Nov 20 08:11 B_G_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  299164 Nov 20 08:11 B_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu  112236 Nov 20 08:11 B_O_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu    7129 Nov 20 09:15 config.json
-rw-r--r-- 1 ubuntu ubuntu    1515 Nov 20 08:18 decisions.txt
-rw-r--r-- 1 ubuntu ubuntu    5009 Nov 20 08:15 G100.epd
-rw-r--r-- 1 ubuntu ubuntu    8745 Nov 20 08:15 harness.py
-rw-r--r-- 1 ubuntu ubuntu     178 Nov 20 09:09 HONESTY_079_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:09 HONESTY_079_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     178 Nov 20 09:09 HONESTY_079_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:09 HONESTY_079_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     178 Nov 20 09:09 HONESTY_079_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 09:09 HONESTY_079_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     178 Nov 20 09:09 HONESTY_079_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 09:09 HONESTY_079_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     199 Nov 20 09:09 HONESTY_079.txt
-rw-r--r-- 1 ubuntu ubuntu     183 Nov 20 08:06 HONESTY_B_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:06 HONESTY_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     183 Nov 20 08:06 HONESTY_B_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:06 HONESTY_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     183 Nov 20 08:06 HONESTY_B_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:06 HONESTY_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     183 Nov 20 08:06 HONESTY_B_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:06 HONESTY_B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     199 Nov 20 08:06 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu     183 Nov 20 08:11 HONESTY_P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:11 HONESTY_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     183 Nov 20 08:11 HONESTY_P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:11 HONESTY_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     183 Nov 20 08:11 HONESTY_P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:11 HONESTY_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     183 Nov 20 08:12 HONESTY_P_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:12 HONESTY_P_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     199 Nov 20 08:12 HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu   14757 Nov 20 08:11 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    1456 Nov 20 08:18 make_r.py
-rw-r--r-- 1 ubuntu ubuntu 3724492 Nov 20 08:24 match.pgn
-rw-r--r-- 1 ubuntu ubuntu  136423 Nov 20 08:24 match_stdout.txt
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:16 OG.epd
-rw-r--r-- 1 ubuntu ubuntu    1202 Nov 20 09:10 partner_claimed_on_O.nodes
-rw-r--r-- 1 ubuntu ubuntu    7124 Nov 20 09:15 partner_config.json
-rw-r--r-- 1 ubuntu ubuntu   16769 Nov 20 09:10 partner_idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu 1791405 Nov 20 09:13 partner_match.pgn
-rwxr-xr-x 1 ubuntu ubuntu    1005 Nov 20 09:10 partner_match.sh
-rw-r--r-- 1 ubuntu ubuntu   70141 Nov 20 09:13 partner_match_stdout.txt
-rw-r--r-- 1 ubuntu ubuntu  299136 Nov 20 09:10 partner_off_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu  112266 Nov 20 09:10 partner_off_O_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  299780 Nov 20 09:10 partner_on_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu  112265 Nov 20 09:10 partner_on_O_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu     296 Nov 20 09:10 partner_uci.txt
-rw-r--r-- 1 ubuntu ubuntu  542223 Nov 20 08:12 P_off_G_d12.txt
-rw-r--r-- 1 ubuntu ubuntu  197951 Nov 20 08:12 P_off_G_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  299238 Nov 20 08:11 P_off_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu  112271 Nov 20 08:11 P_off_O_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu  301108 Nov 20 08:12 P_on_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu  112270 Nov 20 08:12 P_on_O_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu     672 Nov 20 08:02 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu    6848 Nov 20 09:16 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu     185 Nov 20 09:16 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu   19677 Nov 20 08:18 R.fens
-rwxr-xr-x 1 ubuntu ubuntu    1071 Nov 20 08:17 run_match.sh
-rw-r--r-- 1 ubuntu ubuntu      76 Nov 20 07:52 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu      28 Nov 20 08:16 special.fen
-rw-r--r-- 1 ubuntu ubuntu     221 Nov 20 09:16 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu    3683 Nov 20 09:16 summarize.py
-rw-r--r-- 1 ubuntu ubuntu    1901 Nov 20 09:16 summary.txt
-rw-r--r-- 1 ubuntu ubuntu    5100 Nov 20 08:12 uci_options.txt
```
