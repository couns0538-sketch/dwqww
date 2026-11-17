## 2026-11-17T01:10:57Z (from `date -u`)
seat 21. **Threads 1 in every run.** PC build r15 under PC20 unless stated.

**Both of your points are recorded in the files**
1. `REPORT_job44.md` now says explicitly that **F24's four rows (depth 4, depth 10, nodes 20000, nodes
   200000) and the counter-0 control are ONE measurement and must be read together** — the four rows rule
   out "not deep enough", the control rules out "bad move selection". The same sentence is in the 21-F24
   finding line, so it cannot be split off later.
2. The mate-3 restraint is stated as the reason the coverage stops at mate-in-2, in `REPORT_job44.md` and
   repeated in job45's "what I did NOT do".

**NEW: 21-C23 — the acceptance spec now has SIX cases, and S6 is the only one BOTH builds fail.**

| case | base | PC20 |
|---|---|---|
| S1 drawn root + mate in 1 | **FAIL** `cp 0`, f2f3 | PASS `mate 1`, e1e8 |
| S2 drawn root, no mate | PASS `cp 0` | **FAIL** `cp 368` |
| S3 insufficient material | PASS `cp 0` | PASS `cp 0` |
| S4 threefold + mate in 1 | **FAIL** `cp 0`, f2f3 | PASS `mate 1`, e1e8 |
| S5 threefold, no mate | PASS `cp 0` | **FAIL** `cp 292` |
| **S6 drawn root + MATE IN 2** | **FAIL** `cp 0`, h1a1 | **FAIL** `cp 0`, h1g1` |
| pins | 4/4 exact | 4/4 exact |

S1–S5 are **identical** to job43 (adding a case did not perturb the others — the property a spec needs).
S6's premise is asserted in the spec: no mate in 1, and six moves force mate in 2.
One command judges any future fix: `python3 job45/acceptance6.py <exe> <outdir> <label>`.
`ACCEPTANCE_drawn_root.md` updated to six cases.

**What S6 adds to the design note**: "search the root, then take the draw score" is not enough by itself —
the search must be deep enough to see the win, so a fix that searches at depth 1 or 2 passes S1/S4 and still
fails S6. That requirement was not in the note and is now in the table.

**Next**: no verified mate-in-3 board exists in my files, so the spec stops at mate-in-2; the remaining
work I would do is find one by search (not by hand) under a bounded solver, and merge it as S7.
