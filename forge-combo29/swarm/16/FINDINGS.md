# FINDINGS — seat 16 (area 6, SYMMETRY)

| id | area | one sentence | evidence file with the exact command that shows it again | state |
|---|---|---|---|---|

(no findings yet: job 1 produced a negative result — the static evaluation is colour-symmetric on every G
position and 500 R positions; a negative result is not a finding, it is in `REPORT_job1.md`)

| S-C1 | CONFIRMS S-F2 | check_S-F2/raw/results.json (again: `python3 check_S-F2/check_ep.py ~/builds/bld-release/forge raw`) | seat 06's FEN is refused with `info string invalid FEN: inconsistent en-passant square` (9 of 15 ep FENs refused, all 6 accepted ones match python-chess perft 1); beyond the finding: a second message `invalid en-passant square` (board.cpp:319) exists that the finding's code citation omits, and a refused FEN keeps the previous position |
