# REPORT_deepseek5_job22 (deepseek5, 2026-11-16 UTC) — the regret curve: where on the margin the regrets sit

(1) **Part A, the four repairs:** A1 the runner (one diff loop over all five depth classes, refusal-stop
after every option and every go, the .meta written by the runner in the same process, output in this
folder) — its control run with `RegretTopCountX` **STOPPED** (`a1_control.txt`: `REFUSED: info string
unknown option RegretTopCountX`). A2 the count-only run on the job-22 exe: O **12,573,318** exact; G
**22,128,261** — 4 nodes UNDER the known 22,128,265 (see the honesty note); n per step O 174,333 /
10,621 / 850,381 / 0 / 1,065,754 and G 331,857 / 31,152 / 1,787,926 / 0 / 2,106,890 — **exact**; by
depth O: d1–3 167,362 / 10,475 / 517,993 / 0 / 1,030,666, d4–6 6,456 / 140 / 306,239 / 0 / 35,087,
d7+ 515 / 6 / 26,149 / 0 / 1 — **exact to the node**; row 1 shows five depth classes. A3 the probe
with `rt_r1` back inside its `if`: O 15,674,184 (known 15,674,185 — **1 node under**), G 28,778,953
(known 28,778,975 — **22 under**); FULL per step O 13,947 / 1,428 / 14,811 / 0 / 5,483 and G 15,406 /
3,532 / 19,485 / 0 / 16,230 — **exact**; the class totals 2,075,573 / 4,247,643 — **exact**; and now
F + E + R = n in every cell (the runner's second loop that dropped class 7+ is gone). A4 the clamp
test prints **0 0 0** (`a4_clamp.txt`) — job 19's depth-1 probes searched at depth 0, i.e. they were
the loop's own qsearch verdicts.
(2) **Part B, the curve** (FULL per 1,000 dropped moves in each k class; n from the count-only run,
O; the probe run's n in the committed json):

| step | k=1 | k=1.5 | k=2 | k=3 | k=5 |
|---|---|---|---|---|---|
| 2 quiet futility (O) | **104.9** (n 62,620) | 80.8 (72,478) | 27.6 (33,957) | 20.4 (4,885) | 22.8 (393) |
| 3 history (O) | 130.8 (7,076) | 172.3 (2,296) | 148.2 (1,057) | 173.0 (187) | 166.7 (5) |
| 4 quiet SEE (O) | 17.1 (176,919) | 0.0 (6,716) | 3.0 (66,835) | **34.6** (276,054) | 6.0 (323,857) |
| 6 noisy SEE (O) | **8.6** (519,855) | 5.2 (120,763) | 0.4 (123,136) | 0.6 (94,430) | 0.5 (207,570) |
| 2 futility (G) | 52.8 | 69.3 | 26.3 | 8.6 | 5.8 |
| 3 history (G) | 94.0 | 122.3 | 167.0 | 156.5 | 184.2 |
| 4 quiet SEE (G) | 12.0 | 0.6 | 2.1 | **26.3** | 5.8 |
| 6 noisy SEE (G) | **12.8** | 7.1 | 5.1 | 3.8 | 1.0 |

One sentence per step (O): **quiet futility** — taking the margin 1.5 times would spare 62,620 of the
174,333 drops (36 %) and remove 6,841 of the 13,947 FULL regrets (49 %): the rate FALLS with k (104.9 →
~21), the test knows something and its margin is the question. **history** — the rate is FLAT to RISING
(130.8 → 166.7 across k on O; 94 → 184 on G): the history margin does not tell good drops from bad
ones, and it is the most expensive test per regret at every k. **quiet SEE** — the rate is NON-monotone
with a clump at k=3 (34.6 per 1,000 of 276,054 drops): the SEE distribution has real mass between 3×
and 5× the margin; the k=1.5 class is empty. **noisy SEE** — the rate FALLS monotonically (8.6 → 0.5):
the test separates well; its bare-margin drops carry most of the few regrets.
(3) **Parts C and D:** the three settings' count-only sums on O: `HistoryPruneMultiplier 20000` =
**12,537,494** (= your known, exact), `FutilityBase 500 + FutilityMultiplier 500` = **12,668,896**
(= yours, exact), `SeeQuietMultiplier 200` = **13,061,439** (yours 13,061,442 — **3 nodes under**, the
same harness-order sensitivity as A2's 4). Drops left under each setting beside the default's n
(174,333 / 10,621 / 850,381 / 0 / 1,065,754): **HPM 20000: history 0 left of 10,621 — the step is
switched off entirely** (and the OTHER steps' counts move with the tree: futility +1,441, quiet SEE
−328, noisy −8,364); futility 500/500: futility 774 left of 174,333 (the step nearly off), history
9,103, quiet SEE 894,782 (+44,401 — the tree shifts); SeeQuiet 200: quiet SEE 178,716 left of 850,381
(79 % of the drops gone), history 10,935 (+314), futility 171,996 (−2,337), noisy 1,066,468 (+714).
**Part D after the slot repair** (`C5_V5QPREPV + (v5 - C5_V5QPRE)`): qsearch-final at PV nodes
42,803 stores / **19,021** counts (O) and 82,762 / **28,821** (G); main|PV 112,834 / 0 and 269,665 / 0;
qsearch-pre|PV 25,958 / 0 and 52,559 / 0; every non-PV cell 0; the V6 lines back at 33,497 / 0 (O) and
116,755 / 0 (G); the store total of both sets **22,366,344** (printed by a command over the committed
checks files). Every V5/V6 known answer of Part D: **met**.

## stamps.txt, appended by a command

## Step table

| step | done | evidence file | result |
|---|---|---|---|
| A1 the runner + the control | done | `rt_run22.py`, `a1_control.txt` | stops on the unknown option |
| A2 count-only, known answers | done | `RegretTopCount+true_set_{O,G}.epd_d12.{rows,meta}` | exact except G's 4-node sum (below) |
| A3 probe, known answers | done | `RegretTop+true_set_{O,G}.epd_d12.{rows,meta}` | FULL/class exact; the sums 1 and 22 nodes under |
| A4 the clamp test | done | `a4_clamp.txt` | 0 0 0 |
| B1 the k cells, count-only | done | `RegretTopCount+true_set_O…rows`, `partB_tables.json` | the k classes sum to A2's n exactly |
| B2 the k cells, probe | done | `RegretTop+true_set_{O,G}…rows` | the k classes sum to A3's n and FULL exactly; the node sums as in A3 |
| B3 the curve | done | `partB_tables.json` | the table above |
| C the three settings | done | `RegretTopCount+true+*set_O…rows`, `c_runs.txt` | two sums exact, one 3 under; the drops-left table above |
| D the V5 slot repair | done | `Checks5D22.patch.txt`, `C_checks_*.checks.txt` | every known answer met |
| E the cutoff_count restore | done | the source in `RegretTopB22.patch.txt`, the E run's rows | the sum moved +321,451 (+2.05 %); FULL per step +2–3 % |

## The honesty notes

- The three tiny node deviations (G count-only 4, O probe 1, G probe 22, SeeQuiet 3): the same binary
  through the OLD harness gave the exact known sums in job 21; the new runner differs in the
  setoption/readyok ordering around `ucinewgame`, and the prime suspect is the TT-clear race it
  exposes (the async clear vs the first search). Not proven — said as measured.
- The probe-run sums' sensitivity is ALSO the Part-E effect: A3's sums carry the cutoff_count leak;
  after the restore the O sum moves +321,451. The known answers were taken on the leaky build; Part E
  explains why two correct builds can differ by a few hundred nodes, though not the 4-node count-only
  case (count-only never probes).
- Part B's FULL-in-k-cells sums to A3's FULL exactly on both sets, and the k classes sum to A2's n
  exactly on O — the two new counter families are consistent with the old ones.

## 5. From my partner

`cursor/glmflash5-work-cb5c`: job 13's report is still not on its branch at my check (job 12 is its
newest). Its Step-1 reproduction of my B3 sums (two of three) stands; the third (2220) is now
three-source (Fable's PC + mine ×1).

## 6. What I did NOT do

- The Part-E probe runs on G (O only — the clock).
- A game-side follow-up on the curve (Part B's sentence is a tree statement; whether sparing 36 % of
  the futility drops at the cost of 6,841 kept regrets is worth Elo is glmflash5's job 13 territory).
- The k classes for step 5 (it never fires at defaults; n = 0 in every run).

## 7. What I am NOT sure about

- The 4-node count-only deviation's cause (the TT-clear race hypothesis is unproven).
- The quiet-SEE k=3 clump (34.6 per 1,000 on a 276k class): the SEE distribution's shape at depth 12 —
  real structure or the ldd² scaling's artifact; the raw per-depth cells are in the json.

## 8. A better way

The k class was computed at the drop site with three extra read-only comparisons per drop — the same
information could be carried by ONE division (the margin ratio) instead of four threshold tests, but
the integer-exact class boundary (the job's "3/2 applied to the whole product") is what makes the
classes reproducible; keep the threshold tests.

## 9. UTC stamps

## 10. Model name

The runtime serving this Cursor cloud-agent run identifies as GLM, trained by Z.ai; the agent name for
this work is deepseek5. I cannot verify the exact model version beyond what the runtime says.

## Questions for Fable

1. The quiet-SEE k=3 clump: worth a per-depth split of that cell (the raw rows carry it), or is the
   ldd² threshold's shape explanation enough?
2. Part E: with the leak fixed the probe run costs +2 % nodes and finds +2–3 % FULL events — should
   the leak fix become part of the RegretTop patch for all future jobs (it makes the probe sums
   reproducible)?
3. The 4-node count-only deviation: if your build through MY new runner also gives 22,128,261 on G,
   the harness-order sensitivity is confirmed and worth one line in the harness spec (the isready
   after ucinewgame must WAIT for the TT clear, not just for readyok).
```
2026-11-16T10:15:09Z job22 t0
2026-11-16T10:15:09Z A4 clamp test done
2026-11-16T10:15:20Z A1 runner + control done
2026-11-16T10:15:23Z A1 control done
2026-11-16T10:46:25Z A2+A3 runs done
2026-11-16T10:47:21Z A2+A3 runs done
2026-11-16T10:48:01Z part B build done
2026-11-16T10:48:06Z part B build done
2026-11-16T10:48:15Z part B build done
2026-11-16T10:48:56Z B1+B2 runs done
2026-11-16T10:49:09Z B rerun with k fields
2026-11-16T10:49:51Z B rerun done
2026-11-16T10:50:48Z B rerun with k_n
2026-11-16T10:51:34Z part C runs done
2026-11-16T10:52:00Z part D runs done
2026-11-16T10:52:19Z part E run done
```
