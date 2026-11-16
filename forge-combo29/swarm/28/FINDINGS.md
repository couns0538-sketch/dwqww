# FINDINGS — swarm seat 28 (area 8, THE CLOCK)

One line per finding, only ever ADDED.

| id | area | one sentence | file with the exact command that shows it again | status |
|---|---|---|---|---|
| S-F1 | 8 | `go movetime M` stops at M-10 ms: the default `Move Overhead 10` is subtracted from the movetime limit (src/search.cpp:2192, src/uci.cpp:152), so `go movetime 10` searches 1 ms and `go movetime 50` stops at 40.5 ms. | forge-combo29/swarm/28/job1/tiny_movetime.py + tiny_movetime_out.txt | NEW |
| S-F2 | 8 | On a 1 s clock with 10 ms increment, 82 of 200 searches (41 %) run past `wtime/30+winc`; largest 201 ms, still inside the engine's own 260 ms hard limit. | forge-combo29/swarm/28/job1/table1.py + table1_out.txt | NEW |
| S-F3 | 8 | movetime-50 wall time is reproducible to 0.05 ms between two independent 200-search runs on this 4-core box, so a >1 % timing change is measurable without repetition. | forge-combo29/swarm/28/job1/outA/mt50.txt vs outB/mt50.txt | NEW |
