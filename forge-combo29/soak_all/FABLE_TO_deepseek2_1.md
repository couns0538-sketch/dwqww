# Fable to deepseek2, file 1 (2026-11-15): job 1

Step 0 of this job is the honesty check every helper passes first: three numbers that I know. Everything after it
counts only if they are right.

## Job 1. BUDGET: 60 minutes; at 50 minutes stop and write the report with what you have.

### The question
A reviewer started on this and broke off: **can a result stored in the engine's hash table hide a draw?** A stored
score belongs to a position, not to the game that led to it. Two cases matter in real games:
- a move brings a position for the THIRD time (a draw at once), but the table still holds "this position is lost"
  from an earlier search in the same game, when it was not yet a repetition;
- the table holds "mate in N" from earlier in the game, but the 50-move clock no longer leaves room for N.
If the engine trusts the stored score in such a case it throws away a half point. I have read the code and believe
the first level is guarded. Your job is to read it yourself, say exactly what is guarded and what is not, and then
TEST it with cases whose right answer is known by construction.

### What to fetch and build
Commit `6b98f217` (tip of `for-fable-and-opus/astra-0017-v3-path`), folder `forge-combo29`. Release build with CMake
and g++ (GCC 13 or newer, GCC's own C++ library); on a machine without AVX-512 or BMI2 add
`-DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3`. Built-in net, `Threads 1`, `Hash 16` unless a step says otherwise.

### Step 0. The known numbers (raw output as a file)
    bench 11   -> nodes 312866
    bench 13   -> nodes 862329
    go perft 5 -> nodes 4865609     (from the start position)
If one differs: stop and report that; nothing else counts.

### Part A. Read (about 15 minutes). `forge-combo29/src/search.cpp`, with line numbers of commit 6b98f217
For the main search function and for the quiescence search, each: (1) the line where a node is tested for a draw
(repetition, 50-move clock, material); (2) the line where the hash table is probed; (3) the conditions under which
a stored score ends the node (a cutoff), and every condition that involves the 50-move clock or a mate score;
(4) the same three for the ROOT (how the root treats a root move that leads to a repeated position). Then say in
one paragraph: in which order do (1) and (2) happen, and which situations does that order protect, and which not
(think of a repetition that lies two or more plies below the node whose stored score is used).
Quote at most three lines of code per point; cite the rest by line number. I compare your answer with my own notes.

### Part B. Test: the third occurrence against a stored loss (about 30 minutes)
Build the cases mechanically with python-chess; every property is checked by python-chess before a case is used.

 A case is a start position S0 (king and queen, or king and rook, against a bare king; the strong side to move)
 and a move list, made like this: the strong side has a reversible move a and its return a', the bare king a
 reversible move k and its return k'. Play  a k a' k'  (S0 has now occurred twice),  a k a' : the position C
 after a' has now occurred twice and the BARE KING is to move. Its move k' would bring S0 for the third time.
 Requirements, each checked: every move in the list is legal; no position in the list is mate or stalemate;
 after k', `is_repetition(3)` is true; after every OTHER legal move of the bare king at C it is false; the bare
 king is not in check at C if that leaves only one legal move (then there is nothing to choose).
 So at C the bare king has exactly one move that draws at once; every other move leaves it in a lost ending.

 B0. Controls. (i) For 20 cases print the list and the python-chess checks. (ii) A player that picks a random legal
     move at C: how often does it pick k' (expected: about one in the number of legal moves). (iii) A planted
     fault: cases built with one cycle less (S0 occurred only once more) must be REJECTED by your own checks.
 B1. Fresh. 500 cases. For each: a new engine process, `position fen <S0> moves <list>`, `go depth 12`.
     Count: bestmove is k'; the score printed (expect 0 or the engine's draw score); anything else, with the
     full output saved.
 B2. Warmed, the way a game does it. The same 500 cases, ONE engine process per case and NO `ucinewgame` inside
     it: walk through the list from S0, and at EVERY position where the bare king is to move send
     `position fen <S0> moves <list so far>` and `go depth 12`, read the bestmove, but then continue with the
     list's move whatever the engine answered. At C: the same search. Count as in B1. This fills the table with
     the engine's own "lost" scores for these positions before the third occurrence is on offer.
 B3. The same as B2 with `go nodes 2000`, `go nodes 20000` and `go depth 20`, and with `Hash 1`.
 B4. Every case where B1 plays k' and a warmed run does not is a FINDING: give S0, the list, both outputs, and the
     smallest change that makes the difference go away (a `setoption name Clear Hash` before the last search? a
     `ucinewgame`? a different depth?). If there is no such case, say so with the counts.

### Part C. Only if time is left: a stored mate against the 50-move clock
 Find 100 positions (queen against bare king, the strong side to move) where the shortest mate takes exactly 3
 moves (5 plies), by brute force with python-chess, and check 10 of them by hand listing. For each, in ONE engine
 process without `ucinewgame`: first `position fen <the position with halfmove clock 0>` and `go depth 12` (the
 table now holds the mate), then `position fen <the same position with halfmove clock 97>` and `go depth 12`.
 With clock 97 only three plies remain before the draw, so no mate can be completed: the right score is a draw
 score and no move can be "mate in 3". Count: a mate score printed (a finding), a draw score, anything else.
 Control: with halfmove clock 90 the mate fits and must be found.

### The report, forge-combo29/REPORT_deepseek2_job1.md
 1. First line, in plain words: can a stored result hide a draw in this engine, by your tests? Yes with the case,
    no with the counts, or "not established".
 2. Step 0, expected against printed.
 3. Part A, the line numbers and the paragraph.
 4. B0 controls; one table for B1 to B3 (rows: fresh, warmed depth 12, nodes 2000, nodes 20000, depth 20, Hash 1;
    columns: cases, played k', did not, engine errors).
 5. B4 findings, each with a test we can re-run; or "none".
 6. Part C, or "not done".
 7. Suspicions, not proven: file and line, what you suspect, the test that would settle it.
 8. Which files of the repository you opened.
 9. Start and end of each part from recorded stamps (write a stamp file at each part).
10. What you did not do.  11. What you are not sure about.  12. A better way (may be empty).
13. Your model name and version as you know it.
