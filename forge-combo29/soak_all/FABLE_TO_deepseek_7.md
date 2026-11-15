# Fable to deepseek, file 7 (2026-11-15): answer to job 6, and job 7

## Your job 6 report

Read in full. The controls came first and they hold (reader 0 of 1,650, random mover 121, best mover 0, the planted
fault reported), so the numbers count. You also said plainly what you did not measure (seven classes, A3, B3) and
why. That is the right way round.

**F1 is the finding of the job:** single moves in queen and rook endings are clean (0 of 783, 0 of 906), whole
games at 2,000 nodes are not (146 and 166 of 200 won). So the engine does not blunder; it fails to make progress.
What I check on the PC while you work: the same test with the net the loop really plays with (yours is the
built-in one), with `go softnodes 2000` (the command self-play uses), and what the loop's adjudication does to
such games (it calls a game won at 2,000 centipawns; if the score in these endings stays below that, the game
runs on to a repetition and is labelled a draw, which would teach the net the wrong thing).

Three remarks on the report:
- **"Repetition" needs two counts.** `can_claim_threefold_repetition()` is also true when a legal move WOULD
  bring the third occurrence. A match program ends a game only when the position HAS occurred three times
  (`is_repetition(3)`). From now on count both; the second is what costs a half point in a real game.
- **Your defender was the weak one** (random among moves that keep the result). You said so. Job 7 adds the
  strong one.
- **F3 (pawn endings) at 20,000 nodes is not better than at 2,000.** You call it an evaluation error without
  having tested it. Part B settles it.

## Job 7. BUDGET: 60 minutes; at 50 minutes stop and write. Part A first.

Rules: those of your first message. No engine source change. Folder `forge-combo29/tests_deepseek_job7/`, report
`forge-combo29/REPORT_deepseek_job7.md`, commit subject "deepseek job 7 report". Engine as in job 6 (commit
6b98f217, release build, built-in net, Threads 1, Hash 16; print the three numbers). `ucinewgame` before every
game, none inside a game. Seeds written down. Your retrograde tables are the truth; extend the solver so that it
also gives the DISTANCE TO MATE in plies (queen and rook endings; for pawn endings the result class is enough).

### Part A. Why does the engine not finish won queen and rook endings at 2,000 nodes? (about 40 minutes)
 A0. Controls: the reader and counter controls of job 6 again on the extended tables; and for the distance:
     in 1,000 random won positions a player that always picks a move with the smallest distance must mate in
     exactly the table's number of plies, every time.
 A1. The ladder. 200 won starts each for KQvK and KRvK (the same starts for every cell), the engine on the
     strong side, against (i) your job 6 defender and (ii) the BEST defender (a move with the largest distance to
     mate). Limits: `go nodes` 500, 1000, 2000, 5000, 20000, and `go softnodes 2000` (if `go softnodes` is not
     understood by this build, say so and leave the column out). Per cell: mated; third occurrence reached
     (`is_repetition(3)`); only claimable; 50-move rule; mean and largest number of moves to mate.
 A2. Inside the failed games at `go nodes 2000` with the best defender. For every engine move write: ply, the
     move, the score, the depth reached, the table's distance before and after the move. Then count per game:
     moves that made the distance smaller, kept it, made it larger; the ply at which a position first came back;
     and whether, at that ply, a move with a smaller distance existed. One line per game in a table, and the full
     list of three games as examples.
 A3. Does the engine SEE the mate? In 200 won KQvK positions with distance 9 to 15 plies: how often does
     `go nodes 2000` print a mate score, how often a centipawn score, and what are the smallest, median and
     largest centipawn scores? The same at 20,000 nodes. (The loop ends a game as won at 2,000 centipawns; I need
     to know how often these positions stay below that.)
 A4. The switches. With the 200 KQvK starts, the best defender and `go nodes 2000`: the number of games mated
     with each of these UCI options changed alone from its default (take the names and defaults from the `uci`
     output and print that list): `EvalRule50Damp`, `DeadMaterial`, `QuietExtinction`, `SoundMatePruning`,
     `MateAlphaGuard`, `DrawJitter` (0 and its largest value), `HindsightDepth`, `NullThreatVerify`. An option
     the build does not list is left out and named. One table: option, value, mated of 200.
     Control for A4: the row with nothing changed must repeat A1's number for that cell exactly.

### Part B. The pawn endings (about 15 minutes)
 B1. Your 18 + 5 failures at 2,000 nodes and 20 + 4 at 20,000 (job 6, `logs/A1-all-*.json`): for each one the
     FEN, the engine's move and score, one move that keeps the result, and the result of the same search at
     200,000 nodes and at 2,000,000 nodes. Count how many are repaired at each. If most are repaired by more
     nodes, it is the search horizon; if not, it is the evaluation or a pruning rule, and then say which of the
     A4 options changes the count.
 B2. A file for a cross-check on the PC: `tests_deepseek_job7/kpk_20000.txt`, 20,000 random legal KPvK positions
     (seed written in the report), one per line: the FEN, a semicolon, and W, D or L from the side to move's view
     by your table. I solve the same positions on the PC with a solver of my own and compare; that tests your
     table and mine at once. Also the three totals of your table (won, drawn, lost states) and the exact rule by
     which you count a state.

### What to deliver
`REPORT_deepseek_job7.md` in the usual form, the controls in front. Then: 1. table of parts; 2. the A1 ladder
(two tables, one per defender); 3. the A2 table and the three example games; 4. A3; 5. the A4 table; 6. part B;
7. findings with a test we can re-run; 8. suspicions, not proven; 9. files opened; 10. times from stamps;
11. what you did not do; 12. what you are not sure about; 13. a better way.

One sentence at the very top of the report, in plain words: what, by your measurements, is the main reason the
engine does not finish these endings at 2,000 nodes, or "not established" if the measurements do not say.
