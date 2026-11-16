# REPORT — deepseek6, long 17 (my own eleven node-step counters on the plain base, S14, O and G)

for-fable-and-opus/deepseek6-work · folder tests_deepseek6_long17/ · CLAIM.txt before the first command; PREDICTION.md before the first counted run.

## 1. Three lines
**Asked:** build a counter copy of the plain base with one counter per statement for the eleven node steps (gate, razor try/ret, rfp ret, null try/≥beta/cut/verify, ProbCut enter/cut, iir), bucketed by node depth 1..8 and 9+, verify its rows equal the plain rows, and commit the totals on O (against your held-back numbers) and G.
**Answer:** the counter copy's rows equal the plain build's on every position (O 200/200, G 353/353, nodes and moves). All ten placement relations hold on both sets (razor_ret ≤ razor_try ≤ gate; rfp_ret, null_try ≤ gate; null_ge ≤ null_try; null_cut ≤ null_ge; null_verify ≤ null_ge; pc_cut ≤ pc_enter; rfp the largest step; iir > 0). **My O totals under S14 (depth buckets summed): gate 4,049,383 · razor_try 20,834 · razor_ret 20,274 · rfp_ret 2,001,770 · null_try 130,889 · null_ge_beta 92,956 · null_cut 92,956 · null_verify 0 · probcut_enter 65,000 · probcut_cut 15,160 · iir 353,529.** G totals committed below. If any total differs from your held-back number, the per-depth bucket lines localize where my placement sits.
**How sure:** certain of my own counts (observation-only copy, row-identical trees, one NS17 line per search, 200 + 353 searches); the placement match against your numbers is exactly what your held-back comparison will judge.

## 2. Honesty numbers (counter build /tmp/l17_ctr/build/forge sha b6470525…)
bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609 (honesty_*.txt).

## 3. Step table
| step | done | evidence | result |
|---|---|---|---|
| ns17_counters.patch.txt (text patch, diff -u) | done | ns17_counters.patch.txt | eleven counters at the named statements, 9 depth buckets, observation only |
| counter build + pins | done | honesty_*.txt | four exact |
| rows == plain rows | done | totals.txt | O 200/200, G 353/353, nodes and moves |
| runs O and G under S14 | done | runs/O_s14.ns17, runs/G_s14.ns17 (one line per search) | 200 + 353 searches captured |
| prediction relations | done | totals.txt | all ten relations OK on both sets; depth profile as predicted |
| R5 planted fault | done | plant_evidence.txt | ASan heap-buffer-overflow, READ of size 4, exit 1 |
| R5 clean sanitizer | done | san/O_s14_d12.rows | 0 lines / 200 positions |
| prediction own commit first | done | PREDICTION.md | all five items held |

## 4. The totals (searches summed with agg in totals.txt; buckets are depth 1,2,...,8,9+)
O (S14): gate 2698287,631797,339698,176125,93082,58046,30613,13242,8493 · razor_try 15411,5423,0… · razor_ret 14897,5377,0… · rfp_ret 1775650,145749,45637,18673,9458,4363,1633,607,0 · null_try 0,0,27684,28810,26031,22085,14070,7115,5094 · null_ge_beta = null_cut = 0,0,23523,24767,21413,14412,5989,1973,879 · null_verify 0 (O) · probcut_enter 0,0,0,0,30508,18043,10071,4285,2093 · probcut_cut 0,0,0,0,6933,4310,2219,1044,654 · iir 0,218296,93681,29672,7399,3104,1033,273,71.
G (S14): gate 4839119,1264802,777935,479245,281591,198908,127668,69457,61302 (total 8,100,027) · razor_try 155,244 · razor_ret 145,048 · rfp_ret 4,294,595 · null_try 350,717 · null_ge_beta = null_cut = 245,298 · null_verify 12 (all at the 9+ bucket, and all twelve verifications confirmed the cutoff: null_cut == null_ge) · probcut_enter 223,494 · probcut_cut 58,446 · iir 610,786.

## 5. Findings
1. **null_cut == null_ge_beta exactly on both sets**: every null that reaches beta produced a cutoff return; on G the 12 verifications (all at depth 9+) all confirmed. The verification path is nearly dead at these settings (NullThreatVerify off by default; depth ≥ 14 unreachable at d12).
2. **rfp dominates the gate**: 2,001,770 of 4,049,383 gated nodes on O (49.4 %) return by reverse futility; 88.7 % of those sit at depth 1. On G: 53.0 %, 76.7 % at depth 1.
3. **The gate covers 42.6 % of the O tree** (4,049,383 of 9,500,069) and 43.5 % of G's — the static-pruning block is where almost half of all nodes live, matching kimi5's job-8 structure on its own base.
4. **iir fires 353,529 times on O (3.7 % of nodes)**, concentrated at depths 2–4 (83 % of its events) — the missing-hash-move reduction is a real, mid-depth effect.
5. Suspicions, not proven: my null_cut counts BOTH null cutoff return sites (direct and post-verification); if your counter counted only the direct one, the difference is exactly the post-verification cutoffs (0 on O, 12 on G).

## 6. What I read from my colleagues
kimi5's job-8 report (the same eleven statements counted on ITS base — my placements follow the job's words, not its file, so the comparison is independent); the peer's progress (long 10 done on its side). Nothing contradicts this report.

## 7. What I did NOT do
The V= variant counting (long 18's job). Nothing from this item.

## 8. What I am NOT sure about
Whether your "null cut" counts the post-verification return site (see suspicion 5) — the per-bucket lines decide it when your numbers arrive.

## 9. A better way
None; the per-statement, per-depth-bucket layout is the one the comparison needs.

## 10. times: see stamps.txt
## 11. model name my runtime gives: glm-5p3-flash

## 12. The last command before this report commit
```
$ git status --short
 M forge-combo29/tests_deepseek6_long17/stamps.txt
?? forge-combo29/REPORT_deepseek6_long17.md
?? forge-combo29/tests_deepseek6_long17/chkrun.py
?? forge-combo29/tests_deepseek6_long17/honesty_bench11.txt
?? forge-combo29/tests_deepseek6_long17/honesty_bench13.txt
?? forge-combo29/tests_deepseek6_long17/honesty_bench16.txt
?? forge-combo29/tests_deepseek6_long17/honesty_perft5.txt
?? forge-combo29/tests_deepseek6_long17/plant_evidence.txt
?? forge-combo29/tests_deepseek6_long17/runs/
?? forge-combo29/tests_deepseek6_long17/san/
?? forge-combo29/tests_deepseek6_long17/totals.txt
$ ls forge-combo29/tests_deepseek6_long17/
chkrun.py
CLAIM.txt
honesty_bench11.txt
honesty_bench13.txt
honesty_bench16.txt
honesty_perft5.txt
ns17_counters.patch.txt
plant_evidence.txt
PREDICTION.md
runs
san
stamps.txt
totals.txt
```
