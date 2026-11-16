# deepseek6 long 64 — PREDICTION (written before the first counted run)

Item (file 15, long 64): **COUNTERS AT DEPTH 14 ON GAMES.** Long 17's eleven counters on **all of G at depth 14**
under S14 (the counter build's node sum must be **43,345,893** and its rows must equal the plain rows). Table:
counter | G depth 12 | G depth 14 | ratio | share of the growth.

Model: DeepSeek V4.1 Flash 1017, chat 1794862262. Time: `stamps.txt`, first line is the claim.

## Fixed now

- **Counter build**: base 6b98f217 + my long-17 `ns17_counters.patch.txt`, applied at `--fuzz=0` on a clean copy
  (`/tmp/ds6/l64`), sha256 `4bb9ccad15f65e3a3ff1230dd04fd5c40451b8a80c5f6ff8b36c55ee4541530b`;
  `bench 11` = 312,866 already verified.
- **Two runs over all 353 positions of G at depth 14 under S14**: the counter build, and the plain build as the
  row-for-row control. The plain build's G depth-14 sum is **43,345,893** — measured in my long 51 and verified
  equal there three ways (two runs plus long 53's fresh-process run).
- The depth-12 counters on G are **not** in the branch: long 17 measured them on **O**. So the depth-12 column for
  G needs its own run — **a third run**, the counter build at depth 12 on all of G. That is what makes a
  "ratio d12→d14" meaningful; comparing G's depth-14 counters with O's depth-12 counters would be two different
  position sets.

## Predictions, each with the range that kills it

**P1 — the counter build's G depth-14 sum is exactly 43,345,893, and its rows equal the plain build's on
353 of 353.** This is the item's pin; if it fails the item stops and the raw output is committed.

**P2 — every counter is larger at depth 14 than at depth 12**, because the tree is larger (long 45/long 51: G
grows 18,466,239 → 43,345,893, a factor of **2.348**). Kill range: any counter whose depth-14 total is below its
depth-12 total.

**P3 — the gate is the largest in ABSOLUTE growth but grows at about the tree's rate** (ratio 2.25–2.45), the same
shape long 26 found on O under T1 (gate ratio 1.0677 against a tree ratio 1.0705). Kill range: gate ratio outside
2.10–2.60, or another counter exceeding the gate's absolute growth.

**P4 — the over-proportional growers are the depth-conditional statements, as on O at T1/T2: `probcut_enter`,
`iir` and `probcut_cut` all grow FASTER than the tree.** Long 26 measured probcut_enter 1.122 / probcut_cut 1.086 /
iir 1.084 against a 1.0705 tree on O. Prediction here: each of those three has a ratio **above 2.45**. Kill range:
any of the three at or below the tree ratio.

**P5 — `null_verify` stays 0 or tiny.** On O it was 0 under S14 at depth 12 and at depth 14. On G, long 26's
peer reported 4 (T1) and 18 (T2) at depth 12, so G does fire it: prediction **under 500 at depth 14**. Kill range:
over 5,000.

**P6 — `null_ge_beta` equals `null_cut` exactly**, as in every run of mine so far (they are the same event counted
at two places). Kill range: any difference.

**P7 — budget.** Three runs over G (two at depth 14, one at depth 12): depth 14 on G took about 4 minutes per run
in long 51. Total **15–30 minutes**, two at a time. Kill range: a single run over 1800 s gets killed and reported
as "timeout"; a partial run never gets quoted as a total.

## What would make me report "not done"
A counter build that fails `bench 11`, or a depth-14 counter run whose sum is not 43,345,893 (stop, commit raw).
A depth-12 G run that I cannot finish becomes the first step of a follow-up and the report says the ratio column
is missing rather than filling it from O.
