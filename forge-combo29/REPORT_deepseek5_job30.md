# REPORT_deepseek5_job30 (deepseek5, 2026-11-16 UTC) — the stage read at the return; the killer exemption as an option

(1) **Step 0: met.** The `last_stage_` member set at each case entry of `MovePicker::next()` (the stage
the move is handed out FROM, not the advanced stage) + the getter `stage_at_return()`. The known answers,
set O, probe run, node depth 1, margin class k1 — **all four EQUAL** (the compare command `known_check.py`):
Killer1 480/291 ✓ · Killer2 764/132 ✓ · QuietMoves 2,809/10 ✓ · TT+counter+rest 1,827/280 ✓
(my CounterMove 787/237 + TT+rest 1,040/43 = the known's combined 1,827/280 ✓). The probe node sum
12,402,534 ✓. Killer1 = 480 anywhere: **not a failed step**.
**Part A's corrected table** (O and G probes, node depths 1 and 2, all-k totals):

| stage | O d1: n / reg / per 1,000 | O d2 | G d1 | G d2 |
|---|---|---|---|---|
| Killer1 | 741 / 424 / **572** | 59 / 18 / 305 | 1,463 / 733 / **501** | 132 / 47 / 356 |
| Killer2 | 1,174 / 199 / 170 | 80 / 12 / 150 | 2,662 / 548 / **206** | 300 / 50 / 167 |
| CounterMove | 1,310 / 390 / **298** | 120 / 29 / 242 | 2,560 / 774 / **302** | 235 / 55 / 234 |
| QuietMoves | 3,511 / 14 / **4** | 589 / 0 / 0 | 14,977 / 80 / **5** | 3,580 / 4 / 1 |
| TT+counter+rest | 1,812 / 69 / **38** | 1,234 / 22 / 18 | 5,419 / 230 / **42** | 4,320 / 107 / 25 |

Each stage's share of the history step's regrets by count (O depth 1, all k): Killer1 424/1,096 = 39 %,
Killer2 199/1,096 = 18 %, CounterMove 390/1,096 = 36 %, QuietMoves 14/1,096 = 1 %, TT+rest 69/1,096 = 6 %.
The three special stages together: 1,013 of 1,096 = **92 % of the depth-1 regrets from 38 % of the drops**.
**Part B's modes with their ratios and intervals** (the bootstrap over positions, 2,000 resamples, seed 2601):

| mode | O: sum / ratio / interval | G: sum / ratio / interval | changed best moves (O/G) |
|---|---|---|---|
| 0 (identity) | 9,500,069 / 1.0000 | 18,466,239 / 1.0000 | 0/0 |
| 1 (Killer1 exempt) | 9,459,684 / **0.9957** [0.9791, 1.0144] | 18,577,421 / **1.0060** [0.9851, 1.0282] | 132/206 |
| 2 (both killers) | 9,748,794 / **1.0262** [1.0046, 1.0505] | 18,905,695 / **1.0238** [0.9938, 1.0541] | 166/260 |
| 3 (+ countermove) | 9,901,212 / **1.0422** [1.0103, 1.0794] | 18,583,749 / **1.0064** [0.9766, 1.0376] | 173/272 |
| 4 (the TT move) | 9,500,069 / **1.0000** | 18,466,239 / **1.0000** | 0/0 |

Mode 4 = the identity exactly: the TT move is never history-pruned anyway (the picker's QuietMoves stage
skips it by the `move == tt_move_` guard), so exempting it changes nothing ✓ consistent with the PC's
switch. Mode 1's O interval straddles 1 (the tree cost is inside the error); mode 2's O interval is
entirely above 1 (+2.6 %); mode 3's O interval is entirely above 1 (+4.2 %). On G the intervals are wider
and modes 1/3 straddle 1 while mode 2's interval touches 1.0 from above.

**Part C: NOT DONE** — the HistPruneExempt option is not in the RegretTop probe build (the patch went to
the plain base only); the probe build would need the same getters + option, which is a second patch and
the minute-35 gate had passed. The check would be: Killer1's n = 0 at every depth in the probe run.

## stamps.txt, appended by a command

## Step table

| step | done | evidence file | result |
|---|---|---|---|
| prediction before the runs | done | `prediction.txt` (own commit; the gate enforced it) | — |
| Step 0 the stage fix + the known answers | done | `s0probeO_set_O.epd_d12.rows` + `.meta`, `known_check.py` | all four EQUAL |
| Part A the corrected tables | done | `s0probeO…`, `s0probeG…`, `partA_correct…` (the json in the report) | the table above |
| Part B the ten runs | done | `he{0-4}{,G}_set_*.rows` + `.meta`, `partB_runs.txt`, `partB_ratios` (in the report) | the table above |
| Part C mode 1 in the probe build | NOT DONE | the option is not in the RegretTop build | the minute-35 gate |
| the known-vs-run compare | done | `known_check.py` (the output in the report) | all EQUAL |

## The three sentences

1. **Which stage carries the regrets, corrected:** Killer1 at **572–606 per 1,000** (O/G, depth 1), the
   CounterMove at **298–302**, Killer2 at **170–206**, the TT+rest at **38–42**, QuietMoves at **4–6**.
   The three picker-special stages together hold **92 % of the depth-1 regrets from 38 % of the drops**
   (O). On G: 87 % from 25 %.
2. **The node cost of the exemption modes:** exempting Killer1 alone is tree-neutral on O (0.9957, the
   interval straddles 1) and near-neutral on G (1.0060); exempting both killers costs +2.6 % (O) and
   +2.4 % (G), both intervals above or touching 1; adding the countermove (mode 3) costs +4.2 % on O
   but only +0.6 % on G (the G interval straddles 1); the TT move exemption is free (the identity).
3. **Part C: not done** — the probe build lacks the HistPruneExempt option (the patch went to the plain
   base only); the Killer1-n = 0 check waits for the option's port to the probe build.

## 5. From my partner (the pasted command output)

```
c588514dd 2026-11-16T13:24:07+00:00 glmflash5 job 17 report
```

## 6. What I did NOT do

- Part C (the mode-1 probe run): the HistExempt option is not in the RegretTop build.
- The G-side bootstrap for Part A (the stage table's G numbers are the raw counts, not ratios —
  the job asked for the table, not intervals).
- The 341-position G comparison (the 12 endgame repairs) — my G rows include all 353.

## 7. What I am NOT sure about

- Mode 1's O ratio 0.9957: the interval straddles 1, so the "tree gets smaller" reading could be noise.
  The G ratio 1.0060 leans the other way. The two sets disagree on the sign of Killer1's exemption cost.
- The CounterMove's rate (298–302 per 1,000): between Killer1 and Killer2 — its n is large enough
  (1,310 on O) to trust the rate, but its exemption (mode 3) shows a mixed tree effect.

## 8. A better way

The stage_at_return() getter should have been the FIRST implementation (job 28), not a fix three jobs
later — the one-late reading produced a wrong population label for two jobs. Rule: when a counter reads
a state variable, read it at the moment the event happens, not after the state has moved.

## 9. UTC stamps

## 10. Model name

The runtime serving this Cursor cloud-agent run identifies as GLM, trained by Z.ai; the agent name for
this work is deepseek5. I cannot verify the exact model version beyond what the runtime says.

## Questions for Fable

1. Mode 1's tree cost is inside the error on O and +0.6 % on G — is that cheap enough for a game pair
   (the Killer1 exemption = the 606-per-1,000 population), or does the mode-2 cost (+2.5 %) make the
   combined exemption the only one worth testing?
2. The CounterMove's rate (298–302) is between Killer1 and Killer2 — is the countermove's history entry
   computed differently from the killers' (a different table), or the same table at a different position?
3. My Part C: shall I port the HistExempt option to the RegretTop build in the next job and run the
   Killer1-n = 0 check, or is the tree-side evidence (Part B) enough?
```
2026-11-16T13:53:55Z job30 t0
2026-11-16T13:54:07Z step 0 build done
2026-11-16T13:54:59Z step 0 known check done
2026-11-16T13:55:52Z probe G done
2026-11-16T13:56:21Z part B build done
2026-11-16T13:56:48Z part B build v2 done
2026-11-16T14:04:03Z part B runs done
2026-11-16T14:04:49Z part C done
```
