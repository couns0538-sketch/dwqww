## Proposed Code Review handoff

**What this branch is.** Documents and small analysis tools only. It changes no engine source, lock, queue, gate file, net or dataset, and no file that exists on `main`. The result is **NO QUALIFIED GAP**.

**Read in this order.**

1. `NO_QUALIFIED_GAP.md`: verdict, blocker, next evidence request, and the list of terms (section 9).
2. `REVIEW_LOG.md`: what one reviewer found wrong in the first version and what was changed.
3. `EVIDENCE.md` sections 5 and 6: the measurement, the placebo, and the rule that decided the verdict.
4. `DEDUPE.md` sections 3 to 6: what is owned, the one mechanism that is not, and the blind spots of the search.
5. `FALSIFICATION.md` sections 2 and 3: witnesses and the counting request.
6. `COVERAGE.md` section 8: what could not be found.

**Where a second reader is most useful.**

- `tools/etc_probe/etc_probe.cpp`: does the mode that takes the cutoff do what `NO_QUALIFIED_GAP.md` section 3 says, and is the pawn-ending failure a property of the mechanism or of this harness. The reviewer found no unsound cutoff; the cause of the failure is still open.
- `DEDUPE.md` row 20: is the mechanism truly unowned. This job could not look in three banned folders, in branch history, or at boards outside the repo.
- `EVIDENCE.md` section 2: the reading of the gate table, in particular the time-loss rows and the unreliable base column.
- `tools/pin.ps1` and `tools/pinguard.py`: every run of this job depends on them for the CPU 3-6 rule.

**How to re-run anything.** `STATUS.md`, "Resume commands". Every run is pinned and writes only under `D:\forge_jobs_20261109\fable52\out`.

**Review already done.** One pass by a separate agent on a different model, read-only, at the end, and one recheck of the fixes by the same agent. It is independent in context and model, not in organisation. Findings and what was done about each are in `REVIEW_LOG.md`.

**Open items for owners, not acted on here.** `NO_QUALIFIED_GAP.md` section 8: a proven bundle with no result on a current base; time losses in the newest gates; base labels that disagree with gate tags; the lock pointer's `tree` field; a rook underpromotion that is probably a tie; missing gate logs and PGNs; repetition-tainted table scores.

**Requested decision.** Either accept NO QUALIFIED GAP and close, or ask the crew for the counting run of `NO_QUALIFIED_GAP.md` section 6 (a few crew hours and one quiet timing slot, no gate, thresholds already fixed).
