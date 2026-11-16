# deepseek6 job 9 — ADDENDUM: the four readings of "N of M rows differ"

Model: DeepSeek V4.1 Flash 1017. This session's job-9 work was committed as `d4225d250` (19:53:56Z) and the
other deepseek6 session's report was committed at 19:54:00Z (`5cde518c9`); both sessions claimed job 9 in the same
second. `REPORT_deepseek6_job9.md` is that other session's report. **This file adds one measurement to it; it does
not replace or correct it, and it does not touch the long-28 report.**

## What it adds

`REPORT_deepseek6_job9.md` states two counts: "35 of 38 rows differ" and, quoting the job's complaint, "the
direction column differs in nine rows". Those two come from **different definitions of "differ"**, and it is
worth saying so because a reader who applies one definition to both numbers gets a contradiction.

My own comparison of section 4 of `REPORT_deepseek6_long28.md` against `tests_deepseek6_long28/table.txt`
(independently written, at `d4225d250`) gives four counts over the same 38 number-carrying rows:

| reading | count | which known answer it matches |
|---|---|---|
| rows with a NODE-COUNT or SUM difference | **35 of 38** | the job's "35 of 38" |
| rows with a node/sum OR direction-token difference | 36 of 38 | — |
| rows whose direction TOKEN differs (`FLIP` vs `SIGN-FLIP`) | 17 of 38 | — |
| rows whose direction differs under the two-way (same vs flip) reading | **9 of 38** | the job's "nine rows" |

So "35" counts numeric/count cells and "nine" counts directions under a two-way reading. Both are right, about
different things. A reader who computed 17 and thought the job said 9 was wrong would be comparing a three-way
reading against a two-way one.

## The one row the "35" hides

`RfpImproving +c` differs in **no numeric cell** but the report says `FLIP` where table.txt says `SIGN-FLIP`. That
is not prose: the report claims the two sets move in opposite directions when the raw file says both move the same
way. It is the 36th row, and it is a content error the headline count does not capture.

## The other two rows that differ in nothing

`RfpMargin -c` and `RfpImproving -c` match table.txt on all eight cells. So the long-28 section-4 table is not
uniformly wrong; it is wrong wherever one specific slip applied.

## The systematic slip (why this is worth an addendum and not just a count)

Every numeric error of the kind the job names is the count of **unchanged** positions written into the
**changed** column. `1 + 199 = 200` and `16 + 337 = 353` exactly, in every affected row. It is one repeated
mistake, not transcription noise — which is why the corrected table reproduced in `REPORT_deepseek6_job9.md`
(section 2 there, the `render28.py` output) is the only version worth quoting.

## What I did NOT do

- Did not edit `REPORT_deepseek6_long28.md`, `REPORT_deepseek6_job9.md`, or any of the other session's scripts.
- Did not re-publish my version of `render28.py` / `compare28.py`: the other session's are committed and produce
  the same corrected table and the same "35 of 38". A second copy of a working script is noise. Mine remain in the
  history at `d4225d250` if anyone wants the independent implementation.
- No engine build, no search: this job is text.

## Times and the model

Times: `d4225d250` (19:53:56Z, my work), `5cde518c9` (19:54:00Z, the other session's report) — both from
`git log`, not typed.
Model name my runtime gives: **DeepSeek V4.1 Flash 1017**.
