# FINDINGS — swarm seat 28 (area 8, THE CLOCK)

One line per finding, only ever ADDED.

| id | area | one sentence | file with the exact command that shows it again | status |
|---|---|---|---|---|
| S-F1 | 8 | `go movetime M` stops at M-10 ms: the default `Move Overhead 10` is subtracted from the movetime limit (src/search.cpp:2192, src/uci.cpp:152), so `go movetime 10` searches 1 ms and `go movetime 50` stops at 40.5 ms. | forge-combo29/swarm/28/job1/tiny_movetime.py + tiny_movetime_out.txt | NEW |
| S-F2 | 8 | On a 1 s clock with 10 ms increment, 82 of 200 searches (41 %) run past `wtime/30+winc`; largest 201 ms, still inside the engine's own 260 ms hard limit. | forge-combo29/swarm/28/job1/table1.py + table1_out.txt | NEW |
| S-F3 | 8 | movetime-50 wall time is reproducible to 0.05 ms between two independent 200-search runs on this 4-core box, so a >1 % timing change is measurable without repetition. | forge-combo29/swarm/28/job1/outA/mt50.txt vs outB/mt50.txt | NEW |
| S-C1 | CONFIRMS S01-F5 | forge-combo29/swarm/28/checks/CHECK_s01f5.md + check_s01f5_out.txt (again: `python3 check_s01f5.py ~/build/base-release/forge /tmp/o.tsv`) | on my own mate-in-one board the engine gives 126 nodes / `mate 1` / `a1a8` at halfmove 99 and 0 nodes / `cp 0` / `f2f3` at halfmove 100, byte-for-byte seat 01's numbers; controls: hm99 finds the mate (harness can see one) and a quiet board also goes 781 -> 0 nodes at hm100 (so the short circuit skips ALL search, not just mates). |
| S-F4 | 8 | The same 0-node root adjudication also fires on `board.is_repetition()` (src/search.cpp:2250-2252): a mate-in-one board reached a third time by legal moves answers `f2f3`/`cp 0`/0 nodes where the identical board given by `position fen` answers `a1a8`/`mate 1`/126 — so seat 01's patch, which removes only the halfmove term, leaves this door open. | forge-combo29/swarm/28/checks/repetition_root.py + repetition_root_out.txt | NEW |
