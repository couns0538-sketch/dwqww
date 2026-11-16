# PREDICTION — job3 (area 1: `position startpos moves` long lists + one illegal move)

Committed and pushed ALONE before the first measuring command of job 3. Never edited.

The brief's known line: "an illegal move keeps the legal prefix (perft 1 = 29 after
e2e4 e7e5 e1e3)".

1. A 1,000-ply legal move list is ACCEPTED whole (no `illegal move` line), and
   `go perft 1` equals python-chess's legal-move count at that final position.
   KILLED IF: a refusal appears, or the counts differ.

2. An illegal move at ply 1 / 10 / 500 is reported with `info string illegal move <token>`
   and the engine keeps exactly the LEGAL PREFIX before it: `go perft 1` equals the legal
   count at that prefix (not the start position, not the final position).
   KILLED IF: any of the three keeps a different position than the prefix.

3. The three refusal points give three DIFFERENT positions (prefixes of length 0, 9, 499
   plies), so three different perft-1 counts.
   KILLED IF: two of them coincide.

4. The brief's known case: after `e2e4 e7e5 e1e3`, perft 1 = 29.
   KILLED IF: not 29.

5. Zero crashes and zero sanitizer lines under ASan+UBSan over the whole job.
   KILLED IF: any crash or sanitizer line.

6. An illegal move placed at the END of an otherwise legal 1,000-ply list keeps the
   999-ply prefix, so perft 1 equals the count at 999 plies, not at 1,000.
   KILLED IF: the count equals the 1,000-ply position's.

7. A move token that is not valid UCI at all (e.g. `zzzz`) is treated like a legal-but-
   illegal move (reported, prefix kept) rather than crashing or being ignored silently.
   KILLED IF: no answer line for it, or a crash.
