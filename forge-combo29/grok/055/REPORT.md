# Seat 055, idea 5, S37

Idea S37, option IdeaS37. Off the PV and not in check, if the parent already searched this move at least one ply reduced and the mover's corrected eval fell by at least IdeaS37_Margin, this node is searched one ply shallower.
IdeaS37 is a check option, default false. IdeaS37_Margin is a spin option, default 100 (one pawn), range 0 to 1000.
A hash entry already as deep as the current depth blocks the shave. The paired rule that searches one ply deeper when there is no worsening and three plies were withheld is not implemented.

EXISTS: no. HindsightDepth in forge-combo29/src/search.cpp is a different option, default false. It shaves and it also deepens. The default search does not shave. The one ply added when a node is not improving is on every node, including the PV, and it changes the child's reduction rather than this node's depth.

Honesty, from make_tables.py (HONESTY_B and HONESTY_P): bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, go perft 5 nodes 4865609, on exe B and on exe P with no setoption. Exe B also reproduced O depth 12 sum 9500069 (first three positions 41311, 24872, 28574) and G depth 12 sum 18466239.

The block TABLES is the stdout of `python3 make_tables.py`. It reads the raw files.

## Proofs

(1) Honesty on exe P with no setoption: HONESTY_P PASS, the four node counts above.
(2) S14 and IdeaS37 false: O depth 12 and G depth 12 match exe B on every position (node_diff 0, move_diff 0). Sums 9500069 and 18466239.
(3) S14 and IdeaS37 true: O depth 12 sum 9856085. 200 of 200 positions differ in nodes from exe B. 43 best moves differ. The code runs.
(4) `uci` lists `option name IdeaS37 type check default false` and `option name IdeaS37_Margin type spin default 100 min 0 max 1000`.
(5) AddressSanitizer + UndefinedBehaviorSanitizer build, IdeaS37 true, first 100 of G at depth 10: sanitizer_lines 0, stderr empty, `nm -C | grep -c __asan_` = 35. The same runner on a scratch copy with one deliberate read past a one-int heap array, on the FEN `4k3/8/8/8/8/8/8/4K3 w - - 0 1`, reported `runtime error: load of address 0x5020000000b4 with insufficient space for an object of type 'int'`.

`git apply --check` of idea.patch.txt on a fresh worktree of 6b98f2170a3210e71beed04bbd2553972c253ed7 printed APPLY_CHECK_OK.

## Match

s37on versus s37off, both S14, Threads 1, Hash 16, 20000 nodes, openings O then G, both colours, concurrency 3. 1106 games in the PGN. Elo -3.46 +/- 10.17. Wins 331, losses 342, draws 433. No unknown-option line.

The prediction file said the O sum would be 8600000 and would be wrong outside 6500000..9450000. The measured sum is 9856085, so that prediction is wrong: the tree grew. The predicted Elo was +6, wrong outside -25..+35. -3.46 is inside that range. The point is not below -20, and the interval is not entirely below 0, so the match did not trigger another pass over the code.

## Partner

Partner is seat 105 (idea 5, the next seat after 055 that has a branch). Commit e76c7704be458d8524e00a5ee6d9742a55d8e737. Verdict: CONFIRMS.

Their patch applies (`PARTNER_APPLY_CHECK_OK`). Honesty matches the four known node counts, which is what their HONESTY_P.txt claims. Switch false matches exe B's O depth-12 rows, 0 of 200, which is what their compare_O_off.txt claims. Switch true matches their O_P_on.rows on all 200 positions, and those 200 positions all differ from exe B, which is what their compare_O_on.txt claims. Their margin default is 40, reproduced by the uci line. A separate 600-game match of their switch on my 300 R openings (seed 5501) scored Elo -15.06 +/- 9.63. That match is mine; they did not claim it.

## Suspicions, not proven

The on-tree grew (9856085 versus 9500069) because a shallower reduced search fails low and the re-search costs more than the shave saves. I did not count shaves against re-searches.
Seat 105's -15 Elo on the R match may be their two-ply margin of 40 firing too often. I did not separate that from ordinary noise.

## What I did NOT do

I did not try IdeaS37_Margin at any value other than the default 100.
I did not run the sanitizer build on all 353 positions of G, only the first 100 at depth 10.
I did not turn IdeaS37 and HindsightDepth on together.
I did not replay seat 105's 1106-game book. I played 600 games on my R openings.
No FABLE_TO_grok file existed at STEP 1 or at minute 60. I did not fetch the handoff again after that.

## What I am NOT sure about

S37's "two corrected static evals" can be read as the mover's loss (what I built, the comparison already used by HindsightDepth) or as this side's eval against the eval two plies ago (what seat 105 built). I am not sure which reading the one-line index wanted. Both leave the deepen rule off, and both change the search.
The match interval -3.46 +/- 10.17 includes zero. I am not sure the small loss is anything but noise.
The scratch bug was reported by UndefinedBehaviorSanitizer (`runtime error: load ... insufficient space`) and the process stopped there. I did not also capture an AddressSanitizer heap-buffer-overflow banner. The exe does contain __asan_ symbols (35).

times: see stamps.txt

## TABLES
HONESTY_B
bench11 nodes 312866 expected 312866 OK
bench13 nodes 862329 expected 862329 OK
bench16 nodes 3024920 expected 3024920 OK
perft5 nodes 4865609 expected 4865609 OK
HONESTY_B PASS
HONESTY_P
honesty_p_bench11.txt nodes 312866 expected 312866 OK
honesty_p_bench13.txt nodes 862329 expected 862329 OK
honesty_p_bench16.txt nodes 3024920 expected 3024920 OK
honesty_p_perft5.txt nodes 4865609 expected 4865609 OK
HONESTY_P PASS
BASELINE_SUMS
B_O_d12.txt sum	9500069 count	200
B_G_d12.txt sum	18466239 count	353
OFF_COMPARE
left B_O_d12.txt sum 9500069 count 200
right P_off_O_d12.txt sum 9500069 count 200
positions 200 node_diff 0 move_diff 0 missing 0
left B_G_d12.txt sum 18466239 count 353
right P_off_G_d12.txt sum 18466239 count 353
positions 353 node_diff 0 move_diff 0 missing 0
ON_COMPARE
left B_O_d12.txt sum 9500069 count 200
right P_on_O_d12.txt sum 9856085 count 200
positions 200 node_diff 200 move_diff 43 missing 0
UCI_OPTIONS
option name IdeaS37 type check default false
option name IdeaS37_Margin type spin default 100 min 0 max 1000
ASAN_META_TAIL
exe /tmp/forge-asan/forge
sha256 4fddcfb8774a3e09d71ec600a8823efb8dddf8b157850d69473f97bda745c89b
id name Chess Engine Forge 6.4.24 candidate
setoption name IdeaS37 value true
sanitizer_lines 0
fail 
35
asan_positions count	100
asan_stderr_bytes 0
SCRATCH_SANITIZER_FIRST
/tmp/scratch-src/src/uci.cpp:46:26: runtime error: load of address 0x5020000000b4 with insufficient space for an object of type 'int'
MATCH
--------------------------------------------------
Results of s37on vs s37off (20000 nodes, 1t, 16MB, OG.epd):
Elo: -3.46 +/- 10.17, nElo: -6.96 +/- 20.48
LOS: 25.27 %, DrawRatio: 62.57 %, PairsRatio: 0.88
Games: 1106, Wins: 331, Losses: 342, Draws: 433, Points: 547.5 (49.50 %)
Ptnml(0-2): [10, 100, 346, 85, 12], WL/DD Ratio: 1.79
--------------------------------------------------
Finished match
Total Time: 00:05:59 (hours:minutes:seconds)

fastchess_exit 0
end 2026-11-20T08:19:03Z
pgn_events 1106
PARTNER
commit e76c7704be458d8524e00a5ee6d9742a55d8e737
PARTNER_APPLY_CHECK_OK
partner_honesty_bench11.txt nodes 312866 expected 312866 OK
partner_honesty_bench13.txt nodes 862329 expected 862329 OK
partner_honesty_bench16.txt nodes 3024920 expected 3024920 OK
partner_honesty_perft5.txt nodes 4865609 expected 4865609 OK
PARTNER_HONESTY PASS
left B_O_d12.txt sum 9500069 count 200
right partner_off_O.txt sum 9500069 count 200
positions 200 node_diff 0 move_diff 0 missing 0
mine 200 theirs 200 node_diff 0 length_gap 0
left B_O_d12.txt sum 9500069 count 200
right partner_on_O.txt sum 9295011 count 200
positions 200 node_diff 200 move_diff 34 missing 0
partner_uci
option name IdeaS37 type check default false
option name IdeaS37_Margin type spin default 40 min 0 max 500
--------------------------------------------------
Results of s37on vs s37off (20000 nodes, 1t, 16MB, R.epd):
Elo: -15.06 +/- 9.63, nElo: -43.54 +/- 27.80
LOS: 0.11 %, DrawRatio: 84.33 %, PairsRatio: 0.38
Games: 600, Wins: 257, Losses: 283, Draws: 60, Points: 287.0 (47.83 %)
Ptnml(0-2): [7, 27, 253, 11, 2], WL/DD Ratio: 22.00
--------------------------------------------------
Finished match
Total Time: 00:02:31 (hours:minutes:seconds)

fastchess_exit 0
end 2026-11-20T09:14:07Z
partner_pgn_events 600
partner_unknown_option 0
PREDICTION
O depth 12 sum, IdeaS37 true: 8600000
wrong if sum < 6500000 or sum > 9450000
test match Elo (on minus off): +6
wrong if elo < -25 or elo > +35
ON_SUM sum	9856085
STEP_TABLE
step	status	evidence	result
1 seat	done	SEAT.txt	seat file
2 honesty B	done	HONESTY_B.txt	HONESTY_B
2 O and G sums	done	B_O_d12.txt B_G_d12.txt	BASELINE_SUMS
3 patch	done	idea.patch.txt apply_check.txt	APPLY_CHECK_OK
3 proof 1 honesty P	done	HONESTY_P.txt	HONESTY_P
3 proof 2 switch off	done	cmp_off_O.txt cmp_off_G.txt	OFF_COMPARE
3 proof 3 switch on	done	cmp_on_O.txt	ON_COMPARE
3 proof 4 uci	done	uci_p.txt	UCI_OPTIONS
3 proof 5 sanitizer	done	P_asan_G100.meta scratch_asan.stderr	ASAN_META_TAIL
3 match	done	match_og.log match_og.pgn	MATCH
4 partner	done	partner_cmp_off.txt partner_cmp_on.txt partner_r.log	PARTNER
5 report	done	REPORT.md RESULT.txt	this report
## git status --short
 M forge-combo29/grok/055/run_match_r.sh
 M forge-combo29/grok/055/stamps.txt
?? forge-combo29/grok/055/REPORT.md
?? forge-combo29/grok/055/RESULT.txt
?? forge-combo29/grok/055/make_tables.py
?? forge-combo29/grok/055/partner105_HONESTY_P.txt
?? forge-combo29/grok/055/partner105_O_P_on.rows
?? forge-combo29/grok/055/partner105_commit.txt
?? forge-combo29/grok/055/partner105_compare_O_off.txt
?? forge-combo29/grok/055/partner105_compare_O_on.txt
?? forge-combo29/grok/055/partner105_idea.patch.txt
?? forge-combo29/grok/055/partner105_match_og_elo.txt
?? forge-combo29/grok/055/partner_apply_check.txt
?? forge-combo29/grok/055/partner_cmp_off.txt
?? forge-combo29/grok/055/partner_cmp_on.txt
?? forge-combo29/grok/055/partner_cmp_on_vs_B.txt
?? forge-combo29/grok/055/partner_honesty.meta
?? forge-combo29/grok/055/partner_honesty.txt
?? forge-combo29/grok/055/partner_honesty_bench11.txt
?? forge-combo29/grok/055/partner_honesty_bench13.txt
?? forge-combo29/grok/055/partner_honesty_bench16.txt
?? forge-combo29/grok/055/partner_honesty_perft5.txt
?? forge-combo29/grok/055/partner_off_O.meta
?? forge-combo29/grok/055/partner_off_O.stderr
?? forge-combo29/grok/055/partner_off_O.txt
?? forge-combo29/grok/055/partner_on_O.meta
?? forge-combo29/grok/055/partner_on_O.stderr
?? forge-combo29/grok/055/partner_on_O.txt
?? forge-combo29/grok/055/partner_r.log
?? forge-combo29/grok/055/partner_r.pgn
?? forge-combo29/grok/055/partner_r_config.json
?? forge-combo29/grok/055/partner_uci.txt
?? forge-combo29/grok/055/tables.txt
## ls -la
total 7104
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 09:16 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:54 ..
-rw-r--r-- 1 ubuntu ubuntu      15 Nov 20 08:12 apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu     812 Nov 20 08:06 B_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:06 B_G_d12.stderr
-rw-r--r-- 1 ubuntu ubuntu   22911 Nov 20 08:06 B_G_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     812 Nov 20 08:06 B_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:06 B_O_d12.stderr
-rw-r--r-- 1 ubuntu ubuntu   15777 Nov 20 08:06 B_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     133 Nov 20 08:08 cmp_off_G.txt
-rw-r--r-- 1 ubuntu ubuntu     131 Nov 20 08:08 cmp_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu     133 Nov 20 08:08 cmp_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu    1029 Nov 20 08:56 compare_partner_rows.py
-rwxr-xr-x 1 ubuntu ubuntu    1243 Nov 20 08:08 compare_rows.py
-rw-r--r-- 1 ubuntu ubuntu    6931 Nov 20 09:15 config.json
-rw-r--r-- 1 ubuntu ubuntu    1499 Nov 20 08:12 DECISION.txt
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 07:58 honesty_b_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 07:58 honesty_b_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 07:58 honesty_b_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     181 Nov 20 07:58 honesty_b.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 07:58 honesty_b_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     178 Nov 20 08:02 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:07 honesty_p_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:07 honesty_p_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:07 honesty_p_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     181 Nov 20 08:07 honesty_p.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:07 honesty_p_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     234 Nov 20 08:07 HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu    7816 Nov 20 08:07 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu     876 Nov 20 08:02 make_honesty.py
-rwxr-xr-x 1 ubuntu ubuntu     961 Nov 20 08:11 make_r.py
-rw-r--r-- 1 ubuntu ubuntu    4004 Nov 20 09:16 make_tables.py
-rw-r--r-- 1 ubuntu ubuntu  119475 Nov 20 08:19 match_og.log
-rw-r--r-- 1 ubuntu ubuntu 4623787 Nov 20 08:19 match_og.pgn
-rw-r--r-- 1 ubuntu ubuntu    6338 Nov 20 08:11 measure.py
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:13 OG.epd
-rw-r--r-- 1 ubuntu ubuntu      41 Nov 20 09:10 partner105_commit.txt
-rw-r--r-- 1 ubuntu ubuntu     139 Nov 20 09:10 partner105_compare_O_off.txt
-rw-r--r-- 1 ubuntu ubuntu     168 Nov 20 09:10 partner105_compare_O_on.txt
-rw-r--r-- 1 ubuntu ubuntu     191 Nov 20 09:10 partner105_HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu    7610 Nov 20 09:10 partner105_idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu     357 Nov 20 09:10 partner105_match_og_elo.txt
-rw-r--r-- 1 ubuntu ubuntu    4777 Nov 20 09:10 partner105_O_P_on.rows
-rw-r--r-- 1 ubuntu ubuntu      23 Nov 20 09:10 partner_apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu     133 Nov 20 09:11 partner_cmp_off.txt
-rw-r--r-- 1 ubuntu ubuntu      45 Nov 20 09:11 partner_cmp_on.txt
-rw-r--r-- 1 ubuntu ubuntu     135 Nov 20 09:11 partner_cmp_on_vs_B.txt
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:11 partner_honesty_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:11 partner_honesty_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 09:11 partner_honesty_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     179 Nov 20 09:11 partner_honesty.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 09:11 partner_honesty_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     264 Nov 20 09:11 partner_honesty.txt
-rw-r--r-- 1 ubuntu ubuntu     845 Nov 20 09:11 partner_off_O.meta
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 09:11 partner_off_O.stderr
-rw-r--r-- 1 ubuntu ubuntu   15777 Nov 20 09:11 partner_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu     844 Nov 20 09:11 partner_on_O.meta
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 09:11 partner_on_O.stderr
-rw-r--r-- 1 ubuntu ubuntu   15775 Nov 20 09:11 partner_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu    6922 Nov 20 09:15 partner_r_config.json
-rw-r--r-- 1 ubuntu ubuntu   60626 Nov 20 09:14 partner_r.log
-rw-r--r-- 1 ubuntu ubuntu 1940686 Nov 20 09:14 partner_r.pgn
-rw-r--r-- 1 ubuntu ubuntu     107 Nov 20 09:11 partner_uci.txt
-rw-r--r-- 1 ubuntu ubuntu     823 Nov 20 08:11 P_asan_G100.meta
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:10 P_asan_G100.stderr
-rw-r--r-- 1 ubuntu ubuntu    6402 Nov 20 08:10 P_asan_G100.txt
-rw-r--r-- 1 ubuntu ubuntu       3 Nov 20 08:10 P_asan_nm.txt
-rw-r--r-- 1 ubuntu ubuntu     847 Nov 20 08:08 P_off_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:08 P_off_G_d12.stderr
-rw-r--r-- 1 ubuntu ubuntu   22911 Nov 20 08:08 P_off_G_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     847 Nov 20 08:07 P_off_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:07 P_off_O_d12.stderr
-rw-r--r-- 1 ubuntu ubuntu   15777 Nov 20 08:07 P_off_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     846 Nov 20 08:08 P_on_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:08 P_on_O_d12.stderr
-rw-r--r-- 1 ubuntu ubuntu   15775 Nov 20 08:08 P_on_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     144 Nov 20 08:06 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu   19125 Nov 20 08:11 R.epd
-rw-r--r-- 1 ubuntu ubuntu   10859 Nov 20 09:16 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu     184 Nov 20 09:16 RESULT.txt
-rwxr-xr-x 1 ubuntu ubuntu     914 Nov 20 08:03 run_depth.sh
-rwxr-xr-x 1 ubuntu ubuntu    1339 Nov 20 08:21 run_match_r.sh
-rwxr-xr-x 1 ubuntu ubuntu    1531 Nov 20 08:12 run_match.sh
-rw-r--r-- 1 ubuntu ubuntu     822 Nov 20 08:11 scratch_asan.meta
-rw-r--r-- 1 ubuntu ubuntu    1065 Nov 20 08:11 scratch_asan.stderr
-rw-r--r-- 1 ubuntu ubuntu      30 Nov 20 08:11 scratch_fen.epd
-rw-r--r-- 1 ubuntu ubuntu      77 Nov 20 07:54 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu     215 Nov 20 09:16 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu     837 Nov 20 08:21 summarize_match.py
-rw-r--r-- 1 ubuntu ubuntu    4143 Nov 20 09:16 tables.txt
-rw-r--r-- 1 ubuntu ubuntu    5042 Nov 20 08:08 uci_p.txt
