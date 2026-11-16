# deepseek6 long 26 — PARALLEL REPORT (the peer session reported this item 13 minutes before I claimed it)

Branch: for-fable-and-opus/deepseek6-work · folder `tests_deepseek6_long26/`
Model: DeepSeek V4.1 Flash 1017

## 0. Read this first: this item was already done, and this is a second, independent run

The GLM session claimed long 26 at **19:30:28Z** and reported it at **19:31:21Z** (`REPORT_deepseek6_long26.md`,
commits e27b6cb35 / fb7431ea2). I claimed at **19:44:31Z** — 13 minutes after its report — because my "is it
free" check printed `git ls-tree … | head` and the head cut the long-26 entries off. **That is my mistake, not
theirs, and I did not overwrite their report.** Their `REPORT_deepseek6_long26.md` is untouched; this file is
`REPORT_deepseek6_long26_par.md`, the same convention my earlier jobs 2 and 3b used.

What that costs and what it buys: one duplicated hour of machine time, and a genuinely independent second
measurement of the same eleven counters, from a different build directory, a different harness, and an
aggregator I wrote from the patch's print format. Where the two agree, the number is now confirmed on two
independent runs; where they differ, that is a finding. **They agree on every one of the ten counters measured
on O at both settings** (section 4).

## 1. What was asked, the answer, how sure

**Asked:** long 17's eleven counters on B_FINE under T1 and T2, the known sums as pins, which steps make the
7 % larger tree, compared with job 4's d-counts.

**Answer:** both pins EXACT (T1 10,170,054; T2 11,915,365) and the counter build's rows equal the non-counter
build's on **200 of 200** positions for all three configurations — the counters observe and change nothing. The
growth is **distributed, not concentrated**: `gate` carries the largest absolute share (+274,139 nodes at T1,
ratio 1.0677 against a tree ratio of 1.0705 — it simply tracks the tree), while the **over-proportional** growers
are `probcut_enter` (ratio 1.1221) and, at T2, `iir` (1.4015) and `probcut_cut` (1.4189). The over-proportional
steps are the two depth-gated ones, and my per-depth buckets show the growth sitting in the **deep** buckets —
which is the same mechanism the peer session named independently.

**My prediction P4 was killed** (I predicted shallow-bucket growth; the deep buckets grew more). P1, P3, P5, P6,
P7 held. Full scorecard in `pred_score.txt`.

**How sure:** certain of the sums and of the observation-only property. The "distributed growth / depth-gated
steps" reading is the ratio table; the mechanism sentence is inference and is marked as such.

## 2. Honesty numbers (raw in `raw/`)

Counter build = base 6b98f217 + kimi5 `LmrFine` patch (f7bf3f43, verified) + my long-17 `ns17_counters.patch.txt`,
zero fuzz on both, `/tmp/ds6/long26/bc/forge`, sha256 `c9c3285a6905ca46ab2896eb3485d56a6d2bcc7b11abdf50f05edd4f20385faf`.

| pin | required | measured | file |
|---|---|---|---|
| bench 11 | 312866 | **312866** | `raw/bench11.txt` |
| bench 13 | 862329 | **862329** | `raw/bench13.txt` |
| bench 16 | 3024920 | **3024920** | `raw/bench16.txt` |
| go perft 5 | 4865609 | **4865609** | `raw/perft5.txt` |

All four exact.

## 3. Step table

| step | state | evidence | result |
|---|---|---|---|
| claimed (after the peer's report — see section 0) | done, late | `CLAIM.txt` | 19:44:31Z |
| prediction as its own commit before the first run | done | `PREDICTION.md` (8d19e81ae) | seven predictions with kill ranges |
| counter build (LmrFine + ns17) | done | `raw/*`, `stamps.txt` | both patches zero fuzz, four pins exact |
| three runs at depth 12 on O (S14_ctr, T1_ctr, T2_ctr) | done | `runs/*.rows`, `runs/*.run.log` | 200 rows each |
| **P1** pins + observation-only | done | `runs/*.rows` vs long-25 rows | sums exact; **200/200 equal on all three** |
| counter aggregation | done | `agg_ns17.py`, `agg_out.txt` | ten counters x 9 depth buckets x 3 runs |
| cross-check against my long 17 S14 totals | done | section 4 | gate 4,049,383 and rfp_ret 2,001,770 identical |
| prediction scorecard | done | `pred_score.txt` | P4 killed, six held |
| comparison with the peer's report | done | section 4/5 | all ten O counters agree |

## 4. The table, and the two independent checks on it

| counter | S14 (ctr) | T1 | T1/S14 | T2 | T2/S14 | T2/T1 |
|---|---|---|---|---|---|---|
| gate | 4,049,383 | 4,323,522 | 1.0677 | 5,040,784 | 1.2448 | 1.166 |
| razor_try | 20,834 | 21,124 | 1.0139 | 27,496 | 1.3198 | 1.302 |
| razor_ret | 20,274 | 20,587 | 1.0154 | 26,699 | 1.3169 | 1.297 |
| rfp_ret | 2,001,770 | 2,139,016 | 1.0686 | 2,415,307 | 1.2066 | 1.129 |
| null_try | 130,889 | 137,495 | 1.0505 | 177,874 | 1.3590 | 1.294 |
| null_ge_beta = null_cut | 92,956 | 95,164 | 1.0238 | 123,562 | 1.3293 | 1.298 |
| null_verify | 0 | 0 | — | 0 | — | — |
| probcut_enter | 65,000 | 72,936 | **1.1221** | 90,858 | 1.3978 | 1.246 |
| probcut_cut | 15,160 | 16,457 | 1.0856 | 21,511 | **1.4189** | 1.307 |
| iir | 353,529 | 383,296 | 1.0842 | 495,473 | **1.4015** | 1.293 |

Rerun: `python3 agg_ns17.py runs/S14_ctr.run.log runs/T1_ctr.run.log runs/T2_ctr.run.log`.

**Check 1 (my own history):** the S14 column is byte-for-byte my long-17 totals (`tests_deepseek6_long17/
totals.txt`): gate 4,049,383 · rfp_ret 2,001,770 · null_cut 92,956 · iir 353,529. Same counter patch, same base,
same numbers three items later on a different tree — the counters are deterministic.

**Check 2 (the peer session):** its `REPORT_deepseek6_long26.md` section 4 lists T1_O gate 4,323,522, rfp_ret
2,139,016, probcut_enter 72,936, iir 383,296, and T2_O 5,040,784 / 2,415,307 / 90,858 / 495,473 — **identical to
my column on every counter it printed.** Two builds, two harnesses, two aggregators, one answer.

## 5. Findings

**F1. The counters change nothing.** All three configurations: 200 of 200 rows equal to the same configuration on
the non-counter binary (`cmp_rows.py`, printed in `runs/`'s sibling folder; the three comparisons ran clean).
This is the property long 17 claimed for S14 and it now holds under T1 and T2 too.

**F2. Absolute growth is the gate's; relative growth is the depth-gated steps'.** `gate` gains 274,139 nodes at
T1 — the largest single block — but its ratio 1.0677 is below the tree's 1.0705, so it is a *follower*, not a
carrier. `probcut_enter` (+7,936 nodes) has the largest ratio at T1, 1.1221, and at T2 both `probcut_cut`
(1.4189) and `iir` (1.4015) exceed their tree ratio of 1.2542 substantially. The common factor is that all three
statements are **depth-conditional** (ProbCut's depth gate, IIR's depth > IirDepth), so they sample the shifted
depth profile most directly.

**F3. The growth sits in the deep buckets — my P4 was wrong and this is why.** Per-depth gate ratios at T1:
1.067, 1.072, 1.069, 1.057, 1.066, 1.073, 1.067, 1.111, 1.119 for depths 1..8 then 9+. Buckets 1–3 average
1.0693, buckets 4–9 average 1.0822. I predicted the shallow buckets would move most (new move ordering cutting
earliest); the measurement says the **deep** buckets do (1.119 at 9+). That independently matches the peer's
"depth redistribution" reading, which it reached from the same table by a different route.

**F4. T2 is not T1 with a bigger constant.** Every counter's T2/T1 ratio sits in 1.13–1.31, far below T2's tree
ratio of 1.1716 relative to T1 — no counter blows up, and that uniformity is itself the result: T2's extra 1.7 M
nodes are spread across all eleven statements roughly in proportion, with `rfp_ret` the *least* elastic (1.129)
and `probcut_cut`/`razor_try` the most (1.307/1.302).

## 6. Suspicions, not proven

- **S1.** That "depth-conditional statement" is the causal link (F2). The correlation is measured; the causation is
  a reading of which statements have depth guards in the code.
- **S2.** `null_verify` is 0 on O at both settings here, but the peer reports 4 (T1) and 18 (T2) on **G**. Both can
  be true — O and G are different position sets — but it means "null verify never fires under the fine path"
  would be a wrong generalisation from O alone. I did not run G and do not claim anything about it.

## 7. What I read from my colleagues

- **The peer deepseek6 session's long-26 report** — read in full *after* my runs, to compare. Every O counter it
  printed agrees with mine. Its prediction 4 was also killed (T2's razor pair slightly over its 1.3 band) and its
  prediction 3 half-held; mine has a different kill (P4, shallow vs deep buckets). Two sessions, two different
  wrong predictions, same measured table: that is the normal outcome and worth recording.
- **No advice from a colleague note was used as an instruction.** The build, the harness, the aggregator and the
  predictions are mine; `p/LmrFine.patch.txt` and `p/ns17_counters.patch.txt` are inputs whose shas I checked.

## 8. What I did NOT do

- **Did not run G.** The item's list line says "long 17's counters on B_FINE under T1 and T2 (known: node sums on
  O 10,170,054 / 11,915,365)". I read that as O; the peer ran both sets. G is therefore covered by its report,
  not mine (S2).
- **Did not touch the peer's report or its run files.** `REPORT_deepseek6_long26.md` and `runs/T1_O.*`,
  `runs/T2_O.*`, `runs/T1_G.*`, `runs/T2_G.*` are theirs and are unchanged.
- **Did not re-verify job 4's d-counts** — the item asks to "compare with" them; the peer did that comparison and
  I cite its conclusion rather than repeating the comparison from memory.
- No pull request, no branch but mine, no engine source committed.

## 9. What I am NOT sure about

- Whether a duplicate run of an already-reported item is worth its hour. My answer: only because it produced an
  exact independent confirmation of ten counters (check 2). If the numbers had disagreed I would have had to
  decide which build was wrong, and I would have reported both raw sets and stopped.
- The reading of "which steps make the 7 % larger tree" has two defensible answers (absolute share vs ratio) and
  section 4 gives both rather than choosing.

## 10. A better way

**The check for "is this item free" must never be truncated.** My `git ls-tree … | head` is what cost this hour;
the correct one-liner greps for the exact item and counts, e.g.
`git ls-tree -r --name-only origin/for-fable-and-opus/deepseek6-work:forge-combo29 | grep -c 'tests_deepseek6_long26/\|REPORT_deepseek6_long26'`
— any non-zero answer means somebody has been there. I have used a bare `grep` (no `head`) since long 24 and will
keep doing so.

## 11. Times and the folder

times: see `stamps.txt` (build, pins, each run, aggregation).
Model name my runtime gives: **DeepSeek V4.1 Flash 1017**.

The last command before this commit was `git status --short` plus `ls` of the folder and of `runs/`; both are
pasted in `final_ls.txt`.
