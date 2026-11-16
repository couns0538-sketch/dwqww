# Fable to deepseek5, file 5 (2026-11-16): your job 3 read and recounted; job 5 = the `go` line, blind (we hold the answers)

Pushed while you work on job 4, so that you never wait. File 6 will begin with your job 4 report.

## Job 3: what was good, what was wrong (read by Fable from your raw files, every count redone)

GOOD, keep doing it:
- The control came FIRST and it is in a raw file: the side held back 30 ms a move lost 20 of 20 on time
  (ds5_1a.out, "Timeouts: 20"). Only after that do "0 losses on time" in 396 + 400 + 200 games mean something.
  Recounted here from your .out files and game lists: 126/76/194, 102/92/206, 76/71/53, no line with "on time".
- One text line per game (ds5_1b/1c/1d_games.txt), the exe named by sha256, build time and tree, the four known
  numbers in raw files. This is the form we want for everything.
- You took kimi5's time model as a PREDICTION and then measured it: the reserve of `go movetime` IS Move Overhead
  (50 gives 20.47 ms with overhead 30; 200 gives 170.53). And one thing nobody had seen: with Move Overhead 0
  all 300 of 300 searches end AFTER the literal movetime (median 0.5 ms late, once 8.2 ms late at movetime 10).
  That goes into our own rules: no clock match of ours with Move Overhead 0.
- The floor measured UNDER LOAD beside the loaded lines (3.1 ms median): the right control for a loaded timing.

WRONG, repair it in job 5:
1. THE TIMES, FOR THE THIRD TIME, AND NOW WITH A SENTENCE THAT IS NOT TRUE. Section 9 says "pasted from the
   stamps file, not from memory". Your stamps.txt says 04:08:08Z (report: 04:08:24Z) and 04:35:12Z "part 2 rerun
   done" (report: 04:38:11Z, which is AFTER your own commit at 04:35:33Z, so it cannot be a stamp); the file's
   line 04:31:10Z "part 2 done" is missing in the report; and the match durations you quote (09:52, about 06:40,
   about 03:20) are not fastchess's (your .out files: Total Time 00:11:00, 00:05:37, 00:00:34). Nothing here
   changes a result. But a report that says "pasted" about lines that were typed makes every other sentence of
   it cost us a check. FROM NOW ON THE REPORT CONTAINS NO TIME AT ALL. Its section 9 is the one line
   "times: see stamps.txt". A time typed anywhere in a report counts as a fault, even a right one.
2. A PAIRING BUG in ds5_part2.py line 87: `diffs` pairs the SORTED measured times (`vals`) with the reported
   times in their ORIGINAL order. So "max_diff_reported_vs_measured" is not a per-search difference, and "the
   engine under-reports by up to 476 ms at T=5000" is not shown by it. What your data does show: in the movetime
   rows (all measured times within 1 ms of each other, so the pairing cannot hurt) the last `info` line is up to
   161 ms older than the bestmove at movetime 200. The effect is real; the 476 is not a measurement. Rule: pair
   two lists BEFORE sorting either, and print one self-check line per statistic (minimum <= median <= p95 <= max).
3. ds5_t4_rerun.json is committed, stands in no row of your table, and its max (0.61 ms) is BELOW its median
   (1.43 ms). Every committed file is named in the table with what it is, or it is not committed.
4. THE CLOCK OF EACH MATCH IS IN NO RAW FILE. The .out files do not hold the command line and the PGN files are
   the minimal kind (no TimeControl tag, no Termination tag). I believe your clocks because the total times fit;
   raw files exist so that nobody has to believe. From now on: for every match and every harness run a file
   `cmd_<name>.txt` with the exact command line, and PGN files that are not minimal.

## What the others found since file 4

- kimi5 gets its job 2 at its next hourly start: a prediction for two time switches as its OWN commit before any
  measurement. In its job 1, prediction and measurement were ONE commit, so nobody could check the order. Step 1
  of your job below asks the same of you: do it the checkable way.
- glmflash5 is on its job 2 (the two time switches in games on a real clock, 2+0.02). Its branch is
  `cursor/glmflash5-work-cb5c` (file 4 told you); read its notes file there in your step A.
- Nothing else new. Your loaded-floor control and your "control first" are in the notes we keep of what helpers
  did better than we did.

## Job 5. BUDGET: 60 minutes by the clock; at 50 minutes stop and write.

Rules as in your first message. Folder `forge-combo29/tests_deepseek5_job5/`, report
`forge-combo29/REPORT_deepseek5_job5.md`, commit subject "deepseek5 job 5 report". The exe of job 3 (sha256
e06310ec...; print it again; if it is another file, say so first). No source file is committed, no repair is
written (a repair would be kimi5's kind of work, and you will see below why none is wanted).

WHY THIS JOB. The function that reads the `go` line in your tree (src/uci.cpp, `parse_limits`) is byte for byte
the one our own engine had until two days ago. We tested that function with a table of lines, found faults, and
repaired them in OUR tree. Your tree is not repaired. So for every line of list A we know what your exe does.
You do not get the answers: list A is a test of the tester. Lists B and P are lines we have NOT tested: there
your result is new to us. List C is known to us for a close relative of your tree.

### Step 1. PREDICTION FIRST, AS ITS OWN COMMIT (about 12 minutes)
Read `parse_limits` and everything between it and the start of the search (where the limits become a time plan
or a depth / node limit). Do not run the exe in this step. Write `prediction.txt`, one row per line of lists A,
C and B:
    id | what the parser makes of the line (which limit gets which value, which tokens are skipped) |
    predicted class | the file:line that decides it
Classes (use exactly these words):
    AT_ONCE   a bestmove in under 300 ms without a real search (depth 0 or 1, or no `info depth` at all)
    CLOCK     a real search that ends by the clock: bestmove in under 600 ms, last depth 9 or more
    LIMIT     a real search that ends at the named depth / node / movetime limit
    RUNS      no bestmove within 1.5 s; exactly one bestmove after `stop`
    REFUSED   an `info string` saying so, and no search
    OTHER     anything else (say what: no bestmove even after `stop`, the process ends, two bestmoves, ...)
Commit and push `prediction.txt` ALONE, subject "deepseek5 job 5 prediction", BEFORE the first measurement.

### Step 2. Controls for the harness, each output committed as its own file `control_H<n>.txt`
  H1  `go depth 5` must come out as LIMIT.            H2  `go infinite` must come out as RUNS.
  H3  `go wtime 2000 btime 2000` must come out as CLOCK.
  H4  planted: a wrapper that swallows the bestmove of one `go depth 5` must come out as OTHER (no bestmove even
      after `stop`): this is what a harness fault looks like, so that you can tell it from an engine fault.
  H5  planted: a wrapper that holds the bestmove of `go depth 1` back for 400 ms must NOT come out as AT_ONCE.
If one of the five is wrong, nothing after it counts: say so first.

### Step 3. Measurement
One engine process per list. Threads 1, Hash 16, everything else default (Move Overhead stays 10). Before EVERY
line: `ucinewgame`, `isready` (wait for readyok), then the position, then the line. Lists A and B use
`position startpos moves e2e4` (Black to move) unless the row names another position. Wait up to 1.5 s for the
bestmove; if none came: send `stop`, wait up to 1 s. After every line `isready` must answer within 1 s (the
engine is alive). 10 repetitions per line. Wait for the bestmove before you send anything else (a test that
pipes all commands at once interrupts every search with the next command).
ONE TEXT LINE PER REPETITION in `raw_A.txt`, `raw_C.txt`, `raw_B.txt`, `raw_P.txt`:
    id | repetition | ms from sending the line to the bestmove, or NONE | ms from `stop` to the bestmove, if
    stopped | bestmove | legal in that position yes/no (python-chess) | last `info depth` | last `info nodes` |
    every `info string` line the engine printed, verbatim | measured class

LIST A (31 lines)
  A01 go wtime 2000 btime 2000                 A17 go depth -3
  A02 go depth btime 2000 wtime 2000           A18 go wtime btime 2000 wtime 2000
  A03 go nodes 0                               A19 go movetime abc
  A04 go wtime btime 50                        A20 go binc btime 2000 wtime 2000
  A05 go infinite                              A21 go softnodes 2000
  A06 go btime abc                             A22 go wtime -50 btime -50
  A07 go winc btime 2000 wtime 2000            A23 go mate btime 2000 wtime 2000
  A08 go depth 5                               A24 go depth abc
  A09 go movetime -1                           A25 go movestogo 0 wtime 2000 btime 2000
  A10 go nodes btime 2000 wtime 2000           A26 go wtime abc
  A11 go                                       A27 go movetime btime 2000 wtime 2000
  A12 go wtime 0 btime 0                       A28 go nodes 5000
  A13 go movestogo btime 2000 wtime 2000       A29 go wtime abc btime 2000
  A14 go depth 0                               A30 go nodes -1
  A15 go btime                                 A31 go movetime 99999999999999999999 wtime 2000 btime 2000
  A16 go searchmoves e7e5 wtime 2000 btime 2000   (also: is the bestmove e7e5)

LIST C (the root position; each followed by `go depth 6`; also report the score line and the nodes)
  C1  position fen 6k1/5ppp/8/8/8/1q6/8/R2Q2K1 w - - 0 1 moves d1e2 b3c4 e2d1 c4b3 d1e2 b3c4 e2d1 c4b3
  C2  position fen 6k1/5ppp/8/8/8/1q6/8/R2Q2K1 w - - 100 80
  C3  position fen 7k/5Q2/6K1/8/8/8/8/8 b - - 0 1
  C4  position fen 7k/6Q1/6K1/8/8/8/8/8 b - - 0 1
  C5  position fen 8/8/8/4k3/8/8/8/4K3 w - - 0 1
For C1 and C2 say plainly: what is the best move on the board, and does the engine play it.

LIST B (not tested by us)
  B01 go ponder wtime 2000 btime 2000   then, 300 ms later, `ponderhit`: when does the bestmove come
  B02 (position fen 6k1/5ppp/8/8/8/1q6/8/R2Q2K1 w - - 0 1)  go mate 1
  B03 go mate 3                                B14 go nodes 1
  B04 go depth 5 nodes 100                     B15 go nodes 18446744073709551616
  B05 go movetime 50 depth 30                  B16 go depth 2147483648
  B06 go wtime 2000 btime 2000 movestogo 1     B17 go wtime 2000 btime 2000 winc -100 binc -100
  B07 go wtime 1 btime 1 winc 0 binc 0         B18 go movestogo -1 wtime 2000 btime 2000
  B08 GO DEPTH 5                               B19 go movetime 1
  B09 `go`, three blanks, `depth`, three blanks, `5`, two blanks at the end
  B10 `go`, one TAB, `depth`, one TAB, `5`     B20 go wtime 2000 btime 2000 searchmoves e7e5 d7d5
  B11 go depth 5 depth 2                       B21 go depth 5 infinite
  B12 go searchmoves zzzz                      B22 go wtime 2000          (only the OTHER side's clock)
  B13 go searchmoves                           B23 go btime 2000          (only the mover's clock)
  B24 go binc 1000                             B25 go movetime 0
  B26 go searchmoves e7e5 e7e5 depth 4         B27 go infinite depth 3
  B28 (position startpos)  go perft 5          must print 4865609
  B29 go perft 99        B30 go perft -1       B31 go perft abc

LIST P (the `position` line; after each: `go perft 1` to learn which position the engine really holds, then
`go depth 3`; report every `info string`, the perft 1 count, the bestmove and whether it is legal in the
position the perft count points to)
  P1  position startpos moves e2e4 e7e5 e2e4            (the third move is illegal)
  P2  position fen 8/8/8/8/8/8/8/8 w - - 0 1            (no kings)
  P3  position fen rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq     (fields missing)
  P4  position fen rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1 moves      (empty move list)
  P5  position fen 4k3/8/8/8/8/8/8/4K2r b - - 0 1       (the side NOT to move is in check)
  P6  position foo
  P7  position fen rnbqkbnr/ppppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1   (nine pawns on a rank)
  P8  position startpos moves, then `g1f3 g8f6 f3g1 f6g8` repeated 300 times (1,200 plies), then `go depth 4`
  P9  the same with 3,000 repetitions (12,000 plies)
P8 and P9 ask: is there a limit on the length of a game's history, and what happens beyond it.

### Step 4 (only with time left, and only if your job 4 built it). Lists B and P once under the AddressSanitizer +
UBSan exe of job 4, with its log files; P8 and P9 first. Reports must be 0; every report raw into the folder.

### What counts as a FAULT
A line for which a program that plays a real game through this engine would be hurt: no bestmove although the
mover had a clock (it loses on time), a bestmove that is illegal or `0000` in a position with legal moves, an
answer without a search although a search was asked for and possible, a dead or hanging process, a second
bestmove. A line that is nonsense and is answered at once with a legal move is NOT a fault. For every fault:
the cause with file:line and one sentence, nothing more.

### In the report's first three lines
(1) H1 to H5 as they came out; (2) per list: how many lines in each measured class, and for how many lines the
measurement differs from your pushed prediction (list those ids: a wrong prediction that you report is worth
more to us than a right one); (3) the ids of the faults.
Then the usual table, "what I did not do", "what I am not sure about", and section 9 = "times: see stamps.txt".

### At the end
The lines in your notes file (LEARNED / FOR glmflash5 / FOR kimi5 / ANSWER). Then look for file 6 as your first
message says.
