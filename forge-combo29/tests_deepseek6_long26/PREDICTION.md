# deepseek6 long 26 — PREDICTION (written before the first counted run)

Item (file 7, long 26): **long 17's counters on B_FINE under T1 and T2** (known node sums on O at depth 12:
T1 10,170,054 / T2 11,915,365), the question "which steps make the 7 % larger tree", compared with my job 4's
d-counts.

Model: DeepSeek V4.1 Flash 1017. Time: see `stamps.txt`, first line.

## Configuration fixed here

| tag | build | options |
|---|---|---|
| T1 | B_FINE + my long-17 counters (tree = LmrFine patch f7bf3f43 + ns17_counters) | S14 + `LmrFine 1` + `LmrFineHistory 1` + `LmrRoundF 512` |
| T2 | same build | S14 + `LmrFine 1` + `LmrFineHistory 1` + `LmrRoundF 0` |
| S14 (baseline) | same build, T1/T2 options absent | the fourteen S14 options |

The counter build's rows must equal the plain LmrFine build's rows on every position at these settings — that is
the step-0 check, and it is also my long-25 `runs/T1_d12.rows` / `T2_d12.rows` sums (10,170,054 / 11,915,365).

## Predictions, each with the range that kills it

**P1 — the counter build is observation-only.** Its T1 sum is **10,170,054** and its T2 sum **11,915,365** exactly,
and its per-position rows equal the non-counter LmrFine build's rows bit for bit (200 of 200 for both). Kill
range: any sum differing at all, or any position differing → the item stops and the raw output is committed.

**P2 — the "7 % larger tree" is one step, not a spread across the eleven.** I predict the eleven-counter ratio
T1/S14 has **at most three counters outside 0.90–1.10**, and that the largest single contributor is in the
static-pruning gate block (as it was for V in my long 18). Kill range: four or more counters outside that band
kills the "one step" phrasing; the gate not being the largest kills the second half.

**P3 — the mechanism is re-search, not extra pruning.** Under T1 the tree is larger (1.0705 × S14), so the
counters should show MORE work being *done*, not less: `gate` ≥ S14's (i.e. ratio ≥ 1.00) and `rfp_ret` ≥ S14's.
Kill range: gate ratio < 1.00 or rfp_ret ratio < 1.00 kills P3.

**P4 — depth profile shift.** The counters that rise most are at the shallow depth buckets (1–3), because the
fine-history term changes move ordering, which changes cutoffs earliest. Prediction: for the gate counter, the
ratio at buckets 1–3 is larger than the ratio at buckets 4+ by at least 5 %. Kill range: the opposite ordering
kills P4.

**P5 — T2's tree is bigger than T1's and the ratio is close to T2/T1 = 1.1716.** i.e. every counter's
T2/S14 ratio is between 1.05 × and 1.35 × its T1/S14 ratio, so no single counter explains T2's extra 1.7 M nodes.
Kill range: any counter whose T2/T1 ratio (on that counter) is above 2.0 or below 0.6 kills P5.

**P6 — `null_verify` is zero on both.** My long 17/18 rows had it at zero under S14 and V; `LmrFine` does not
touch null-move verification. Kill range: any non-zero → that is a finding about the patch, not a failure.

**P7 — budget.** Two counter runs (T1, T2) at depth 12 on O plus one S14 baseline: about 3–6 minutes total on
this VM (my long-25 d12 runs took 20–30 s each). Kill range: if any single run exceeds 900 s I report the part
done.

## What would make me report "not done"
A counter build that fails the four honesty pins or an option refusal (the engine's line goes into the report,
that configuration says "refused"). A counter whose placement disagrees with kimi5's or Opus's known numbers is
a FINDING to report, not a stop.
