IdeaK9 is the null-move reduction growing with (eval - beta) / a divisor.
The plain engine already adds min((eval - beta) / NullMoveEvalDivisor, 3), and NullMoveEvalDivisor is already a spin.
I added check IdeaK9, default false, which keeps the literal cap 3, and spin IdeaK9_Cap, default 3, range 0 to 6, used only when the check is true.

EXISTS: forge-combo29/src/search.cpp:1701
NullMoveEvalDivisor is already advertised at forge-combo29/src/search.cpp:120, default 200, range 50 to 1000. The cap 3 on that same line was the remaining literal, so it became IdeaK9_Cap.

Honesty numbers are the PASS blocks below. bench 11 is 312866, bench 13 is 862329, bench 16 is 3024920, perft 5 is 4865609, on exe B and on exe P with no setoption.

The table and the proof numbers are the output of print_evidence.py, which reads the raw files:

HONESTY_B
date=2026-11-20T08:01:58Z
exe=/agent/repos/base/forge-combo29/build-release/forge
sha256=e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83
id_name=Chess Engine Forge 6.4.24 candidate
bench11_nodes=312866 expected=312866
bench13_nodes=862329 expected=862329
bench16_nodes=3024920 expected=3024920
perft5_nodes=4865609 expected=4865609
result=PASS

HONESTY_P
date=2026-11-20T08:06:33Z
exe=/agent/repos/work/forge-combo29/build-release/forge
sha256=b02050b4999ee8449f2b54472db6af1e768fbcecba3c6b758184946866526334
id_name=Chess Engine Forge 6.4.24 candidate
bench11_nodes=312866 expected=312866
bench13_nodes=862329 expected=862329
bench16_nodes=3024920 expected=3024920
perft5_nodes=4865609 expected=4865609
result=PASS

PROOF_O
o_b positions=200 missing=0 sum=9500069 file=forge-combo29/grok/098/o_b_d12.raw.txt
o_b first3=41311 24872 28574
o_p_off positions=200 missing=0 sum=9500069 file=forge-combo29/grok/098/o_p_off_d12.raw.txt
o_p_off first3=41311 24872 28574
o_p_on positions=200 missing=0 sum=9500069 file=forge-combo29/grok/098/o_p_on_d12.raw.txt
o_p_on first3=41311 24872 28574
o_p_cap0 positions=200 missing=0 sum=9518441 file=forge-combo29/grok/098/o_p_cap0_d12.raw.txt
o_p_cap0 first3=45304 24884 28574
diff o_p_off vs o_b differ=0 of 200
diff o_p_on vs o_b differ=0 of 200
diff o_p_cap0 index=0 o_b=41311 o_p_cap0=45304
diff o_p_cap0 index=1 o_b=24872 o_p_cap0=24884
diff o_p_cap0 index=3 o_b=27838 o_p_cap0=27841
diff o_p_cap0 index=4 o_b=18020 o_p_cap0=18022
diff o_p_cap0 index=5 o_b=43043 o_p_cap0=43064
diff o_p_cap0 vs o_b differ=172 of 200

PROOF_G
g_b positions=353 missing=0 sum=18466239 file=forge-combo29/grok/098/g_b_d12.raw.txt
g_b first3=37203 70845 144383
g_p_off positions=353 missing=0 sum=18466239 file=forge-combo29/grok/098/g_p_off_d12.raw.txt
g_p_off first3=37203 70845 144383
diff g_p_off vs g_b differ=0 of 353

UCI_NEW_OPTIONS
24:option name IdeaK9 type check default false
42:option name IdeaK9_Cap type spin default 3 min 0 max 6

APPLY_CHECK
apply_check_exit=0
date=2026-11-20T08:12:24Z
command=git -C /agent/repos/base apply --check /agent/repos/dwqww/forge-combo29/grok/098/idea.patch.txt
base=6b98f2170a3210e71beed04bbd2553972c253ed7

ASAN_NM
35
sha256=2f65684e91342144fc3dcabb58e22f35710e4e82e11d6785646171c47d66a7d4
exe=/agent/repos/work/forge-combo29/build-asan/forge

ASAN_CLEAN_LINES
0

ASAN_SCRATCH
runner_exit=2
107:/tmp/scratch-forge/src/uci.cpp:46:26: runtime error: load of address 0x5020000000d0 with insufficient space for an object of type 'int'
112:==6395==ERROR: AddressSanitizer: heap-buffer-overflow on address 0x5020000000d0 at pc 0x5568a2e25377 bp 0x7ffca2589ef0 sp 0x7ffca2589ee0
129:SUMMARY: AddressSanitizer: heap-buffer-overflow (/tmp/scratch-forge/build-asan/forge+0x62f376) (BuildId: f6a2ae021a227aa1645c15a8d359ff0c2ac606a7) in (anonymous namespace)::apply_position(forge::Board&, std::__cxx11::basic_istringstream<char, std::char_traits<char>, std::allocator<char> >&)

MATCH_OG
Results of on vs off (20000 nodes, 1t, 16MB, openings_og.epd):
Elo: -0.00 +/- 0.00, nElo: -nan +/- -nan
LOS: -nan %, DrawRatio: 100.00 %, PairsRatio: -nan
Games: 1106, Wins: 336, Losses: 336, Draws: 434, Points: 553.0 (50.00 %)
Ptnml(0-2): [0, 0, 553, 0, 0], WL/DD Ratio: 1.55
--------------------------------------------------
Finished match

MATCH_R
on vs off (20000 nodes, 1t, 16MB, R.fens):
Elo: -0.00 +/- 0.00, nElo: -nan +/- -nan
LOS: -nan %, DrawRatio: 100.00 %, PairsRatio: -nan
Games: 600, Wins: 261, Losses: 261, Draws: 78, Points: 300.0 (50.00 %)
Ptnml(0-2): [0, 0, 300, 0, 0], WL/DD Ratio: 6.69
--------------------------------------------------
Finished match
Total Time: 00:03:10 (hours:minutes:seconds)

PARTNER_FETCH
2026-11-20T08:21:50Z fetch grok-048 no idea.patch.txt
2026-11-20T08:31:19Z fetch grok-048 after wait
2026-11-20T08:31:27Z grok-048 still no idea.patch.txt; second match of own patch

STEP_TABLE
step | status | evidence | result
1 seat | done | SEAT.txt | seat 098, idea 48, model Grok 4.7, 2026-11-20T07:56:02Z, token 53412549824471
2 honesty B | done | HONESTY_B.txt | PASS
3 prediction | done | prediction.txt | file present
3 patch | done | apply_check.txt | 0
3 honesty P | done | HONESTY_P.txt | PASS
3 off O | done | proof_o.txt | diff o_p_off vs o_b differ=0 of 200
3 off G | done | proof_g.txt | diff g_p_off vs g_b differ=0 of 353
3 on default | done | proof_o.txt | diff o_p_on vs o_b differ=0 of 200
3 cap 0 | done | proof_o.txt | diff o_p_cap0 vs o_b differ=172 of 200
3 uci | done | uci_p_new_options.txt | 24:option name IdeaK9 type check default false | 42:option name IdeaK9_Cap type spin default 3 min 0 max 6
3 asan nm | done | asan_nm_count.txt | 35
3 asan clean | done | asan_g100_sanitizer_lines.txt | 0
3 asan scratch | done | asan_scratch_result.txt | runner_exit=2
3 match | done | match_og_result.txt | Elo: -0.00 +/- 0.00, nElo: -nan +/- -nan
4 partner patch | not done | partner_fetch.txt | 2026-11-20T08:21:50Z fetch grok-048 no idea.patch.txt | 2026-11-20T08:31:19Z fetch grok-048 after wait | 2026-11-20T08:31:27Z grok-048 still no idea.patch.txt; second match of own patch
4 second match | done | match_r.txt | Elo: -0.00 +/- 0.00, nElo: -nan +/- -nan

Proofs:
(1) Honesty on exe P with no setoption: PASS, the four known node counts.
(2) S14 and IdeaK9 false: O depth 12 differs in 0 of 200 and the sum is 9500069. G depth 12 differs in 0 of 353 and the sum is 18466239. Exe B's own sums are those same known sums, first three of O 41311 24872 28574.
(3) S14 and IdeaK9 true with IdeaK9_Cap 3: O depth 12 differs in 0 of 200, sum 9500069. The default cap is today's literal 3, so the reduction integer does not change. That is why the count is 0. IdeaK9 true with IdeaK9_Cap 0, which is not the default, differs in 172 of 200, sum 9518441. The option is read.
(4) The uci answer lists `option name IdeaK9 type check default false` and `option name IdeaK9_Cap type spin default 3 min 0 max 6`.
(5) The sanitizer exe has 35 `__asan_` symbols. The first 100 positions of G at depth 10 with IdeaK9 true produced 0 sanitizer lines. A scratch copy with one heap read past the end of a 4-int array, only on the FEN `4k3/8/8/8/8/8/8/4K3 w - - 0 1`, built the same way and run through harness_depth.py, printed AddressSanitizer heap-buffer-overflow. The runner exited 2 because the engine died on that line.

Match: exe P with IdeaK9 true and IdeaK9_Cap 3 against exe P with IdeaK9 false, S14, Threads 1, Hash 16, 20000 nodes, openings O then G, both colours, 1106 games, concurrency 3. Elo -0.00 +/- 0.00. Wins 336, losses 336, draws 434. Pentanomial [0, 0, 553, 0, 0]. The prediction file, committed before these searches, said the O sum would be 9500069 and the Elo 0, and would be wrong if the sum differed or the Elo interval excluded 0. The sum matched. The interval is 0 +/- 0.

Partner: seat 048. Fetched at 2026-11-20T08:21:50Z and again at 2026-11-20T08:31:19Z. No idea.patch.txt. Their DECISION.txt says the divisor is already an option and they are not adding a switch. Verdict: not done. Fallback: a second match of this patch on 300 R openings, both colours, 600 games. Elo -0.00 +/- 0.00. Wins 261, losses 261, draws 78. R was built by make_r_positions.py with seed 9801.

suspicions, not proven: IdeaK9_Cap 0 changes the node count on 172 of 200 openings. I did not play a match at cap 0, so I do not know its Elo.

What I did NOT do: I did not add another divisor. I did not play any cap other than 3 in a match. I did not review a patch from 048, because there was none. I did not wait until minute 75; the 1106-game match had already finished and the partner branch still had no patch. The minute-60 handoff read was early, at 2026-11-20T08:35:36Z, and there was no FABLE_TO_grok file. No STOP line.

What I am NOT sure about: fastchess prints nElo nan, LOS nan and DrawRatio 100% when every opening pair sits in the middle pentanomial bin. The Games line shows real wins, losses and draws, with equal wins and losses. I read the Elo as 0 from that score. I am also not sure the cap needed to become an option, because the idea's divisor was already NullMoveEvalDivisor. I made the remaining literal optional and left its default at 3 so the default search does not change.

times: see stamps.txt

git apply --check of idea.patch.txt on the base commit 6b98f2170a3210e71beed04bbd2553972c253ed7 exited 0. See apply_check.txt.

git status --short
 M forge-combo29/grok/098/partner_fetch.txt
 M forge-combo29/grok/098/stamps.txt
?? config.json
?? forge-combo29/grok/098/REPORT.md
?? forge-combo29/grok/098/RESULT.txt
?? forge-combo29/grok/098/evidence_block.txt
?? forge-combo29/grok/098/match_r.meta
?? forge-combo29/grok/098/match_r.pgn
?? forge-combo29/grok/098/match_r.txt
?? forge-combo29/grok/098/print_evidence.py

ls -la
total 8044
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 08:37 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:56 ..
-rw-r--r-- 1 ubuntu ubuntu     195 Nov 20 08:12 apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu    1011 Nov 20 08:11 asan_g100.meta
-rw-r--r-- 1 ubuntu ubuntu  133436 Nov 20 08:11 asan_g100.raw.txt
-rw-r--r-- 1 ubuntu ubuntu       2 Nov 20 08:11 asan_g100_sanitizer_lines.txt
-rw-r--r-- 1 ubuntu ubuntu     128 Nov 20 08:11 asan_nm_count.txt
-rw-r--r-- 1 ubuntu ubuntu      30 Nov 20 08:12 asan_scratch.fen
-rw-r--r-- 1 ubuntu ubuntu       3 Nov 20 08:12 asan_scratch_nm_count.txt
-rw-r--r-- 1 ubuntu ubuntu    9267 Nov 20 08:12 asan_scratch.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     591 Nov 20 08:12 asan_scratch_result.txt
-rw-r--r-- 1 ubuntu ubuntu    5190 Nov 20 08:36 evidence_block.txt
-rw-r--r-- 1 ubuntu ubuntu    5009 Nov 20 08:11 g100.epd
-rw-r--r-- 1 ubuntu ubuntu     937 Nov 20 08:08 g_b_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  553053 Nov 20 08:08 g_b_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     975 Nov 20 08:09 g_p_off_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  555783 Nov 20 08:09 g_p_off_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    5582 Nov 20 08:08 harness_depth.py
-rw-r--r-- 1 ubuntu ubuntu     236 Nov 20 08:01 honesty_b_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:01 honesty_b_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     236 Nov 20 08:01 honesty_b_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:01 honesty_b_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     236 Nov 20 08:01 honesty_b_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:01 honesty_b_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     238 Nov 20 08:01 honesty_b_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:01 honesty_b_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     956 Nov 20 08:01 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu    4933 Nov 20 08:01 honesty_b_uci.txt
-rw-r--r-- 1 ubuntu ubuntu     236 Nov 20 08:06 honesty_p_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:06 honesty_p_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     236 Nov 20 08:06 honesty_p_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:06 honesty_p_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     236 Nov 20 08:06 honesty_p_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:06 honesty_p_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     238 Nov 20 08:06 honesty_p_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:06 honesty_p_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     361 Nov 20 08:06 HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu    5032 Nov 20 08:06 honesty_p_uci.txt
-rw-r--r-- 1 ubuntu ubuntu    5123 Nov 20 08:03 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    1596 Nov 20 08:10 make_r_positions.py
-rw-r--r-- 1 ubuntu ubuntu     389 Nov 20 08:19 match_og.meta
-rw-r--r-- 1 ubuntu ubuntu 3481284 Nov 20 08:19 match_og.pgn
-rw-r--r-- 1 ubuntu ubuntu     343 Nov 20 08:21 match_og_result.txt
-rw-r--r-- 1 ubuntu ubuntu  124724 Nov 20 08:19 match_og.txt
-rw-r--r-- 1 ubuntu ubuntu     418 Nov 20 08:34 match_r.meta
-rw-r--r-- 1 ubuntu ubuntu 1685576 Nov 20 08:34 match_r.pgn
-rw-r--r-- 1 ubuntu ubuntu   63331 Nov 20 08:34 match_r.txt
-rw-r--r-- 1 ubuntu ubuntu     941 Nov 20 08:08 o_b_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  307557 Nov 20 08:08 o_b_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    1013 Nov 20 08:09 o_p_cap0_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  310852 Nov 20 08:09 o_p_cap0_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:13 openings_og.epd
-rw-r--r-- 1 ubuntu ubuntu     979 Nov 20 08:08 o_p_off_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  309186 Nov 20 08:08 o_p_off_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    1011 Nov 20 08:09 o_p_on_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  310752 Nov 20 08:09 o_p_on_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     182 Nov 20 08:31 partner_fetch.txt
-rw-r--r-- 1 ubuntu ubuntu     947 Nov 20 08:03 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu    3118 Nov 20 08:36 print_evidence.py
-rw-r--r-- 1 ubuntu ubuntu     278 Nov 20 08:09 proof_g.txt
-rw-r--r-- 1 ubuntu ubuntu     833 Nov 20 08:09 proof_o.txt
-rw-r--r-- 1 ubuntu ubuntu     424 Nov 20 08:21 read_match_result.py
-rw-r--r-- 1 ubuntu ubuntu    9612 Nov 20 08:37 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu     219 Nov 20 08:37 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu   19444 Nov 20 08:14 R.fens
-rw-r--r-- 1 ubuntu ubuntu     129 Nov 20 08:14 R.fens.meta
-rw-r--r-- 1 ubuntu ubuntu    2119 Nov 20 08:12 run_asan_scratch.sh
-rw-r--r-- 1 ubuntu ubuntu     832 Nov 20 08:11 run_asan.sh
-rw-r--r-- 1 ubuntu ubuntu    2015 Nov 20 08:01 run_honesty_b.sh
-rw-r--r-- 1 ubuntu ubuntu    1610 Nov 20 08:06 run_honesty_p.sh
-rw-r--r-- 1 ubuntu ubuntu    1609 Nov 20 08:21 run_match_r.sh
-rw-r--r-- 1 ubuntu ubuntu    1739 Nov 20 08:12 run_match.sh
-rw-r--r-- 1 ubuntu ubuntu    1110 Nov 20 08:08 run_proofs.sh
-rw-r--r-- 1 ubuntu ubuntu     689 Nov 20 08:10 run_uci_options.sh
-rw-r--r-- 1 ubuntu ubuntu      78 Nov 20 07:56 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu     140 Nov 20 08:36 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu    1843 Nov 20 08:06 summarize_depth.py
-rw-r--r-- 1 ubuntu ubuntu     202 Nov 20 08:10 uci_p.meta
-rw-r--r-- 1 ubuntu ubuntu     105 Nov 20 08:10 uci_p_new_options.txt
-rw-r--r-- 1 ubuntu ubuntu    5032 Nov 20 08:10 uci_p.txt
