# Seat 63 — STATUS

Branch `for-fable-and-opus/swarm-63` · base `6b98f217` · folder `forge-combo29/swarm/63/`

## 2026-11-17T04:30Z

Done, all measured (scripts and raw output in `job1/`):

1. Composition reproduced in BOTH orders -> one identical `search.cpp`,
   sha256 `24912a43d315243f2f9dcb0ea032e7160633b99483c0a5e26541e870b2a26671`.
   Exit codes checked individually: `EXIT_mate=0` / `EXIT_report=0` both ways.
2. Wrong `-p1` level fails loudly (`1 out of 1 hunk ignored`, exit 1), not silently.
3. Four honesty pins, DEFAULT options, base AND patched: 312866 / 862329 / 3024920 / 4865609.
4. Same four pins on ASan+UBSan builds, both base and patched: identical, zero sanitizer lines.
   Instrumentation is not vacuous: `__asan_` 35, `__ubsan_` 15 symbols; a planted heap
   over-read is caught by the same runner (`runtime error:` at the planted line).
5. **Scan cost (item 3), answered by counters, not by reading:** 0 of 5 normal roots entered
   the scan; 6 of 6 drawn roots did. Cost when it runs: ~220–280 ns per legal move, 9.4 us at
   42 moves — 0.01–0.05 % of a single depth-12 search, on a root that returns in microseconds.
6. The repair fixes the defect: at halfmove 100 with a mate available the base reports
   `score cp 0` and plays `b3b1` (not a mate); the patched build reports `score mate 1`
   with `pv b3a3`.
7. Wire contract: 16 observations, no violation. Drawn root: base 8 info lines ending
   `depth 8`, patched 1 line ending `depth 1`; both play the same legal move.
   A normal search after a drawn root in the same session is unaffected (16646 nodes both).

## Next

- Extend the adversarial set with repetition roots built from move lists that DO have a mate.
- Check `stop`/`go infinite` interaction on a drawn root.
- Write REPORT_job1.md and finish the ship/no-ship verdict.
