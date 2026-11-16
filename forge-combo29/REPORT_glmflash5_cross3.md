# REPORT glmflash5 — CROSS 3 — kimi5's job-10 quiescence shares, counted by my own script

Branch `cursor/glmflash5-work-cb5c`. Build B11 = the plain base 6b98f217 + kimi5's
`tests_kimi5_job10/QsSteps.patch.txt` (666 lines, repo-root relative, applied with `git apply
-p1`; observe-only counters behind `-DFORGE_QS_STEPS=1`; B11 sha256
0784ccc9fcebc1b12575def377437b8df2569569f1d3d78d8aa6793bd5cdb4b3). 200 openings (kimi5's
first200.fens), `go depth 12`, Threads 1, Hash 16, ucinewgame + isready per search; the QSTEPS
line's `nodes` and its `q0` array (qsearch nodes by pv×q-class×in-check, 20 cells) summed by MY
script over all 200 searches per setting. times: see stamps.txt.

## 1. The cross-check, the answer, how sure

Asked: kimi5's job-10 headline — "qsearch is 44.89 % of all nodes on O at the defaults and
48.74 % under S14".

Answer: **defaults 44.89 % (5,643,723 of 12,573,318); S14 48.74 % (4,629,887 of 9,500,069) —
BOTH EXACT, to the decimal AND to the node: my two absolute counts equal the raw numbers its
report quotes (X_end-line totals 5,643,723 and 4,629,887 appear verbatim in its text).** The
anchor also held (the totals ARE the session's two known sums).

How sure: deterministic counters, same positions, same settings, my own summing script (the
only parsing: the `QSTEPS v1 nodes N q0 <20 ints> cs ...` line). Exact.

## 2. The numbers

| setting | searches | total nodes | qsearch nodes | share | kimi5's |
|---------|----------|-------------|---------------|-------|---------|
| defaults | 200 | 12,573,318 | 5,643,723 | 44.89 % | 44.89 % ✓ |
| S14 | 200 | 9,500,069 | 4,629,887 | 48.74 % | 48.74 % ✓ |

The S14 total is the bridge layer's known sum (9,500,069) — a third anchor inside the same run.

## 3. What this buys the session

- kimi5's counter build now has an independent counter-sum on my machine; its qsearch-share
  claims (and the S14-sends-more-nulls-into-qsearch reading) stand on two builds.
- My counter-driver pattern (build with the observe macro, sum the printed arrays) is reusable
  for any of kimi5's observe-only counter jobs.

## 4. What I did NOT do

- The per-class breakdowns (stand-pat margins, SEE/futility MISSED rates) — those need its
  probe mode (FORGE_QS_REGRET), which CHANGES the tree; a different and heavier cross-check.
- The G set under the counters — one setting pair was the assignment.

## 5. What I am NOT sure about

- Nothing material: the two shares and both absolute counts reproduce exactly.

## 6. UTC stamps

times: see stamps.txt (cross 3 ran 16:06:2x–16:08Z, after the second file-22 wait expired at
16:06:18Z).

## 7. Model name

glmflash5 (GLM, flash tier), run A on `cursor/glmflash5-work-cb5c`.
