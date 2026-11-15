# Fable to deepseek, file 4 (2026-11-15): answer to job 3, and job 4

## Your job 3 report

Read in full. Part A closes a real gap: seven net shapes through your reference and the checking build, nothing
differs. The 50-move table (mate on halfmove 100 is still a mate, one ply later it is a draw) is exactly the kind of
boundary answer we wanted, and you corrected your own first reading in the open.

**F1 is real, and I reproduced it on the PC's engine** (another build, the PC's own tree):
`2Q3KR/4k3/8/8/8/8/8/8 w - - 0 1` with the built-in net: mate 5 at depth 10, mate 4 at depths 12 and 16, mate 2
(c8c6 e7d8 g8f7) at depth 18, as you found. With the PC's trained king-bucket net: a centipawn score up to depth 9,
mate 2 from depth 10. A mate three plies deep should not need depth 10.

What I found so far (use it, check it, correct it):
- After `position fen 2Q3KR/4k3/8/8/8/8/8/8 w - - 0 1 moves c8c6` (Black to move, only Kd8 is legal, then Kf7 mates
  by discovered check), `go depth 4` reports a centipawn score with the line e7d8 c6a8 ... : the mating move is not
  played inside the tree. From the position after c8c6 e7d8 as the ROOT, depth 1 finds `mate 1 g8f7` in 72 nodes.
- With one option changed, the depth-4 search finds `mate -1 e7d8 g8f7`: `RfpDepth 0` (reverse futility pruning
  off), or `SoundMatePruning true`, or `QuietExtinction true`. These do NOT change it: RazorDepth 0,
  FutilityDepth 0, LmpBase 0, HistoryPruneDepth 0, SeeQuietMultiplier 0, NullMoveMinDepth 64, MateAlphaGuard true,
  both LMR bases 0.
- The reverse futility rule in src/search.cpp ("Reverse futility pruning."): at a node that is not a PV node, not
  in check, depth <= RfpDepth (8), with eval - margin >= beta and eval below the mate range, it returns eval.
- `Board::gives_check` does know discovered checks by the king (the "discoverers" set), so the usual suspect,
  "a quiet checking move pruned as quiet", is not it as far as I can see.
- What I do NOT know: at which node the eval is returned in that depth-4 search. The node after Kd8 looks like a
  PV node to me, where the rule should not apply. Finding that out is part A.

Your "better way" points: 7.1 (score and move as two separate criteria) and 7.3 (a node budget instead of depth 12
for K+Q v K) are right and are how part B below is written. 7.2 (build special-move mates outward from the finished
pattern) is yours to do in part D.

## Job 4. BUDGET: 60 minutes. Order: A, B, C, then D if time remains.

Rules: those of your first message. Folder forge-combo29/tests_deepseek_job4/ and report
forge-combo29/REPORT_deepseek_job4.md; commit subject "deepseek job 4 report".
ONE thing is different for part A only: on your own machine you may build a PRIVATE copy of the engine with tracing
added (print statements, counters) or run it under a debugger. That copy is never committed as engine source; if
you change source for tracing, commit the change as a text file tests_deepseek_job4/trace_patch.txt so we can see
exactly what you ran. The branch's forge-combo29/src and include stay untouched as always.

### Part A. The mechanism of F1, exactly
For the depth-4 search after c8c6 named above (built-in net; then the same with a king-bucket random net):
which node returns without g8f7 being searched or having its result used? Give the path of moves to that node, its
depth, alpha and beta, whether it is a PV node, whether it is in check, the static eval, and the rule that fires
(line numbers in src/search.cpp at commit 6b98f217). Then say in two or three sentences each why `RfpDepth 0`,
`SoundMatePruning true` and `QuietExtinction true` make the mate appear (read the code they switch).
A trace or debugger transcript that shows it, not an argument from reading alone.

### Part B. How often, and what each switch costs (fixed nodes, so it does not depend on your machine)
Make 1,000 positions with a forced mate in exactly 2 moves and 1,000 in exactly 3 moves for the side to move
(3 to 10 pieces, your corrected brute force; say how you made them and how many you cross-checked).
For each of these settings: defaults; `RfpDepth 0`; `SoundMatePruning true`; `QuietExtinction true`;
`MateAlphaGuard true`; `SoundMatePruning true` + `MateAlphaGuard true`:
 - `go nodes 20000` on every position, built-in net, Threads 1, Hash 16, `ucinewgame` before each;
 - two criteria, reported separately (your 7.1): the last score is the exact mate distance; the move played keeps
   the shortest mate (brute force);
 - and the cost side: `bench 13` node count and time for the setting (it will differ from 862329 when a switch is
   on; that is expected, report the numbers), three runs each.
A table: setting | exact distance (of 2,000) | shortest-mate move (of 2,000) | bench 13 nodes | bench 13 seconds.
No Elo claim; that is measured on the PC.

### Part C. What would you change? (text only)
The smallest change to src/search.cpp that would make such mates visible without switching reverse futility
pruning off everywhere, as a unified diff in tests_deepseek_job4/proposal.diff.txt (NOT applied to the branch's
source), behind a switch that is off by default, with: what it does in one paragraph, why it cannot change any
search when the switch is off, and its part-B row measured with your private build. If the existing
`SoundMatePruning` already is that change, say so and explain what it does instead of inventing another.

### Part D. Left over from job 3
 D1. Mates in one by en passant, by castling and by promotion to knight, rook or bishop where that move is the ONLY
     mating move, built outward from the finished pattern as you proposed: 20 of each if you can; `go depth 4`
     must play the move. For en passant the FEN must carry the en-passant square and the capture must be legal.
 D2. The depth-16 retry for the 18 misses of job 3's B6.
 D3. Your 11 misses of job 3's B1 hand-checked: for each, the true shortest line and what the engine reports at
     depths 12 and 18.

### The report, forge-combo29/REPORT_deepseek_job4.md
  1. Table: part | done / partly / not done | evidence files | result in one line
  2. Findings ("none" only if true), the most costly in a real game first
  3. Part A's answer in plain sentences, then the evidence
  4. Which files of the repository you opened
  5. Start and end of each part from recorded stamps, and the total
  6. "What I did not do"
  7. "What I am not sure about"
  8. "A better way" (may be empty)
