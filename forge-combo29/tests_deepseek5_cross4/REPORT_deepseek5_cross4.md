# REPORT_deepseek5_cross4 (deepseek5, 2026-11-16 UTC) — the DoubleExt options: three independent implementations, one tree

**What was compared:** the partner's job-14 Step-1 rows (its own hand-written DoubleExt patch — its B6
build, sha 9938d880… — written independently of mine because my patch was not yet on its branch when it
started) against MY committed job-23 runs (my DoubleExt.patch.txt on the plain base, exe c73ca859…).
Fable's PC-side numbers are the third implementation and the source of the known answers.

**The four shared settings (set O, depth 12; its table quoted from its report; my rows committed here):**

| setting | glmflash5's B6 (its report, quoted) | deepseek5's DoubleExt.patch.txt (committed rows) | agree |
|---|---|---|---|
| DoubleExtLimit −1 | 18,422 / 25,152 / 53,004, sum 12,217,726 | same, from `DoubleExtLimit+-1_set_O…rows` | EQUAL |
| DoubleExtLimit 64 | 18,407 / 25,756 / 64,000, sum 12,573,318 (= base) | same | EQUAL |
| DoubleExtMargin 0 | 20,884 / 42,041 / 54,754, sum 13,805,238 | same | EQUAL |
| DoubleExtMargin 96 | 18,422 / 25,152 / 50,341, sum 12,377,094 | same | EQUAL |

**What this means:** the two new options now have THREE independent implementations written apart (mine,
the partner's, Fable's PC-side) that produce the same searches on the shared settings — the same
standard of check as job 25's seven terms (three versions of one option set agreeing per position).
The partner's match results (M15–M17) rest on its B6; my tree factors (job 23's A3) rest on mine; the
known answers were Fable's — all three now agree where they overlap.

Raw files: my four committed rows + .meta (the exe path and sha inside). Model: deepseek5 (GLM flash).
