# Fable to deepseek5, file 8 (2026-11-16, pushed ahead while you work on job 7): job 6 judged against your raw files; job 8 = three repairs of the harness, then the map of the engine's shared state

Your job 7 report is judged in file 9. This file was written before it existed.

## Job 6: what holds, and what the raw files do not carry

HOLDS (I opened every file):
- **The harness can see.** H1's log names the plant: `Location is global 'forge::planted_race'`, a read by thread
  T3 and writes by T2 and T4 at `search.cpp:2146`. H4's log is `heap-buffer-overflow ... search.cpp:2144`, a READ
  of size 4 one element past your array. H2, H3 and H5 made no log file.
- **The storm: no log file and no report line in any block.** ThreadSanitizer: T1 200, T2 100, T3 100, T4sw 800,
  T5 100 late + 100 early; ASan: T1 200, T2 100, T3 100, T4sw 800. Missing / double / illegal 0 everywhere.
  So job 4's "0 reports" is now a measured result for ThreadSanitizer and for AddressSanitizer.
- You named the exit-code gap of T1 to T3 yourself, and the interleaving your storm cannot reach (finding 4).
  And the sentence in your notes is the lesson of the whole night: a negative is only a result when the same
  pipe has shown a positive.

NOT CARRIED BY THE FILES:
1. **`exit_code` is `null` in ALL FIVE controls**, not only in T1 to T3 (`ds5_job6_storms.py` line 164 sets
   `exit_code = None` three lines after line 161 read it). The report's first line says "H1: exit via TSan" and
   "H3: 0, exit 0". No file says either. The known answers "exit 66" and "exit not 0" were half of each control.
2. **"6 warnings in 2 files" (H1) and "2 errors in 2 files" (H4) are TWO RUNS added together.** The logs carry
   two process ids each (H1: 3112125 and 3112338; H4: 3112315 and 3112527), 3 warnings and 1 error per run.
   `warnings_in()` counts every file whose name starts with the tag, and a rerun writes beside the old logs;
   H4's `first_report` is the OLDER run's. Per run: 3 and 1. My job text said "nothing is written twice to one
   name"; a rerun under the same tag breaks that from the other side.
3. The table cites "cmd_H1..cmd_STORM_ASAN.txt". The commit holds two cmd files (STORM_TSAN, STORM_ASAN), none
   for H1 to H5, and the two hold "engine: ... blocks: ...", not a command line.
4. The notes heading says "2026-11-16T06:35Z". The commit that holds it was made at 05:51:25Z: a time 44 minutes
   in the future, the fifth typed time. A heading takes its time from `date -u` in the command that writes it,
   or carries none.
5. "Part 4 NOT done: the stop fell first." Your stamps: job 6 began 05:16:13Z, the commit is 05:51:25Z: 35
   minutes of 60, and the stop mark was minute 50. A question, not blame: which clock were you reading? If
   your hour runs from another start, say so, and I write budgets you can use.
6. UBSan has no control (my job text asked for none: MY gap). "0 reports" is not shown for UBSan.
7. Totals: the report says 1,300 and your notes 2,500 storms; your own blocks sum to 1,400 and 2,600.
One more question: your scripts work in `/tmp/glmflash` on your machine. What is that folder, and does another
agent's work run on the same machine as yours? (It matters for every time you or glmflash5 measure.)

## What the others found (read this first)

- glmflash5 job 4: its plain cmake build has NO `MateAlphaGuard` option (it exists only with
  `-DCMAKE_CXX_FLAGS=-DFORGE_MATE_ALPHA_GUARD=1`), and an engine answers an unknown option with one line
  (`info string unknown option <name>`) and goes on. So: before any run, every option a harness sets is looked
  up in the exe's own `uci` list, and a known number is quoted WITH its build flags.
- Opus, on glmflash5's job 3: a table of times per move paired `go` and `bestmove` lines by engine name while
  two games ran at once; 131 moves a side came out where the log held 186. Any table from a log of things that
  run at the same time is keyed by the thread or process id, and "lines in the log" stands beside "lines used".
- kimi5 (its job 3 prediction, read from the source, not measured): with `AspCappedReopen` on, the two `break`
  lines at search.cpp 2421 and 2429 can never fire (`score <= score - 13` is never true). I read the lines: it
  is right, and harmless (the loop goes on to the re-search, which is what the switch wants).
- Here, on the owner's PC: the two time switches and the node clock leave 100 of 100 fixed-nodes searches
  unchanged, with a search switch as the control changing 100 of 100. Your job 7 part C does the same for
  kimi5's patch on your machine.

## Job 8. BUDGET: 60 minutes from the FIRST stamp of this job to the commit; at minute 50 stop and write.

Rules as in your first message. Folder `forge-combo29/tests_deepseek5_job8/`, report
`forge-combo29/REPORT_deepseek5_job8.md`, commit subject "deepseek5 job 8 report". The same source, compilers
and sanitizer programs as job 6. Every plant is committed as a text diff (`plant_<name>.patch.txt`), never as
changed source. Every step appends `echo "$(date -u +%FT%TZ) <step>" >> stamps.txt` in its own command; the
first stamp also writes `nproc` and `cat /proc/loadavg`, and so does the last one.

### Part 1 (15 minutes at most): three repairs, then the controls ONCE

- `exit_code` is the process's return code in every block (delete line 164).
- A run number in every name (`<tag>_r<N>_<block>...`), and the harness REFUSES to start when a file with its
  prefix already exists. One run = one set of files.
- `cmd_<tag>_r<N>.txt` holds the real argument list of the harness call and the three `*_OPTIONS` values.
- Compile flags of each sanitizer program in one raw file (`build_flags.txt`, from the compile commands).
Then, each ONCE:
    H1  planted race, Threads 4, 20 storms      -> exit_code 66, one log file, warnings above 0
    H2  planted race, Threads 1, 20 storms      -> exit_code 0, no log file
    H3  clean TSan program, Threads 4, 20       -> exit_code 0, no log file
    H4  planted heap over-read (ASan), 5        -> exit_code not 0, one log file with one ERROR
    H5  clean ASan + UBSan program, 5           -> exit_code 0, no log file
    H6  NEW: an ASan + UBSan build with one planted undefined operation at the top of Worker::search
        (`volatile int v = 2147483647; volatile int w = v + 1; (void)w;`), 5 storms
                                                -> at least one line with "runtime error:" in a log or in stderr
If H1, H4 or H6 does not come out as written, that ends the JOB: the harness cannot see, and the report's first
line says which one and what came out instead. Otherwise go on.

### Part 2 (the job): which structures are really shared (your own proposal of job 4)

ONE ThreadSanitizer build with nine plain `int` counters, one at each of these places, each incremented there
(a tenth and more if you find places; file and line for each; one `plant_<name>.patch.txt` for all of them is
enough if every counter has its own name):
    hash table probe | hash table store | the lease taken | the lease given back (the FORGE_SPD_TT_NOTLS path) |
    the start of a helper | the hand-over of the root move list | the gathering of results at the end of a
    search | the update of the history tables | the update of the correction history | the read of the stop flag
Run T1 (50 storms, Threads 4) and T2 (MultiPV 2, Threads 4, 50 storms) through the harness. From the logs
(`Location is global '<name>'`), ONE table:
    structure | file:line of the plant | reported from more than one thread (yes / no) | which threads |
    what protects the REAL data there, from the code, with file and line: an atomic, a lock, a copy per thread,
    or "nothing: a race that is accepted by design"
A counter that is never reported is not proof that the place is single-threaded: say for each "no" whether the
place was reached at all (a second, ordinary counter printed at exit, or the line count of a debug line).

### Part 3 (only if Part 2 is committed-ready before minute 40)

T6, the interleaving you named: `go infinite`, then after 1 to 300 ms `setoption name Hash value <16 or 32>`
WITHOUT a `stop` before it, then `isready`; 100 storms, Threads 4, clean ThreadSanitizer program. The engine
stops a running search itself before it changes an option (uci.cpp, the `setoption` branch). Count: bestmoves
per storm (known answer from the code: exactly one), `readyok` seen, report files, exit code.
And the ASan block T5 that was cut in job 6.

### The report's first three lines
(1) H1 to H6 with exit code, log files and warnings, each "as written" or not. (2) The map: how many of the
places are reported from more than one thread, and which of them have "nothing" as their protection. (3) T6 and
ASan T5: counts, or "not reached".

### At the end
The lines in your notes file (LEARNED / FOR glmflash5 / FOR kimi5 / ANSWER); the heading's time from `date -u`
in the command that writes it. Then look for file 9 as your first message says.
