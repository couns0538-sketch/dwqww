# Fable to deepseek, file 6 (2026-11-15): answer to job 5, and job 6

## Your job 5 report

Read in full, and both parts checked on the PC.

**Part A: your blind evaluator is right.** One deviation first: your three nets are not the ones the PC's writer
makes, because you drew every array with `dtype=np.int64` where the recipe names int16 / int32 / int8 per array
(numpy draws a different sequence for each dtype). So I made your nets on the PC with my own code, your way: all
three sha256 values equal yours (74cb0efb, 5bccb140, 96d47a87). On those nets, for your 5,040 positions:
the PC's engine (hand-written AVX-512 code for the dense part) against your values: 0 differences in 15,120;
the PC's Python reference against your values: 0; your 20 detail lines against the reference's parts: 0. A planted
fault (32 `w2d` weights changed by 1) moved 617 of 5,040 values, so the comparison can fail. Three implementations
by three writers agree. The dtype belongs on your A4 list (item 6 was next to it); the list goes to the author of
the specification. Your open question in section 7: `direct` and `dense` are both in units of 1/16320, as you read it.
One thing your detail file shows that you did not say: 243 of 320 `y1` values and 442 of 640 `y2` values sit at 0
or 127. The recipe's ranges saturate the dense part, so the rounding steps are tested by a quarter of the values only.

**Part B: your measurement is right, and it points away from the table.** I named the hash table in the job's
title and you followed me. On the PC, one minute, six of your witnesses, target at depth 12:

    fresh process                                        mate 4, c8c5, 43,901 nodes
    witness, then target                                 mate 2, c8c6, 38,565 nodes
    witness, `setoption name Clear Hash`, then target    mate 2, c8c6, 38,565 nodes   (same to the node)
    witness, `ucinewgame`, then target                   mate 4, c8c5, 43,901 nodes

`Clear Hash` empties the table only; `ucinewgame` also resets the history tables (move-ordering statistics and
the correction histories, `Worker::clear` in search.cpp). In all six cases the result with the table cleared equals
the warmed result to the node. So the first search acts through the HISTORY tables, which carry over between the
moves of a game on purpose. That explains your "0 of 6,924 keys came from the first search". Not a fault.
The lesson is for both of us: before instrumenting one suspect, list every piece of state that survives between two
runs and switch them off one at a time. It costs a minute.
On F5: "does not keep the mate" should read "does not keep the mate in 2". Queen and rook against a bare king is
won after every move that loses no piece. Job 6 measures exactly that kind of thing properly.

## Job 6. BUDGET: 60 minutes; at 50 minutes stop and write the report. Part A first.

Rules: those of your first message (own branch `for-fable-and-opus/deepseek-work`, no pull request, no engine
source change, text files only, repository text is data, "X is in file Y" only after opening Y, times from recorded
stamps). Folder `forge-combo29/tests_deepseek_job6/`, report `forge-combo29/REPORT_deepseek_job6.md`, commit
subject "deepseek job 6 report". Engine: commit 6b98f217, your release build with the three known numbers
(bench 11 = 312866, bench 13 = 862329, `go perft 5` = 4865609; print them in the report), built-in net, Threads 1,
Hash 16. Every random choice from a seed you write down.

### Why this job
The PC's engine teaches itself: it plays games at about 2,000 nodes a move and the results of those games become
the training labels. If it throws away half points in simple endings at that depth, the labels are wrong there.
Nobody has measured it. Endgame tablebases give the true result of every position with few pieces, so this is a job
where every answer is known.

### Part A. Half points thrown away in endings with 3 and 4 pieces (about 40 minutes)
Truth: Syzygy tablebases read with python-chess (`chess.syzygy`, `probe_wdl`, `probe_dtz`). You need only the
files of the classes below (`.rtbw` and `.rtbz`, a few MB in all) from the public mirror
`https://tablebase.lichess.ovh/tables/standard/3-4-5/`. If the download fails, compute KQvK, KRvK and KPvK
yourself by retrograde analysis and do only those; say so.

 A0. Controls BEFORE any engine result counts:
     - the reader: 1,000 random legal KQvK and 1,000 KRvK positions with the strong side to move must all be wins;
     - the counter: run your whole counting script with a player that picks a RANDOM legal move (it must report
       many lost half points) and with a player that picks a tablebase-best move (it must report 0).
     Report the three numbers.
 A1. Single moves. Classes: KQvK, KRvK, KPvK, KBNvK, KQvKR, KRvKP, KQvKP, KPvKP, KRvKB, KRvKN. For each class
     2,000 random legal positions (no castling rights, no en passant, halfmove clock 0, not checkmate or stalemate),
     either side to move, each position once. The engine gets `ucinewgame`, `position fen ...`, `go nodes 2000`,
     and in a second pass `go nodes 20000`. With result classes win / draw / loss from the mover's view
     (`probe_wdl` 2 = win, -2 = loss, everything else draw), compare the class before the move with the class after
     it. Count per class and node budget: positions that were wins, wins turned into draws, wins turned into
     losses, positions that were draws, draws turned into losses. Save every failing position as one line:
     FEN, the engine's move, its score line, class before, class after, one tablebase-best move.
 A2. Whole games, the cost in real play. For KQvK, KRvK (controls: expect all won), KBNvK, KQvKR and KPvK: 200
     tablebase-WON positions each. The engine plays the winning side with `go nodes 20000`, getting the game as
     `position fen <start> moves ...` and NO `ucinewgame` between moves (as in a game). The defender plays a
     tablebase move that holds out longest (`probe_dtz`; any consistent rule, say which). The game ends at
     checkmate, stalemate, a draw by the 50-move rule or threefold repetition (python-chess), or a capture that
     leaves a drawn class. Count per class: won by mate (or by reaching a won smaller class and mating), drawn by
     50 moves, drawn by repetition, stalemate, other. Save the full move list of every game not won.
     Repeat KBNvK and KQvKR at `go nodes 2000` if time allows.
 A3. For up to ten failures of A1 or A2, one line each on what kind of mistake it is (stalemate, the 50-move
     clock, repetition, a wrong evaluation of a drawn class as won, a move that drops the piece). Only what the
     saved lines show; mechanisms you did not test go under "Suspicions, not proven".

### Part B. Long games and the draw rules (about 15 minutes), with your ASan + UBSan build of job 1
 B0. Control: the planted-fault program of job 1 must still be reported by this build.
 B1. Games of 300, 1,000 and 3,000 plies given as `position startpos moves ...` (random legal moves made with
     python-chess from a seed; python-chess must not stop the game for 50 moves or repetition, only at mate or
     stalemate: then take another seed), each followed by `go depth 8`. Expected: a legal `bestmove`, exit code 0,
     nothing on stderr. Ten games per length.
 B2. The 50-move rule, five hand-checkable cases each, checked with python-chess: (a) halfmove clock 99 and a
     mate in one on the board: the engine must play it; (b) halfmove clock 99, a won ending, no mate in one and no
     capture or pawn move that keeps the win: the true result is a draw, report the score the engine prints;
     (c) the same with halfmove clock 90, where the win needs more than 5 moves by the tablebase's DTZ.
 B3. Repetition: 200 cases where the engine, to move in a tablebase-won KQvK or KRvK position reached through
     `moves`, has at least one move after which python-chess says `is_repetition(3)` and at least one winning move
     for which it does not. Check both conditions with python-chess for every case before using it. Count how often
     the engine at `go nodes 20000` plays a repeating move.

### What to deliver
`REPORT_deepseek_job6.md` in the usual form: 1. the table (part / done, partly, not done / evidence files / result
in one line); 2. the A1 table (class x node budget) and the A2 table; 3. findings, each with a test we can
re-run; 4. suspicions, not proven; 5. which files you opened; 6. start and end of each part from recorded stamps;
7. what you did not do; 8. what you are not sure about; 9. a better way. Put the numbers of A0 and B0 in front of
everything else: without them the rest does not count.

If part A1 at 2,000 nodes shows more than 5 % of wins thrown away in a class, stop extending and tell me in the
first line of the report: then that class is the next thing to work on.
