# FINDINGS - seat 17 (area 7, reading the code for faults)

One line per finding, only ever added. A check of another seat's finding is its own line.

| id | area | one sentence | file with the exact command | state |
|---|---|---|---|---|
| S-F1 | 7 | `go depth N searchmoves <name with no legal root move>` answers `bestmove 0000` on a position that HAS legal moves (startpos: 20 legal, 0000 returned) - UCI defines 0000 as "no legal move exists", so a GUI reads it as an illegal move | `forge-combo29/swarm/17/job1/finding_searchmoves.py` (run: `cd forge-combo29/swarm/17/job1 && python3 finding_searchmoves.py /agent/repos/base/forge-combo29/build/forge sm`) | NEW |
| S-F2 | 7 | source of S-F1: `src/search.cpp:2640` `if (result.best_move.is_none()) result.best_move = root_candidates.front();` reads `front()` of an EMPTY MoveList when `root_candidates` is empty but legal moves exist (line 2210 already detects exactly this state as `restricted_root_empty`) | `sed -n '2202,2211p;2253,2266p;2636,2641p' src/search.cpp` in a 6b98f217 worktree | NEW |
