# REPORT_deepseek5_cross2 (deepseek5, 2026-11-16 UTC) — the job-20 Part C side-by-side: my Checks5 against kimi5's SearchChecks, same sets, same protocol

**What was compared:** kimi5's job-6 check build (its `SearchChecks.patch.txt` applied on the plain base
by me, built with `-DFORGE_SEARCH_CHECKS=1`, exe sha in `exe_shas.txt`) run by MY harness (ucinewgame +
isready before every go, depth 12, sets O and G) against MY Checks5 build's numbers from job 20/21.

**AGREEMENT — V4's four sites, both sets, to the event (kimi5's build under my protocol / my build):**

| V4 site | O (kimi5 / mine) | G (kimi5 / mine) |
|---|---|---|
| tt-cutoff-search | 646 / 646 | 19,912 / 19,912 |
| tt-cutoff-qsearch | 200 / 200 | 3,674 / 3,674 |
| probcut | 74 / 74 | 2,433 / 2,433 |
| razor | 0 / 0 | 3 / 3 |

Two independently written counters of the same statistic at the same sites: identical on 8 of 8 cells.
kimi5's extra site (standpat-cutoff 11 / 268) counts the qsearch stand-pat cutoffs — a site my V4 does
not have; noted, not a disagreement.

**DISAGREEMENT — V5 at the qsearch final store, three orders of magnitude:**

| check | O d12 | G d12 | its score input | its alpha reference |
|---|---|---|---|---|
| mine (Checks5, job 21 form) | **0** breaches / 2,960,097 made | **0** / 4,458,366 | best_score itself | the node's ENTRY alpha (captured at function entry) |
| kimi5's build, MY protocol | **158** / 34,330 | (see file) | the shifted form AND the raw one (its patch line: `const int shifted = score_to_tt(score, ply);`) | its report says the entry alpha |
| kimi5's own protocol (its report) | 19,021 | 28,821 | " | " |

- Its own binary under MY protocol gives 158, not its reported 19,021 — the protocol difference (my
  per-position ucinewgame) is itself worth a look, but the deeper fact stands: MY check sees ZERO
  qualifying stores where ITS check sees 158 (and, on its protocol, 19,021).
- Its V6 numbers are a different population BY DESIGN (its site counts the guard's SUPPRESSED stores,
  33,427/115,247 — "NOT breaches: arrivals where the excluded guard suppressed the store"; my V6 counts
  actual stores under the excluded key = 0). Labeled, not a disagreement.
- Its V13 and my V13: both 0 ✓.

**What this means:** the side-by-side did exactly what side-by-sides are for. Where the two checks
measure the same statistic the same way (V4), they agree to the event on 8/8 cells. Where they measure
the "same" invariant with a different reading of the inputs (V5's score form and alpha reference, and
the store population each site samples), they disagree by 10²–10³. My job-21 conclusion ("V5 clean, the
job-20 counts were the ply-shift artifact") is NOT confirmed by its build under my protocol — its 158
stand-pat cases are exactly the population I claimed could not exist. One of the two checks reads a
different variable than its author thinks; finding which is a one-hour line-by-line job and is PROPOSED
as the next cross-check, with both sources already committed (mine: tests_deepseek5_job20/Checks5C21.patch.txt;
its: tests_kimi5_job6/SearchChecks.patch.txt on its branch).

**Not done:** the nested-singular comparison (its report does not print one), the V1/V2/V3/V8-V18
invariants it has and I do not (fourteen more — a future job could port three of mine to its build
under the same names, which is the cheapest way to make the two check builds interoperable).

Raw files: `kimi5_build_O_d12.checks.txt`, `kimi5_build_G_d12.checks.txt` (its build under my harness,
70 sites each), `exe_shas.txt`, `stamps.txt`. Model: deepseek5 (GLM flash).
