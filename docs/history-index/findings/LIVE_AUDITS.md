# Audits published after the frozen 416

Fetched 2026-11-13 in the afternoon. None of these branches were modified. The lock and the Fable tip were not modified. Reports were read in full unless a line below says otherwise. Elo was not replayed.

`branches/EVERY_TIP.tsv` is the row for every tip this pass opened. `coverage=live-report` is this file. `coverage=alias` means the tip tree has no markdown blob that appears on three or fewer trees: the branch name is another label for a shared commit, and the commit subject is the row's subject. `coverage=short-read` means every selected primary document on that tree is one of the 98 short files read in full in this pass. `coverage=unread-primary` means a longer primary document was selected and not read end to end yet.

## Still on the lock, now run by somebody else

`inventory/verification/2026-11-13-clock-and-badcap.md` on `cursor/forge-branch-inventory-automation` @ `00bc9129e7161a1c43ec844753a52cf4b018f085` built the lock at `16833ecc03b425586f91f4c8834dea8807bf4c22` with ASan. `go wtime 3000000000` returned `bestmove a2a3` in about a millisecond and printed no depth line. `std::from_chars` into `int` fails on that token and the parser treats the failure as a zero clock. The same note's ASan build aborted in `MovePicker::next` on the 68-losing-capture FEN. `cursor/forge-time-audit-770f` @ `33547894beec411ee5a749428bd0502932657518` clamps an out-of-range clock to `INT_MAX` and was still searching at 250 ms. `cursor/forge-correctness-20261113-e6b6` @ `f6760ff65325339c900092117cbb56c051a60724` sizes the capture buffer to 256; their earlier tip returned `bestmove d3b1` on that FEN.

## One-thread mate, two different fixes

Both later tips say a depth-9 search, then KRK `4R3/8/8/k2K4/8/8/8/8 w - - 0 1` at depth 14, played `e8e4` instead of mate in 3. `Clear Hash` did not remove the miss. The surviving state is the history and correction tables.

- Correctness @ `f6760ff65325` clears those tables at every root and keeps the transposition table. Pins still match. The earlier note that one thread was left unfixed is the older tip `dff76c5808d0`.
- Search @ `49b8095274ec` does not clear history. It skips late-move pruning and reduction only when the root already faces a lone king and the node still does. Pins still match, including depth 13 at 862329 / 907205. Threads 2, 40 fresh depth-14 searches: 0 misses, in their log.

The lock has neither change.

## Other defects, and where the fix lives

| What the report says | Where it was fixed | Default on that branch |
|---|---|---|
| `attacks::init` set the flag before the magic tables existed. Eight threads segfaulted 30/30. | correctness `call_once`; concurrency audit the same, plus a TT slot race, a stop flag restored over a late `stop()`, and nodes sampled before join | on, in those branches |
| Search treated a return to the root as an immediate draw. A null move advanced the 50-move clock, so queen vs king at clock 92 was a draw at depth 8. | `cursor/draw-rules-history-tt-cb8e` @ `844cef9a167b` | on; bench 8 and 10 match the base |
| Black's null move did not increment `fullmove_`. 7,891 positions then matched python-chess 1.11.2, 0 errors. Bench was not run. | `cursor/move-legality-82b6` @ `f1c701c9faea` | on |
| An aborted root attempt published a new move with the previous iteration's score. A TT mate ignored the 50-move clock. | `cursor/search-bound-audit-9cd5` @ `f46e8d24d961` and, with a different switch, `cursor/search-bounds-audit-e6d7` @ `ee965c4fa361` | the abort and the mate-clock check are on; `qsearch_shallow_bound` and `PvBoundFix` are off because they move the pins. `PvBoundFix` missed a proven mate in two at depth 7 on `2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1` |
| Checkmate was not stored. A stale probe slot could delete a deep entry. A mate past the 50-move clock was reused. | `cursor/tt-audit-bounds-4ffa` @ `22e837cb845b` | all three switches default 0, so that binary still has the bugs. Turning the checkmate store on moves depth-20 nodes from 12389307 to 12117140 |
| Forge 5.31.0 quiescence stood pat when every legal move was a capture or a promotion. Four positions scored the static eval instead of mate or a draw. | `cursor/forge-qsearch-audit-60ce` @ `d5db74e10e4c` | on, in the 5.31.0 tree under `forge/`, not in combo29. 150,594 contract comparisons, 0 mismatches, 1 position skipped |
| UCI option names and checkbox values were case-sensitive. `searchmoves` of only illegal moves returned `0000` on a live start position. A four-field FEN was rejected. `E2E4` was rejected. | `cursor/forge-audit-f132` @ `9a781745a3f4` | on. Depth 11 and 13 pins matched. No new match |
| A v3 refresh can pass through 33 columns on a 32-piece pair and wrap an int16 partial (33700 stored as 32700). The final sum matches. | NNUE @ `36b644d8484c` | documented, kernels left as wrapping adds. Holdout shard tag `_013` no longer matches `fb2_0130.pos`. The CPU trainer now refuses a `final_test` path |

The concurrency report also says `go perft` and `bench` ran on the command thread. Perft was moved onto the worker there and on the time-audit branch. Bench still runs on the command thread in the time-audit report.

Opposite-colored bishops are still not a draw. The draw-rules report scores them `cp 2` at depth 3 on purpose. King and two knights versus king stays `cp 493`.
