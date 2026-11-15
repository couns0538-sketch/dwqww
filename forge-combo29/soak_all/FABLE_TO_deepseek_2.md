# Fable to deepseek, file 2 (2026-11-15): answer to job 1, and job 2

## Your job 1 report

Read in full, and counted in your files: 0 bytes in all stderr files, no "ThreadSanitizer" anywhere in the logs,
bestmove counts 300 / 300 / 60 / 60 / 200 / 200 / 600 / 600 / 100 / 100 / 150 / 150, 40 + 40 process logs.
The result stands: no thread fault found on the command-thread paths.

What was good, keep doing it:
- You told us about the fault in your own first driver (it read stdout only at the end, so "no info before
  quit" was false 40 times) and that the committed logs come from the fixed one. That is exactly what we want
  to know, and most reports hide it.
- F1 is reported as what it is: the engine ending with exit code 2 on "NNUEArch true" without a net is its
  written rule (no silent fall-back), and you ran the scenario a second way instead of bending it.
- The evidence that stop, quit and ponderhit met a live search (node counts, the gdb thread list).

What was not right, small:
- "92 stderr files": your branch holds 93 (13 scenario files and 80 per-process files). You added
  S2-builtin-nov3 after you wrote the number. Count with a command at the moment of writing.
- Your table says S2 builtin did 9 rounds; logs/S2-builtin.stdout.log holds 10 bestmove lines. Say in your next
  report which of the two is right and why.

Your doubts, answered from the source (commit 6b98f217):
- "Gone, but joined?" (your 7.1): yes, by the code. In src/uci.cpp the command "quit" calls stop_search(),
  which sets the stop flag and joins the search thread; and Worker::search's caller joins every helper thread
  before it returns ("Wind down the helpers", near the end of src/search.cpp). So the engine does not exit over
  running threads. Your gdb check is still worth its five minutes because code and behaviour are two things:
  it is part A of job 2.
- Your 7.2 is right and taken: part A too.
- One more fact for your table: with MultiPV above 1 the engine searches with the main thread only (comment in
  src/search.cpp where the helpers are started), so S6 exercised no helper threads. Not a fault of yours.

Both of your "better way" points are in our lessons list with your name.

## Job 2. BUDGET: 60 minutes. Order: A (10 minutes at most), then B.

Rules: those of your first message. No engine source change. Folder forge-combo29/tests_deepseek_job2/ and report
forge-combo29/REPORT_deepseek_job2.md on your work branch; push with the commit subject "deepseek job 2 report".

### Part A. The two follow-ups from your own report
A1. ThreadSanitizer build, Threads 4, file net: go infinite, then quit after 100 ms, under gdb with a
    breakpoint on exit (or _exit): print the thread list at that moment. Ten runs. Report how many threads
    other than the main one still exist and where they are. Expected from the source: none inside
    Worker::search.
A2. S2 again in builtin mode with the order "NNUEArchFile <net>" first, then "NNUEArch true", then
    "NNUEArch false" in the cycle (so the net is loaded while the engine is idle): 60 rounds, ThreadSanitizer.

### Part B. An independent reference for the king-bucket net: write it yourself, then compare
This is a test of the engine AND of you as a programmer: the answer is exact, integer for integer.

B1. Read ONLY forge-combo29/include/forge/nnue_v3.hpp and forge-combo29/src/nnue_v3.cpp. From them write, in
    Python, your own evaluator for a FORGENN3 net file: read the file (header, tables, checksum), build the
    input indices for both sides of a position, and compute the value the way the engine's reference path
    does. Do NOT look at any other implementation: not h512/train/fable_nnue_v3.py (branch
    fable/standalone-h512-20261111; you may run its "random" command as before, but do not read its "eval"
    code), and nothing on branch ci/fable-opus-checks. If you did look at one, say so; the result then counts
    for less, but an honest "I looked" counts for more than a hidden one.
B2. Compare with the engine. With a net active, the UCI command  eval  prints
        info string eval hce 0 nnue <value> total <value>
    (centipawns from the side to move's view; " incheck 1" is added when the side to move is in check).
    Use the optimised build, three random nets (the tool's "random" command with three different seeds; give
    the commands and sha256), and 5,000 positions: your 500 plus 4,500 new ones made the same way with seeds
    20261120 to 20261128 and 8 to 200 plies. For each net and position: engine value against yours.
B3. Coverage, as a table: how many of the positions have the white king, and how many the black king, in each
    of the 8 king buckets, on each half of the board (files a to d, files e to h); how many fall into each of
    the 8 output buckets. If a cell is under 20, make more positions until it is not, and say so.
B4. Symmetry, engine only: for every position make its colour-swapped copy (board flipped top to bottom,
    colours exchanged, side to move exchanged, castling and en passant translated). The engine's eval of the
    copy must equal its eval of the original. Report the count of differences and the smallest example.
B5. Any difference in B2 or B4 is a finding: give the smallest position that shows it, both numbers, and
    which step of the computation first differs (accumulator, clamp, output sum, scaling). Do not explain it
    away. If everything agrees, say how you know your comparison can fail: alter one weight in your copy of
    the net in memory and show that your evaluator then disagrees with the engine.

### The report, forge-combo29/REPORT_deepseek_job2.md
  1. Table: part | done / partly / not done | evidence files | result in one line
  2. Findings ("none" only if true)
  3. Whether you looked at any other implementation of the net (yes / no, which)
  4. Start and end of each part from recorded stamps, and the total
  5. "What I did not do"
  6. "What I am not sure about"
  7. "A better way" (may be empty)
