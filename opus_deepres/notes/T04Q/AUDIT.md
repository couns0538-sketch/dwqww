# T04Q audit - lock FD3A5190 source vs notes/T04/BUG_CHECKLIST.md (+ extra spots)
Status: PARTIAL (rows added as the source is read; PENDING rows not yet checked)

Started 03:47 PC clock (`date`). Read-only audit, no build or run. Lock = `src_al1s198_clean` (path in WORKER_RULES).
Known items not re-reported: bad_captures_ write at search.cpp:361 (own fix b0c3882b), R7TtExclusive (not in the lock).

## A. Checklist rows (notes/T04/BUG_CHECKLIST.md)
| # | pattern | verdict | evidence (file:line) / box test |
|---|---|---|---|

## B. Extra spots (brief)
| # | spot | verdict | evidence (file:line) / box test |
|---|---|---|---|
