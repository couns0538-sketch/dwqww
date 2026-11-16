# REPORT_kimi5_job4 — LmrDeeperShallower from the inside (kimi5, 2026-11-16 UTC)

(1) K0–K5 ALL MET: K0 312866/862329/3024920/4865609 on base AND on the tunable build; K1 200/200
nodes + 200/200 bestmove (tunable OFF = base); K2 200/200 + 200/200 (tunable ON defaults = base ON);
K3 200/200 + 200/200 (margins ±100000 = switch OFF, node-for-node: the switch IS the three quoted
lines and nothing else); K4 each of the four options alone changes 200/200 positions; K5 all four
names in the exe's `uci` list with the right defaults/ranges, setoption lines in the input logs.
(2) Prediction vs measurement: (a) per 1000 candidates d12/d16 — S1 45.4/43.6 [10,150], S2 19.3/16.2
[5,120], S3 320.2/360.3 [150,500], unchanged 615.2/579.8 [300,800]: ALL inside. (b) shallower-only
0.924/0.891, deeper-only 1.062/1.087: inside, kill criteria not triggered; my independence model IS
killed (|product−both| 0.086/0.059 > 0.05). (c) inf_best 0 at both depths (proven unreachable);
mate_best 85/713 — the unguarded mate case is REAL (0.07/0.11 % of candidates). The saved tree comes
from the SHALLOWER arm alone (d16: 0.891 [0.838, 0.945]) while the deeper arm is a tax
(d16: 1.087 [1.018, 1.157]) that cancels about half of it, netting 0.909 [0.851, 0.970].
(3) Settings for a match first: (i) LmrDeeperBase 100000 / DepthMul 2 / ShallowerBase 0 / Mul 1
("shallower only", the isolated saver); (ii) 40 / 2 / 8 / 0 ("flat shallower", cheapest tree
measured, 0.882 [0.832, 0.935] d16). The ONE match asked of glmflash5: side A LmrDeeperShallower
true with the four at defaults (40/2/0/1) vs side B LmrDeeperShallower true + LmrDeeperBase 100000
(2/0/1), 80,000 nodes per move, built-in net, all other options default — 800 opening pairs
(1,600 games) for ±10 Elo at 95 % (your job-5 ±13.35 at 396 pairs scales to ≈706 pairs; 800 is
margin). It prices the deeper arm in Elo at fixed nodes.

How sure: sure of every number (deterministic re-runs, node-exact cross-checks against job 3 and
Fable's harness, patches proven by `patch -p1 --fuzz=0` + 200/200 behavior proofs). The Part-5
"how often wrong" shares come from a statistics build whose tree is ANOTHER tree — stated plainly
where used.

Engine for every table: commit 6b98f217 (forge-combo29), built-in net, Threads 1, Hash 16,
OwnBook false, every other option at default except the ones each row names. Empty table before
every search (ucinewgame + isready before every `go`). The same 200 UHO positions as job 3
(tests_kimi5_job3/first200.fens, copied into this folder). Release build, CMake + g++ 13.3,
-march=x86-64-v4 (this machine has AVX-512 + BMI2).

## Step 0 (K0), the known numbers
- Base build: step0_bench11.txt 312866, step0_bench13.txt 862329, step0_bench16.txt 3024920,
  step0_perft5.txt 4865609 — all four match.
- Tunable build: tun_step0_bench11/13/16.txt, tun_step0_perft5.txt — the same four numbers.

## Step table

| step | done? | evidence | result |
|---|---|---|---|
| claim + stamps | done | CLAIM_kimi5_job4.txt, stamps.txt | first stamp 06:48:24Z inside the claim command |
| Part 1 prediction, own commit, pre-measurement | done | PREDICTION_kimi5_job4.md (commit "kimi5 job 4 prediction") | ranges + kill criteria, never edited |
| colleagues read (step 2) | done | section below | deepseek5 job 8 + notes to job 9 P0; glmflash5 job 5 (branch cursor/glmflash5-work-cb5c) |
| base build + K0 | done | step0_*.txt | four known numbers |
| Part 2 tunables patch | done | LmrDS_tunables.patch.txt (applies `patch -p1 --fuzz=0`, result byte-identical to the built tree) | K0–K5 all met, numbers above |
| Part 3 counters patch on top + must-be-nonzero | done | LmrDS_counters.patch.txt; k5_j4_on_d16_fresh_1pos_ctr.json (cand 1675, s3 566, s1 79, s2 37 on ONE position) | ctr = tun proven: 200/200 + 200/200 at d12 (k5_j4_on_d12_fresh_ctr vs _tun) |
| Part 4 factors, 6 columns × d12/d16, bootstrap | done | analysis_summary.txt, k5_j4_*.json | table below; 4000 resamples, seed 20261116, both halves |
| Part 5 stat build: how often the shortcut is wrong | done | LmrDS_statbuild.patch.txt, part5_summary.txt, k5_j4_on_d1*_fresh_stat.json | S1 contradicted 14.0/15.7 %, S2 unverified stand wrong 30.4/32.5 % (d16/d12) |
| report + notes + push | done | this file, NOTES_kimi5.md | — |

## Part 4: tree factors vs switch OFF (200 positions, nodes ON/OFF; [95 % bootstrap over positions, 4000 resamples, seed 20261116]; halves = positions 1-100 / 101-200; bestmove-diff = positions whose bestmove differs from OFF)

| depth | column | factor [interval] | halves | bestmove-diff |
|---|---|---|---|---|
| d16 | both (defaults 40/2/0/1) | 0.9091 [0.8507, 0.9703] | 0.958/0.864 | 60/200 |
| d16 | shallower only (100000/2/0/1) | 0.8909 [0.8381, 0.9451] | 0.883/0.898 | 41/200 |
| d16 | deeper only (40/2/-100000/1) | 1.0868 [1.0180, 1.1573] | 1.080/1.093 | 47/200 |
| d16 | half margins (20/1/0/1) | 0.9545 [0.8959, 1.0174] | 0.965/0.945 | 46/200 |
| d16 | double margins (80/4/0/1) | 0.8965 [0.8425, 0.9506] | 0.908/0.886 | 54/200 |
| d16 | flat shallower (40/2/8/0) | 0.8824 [0.8319, 0.9348] | 0.878/0.886 | 43/200 |
| d12 | both | 0.8951 [0.8518, 0.9430] | 0.892/0.898 | 58/200 |
| d12 | shallower only | 0.9238 [0.8738, 0.9777] | 0.952/0.898 | 54/200 |
| d12 | deeper only | 1.0623 [1.0003, 1.1300] | 1.089/1.038 | 59/200 |
| d12 | half margins | 0.9738 [0.9211, 1.0304] | 0.989/0.960 | 57/200 |
| d12 | double margins | 0.9111 [0.8620, 0.9624] | 0.947/0.879 | 54/200 |
| d12 | flat shallower | 0.8830 [0.8377, 0.9306] | 0.888/0.879 | 54/200 |

Node sums: OFF d12 12,573,318 (= job 3 to the node), OFF d16 67,796,692 (= Fable's sum on his
harness to the node), both d12 11,254,768 (= job 3's lmrs single to the node). Three harnesses,
three builds, identical numbers.

## Part 3: the candidates from the inside (ctr build, sums over 200 positions)

d12: 117,467 candidates (10.44 per 1000 nodes); d16: 635,717 (10.31 per 1000 nodes).
Per 1000 candidates: | class | d12 | d16 |; S1 45.4/43.6, S2 19.3/16.2, S3 320.2/360.3,
unchanged 615.2/579.8.
Splits (d16; d12 same shape): S3 is 80 % cut nodes, 89 % new_depth 1-3, 85 % quiet.
S1 is 67-75 % new_depth 4-7, S2 51-56 %, both ~99 % quiet, spread over node types.
Full table in analysis_summary.txt.
S1's shallower re-search FAILS LOW 51.2 % (d12) / 52.6 % (d16) of the time.
mate_best 85 (d12) / 713 (d16); inf_best 0 / 0.

## Part 5: how often is the shortcut wrong (STATISTICS build — its tree is ANOTHER TREE:
the extra old-code re-searches write TT and history, so its candidate population differs;
sums over the same 200 positions, switch on, defaults)

| class | band | d12 | d16 |
|---|---|---|---|
| S1: old re-search contradicts the shortcut's verdict | nd 1-3 | 21.9 % (128/585) | 19.0 % (494/2,606) |
| | nd 4-7 | 14.8 % (641/4,321) | 14.3 % (2,951/20,697) |
| | nd 8+ | 16.0 % (114/713) | 11.4 % (824/7,201) |
| | ALL | 15.7 % (883/5,619) | 14.0 % (4,269/30,504) |
| S2: the unverified stand is rejected by the old re-search | nd 1-3 | 50.9 % (369/725) | 52.8 % (1,490/2,820) |
| | nd 4-7 | 25.0 % (302/1,209) | 24.5 % (1,384/5,642) |
| | nd 8+ | 15.9 % (41/258) | 18.3 % (462/2,519) |
| | ALL | 32.5 % (712/2,192) | 30.4 % (3,336/10,981) |

The old re-search itself fails low in ~57 % of S1 cases — most S1 candidates never confirm at
any depth; S1 mostly shortens re-searches that fail anyway. S2 is the risky one: at new_depth
1-3 (its dominant band is 4-7, but it fires at 1-3 too) the skipped verification would have
rejected the stand about HALF the time.

## Findings (file:line = commit 6b98f217 forge-combo29/src/search.cpp unless said)

- F1. The switch is EXACTLY its three lines. K3 (margins ±100000, neither can fire: two scores
  are never more than 64,001 apart) reproduces the switch-OFF run 200/200 nodes AND bestmove.
  So there is nothing else hiding in it (lines 2016-2023; PV full-window at 2035-2037 uses the
  changed new_depth). Reproduce: `python3 k5_j4.py <tun> first200.fens k3 12 fresh 200` vs
  `... off 12 fresh 200` on the base exe.
- F2. The saving comes from the shallower arm alone; the deeper arm is a tax that cancels about
  half of it (Part 4 table). The job-3 sentence "shallower dominates the saved re-searches" is now
  SHOWN (deeper-only > 1, shallower-only < 1 at both depths, all intervals on their own side of
  1.00 except deeper-only d12 whose interval's lower edge is 1.0003).
- F3. The arms are NOT independent: both = 0.895/0.909 but shallower×deeper = 0.981/0.968
  (d12/d16). My prediction's 0.05 kill line is crossed: the combination saves MORE than the
  product — deeper's extra plies partly live inside subtrees the shallower arm removes (or the
  reverse through TT). Mechanism not isolated; the fact is in the sums.
- F4. The unguarded mate case is real: 85/713 candidates arrive with best_score a mate score
  (0.07/0.11 %). The block (2016-2020) has no is_mate_score guard, unlike the pruning gate at
  1842 and the singular guard at 1930. The -Infinite start (line 1797) is unreachable at a
  candidate: move_count > 1 (1991-1993), every counted move reaches a search because all
  pre-search pruning requires best_score > -MateInMaxPly (1842, 1918-1919), and search never
  returns -Infinite — measured: inf_best = 0 at both depths. First real value: lines 2043-2044.
- F5. S3 concentrates at new_depth 1-3 (89-91 %) and cut nodes (~80 %): the 40+2·nd band is
  only beatable by small-depth fail-highs. S1 concentrates at new_depth 4-7 (67-75 %), S2 less
  so (51-56 %); both ~99 % quiet. So the literal 40/2/0/1 tunes two different populations.
- F6. Tuner direction from the margins columns: making deeper rarer (80/4) leaves the saving
  ~unchanged (0.897 vs 0.909 d16) — the tax is nearly all in its cheapest, most frequent fires;
  widening the shallower band to a flat 8 cp (40/2/8/0) gives the cheapest tree measured
  (0.882 [0.832, 0.935] d16). Making deeper MORE frequent (20/1) cuts the saving to
  0.955 [0.896, 1.017] — the dose-response is monotone in the deeper arm's fire rate, which is
  the cleanest sign yet that the deeper arm only spends.
- F7. S2's unverified stand is wrong ~30 % of the time overall and ~half the time at new_depth
  1-3 (Part 5). With S1 contradicted only ~14-16 %, the SKIPPED re-search is where the shortcut
  is most often wrong.

### Suspicions, not proven
- S1. The ~30 % S2 wrong-stand rate is the prime suspect for "tree 9-14 % smaller, strength
  flat" (+13.2 ± 12.2 / +2.6 ± 10.8 at 20k nodes): the savings include verification skips that
  flip verdicts. Only a match decides; not measured here.
- S2. At a PV node the full-window search (2035) still runs after S1/S2 with the changed
  new_depth, so PV-node shortcuts partially self-correct; the costly shortcuts should be the
  cut-node ones (~60-70 % of S1/S2 by the Part-3 splits). The Part-5 counters were not split by
  node type — see "A better way".
- S3. The d16 "both" halves (0.958/0.864) say the saving is position-heterogeneous; the
  interval covers it, but a position-stratified look may find the saver population.

## From my colleagues (step 2)
- deepseek5: NOTES through "after job 9 Part 0" + REPORT_deepseek5_job8 (head). His job-8
  headline corrected itself: the 14k TSan reports were on PLANTED counters; the real history
  tables are per-Worker. My runs are Threads 1, one process, fixed depth — nothing in his map
  touches these node counts. His B21/B27 warning (`infinite` overrides depth limits) does not
  apply: my harness sends only `go depth N`. Read, nothing to apply.
- glmflash5 (branch cursor/glmflash5-work-cb5c): NOTES through job 5 + REPORT_glmflash5_job5
  (head). Applied TWICE: (i) his job-5 measured variance (±13.35 Elo at 396 pairs) scales my
  game-count ask to 800 pairs for ±10; (ii) the rule "every option a harness sets is looked up
  in the exe's own uci list" — K5's evidence is exactly that lookup (uci_list_tun.txt) plus the
  input logs. His confirmation of my TmNodeShare -12 % prediction noted for the ledger.

## What I did NOT do
- Part-5 contradiction counters are split by new_depth band only, not by node type (time;
  the classes themselves ARE split by node type in Part 3).
- No games / Elo (glmflash5's trade).
- No repair patch for the unguarded mate case (F4) — measured and located, not fixed; a repair
  was not asked for.
- The d12 margins columns are measured and tabled but not discussed; d16 carried the argument.

## What I am NOT sure about
- Whether the old re-search failing low (my "wrong" label for S2) is truly wrong — the reduced
  search is a proxy too; only games price it.
- Whether flat(8,0)'s edge survives other position sets; its interval overlaps "both".
- The 60/200 bestmove diffs at d16: how many are mate-line flips vs harmless swaps.

## A better way
- Split s1_contra / s2_old_low by node type (one more array index, same patch shape): the
  cut-node share is the honest "how often wrong" number because PV nodes re-search full-window
  afterwards anyway (line 2035). Expect the cut-node S2 wrong-stand to sit above the 30 % mean.
- A 5th option "LmrShallowerNoSkip" (do_shallower only shortens, never skips) would price the
  S2 skip as a clean tree factor with the existing harness — no stat build, and K3's no-op trick
  still proves the wiring. Cheaper than the stat build and directly matchable.
- Bootstrap the bestmove-diff counts too (raw counts now); 60/200 at d16 "both" has its own
  position error that a resample would quote.

## UTC stamps
Run start (trigger) 2026-11-16T06:47:49Z; first command's now-stamp 06:47:59Z; then stamps.txt:
claim 06:48:24Z; prediction commit 06:50:01Z; binaries base 06:51:55Z, tun 06:52:14Z, ctr
06:52:20Z (file mtimes); matrix 06:52:26Z → 06:59:25Z (every run stamped inside stamps.txt);
stat binary 07:00:33Z; stat runs 07:00:33Z → done 07:05:35Z; tun step0 + analysis 07:05:56Z;
report written ~07:10Z. Minute-40 mark (07:28:24Z) never reached: all measuring stopped at
07:05:56Z on my own schedule, Parts 1-5 complete.

## Model
Kimi K3 (run name kimi5).
