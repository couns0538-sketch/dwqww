# Gate time audit s38fx_A

Tool: S38 gate_time_audit 2026-10-27 v1. Inputs (read-only): s38fx_A.pgn (51626 B, sha256 edda9f577ef8), s38fx_A.log (3825 B, sha256 9b1c4066ad4a), s38fx_A_engine_io.log (888472 B, sha256 69ef91a26d77)

PGN games 30, terminations {'abandoned': 1, 'illegal move': 1, 'normal': 25, 'time forfeit': 3}, TC {'10+0.1': 30}. Time model {'soft_div': 22, 'inc_pct': 75, 'hard_pct': 60, 'hard_mult': 5, 'overhead_ms': 10}; phases by ply [40, 80]; nps from searches >= 100 ms.

| engine | role | moves | TL | illegal | crash | depth mean / median | used ms p50/p95/p99/max | used/soft p50/p95/p99/max | over inc | over hard | lowest clock ms | median nps | agg nps |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| base_s38 | base | 538 | 1 | 1 | 0 | 18.25 / 18.0 | 346/564/638/662 | 0.845/1.207/1.237/1.242 | 1.0 | 0 (max +0 ms) | 4001 | 1574018.0 | 1572314 |
| cand_s38 | cand | 536 | 2 | 0 | 1 | 18.17 / 18.0 | 357/813/1102/1249 | 0.91/2.134/2.482/2.595 | 1.0 | 0 (max +0 ms) | 3150 | 1645649.0 | 1641726 |

| engine | phase | median depth | median nps |
|---|---|---|---|
| base_s38 | P0_ply<40 | 18.0 | 1556334.0 |
| base_s38 | P1_ply40-79 | 19.0 | 1624159.5 |
| cand_s38 | P0_ply<40 | 18.0 | 1623253.5 |
| cand_s38 | P1_ply40-79 | 19.0 | 1699224.0 |

fastchess log: 30 Finished-game lines, events {'base_s38': {'tl': 1, 'illegal': 1, 'crash': 0}, 'cand_s38': {'tl': 2, 'illegal': 0, 'crash': 1}}, "Warning;" lines 1, results block {'games': 30, 'wins': 8, 'losses': 11, 'draws': 11}; autopromote-style crash-regex matches 3 (for comparison only).

Cross-checks: {"games_pgn_vs_finished_lines": {"log": 30, "match": true, "pgn": 30}, "illegal_crash_pgn_vs_fastchess_log": {"log": {"base_s38": 1, "cand_s38": 1}, "match": true, "pgn": {"base_s38": 1, "cand_s38": 1}}, "nps_asymmetry": {"asymmetry": 0.0455, "median_nps": {"base_s38": 1574018.0, "cand_s38": 1645649.0}, "threshold": 0.03}, "p99_vs_reference": {"engines": {"base_s38": {"p99_used_over_soft": 1.237, "ratio": 1.001, "ref_p99": 1.236}, "cand_s38": {"p99_used_over_soft": 2.482, "ratio": 2.013, "ref_p99": 1.233}}, "reference": "s38fx_REF"}, "tl_pgn_vs_fastchess_log": {"log": {"base_s38": 1, "cand_s38": 2}, "match": true, "pgn": {"base_s38": 1, "cand_s38": 2}}}

Flags: NPS_ASYMMETRY 4.55% > 3.0% (median nps {'base_s38': 1574018.0, 'cand_s38': 1645649.0}); P99_OVERSHOOT cand_s38: p99 used/soft 2.482 = 2.01x reference 1.233 (> 1.5x)

Per-game nps (first games per engine in the engine log):

- base_s38 game 0:1:1: searches 22, median nps 1573778.5, aggregate nps 1573319
- base_s38 game 0:1:2: searches 15, median nps 1567839.0, aggregate nps 1563312
- base_s38 game 0:1:3: searches 17, median nps 1571330.0, aggregate nps 1579763
- base_s38 game 0:1:4: searches 13, median nps 1553002.0, aggregate nps 1547869
- base_s38 game 0:1:5: searches 17, median nps 1573279.0, aggregate nps 1566367
- cand_s38 game 0:1:1: searches 22, median nps 1646404.5, aggregate nps 1632649
- cand_s38 game 0:1:2: searches 15, median nps 1609718.0, aggregate nps 1623264
- cand_s38 game 0:1:3: searches 18, median nps 1654726.5, aggregate nps 1652172
- cand_s38 game 0:1:4: searches 12, median nps 1611018.5, aggregate nps 1623983
- cand_s38 game 0:1:5: searches 17, median nps 1644997.0, aggregate nps 1650397
