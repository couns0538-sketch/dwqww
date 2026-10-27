# IDEA_SOURCE (S38, opus 2026-10-27)
- Spec: Sol inventory `jobs[S38].spec_verbatim` (branch 17aa0cae).
- Formats: fastchess 1.8.2 output as found in the PC gate files (PGN timeleft comments, stdout log, `-log engine=true`
  lines) and the termination strings inside fastchess.exe (read only). Time model: the AL1 lock time manager in
  src/search.cpp (TmSoftDivisor 22, TmIncrementPercent 75, TmHardPercent 60, TmHardSoftMultiple 5, Move Overhead 10).
- Cross-check sources: forge_queue.ps1 RESULT.md (avg PGN depth, time losses, crashes, Warning; lines) and
  gate_results.ps1 GATE_RESULTS.csv (lock archive 7_history/gate_results).
- Own code; no third-party code. No engine option, no gate, no Elo or speed claim.
