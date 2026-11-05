# Job C results - cut gate wall time (measurements and tests, 2026-11-05)

Worker jobc, branch opus-speed-20261105, folder `F:/ospd/wt/opus_speed/jobc/`. All numbers come from the
files named next to them (gate folders under `F:/forge_push` and `D:/grok-pc-data/forge_push`, read-only; outputs
under `F:/ospd/jobc/out/`, scratch copies under `F:/ospd/jobc/tmp/`). Every tool ran on CPUs 0-1 at Idle next to the
crew's NNUE trainer and the other workers' processes, so the wall times quoted here are not speed measurements.
No Elo claim and no speed claim for Forge is made; the queue, its config and the gate folders were not touched.

## 1. gate_replay.py - replay of 13 finished gates (test a)

Source: `F:/ospd/jobc/out/tests_20261105_094859.md` (final run of `tests/run_tests.py`, 09:48:58-09:50:06 PC
clock, ALL PASS; copy in `results/`; the first run `tests_20261105_091738.md` had the same replay rows and only
failed its csv formula check because it assumed [0,10] bounds for four gates that play with other bounds).
Recorded = RESULT.md verdict class; replay = the first pair whose exact fastchess LLR crosses a bound (H1 / H0)
else CAP; LLR compared at the printed pair count.

| gate | why it is in the set | recorded | replay | decided at pair (games) | LLR recorded / replay | singles | exit | s |
|---|---|---|---|---|---|---|---|---|
| gate_sf26bundle14_vs_AL1 | [0,10] cap 1500, LLR -1.68 | CAP | CAP | - | -1.68 / -1.6767 at 750 | 0 | 0 PASS | 4.0 |
| gate72_B4_bundleint_vs_h256e12_confirm | [0,10] H1 at 2108 games | H1 | H1 | 1054 (2108) | 2.96 / 2.9631 at 1054 | 2 | 0 PASS | 3.7 |
| gate68_bundle_g43g33g49_vs_h256e12 | [0,10] H1 with 2 in-flight singles | H1 | H1 | 695 (1390) | 2.99 / 2.9921 at 695 | 2 | 0 PASS | 3.1 |
| gate71_B3_bundleint_vs_h256e12 | [0,10] H0 at 2160 games | H0 | H0 | 1080 (2160) | -2.99 / -2.9895 at 1080 | 1 | 0 PASS | 4.5 |
| gate_stB_lmrttcapall1_vs_AL1 | [0,10] cap 3000 at LLR -2.88 (near the bound) | CAP | CAP | - | -2.88 / -2.8835 at 1500 | 0 | 0 PASS | 7.8 |
| gate69_B1_bundleint_vs_h256e12_confirm | [0,10] cap 3000 at LLR 2.77 (near the bound) | CAP | CAP | - | 2.77 / 2.7659 at 1500 | 0 | 0 PASS | 4.4 |
| gateR7_ttexclusive_nonreg_vs_r7off | [-10,0] non-regression H1 | H1 | H1 | 1267 (2534) | 2.96 / 2.9577 at 1267 | 1 | 0 PASS | 5.0 |
| uhoO30U8soup_v2p4_v2net_vs_AL1lp | [0,5] H1, net gate with early-stop rule, UHO book | H1 | H1 | 1264 (2528) | 2.95 / 2.9483 at 1264 | 1 | 0 PASS | 5.6 |
| uhoE3a_evalmatscale12_r6k_vs_AL1lp | [0,10] cap 6000 (largest PGN, 36 MB) | CAP | CAP | - | 0.78 / 0.785 at 3000 | 0 | 0 PASS | 13.4 |
| uhoE3b_evaloptimism40_r6k_vs_AL1lp | [0,10] H0 at 2360 games, UHO | H0 | H0 | 1180 (2360) | -2.99 / -2.9912 at 1180 | 0 | 0 PASS | 4.1 |
| gateR5A_2_corrext1_vs_r5aoff | [0,10] cap, recorded NOT CLEAN (3 time losses) | CAP | CAP | - | 0.41 / 0.408 at 1500 | 0 | 0 PASS | 4.0 |
| uhoT2_sf26b14 | [0,10] cap, recorded TRIAL-ONLY | CAP | CAP | - | -1.44 / -1.4436 at 750 | 0 | 0 PASS | 1.7 |
| gate_npts3_ep06_vs_AL1 | [0,10] early H0 (net far below), 288 games | H0 | H0 | 144 (288) | -2.99 / -2.9941 at 144 | 0 | 0 PASS | 1.1 |

13 of 13: same verdict, same W/D/L and Ptnml, Elo / nElo / LLR within 0.006 of the recorded values. In every
decided gate the crossing pair equals the printed pair count (fastchess stopped at the first crossing); the
singles are the partner games aborted in flight at the stop (gate68: games 1391 and 1393 have a `Started game`
line, no `Finished game` line, and are not in the PGN). `--verify-moves` (python-chess replay of every move) on
gate_npts3_ep06_vs_AL1: 288 games in 4.1 s, verdict H0 = recorded, PASS. Formula check on FORGE_RESULTS.csv: 111
rows with a Ptnml; with the bounds read from each gate folder (gate101 [-3,1], R5D-MF [-10,0], R7-PFE [-0.5,0.5],
UO30U8 [0,5]) LLR / Elo / nElo of all 111 rows agree within 0.006 (worst LLR difference 0.0050).

## 2. gate_replay.py - deliberate failures (test b)

Copies of `gate_npts3_ep06_vs_AL1.pgn` under `F:/ospd/jobc/tmp/`, each run with and without the gate's log
(`tests_20261105_091738.md`); required: exit 2, an ERROR line, no verdict line.

| copy | what was done | exit (with log / without) | error line (with log) | verdict printed | result |
|---|---|---|---|---|---|
| truncated | file cut at byte 982649 inside a movetext | 2 / 2 | game at line 16244 has no result token (truncated) | no | PASS |
| truncated_headers | file ends after a header block | 2 / 2 | file ends inside the headers of the game at line 13320 (truncated) | no | PASS |
| corrupt_move | game 11: one SAN token replaced by Zz9 | 2 / 2 | game at line 944: not a SAN move: 'Zz9' (corrupt movetext) | no | PASS |
| corrupt_result | game 21: result token changed, Result tag kept | 2 / 2 | result token 0-1 differs from the Result tag 1-0 | no | PASS |
| corrupt_plycount | game 31: one move with its comment deleted | 2 / 2 | PlyCount 49 but 48 moves in the movetext | no | PASS |
| corrupt_binary | NUL / 0xFF bytes written over the middle | 2 / 2 | line 8853: NUL byte (binary garbage) | no | PASS |
| unpaired | game 41 removed, its pair partner kept | 2 / 2 | round 21 has a single game: unpaired PGN (partner game 41 finished in the log but is missing from the PGN) / (no log to prove the partner game was aborted in flight) | no | PASS |
| duplicated | game 51 written twice | 2 / 2 | round 26 has 3 games (expected 2): unpaired / duplicated PGN | no | PASS |
| corrupt_tag | a tag line without its closing bracket | 2 / 2 | line 1040: malformed tag line '[Round "7"' | no | PASS |

18 of 18 PASS.

## 3. queue_throughput.py - games per hour and idle gaps

Source: `F:/ospd/jobc/out/throughput_all.{md,csv,json}` (109 gates with a start time, 2026-10-23 14:46 to the
running gate; 108 finished gates cover 260.7 h of game windows). Groups (finished gates, median over the group,
never pooled across groups):

| threads | conc | book | gates | games/h median (min-max) | games/h per slot | mean game s (PGN GameDuration) | slot overhead s |
|---|---|---|---|---|---|---|---|
| 1 | 5 | 8moves_v3 | 22 | 612.9 (559.6-635.5) | 122.6 | - (D: layout, no PGN) | - |
| 1 | 7 | 8moves_v3 | 2 | 853.8 (844.9-862.6) | 122.0 | - | - |
| 1 | 8 | 8moves_v3 | 49 | 992.8 (255.0-1011.3) | 124.1 | 28.4 | 0.6 |
| 2 | 4 | 8moves_v3 | 14 | 464.6 / 473.4 (443.9-502.0) | 116.2 / 118.4 | 29.3 / 28.9 | 1.5 / 1.2 |
| 2 | 4 | uho_lichess_v1 | 10 | 433.9 (430.6-451.7) | 108.5 | 32.7 | 0.5 |
| 2 | 2 | uho_lichess_v1 | 1 | 215.2 | 107.6 | 32.9 | 0.6 |

Last 16 gates of the queue (F: layout; times = PC wall clock from the PGN tags; gap = last game end -> next gate's
RUN_INFO started_pc):

| gate | first game | last game | games | conc | thr | book | window h | games/h | mean game s | gap to next s |
|---|---|---|---|---|---|---|---|---|---|---|
| uhoE3a_evalmatscale12_vs_AL1lp | 2026-11-01 15:20:54 | 2026-11-01 22:14:11 | 3000 | 4 | 2 | uho | 6.9 | 435.5 | 32.5 | 118 |
| uhoE3b_evaloptimism40_vs_AL1lp | 2026-11-01 22:16:10 | 2026-11-02 05:14:13 | 3000 | 4 | 2 | uho | 7.0 | 430.6 | 32.9 | 227 |
| uhoE3c_evalrule50damp30_vs_AL1lp | 2026-11-02 05:18:01 | 2026-11-02 12:13:28 | 3000 | 4 | 2 | uho | 6.9 | 433.3 | 32.7 | 176 |
| gate_npt104_k32h3_l1024_ep06_r10fix1_vs_AL1 | 2026-11-02 12:16:24 | 2026-11-02 12:51:00 | 256 | 4 | 2 | 8moves | 0.6 | 443.9 | 30.2 | 112 |
| gate_npt104_k32h3_l1024_ep20_r10fix1_vs_AL1 | 2026-11-02 12:52:53 | 2026-11-02 13:27:02 | 262 | 4 | 2 | 8moves | 0.6 | 460.3 | 29.3 | 74 |
| gate_p27r_qsevnonpv1_al1_vs_AL1 | 2026-11-02 13:28:17 | 2026-11-02 19:32:59 | 3000 | 4 | 2 | 8moves | 6.1 | 493.6 | 28.6 | 203 |
| gate_npts3_ep06_vs_AL1 | 2026-11-02 19:36:22 | 2026-11-02 20:14:04 | 288 | 4 | 2 | 8moves | 0.6 | 458.4 | 29.9 | 98 |
| gate_npts3_ep09last_vs_AL1 | 2026-11-02 20:15:42 | 2026-11-02 20:48:56 | 248 | 4 | 2 | 8moves | 0.6 | 447.7 | 30.4 | 82 |
| gate_stA_v2_corrsignedkey1_vs_AL1 | 2026-11-02 20:50:18 | 2026-11-03 02:55:22 | 3000 | 4 | 2 | 8moves | 6.1 | 493.1 | 28.7 | 136 |
| gate_nptw4s4_ep09last_vs_AL1 | 2026-11-03 02:57:38 | 2026-11-03 03:33:32 | 278 | 4 | 2 | 8moves | 0.6 | 464.6 | 29.5 | 109 |
| gate_nptw4s4_ep07_vs_AL1 | 2026-11-03 03:35:22 | 2026-11-03 04:07:49 | 248 | 4 | 2 | 8moves | 0.5 | 458.6 | 29.9 | 56 |
| gate_stB_lmrttcapall1_vs_AL1 | 2026-11-03 04:08:45 | 2026-11-03 10:10:59 | 3000 | 4 | 2 | 8moves | 6.0 | 496.9 | 28.4 | 138 |
| gate_stB_lmrcapvictim1_vs_AL1 | 2026-11-03 10:13:17 | 2026-11-03 12:22:24 | 1070 | 4 | 2 | 8moves | 2.2 | 497.2 | 28.4 | 69 |
| uhoE3a_evalmatscale12_r6k_vs_AL1lp | 2026-11-03 12:23:34 | 2026-11-04 02:06:45 | 6000 | 4 | 2 | uho | 13.7 | 437.3 | 32.4 | 35305 |
| uhoE3b_evaloptimism40_r6k_vs_AL1lp | 2026-11-04 11:55:11 | 2026-11-04 22:53:10 | 2360 | 2 | 2 | uho | 11.0 | 215.2 | 32.9 | 93 |
| uhoO30U8soup_v2p4_v2net_vs_AL1lp | 2026-11-04 22:54:44 | 2026-11-05 04:46:31 | 2528 | 4 | 2 | uho | 5.9 | 431.2 | 32.9 | 107 |
| uhoO30R5kb8short_v2p4_v2net_vs_AL1lp (RUNNING, excluded from gaps) | 2026-11-05 04:48:20 | (1958 games by 09:20:33) | - | 4 | 2 | uho | - | 431.6 | 32.7 | - |

Findings (all from `throughput_all.json`):
- Gate-to-gate gaps: 108 transitions, median 94 s, 95 of them under 5 min; the 99 gaps under 30 min add up to 3.26 h
  (1.25 % of the 260.7 h of game windows). Composition, measured on 13 consecutive F: gates (2026-11-01..03) from
  the previous gate's last GameEndTime, its RESULT.md mtime, the next gate's PREBENCH.txt mtime, RUN_INFO
  started_pc and first GameStartTime: post-gate work (RESULT.md, option check) 6-176 s (median 29 s), the
  candidate's pre-gate bench d11-d22 OFF and ON until PREBENCH.txt is written 47-96 s (median 56 s), RUN_INFO and
  fastchess start 0-1 s. So about half of a typical transition is the pre-gate bench (ten `bench` runs, the two
  `bench 22` alone take ~27 s each on a free core), the rest is the post-processing of the previous gate.
- Five gaps over 30 min dominate the idle time: 38908 s (gate_auto_e48f029_confirm -> gate101), 16874 s (gate101 ->
  gate109), 8008 s (gate72_B4 -> gateR5A_1), 7965 s (gateR7_prefetchearly -> gateR5A_2), 35305 s
  (uhoE3a_r6k -> uhoE3b_r6k) = 29.7 h of an empty or paused queue. Keeping the queue fed is worth more than any
  per-gate saving below.
- uhoE3b_evaloptimism40_r6k_vs_AL1lp ran at concurrency 2 (RUN_INFO.json `concurrency: 2`, `cap_warning: null`, no
  note that explains it; runner forge_queue.ps1 v3-6day r8d2, affinity 0xFFF0 as always): 215 games/h, 11.0 h for
  2360 games; at concurrency 4 the same games take ~5.4 h. Whether that was intended (a GPU / training window)
  the RUN_INFO does not say; worth a look at how that gate was queued.
- Per slot the rate is stable: 108-124 games/h per concurrency slot across every setting; a 10+0.1 game lasts 28.4 s
  (8moves_v3) to 32.7 s (UHO) on average with 0.5-1.5 s of overhead per game per slot. The Threads=2 conc 4 setting
  (8 engine threads on the 12 logical CPUs 4-15) gives 431-502 games/h; Threads=1 conc 8 gave 993 games/h.

## 4. concurrency_plan.py - games per hour at Threads=1 (math only)

Source: `F:/ospd/jobc/out/concurrency_plan.json` from the throughput groups above (seconds per game + slot
overhead per group; the game length at 10+0.1 does not depend on Threads).

| book (measured group) | slot s per game | cores (one game each) | games/h | h to 3000 / 4000 / 6000 games |
|---|---|---|---|---|
| 8moves_v3 (Threads=1 conc 8, 49 gates) | 29.0 | 4 | 497 | 6.0 / 8.1 / 12.1 |
| 8moves_v3 | 29.0 | 6 | 745 | 4.0 / 5.4 / 8.1 |
| 8moves_v3 | 29.0 | 8 | 993 | 3.0 / 4.0 / 6.0 |
| 8moves_v3 | 29.0 | 12 | 1490 | 2.0 / 2.7 / 4.0 |
| uho_lichess_v1 (Threads=2 conc 4, 10 gates) | 33.2 | 4 | 434 | 6.9 / 9.2 / 13.8 |
| uho_lichess_v1 | 33.2 | 6 | 651 | 4.6 / 6.1 / 9.2 |
| uho_lichess_v1 | 33.2 | 8 | 867 | 3.5 / 4.6 / 6.9 |
| uho_lichess_v1 | 33.2 | 12 | 1301 | 2.3 / 3.1 / 4.6 |

CPUs 4-15 of the queue are 6 physical cores / 12 logical CPUs, and every gate's RUN_INFO says affinity 0xFFF0
(CPUs 4-15), the conc-8 Threads=1 gates included (gateR5A_1, gate39 checked). So the 993 games/h baseline was
already 8 single-threaded games on 6 physical cores (at least two games on SMT siblings at any time), and the
Threads=2 conc 4 setting is 8 engine threads on the same 12 logical CPUs. Games per hour at a wall-clock TC do not
tell how many nodes each game searched: 6 games on 6 physical cores would search more nodes per game than the
conc-8 baseline, 12 games fewer; either is a different gate from the recorded ones, the crew's call. The table
above is throughput only.

## 5. adjudication_audit.py - settings, endings and what adjudication would save

Source: `F:/ospd/jobc/out/adjudication_audit2.{md,json}` (five gates: two books, both thread settings). Every gate
in the queue runs with resign / draw / maxmoves / tablebase adjudication DISABLED (config.json), tc=10+0.1
timemargin=1000, Hash 16, OwnBook false, order=random with a per-gate start offset; book 8moves_v3.pgn (PGN, 16
plies) or UHO_Lichess_4852_v1.epd (EPD, either side to move).

| gate | games | book | thr / hash / conc | endings (log reasons) | plies mean / median / p90 / max | engine s per game |
|---|---|---|---|---|---|---|
| gate_sf26bundle14_vs_AL1 | 1500 | 8moves_v3 | 2 / 16 / 4 | 3-fold 962, mate 341, fifty 103, insufficient 92, stalemate 2 | 140.7 / 127 / 230 / 640 | 28.5 |
| uhoE3a_evalmatscale12_r6k_vs_AL1lp | 6000 | UHO | 2 / 16 / 4 | mate 2598, 3-fold 2434, fifty 544, insufficient 412, stalemate 12 | 154.6 / 146 / 238 / 748 | 32.8 |
| gate_stB_lmrttcapall1_vs_AL1 | 3000 | 8moves_v3 | 2 / 16 / 4 | 3-fold 1881, mate 678, insufficient 231, fifty 200, stalemate 10 | 142.6 / 129 / 231 / 769 | 28.8 |
| uhoO30U8soup_v2p4_v2net_vs_AL1lp | 2529 | UHO | 2 / 16 / 4 | mate 1142, 3-fold 989, fifty 227, insufficient 166, stalemate 5 | 158.7 / 148 / 247 / 850 | 33.2 |
| gateR5A_1_corrhistplus4_vs_r5aoff | 3000 | 8moves_v3 | 1 / 16 / 8 | 3-fold 1871, mate 734, insufficient 203, fifty 184, stalemate 8 | 141.6 / 131 / 231 / 553 | 28.6 |

Simulation of fastchess rules on the recorded move comments (mover's score; mate = beyond any threshold; side
parity from the FEN tag). "Disagreements" = games whose adjudicated result differs from the played one (the price
of the rule: it changes what the gate measures):

| gate | rule set | games ended early | plies saved | engine s saved | disagreements |
|---|---|---|---|---|---|
| gate_sf26bundle14_vs_AL1 | draw34/8/20 | 953 (63.5 %) | 28062 (13.3 %) | 4101 (9.6 %) | 12 |
| gate_sf26bundle14_vs_AL1 | draw40/16/5 | 560 (37.3 %) | 7645 (3.6 %) | 1117 (2.6 %) | 0 |
| gate_sf26bundle14_vs_AL1 | resign3/600two | 343 (22.9 %) | 14761 (7.0 %) | 1587 (3.7 %) | 2 |
| gate_sf26bundle14_vs_AL1 | resign5/1000two | 339 (22.6 %) | 8139 (3.9 %) | 685 (1.6 %) | 0 |
| gate_sf26bundle14_vs_AL1 | fishtest-like (resign3/600two + draw34/8/20) | 1282 (85.5 %) | 42343 (20.1 %) | 5645 (13.2 %) | 14 |
| gate_sf26bundle14_vs_AL1 | maxmoves200 | 14 (0.9 %) | 1413 (0.7 %) | 144 (0.3 %) | 1 |
| uhoE3a_evalmatscale12_r6k_vs_AL1lp | draw34/8/20 | 3167 (52.8 %) | 84413 (9.1 %) | 11145 (5.7 %) | 52 |
| uhoE3a_evalmatscale12_r6k_vs_AL1lp | draw40/16/5 | 1742 (29.0 %) | 22534 (2.4 %) | 3018 (1.5 %) | 4 |
| uhoE3a_evalmatscale12_r6k_vs_AL1lp | resign3/600two | 2598 (43.3 %) | 105558 (11.4 %) | 11398 (5.8 %) | 0 |
| uhoE3a_evalmatscale12_r6k_vs_AL1lp | resign5/1000two | 2589 (43.1 %) | 60717 (6.5 %) | 5129 (2.6 %) | 0 |
| uhoE3a_evalmatscale12_r6k_vs_AL1lp | fishtest-like | 5713 (95.2 %) | 187973 (20.3 %) | 22351 (11.4 %) | 52 |
| gate_stB_lmrttcapall1_vs_AL1 | draw34/8/20 | 1984 (66.1 %) | 62570 (14.6 %) | 9114 (10.5 %) | 32 |
| gate_stB_lmrttcapall1_vs_AL1 | draw40/16/5 | 1140 (38.0 %) | 16197 (3.8 %) | 2335 (2.7 %) | 4 |
| gate_stB_lmrttcapall1_vs_AL1 | resign3/600two | 679 (22.6 %) | 28719 (6.7 %) | 3103 (3.6 %) | 1 |
| gate_stB_lmrttcapall1_vs_AL1 | resign5/1000two | 677 (22.6 %) | 16773 (3.9 %) | 1436 (1.7 %) | 0 |
| gate_stB_lmrttcapall1_vs_AL1 | fishtest-like | 2630 (87.7 %) | 90169 (21.1 %) | 12113 (14.0 %) | 33 |
| uhoO30U8soup_v2p4_v2net_vs_AL1lp | draw34/8/20 | 1286 (50.9 %) | 34494 (8.6 %) | 4486 (5.3 %) | 22 |
| uhoO30U8soup_v2p4_v2net_vs_AL1lp | resign3/600two | 1145 (45.3 %) | 50392 (12.6 %) | 5555 (6.6 %) | 3 |
| uhoO30U8soup_v2p4_v2net_vs_AL1lp | resign5/1000two | 1139 (45.0 %) | 28211 (7.0 %) | 2453 (2.9 %) | 0 |
| uhoO30U8soup_v2p4_v2net_vs_AL1lp | fishtest-like | 2406 (95.1 %) | 83961 (20.9 %) | 9957 (11.9 %) | 25 |
| gateR5A_1_corrhistplus4_vs_r5aoff | draw34/8/20 | 1928 (64.3 %) | 56597 (13.3 %) | 8156 (9.5 %) | 38 |
| gateR5A_1_corrhistplus4_vs_r5aoff | resign5/1000two | 726 (24.2 %) | 16796 (4.0 %) | 1474 (1.7 %) | 0 |
| gateR5A_1_corrhistplus4_vs_r5aoff | fishtest-like | 2624 (87.5 %) | 85492 (20.1 %) | 11335 (13.2 %) | 41 |

Reading (projection only, crew decision): a fishtest-like rule set ends 85-95 % of the games early and saves about
20 % of the plies but only 11-14 % of the engine time, because the plies it cuts are the fast endgame and mate
tails (0.001-0.1 s per move). The draw rule at 20 cp is the part that changes results: 12-52 games per gate
(0.8-1.3 % of the games, 1.0-1.6 % of the adjudicated ones) that were adjudicated as draws ended decisively. A
twosided resign at 5 moves / 1000 cp changed no result in any of the five gates and saves 1.6-2.9 % of the engine
time (3.9-7.0 % of the plies); a draw rule at 5 cp over 16 plies after move 40 changed 0-4 results for 1.3-2.7 % of
the time. The engine-time share is the right currency: a gate is clock-bound at 10+0.1, so 10 % of engine time is
roughly 10 % of wall time, not 20 %. maxmoves 200 does almost nothing (0.5-1.5 % of the games).

## 6. pregate_screen.py - screens before the games (tool 6 tests)

Source: `F:/ospd/jobc/out/pregate_chain_console.txt`, `pregate_lock2.json`, `pregate_whoami.json`,
`pregate_badpins.json`, `pregate_notengine.json`, `pregate_lock_nnueoff.json`; engine log
`pregate_lock2.uci.log`. One engine at a time on CPUs 0-1 at Idle next to the trainer and the other workers.

| run | input | result | time | detail |
|---|---|---|---|---|
| 1 | lock exe (sha256 FD3A5190...), all defaults, reference = itself, WAC = tools/wac300.epd of the kit stage | PASS, exit 0 | 57.7 s (budget 300) | uciok (61 options, 0 changed vs reference), bench d11/13/16/20/22 = 312866 / 862329 / 3024920 / 12389307 / 34048354 (pins), perft 5 startpos 4865609 and kiwipete 193690690 (pins), smoke 20 six-field FENs at go movetime 200: 0 bad, max 0.20 s; WAC 55/60 solved at go nodes 100000; no rejected-input line; quit exit 0 |
| 2 | C:/Windows/System32/whoami.exe (not an engine) | FAIL, exit 1 | 0.3 s | file PASS (PE image), uci FAIL: engine closed its output without uciok |
| 3 | lock exe with a wrong pin list (d13=1) | FAIL, exit 1 | 0.9 s | bench11 PASS, bench13 FAIL: nodes 862329 want 1; the run stops there |
| 4 | a 14-byte text file renamed .exe | FAIL, exit 1 | 0.0 s | file FAIL: not a PE image |
| 5 | lock exe with --opt UseNNUE=false (net off in the smoke / WAC phase; bench at defaults) | PASS, exit 0 | 8.9 s | d11 pin, both perft pins, 10 FENs smoke 0 bad, WAC 29/30 at 100k nodes (different subset than run 1) |

| 6 | lock exe with `--fen-selftest` (the tool sends ONE placement-only FEN before the smoke) | FAIL, exit 1 | 1.2 s | smoke FAIL: "selftest placement-only FEN: engine reported 'info string invalid FEN: FEN must contain six fields' (the screen fails on it, as required)"; `pregate_chain2_console.txt`, `pregate_fenselftest.json` |
| 7 | real candidate forge_ltopgo_x_sf26bundle_al1_e417a34e.exe, `--ref-exe` lock, `--opt Sf26Bundle=14`, pins d11/d13 | PASS, exit 0 | 3.7 s | 65 options: 0 changed vs the lock, 4 added (Sf26Bundle, Sf26RazorAllRelief, Sf26NmpPriorBonus, Sf26LmrAlphaGap), 0 removed; OFF pins d11 312866 / d13 862329 at defaults; perft startpos pin; 5-FEN smoke 0 bad; WAC 10/10; `pregate_sf26cand.json` |

The bench pins take 43 s of the 58 s of run 1 (d22 alone 27 s); perft 5 kiwipete 2.6 s; the 20-position smoke
3.6 s; 60 WAC positions at 100k nodes 8.6 s. The lock rejects a placement-only FEN with
`info string invalid FEN: FEN must contain six fields` and keeps its old position: the screen sends six-field
FENs only (python-chess `fen()`), any such engine line is a FAIL, and run 6 shows that path end to end.

## 7. llr_project.py - projections (planning only)

Source: `F:/ospd/jobc/out/proj_*.json` and `series_*.csv` (the LLR after every pair from gate_replay.py; copies in
`results/`). Validation idea: take the counts at an early pair of a finished gate (from its series), project with
the tool (Dirichlet posterior, 1000 paths, seed 1, exact LLR after every pair), compare with what happened.

| gate, state used | Ptnml at that pair, LLR | P(H1) / P(H0) before cap / P(cap) | decided paths: median (p90) more pairs | what actually happened |
|---|---|---|---|---|
| uhoO30U8soup [0,5] cap 4000, at pair 300 | [2,71,147,78,2], 0.13 | 0.167 / 0.038 / 0.795 | 1279 (1592) | H1 at pair 1264 (964 more pairs) |
| gate_stB_lmrttcapall1 [0,10] cap 3000, at pair 400 | [4,68,256,68,4], -0.33 | 0.079 / 0.293 / 0.628 | 715 (1024) | cap at pair 1500, LLR -2.88, no decision |
| gateR7_ttexclusive [-10,0] cap 3000, at pair 400 | [2,58,278,57,5], 0.67 | 0.469 / 0.026 / 0.505 | 625 (957) | H1 at pair 1267 (867 more pairs) |

Reading: at 300-400 pairs the posterior is wide, so the tool says "most likely still undecided at the cap" for all
three, and the two gates that did decide did so late (864-964 more pairs, inside the projected decided-path range).
The Brownian plug-in column (point estimate, no cap) is over-confident (P(H1) 0.998 / 0.035 / 0.999) because it
ignores the uncertainty of the current estimate; the simulation is the number to use for ordering. Run time at
step 1 pair: 77-183 s per projection (1000 paths, 1300-2800 pairs) on this CPU budget.

## 8. book_load_check.py - book loading (measure only)

Source: `F:/ospd/jobc/out/book_load_check2.json` (the valid run; `book_load_check.json` is the first attempt, whose
fastchess A/B measured nothing because fastchess checks the engine path BEFORE indexing - with a non-existent
engine it exits in 0.1 s without reading the book). Copies under `F:/ospd/jobc/tmp/` (8moves_v3.pgn 8.0 MB,
UHO_Lichess_4852_v1.epd 174.9 MB, the converted 8moves_v3.epd 2.3 MB, 34700 lines; F: had 58.2 GB free before
the 175 MB copy). Minimum of 3 repeats, wall clock on CPUs 0-1 at Idle; files were in the OS cache (the copies had
just been written), so these are warm numbers.

| book | raw read | python parse | fastchess index (launch-to-exit minus the 1-line EPD baseline of 1.075 s) |
|---|---|---|---|
| 8moves_v3.pgn (34700 games, 555200 moves) | 0.002 s | 0.215 s | 0.379 s |
| 8moves_v3 converted to EPD (34700 FENs, python-chess, conversion 39.8 s once) | - | 0.006 s | 0.093 s |
| UHO_Lichess_4852_v1.epd (2632036 lines) | 0.045 s | 0.441 s | 1.337 s |

Cross-check on real gates (`throughput_all.json`, field setup_s = first PGN GameStartTime minus RUN_INFO
started_pc, 118 gates): median 0 s, p90 1 s, max 2 s for both books. Verdict: book loading costs under 1.5 s per
gate (0.4 s for the PGN book; an EPD conversion of 8moves_v3 would save ~0.3 s per gate, i.e. nothing against
a 6 h gate). Not worth a change; the per-gate transition cost is elsewhere (section 3: the candidate bench).

## 9. What is unverified / open
- The replay's completion-order model (fastchess checks the SPRT after every completed pair) is confirmed on 13
  gates by the equality crossing pair = printed pair count; no gate in the set crossed a bound before a cap stop, so
  "cap but a crossing would have been missed" never occurred and cannot be excluded for the ratinginterval cadence.
- The net early-stop rule (H0-early at the first block >= 750 games) was evaluated on the UHO net gates present on
  F: (it does not fire there); the four gates where it fired (gate109, 112, 55, 56) have no PGN (D: layout), so the
  runner's block cadence could not be replayed.
- adjudication_audit.py simulates rules on recorded games; an active rule would also change the later moves of the
  games it does not end. The saved plies / seconds are an upper bound of a projection, not a measurement.
- The screen's WAC floor is informational (default 0); a floor for candidates needs the crew's number (the lock
  solves 55/60 of positions 21-80 at 100k nodes with the net, 29/30 of positions 11-40 with the net off).
- The gap composition (section 3) is measured on 13 transitions of one runner version (r8d2); the D: layout gates
  have no PREBENCH.txt mtime trail and were not decomposed.
- No jobc process was left running across the coordinator restart (checked with Get-CimInstance at 09:36); the
  scratch under `F:/ospd/jobc/` (190 MB: book copies, failure-test PGNs, fastchess's autosave config.json) stays
  in place as the rules ask.
- llr_project.py at step 1 pair takes about 30 s per 1000 paths and 1500 pairs on this CPU budget; `--step 5`
  is 5x faster and can delay a simulated stop by up to 4 pairs.
- Times are PC wall clock from the PGN tags; the "-0700/-0800" zone labels in the tags do not match the Vienna
  clock the crew uses and are ignored.
