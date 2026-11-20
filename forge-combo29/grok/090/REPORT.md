IdeaK1 is hash probcut. Off the principal line, a hash lower bound at least beta+180, from a search at least depth-4 deep, at depth at least 5, returns beta+180.
The check option IdeaK1 defaults to false. The spins are IdeaK1_Margin 180, IdeaK1_DepthSlack 4, and IdeaK1_MinDepth 5.
The change is only in forge-combo29/grok/090/idea.patch.txt. git apply --check on a clean copy of 6b98f2170a3210e71beed04bbd2553972c253ed7 succeeded (apply_check.txt).

EXISTS: no. The capture ProbCut in search.cpp searches a capture. The ordinary hash cutoff returns a stored score only when the stored depth is at least the current depth. Neither of those is this cutoff.

Honesty, no setoption, exe B and exe P (HONESTY_B.txt and proofs_summary.py): bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, go perft 5 nodes 4865609.

| step | done / partly / not done | evidence file | result |
| --- | --- | --- | --- |
| 1 seat | done | SEAT.txt, stamps.txt | seat 090, idea 40, IdeaK1 |
| 2 builds and baseline | done | HONESTY_B.txt, BASELINE_BG.txt | honesty matches; O depth 12 sum 9500069 first3 41311 24872 28574; G depth 12 sum 18466239 |
| 3 idea | done | idea.patch.txt, PROOFS.txt, MATCH_OG.txt | off identical; on differs 200 of 200, sum 9457615; match elo -0.63 err 9.93 games 1106 |
| 4 partner 040 | done | partner_apply.txt, PARTNER_NODES.txt, MATCH_PARTNER_R.txt | CONFIRMS; their on rows reproduced 200 of 200; R match elo -2.90 err 8.56 games 600 |
| 5 report | done | REPORT.md, RESULT.txt | this file |

Proof (1), exe P, no setoption: bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609.

Proof (2), S14, IdeaK1 false. compare_rows.py: B_O_d12 vs P_off_O_d12 positions 200 same 200 differ 0 sum 9500069. B_G_d12 vs P_off_G_d12 positions 353 same 353 differ 0 sum 18466239.

Proof (3), S14, IdeaK1 true, margin 180, slack 4, min depth 5. B_O_d12 vs P_on_O_d12 positions 200 same 0 differ 200. Sum 9457615. The node column itself differs on all 200 positions.

Proof (4), uci_p.txt lists: option name IdeaK1 type check default false; option name IdeaK1_Margin type spin default 180 min 0 max 1000; option name IdeaK1_DepthSlack type spin default 4 min 0 max 16; option name IdeaK1_MinDepth type spin default 5 min 1 max 32.

Proof (5). asan_G100_d10.meta has nm_asan_count=35 and exe build-asan/forge. asan_G100_d10.err is empty (0 bytes) for the first 100 of G at depth 10 with the switch true. The same depth_harness.py on a scratch copy with one heap read past the end of a 4-int allocation, on the FEN in scratch_fen.fen, wrote asan_scratch.err. That file contains "AddressSanitizer: heap-buffer-overflow".

Match, exe P switch true versus exe P switch false, S14, Threads 1, Hash 16, 20000 nodes, openings O then G, both colours. match_summary.py on match_og.txt: elo -0.63 err 9.93 games 1106. The whole interval is not below 0, so the "below -20" look was not triggered. Finished games include threefold repetition and insufficient material; those are legal results.

Partner is seat 040 (same idea; 140 is past 120). Verdict: CONFIRMS. Their patch applied with git apply --check (partner_apply.txt). Their honesty numbers matched. Switch false matched exe B on all 200 O positions. Switch true matched their published O_d12_P_on.nodes on all 200 positions, sum 9339181 (PARTNER_NODES.txt). I then played their switch on 300 R openings, both colours: elo -2.90 err 8.56 games 600. That match is not their O+G match. They published O+G elo -10.37 +/- 10.77 over 1106 games; I did not replay it.

The minute-60 fetch of handoff/fable-opus-combo29-all-20261114 was at 2026-11-20T08:55:53Z, commit 8c5536863464d4af8c07b4788883463eb950ab1d. There was no forge-combo29/soak_all/FABLE_TO_grok_<N>.md. Nothing said STOP.

suspicions, not proven: the O-sum prediction (9200000, wrong outside 8600000..9450000) was wrong. The measured sum is 9457615, above 9450000. The cut is real and small. The Elo prediction (+5, wrong outside -35..+40) was not shown wrong. I am not claiming the margin 180 is the best value.

what I did NOT do: I did not re-search the partner's G set. I did not replay the partner's 1106-game match. I did not wait until minute 75; their idea.patch.txt and STEP 3 stamp were already on for-fable-and-opus/grok-040 when I fetched it (their stamp 2026-11-20T08:18:12Z). I did not play a second R match of my own patch. I did not open a pull request. I did not commit an engine source file. The STEP 3 line in stamps.txt was appended with this report, not at the minute step 3 finished; the step 3 commits are the ones named in git log.

what I am NOT sure about: my cutoff runs before the ordinary hash cutoff, so a deep lower bound that clears beta by the margin returns beta+margin instead of the stored score. Seat 040 runs the test only after that ordinary cutoff misses, uses margin 120, and also accepts an exact bound. Both fit the sentence. I do not know which is stronger on the owner's net.

times: see stamps.txt

The machine has AVX-512 and BMI2, so the release builds used the default march and not FORGE_PORTABLE. Honesty passed on those builds.

```
$ git status --short
 M forge-combo29/grok/090/stamps.txt
?? forge-combo29/grok/090/REPORT.md
?? forge-combo29/grok/090/RESULT.txt
?? forge-combo29/grok/090/apply_check.txt
?? forge-combo29/grok/090/config.json

$ ls -la forge-combo29/grok/090
total 10300
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 08:57 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:55 ..
-rw-r--r-- 1 ubuntu ubuntu     131 Nov 20 08:56 apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:07 asan_G100_d10.err
-rw-r--r-- 1 ubuntu ubuntu    1087 Nov 20 08:07 asan_G100_d10.meta
-rw-r--r-- 1 ubuntu ubuntu    8615 Nov 20 08:07 asan_G100_d10.rows
-rw-r--r-- 1 ubuntu ubuntu  252012 Nov 20 08:07 asan_G100_d10.txt
-rw-r--r-- 1 ubuntu ubuntu       3 Nov 20 08:07 asan_nm_count.txt
-rw-r--r-- 1 ubuntu ubuntu    3461 Nov 20 08:08 asan_scratch.err
-rw-r--r-- 1 ubuntu ubuntu    1091 Nov 20 08:08 asan_scratch.meta
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:08 asan_scratch.rows
-rw-r--r-- 1 ubuntu ubuntu    6491 Nov 20 08:08 asan_scratch.txt
-rw-r--r-- 1 ubuntu ubuntu     130 Nov 20 08:02 BASELINE_BG.txt
-rw-r--r-- 1 ubuntu ubuntu     501 Nov 20 08:02 baseline_sums.py
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:01 B_G_d12.err
-rw-r--r-- 1 ubuntu ubuntu     917 Nov 20 08:01 B_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu   30749 Nov 20 08:01 B_G_d12.rows
-rw-r--r-- 1 ubuntu ubuntu  892088 Nov 20 08:01 B_G_d12.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:01 B_O_d12.err
-rw-r--r-- 1 ubuntu ubuntu     921 Nov 20 08:01 B_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu   20046 Nov 20 08:01 B_O_d12.rows
-rw-r--r-- 1 ubuntu ubuntu  502447 Nov 20 08:01 B_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu    1094 Nov 20 08:20 compare_partner.py
-rw-r--r-- 1 ubuntu ubuntu    1313 Nov 20 08:05 compare_rows.py
-rw-r--r-- 1 ubuntu ubuntu    7154 Nov 20 08:23 config.json
-rw-r--r-- 1 ubuntu ubuntu    9924 Nov 20 08:01 depth_harness.py
-rw-r--r-- 1 ubuntu ubuntu    1933 Nov 20 08:04 DESIGN.txt
-rw-r--r-- 1 ubuntu ubuntu   12861 Nov 20 08:01 first200.fens
-rw-r--r-- 1 ubuntu ubuntu    1504 Nov 20 08:06 gen_r.py
-rw-r--r-- 1 ubuntu ubuntu     275 Nov 20 07:58 honesty_b_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 07:58 honesty_b_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     275 Nov 20 07:58 honesty_b_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 07:58 honesty_b_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     275 Nov 20 07:58 honesty_b_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 07:58 honesty_b_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     277 Nov 20 07:58 honesty_b_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 07:58 honesty_b_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     937 Nov 20 07:57 honesty_b.sh
-rw-r--r-- 1 ubuntu ubuntu     233 Nov 20 08:01 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu    1602 Nov 20 08:04 honesty_exe.sh
-rw-r--r-- 1 ubuntu ubuntu     275 Nov 20 08:04 honesty_p_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:04 honesty_p_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     275 Nov 20 08:04 honesty_p_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:04 honesty_p_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     275 Nov 20 08:04 honesty_p_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:04 honesty_p_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     277 Nov 20 08:04 honesty_p_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:04 honesty_p_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    5477 Nov 20 08:04 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu     220 Nov 20 08:15 match_og.meta
-rw-r--r-- 1 ubuntu ubuntu 3592755 Nov 20 08:15 match_og.pgn
-rw-r--r-- 1 ubuntu ubuntu    1617 Nov 20 08:09 match_og.sh
-rw-r--r-- 1 ubuntu ubuntu  132675 Nov 20 08:15 match_og.txt
-rw-r--r-- 1 ubuntu ubuntu      43 Nov 20 08:20 MATCH_OG.txt
-rw-r--r-- 1 ubuntu ubuntu     249 Nov 20 08:23 match_partner_r.meta
-rw-r--r-- 1 ubuntu ubuntu 1447350 Nov 20 08:23 match_partner_r.pgn
-rw-r--r-- 1 ubuntu ubuntu    1518 Nov 20 08:21 match_partner_r.sh
-rw-r--r-- 1 ubuntu ubuntu   67028 Nov 20 08:23 match_partner_r.txt
-rw-r--r-- 1 ubuntu ubuntu      49 Nov 20 08:23 MATCH_PARTNER_R.txt
-rw-r--r-- 1 ubuntu ubuntu     595 Nov 20 08:20 match_summary.py
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:09 openings_OG.epd
-rw-r--r-- 1 ubuntu ubuntu    1202 Nov 20 08:19 partner040_O_on.nodes
-rw-r--r-- 1 ubuntu ubuntu    4386 Nov 20 08:19 partner040.patch.txt
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:23 partner_apply.txt
-rw-r--r-- 1 ubuntu ubuntu     278 Nov 20 08:20 partner_h_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:20 partner_h_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     278 Nov 20 08:20 partner_h_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:20 partner_h_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     278 Nov 20 08:20 partner_h_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:20 partner_h_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     280 Nov 20 08:20 partner_h_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:20 partner_h_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     160 Nov 20 08:21 PARTNER_NODES.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:20 partner_off_O_d12.err
-rw-r--r-- 1 ubuntu ubuntu     997 Nov 20 08:20 partner_off_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu   20046 Nov 20 08:20 partner_off_O_d12.rows
-rw-r--r-- 1 ubuntu ubuntu  525769 Nov 20 08:20 partner_off_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:20 partner_on_O_d12.err
-rw-r--r-- 1 ubuntu ubuntu     996 Nov 20 08:20 partner_on_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu   20043 Nov 20 08:20 partner_on_O_d12.rows
-rw-r--r-- 1 ubuntu ubuntu  526143 Nov 20 08:20 partner_on_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:05 P_off_G_d12.err
-rw-r--r-- 1 ubuntu ubuntu     951 Nov 20 08:05 P_off_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu   30749 Nov 20 08:05 P_off_G_d12.rows
-rw-r--r-- 1 ubuntu ubuntu  911936 Nov 20 08:05 P_off_G_d12.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:05 P_off_O_d12.err
-rw-r--r-- 1 ubuntu ubuntu     955 Nov 20 08:05 P_off_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu   20046 Nov 20 08:05 P_off_O_d12.rows
-rw-r--r-- 1 ubuntu ubuntu  513763 Nov 20 08:05 P_off_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:05 P_on_O_d12.err
-rw-r--r-- 1 ubuntu ubuntu    1073 Nov 20 08:05 P_on_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu   20045 Nov 20 08:05 P_on_O_d12.rows
-rw-r--r-- 1 ubuntu ubuntu  550877 Nov 20 08:05 P_on_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu     562 Nov 20 08:03 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu    1920 Nov 20 08:09 proofs_summary.py
-rw-r--r-- 1 ubuntu ubuntu     873 Nov 20 08:09 PROOFS.txt
-rw-r--r-- 1 ubuntu ubuntu    5370 Nov 20 08:57 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu     186 Nov 20 08:56 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu      29 Nov 20 08:07 scratch_fen.fen
-rw-r--r-- 1 ubuntu ubuntu      79 Nov 20 07:55 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu   17691 Nov 20 08:01 set_G.epd
-rw-r--r-- 1 ubuntu ubuntu   19291 Nov 20 08:06 set_R.fen
-rw-r--r-- 1 ubuntu ubuntu     140 Nov 20 08:57 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu    5164 Nov 20 08:05 uci_p.txt
-rw-r--r-- 1 ubuntu ubuntu    1274 Nov 20 08:00 write_honesty_b.py
```
