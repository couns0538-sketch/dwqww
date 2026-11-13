# Where to resume

Last checkpoint intent: commit and push of this index after the tip inventory and the H512 / fair-eval / combo29 full reads. Confirm the push by comparing `git rev-parse HEAD` with `git ls-remote origin refs/heads/cursor/forge-history-index-20261113-712a`. If those differ, the checkpoint did not land.

## Do not repeat

- Another full `ls-tree` of all tips unless `git ls-remote --heads origin` disagrees with `branches/HEADS.tsv`.
- Re-reading the blobs listed as full reads in `COVERAGE.md`.
- Executing repository scripts, trainers, or engines. Inspection stays at `git show` / `git cat-file`.
- Pushing to `main`, `lock/combo29-20261110`, `fable/standalone-h512-20261111`, or any branch this index did not create.

## Done since the first list

Search-gap dossier verdict files, speed-lane STATUS and README, movegen STATUS, and the CPU job STATUS and README are full reads. See `COVERAGE.md` checkpoint 2 and `findings/SEARCH.md`.

## Next reading batches, in order

1. Still on the four fable52 tips, the evidence files named as unread in `COVERAGE.md` checkpoint 2. `fable_search_gap/DEDUPE.md` before anyone re-opens enhanced transposition cutoffs. `fable_speed_lane/BENCH.md` before anyone quotes a percentage from that lane. `fable_cpu_speed/DONE.md` before treating the sanitizer PASS as more than the README's summary.
2. `fable-nnue-arch` at `08b589e197202d00bb2a840c80c2233262cd9918` and `fable-fb2-j1` at `014f3fd8b0ebf86c5ecd8c5e149b10119d9f7f3c`: `FABLE_REPORT.md`, `FABLE_REPORT_FB2.md`. These are the warm start the H512 reports cite.
3. `fable-review-summary` at `fa6411f6f984f86d0adacfc2868967f2698d4e67`: `FABLE_REVIEW_OPUS.md`.
4. `opus-summary` at `e89d2af1c5f3b9268836c8b949fb4f3951de6a29`: `REPORT.md`, `SOL_LEFTOVERS_PROGRESS.md`. Then the 20 `FINAL_REPORT.md` blobs, largest first.
5. `astra-notes` at `3e50336ac0249cfcc87d23f8154e1e842d2f7c79`: `FINAL_REPORT.md`, `NOTES.md`, `REPORT.md`, `OPUS_R3_REPORT.md`.
6. Early cursor Elo line, oldest first: `cursor/chess-engine-elo-bba2` `2285d91270f5` through `cursor/smp-threads-fixes-c7cb` `c4314e3bde6e8372419227cc22b032319487aa71`.
7. October `results/*` and `forge/hosted-*` strength branches. Read the short declaration at each tip. Do not unpack the zip parts.
8. Diff `search.cpp` and `nnue.cpp` blobs only where a report names a change. The speed-lane and CPU patches are the first pairs.

## How to rebuild the blob census

From a full clone, the census that produced the TSVs in `inventory/` is: for each unique tip tree in `branches/HEADS.tsv`, `git ls-tree -r -l -z <tree>`, then group by blob id. It took about 6 seconds here. Regenerating is cheaper than storing every text blob, and `/tmp` on the machine that built checkpoint 1 is not part of the branch.

## Changing heads

If a tip SHA in `ls-remote` differs from `HEADS.tsv`, add a row to a new `branches/HEAD_MOVEMENT.tsv` (branch, old, new, time observed) and re-list only that tree. Do not rewrite the old row. The old SHA stays as the frozen id from 2026-11-13T11:46:13Z.
