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

## Run 2

Trigger 15:26 UTC on 2026-11-13. `git fetch origin --prune` and `git ls-remote --heads origin` at 15:33 UTC. The run-1 table `inventory/branches.tsv` is unchanged. The live list is `inventory/branches-current.tsv`. Movement is appended in `inventory/HEAD_MOVEMENT.tsv`. Per-branch status is `inventory/review-status.tsv`.

| Item | Value |
|---|---|
| Remote heads | 430. The local remote-tracking refs match `ls-remote`. |
| Same tip as run 1 | 421 |
| Moved | 3 |
| New | 6 |
| Gone | 0 |
| Unique tips now | 341 (335, minus the 3 replaced tips, plus 9 new tip commits) |
| Unique tip trees | 341. None of the 9 new trees matches a run-1 tip tree. |
| Shared-tip groups | still 16 groups, 105 branches. The 9 new tips are not in those groups. |
| Tags | the same 3 as run 1, not reviewed |
| Inaccessible heads | none in this fetch |

`refs/remotes/origin/HEAD` still points at `main`. Prefix counts are unchanged except `cursor/`, which is 23. The run-1 prose said `fable*` 26; the run-1 table has 28 names that start with `fable`. No fable branch moved.

The 421 unchanged tips were not opened. Five of them stay at the run-1 detail status (`cursor/forge-concurrency-audit-8d98`, `cursor/forge-history-index-20261113-712a`, `cursor/forge-nnue-eval-20261113-22cc`, `cursor/forge-qsearch-audit-60ce`, `cursor/move-legality-82b6`). The other 416 stay "tip and tree confirmed, files not read."

Ancestry of the 341 current unique tips, from the run-1 census plus these nine commits (the 421 were not re-merged):

- 17 contain the lock commit `16833ecc`. Eleven of those also contain the H512 commit `efb2ff96`.
- 39 contain `main` and do not contain the lock.
- 285 contain neither.

### Moved tips

| Branch | Was | Now | What the new commits are |
|---|---|---|---|
| `cursor/forge-correctness-20261113-e6b6` | `dff76c58` | `f6760ff6` | `ffc19fa3` clears per-worker history at each root. `f6760ff6` waits for attack tables with `std::call_once`. |
| `cursor/forge-search-strength-20261113-9558` | `c9cb47a4` | `49b80952` | One commit. Late-move pruning and reduction are skipped when the root opponent is a lone king and the node still faces a lone king. |
| `cursor/forge-time-audit-770f` | `82b4a082` | `33547894` | The time-audit script runs `forge` from `PATH` and no longer takes a binary argument. Engine search is unchanged in this commit. |

### New heads

All five engine branches are one to three commits on `fable/standalone-h512-20261111` (`efb2ff96`). They do not contain each other's commits. The sixth new head is this checkpoint at its pre-commit tip `13dcd58e` (77 files, contains the lock, does not contain H512).

| Branch | Tip | Files | Note that was read |
|---|---|---:|---|
| `cursor/search-bound-audit-9cd5` | `f46e8d24` | 659 | `forge-combo29/docs/audit/ASPIRATION_PVS_BOUNDS.md` |
| `cursor/search-bounds-audit-e6d7` | `ee965c4f` | 659 | `forge-combo29/docs/search_bounds_audit.md` |
| `cursor/draw-rules-history-tt-cb8e` | `844cef9a` | 659 | `forge-combo29/docs/draw_rules_check_20261113.md` |
| `cursor/tt-audit-bounds-4ffa` | `22e837cb` | 659 | `forge-combo29/docs/tt_audit_20261113.md` |
| `cursor/forge-audit-f132` | `9a781745` | 660 | `AUDIT_REPORT.md` |
| `cursor/forge-branch-inventory-automation` | `13dcd58e` | 77 | the run-1 inventory |

`cursor/forge-audit-f132` says it saw 417 refs. That count is earlier than this fetch. It is not the current census.

## Defects present in source

These are on the lock `16833ecc` and on H512 `efb2ff96` unless a row says otherwise. Line numbers are the ones read this run. A "their result" column is the other branch's log. This run did not rebuild those binaries and did not replay the numbers.

### Quiet mate lost after another search

Position `4R3/8/8/k2K4/8/8/8/8 w - - 0 1` is mate in 3 by `d5c5`. On H512, late-move pruning is the block at `forge-combo29/src/search.cpp:1575` (`!root_node && best_score > -MateInMaxPly && has_material`); the quiet threshold is `lmp_threshold` at line 1576. History tables survive the previous root. `Clear Hash` does not clear them.

Two unmerged fixes, both claiming the combo29 bench pins and no games:

- Correctness `ffc19fa3`, `Worker::search` calls `clear_heuristics()` at `forge-combo29/src/search.cpp:1786` on `f6760ff6`. Their note: after any of three depth-9 searches, depth 14 played `e8e4`; after the clear, all four protocols played `d5c5` mate 3. Threads 2 missed 57/400 before an earlier bare-king gate and 0/400 after it. That gate stays off for one worker because turning it on moved depth 13 to 862954 net on and 907307 net off.
- Search-strength `49b80952` does not clear history. `root_bare_king_` is set at `search.cpp:1994` and the prune skip is at `search.cpp:1775`. Their note: the same three poison searches then played `d5c5` mate 3, and 40 two-thread depth-14 searches missed 0. Depth 13 stayed 862329 net on and 907205 net off. A bare king that appears only after trades still uses the old pruning.

The two patches are not on one branch. Neither is an Elo result. The node counts are their logs.

### Attack tables published before they are filled

H512 and the lock: `forge-combo29/src/bitboard.cpp` sets `initialized = true` and then fills the tables (lock line 137, H512 line 137). Correctness `f6760ff6` uses `std::call_once` at `bitboard.cpp:143`. Their driver: 30/30 segfaults before, `bad 0` on 30/30 after, then `PINS MATCH combo29`. `cursor/forge-concurrency-audit-8d98` describes the same race on a different history. This run did not repeat it. The concurrency branch still has the integer clock parse. The clock fix is only on `cursor/forge-time-audit-770f`.

### Draw rules inside the search

Game adjudication at the root already treats threefold, a clock of 100, and insufficient material as draws. Inside the tree, on the lock and on H512:

- `Board::is_repetition(root_index)` returns a draw when the matching key index is `>= root_index` (lock `board.cpp:1208`, H512 `board.cpp:1208`). Returning to the root is only the second occurrence.
- `Board::make_null_move` increments `halfmove_` (lock `board.cpp:1126`, H512 the same assignment). A null move is not a game ply.
- `score_from_tt` adjusts a mate by ply and does not look at the halfmove clock (`search.cpp:126` on H512, `search.cpp:123` on the lock).

`cursor/draw-rules-history-tt-cb8e` commit `7639e548` stops the null-move clock and requires the repeat to be strictly after the root. Their `draw_rules_test` passed. Their engine table, UseNNUE false, says a twofold knight shuttle at depth 4 stays `cp 13` and a threefold shuttle at depth 3 is `cp 0`. Queen versus king at clock 92 was a draw at depth 8 on unmodified H512 as well (87721 nodes); after the null-move change and before the quiescence correction it was `cp 695`. Bench depths 8 and 10 matched H512 (67223 and 172081). They did not run the depth 11–22 pin script. Opposite-colour bishops and king plus two knights are not adjudicated. No match.

The same mate-versus-clock idea is patched three more times, with different cutoffs, and those patches are not stacked:

| Branch | Default | Rule they implemented |
|---|---|---|
| `cursor/search-bounds-audit-e6d7` | always on | Drop a mate longer than `99 - min(clock, 99)`. Distance 19 is kept at clock 80 and distance 20 is not. Their full pin script matched. |
| `cursor/search-bound-audit-9cd5` | `mate_horizon` on | Drop a mate when `D > 100 - min(clock, 100)`. Their shipping combination matched the pins through depth 22. |
| `cursor/tt-audit-bounds-4ffa` | `FORGE_TT_MATE_CLOCK` **off** | With the switch on, drop a mate when the distance is greater than `100 - clock`. The default `forge` binary still has the unguarded conversion. |

### Transposition table, default binary unchanged

On H512, `TranspositionTable::store_body` writes `clusters_[probe.cluster_].entries[probe.slot_]` (`search.cpp` store body, the `FORGE_SPD_TT_NOTLS` path). Qsearch returns `mated_in(ply)` at `search.cpp:1355` before `tt.store`. Main search returns `mated_in(ply)` at `search.cpp:1717` before the store. `cursor/tt-audit-bounds-4ffa` reproduces three failures on the baseline objects and compiles the fixes only into `tt_audit` (`FORGE_TT_MATE_CLOCK`, `FORGE_TT_STORE_TERMINAL`, `FORGE_TT_RESOLVE_SLOT`). The default binary leaves all three at 0, and their `check_pins.sh` on that default binary matched. With the switches compiled on, depth 20 net on moved from 12389307 to 12117140 and depth 22 net on moved from 34048354 to 37041976. Their isolation build says the depth-20 delta is the checkmate store. Those switches stay off because the pins move. The three bugs are still in the default engine.

### Aspiration, PV bounds, and the LMR clamp

`cursor/search-bound-audit-9cd5` keeps `mate_horizon` and `aspiration` on and `qsearch_shallow_bound` off. Their note, not replayed here:

- Fail-low arithmetic can leave the window unchanged: alpha `-32001`, beta `-32000`, score `-32001`. They did not see a finished bench return the `-Infinite` sentinel. The loop can no longer repeat that window.
- An aborted re-search used to publish a worse root move with the previous iteration's score. Their test hook keeps `d2d4` at +16 instead of `a2a3` at +16.
- A depth-0 TT upper bound of `-400` in a queen ending was returned as `-400` with the qsearch switch off and 832 with it on. The switch is off because depth 13 net on moves from 862329 to 793816.
- `std::clamp(new_depth - r, 1, new_depth)` is undefined when `new_depth < 1`. H512 `search.cpp:1671`, lock `search.cpp:1417`. The guard is unconditional. At the default singular depth of 7 they say it does not change the pins. They did not show a search that actually took a negative extension.

`cursor/search-bounds-audit-e6d7` is a different patch. Always on: an aborted aspiration no longer pairs a new move with the previous score, and the fifty-move mate filter above. Default off: `PvBoundFix` (skip move pruning on PV nodes) and `AspirationKeepExact`. Their start-position command `go depth 10 nodes 2066`, NNUE off, printed depth 6 `cp 3` and `g1f3` while a finished depth 6 was `cp 18` and `e2e3` (2524 nodes). With the patch the partial line keeps its own score. `PvBoundFix` at 1 changed root scores at depth 7, including missing a mate in two (`g3g6` on `2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1`) that the lock finds at depth 7 in 2725 nodes. The switch stays 0. Quiescence still prunes on PV nodes. No Elo.

### UCI protocol on the H512 binary

`cursor/forge-audit-f132` confirmed these on a g++ build of `efb2ff96` and then changed the default binary, not a switch:

- `uci.cpp:377` compares the option name to `"UseNNUE"` and the value to `"true"` / `"false"` (lock `uci.cpp:262`). `usennue` and `False` do not match. Their pre-fix `bench 11` stayed at the net-on pin 312866 after `setoption name usennue value false`.
- `searchmoves` of only illegal moves set the restriction and then played `bestmove 0000` (`uci.cpp:117`). Their fixed binary returns a legal move.
- `Board::set_fen` rejects a FEN that is not six fields (`board.cpp:219` on H512). A four-field FEN was consumed together with the word `moves`.
- `Board::parse_uci` compares the token to the lowercase UCI text (`board.cpp:1148`). `E2E4` and `a7a8Q` were rejected.

Their fixed g++ binary matched depth 11 and depth 13 pins, net on and off, and perft 5 was 4865609. They did not print depths 16, 20, or 22. `uci_protocol.py` reported 0 failures after the book test was pinned to variety 0 (`e2e4`). No games. Classic NNUE accumulator versus a full refresh: 181 plies, gap 0, so they did not change the accumulator. An AVX2 accumulator update was bit-identical and slower on this VM (update loop 31–32 ms versus 23–24 ms) and stays off. That timing is not a speed claim for another machine.

`dot/review-20261110` at `f5c5efaa` has `F6-uci-case.patch` behind `FORGE_FIX_UCI_OPTION_CASE`. Their reading: it lowercases names and still compares checkbox values to exact `true` and `false`. This run did not open that patch.

### Still open from run 1

`bad_captures_[bad_count_++]` has no capacity test. The lock array is 64 (`search.cpp:576`). Correctness sizes it to `MoveList::Capacity` (256, `board.hpp:109`) and still writes at `search.cpp:472` with no index check. A position with more than 256 deferred captures was not searched.

H512 `uci.cpp:92` still returns 0 when `std::from_chars` fails, which is the clock overflow run 1 reproduced on the lock (`go wtime 3000000000` played `a2a3` with no `info depth`). The five new H512 branches do not include the time-audit parser. The time-audit branch does, and its new commit does not change that parser.

## Not claimed

- No Elo. H512 `STATUS.md` numbers quoted inside `AUDIT_REPORT.md` (M8 +53.2, M9 -5.9) were not replayed. Bench node counts above are the other branches' pin logs.
- The 421 unchanged tips were not re-read. The fable52 evidence files named for this run were not opened, because the remote moved and this batch is that movement.
- No engine was promoted. Nothing was pushed to `main`, `lock/combo29-20261110`, `fable/standalone-h512-20261111`, or another agent's branch.
- Supermemory was unavailable. Adapter was not used.

## Next run

1. `git fetch` and `git ls-remote --heads origin`. Diff against `inventory/branches-current.tsv`. Append new rows to `inventory/HEAD_MOVEMENT.tsv`. Do not rewrite run-1 `inventory/branches.tsv` or earlier movement rows. This branch's tip will have moved by the commit that adds these files; record that as this checkpoint, then continue.
2. If a foreign tip moved, read that delta before the fable52 files.
3. Otherwise read, on their own tips, and do not quote a speed or sanitizer figure past what those files themselves show:
   - `fable52-search-gap-20261109` `56a76b153bb8` `fable_search_gap/EVIDENCE.md`
   - `fable52-speed-lane-20261109` `08897a88e11c` `fable_speed_lane/BENCH.md`
   - `fable52-movegen-proof-20261110` `2ff77f98927c` `fable_movegen_proof/PROOF.md`
   - `fable52-cpu-20261110` `ea3759a9ec3b` `fable_cpu_speed/DONE.md`
4. The highest-priority unverified finding is the KRK history miss (`4R3/8/8/k2K4/8/8/8/8 w - - 0 1`, `d5c5` mate 3). Replay it on H512, then on `f6760ff6` and `49b80952`, before treating either fix as the one to keep. Second: one UCI case from `efb2ff96` (`setoption name usennue value false`, or `go depth 1 searchmoves h7h5`). Third: the 256-slot `bad_captures_` write still has no check.

## Run 3

Trigger 16:26 UTC on 2026-11-13. `git fetch origin --prune` and `git ls-remote --heads origin` at 16:28 UTC. The run-1 table `inventory/branches.tsv` is unchanged. The live list is `inventory/branches-current.tsv`. The new movement row is appended in `inventory/HEAD_MOVEMENT.tsv`.

| Item | Value |
|---|---|
| Remote heads | 430. Local remote-tracking refs match `ls-remote`. |
| Same tip as the run-2 table | 429 |
| Moved | 1. This checkpoint, `13dcd58e` to `b39899a4`, the run-2 commit. Not foreign work. |
| New | 0 |
| Gone | 0 |
| Unique tips | 341. One tip replaced another. |
| Unique tip trees | 341. The new checkpoint tree `2868c708` matches no other tip. |
| Shared-tip groups | still 16 groups, 105 branches |
| Tags | the same 3, not reviewed |
| Inaccessible heads | none in this fetch |

`refs/remotes/origin/HEAD` still points at `main`. Ancestry counts are unchanged: both checkpoint tips contain the lock and `main`, and neither contains H512. 412 branches stay tip-only. The four fable52 tips below were tip-only and are now `run3-read`.

No engine was built this run. Every number below is a number in the named file. None of it is a match, and none of it is Elo.

### Enhanced transposition cutoffs

`fable52-search-gap-20261109` at `56a76b153bb88026f2d83d65df6e422b0f3298f9` (75 files). Read: `fable_search_gap/EVIDENCE.md`, `fable_search_gap/STATUS.md`. Not opened line by line: `NO_QUALIFIED_GAP.md`, `tools/etc_probe/etc_probe.cpp`, the TSV files. This tip contains `main` and does not contain the lock commit or H512. The measurements used a lock executable and a source snapshot on a PC. This branch does not hold combo29 `search.cpp`.

Their verdict is **NO QUALIFIED GAP**. The lock, in the source they read, takes a table cutoff only from its own entry (`search.cpp:1165-1170`) and prefetches a child without reading it (`search.cpp:1379-1383`, quiescence `1066-1070`). The probe is a separate search linked to the lock board and evaluation. It has no singular extension, multi-cut, ProbCut, razoring, continuation history, or net. On 24 positions the lock searched 36.9 million nodes and the replica 25.5 million.

On 91 distinct positions, taking the cutoff gave geometric node ratios 0.919 to 0.950, and every range that treats a base position and its descendants as one cluster includes 1.00. A placebo that only changes a history constant from -32 to -31 gave 0.984 and changed as many best moves. On 336 positions from 48 openings, with the reading rule committed before the run, cut6 is 0.987 with range by opening [0.954, 1.022]. They treat that as "not shown either way" and say an average saving above about 5% is ruled out in that replica at those depths. With six pieces or fewer the estimate is 5 to 6% and the range still includes 1.00.

Fine 70, `8/k7/3p4/p2P1p2/P2P1P2/8/8/K7 w - - 0 1`: the lock executable plays Kb1 from depth 22. The plain replica also plays Kb1. Three of eight mechanism settings play the drawing move Kb2 at some depth. Under ten nearby history constants, plain is right in 10 of 10 and the mechanism settings miss in 31 of 80 runs. Those ten constants collapse into two or three groups, and at depth 40 only 3 of 80 still miss. The cause is not established. It is one position in the replica.

Lookup wall time was a few percent and too noisy, on a loaded machine, to say whether the lookups cost more than they save. The optional counting run named in `FALSIFICATION.md` was not done. No Elo.

The probe source exists. That is not a measured gain in the lock search, and the Fine 70 miss is a reason not to port the cutoff until a lock-search test checks the move as well as the node count.

### Bit-exact speed patches

`fable52-speed-lane-20261109` at `08897a88e11c707c0ac4e39c19e44c06e1360bdd` (293 files). Read: `fable_speed_lane/BENCH.md`, `fable_speed_lane/STATUS.md`. The eight patch files under `fable_speed_lane/patches/` exist and were not opened. Evidence JSON was not opened. This tip contains `main` and does not contain the lock commit.

The patches are against a combo29 snapshot that this branch does not contain. New switches: `WITNESS_NOPIN`, `EVADE_LEGAL`, `PAWN_CAPMASK`, `CHECKERS_KL`, `BUNDLE4` (all four), `BUNDLE3` (without `WITNESS_NOPIN`). `KING_PAWN_CACHE` is the shelter cache already committed as `928f1ff7` on `cursor/chess-engine-elo-8295`. They kept the combo29 port as a labelled extra, not a new idea.

Finished identity checks found no difference: switch-0 builds differ from the lock executable in 89 debug-record bytes and 0 other bytes; 12 pins match; a harness over 12,000 FENs matches; the warm transcript matches and bench 13 stays 862329; a Threads 2-4 soak returns legal moves; the perft set matches. Planted faults: 15 of 15 caught in the single trees, 12 of 12 in `BUNDLE4`. The `BUNDLE4` verify engine matched all 12,000 cold rows. The first text of `CHECKERS_KL` treated an illegal king step beside the enemy king as "no check"; the final text keeps `attackers_to()` for king moves. That final text is the one in the pack. This run did not re-check it.

Plain cold runs of 12,000 positions were stopped at 16:56 Vienna. Every finished row equalled the lock. No item finished both nets. `BUNDLE3` mutants stopped after a clean control.

Cycle timing, their label INDICATIVE, one Idle core while gates ran. Positive means the candidate used fewer cycles. Lock against lock, 40 blocks: -0.02%, interval -0.27 to +0.24. `WITNESS_NOPIN`, 60 blocks: -1.02%, interval -1.25 to -0.86. `BUNDLE4`, 100 blocks: -0.70%, interval -0.99 to -0.39. `BUNDLE3` and the three singles stopped at 34 blocks; the intervals include 0 and the point estimates are -0.22 to -0.63. `KING_PAWN_CACHE` has 5 blocks. No item's interval sits entirely above 0. No Elo.

A separate method result, not an engine result: one fixed pair of executable files read -3.65% over 30 tight blocks and about +0.30% two hours later. Byte-identical copies differed by as much as 6% in a single block. Their later rows use a new copy for every arm. This run did not repeat that test.

On one frozen workload of 4,200,115 nodes, exact counters (not time): `WITNESS_NOPIN` removes 37.7% of king-line builds and 21.7% of `is_legal` calls; `EVADE_LEGAL` removes 64.2% of full king-attack tests; `PAWN_CAPMASK` removes 93.3% of pawn-capture loop iterations and emits the same captures; `CHECKERS_KL` removes 42.2% of `attackers_to` calls; `KING_PAWN_CACHE` removes 69.5% of shelter terms. Searches entered and `make_move` counts stay the same. Less counted work did not become a measured speed gain.

### Move-generator proof of those patches

`fable52-movegen-proof-20261110` at `2ff77f98927cf19d55d6cac5cf182a81eb0d71e6` (594 files), one job on top of the speed-lane tip. Read: `fable_movegen_proof/PROOF.md` (verdicts, pins, perft, fuzz counts, limits, replay table) and `STATUS.md`. Ledgers, `VERDICTS.json`, and the harness source were not re-counted. This tip contains `main` and does not contain the lock commit.

Six candidates PASS their two-tier rule, 0 differences: `EVADE_LEGAL`, `PAWN_CAPMASK`, `CHECKERS_KL` mode 1, `WITNESS_NOPIN`, `KING_PAWN_CACHE`, and `BUNDLE3`. Each has 20,000,000 auxiliary comparisons (moves, checkers, static eval, both net modes) and 20,000,000 release-executable `go perft 2` comparisons. All nine executables match 13 pins, including net-on 312866 / 862329 / 3024920 / 12389307 / 34048354 and net-off 375354 / 907205 / 2448617 / 13573040 / 24506465 at depths 11, 13, 16, 20, and 22. Perft divide matches the published totals where they name one. The warm transcript matches. The Threads soak shows no crash and legal moves; it does not show node identity.

`CHECKERS_KL` mode 2 was never built. The five-flag bundle was not tested. Checkers and static eval were not printed by the release executables; those fields were compared on probes built at `-O3` without link-time or profile-guided optimisation. Job 3 did not plant engine mutants. The second review was written by the author after an independent reviewer was stopped. A PASS, in their own words, does not authorise a lock change and says nothing about speed. This run did not replay a chunk.

`WITNESS_NOPIN` can be node-identical on the positions they tested and still slower in the speed-lane cycle screen. Both notes are about different questions.

### CPU lane on the lock commit

`fable52-cpu-20261110` at `ea3759a9ec3b17c58e3daeab8ff31af53e7ae6ab` (222 files) contains the lock commit `16833ecc` and does not contain H512. Read: the verdict tables and bug-hunt table in `fable_cpu_speed/DONE.md`, and `fable_cpu_speed/STATUS.md`. The MD5 catalogue, raw logs, and the four patch files were not opened. Nothing was rebuilt.

Their control rebuild matches 13 pins and the lock executable's code and data bytes. The executable SHA256 differs because of the debug record. A sampler attributed 20.9% of samples to hand-crafted evaluation. That is one profile on their machine.

Speed verdict: **NO WIN** against a bar of +2.0% they set before the runs. Screening medians of 12 pairs, other work running. Lock against lock by the same method: median -0.30%, min -5.19%, max +7.68%. `NNUE_FUSE_EVAL` +0.93% (a repeat +1.46%). `PREFETCH_PICK` +0.72%; their harness comparison does not exercise that patch. `EVAL_PIPELINE` -1.53%. `NNUE_WPREFETCH` at distance 16, -4.42%. The two positive medians sit inside the null range. They stopped them. No Elo. A combined quiet test of the two small flags was not run.

ASan and UBSan: their logs say the bench node counts equal the pins and no report was printed. ThreadSanitizer is BLOCKED; the Windows compiler refused the flag. Determinism: 13,000 of 13,000 row comparisons equal. Table stress: 480 of 480, and an ASan run of 240 searches printed no report. Threads 2 through 9, fixed nodes: 600 of 600 legal best moves and no sanitizer report. That is not node identity. The extra bug hunt found no defect: 520 UCI cases with no crash, and a hardened build matched the lock executable on 4,000 depth-13 rows and 20,000 depth-10 rows. Clocked searches stayed inside the budget except by under half a millisecond at 1 ms budgets. C6 and C7 did not run. The branch-history duplicate check is UNVERIFIED because that job was not allowed to fetch.

### Not claimed

- No Elo, and no new measurement from this run. Node ratios and cycle percentages above are the other jobs' logs.
- 412 tips are still unread. Probe source, patch texts, ledgers, and raw logs of these four branches were not opened.
- The KRK history miss, the H512 UCI case, and the 256-slot `bad_captures_` write were not replayed.
- Nothing was pushed to `main`, `lock/combo29-20261110`, `fable/standalone-h512-20261111`, or another agent's branch.

## Next run

1. `git fetch` and `git ls-remote --heads origin`. Diff against `inventory/branches-current.tsv`. Append one row to `inventory/HEAD_MOVEMENT.tsv`. Do not rewrite `inventory/branches.tsv` or earlier movement rows. This branch's tip will have moved by the commit that adds these files; record that as this checkpoint, then continue.
2. If a foreign tip moved, read that delta before the packs below.
3. Otherwise read these small unread tips, and do not execute their scripts:
   - `cursor/match-pgns-66cc` at `f481fc5afc6bf13b730fe5853fbefaeeb6047162`: `EXPERIMENTS.md` and `README.md`.
   - `cursor/smp-threads-fixes-c7cb` at `c4314e3bde6e8372419227cc22b032319487aa71`: the four documents on that tip.
   - `cursor/speed-and-search-patches-c7cb` at `2cf370d3e7672c18692bfa044ec376e6e584eff6`: the patch list and any result note.
4. The KRK replay remains the first reproduction when a run investigates instead of opening the next pack. Position `4R3/8/8/k2K4/8/8/8/8 w - - 0 1` should play `d5c5`. Run it on H512 `efb2ff96`, then on `f6760ff6`, then on `49b80952`. Do not keep either fix until both have been replayed on one machine.
5. Do not push to `main`, the lock, the H512 branch, or another agent's branch.

## Run 4

Trigger 17:24 UTC on 2026-11-13. `git fetch origin --prune` and `git ls-remote --heads origin` at 17:29 UTC. The run-1 table `inventory/branches.tsv` is unchanged. The live list is `inventory/branches-current.tsv`. Seven movement rows are appended in `inventory/HEAD_MOVEMENT.tsv`.

| Item | Value |
|---|---|
| Remote heads | 430. Local remote-tracking refs match `ls-remote`. |
| Same tip as the run-3 table | 423 |
| Moved | 7. One is this checkpoint, `b39899a4` to `00bc9129`, the run-3 commit. The other six are foreign. |
| New | 0 |
| Gone | 0 |
| Unique tips | 341. Seven tips replaced seven tips, and none of the replaced commits is still a branch tip. |
| Unique tip trees | 341. None of the seven new trees matches another current tip. |
| Shared-tip groups | still 16 groups, 105 branches |
| Tags | the same 3, not reviewed |
| Inaccessible heads | none in this fetch |

`refs/remotes/origin/HEAD` still points at `main`. Each new tip has the same lock, H512, and `main` ancestor bits as the tip it replaced, so the ancestry counts stay 17, 11, 39, and 285. 409 branches stay tip-only. The only remaining `run1-detail` tip is `cursor/forge-nnue-eval-20261113-22cc`.

No engine was built this run. Game counts below were counted in the PGN files. Every Elo, LLR, bench, and sanitizer figure is a figure in the named file.

### Joined node count on the info line

`cursor/forge-concurrency-audit-8d98` moved from `2d2a3fa7` to `9267bf2efabd28fc8a958c08c22b4c46fe87da68` (43 files). One commit. This history contains `main` and does not contain the lock commit. Read: the diff in `forge-combo29/src/search.cpp`, `include/forge/search.hpp`, and `docs/CONCURRENCY_AUDIT.md`, plus the evidence lines that carry the node counts.

Helpers already summed into `SearchInfo::nodes` after the join. The `info` lines were still sampled before that join. The new code stores the last printed line on the main worker and, when `emit_info` is set and the post-join total differs, prints one more `info` line with the same depth, score, and PV and the joined node count (`search.cpp:1856`). That line's `nps` uses the earlier line's timestamp. Bench does not print `info`.

Their evidence files contain the counts the note quotes. `docs/evidence/info-nodes-gap.txt` says `info_nodes 1883` against `result_nodes 3526` before the extra line, and `2717` against `2717` after it. `docs/evidence/post-fix-info-nodes.txt` and `docs/evidence/tsan-concurrency-info.txt` end `ALL PASS failures 0`. This run did not rebuild the suite. The integer clock parser on this branch is untouched. No Elo.

### Capped middlegame on the 5.31.0 quiescence branch

`cursor/forge-qsearch-audit-60ce` moved from `d5db74e1` to `b763354d4e46b8d9cc03e7087ef8026f9f27698d` (23 files). The only change is `forge/QSEARCH_AUDIT.md`. No source file and no log was added.

The note now says the FEN `r2qk1nr/3n1ppp/1pp2b2/p2pp3/1PP3bP/P4N2/2QPPPPR/RNB1KB2 w Qkq - 2 11` is not in check, has 28 quiet moves and 4 tactical moves, and has static evaluation -26. It says the engine quiescence search returns -26 after 563 nodes, and the same contract with its own transposition table searched 1,353,971 nodes and also returned -26. That agreement is their sentence. This run did not rebuild the 5.31.0 tree. This is not combo29.

### Leading plus, and `bench` honoring `stop`

`cursor/forge-time-audit-770f` moved from `33547894` to `e5fe43671ead84fe48bb9696a8ca119bb3636c05` (74 files). One commit on the lock history. Read: `forge-combo29/src/uci.cpp` and `docs/time-audit.md`.

`read_int` skips one leading `+` before `std::from_chars` (`uci.cpp:81`). `+80` parses as 80. `++80` and `+80abc` still fall through to 0. An out-of-range token still clamps, which was already on the previous tip. `bench` now runs on a worker thread (`uci.cpp:429`). `stop` sets the flag on that searcher under the same mutex that publishes it. On cancel the engine prints `info string bench stopped` and does not print a node signature.

Their note says `ctest` passed `uci_time_audit` in 4.92 s, `movetime +80` used 81.2 ms, and `bench 14` then `isready` then `stop` answered `readyok` in 0.4 ms and `bench stopped` in 0.7 ms, with uninterrupted depth-10/12/14 signatures 172081, 467411, and 1196277. This run did not execute `tools/uci_time_audit.py`. No Elo.

### Bench pins and the network update, as recorded

`cursor/move-legality-82b6` moved from `f1c701c9` to `1adfc1c2cb9b958c2bc69cfe32d0f5916aff7077` (661 files). One commit on H512. The search behavior of the fullmove fix is unchanged. Read: the new section of `forge-combo29/docs/MOVE_LEGALITY_20261113.md`. The probe source `forge-combo29/tools/nnue_delta_probe.cpp` was added (186 lines) and was not compiled.

The note says a Linux g++ release build matched the lock pins: net on 312866, 862329, 3024920, 12389307, 34048354 and net off 375354, 907205, 2448617, 13573040, 24506465 at depths 11, 13, 16, 20, and 22, and `go perft 5` printed 4865609. It says the probe checked 525 legal moves (13 castles, 6 en passant, 41 promotions, 36 null moves) and every incremental accumulator matched the refresh with `max_abs 0`. The transcript is outside the tree. The note says the binary is not the published clang PGO executable and that its nodes per second are not a speed result. This run did not rebuild it.

### Quiescence PV pruning stays behind the same switch

`cursor/search-bounds-audit-e6d7` moved from `ee965c4f` to `569c9315b501a1910c174c8908cd633468e09dbf` (659 files). One commit on H512. Read: the diff in `search.cpp`, `search.hpp`, and `docs/search_bounds_audit.md`.

`PvBoundFix` remains 0 (`search.cpp:76`). At 0 the new condition `!(pv_node && tune::PvBoundFix != 0)` is true, so futility and SEE in quiescence stay on the lock path (`search.cpp:1343`). The added counter does not change which move is searched. At 1, a PV quiescence node skips that pruning. Their note says the start-position depth-7 counters, NNUE off, are 201 in the main search and 18 in quiescence with the switch at 0, and both 0 with the switch at 1. On `2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1` they now say the switch at 1 misses `g3g6` at depth 7 (`cp 148`, `f6e8`, 3359 nodes) and at depth 10 (`cp 133`, `f6e8`, 32191 nodes) and finds it at depth 11 (66435 nodes). The previous tip of this same note had found the mate at depth 10. The switch stays 0. No Elo. This run did not replay the position.

### History-index pass, and what was opened

`cursor/forge-history-index-20261113-712a` moved from `da51693e` to `d4532d72914100569331a2f66abdb9ebbaf4f68a` (681 files). Four commits. Read: the diffs of `COVERAGE.md`, `HANDOFF.md`, `README.md`, `RESUME.md`, `findings/BUGS.md`, and the new `findings/LIVE_AUDITS.md`. Counted from the tip: `EVERY_TIP.tsv` has 429 data rows (246 `claimed`, 170 `alias`, 13 `live-report`), `PRIMARY_CLAIMS.tsv` has 387, `WAVE2_CLAIMS.tsv` has 2304, and `LONG_PRIMARY_REREAD.tsv` has 53. The 2304 sentences were not each opened. The engine was not run.

`EVERY_TIP.tsv` matches 424 of the 430 heads in this fetch. It omits its own branch. It is stale on the five engine tips above (concurrency, qsearch, time, move legality, search bounds). `LIVE_AUDITS.md` still cites the older tips of those branches, and it cites this checkpoint at `00bc9129`, which is the tip before the commit that adds this section. Its movement log does not contain those five moves.

Eight blobs named in the new `BUGS.md` lines were opened. The sentences match the blobs, with the figures below taken from the blobs themselves:

- SEE research note, blob `954844ec`, `validation/see-recapture-promotion-20261020/DESIGN.md`. Status in the file: research and design only, no implementation and no match. At `1r6/P1Q5/2n4k/8/8/8/8/7K w - - 0 1`, move `c7b8`, source16 `see_ge(0)` is false and the target-only oracle is +500. The same note says six exchange-value disagreements and 44 wrong answers among 200 threshold queries.
- Promotion-SEE status, blob `29a7fa54`. The parent fails 16 assertions. The candidate passes those, a 324-case oracle, and 30 search-margin checks where the parent had 10 errors. The file says one forced position, not a best-move or Elo result.
- Syzygy review, blob `2a711099`, `opus_syzygy_gaps/review/R2.md`. At depth 14, 27 of 39 null-move tablebase claims on 120 near-zugzwang roots were wrong, in 12 roots. That is their instrumented candidate, not the lock.
- Rule-50 plan, blob `d26b9730`. At halfmove 99 a low-clock table bound returns -426 instead of 0, and the plan says reverse reuse turns a quiescence score of -426 into 0 and a static evaluation of 453 into 0. The underlying log is a zip this run did not open.
- KRK report, blob `89cf9262`, `opus_r5/r5d/MATEFIX_REPORT.md`. Baseline 180 misses in 8,000 KRK runs. Their BKM fix is on only while more than one worker searches, and Threads 1 stays bit-identical. They record 0 misses in 40,000 KRK runs at Threads 2 and 4. That patch is not either of the two unmerged one-thread fixes (`f6760ff6` clears history, `49b80952` gates a lone king already at the root). It was not replayed.
- SMP note, blob `e194ba22`. Initial CTest 52/54, with one node-overshoot failure at 27,398 nodes. Later suites in that note pass 133/133.
- Clock matrix, blob `0a38df5c`. 100 of 100 games, 0 illegal moves, and the longest of 28 clock overruns is 62.1 ms. Their matrix, not replayed.
- Hard deadline, blob `a3c1df0d`. `HardDeadline` defaults to 0. Under Windows idle-priority starvation the note records answers 3,750–4,651 ms late, 24 of 24 over 50 ms. With `HardDeadline` 10 the same row is at most 28.8 ms late and 0 of 24 over 50 ms. The Linux row in that note still has 3 of 60 over 50 ms with the option at 10. This is not the combo29 lock.

### October 6.x match record

`cursor/match-pgns-66cc` is unchanged at `f481fc5afc6bf13b730fe5853fbefaeeb6047162` (46 files). It contains neither the lock commit, H512, nor `main`. Read in full: `EXPERIMENTS.md` (244 lines) and `README.md`. The 44 files under `pgns/` were counted and not replayed. `all-match-pgns.zip` and every `console.txt` named in the document are absent from this tip. The document says its Elo and LLR figures were re-read from those consoles.

Every `[Result "` count matches the index. There are 44 files and 76,047 result tags, which is the total the document gives. Sampled files include the cutoff-count SPRT (2,804), the adopted LMP-plus-history SPRT (3,670), the material-correction SPRT (3,213), the 128-net fixed-node match (500), the 128-net 10+0.1 match (200), the 6.4.0 Stockfish match (100), Threads 4 versus 1 (50), the book match (120), and the rejected 768x256 net (300). W/L/D were not re-tallied, so the Elo columns are still their console figures.

What their table treats as accepted by the SPRT rule, elo0=0 elo1=5: cutoff-count LMR, H1 after 2,804 games, LLR 2.96, +20.8 +/- 9.5; and `LmpBase=4` together with the larger history bonus, H1 after 3,670 games, LLR 2.97, +16.5 +/- 8.4. Each half of that pair had run to 8,000 games without a bound.

Adopted in their table without H1: material correction at 3,200 games, 50.77 %, LLR 0.60; the opening book, 120 games, +20 +/- 30; the new evaluation terms, 400 games, +10 +/- 27. Those intervals include 0. The first cutoff-LMR and material-correction runs were A/A: fastchess dropped options the binary did not advertise, both scores were 50.0 %, and the runs were overwritten. The reruns are items 21 and 22.

Their residual 768x128 net, pure search-score targets, is +86 +/- 24 at 20,000 nodes over 500 games and +45 +/- 26 at 10+0.1 over 200 games, against 6.3.0. The 200-game file has 200 `[Termination "normal"]` tags. The 256-hidden net scored +85 +/- 26 at the same node limit and was not shipped. A plain 768x256 net earlier scored 14 wins, 257 losses, 29 draws in 300 games against the hand-crafted evaluation. Against Stockfish 19 at `UCI_Elo` 3000 their 100-game matches do not separate the releases: 6.2.0 +10 +/- 60, 6.3.0 0 +/- 54, 6.4.0 +17 +/- 53. `bench 11` in this document (6.4.0 = 417491) is not a combo29 pin. No figure in this paragraph was recomputed from the games.

### GrokChess threads, and the packed-move patches

`cursor/smp-threads-fixes-c7cb` is unchanged at `c4314e3bde6e8372419227cc22b032319487aa71` (75 files). The engine notes on that tip are `gc1748/README.txt` and `gc1748/SMP-THREADS.txt`. Both were read. There is no fourth engine note. `three_model_prompt.txt` and `grokchess_1745_full_source.txt` were not read. The unified diffs under `gc1748/patches/` were not applied. This is GrokChess 1.7.48, not combo29.

The note describes nine Threads-greater-than-1 failures: a helper's move printed as `bestmove` against the main PV, a depth or infinite search waiting up to 180 seconds, `searchmoves` ignored, ponder starting the clock immediately, a torn shared table whose age advanced once per worker, stores continuing after `bestmove`, a `position` applied during search, and an empty PV when the clock aborted before the first root move. It says the patched single-thread bench matches the unmodified tree at 194011 nodes for depth 9 and 350802 for depth 10, position by position, and that perft 5 is 4865609. Those checks were not run here. No Elo.

`cursor/speed-and-search-patches-c7cb` is unchanged at `2cf370d3e7672c18692bfa044ec376e6e584eff6` (36 files). The commit message lists packed per-ply move lists, `Uint8Array` squares, a flat history, a SEE side array, capture-history ordering, cut-node LMR, history LMR and LMP thresholds, and a lockless shared table, and it calls the speed patches node-identical. No bench log, PGN, or result note is in the tree. The five patch headers were read. `engine/move/movegen.js:19` writes `sink.buf[sink.n++]` into an `Int32Array` of `GEN_CAP` 256 (`movegen.js:31`) with no capacity test in that file. A position that overflows 256 was not searched. This is the GrokChess tree, not combo29. No Elo.

### Not claimed

- No Elo and no new bench from this run. The 76,047 result tags confirm game counts. They do not confirm the W/L/D or Elo columns.
- 409 tips are still unread. The 2,304 wave-2 sentences, the JavaScript patches, and the GrokChess source dump were not read line by line.
- The KRK history miss was not replayed on H512, `f6760ff6`, or `49b80952`.
- Nothing was pushed to `main`, `lock/combo29-20261110`, `fable/standalone-h512-20261111`, or another agent's branch.
- Supermemory was unavailable. Adapter was not used.

## Next run

1. `git fetch` and `git ls-remote --heads origin`. Diff against `inventory/branches-current.tsv`. Append new rows to `inventory/HEAD_MOVEMENT.tsv`. Do not rewrite `inventory/branches.tsv` or earlier movement rows. This branch's tip will have moved by the commit that adds these files; record that as this checkpoint, then continue.
2. If a foreign tip moved, read that delta before the documents below.
3. Otherwise read, on `cursor/engine-strength-overhaul-66cc` at `24cc2cce3eda0e12ddfa4036cd25f7d50e8a3b0b`, and do not execute repository scripts: `README.md`, `CHANGELOG.md`, `RELEASE_STATE.md`, `VALIDATION.md`, and `engine-improvement-log.md`. That tip is the source named by the match-PGN note. Leave the Elo columns in `EXPERIMENTS.md` as their console figures.
4. The KRK replay remains the first reproduction when a run investigates instead of opening the next pack. Position `4R3/8/8/k2K4/8/8/8/8 w - - 0 1` should play `d5c5`. Run it on H512 `efb2ff96`, then on `f6760ff6`, then on `49b80952`. The Opus R5 BKM patch is multi-thread only and is not a substitute for those two.
5. Do not push to `main`, the lock, the H512 branch, or another agent's branch.
