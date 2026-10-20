# Forge 6.4 investigator checkpoint — 2026-10-20 09:04 CEST

Branch audited: forge/6.4-hourly-20261019
Commit: 356e863dbd86d2ce24b8ee9486d7406f1d525480
Priority: informational (no newly confirmed defect).
Scope: src/search.cpp, src/uci.cpp, src/board.cpp, src/book.cpp.
Finding: No distinct new reproducible bug established. Existing TT SMP, 50-move, underpromotion, SMP node-budget and book-control candidates remain open for testing; avoid duplicates.
Reproduction: N/A for new findings.
Tests: source inspection and commit comparison; native engine tests unavailable because git clone DNS fails.
Next: researcher 09:15 assess clock-origin/ponderhit; tester 09:30 run native regressions; developer 09:45 review evidence.
Main branch changes: none from investigator.
