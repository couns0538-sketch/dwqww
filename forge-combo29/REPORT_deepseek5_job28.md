# REPORT_deepseek5_job28 (deepseek5, 2026-11-16 UTC) — why the history margin's survivors regret more

(1) **Step 0: met.** The split patch (HistSplit.patch.txt, counters only) moves nothing: the count run on
O under S14 = **9,500,069**, the probe = **12,402,534**, G = **18,466,239** / **24,206,937** — all four of
your known sums to the node; the FULL per step 7,760 / 1,367 / 10,775 / 2,126 (O) and 9,131 / 3,551 /
15,344 / 9,356 (G) ✓; the history n by node depth 6,996 / 1,519 / 259 / 81 / 0 (count) and 8,548 / 2,082 /
401 / 275 / 3 (probe) ✓ — from the k_n arrays' depth index, confirming job 26's decode of the file layout.
**The three sentences, each with its cells:**
1. **Inside one (static eval − alpha) class the rate STILL rises with k — the rise is not (only) a node
   mix, but the biggest split is the MOVE NUMBER, which my cross does not control.** The cross table
   (history, O probe, node depth 1), rate per 1,000 by k = 1/1.5/2/3: (eval−alpha) −200..−51:
   119 → 128 → 133 → 167; −50..−1: 112 → 141 → 156 → (50, n 20); 0..49: **203 → 247 → 297 → 429**;
   200+: 56 → 53 → 74 → 81. The same rise on G (0..49: 148 → 167 → 204 → 267) and two plies deeper at
   depth 14 (−50..−1: 78 → 101 → 140 → 177; 0..49: 172 → 211 → 286 → 279). BUT the move-number split:
   **moves 1–4 regret 232.7 per 1,000 (F 1,184 of 1,367 = 87 % of the step's regrets) against moves 5–8
   34.7, 9–16 23.4, 17+ 4.0** — a 58× spread my cross ignores, so the within-class rise may still be the
   early-move mix; the (eval−alpha) × (move number) × k cross is the missing table.
2. **The exemption candidate and the safe part (O, the probe run):** the class with ≥ 250 per 1,000
   holding a fifth of the regrets: **none of the single splits reaches 250** — the closest is the
   move-number class moves 1–4 at 232.7 per 1,000 carrying **1,184 of 1,367 regrets (87 %)** — it IS the
   candidate in substance, a hair under your bar. The safe class under 30 per 1,000 holding a fifth of
   the drops: **moves 9–16 (23.4 per 1,000, n 2,226 = 20 %) plus 17+ (4.0, n 253)** — together 22 % of
   the drops at ~20 per 1,000. On G the same two: moves 1–4 = 179.5 per 1,000 with 2,662 of 3,551
   regrets (75 %); moves 9–16 = 29.6 with 10,011 drops (25 %).
3. **Futility (the comparison that behaves):** its (eval − alpha) split is degenerate — ALL drops sit in
   the < −200 class (the futility condition requires eval − alpha ≤ −margin), so (c) cannot split it; the
   informative splits are the MOVE NUMBER (moves 1–4: 83.1 per 1,000 with F 7,680 of 7,760 = 99 % of the
   regrets; moves 5–8: 6.9) and the node kind (pv 142.3, cut 141.5, neither 66.8) and improving
   (73.5 not-improving vs 92.0 improving — the improving moves regret MORE, the same direction as
   history's 107.0 vs 134.5). No futility class reaches 250 per 1,000; the safe fifth: moves 5–8 and
   later = 12,284 drops (11.7 %) at ≤ 6.9 per 1,000.
(2) **Part B (depth 14, O, S14):** the count run **21,812,100**, the probe **28,687,566**. Sentence 1
holds two plies deeper: the cross rates rise with k inside the (eval−alpha) classes (−50..−1: 78 → 101 →
140 → 177; 0..49: 172 → 211 → 286 → 279) and the move-number split dominates the same way (moves 1–4:
219 per 1,000, F 5,655 of 6,555 = 86 %). One line per split, no new tables.

## stamps.txt, appended by a command

## Step table

| step | done | evidence file | result |
|---|---|---|---|
| prediction before the runs | done | `prediction.txt` (own commit; the gate in the runner refused to start without it) | prediction 1 WRONG (the rise survives the eval split), said plainly |
| Step 0 the four known sums | done | `step0_runs.txt`, the rows+meta | all exact |
| Part A the splits + the cross | done | `HistSplit.patch.txt`, the rows, `partA_splits.txt` | the tables above |
| Part B depth 14 | done | the d14 rows | sentence 1 holds |

## The prediction scored

My prediction 1 ("within one (eval − alpha) class the rate should be flat or falling") is **WRONG**:
the cross rates rise with k inside every populated class (O d1: 119 → 128 → 133 → 167 in one class). My
prediction 3's direction (a high-rate class at node depth 1) is right in substance but the strongest
split is the MOVE NUMBER, which I did not predict. The mechanism your question asks for: the history
value is computed from what the move has done BEFORE this search; the moves that survive a wider margin
are the ones whose history lied — and they lie more the further below the threshold they start. The
move-number split says most of the lying happens among the first four moves tried.

## 5. From my partner

`cursor/glmflash5-work-cb5c` at my check: job 13's report still not on its branch. Nothing new to
cross-check; my Part-B S14 rows from job 26/27 remain its bridge data.

## 6. What I did NOT do

- The (eval − alpha) × (move number) × k cross — the table that would separate the two explanations of
  the rise; the counters for it are one more array in the same patch.
- The G depth-14 runs (O only, per the job's text).
- The futility cross table (its (c) split is degenerate — all drops in one class — so (c) × k for
  futility is empty by construction; the useful futility cross would be (move number) × k).

## 7. What I am NOT sure about

- The move-number split's causality: moves 1–4 at a node are the PICKER'S BEST moves (good ordering) —
  their high regret rate may be "the good moves' refutations matter" rather than "the history lied" —
  the two readings need the (move number) × k cross to separate.
- The improving split's direction (the improving moves regret more): n = 3,468 on O — small.

## 8. A better way

The splits should have included the move-number × k cross from the start: the move number is the
strongest single predictor in the data (a 58× spread) and it was one array away. Rule for my next
split design: before planting the splits, rank the candidate variables by how much they could spread
the rate — the move number was visible in the job-26 data (the LMP threshold's neighborhood) and I
missed it.

## 9. UTC stamps

## 10. Model name

The runtime serving this Cursor cloud-agent run identifies as GLM, trained by Z.ai; the agent name for
this work is deepseek5. I cannot verify the exact model version beyond what the runtime says.

## Questions for Fable

1. The move-number dominance (87 % of the history's regrets at 232.7 per 1,000): is the exemption
   candidate you wanted "the first four moves at a node keep their double-check" — i.e. an exemption by
   MOVE NUMBER rather than by margin?
2. Should the (move number) × k cross be the next job's first run (one array, one build, both sets)?
3. The futility split2's degeneracy: the whole step in one (eval − alpha) class — is FutilityBase's
   default the reason (the margin includes the base), or is my eval − alpha computed at the wrong point?
```
2026-11-16T12:22:44Z job28 t0 + split build
2026-11-16T12:25:14Z step 0 runs done
2026-11-16T12:30:12Z step0 + part B runs done
```
