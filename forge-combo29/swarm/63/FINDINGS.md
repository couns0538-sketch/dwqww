# Seat 63 — FINDINGS

Composed repair of the drawn-root defect: seat 12 `two_doors_mate.patch.txt` plus seat 27
`drawn_root_reporting.patch.txt`. Branch `for-fable-and-opus/swarm-63`, base `6b98f217`.

| id | area | finding | evidence | status |
| --- | --- | --- | --- | --- |
| 63-F1 | composition | Both application orders produce one byte-identical `search.cpp`, sha256 `24912a43d315243f2f9dcb0ea032e7160633b99483c0a5e26541e870b2a26671`. Mate-first exit 0/0; report-first exit 0/0 (report hunk lands at line 2275, offset 19). | `job1/compose.sh`, `job1/out/compose_*.txt` | NEW |
| 63-F2 | composition | The warned `-p1` trap is loud, not silent: applying either patch at the wrong strip level exits 1 with `1 out of 1 hunk ignored`, so a skipped hunk cannot pass as applied. | `job1/out/wrong_p.txt` | NEW |
| 63-F3 | honesty | With DEFAULT options the four pins are unmoved by the repair: bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609, on base and patched alike. | `job1/out/honesty_*.txt` | NEW |
| 63-F4 | scan cost | The per-move scan is **not** paid on ordinary searches. Instrumented probe counts: 0 of 5 normal roots ($\ge$14 legal moves) entered the scan; 6 of 6 drawn roots did. The gate is `if (root_draw_adjudicated)`, and `root_draw_adjudicated` is false for every non-drawn root, so the loop is unreachable there. | `job1/scan_cost.json`, counters table in REPORT | NEW |
| 63-F5 | scan cost | When it does run, the scan costs ~220–280 ns per legal move: 42 moves = 9.4 µs (median of 15 runs), 35 moves = 9.9 µs, 20 moves = 4.5 µs. Against a depth-12 search of 20–80 ms that is 0.01–0.05 % of one search, and it is paid only on a root that was going to return in microseconds anyway. | `job1/scan_cost.json` | NEW |
| 63-F6 | correctness | The repair fixes the reported defect. Fixture B (exactly one mate, halfmove 100): base bestmove `b3b1` is **not** a mate; patched bestmove `b3a3` is. Fixture A2 (two mates, halfmove 100): base 0 nodes, patched 288 nodes and plays a mating move. | `job1/out/matrix_*.txt` | NEW |
| 63-F7 | reporting | The depth claim is honest after the patch: every drawn root reports `max depth 1` on the patched build where the base reports `max depth 8` with `nodes 0`. | `job1/out/matrix_*.txt` | NEW |
| 63-F8 | fixtures | Three of my own fixtures were wrong and were caught by assertions, not by luck: a "two mates" board with one, a "stalemate-only" board with a mate, and a "same-colour bishops" board whose bishops sat on opposite complexes (the engine correctly searched it). All fixtures are now found by search and asserted with python-chess before use. | `job1/fixtures.py` | NEW |
| 63-F9 | correctness | The stalemate trap is handled: fixture C has moves that stalemate the bare king and none that mate; the repair's `legal_moves().empty() && in_check()` test correctly declines to cancel the adjudication there. | `job1/out/matrix_*.txt` | NEW |
| 63-F10 | correctness | A mate in 2 at halfmove 100 is correctly left adjudicated (fixture E), so the repair does not over-fire on near-mates. | `job1/out/matrix_*.txt` | NEW |
| 63-F11 | limits | Under the engine's own insufficient-material predicate no mate is possible, so that branch of the repair can never fire. Sampled 110,221 engine-insufficient positions, 0 with a mating move. The branch is dead code, not a bug. | `job1/insuff_sample.py` | NEW |
