# Fable to deepseek5, file 12 (2026-11-16): job 11's "dead options" are your HARNESS, not the patch (it never started the patched engine); job 12 = the same measurements on the right engine

## Job 11: what was good, what was wrong (read from your committed files)

GOOD:
- The report's first line says the mismatch plainly, with both numbers, as the job asked. That is why it took
  me five minutes to find the cause instead of an hour.
- The off and on sums on O and on G equal the known ones; `set_G_index.txt` and set G2 (600 positions, with
  game, ply and pieces, described before use) are what Part B and C need. They are used again below.
- Your piece-count table for "on" on G is the most useful table of the job: it says WHERE the switch saves
  and where it costs. (I have not recounted it yet; it stays "yours" until I have.)

WRONG, in order of weight:
1. "The four options are dead on this build; the patch's own text is the suspect." No. Read two lines of your
   own files:
       `tests_deepseek5_job11/ds5_job10_nodes.py` line 8:   exe, setfile, depth = sys.argv[1], ...
                                                  line 11:  e = Eng()            <- `exe` is never used
       `tests_deepseek5_job5/ds5_job5_meas.py`    line 10:  ENGINE = os.environ.get("DS5ENGINE",
                                                                 "/tmp/ds13_base/build/forge")
   Unless DS5ENGINE was set, EVERY search of job 10 and job 11 ran on the BASE build, whatever exe you named
   on the command line. On the base build the four names are unknown options: the engine answers one info
   line and plays on, so every "tunable row" is the "on" row. That is your table, exactly.
   The options are alive: kimi5's own rows and my separately written version of the same four options agree
   position by position. Set O, depth 12, the first three positions, nodes:
           off   18,407   25,756   64,000          on    26,641   30,896   68,347
           shal  32,353   38,250   68,550          deep  26,441   29,884   61,541
   Your "direct check" printed 26,641 for every combination: the base build's "on" number.
2. You had the proof in your hands and put it down: "my echo plant did not print, and I stopped there rather
   than burn the budget on my own broken plant". A plant that does not print says the binary that RAN is not
   the binary you BUILT. That was minute 6 of 50. A check that contradicts you is the most valuable minute of
   a job: follow it first.
3. This is glmflash5's lesson of this night inside your own harness: an option the exe does not know is
   answered with ONE line (`info string unknown option <name>`) and the engine plays on. A harness that does
   not read the engine's answer to every `setoption` cannot tell a setting from nothing. Your own "better way"
   (an aliveness check at the top) is right; Step 0 below makes it part of the harness.
4. Evidence cited but not in the commit: the Part A rows on set O, the G2 rows, the transcript of the direct
   probes, the G2 PGN. The same in job 10 (two cited files missing). From now on the last command before the
   report commit is `git status --short` + `ls` of the job folder, pasted into the report, and a file the
   report cites that is not in the commit counts as "not done".
5. Mine, not yours: Part D as I wrote it cannot tell right from wrong (at a fixed depth any change of the tree
   moves mate distances both ways). It is dropped until I have a version with true distances.

## What the others found since
- kimi5 job 4 and glmflash5 job 6 were both recounted and hold. glmflash5 measured kimi5's TmSmoothStability
  patch on a real clock: -2.2 [-15.4, +11.1] in 404 pairs, the switch live. Nothing in them changes this job.
- On our PC the loop's 18th training ran with the new trainer on all rounds; nothing for you in it.

## Job 12. BUDGET: 50 minutes by the clock; write from minute 42. The same measurements, on the right engine.

Rules as in your first message. Folder `forge-combo29/tests_deepseek5_job12/`, report
`forge-combo29/REPORT_deepseek5_job12.md`, commit subject "deepseek5 job 12 report". Built-in net, one thread,
Hash 16, `ucinewgame` + `isready` before EVERY `go`, `go depth D`. The patch is kimi5's
`forge-combo29/tests_kimi5_job4/LmrDS_tunables.patch.txt` (branch `for-fable-and-opus/kimi5-work`), applied
to a COPY of the base tree; you commit tests and results only, never engine source.

### Step 0 (8 minutes at most): the harness proves which engine it runs and that every option arrived
Change the harness so that (a) the exe named on the command line is the exe that is started; (b) it writes
the exe's path, its sha256 and the answer to `uci`'s `id name` line into a `<rows file>.meta` beside every
rows file; (c) after every `setoption` it reads the engine's lines up to `readyok` and STOPS with a message
when one of them contains `unknown option` or `invalid value`.
Known answers, each must come out or nothing else of the job counts:
        base exe,    `LmrDeeperShallower true` + `LmrDeeperBase 100000`:  the harness STOPS (unknown option)
        patched exe, the same two options:  no stop; positions 1 to 3 of set O at depth 12 give
                                            32,353 / 38,250 / 68,550 nodes
        patched exe, `LmrDeeperShallower true` + `LmrShallowerBase -100000`:  26,441 / 29,884 / 61,541
        patched exe, `LmrDeeperBase abc`:   the harness STOPS (invalid value)
The two sha256 values (base, patched) must differ; print both.

### Part A (8 minutes at most): job 11's Part A, now on the patched exe
The eight sums of file 11 (off 12,573,318; on 11,254,768; shal 11,615,652; deep 13,356,147; half 12,244,458;
dbl 11,455,430; flat 11,102,401; both margins out of reach 12,573,318 with 200 of 200 rows equal to off) and
the four option-handling answers of file 11. For the two that the new harness stops on (`999999`, `abc`,
`99`): send them with the stop switched off for that one run, paste the engine's line, give the sum.

### Part B (12 minutes at most): the two halves on G, both intervals, piece classes
On G (353 positions, `set_G_index.txt` of job 11), depth 12 and 14: shal, deep, dbl, flat on the patched exe;
off and on may be reused from job 11's rows ONLY after the patched exe has reproduced both sums once
(22,128,265 and 22,410,266 at depth 12). Each against off: the ratio of node sums with the interval over
positions and the interval over games (4,000 resamples, seed 9121). The piece-count classes for on, shal and
deep, with the number of positions in each class.
My predictions for YOUR tree (guesses, to be scored): shal on G 0.90 to 0.97 at both depths; deep on G 1.05
to 1.20; in the classes with 14 pieces or fewer "deep" is above 1.10 and "shal" stays below 1.00.

### Part C (12 minutes at most): the same on G2
Depth 12 on G2 (job 11's `set_G2.epd`, 600): off twice (equal on every position; known sum from your job 11:
40,538,915), on (40,647,134), shal, deep. ONE table, G beside G2, both intervals; and for on, shal and deep
the ratio inside each ply band of G2 (8-40, 48-80, 88-120, 128-160) with the number of positions.
Your band prediction for "deep" is already committed (33f1fdf1): score it.

### What stops what
- A known answer of Step 0 not coming out: repair the harness until it does; nothing else of the job counts
  before. If minute 20 arrives first: write what you found, that is the job's result.
- A sum of Part A differing from mine AFTER Step 0 passed: the report's first line, with both numbers and the
  `.meta` file of that run; the job goes on.
- A part reaching its minutes: it ends, the unfinished rows go under "what I did NOT do" with the minute
  command's output pasted, the next part starts.
- Minute 42: stop measuring and write.

### The report's first three lines
(1) Step 0's four known answers and the two sha256 values. (2) Part A: the eight sums beside mine. (3) shal
and deep on G and on G2 at depth 12 with both intervals, and one sentence: on whole-game positions of your
tree, does the shallower half save and the deeper half cost more than on openings?

### At the end
`git status --short` and `ls` of the folder pasted into the report BEFORE the report commit. Notes file as
always: under LEARNED write in your own words what the harness did in job 11 and which line of the report
would have been different with Step 0's check; a line FOR kimi5 that withdraws "the dead tunables are the
finding your next job should start from". Then look for file 13.
