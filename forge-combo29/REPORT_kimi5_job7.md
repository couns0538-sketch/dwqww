# kimi5 job 7 report — the LMR reductions' calibration table

## 1. Three lines in plain words

- What was asked: measure, per pass through src/search.cpp line 2013, whether each of the
  eight LMR reduction terms separates moves that beat alpha from moves that do not (Part 2,
  observe-only), what the reductions miss (Part 3, full-depth probes), and whether the
  double-extension cap of line 1945 bites on set G (Part 5); verdicts and up to three
  spin-option patches (Part 4). Budget 50 minutes from the claim commit.
- The answer: K0, K1 and K2 all met on both sets; the reductions miss 4-20 per 1,000
  fail-low reduced searches, peaking at applied reduction 2, NOT growing with the
  reduction; history separates strongly and monotonically, not-improving separates, the
  cut_node +2 goes the WRONG WAY on every table (its events beat alpha and regret 2-3x
  more at equal reduction), tt_pv -1 goes the wrong way at a>=1 on FH/CONF.
- How sure: counting proven by K2 in every one of 1,106 searches and by a planted fault
  that the check catches verbatim; node sums match Fable's K1 to the node on both sets;
  the probe's disturbance is measured (+51.5 % O, +48.4 % G nodes) and its missed rates
  are consistent across two independent position sets. The equal-a comparison is
  confounded (named in 4.6); verdicts state it.

## 2. Step 0 (honesty check), plain base 6b98f217, fresh process per line

| check | known | got | raw file |
|---|---|---|---|
| bench 11 | 312866 | 312866 | tests_kimi5_job7/k0_bench11.txt |
| bench 13 | 862329 | 862329 | tests_kimi5_job7/k0_bench13.txt |
| bench 16 | 3024920 | 3024920 | tests_kimi5_job7/k0_bench16.txt |
| go perft 5 | 4865609 | 4865609 | tests_kimi5_job7/k0_perft5.txt |
| bench 11, flag build (K0 with flag) | 312866 | 312866 | tests_kimi5_job7/k0f_bench11.txt |
| bench 13, flag build | 862329 | 862329 | tests_kimi5_job7/k0f_bench13.txt |
| go perft 5, flag build | 4865609 | 4865609 | tests_kimi5_job7/k0f_perft5.txt |

K1 (flag build FORGE_LMR_CALIB=1, depth 12, Threads 1, Hash 16, OwnBook false,
ucinewgame+isready before every go): O sum **12,573,318** with first three
**18,407 / 25,756 / 64,000** (k2_flag_O_d12.json), G sum **22,128,265**
(k3_flag_G_d12.json): both match the job's known answers to the node.

## 3. Step table

| step | state | evidence | result |
|---|---|---|---|
| claim, prediction commit | done | tests_kimi5_job7/prediction.txt (commit "kimi5 job 7 prediction") | in before any measurement |
| Part 2 patch LmrCalib.patch.txt, FORGE_LMR_CALIB=1 | done | tests_kimi5_job7/LmrCalib.patch.txt | applies with `patch -p1`, no fuzz; observe-only (K0 with flag = K0) |
| K0 plain + flag | done | k0*.txt above | all four known numbers, both builds |
| K1 O and G | done | k2_flag_O_d12.json, k3_flag_G_d12.json | 12,573,318 and 22,128,265, first three exact |
| K2 every search | done | agg_k2.txt, agg_k3.txt, agg_r1.txt, agg_r2.txt ("K2_violations 0") | 0 violations in 200+353+200+353 searches |
| K2 positive control (planted fault) | done | plant_j7.diff.txt, agg_plant.txt | double-count of term3 reported as `term3 16566 cells 8283 viol 1` (exactly 2x) in all 5 searches; agg exits 2 |
| Part 3 probe build FORGE_LMR_REGRET=1 | done | same patch file, second flag; r1/r2 outputs | ready well before minute 28; cadence viol 0 in every search |
| Part 4 verdicts | done | section 4.4 below | 8 verdicts from agg_k2/k3/r1/r2 |
| Part 4 patches (3) | done | LmrCutNode.patch.txt, LmrTtPv.patch.txt, LmrGiveCheck.patch.txt | each: K0 and K1 at default exact, listed by uci, wrong name refused, O+G sums at one other value (4.5) |
| Part 5 double-extension cap | done | DBL lines in agg_k2.txt / agg_k3.txt | O: 0 in all 200 (known answer met); G: 225 refusals in 28 of 353 |
| runner sends OwnBook false | done | every *_input.log (Fable's job-6 criticism) | `setoption name OwnBook value false` before every set |

## 4. Findings

All numbers below are printed by the one committed aggregation command
`python3 agg_j7.py <checks file> [positions file]` over the committed raw files
(outputs committed as agg_k2.txt (O), agg_k3.txt (G), agg_r1.txt (probe O),
agg_r2.txt (probe G)). Per-search lines are summed by that command; no number is typed
from memory. Reproduce any cell: `grep "LMRCELL a2 " tests_kimi5_job7/k2_flag_O_d12_checks.txt`.

### 4.1 The shape of the tree (Part 2, sets O and G, depth 12)

Passes through line 2013: O 4,764,594 (200 searches), G 9,152,539 (353 searches).
Applied reduction a = new_depth - reduced_depth, share of passes / FH per 1,000
(reduced score above alpha) / CONF per 1,000 (above alpha after the re-search;
for a=0 CONF=FH):

| a | O share | O FH | O CONF | G share | G FH | G CONF |
|---|---|---|---|---|---|---|
| 0 | 31.9 % | 75.2 | 75.2 | 27.3 % | 81.4 | 81.4 |
| 1 | 24.9 % | 71.5 | 48.7 | 27.8 % | 70.6 | 48.7 |
| 2 | 15.2 % | 34.2 | 22.2 | 17.7 % | 39.7 | 25.1 |
| 3 | 13.8 % | 21.0 | 10.2 | 13.3 % | 25.7 | 11.9 |
| 4 | 8.4 % | 12.0 | 4.5 | 7.8 % | 16.8 | 6.2 |
| 5+ | 5.9 % | 7.3 | 2.3 | 6.0 % | 11.0 | 2.9 |

FH and CONF fall monotonically with a on both sets: the applied reduction orders the
move classes exactly as intended. a=0 (r<=0 after the terms) is 31.9 % (O) / 27.3 % (G)
of all passes, not the predicted 15 %.

### 4.2 What the reductions miss (Part 3, probes: every 8th fail-low reduced search
with a>=1 re-searched at full depth, result counted and thrown away)

Probes: O 372,142 of 2,977,871 fail-low events (exactly 1/8, cadence viol 0);
G 782,704 of 6,262,882. MISSED = probe score above alpha.

| a | O n | O MISSED/1000 | G n | G MISSED/1000 |
|---|---|---|---|---|
| 1 | 130,344 | 10.6 | 290,304 | 15.5 |
| 2 | 83,776 | 16.4 | 192,239 | 20.1 |
| 3 | 77,858 | 10.5 | 146,898 | 14.8 |
| 4 | 46,775 | 7.9 | 87,109 | 10.6 |
| 5+ | 33,389 | 4.3 | 66,154 | 7.5 |

The miss rate PEAKS AT a=2 AND FALLS: deep reductions are applied to moves that fail low
at any depth; the regret lives in the small reductions. By move class (O/G at a=1):
quiet 11.3/17.1 per 1,000, noisy 6.4/4.5. By node kind at a=1 (O, quiet): tt_pv 14.5,
cut 18.4, neither 6.6; (G, quiet): 16.2 / 29.0 / 11.0 - cut nodes miss most.
Nodes per probe: O 19.0, G 14.5. Probes ending within one node (an older, deeper entry
answered them; includes the rare instant return): O 67,871 of 372,142 (18.2 %),
G 256,233 of 782,704 (32.7 %).
Disturbance stated as node sums: probe run O 19,053,262 vs K1 12,573,318
(+6,479,944, +51.5 %); G 32,843,918 vs 22,128,265 (+10,715,653, +48.4 %). Probe nodes
alone are 7,082,311 (O) / 11,370,555 (G); the main tree shrank slightly under the probe
(TT and history pollution), which is part of the stated disturbance.
Saved and restored around each probe: (ss+1) and (ss+2) cutoff_count and killers.
Not restored: the hash table and the history tables (cannot be), per-ply killers below
ss+2 (global state like the histories), and fields overwritten before any later read
(pv/pv_length, static_eval, raw_eval, tt_pv, arrival_index, current_move, moved_piece,
continuation, ply; the reader analysis is in the patch header and section 7).

### 4.3 The double-extension cap (Part 5, in the Part-2 build)

O: 0 refusals in all 200 searches - the job's known answer is met. G: **225 refusals
in 28 of the 353 searches**. Split by the root position's piece count (agg command with
the epd file): <=10 pieces: 133 refusals in 17 of 99 searches; 11-20: 90 in 10 of 144;
>=21: 2 in 1 of 110. The cap bites almost only in low-material positions (deepest
effective searches), never in the opening set.

### 4.4 The verdict per term (Part 4)

Rates are FH (CONF) per 1,000 with the term fired vs not fired AT EQUAL a, both sets;
MISSED per 1,000 from the probe runs. Full per-a rows: TERM_TABLE / HIST_TABLE /
RGT_TERM / RGT_HIST sections of the four agg files.

| # | term (line, sign) | n fired O/G | verdict (eight words) | key numbers |
|---|---|---|---|---|
| 1 | tt_pv -1 (1995) | 1.23M/1.96M | WRONG WAY: less FH and CONF at a>=1, both sets | a2: O 25.4 vs 38.1, G 27.2 vs 44.9; CONF O 15.3 vs 25.2; regret a2 G 17.4 vs 21.3 (fired less, opposite) |
| 2 | not improving +1 (1996) | 2.89M/4.97M | SEPARATES in direction of sign, both sets | a1: O FH 40.8 vs 121.7, G 49.6 vs 100.1; regret a2 O 14.2 vs 19.4 |
| 3 | cut_node +2 (1997) | 1.23M/2.57M | WRONG WAY: more FH, more CONF, triple regret | a1: O FH 160.5 vs 30.0, G 135.7 vs 35.9; regret a2 O 33.0 vs 10.7, G 36.5 vs 13.1 |
| 4 | tt_capture+quiet +1 (1998) | 0.31M/0.63M | Carries almost NOTHING; slight wrong way a2-a3 | a1: O 72.4 vs 71.4, G 55.4 vs 71.4; a3: O 28.4 vs 20.2; regret splits |
| 5 | gives_check -1 (1999) | 0.22M/0.56M | MIXED: wrong way at a0-a1, separates at a>=2 | a0: O 23.8 vs 78.4, G 60.1 vs 84.4; a2: O 68.5 vs 32.9, G 86.6 vs 35.3 |
| 6 | in_check -1 (2000) | 0.16M/0.60M | WRONG WAY at a1 (largest cell); separates a>=2 | a1: O 40.0 vs 73.2, G 59.1 vs 71.8; a2: O 82.1 vs 33.6, G 90.1 vs 38.2 |
| 7 | cutoff_count +1 (2001) | 1.57M/1.83M | MIXED: separates on O, contradicts on G | a2: O 27.6 vs 37.8 but G 41.0 vs 39.3; regret a1: O 6.2 vs 11.4, G 11.0 vs 16.0 |
| 8 | history -2..+2 (2002) | five values | SEPARATES strongest, monotone per value, both sets | O a1: h-1 22.4, h0 59.1, h+1 90.2, h+2 349.0 FH; h+2 regret 42.5-70.0/1000, the largest of any class |

The equal-a comparison is confounded by construction (4.6); the verdicts read the
tables as the job asks, with the confounder named.

### 4.5 The three patches (each ONE spin option, registered like its neighbours at
search.cpp 126-139, default = today's number; each is a standalone diff against
6b98f217, and the proof build = base + LmrCalib.patch.txt + the option patch, flag on)

| patch | option | K0 at default | K1 at default | uci lists | wrong name refused | O sum / G sum at other value |
|---|---|---|---|---|---|---|
| LmrCutNode.patch.txt | LmrCutNode spin 0-4 default 2 | 312866 / 862329 / 4865609 (o1_bench11/13.txt, o1_perft5.txt) | 12,573,318 / 22,128,265 (o1_def_*.json) | o1_uci.txt | o1_wrongname.txt ("unknown option LmrCutNodex") | value 1: O 12,310,830, G 22,228,946 |
| LmrTtPv.patch.txt | LmrTtPv spin 0-4 default 1 | same three K0 numbers (o2_*.txt) | 12,573,318 / 22,128,265 | o2_uci.txt | o2_wrongname.txt | value 0: O 8,572,032 (-31.8 %), G 16,869,889 (-23.8 %) |
| LmrGiveCheck.patch.txt | LmrGiveCheck spin 0-4 default 1 | same three K0 numbers (o3_*.txt) | 12,573,318 / 22,128,265 | o3_uci.txt | o3_wrongname.txt | value 0: O 11,811,886, G 21,239,639 |

Chosen where the tables speak loudest: cut_node (wrong way on all three tables, 2-3x),
tt_pv (wrong way on FH/CONF at every a>=1 on both sets), gives_check (wrong way exactly
on its biggest cells). No word about strength: deepseek5 measures trees, glmflash5 and
Opus play games. The setoption lines of the alt-value runs are in o*_v*_input.log.

### 4.6 Suspicions, not proven

- The equal-a comparison is confounded: a cut_node event at a=1 REQUIRED the negative
  terms to overcompensate the +2, so its population is enriched with strong-history,
  checking, tt_pv moves. Part of term 3's wrong way is this enrichment; how much, the
  tables cannot say (that needs the term randomized within a search, not observed).
- Term 3's design goal may be node economy under null windows, not FH separation; the
  "WRONG WAY" verdict is by the job's metric, not necessarily by Elo. Games decide.
- The probe's one-node count (18.2 % / 32.7 %) includes instant returns (mate-distance
  pruning, draws), not only older-deeper-entry answers; the split was not instrumented.
- rn/re node columns sum across nesting levels (an event inside another event's reduced
  search is counted in both); ratios within a row family are comparable, sums are not
  the root node total.

## 5. From my colleagues

- deepseek5 (branch 24e4bb01, notes through "after cross2", newest report job 21): the
  V5 cross-check "disagreement" is resolved by Fable's job file (its 70-line file is the
  last search of my build; its own slot fault named in its file 22). Not pursued, as
  instructed. Its job-21/22 bracket (history-pruning drops carry the most full-depth
  regrets, 147/114 per 1,000) is a PRUNING population, mine is REDUCTION fail-lows;
  the two are consistent in direction (history-marked moves carry the most regret).
- glmflash5 (branch cursor/glmflash5-work-cb5c - its tool gave it that name; notes
  through job 13, newest report job 9): the pv1 headline (+31.0 for exempting late-move
  pruning at PV nodes only) and the histoff +10.6 / futoff -10.8 / qseewide -15.4 game
  results say pruning steps carry signed value; my term table says the same from the
  counting side for history and futility-class moves. Its warning "if SoundRegret
  counters go on top, expect interactions" applies to my probe: stated as the
  disturbance numbers above.
- deepseek5's LEARNED (big edits via patch files, never in-place splices) was applied:
  every source change of this job is a committed .patch.txt applied with patch(1).
- Applied to my own protocol: the job-6 runner got OwnBook false (Fable's criticism);
  my first manual sanity search hit the book exactly as deepseek5's notes describe
  (startpos answered from the book, zero search, zero counters) - the runner's
  handshake + OwnBook false is the fix and is in every committed input log.

## 6. What I did NOT do

- No strength measurement (per the job: deepseek5 measures trees, glmflash5/Opus play).
- The full.txt info streams of the six big runs are not committed (size); the jsons
  (per-position nodes), the checks (counter lines) and the input logs are.
- The option runs' LMR counter files are not committed (not quoted here); their jsons,
  metas and input logs are.
- No second seed, no Threads>1, no other depths: the job fixed depth 12, Threads 1.
- The confounder-free experiment (randomized term firing) is designed but not run (4.6).

## 7. What I am NOT sure about

- How much of term 3's (and term 1's) wrong way is the equal-a enrichment (4.6) versus
  a genuine mis-signing. The verdicts state the metric; the cause is not isolated.
- Whether restored (ss+1)/(ss+2) killers + cutoff_count are the complete read-set a
  probe touches: I read every (ss+1)/(ss+2) use in search.cpp and believe the list in
  4.2 is complete for fields read by this node or later siblings; pv_length/pv are
  written by the probe but provably not read before the next overwrite on the fail-low
  path (only line 2049 reads them, unreachable for probe events).
- The probe cadence "every 8th of a search" is per UCI search (per position), matching
  "every run probes the same events"; a per-position interpretation difference would
  change comparability with Fable's probes, not my internal consistency.

## 8. A better way

The equal-a confounder (4.6) has a clean fix: for one event per search, chosen by the
same 1/8 cadence, toss a coin and ADD or REMOVE one ply of reduction beyond the formula
(observe-only otherwise). The fired/not-fired comparison of that random +/-1 is
unconfounded by construction, and the same probe machinery prices it. It answers
"does one more ply of reduction at THIS node class cost score" directly, which is the
tunable question; the current tables answer it only through the confounded lens.
Check that it is better: the randomized estimate's sign for cut_node should agree with
the match result of LmrCutNode=1 vs =2 that glmflash5 can run today; if they agree, the
observational table was misleading and the randomized probe becomes the calibration tool.

## 9. UTC stamps (all from recorded commands; full block in tests_kimi5_job7/stamps.txt)

- run start (step 1 fetch): 2026-11-16T10:48:52Z
- claim pushed: 2026-11-16T10:49:49Z
- prediction committed and pushed: 2026-11-16T10:51:27Z
- plain build done, step 0 run: 10:53:36Z-10:54:0xZ
- flag builds A/B done: 10:55:3xZ; K1 runs + probe runs: 10:56:15Z-10:57:20Z
- planted-fault control: 10:58:1xZ; option builds and proofs: 10:59:44Z-11:03:19Z
- report written and committed: see stamps.txt tail

## 10. Model

kimi-k3 (Kimi K3, Cursor cloud agent), one run, no memory beyond this text and GitHub.
