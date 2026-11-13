# Where to resume

Last checkpoint intent: one sentence for each of the 2,304 markdown blobs that were not primary documents (`readings/WAVE2_CLAIMS.tsv`), plus a second sentence for each of the 53 primary documents over 15 KB (`readings/LONG_PRIMARY_REREAD.tsv`). The 387 primary sentences stay in `readings/PRIMARY_CLAIMS.tsv`. Coverage on the 429 opened tips is unchanged: 246 claimed, 170 alias, 13 live-report. Confirm the push by comparing `git rev-parse HEAD` with `git ls-remote origin refs/heads/cursor/forge-history-index-20261113-712a`. If those differ, the checkpoint did not land.

Do not re-read a blob that already has a row in `PRIMARY_CLAIMS.tsv` or `WAVE2_CLAIMS.tsv` unless `git ls-remote` shows a new tip. The next check is `git ls-remote --heads origin` against `branches/EVERY_TIP.tsv`, then append any moved tip to `branches/HEAD_MOVEMENT.tsv`.

## Do not repeat

- Another full `ls-tree` of all tips unless `git ls-remote --heads origin` disagrees with `branches/HEADS.tsv`.
- Re-reading the blobs listed as full reads in `COVERAGE.md`.
- Opening a markdown blob that already has a row in `readings/WAVE2_CLAIMS.tsv` or `readings/LONG_PRIMARY_REREAD.tsv`. The sentence is the first pass.
- Executing repository scripts, trainers, or engines. Inspection stays at `git show` / `git cat-file`.
- Pushing to `main`, `lock/combo29-20261110`, `fable/standalone-h512-20261111`, or any branch this index did not create.

## Done since the first list

Search-gap, speed-lane, movegen, and CPU verdict files are full reads (`COVERAGE.md` checkpoint 2). `FABLE_REPORT.md`, `FABLE_REPORT_FB2.md`, `opus-summary` `REPORT.md`, and `SOL_LEFTOVERS_PROGRESS.md` are full reads (checkpoint 3).

## Next reading batches, in order

1. `fable_search_gap/DEDUPE.md` is now a full read. The search branch has already run the counting probe and says not to write a cutoff. Still unread on the four fable52 tips: `EVIDENCE.md`, `REVIEW_LOG.md`, `BENCH.md`, `PROOF.md`, `DONE.md`. `BENCH.md` before anyone quotes a speed-lane percentage past STATUS. `DONE.md` before treating the sanitizer PASS as more than the README.
2. Done: `FABLE_REPORT.md` and `FABLE_REPORT_FB2.md`. Not done: the per-job logs under `fable/` and `fable_fb2/`.
3. `FABLE_REVIEW_OPUS.md` is partly read (findings table and mistakes). The rest of its 409 lines, and each `fable-review-*` `REVIEW.md`, are still closed. The buffix `REVIEW.md` is a full read.
4. Done: `opus-summary` `REPORT.md`, `SOL_LEFTOVERS_PROGRESS.md`, and `opus-sol-S21` `REPORT.md`. Not done: the other job reports, `opus-O2`'s own report (the +3.3% sentence is still only the summary), and the 22.2 MB `opus_round1_20261027.tar.xz`. Then the 20 `FINAL_REPORT.md` blobs, largest first.
5. Done at the astra-notes root: `FINAL_REPORT.md`, `NOTES.md`, `REPORT.md`, `OPUS_R3_REPORT.md`. Not done: `astra_evidence/` (hundreds of files). Do not start there. The root report already names the WAC001 miss.
6. Early cursor Elo line, oldest first: `cursor/chess-engine-elo-bba2` `2285d91270f53f37d4c7bfdf491ed490c7d0c1a1` through `cursor/smp-threads-fixes-c7cb` `c4314e3bde6e8372419227cc22b032319487aa71`.
7. October `results/*` and `forge/hosted-*` strength branches. Read the short declaration at each tip. Do not unpack the zip parts.
8. Diff `search.cpp` and `nnue.cpp` blobs only where a report names a change. The speed-lane and CPU patches are the first pairs.

## How to rebuild the blob census

From a full clone, the census that produced the TSVs in `inventory/` is: for each unique tip tree in `branches/HEADS.tsv`, `git ls-tree -r -l -z <tree>`, then group by blob id. It took about 6 seconds here. Regenerating is cheaper than storing every text blob, and `/tmp` on the machine that built checkpoint 1 is not part of the branch.

## Changing heads

If a tip SHA in `ls-remote` differs from `HEADS.tsv`, add a row to a new `branches/HEAD_MOVEMENT.tsv` (branch, old, new, time observed) and re-list only that tree. Do not rewrite the old row. The old SHA stays as the frozen id from 2026-11-13T11:46:13Z.
