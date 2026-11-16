# REPORT_deepseek5_job29 (deepseek5, 2026-11-16 UTC) — which early moves history pruning throws away wrongly

(1) **Step 0: met.** HistStage.patch.txt (counters only, on job 28's build) moves nothing: the four
runs under S14 = **9,500,069 / 12,402,534 (O)** and **18,466,239 / 24,206,937 (G)** — all four of your
known sums to the node; job 28's cells reproduced (the history by move number, count run O: 4,150 /
2,862 / 1,740 / 103; probe 5,088 / 3,742 / 2,226 / 253 with 1,184 / 130 / 52 / 1 regretted; G's probe
14,827 / 13,412 / 10,011 / 1,781 with 2,662 / 578 / 296 / 15) ✓.
**The three sentences:**
1. **The rise with k does NOT survive inside one exact move number.** The move-number × k cross
   (history, O probe, node depth 1): **move 2: 364 → 339 → 300 → 182 per 1,000 (FALLS)**; move 3:
   195 → 208 → 186 → 389 (n 18 at k3 — noise); move 4: 104 → 78 → 158 → 100 (noise); moves 5–8:
   32 → 33 → 57 → 67 (rises, n small). On G move 2: 298 → 277 → 290 → 273 (flat), moves 5–8: 42 → 39 →
   50 → 27. The aggregate rise of job 26/28 is the MIX of move numbers and stages, not a within-class
   effect. My prediction 2 was wrong: said plainly.
2. **The stage carries the wrong drops: Killer2.** The stage × k cross (O probe, depth 1): **Killer2:
   606 per 1,000 at k1 (n 480, F 292) falling to 389 at k3** — far above every other stage; CounterMove
   ~173–177 (flat); QuietMoves 4–7 (n 2,809–10,417); other ~125–153. On G: Killer2 522 → 400 (n 812 →
   55), CounterMove ~202–227, QuietMoves 4–6. The killers' history entries lie badly and keep lying
   after the margin widens; the ordinary quiets (QuietMoves) are nearly regret-free at every margin.
   The killers' share of the history FULL on O: the stage split's F by kind — Killer2's F share of the
   step = 1,002/1,367 = 73 % (the job-28 kind table) — the exemption candidate in substance.
3. **(f) The futility–history overlap is 0.29 % (O) / 0.33 % (G):** the futility drops that the history
   test would also drop: n 315 of 109,360 (F 32, rate 101.6 per 1,000) against the rest's 201.7; G: 856
   of 262,609 (F 100, 116.8) against 142.4. The two steps drop almost disjoint populations, and the
   small overlap regrets LESS than the rest — neither step covers for the other at the drop level; the
   Opus "both off −14.95" has to come from the search's dynamics, not from shared drops.

## The (e) table: the history parts for the drops with move number ≤ 4 (O probe; the means per part)

| part (from the source) | not-regretted mean | regretted mean | alone under the threshold |
|---|---|---|---|
| main history (`(*main_history_)[side][from][to]`) | **−2723.8** (n 3,829) | **−2290.5** (n 1,177) | 2,713 |
| continuation (ss−1) | −441.7 | −550.0 | 320 |
| continuation (ss−2) | −592.6 | −589.8 | 239 |
| continuation (ss−4)/2 | 0.0 (ContHist4PlyRead off under S14) | 0.0 | 0 |
| threat_quiet_bonus | 0.0 | 0.0 | 0 |

The mechanism, read off the cells: the regretted drops' MAIN history is CLOSER to zero (−2290 against
−2724) — the wider margin's survivors are the moves whose main history is least negative, i.e. the
margin's survivors are the moves the main history trusts MOST among the dropped — and they still fail.
The continuations point the other way (the regretted ones' cont1 is more negative: −550 vs −442). The
main history ALONE is under the threshold for 2,713 of the ~5,000 move-number ≤ 4 drops (54 %): the
main table drives most of the drops by itself. G's numbers agree (−2734 regretted vs −3087 not;
alone-under 8,742).

## stamps.txt, appended by a command

## Step table

| step | done | evidence file | result |
|---|---|---|---|
| prediction (the gate enforced it) | done | `prediction.txt` (own commit) | predictions 2 and 3 WRONG, 1 partly wrong — all said in the report |
| Step 0 the four sums + job 28's cells | done | `step0_runs.txt`, the rows+meta | all exact |
| Part A the new counters | done | `HistStage.patch.txt` (the full state), `partA_O_probe.json`, `partA_G_probe.json` | the tables above |
| Part B the exemption option | NOT DONE | — | the budget went to Part A's counters (two build-fix cycles); proposed as the next job's first item |

## 6. What I did NOT do

- Part B (the HistExempt option and its tree factors): not built in the budget — the counters took two
  build-fix cycles (the stage getter's placement, the enum's numeric values, the constant-expression
  error that vanished when the comparison moved out of the lambda).
- The (move number) × (eval−alpha) × k three-way cross (the confound remover for sentence 1).
- The stage split for node depths 3+ (the counters cover depths 1 and 2 only, per the job).

## 7. What I am NOT sure about

- The Killer2 population's smallness at the wider margins (n 480 → 18): the rates at k3 rest on tens of
  events; the FALL could be noise beyond k2.
- The stage bucket "other" (7,358 drops on O): it holds the picker's other stages (the bad captures'
  stage, the evasion stages) — my bucket lumps them; the killer story does not depend on it.

## 8. A better way

The stage getter (one line in the MovePicker) turned "which moves" into an answerable question at every
pruning site — it should be standard equipment in every counting build from now on, together with the
move number, because the two together explained in one job what three jobs of margin curves could not.

## 9. UTC stamps

## 10. Model name

The runtime serving this Cursor cloud-agent run identifies as GLM, trained by Z.ai; the agent name for
this work is deepseek5. I cannot verify the exact model version beyond what the runtime says.

## Questions for Fable

1. The Killer2 population (606 per 1,000 at k1, 73 % of the step's regrets on O): is the exemption
   "no history pruning of Killer1/Killer2/CounterMove moves" (your Part B's mode 1) the match to
   request from Opus, given that my Part B did not get built?
2. The regretted drops' main history being CLOSER to zero than the not-regretted's (−2290 vs −2724):
   does that match your PC-side data, or is my part accounting (the threat bonus excluded from the
   site's `history`) off?
3. The (f) disjointness (0.3 %): with Opus's "both off −14.95" the coverage must be dynamic — is that
   worth a counter of the REVERSE direction (the history drops the futility would have kept)?
```
2026-11-16T12:44:07Z job29 t0 + build
2026-11-16T12:45:22Z step 0 runs done
2026-11-16T12:48:26Z step 0 runs done
2026-11-16T12:51:42Z step 0 v2 done
2026-11-16T12:53:32Z probe reruns done
2026-11-16T12:55:19Z probe reruns v2
```
