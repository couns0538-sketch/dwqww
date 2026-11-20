# Seat 046, idea 46, IdeaK7

IdeaK7 adds a correction history indexed by the last two moves (piece and destination square) to the static evaluation. The check option `IdeaK7` defaults to false. The spin option `IdeaK7_Weight` defaults to 100 (percent of the stored entry, same grain as the pawn correction). The table is a heap array of side × older piece × older square × recent piece × recent square. A missing move or a null move adds nothing and is not updated.

The patch is `idea.patch.txt`. `git apply --check` on the base worktree `/agent/repos/base` exited 0 (`apply_check.txt`).

EXISTS: no. In `src/search.cpp`, `Worker::corrected_eval` indexes the pawn key, the material key, and, when `NonPawnCorrection` is on, two non-pawn keys. It does not index the last two moves.

## Honesty numbers

Exe B and exe P, no setoption, one fresh process per line. Exe B is in `HONESTY_B.txt`. Exe P printed the same four node lines (`honesty_p_bench11.txt`, `honesty_p_bench13.txt`, `honesty_p_bench16.txt`, `honesty_p_perft5.txt`).

| command | nodes |
| --- | --- |
| bench 11 | 312866 |
| bench 13 | 862329 |
| bench 16 | 3024920 |
| go perft 5 | 4865609 |

Exe B, S14, Threads 1, Hash 16, from `sum_B_O.txt` and `sum_B_G.txt`: O depth 12 sum 9500069, first three 41311 24872 28574. G depth 12 sum 18466239.

## Steps

| step | done / partly / not done | evidence file | result |
| --- | --- | --- | --- |
| 1 seat | done | SEAT.txt | seat 046, idea 46, Grok 4.7 |
| 2 honesty and base sums | done | HONESTY_B.txt, sum_B_O.txt, sum_B_G.txt | honesty matches; O 9500069; G 18466239 |
| 3a read | done | design.txt | EXISTS no |
| 3b prediction | done | prediction.txt | 10800000 and +5, pushed before the on measurement |
| 3c patch | done | idea.patch.txt, apply_check.txt | apply_exit 0 |
| 3d proofs | done | compare_Poff_O.txt, compare_Poff_G.txt, compare_Pon_O.txt, uci_ideak7.txt, asan_G100_d10.meta, asan_bug.raw.txt | off identical; on 200 of 200; sanitizer clean |
| 3e match | done | match_result.txt, match_k7.log, match_k7.pgn | Elo 2.20 +/- 10.29, 1106 games |
| 4 partner | not done | partner_seats.txt, match_r_result.txt | no other idea-46 branch; second match played instead |
| 5 report | done | REPORT.md, RESULT.txt, stamps.txt | this file |

## Proofs

(1) Exe P with no setoption: bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, perft 5 nodes 4865609.

(2) S14 and `IdeaK7` false. `compare_Poff_O.txt`: positions 200, node_diff 0, move_diff 0. `compare_Poff_G.txt`: positions 353, node_diff 0, move_diff 0. Sums in `sum_Poff_O.txt` and `sum_Poff_G.txt` are 9500069 and 18466239.

(3) S14 and `IdeaK7` true, weight 100. `compare_Pon_O.txt`: node_diff 200, move_diff 50, of 200 positions. `sum_Pon_O.txt`: sum 9717843. That is inside the prediction's wrong-range (below 7000000 or above 15000000).

(4) `uci_ideak7.txt`:

```
option name IdeaK7 type check default false
option name IdeaK7_Weight type spin default 100 min 0 max 400
```

(5) AddressSanitizer and UndefinedBehaviorSanitizer build of `../work`. `asan_G100_d10.meta` has `nm_asan_count=35`. First 100 of G at depth 10 with the switch on: `asan_clean_grep.txt` is 0 matches for ERROR, SUMMARY, or runtime error. A scratch copy with one read past the end of a 4-int heap array, on the FEN in `asan_bug.fen`, run through `measure_set.py`, reports in `asan_bug.raw.txt`: `AddressSanitizer: heap-buffer-overflow` and a UBSan runtime error in `corrected_eval`.

## Match

`extract_match.py` on `match_k7.log` (`match_result.txt`):

```
Elo: 2.20 +/- 10.29, nElo: 4.38 +/- 20.48
LOS: 66.24 %, DrawRatio: 62.03 %, PairsRatio: 1.06
Games: 1106, Wins: 349, Losses: 342, Draws: 415, Points: 556.5 (50.32 %)
```

PGN `match_k7.pgn`: 1106 result tags, 553 with White K7on and 553 with White K7off. The interval is not entirely below 0, so the code was not re-opened for a mistake. The prediction (+5, wrong only if the interval lies entirely below -20 or entirely above +30) is not proved wrong.

## Partner

Seats for idea 46 are 046, 096, and 146. 146 is outside 001..120. `git ls-remote` at 2026-11-20T09:08:55Z, 2026-11-20T09:14:04Z, and 2026-11-20T09:19:14Z showed only `for-fable-and-opus/grok-046`. The final check is `partner_seats.txt`. There is no partner. No partner patch was applied, built, or played.

Second match of this patch, 300 R openings, both colours, 600 games (`match_r_result.txt`):

```
Elo: -6.95 +/- 9.87, nElo: -19.59 +/- 27.80
LOS: 8.37 %, DrawRatio: 85.67 %, PairsRatio: 0.72
Games: 600, Wins: 267, Losses: 279, Draws: 54, Points: 294.0 (49.00 %)
```

`match_r.pgn` has 600 result tags, 300 each way. partner_verdict is not done.

## Suspicions, not proven

The R match's DrawRatio is 85.67% while the Games line says 54 draws out of 600. I did not look up which statistic fastchess calls DrawRatio. I am not treating that line as a fault in the engine.

`make_r.py` kept 30 games out of 30 tries to reach ply 80. I did not replay those games by hand.

## What I did NOT do

I did not review a partner patch. I did not measure G at depth 12 with the switch on. I did not run the main match under a sanitizer. The minute-60 fetch of `handoff/fable-opus-combo29-all-20261114` listed no `FABLE_TO_grok_*.md`. No pull request.

## What I am NOT sure about

Whether a smaller hashed table would have changed the match. The full table is what ran. The main-match Elo interval includes both negative and positive values, so this is not a strength result. The prediction's point (10800000 nodes, +5 Elo) is not the measured point (9717843 nodes, +2.20 Elo); both sit inside the ranges written in `prediction.txt`.

## times: see stamps.txt

## git status --short and ls -la

The pasted output follows.

```
$ git status --short
 M forge-combo29/grok/046/stamps.txt
?? config.json
?? forge-combo29/grok/046/REPORT.md
?? forge-combo29/grok/046/RESULT.txt
?? forge-combo29/grok/046/apply_check.txt
?? forge-combo29/grok/046/asan_clean_grep.txt
?? forge-combo29/grok/046/match_r.log
?? forge-combo29/grok/046/match_r.pgn
?? forge-combo29/grok/046/match_r_result.txt
?? forge-combo29/grok/046/partner_seats.sh
?? forge-combo29/grok/046/partner_seats.txt
?? forge-combo29/grok/046/run_match_r.sh
?? forge-combo29/grok/046/sum_B_G.txt
?? forge-combo29/grok/046/sum_B_O.txt
?? forge-combo29/grok/046/sum_Poff_G.txt
?? forge-combo29/grok/046/sum_Poff_O.txt

$ ls -la forge-combo29/grok/046
total 4336
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 09:23 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:53 ..
-rw-r--r-- 1 ubuntu ubuntu      13 Nov 20 09:22 apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu      32 Nov 20 08:08 asan_bug.fen
-rw-r--r-- 1 ubuntu ubuntu    1054 Nov 20 08:09 asan_bug.meta
-rw-r--r-- 1 ubuntu ubuntu    1689 Nov 20 08:09 asan_bug_meta.py
-rw-r--r-- 1 ubuntu ubuntu   12741 Nov 20 08:08 asan_bug.raw.txt
-rw-r--r-- 1 ubuntu ubuntu      14 Nov 20 09:23 asan_clean_grep.txt
-rw-r--r-- 1 ubuntu ubuntu     962 Nov 20 08:07 asan_G100_d10.meta
-rw-r--r-- 1 ubuntu ubuntu  134136 Nov 20 08:07 asan_G100_d10.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    6410 Nov 20 08:07 asan_G100_d10.tsv
-rw-r--r-- 1 ubuntu ubuntu     458 Nov 20 08:07 asan_nm.py
-rw-r--r-- 1 ubuntu ubuntu     809 Nov 20 08:02 B_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  558563 Nov 20 08:02 B_G_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu   22915 Nov 20 08:02 B_G_d12.tsv
-rw-r--r-- 1 ubuntu ubuntu     809 Nov 20 08:02 B_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  314093 Nov 20 08:02 B_O_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu   15782 Nov 20 08:02 B_O_d12.tsv
-rw-r--r-- 1 ubuntu ubuntu     143 Nov 20 08:06 compare_Poff_G.txt
-rw-r--r-- 1 ubuntu ubuntu     143 Nov 20 08:06 compare_Poff_O.txt
-rw-r--r-- 1 ubuntu ubuntu     145 Nov 20 08:06 compare_Pon_O.txt
-rw-r--r-- 1 ubuntu ubuntu    1021 Nov 20 08:03 compare_tsv.py
-rw-r--r-- 1 ubuntu ubuntu    1348 Nov 20 08:07 design.txt
-rw-r--r-- 1 ubuntu ubuntu     687 Nov 20 08:10 extract_match.py
-rw-r--r-- 1 ubuntu ubuntu   12861 Nov 20 08:02 first200.fens
-rw-r--r-- 1 ubuntu ubuntu     195 Nov 20 07:59 honesty_b_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 07:59 honesty_b_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     195 Nov 20 08:00 honesty_b_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:00 honesty_b_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     195 Nov 20 08:00 honesty_b_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:00 honesty_b_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    4933 Nov 20 07:59 honesty_b_id.txt
-rw-r--r-- 1 ubuntu ubuntu     197 Nov 20 08:00 honesty_b_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:00 honesty_b_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    1544 Nov 20 07:59 honesty_b.py
-rw-r--r-- 1 ubuntu ubuntu     538 Nov 20 08:02 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu     195 Nov 20 08:04 honesty_p_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:04 honesty_p_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     195 Nov 20 08:04 honesty_p_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:04 honesty_p_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     195 Nov 20 08:04 honesty_p_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:04 honesty_p_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    5039 Nov 20 08:04 honesty_p_id.txt
-rw-r--r-- 1 ubuntu ubuntu    1543 Nov 20 08:04 honesty_plain.py
-rw-r--r-- 1 ubuntu ubuntu     197 Nov 20 08:04 honesty_p_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:04 honesty_p_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu   13149 Nov 20 08:02 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    1342 Nov 20 08:09 make_r.py
-rw-r--r-- 1 ubuntu ubuntu  114565 Nov 20 08:14 match_k7.log
-rw-r--r-- 1 ubuntu ubuntu 1066928 Nov 20 08:14 match_k7.pgn
-rw-r--r-- 1 ubuntu ubuntu     734 Nov 20 08:15 match_result.txt
-rw-r--r-- 1 ubuntu ubuntu   57965 Nov 20 09:22 match_r.log
-rw-r--r-- 1 ubuntu ubuntu  461735 Nov 20 09:22 match_r.pgn
-rw-r--r-- 1 ubuntu ubuntu     718 Nov 20 09:22 match_r_result.txt
-rw-r--r-- 1 ubuntu ubuntu    6495 Nov 20 08:02 measure_set.py
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:07 openings_OG.epd
-rw-r--r-- 1 ubuntu ubuntu     361 Nov 20 08:15 partner_seats.sh
-rw-r--r-- 1 ubuntu ubuntu     105 Nov 20 09:22 partner_seats.txt
-rw-r--r-- 1 ubuntu ubuntu     842 Nov 20 08:04 Poff_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  558891 Nov 20 08:04 Poff_G_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu   22915 Nov 20 08:04 Poff_G_d12.tsv
-rw-r--r-- 1 ubuntu ubuntu     842 Nov 20 08:04 Poff_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  314134 Nov 20 08:04 Poff_O_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu   15782 Nov 20 08:04 Poff_O_d12.tsv
-rw-r--r-- 1 ubuntu ubuntu     879 Nov 20 08:05 Pon_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  313914 Nov 20 08:05 Pon_O_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu   15780 Nov 20 08:05 Pon_O_d12.tsv
-rw-r--r-- 1 ubuntu ubuntu     584 Nov 20 08:05 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu    6400 Nov 20 09:23 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu     187 Nov 20 09:23 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu   19168 Nov 20 08:09 R.fen
-rw-r--r-- 1 ubuntu ubuntu    1407 Nov 20 09:19 run_match_r.sh
-rw-r--r-- 1 ubuntu ubuntu    1435 Nov 20 08:07 run_match.sh
-rw-r--r-- 1 ubuntu ubuntu      78 Nov 20 07:53 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu   17691 Nov 20 08:02 set_G.epd
-rw-r--r-- 1 ubuntu ubuntu     140 Nov 20 09:22 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu      70 Nov 20 09:23 sum_B_G.txt
-rw-r--r-- 1 ubuntu ubuntu      68 Nov 20 09:23 sum_B_O.txt
-rw-r--r-- 1 ubuntu ubuntu      73 Nov 20 09:23 sum_Poff_G.txt
-rw-r--r-- 1 ubuntu ubuntu      71 Nov 20 09:23 sum_Poff_O.txt
-rw-r--r-- 1 ubuntu ubuntu      70 Nov 20 08:06 sum_Pon_O.txt
-rw-r--r-- 1 ubuntu ubuntu     568 Nov 20 08:03 sum_tsv.py
-rw-r--r-- 1 ubuntu ubuntu     106 Nov 20 08:06 uci_ideak7.txt
-rw-r--r-- 1 ubuntu ubuntu     159 Nov 20 08:06 uci_options.meta
-rw-r--r-- 1 ubuntu ubuntu     864 Nov 20 08:05 uci_options.py
-rw-r--r-- 1 ubuntu ubuntu    5039 Nov 20 08:06 uci_options.txt
-rw-r--r-- 1 ubuntu ubuntu     491 Nov 20 08:01 write_honesty_b.py
```
