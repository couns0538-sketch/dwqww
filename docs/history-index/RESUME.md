# Where to resume

Last checkpoint intent: commit and push of this index after the tip inventory and the H512 / fair-eval / combo29 full reads. Confirm the push by comparing `git rev-parse HEAD` with `git ls-remote origin refs/heads/cursor/forge-history-index-20261113-712a`. If those differ, the checkpoint did not land.

## Do not repeat

- Another full `ls-tree` of all tips unless `git ls-remote --heads origin` disagrees with `branches/HEADS.tsv`.
- Re-reading the blobs listed as full reads in `COVERAGE.md`.
- Executing repository scripts, trainers, or engines. Inspection stays at `git show` / `git cat-file`.
- Pushing to `main`, `lock/combo29-20261110`, `fable/standalone-h512-20261111`, or any branch this index did not create.

## Next reading batches, in order

1. `fable52-search-gap-20261109` at `56a76b153bb8`: `fable_search_gap/STATUS.md`, `NO_QUALIFIED_GAP.md`, `FALSIFICATION.md`, `EVIDENCE.md`. Search-strength handoff depends on this.
2. `fable52-speed-lane-20261109` at `08897a88e11c` and `fable52-cpu-20261110` at `ea3759a9ec3b`: `STATUS.md` / `DONE.md` / `README.md`. Speed claims. Do not promote them to Elo.
3. `fable52-movegen-proof-20261110` at `2ff77f98927c`: `PROOF.md`, `STATUS.md`, `evidence/TABLES.md`. Correctness of move generation.
4. `fable-nnue-arch` at `08b589e19720` and `fable-fb2-j1` at `014f3fd8b0eb`: `FABLE_REPORT.md`, `FABLE_REPORT_FB2.md`. These are the warm start the H512 reports cite.
5. `fable-review-summary` at `fa6411f6f984`: `FABLE_REVIEW_OPUS.md`. Independent review of the opus stack.
6. `opus-summary` at `e89d2af1c5f3`: `REPORT.md`, `SOL_LEFTOVERS_PROGRESS.md`. Then the 20 `FINAL_REPORT.md` blobs, largest first (`FINAL_REPORT.md` 137,704 bytes, `opus_30h/FINAL_REPORT.md` 93,932, `opus_speed/FINAL_REPORT.md` 64,707).
7. `astra-notes` at `3e50336ac024`: `FINAL_REPORT.md`, `NOTES.md`, `REPORT.md`, `OPUS_R3_REPORT.md`. This tree has 228 markdown files; read the four roots before the `astra_evidence/` pile.
8. Early cursor Elo line, oldest first: `cursor/chess-engine-elo-bba2` `2285d91270f5` through `cursor/smp-threads-fixes-c7cb` `c4314e3bde6e`. `engine-improvement-log.md` and `RELEASE_STATE.md`.
9. October `results/*` and `forge/hosted-*` strength branches. Read the short declaration or handoff at each tip. Do not unpack the zip parts.
10. After those, diff the 95 `search.cpp` blobs and 50 `nnue.cpp` blobs only where a report says the source changed. Record the blob pair and the conclusion. Do not try to narrate all 95 by eye in one pass.

## How to rebuild the blob census

From a full clone, the census that produced the TSVs in `inventory/` is: for each unique tip tree in `branches/HEADS.tsv`, `git ls-tree -r -l -z <tree>`, then group by blob id. It took about 6 seconds here. Regenerating is cheaper than storing every text blob, and `/tmp` on the machine that built checkpoint 1 is not part of the branch.

## Changing heads

If a tip SHA in `ls-remote` differs from `HEADS.tsv`, add a row to a new `branches/HEAD_MOVEMENT.tsv` (branch, old, new, time observed) and re-list only that tree. Do not rewrite the old row. The old SHA stays as the frozen id from 2026-11-13T11:46:13Z.
