# Seat 072, idea 22, S27

Idea S27 is a veto on quiet history. When the previous-move continuation and the threat-role entry have opposite signs outside a dead zone, the score keeps only the from-to history.
I added the check option IdeaS27, default false, and the spin IdeaS27_DeadZone, default 64 (range 0 to 8192).
While IdeaS27 is on, quiet updates also write the threat-role table, because under S14 that table would otherwise stay zero. While it is off, the score and the update guard are the old ones. Decisions are in decisions.txt.

EXISTS: no. ThreatHistory in search.cpp is the B8 table. Nothing in the plain engine drops both context terms when their signs disagree.

## Honesty

Exe B and exe P, no setoption. Output of report_tables.py, which reads the raw bench and perft files:

```
HONESTY_B
honesty_b_bench11 312866 expected 312866 OK
honesty_b_bench13 862329 expected 862329 OK
honesty_b_bench16 3024920 expected 3024920 OK
honesty_b_perft5 4865609 expected 4865609 OK
HONESTY_P
honesty_p_bench11 312866 expected 312866 OK
honesty_p_bench13 862329 expected 862329 OK
honesty_p_bench16 3024920 expected 3024920 OK
honesty_p_perft5 4865609 expected 4865609 OK
```

Exe B, S14, Threads 1, Hash 16, depth 12, same script:

```
B_O positions 200 sum 9500069 first3 41311 24872 28574
B_G positions 353 sum 18466239 first3 37203 70845 144383
```

## Steps

Pasted from report_tables.py (STEP_TABLE). The script checks the raw files for the sums and the differ counts.

```
step | status | evidence | result
1 seat | done | SEAT.txt stamps.txt | seat 072 idea 22
2 honesty B | done | HONESTY_B.txt | PASS 312866 862329 3024920 4865609
2 O and G sums | done | B_O_d12.raw.txt B_G_d12.raw.txt | O 9500069 G 18466239
3 prediction | done | prediction.txt | committed before exe P searches
3 patch applies | done | apply_check.txt idea.patch.txt | APPLY_CHECK_OK
3 proof off | done | P_off_O_d12.raw.txt P_off_G_d12.raw.txt | O differ 0 G differ 0
3 proof on | done | P_on_O_d12.raw.txt | differ 200 of 200 sum 9671966
3 uci options | done | uci_p.txt | IdeaS27 false, IdeaS27_DeadZone 64
3 sanitizer | done | asan_G100_d10.err.txt asan_probe.err.txt | nm 35 stderr 0 probe yes
3 match | done | match_og.log match_og.pgn | see MATCH lines above
4 partner | done | partner_proofs.txt partner_match_r.log | CONFIRMS off 0 on equal 600 games
```

## Proofs

(1) Honesty, no setoption: the four numbers above, on exe P as well as exe B.

(2) S14 and IdeaS27 false. O depth 12 differs from exe B in 0 of 200. G depth 12 differs in 0 of 353.

(3) S14 and IdeaS27 true. O depth 12 differs from exe B in 200 of 200. The sum is 9671966. Prediction was 10200000, wrong outside 7500000 to 13500000, so the sum does not falsify it.

(4) `uci` lists `option name IdeaS27 type check default false` and `option name IdeaS27_DeadZone type spin default 64 min 0 max 8192`.

(5) AddressSanitizer and UndefinedBehaviorSanitizer build, IdeaS27 true, first 100 of G at depth 10: 100 positions, stderr length 0. `nm -C` count of `__asan_` is 35, stored as nm_asan_count in asan_G100_d10.meta. A scratch copy with one read past the end of a 4-int heap array, on the FEN in probe.fen, run through search_set.py, printed `ERROR: AddressSanitizer: heap-buffer-overflow`. That stderr is asan_probe.err.txt.

idea.patch.txt applies to a fresh checkout of 6b98f2170a3210e71beed04bbd2553972c253ed7. apply_check.txt says APPLY_CHECK_OK.

## Match

Exe P with IdeaS27 true against exe P with IdeaS27 false. S14, Threads 1, Hash 16, 20000 nodes, openings O then G (553), both colours, 1106 games. fastchess from github.com/Disservin/fastchess. Final lines of match_og.log, as printed by report_tables.py:

```
Elo: -8.48 +/- 10.67, nElo: -16.29 +/- 20.48
Games: 1106, Wins: 324, Losses: 351, Draws: 431, Points: 539.5 (48.78 %)
```

Prediction was +3 Elo, wrong below -35 or above +45. -8.48 is inside that range. The point is not below -20, and the interval is not entirely below 0, so I did not go back and change the code.

## Partner

Partner is seat 022 (same idea, the next seat after 072 that has a branch). Fetched for-fable-and-opus/grok-022 at 41a9eeec99fdab01fe4d1dd95ebe99274de325e8. The tip was the same again at 2026-11-20T09:02:20Z. Their patch applies on a fresh base (partner_apply_check.txt). Their build's honesty numbers match. IdeaS27 false matches exe B on O depth 12, 0 of 200. IdeaS27 true matches their o_p_on_d12.nodes, 0 of 200 different, sum 9605430, and differs from exe B in 200 of 200, which is what their proof_compare.txt says. My R match of their switch, 300 openings, both colours, 600 games:

```
Elo: 5.21 +/- 9.41, nElo: 15.40 +/- 27.80
Games: 600, Wins: 274, Losses: 265, Draws: 61, Points: 304.5 (50.75 %)
```

Verdict: CONFIRMS. I did not replay their 1106-game O+G match, and I did not remeasure their G off rows. The proofs the brief lists for the partner all matched their files.

## Suspicions, not proven

The match interval is about -19.2 to +2.2. A small loss is possible and a small gain is possible. I am not calling the idea bad from this net.

Many games ended by threefold repetition, the fifty-move rule, or insufficient material. Those are legal draws.

Seat 022 adds the threat-role value on the non-veto path even when ThreatHistory is off. My patch adds it only when ThreatHistory is on, and only drops terms on a veto. Both patches change all 200 positions. I do not know which reading Opus will prefer.

## What I did NOT do

I did not replay the partner's 1106-game match. I did not remeasure the partner's G depth-12 off rows. I did not turn ThreatHistory on in the measured searches. I did not edit prediction.txt after the prediction commit. I started the partner check at 2026-11-20T08:55:03Z, after the minute-60 handoff, rather than waiting until minute 75. Their branch already held idea.patch.txt, and the tip did not move before I finished.

## What I am NOT sure about

Whether dead zone 64 is a good width. Whether "as usual" should add the threat-role value when ThreatHistory is off. The built-in net is only a first look.

There was no FABLE_TO_grok file on the handoff branch at step 1 or at minute 60.

times: see stamps.txt

## git status and folder listing

The listing below was taken after every evidence file existed, and it is pasted after that command.
```
$ git status --short
 M forge-combo29/grok/072/stamps.txt
?? forge-combo29/grok/072/PARTNER_HONESTY.txt
?? forge-combo29/grok/072/REPORT.md
?? forge-combo29/grok/072/RESULT.txt
?? forge-combo29/grok/072/compare_partner_on.py
?? forge-combo29/grok/072/partner_apply_check.txt
?? forge-combo29/grok/072/partner_bench11.meta
?? forge-combo29/grok/072/partner_bench11.txt
?? forge-combo29/grok/072/partner_bench13.meta
?? forge-combo29/grok/072/partner_bench13.txt
?? forge-combo29/grok/072/partner_bench16.meta
?? forge-combo29/grok/072/partner_bench16.txt
?? forge-combo29/grok/072/partner_honesty.sh
?? forge-combo29/grok/072/partner_idea.patch.txt
?? forge-combo29/grok/072/partner_match_r.log
?? forge-combo29/grok/072/partner_match_r.pgn
?? forge-combo29/grok/072/partner_match_summary.txt
?? forge-combo29/grok/072/partner_o_on.nodes
?? forge-combo29/grok/072/partner_off_O_d12.err.txt
?? forge-combo29/grok/072/partner_off_O_d12.meta
?? forge-combo29/grok/072/partner_off_O_d12.raw.txt
?? forge-combo29/grok/072/partner_on_O_d12.err.txt
?? forge-combo29/grok/072/partner_on_O_d12.meta
?? forge-combo29/grok/072/partner_on_O_d12.raw.txt
?? forge-combo29/grok/072/partner_perft5.meta
?? forge-combo29/grok/072/partner_perft5.txt
?? forge-combo29/grok/072/partner_proofs.txt
?? forge-combo29/grok/072/report_tables.py
?? forge-combo29/grok/072/report_tables.txt
?? forge-combo29/grok/072/run_partner_match.sh

$ ls -la forge-combo29/grok/072
total 8000
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 09:03 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:54 ..
-rw-r--r-- 1 ubuntu ubuntu     120 Nov 20 08:06 apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:07 asan_G100_d10.err.txt
-rw-r--r-- 1 ubuntu ubuntu     911 Nov 20 08:07 asan_G100_d10.meta
-rw-r--r-- 1 ubuntu ubuntu  114099 Nov 20 08:07 asan_G100_d10.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    4031 Nov 20 08:08 asan_probe.err.txt
-rw-r--r-- 1 ubuntu ubuntu     902 Nov 20 08:08 asan_probe.meta
-rw-r--r-- 1 ubuntu ubuntu     176 Nov 20 08:08 asan_probe.raw.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:02 B_G_d12.err.txt
-rw-r--r-- 1 ubuntu ubuntu     868 Nov 20 08:02 B_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  503265 Nov 20 08:02 B_G_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:02 B_O_d12.err.txt
-rw-r--r-- 1 ubuntu ubuntu     869 Nov 20 08:02 B_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  277367 Nov 20 08:02 B_O_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:02 B_O_smoke.err.txt
-rw-r--r-- 1 ubuntu ubuntu     867 Nov 20 08:02 B_O_smoke.meta
-rw-r--r-- 1 ubuntu ubuntu    4184 Nov 20 08:02 B_O_smoke.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    1396 Nov 20 08:56 compare_partner_on.py
-rw-r--r-- 1 ubuntu ubuntu    1227 Nov 20 08:04 compare_raw.py
-rw-r--r-- 1 ubuntu ubuntu    1581 Nov 20 08:06 decisions.txt
-rw-r--r-- 1 ubuntu ubuntu    1442 Nov 20 08:01 gen_r.py
-rw-r--r-- 1 ubuntu ubuntu   17691 Nov 20 08:00 G.epd
-rw-r--r-- 1 ubuntu ubuntu     179 Nov 20 07:59 honesty_b_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 07:59 honesty_b_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     179 Nov 20 07:59 honesty_b_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 07:59 honesty_b_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     179 Nov 20 07:59 honesty_b_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 07:59 honesty_b_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     179 Nov 20 07:59 honesty_b_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 07:59 honesty_b_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    1782 Nov 20 07:59 honesty_b.sh
-rw-r--r-- 1 ubuntu ubuntu     218 Nov 20 07:59 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu     179 Nov 20 08:04 honesty_p_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:04 honesty_p_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     179 Nov 20 08:04 honesty_p_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:04 honesty_p_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     179 Nov 20 08:04 honesty_p_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:04 honesty_p_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu     179 Nov 20 08:04 honesty_p_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:04 honesty_p_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu    1763 Nov 20 08:04 honesty_p.sh
-rw-r--r-- 1 ubuntu ubuntu     218 Nov 20 08:04 HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu    9647 Nov 20 08:03 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu  119327 Nov 20 08:14 match_og.log
-rw-r--r-- 1 ubuntu ubuntu 3514747 Nov 20 08:14 match_og.pgn
-rw-r--r-- 1 ubuntu ubuntu    1404 Nov 20 08:17 match_summary.txt
-rw-r--r-- 1 ubuntu ubuntu   12861 Nov 20 08:00 O.fens
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:06 OG.fens
-rw-r--r-- 1 ubuntu ubuntu     726 Nov 20 08:17 parse_match.py
-rw-r--r-- 1 ubuntu ubuntu     131 Nov 20 08:55 partner_apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu     174 Nov 20 08:56 partner_bench11.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:56 partner_bench11.txt
-rw-r--r-- 1 ubuntu ubuntu     174 Nov 20 08:56 partner_bench13.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:56 partner_bench13.txt
-rw-r--r-- 1 ubuntu ubuntu     174 Nov 20 08:56 partner_bench16.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:56 partner_bench16.txt
-rw-r--r-- 1 ubuntu ubuntu    1766 Nov 20 08:56 partner_honesty.sh
-rw-r--r-- 1 ubuntu ubuntu     216 Nov 20 08:56 PARTNER_HONESTY.txt
-rw-r--r-- 1 ubuntu ubuntu   10518 Nov 20 08:55 partner_idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu   60390 Nov 20 08:59 partner_match_r.log
-rw-r--r-- 1 ubuntu ubuntu 1536337 Nov 20 08:59 partner_match_r.pgn
-rw-r--r-- 1 ubuntu ubuntu     703 Nov 20 09:02 partner_match_summary.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:56 partner_off_O_d12.err.txt
-rw-r--r-- 1 ubuntu ubuntu     899 Nov 20 08:56 partner_off_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  277094 Nov 20 08:56 partner_off_O_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:56 partner_on_O_d12.err.txt
-rw-r--r-- 1 ubuntu ubuntu     898 Nov 20 08:56 partner_on_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  277364 Nov 20 08:56 partner_on_O_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu    1202 Nov 20 08:55 partner_o_on.nodes
-rw-r--r-- 1 ubuntu ubuntu     174 Nov 20 08:56 partner_perft5.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:56 partner_perft5.txt
-rw-r--r-- 1 ubuntu ubuntu     872 Nov 20 08:56 partner_proofs.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:05 P_off_G_d12.err.txt
-rw-r--r-- 1 ubuntu ubuntu     903 Nov 20 08:04 P_off_G_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  502599 Nov 20 08:05 P_off_G_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:04 P_off_O_d12.err.txt
-rw-r--r-- 1 ubuntu ubuntu     904 Nov 20 08:04 P_off_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  277083 Nov 20 08:04 P_off_O_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:05 P_on_O_d12.err.txt
-rw-r--r-- 1 ubuntu ubuntu     903 Nov 20 08:05 P_on_O_d12.meta
-rw-r--r-- 1 ubuntu ubuntu  277464 Nov 20 08:05 P_on_O_d12.raw.txt
-rw-r--r-- 1 ubuntu ubuntu     478 Nov 20 08:03 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu      28 Nov 20 08:08 probe.fen
-rw-r--r-- 1 ubuntu ubuntu    1180 Nov 20 08:06 proofs_search.txt
-rw-r--r-- 1 ubuntu ubuntu    7757 Nov 20 09:04 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu    5271 Nov 20 09:03 report_tables.py
-rw-r--r-- 1 ubuntu ubuntu    3026 Nov 20 09:03 report_tables.txt
-rw-r--r-- 1 ubuntu ubuntu     185 Nov 20 09:03 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu   19383 Nov 20 08:02 R.fens
-rw-r--r-- 1 ubuntu ubuntu    1130 Nov 20 08:06 run_match.sh
-rw-r--r-- 1 ubuntu ubuntu    1144 Nov 20 08:56 run_partner_match.sh
-rw-r--r-- 1 ubuntu ubuntu    5777 Nov 20 08:01 search_set.py
-rw-r--r-- 1 ubuntu ubuntu      78 Nov 20 07:54 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu     196 Nov 20 09:04 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu    1059 Nov 20 08:01 sum_raw.py
-rw-r--r-- 1 ubuntu ubuntu     179 Nov 20 08:05 uci_p.meta
-rw-r--r-- 1 ubuntu ubuntu    5043 Nov 20 08:05 uci_p.txt
```
