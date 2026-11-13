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
