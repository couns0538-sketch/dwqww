# TIME MODEL of forge-combo29 (commit 6b98f2170a3210e71beed04bbd2553972c253ed7), from the source
Written by kimi5, job 1, 2026-11-16. Every line number was opened and read; grep-verified.

## A1. How `go` parameters become limits

Parsing: `parse_limits` (src/uci.cpp:80-134). `wtime`/`btime` set `limits.time_ms` only for the
side to move (uci.cpp:121-124), `winc`/`binc` likewise `limits.increment_ms`; all four go through
`parse_clock_ms` (include/forge/uci_clock.hpp:26-48: garbage -> 0, negative -> 0, ceiling
kMaxClockMs). `movestogo` -> `limits.moves_to_go` (>=1, uci.cpp:116). `movetime` ->
`limits.movetime_ms` (uci.cpp:115). `Move Overhead` (spin, default 10, uci.cpp:152, advertised
uci.cpp:203, set uci.cpp:470-471) is copied into `limits.move_overhead_ms` at `go` (uci.cpp:518).

The clock origin: `command_start` is stamped when the `go` LINE IS READ (uci.cpp:192); for any
finite externally clocked search it becomes `limits.start_time` (uci.cpp:520-522:
`!infinite && !ponder && (time_ms >= 0 || movetime_ms >= 0)`). `Worker::search` adopts it as
`start_` (src/search.cpp:2143-2147). So parse, book probe and thread creation are INSIDE the
budget; the budget does not wait for the engine to catch up.

Limit computation (search.cpp:2185-2200):
- infinite: no limits.
- movetime: `hard = max(1, movetime_ms - overhead)`; soft = hard (search.cpp:2190-2192).
- clock play: `plan_clock_budget` (include/forge/clock_plan.hpp:26-50) with
  overhead = max(0, Move Overhead):
  - `time <= overhead` -> {0,0,reserve_empty=true} (clock_plan.hpp:32) — see A6.
  - `available = time - overhead` (line 34).
  - movestogo > 0: `soft = available/(min(mtg,50)+1) + inc*3/4`;
    `hard = min(available*4/5, soft*4)` (lines 38-40).
  - else: `soft = available/TmSoftDivisor + inc*TmIncrementPercent/100`;
    `hard = min(available*TmHardPercent/100, soft*TmHardSoftMultiple)` (lines 42-44).
  - both clamped into [1, available], then `soft <= hard` (lines 46-48).
  INVARIANT: hard <= available = time - overhead. With the default overhead 10, no plan ever
  allows the search to run past T - 10 ms of its own clock.

Worked examples (Move Overhead 10; TmSoftDivisor 22, TmIncrementPercent 75, TmHardPercent 60,
TmHardSoftMultiple 5 — search.cpp:79-82):
- `wtime 1000 winc 10`: available 990; soft = 990/22 + 10*75/100 = 45+7 = 52 ms;
  hard = min(594, 260) = 260 ms.
- `wtime 100`: available 90; soft = 90/22 = 4 ms; hard = min(54, 20) = 20 ms.
- `wtime 20`: available 10; soft = 10/22 = 0 -> clamped to 1 ms; hard = min(6, 5) = 5 ms.
- `wtime 300 movestogo 1`: available 290; soft = 290/2 = 145 ms; hard = min(232, 580) = 232 ms.
- `movetime 50`: hard = soft = max(1, 50-10) = 40 ms.

The soft limit is used only between iterations (see A3); the hard limit stops the search
mid-iteration. Nothing ever raises a limit above `available` after planning: the only later
adjustment is TmNodeShare's soft scale, clamped to [1, hard] (tm_node_share.hpp:50-51).

## A2. Every option whose name starts with `Tm`

Advertised in the `uci` answer (uci.cpp:233-234 two checks; the spins via FORGE_EXPOSE_TUNABLES,
uci.cpp:240-245, registered search.cpp:141-148, defaults search.cpp:79-88):

| option | kind | default | where read | what it changes |
|---|---|---|---|---|
| TmFinishIteration | check | false | declared search.cpp:106; set uci.cpp:403-421; used search.cpp:2395-2399, 2613-2626 | After each finished iteration, predict the next iteration's duration from the last two (tm_finish.hpp:27-37: steady growth -> last^2/prev; a >2x spike -> geometric mean); if the estimate exceeds the remaining soft budget, stop and keep the finished move. Clock play only. |
| TmNodeShare | check | false | declared search.cpp:107; set uci.cpp:437-439; used search.cpp:2577, 2592-2611 | Replaces the soft basis by the best root move's share of root nodes: 0% -> 1.5x soft, 50% -> 1x, 100% -> 0.5x, clamped to [1, hard] (tm_node_share.hpp:33-54). While on, the older effort factor is forced to 1 (2577, tm_node_share.hpp:61-66). Clock play only. |
| TmSoftDivisor | spin | 22 | search.cpp:79; clock_plan.hpp:43 | soft = available/divisor + inc share. |
| TmIncrementPercent | spin | 75 | search.cpp:80; clock_plan.hpp:43 | percent of the increment added to soft. |
| TmHardPercent | spin | 60 | search.cpp:81; clock_plan.hpp:44 | hard cap as % of available. |
| TmHardSoftMultiple | spin | 5 | search.cpp:82; clock_plan.hpp:44 | hard cap as multiple of soft. |
| TmStableFactor | spin | 60 | search.cpp:83; 2564 | x0.01 soft multiplier after >=6 stable best-move iterations. |
| TmSemiStableFactor | spin | 80 | search.cpp:84; 2565 | x0.01 after >=3 stable. |
| TmUnstableFactor | spin | 140 | search.cpp:85; 2566 | x0.01 when the best move just changed (depth>=6). |
| TmEffortBase | spin | 155 | search.cpp:86; 2578 | effort factor clamp(1.55 - best-move node share, 0.6, 1.4) when TmNodeShare is OFF. |
| TmFallingEvalPercent | spin | 100 | search.cpp:87; 2582-2584 | extra soft factor per 100 cp of score drop: factor *= 1 + drop*100/10000 (drop capped 150). |
| TmMinFactorPercent | spin | 45 | search.cpp:88; 2586 | lower bound of the combined factor (x0.01). |

## A3. Where the search looks at the clock

- Inside the tree: src/search.cpp:1561 (`Worker::search`) and 1419 (`Worker::qsearch`):
  `if (((local_nodes_ & 1023U) == 0 || node_limit_specified_) && should_stop()) aborted_ = true;`
  -> one look every 1024 nodes per worker (every node under a node budget). Quiescence is
  covered by the same line. Between two looks at most 1024 nodes run.
- `should_stop` (1292-1298) publishes this worker's node count, then `should_stop_with`
  (1265-1289): external stop (1266); node budget (1272-1276); HELPERS RETURN FALSE for the
  clock (1280) — only the main worker ever stops on time; empty reserve -> stop now
  (1281-1284, unless still waiting to ponder); `elapsed_ms() >= hard_limit_ms_` -> stop
  (1285-1288). `elapsed_ms()` (1244-1254) reads steady_clock vs `start_` and truncates to ms.
- Between iterations (ID loop, 2392-2628): `should_stop()` at 2556; the soft test at 2612
  (`elapsed_ms() >= soft_basis * factor`); TmFinishIteration hold at 2613-2626. The soft test
  can only end the search between iterations; it never aborts one.
- Threads > 1: helpers are plain workers launched at search.cpp:2736-2743. They never look at
  the clock (1280); they stop on `shared_.stop`, which the main thread sets right after the
  main worker returns, before joining them (2745-2749). A helper can therefore run at most one
  more 1024-node interval after the main worker stopped.
- What is played when the hard limit has passed: the iteration is aborted (`aborted_`). For a
  CLOCK or external stop, if the unfinished root iteration already produced a PV that raised
  alpha (pv_length > 0 and pv[0] != the previous best), THAT move is played
  (search.cpp:2439-2452); otherwise the last finished iteration's move (2454-2460). For a NODE
  stop (`stopped_by_nodes_`) the partial move is never taken (2443). A search aborted before
  any PV plays the first legal root candidate (2640).

## A4. What is NOT interruptible

- Between the `go` line and the first node (all INSIDE the budget, A1): `stop_search()` of any
  previous search (uci.cpp:482, joins the old worker), parsing (uci.cpp:516), the book probe
  (uci.cpp:526-543; a book hit prints bestmove at once), `std::thread` creation
  (uci.cpp:552), TT aging `new_search` (search.cpp:2707), per-worker Board copies
  (2739, 2744), root legal-move generation (search.cpp:2202-2209). All are O(microseconds);
  nothing here loops over the tree. Measured floor: Control 1 of B2.
- The first iteration: NOT special — the first node already calls `should_stop` at
  local_nodes_ == 0 (0 & 1023 == 0, search.cpp:1561), so even depth 1 can abort at entry.
- Between the last node and the `bestmove` line: ID-loop tail (search.cpp:2630-2645); the
  helper join (2747-2749) — each helper finishes at most its current 1024-node interval;
  bestmove formatting and printing with a flush (uci.cpp:561-573, `std::endl`). For clocked
  searches the worker prints immediately; the stop_cv wait exists only for infinite/ponder
  (uci.cpp:555-560).
- `isready`/`ucinewgame` work (hash clear) happens while reading those commands, before the
  `go` line is read, so it is outside the measured window (but delays a GUI that pipelines).

## A5. `go ponder` / `ponderhit`

- `go ponder` sets `limits.ponder`; `start_time` is NOT stamped (uci.cpp:520-522). The plan
  (soft/hard) is computed at search start from the go-ponder clock fields as usual.
- While `shared_.ponder_hit_ns == 0`: `elapsed_ms()` returns 0 (search.cpp:1246-1248), every
  clock stop is suspended (1282-1283, 1286-1287, 2398, 2557) — the search thinks on the
  opponent's clock, stoppable only by `stop`.
- `Searcher::ponderhit` (include/forge/search.hpp:585-590) stamps the hit time (first hit
  wins). From that moment `elapsed_ms()` counts FROM THE HIT (search.cpp:1249-1251) and the
  precomputed soft/hard limits apply to the post-hit elapsed. So the engine's budget restarts
  at ponderhit; the wall time spent pondering was the opponent's.
- After finishing, a ponder worker waits for stop/ponderhit before printing bestmove
  (uci.cpp:555-560; ponderhit path uci.cpp:627-636).

## A6. Time left smaller than Move Overhead

- `time <= overhead`: `reserve_empty` (clock_plan.hpp:32). `time_managed_` stays false
  (search.cpp:2199). If not waiting to ponder (search.cpp:2287-2320): probe the TT; a legal
  hash move is played at once (depth 0, 0 nodes, 2302-2308); otherwise a 1-ply emergency
  search capped at 2000 nodes with helpers left off (2310-2320; helpers excluded at
  2696-2700). If the search was pondering, the emergency path is skipped; after ponderhit
  `should_stop_with` returns true immediately (1281-1284) and the first legal root move is
  played (2640).
- `movetime <= overhead`: hard = max(1, movetime - overhead) = 1 ms floor (2190-2192).
- `wtime 0` or absent: parse clamps to 0 / time_ms stays -1 (no clock play at all when -1).
