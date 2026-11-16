# PREDICTION — job1 (area 1: 20,000 mutated FENs under ASan+UBSan)

Committed and pushed ALONE before the first measuring command of job 1. Never edited afterwards.

Kill ranges are the numbers that make this prediction WRONG.

1. Refusals: I predict 60–85 % of the 20,000 mutated FENs are REFUSED by `set_fen`
   (most mutations break the six-field/trailing rule or the rank-sum rule).
   KILLED IF: refusal rate < 40 % or > 92 %.

2. python-chess agreement among ACCEPTED FENs: I predict at least 97 % of the
   accepted FENs are also accepted AND parse as a legal-looking board by python-chess
   (`Board(fen)` raises nothing).
   KILLED IF: the agreement rate is below 90 %.

3. The count of "accepted and python-chess INVALID" will be > 0 (the brief already
   names two such classes: impossible castling and triple check).
   KILLED IF: the count is exactly 0.

4. Crashes: 0 engine process crashes over the 20,000 mutated FENs.
   KILLED IF: any crash.

5. Sanitizer lines: 0 sanitizer lines from the real ASan+UBSan build, PROVIDED proof 2
   is shown (the planted build through the same runner must count its line).
   KILLED IF: any sanitizer line, or if proof 2 does not fire.

6. Illegal bestmoves after an accepted position: 0 (a `go depth 2` bestmove that
   python-chess rejects in that position).
   KILLED IF: any illegal bestmove.

7. The 3,000-character first-field control is refused, no crash.
   KILLED IF: accepted, or a crash.

8. Wall time: the 20,000 cases finish in under 40 minutes on 4 cores.
   KILLED IF: over 80 minutes.
