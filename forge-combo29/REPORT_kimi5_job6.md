# kimi5 job 6 report: the search's own invariants, counted for the first time

(1) K0 met with AND without the flag (bench 11 = 312,866, bench 13 = 862,329, go perft 5 =
4,865,609 on both exes; step-0 bench 16 = 3,024,920); K1 met (no-flag tree, set O depth 12:
12,573,318, first three 18,407 / 25,756 / 64,000); K2 met (flag build, same numbers to the
node); K3 met (flag build, set G depth 12: 22,128,265 = my job-5 "none" sum). The THREE
plants are caught, each by exactly its own invariant (a fourth, first attempt at the
history plant, was inert and is reported as my mistake, superseded by the caught one).
(2) 18 invariants checked at 70 counter sites; 888,114,529 checks made across the four
measured runs; ONE invariant has breaches: V5, at one of its four store sites.
(3) V5.store-qfinal (qsearch final hash store, src/search.cpp:1539-1543): 19,021 / 28,821 /
8,286 / 14,649 breaches on the four runs = 1,513 / 1,302 / 441 / 2,214 per million nodes.
Cause: the stand-pat alpha raise at search.cpp:1482 lets a non-cutoff qsearch node store
UPPER with a score above the entry alpha. Judged HARMLESS (the stored value is still a
valid upper bound of the qsearch value; section "Part 4"). Every other strict invariant:
no breach in the counts of section "The counts".

## Prediction against the result
- V4 (mate from early returns): predicted ProbCut + both hash cutoffs + stand-pat CAN,
  razoring rare, RFP / null / multi-cut CANNOT. CONFIRMED to the site: ProbCut 74 / 2,433 /
  7,389 / 31, tt-cutoff-search 646 / 19,912 / 20,174 / 311, tt-cutoff-qsearch 200 / 3,674 /
  3,029 / 103, stand-pat 11 / 268 / 71 / 19, razor 0 / 3 / 5 / 0, RFP 0, null 0, multi-cut 0
  (O d12 / G d12 / G50 d16 / O50 T4 d12).
- V5: predicted HOLDS at all four store sites. REFUTED at the qsearch final store (the
  stand-pat case I argued away with "alpha tracks best_score" — I missed that the raise at
  1482 leaves best_move empty, so the UPPER branch is taken with score > alpha-at-entry).
- V6: predicted the picker DOES hand out the excluded move and the loop blocks all of them:
  33,497 / 115,247+ handouts, 0 reaching make_move; static_eval survives the singular search
  in 29,263 of 29,263 checked. CONFIRMED.
- V7: predicted nonzero hash-move rejections. REFUTED: 0 rejections in 884,644 + 1,859,745
  pseudo-legal tests and 832k + 1.68M legality tests (O / G). The two-level test never fires
  on these sets.
- V11: predicted main-history extreme in [12000, 16384]: measured 15,873 (O) — and the
  bound can SATURATE: main 16,384, capture 16,384, continuation 16,384, correction 8,192 on
  single searches of the G50 d16 run (equality allowed, never crossed).
- All other strict invariants (V1, V2, V3, V8, V9, V10, V12, V13, V14, V15, V16, V17, V18):
  predicted HOLDS, CONFIRMED with 0 breaches (made counts in agg_*.txt).

## Step 0 (honesty check, base exe from 6b98f217, fresh process per line, raw files)
- k0_bench11.txt: nodes 312866. k0_bench13.txt: nodes 862329. k0_bench16.txt: nodes
  3024920. k0_perft5.txt: nodes 4865609. All exact.

## The table
| step | done | evidence file | result |
|---|---|---|---|
| claim + stamps start | done | CLAIM_kimi5_job6.txt, tests_kimi5_job6/stamps.txt | claimed 09:49:15Z |
| step 0 | done | tests_kimi5_job6/k0_bench{11,13,16}.txt, k0_perft5.txt | 4/4 exact |
| Part 1 prediction (own commit, unedited) | done | tests_kimi5_job6/PREDICTION.md | commit "kimi5 job 6 prediction" |
| Part 2 patch SearchChecks.patch.txt | done | tests_kimi5_job6/SearchChecks.patch.txt | applies with patch -p1 from repo root (dry-run clean), 951 lines, search.cpp only |
| K0 with and without flag | done | k0f_bench11/13.txt, k0f_perft5.txt, k0n_bench11/13.txt, k0n_perft5.txt | 312866 / 862329 / 4865609 both |
| K1 no-flag tree, O d12 | done | k1_noflag_O_d12.json(+meta, input log) | 12,573,318; 18,407/25,756/64,000 |
| K2 flag, O d12 | done | k2_flag_O_d12.json, _checks.txt | identical to K1 to the node |
| K3 flag, G d12 | done | k3_flag_G_d12.json, _checks.txt | 22,128,265 (= job-5 none sum; set G sha256 == deepseek5_job10's) |
| positive control: 3 plants | done | plant1/2b/3.diff.txt, plant1_O10_d8_checks.txt, plant2b_O10_d8_checks.txt, plant3_O10_d8_checks.txt, plant2_inert.diff.txt | 3 caught by exactly their own invariant; one inert first attempt disclosed |
| Part 3 counts (4 runs) | done | agg_k2.txt, agg_k3.txt, agg_g50d16.txt, agg_o50t4.txt + raw *_checks.txt | section "The counts" |
| Part 4 (V5.qfinal) | done | p4_smallest_d1_checks.txt, p4_one.fens; analysis below | cause + smallest input + harmless verdict; no repair (reason given) |
| Part 5 sanitizers (allowed: Part 4 analysis done before minute 32) | done | p5_san_O50_d10_full.txt, p5_san_O50_d10.json; sanitizer plant below | ASan+UBSan clean on O50 d10; plant reported, exit 1 |
| harness | done | tests_kimi5_job6/k5_j6.py | pure stdlib, .meta + refusal stop, waits for bestmove |

## The counts (Part 3; per-site made / breaches, summed over all searches of the run)
Full tables: agg_k2.txt (O, 200 pos, d12, T1), agg_k3.txt (G, 353 pos, d12, T1),
agg_g50d16.txt (G first 50, d16, T1), agg_o50t4.txt (O first 50, d12, T4, counters summed
over threads; no node sum known). Totals of the "made" column: 185.5M / 327.5M / 276.2M /
98.9M = 888,114,529 checks. Rows with a nonzero breach column (all runs):

| site (file:line of the check) | O d12 | G d12 | G50 d16 | O50 T4 | reading |
|---|---|---|---|---|---|
| V5.store-qfinal (search.cpp:1539-1543) | 19,021 | 28,821 | 8,286 | 14,649 | the one real deviation, Part 4 |
| V6.store-under-excluded (2093) | 33,427 | 115,247 | 140,170 | 24,048 | NOT breaches: arrivals where the excluded guard SUPPRESSED the store (guard works) |
| V6.ttcut-under-excluded (1637) | 33,497 | 116,755 | 141,901 | 24,083 | NOT breaches: tt cutoffs the excluded guard suppressed (would-have-fired count) |
| V4.tt-cutoff-search (1643) | 646 | 19,912 | 20,174 | 311 | mate scores returned, by design counted |
| V4.tt-cutoff-qsearch (1454) | 200 | 3,674 | 3,029 | 103 | " |
| V4.probcut (1777) | 74 | 2,433 | 7,389 | 31 | " |
| V4.standpat-cutoff (1481) | 11 | 268 | 71 | 19 | " |
| V4.razor (1686) | 0 | 3 | 5 | 0 | " |

Every other site: 0 breaches. Key exercised-but-clean counts (O d12 / G d12): V1.search
9.9M / 18.7M, V1.qsearch 5.6M / 12.0M, V2.child-score 12,573,318 / 22,128,265 — EQUAL to
the engine's own node sums, an internal consistency check — V3 same, V7.make-* 12.1M /
20.9M, V13.key-* 12.3M / 22.4M, V8.* reads 12.5M / 25.1M, V10.* 12.4M / 22.6M plus 2,400 /
4,232 root-PV replays, V11.* 7.9M / 12.8M updates, V12 9.9M / 18.7M, V14 2,400 / 4,232
iterations, V15 9.2M / 15.4M stores, V16 97,812 / 208,273 root moves, V17 200 / 353,
V18 11.5M / 21.9M early keys, V6.make-excluded 9.5M / 17.3M with 0 excluded moves made,
V6.static-eval-survives 29,263 / 67,834 unchanged.

NOT REACHED (checks made = 0 in ALL four runs; option-gated code that defaults off):
V8.capture-futility (CaptureFutilityBase = 0), V8.extinction-tight (QuietExtinction off),
V8.hindsight-parent (HindsightDepth off), V8.signed-correction (LmrSignedCorrection off),
V9.deeper-shallower (LmrDeeperShallower off), V11.hist-threat (ThreatHistory off),
V11.corr-nonpawn-w/b (NonPawnCorrection off). V4.null-verify: reached only on G50 d16
(1,069 verification searches, 0 mate returns); the d12 runs never verify (depth < 14).
Extremes (CHECKX lines, last search per run): max ply vs root depth 18/12, 20/12, 29/16,
25/12 — extensions add up to +13 plies; max consecutive double extensions 1 / 2 / 3 / 3
(cap 7 never approached); history extremes in the prediction table above.

## Part 4: V5.store-qfinal — cause, smallest input, verdict
- Cause, with file and line: qsearch's stand-pat block sets `best_score = eval`
  (src/search.cpp:1473) and raises alpha without a move (`if (best_score > alpha)
  alpha = best_score;`, search.cpp:1482). When no capture/check then beats best_score and
  the node is not PV (or is PV but no move raised alpha), the final store at
  search.cpp:1539-1543 picks BoundUpper with best_score above the alpha the node started
  with. The strict invariant "UPPER only with score <= entry alpha" (my Part-1 wording)
  does not hold for this site.
- Smallest input (one position line + one go): `position fen
  rnb1kbnr/ppp1pppp/8/4q3/8/2N5/PPPP1PPP/R1BQKBNR w KQkq - 2 4` then `go depth 1` →
  `info string CHECK V5.store-qfinal 20 8` and CHECKFIRST (ply 5, score 531, alpha0 420,
  beta 32001). Evidence: p4_one.fens, p4_smallest_d1_checks.txt (+ its first-run sibling
  p4_smallest_V5qfinal.txt, kept: it documents that a `quit` raced into the pipe aborts a
  depth-1 search after 1 node — the wait-for-bestmove rule).
- Can it change a move or a stored bound? Only a number's classification, not a move and
  not a wrong bound. The stored UPPER value remains a VALID upper bound of the qsearch
  value: stand pat (eval <= best_score) is one option of the node, every capture is either
  searched with the full qsearch window (-beta,-alpha at search.cpp:1520) and returned
  <= best_score, or skipped with its futility estimate folded INTO best_score
  (search.cpp:1496-1497), or refused as SEE-losing (1500). A reader cuts on UPPER only
  when `tt_score <= alpha` (search.cpp:1451-1453, 1637-1642), which a valid upper bound
  justifies. VERDICT: harmless; a convention of the alpha-beta qsearch family (stand-pat
  is a lower bound on the node value, the store is the tight upper bound), not a defect.
- Repair: NONE offered, by decision: every alternative is unsound or strictly worse —
  BoundExact would overstate skipped-move estimates, BoundLower is no sounder and breaks
  bound symmetry, suppressing the store loses real reuse. If Fable wants the strict
  invariant back, the honest change is in the counter's definition (UPPER means
  "no searched move beat alpha-at-entry"), not in the engine. No-op proof and
  count-at-zero are therefore not applicable; stated plainly instead of fabricating a patch.

## Part 5: sanitizers
- Positive control first: san_plant.cpp (heap write one past a 4-int malloc), built with
  the same g++ -fsanitize=address,undefined: AddressSanitizer reports
  heap-buffer-overflow, exit code 1 (san_plant_out.txt committed as
  p5_sanitizer_plant.txt — copied below in evidence list).
- The flag build (FORGE_SEARCH_CHECKS=1) under ASan+UBSan (-O1, RelWithDebInfo flags):
  first 50 of O at depth 10: 1,175,574 nodes, ZERO sanitizer lines in the full captured
  output (p5_san_O50_d10_full.txt, grep count 0), node sum identical to the unsanitized
  flag build's earlier partial run of the same set/depth.

## From my colleagues
- Read: deepseek5 NOTES (jobs 16-19) and newest reports list (REPORT_t23.md is the tip);
  glmflash5 NOTES (jobs 5-11) on its real branch `cursor/glmflash5-work-cb5c` (Fable's
  correction in the job file applied; the branch in the first message does not exist).
- Applied: deepseek5's table-replay warning (a probe at equal/lower depth after another on
  the same node and window replays the hash) — my build NEVER re-searches; counters only
  observe the real tree, so the job-5 disturbance class is absent by construction.
  glmflash5's sha256-pair rule applied to my copied build trees (each plant exe was rebuilt
  from its own source dir, and plant node sums differ from the checks build as expected).
  The strip-the-FEN lesson (deepseek5 LEARNED 2) is in my harness (.strip() at read).
- Checked: K3 reproduces my job-5 "none" sum on G (22,128,265) on a fresh tree with a fresh
  harness; set G in tests_kimi5_job5/set_G.epd is byte-identical to deepseek5's
  tests_deepseek5_job10/set_G.epd (sha256 af3aefd8...). deepseek5's job-18 note that the
  in-check picker stages never read skip_quiets matches what I count here (evasion stages
  untouched by my checks).

## What I did NOT do
- No repair patch for V5.qfinal (verdict harmless; reasoning in Part 4, not laziness).
- The Threads-4 run has no known node sum (per the job) — no equality claimed for it.
- No games played, no Elo. No per-position breach histograms (the per-search CHECK lines
  in the raw *_checks.txt carry them; agg_*.txt are the sums). plant2 (inert) was not run
  beyond its 10 positions once seen inert; it is disclosed, not hidden.
- Part 5 was run only on O50 d10 (the job's scope), no wider sanitizer sweep.

## What I am NOT sure about
- The near50 paths (halfmove >= 90, `score_usable`, rule50 clocks) are unexercised by O/G
  (low clocks); the UPPER-above-alpha0 convention near the 50-move horizon is unmeasured.
- Whether V5.qfinal should be DOCUMENTED as intended behavior (Fable's call, question below).
- V7 counting quiet tt moves in qsearch: the picker drops non-capture/non-promotion tt
  moves at search.cpp:585-588 BEFORE the loop, so V7_LEGAL_Q "made" counts only
  capture/promotion hash moves; the pseudo-legal test at 584 runs before that drop and
  counts them. The two counters measure different sets by construction.
- The suppression counts V6.store/V6.ttcut are printed in the breach column of their sites
  (my naming mistake from Part 1's design; semantics documented in the counts table).

## A better way
- Print three columns (checks made / expected events / violations) instead of two. My V6
  and V4 sites put designed-to-fire events in the same column as true violations, which
  forced the recount distinction in every table above. With three columns, "breaches" alone
  would be the alarm channel Fable can grep.
- Gate the print behind a UCI option (counters compiled in anyway): 70 lines per search is
  fine for harness runs but would flood game runners' logs if a helper ever matches a
  flag build. One `setoption` and the same binary serves both.
- The V2.made == node-sum identity (12,573,318 / 22,128,265 to the node) is the cheapest
  cross-check a counter build can have: any future check build should print both sums side
  by side; a difference localizes the bug to the counter or the node accounting instantly.

## UTC stamps (every step; start of the run first) — `cat stamps.txt` put here by a command
STAMPS_BLOCK

## Model name
Kimi K3 (one cloud run; no memory of earlier runs beyond what is on GitHub).

## Folder state — `git status --short` and `ls forge-combo29/tests_kimi5_job6` after the last commit (put here by a command)
STATUS_BLOCK
