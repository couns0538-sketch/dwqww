# Seat 064

The printed idea is 14. On the list, idea 14 is S5 (nothing useful to play). I built S6 (the idle piece) instead. That is a mistake in reading the list. Everything below is the S6 patch that was actually built and measured. Seat 014, the partner, built S5.

IdeaS6 is a check, default false. At remaining depth IdeaS6_Depth (default 4), on a quiet node, the friendly non-king piece whose removal changes the network evaluation least has its quiet moves searched one ply deeper, once. IdeaS6_Margin (default 120) is the SEE band for "quiet".

EXISTS: no. src/search.cpp has no idle-piece probe.

## Honesty

exe B and exe P, no setoption. HONESTY_B.txt and HONESTY_P.txt.

```
bench11 nodes 312866
bench13 nodes 862329
bench16 nodes 3024920
perft5 nodes 4865609
```

Both builds match. exe B also reproduced S14 O depth 12 = 9500069 (first three 41311 24872 28574) and G depth 12 = 18466239. B_SUMS.txt.

## Steps

| step | status | evidence | result |
| --- | --- | --- | --- |
| 1 seat | done | SEAT.txt stamps.txt | 064 idea 14 |
| 2 honesty and known sums | done | HONESTY_B.txt B_SUMS.txt | pins match, O 9500069, G 18466239 |
| 3a read | done | DECISIONS.txt | built S6, not the list's S5 |
| 3b prediction | done | prediction.txt | 11200000 and +8, committed before measuring P |
| 3c patch | done | idea.patch.txt | git apply --check passed |
| 3d proofs | done | P_SUMS.txt CMP_*.txt HONESTY_P.txt asan_G100.* asan_bad.err | see below |
| 3e match | done | match_summary.txt match.pgn | 1106 games, Elo -8.17 +/- 10.54 |
| 4 partner | done | partner_verdict.txt | 014 CONFIRMS |
| 5 report | done | REPORT.md RESULT.txt | this file |

## Proofs

(1) Honesty with no setoption: unchanged, numbers above. HONESTY_P.txt.

(2) S14, IdeaS6 false. O depth 12 differ 0 of 200, sum 9500069. G depth 12 differ 0 of 353, sum 18466239. CMP_off_O.txt CMP_off_G.txt.

(3) S14, IdeaS6 true. O depth 12 sum 9749922, first three 43634 25742 47791. Differ 200 of 200 versus exe B. CMP_on_O.txt P_SUMS.txt. Prediction was 11200000, wrong outside 8000000..16000000. 9749922 is inside that range.

(4) uci lists `option name IdeaS6 type check default false`, `IdeaS6_Depth` spin default 4 min 2 max 16, `IdeaS6_Margin` spin default 120 min 0 max 1000. uci_options.txt.

(5) AddressSanitizer + UBSan build, `nm -C` count of `__asan_` is 37. First 100 of G at depth 10, IdeaS6 true, stderr empty, sum 2007877. asan_G100.err asan_G100.meta. A scratch copy with one read past a 4-int heap array, on the FEN `4k3/8/8/8/8/4P3/8/4K3 w - - 0 1`, run through depth_sum.py, reports `runtime error: load of address ... with insufficient space for an object of type 'int'`. asan_bad.err. Leak detection was off.

## Match

IdeaS6 true versus IdeaS6 false, both S14, Threads 1, Hash 16, 20000 nodes, openings O then G, both colours. parse_match.py on match_stdout.txt:

```
Elo: -8.17 +/- 10.54, nElo: -15.87 +/- 20.48
LOS: 6.43 %, DrawRatio: 62.57 %, PairsRatio: 0.78
Games: 1106, Wins: 325, Losses: 351, Draws: 430, Points: 540.0 (48.82 %)
```

Prediction was +8, wrong if the point estimate is below -30 or above +45. -8.17 is inside that range. The interval is not entirely below 0, and the point is not below -20, so the brief's "look once" rule did not apply. The infinite-depth bug in an earlier extra-ply version was found and fixed before this match. match.pgn has 1106 Result tags.

## Partner

Seat 014. Verdict CONFIRMS. Their IdeaS5 patch applies, honesty matches, IdeaS5 false matches exe B on O (0 of 200), IdeaS5 true matches their own O rows (0 of 200 differ, sum 9620456). A 600-game match of their switch on 300 R openings: Elo -2.90 +/- 8.86. partner_verdict.txt partner_match_summary.txt.

## Suspicions, not proven

The negative point estimate may be the extra ply being spent on a piece that is idle because it is bad, not because it needs a plan. Not shown.

Draws by the fifty-move rule and threefold repetition in the match are legal results.

## What I did NOT do

I did not build S5, which is idea 14 on the list. I did not re-run the partner's 1106-game match or their sanitizer. I did not play a second match of IdeaS6 on the R set. No FABLE_TO_grok file was on the handoff branch at the minute-60 fetch.

## What I am NOT sure about

Whether one extra ply, rather than only clearing a reduction that never applied, is the change the S6 text wants. The reduction clear is still in the patch. It did not by itself change a node. See DECISIONS.txt.

## times: see stamps.txt
## git status --short
 M forge-combo29/grok/064/config.json
 M forge-combo29/grok/064/stamps.txt
?? forge-combo29/grok/064/HONESTY_partner.txt
?? forge-combo29/grok/064/REPORT.md
?? forge-combo29/grok/064/RESULT.txt
?? forge-combo29/grok/064/honesty_partner_bench11.err
?? forge-combo29/grok/064/honesty_partner_bench11.meta
?? forge-combo29/grok/064/honesty_partner_bench11.txt
?? forge-combo29/grok/064/honesty_partner_bench13.err
?? forge-combo29/grok/064/honesty_partner_bench13.meta
?? forge-combo29/grok/064/honesty_partner_bench13.txt
?? forge-combo29/grok/064/honesty_partner_bench16.err
?? forge-combo29/grok/064/honesty_partner_bench16.meta
?? forge-combo29/grok/064/honesty_partner_bench16.txt
?? forge-combo29/grok/064/honesty_partner_perft5.err
?? forge-combo29/grok/064/honesty_partner_perft5.meta
?? forge-combo29/grok/064/honesty_partner_perft5.txt
?? forge-combo29/grok/064/partner014_O_on.nodes.txt
?? forge-combo29/grok/064/partner014_idea.patch.txt
?? forge-combo29/grok/064/partner_CMP_off.txt
?? forge-combo29/grok/064/partner_CMP_on.txt
?? forge-combo29/grok/064/partner_R300.fens
?? forge-combo29/grok/064/partner_SUMS.txt
?? forge-combo29/grok/064/partner_match.pgn
?? forge-combo29/grok/064/partner_match.sh
?? forge-combo29/grok/064/partner_match_stderr.txt
?? forge-combo29/grok/064/partner_match_stdout.txt
?? forge-combo29/grok/064/partner_match_summary.txt
?? forge-combo29/grok/064/partner_off_O.err
?? forge-combo29/grok/064/partner_off_O.meta
?? forge-combo29/grok/064/partner_off_O.nodes.txt
?? forge-combo29/grok/064/partner_off_O.raw.txt
?? forge-combo29/grok/064/partner_on_O.err
?? forge-combo29/grok/064/partner_on_O.meta
?? forge-combo29/grok/064/partner_on_O.nodes.txt
?? forge-combo29/grok/064/partner_on_O.raw.txt
?? forge-combo29/grok/064/partner_verdict.txt

## ls -la
total 8760
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 09:16 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:54 ..
-rw-r--r-- 1 ubuntu ubuntu    1589 Nov 20 08:29 asan_bad.err
-rw-r--r-- 1 ubuntu ubuntu     438 Nov 20 08:30 asan_bad.meta
-rw-r--r-- 1 ubuntu ubuntu    6575 Nov 20 08:29 asan_bad.raw.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:28 asan_G100.err
-rw-r--r-- 1 ubuntu ubuntu     998 Nov 20 08:28 asan_G100.meta
-rw-r--r-- 1 ubuntu ubuntu    6381 Nov 20 08:28 asan_G100.nodes.txt
-rw-r--r-- 1 ubuntu ubuntu  136402 Nov 20 08:28 asan_G100.raw.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:06 B_G.err
-rw-r--r-- 1 ubuntu ubuntu     845 Nov 20 08:06 B_G.meta
-rw-r--r-- 1 ubuntu ubuntu   22890 Nov 20 08:06 B_G.nodes.txt
-rw-r--r-- 1 ubuntu ubuntu  565930 Nov 20 08:06 B_G.raw.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:06 B_O.err
-rw-r--r-- 1 ubuntu ubuntu     846 Nov 20 08:06 B_O.meta
-rw-r--r-- 1 ubuntu ubuntu   15757 Nov 20 08:06 B_O.nodes.txt
-rw-r--r-- 1 ubuntu ubuntu  318259 Nov 20 08:06 B_O.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     132 Nov 20 08:07 B_SUMS.txt
-rw-r--r-- 1 ubuntu ubuntu      32 Nov 20 08:27 CMP_off_G.txt
-rw-r--r-- 1 ubuntu ubuntu      32 Nov 20 08:27 CMP_off_O.txt
-rw-r--r-- 1 ubuntu ubuntu      32 Nov 20 08:27 CMP_on_O.txt
-rw-r--r-- 1 ubuntu ubuntu     991 Nov 20 08:08 compare_nodes.py
-rw-r--r-- 1 ubuntu ubuntu    7132 Nov 20 09:15 config.json
-rw-r--r-- 1 ubuntu ubuntu    2774 Nov 20 08:30 DECISIONS.txt
-rw-r--r-- 1 ubuntu ubuntu    6519 Nov 20 08:20 depth_sum.py
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:03 honesty_b_bench11.err
-rw-r--r-- 1 ubuntu ubuntu     206 Nov 20 08:03 honesty_b_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu    4994 Nov 20 08:03 honesty_b_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:03 honesty_b_bench13.err
-rw-r--r-- 1 ubuntu ubuntu     206 Nov 20 08:03 honesty_b_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu    4994 Nov 20 08:03 honesty_b_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:03 honesty_b_bench16.err
-rw-r--r-- 1 ubuntu ubuntu     206 Nov 20 08:03 honesty_b_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu    4996 Nov 20 08:03 honesty_b_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:03 honesty_b_perft5.err
-rw-r--r-- 1 ubuntu ubuntu     208 Nov 20 08:03 honesty_b_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    5207 Nov 20 08:03 honesty_b_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    2604 Nov 20 08:02 honesty_b.py
-rw-r--r-- 1 ubuntu ubuntu     275 Nov 20 08:03 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu    2348 Nov 20 08:07 honesty_exe.py
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 09:12 honesty_partner_bench11.err
-rw-r--r-- 1 ubuntu ubuntu     204 Nov 20 09:12 honesty_partner_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu    5282 Nov 20 09:12 honesty_partner_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 09:12 honesty_partner_bench13.err
-rw-r--r-- 1 ubuntu ubuntu     204 Nov 20 09:12 honesty_partner_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu    5282 Nov 20 09:12 honesty_partner_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 09:12 honesty_partner_bench16.err
-rw-r--r-- 1 ubuntu ubuntu     204 Nov 20 09:12 honesty_partner_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu    5284 Nov 20 09:12 honesty_partner_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 09:12 honesty_partner_perft5.err
-rw-r--r-- 1 ubuntu ubuntu     206 Nov 20 09:12 honesty_partner_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    5495 Nov 20 09:12 honesty_partner_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     273 Nov 20 09:12 HONESTY_partner.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:27 honesty_P_bench11.err
-rw-r--r-- 1 ubuntu ubuntu     206 Nov 20 08:27 honesty_P_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu    5159 Nov 20 08:27 honesty_P_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:27 honesty_P_bench13.err
-rw-r--r-- 1 ubuntu ubuntu     206 Nov 20 08:27 honesty_P_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu    5159 Nov 20 08:27 honesty_P_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:27 honesty_P_bench16.err
-rw-r--r-- 1 ubuntu ubuntu     206 Nov 20 08:27 honesty_P_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu    5161 Nov 20 08:27 honesty_P_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:27 honesty_P_perft5.err
-rw-r--r-- 1 ubuntu ubuntu     208 Nov 20 08:27 honesty_P_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu    5372 Nov 20 08:27 honesty_P_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     275 Nov 20 08:27 HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu   10915 Nov 20 08:30 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    1357 Nov 20 08:06 make_r.py
-rw-r--r-- 1 ubuntu ubuntu 3690361 Nov 20 08:37 match.pgn
-rwxr-xr-x 1 ubuntu ubuntu    1243 Nov 20 08:30 match.sh
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:30 match_stderr.txt
-rw-r--r-- 1 ubuntu ubuntu  132664 Nov 20 08:37 match_stdout.txt
-rw-r--r-- 1 ubuntu ubuntu     288 Nov 20 08:38 match_summary.txt
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:28 OG.epd
-rw-r--r-- 1 ubuntu ubuntu     487 Nov 20 08:38 parse_match.py
-rw-r--r-- 1 ubuntu ubuntu   12614 Nov 20 09:12 partner014_idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu   15766 Nov 20 09:12 partner014_O_on.nodes.txt
-rw-r--r-- 1 ubuntu ubuntu      32 Nov 20 09:12 partner_CMP_off.txt
-rw-r--r-- 1 ubuntu ubuntu      92 Nov 20 09:12 partner_CMP_on.txt
-rw-r--r-- 1 ubuntu ubuntu 1568861 Nov 20 09:15 partner_match.pgn
-rw-r--r-- 1 ubuntu ubuntu    1271 Nov 20 09:13 partner_match.sh
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 09:13 partner_match_stderr.txt
-rw-r--r-- 1 ubuntu ubuntu   68152 Nov 20 09:15 partner_match_stdout.txt
-rw-r--r-- 1 ubuntu ubuntu     294 Nov 20 09:16 partner_match_summary.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 09:12 partner_off_O.err
-rw-r--r-- 1 ubuntu ubuntu     878 Nov 20 09:12 partner_off_O.meta
-rw-r--r-- 1 ubuntu ubuntu   15757 Nov 20 09:12 partner_off_O.nodes.txt
-rw-r--r-- 1 ubuntu ubuntu  318572 Nov 20 09:12 partner_off_O.raw.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 09:12 partner_on_O.err
-rw-r--r-- 1 ubuntu ubuntu     877 Nov 20 09:12 partner_on_O.meta
-rw-r--r-- 1 ubuntu ubuntu   15754 Nov 20 09:12 partner_on_O.nodes.txt
-rw-r--r-- 1 ubuntu ubuntu  318891 Nov 20 09:12 partner_on_O.raw.txt
-rw-r--r-- 1 ubuntu ubuntu   19138 Nov 20 09:13 partner_R300.fens
-rw-r--r-- 1 ubuntu ubuntu     149 Nov 20 09:12 partner_SUMS.txt
-rw-r--r-- 1 ubuntu ubuntu     917 Nov 20 09:16 partner_verdict.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:27 P_off_G.err
-rw-r--r-- 1 ubuntu ubuntu     879 Nov 20 08:27 P_off_G.meta
-rw-r--r-- 1 ubuntu ubuntu   22890 Nov 20 08:27 P_off_G.nodes.txt
-rw-r--r-- 1 ubuntu ubuntu  566757 Nov 20 08:27 P_off_G.raw.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:27 P_off_O.err
-rw-r--r-- 1 ubuntu ubuntu     880 Nov 20 08:27 P_off_O.meta
-rw-r--r-- 1 ubuntu ubuntu   15757 Nov 20 08:27 P_off_O.nodes.txt
-rw-r--r-- 1 ubuntu ubuntu  318769 Nov 20 08:27 P_off_O.raw.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:27 P_on_O.err
-rw-r--r-- 1 ubuntu ubuntu     879 Nov 20 08:27 P_on_O.meta
-rw-r--r-- 1 ubuntu ubuntu   15755 Nov 20 08:27 P_on_O.nodes.txt
-rw-r--r-- 1 ubuntu ubuntu  320033 Nov 20 08:27 P_on_O.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     246 Nov 20 08:07 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu     786 Nov 20 08:07 print_nodes.py
-rw-r--r-- 1 ubuntu ubuntu     208 Nov 20 08:27 P_SUMS.txt
-rw-r--r-- 1 ubuntu ubuntu    6305 Nov 20 09:16 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu     183 Nov 20 09:16 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu   25464 Nov 20 08:07 R.fens
-rw-r--r-- 1 ubuntu ubuntu      77 Nov 20 07:54 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu     112 Nov 20 09:16 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu    5098 Nov 20 08:30 uci_options.txt
