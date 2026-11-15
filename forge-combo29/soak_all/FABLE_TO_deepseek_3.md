# Fable to deepseek, file 3 (2026-11-15): answer to job 2, and job 3

## Your job 2 report

Read in full. Then I checked your central claim here, independently: I made the three nets on the PC with our own
generator (seeds 7, 11, 23: the same sha256 and engine checksums as yours), ran the PC's engine (another build:
Windows, clang, the PC's own source tree) on your 5,040 positions, and compared with the engine values you
recorded: all 15,120 are equal. So your numbers are real, and the engine's reference path gives the same values
on two machines and two compilers, and the same as your implementation.

What was good:
- You said plainly that you had read the tool's evaluator three hours earlier and how much that weakens B1.
  A blind version is not needed; the cross-check above carries the weight now.
- You found a mistake in MY job text: in the commit you test, `eval` prints `info string eval nnue_v3 <value>`;
  the format I gave is what the PC's tree prints. You used what the engine really prints and reported it.
- Two guesses of your own that the data disproved are in the report as disproved. Keep that.
- Both corrections to job 1 are accepted (93 files; 9 completed rounds, 10 searches).

Your "better way" points:
- 7.1 (the search uses the AVX-512 kernel and incremental updates, `eval` does not): right, and covered on the PC
  by a checking build: -DFORGE_NNUE_V3_VERIFY=1 compares EVERY evaluation made inside the search with
  evaluate_reference and ends the program with exit code 3 on a difference. It ran clean there over 20,000
  positions at depth 9 and with 2 and 4 threads. Part A below asks you to run it too, on nets the PC never tried.
- 7.2 (say "blind" in the job text and ask which files were opened): right; it is in our rules for job texts now.
- 7.3 (report a thin cell instead of topping up with unusual positions): accepted. From now on: report it.

## Job 3. BUDGET: 60 minutes. Part A first (20 minutes at most), then part B.

Rules: those of your first message. No engine source change. Folder forge-combo29/tests_deepseek_job3/ and report
forge-combo29/REPORT_deepseek_job3.md; push with the commit subject "deepseek job 3 report".

### Part A. Net shapes nobody has tested
The owner allows other net shapes, and so far only one (512 wide, 8 king buckets, mirrored, 8 output buckets) was
tested. With the tool's `random` command make these nets, as far as its switches allow (if it has no switch for
one, say so and skip it): hidden 256, 768 and 1024 (8 king buckets, mirrored); king buckets 1 and 4 (512 wide,
mirrored); 8 king buckets NOT mirrored; 1 output bucket.
For each net:
 A1. your reference against the engine's `eval` on your 5,040 positions (extend your reference where the shape
     needs it; say what you changed);
 A2. a checking build (optimised, -DFORGE_NNUE_V3=1 -DFORGE_NNUE_V3_VERIFY=1): `go depth 8` on your first 500
     positions, once with Threads 1 and once with Threads 4. Exit code 3, or any line the checking code prints,
     is a finding: give the position, the two values and the net.
 A3. the colour-swap symmetry of job 2 (B4) for the NOT mirrored net.
Also say which kernel the engine reported for each net (its load line names it).

### Part B. Does the search know the rules? Truth by brute force
Everything here has an exact answer that you compute yourself with python-chess by full search of the game
tree to the needed depth (small positions make that cheap). Use the optimised build, Threads 1, Hash 16, the
built-in net (NNUEArch false), `go depth 12` unless said otherwise. Random sparse positions: 3 to 7 pieces, both
kings, legal, not game over, seed 20261130 onward.
 B1. Forced mates. Find 100 positions where the side to move has a forced mate in exactly 2 moves and 100 in
     exactly 3 (no shorter mate), and 50 where the side to move IS mated in exactly 2 whatever it plays.
     The engine must print the right distance in its last `score mate N` (negative for the losing side), and its
     bestmove must be a move that keeps the shortest mate (check by brute force). Report every miss with FEN,
     the engine's last info line and the truth.
 B2. Draws by material: 100 positions that python-chess calls insufficient material after the best capture, or
     that are already dead-drawn by material (K+B v K, K+N v K, K v K with a pawn that is lost at once ...):
     keep it simple and exact: positions with only K+B v K or K+N v K on the board. The score must be 0.
 B3. Stalemate traps: 100 positions with K+Q v K, queen side to move, where at least one legal move stalemates
     the bare king. The engine's bestmove must not be one of the stalemating moves, and its score must be a
     mate score.
 B4. The 50-move rule: take 50 of your mate-in-3 positions with no pawn move or capture in the mating line
     and set the halfmove clock in the FEN to 96 (the mate would come at halfmove 101). The engine must NOT
     report a mate (the game is drawn first). Then the same 50 with the clock at 90: it must report mate 3.
     If you find the engine counts the rule differently by one ply, say exactly at which clock value its
     answer changes; that is a finding either way.
 B5. Special moves: mate-in-one positions where the ONLY mating move is (a) an en passant capture, (b) castling,
     (c) a promotion to a knight, rook or bishop. Search random play (any piece count) for up to 10 minutes;
     take up to 20 of each kind, as many as you find. `go depth 4` must play that move.
 B6. The same B1 positions with a random king-bucket net active (your trial net). A random net judges
     positions badly, so misses here are expected to need more depth; report the counts next to B1's, and for
     every miss try depth 16 once. A miss that stays at depth 16 is listed.
Every class: how many positions, how many passed, each failure in full.

### The report, forge-combo29/REPORT_deepseek_job3.md
  1. Table: part | done / partly / not done | evidence files | result in one line
  2. Findings ("none" only if true), the most costly in a real game first
  3. Which files of the repository you opened for this job
  4. Start and end of each part from recorded stamps, and the total
  5. "What I did not do"
  6. "What I am not sure about"
  7. "A better way" (may be empty)
