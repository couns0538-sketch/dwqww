# STATUS — swarm/rule50tt

**State: complete for what the design can reach. Pushed. No patch proposed.**

## Delivered

| branch of `score_usable` | verified? | how |
|---|---|---|
| A — exact-clock short circuit | **verified**, and shown to pre-empt B | 43-cell object harness through the real `store()`/`probe()`; 262 M verdicts in live search |
| B — mate distance past 100 | **verified** | `90+15` refused at clocks 91/95/86; accepted at 90 (branch A) |
| C — inside horizon | **verified** | 142,928 verdicts in live search; object rows for 10→20, 10→89, 89→10 |
| D — outside horizon | **verified** | 37 M verdicts in live search; stored≥90 and current≥90 both refused |

## Headline results

- **Stale-clock reuse did not change a score** in 7 boards × one clock pair, and the
  same-clock warm control reproduces every change — so the drift is warm-table, not
  clock provenance. Negative.
- **The guard is load-bearing at clocks 80–88**: removing it moves scores by up to **524 cp**
  (kqk_a clock 80: 1013 → 489) on 18 of 40 cells.
- **The 90 constant sits on a plateau**: `<89` differs on 3 of 40 cells, `<91` on 4, all at
  clock 85. Above 90 the twin `near50` guards and the `+depth<100` conjuncts decide, not 90.
- **The drawn-root bail stores nothing**: 0 stores on 5 bail cases against 12 / 6,952 / 40,629
  on search controls. A planted clock-100 zero is accepted only at clock 100.

## Withdrawn (all in FINDINGS.md)

1. The first threshold sweep — shared-process design, measured table warmth.
2. Two hand-written expectations in the object harness (my arithmetic, not the code's).
3. A bail classifier that reported "NO BAIL REACHED" while 5 real bails were on screen.
4. A fixture generator that emitted illegal boards.

## Gaps, stated rather than hidden

- **The eval-channel path at clock ≥ 90 through an in-check evasion near 99.** The SHAPE is
  now confirmed reachable — three roots put a node at clock 100 on the PV via a quiet king
  move (§6) — but all three returned `cp 0`, so the warm/cold differential there is a
  **weak null**: a drawn score has nowhere to show a stale one. Still not demonstrated.
- **The clock-97 false draw is now ATTRIBUTED**: it is the rule-50 **leaf** rule, not the TT.
  `always_true` (TT guard removed entirely) returns the same `cp 0` at clock 97, and
  `rule50_damped_static` scales eval by 0.03 there. The report's open question is answered
  in the negative for the TT — see FINDINGS.md §6.
- Threads 1, fixed depth only. No self-play corpus.

## Evidence index

| file | what it is |
|---|---|
| `evidence/pins.txt` | the four pins, from `pins.sh` |
| `evidence/object_harness_shipped.json` | 43 cells, all landed, 0 mismatches, both controls fired |
| `evidence/plan_objects.csv` | the plan, expectations from the independent Python model |
| `evidence/branch_sweep.json` | 77 searches, per-branch counters, 1 timeout recorded |
| `evidence/stale_fresh.json` | the warm/cold design, 3 repeats, 0 unstable cells |
| `evidence/aa_control.json` | the A/A that caught the withdrawn sweep |
| `evidence/threshold_fresh.json` | thr89 / thr91 / no_horizon, fresh process per cell, 0 unstable |
| `evidence/mate_first.json` | pre-`d9a8587df` ordering vs shipped, 48 cells, 0 differences |
| `evidence/bail.json` | 5 bails (0 stores) + 4 search controls |
| `evidence/poison_probe.txt` | a planted clock-100 zero, accepted only at clock 100 |
| `evidence/evasion.json` | 5 in-check roots; 3 reach a clock-100 node on the PV |
| `evidence/evasion_diff.json` | warm/cold on those boards (weak null) + the clock-97 sweep |

## Scripts

`pins.sh` · `make_plan.py` · `tt_probe_harness.cpp` · `score_usable_table.cpp` ·
`analyse_table.py` · `branch_power.py` · `make_variants.py` · `make_mate_first.py` ·
`fresh_diff.py` · `report_stale.py` · `aa_control.py` · `sweep_branches_final.py` · `exp_evasion.py` · `exp_evasion_diff.py` ·
`threshold_sweep.py` · `exp_bail.py` · `poison_probe.cpp` · `uci_driver.py` ·
`make_fixtures.py` · `guard_power.py` · `sweep_branches.py` · `sweep_threshold.py`
(the two shared-process sweeps, retained as the withdrawn designs their successors fixed)

No binaries, no `__pycache__` committed.
