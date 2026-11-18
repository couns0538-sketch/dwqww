# Forge PC r15 history inventory

This inventory comes from the Job 4 buttons counting source. Its build uses
`FORGE_SEARCH_SPEED2=1` and `FORGE_MATE_ALPHA_GUARD=1`. The baseline is PC20
with built-in evaluation, Threads 1, and Hash 16. Line numbers are from the
unmodified Job 4 counting tree. See [verbatim source excerpts](forge-history-lines.txt).

## Step 1 source gates

1. **Met.** The root overload begins at `src/search.cpp:2677`. At
   `src/search.cpp:2893–2914` it initializes stack fields, including the killers
   at line 2904. The continuation assignment on line 2899 sets a pointer. It
   does not write the history table. A normal primary search starts without
   clearing or ageing the history tables.
2. **Met for WARM.** Every direct caller of `Worker::clear()` in the engine
   source is listed below. With fixed Threads 1 and MultiPV 1 before game
   start, options sent before the game, disabled buttons, and no bench command
   within the game, no such caller intervenes between searches. The prior
   replay sends all options before entering the game loop, calls
   `reset_tables` once at each warm game's start, and sends only a position
   and search command per ply (`run_sweep.py:45–46,85–109` and
   `run_games.py:111–114`). UCI defaults MultiPV to 1 and copies it to the
   search limits (`src/uci.cpp:278,681`). History updates during each search
   remain active and feed later searches.
3. **Met.** `src/search.cpp:396` sets `HistoryMax = 16384`.
   `apply_history` clamps the bonus and uses
   `entry + clamped - entry * abs(clamped) / HistoryMax`
   (`src/search.cpp:469–472`). In exact arithmetic, this is a weighted
   average of the current entry and the signed endpoint. The division's
   truncation keeps the result between the inclusive integer endpoints:
   the formula is monotone in the entry for a fixed bonus and stays within
   the limits at both endpoints. The entry starts at zero.

| Direct caller | Exact site | Reachability in a warm game |
| --- | --- | --- |
| `Worker::Worker` | `src/search.cpp:1233–1254`, call at 1253 | Initialization. The primary `Searcher` constructs workers through `set_threads` at 3251–3262. `setoption Threads` invokes this at `src/uci.cpp:626–627` before the game. |
| `Searcher::clear` | `src/search.cpp:3287–3290`, call at 3289 | `ucinewgame` calls this at `src/uci.cpp:388–391` once per warm game. A changed `SoundMatePruning` or `MateAlphaGuard` calls it at `src/uci.cpp:588–609`, outside the per-ply loop. Bench calls it on a separate local searcher at `src/uci.cpp:781–789`. |
| Alternate worker | `src/search.cpp:3102–3104`, call at 3103 | The alternate worker is allocated only when `multipv > 1 && is_main()`, at `src/search.cpp:2944–2954`. |
| `Searcher::clear_workers` | `src/search.cpp:3272–3274`, call at 3273 | The Job 4 `ClearWorkers` button calls this at `src/uci.cpp:436–438`. The warm replay sends no buttons. |

`Clear Hash` and `ClearPawnCache` call `clear_caches`, which only clears the
evaluator's pawn cache (`src/search.cpp:3267–3278`,
`include/forge/search.hpp:474`, `src/eval.cpp:569–571`). The pawn evaluation
cache, per-node `threat_maps_`, and stack killers are separate from learned
history entries. `Worker::clear()` also clears them (`src/search.cpp:1258–1278`).
The threat maps are recomputed where needed (`src/search.cpp:1838,2220`).

## Worker history tables

Unless otherwise qualified, read, update, and clear line numbers in this table
are in `src/search.cpp`. Member declarations are in
`include/forge/search.hpp:494–503,556–559`. The integer table aliases and
correction bound are in `include/forge/search.hpp:389–413` and
`include/forge/b4.hpp:20–22,103–108`.

| Member and stored value | Element type and bound | Updates | Reads | Emptied by `Worker::clear()` | Read by `quiet_history` under PC20 |
| --- | --- | --- | --- | --- | --- |
| `main_history_`, butterfly score by side/from/to | `std::int16_t`, ±16384 | Quiet cutoff bonus/malus 1718,1727. Quiet PV bonus 2563–2564. Optional TT cutoff history 2014 and eval swing 2055–2057. | Move picker 1013,1025 and `quiet_history` 1594–1604. Rework's blend also reads the plain entry at 1634. | Yes, 1260 | **Yes** |
| `threat_history_`, threat-indexed quiet score | `std::int16_t`, ±16384 | Threat-history update 1684–1687 from quiet cutoff 1719,1728 and PV bonus 2565. | Helper 1648–1651, used at 1025 and 1600. `ThreatHistory=false` at 306 returns before any table read. | Yes, 1261 | No |
| `capture_history_`, capture ordering score | `std::int16_t`, ±16384 | Capture bonus/malus 1738–1751 from beta cutoff 2560. | Capture picker 1127–1137, optional capture evasions 1207–1213, and 1690–1693 called by main for non-quiets at 2264. | Yes, 1266 | No |
| `continuation_history_`, prior move/current move score | `std::int16_t`, ±16384 | Gravity at 1696–1702 via quiet cutoff 1723,1732, optional TT cutoff 2015, LMR success 2507, and optional fail-low continuation 2575–2580. Updates include contexts 1, 2, and 4 plies back when available. | `quiet_history_sum` reads entries at 488–490 from 1594–1599, also used by move picker at 1014–1025. Search binds prior-move contexts at 1865,2121,2175,2441. | Yes, 1267 | **Yes**, contexts 1 and 2 under PC20. `ContHist4PlyRead=false` at 302 disables the optional fourth-ply read. |
| `rework_history_`, lesser-threat-keyed butterfly twin | `std::int16_t`, ±16384 | Gravity 1641–1644 via quiet cutoff 1735, and quiet PV bonus 2572. | 1624–1635, called by the move picker at 1029 and `quiet_history` at 1592. | Yes, 1274 | **Yes**, PC20 `HistRework=2` takes three quarters from this table and one quarter from the butterfly table, truncating the combined term toward zero. |
| `pawn_history_`, optional pawn-structure move score | `std::int16_t`, ±16384 when built | 1670–1675 via 1721,1730 and optional PV bonus 2566–2570. | 1656–1666 via 1026–1028 and 1601–1603. | When compiled and enabled, 1263–1265. Pointer is empty in this build, 1238–1242. | No, compiled out |
| `counter_moves_`, prior move to reply move | `Move`, no numeric score bound, empty is `Move{}` | Quiet cutoff learns reply at 1713–1715. | Move picker 815–819 and quiet extinction 2243–2245. | Yes, 1268 | No |
| `correction_history_`, pawn-structure evaluation correction | `std::int32_t`, ±8192 | 1472–1475. | 1439. | Yes, 1269 | No |
| `material_correction_`, material evaluation correction | `std::int32_t`, ±8192 | 1472–1474,1476 when weight is positive. | 1440–1441 when weight is positive. | Yes, 1270 | No |
| `non_pawn_white_correction_`, white non-pawn evaluation correction | `std::int32_t`, ±8192 | 1472–1474,1477–1478 with `NonPawnCorrection`. | 1443–1446. | Yes, 1271 | No |
| `non_pawn_black_correction_`, black non-pawn evaluation correction | `std::int32_t`, ±8192 | 1472–1474,1477,1479 with `NonPawnCorrection`. | 1443–1446. | Yes, 1272 | No |
| `joint_correction_`, pawn-structure × non-pawn-material correction | `std::int32_t`, ±8192 | B4 gravity 1483–1485 with `HistRework`. It clamps to ±8192 (`include/forge/b4.hpp:69–75`). | 1448–1451 with `HistRework`. | Yes, 1275 | No |
| `continuation_correction_`, corrections for prior moves | `std::int32_t`, ±8192 | 1472–1474,1487–1496 with `CorrHistV2`. | 1453–1463 with `CorrHistV2`. | Yes, 1276 | No |

All correction entries are updated under the main-search bound gate at
`src/search.cpp:2592–2598`, and read separately in `corrected_eval` from
quiescence, optional hindsight adjustment, and main search at 1817, 1989, and
2030. The corrected evaluation can influence pruning indirectly.

PC20 ageing therefore covers the entire butterfly, continuation, and
lesser-threat rework tables. This follows the live call at
`src/search.cpp:1590–1604`, the separate threat table's early return at
1648–1651, and the `HistRework=2` blend at 1633–1635 with
`include/forge/b4.hpp:24–28,62–67`. The three aged tables are distinct from the
correction tables. The quiet score is assigned at `src/search.cpp:2264`
and used by history pruning at 2332–2336 and LMR at 2475.
