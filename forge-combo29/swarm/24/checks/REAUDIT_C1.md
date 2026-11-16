## 2026-11-16T21:47Z — re-audit of my C1 under the seat-19 integrity rule

Seat 19 warned that a checker which greps engine output can print CONFIRMS without measuring anything (a missing
line -> NaN/None -> a truthy comparison).  My only check that parses engine output is 24-C1 (CONFIRMS seat 02
S-F2), so I re-audited it and it FAILED its own control twice before it was right.  Recorded honestly:

1. First hardening: I added assertions that every case ran, every board had a positive python-chess legal-move
   count, and every searchmoves case contained the quoted info string.  A missing case or line now prints
   INCONCLUSIVE and exits 2.
2. My negative control (control_02f2_missing_line.py) builds a scratch copy of the engine with the printed
   sentence replaced by an unrelated one and runs the same checker on it.  Attempt 1: the control refused to doctor
   because the printed line is in src/search.cpp, not src/uci.cpp (I had guessed the file).  Attempt 2: the
   doctored string `XXsearchmoves restriction ...` still contained the substring `searchmoves`, so the checker
   confirmed on an engine that never printed the sentence — the control caught a real hole in my own assertion.
   Attempt 3: the checker now matches the whole sentence `searchmoves restriction has no legal root moves` and the
   doctor replaces the whole sentence; the doctored build gives INCONCLUSIVE (exit 2) and the real build CONFIRMS.
3. Result: control PASS.  The recorded 24-C1 conclusion is unchanged (the real run still shows the line in all
   five searchmoves cases), but the check now cannot confirm without it.

Files: checks/check_02f2.py (hardened), checks/control_02f2_missing_line.py (the control), checks/stamps.txt.
