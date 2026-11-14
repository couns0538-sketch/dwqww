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

## Run 5

Trigger 18:26 UTC on 2026-11-13. `git fetch origin --prune` and `git ls-remote --heads origin` at 18:28 UTC. The run-1 table `inventory/branches.tsv` is unchanged. The live list is `inventory/branches-current.tsv`. One movement row is appended in `inventory/HEAD_MOVEMENT.tsv`.

| Item | Value |
|---|---|
| Remote heads | 430. Local remote-tracking refs match `ls-remote`. |
| Same tip as the run-4 table | 429 |
| Moved | 1. This checkpoint, `00bc9129` to `064b3672`, the run-4 commit. Not foreign work. |
| New | 0 |
| Gone | 0 |
| Unique tips | 341. One tip replaced another. `00bc9129` is no longer a branch tip. |
| Unique tip trees | 341. The checkpoint tree `f293db16` matches no other tip. |
| Shared-tip groups | still 16 groups, 105 branches |
| Tags | the same 3, not reviewed |
| Inaccessible heads | none in this fetch |

`refs/remotes/origin/HEAD` still points at `main`. Ancestry counts stay 17, 11, 39, and 285. 408 branches stay tip-only. `cursor/engine-strength-overhaul-66cc` was tip-only and is now `run5-read`.

No engine was built. The nine loose ladder PGNs were scored from `[Result` tags and the engine names in each game. The SHA-256 of `chess-engine-forge-6.4.0.zip` was computed and compared with the release note. Every Elo interval below is a figure in the named document.

### Forge 6.4.0 documents

`cursor/engine-strength-overhaul-66cc` is unchanged at `24cc2cce3eda0e12ddfa4036cd25f7d50e8a3b0b` (928 files). It contains `68f01122` and does not contain the lock commit, H512, or `main`. Read in full: `README.md` (249 lines), `CHANGELOG.md` (925 lines), `RELEASE_STATE.md` (174 lines), `VALIDATION.md` (150 lines), and `engine-improvement-log.md` (80 lines). `validation/release-6.0.0/EXPERIMENTS.md` is blob `4194acfb7accbf58781c24ae7b97dfd1c0c30d84`, the same blob run 4 read on `cursor/match-pgns-66cc`. It was not read again.

The tip contains the archive the PGN branch does not. `validation/release-6.0.0/all-match-pgns.zip` is 67,169,642 bytes. It was not extracted. `chess-engine-forge-6.4.0.zip` is 77,476,927 bytes. Its SHA-256 is `98d2ff2c523a25931897794bad3c39d40398799b8907d51596dad3e326a2ba9d`, which is the digest in `validation/release-6.0.0/release-zip-sha256.txt`. The six binary digests in that note were not recomputed, and the binaries were not run. No `console.txt` for the 6.x matches is in the tree. `bench 11` = 417491 is their signature. This run did not run `bench`.

### Ladder scores counted from the loose PGNs

These files are under `validation/release-6.0.0/` on this tip. Wins are the named Forge side. The counts match the README table. The `+/-` Elo columns were not recomputed.

| File | Forge side | Games | W | L | D |
|---|---|---:|---:|---:|---:|
| `forge-5.31.0-vs-sf19-2800-10+0.1.pgn` | `base531` | 20 | 1 | 17 | 2 |
| `forge-6.0.0-vs-sf19-2800-10+0.1.pgn` | `v3` | 200 | 118 | 42 | 40 |
| `forge-6.0.0-vs-sf19-2800-30+0.3.pgn` | `final` | 100 | 79 | 14 | 7 |
| `forge-6.1.0-vs-sf19-2800-10+0.1.pgn` | `v61` | 200 | 134 | 34 | 32 |
| `forge-6.1.0-threads4-vs-threads1-8+0.08.pgn` | `threads4` | 50 | 26 | 1 | 23 |
| `forge-6.2.0pre-vs-sf19-3000-10+0.1.pgn` | `v62a` | 200 | 66 | 75 | 59 |
| `forge-6.2.0-vs-sf19-3000-20+0.2.pgn` | `v62` | 100 | 35 | 32 | 33 |
| `forge-6.3.0-vs-sf19-3000-20+0.2.pgn` | `v63` | 100 | 33 | 33 | 34 |
| `forge-6.4.0-vs-sf19-3000-20+0.2.pgn` | `v64` | 100 | 35 | 30 | 35 |

`RELEASE_STATE.md` says the 100-game Stockfish 19 games at `UCI_Elo` 3000 do not separate 6.2.0, 6.3.0, and 6.4.0. The separation they claim for 6.4.0 is the self-play against 6.3.0: 209W 88L 203D at 20,000 nodes over 500 games, and 49W 23L 128D at 10+0.1 over 200 games. Those two PGNs are inside the zip. Run 4 counted result tags for those files on the extracted PGN branch and did not re-tally wins. This run did not open the zip, so those two W/L/D columns stay their console figures.

### What the 6.4.0 source contains

The residual network is compiled in. `src/nnue_weights.inc` defines `FORGE_NNUE_RESIDUAL` as 1. `Worker::static_evaluate` returns the hand-crafted score plus the network, clamped, when `nnue::residual()` is true (`src/search.cpp:528`). `CMakeLists.txt:27` compiles the engine library with `-ffp-contract=off`. The changelog's 4–5× `evaluate()` and 1.6–1.8 Mnps sentences are their timing. They were not repeated.

The adopted search defaults are in `src/search.cpp`: `LmpBase` 4 at line 30, `HistoryBonusQuadratic` 20 at line 43, `HistoryBonusMax` 2048 at line 45, `LmrCutoffThreshold` 3 at line 48, `MaterialCorrectionWeight` 100 at line 49. The cutoff reduction is applied at line 1026. The material correction is added at line 544. The SPRT that accepted `LmpBase` together with the history bonus, and the SPRT that accepted cutoff-count LMR, are the run-4 rows. The material-correction SPRT was inconclusive in that same table (LLR 0.60) and the default is still 100.

Rejected in their changelog, with the search defaults left at 6.3.0: `FutilityBase=80` plus `FutilityMultiplier=130` (5,600 games, 50.20 %), `SeeQuietMultiplier=18` (5,000 games, 50.50 %), `QsSeeMargin=80` (3,198 games, 50.00 %), `HistoryPruneMultiplier=3000` (4,600 games, 49.93 %), and `NullMoveEvalDivisor=150` (4,000 games, 49.16 %). A stand-alone 768→256 net and residual training at `--lambda 0.5` are described as worse than the hand-crafted evaluation on their validation loss. Those losses and the game scores were not recomputed.

### Source shapes that were not played

`MovePicker::next` writes `bad_captures_[bad_count_++]` with no capacity test (`src/search.cpp:296`). The array has 64 slots (`src/search.cpp:384`). `MoveList::push_back` asserts at 256 (`include/forge/board.hpp:55`). This is the 6.4.0 tree, not the combo29 lock. No overflow position was searched.

`read_int` parses clocks with `std::from_chars` into an `int` and returns 0 unless the whole token converts (`src/uci.cpp:73`). `wtime` stores `max(0, that)` (`src/uci.cpp:99`). `go` node limits use `uint64_t` (`src/uci.cpp:86`). A present clock of 0 enters the time manager (`src/search.cpp:1136`). With the default move overhead of 10 ms (`src/uci.cpp:128`), `available` is `max(1, time - overhead)` (`src/search.cpp:1139`), so a failed parse becomes a 1 ms budget. That is a different consequence from the lock, where the same class of parse failure played `a2a3` with no depth line. This binary was not run.

A checkmate in quiescence returns `mated_in(ply)` at `src/search.cpp:763` and does not reach the store at line 766. An empty main-search node returns `mated_in(ply)` at line 1074 and does not reach the store at line 1095. `UseNNUE` compares the option name and the value to `true` and `false` (`src/uci.cpp:261`). `Board::parse_uci` accepts a token only when it equals the lowercase text from `move_to_uci` (`src/board.cpp:750`). None of these were played.

The empty-`searchmoves` guard from the 5.30.0 changelog is present: `restricted_root_empty` is set at `src/search.cpp:1169` and the info string is printed at line 1172.

### Older changelog entries

`CHANGELOG.md` from 6.3.0 back through 0.1.0 was read. `VALIDATION.md` and `engine-improvement-log.md` stop at the 5.29.0–5.31.0 cycle; they are the same story as the 5.30 and 5.31 changelog sections. The 6.0.0 section says the 5.x search was replaced. The 5.x entries are records of that older engine. Two positions they name:

- `4r2k/8/8/8/8/8/8/4K3 w - - 0 1` with `go depth 1 searchmoves a1a8`. Unchanged 5.29.0 printed `score mate 0`. 5.30.0 reports a neutral score. The 6.4.0 guard above is the descendant of that fix. It was not replayed.
- `rn1qkb1r/p1p1ppp1/1p1pbn2/7p/3P4/2N1PN2/PPP1BPPP/R1BQK2R w KQkq - 0 1`. 5.30.0 fails low in the depth-9 windows `[53,54]` and `[54,55]`; 5.31.0 raises the quiet LMR floor from 9 to 10. The 6.4.0 reduction is the cutoff-count formula, and this run did not check whether a depth floor of 10 remains.

The 5.x sections say each of those releases made one behavior change and claim no Elo. Small paired screens of 32 games appear from 0.2.0 through 1.7.0 and are described there as provisional. This run did not treat them as measurements.

### Not claimed

- No new Elo and no new bench. The nine loose PGNs confirm the README W/L/D. They do not confirm an error bar.
- 408 tips are still unread. The 6.4.0 zip was hashed and not unpacked. `all-match-pgns.zip` was not unpacked.
- The KRK history miss was not replayed.
- Nothing was pushed to `main`, `lock/combo29-20261110`, `fable/standalone-h512-20261111`, or another agent's branch.
- Supermemory was unavailable. Adapter was not used.

## Next run

1. `git fetch` and `git ls-remote --heads origin`. Diff against `inventory/branches-current.tsv`. Append new rows to `inventory/HEAD_MOVEMENT.tsv`. Do not rewrite `inventory/branches.tsv` or earlier movement rows. This branch's tip will have moved by the commit that adds these files; record that as this checkpoint, then continue.
2. If a foreign tip moved, read that delta before the documents below.
3. Otherwise read the changelog and release-state difference between `cursor/chess-engine-elo-8295` at `928f1ff7a10ad2d36d579b854bfa498768faba2f` and this overhaul tip. `928f1ff7` contains `cursor/chess-engine-elo-d8c5`, `cursor/engine-elo-improvement-3c5f`, and `cursor/chess-engine-elo-6a55`. It does not contain `24cc2cce`. `VALIDATION.md` and `engine-improvement-log.md` are the same blobs already read. Do not execute repository scripts.
4. `cursor/chess-engine-elo-bba2` at `2285d91270f53f37d4c7bfdf491ed490c7d0c1a1` is nine commits past `f96b7475` and is not an ancestor of the 6.x line. Read it after the 8295 delta.
5. The KRK replay remains the first reproduction when a run investigates instead of opening the next pack. Position `4R3/8/8/k2K4/8/8/8/8 w - - 0 1` should play `d5c5`. Run it on H512 `efb2ff96`, then on `f6760ff6`, then on `49b80952`.
6. Do not push to `main`, the lock, the H512 branch, or another agent's branch.

## Run 6

Trigger 19:25 UTC on 2026-11-13. `git fetch origin --prune` and `git ls-remote --heads origin` at 19:30 UTC. The run-1 table `inventory/branches.tsv` is unchanged. The live list is `inventory/branches-current.tsv`. One movement row is appended in `inventory/HEAD_MOVEMENT.tsv`.

| Item | Value |
|---|---|
| Remote heads | 430. Local remote-tracking refs match `ls-remote`. |
| Same tip as the run-5 table | 429 |
| Moved | 1. This checkpoint, `064b3672` to `d6e50b49`, the run-5 commit. Not foreign work. |
| New | 0 |
| Gone | 0 |
| Unique tips | 341. One tip replaced another. `064b3672` is no longer a branch tip. |
| Unique tip trees | 341. The checkpoint tree `b5755ae1` matches no other tip. |
| Shared-tip groups | still 16 groups, 105 branches |
| Tags | the same 3, not reviewed |
| Inaccessible heads | none in this fetch |

`refs/remotes/origin/HEAD` still points at `main`. Ancestry counts stay 17, 11, 39, and 285. 406 branches stay tip-only. `cursor/chess-engine-elo-8295` was tip-only and is now `run6-read`. `cursor/chess-engine-elo-6a55` is `run6-same-docs`: its changelog, release state, README, and 6.0–6.3 validation notes are the same blobs as `928f1ff7`.

No engine was built. One PGN was scored. Every Elo figure below is a sentence in the named file or commit message.

### Two 6.x histories

`cursor/chess-engine-elo-8295` is unchanged at `928f1ff7a10ad2d36d579b854bfa498768faba2f` (910 files). It contains `193a91ec`, `86c91628`, and `5c1cec8d`. It contains neither the lock commit, H512, `main`, nor `24cc2cce`. The merge base with `cursor/engine-strength-overhaul-66cc` is `68f01122`.

`VALIDATION.md` (`f22894fa`) and `engine-improvement-log.md` (`52a0ff13`) are the same blobs run 5 read. They were not read again. `CHANGELOG.md` and `RELEASE_STATE.md` differ. Eighty-four changelog sections, from `## 5.31.0` through `## 0.1.0`, are the same text on both tips. The title line is the same text as well. The release-state sections for 5.31.0 and 5.30.0 are the same text. Everything from 6.0.0 upward is a different document.

`928f1ff7` stops at 6.3.0, dated 2026-10-13. `24cc2cce` has its own 6.2.0 (2026-10-13), 6.3.0 (2026-10-14), and 6.4.0 (2026-10-14). The version numbers are not the same engines. `CHANGELOG.md`, `RELEASE_STATE.md`, and `README.md` at `5c1cec8` are the same blobs as at `928f1ff7`. The two commits after `5c1cec8` do not touch those files.

### What the 8295 notes claim, and which games are in the tree

Read in full on `928f1ff7`: `CHANGELOG.md` lines 1–198 (the 6.3.0 through 6.0.0 sections; the older sections match the overhaul text already read), `RELEASE_STATE.md` (151 lines), `validation/release-6.3.0/README.md`, `validation/release-6.2.0/README.md`, `validation/release-6.1.0/README.md`, `validation/release-6.1.0/stockfish-ladder.md`, and `validation/release-6.0.0/README.md`. `validation/release-6.3.0/`, `validation/release-6.2.0/`, and `validation/release-6.1.0/` contain those notes and no PGNs.

Their 6.3.0 table, 1,000 games at 25,000 nodes, no adjudication, says cutoff-count reductions +12.5 +/- 14.0, quiescence move-count pruning +12.5 +/- 15.1, deeper or shallower re-search +11.8 +/- 14.5, eleven new evaluation terms +9.0 +/- 14.5, a full refit on 688,237 positions +31.4 +/- 14.7, and a second refit +13.6 +/- 13.3. The time-control row is the first refit against 6.2.0 at 3+0.03: 133 / 86 / 81, +55 +/- 26, over 300 games. The second refit is described as adopted after that match. The same note says the error bars on the component rows are about +/- 14. Those rows were not recomputed. The games are not in the tree.

Their 6.2.0 table says quiet checks +7.6 +/- 14.3, history-aware futility +7.6 +/- 14.0, pawn-structure history for ordering +2.4 +/- 13.5, and the removed check extension +0.4 +/- 14.6. The final build against 6.1.0 at 3+0.03 is 108 / 93 / 99, +17 +/- 22, over 300 games. The same search before the check-aware generator is 105 / 112 / 83, -8 +/- 24. `Threads=2` versus `Threads=1` is 9 / 3 / 12 over 24 games, +89 +/- 69. No PGN.

Their 6.1.0 table says `Threads=2` versus `Threads=1` is 41 / 18 / 41, +81 +/- 40, over 100 games at 5+0.05. Single-thread against 6.0.0 at 3+0.03 is 100 / 98 / 102, +2 +/- 19, over 300 games. Capture futility is +11 +/- 14 over 1,000 adjudicated games at 25,000 nodes. Extended correction history is -2 +/- 14 at 25,000 nodes, +24 +/- 22 over 400 adjudicated games at 100,000 nodes, and +12 +/- 17 over 300 games at 100,000 nodes without adjudication. The note itself says the adjudicated result did not predict the time-control result. No PGN.

`stockfish-ladder.md` says Forge 6.0.0 scored 70.5% and Forge 6.1.0 scored 71.0% against Stockfish 19 at `UCI_Elo` 2800, 100 games each, and that `sf-610.pgn` and `sf-base.pgn` were left out of the repository. The overhaul changelog's 6.1.0, a different tree, says 75.0% over 200 games (134 / 34 / 32) against the same opponent setting. Run 5 counted that overhaul PGN. The two sentences are about two engines that share a version label. This run does not choose between them.

The overhaul 6.1.0 release state says, at `RELEASE_STATE.md:109`, that 6.1.0 adds `Threads`, and at line 120 that multi-threaded search was not done for that release. Line 93 ends with "the Zen 4 (`znver4`) builds were 4." Those are sentences in the document.

### The one PGN on this tip

`validation/release-6.0.0/` on `928f1ff7` has `README.md` and `forge-6.0.0-pretune2-vs-sf19-2800-10+0.1.pgn`. The PGN is blob `aa352b28249d2d49cff20ad359a565bcb91c4ebb`, the same blob as `forge-6.0.0-vs-sf19-2800-10+0.1.pgn` on `24cc2cce`. Counted here: 200 games, Forge side `v3`, 118 wins, 42 losses, 40 draws. The README calls that file the first tuned table, 69.0%. The hand-set row in the same README, 47 / 32 / 21 over 100 games, has no PGN on this tip. The README says "See the final rows below for the shipped parameter table" and the file ends at the tuning paragraph.

### Two commits the changelog does not mention

`ba4572e1` stores transposition depth plus one (`src/search.cpp:123`). Quiescence uses depth 0 when the node is in check or `depth >= 0`, and depth -1 otherwise (`src/search.cpp:677`). The commit message says +8.0 +/- 13.8 over 1,000 games at 25,000 nodes. There is no PGN and no changelog sentence.

`928f1ff7` caches each side's king shelter on the pawn-cache entry (`src/eval.cpp:194`). The commit message says the bench signature was unchanged and the speed was about 1%. There is no bench log in the commit.

### Source shapes that were not played

`MovePicker::next` writes `bad_captures_[bad_count_++]` with no capacity test (`src/search.cpp:202`). The array has 64 slots (`src/search.cpp:306`). This is the same shape run 5 recorded on the 6.4.0 tip at different line numbers. No overflow position was searched.

`read_int` parses clocks into an `int` and returns 0 unless the whole token converts (`src/uci.cpp:71`). `wtime` stores `max(0, that)` (`src/uci.cpp:97`). The default `time_ms` is -1 (`include/forge/search.hpp:22`), so a parsed 0 is a present clock (`src/search.cpp:1154`). With the default overhead of 10 ms (`include/forge/search.hpp:27`), `available` is `max(1, time - overhead)` (`src/search.cpp:1157`). A failed parse becomes a 1 ms budget. Node limits use `uint64_t` (`src/uci.cpp:85`). This binary was not run.

A checkmate in quiescence returns `mated_in(ply)` at `src/search.cpp:775` and does not reach the store at line 778. An empty main-search node returns at line 1079 and does not reach the store at line 1095. `Board::parse_uci` returns a move only when the token equals `move_to_uci` (`src/board.cpp:828`), and `move_to_uci` writes lowercase letters (`src/board.cpp:837`). This tip has no `UseNNUE` option. None of these were played.

`cursor/chess-engine-elo-d8c5` and `cursor/engine-elo-improvement-3c5f` stay tip-only. The validation notes that exist on those tips are the blobs named above. Their own `CHANGELOG.md` and `RELEASE_STATE.md` blobs differ from `928f1ff7` and were not opened.

### Not claimed

- No new Elo and no new bench. The pretune PGN confirms 118 / 42 / 40. It does not confirm an error bar. The 6.1, 6.2, and 6.3 tables have no games in this tree.
- 406 tips are still unread. `cursor/chess-engine-elo-bba2` was not opened.
- The KRK history miss was not replayed.
- Nothing was pushed to `main`, `lock/combo29-20261110`, `fable/standalone-h512-20261111`, or another agent's branch.
- Supermemory was unavailable. Adapter was not used.

## Next run

1. `git fetch` and `git ls-remote --heads origin`. Diff against `inventory/branches-current.tsv`. Append new rows to `inventory/HEAD_MOVEMENT.tsv`. Do not rewrite `inventory/branches.tsv` or earlier movement rows. This branch's tip will have moved by the commit that adds these files; record that as this checkpoint, then continue.
2. If a foreign tip moved, read that delta before the branch below.
3. Otherwise read `cursor/chess-engine-elo-bba2` at `2285d91270f53f37d4c7bfdf491ed490c7d0c1a1`. It is nine commits past `f96b7475` and is not an ancestor of `928f1ff7`. Do not execute repository scripts.
4. The changelogs at `193a91ec` and `86c91628` are different blobs from `928f1ff7`. Open them after the bba2 batch, before calling those tips read.
5. The KRK replay remains the first reproduction when a run investigates instead of opening the next pack. Position `4R3/8/8/k2K4/8/8/8/8 w - - 0 1` should play `d5c5`. Run it on H512 `efb2ff96`, then on `f6760ff6`, then on `49b80952`.
6. Do not push to `main`, the lock, the H512 branch, or another agent's branch.

## Run 7

Trigger 20:27 UTC on 2026-11-13. `git fetch origin --prune` and `git ls-remote --heads origin` at 20:34 UTC. The run-1 table `inventory/branches.tsv` is unchanged. The live list is `inventory/branches-current.tsv`. One movement row is appended in `inventory/HEAD_MOVEMENT.tsv`.

| Item | Value |
|---|---|
| Remote heads | 430. Local remote-tracking refs match `ls-remote`. |
| Same tip as the run-6 table | 429 |
| Moved | 1. This checkpoint, `d6e50b49` to `6cf670a6`, the run-6 commit. Not foreign work. |
| New | 0 |
| Gone | 0 |
| Unique tips | 341. One tip replaced another. `d6e50b49` is no longer a branch tip. |
| Unique tip trees | 341. The checkpoint tree `e6f2f33a` matches no other tip. |
| Shared-tip groups | still 16 groups, 105 branches |
| Tags | the same 3, not reviewed |
| Inaccessible heads | none in this fetch |

`refs/remotes/origin/HEAD` still points at `main`. Ancestry counts stay 17, 11, 39, and 285. `cursor/chess-engine-elo-bba2` was tip-only and is now `run7-read`. 405 branches stay tip-only.

No engine was built. No PGN was scored. Every Elo figure below is a sentence in the named file. The W/D/L columns were checked against the usual score-to-Elo transform. That checks the sentences against each other.

### Where this tip sits

`cursor/chess-engine-elo-bba2` is unchanged at `2285d91270f53f37d4c7bfdf491ed490c7d0c1a1` (892 files, tree `824d9962`). It contains neither the lock commit, H512, nor the current `main` tip. Its parent chain includes `f96b7475`, which is also an ancestor of `main`. `main` then adds nine files that are not on this branch. Those nine files were not opened.

The merge base with `928f1ff7` and with `24cc2cce` is `f96b7475`. This tip is nine commits later and is not an ancestor of either line. The first of those commits, `3293deb7`, extracts the 5.31.0 tree. The 6.x extraction `f5ba2c40` has the same tree except `.gitignore`: this line ignores `__pycache__/`, and the 6.x extraction deletes that line. `VALIDATION.md` (`f22894fa`) and `engine-improvement-log.md` (`52a0ff13`) are the blobs already read. They were not read again. `src/board.cpp` (`587169c3`) is the extraction blob. `parse_uci` and pawn-move order were read from it. The rest of that file was not.

The eight commits after the extraction change 11 files: `CHANGELOG.md`, `CMakeLists.txt`, `README.md`, `RELEASE_STATE.md`, `SOURCE_PROVENANCE.json`, `include/forge/board.hpp`, `include/forge/search.hpp`, `src/search.cpp`, `src/uci.cpp`, `tests/tests.cpp`, and `tools/uci_regression.py`. `src/uci.cpp` changes only the version string, from 5.31.0 to 6.0.0, at line 140.

### What the 6.0.0 notes claim

Read in full for the 6.0.0 material: `CHANGELOG.md` through the 6.0.0 section, `README.md`, `RELEASE_STATE.md` through the 6.0.0 section, `SOURCE_PROVENANCE.json`, and `LOCAL_IMPLEMENTATION_SUMMARY.md` (the 5.31.0 summary, unchanged from the extraction). The older changelog sections are the 5.31.0 document. They were not compared line by line with the overhaul copy in this run.

Their table, fastchess, Hash 32, `forge-10000.epd`, single thread, no adjudication, says:

| Step | Control | Games | W/D/L | Their Elo |
|---|---|---|---|---|
| Selective search vs 5.31.0 | 5+0.05 | 100 | 88/7/5 | +413 +/- 111 |
| Position-indexed TT and the repetition rule | 5+0.05 | 120 | 42/40/38 | +12 +/- 38 |
| PeSTO piece-square tables | 5+0.05 | 120 | 64/36/20 | +134 +/- 56 |
| Attack-unit king safety | 5+0.05 | 200 | 60/94/46 | +24 +/- 30 |
| Final 6.0.0 vs 5.31.0 | 10+0.1 | 100 | 84/9/7 | +355 +/- 92 |

The usual transform of those five W/D/L rows is 412.8, 11.6, 133.6, 24.4, and 354.5. The written Elo column matches that arithmetic. The error bars were not recomputed. The tip has two PGNs, `validation/5.29.0-ponder-evidence/ab-games.pgn` and `validation/5.30.0-empty-searchmoves/fastchess-aa-games.pgn`. Neither is a 6.0.0 match. `git grep` finds the five result rows only in `README.md`, `CHANGELOG.md`, and `RELEASE_STATE.md`. The three-second depth claim, depth 9 versus depth 19, is also only that README sentence. There is no bench log.

`README.md:5` says the evaluation function is unchanged. The table in the same file, and `src/search.cpp`, replace the center-distance terms with PeSTO tables and add king safety. `SOURCE_PROVENANCE.json:34` still says the evaluation has no king-attack term beyond pawn shelter. That file was last changed in `36d55208`, before the king-safety commit `aa2a9b4f`. The final commit `2285d912` updates the changelog, the README table, and the release state, and leaves both the provenance sentence and `README.md:5` in place.

### Search that is actually in the tree

`src/search.cpp` is the mailbox engine plus the selective search. Late-move reductions start at depth 3 (`src/search.cpp:842`) and a reduced search that beats alpha is searched again at full depth (`src/search.cpp:855`). The 5.23 through 5.31 zero-window fail-low fixtures were removed from `tests/tests.cpp`. This run did not compile the replacement tests, so those old failures are not shown to be gone.

Null-move pruning starts at depth 3. Below depth 10 it returns beta with no verification search (`src/search.cpp:772`). At depth 10 and above it runs the reduced verification (`src/search.cpp:777`). `tests/tests.cpp:701` searches the start position at depth 8 and `tests/tests.cpp:712` calls a positive null-cutoff count "verified cutoffs". A check extension sets the child depth to the parent depth, not above it (`src/search.cpp:836`), so a depth-8 root never enters the verification branch. The counter still increments at `src/search.cpp:773`. The test was not compiled.

Whole-node pruning, reverse futility and null move, is skipped when the side to move has only pawns (`src/search.cpp:183` and `src/search.cpp:753`). The test source checks that on `8/8/8/3k4/8/4K3/4P3/8 w - - 0 1`. Four mate fixtures are in `tests/tests.cpp:724`: `b3b8`, `d3d8`, `d1d8`, and `h5f7`, each required to score above 29000. They were not run.

The transposition table is indexed by `Board::key()` (`include/forge/search.hpp:164`). `current_tt_context` maps every halfmove clock below 90 to context 0 (`include/forge/search.hpp:106`). A node whose clock is already 100 returns before the probe (`src/search.cpp:714`). A mate stored at a low clock can still satisfy a probe at clock 89, and a mate longer than 11 plies reaches the fifty-move rule inside that window. The comment says the result depends on the clock only from 90 upward. Not played.

An empty main-search node returns mate or stalemate at `src/search.cpp:793` and does not reach the store at line 893. An in-check mate in quiescence returns at `src/search.cpp:651` and does not reach the store at line 698. When a score is stored, `normalized_score_for_tt` (`src/search.cpp:167`) does adjust mate scores by ply. Not played.

Quiet moves that failed low are recorded in a 256-slot array and the write is guarded (`src/search.cpp:811` and `src/search.cpp:888`). This tip does not have the unchecked 64-slot `bad_captures_` write recorded on `928f1ff7` and `24cc2cce`.

`Board::parse_uci` returns a move only when the token equals `move_to_uci` (`src/board.cpp:809`). `move_to_uci` writes lowercase letters (`src/board.cpp:817`). Not played. This tip has no `UseNNUE` option.

### Clock parser

`read_int` parses into an `int` and returns 0 unless the whole token converts (`src/uci.cpp:68`). `wtime` stores `max(0, that)` (`src/uci.cpp:94`). `movetime` does the same (`src/uci.cpp:89`). The default `time_ms` is -1 (`include/forge/search.hpp:21`), so a parsed 0 is a present clock (`src/search.cpp:931`). With the default overhead of 10 ms, `available` is `max(1, time - overhead)` (`src/search.cpp:937`). A token that does not fit in a 32-bit `int`, including `3000000000`, and a token with a leading `+`, which `std::from_chars` rejects, both become that 1 ms budget.

`tests/tests.cpp:853` expects a `SearchLimits` clock of 0 to be a 1 ms budget. `tests/tests.cpp:884` passes `INT_MAX` straight into `SearchLimits` and expects `1073741813`. That test does not go through the UCI parser. The arithmetic of the formula matches 1,073,741,813. The test was not compiled.

If the search stores no move, `src/search.cpp:1063` plays `legal_moves().front()`. `legal_moves` keeps `pseudo_legal_moves` order (`src/board.cpp:756`). Pieces are scanned from the lowest square. The a1 rook has no legal move at the start. The b1 knight is next, and its first offset is +17 (`src/board.cpp:41`), which is `b1c3`. A 1 ms search can still return a move it searched. This is not the lock's immediate `a2a3` on `wtime 3000000000`. This binary was not run.

### Not claimed

- No new Elo and no new bench. The five 6.0.0 rows are sentences. Their W/D/L and Elo columns agree arithmetically. The games are not in the tree.
- 405 tips are still unread. The changelogs at `193a91ec` and `86c91628` were not opened. Their blobs differ from `928f1ff7`: changelogs `ad5b9bcb` and `68ef6c76`, release states `f81ebd5f` and `7fd220fb`.
- The KRK history miss was not replayed.
- Nothing was pushed to `main`, `lock/combo29-20261110`, `fable/standalone-h512-20261111`, or another agent's branch.
- Supermemory was unavailable. Adapter was not used.

## Next run

1. `git fetch` and `git ls-remote --heads origin`. Diff against `inventory/branches-current.tsv`. Append new rows to `inventory/HEAD_MOVEMENT.tsv`. Do not rewrite `inventory/branches.tsv` or earlier movement rows. This branch's tip will have moved by the commit that adds these files; record that as this checkpoint, then continue.
2. If a foreign tip moved, read that delta before the documents below.
3. Otherwise read `CHANGELOG.md` and `RELEASE_STATE.md` at `193a91eca17c1b47372f408df67fd06ec08c8312` (`cursor/chess-engine-elo-d8c5`) and `86c916289f27225313e60388ca05fffc7e257f39` (`cursor/engine-elo-improvement-3c5f`). Those four blobs differ from `928f1ff7`. Validation notes that are the same blobs as `928f1ff7` were already read. Do not execute repository scripts.
4. The KRK replay remains the first reproduction when a run investigates instead of opening the next pack. Position `4R3/8/8/k2K4/8/8/8/8 w - - 0 1` should play `d5c5`. Run it on H512 `efb2ff96`, then on `f6760ff6`, then on `49b80952`.
5. Do not push to `main`, the lock, the H512 branch, or another agent's branch.

## Run 8

Trigger 21:27 UTC on 2026-11-13. `git fetch origin --prune` and `git ls-remote --heads origin` at 21:31 UTC. The run-1 table `inventory/branches.tsv` is unchanged. The live list is `inventory/branches-current.tsv`. One movement row is appended in `inventory/HEAD_MOVEMENT.tsv`.

| Item | Value |
|---|---|
| Remote heads | 430. Local remote-tracking refs match `ls-remote`. |
| Same tip as the run-7 table | 429 |
| Moved | 1. This checkpoint, `6cf670a6` to `0b5eff7f`, the run-7 commit. Not foreign work. |
| New | 0 |
| Gone | 0 |
| Unique tips | 341. One tip replaced another. `6cf670a6` is no longer a branch tip. |
| Unique tip trees | 341. The checkpoint tree `1a89bd59` matches no other tip. |
| Shared-tip groups | still 16 groups, 105 branches |
| Tags | the same 3, not reviewed |
| Inaccessible heads | none in this fetch |

`refs/remotes/origin/HEAD` still points at `main`. Ancestry counts stay 17, 11, 39, and 285. `cursor/chess-engine-elo-d8c5` and `cursor/engine-elo-improvement-3c5f` were tip-only and are now `run8-read`. 403 branches stay tip-only.

No engine was built. No PGN was scored. Every Elo figure below was already a sentence in the 6.3.0 copies of these files.

### The two documents are earlier copies

`cursor/chess-engine-elo-d8c5` is unchanged at `193a91eca17c1b47372f408df67fd06ec08c8312` (908 files). `cursor/engine-elo-improvement-3c5f` is unchanged at `86c916289f27225313e60388ca05fffc7e257f39` (909 files). The first is an ancestor of the second, and the second is an ancestor of `928f1ff7`. Neither contains the lock commit, H512, or `main`.

`CHANGELOG.md` blobs are `ad5b9bcb` and `68ef6c76`. They differ from `928f1ff7` (`b5b0df96`) because the later file has more sections, not because an old section was rewritten. All 86 sections on `193a91ec` equal the matching sections on `928f1ff7`. The later file adds `## 6.2.0 - 2026-10-12` and `## 6.3.0 - 2026-10-13`. All 87 sections on `86c91628` equal the matching sections. The later file adds only the 6.3.0 section.

`RELEASE_STATE.md` blobs are `f81ebd5f` and `7fd220fb`. `193a91ec` is the exact suffix of the `928f1ff7` file from the 6.1.0 heading. `86c91628` is the exact suffix from the 6.2.0 heading. The 5.31.0 and 5.30.0 sections are also the same text as `24cc2cce`. The 6.0.0 and 6.1.0 sections differ from `24cc2cce`. Run 6 already recorded that difference.

Eight hundred fifty-five validation files that exist on all three tips are identical blobs. `193a91ec` has no `validation/release-6.2.0/` and no `validation/release-6.3.0/`. `86c91628` has no `validation/release-6.3.0/`. The 6.0 and 6.1 notes, and the 6.2 note on the second tip, are the blobs run 6 read.

`README.md` on `193a91ec` (`0b4e9111`) lists four ladder rows: 5.31.0 is 1/17/2 over 20 games, the tuned 6.0.0 is 118/42/40 over 200 games, the same-machine 6.0.0 is 63/22/15 over 100 games, and one-thread 6.1.0 is 67/25/8 over 100 games. Those scores are 10.0%, 69.0%, 70.5%, and 71.0%. The 200-game PGN was counted on `928f1ff7`. The two 100-game PGNs are still absent. `README.md` on `86c91628` (`2d1eabe6`) adds the changelog's +17 +/- 22 sentence for 6.2.0 against 6.1.0 and does not add a game file.

### Two sentences that disagree with the tree

`RELEASE_STATE.md:20` on `86c91628` starts the sentence that says single-thread bench signatures are unchanged by the threading and generation changes; the clause is line 21. The same sentence is `RELEASE_STATE.md:47` on `928f1ff7`, with the clause on line 48. Three of the generation and threading commits say the signature stayed put: `7dda4a96` at 1188868, `40b54a70` at 1188868, and `b84ed559` at 1390079. `d2b85db5` says the check-aware generator changes the bench 13 signature to 1234322, because the picker's selection swaps break ties once illegal evasions are absent from the list. The same message says 42,513 in-check positions kept the same legal-move lists and that perft was unchanged. `CHANGELOG.md:36` says the generation order is unchanged, and line 37 says the legal moves come out in the same sequence. `CHANGELOG.md:44` states the final signature 1,234,322. There is no bench log in the tree. This run did not run `bench`.

`CHANGELOG.md:16` on `193a91ec` says `Board` maintains the piece-class Zobrist keys in `put_piece`, `remove_piece`, and `move_piece`, and that `unmake_move` restores them without undo state. The next sentences, at line 22, say the keys are updated in `make_move` registers and restored from `Undo`. The 6.1.0 section is the same text on `86c91628` and on `928f1ff7`. In `src/board.cpp` at `193a91ec`, `put_piece` (`:99`), `remove_piece` (`:106`), and `move_piece` (`:114`) do not touch those keys. `make_move` saves them at `:659`, writes the deltas at `:723`, and `unmake_move` copies the saved values back at `:772`.

### The same defect shapes, at these lines

`bad_captures_[bad_count_++]` has no capacity test. On `193a91ec` the write is `src/search.cpp:199` and the array has 64 slots at `:287`. On `86c91628` the write is `src/search.cpp:201` and the array has 64 slots at `:305`. `MoveList::Capacity` is 256 at `include/forge/board.hpp:51` on both tips. No overflow position was searched.

`read_int` parses clocks into an `int` and returns 0 unless the whole token converts (`src/uci.cpp:71` and `:76` on both tips). `wtime` stores `max(0, that)` at `src/uci.cpp:97`. `src/uci.cpp` differs across `193a91ec`, `86c91628`, and `928f1ff7` only by the version string. The default `time_ms` is -1 (`include/forge/search.hpp:22`) and the default overhead is 10 ms (`include/forge/search.hpp:27`), so a parsed 0 is a 1 ms budget: `src/search.cpp:1018` on `193a91ec` and `src/search.cpp:1134` on `86c91628`. This is the same budget already described on `928f1ff7`. It is not the lock's immediate `a2a3`. These binaries were not run.

A checkmate in quiescence returns before the store: `src/search.cpp:664` before `:667` on `193a91ec`, and `:762` before `:765` on `86c91628`. An empty main-search node returns before the store: `:958` before `:974`, and `:1056` before `:1072`. `Board::parse_uci` returns a move only when the token equals `move_to_uci` (`src/board.cpp:810` and `:831`). `move_to_uci` writes lowercase letters (`src/board.cpp:817` and `:838`). Neither tip has a `UseNNUE` option. None of these were played.

### Not claimed

- No new Elo and no new bench. The 6.1.0 and 6.2.0 tables are the sentences already recorded from `928f1ff7`. The ladder percents match the W/D/L arithmetic. The games that were missing there are missing here.
- 403 tips are still unread. The 29 branches at `356e863d` were not opened.
- The KRK history miss was not replayed.
- Nothing was pushed to `main`, `lock/combo29-20261110`, `fable/standalone-h512-20261111`, or another agent's branch.
- Supermemory was unavailable. Adapter was not used.

## Next run

1. `git fetch` and `git ls-remote --heads origin`. Diff against `inventory/branches-current.tsv`. Append new rows to `inventory/HEAD_MOVEMENT.tsv`. Do not rewrite `inventory/branches.tsv` or earlier movement rows. This branch's tip will have moved by the commit that adds these files; record that as this checkpoint, then continue.
2. If a foreign tip moved, read that delta before the files below.
3. Otherwise read the clock evidence on the shared tip `356e863dbd86d2ce24b8ee9486d7406f1d525480`. Twenty-nine branches name that one commit, including `research/forge-forfeit-clock-gap-20261020-2120`. The tip commit edits `validation/hourly/2026-10-20-go-origin-native/CI_ATTEMPT_2.md` and `run_native_validation.sh`. Read `tools/audit/extreme_clock.cpp`, `validation/hourly/2026-10-20-go-origin-native/native_clock_probe.py`, `uci-clock-origin-scoped.patch`, and `validation/hourly/2026-10-20-go-origin/uci-clock-origin.patch` as data. Do not execute repository scripts.
4. The KRK replay remains the first reproduction when a run investigates instead of opening the next pack. Position `4R3/8/8/k2K4/8/8/8/8 w - - 0 1` should play `d5c5`. Run it on H512 `efb2ff96`, then on `f6760ff6`, then on `49b80952`.
5. Do not push to `main`, the lock, the H512 branch, or another agent's branch.

## Run 9

Trigger 22:26 UTC on 2026-11-13. `git fetch origin --prune` and `git ls-remote --heads origin` at 22:31 UTC. The run-1 table `inventory/branches.tsv` is unchanged. The live list is `inventory/branches-current.tsv`. One movement row is appended in `inventory/HEAD_MOVEMENT.tsv`.

| Item | Value |
|---|---|
| Remote heads | 430. Local remote-tracking refs match `ls-remote`. |
| Same tip as the run-8 table | 429 |
| Moved | 1. This checkpoint, `0b5eff7f` to `db4613f1`, the run-8 commit. Not foreign work. |
| New | 0 |
| Gone | 0 |
| Unique tips | 341. One tip replaced another. `0b5eff7f` is no longer a branch tip. |
| Unique tip trees | 341. The checkpoint tree `d0e43a6a` matches no other tip. |
| Shared-tip groups | still 16 groups, 105 branches |
| Tags | the same 3, not reviewed |
| Inaccessible heads | none in this fetch |

`refs/remotes/origin/HEAD` still points at `main`. Ancestry counts stay 17, 11, 39, and 285. The 29 branches at `356e863d` were tip-only and are now `run9-read` for the clock files named below. 374 branches stay tip-only.

No engine was built. No script in the tree was executed. No PGN was scored. The timing figures below are sentences and one stored model stdout. They are not a new measurement.

### One tree, twenty-nine names

`356e863dbd86d2ce24b8ee9486d7406f1d525480` (tree `41f7a4cb`, 1068 files, 2026-10-20 09:04 +02:00) is the whole shared group. It contains `24cc2cce` and does not contain the lock, H512, or `main`. The commit itself changes two files: `validation/hourly/2026-10-20-go-origin-native/CI_ATTEMPT_2.md` and `run_native_validation.sh`. The subject is a CI baseline pin, "Fix Forge 6.4 native CI to compare pinned pre-fix commit."

These names all point at that commit. None of them is a separate experiment:

`forge/candidate-ownbook-native-20261020-0945`, `forge/candidate-terminal-zero-nodes-20261020-1445`, `forge/candidate-terminal-zero-nodes-20261020-1545`, `forge/candidate-terminal-zero-nodes-20261020-1645`, `forge/research-20261020-0915`, `forge/research-20261020-1015`, `forge/research-20261020-1115`, `forge/research-20261020-1215`, `forge/research-20261020-1315`, `forge/test-20261020-0930`, `forge/test-20261020-1030`, `forge/test-20261020-1130`, `forge/test-20261020-1230`, `forge/test-20261020-1330`, `forge/test-20261020-1430`, `forge/test-20261020-1530`, `forge/test-20261020-1630`, `forge/test-20261020-1830`, `forge/test-20261020-1930`, `forge/test-20261020-2030`, `investigator/hourly-20261020-1000`, `investigator/hourly-20261020-1100`, `investigator/hourly-20261020-1500-dedup`, `investigator/null-rule50-20261020-1200`, `investigator/ownbook-native-confirmation-20261020-1800`, `research/forge-forfeit-clock-gap-20261020-2120`, `research/forge-terminal-zero-node-native-20261020-1519`, `research/forge-tt-abort-audit-20261020-1433`, `research/forge64-ownbook-integration-20261020-1908`.

### What the clock change is

Parent `294cf1ba` ("Fix Forge 6.4 timed UCI go dispatch clock origin") is the integration. Its parent is the pinned pre-fix commit `06c581895708a6eb9ff26b380d818f72f7bd9ebf`. The blobs named in the cycle-7 note match that parent: `include/forge/search.hpp` `f3f96e4b`, `src/search.cpp` `ca5b3541`, `src/uci.cpp` `9bf1b757`.

On this tip, `go` records `go_received` before `stop_search()` (`src/uci.cpp:288`). A finite clock or movetime, with infinite and ponder both clear, copies that timestamp into `limits.start_time` (`src/uci.cpp:325`). `Worker::search` uses it when it is set and otherwise uses `steady_clock::now()` (`src/search.cpp:1112`). `SearchLimits::start_time` is a default time point (`include/forge/search.hpp:31`). `<chrono>` is already included at `include/forge/search.hpp:9`.

`go depth`, `go nodes`, `go infinite`, and `go ponder` leave `start_time` unset. `elapsed_ms` while pondering returns 0 until `ponder_hit_ns` is set, and then measures from that hit (`src/search.cpp:561`). That rebase was read. It was not played.

Depth and node limits still use `uint64_t` (`src/uci.cpp:86`). Clocks still use `read_int` into an `int` (`src/uci.cpp:73`). A token that does not convert, including `3000000000` and a leading `+`, returns 0 (`src/uci.cpp:78`). `wtime` stores `max(0, that)` (`src/uci.cpp:99`). A parsed 0 is a present clock. With the default overhead of 10 ms, `available` is `max(1, time - overhead)` (`src/search.cpp:1141`). These are the same lines already recorded on `24cc2cce`. This binary was not run. `movestogo` uses the same parser and then `max(1, read_int())` (`src/uci.cpp:95`), so a failed movestogo token becomes 1. That case was not played.

`bad_captures_[bad_count_++]` is still unchecked at `src/search.cpp:296`. The array is 64 slots at `src/search.cpp:384`. No overflow position was searched.

### Patches, probe, and the unfinished driver

`validation/hourly/2026-10-20-go-origin/uci-clock-origin.patch` sets `limits.start_time = go_received` for every non-perft `go`. `validation/hourly/2026-10-20-go-origin-native/uci-clock-origin-scoped.patch` sets it only for a finite clock or movetime. The integrated condition matches the scoped patch. The comment text in `294cf1ba` does not match either stored patch. In a throwaway checkout of `06c58189`, `git apply --check` accepted both patches. On a throwaway checkout of this tip, both patches failed at `include/forge/search.hpp:25`, `src/search.cpp:1109`, and `src/uci.cpp:285`. That matches `CI_ATTEMPT_2.md`: workflow `39383195419` stopped in `git apply -R` before compilation. The tip's driver now archives `06c58189` and `HEAD` instead of reversing a patch (`run_native_validation.sh:25` and `:35`). The workflow file `.github/workflows/forge64-clock-origin.yml` runs that driver only for pushes to `forge/6.4-hourly-20261019`. `CI_ATTEMPT_2.md` says the new driver had not been seen to pass. This run did not download either Actions artifact.

`native_clock_probe.py` compares two binaries under `delayed_pthread_create.c`. The shim sleeps inside `pthread_create` when `FORGE_TEST_CREATE_DELAY_MS` is 1..1000. The probe's default delay is 440 ms. It sends `go movetime 1200` to the baseline and the candidate, then `go depth 1` to the candidate, and it turns OwnBook off first. Pass requires the baseline's first `info time` to be under half the delay, the candidate's timed `info time` to be at least delay-minus-60, and the depth-1 `info time` to be under half the delay. The script's own docstring says this is UCI elapsed accounting, not Elo. It was not run.

`INTEGRATION_REPORT.md` quotes an earlier success, workflow `39382802396`, GCC 13.3.0, CTest 4/4 on both trees, and these UCI lines under a 440 ms admission delay: pre-fix `go movetime 1200` info time 0 ms, wall 1630.492 ms, `d2d4`; scoped fix info time 440 ms, wall 1190.489 ms, `e2e4`; scoped `go depth 1` info time 0 ms, wall 440.890 ms, `e2e3`. The journals are not in this commit. The note says the move change comes from a different time budget. It claims no Elo. The same file says the first TT-tag match stopped at 6 games, 3 pairs, and 1 candidate timeout, with no H0/H1 result.

`validation/hourly/2026-10-20-go-origin/REPORT.md` describes a standalone sleep model, not Forge. `time_origin_model.cpp` sleeps 440 ms, then samples a worker-local clock and a go-receipt clock against a hard budget of 351 ms. `model-test.stdout` contains `budget_ms=351 old_elapsed_ms=0 go_origin_elapsed_ms=440` and the PASS line. That file was not regenerated. The native-directory `REPORT.md` describes a three-mode fixture (`native_probe_fixture.cpp`) whose journals are also absent: unpatched `info time` 12 ms, scoped timed 452 ms, scoped depth 1 at 12 ms, and the unscoped depth path at 452 ms. The fixture prints `bestmove e2e4` after a 12 ms sleep. It is not Forge. `CI_ATTEMPT_1.md` says workflow `39382382647` compiled and passed CTest 4/4 on both trees, then the probe failed because the embedded book returned `bestmove c2c4` before any `info depth` line.

### OwnBook and the extreme-clock probe

At this tip a game search still probes the book when `own_book` is true or `book_file` is non-empty (`src/uci.cpp:331`). `OwnBook false` clears only `own_book` (`src/uci.cpp:229`). `Book File` still loads that file (`src/uci.cpp:242`). The following commit, `af194137`, which is not this tip, drops the `book_file` clause. It was not played here.

`tools/audit/extreme_clock.cpp` assigns `depth = 1` and `numeric_limits<int>::max()` to `time_ms` and `increment_ms` on a `SearchLimits` object. It does not send UCI text, so it does not reach `read_int`. `tools/audit/README.md:16` says an untouched 5.6.0 build trips UBSan on this probe and that the 5.7.0 fix and the candidate pass. There is no log of that run in the files opened here. The probe was not compiled. The same README says `go infinite` on `7k/6Q1/6K1/8/8/8/8/8 b - - 100 1` returns `bestmove 0000` after a 64-depth loop. That sentence was not replayed.

### Not claimed

- No new Elo and no new bench. The 1630 ms and 1190 ms walls are the integration note's figures. The journals are not in the tree, and the later driver run is described as unfinished.
- 374 branches are still tip-only. The 12 branches at `5101c252` were not opened. That tip is two commits later: `af194137` and the OwnBook test.
- The KRK history miss was not replayed.
- Nothing was pushed to `main`, `lock/combo29-20261110`, `fable/standalone-h512-20261111`, or another agent's branch.
- Supermemory was unavailable. Adapter was not used.

## Next run

1. `git fetch` and `git ls-remote --heads origin`. Diff against `inventory/branches-current.tsv`. Append new rows to `inventory/HEAD_MOVEMENT.tsv`. Do not rewrite `inventory/branches.tsv` or earlier movement rows. This branch's tip will have moved by the commit that adds these files; record that as this checkpoint, then continue.
2. If a foreign tip moved, read that delta before the files below.
3. Otherwise read the shared tip `5101c2529d386b7c3a04ba9156a69ee34df6bb43` (12 branches, one tree). It is `af194137` plus `5101c252`. `af194137` changes `src/uci.cpp:331` so a game search probes the book only when `own_book` is true. `5101c252` adds `validation/hourly/2026-10-20-ownbook-native/test_ownbook.py`. Read that test as data. Do not execute repository scripts.
4. The KRK replay remains the first reproduction when a run investigates instead of opening the next pack. Position `4R3/8/8/k2K4/8/8/8/8 w - - 0 1` should play `d5c5`. Run it on H512 `efb2ff96`, then on `f6760ff6`, then on `49b80952`.
5. Do not push to `main`, the lock, the H512 branch, or another agent's branch.

## Run 10 — 2026-11-13 23:23 UTC

Trigger 23:23 UTC on 2026-11-13. `git fetch origin --prune` and `git ls-remote --heads origin` at 23:24 UTC. The run-1 table `inventory/branches.tsv` is unchanged. The live list is `inventory/branches-current.tsv`. One movement row is appended in `inventory/HEAD_MOVEMENT.tsv`.

| Item | Value |
|---|---|
| Remote heads | 430. Local remote-tracking refs match `ls-remote`. |
| Same tip as the run-9 table | 429 |
| Moved | 1. This checkpoint, `db4613f1` to `1d458a9a`, the run-9 commit. Not foreign work. |
| New | 0 |
| Gone | 0 |
| Unique tips | 341. One tip replaced another. `db4613f1` is no longer a branch tip. |
| Unique tip trees | 341. The checkpoint tree `a6791b6c` matches no other tip. |
| Shared-tip groups | still 16 groups, 105 branches |
| Tags | the same 3, not reviewed |
| Inaccessible heads | none in this fetch |

`refs/remotes/origin/HEAD` still points at `main`. Ancestry counts stay 17, 11, 39, and 285. The 12 branches at `5101c252` were tip-only and are now `run10-read`. The two branches at `af194137` are `run10-fix-line`. `research/forge-ownbook-native-verify-20261020-1706` is `run10-workflow`. 359 branches stay tip-only.

No engine was built. No script in the tree was executed. No PGN was scored. The Polyglot key check below is a calculation from the key table and the function in `src/book.cpp`. It is not a UCI transcript.

### One tree, twelve names

`5101c2529d386b7c3a04ba9156a69ee34df6bb43` (tree `58d0596f`, 1069 files, 2026-10-20 12:51 +02:00) is the whole shared group. It contains `24cc2cce` and `356e863d`. It contains neither the lock, H512, nor `main`. Its parent is `af194137`. That parent’s parent is `356e863d`.

These names all point at `5101c252`. None of them is a separate experiment:

`forge/6.4-hourly-20261019`, `forge/candidate-ownbook-native-ci-20261020-1245`, `forge/lead-ownbook-native-20261020-1345`, `forge/test-20261021-0030`, `forge/test-20261021-0230`, `forge/test-20261021-0330`, `forge/test-20261021-0430`, `investigator/hourly-20261021-1000-no-new-finding`, `investigator/hourly-20261021-1100-qsearch-candidate-native`, `investigator/hourly-20261021-1200-terminal-zero-nodes-native`, `research/forge24-paired-speed-calibration-20261021`, `tester/forge64-20261022-1230-budget-matrix`.

### The book gate

`af194137` changes one line of `src/uci.cpp`. Blob `debb80cb` becomes `cc5efeb3`. `5101c252` has that same blob. A game search is a clock or movetime search with infinite, ponder, searchmoves, and mate all clear (`src/uci.cpp:329`). The probe at `src/uci.cpp:331` requires `own_book`. On `356e863d` the same site also probed when `book_file` was non-empty. On `24cc2cce` that older condition is `src/uci.cpp:325`.

`OwnBook false` writes only `own_book` (`src/uci.cpp:229`). A non-empty `Book File` still loads the path and replaces the entry table (`src/uci.cpp:242`, `src/book.cpp:100`). An empty path clears `book_file` and reloads the embedded book (`src/uci.cpp:239`). After the change, a loaded external file stays in memory while `OwnBook` is false, and a game search does not call `book.probe`. Setting `OwnBook true` again probes that loaded file. This binary was not run.

`Book::probe` with variety 0 returns the heaviest legal candidate (`src/book.cpp:164`). One entry of weight 100 is that candidate. `Book::size` is the entry count (`include/forge/book.hpp:34`).

The two names at `af194137` have this gate and do not have the test file: `forge/candidate-ownbook-20261020-1045` and `forge/candidate-ownbook-native-20261020-1145`.

### The regression file

`5101c252` adds only `validation/hourly/2026-10-20-ownbook-native/test_ownbook.py`. The file builds a 16-byte Polyglot record: key `0x463B96181691FC9C`, move `(12 << 6) | 28`, weight 100, learn 0. A separate calculation of `polyglot_key` for the standard start position, using this tree’s `Random64` table and the formula at `src/book.cpp:38`, produced that key. The move word is 796 (`0x031c`), which is e2e4 under `encode_squares` at `src/book.cpp:31`.

The script looks for `id name Chess Engine Forge`. The book path contains spaces. `setoption` keeps the first value token and the rest of the line (`src/uci.cpp:200`, `src/uci.cpp:237`), so the loaded path includes those spaces. It then checks:

- `go movetime 150` with `OwnBook false`: a book info line is required when `--expect-leak yes`, and forbidden when `--expect-leak no`.
- `OwnBook true`, then `go movetime 150`: a book info line and `bestmove e2e4`.
- `go depth 2`: no book info line. Depth leaves `time_ms` and `movetime_ms` at -1 (`include/forge/search.hpp:22`), so `game_search` is false.
- `OwnBook false` again, with the same expectation as the first movetime search.

A book hit is any line that starts with `info string book move `. The disabled case does not require a different move, so a search that plays e2e4 without that line still passes. The leak case does not require e2e4. The script appends five checks before it records PASS. No `result.json` and no `raw_uci.log` are in the commit. The script was not executed.

### Documents that still describe the old gate

`validation/hourly/2026-10-19-initial/forge-state-nnue-audit.md:22` quotes `src/uci.cpp:325` as `(own_book || !book_file.empty())`. That citation matches `24cc2cce`. On this tip, line 325 assigns `limits.start_time`, and the book condition is line 331. The audit says the protocol reproduction was not executed. `af194137` and `5101c252` do not edit that file. `validation/hourly/README.md:138` still lists reproducing the bypass as an open item. Neither file is a measurement of this tip.

The 6.2.0 changelog row, 18 wins, 11 losses, 91 draws at 10+0.1, is the older embedded-book on/off match already stored in this tree. It is not a result for `af194137`.

### The workflow one commit later

`research/forge-ownbook-native-verify-20261020-1706` at `9a6598bc718bfc144b2499277b7affc89a152e10` is the only branch there. It is `5101c252` plus `.github/workflows/forge-ownbook-independent.yml` (56 lines). The workflow builds `356e863d` and `5101c252` with `FORGE_NATIVE=OFF`, runs ctest on each, then runs the script with `--expect-leak yes` on the older binary and `--expect-leak no` on the newer one. `set -euo pipefail` is on, and each Python command is piped to `tee`, so a non-zero script status fails the step before the decision line. That line says both 4-test suites passed. The script’s own list has five checks. Logs go to the runner temp directory and an uploaded artifact. None of those logs are in the commit. This run did not start the workflow. The file claims no Elo.

### Clock and captures

`src/search.cpp` is blob `d48e9f16`, the same blob as on `356e863d`. `read_int` is still `src/uci.cpp:73`. A token that does not convert returns 0 (`src/uci.cpp:78`). `wtime` stores `max(0, that)` (`src/uci.cpp:99`). A parsed 0, with the default overhead of 10 ms, becomes a 1 ms budget (`src/search.cpp:1141`). `bad_captures_[bad_count_++]` is still unchecked at `src/search.cpp:296`. The array has 64 slots at `src/search.cpp:384`. These lines were not played.

### Not claimed

- No new Elo and no new bench. The book edit is a configuration gate. The regression file and the workflow are source. They are not a stored pass.
- 359 branches are still tip-only. The next shared tip is `9108d012` (11 names), whose parent is `24cc2cce`.
- The KRK history miss was not replayed.
- Nothing was pushed to `main`, `lock/combo29-20261110`, `fable/standalone-h512-20261111`, or another agent’s branch.
- Supermemory was unavailable. Adapter was not used.

## Next run

1. `git fetch` and `git ls-remote --heads origin`. Diff against `inventory/branches-current.tsv`. Append new rows to `inventory/HEAD_MOVEMENT.tsv`. Do not rewrite `inventory/branches.tsv` or earlier movement rows. This branch’s tip will have moved by the commit that adds these files; record that as this checkpoint, then continue.
2. If a foreign tip moved, read that delta before the files below.
3. Otherwise read the shared tip `9108d012526be80c6d163f7cab684e6acd9abf8d` (11 branches, one tree). Its parent is `24cc2cce`. The commit changes `include/forge/search.hpp`, `src/search.cpp`, and `tests/tests.cpp`, and adds `tools/audit/audit_match_archive.py` plus `validation/hourly/2026-10-19-initial/`. Read the source diff, `candidate.patch`, `forge-tt-review.md`, `forge-search-audit.md`, and `forge-match-evidence.md`. Check a cited W/L/D against the PGN or stats file it names. Do not execute repository scripts.
4. The KRK replay remains the first reproduction when a run investigates instead of opening the next pack. Position `4R3/8/8/k2K4/8/8/8/8 w - - 0 1` should play `d5c5`. Run it on H512 `efb2ff96`, then on `f6760ff6`, then on `49b80952`.
5. Do not push to `main`, the lock, the H512 branch, or another agent’s branch.

## Run 11 — 2026-11-14 00:24 UTC

Trigger 00:24 UTC on 2026-11-14. `git fetch origin --prune` and `git ls-remote --heads origin`, rechecked at 00:28 UTC. The run-1 table `inventory/branches.tsv` is unchanged. The live list is `inventory/branches-current.tsv`. One movement row is appended in `inventory/HEAD_MOVEMENT.tsv`.

| Item | Value |
|---|---|
| Remote heads | 430. Local remote-tracking refs match `ls-remote`. |
| Same tip as the run-10 table | 429 |
| Moved | 1. This checkpoint, `1d458a9a` to `12819522`, the run-10 commit. Not foreign work. |
| New | 0 |
| Gone | 0 |
| Unique tips | 341. One tip replaced another. `1d458a9a` is no longer a branch tip. |
| Unique tip trees | 341. The checkpoint tree `133c75f2` matches no other tip. |
| Shared-tip groups | still 16 groups, 105 branches |
| Tags | the same 3, not reviewed |
| Inaccessible heads | none in this fetch |

`refs/remotes/origin/HEAD` still points at `main`. Ancestry counts stay 17, 11, 39, and 285. The 11 branches at `9108d012` were tip-only and are now `run11-read`. 348 branches stay tip-only.

No engine was built. No script in the tree was executed. Three named PGNs were scored from `Result` tags. The cluster-index table was recalculated from the key formula. The regression binary was not run.

### One tree, eleven names

`9108d012526be80c6d163f7cab684e6acd9abf8d` (tree `9f03c88a`, 982 files, 2026-10-19 15:22 +02:00) is the whole shared group. Its parent is `24cc2cce3eda0e12ddfa4036cd25f7d50e8a3b0b`. It contains that parent. It contains neither the lock, H512, nor `main`. `356e863d`, `af194137`, and `5101c252` contain this commit. `cursor/engine-strength-overhaul-66cc` is still `24cc2cce` and does not.

These names all point at `9108d012`. None of them is a separate experiment:

`forge/audit-perft-uci-responsiveness-20261019-2300`, `forge/audit-rule50-tt-bypass-20261019-2100`, `forge/audit-tt-exact-layout-20261019-2000`, `forge/candidate-lazy-checks-20261019-1745`, `forge/candidate-lazy-movepicker-20261019-1945`, `forge/research-20261019-1815`, `forge/research-20261019-1915`, `forge/research-20261019-2015`, `forge/test-20261019-1730`, `forge/test-20261019-2030`, `forge/test-20261019-2230`.

### The tag and the index

`candidate.patch` is the three-file source diff. Its SHA-256 is `954a804ba8ba624c2823dafa9d303dc29c618722bd8e38bc49d7a1b1709eeb39`, the digest named in `forge-tt-review.md`. A current `git diff` of the same three paths differs only in the length of the index abbrev.

On `24cc2cce`, `cluster_for` is `include/forge/search.hpp:106`. Multiply-high indexing is `(key * cluster_count) >> 64`. The modulo fallback is `key % cluster_count`. `probe` and `store` both keep `key >> 32` (`src/search.cpp:197` and `:218`). `TTCluster` is 64 bytes: four 16-byte `TTEntry` values, `alignas(64)` at `include/forge/search.hpp:76`. One MiB is 16,384 clusters. Thirty-two MiB is 2^19 clusters, so the old 32-bit tag repeats the top 19 index bits and has 13 bits left. Sixty-four MiB leaves 12. Hash is 1 to 2048 MiB at `src/uci.cpp:164`, which is at most 2^25 clusters.

This commit adds `verification_key` at `include/forge/search.hpp:106`. The multiply-high path returns the low 32 bits. The modulo path still returns `key >> 32`. `probe` and `store` both call it (`src/search.cpp:197`, `:218`). The low 32 bits and a top-25 index do not overlap. The helper adds no field to `TTEntry`.

`tests/tests.cpp:484` clears the table, stores four keys, and expects four distinct scores, at 1 MiB and at 3 MiB. Group one shares the high half `0x12345678` and uses low halves 1 through 4. Group two shares the low half `0x9abcdef0` and steps the high half by `3 << 60`. That step is divisible by 16,384 and by 49,152. Recalculated multiply-high and modulo indices:

| Size | Group | Multiply-high | Modulo |
|---|---|---|---|
| 1 MiB / 16,384 | high half shared | 1165, 1165, 1165, 1165 | 1, 2, 3, 4 |
| 1 MiB / 16,384 | low half shared | 1165, 4237, 7309, 10381 | 7920, 7920, 7920, 7920 |
| 3 MiB / 49,152 | high half shared | 3495, 3495, 3495, 3495 | 1, 2, 3, 4 |
| 3 MiB / 49,152 | low half shared | 3495, 12711, 21927, 31143 | 7920, 7920, 7920, 7920 |

Those are the four rows in `forge-tt-review.md`. On the old multiply-high tag, group one shares a cluster and a tag. The last three inserts hit, and the first three reads return the last score: six failures per table size, twelve across the two sizes. Group two uses different high halves, so it does not add failures on that path.

`baseline-new-regression.log` lists three "distinguishes keys" lines, three "retain their own scores" lines, and the same six lines again, then `12 test failure(s)`. The exit file is `1`. `baseline-ctest.log` records 4/4 pass on the parent tests. `candidate-ctest.log` records 4/4 pass with the new test included. `modulo-verification-method.txt` says a disposable copy replaced the two `__SIZEOF_INT128__` guards with `#if 0`, and `modulo-ctest.log` records 4/4 pass. That copy is not in the commit. `fallback-build.log` ends in a libstdc++ `charconv` error for `__int128` after `-U__SIZEOF_INT128__`, and `fallback-status.json` records build exit 2. None of these binaries were rebuilt here.

Both `baseline-bench11.log` and `candidate-bench11.log` print `nodes 417491`. The times are one sample each, 654 ms and 836 ms. That is the same node signature and not a speed result. `validation/hourly/STATE.json` sets `candidate_status` to `correctness_verified_strength_pending` and `strength.decision` to `pending`.

### Sanitizer logs disagree with each other

`sanitizer-ctest.log` starts with `LeakSanitizer has encountered a fatal error` and ends at 1 of 4 tests passed. `forge_tests`, `uci_regression`, and `ponder_regression` fail when the engine process exits 1. `sanitizer-status.json` records ctest exit 8 and does not mention a retry. `sanitizer-ctest-no-lsan.log` records 4/4 pass. `sanitizer-environment.json` sets `ASAN_OPTIONS` to `detect_leaks=0` and records `ctest_exit` 0. `STATE.json` says the address and undefined-behavior run passed and that LeakSanitizer was unavailable. `additional-validation-status.json` records `asan_ubsan_exit` 0. The passing sentence is the second log. The first log is a LeakSanitizer abort under the sandbox restriction named in the environment file. This run did not rerun either ctest and did not identify an engine leak from these files.

### Match counts that were checked

`validation/release-6.0.0/all-match-pgns.zip` is blob `c8eb1422`, 67,169,642 bytes. Its SHA-256 is `acbd91b4a7f7829092eede5472e2c40de1e34f33e469f6b2927c61b58ad27960`, the same digest as `forge-match-raw-stats.json`. The json says 44 PGNs and 76,047 games. This run did not recount the archive. It scored three PGNs the evidence note names. Every header `Result` matched the final movetext result. No Elo was recomputed.

`validation/release-6.0.0/forge-6.4.0-vs-sf19-3000-20+0.2.pgn` is blob `d2ba8f9e`, SHA-256 `076d1f5f6d8e44da96b0ae211944188c18f75cf48255ecbe47db20c4cd39f855`. From `v64`: 35 wins, 30 losses, 35 draws, 100 games, time control `20+0.2`, termination `normal` on all 100. Fifty rounds, each a color swap, opening names agree inside each round. Pair scores 0, 0.5, 1, 1.5, 2 are 5, 8, 18, 15, 4. The json row for `v64` is the same count and the same histogram. White and Black engine-name tags are Stockfish 19 and Chess Engine Forge 6.4.0. The player tags are `SF19-3000` and `v64`. The note's +17 +/- 53 figure was not recomputed. 52.5 points per 100 games is the win/draw/loss arithmetic.

`pgns/dev-residual-nnue-128-vs-6.3.0-10+0.1.pgn` at `f481fc5a` is blob `b03d55a9`, SHA-256 `85cf152a44ae4963e4ed008cd392ea5e481e071401ffc96e3be0fdf86d8e9559`. From `res128`: 49 wins, 23 losses, 128 draws, 200 games, `10+0.1`, all `normal`. One hundred color-swapped rounds, opening names agree. The histogram is 0, 12, 57, 24, 7. Both engine-name tags say Chess Engine Forge 6.3.0. The json row matches. 56.5 points per 100 games is the arithmetic. The note's +45 +/- 26 figure was not recomputed.

`pgns/dev-residual-nnue-128-vs-6.3.0-20k.pgn` at the same commit: 209 wins, 88 losses, 203 draws, 500 games. Terminations are 170 `normal` and 330 `adjudication`. The json row matches. 62.1 points per 100 games is the arithmetic. The note's +86 +/- 24 figure was not recomputed. Adjudication is 330 of these 500 games.

The eight-game file added by this commit, `validation/hourly/2026-10-19-initial/matches/aa/games.pgn`, scores 4 wins, 0 draws, 4 losses for `Candidate`. Four color-swapped rounds each score 1. Rounds 1 and 2 are `0-1` both colors. Rounds 3 and 4 are `1-0` both colors. `stats.json` has the same 4/0/4, pentanomial `[0, 0, 4, 0, 0]`, and `elo_claim` null. Both engine-name tags say Chess Engine Forge 6.4.0. `fastchess.log` is empty. The console's last block says `Draws: 0` and, on the line above, `DrawRatio: 100.00 %`. The PGN has no draw. The games do not separate the candidate from the baseline. This is not an Elo result. The bench signature above is the same 417491 on both logs.

### Other source lines read, not played

`read_int` is `src/uci.cpp:73`. A token that does not convert returns 0 (`src/uci.cpp:78`). `wtime` stores `max(0, that)` (`src/uci.cpp:99`). The default overhead is 10 ms (`include/forge/search.hpp:28`). A parsed 0 becomes available time `max(1, 0 - 10)` at `src/search.cpp:1139`, so the budget is 1 ms. `bad_captures_[bad_count_++]` is unchecked at `src/search.cpp:296`. The array has 64 slots at `src/search.cpp:384`. A game search still probes the book when `own_book` is false and `book_file` is non-empty (`src/uci.cpp:325`). The later gate that requires `own_book` is `af194137`, already read on `5101c252`.

`Board::compute_key` (`src/board.cpp:896`) mixes pieces, castling, en passant, and side. It does not mix `halfmove_`. Quiescence returns a TT score with no halfmove test (`src/search.cpp:692`). The main-search cutoff requires `halfmove_clock() < 90` (`src/search.cpp:813`). Both paths can replace static eval with a TT score (`src/search.cpp:708`, `:830`). `forge-search-audit.md` describes a clock-99 position for this. That position was not searched here.

Root nodes are added to `root_move_nodes_[move_count - 1]` (`src/search.cpp:1048`). The array is cleared once at `src/search.cpp:1239`. The best-move ordinal is stored at `src/search.cpp:1059` and read for the soft-time factor at `src/search.cpp:1303`. Check masks are built in every `MovePicker` constructor (`src/search.cpp:266`) and read from quiet generation (`src/search.cpp:449`, `:466`). `material_key` recomputes ten popcounts at `src/search.cpp:504`. These are the audit's source notes. No timing and no match was run for them.

`TTEntry` fields are ordinary members (`include/forge/search.hpp:60`). The class comment at `include/forge/search.hpp:80` says a torn entry is caught by the key and by move legality. The tag patch does not add atomics.

### Not claimed

- No new Elo and no new bench. The identical 417491 lines are stored logs. The 654 ms and 836 ms samples are not a speed comparison. `STATE.json` still says strength is pending.
- The twelve-failure log matches the collision count. It is their log. This run did not link the new test against `24cc2cce`.
- `cursor/engine-strength-overhaul-66cc` still stores `key >> 32` for both index backends. The repair is on this tip and on the later hourly tips that contain it.
- 348 branches are still tip-only. The TT-tag SPRT text starts at `91885905`, which is not a branch tip. The next branch tip on that line is `374a71d4` (`forge/review-pgn-nps-signal-20261020-0010`). The recorded outcome files are the unique diff of shared tip `2fc649ef` (9 names).
- The KRK history miss was not replayed.
- Nothing was pushed to `main`, `lock/combo29-20261110`, `fable/standalone-h512-20261111`, or another agent's branch.
- Supermemory was unavailable. Adapter was not used.

## Run 12 — 2026-11-14 01:23 UTC

Trigger 01:23 UTC on 2026-11-14. `git fetch origin --prune` and `git ls-remote --heads origin`, rechecked at 01:27 UTC. The run-1 table `inventory/branches.tsv` is unchanged. The live list is `inventory/branches-current.tsv`. One movement row is appended in `inventory/HEAD_MOVEMENT.tsv`.

| Item | Value |
|---|---|
| Remote heads | 430. Local remote-tracking refs match `ls-remote`. |
| Same tip as the run-11 table | 429 |
| Moved | 1. This checkpoint, `12819522` to `da310bf1`, the run-11 commit. Not foreign work. |
| New | 0 |
| Gone | 0 |
| Unique tips | 341. One tip replaced another. `12819522` is no longer a branch tip. |
| Unique tip trees | 341. The checkpoint tree `49e83e35` matches no other tip. |
| Shared-tip groups | still 16 groups, 105 branches |
| Tags | the same 3, not reviewed |
| Inaccessible heads | none in this fetch |

`refs/remotes/origin/HEAD` still points at `main`. Ancestry counts stay 17, 11, 39, and 285. The nine branches at `2fc649ef` and `forge/review-pgn-nps-signal-20261020-0010` were tip-only and are now `run12-read`. 338 branches stay tip-only.

No engine was built. No script in the tree was executed. The 45 `.b64` parts were not decoded. Four cited win/loss/draw counts were scored from PGN `Result` tags.

### Three commits, ten names

`918859057a433d58e6b7fecd62f83861665f05f2` (tree `92bb5e89`, 1013 files, 2026-10-20 00:00 +02:00) is not a branch tip. Its parent is `9108d012`. It adds the SPRT protocol, `tools/match/run_hourly_sprt.py`, and the first STATE change.

`374a71d44ea0a2d28ac26b196ced57c34ddfdcd8` (tree `1aa627cc`, 1045 files, 2026-10-20 00:05 +02:00) is the only tip of `forge/review-pgn-nps-signal-20261020-0010`. It records the first attempt as failed and adds the cold-replay protocol.

`2fc649effb6d2f09f4fdf63b44d59283fe26b616` (tree `66d93948`, 1048 files, 2026-10-20 00:22 +02:00) is the next commit and the whole shared group of nine names. It adds `validation/hourly/2026-10-19-initial/REPORT.md`. These three commits contain neither the lock, H512, nor `main`. `src/search.cpp` blob `ca5b3541` and `src/uci.cpp` blob `9bf1b757` are the same bytes as on `9108d012`.

These names all point at `2fc649ef`:

`forge/audit-20261020-0102-ci-preservation`, `forge/candidate-uci-perft-interrupt-20261020-0045`, `forge/integrator-ownbook-ci-20261020-0245`, `forge/research-20261020-0115`, `forge/research-20261020-0315`, `forge/test-20261020-0130`, `forge/test-20261020-0330`, `forge/timeout-journal-20261019-1625`, `forge/timeout-warm-replay-20261020-0034`.

`forge/research-20261020-0015` at `72bf672e` also contains `374a71d4`, then eight later notes. Those eight files were not read. `3cabc1b2` is another child of this line and is 1368 files. It is not a branch tip, and it was not opened.

### Protocol, driver, and STATE

`protocol.json` SHA-256 is `7cc725dddece0cb1b1db04f9644c98c2420072aeda3b2ced6e0bef0837c3b885`, matching `protocol.sha256` and the STATE field. `tools/match/run_hourly_sprt.py` SHA-256 is `7829a8699941f79dce60e0f001d6c9b8f3a86592c284ceade67e80585303edc5`, matching `driver_sha256`. The script says a tranche is not interrupted to manufacture a checkpoint, and a non-zero fastchess exit is stored as `failed_no_resume`. The script was not executed. `hourly-sprt-driver-review-tests.json` records status pass, `check_count` 22, `strength_games_launched` 0, and the same driver digest. That review script was not run here.

`tools/openings/forge-10000.epd` is 10000 lines. Its SHA-256 is `de36a48f856a5a0c10d0865747965a7b2f5d89149078923ba2d766979238bf6c`, the protocol's opening-source hash. The selected-order hash was not recomputed.

`strength.decision` is `pending` at `9108d012`, `prepared_not_started` at `91885905`, and `failed_no_resume_timeout_diagnosis` at `374a71d4`. The `374a71d4` note says the runner exited 1, one Candidate timeout, after 54.27 seconds, with no Elo claim. At `2fc649ef`, `candidate_status` is `correctness_verified_strength_blocked` and `strength.decision` is `failed_no_resume_timeout_unresolved`. That object says 6 completed games, 3 completed pairs, and `counts_usable_for_strength` false. The `recovery` object is unchanged and still says `strength_games_started` false.

`validation/hourly/2026-10-19-initial/matches/tt-tag-sprt/tranche-00100-result.json` is not in this tree. `git log --all` shows no commit that adds it. `tt-tag-first-attempt-evidence.zip` is also absent. STATE names that zip as 871904 bytes, SHA-256 `a46354a38c4866a748aca459e794be33a934957e8e1c1f041a99d85c73b9533e`, 43 members, and says publication is blocked. The 45 encoded parts under `validation/hourly/encoded-artifacts/` were not decoded. The six-game count is a sentence in STATE and in REPORT. This run did not score those six games.

### Initial clock limits, not a played search

The cold-replay position starts from a white-to-move FEN and then gives 49 moves, so Black is to move. The command is `go wtime 401 btime 596 winc 100 binc 100`.

`src/search.cpp:50-53` sets `TmSoftDivisor` 22, `TmIncrementPercent` 75, `TmHardPercent` 60, and `TmHardSoftMultiple` 5. Overhead is 10 at `include/forge/search.hpp:28`. With no `movestogo`, `src/search.cpp:1139-1148` gives available `max(1, 596-10) = 586`, soft `586/22 + 75 = 101`, and hard `min(351, 505) = 351`. The protocol's derived budgets are 586, 101, and 351. Those are the initial limits. `src/search.cpp:1314` can stop on the soft limit times a factor. The stable, semi-stable, unstable, and minimum factors are 60, 80, 140, and 45 (`src/search.cpp:54-59`). The hard stop at `src/search.cpp:590` compares elapsed time with `hard_limit_ms_` and does not apply that factor.

REPORT says the runner returned after about 1404 ms and that an explicit stop then produced `c5e3` in 1.581 ms. That trace is not in the commit. This run did not play the position. The ten cold-trial sentences (both binaries `e7e4`, depth 11, 98549 nodes) were read. `diagnostic-evidence-integrity.md` gives trial 6 as 3442 bytes, original SHA-256 `f54678999550fcc9bd286a62954d790ec20c3900d0663970891dd5ac5566774a`, available SHA-256 `036a75d3630b1781afd94db6f30dc0ed04f2f4ae6b18eedac87ed9ebeb81b2bb`. Those trial files are not plaintext in the tree, so the digests were not recomputed.

### Match counts that were checked

`validation/release-6.0.0/all-match-pgns.zip` is blob `c8eb1422`, SHA-256 `acbd91b4a7f7829092eede5472e2c40de1e34f33e469f6b2927c61b58ad27960`, the digest in `forge-match-raw-stats.json`. The zip has 45 members: 44 PGNs and the directory entry `pgns/`. Counting `[Result "` across the 44 PGNs gives 76047, matching `games` in the json. In the files scored below, every header `Result` matched the movetext result.

`validation/release-6.0.0/forge-6.4.0-vs-sf19-3000-20+0.2.pgn` is the same bytes as zip member `pgns/forge-6.4.0-vs-sf19-3000-20+0.2.pgn`, SHA-256 `076d1f5f6d8e44da96b0ae211944188c18f75cf48255ecbe47db20c4cd39f855`. From `v64`: 35 wins, 30 losses, 35 draws, 100 games, time control `20+0.2`, termination `normal`. Engine names are Stockfish 19 and Chess Engine Forge 6.4.0. `(35 + 17.5) / 100 = 52.5`, the table's score. The note's Elo figure was not recomputed.

The two residual PGNs are inside the zip. They are the same bytes as on `f481fc5a`, and `f481fc5a` is not an ancestor of this tip. `pgns/dev-residual-nnue-128-vs-6.3.0-10+0.1.pgn`, SHA-256 `85cf152a44ae4963e4ed008cd392ea5e481e071401ffc96e3be0fdf86d8e9559`: `res128` 49 wins, 23 losses, 128 draws, 200 games, `10+0.1`, all `normal`. `(49 + 64) / 200 = 56.5`. `pgns/dev-residual-nnue-128-vs-6.3.0-20k.pgn`, SHA-256 `5f277d26c1ed4e51003bbf94452047973e1574d501a9f1fb475cff826ee286a2`: `res128` 209 wins, 88 losses, 203 draws, 500 games, `TimeControl` `-`, terminations 170 `normal` and 330 `adjudication`. `(209 + 101.5) / 500 = 62.1`. The +45 and +86 figures were not recomputed.

The ten loose PGNs under `validation/release-6.0.0/` have 1170 `Result` tags. Nine name Stockfish 19 on one side and sum to 1120 games, which is the REPORT's aggregate. The other file, `forge-6.1.0-threads4-vs-threads1-8+0.08.pgn`, is 50 games of `threads4` against `threads1`. Both engine-name tags say Chess Engine Forge 6.0.0 on every game. `forge-6.2.0pre-vs-sf19-3000-10+0.1.pgn` is one of the nine Stockfish matches, 200 games, and its Forge engine-name tags say Chess Engine Forge 6.1.0.

`validation/hourly/2026-10-19-initial/matches/aa/games.pgn` is still blob `c2de1f31`. `Candidate` is 4 wins, 0 draws, 4 losses, 8 games, all `normal`. `stats.json` and `matches/resume-aa/verification.json` record the same 4/0/4, pentanomial `[0, 0, 4, 0, 0]`, and `elo_claim` null. That is the fixed-node A/A recovery bookkeeping.

### Source bytes that did not change

The integer clock parser, the 1 ms budget for a failed parse, the unchecked 64-slot `bad_captures_` write, and the book probe when `own_book` is false and `book_file` is non-empty are the same `search.cpp` and `uci.cpp` blobs recorded on `9108d012`. The SPRT protocol sets `OwnBook` false and `external_book` null. This run did not start the engine.

### Not claimed

- No new Elo. The committed text has no H0 or H1 acceptance for the TT-tag repair. Six games are a STATE sentence, and their PGN is not in git.
- The 101 ms and 351 ms figures match the initial limit formula. They are not a timed search from this run. The reported 1404 ms return was not replayed.
- The 22-check review JSON was read. The review script was not executed.
- 338 branches are still tip-only. The next unread commit on the timeout line is `d2d8dfe4` (7 names, three files). `investigator/tt-smp-publication-20261020-0300` is `50149f78`, four commits and 32 added lines past `2fc649ef`. `forge/research-20261020-0015` is `72bf672e`, eight unread notes past `374a71d4`.
- The KRK history miss was not replayed.
- Nothing was pushed to `main`, `lock/combo29-20261110`, `fable/standalone-h512-20261111`, or another agent's branch.
- Supermemory was unavailable. Adapter was not used.

## Run 13 — 2026-11-14 02:26 UTC

Trigger 02:26 UTC on 2026-11-14. `git ls-remote --heads origin` at the start of the run, rechecked with the same 430 heads before writing. The run-1 table `inventory/branches.tsv` is unchanged. The live list is `inventory/branches-current.tsv`. One movement row is appended in `inventory/HEAD_MOVEMENT.tsv`.

| Item | Value |
|---|---|
| Remote heads | 430. |
| Same tip as the run-12 table | 429 |
| Moved | 1. This checkpoint, `da310bf1` to `095e8120`, the run-12 commit. Not foreign work. |
| New | 0 |
| Gone | 0 |
| Unique tips | 341. One tip replaced another. `da310bf1` is no longer a branch tip. |
| Unique tip trees | 341. The checkpoint tree `ece0ace1` matches no other tip. |
| Shared-tip groups | still 16 groups, 105 branches |
| Tags | the same 3, not reviewed |
| Inaccessible heads | none in this fetch |

`refs/remotes/origin/HEAD` still points at `main`. Ancestry counts stay 17, 11, 39, and 285. Twenty-two branches that were tip-only are now `run13-read`. 316 branches stay tip-only.

No engine was built. No patch was applied. No script in the tree was executed. The deadline and hard-budget evidence zips are not in git. Six same-binary timing ratios were recomputed from a stored JSON file. No Elo was measured.

### Deadline diagnostic, seven names

`d2d8dfe4fe9df20697f993bf44dea0f65e57ba39` (tree `b2068219`, 1051 files, 2026-10-20 03:40 +02:00) is one commit past `2fc649ef`. It adds 129 lines in three files and contains neither the lock, H512, nor `main`. `src/search.cpp` blob `ca5b3541` and `src/uci.cpp` blob `9bf1b757` are the same bytes as on `2fc649ef` and `9108d012`.

These names all point at `d2d8dfe4`:

`forge/candidate-ownbook-optout-20261020-0445`, `forge/candidate-tt-smp-snapshot-20261020-0345`, `forge/research-20261020-0415`, `forge/test-20261020-0430`, `forge/test-20261020-0530`, `investigator/hourly-20261020-0500-node-budget-audit`, `investigator/hourly-source-audit-20261020-0400`.

`validation/hourly/2026-10-20-deadline/REPORT.md` says the TT-tag strength attempt is still failed and not resumable: six games, three pairs, one Candidate timeout, and no SPRT decision. That repeats the STATE sentence already recorded on `2fc649ef`. The report says a separate Python diagnostic started its timeout at dequeue, judged delivery by dequeue time, and could treat an exited child with an undrained stdout pipe as a missing bestmove. The two patches change `warm_timeout_probe.py` and its test. They do not change engine source. The report says the old diagnostic produced two errors and one failed assertion, then 11/11 synthetic tests and 8/8 mocked trials passed. The zip it names, SHA-256 `c82add3a7589d53cf323417688d6ec47aab771be2aa5241e442d2c6fb4c3d986`, appears only as that sentence. `git log -S` finds the digest in this commit and in no added zip. Those pass counts were not rerun here.

### Hard-budget classification, ten names

`87a319fdcd028ae7058036735b7e75adebfaaa84` (tree `44a96fb2`, 1054 files, 2026-10-20 05:37 +02:00) is one commit past `d2d8dfe4`. It adds `validation/hourly/2026-10-20-hard-budget/REPORT.md`, `hard_limit.patch`, and `test_and_fixture.patch`, 111 lines. The same two engine blobs are unchanged. It contains neither the lock, H512, nor `main`.

These names all point at `87a319fd`:

`forge/candidate-ownbook-optout-20261020-0545`, `forge/candidate-ownbook-optout-20261020-0645`, `forge/candidate-ownbook-optout-20261020-0745`, `forge/research-20261020-0615`, `forge/research-20261020-0715`, `forge/test-20261020-0630`, `investigator/ownbook-off-external-20261020-0700`, `investigator/tt-rule50-qsearch-20261020-0600`, `research/forge-nnue-independent-audit-20261020-0710`, `research/grokchess-tt-trylock-20261020-0605`.

The frozen command is `go wtime 401 btime 596 winc 100 binc 100` with Move Overhead 10, Black to move. `src/search.cpp:50-53` sets `TmSoftDivisor` 22, `TmIncrementPercent` 75, `TmHardPercent` 60, and `TmHardSoftMultiple` 5. Integer arithmetic from `src/search.cpp:1139-1151` gives available `max(1, 596-10) = 586`, soft `586/22 + 75 = 101`, and hard `min(351, 505) = 351`. The patch's `HARD_LIMIT_MS` expression is that same arithmetic and asserts 351. The 2-second value is the diagnostic `deadline` argument, which the patch default still shows as `2.0`. A bestmove at 650 ms is inside that watchdog and outside 351 ms. The report says 14/14 unit tests passed, 8/8 ordinary synthetic trials stayed clean, and 4/4 deliberately delayed 650 ms trials were marked as hard-budget overruns. Zip SHA-256 `1e5fdb8d0cc1bc1d21f8e3aa53f0e851f5912c81a6d7274e0eb773e4d795d3e3` is only that sentence. The patches were not applied and the tests were not run. The report itself says a wall-clock overrun leaves engine, scheduler, and stdout buffering open. `src/search.cpp:590` compares `elapsed_ms()` with `hard_limit_ms_` and does not apply the soft factor. `src/search.cpp:674` and `:779` call `should_stop` every 1024 nodes unless a node limit is set. That poll gap is in the source. This commit does not measure it.

### Same-binary NNUE calibration, recomputed

`430329cec4576de5746a65970c6cd34bbabe3266` (tree `db9d60d3`, 1049 files, 2026-10-20 00:34 +02:00) is the only tip of `forge/test-20261020-0030`. It adds `validation/hourly/2026-10-20-0030/TESTER-STATUS.md`, 37 lines, on parent `2fc649ef`. The engine blobs are unchanged.

The note points at `results/nnue-performance-39334266771-1` `hosted-nnue-performance-results/performance/report.json` and at the protocol on `forge/hosted-nnue-performance-20261019-2220`. The protocol names experiment `forge-6.4.10-fused-nnue-update-vs-6.4.9-hosted-linux`, baseline `4edda780c68a742f20565d4e6a54a0c99a2c88a6`, candidate `36f5b2f6e1ff519e82a4b52edc85caceaf15aed0`. Gates are each ratio in `[0.97, 1.03]` and each median in `[0.99, 1.01]`.

The report's six A/A pairs are twelve processes, and every command is `frozen/artifacts/baseline/forge`. Dividing each pair's A seconds by its B seconds reproduces the stored ratios exactly.

| Pair | CPU A/B | Wall A/B |
|---|---|---|
| 1 | 0.9779746970333036 | 0.9772402859698365 |
| 2 | 1.0142985934967326 | 1.0135423649340312 |
| 3 | 1.0329386002802807 | 1.0337375655593846 |
| 4 | 1.00967519727259 | 1.0079057757275274 |
| 5 | 0.9780256772981446 | 0.9795777539748349 |
| 6 | 1.0472249068040853 | 1.0484324974942478 |

CPU median `1.0119868953846614`. Wall median `1.0107240703307792`. Pairs 3 and 6 are above 1.03 on both metrics. Both medians are above 1.01. `status` is `failed_primary_calibration_no_ab`. `qualifies_hosted_speed_claim` is false. `primary.ab_status` and `kernel.status` are both `skipped_failed_primary_calibration`. The stored rehash records expected and actual SHA-256 equal for baseline `forge` (`82a385d5504733bf355dfad1ece2266c7889ef33229454e45c1f0cee4f0d2260`) and candidate `forge` (`1946bfd9c59f88582d018eda2fc74bda0025c4bd700791cb1fd1b7303c0aa9e4`). This run did not hash the executable bytes. `frozen/correctness.json` records `bench_nodes_each` 419798, `full_ctest_both_passed` true, and `both_snapshot_streams_byte_identical` true. That bench was not rerun. It is a different signature from the hourly 417491 logs. There is no candidate-versus-baseline speed result and no Elo.

### TT publication order, one name

`50149f788fda75eff8d2882fe104e5232ad9903a` (tree `15f69741`, 1052 files, 2026-10-20 03:06 +02:00) is the only tip of `investigator/tt-smp-publication-20261020-0300`. Four commits past `2fc649ef` add 32 lines. The engine blobs are unchanged.

`TranspositionTable::store` writes `key32`, then `score`, then `eval`, then `depth`, then `gen_bound` (`src/search.cpp:222-226`). `probe` accepts an entry when `key32` matches and `occupied()` is true (`src/search.cpp:199`). `occupied()` is `gen_bound & 3`. The comment at `include/forge/search.hpp:80-81` says a torn entry is caught by the key check and by move legality. On a slot that is already occupied, the old bound stays non-zero until the last assignment, so a reader can observe the new key together with the previous score. Move legality does not check that score. An empty slot stays unoccupied until `gen_bound` is written, so the key-first order does not by itself publish an empty slot.

`investigations/tt_smp_20261020/tt_publication_minimal.cpp` forces that interleaving with a handshake and asserts the false hit. `raw_minimal.txt` says `PASS: wrong-key score accepted`. The toy was not compiled here. `CHECKPOINT.md` says the engine was not run and asks for ThreadSanitizer. No such log is in the commit.

### Research notes whose citations were checked

`52085b2775ca58e71a6629f952b326cda184620a` (tree `a9f7effe`, 1049 files) is the only tip of `forge/research-20261020-0215`. `72bf672e8adbbfd72871fcf0f74926b34ddacf6b` (tree `4e1b461f`, 1053 files) is the only tip of `forge/research-20261020-0015` and adds eight two-line notes past `374a71d4`. `761ae645cf1db4979b78357a6bd27752aafa0084` (tree `ed81071b`, 1052 files) is the only tip of `forge/research-20261020-0515` and adds one 18-line note past `d2d8dfe4`. None of these three changes the engine blobs. None contains the lock, H512, or `main`.

Quiescence returns a TT score with no halfmove test at `src/search.cpp:692-695`. The main-search cutoff requires `halfmove_clock() < 90` at `src/search.cpp:813-816`. Both paths can replace static eval with a TT score at `src/search.cpp:708-711` and `:830-833`. `TTEntry` (`include/forge/search.hpp:60-74`) has no halfmove field. The 02:15 note says this is eligibility, and that no mis-searched position was shown. No position was searched here.

`MovePicker`'s constructor fills `check_squares_` at `src/search.cpp:266-275` for every mode, including capture-only quiescence. `direct_check` is used by `generate_quiets` (`src/search.cpp:449`) and `generate_evasions` (`src/search.cpp:466`). The quiescence capture loop at `src/search.cpp:336-346` does not call it. That is a real per-node cost in the source. No timing was measured.

`src/nnue.cpp` on this blob `6b1f40ad` is 176 lines. `update` is `src/nnue.cpp:95-109`. `dirty_pieces` is `src/nnue.cpp:155-174`. The 02:15 note cites `src/nnue.cpp:57-111` and `:169-193`. Those numbers do not locate the functions, and line 193 does not exist. The hosted calibration above is the failed same-binary gate for the 6.4.10-versus-6.4.9 experiment. It supplies no accepted speed gain.

`Worker::should_stop` returns before the node-limit test when the caller is not the main thread (`src/search.cpp:586-587`). The node publish is inside `should_stop` (`src/search.cpp:584`). Quiescence and main search call it every 1024 nodes (`src/search.cpp:674`, `:779`) unless `node_limit_specified_` is set, and that flag is main-only (`src/search.cpp:1125`). Helpers are launched at `src/search.cpp:1363-1365` and joined after `stop` is set at `src/search.cpp:1367-1371`. The file ends at line 1375. The 05:15 note's range `1365-1395` extends past the file. The overshoot hypothesis was not measured.

Root nodes are added to `root_move_nodes_[move_count - 1]` at `src/search.cpp:1048`. The best-move ordinal is stored at `src/search.cpp:1059`. The array is cleared once at `src/search.cpp:1239`, before the depth loop. The soft-time factor reads that ordinal at `src/search.cpp:1303-1306`. The ordinal is the current iteration's move order, so a slot is not a stable move identity across depths. The 05:15 note's 1355-versus-601 bucket is a citation of another STATUS. That figure is not in this commit and was not recomputed.

`tests/tests.cpp:484-514` is `test_transposition_tag_independence`. `main` calls it at `tests/tests.cpp:525`. The 00:15 note's range `484-523` includes the test and the start of `main`.

The integer clock parser is still `src/uci.cpp:73-78`. A failed conversion returns 0, and `wtime` stores `max(0, that)` at `src/uci.cpp:99`. The default overhead is 10. A parsed 0 becomes a 1 ms budget at `src/search.cpp:1139`. `bad_captures_[bad_count_++]` is unchecked at `src/search.cpp:296`. The array has 64 slots at `src/search.cpp:384`. A game search still probes the book when `own_book` is false and `book_file` is non-empty (`src/uci.cpp:325`). These lines were read again because the cited ranges overlap them. They were not played.

### Not claimed

- No new Elo. The TT-tag SPRT remains the unresolved six-game STATE sentence. The deadline and hard-budget pass counts were not rerun, and their zips are absent.
- The 101 ms and 351 ms figures match the source formula. They are not a timed search from this run. A 650 ms bestmove was not produced here.
- The NNUE result is a failed same-binary calibration. It is not a candidate speedup and not an Elo result. Bench 419798 was not rerun.
- The TT store order is a source fact. The toy's PASS line is their stored stdout. Forge was not run under ThreadSanitizer.
- The unused quiescence check masks, the 1024-node helper publish, and the ordinal root buckets are source facts. None has a measurement in these commits.
- 316 branches are still tip-only. `3cabc1b2` is still unread. It is not a branch tip.
- The KRK history miss was not replayed.
- Nothing was pushed to `main`, `lock/combo29-20261110`, `fable/standalone-h512-20261111`, or another agent's branch.
- Supermemory was unavailable. Adapter was not used.

## Next run

1. `git fetch` and `git ls-remote --heads origin`. Diff against `inventory/branches-current.tsv`. Append new rows to `inventory/HEAD_MOVEMENT.tsv`. Do not rewrite `inventory/branches.tsv` or earlier movement rows. This branch's tip will have moved by the commit that adds these files; record that as this checkpoint, then continue.
2. If a foreign tip moved, read that delta before the files below.
3. Otherwise read `7e3fa78a1e756e3ad9cb36e328d3d4bfa0e3ca79`. It is not a branch tip. It adds one 8-line handoff past `87a319fd`. Then read tip `ec013151745b524a7f7095b834ff97f75fecad2c` (`forge/test-20261020-0830`). It adds `validation/hourly/2026-10-20-go-origin/REPORT.md`, `model-test.stdout`, `time_origin_model.cpp`, and `uci-clock-origin.patch`. Read them as data. Do not apply the patch, compile the model, or execute repository scripts.
4. Leave `3cabc1b2` unread. It is not a branch tip, and the diff from `2fc649ef` is 1368 files. Do not decode the `.b64` artifact parts.
5. The KRK replay remains the first reproduction when a run investigates instead of opening the next pack. Position `4R3/8/8/k2K4/8/8/8/8 w - - 0 1` should play `d5c5`. Run it on H512 `efb2ff96`, then on `f6760ff6`, then on `49b80952`.
6. Do not push to `main`, the lock, the H512 branch, or another agent's branch.

## Run 14 — 2026-11-14 03:25 UTC

Trigger 03:25 UTC on 2026-11-14. `git ls-remote --heads origin` listed 430 heads. A second read of the same listing, saved before writing, still had 430. The run-1 table `inventory/branches.tsv` is unchanged. The live list is `inventory/branches-current.tsv`. One movement row is appended in `inventory/HEAD_MOVEMENT.tsv`.

| Item | Value |
|---|---|
| Remote heads | 430. |
| Same tip as the run-13 table | 429 |
| Moved | 1. This checkpoint, `095e8120` to `47608fb7`, the run-13 commit. Not foreign work. |
| New | 0 |
| Gone | 0 |
| Unique tips | 341. One tip replaced another. `095e8120` is no longer a branch tip. |
| Unique tip trees | 341. The checkpoint tree `214fd197` matches no other tip. |
| Shared-tip groups | still 16 groups, 105 branches |
| Tags | the same 3, not reviewed |
| Inaccessible heads | none in this fetch |

`refs/remotes/origin/HEAD` still points at `main`. Ancestry counts stay 17, 11, 39, and 285. Three branches that were tip-only are now `run14-read`. 313 branches stay tip-only.

No engine was built. No patch was applied. No model was compiled. No script in the tree was executed. No Elo was measured.

### 07:30 tester handoff, one name

`7e3fa78a1e756e3ad9cb36e328d3d4bfa0e3ca79` (tree `e5a4ccec`, 1055 files, 2026-10-20 07:33 +02:00) is not a branch tip. It is the parent of `forge/test-20261020-0730`. It adds `validation/hourly/2026-10-20-0730/HANDOFF.txt`, eight lines, on parent `87a319fd`. `src/search.cpp` blob `ca5b3541`, `src/uci.cpp` blob `9bf1b757`, and `src/book.cpp` blob `5f79f022` are unchanged. The commit contains neither the lock, H512, nor `main`.

`a9f14bab5beb1e8d0e6ae21cc835a3afa66776c9` (tree `7b40ff89`, 1056 files, 2026-10-20 07:34 +02:00) is the only tip of `forge/test-20261020-0730`. It adds `validation/hourly/2026-10-20-0730/PROVENANCE.md`, eleven lines. The same engine blobs are unchanged.

The handoff says archived 6.4.4 and 6.4.7 passed 54/54 standalone UCI checks, OwnBook=false matched 6/6 opening and version groups on moves, scores, and nodes, and rule50 clocks 98 and 99 matched 12/12 cold/warm comparisons at a zero-centipawn score. It also says this cycle ran no candidate sanitizer, CTest, or fastchess match, that strength is inconclusive, and that the candidate is blocked. `git grep` finds `54/54` only in that handoff. There is no PGN, no stdout, and no executable in the two added files.

The provenance names the development head `87a319fd` and the three engine blobs above. Those three blobs match. It names checkpoint zip SHA-256 `47b63b4fb58cdc0d1e416b5c478dbb46615008c9f4c93edb87088f99b9e64c1f` and says that zip is not on GitHub. `git log -S` finds that digest only in `7e3fa78a` and `a9f14bab`. Neither tree adds a file of that digest. The same note names Actions run `39332822379` and evidence zip SHA-256 `1dc3d43767bc95251acdf2ec363e4e79b8a00e15d16b1fbd3202ec644b9a5600`. That digest string also occurs in commits this run did not open. The zip bytes were not read here.

The named 6.4.4 source is `816423b1ddac23a00244449deef59dba736055a9`. `src/uci.cpp:163` on that commit prints `Chess Engine Forge 6.4.4 candidate`. The subject is the isolated rule50 TT score-context candidate. The named 6.4.7 source is `2c0c7efa49023d8e3f49de3f5596f333a3f01202`. `src/uci.cpp:163` there prints `Chess Engine Forge 6.4.7 candidate`. The subject initializes MovePicker check masks only when quiet or evasion scoring consumes them. Neither commit is an ancestor of `87a319fd`. Their merge base with that head is `9108d012`. No branch points at either commit. The named executable SHA-256 values were not checked, because those binaries are not in this tree.

The live table still has `investigator/ownbook-off-external-20261020-0700` and `investigator/tt-rule50-qsearch-20261020-0600` at `87a319fd`. The provenance points at the 03:00 TT note `50149f78` and the 05:15 research note, both already read.

### Staged go-origin patch, one name

`ec013151745b524a7f7095b834ff97f75fecad2c` (tree `f928a898`, 1058 files, 2026-10-20 07:46 +02:00) is the only tip of `forge/test-20261020-0830`. It is a sibling of `7e3fa78a`, not a descendant. It adds four files, 108 lines, and does not change the engine blobs. It contains neither the lock, H512, nor `main`.

The four blobs are identical to the copies already read on `356e863d`:

| File | Blob |
|---|---|
| `validation/hourly/2026-10-20-go-origin/REPORT.md` | `d8b89a72` |
| `model-test.stdout` | `e08ef2bc` |
| `time_origin_model.cpp` | `d6bce27f` |
| `uci-clock-origin.patch` | `4f5362a1` |

`REPORT.md` says the parent head was `87a319fd` and names the same three source blobs this tree has: `include/forge/search.hpp` `f3f96e4b`, `src/search.cpp` `ca5b3541`, `src/uci.cpp` `9bf1b757`. On that search blob, `Worker::search` sets `start_` to `steady_clock::now()` at `src/search.cpp:1112`. `elapsed_ms` at `src/search.cpp:561` measures from `start_`, or from `ponder_hit_ns` after a ponder hit. The hard comparison is `src/search.cpp:590`. The `go` command begins at `src/uci.cpp:286`, calls `stop_search` at `src/uci.cpp:287`, parses limits at `src/uci.cpp:319`, and starts the worker thread at `src/uci.cpp:350`. The report's description of a timer that starts after dispatch matches those lines. The report says this has not been shown to cause the 1404 ms candidate timeout.

The patch context is present in those blobs. The search.cpp hunk starts at the iterative-deepening comment, which is `src/search.cpp:1109`, and replaces `start_` at `src/search.cpp:1112`. The search.hpp hunk's first old line is `int moves_to_go`, which is line 26; line 25 is the movestogo comment. The first uci hunk's first old line is the position command's `stop_search`, which is `src/uci.cpp:284`; the hunk header says 285. The second uci hunk matches `src/uci.cpp:318-320`. The report says `git apply` passed on a synthetic fixture and not on the full source tree. This run did not apply the patch.

The patch records `go_received` before `stop_search()`, so the staged clock includes the wait for the previous worker. It then assigns `limits.start_time` for every non-perft `go`, including depth, nodes, infinite, and ponder. The comment talks about clock-managed searches. The assignment has no `time_ms` or `movetime_ms` test. The later scoped patch, already read on `356e863d`, is a different file and is not this commit.

`time_origin_model.cpp` sleeps 440 ms and then samples two clocks against a hard budget of 351. `model-test.stdout` is `budget_ms=351 old_elapsed_ms=0 go_origin_elapsed_ms=440` plus the PASS line. The model was not compiled again. The report's 17/17 diagnostic count was not rerun. It says the original TT-tag match is `failed_no_resume`, six games, one candidate timeout, and no new games. The cycle7 zip is named as a conversation download and is not a file in this tree. No Elo.

The integer clock parser, the 64-slot `bad_captures_` write, and the book probe when `own_book` is false remain the parent lines already recorded for this blob: `src/uci.cpp:73`, `src/search.cpp:296`, and `src/uci.cpp:325`. They were not played.

### 08:15 research note, one name

`b0ed22d96b71803671736d68c13ba0b77d02214f` (tree `4397df2d`, 1059 files, 2026-10-20 08:21 +02:00) is the only tip of `forge/research-20261020-0815`. It adds `validation/hourly/2026-10-20-0815/RESEARCH.md`, 44 lines, on parent `ec013151`. The engine blobs are unchanged. It contains neither the lock, H512, nor `main`. The note says it produced no benchmark, speedup, or Elo.

The note repeats the 07:30 counts and the staged clock patch as inputs. It says the 07:00 and 06:00 investigator branches have no commits past `87a319fd`, which matches the live table.

Three P0 ranges do not match the blob the note names. `src/uci.cpp:286-329` includes `stop_search`, parsing, and the book probe. The worker thread starts at `src/uci.cpp:350`, outside that range. `src/search.cpp:574-580` is `total_nodes`. The hard comparison is `src/search.cpp:590`, inside `should_stop` at `src/search.cpp:582-592`. Helpers are launched at `src/search.cpp:1363-1365` and joined at `src/search.cpp:1370`. The file ends at line 1375. The note's range `1370-1395` does not contain the launch, and line 1395 does not exist. The timer and budget range does match: `src/search.cpp:1112` sets `start_`, and `src/search.cpp:1127-1153` computes the limits. Helpers then clear those limits at `src/search.cpp:1154-1158`.

The P1 store order matches the lines already recorded. `probe` accepts `key32` and `occupied()` at `src/search.cpp:199`. `store` writes `key32` at `src/search.cpp:222` and `gen_bound` at `src/search.cpp:226`. `TTEntry` is `include/forge/search.hpp:60-74`. The note's range `54-95` starts at `is_mate_score`. Quiescence returns a TT score with no halfmove test at `src/search.cpp:692-695`. The main-search cutoff requires `halfmove_clock() < 90` at `src/search.cpp:813-816`. `verification_key` is `include/forge/search.hpp:106-115`. The note's range `90-116` also covers `hashfull` and `prefetch`.

The note says `df5d839a6a03f705310bb958601375fa9411e810` passed TSan, ASan, and UBSan, with six-position single-thread parity and bench 11 equal to 419798, and that a separate baseline TSan hit the write at `src/search.cpp:222` against the read at `src/search.cpp:199` with Threads 4, Hash 1, and `go nodes 200000`. That commit exists and is not an ancestor of this tip. Its logs were not opened. The integer 419798 is the same integer stored on the failed NNUE calibration. These notes do not say it is the same run. Nothing was rebuilt here. The note's perft figures, start position depth 6 `119060324`, Kiwipete depth 4 `4085603`, and CPW position 3 depth 5 `674624`, were not run.

The rule50 candidate it names is `816423b1`, the 6.4.4 side commit above. The note says that candidate has seven old-code failing assertions and passing repaired-code tests. Those tests were not opened. The 12/12 handoff sentence is not a pass for the current quiescence path. The note says that itself.

### Not claimed

- No new Elo. The 54/54, 6/6, 12/12, and 17/17 counts are sentences. Their logs are not in these commits.
- The 351 ms and 440 ms model line was already on `356e863d`. It is a sleep model. It is not a Forge forfeit and was not regenerated.
- The staged patch is unscoped and records time before `stop_search`. It was not applied. The integrated scoped clock is a later commit, already described on `356e863d`.
- The 08:15 note is a hypothesis list. The three P0 range errors are citation errors. The TT store order and the quiescence halfmove gap remain source facts, not new measurements.
- 313 branches are still tip-only. `3cabc1b2` is still unread. It is not a branch tip.
- The KRK history miss was not replayed.
- Nothing was pushed to `main`, `lock/combo29-20261110`, `fable/standalone-h512-20261111`, or another agent's branch.
- Supermemory was unavailable. Adapter was not used.

## Next run

1. `git fetch` and `git ls-remote --heads origin`. Diff against `inventory/branches-current.tsv`. Append new rows to `inventory/HEAD_MOVEMENT.tsv`. Do not rewrite `inventory/branches.tsv` or earlier movement rows. This branch's tip will have moved by the commit that adds these files; record that as this checkpoint, then continue.
2. If a foreign tip moved, read that delta before the files below.
3. Otherwise read tip `bcfb3503b2d39f569677e4af675a09d5b870b3ca` (`forge/candidate-uci-clock-origin-native-20261020-0845`). Its own commit adds only `validation/hourly/2026-10-20-0845/LEAD.md`, 13 lines. That file is absent from `356e863d`. Parent `7e6e977c` adds `.github/workflows/forge64-clock-origin.yml`, and that blob matches `356e863d`. Non-tip `545c56a1` adds the six `validation/hourly/2026-10-20-go-origin-native/` files. `REPORT.md`, `delayed_pthread_create.c`, `native_probe_fixture.cpp`, and `uci-clock-origin-scoped.patch` match blobs already read on `356e863d`. Diff `native_clock_probe.py` and `run_native_validation.sh` against `356e863d` and read the changed lines. Do not apply patches or execute repository scripts.
4. If that delta is short, read tip `66849e5c6fc97b9d7a2f89f7fac54ea6f6253b26` (`forge/candidate-ci-clock-parent-20261020-0858`). Its commit changes `run_native_validation.sh` by 12 lines past `294cf1ba`. Read the diff as data.
5. Leave `3cabc1b2` unread. It is not a branch tip, and the diff from `2fc649ef` is 1368 files. Do not decode the `.b64` artifact parts.
6. The KRK replay remains the first reproduction when a run investigates instead of opening the next pack. Position `4R3/8/8/k2K4/8/8/8/8 w - - 0 1` should play `d5c5`. Run it on H512 `efb2ff96`, then on `f6760ff6`, then on `49b80952`.
7. Do not push to `main`, the lock, the H512 branch, or another agent's branch.
