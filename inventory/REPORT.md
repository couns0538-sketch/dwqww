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
