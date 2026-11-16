# Fable to kimi5, file 1 (2026-11-16): job 1, the clock from the inside

This is your first job. Your automation text has the rules, the engine build, step 0 and the report form; this
file has only the task.

## What the others are doing (read this first)

- **deepseek5** measures the clock from the OUTSIDE (its job 1): 300 positions at `go wtime T btime T` for T from 20
  to 5000 ms, `movestogo 1`, `movetime`, with the floor of its own harness and a planted 30 ms delay as controls,
  then games at 10+0.1, 1+0.01 and 0.5+0.005 counting losses on time. Its report, if it is there:
  `forge-combo29/REPORT_deepseek5_job1.md` on `for-fable-and-opus/deepseek5-work`. Its job 2 asks it for the same
  repair you may write below (Part C), without seeing yours. **Do not read a patch of deepseek5's before yours is
  pushed: the two are compared afterwards.** Its MEASUREMENTS you read and use.
- **glmflash5** plays the two time switches `TmFinishIteration` and `TmNodeShare` on a real clock (its job 2).
- Why the clock: an earlier helper saw this engine overstep its time in about a third of its games under exact
  bookkeeping with no margin, and nobody has explained it from the source. A loss on time loses a won game, and
  the engine's strength is judged on the clock. Correctness comes first for the owner.

## Job 1. BUDGET: 50 minutes by the clock; at minute 40 stop and write the report with what you have.

Folder `forge-combo29/tests_kimi5_job1/`, report `forge-combo29/REPORT_kimi5_job1.md`, commit subject
"kimi5 job 1 report". Step 0 first (the four known numbers).

### Part A (about 15 minutes): the time model, from the source. Deliverable: `TIME_MODEL.md` in your job folder
Read the engine's time code in `forge-combo29/src` and `include` (start from where `go` is parsed in the UCI loop
and follow it into the search). Write down, each point WITH FILE AND LINE:
 A1. How the parameters of `go` (`wtime`, `btime`, `winc`, `binc`, `movestogo`, `movetime`) and the option
     `Move Overhead` become limits: the formulas for the soft limit and the hard limit, in milliseconds, and one
     worked example each for `wtime 1000 winc 10`, `wtime 100`, `wtime 20`, `wtime 300 movestogo 1`, `movetime 50`.
 A2. Every option whose name starts with `Tm` in the `uci` answer: its default, where it is read, what it changes.
 A3. Where the search LOOKS AT THE CLOCK: in which functions, every how many nodes, also inside quiescence, and
     what helper threads (Threads > 1) do. What exactly happens when the hard limit has passed: which move is
     played (the last finished iteration's, or the unfinished one's)?
 A4. What is NOT interruptible: the first iteration, anything between `go` and the first node (position set-up,
     clearing or resizing the hash, starting threads), anything between the last node and the `bestmove` line
     (joining threads, printing).
 A5. `go ponder` and `ponderhit`: from which moment the clock counts.
 A6. What the engine does when the time left is smaller than `Move Overhead`.

### Part B (about 15 minutes): the worst case, predicted and then tested
 B1. From Part A, PREDICT in milliseconds on your machine the largest time a search can run past its hard limit
     (nodes between two looks at the clock divided by your nodes per second, plus whatever A4 adds). Write the
     number down BEFORE you measure. Name every code path by which the limit can be exceeded by more than one
     interval between two looks.
 B2. TEST it with your own script (one engine process; a monotonic clock in the process that writes and reads
     the pipes; `ucinewgame`, `position fen`, one `go`, wait for `bestmove`; elapsed from writing `go` to reading
     `bestmove`): `go wtime T btime T winc 0 binc 0` for T = 20, 50, 100 on
       (i) the first 300 lines of `UHO_Lichess_4852_v1.epd` (github.com/official-stockfish/books), and
       (ii) 20 positions YOU choose from your model as the worst for the clock (say for each why: long captures
            sequences, many legal moves, many checks, whatever A3 and A4 point at),
     each with Threads 1 and with Threads 4 (Hash 16, OwnBook false, Move Overhead at its default).
     Report per line: count, median, 95th percentile, maximum of elapsed, how many searches took LONGER than T,
     and every bestmove checked as legal (python-chess from PyPI).
     Control 1: `go depth 1` on the 300 positions: the floor of your harness (median, maximum).
     Control 2, the planted fault: a wrapper between harness and engine that holds every `bestmove` back by
     30 ms; with it the T = 20 line must show an overshoot in nearly every search.
 B3. Compare with B1 and with deepseek5's numbers (quote them with its file name). If prediction and measurement
     differ by more than a factor of two, the cause is not found yet: say so and say where you would look next.

### Part C (the rest of the time): the repair as a TEXT PATCH, or the proof that none is needed
 If B2 shows a search longer than its time, or Part A shows a path that can exceed it:
   `time_safety.patch.txt`: the smallest change that makes elapsed <= T - 1 hold in every search of B2 at T >= 20
   with Move Overhead at its default. Behind a UCI option that is OFF by default (a check option `TimeSafety`,
   declared, set and read exactly as `ThreatHistory` is): with the option off not one decision changes.
   Proof, as raw output files:
   - the four known numbers on the patched build with the option OFF and with the option ON (a bench has no
     clock: all eight must be the known numbers; if not, the patch changes more than the clock);
   - B2 again on the patched build, option OFF (the overshoots must still be there: the control) and option ON
     (must be 0), with both controls;
   - 400 games with fastchess at `nodes=20000`, the option ON against OFF, UHO openings, each twice with colours
     reversed: every pair must be 1-1 (at fixed nodes the option may change nothing). One text line per game.
 If nothing can exceed the time: say so with the proof from Part A (which line guarantees it), and write instead,
 as text only, the three weakest points of the time ALLOCATION that you see in the code (how the soft limit is
 chosen, what makes the engine stop early or late), each with what a patch would change and how it could be
 measured. We decide the next job from that list.

### The report's first three lines
(1) the largest overshoot you predicted and the largest you measured, with the `go` line and the thread count;
(2) the cause in one sentence with file and line, or "none found, because <line>"; (3) whether a patch is
committed and whether it changed anything at fixed nodes.
If the time runs short: Part A complete comes first (a later run builds on `TIME_MODEL.md`), then B2 line (i) at
Threads 1 with its two controls, then the rest.
