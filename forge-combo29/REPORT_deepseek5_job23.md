# REPORT_deepseek5_job23 (deepseek5, 2026-11-16 UTC) — the double-extension cap and margin as options; kimi5's check build with the switches on

(1) **Step 0 and Part A: every control stopped and every known answer met.** S1/S2: the runner writes its
own `.meta` per rows file and stops on refusals — the control `DoubleExtLimitX` **stopped** (`a1_control_x.txt`)
and `DoubleExtLimit 65` **stopped** (`a1_control_65.txt`: outside the spin's range). S3: the block-summing
script prints "blocks summed: 200" (and 353) over kimi5's build (`k6_run.py`, the C1 file). Part A on O:
A0 the pins exact; A1 no option **12,573,318** (18,407 / 25,756 / 64,000) exact; A2 limit 4, limit 10,
limit 64, limit 6 explicit and margin 24 explicit — **each 12,573,318, equal to A1 on 200 of 200**; A3 all
eleven sums and differing-position counts **exact to the number**: limit 3 = 12,573,282 (3), limit 2 =
12,510,250 (13), limit 1 = 12,673,468 (48), limit 0 = 12,562,872 (136), limit −1 = 12,217,726 (195, first
three 18,422 / 25,152 / 53,004), margin 0 = 13,805,238 (200, first three 20,884 / 42,041 / 54,754), margin
12 = 12,991,342 (192), margin 48 = 12,700,011 (190), margin 96 = 12,377,094 (193), margin 400 = 12,211,314
(195); margin 0 with limit 64 = margin 0's rows **on 200 of 200**. A4's M-rule: for L = 3, 2, 1, 0, −1 —
"positions that differ: 3 / 13 / 48 / 136 / 195; of them outside the allowed list: **0**" — every differing
position has M > L + 1 in kimi5's own per-search records (`a4_m_rule.json`).
(2) **Part B on G** (the ratio to the base, the bootstrap 95 % interval over positions, 4,000 resamples,
seed 2301; the differing positions; the M-rule check): limit −1 = **0.8984 [0.8533, 0.9451]** (343 differ);
limit 0 = 0.9471 [0.9085, 0.9879] (325); limit 1 = 0.9622 [0.9297, 0.9952] (260); limit 3 = 0.9967
[0.9737, 1.0222] (108); limit 10 = 0.9954 (25); **limit 64 = 0.9954 [0.9877, 1.0010] (25 — all 25 have
M = 7, i.e. the cap binds only inside the 47 M = 7 searches, as your known answer says)**; margin 0 =
**1.1067 [1.0515, 1.1623]** (346); margin 12 = 1.0489 (334); margin 48 = 0.9992 (341); margin 96 = 0.9491
(342). **B3, the first 50 of G at depth 16:** no option **18,795,747** = kimi5's check build's sum, exact;
limit 64 = 18,874,209 (ratio **1.0042** — the cap's sign FLIPS with depth: at 12 removing it saves 0.46 %,
at 16 it costs 0.42 %); limit −1 = 16,004,400 (ratio **0.8515** — the double extension costs ~15 % at
depth 16 against ~10 % at depth 12: it GROWS); margin 48 = 17,820,905 (0.9481). **B2's counting build was
not built in the budget** (see section 6).
(3) **Part C:** C1 on kimi5's build (its flag on, my block-summing runner): all five known sums **exact**
(V2.child-score 12,573,318 / 0; V5.store-qfinal 3,002,900 / 19,021; V4.tt-cutoff-search 728,887 / 646;
V6.ttcut-under-excluded 6,929,385 / 33,497; V7.make-search 9,507,236 / 0) with "blocks summed: 200"; the
nine listed sites all **NOT REACHED** at the defaults (0 made). The S2 stop control on the guard-less
build: `MateAlphaGuard` → **REFUSED: unknown option** ✓. C2: all four known V2 sums **exact** —
NonPawnCorrection 11,949,131; LmrDeeperShallower 11,254,768; ThreatHistory 13,003,036; the eight together
12,474,415 — and `bench 13` with the eight = **868,694** exact. C3's answer: a count that is 0 at the
defaults DOES become non-zero with a switch on — `V11.corr-nonpawn-w` and `V11.corr-nonpawn-b` reach
952,566 reads each with NonPawnCorrection; the CHECKX maxima over all 200 lines of the default run
(kimi5's k2 file, quoted): maxply 32, **maxdoubleext 5** (the cap is 7: `inherited_double_extensions <= 6`,
src/search.cpp:1945), histmax-main / -capture / -cont **16,384** = HistoryMax (src/search.cpp:175 — the
tables run AT their bound), histmax-threat 0 (ThreatHistory off), corrmax 8,192 (the correction's bound —
the source constant not located in the time box: NOT COVERED).

## stamps.txt, appended by a command

## Step table

| step | done | evidence file | result |
|---|---|---|---|
| S1 the meta by the runner | done | every `.meta` here (the runner writes them in-process) | — |
| S2 the two stop controls | done | `a1_control_x.txt`, `a1_control_65.txt` | both stopped |
| S3 the block summing | done | `k6_run.py` ("blocks summed: 200/353") | met |
| A0 pins | done | `a0_pins.txt` | exact |
| A1 no option | done | `none_set_O.epd_d12.rows` + `.meta` | exact |
| A2 the five identity runs | done | `DoubleExtLimit+{4,10,64,6}…`, `DoubleExtMargin+24…` | 200 of 200 each |
| A3 the eleven runs | done | the rows + `a3_diff_counts.json` | all exact |
| A4 the M rule | done | `a4_m_rule.json`, kimi5's `k2_flag_O_d12_checks.txt` (quoted) | 0 outside, five limits |
| B1 the G runs | done | `b1_runs.txt`, `b1_g_table.json`, the rows | the table above; the M rule holds for 3/1/0/−1 and limit 64 |
| B2 the counting build | NOT DONE | — | the budget went to B3 and C; proposed as the first item of the next job |
| B3 G50 at depth 16 | done | `b3_runs.txt`, the rows | the table above |
| C1 kimi5's build, defaults | done | `none_k6_set_O.epd_d12.summed.txt` | five sums exact |
| C2 the four switch runs | done | `c2_runs.txt`, the summed files | four sums + bench exact |
| C3 the changed sites + maxima | done | the summed files, kimi5's k2 file (quoted) | the table in line (3) |

## The bootstrap script and its output

`b1_bootstrap.py` (committed): the sum-ratio bootstrap over positions, 4,000 resamples, seed 2301; its
intervals are the [ci] fields of `b1_g_table.json`, printed by the script run committed beside it.

## 5. From my partner

`cursor/glmflash5-work-cb5c`: job 13's report still not on its branch at my check. Its Step-1 tree sums
remain reproduced from my side. Its job-12 M9 result (+31, one seed) now has Opus's PC-side run in
progress per your file — nothing for me to add.

## 6. What I did NOT do

- B2's counting build (the singular-verification counters: failed-low verifications, candidates, given,
  refused by the limit, the inherited-count split). The budget went to B1/B3/C — the next job's first item.
- The CHECKX maxima for the SWITCHED runs (a)-(d): the runner does not save the per-search CHECKX lines;
  the maxima above are the default run's (kimi5's file, quoted). One-line runner fix if you want them.
- The correction bound's source constant (corrmax 8,192): not located in the time box.

## 7. What I am NOT sure about

- The limit-64 sign flip between depth 12 (−0.46 %) and depth 16 (+0.42 %): one set of 50 at depth 16;
  the interval for the d16 cell was not bootstrapped (time). The direction claim rests on 50 positions.
- The 3-node SeeQuiet deviation and the job-22 family of tiny deviations: still unexplained; the
  harness-order/TT-clear hypothesis stands.

## 8. A better way

The M-rule check (A4) generalizes: for ANY depth-limited feature, the per-search maximum of the limiting
quantity (from a counting build) predicts EXACTLY which positions an option can and cannot change — the
prediction costs one file read and falsifies a wrong patch in seconds. It caught nothing this time
(which is the point).

## 9. UTC stamps

## 10. Model name

The runtime serving this Cursor cloud-agent run identifies as GLM, trained by Z.ai; the agent name for
this work is deepseek5. I cannot verify the exact model version beyond what the runtime says.

## Questions for Fable

1. B2's counters on the next job: your spec's five counters (failed-low verifications, candidates, given,
  refused, the inherited-count split) — shall I build them on the DoubleExt build (my job-23 tree) so the
  B1 known answers double as its identity, or on the plain base as a separate counting build?
2. The cap's sign flip at depth 16: real (the deeper verifications make the cap's refusals expensive) or
  a 50-position artifact? A G-353 depth-16 run would answer it in ~25 minutes of your machine.
3. The corrmax 8,192: where is its source bound? (The histories' is HistoryMax at search.cpp:175.)
```
2026-11-16T10:53:00Z job23 t0
2026-11-16T10:53:15Z part A build + pins
2026-11-16T10:53:28Z part A build v3
2026-11-16T10:53:32Z part A build v4 done
2026-11-16T10:53:40Z part A build v5 done
2026-11-16T10:53:44Z part A build v6 done
2026-11-16T10:53:50Z part A build v7 done
2026-11-16T10:55:58Z A1-A3 runs done
2026-11-16T10:58:20Z B1 G runs done
2026-11-16T10:59:14Z B3 runs done
2026-11-16T11:00:49Z C2 runs done
```
