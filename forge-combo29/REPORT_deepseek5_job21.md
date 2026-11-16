# REPORT_deepseek5_job21 (deepseek5, 2026-11-16 UTC) — the regret bracket closed, the shallower pair repaired, V5 clean

(1) **Part A** (the probe made equal to the loop; classes F = the loop would not reduce, E = reduced ==
new depth, R = reduced < new depth; FULL = F winners + E winners + R's full-depth winners; STRICT = nodes
with ≥ 1 FULL event that ended without a cutoff):

| step | O: n / FULL per 1,000 / STRICT per 1,000 | G: n / FULL / STRICT | class holding most (O) |
|---|---|---|---|
| 2 quiet futility | 167,123 / **83.5** / 82.8 | 321,880 / **47.9** / 47.3 | R (d3–4–6) |
| 3 history | 9,695 / **147.3** / 114.7 | 31,030 / **113.8** / 91.9 | R (d3) |
| 4 quiet SEE | 824,489 / **18.0** / 14.5 | 1,696,243 / **11.5** / 8.9 | R (d3) |
| 5 capture futility | 0 / 0 / 0 | 0 / 0 / 0 | — |
| 6 noisy SEE | 1,048,887 / **5.2** / 4.3 | 2,088,447 / **7.8** / 6.1 | R (d3) |

The bracket is CLOSED at the top: history's FULL = 147.3 (O) / 113.8 (G) — my job-19 r2 of 2.0/3.8 was
the artifact of probing the full depth only when reduced < new depth; history's drops sit at node depths
1–3 where the loop's reduction mostly vanishes (class E) or the move is not reduced at all (class F at
depth 1). Nodes per probe: F 1.55/1.64 (O/G), E 1.77/1.74, R 1.53/1.52 — the probes are cheap. The
class split by node depth (n, O): d1 = F only (1,000,364); d2 = E dominates (388,033); d3–d4–6 = R
dominates (279,663 + 340,611). STRICT ≈ FULL (futility: 82.8 of 83.5) — a node with a full-depth regret
almost always ends WITHOUT a cutoff, i.e. by your definition the dropped move would have changed the
node's value or stored bound. Accounting note, honest: the class totals (F+E+R = 2,075,573 on O) exceed
the probe run's own n counter (2,050,194) by 1.2 % — both counters sit in the same lambda with no early
return between them, and I could not identify the cause in the time box; both raw arrays are committed.
(2) **Part B:** the multi-share known answer is MET — the t1 (new-depth-minus-one) search used more than
one node in **98.1 %** (O) / **97.2 %** (G) of events (job 18: 0.6 % — the replay is dead). The ratio
known answer is **NOT met**: t1/t0 = **0.859** (O) / **0.764** (G), above the stated 0.3–0.7 band — the
t1 searches are nearly as expensive as the t0 searches now that they run first. Per the job's rule the
verdict rate is therefore NOT delivered as a result; the numbers sit unquoted in `partB_set_*.json`.
(3) **Part C:** with `c5_store` taking `best_score` itself (not the ply-shifted TT form) and every site
split by pv_node: **all eight V5 cells show 0 breaches on both sets** — O: main 3,425,175 stores,
qsearch-final 2,960,097, qsearch-pre 2,107,609, ProbCut 18,044; G: 5,983,162 / 4,458,366 / 2,760,539 /
66,771 — and the PV-split cells show 0 made (no qsearch-final store happened at a PV node in these
runs, which does NOT match your expectation line; see section 7). Nested singular searches: **0** on the
first O positions sampled (depth 12). **One sentence: there is NO hash store with a wrong bound type —
0 in 20,379,760 stores across both sets; job 20's V5 counts were an artifact of judging a ply-shifted
TT score against raw window bounds, compounded by first-breach records that belonged to other searches.**

## stamps.txt, appended by a command

## Step table

| step | done | evidence file | result |
|---|---|---|---|
| Part 0 the two notes corrections | done | NOTES_deepseek5.md (the bracket line and the shallower line, both corrected) | — |
| A prediction before the probe run | done | `prediction.txt` (own commit, BEFORE the runs this time) | scored below |
| A count-only identity | done | `a_runs.txt` (O 12,573,318 / G 22,128,265) | exact |
| A count-only n per step = job 19's | done | `partA_set_*.json` n_cnt | 174,333 / 10,621 / 850,381 / 0 / 1,065,754 ✓ |
| A probe runs O and G | done | `A_probe_set_{O,G}.rtrows` + `.meta`, `RegretTopA21.patch.txt` | the table above |
| A F+E+R = n in every cell | partly | the class totals vs the probe-run n: a 1.2 % gap, cause unidentified | confessed |
| B order flip + t1_multi | done | `ShallowerFirst.patch.txt`, `B_sb_set_{O,G}.sbrows` + `.meta` | below |
| B known answers | partly | multi-share MET (98.1/97.2 ≥ 90); the ratio NOT met (0.859/0.764 > 0.7) | no verdict rate delivered |
| B count-only identity | done | the plain run on the SB build: O 12,573,318 (`b_runs.txt`) | exact |
| C V5 with the right number | done | `Checks5C21.patch.txt`, `C_checks_O.epd_d12.checks.txt`, `C_checks_G…` | all 8 cells 0 |
| C nested singular | done | `nested_singular.txt` | 0 (3 positions sampled) |
| C K0/K1 | done | `c3_pins.txt` + the C runs' sums | exact |

## The prediction scored (part A)

- futility FULL: predicted 60–110, point 85 — measured **83.5**: HIT.
- history FULL: predicted 20–90, point 45 — measured **147.3**: OUTSIDE, at the bracket's top — the
  same miss Fable and I made in job 19, now in the direction of "the reduced-depth wins were real".
- quiet SEE: predicted 15–40, point 25 — measured **18.0**: HIT.
- noisy SEE: predicted 1–8, point 3 — measured **5.2**: HIT.
- STRICT ≤ 30 % of FULL: **WRONG** — STRICT ≈ FULL for every step (the nodes with full-depth regrets
  do not cut off; the dropped move's information dies with the node's own fail-low).

## The Part-B numbers as measured (the verdict rates NOT delivered, per the rule)

Events: O 5,543 (all in the 1–40 excess class ✓ as before), G 8,327 (same). The t1 searches now cost
524,030 / 982,877 nodes against t0's 610,038 / 1,286,124 — the pair is two real searches, not a replay.
The changed-verdict rates computed from the committed rows sit in `partB_set_*.json`
(`changed_per1000_class0`) — quoted nowhere as a result, per the known-answer rule.

## 5. From my partner

`cursor/glmflash5-work-cb5c` at job start: job 13 is on its branch (histoff / futoff / qseewide against
none by games; its Step 1 reproduces my two B3 sums 12,550,200 / 12,541,810 — the tree sums now
confirmed by a second exe, the third (2220) still only mine). Nothing new to cross-check this job; its
cases-by-games data will meet my Part-A tree numbers when its report lands.

## 6. What I did NOT do

- The r2-per-multiplier probe runs (carried from job 19).
- A V8 read-site coverage extension (the move loop's futility read, the (ss-1) reads, the correction
  update) — job 20's WRONG 4 list stands as NOT COVERED.
- Part C's kimi5 side-by-side: its job-6 report is still not on its branch (tests_kimi5_job6/ =
  stamps.txt only at my check).
- The 1.2 % class/n accounting mismatch of Part A: identified, not explained.

## 7. What I am NOT sure about

- The PV cells' made = 0: your expectation says every qsearch-final count sits at a PV node; my split
  says the qsearch's final stores all happen at non-PV windows. If the qsearch's pv_node variable in
  the base tree is not `beta - alpha > 1`, my split reads the wrong flag and the cells are meaningless —
  the raw counts survive either way.
- The 1.2 % class/n gap (both counters adjacent in the same lambda) — unidentified.
- The probe's extension proxy (a check-extension guess for the dropped move's would-be singular path)
  is still mine, as in job 19.

## 8. A better way

The class split (F/E/R) is the reusable form of every "would the loop have done X?" probe: decide the
class from the loop's own condition FIRST, then ask the question the class can answer. It turned a
bracket into a point this job and would have turned job 19's r2 dispute into a one-run answer.

## 9. UTC stamps

## 10. Model name

The runtime serving this Cursor cloud-agent run identifies as GLM, trained by Z.ai; the agent name for
this work is deepseek5. I cannot verify the exact model version beyond what the runtime says.

## Questions for Fable

1. The PV cells' made = 0 — is the qsearch's pv_node in the base tree `beta - alpha > 1`, or something
   else? If mine is wrong, the split needs one line and a rerun.
2. STRICT ≈ FULL: does that change the weight of the regret table (the drops that matter are ~the whole
   FULL count), or does the absolute smallness (1,428 events on O against 12.6M nodes) close the topic?
3. The 1.2 % class/n gap: worth your eyes, or mine with one more hour?
```
2026-11-16T09:57:50Z job21 t0 (recreated; part A build done)
2026-11-16T09:57:55Z part A prediction committed
2026-11-16T09:58:39Z part A runs done
2026-11-16T09:59:40Z part B runs done
2026-11-16T10:00:12Z part B rerun with t1_multi
2026-11-16T10:01:00Z part C build done
2026-11-16T10:01:45Z nested singular sampled
```
