# Seat 017, idea 17, S15

Idea S15 searches a rook move that meets a passed pawn at full depth in a rook ending, and does not extend it and does not add an evaluation term.
The option is IdeaS15, a check defaulting to false, plus the spin IdeaS15_MinPieces defaulting to 8 (range 2 to 32).
With IdeaS15 false the predicate is not called and the reduction is the one the engine already computed. The rule is in design.txt and the diff is idea.patch.txt. `git apply --check` on a clean base tree printed `own apply --check ok` (apply_check.txt).

EXISTS: no. I read forge-combo29/src/search.cpp. Late-move reduction is adjusted by several options already (history, correction, late-parent relief, and the rest). None of them cancels a reduction because a rook has reached a passed pawn's file.

## Honesty numbers

Plain engine B, no setoption, from HONESTY_B.txt: bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, go perft 5 nodes 4865609.
Patched engine P, no setoption, from HONESTY_P.txt: the same four counts.
Exe B with S14, Threads 1, Hash 16, from B_O_summary.txt and B_G_summary.txt: O depth 12 sum 9500069, first three 41311 / 24872 / 28574. G depth 12 sum 18466239.

## Step table

Pasted from report_numbers.py, which reads the saved files:

```
step | status | evidence | result
STEP 1 seat | done | SEAT.txt | seat 017 idea 17
STEP 2 honesty B | done | HONESTY_B.txt | 312866 862329 3024920 4865609
STEP 2 known sums | done | B_O_summary.txt B_G_summary.txt | O 9500069 G 18466239
STEP 3 prediction | done | prediction.txt | committed before measuring P
STEP 3 patch applies | done | idea.patch.txt apply_check.txt | git apply --check ok
proof 1 honesty P | done | HONESTY_P.txt | same four node counts
proof 2 switch off | done | compare_off_O.txt compare_off_G.txt | 0 of 200 and 0 of 353
proof 3 switch on | done | compare_on_O.txt | 0 of 200
proof 4 uci options | done | uci_P.txt | IdeaS15 false, IdeaS15_MinPieces 8
proof 5 sanitizer | done | raw_asan_G100_d10.txt.meta raw_asan_scratch.txt.err | nm 35, clean stderr, scratch reported
STEP 3 match | done | match_OG_summary.txt | elo -0.63 +/- 5.84 games 1106
STEP 4 partner | done | compare_partner_067_off.txt compare_partner_067_on_vs_theirs.txt match_partner_067_summary.txt | 067 CONFIRMS on the repeated proofs
handoff minute 60 | done | gate_notes.txt | no FABLE_TO_grok file
```

## Proofs

(1) Honesty on exe P with no setoption: bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609. HONESTY_P.txt.

(2) S14 and IdeaS15 false. O depth 12: differ 0 of 200, both sums 9500069 (compare_off_O.txt). G depth 12: differ 0 of 353, both sums 18466239 (compare_off_G.txt).

(3) S14 and IdeaS15 true, O depth 12: differ 0 of 200, sum 9500069 (compare_on_O.txt). The same binary does change a rook ending. probe_rook.fen at depth 12 is 136029 with the switch off and 127559 with it on (probe_off_d12_summary.txt, probe_on_d12_summary.txt). The 200 openings at depth 12 never reach a node where a reduced rook move meets a passer under this gate. prediction.txt said the O sum would be 9690000 and would be wrong at 9500069 or below. The measured sum is 9500069, so that prediction is wrong. I did not edit prediction.txt.

(4) The uci listing in uci_P.txt contains `option name IdeaS15 type check default false` and `option name IdeaS15_MinPieces type spin default 8 min 2 max 32`.

(5) AddressSanitizer and UndefinedBehaviorSanitizer build. First 100 positions of G at depth 10 with IdeaS15 true: stderr is 0 bytes (raw_asan_G100_d10.txt.err). The meta line `nm -C /tmp/build-asan/forge | grep -c __asan_` printed 35. A scratch copy with one heap read past the end of a 4-int array, on the FEN in special_heap.fen, built the same way and run through uci_suite.py, printed: `/tmp/scratch-src/src/uci.cpp:46:26: runtime error: load of address 0x5020000000c0 with insufficient space for an object of type 'int'`.

## Match

Exe P with IdeaS15 true against exe P with IdeaS15 false. Both S14, Threads 1, Hash 16, 20000 nodes, openings O and G (553), both colours, 1106 games. fastchess concurrency 3. OwnBook was set false because the engine's default book is on and would play moves without searching; that choice is written in match.sh.

Pasted from match_OG_summary.txt, which parse_match.py wrote from match_OG.log:

```
Elo: -0.63 +/- 5.84, nElo: -2.20 +/- 20.48
LOS: 41.65 %, DrawRatio: 86.44 %, PairsRatio: 0.97
Games: 1106, Wins: 339, Losses: 341, Draws: 426, Points: 552.0 (49.91 %)
summary elo -0.63 err 5.84 games 1106 wins 339 losses 341 draws 426 finished_lines 1106
```

The point is -0.63 and the interval is about -6.47 to +5.21. It is not below -20 with the whole interval below 0, so I did not open the code a second time for a match bug. prediction.txt said Elo -6, wrong if above +20 or below -45. -0.63 is inside that range.

## Partner

Partner is seat 067, the next seat with idea 17 that had a branch at minute 75 (09:07:30Z). Seat 117 was not needed. Their idea.patch.txt applies: apply_check.txt says `partner 067 apply --check ok`, and the build of that tree produced /tmp/build-partner/forge.

Their HONESTY_P.txt claims the four honesty counts. My rerun on their binary matched those counts (HONESTY_Partner067.txt).
Their cmp_O_off.txt says DIFFER 0 of 200. My compare_partner_067_off.txt says differ 0 of 200 against exe B.
Their cmp_O_on.txt says DIFFER 0 of 200. My run of their switch-on binary matches their O_d12_P_on.nodes on all 200 positions (compare_partner_067_on_vs_theirs.txt, both sums 9500069) and also matches exe B on all 200 (compare_partner_067_on_vs_B.txt).

A 600-game match of their switch, my R.epd, both colours, from match_partner_067_summary.txt: Elo -0.58 +/- 4.09, 600 games. That is a different opening set from their 1106-game OG result (they recorded Elo -3.14 +/- 6.39 in the file I saved as their match_result claim). I am not treating those two matches as the same measurement.

Verdict: CONFIRMS. The proofs this step repeats (apply, honesty, switch off versus B's O rows, switch on versus their O rows) agree with what seat 067 recorded.

## Suspicions, not proven

The O depth-12 sum did not move with the switch on because those trees do not reach the gate. The probe shows the gate can shrink a rook-ending tree (127559 versus 136029 at depth 12), which is an earlier cutoff rather than a larger tree. I do not know whether that helps or hurts once a real game is a rook ending. The 1106-game result is too close to zero to separate those stories.

## What I did NOT do

I did not search G at depth 12 with IdeaS15 true.
I did not repeat seat 067's G comparison, their sanitizer build, or their 1106-game match.
I did not replay an opening list to add games.
There was no FABLE_TO_grok file on the handoff branch at step 1 or at minute 60 (gate_notes.txt).

## What I am NOT sure about

I required exactly one rook on each side. Seat 067's patch allows any number of rooks as long as there is no queen, bishop, or knight. Both versions leave the 200 opening searches unchanged, so this difference is not measured on O.
A rook needs 0 or 1 move to reach a file, and the pawn's next step costs 1 or 2, so that comparison accepts every rook move onto the passer file. IdeaS15_MinPieces and the rook-ending test are what actually select moves.
The match turned OwnBook off. The brief's S14 list does not mention the book.

times: see stamps.txt

## git status --short

```
 M forge-combo29/grok/017/config.json
 M forge-combo29/grok/017/stamps.txt
?? forge-combo29/grok/017/HONESTY_Partner067.txt
?? forge-combo29/grok/017/REPORT.md
?? forge-combo29/grok/017/RESULT.txt
?? forge-combo29/grok/017/apply_check.txt
?? forge-combo29/grok/017/compare_partner_067_off.txt
?? forge-combo29/grok/017/compare_partner_067_on_vs_B.txt
?? forge-combo29/grok/017/compare_partner_067_on_vs_theirs.txt
?? forge-combo29/grok/017/gate_notes.txt
?? forge-combo29/grok/017/honesty_Partner067_bench11.meta
?? forge-combo29/grok/017/honesty_Partner067_bench11.txt
?? forge-combo29/grok/017/honesty_Partner067_bench13.meta
?? forge-combo29/grok/017/honesty_Partner067_bench13.txt
?? forge-combo29/grok/017/honesty_Partner067_bench16.meta
?? forge-combo29/grok/017/honesty_Partner067_bench16.txt
?? forge-combo29/grok/017/honesty_Partner067_perft5.meta
?? forge-combo29/grok/017/honesty_Partner067_perft5.txt
?? forge-combo29/grok/017/honesty_Partner067_uci.txt
?? forge-combo29/grok/017/insert_listing.py
?? forge-combo29/grok/017/match_partner_067.log
?? forge-combo29/grok/017/match_partner_067.pgn
?? forge-combo29/grok/017/match_partner_067_summary.txt
?? forge-combo29/grok/017/partner_067.patch.txt
?? forge-combo29/grok/017/partner_067_HONESTY_P.txt
?? forge-combo29/grok/017/partner_067_O_off.nodes
?? forge-combo29/grok/017/partner_067_O_on.nodes
?? forge-combo29/grok/017/partner_067_cmp_O_off.txt
?? forge-combo29/grok/017/partner_067_cmp_O_on.txt
?? forge-combo29/grok/017/partner_measure.sh
?? forge-combo29/grok/017/partner_review.sh
?? forge-combo29/grok/017/raw_partner_067_off_O_d12.txt
?? forge-combo29/grok/017/raw_partner_067_off_O_d12.txt.err
?? forge-combo29/grok/017/raw_partner_067_off_O_d12.txt.meta
?? forge-combo29/grok/017/raw_partner_067_off_O_d12.txt.sent
?? forge-combo29/grok/017/raw_partner_067_on_O_d12.txt
?? forge-combo29/grok/017/raw_partner_067_on_O_d12.txt.err
?? forge-combo29/grok/017/raw_partner_067_on_O_d12.txt.meta
?? forge-combo29/grok/017/raw_partner_067_on_O_d12.txt.sent
?? forge-combo29/grok/017/report_numbers.py
?? forge-combo29/grok/017/report_numbers.txt
?? forge-combo29/grok/017/wait_gates.sh
```

## ls -la

```
total 5020
drwxr-xr-x 2 ubuntu ubuntu   12288 Nov 20 09:24 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:52 ..
-rw-r--r-- 1 ubuntu ubuntu      50 Nov 20 09:23 apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu      53 Nov 20 08:03 B_G_summary.txt
-rw-r--r-- 1 ubuntu ubuntu      51 Nov 20 08:03 B_O_summary.txt
-rw-r--r-- 1 ubuntu ubuntu     958 Nov 20 08:02 compare_nodes.py
-rw-r--r-- 1 ubuntu ubuntu     109 Nov 20 08:08 compare_off_G.txt
-rw-r--r-- 1 ubuntu ubuntu     107 Nov 20 08:08 compare_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu     106 Nov 20 08:08 compare_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu     117 Nov 20 09:18 compare_partner_067_off.txt
-rw-r--r-- 1 ubuntu ubuntu     116 Nov 20 09:18 compare_partner_067_on_vs_B.txt
-rw-r--r-- 1 ubuntu ubuntu      60 Nov 20 09:18 compare_partner_067_on_vs_theirs.txt
-rw-r--r-- 1 ubuntu ubuntu    7052 Nov 20 09:21 config.json
-rw-r--r-- 1 ubuntu ubuntu    1994 Nov 20 08:08 design.txt
-rw-r--r-- 1 ubuntu ubuntu      94 Nov 20 09:07 gate_notes.txt
-rw-r--r-- 1 ubuntu ubuntu   17691 Nov 20 08:01 G.epd
-rw-r--r-- 1 ubuntu ubuntu     204 Nov 20 08:00 honesty_B_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:00 honesty_B_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     204 Nov 20 08:00 honesty_B_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:00 honesty_B_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     205 Nov 20 08:00 honesty_B_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:00 honesty_B_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     207 Nov 20 08:00 honesty_B_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:00 honesty_B_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    1961 Nov 20 08:00 honesty_b.py
-rw-r--r-- 1 ubuntu ubuntu     499 Nov 20 08:00 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu    4933 Nov 20 08:00 honesty_B_uci.txt
-rw-r--r-- 1 ubuntu ubuntu    1862 Nov 20 08:04 honesty_check.py
-rw-r--r-- 1 ubuntu ubuntu     210 Nov 20 09:08 honesty_Partner067_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:08 honesty_Partner067_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     210 Nov 20 09:08 honesty_Partner067_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:08 honesty_Partner067_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     211 Nov 20 09:08 honesty_Partner067_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 09:08 honesty_Partner067_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     213 Nov 20 09:08 honesty_Partner067_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 09:08 honesty_Partner067_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     505 Nov 20 09:08 HONESTY_Partner067.txt
-rw-r--r-- 1 ubuntu ubuntu    5041 Nov 20 09:08 honesty_Partner067_uci.txt
-rw-r--r-- 1 ubuntu ubuntu     204 Nov 20 08:04 honesty_P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:04 honesty_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     204 Nov 20 08:04 honesty_P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:04 honesty_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     205 Nov 20 08:04 honesty_P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:04 honesty_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     207 Nov 20 08:04 honesty_P_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:04 honesty_P_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     499 Nov 20 08:04 HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu    5041 Nov 20 08:04 honesty_P_uci.txt
-rw-r--r-- 1 ubuntu ubuntu    7236 Nov 20 08:03 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    1235 Nov 20 09:24 insert_listing.py
-rw-r--r-- 1 ubuntu ubuntu    1370 Nov 20 08:06 make_r.py
-rw-r--r-- 1 ubuntu ubuntu  119112 Nov 20 08:15 match_OG.log
-rw-r--r-- 1 ubuntu ubuntu 1090718 Nov 20 08:15 match_OG.pgn
-rw-r--r-- 1 ubuntu ubuntu     315 Nov 20 08:16 match_OG_summary.txt
-rw-r--r-- 1 ubuntu ubuntu   69854 Nov 20 09:21 match_partner_067.log
-rw-r--r-- 1 ubuntu ubuntu  455952 Nov 20 09:21 match_partner_067.pgn
-rw-r--r-- 1 ubuntu ubuntu     317 Nov 20 09:21 match_partner_067_summary.txt
-rw-r--r-- 1 ubuntu ubuntu    1382 Nov 20 08:07 match.sh
-rw-r--r-- 1 ubuntu ubuntu   12861 Nov 20 08:01 O.fens
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:07 OG.epd
-rw-r--r-- 1 ubuntu ubuntu    1631 Nov 20 08:12 parse_match.py
-rw-r--r-- 1 ubuntu ubuntu      24 Nov 20 09:08 partner_067_cmp_O_off.txt
-rw-r--r-- 1 ubuntu ubuntu      24 Nov 20 09:08 partner_067_cmp_O_on.txt
-rw-r--r-- 1 ubuntu ubuntu     338 Nov 20 09:08 partner_067_HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu    2894 Nov 20 09:08 partner_067_O_off.nodes
-rw-r--r-- 1 ubuntu ubuntu    2894 Nov 20 09:08 partner_067_O_on.nodes
-rw-r--r-- 1 ubuntu ubuntu    6634 Nov 20 09:07 partner_067.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    2070 Nov 20 09:08 partner_measure.sh
-rwxr-xr-x 1 ubuntu ubuntu    2043 Nov 20 08:46 partner_review.sh
-rw-r--r-- 1 ubuntu ubuntu      51 Nov 20 08:08 P_on_O_summary.txt
-rw-r--r-- 1 ubuntu ubuntu     618 Nov 20 08:03 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu    1296 Nov 20 08:05 probe_off_d10.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:05 probe_off_d10.txt.err
-rw-r--r-- 1 ubuntu ubuntu     844 Nov 20 08:05 probe_off_d10.txt.meta
-rw-r--r-- 1 ubuntu ubuntu     894 Nov 20 08:05 probe_off_d10.txt.sent
-rw-r--r-- 1 ubuntu ubuntu      33 Nov 20 08:08 probe_off_d12_summary.txt
-rw-r--r-- 1 ubuntu ubuntu    1592 Nov 20 08:05 probe_off_d12.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:05 probe_off_d12.txt.err
-rw-r--r-- 1 ubuntu ubuntu     844 Nov 20 08:05 probe_off_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu     894 Nov 20 08:05 probe_off_d12.txt.sent
-rw-r--r-- 1 ubuntu ubuntu     725 Nov 20 08:05 probe_off_d6.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:05 probe_off_d6.txt.err
-rw-r--r-- 1 ubuntu ubuntu     843 Nov 20 08:05 probe_off_d6.txt.meta
-rw-r--r-- 1 ubuntu ubuntu     893 Nov 20 08:05 probe_off_d6.txt.sent
-rw-r--r-- 1 ubuntu ubuntu     987 Nov 20 08:05 probe_off_d8.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:05 probe_off_d8.txt.err
-rw-r--r-- 1 ubuntu ubuntu     843 Nov 20 08:05 probe_off_d8.txt.meta
-rw-r--r-- 1 ubuntu ubuntu     893 Nov 20 08:05 probe_off_d8.txt.sent
-rw-r--r-- 1 ubuntu ubuntu    1296 Nov 20 08:05 probe_on_d10.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:05 probe_on_d10.txt.err
-rw-r--r-- 1 ubuntu ubuntu     843 Nov 20 08:05 probe_on_d10.txt.meta
-rw-r--r-- 1 ubuntu ubuntu     893 Nov 20 08:05 probe_on_d10.txt.sent
-rw-r--r-- 1 ubuntu ubuntu      33 Nov 20 08:08 probe_on_d12_summary.txt
-rw-r--r-- 1 ubuntu ubuntu    1612 Nov 20 08:05 probe_on_d12.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:05 probe_on_d12.txt.err
-rw-r--r-- 1 ubuntu ubuntu     843 Nov 20 08:05 probe_on_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu     893 Nov 20 08:05 probe_on_d12.txt.sent
-rw-r--r-- 1 ubuntu ubuntu     725 Nov 20 08:05 probe_on_d6.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:05 probe_on_d6.txt.err
-rw-r--r-- 1 ubuntu ubuntu     842 Nov 20 08:05 probe_on_d6.txt.meta
-rw-r--r-- 1 ubuntu ubuntu     892 Nov 20 08:05 probe_on_d6.txt.sent
-rw-r--r-- 1 ubuntu ubuntu     987 Nov 20 08:05 probe_on_d8.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:05 probe_on_d8.txt.err
-rw-r--r-- 1 ubuntu ubuntu     842 Nov 20 08:05 probe_on_d8.txt.meta
-rw-r--r-- 1 ubuntu ubuntu     892 Nov 20 08:05 probe_on_d8.txt.sent
-rw-r--r-- 1 ubuntu ubuntu      46 Nov 20 08:05 probe_rook.fen
-rw-r--r-- 1 ubuntu ubuntu  114185 Nov 20 08:12 raw_asan_G100_d10.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:12 raw_asan_G100_d10.txt.err
-rw-r--r-- 1 ubuntu ubuntu     888 Nov 20 08:12 raw_asan_G100_d10.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   11004 Nov 20 08:12 raw_asan_G100_d10.txt.sent
-rw-r--r-- 1 ubuntu ubuntu     144 Nov 20 08:12 raw_asan_scratch.txt
-rw-r--r-- 1 ubuntu ubuntu     835 Nov 20 08:12 raw_asan_scratch.txt.err
-rw-r--r-- 1 ubuntu ubuntu     912 Nov 20 08:12 raw_asan_scratch.txt.meta
-rw-r--r-- 1 ubuntu ubuntu     858 Nov 20 08:12 raw_asan_scratch.txt.sent
-rw-r--r-- 1 ubuntu ubuntu  502526 Nov 20 08:02 raw_B_G_d12.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:02 raw_B_G_d12.txt.err
-rw-r--r-- 1 ubuntu ubuntu     802 Nov 20 08:02 raw_B_G_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   36800 Nov 20 08:02 raw_B_G_d12.txt.sent
-rw-r--r-- 1 ubuntu ubuntu  276977 Nov 20 08:02 raw_B_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:02 raw_B_O_d12.txt.err
-rw-r--r-- 1 ubuntu ubuntu     803 Nov 20 08:02 raw_B_O_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   24014 Nov 20 08:02 raw_B_O_d12.txt.sent
-rw-r--r-- 1 ubuntu ubuntu  277484 Nov 20 09:13 raw_partner_067_off_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 09:13 raw_partner_067_off_O_d12.txt.err
-rw-r--r-- 1 ubuntu ubuntu     895 Nov 20 09:13 raw_partner_067_off_O_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   24057 Nov 20 09:13 raw_partner_067_off_O_d12.txt.sent
-rw-r--r-- 1 ubuntu ubuntu  277584 Nov 20 09:18 raw_partner_067_on_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 09:18 raw_partner_067_on_O_d12.txt.err
-rw-r--r-- 1 ubuntu ubuntu     894 Nov 20 09:18 raw_partner_067_on_O_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   24056 Nov 20 09:18 raw_partner_067_on_O_d12.txt.sent
-rw-r--r-- 1 ubuntu ubuntu  502784 Nov 20 08:04 raw_P_off_G_d12.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:04 raw_P_off_G_d12.txt.err
-rw-r--r-- 1 ubuntu ubuntu     837 Nov 20 08:04 raw_P_off_G_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   36843 Nov 20 08:04 raw_P_off_G_d12.txt.sent
-rw-r--r-- 1 ubuntu ubuntu  276987 Nov 20 08:04 raw_P_off_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:04 raw_P_off_O_d12.txt.err
-rw-r--r-- 1 ubuntu ubuntu     838 Nov 20 08:04 raw_P_off_O_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   24057 Nov 20 08:04 raw_P_off_O_d12.txt.sent
-rw-r--r-- 1 ubuntu ubuntu  276925 Nov 20 08:04 raw_P_on_O_d12.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:04 raw_P_on_O_d12.txt.err
-rw-r--r-- 1 ubuntu ubuntu     837 Nov 20 08:04 raw_P_on_O_d12.txt.meta
-rw-r--r-- 1 ubuntu ubuntu   24056 Nov 20 08:04 raw_P_on_O_d12.txt.sent
-rw-r--r-- 1 ubuntu ubuntu     740 Nov 20 08:01 read_nodes.py
-rw-r--r-- 1 ubuntu ubuntu   19119 Nov 20 08:07 R.epd
-rw-r--r-- 1 ubuntu ubuntu   20655 Nov 20 09:24 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    3178 Nov 20 09:23 report_numbers.py
-rw-r--r-- 1 ubuntu ubuntu    4768 Nov 20 09:23 report_numbers.txt
-rw-r--r-- 1 ubuntu ubuntu     182 Nov 20 09:23 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu     620 Nov 20 08:01 s14.txt
-rw-r--r-- 1 ubuntu ubuntu      35 Nov 20 08:01 s15_off.txt
-rw-r--r-- 1 ubuntu ubuntu      34 Nov 20 08:01 s15_on.txt
-rw-r--r-- 1 ubuntu ubuntu      75 Nov 20 07:52 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu     641 Nov 20 08:07 smoke_match.log
-rw-r--r-- 1 ubuntu ubuntu    4415 Nov 20 08:07 smoke_match.pgn
-rw-r--r-- 1 ubuntu ubuntu      28 Nov 20 08:08 special_heap.fen
-rw-r--r-- 1 ubuntu ubuntu     212 Nov 20 09:23 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu    1079 Nov 20 08:04 uci_options.py
-rw-r--r-- 1 ubuntu ubuntu     166 Nov 20 08:04 uci_P.meta
-rw-r--r-- 1 ubuntu ubuntu    5041 Nov 20 08:04 uci_P.txt
-rw-r--r-- 1 ubuntu ubuntu    6514 Nov 20 08:06 uci_suite.py
-rwxr-xr-x 1 ubuntu ubuntu    1465 Nov 20 08:46 wait_gates.sh
```
