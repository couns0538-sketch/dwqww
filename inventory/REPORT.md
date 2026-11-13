# Forge branch inventory

Cumulative record for `couns0538-sketch/dwqww`. This file is the run-1 report. The machine index is `inventory/PROGRESS.json`. Every remote head is one row of `inventory/branches.tsv`. Branches that share a commit are `inventory/shared-tips.tsv`.

This checkpoint is `cursor/forge-branch-inventory-automation`, cut from the engine lock and then given these notes only. It does not change lock source, and it was not pushed to `main`, `lock/combo29-20261110`, or `fable/standalone-h512-20261111`.

## Snapshot

Taken after `git fetch origin --prune` and `git ls-remote --heads origin` on 2026-11-13, trigger 14:23 UTC.

| Item | Value |
|---|---|
| Remote heads | 424, and the local remote-tracking refs match that list |
| Unique tip commits | 335 |
| Unique tip trees | 335 |
| Two different tips with the same tree | 0 |
| Branches sharing a tip with another branch | 105 branches in 16 groups |
| Tags seen, not reviewed | 3 (`astra-a1-data-results-20261030`, `data-sample-10m-20261030` = `main`, `opus-sol-S48fix-grids-20261027`) |
| Inaccessible heads | none in this fetch |

`refs/remotes/origin/HEAD` is symbolic and points at `main` (`5176ddf79ae15b76c08c4485d90ee5600ba30a1a`). It is not a 425th branch.

File counts are `git ls-tree -r` on each tip tree. They are not a GitHub page count. A 300-file cap on a website listing does not apply to this table. The earlier census of directories that exceed 300 immediate children is in `cursor/forge-history-index-20261113-712a` `docs/history-index/findings/GITHUB_FILE_CAP.md`. This run did not reopen those directories.

## What "reviewed" means here

| Status | Branches | What happened |
|---|---|---|
| Tip confirmed, files not re-read | 416 | SHA and tree hash match `docs/history-index/branches/HEADS.tsv` frozen at 2026-11-13T11:46:13Z on `cursor/forge-history-index-20261113-712a` (`da51693e`). No tip moved. None disappeared. |
| Read this run | 8 | The heads absent from that frozen list. Subjects, unique diffs, and the audit notes named below. |

This run does not say the 416 were reviewed again, and it does not say every file in the 8 was read. Archives, zip parts, nets, and multi-megabyte logs were not opened.

## Base used for "relationship to the lock"

The pinned engine is `lock/combo29-20261110` at `16833ecc03b425586f91f4c8834dea8807bf4c22`. `fable_cpu_speed/README.md` on `fable52-cpu-20261110` calls that commit its base. Later Fable work that already contains it is `fable/standalone-h512-20261111` at `efb2ff960037087299332bc6a44baea69441a17a`.

Of the 335 unique tips:

- 11 contain the lock commit (the lock itself, `fable52-cpu-20261110`, `fable/fair-eval-builds-20261111`, `fable/standalone-h512-20261111`, `dot/review-20261110`, and six of the eight new heads).
- 6 contain the H512 commit (the H512 branch and five descendants).
- 39 contain `main` and do not contain the lock. `main` is the ten-file upload (`chess-engine-forge-5.31.0(2).zip` and a handful of logs and prompts).
- 285 contain neither `main` nor the lock. They are other histories, mostly the October Forge 6.4 and Opus lines. Absence of the lock commit is not a missing object.

`cursor/forge-qsearch-audit-60ce` and `cursor/forge-concurrency-audit-8d98` do not contain the lock commit. The concurrency branch imported the lock *files* (`search.cpp` blob `2ffe2556113ce83200d49030064e164650cfe890` matches the lock) onto a history that starts at `main`. The qsearch branch is Forge 5.31.0 source under `forge/`, not combo29.

## Eight heads that were not in the 11:46 list

| Branch | Tip | Date | Ahead of which parent | Files |
|---|---|---|---|---|
| `cursor/forge-time-audit-770f` | `82b4a082b18c8fa6f633d29019f4fa7b524c916a` | 14:21Z | 1 commit past the lock | 74 |
| `cursor/forge-qsearch-audit-60ce` | `d5db74e10e4c5c770004d4781ee26ae31f07c007` | 14:21Z | 3 commits past `main` | 23 |
| `cursor/forge-concurrency-audit-8d98` | `2d2a3fa7db799c5e35a407515e952bac19956724` | 14:17Z | 2 commits past `main` | 40 |
| `cursor/move-legality-82b6` | `f1c701c9faea6e30b39f8b0370511924eaa62bf1` | 14:17Z | 3 commits past H512 | 660 |
| `cursor/forge-nnue-eval-20261113-22cc` | `36b644d8484cdcfaad95247a8966b2d8bb9f4236` | 14:14Z | 10 commits past H512 | 670 |
| `cursor/forge-history-index-20261113-712a` | `da51693e0fbac616c73c454a9bd2cf93f1f4ee24` | 13:47Z | 5 commits past H512 | 676 |
| `cursor/forge-search-strength-20261113-9558` | `c9cb47a467a75051e1c6a09c4508f32f3bb9ddf9` | 12:34Z | 2 commits past H512 | 659 |
| `cursor/forge-correctness-20261113-e6b6` | `dff76c5808d0ceb7fc3940d1758991c3c33fb26d` | 12:31Z | 5 commits past H512 | 668 |

### Reproduced on the lock

Details, commands, and the exact UCI observations are in `inventory/verification/2026-11-13-clock-and-badcap.md`. Both were run this session from `git archive` of the named commits. No Elo and no nodes-per-second claim.

**A clock that does not fit in a 32-bit `int` is played as a forfeit.** `forge-combo29/src/uci.cpp:74` starts the parsed value at 0. Lines 77-78 return 0 when `std::from_chars` fails. Line 99 stores that as `wtime`. A separate g++ 13.3.0 program showed `3000000000` and `2147483648` leave the `int` at 0 with `result_out_of_range`. On an ASan build of the lock, `OwnBook false`, `go wtime 3000000000 btime 3000000000` printed `bestmove a2a3` and no `info depth` line. `go wtime 2000` on the same binary kept searching. The release build of `cursor/forge-time-audit-770f` was still at depth 16 when stopped. That branch's own suite (`forge-combo29/tools/uci_time_audit.py`, `docs/time-audit.md`) was not executed. `movestogo` uses the same parser and then `max(1, 0)` at line 95, so an overflowing movestogo becomes 1 in the source. This run did not time that case.

**The deferred-capture buffer is 64 slots and the write does not check.** `forge-combo29/src/search.cpp:469` is `bad_captures_[bad_count_++] = move`. The lock build defines `FORGE_SPD_NO_ZERO_MOVELISTS` and not `FORGE_SDK_BADCAP_PREFIX`, so the array is 64 at line 576. ASan on

`3r4/Pn1Q1p2/1Q1n1QpN/1p1Q1pRB/1Qbp1QpN/2bQ1pRB/3r1QpK/2k2q2 w - - 0 1`

died with a write SEGV in `MovePicker::next` at `search.cpp:469` (`UseNNUE false`, `go depth 3`). Startpos depth 2 on that binary completed. The same FEN with UseNNUE left on also aborted with an ASan SEGV. `cursor/forge-correctness-20261113-e6b6` sizes the array to `MoveList::Capacity` (256) at its `search.cpp:581` and still does not test the index. Its ASan build returned `bestmove d3b1` and printed `score mate 1`. This run did not check that mate with a second generator. A position with more than 256 deferred captures would still overflow. This run did not search for one.

### Read, not re-run

**Concurrency** (`cursor/forge-concurrency-audit-8d98`, note `forge-combo29/docs/CONCURRENCY_AUDIT.md`). The imported `search.cpp` blob matches the lock. The tip changes attack-table init to `std::call_once`, refuses a transposition replacement when the slot changed after the stripe lock was dropped, stops clearing a late `stop()` during helper join, and sums nodes after the join. Their pre-fix log says four failures, including SIGSEGV on concurrent first `Board` construction and a lost TT entry. Their post-fix log and a TSan run of their suite say pass. This run did not rebuild that branch or repeat TSan. Their perft stop polls at depth 4. The time-audit branch polls at depth 2 and also fixes the clock. The two fixes are not on one branch. The concurrency tree still has the integer clock parse.

**Quiescence on 5.31.0** (`cursor/forge-qsearch-audit-60ce`, `forge/QSEARCH_AUDIT.md`, `forge/src/search.cpp`). Stand-pat is no longer treated as legal when every legal move is a capture or a promotion. Their note says release `forge_tests` passed, an ASan/UBSan rebuild of those tests passed, and 150,594 positions matched an in-process contract with 0 mismatches and 1 position skipped for a node cap. The contract shares move generation and evaluation with the engine, which the note says. No match was played. Quiet checks stay out of quiescence. This is not the combo29 engine. The follow-up commit only skips building an opening generator whose source file is absent.

**Null-move fullmove** (`cursor/move-legality-82b6`, `forge-combo29/docs/MOVE_LEGALITY_20261113.md`, `src/board.cpp` `make_null_move`). A Black null move did not increment `fullmove_`. A real Black move did. The patch stores `fullmove` in `NullUndo` and increments it for Black, saturating at 65535. Their oracle against python-chess 1.11.2 reports 7,891 positions, 0 mismatches, after the fix, and the Black null FEN `r3k2r/8/8/8/8/8/8/R3K2R b KQkq - 0 1` going to fullmove 2. This run read that note and the diff. It did not rerun the oracle. They say search does not read `fullmove_` except the book ply check, and they did not re-bench. The last commit on the branch only records which lock source hashes changed.

**History index** (`cursor/forge-history-index-20261113-712a`). Its `HEADS.tsv` is the 416-tip census used above. `COVERAGE.md`, `BUGS.md`, `GITHUB_FILE_CAP.md`, `HANDOFF.md`, and `RESUME.md` were read. Elo and NPS figures in that index are copied from reports. They were not replayed there and not replayed here. Useful carry-forward, still not a new measurement: H512 candidate 3 is the net those reports ask to gate, and the reports' equal-node and timed Elo numbers disagree in the way `HANDOFF.md` tabulates; do not quote one of them alone. The destructive script `opus_round1/C4/instrument_refresh_stats.py` was removed at many later tips and must not be run from an old commit.

**NNUE branch and search branch.** Commit subjects were listed. The history index already records what it read on them (`findings/SIBLINGS.md`, `NNUE.md`, `SEARCH.md`). This run did not re-read those notes or replay benches. Search-strength commits say a default-off enhanced-transposition probe was counted and did not clear a pre-registered bar. That is their bench note, not a new one.

## Shared tips

A branch name is not evidence that the tip contains that experiment. These 16 commits are the whole shared set. The full name list is `inventory/shared-tips.tsv`.

| Branches | Tip | Files | Subject of that commit |
|---:|---|---:|---|
| 29 | `356e863dbd86` | 1068 | Fix Forge 6.4 native CI to compare pinned pre-fix commit |
| 12 | `5101c2529d38` | 1069 | OwnBook native regression test |
| 11 | `9108d012526b` | 982 | Transposition verification tags |
| 10 | `87a319fdcd02` | 1054 | Hard-budget timeout diagnostic |
| 9 | `2fc649effb6d` | 1048 | TT trial outcome and archive hold |
| 7 | `d2d8dfe4fe9d` | 1051 | UCI timeout deadline correction |
| 7 | `5176ddf79ae1` | 10 | `main`, "Add files via upload" |
| 4 | `f1b44cc71554` | 2038 | Forge 6.4.7 confirmation preregistration |
| 2 each | eight further tips | | OwnBook, nearest pawn, NNUE strength, promotion SEE, TT strength, Forge24, two GrokChess pairs |

Six `research/grokchess-*` names dated in October 2026-10-20 or 10-21 point at `main`. That tree is the ten-file upload. The experiments in the branch names are not in the commit.

Hourly `forge/` and `investigator/` names often share one of the large October commits. Read the tip subject before treating the branch name as the work.

## Family counts

Prefix of the branch name, 424 heads: `forge/` 147, other `opus-*` 71, `opus-sol-*` 57, `research/` 30, `astra*` 29, `fable*` 26, `cursor/` 17, `investigator/` 16, `results/` 12, `data/` 8, and smaller singles (`lock/` 1, `qa*` 3, `dot` 1, `tester` 1).

## Not claimed

- The 416 frozen tips were not re-read. Their reports' Elo and speed numbers were not replayed.
- No engine was promoted and no lock pin was changed. Bench pins of the lock were not re-measured. The ASan builds are for the two defects above, not a speed result.
- `bad_captures_` at 256 on the correctness branch is still an unchecked write.
- The time-audit and concurrency perft-stop patches differ (poll depth 2 versus 4) and the clock fix is only on the time-audit branch.
- Supermemory was unavailable. Nothing from it is in this report.

## Next run

1. `git fetch` and `git ls-remote --heads origin`. Diff against `inventory/branches.tsv`. Append new or moved tips to a new `inventory/HEAD_MOVEMENT.tsv`. Leave the old rows.
2. If nothing moved, do not repeat the 335-tree file count.
3. Read, on their own tips, `fable_search_gap/EVIDENCE.md`, `fable_speed_lane/BENCH.md`, `fable_movegen_proof/PROOF.md`, and `fable_cpu_speed/DONE.md` before quoting a speed or sanitizer figure past the STATUS files already summarised elsewhere.
4. Then the early cursor Elo line, from `cursor/chess-engine-elo-bba2` at `2285d91270f53f37d4c7bfdf491ed490c7d0c1a1` through `cursor/smp-threads-fixes-c7cb` at `c4314e3bde6e8372419227cc22b032319487aa71`.
5. Keep fixes and experiments on this checkpoint branch, separate from `inventory/`. Do not push to `main`, the lock, the H512 branch, or another agent's branch.
