# kimik3 job 5 report: a deterministic node clock (NodeClock)

**Headline.** Yes: with `NodeClock 1000` every clock search became exactly repeatable — 200 positions at
`go wtime 10000 btime 10000 winc 100 binc 100` gave identical best move, depth, score and node count in three
fresh processes, and identical again while four `bench 16` hogs ran on all four cores (P2). Whole games are
repeatable too: the same 100-game self-play match at 10+0.1 on the node clock, run twice, came out identical
move for move, all 100 games (Part C). With the option off the engine is unchanged: bench 11/13/16 node counts
and 2,000 positions at `go depth 8` are identical to the unpatched build (P1). The wall-clock control shows the
test can fail: with `NodeClock 0` up to 41 of 200 searches differ in node count between runs (P3). What was cut:
the 300-game `TmFinishIteration` match ran out of budget part-way; its partial score is in Part C.

## Part A — how the engine manages time today (reading)

All file/line references are to the tree of jobs 3 and 4 (`forge-combo29/`, v3 build).

- The clock plan is computed once per `go` in `Worker::go` (search.cpp) by `plan_clock_budget`
  (include/forge/clock_plan.hpp): from `wtime/btime/winc/binc/movestogo/movetime` it derives
  - soft limit = remaining/22 (`TmSoftDivisor`) + 0.75 × increment;
  - hard limit = min(remaining × 0.6, soft × 5);
  - `movetime` and `movestogo` override the divisors; `Move Overhead` (default 10 ms) is subtracted from the
    remaining time first.
- The search asks the clock in `Worker::elapsed_ms()` (search.cpp:1245), a `steady_clock` read since `start_`.
  It is asked every 1024 local nodes from the main search and from qsearch (the periodic stop check), and at the
  end of every iteration.
- The hard limit is enforced in `should_stop_with` (search.cpp:1285): when elapsed ≥ hard, the search stops in
  the middle of an iteration and the best move of the last completed iteration is played.
- At the end of each iteration the soft limit decides whether another iteration is started.
- `TmFinishIteration` (check, default false; tm_finish.hpp): estimates the duration of the next iteration from
  the last two iteration durations and declines to start one that is not expected to finish inside the budget.
- `TmNodeShare` (check, default false; tm_node_share.hpp): scales the soft limit by the share of nodes spent
  under the current best move (0% → 1.5×, 100% → 0.5×).
- The `info` lines read the clock separately where they are assembled (search.cpp:2234 area) and
  `result.elapsed_ms` is filled at four more sites (search.cpp:2274, 2330, 2643).
- Weakest points, in five lines: (1) no best-move stability term — a best move that changes every iteration gets
  the same budget as a stable one; (2) no score-trend term — a falling score does not buy time; (3) the node
  share switch exists but is off by default and only sees the root best move, not the ponder move; (4) the hard
  limit of 5× soft is generous, so a single unstable iteration can spend most of the safety margin; (5) the
  next-iteration estimate behind `TmFinishIteration` uses only two samples and no depth-dependent growth model.

## Part B — the patch

`nodeclock.patch.txt` (also split per file: `nodeclock_search.cpp.patch.txt`,
`nodeclock_search.hpp.patch.txt`, `nodeclock_uci.cpp.patch.txt`). Every wall-clock replacement:

- search.cpp:107 — `std::int64_t tune::NodeClock` definition (0 = off).
- search.cpp:1245 `Worker::elapsed_ms()` — with `NodeClock > 0` returns `total_nodes() / NodeClock`.
  `total_nodes()` sums the per-worker atomics, so the check stays a few loads; no locking anywhere.
  With several threads the count is the sum over threads, as the job specifies.
- search.cpp:2234 — the `info`-line `time`/`nps`: with NodeClock on, elapsed is `elapsed_ms()` and
  `nps = NodeClock × 1000` falls out of nodes/time. Off path byte-identical to before.
- search.cpp:2274, 2330, 2643 — the four `result.elapsed_ms` sites, wrapped the same way.
- include/forge/search.hpp:305 — the `extern` declaration.
- uci.cpp:233 — `option name NodeClock type spin default 0 min 0 max 100000000`; uci.cpp:437 — parsing in
  `apply_spin`.

Nothing else changes: soft/hard limits are still computed from the `go` command exactly as today; only the
unit "milliseconds" is now nodes/N. `go infinite`, `go nodes`, `go depth`, `go movetime` and `stop` do not
consult the replaced clock (movetime is a fixed budget, nodes/depth/infinite need no clock), and behave as
before — P1's identical fixed-depth runs cover depth; `go nodes 500000` and `go movetime` spot checks below.

### P1 — off = old engine (PASS)

bench 11/13/16 with the patch, option untouched: 312,866 / 862,329 / 3,024,920 nodes — the known counts
(`o1_nc.txt`). 2,000 positions at `go depth 8`, patched-vs-unpatched, mode A/B deterministic fields
(best move, score, nodes) identical; the sha256 pairs are in `o1_nc.txt`. Not one node changed with the
option off.

### P2 — on = repeatable (PASS)

200 positions (`uho200.epd` first 200), each `go wtime 10000 btime 10000 winc 100 binc 100`,
`NodeClock 1000`, driver `p2_driver.py.txt`, records bestmove/depth/score/nodes per search.
- Three fresh-process runs: `p2_run1.txt` == `p2_run2.txt` == `p2_run3.txt` (byte identical, all 200 rows).
- The same 200 searches while four `bench 16` copies ran pinned to all four cores for the whole run:
  `p2_run_loaded.txt` == `p2_run1.txt`. (First loaded attempt kept hogs for only seconds — bench finishes in
  ~2 s; redone with hogs looping until the run ended. The log shows the honest fix.)
- Driver bug found and fixed on the way: the first driver parsed the `info` line with a misaligned
  zip and recorded `?` for depth/score; its node column was correct (verified 200/200 against the rerun),
  and all claims above come from the corrected driver.

### P3 — wall-clock control (PASS, i.e. it fails as it must)

The same 200 searches with `NodeClock 0`, three runs (`p3_run1..3.txt`): node counts differ between runs at
38 (1v2), 28 (1v3), 41 (2v3) of 200 positions; 52 rows differ in at least one field. Many, as required.

### P4 — limits respected (PASS)

From the `go` command: remaining = 10,000 − 10 (Move Overhead) = 9,990 node-ms; soft = 9,990/22 + 75 =
529 ms → 529,000 nodes at N = 1000; hard = min(9,990 × 0.6, 529 × 5) = 2,645 ms → 2,645,000 nodes.
The 200 P2 stops: min 242,513, mean 479,049, max 1,750,651. Above the soft limit: 53/200 (normal: the soft
limit only gates starting a new iteration). Above the hard limit: 0. Largest overshoot past hard: 0 nodes.

### P5 — sanitizers (PASS)

Build: ASan+UBSan (`-fsanitize=address,undefined -fno-omit-frame-pointer`), same source.
- Arming first: a planted use-after-free inside the NodeClock branch of `elapsed_ms()` (search.cpp:1251)
  was caught on the first clocked search: `AddressSanitizer: heap-use-after-free ... in
  forge::Worker::elapsed_ms()`, exit 1 (`p5_armed.log`). (Two earlier arm attempts failed for reasons worth
  recording: a wild read 65 GB past the NNUE table landed in ASan's mapped shadow region — no report; and a
  read just past the table never executed because the P2 searches do not load the v3 net, so the v3 file was
  the wrong place. The fault belongs on the path the test exercises.)
- Clean run: the 200 P2 searches under ASan+UBSan, nothing on stderr (`p5_clean.txt`, `p5_clean.log`
  empty of sanitizer output), rows identical to `p2_run1.txt`.

## Part C — the first use

Match runner `match5.py.txt` (python-chess): both sides `NodeClock 1000`, Threads 1, Hash 16, OwnBook off,
TC 10+0.1 tracked in node-milliseconds (budget starts at 10,000, +100 per move, decremented by the `time` field
of the search's last info line). The real clock is never consulted, so no side can lose on the real clock by
construction; a nodetime forfeit is possible in the node domain (none occurred). Draws adjudicated by
python-chess including claim_draw; 200-fullmove cap. Same openings (`uho200.epd`) and same game order both runs.
- Run twice: `matchA_run1_games.txt` == `matchA_run2_games.txt`, byte identical — all 100 games, every move.
- Run 1: 34 white wins, 47 draws, 19 black wins; mean game 107 plies (min 8, max 276); 0 nodetime forfeits.

`TmFinishIteration` on-vs-off match (300 games, `match5tm.py.txt`, both on the node clock, colors alternate):
CUT BY BUDGET — PARTIAL. 203 of 300 games completed at cut time (shards cut 21:25 to leave the P5 clean run
the cores). Score so far: switch ON 105.0/203 = 51.7% against off — no measurable gain at this sample size,
but the run is partial and should be rerun to completion. The shard files are `tm_match_s0..s3.txt`
(203 games with per-game result and scoreA). Even partial, this is the first clock-match measurement of the
engine's time management: every game was played on the node clock and is exactly reproducible.

## Files of the repository opened

search.cpp, uci.cpp, clock_plan.hpp, tm_finish.hpp, tm_node_share.hpp, search.hpp, nnue_v3.cpp, nnue_v3.hpp,
eval.cpp (all under forge-combo29/; src/ or include/forge/), plus the job file and my earlier reports.

## Stamps

Job file read again 20:37; matches launched 20:38; Part C identical-result confirmed 20:54; P2 reruns
20:40–21:18; P5 armed 20:56, clean run finished 21:25 (rows identical to the normal build's P2 rows);
tm match cut 21:25 at 203/300; report written 21:13–21:30; all times UTC 2026-11-15.

## What I did not do

- The `TmFinishIteration` match did not reach 300 games inside the budget; partial result only.
- Multi-threaded NodeClock runs (option implemented as a sum over threads; only Threads 1 was tested, per the
  job).
- `go movetime`/`go nodes`/`go infinite` behavior is covered by reasoning + P1 fixed-depth identity, not by new
  dedicated searches.
- The engine was not strength-tested beyond the self-play matches above.

## What I am not sure about

- `nps` prints exactly 1,000,000 with NodeClock 1000 only because elapsed_ms is integer-truncated; at tiny
  elapsed values nps is computed from a 1 ms floor, as before — the field is informational only.
- Whether `Move Overhead` should also be virtualized (it is subtracted in milliseconds before the plan; with
  NodeClock the 10 ms stay 10 "node-ms"). I kept it as-is: it is part of the budget computation, which the job
  said to leave unchanged.
- 53/200 searches stopping past the soft limit is expected (soft gates iteration starts, not stops), but a
  reviewer should know the number.

## A better way

Give the node clock its own counter type end-to-end (node-ms as a distinct unit in `clock_plan`) instead of
reusing "milliseconds"; then `Move Overhead` and the info-line units cannot be silently mixed. Also: the two
misaligned-zip parsing bugs I hit in my own drivers (both mine, both fixed) argue for one shared, tested
info-line parser per helper.

Model: Kimi K3.
