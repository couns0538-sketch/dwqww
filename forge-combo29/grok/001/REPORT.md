# Seat 001, idea 1, E2

Idea E2 scales the static evaluation toward 0 as the half-move clock rises, at the node, and leaves the hash value unscaled.
The plain engine already does that when EvalRule50Damp is true, at one percent per half-move.
I added one spin, EvalRule50Damp_Span, default 100, and the search reads it only while EvalRule50Damp is true, so 100 is today's on-path.

EXISTS: include/forge/search.hpp:351 (rule50_damped_static) and the check option in src/uci.cpp. The on/off was already an option, default false. The fixed 100 was not an option. It is EvalRule50Damp_Span, min 1 max 200, default 100. git apply --check on the fresh base worktree printed CHECK_OK and the patch then applied (apply_check.txt, partner-style note in that file).

Honesty numbers, no setoption, exe B and exe P. Bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, go perft 5 nodes 4865609. Exe B also reproduced O depth 12 sum 9500069 (first three 41311 / 24872 / 28574) and G depth 12 sum 18466239.

Pasted TABLE lines from report_from_files.py (report_numbers.txt):

```
step | status | evidence | result
1 seat | done | SEAT.txt stamps.txt | seat 001 idea 1
2 builds and honesty | done | HONESTY_B.txt B_O_d12.sum.txt B_G_d12.sum.txt | known nodes and known sums
3 idea | done | idea.patch.txt apply_check.txt cmp_off_O.txt cmp_on_O.txt asan_G100_d10.meta match_OG.txt | off identical, on differs, match played
4 partner | done | partner_cmp_off_O.txt partner_cmp_on_O.txt partner_match_R.txt | see partner section
5 report | done | REPORT.md RESULT.txt | this file
```

Proofs on exe P:

(1) No setoption. honesty_p_bench11.txt has `nodes 312866`, honesty_p_bench13.txt has `nodes 862329`, honesty_p_bench16.txt has `nodes 3024920`, honesty_p_perft5.txt has `nodes 4865609`.

(2) S14 and EvalRule50Damp false. compare_rows.py: O differ=0 of 200, G differ=0 of 353 (cmp_off_O.txt, cmp_off_G.txt).

(3) S14 and EvalRule50Damp true, span left at 100. compare_rows.py: differ=200 of 200. node_diff.py: node_differ=200 of 200. sum_rows.py: sum=10347764. The same 200 positions on the unmodified exe B with EvalRule50Damp true match exe P: node_differ=0 of 200 (node_diff_Bon_Pon.txt).

(4) uci_p.txt lists `option name EvalRule50Damp type check default false` and `option name EvalRule50Damp_Span type spin default 100 min 1 max 200`.

(5) AddressSanitizer and UndefinedBehaviorSanitizer build of ../work. First 100 of G at depth 10 with the switch true: 100 rows, failed empty, 0 sanitizer lines in the raw log. asan_G100_d10.meta has NM_COUNT=35 from `nm -C` counting `__asan_`. The scratch copy, one heap read past the end of a 4-int array on the FEN in special_fen.txt, run through depth_set.py, reports `ERROR: AddressSanitizer: heap-buffer-overflow` in uci.cpp apply_position (asan_scratch_special.raw.txt).

Match: exe P switch true vs switch false, S14, Threads 1, Hash 16, OwnBook false, nodes 20000, openings O+G, both colours. fastchess output match_OG.txt, last result lines:

```
Elo: -22.02 +/- 10.40, nElo: -43.46 +/- 20.48
Games: 1106, Wins: 318, Losses: 388, Draws: 400, Points: 518.0 (46.84 %)
```

That point is below -20 and the printed interval is entirely below 0, so I looked once. looked_once.txt: at span 100 the fade is the original formula, and exe B with the switch on matches exe P on all 200 O rows. I did not find a mistake. prediction.txt said sum 10400000 (wrong outside 8000000..13000000) and Elo +8 (wrong outside -30..+45). The measured sum 10347764 and Elo -22.02 sit inside those ranges.

Partner: seat 051 (idea 1; seat 101 has no branch). Verdict CONFIRMS. Their patch adds IdeaE2 default false and IdeaE2_Span default 100 beside the existing switch. On a fresh worktree of the base, git apply --check succeeded and the patch applied. Honesty numbers matched. IdeaE2 false: differ=0 of 200 against exe B's O rows (partner_cmp_off_O.txt). IdeaE2 true: node_differ=0 of 200 against their P_on_O.nodes, sum=10347764, and node_differ=200 of 200 against exe B (partner_cmp_on_O.txt, partner_on_O.sum.txt, partner_node_on_vs_B.txt). Their R match, my 300 R openings, both colours, last lines of partner_match_R.txt:

```
Elo: -6.37 +/- 11.05, nElo: -16.04 +/- 27.80
Games: 600, Wins: 268, Losses: 279, Draws: 53, Points: 294.5 (49.08 %)
```

I did not repeat their sanitizer build or their 1106-game match. The checks STEP 4 names agree with what they claim, including on_differs=200 of 200 and off_identical=yes.

suspicions, not proven: their published Elo -22.02 +/- 10.40 is the same pair as my match. I did not show that this came from copying. The on-path node counts are identical and the games are fixed-node and single-thread, so the same games are what the rules of the match produce. All 200 opening rows change with the switch on. That fits the clock rising inside the tree. The off path matches to the node.

what I did NOT do: I did not add a second check named IdeaE2. I did not measure a span other than 100. I did not play my own patch on the R set, because the partner patch was there. I did not find a FABLE_TO_grok file on the handoff branch at STEP 1 or at minute 60. I did not open a pull request.

what I am NOT sure about: whether any span other than 100 is worth a match. This sample only says that today's scale, switched on, lost about 22 Elo at 20000 nodes on the built-in net, with an error of 10.40.

times: see stamps.txt

## pasted report_from_files.py

TABLE
step | status | evidence | result
1 seat | done | SEAT.txt stamps.txt | seat 001 idea 1
2 builds and honesty | done | HONESTY_B.txt B_O_d12.sum.txt B_G_d12.sum.txt | known nodes and known sums
3 idea | done | idea.patch.txt apply_check.txt cmp_off_O.txt cmp_on_O.txt asan_G100_d10.meta match_OG.txt | off identical, on differs, match played
4 partner | done | partner_cmp_off_O.txt partner_cmp_on_O.txt partner_match_R.txt | see partner section
5 report | done | REPORT.md RESULT.txt | this file
HONESTY_B
honesty_b_bench11.txt PASS hits=1 expected_nodes=312866
info string bench depth 11 nodes 312866 time 215 nps 1455190
honesty_b_bench13.txt PASS hits=1 expected_nodes=862329
info string bench depth 13 nodes 862329 time 470 nps 1834742
honesty_b_bench16.txt PASS hits=1 expected_nodes=3024920
info string bench depth 16 nodes 3024920 time 1426 nps 2121262
honesty_b_perft5.txt PASS hits=1 expected_nodes=4865609
nodes 4865609
HONESTY_B PASS
SUM_B_O
file=forge-combo29/grok/001/B_O_d12.rows.txt
positions=200
sum=9500069
first3=41311 / 24872 / 28574
SUM_B_G
file=forge-combo29/grok/001/B_G_d12.rows.txt
positions=353
sum=18466239
first3=37203 / 70845 / 144383
CMP_OFF_O
left=forge-combo29/grok/001/B_O_d12.rows.txt
right=forge-combo29/grok/001/P_off_O_d12.rows.txt
positions=200
differ=0 of 200
CMP_OFF_G
left=forge-combo29/grok/001/B_G_d12.rows.txt
right=forge-combo29/grok/001/P_off_G_d12.rows.txt
positions=353
differ=0 of 353
CMP_ON_O
left=forge-combo29/grok/001/B_O_d12.rows.txt
right=forge-combo29/grok/001/P_on_O_d12.rows.txt
positions=200
differ=200 of 200
NODE_ON
left=forge-combo29/grok/001/B_O_d12.rows.txt
right=forge-combo29/grok/001/P_on_O_d12.rows.txt
node_differ=200 of 200
SUM_P_ON
file=forge-combo29/grok/001/P_on_O_d12.rows.txt
positions=200
sum=10347764
first3=18069 / 37645 / 36805
NODE_BON_PON
left=forge-combo29/grok/001/B_on_O_d12.rows.txt
right=forge-combo29/grok/001/P_on_O_d12.rows.txt
node_differ=0 of 200
ASAN_META_TAIL
rows=100
failed=
NM_COUNT=35
nm_command=nm -C /tmp/asan-work/forge | grep -c __asan_
ASAN_SCRATCH_HITS
lines=2
<< ==8163==ERROR: AddressSanitizer: heap-buffer-overflow on address 0x5020000000c0 at pc 0x561bfd612dd7 bp 0x7ffda8a006f0 sp 0x7ffda8a006e0
<< SUMMARY: AddressSanitizer: heap-buffer-overflow /tmp/asan-scratch/forge-combo29/src/uci.cpp:48 in apply_position
MATCH_OG
Elo: -22.02 +/- 10.40, nElo: -43.46 +/- 20.48
Games: 1106, Wins: 318, Losses: 388, Draws: 400, Points: 518.0 (46.84 %)
PARTNER_OFF
left=forge-combo29/grok/001/B_O_d12.rows.txt
right=forge-combo29/grok/001/partner_off_O.rows.txt
positions=200
differ=0 of 200
PARTNER_ON_VS_THEIRS
left=forge-combo29/grok/001/partner051_P_on_O.nodes
right=forge-combo29/grok/001/partner_on_O.rows.txt
node_differ=0 of 200
PARTNER_ON_VS_B
left=forge-combo29/grok/001/B_O_d12.rows.txt
right=forge-combo29/grok/001/partner_on_O.rows.txt
node_differ=200 of 200
PARTNER_ON_SUM
file=forge-combo29/grok/001/partner_on_O.rows.txt
positions=200
sum=10347764
first3=18069 / 37645 / 36805
PARTNER_MATCH
Elo: -6.37 +/- 11.05, nElo: -16.04 +/- 27.80
Games: 600, Wins: 268, Losses: 279, Draws: 53, Points: 294.5 (49.08 %)

## git status --short

 M forge-combo29/grok/001/depth_set.py
 M forge-combo29/grok/001/stamps.txt
?? forge-combo29/grok/001/REPORT.md
?? forge-combo29/grok/001/RESULT.txt
?? forge-combo29/grok/001/partner051_P_on_O.nodes
?? forge-combo29/grok/001/partner051_idea.patch.txt
?? forge-combo29/grok/001/partner_apply_check.txt
?? forge-combo29/grok/001/partner_cmp_off_O.txt
?? forge-combo29/grok/001/partner_cmp_on_O.txt
?? forge-combo29/grok/001/partner_h_bench11.meta
?? forge-combo29/grok/001/partner_h_bench11.txt
?? forge-combo29/grok/001/partner_h_bench13.meta
?? forge-combo29/grok/001/partner_h_bench13.txt
?? forge-combo29/grok/001/partner_h_bench16.meta
?? forge-combo29/grok/001/partner_h_bench16.txt
?? forge-combo29/grok/001/partner_h_perft5.meta
?? forge-combo29/grok/001/partner_h_perft5.txt
?? forge-combo29/grok/001/partner_match_R.meta
?? forge-combo29/grok/001/partner_match_R.pgn
?? forge-combo29/grok/001/partner_match_R.txt
?? forge-combo29/grok/001/partner_node_off_O.txt
?? forge-combo29/grok/001/partner_node_on_vs_B.txt
?? forge-combo29/grok/001/partner_off_O.meta
?? forge-combo29/grok/001/partner_off_O.raw.txt
?? forge-combo29/grok/001/partner_off_O.rows.txt
?? forge-combo29/grok/001/partner_on_O.meta
?? forge-combo29/grok/001/partner_on_O.raw.txt
?? forge-combo29/grok/001/partner_on_O.rows.txt
?? forge-combo29/grok/001/partner_on_O.sum.txt
?? forge-combo29/grok/001/partner_uci.meta
?? forge-combo29/grok/001/partner_uci.txt
?? forge-combo29/grok/001/report_from_files.py
?? forge-combo29/grok/001/report_numbers.txt
?? forge-combo29/grok/001/run_partner_match.sh

## ls -la

total 9140
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 09:15 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:51 ..
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:01 apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu     924 Nov 20 08:02 asan_G100_d10.meta
-rw-r--r-- 1 ubuntu ubuntu  135688 Nov 20 08:02 asan_G100_d10.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    2111 Nov 20 08:02 asan_G100_d10.rows.txt
-rw-r--r-- 1 ubuntu ubuntu       3 Nov 20 08:02 asan_nm_count.txt
-rw-r--r-- 1 ubuntu ubuntu     888 Nov 20 08:03 asan_scratch_special.meta
-rw-r--r-- 1 ubuntu ubuntu   10074 Nov 20 08:03 asan_scratch_special.raw.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:03 asan_scratch_special.rows.txt
-rw-r--r-- 1 ubuntu ubuntu     838 Nov 20 07:58 B_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  566393 Nov 20 07:58 B_G_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    7765 Nov 20 07:58 B_G_d12.rows.txt
-rw-r--r-- 1 ubuntu ubuntu     102 Nov 20 07:59 B_G_d12.sum.txt
-rw-r--r-- 1 ubuntu ubuntu     838 Nov 20 07:58 B_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  318546 Nov 20 07:58 B_O_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    4187 Nov 20 07:58 B_O_d12.rows.txt
-rw-r--r-- 1 ubuntu ubuntu     100 Nov 20 07:59 B_O_d12.sum.txt
-rw-r--r-- 1 ubuntu ubuntu     879 Nov 20 08:13 B_on_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  318073 Nov 20 08:13 B_on_O_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    4178 Nov 20 08:13 B_on_O_d12.rows.txt
-rw-r--r-- 1 ubuntu ubuntu     127 Nov 20 08:13 cmp_Bon_Pon.txt
-rw-r--r-- 1 ubuntu ubuntu     125 Nov 20 08:01 cmp_off_G.txt
-rw-r--r-- 1 ubuntu ubuntu     125 Nov 20 08:01 cmp_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu     471 Nov 20 08:01 cmp_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu     753 Nov 20 08:00 compare_rows.py
-rw-r--r-- 1 ubuntu ubuntu    7394 Nov 20 08:14 depth_set.py
-rw-r--r-- 1 ubuntu ubuntu   12861 Nov 20 07:58 first200.fens
-rw-r--r-- 1 ubuntu ubuntu     199 Nov 20 07:57 honesty_b_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 07:57 honesty_b_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     199 Nov 20 07:57 honesty_b_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 07:57 honesty_b_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     199 Nov 20 07:57 honesty_b_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 07:57 honesty_b_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     201 Nov 20 07:57 honesty_b_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 07:57 honesty_b_perft5.txt
-rwxr-xr-x 1 ubuntu ubuntu    1830 Nov 20 07:57 honesty_b.sh
-rw-r--r-- 1 ubuntu ubuntu     439 Nov 20 07:57 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu    1286 Nov 20 08:00 honesty_fresh.sh
-rw-r--r-- 1 ubuntu ubuntu     199 Nov 20 08:00 honesty_p_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:00 honesty_p_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     199 Nov 20 08:00 honesty_p_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:00 honesty_p_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     199 Nov 20 08:00 honesty_p_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:00 honesty_p_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     201 Nov 20 08:00 honesty_p_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:00 honesty_p_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    3384 Nov 20 08:00 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu     815 Nov 20 08:14 looked_once.txt
-rw-r--r-- 1 ubuntu ubuntu    1113 Nov 20 08:04 make_r.py
-rw-r--r-- 1 ubuntu ubuntu     331 Nov 20 08:05 match_OG.meta
-rw-r--r-- 1 ubuntu ubuntu 3602869 Nov 20 08:12 match_OG.pgn
-rw-r--r-- 1 ubuntu ubuntu  124718 Nov 20 08:12 match_OG.txt
-rw-r--r-- 1 ubuntu ubuntu     118 Nov 20 08:13 node_diff_Bon_Pon.txt
-rw-r--r-- 1 ubuntu ubuntu     116 Nov 20 08:04 node_diff_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu     117 Nov 20 08:04 node_diff_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu     587 Nov 20 08:04 node_diff.py
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:04 openings_OG.epd
-rw-r--r-- 1 ubuntu ubuntu    5339 Nov 20 09:08 partner051_idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    1897 Nov 20 09:08 partner051_P_on_O.nodes
-rw-r--r-- 1 ubuntu ubuntu     410 Nov 20 09:09 partner_apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu     127 Nov 20 09:09 partner_cmp_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu     124 Nov 20 09:09 partner_cmp_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu     191 Nov 20 09:09 partner_h_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:09 partner_h_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     191 Nov 20 09:09 partner_h_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:09 partner_h_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     191 Nov 20 09:09 partner_h_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 09:09 partner_h_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     193 Nov 20 09:09 partner_h_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 09:09 partner_h_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     248 Nov 20 09:09 partner_match_R.meta
-rw-r--r-- 1 ubuntu ubuntu 1798203 Nov 20 09:13 partner_match_R.pgn
-rw-r--r-- 1 ubuntu ubuntu   63494 Nov 20 09:13 partner_match_R.txt
-rw-r--r-- 1 ubuntu ubuntu     118 Nov 20 09:09 partner_node_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu     119 Nov 20 09:09 partner_node_on_vs_B.txt
-rw-r--r-- 1 ubuntu ubuntu     864 Nov 20 09:09 partner_off_O.meta
-rw-r--r-- 1 ubuntu ubuntu  318350 Nov 20 09:09 partner_off_O.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    4187 Nov 20 09:09 partner_off_O.rows.txt
-rw-r--r-- 1 ubuntu ubuntu     863 Nov 20 09:09 partner_on_O.meta
-rw-r--r-- 1 ubuntu ubuntu  318189 Nov 20 09:09 partner_on_O.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    4178 Nov 20 09:09 partner_on_O.rows.txt
-rw-r--r-- 1 ubuntu ubuntu     106 Nov 20 09:09 partner_on_O.sum.txt
-rw-r--r-- 1 ubuntu ubuntu     186 Nov 20 09:09 partner_uci.meta
-rw-r--r-- 1 ubuntu ubuntu    5037 Nov 20 09:09 partner_uci.txt
-rw-r--r-- 1 ubuntu ubuntu     880 Nov 20 08:01 P_off_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  566591 Nov 20 08:01 P_off_G_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    7765 Nov 20 08:01 P_off_G_d12.rows.txt
-rw-r--r-- 1 ubuntu ubuntu     106 Nov 20 08:01 P_off_G_d12.sum.txt
-rw-r--r-- 1 ubuntu ubuntu     880 Nov 20 08:00 P_off_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  318665 Nov 20 08:00 P_off_O_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    4187 Nov 20 08:00 P_off_O_d12.rows.txt
-rw-r--r-- 1 ubuntu ubuntu     104 Nov 20 08:01 P_off_O_d12.sum.txt
-rw-r--r-- 1 ubuntu ubuntu     879 Nov 20 08:01 P_on_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  318432 Nov 20 08:01 P_on_O_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    4178 Nov 20 08:01 P_on_O_d12.rows.txt
-rw-r--r-- 1 ubuntu ubuntu     104 Nov 20 08:01 P_on_O_d12.sum.txt
-rw-r--r-- 1 ubuntu ubuntu     906 Nov 20 07:59 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu   19974 Nov 20 08:04 R300.epd
-rw-r--r-- 1 ubuntu ubuntu      89 Nov 20 08:04 R300.meta
-rw-r--r-- 1 ubuntu ubuntu    2646 Nov 20 09:14 report_from_files.py
-rw-r--r-- 1 ubuntu ubuntu   10163 Nov 20 09:15 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    3123 Nov 20 09:14 report_numbers.txt
-rw-r--r-- 1 ubuntu ubuntu     221 Nov 20 09:15 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu    1711 Nov 20 08:05 run_match.sh
-rw-r--r-- 1 ubuntu ubuntu    1541 Nov 20 09:09 run_partner_match.sh
-rw-r--r-- 1 ubuntu ubuntu      76 Nov 20 07:51 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu    5009 Nov 20 08:02 set_G100.epd
-rw-r--r-- 1 ubuntu ubuntu   17691 Nov 20 07:58 set_G.epd
-rw-r--r-- 1 ubuntu ubuntu      28 Nov 20 08:02 special_fen.txt
-rw-r--r-- 1 ubuntu ubuntu     112 Nov 20 09:15 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu     501 Nov 20 07:58 sum_rows.py
-rw-r--r-- 1 ubuntu ubuntu     771 Nov 20 08:00 uci_options.sh
-rw-r--r-- 1 ubuntu ubuntu     194 Nov 20 08:00 uci_p.meta
-rw-r--r-- 1 ubuntu ubuntu    5001 Nov 20 08:00 uci_p.txt

## final git status --short

 M forge-combo29/grok/001/depth_set.py
 M forge-combo29/grok/001/stamps.txt
?? forge-combo29/grok/001/REPORT.md
?? forge-combo29/grok/001/RESULT.txt
?? forge-combo29/grok/001/partner051_P_on_O.nodes
?? forge-combo29/grok/001/partner051_idea.patch.txt
?? forge-combo29/grok/001/partner_apply_check.txt
?? forge-combo29/grok/001/partner_cmp_off_O.txt
?? forge-combo29/grok/001/partner_cmp_on_O.txt
?? forge-combo29/grok/001/partner_h_bench11.meta
?? forge-combo29/grok/001/partner_h_bench11.txt
?? forge-combo29/grok/001/partner_h_bench13.meta
?? forge-combo29/grok/001/partner_h_bench13.txt
?? forge-combo29/grok/001/partner_h_bench16.meta
?? forge-combo29/grok/001/partner_h_bench16.txt
?? forge-combo29/grok/001/partner_h_perft5.meta
?? forge-combo29/grok/001/partner_h_perft5.txt
?? forge-combo29/grok/001/partner_match_R.meta
?? forge-combo29/grok/001/partner_match_R.pgn
?? forge-combo29/grok/001/partner_match_R.txt
?? forge-combo29/grok/001/partner_node_off_O.txt
?? forge-combo29/grok/001/partner_node_on_vs_B.txt
?? forge-combo29/grok/001/partner_off_O.meta
?? forge-combo29/grok/001/partner_off_O.raw.txt
?? forge-combo29/grok/001/partner_off_O.rows.txt
?? forge-combo29/grok/001/partner_on_O.meta
?? forge-combo29/grok/001/partner_on_O.raw.txt
?? forge-combo29/grok/001/partner_on_O.rows.txt
?? forge-combo29/grok/001/partner_on_O.sum.txt
?? forge-combo29/grok/001/partner_uci.meta
?? forge-combo29/grok/001/partner_uci.txt
?? forge-combo29/grok/001/report_from_files.py
?? forge-combo29/grok/001/report_numbers.txt
?? forge-combo29/grok/001/run_partner_match.sh

## final ls -la

total 9148
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 09:15 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:51 ..
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:01 apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu     924 Nov 20 08:02 asan_G100_d10.meta
-rw-r--r-- 1 ubuntu ubuntu  135688 Nov 20 08:02 asan_G100_d10.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    2111 Nov 20 08:02 asan_G100_d10.rows.txt
-rw-r--r-- 1 ubuntu ubuntu       3 Nov 20 08:02 asan_nm_count.txt
-rw-r--r-- 1 ubuntu ubuntu     888 Nov 20 08:03 asan_scratch_special.meta
-rw-r--r-- 1 ubuntu ubuntu   10074 Nov 20 08:03 asan_scratch_special.raw.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:03 asan_scratch_special.rows.txt
-rw-r--r-- 1 ubuntu ubuntu     838 Nov 20 07:58 B_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  566393 Nov 20 07:58 B_G_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    7765 Nov 20 07:58 B_G_d12.rows.txt
-rw-r--r-- 1 ubuntu ubuntu     102 Nov 20 07:59 B_G_d12.sum.txt
-rw-r--r-- 1 ubuntu ubuntu     838 Nov 20 07:58 B_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  318546 Nov 20 07:58 B_O_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    4187 Nov 20 07:58 B_O_d12.rows.txt
-rw-r--r-- 1 ubuntu ubuntu     100 Nov 20 07:59 B_O_d12.sum.txt
-rw-r--r-- 1 ubuntu ubuntu     879 Nov 20 08:13 B_on_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  318073 Nov 20 08:13 B_on_O_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    4178 Nov 20 08:13 B_on_O_d12.rows.txt
-rw-r--r-- 1 ubuntu ubuntu     127 Nov 20 08:13 cmp_Bon_Pon.txt
-rw-r--r-- 1 ubuntu ubuntu     125 Nov 20 08:01 cmp_off_G.txt
-rw-r--r-- 1 ubuntu ubuntu     125 Nov 20 08:01 cmp_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu     471 Nov 20 08:01 cmp_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu     753 Nov 20 08:00 compare_rows.py
-rw-r--r-- 1 ubuntu ubuntu    7394 Nov 20 08:14 depth_set.py
-rw-r--r-- 1 ubuntu ubuntu   12861 Nov 20 07:58 first200.fens
-rw-r--r-- 1 ubuntu ubuntu     199 Nov 20 07:57 honesty_b_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 07:57 honesty_b_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     199 Nov 20 07:57 honesty_b_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 07:57 honesty_b_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     199 Nov 20 07:57 honesty_b_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 07:57 honesty_b_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     201 Nov 20 07:57 honesty_b_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 07:57 honesty_b_perft5.txt
-rwxr-xr-x 1 ubuntu ubuntu    1830 Nov 20 07:57 honesty_b.sh
-rw-r--r-- 1 ubuntu ubuntu     439 Nov 20 07:57 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu    1286 Nov 20 08:00 honesty_fresh.sh
-rw-r--r-- 1 ubuntu ubuntu     199 Nov 20 08:00 honesty_p_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:00 honesty_p_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     199 Nov 20 08:00 honesty_p_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:00 honesty_p_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     199 Nov 20 08:00 honesty_p_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:00 honesty_p_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     201 Nov 20 08:00 honesty_p_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:00 honesty_p_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    3384 Nov 20 08:00 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu     815 Nov 20 08:14 looked_once.txt
-rw-r--r-- 1 ubuntu ubuntu    1113 Nov 20 08:04 make_r.py
-rw-r--r-- 1 ubuntu ubuntu     331 Nov 20 08:05 match_OG.meta
-rw-r--r-- 1 ubuntu ubuntu 3602869 Nov 20 08:12 match_OG.pgn
-rw-r--r-- 1 ubuntu ubuntu  124718 Nov 20 08:12 match_OG.txt
-rw-r--r-- 1 ubuntu ubuntu     118 Nov 20 08:13 node_diff_Bon_Pon.txt
-rw-r--r-- 1 ubuntu ubuntu     116 Nov 20 08:04 node_diff_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu     117 Nov 20 08:04 node_diff_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu     587 Nov 20 08:04 node_diff.py
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:04 openings_OG.epd
-rw-r--r-- 1 ubuntu ubuntu    5339 Nov 20 09:08 partner051_idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    1897 Nov 20 09:08 partner051_P_on_O.nodes
-rw-r--r-- 1 ubuntu ubuntu     410 Nov 20 09:09 partner_apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu     127 Nov 20 09:09 partner_cmp_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu     124 Nov 20 09:09 partner_cmp_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu     191 Nov 20 09:09 partner_h_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:09 partner_h_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     191 Nov 20 09:09 partner_h_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:09 partner_h_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     191 Nov 20 09:09 partner_h_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 09:09 partner_h_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     193 Nov 20 09:09 partner_h_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 09:09 partner_h_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     248 Nov 20 09:09 partner_match_R.meta
-rw-r--r-- 1 ubuntu ubuntu 1798203 Nov 20 09:13 partner_match_R.pgn
-rw-r--r-- 1 ubuntu ubuntu   63494 Nov 20 09:13 partner_match_R.txt
-rw-r--r-- 1 ubuntu ubuntu     118 Nov 20 09:09 partner_node_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu     119 Nov 20 09:09 partner_node_on_vs_B.txt
-rw-r--r-- 1 ubuntu ubuntu     864 Nov 20 09:09 partner_off_O.meta
-rw-r--r-- 1 ubuntu ubuntu  318350 Nov 20 09:09 partner_off_O.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    4187 Nov 20 09:09 partner_off_O.rows.txt
-rw-r--r-- 1 ubuntu ubuntu     863 Nov 20 09:09 partner_on_O.meta
-rw-r--r-- 1 ubuntu ubuntu  318189 Nov 20 09:09 partner_on_O.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    4178 Nov 20 09:09 partner_on_O.rows.txt
-rw-r--r-- 1 ubuntu ubuntu     106 Nov 20 09:09 partner_on_O.sum.txt
-rw-r--r-- 1 ubuntu ubuntu     186 Nov 20 09:09 partner_uci.meta
-rw-r--r-- 1 ubuntu ubuntu    5037 Nov 20 09:09 partner_uci.txt
-rw-r--r-- 1 ubuntu ubuntu     880 Nov 20 08:01 P_off_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  566591 Nov 20 08:01 P_off_G_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    7765 Nov 20 08:01 P_off_G_d12.rows.txt
-rw-r--r-- 1 ubuntu ubuntu     106 Nov 20 08:01 P_off_G_d12.sum.txt
-rw-r--r-- 1 ubuntu ubuntu     880 Nov 20 08:00 P_off_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  318665 Nov 20 08:00 P_off_O_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    4187 Nov 20 08:00 P_off_O_d12.rows.txt
-rw-r--r-- 1 ubuntu ubuntu     104 Nov 20 08:01 P_off_O_d12.sum.txt
-rw-r--r-- 1 ubuntu ubuntu     879 Nov 20 08:01 P_on_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  318432 Nov 20 08:01 P_on_O_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    4178 Nov 20 08:01 P_on_O_d12.rows.txt
-rw-r--r-- 1 ubuntu ubuntu     104 Nov 20 08:01 P_on_O_d12.sum.txt
-rw-r--r-- 1 ubuntu ubuntu     906 Nov 20 07:59 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu   19974 Nov 20 08:04 R300.epd
-rw-r--r-- 1 ubuntu ubuntu      89 Nov 20 08:04 R300.meta
-rw-r--r-- 1 ubuntu ubuntu    2646 Nov 20 09:14 report_from_files.py
-rw-r--r-- 1 ubuntu ubuntu   19402 Nov 20 09:16 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    3123 Nov 20 09:14 report_numbers.txt
-rw-r--r-- 1 ubuntu ubuntu     221 Nov 20 09:15 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu    1711 Nov 20 08:05 run_match.sh
-rw-r--r-- 1 ubuntu ubuntu    1541 Nov 20 09:09 run_partner_match.sh
-rw-r--r-- 1 ubuntu ubuntu      76 Nov 20 07:51 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu    5009 Nov 20 08:02 set_G100.epd
-rw-r--r-- 1 ubuntu ubuntu   17691 Nov 20 07:58 set_G.epd
-rw-r--r-- 1 ubuntu ubuntu      28 Nov 20 08:02 special_fen.txt
-rw-r--r-- 1 ubuntu ubuntu     140 Nov 20 09:16 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu     501 Nov 20 07:58 sum_rows.py
-rw-r--r-- 1 ubuntu ubuntu     771 Nov 20 08:00 uci_options.sh
-rw-r--r-- 1 ubuntu ubuntu     194 Nov 20 08:00 uci_p.meta
-rw-r--r-- 1 ubuntu ubuntu    5001 Nov 20 08:00 uci_p.txt
