# Gate time audit s38fx_REF

Tool: S38 gate_time_audit 2026-10-27 v1. Inputs (read-only): s38fx_REF.pgn (20710 B, sha256 bf89dff0e974), s38fx_REF.log (1744 B, sha256 196b9c8cc8d3), s38fx_REF_engine_io.log (355148 B, sha256 18cac8cb6443)

PGN games 12, terminations {'normal': 12}, TC {'10+0.1': 12}. Time model {'soft_div': 22, 'inc_pct': 75, 'hard_pct': 60, 'hard_mult': 5, 'overhead_ms': 10}; phases by ply [40, 80]; nps from searches >= 100 ms.

| engine | role | moves | TL | illegal | crash | depth mean / median | used ms p50/p95/p99/max | used/soft p50/p95/p99/max | over inc | over hard | lowest clock ms | median nps | agg nps |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| base_s38 | base | 215 | 0 | 0 | 0 | 18.35 / 18.0 | 337/577/636/649 | 0.839/1.21/1.236/1.241 | 1.0 | 0 (max +0 ms) | 4065 | 1576210.0 | 1573671 |
| cand_s38 | cand | 215 | 0 | 0 | 0 | 18.11 / 18.0 | 333/580/632/657 | 0.809/1.206/1.233/1.246 | 1.0 | 0 (max +0 ms) | 4481 | 1569801.0 | 1570895 |

| engine | phase | median depth | median nps |
|---|---|---|---|
| base_s38 | P0_ply<40 | 18.0 | 1558114.5 |
| base_s38 | P1_ply40-79 | 19.0 | 1619096.0 |
| cand_s38 | P0_ply<40 | 18.0 | 1547252.0 |
| cand_s38 | P1_ply40-79 | 19.0 | 1639725.0 |

fastchess log: 12 Finished-game lines, events {'base_s38': {'tl': 0, 'illegal': 0, 'crash': 0}, 'cand_s38': {'tl': 0, 'illegal': 0, 'crash': 0}}, "Warning;" lines 0, results block {'games': 12, 'wins': 3, 'losses': 2, 'draws': 7}; autopromote-style crash-regex matches 0 (for comparison only).

Cross-checks: {"games_pgn_vs_finished_lines": {"log": 12, "match": true, "pgn": 12}, "illegal_crash_pgn_vs_fastchess_log": {"log": {"base_s38": 0, "cand_s38": 0}, "match": true, "pgn": {"base_s38": 0, "cand_s38": 0}}, "nps_asymmetry": {"asymmetry": 0.0041, "median_nps": {"base_s38": 1576210.0, "cand_s38": 1569801.0}, "threshold": 0.03}, "tl_pgn_vs_fastchess_log": {"log": {"base_s38": 0, "cand_s38": 0}, "match": true, "pgn": {"base_s38": 0, "cand_s38": 0}}}

Flags: none
