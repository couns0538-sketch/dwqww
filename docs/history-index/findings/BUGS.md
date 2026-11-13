# Defects visible in git

These are source facts or report reproductions. This index did not compile or run the engine. A report that says a test aborted is cited as that report, not as a new run.

## The deferred-capture buffer is still 64 slots on the lock

`MovePicker::bad_captures_` is `std::array<Move, 64>`. The picker writes it with `bad_captures_[bad_count_++] = move` and does not test the size. Every noisy move that fails the SEE threshold is stored there. `quiets_tried` (128) and `captures_tried` (64) in the same file do test their size before writing. The deferred-capture buffer does not.

| Tree | Blob | Line of the write |
|---|---|---|
| `lock/combo29-20261110` @ `16833ecc03b425586f91f4c8834dea8807bf4c22` | `2ffe2556113c` | 469 |
| `fable/standalone-h512-20261111` @ `efb2ff960037087299332bc6a44baea69441a17a` | `3ca25955f564` | 472 |

Across the 416 frozen tips there are 78 unique `search.cpp` blobs that sit at a path ending in `src/search.cpp` or a copy of it. 53 of those blobs contain the 64-slot declaration and the unchecked write. 22 do not mention `bad_captures_`. Three size the array to `MoveList::Capacity` (256) and keep the same write:

- `fable-review-buffix` @ `8632e8ab35f6b269fa66c57043121dd55e4c5756`, blob `30b9c791bcb1`
- `forge/sol-jobACD-20261025`, blob `f02d05f7e7aa`
- one overlay copy inside `forge/sol-pack31-20261025`, blob `7d8e54c1d451`

`fable_review/REVIEW.md` on the buffix branch (blob `3b6e2386b6533f8ab797244888c96fb297ea6b2a`) says the overflow was known to Opus S14, a node-identical patch was already in the lock archive, and that patch was not in AL1. The same file says a later fixture, FEN `3r4/Pn1Q1p2/1Q1n1QpN/1p1Q1pRB/1Qbp1QpN/2bQ1pRB/3r1QpK/2k2q2 w - - 0 1`, has 69 pseudo-legal noisy moves and 68 SEE-losing ones. With libstdc++ assertions on, the 64-slot engine aborted in `operator[]` and the 256-slot engine completed a depth-3 search. The review also says an earlier regression only reached 50 losing moves, so that earlier test did not demonstrate the overflow.

`FABLE_REVIEW_OPUS.md` (blob `3f18d1a9ac192535c5461cd0780100ecc7efac9b`) tells the owner to merge `fable-review-buffix` into the next lock. `lock/combo29-20261110` still has the 64-slot write. The merge did not land there.

The correctness branch, read at `cursor/forge-correctness-20261113-e6b6` @ `dff76c5808d0ceb7fc3940d1758991c3c33fb26d`, sizes the same array to `MoveList::Capacity` at `forge-combo29/src/search.cpp:581`. Its `RESUME.md` reports the same FEN aborting before the change and returning `bestmove=d3b1` after it. That is their run, not one done for this index.

`MoveList::push_back` only `assert`s its capacity. Release builds define `NDEBUG`, so that assert is absent. The generator's capacity is 256. The buffix note treats 256 as enough because a move is stored once. This index did not search for a position with more than 256 pseudo-legal moves.

## Position text and a zero-node budget, still in the Fable tip

Read in `forge-combo29/src/uci.cpp` on this branch, which is the Fable tip's file. `apply_position` returns on an illegal move token before `board = candidate` (the illegal-move message is at line 64, the assignment at line 70). A token other than `moves` also returns before that assignment (line 60). The correctness resume says `position startpos moves NOTAMOVE` from a checkmate used to leave the engine in mate, and that their branch now keeps the legal prefix. Their branch was not modified here.

In `forge-combo29/src/search.cpp` on the same tip, a terminal or drawn root emits depth lines and returns (from line 1839) before the explicit `nodes == 0` return (line 1857). The correctness resume says a stalemate `go nodes 0` printed `info depth 1` on their binary before they moved that return ahead of the terminal report. Not re-run here.

## Other defects the reports already name

These were read. They are not new reproductions.

- WAC001 at depth 12 misses Qg6 mate in two. `astra-notes` @ `3e50336ac0249cfcc87d23f8154e1e842d2f7c79`, `FINAL_REPORT.md` blob `0d09e3fd90ccd944a7c7d6ed14fe1b6a39d8be99`. Raw CTest stays 55/56 with four pre-existing `forge_tests` lines. The report does not name the search cause. `SmpProtectProvenScore` is default off and is a score-band guard, not a proof that a high score came from a tablebase.
- HardDeadline could print `info depth` after the watchdog bestmove. `OPUS_R3_REPORT.md` blob `80d807111ce3d79d1187ab0b32bdbf12c0ac3a60` says that was fixed at `5792074`, with 0 late lines in a later self-play. Not re-run.
- `SmpHelpersPastDepth` removes helper idle time on `go depth` and does not shorten time-to-depth on the quiet-runner repeat. The option stays off. Same report.
- `NetScale` and `NnueInt16` do nothing when a v2 net is loaded, and `NnueInt16` can still print that it is active. Same report. No warning was added.
- UCI option names are case-sensitive. The report says the protocol is not. No engine change.
- `CaptureFutilityMultiplier` changes 0 nodes. `QsSeeMargin` values 0 through 99 search the same tree because SEE balances are multiples of 100. Same report.
- Eight tracked `.pyc` files. `FABLE_REVIEW_OPUS.md` says they were untracked on `fable-review-r3-stack` and remain on the opus branches.
- A Windows checkout cannot hold both `source/a` and `source/A/child.txt`. Stated in astra datafilter `RESULTS.md` blob `c25059861c4d4e66f373d4d9c0a5c19511023cc7`, which sits inside the 4,035-file commit on `astra-r10-3jobs` and is past a 300-file listing. See `GITHUB_FILE_CAP.md`.
- The search-gap dedupe (blob `44365b23b2a5166521f2a5f3399781f994a2a657`) saw a move-list overflow mention and did not treat it as a search-strength idea. Its snapshot is 2026-11-09 and does not include the later lock.

## Not a bug from this pass

The S11 scalar-parity JSON that a 300-file listing hides (blob `720e799e36f60a24880d663d081ff7cb7ace3a69`, on `forge/sol-pack31-20261025`) has status `PASS_NATIVE_EXACT_PARITY` for 1,000,000 positions. It points at an earlier failed receipt by sha256 `7877d436b260d802035d98d497d715a3d8c218c20df4e0180ebb425ba8c67630` and a `/tmp` path. That failed file is not in the tip. The pass was not re-run.
