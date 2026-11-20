# REPORT seat 083

IdeaA2. At a node off the principal line, a fail-high at depth 2 or more that is not a mate is returned as (score * depth + beta) / (depth + 1).
I added check option IdeaA2, default false, and spin IdeaA2_MinDepth, default 2. The change is only in idea.patch.txt. `git apply --check` on a clean copy of 6b98f2170 exits 0 (apply_check.txt).
With the check false, idea_a2_score returns the original score before any arithmetic. With the check true, the blended value is what the node stores, what the correction history is taught, and what the parent receives. Quiescence is unchanged. A hash hit is not blended again.

EXISTS: no. I read search.cpp and uci.cpp. The plain engine does not blend a fail-high toward beta.

Honesty, no setoption, exe B and exe P. bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, go perft 5 nodes 4865609. All four match. See HONESTY_B.txt and HONESTY_P.txt.

The block below is the output of paste_evidence.py. It reads the raw files. I did not retype those numbers.

```
file	key
HONESTY_B.txt	['bench11 312866 312866 yes honesty_b_bench11.txt', 'bench13 862329 862329 yes honesty_b_bench13.txt', 'bench16 3024920 3024920 yes honesty_b_bench16.txt', 'perft5 4865609 4865609 yes honesty_b_perft5.txt']
--- HONESTY_B ---
exe /agent/repos/base/forge-combo29/build/forge
sha256 e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83
id name Chess Engine Forge 6.4.24 candidate
label nodes expect match file
bench11 312866 312866 yes honesty_b_bench11.txt
bench13 862329 862329 yes honesty_b_bench13.txt
bench16 3024920 3024920 yes honesty_b_bench16.txt
perft5 4865609 4865609 yes honesty_b_perft5.txt
--- HONESTY_P ---
exe /agent/repos/work/forge-combo29/build/forge
sha256 4f3a4eabd8638f62b24367ace288e958108fccaf05a1e2f36b6e2e47d4ef880a
id name Chess Engine Forge 6.4.24 candidate
label nodes expect match file
bench11 312866 312866 yes honesty_p_bench11.txt
bench13 862329 862329 yes honesty_p_bench13.txt
bench16 3024920 3024920 yes honesty_p_bench16.txt
perft5 4865609 4865609 yes honesty_p_perft5.txt
--- B_SUMS ---
file	positions	sum	first3
O_d12_B.tsv	200	9500069	41311 24872 28574
G_d12_B.tsv	353	18466239	37203 70845 144383
--- P_SUMS ---
file	positions	sum	first3
O_d12_P_off.tsv	200	9500069	41311 24872 28574
G_d12_P_off.tsv	353	18466239	37203 70845 144383
O_d12_P_on.tsv	200	9235597	20289 17907 37480
--- compare off O ---
left forge-combo29/grok/083/O_d12_B.tsv
right forge-combo29/grok/083/O_d12_P_off.tsv
positions 200
differ 0
same 200
--- compare off G ---
left forge-combo29/grok/083/G_d12_B.tsv
right forge-combo29/grok/083/G_d12_P_off.tsv
positions 353
differ 0
same 353
--- compare on O head ---
left forge-combo29/grok/083/O_d12_B.tsv
right forge-combo29/grok/083/O_d12_P_on.tsv
positions 200
differ 200
same 0
pos 1 41311 20289
pos 2 24872 17907
pos 3 28574 37480
--- match elo ---
Results of IdeaA2on vs IdeaA2off (20000 nodes, 1t, 16MB, OG_553.epd):
Elo: -10.06 +/- 10.86, nElo: -18.98 +/- 20.48
LOS: 3.46 %, DrawRatio: 61.48 %, PairsRatio: 0.78
Games: 1106, Wins: 327, Losses: 359, Draws: 420, Points: 537.0 (48.55 %)
Ptnml(0-2): [19, 101, 340, 79, 14], WL/DD Ratio: 1.83
--------------------------------------------------
---
Elo: -10.06 +/- 10.86, nElo: -18.98 +/- 20.48
Games: 1106, Wins: 327, Losses: 359, Draws: 420, Points: 537.0 (48.55 %)
--- asan meta tail ---
setoption name HistoryBonusLinear value 54
setoption name HistoryBonusMax value 2212
setoption name SingularDepth value 6
setoption name IirDepth value 2
setoption name NonPawnCorrection value true
nm_asan_count: 35
--- scratch meta ---
exe: /tmp/scratch-forge/build-asan/forge
sha256: 1bb92a4a052cddf17b4266470af1c6c767af2a9683c591e4495ed9ddbde328b8
nm_asan_count: 35
fen: 4k3/8/8/8/3Q4/8/8/4K3 w - - 0 1
runner: python3 search_set.py --exe this --fens scratch_fen.epd --depth 10 --idea true --label scratch_asan
search_exit: 1
/tmp/scratch-forge/src/search.cpp:1571:22: runtime error: load of address 0x502000001090 with insufficient space for an object of type 'int'
--- uci idea lines ---
option name IdeaA2 type check default false
option name IdeaA2_MinDepth type spin default 2 min 1 max 64
--- apply_check ---
exit:0
--- prediction ---
predicted_at: 2026-11-20T08:16:30Z
O_depth12_sum_IdeaA2_on: 11000000
wrong_if_outside: 9600000 14000000
elo_IdeaA2_on_vs_off: -8
elo_wrong_if_outside: -45 30
why: A stored fail-high closer to beta cuts off less often later, so the O depth-12 sum should rise above 9500069 and stay inside 9600000..14000000. Blending throws away fail-soft margin, so the match Elo should be a small loss inside -45..30. An unchanged 9500069, or any result outside those bands, shows this prediction was wrong.
--- partner honesty ---
exe /agent/repos/partner/forge-combo29/build/forge
sha256 a7f77b0f8279587a8073fbabfdd9120ba41f7468aebb68f959e73daf5cd7be25
id name Chess Engine Forge 6.4.24 candidate
label nodes expect match file
bench11 312866 312866 yes partner_h_bench11.txt
bench13 862329 862329 yes partner_h_bench13.txt
bench16 3024920 3024920 yes partner_h_bench16.txt
perft5 4865609 4865609 yes partner_h_perft5.txt
--- partner off ---
left forge-combo29/grok/083/O_d12_B.tsv
right forge-combo29/grok/083/partner_O_off.tsv
positions 200
differ 0
same 200
--- partner on vs claimed ---
positions 200
differ 0
same 200
my_sum 9490331
claimed_sum 9490331
--- partner on vs B head ---
left forge-combo29/grok/083/O_d12_B.tsv
right forge-combo29/grok/083/partner_O_on.tsv
positions 200
differ 200
same 0
pos 1 41311 42509
--- partner apply ---
apply_check_exit:0
patch: /agent/repos/dwqww/forge-combo29/grok/083/partner_033_idea.patch.txt
clean_tree: /agent/repos/applycheck 6b98f2170a3210e71beed04bbd2553972c253ed7
--- partner match ---
Results of IdeaA2on vs IdeaA2off (20000 nodes, 1t, 16MB, R_300.epd):
Elo: -11.59 +/- 8.85, nElo: -36.42 +/- 27.80
LOS: 0.51 %, DrawRatio: 83.33 %, PairsRatio: 0.52
Games: 600, Wins: 258, Losses: 278, Draws: 64, Points: 290.0 (48.33 %)
Ptnml(0-2): [4, 29, 250, 17, 0], WL/DD Ratio: 26.78
--------------------------------------------------
---
Elo: -11.59 +/- 8.85, nElo: -36.42 +/- 27.80
Games: 600, Wins: 258, Losses: 278, Draws: 64, Points: 290.0 (48.33 %)
--- stamps ---
2026-11-20T07:55:44Z STEP 1 seat
2026-11-20T08:16:16Z STEP 2 honesty and known sums
2026-11-20T08:31:36Z STEP 3 idea built, proved, match played
2026-11-20T09:17:24Z STEP 4 partner 033
2026-11-20T09:17:24Z STEP 5 report
--- step table ---
step	status	evidence	result
1 seat	done	SEAT.txt stamps.txt	seat 083 idea 33
2 honesty and known sums	done	HONESTY_B.txt B_SUMS.txt	bench11 312866 312866 yes honesty_b_bench11.txt bench13 862329 862329 yes honesty_b_bench13.txt bench16 3024920 3024920 yes honesty_b_bench16.txt perft5 4865609 4865609 yes honesty_b_perft5.txt
2 O and G on exe B	done	B_SUMS.txt	O_d12_B.tsv	200	9500069	41311 24872 28574 | G_d12_B.tsv	353	18466239	37203 70845 144383
3 prediction	done	prediction.txt	committed before measuring exe P; node band missed, elo band hit
3 proof off	done	compare_O_off.txt compare_G_off.txt	differ 0 O; differ 0 G
3 proof on	done	compare_O_on.txt P_SUMS.txt	differ 200 of 200; sum 9235597
3 uci options	done	uci_p.txt	IdeaA2 check default false; IdeaA2_MinDepth spin default 2
3 sanitizer	done	G_d10_asan.meta scratch_asan.meta	nm_asan_count 35; clean G100; scratch reported a runtime error
3 match	done	match_og.txt match_og.pgn match_og_elo.txt	Elo: -10.06 +/- 10.86, nElo: -18.98 +/- 20.48; games 1106
4 partner 033	done	partner_compare_off.txt partner_compare_on.txt partner_match_elo.txt	CONFIRMS; Elo: -11.59 +/- 8.85, nElo: -36.42 +/- 27.80
5 report	done	REPORT.md RESULT.txt	this file
```

## Proofs

(1) Honesty on exe P with no setoption: the four pins above, unchanged. HONESTY_P.txt.

(2) S14 and IdeaA2 false. O depth 12: differ 0 of 200, sum 9500069, first three 41311 24872 28574, equal to exe B. G depth 12: differ 0 of 353, sum 18466239. compare_O_off.txt, compare_G_off.txt, P_SUMS.txt.

(3) S14 and IdeaA2 true. O depth 12: differ 200 of 200 from exe B, sum 9235597, first three 20289 17907 37480. compare_O_on.txt. The switch runs on every opening in the set.

(4) The uci answer lists `option name IdeaA2 type check default false` and `option name IdeaA2_MinDepth type spin default 2 min 1 max 64`. uci_p.txt.

(5) AddressSanitizer and UndefinedBehaviorSanitizer build. `nm -C` count of `__asan_` is 35 (G_d10_asan.meta). First 100 of G at depth 10, switch true: grep of the raw transcript for a sanitizer line is 0 (asan_clean_grep.txt). A scratch copy of that engine, one read past the end of a 4-int heap array, only when the FEN is `4k3/8/8/8/3Q4/8/8/4K3 w - - 0 1`, built the same way and run through search_set.py, reports `runtime error: load of address ... with insufficient space for an object of type 'int'` (scratch_asan.meta, scratch_asan.raw.txt).

## Match

exe P with IdeaA2 true against exe P with IdeaA2 false. S14, Threads 1, Hash 16, 20000 nodes a move, OwnBook false. Openings O then G, 553 positions, both colours, 1106 games. fastchess concurrency 3.

Elo: -10.06 +/- 10.86. Games 1106, wins 327, losses 359, draws 420. match_og.txt, match_og.pgn, match_og_elo.txt.

The point estimate is not below -20, and the interval is not entirely below 0, so I did not open the search for a second bug hunt.

Prediction, committed before any measurement of exe P (prediction.txt): O depth-12 sum 11000000, wrong outside 9600000..14000000. The measured sum is 9235597, so that prediction is wrong: the sum fell, it did not rise. Elo prediction -8, wrong outside -45..30. Measured Elo -10.06 is inside that band.

## Partner

Partner is seat 033. Idea seats are 033, 083, 133. I am 083. 133 has no branch. 033 does. Fetched for-fable-and-opus/grok-033 at b5434b023b1c5f9096c5a96796351cf679ece327.

Verdict: CONFIRMS. On a clean tree, git apply --check of their idea.patch.txt exits 0 (partner_apply_check.txt). Their build's honesty pins match. Switch false: O depth 12 differs in 0 of 200 positions from exe B. Switch true: my run's 200 node counts are identical to the counts I parsed from their P_on_O_d12.raw.txt (sum 9490331 both), and those 200 all differ from exe B, which is what they report in proof_on_O.txt. Their option names are IdeaA2 and IdeaA2_MinDepth, same defaults.

I then played their switch on against off, 300 of my R openings, both colours, 600 games. Elo: -11.59 +/- 8.85. partner_match.txt, partner_match.pgn. I did not replay their 1106-game OG match. They report Elo -1.88 +/- 10.45 for that match. That figure is theirs.

## suspicions, not proven

Blending the stored hash score, which my patch does and seat 033's patch does not, may be why my O sum moved further (9235597 against their 9490331). I did not isolate that one difference in a third build.

The 1106-game loss of about 10 Elo may be noise. The interval reaches above 0.

## what I did NOT do

I did not re-run seat 033's G depth-12 off proof (they say 0 of 353 differ). I re-ran their O set only, which is the check this step names.

I did not replay their 1106-game match.

I did not try IdeaA2_MinDepth at any value other than the default 2.

I did not run the sanitizer build on all of G, only the first 100 at depth 10.

The minute-60 fetch of handoff/fable-opus-combo29-all-20261114 found no FABLE_TO_grok file. Nothing there said STOP.

## what I am NOT sure about

The one-line idea says the fail-high score "is returned" blended. I also store that blended value. Seat 033 returns the blend and stores the raw score. I am not sure which reading the line requires. Both are off by default and both change all 200 openings.

I set OwnBook false in the matches. The engine's default is true, and a book would play the first moves without searching. I am not sure the match would look the same with the book left on.

I did not prove with a separate test that integer division of (score * depth + beta) / (depth + 1) always stays at least beta. The searches finished and still failed high often enough to change the tree. I am not sure about a negative-score edge.

R positions: seed 8301, games cut at ply 80, a position every 7 plies after ply 8, a game that ends before ply 80 is dropped. None of the 30 games ended before the cut. I am not sure that reading of "games that end are dropped" is the only one.

times: see stamps.txt


## git status --short

```
 M forge-combo29/grok/083/stamps.txt
?? forge-combo29/grok/083/HONESTY_PARTNER.txt
?? forge-combo29/grok/083/REPORT.md
?? forge-combo29/grok/083/RESULT.txt
?? forge-combo29/grok/083/asan_clean_grep.txt
?? forge-combo29/grok/083/compare_claimed.py
?? forge-combo29/grok/083/evidence_paste.txt
?? forge-combo29/grok/083/extract_bestmove_nodes.py
?? forge-combo29/grok/083/partner_033_O_on_claimed.tsv
?? forge-combo29/grok/083/partner_033_idea.patch.txt
?? forge-combo29/grok/083/partner_O_off.meta
?? forge-combo29/grok/083/partner_O_off.raw.txt
?? forge-combo29/grok/083/partner_O_off.tsv
?? forge-combo29/grok/083/partner_O_on.meta
?? forge-combo29/grok/083/partner_O_on.raw.txt
?? forge-combo29/grok/083/partner_O_on.tsv
?? forge-combo29/grok/083/partner_apply_check.txt
?? forge-combo29/grok/083/partner_compare_off.txt
?? forge-combo29/grok/083/partner_compare_on.txt
?? forge-combo29/grok/083/partner_compare_on_vs_B.txt
?? forge-combo29/grok/083/partner_h_bench11.meta
?? forge-combo29/grok/083/partner_h_bench11.txt
?? forge-combo29/grok/083/partner_h_bench13.meta
?? forge-combo29/grok/083/partner_h_bench13.txt
?? forge-combo29/grok/083/partner_h_bench16.meta
?? forge-combo29/grok/083/partner_h_bench16.txt
?? forge-combo29/grok/083/partner_h_perft5.meta
?? forge-combo29/grok/083/partner_h_perft5.txt
?? forge-combo29/grok/083/partner_match.log
?? forge-combo29/grok/083/partner_match.pgn
?? forge-combo29/grok/083/partner_match.txt
?? forge-combo29/grok/083/partner_match_elo.txt
?? forge-combo29/grok/083/paste_evidence.py
```

## ls -la

```
total 12416
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 09:18 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:55 ..
-rw-r--r-- 1 ubuntu ubuntu       7 Nov 20 08:19 apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu      14 Nov 20 09:17 asan_clean_grep.txt
-rw-r--r-- 1 ubuntu ubuntu     112 Nov 20 08:16 B_SUMS.txt
-rw-r--r-- 1 ubuntu ubuntu    1225 Nov 20 09:12 compare_claimed.py
-rw-r--r-- 1 ubuntu ubuntu     117 Nov 20 08:17 compare_G_off.txt
-rw-r--r-- 1 ubuntu ubuntu     117 Nov 20 08:17 compare_O_off.txt
-rw-r--r-- 1 ubuntu ubuntu     500 Nov 20 08:17 compare_O_on.txt
-rw-r--r-- 1 ubuntu ubuntu    1160 Nov 20 08:17 compare_tsv.py
-rw-r--r-- 1 ubuntu ubuntu    1567 Nov 20 08:15 DECISIONS.txt
-rw-r--r-- 1 ubuntu ubuntu    6613 Nov 20 09:17 evidence_paste.txt
-rw-r--r-- 1 ubuntu ubuntu    1005 Nov 20 09:11 extract_bestmove_nodes.py
-rw-r--r-- 1 ubuntu ubuntu   56926 Nov 20 08:20 G_d10_asan.meta
-rw-r--r-- 1 ubuntu ubuntu  215135 Nov 20 08:20 G_d10_asan.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    6342 Nov 20 08:20 G_d10_asan.tsv
-rw-r--r-- 1 ubuntu ubuntu  198553 Nov 20 08:14 G_d12_B.meta
-rw-r--r-- 1 ubuntu ubuntu  844909 Nov 20 08:14 G_d12_B.raw.txt
-rw-r--r-- 1 ubuntu ubuntu   22682 Nov 20 08:14 G_d12_B.tsv
-rw-r--r-- 1 ubuntu ubuntu  198587 Nov 20 08:17 G_d12_P_off.meta
-rw-r--r-- 1 ubuntu ubuntu  844767 Nov 20 08:17 G_d12_P_off.raw.txt
-rw-r--r-- 1 ubuntu ubuntu   22682 Nov 20 08:17 G_d12_P_off.tsv
-rw-r--r-- 1 ubuntu ubuntu    1272 Nov 20 08:15 gen_r.py
-rw-r--r-- 1 ubuntu ubuntu   17691 Nov 20 07:59 G_set.epd
-rw-r--r-- 1 ubuntu ubuntu     260 Nov 20 08:03 honesty_b_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:03 honesty_b_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     260 Nov 20 08:03 honesty_b_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:03 honesty_b_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     260 Nov 20 08:03 honesty_b_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:03 honesty_b_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     262 Nov 20 08:03 honesty_b_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:03 honesty_b_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    2890 Nov 20 08:17 honesty_b.py
-rw-r--r-- 1 ubuntu ubuntu     388 Nov 20 08:03 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu     391 Nov 20 09:12 HONESTY_PARTNER.txt
-rw-r--r-- 1 ubuntu ubuntu     260 Nov 20 08:17 honesty_p_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:17 honesty_p_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     260 Nov 20 08:17 honesty_p_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:17 honesty_p_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     260 Nov 20 08:17 honesty_p_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:17 honesty_p_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     262 Nov 20 08:17 honesty_p_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:17 honesty_p_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     388 Nov 20 08:17 HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu    9394 Nov 20 08:16 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu     467 Nov 20 08:31 match_og_elo.txt
-rw-r--r-- 1 ubuntu ubuntu     482 Nov 20 08:29 match_og.log
-rw-r--r-- 1 ubuntu ubuntu 4621132 Nov 20 08:29 match_og.pgn
-rw-r--r-- 1 ubuntu ubuntu  151780 Nov 20 08:29 match_og.txt
-rw-r--r-- 1 ubuntu ubuntu    4000 Nov 20 08:23 match_smoke_options.txt
-rw-r--r-- 1 ubuntu ubuntu  112871 Nov 20 08:14 O_d12_B.meta
-rw-r--r-- 1 ubuntu ubuntu  476051 Nov 20 08:14 O_d12_B.raw.txt
-rw-r--r-- 1 ubuntu ubuntu   15470 Nov 20 08:14 O_d12_B.tsv
-rw-r--r-- 1 ubuntu ubuntu  112905 Nov 20 08:17 O_d12_P_off.meta
-rw-r--r-- 1 ubuntu ubuntu  476080 Nov 20 08:17 O_d12_P_off.raw.txt
-rw-r--r-- 1 ubuntu ubuntu   15470 Nov 20 08:17 O_d12_P_off.tsv
-rw-r--r-- 1 ubuntu ubuntu  112904 Nov 20 08:17 O_d12_P_on.meta
-rw-r--r-- 1 ubuntu ubuntu  476502 Nov 20 08:17 O_d12_P_on.raw.txt
-rw-r--r-- 1 ubuntu ubuntu   15471 Nov 20 08:17 O_d12_P_on.tsv
-rw-r--r-- 1 ubuntu ubuntu   12861 Nov 20 07:59 O_first200.fens
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:19 OG_553.epd
-rw-r--r-- 1 ubuntu ubuntu     526 Nov 20 08:24 parse_match.py
-rw-r--r-- 1 ubuntu ubuntu    9487 Nov 20 09:11 partner_033_idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    2515 Nov 20 09:11 partner_033_O_on_claimed.tsv
-rw-r--r-- 1 ubuntu ubuntu     172 Nov 20 09:16 partner_apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu     119 Nov 20 09:12 partner_compare_off.txt
-rw-r--r-- 1 ubuntu ubuntu      67 Nov 20 09:12 partner_compare_on.txt
-rw-r--r-- 1 ubuntu ubuntu     503 Nov 20 09:12 partner_compare_on_vs_B.txt
-rw-r--r-- 1 ubuntu ubuntu     263 Nov 20 09:12 partner_h_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:12 partner_h_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     263 Nov 20 09:12 partner_h_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:12 partner_h_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     263 Nov 20 09:12 partner_h_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 09:12 partner_h_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     265 Nov 20 09:12 partner_h_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 09:12 partner_h_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     458 Nov 20 09:15 partner_match_elo.txt
-rw-r--r-- 1 ubuntu ubuntu     483 Nov 20 09:15 partner_match.log
-rw-r--r-- 1 ubuntu ubuntu 1927126 Nov 20 09:15 partner_match.pgn
-rw-r--r-- 1 ubuntu ubuntu   78048 Nov 20 09:15 partner_match.txt
-rw-r--r-- 1 ubuntu ubuntu  112908 Nov 20 09:12 partner_O_off.meta
-rw-r--r-- 1 ubuntu ubuntu  476076 Nov 20 09:12 partner_O_off.raw.txt
-rw-r--r-- 1 ubuntu ubuntu   15470 Nov 20 09:12 partner_O_off.tsv
-rw-r--r-- 1 ubuntu ubuntu  112907 Nov 20 09:12 partner_O_on.meta
-rw-r--r-- 1 ubuntu ubuntu  476277 Nov 20 09:12 partner_O_on.raw.txt
-rw-r--r-- 1 ubuntu ubuntu   15464 Nov 20 09:12 partner_O_on.tsv
-rw-r--r-- 1 ubuntu ubuntu    3600 Nov 20 09:17 paste_evidence.py
-rw-r--r-- 1 ubuntu ubuntu     492 Nov 20 08:16 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu     165 Nov 20 08:17 P_SUMS.txt
-rw-r--r-- 1 ubuntu ubuntu   19235 Nov 20 08:16 R_300.epd
-rw-r--r-- 1 ubuntu ubuntu   12324 Nov 20 09:18 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu     188 Nov 20 09:18 RESULT.txt
-rwxr-xr-x 1 ubuntu ubuntu    1229 Nov 20 08:22 run_match.sh
-rw-r--r-- 1 ubuntu ubuntu     433 Nov 20 08:22 scratch_asan.meta
-rw-r--r-- 1 ubuntu ubuntu    8339 Nov 20 08:22 scratch_asan.raw.txt
-rw-r--r-- 1 ubuntu ubuntu      32 Nov 20 08:22 scratch_fen.epd
-rw-r--r-- 1 ubuntu ubuntu     993 Nov 20 08:22 scratch_insertion.txt
-rw-r--r-- 1 ubuntu ubuntu    7608 Nov 20 08:18 search_set.py
-rw-r--r-- 1 ubuntu ubuntu      79 Nov 20 07:55 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu     220 Nov 20 09:17 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu     769 Nov 20 08:15 sum_tsv.py
-rw-r--r-- 1 ubuntu ubuntu     877 Nov 20 08:19 uci_dump.py
-rw-r--r-- 1 ubuntu ubuntu     188 Nov 20 08:19 uci_p.meta
-rw-r--r-- 1 ubuntu ubuntu    5038 Nov 20 08:19 uci_p.txt
```
