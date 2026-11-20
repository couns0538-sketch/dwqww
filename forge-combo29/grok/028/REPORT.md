# Seat 028, idea 28, B8

IdeaB8 is a check, default false. In a position where a cheaper enemy piece attacks a dearer friendly piece, each quiet is labelled by one role (the attacked piece steps away, another piece blocks a slider, the quiet attacks the attacker, the quiet creates a greater threat, or none) and a table of those roles is added to quiet ordering, history pruning, and late-move reduction.
The table is updated when that quiet cuts off or becomes the best move. If the child's static eval is at least IdeaB8_Swing centipawns better for us than the parent eval, the cutoff quiet gets one extra bonus. IdeaB8_Weight defaults to 1024 and IdeaB8_Swing to 40.
With the switch false those reads and writes do not run, so the search stays on today's path.

EXISTS: no. `ThreatHistory` in `src/search.cpp` (the flag near the other tune flags, and `quiet_threat_index`) is the cheaper-attacker from-to table, idea S28, and it defaults to false. There is no piece-value bonus for stepping off an attacked square, so nothing of that kind was removed.

## Honesty

Plain exe B and patched exe P, no setoption, from `HONESTY_B.txt` and `HONESTY_P.txt`:

bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, go perft 5 nodes 4865609.

Known sums of exe B, S14, Threads 1, Hash 16, from `read_nodes.py` on `O12_B.nodes` and `G12_B.nodes`: O depth 12 sum 9500069, first three 41311 24872 28574. G depth 12 sum 18466239.

## Steps

| step | done / partly / not done | evidence file | result |
| --- | --- | --- | --- |
| 1 seat | done | SEAT.txt | seat 028, idea 28, Grok 4.7 |
| 2 honesty and known sums | done | HONESTY_B.txt, O12_B.nodes, G12_B.nodes | pins match, O 9500069, G 18466239 |
| 3a read | done | design.txt | the idea is not already in the engine |
| 3b prediction | done | prediction.txt | pushed before any exe P measurement |
| 3c patch | done | idea.patch.txt, apply_check.txt | `git apply --check` printed MY_APPLY_CHECK_OK |
| 3d proofs | done | HONESTY_P.txt, O12_P_off.nodes, G12_P_off.nodes, O12_P_on.nodes, uci_P.txt, G10_asan.meta, scratch_asan.txt | see proofs below |
| 3e match | done | match_OG.txt, match_OG.pgn | 1106 games, Elo -8.48 +/- 10.49 |
| 4 partner 078 | done | partner_idea.patch.txt, HONESTY_partner.txt, partner_O12_off.nodes, partner_O12_on.nodes, partner_R.txt | CONFIRMS |
| 5 report | done | REPORT.md, RESULT.txt | this file |

## Proofs

(1) exe P, no setoption: the same four numbers as exe B. `HONESTY_P.txt`.

(2) exe P, S14, IdeaB8 false. `read_nodes.py` on `O12_B.nodes` against `O12_P_off.nodes`: n 200, differ 0. On `G12_B.nodes` against `G12_P_off.nodes`: n 353, differ 0.

(3) exe P, S14, IdeaB8 true. `read_nodes.py` on `O12_B.nodes` against `O12_P_on.nodes`: n 200, differ 200. `read_nodes.py` on `O12_P_on.nodes`: sum 9718009, first three 17283 17878 31115. Prediction in `prediction.txt` was 10400000, wrong outside 7500000..13500000 or if equal to 9500069. 9718009 is inside that band.

(4) `uci_P.txt` lists `option name IdeaB8 type check default false`, `option name IdeaB8_Weight type spin default 1024 min 0 max 4096`, and `option name IdeaB8_Swing type spin default 40 min 0 max 500`.

(5) AddressSanitizer and UndefinedBehaviorSanitizer build of the patched tree. `G10_asan.meta` has `nm_asan_count 35`. First 100 of G at depth 10 with IdeaB8 true: `G10_asan.txt` has 0 lines matching ERROR, runtime error, or heap-buffer-overflow, and `G10_asan.nodes` has 100 rows. A scratch copy with one read past a 4-int heap array, triggered by the FEN in `scratch.fen` and run with the same `measure_depth.py`, wrote this line into `scratch_asan.txt`: `/tmp/scratch-forge/src/uci.cpp:194:26: runtime error: load of address 0x502000000080 with insufficient space for an object of type 'int'`. `scratch_asan.nm` is 35. Leak detection was off (`ASAN_OPTIONS` in the meta) so a shutdown leak would not count; the overrun still reported.

## Match

`match_OG.txt`, last result block, B8on versus B8off, S14, Threads 1, Hash 16, 20000 nodes, openings `OG.epd` (200 O plus 353 G), both colours:

```
Results of B8on vs B8off (20000 nodes, 1t, 16MB, OG.epd):
Elo: -8.48 +/- 10.49, nElo: -16.57 +/- 20.48
LOS: 5.63 %, DrawRatio: 62.57 %, PairsRatio: 0.77
Games: 1106, Wins: 327, Losses: 354, Draws: 425, Points: 539.5 (48.78 %)
Ptnml(0-2): [14, 103, 346, 76, 14], WL/DD Ratio: 1.81
```

`match_OG.pgn` has 1106 Event tags. The point estimate is not below -20, and the interval is not entirely below 0, so the brief's one look for a code mistake was not triggered. Prediction was +6 Elo, wrong below -35 or above +45. -8.48 is inside that band.

## Partner

Partner is seat 078 (next seat with idea 28; 128 is past 120). `git apply --check` of `partner_idea.patch.txt` on the base commit printed PARTNER_APPLY_CHECK_OK.

Rebuilt exe, no setoption: `HONESTY_partner.txt` has the four honesty numbers. Its sha256 is `4109ff6c22cb70f4566803f0f42dba3ff6653c6ab173acefe865ce5945fdadee`, the same sha256 as in their `HONESTY_P.txt`.

IdeaB8 false versus my exe B O depth-12 rows: `read_nodes.py` differ 0 of 200.

IdeaB8 true versus the rows extracted from their `P_on_O_d12.raw` by `extract_bestmove_nodes.py` into `partner_claimed_O12_on.nodes`: differ 0 of 200. Both sums are 9295189 and the first three are 24947 29945 39302, which is what their `P_on_O_d12.sum.txt` says. They claimed differ 200 against the plain engine and differ 0 with the switch off. Both match what I measured.

Their switch, 300 of my R openings, both colours, 600 games, `partner_R.txt`:

```
Results of B8on vs B8off (20000 nodes, 1t, 16MB, R300.fens):
Elo: -1.16 +/- 10.15, nElo: -3.17 +/- 27.80
LOS: 41.15 %, DrawRatio: 83.33 %, PairsRatio: 0.92
Games: 600, Wins: 261, Losses: 263, Draws: 76, Points: 299.0 (49.83 %)
```

`partner_R.pgn` has 600 Event tags.

Verdict: CONFIRMS. I did not replay their 1106-game OG match (they report Elo 7.23 +/- 10.49). The proofs the brief names, honesty, switch off, and switch on against their own rows, match.

## Suspicions, not proven

Role labels can be wrong when a pin or a discovery is the real answer. I did not count how often each role fires.
The extra swing bonus is skipped when the child returns from the hash before it writes a static eval. I did not measure how often that happens.
The 1106-game interval includes both sides of zero. That is not a shown loss and not a shown gain.

## What I did not do

I did not replay the 1106-game match, and I did not replay the partner's 1106-game match.
I did not try IdeaB8_Weight or IdeaB8_Swing at any value other than the defaults.
The sanitizer run is the first 100 positions of G at depth 10, not all of G and not depth 12.
There was no FABLE_TO_grok file on the handoff branch at step 1 or at minute 60.
No pull request.

## What I am not sure about

Whether a weight of 1024 is too large for a table that fills from every quiet cutoff. The match does not separate that from the idea itself.
Whether seat 078's different role numbers (they start at 0 for stepping away) would score the same games as mine. The node proofs say their patch does what they recorded. They do not say the two patches are the same search.

times: see stamps.txt

## git status --short

```
 M forge-combo29/grok/028/stamps.txt
?? forge-combo29/grok/028/HONESTY_partner.txt
?? forge-combo29/grok/028/R300.fens
?? forge-combo29/grok/028/REPORT.md
?? forge-combo29/grok/028/RESULT.txt
?? forge-combo29/grok/028/apply_check.txt
?? forge-combo29/grok/028/bench11_partner.meta
?? forge-combo29/grok/028/bench11_partner.txt
?? forge-combo29/grok/028/bench13_partner.meta
?? forge-combo29/grok/028/bench13_partner.txt
?? forge-combo29/grok/028/bench16_partner.meta
?? forge-combo29/grok/028/bench16_partner.txt
?? forge-combo29/grok/028/extract_bestmove_nodes.py
?? forge-combo29/grok/028/partner_O12_off.meta
?? forge-combo29/grok/028/partner_O12_off.nodes
?? forge-combo29/grok/028/partner_O12_off.txt
?? forge-combo29/grok/028/partner_O12_on.meta
?? forge-combo29/grok/028/partner_O12_on.nodes
?? forge-combo29/grok/028/partner_O12_on.txt
?? forge-combo29/grok/028/partner_P_on_O_d12.raw
?? forge-combo29/grok/028/partner_R.meta
?? forge-combo29/grok/028/partner_R.pgn
?? forge-combo29/grok/028/partner_R.txt
?? forge-combo29/grok/028/partner_claimed_O12_on.nodes
?? forge-combo29/grok/028/partner_idea.patch.txt
?? forge-combo29/grok/028/perft5_partner.meta
?? forge-combo29/grok/028/perft5_partner.txt
?? forge-combo29/grok/028/run_partner_match.sh
```

## ls -la

```
total 8900
drwxr-xr-x 2 ubuntu ubuntu    4096 Nov 20 09:15 .
drwxr-xr-x 3 ubuntu ubuntu    4096 Nov 20 07:52 ..
-rw-r--r-- 1 ubuntu ubuntu      41 Nov 20 09:15 apply_check.txt
-rw-r--r-- 1 ubuntu ubuntu     179 Nov 20 08:06 bench11_B.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:06 bench11_B.txt
-rw-r--r-- 1 ubuntu ubuntu     182 Nov 20 09:09 bench11_partner.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:09 bench11_partner.txt
-rw-r--r-- 1 ubuntu ubuntu     179 Nov 20 08:06 bench11_P.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:06 bench11_P.txt
-rw-r--r-- 1 ubuntu ubuntu     179 Nov 20 08:06 bench13_B.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:06 bench13_B.txt
-rw-r--r-- 1 ubuntu ubuntu     182 Nov 20 09:09 bench13_partner.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 09:09 bench13_partner.txt
-rw-r--r-- 1 ubuntu ubuntu     179 Nov 20 08:06 bench13_P.meta
-rw-r--r-- 1 ubuntu ubuntu      61 Nov 20 08:06 bench13_P.txt
-rw-r--r-- 1 ubuntu ubuntu     179 Nov 20 08:06 bench16_B.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:06 bench16_B.txt
-rw-r--r-- 1 ubuntu ubuntu     182 Nov 20 09:09 bench16_partner.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 09:09 bench16_partner.txt
-rw-r--r-- 1 ubuntu ubuntu     179 Nov 20 08:06 bench16_P.meta
-rw-r--r-- 1 ubuntu ubuntu      63 Nov 20 08:06 bench16_P.txt
-rw-r--r-- 1 ubuntu ubuntu    1912 Nov 20 08:05 design.txt
-rw-r--r-- 1 ubuntu ubuntu     881 Nov 20 09:09 extract_bestmove_nodes.py
-rw-r--r-- 1 ubuntu ubuntu    1080 Nov 20 08:08 G10_asan.meta
-rw-r--r-- 1 ubuntu ubuntu       3 Nov 20 08:08 G10_asan.nm
-rw-r--r-- 1 ubuntu ubuntu    5883 Nov 20 08:08 G10_asan.nodes
-rw-r--r-- 1 ubuntu ubuntu  131678 Nov 20 08:08 G10_asan.txt
-rw-r--r-- 1 ubuntu ubuntu     934 Nov 20 08:04 G12_B.meta
-rw-r--r-- 1 ubuntu ubuntu   21123 Nov 20 08:04 G12_B.nodes
-rw-r--r-- 1 ubuntu ubuntu  550031 Nov 20 08:04 G12_B.txt
-rw-r--r-- 1 ubuntu ubuntu     967 Nov 20 08:06 G12_P_off.meta
-rw-r--r-- 1 ubuntu ubuntu   21123 Nov 20 08:06 G12_P_off.nodes
-rw-r--r-- 1 ubuntu ubuntu  550150 Nov 20 08:06 G12_P_off.txt
-rw-r--r-- 1 ubuntu ubuntu   17691 Nov 20 08:03 G.epd
-rwxr-xr-x 1 ubuntu ubuntu    1243 Nov 20 08:05 honesty_b.sh
-rw-r--r-- 1 ubuntu ubuntu     225 Nov 20 08:06 HONESTY_B.txt
-rw-r--r-- 1 ubuntu ubuntu     228 Nov 20 09:09 HONESTY_partner.txt
-rw-r--r-- 1 ubuntu ubuntu     225 Nov 20 08:06 HONESTY_P.txt
-rw-r--r-- 1 ubuntu ubuntu   20136 Nov 20 08:05 idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu    1386 Nov 20 08:05 make_r.py
-rw-r--r-- 1 ubuntu ubuntu     352 Nov 20 08:10 match_OG.meta
-rw-r--r-- 1 ubuntu ubuntu 3576127 Nov 20 08:17 match_OG.pgn
-rw-r--r-- 1 ubuntu ubuntu  133630 Nov 20 08:17 match_OG.txt
-rw-r--r-- 1 ubuntu ubuntu    5910 Nov 20 08:04 measure_depth.py
-rw-r--r-- 1 ubuntu ubuntu     935 Nov 20 08:04 O12_B.meta
-rw-r--r-- 1 ubuntu ubuntu   14757 Nov 20 08:04 O12_B.nodes
-rw-r--r-- 1 ubuntu ubuntu     935 Nov 20 08:04 O12_B_probe.meta
-rw-r--r-- 1 ubuntu ubuntu     211 Nov 20 08:04 O12_B_probe.nodes
-rw-r--r-- 1 ubuntu ubuntu   10352 Nov 20 08:04 O12_B_probe.txt
-rw-r--r-- 1 ubuntu ubuntu  308949 Nov 20 08:04 O12_B.txt
-rw-r--r-- 1 ubuntu ubuntu     968 Nov 20 08:06 O12_P_off.meta
-rw-r--r-- 1 ubuntu ubuntu   14757 Nov 20 08:06 O12_P_off.nodes
-rw-r--r-- 1 ubuntu ubuntu  309194 Nov 20 08:06 O12_P_off.txt
-rw-r--r-- 1 ubuntu ubuntu     966 Nov 20 08:06 O12_P_on.meta
-rw-r--r-- 1 ubuntu ubuntu   14760 Nov 20 08:06 O12_P_on.nodes
-rw-r--r-- 1 ubuntu ubuntu  309750 Nov 20 08:06 O12_P_on.txt
-rw-r--r-- 1 ubuntu ubuntu   12861 Nov 20 08:03 O.fens
-rw-r--r-- 1 ubuntu ubuntu   30552 Nov 20 08:07 OG.epd
-rw-r--r-- 1 ubuntu ubuntu    1893 Nov 20 09:10 partner_claimed_O12_on.nodes
-rw-r--r-- 1 ubuntu ubuntu   22945 Nov 20 09:09 partner_idea.patch.txt
-rw-r--r-- 1 ubuntu ubuntu     971 Nov 20 09:09 partner_O12_off.meta
-rw-r--r-- 1 ubuntu ubuntu   14757 Nov 20 09:09 partner_O12_off.nodes
-rw-r--r-- 1 ubuntu ubuntu  309335 Nov 20 09:09 partner_O12_off.txt
-rw-r--r-- 1 ubuntu ubuntu     969 Nov 20 09:10 partner_O12_on.meta
-rw-r--r-- 1 ubuntu ubuntu   14754 Nov 20 09:10 partner_O12_on.nodes
-rw-r--r-- 1 ubuntu ubuntu  309294 Nov 20 09:10 partner_O12_on.txt
-rw-r--r-- 1 ubuntu ubuntu  284018 Nov 20 09:09 partner_P_on_O_d12.raw
-rw-r--r-- 1 ubuntu ubuntu     342 Nov 20 09:10 partner_R.meta
-rw-r--r-- 1 ubuntu ubuntu 1640796 Nov 20 09:13 partner_R.pgn
-rw-r--r-- 1 ubuntu ubuntu   68460 Nov 20 09:13 partner_R.txt
-rw-r--r-- 1 ubuntu ubuntu     179 Nov 20 08:06 perft5_B.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:06 perft5_B.txt
-rw-r--r-- 1 ubuntu ubuntu     182 Nov 20 09:09 perft5_partner.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 09:09 perft5_partner.txt
-rw-r--r-- 1 ubuntu ubuntu     179 Nov 20 08:06 perft5_P.meta
-rw-r--r-- 1 ubuntu ubuntu     274 Nov 20 08:06 perft5_P.txt
-rw-r--r-- 1 ubuntu ubuntu     561 Nov 20 08:04 prediction.txt
-rw-r--r-- 1 ubuntu ubuntu   19522 Nov 20 09:10 R300.fens
-rw-r--r-- 1 ubuntu ubuntu    1080 Nov 20 08:05 read_nodes.py
-rw-r--r-- 1 ubuntu ubuntu   14277 Nov 20 09:15 REPORT.md
-rw-r--r-- 1 ubuntu ubuntu     183 Nov 20 09:15 RESULT.txt
-rw-r--r-- 1 ubuntu ubuntu   25991 Nov 20 08:05 R.fens
-rwxr-xr-x 1 ubuntu ubuntu    1584 Nov 20 08:10 run_match.sh
-rwxr-xr-x 1 ubuntu ubuntu    1526 Nov 20 09:10 run_partner_match.sh
-rw-r--r-- 1 ubuntu ubuntu       3 Nov 20 08:09 scratch_asan.nm
-rw-r--r-- 1 ubuntu ubuntu       0 Nov 20 08:09 scratch_asan.nodes
-rw-r--r-- 1 ubuntu ubuntu    7005 Nov 20 08:09 scratch_asan.txt
-rw-r--r-- 1 ubuntu ubuntu      28 Nov 20 08:09 scratch.fen
-rw-r--r-- 1 ubuntu ubuntu      78 Nov 20 07:52 SEAT.txt
-rw-r--r-- 1 ubuntu ubuntu     140 Nov 20 09:15 stamps.txt
-rw-r--r-- 1 ubuntu ubuntu     158 Nov 20 08:06 uci_P.meta
-rw-r--r-- 1 ubuntu ubuntu    5101 Nov 20 08:06 uci_P.txt
```
