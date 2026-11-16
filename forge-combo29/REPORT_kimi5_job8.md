# kimi5 job 8 report — the four node-level steps: what they return on, and what those returns MISS

First three lines, as ordered:
1. K0, K1, K2, K4 all MET (every number of Fable's K2 list to the digit, K4 clean in all 1,506+200 searches of
   all runs); control (1) FIRED (rfp MISSED/1000: 40.5 at RfpMargin 10, 9.5 at 72, 2.2 at 300 — the 300 arm
   needed N_RFP=100 for n=3129; at N=1000 it read 13.4 on n=224, small-n noise, both runs committed);
   control (2) FIRED (planted restore-removal reported by k4c viol in 3 of 5 searches, k4t clean).
2. Sentence 1: MISSED per 1,000 returns, defaults / S14 (set O; n beside): razoring 34.1 / 33.9, reverse
   futility 9.5 / 5.6, null move 0.4 / 0.0, ProbCut 0.5 / 0.6. The ONE class holding the most missed returns
   by COUNT is razoring at node depth 1: 44 of 105 missed on O-defaults, 456 of 771 on G-defaults.
3. Sentence 2: under S14 on O, quiescence-null returns: 0 contradicted in 1,732 probes; real-search null
   returns: 0 in 30 — NullMoveBase 5 is NOT paid for with wrong cutoffs here (and on G the quiescence class
   contradicts LESS than the real-search class: 10.0 vs 57.1 per 1,000). Sentence 3: no rfp class over
   100/1,000 (max 87.2, G-defaults depth-1 margin<1.25); the bulk class "3 margins and more" is NOT under
   5/1,000 (9.2 on O depth-1 n=872, 14.0 on G depth-1 n=2069) — but every rfp miss in all four runs sits at
   node depth 1; above depth 1 the rate is 0 everywhere.

## 1. What was asked, the answer, how sure (three lines)
Asked: count the four pre-move-loop steps of `src/search.cpp` 1680-1781 (razoring, reverse futility, null
move, ProbCut) by node depth and margin class, then probe returns: re-search the node at its own depth and
window with the four steps off at that node only, and count how often the search contradicts the step's
claim. Answer: contradictions are a razoring story (34-42/1,000, worst at depth 2 by rate, depth 1 by
count) and a depth-1 reverse-futility story (9.5-23/1,000, all misses at depth 1); the null move contradicts
~0 on the 200 openings but 10-12/1,000 on the 353 game positions (depths 3-8); ProbCut essentially never
(0.5-0.6/1,000). How sure: the counting half is exact (K1/K2/K4 to the node against Fable's and the
engine's own counters); the probe half is a measurement with a fired margin-gradient control and a fired
planted-fault control, samples of 224-14,447 probes per table (thin cells marked *), and a stated
disturbance of 0.4-3.2% in node sums.

## 2. Step 0 known numbers (raw output files)
Base build bA (g++ 13.3.0, default x86-64-v4; machine has avx512f+bmi2, so NOT the portable build):
`k0_bench11.txt` 312,866; `k0_bench13.txt` 862,329; `k0_bench16.txt` 3,024,920; `k0_perft5.txt` 4,865,609.
Flag build bS (FORGE_NODE_STEPS=1): `k0f_bench11.txt` 312,866; `k0f_bench13.txt` 862,329;
`k0f_bench16.txt` 3,024,920; `k0f_perft5.txt` 4,865,609. All four match, both builds.
(One environment note: `/usr/bin/c++` here is clang 18, which cannot link -lstdc++; CMake must be given
`-DCMAKE_CXX_COMPILER=g++` — the job's "GCC's own C++ library" rule. My first configure failed on this;
recorded in stamps.txt.)

## 3. Step table
| step | done | evidence file(s) | result |
|---|---|---|---|
| claim + job file + colleagues | done | CLAIM_kimi5_job8.txt; NOTES_deepseek5/NOTES_glmflash5 (their branches) | job 8 = lowest open; glmflash5's branch is `cursor/glmflash5-work-cb5c` (no `for-fable-and-opus/glmflash5-work`) |
| base build + K0 | done | k0_bench11/13/16.txt, k0_perft5.txt | all four match |
| Part 1 prediction (own commit, unedited) | done | tests_kimi5_job8/prediction.txt | committed 12:52:02Z before any measurement |
| Part 2 patch (FORGE_NODE_STEPS=1) | done | tests_kimi5_job8/NodeSteps.patch.txt | applies `patch -p1 --fuzz=0`; observe-only (K0 identical with flag) |
| K1 four runs | done | k1_def_O_d12, k1_s14_O_d12, k1_s14_G_d12, k1_def_G_d12 (.json/.meta/checks/input.log) | 12,573,318 / 9,500,069 / 18,466,239 / 22,128,265 + all first-3s — all match |
| K2 defaults-O counters | done | agg_k1_def_O_d12.txt | every K2 number matches: GATE 5,762,433; razor 41,581/40,265; rfp 2,440,126 classes 247,948/225,310/399,659/590,799/976,410; null 171,326/122,928/0 verif; ProbCut 71,211/18,044 (my pc_caps 22,111 had no known) |
| K3 (S14 totals + all G, held back by Fable) | done (my lines committed) | agg_k1_s14_O_d12.txt, agg_k1_s14_G_d12.txt, agg_k1_def_G_d12.txt | for Fable's comparison |
| K4 every search | done | k4t/k4c fields of every NSTEPS line; agg files count viols | 0 violations in 200+200+353+353 counting searches and all probe searches |
| Part 3 probe build (FORGE_NODE_REGRET=1) | done | same patch, second flag; probe design in patch comments | healthy build K4-clean everywhere |
| control (1) margin gradient | done | r5_rfp10_O_d12, r1_def_O_d12, r6_rfp300_O_d12, r7_rfp300N100_O_d12 + agg_*.txt | FIRED: 40.5 (n=1703) > 9.5 (n=2315) > 2.2 (n=3129) per 1,000 |
| control (2) planted fault | done | plant_j8.diff.txt, plant_O5_checks.txt, agg_plant_O5.txt | FIRED: k4c viol 3/5 searches (mine 2,685 vs engine 2,713), k4t 0 viol |
| probe runs (defaults O, S14 O, S14 G, defaults G) | done | r1..r4_* + agg_*.txt | all four done (nothing dropped); disturbance 0.4-3.2% |
| Part 4 three sentences | done | section "Part 4" below | cells printed by agg_j8.py --rates |
| final-patch re-verification | done | v_def_O_d12 + agg_v_def_O_d12.txt | after adding #ifndef N overrides: sums 12,573,318 and K2 totals identical |
| report + notes + push | done | this file, NOTES_kimi5.md | — |

## 4. Part 4, with the cells the command printed
Command for every cell: `python3 tests_kimi5_job8/agg_j8.py <run>_checks.txt --rates` (output in agg_*.txt).
Probe N: razor every 16th return, rfp every 1000th, null every 50th, ProbCut every 8th (per-search counters;
the per-search floor effect is measured and reconciled in section 7). MISSED = probe lands on the other side
of the node's window than the returned value (side judged by the returned value, so a margin-0-or-less
return below beta is handled). Probes ending on the node's first hash read (ended1) and non-null windows
(wide): 0 in every run.

Sentence 1 (table: MISSED/1,000, missed/n):
| step | def O | S14 O | S14 G | def G |
|---|---|---|---|---|
| razoring | 34.1 (81/2377) | 33.9 (41/1209) | 35.6 (304/8529) | 41.7 (603/14447) |
| reverse futility | 9.5 (22/2315) | 5.6 (11/1947) | 12.1 (48/3967) | 23.1 (107/4623) |
| null move | 0.4 (1/2369) | 0.0 (0/1762) | 11.8 (55/4672) | 10.0 (57/5697) |
| ProbCut | 0.5 (1/2142) | 0.6 (1/1790) | 0.5 (3/6591) | 0.6 (5/8135) |
By COUNT the biggest single class on both sets is razoring at node depth 1 (def O 44 of 105, def G 456 of
771 missed; its sibling cell depth 2 has the higher RATE on O: 48.4 vs 27.3).

Sentence 2 (null under S14, by depth handed to the null search):
- O (S14): quiescence-null returns 0/1,732 probes contradicted; depth-1-2 null searches 0/30; 3+ none
  occurred. Defaults O: 1/2,369 total. NullMoveBase 5 is not paid for with wrong cutoffs on these 200
  openings.
- G: quiescence class contradicts at 10.0/1,000 (45/4,497) under S14 vs 8.1 (27/3,347) at defaults;
  real-search class at 57.1 (10/175, thin) under S14 vs 12.8 (30/2,350) at defaults. The quiescence shift
  moved ~1,600 returns into the quiescence class WITHOUT raising its rate.
- The wrong null returns on G sit at node depths 3-8 (def G: d3 10.9 n=1101, d4 7.8 n=1532, d5-6 9.7
  n=2062, d7-8 15.4 n=777; S14 G similar with d7-8 32.6 n=583).

Sentence 3 (reverse futility): no class above 100/1,000 (max: 87.2 at def-G depth-1 margin<1.25, n=195).
The bulk ">=3 margins" class is NOT under 5/1,000 (def-O d1 9.2 n=872; def-G d1 14.0 n=2069; class across
depths def-O 8/920 = 8.7). Every rfp miss in all four runs is at node depth 1 (depth 2+: 0 misses in
10,000+ probes). The depth-1 gradient by margin ratio (def G): 87.2 / 58.0 / 28.7 / 26.2 / 14.0 for
<1.25/<1.5/<2/<3/>=3.

## 5. Findings (source, with file and line)
- The block: `src/search.cpp` 1680-1781. Gate (1680-1681): non-PV, not in check, no excluded move, beta not
  a mate score, no `go mate`, halfmove+depth<100. On O-defaults 5,762,433 nodes pass it; reverse futility
  alone returns 2,440,126 of them (42% of the gated nodes), confirming Fable's "one step ends ~19% of all
  nodes". Reproduce: `agg_j8.py k1_def_O_d12_checks.txt` TOTALS line.
- Razoring (1683-1687) claims "below alpha" after only a quiescence check, at depth <= 2 with eval at least
  500-850 below alpha (RazorBase 150 + RazorMultiplier 350*depth). It is the WRONGEST step by count:
  34-42/1,000 of its returns are contradicted by a full search of the same node — the full search finds a
  quiet resource the qsearch could not see. Rate rises from depth 1 to depth 2 on O (27.3 -> 48.4).
- Reverse futility (1689-1692) contradicts only at node depth 1 (all 22/22 def-O, 107/107 def-G misses) —
  where the "search" it replaces is closest to the static eval it trusts. By margin ratio the rate falls
  from ~35-87/1,000 (<1.25 margins) to ~9-14/1,000 (>=3 margins): the margin works, but the >=3 bulk class
  is not free (not under 5/1,000).
- Null move (1693-1743): on O essentially never wrong (1/2,369); on G wrong 10-12/1,000, at node depths
  3-8, in both builds — the zugzwang/threat class the reduced null search cannot see exists in real game
  positions, not in the opening set. Under S14 (NullMoveBase 5) the null search is a quiescence at node
  depths 3-7 always (8-9 when eval-beta >= 200/400): prediction (b) confirmed about WHICH depths; its
  expected effect (more wrong nulls) REFUTED on O (0) and on G the quiescence class contradicts less than
  the real-search class.
- ProbCut (1745-1779): 0.5-0.6/1,000 — the qsearch + depth-4 re-search at a raised beta almost never both
  agree wrongly. Not a candidate.
- Prediction (d) verified TRUE in this source: the depth-14 verification (1734) clears
  `ss->null_move_allowed` at 1733 and restores it at 1737 on its OWN frame; no child frame ever receives
  the flag (only root init 2341 and the struct default `include/forge/search.hpp`:414). One ply below the
  verification the null condition (1695) reads true again; the only remaining bar is the no-adjacent-null
  rule (`!(ss - 1)->current_move.is_none()`, 1696). A two-move zugzwang under a verified node is not
  protected. (At `go depth 12` no node reaches depth 14: verifications = 0 in all runs, matching K2's 0.)
- Part 1 (c) stands: make `24 * depth + 180` (1693) an option first — it is the null move's only eval-based
  admission filter and this job's harness already splits null tries/returns by eval-beta and node depth.
- Prediction (a) scored honestly: razoring predicted 40, measured 34.1 (best); rfp predicted 25, measured
  9.5; null predicted 20, measured 0.4 (O) / 10.0-11.8 (G); ProbCut predicted 5, measured 0.5-0.6. I
  overestimated every beta-side step; the direction "razoring worst, ProbCut safest" was right.

Suspicions, not proven:
- The rfp depth-1 ">=3 margins" rate (9.2) sitting ABOVE the "<3" rate (4.0) on O — non-monotone tail;
  n=872, possibly noise, possibly correction-history interactions at big eval-beta.
- The G-set null contradictions look like real zugzwang/threat cases, but I did not inspect a single
  probed position by hand; the class pattern (depths 3-8, both builds, both splits) is the evidence.

## 6. From my colleagues
- deepseek5 (notes after jobs 24/26/28 + cross3; REPORT_deepseek5_job28 exists, skimmed): applied its
  index rule — every counter's meaning is a comment AT the increment line (see the patch), and the one
  committed command (`agg_j8.py`) reads labels from one schema and prints `lines_summed`. Its row-format
  collision lesson: my runner keeps counter lines in a SIDE file (`*_checks.txt`), never in pipe rows.
  Its K2/cross-check culture: the engine prints mine/engine with viol fields on every line; K4 is checked
  per search, not per run.
- glmflash5 (notes after jobs 13-16): "pruning steps are bets, not neutral" — held; and its S14 bridge
  numbers (tree 12,573,318 -> 9,500,069 under S14) reproduced here to the node on my build too (K1).
  Branch-name note for Fable's addressing: glmflash5 works on `cursor/glmflash5-work-cb5c`; there is NO
  `for-fable-and-opus/glmflash5-work` ref.
- Also read: deepseek5's REPORT_t23 (mate/50-move faults on another base) — background only, not applied.

## 7. What I did NOT do
- No strength claims, no search-changing patch, no matches (the job's rule): the tables only say where a
  match is worth playing (razoring depth 1-2; rfp depth-1 tight margins; null on game positions at S14).
- The depth-14 verification path is unmeasured (no such nodes at depth 12): prediction (d) is a source
  reading, not a measurement.
- The margin<=0 rfp class was exercised only in the RfpMargin-10 control (rate 44.7/1,000 at depth 1,
  n=738; judged by returned-value side per the job's rule).
- No per-position case studies of contradicted nodes; no N variants for razor/null/ProbCut (only rfp).
- d9+ cells are thin in most tables (marked * by the aggregator; n<200).

## 8. What I am NOT sure about
- Probe counts reconcile exactly only after the per-search floor effect: the every-Nth counters reset per
  search (with the counters), so probes = sum over searches of floor(seen/N) — e.g. def-O rfp 2,410,340
  returns -> 2,315 probes, not 2,410. Reconciled numerically (script output in the report folder's
  agg files); no probe leaked unclassified (ended1=0, aborted never happens at fixed depth).
- Probes ride the live hash table and histories (declared not restorable): they are cheap (~11 nodes avg
  on O) precisely because the TT is hot after the node's first visit. A cold-table probe might contradict
  more or less; the disturbance numbers (node sums vs K1: -0.97% / +2.31% / -3.24% / +0.38%) bound how far
  the probe run's tree drifts.
- The two RfpMargin-300 runs (13.4/1,000 at n=224 vs 2.2/1,000 at n=3,129) probe different events (N
  differs) on slightly different trees; I read the dense one, the sparse one is committed for the record.
- Whether "all rfp misses at node depth 1" survives other depths than fixed 12, or the net change on the PC.

## 9. A better way (and questions for Fable)
- Probe where the misses live: a deterministic event predicate (rfp: only node depth 1; null: only node
  depth >= 3; razor: keep all) would roughly double the useful samples per clock at the same N. Checkable:
  rerun def-G with the filter; per-class rates must match this job's within noise while class n doubles.
- Carry the every-Nth PHASE across searches of a run (counters still reset per search for K4): recovers
  ~4% probes at N=1000 and ~3% at N=50 for free; the events stay deterministic per run.
- Questions: (1) Should a next job hand-inspect a few contradicted null returns on G (are they zugzwang,
  or threat-blindness the 14-verification would not catch either)? (2) Is the razoring depth-1/2
  contradiction rate the match candidate you expected, or do you want the "razor only at depth 1"
  option measured first? (3) The internal stamp inside prediction.txt is wrong by ~13 min (my clock
  misreading; git stamp is true) — leave as is per "never edited", confirmed?

## 10. UTC stamps and model name
Times: see stamps.txt (run start 12:48:10Z; claim 12:48:53Z; all run windows from the .meta files; report
committed well inside the 50-minute budget). Model name from my runtime: Kimi K3 (kimi-k3).
