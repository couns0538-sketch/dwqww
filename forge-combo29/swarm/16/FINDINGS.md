# FINDINGS — seat 16 (area 6, SYMMETRY)

| id | area | one sentence | evidence file with the exact command that shows it again | state |
|---|---|---|---|---|

(no findings yet: job 1 produced a negative result — the static evaluation is colour-symmetric on every G
position and 500 R positions; a negative result is not a finding, it is in `REPORT_job1.md`)

| S-C1 | CONFIRMS S-F2 | check_S-F2/raw/results.json (again: `python3 check_S-F2/check_ep.py ~/builds/bld-release/forge raw`) | seat 06's FEN is refused with `info string invalid FEN: inconsistent en-passant square` (9 of 15 ep FENs refused, all 6 accepted ones match python-chess perft 1); beyond the finding: a second message `invalid en-passant square` (board.cpp:319) exists that the finding's code citation omits, and a refused FEN keeps the previous position |
| S-C2 | CONFIRMS S-F1 | check_S-F1/raw/default.tsv check_S-F1/raw/nonnue.tsv check_S-F1/raw/deadmat.tsv check_S-F1/raw/both.tsv (again: `python3 check_S-F1/check_sym.py ~/builds/bld-release/forge default /tmp/o.tsv check_S-F1/G_353.fens`) | static eval hce/nnue/total colour-symmetric on 25,532 pairs across 4 configurations, 0 differences; beyond the finding: DeadMaterial changes 30/30 dead-material boards but 0/353 game positions, UseNNUE false changes 350/353, and the finding's own 8,103 pair count could not be re-counted from its files |
