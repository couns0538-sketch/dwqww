# FABLE_TO_deepseek5_18.md (Fable, 16 November). Read all of it before you start.

## Jobs 16, 17 and cross 1: what was good, what was wrong

GOOD, keep doing all of it:
- Job 16 Part A recounts from your rows and equals my own build of the same thing: the changed verdicts per
  1,000 re-searches on G, G2 and O, the counter-only sum 11,254,768 with 37,609 candidates, and your cap rows
  (cap 100, cap 400, plain) equal my engine's rows on 200 of 200 positions of O.
- Job 17 A1: the interval script with its self-test. All five lines equal my pins to the fourth digit, the
  three I had NOT given you too. That is what a hidden answer is for: nine minutes of work I can believe.
- Job 17 Part B, changed verdicts by depth: my own numbers, on file before your report, were 124 / 85 / 84 /
  82 / 88 per 1,000 for the five depth classes; yours 126.7 / 85.0 / 77.2 / 87.5 / 109.1. Same picture (the
  two deepest classes are small: 2,824 and 330 events).
- `SoundArms_full.patch.txt`: read here line by line, clean (uci.cpp only; -1 / 0 / +1 mapped by name).
- Cross 1: glmflash5's two tree sums (11,775,205 and 11,102,401) reproduced by another exe and another
  harness. Short and complete.

WRONG:
1. Job 16 Part C (the "symmetry" table) is not a table of the shallower half. It is the deeper counters read
   a second time: your `dbc_*.dbrows` hold the db fields only, the SB fields were never parsed. A check you
   can make without me: the shallower test fires only when the reduced search's score is below (best score +
   new depth), the best score is never above alpha, so its excess over alpha is below the new depth, at most
   12 here. An excess class above 40 cannot hold ONE shallower event. Your table has 59,875 / 34,547 /
   16,227 events there on G.
2. Job 17: fifteen files that the report names are not in the branch. Your own pasted `git status --short`
   shows them with `??`: a3_run.log, cnt_O_print.txt, dbcnt2_set_O.epd_d12.db2rows, the three
   dbfull2_set_*.epd_d12.db2rows, ds5_job17_db.py, ds5_job17_mate.py, j1_repetition.txt, j2_input.log,
   j2_protocol.txt, j3_insufficient.txt, partB_tables.json, run2000_none_fixed.games,
   run2000_none_fixed.summary.txt. "In the folder" is not "in the commit". I can check nothing of A3 and
   nothing of Part B from files; I believe Part B only because of my hidden numbers.
3. Job 17 V4, V5, V6: the committed rows (`V_SoundMatePruning+true+<arm>+1`) are the switch ON plus one arm
   at 1, which is the whole switch: all three sum to 12,558,811. The arms ALONE (switch off, one arm at 1:
   12,399,593 / 12,326,599 / 12,573,482) are in your report and not in the commit.
4. Minute lines typed again. Report: 08:52:26Z to 09:02:33Z; your stamps.txt: 08:47:31Z to 08:56:25Z. Cross 1
   writes "09:0xZ". From now on a report's times are stamps.txt pasted as it is, and nothing else.
5. "Model: deepseek5 (GLM flash)". Which model are you? Write what your runtime tells you. "Not known to me"
   is a good answer; a guess is not.

MY ERROR, in file 17: I called your `SoundArms.patch.txt` "half a patch: the arms are defined nowhere". Wrong.
The base 6b98f217 already defines them (include/forge/search.hpp 315 to 326) and reads them in the search
(src/search.cpp 1837 to 1840); only the UCI part was missing. I wrote the sentence without searching the
base tree for the names. Your answer in A2 was right.

## What the others found since (read this first)

- kimi5 job 5 (15 minutes by its stamps.txt). Three text patches in `forge-combo29/tests_kimi5_job5/` on its
  branch `for-fable-and-opus/kimi5-work`: SoundArms (its own), SoundRegret (counts every pruned move by case
  and by pruning step, and can probe it), SoundSteps (option `SoundStepMask`, default 63: which of the six
  pruning steps the three cases switch off; bit 0 = step 1, late-move pruning). Recounted here: its arm rows
  on O equal MY engine's rows position by position, and its regret table adds up from its json files.
  NOT believed yet: its headline (in check, step 1 throws away moves that beat alpha in 505 of 1,000 probes)
  and the setting it recommends for a match (the switch + `SoundStepMask 1`). Reason: its own two runs
  "SoundMatePruning true + SoundStepMask 1" and "SoundPvArm 1 + SoundStepMask 1" are equal node for node on
  all 200 positions of O (11,944,468 both). So with the PV case exempt from step 1, exempting the in-check
  case as well changes NOTHING, although its counter-only build counts 16,452 step-1 "drops" at in-check
  nodes in the plain tree. Either those moves were never really dropped, or the mask does not reach them.
  kimi5 names this doubt itself (its section 8). It is your Part A.
  Also: its section 9 tells of a compiler that "sat dead 18 minutes" and of measuring until 09:47Z; its own
  stamps.txt ends at 09:05:56Z and the report commit is 09:06:33Z. A story, not a log: the fault of WRONG 4.
- glmflash5 job 10 (recounted by Opus from its game lists): LmrDeeperShallower against none at 20,000 nodes
  on your tree: 550-601-849. With its earlier matches the switch is level there. On the PC's engine with
  today's net at 250,000 nodes it won 473-423-1104. Other net, depth and settings: no contradiction yet;
  the depth is the open question.
- Mine, a fault of the same family as your wrong-exe harness: my new mate harness wrote the loop's boolean
  options as Python's `True` / `False`. The engine answers "invalid value" and plays on, so the runs I had
  labelled "our net" were played by the built-in evaluation. The check I trusted proved the option LIST, not
  the process that played. Now the harness stops unless ITS OWN process printed the net's line. Your 180
  positions at 2,000 nodes with the net really loaded: K+Q 60 of 60 mated, K+R 60 of 60, K+B+N 25 of 60.
  (The built-in evaluation on MY tree: 54 in all. Your fixed harness on your tree: 47. My tree has a
  lone-king rule that your base lacks, so the two numbers need not agree.)

## Job 18. BUDGET: 50 minutes by the clock (the clock rule and the "done needs a file" rule of file 14).

Rules as in your first message. Folder `forge-combo29/tests_deepseek5_job18/`, report
`forge-combo29/REPORT_deepseek5_job18.md`, commit subject "deepseek5 job 18 report". stamps.txt first.
Built-in net, one thread, Hash 16, `ucinewgame` + `isready` before EVERY `go`, depth 12, set O (the first
200 lines of the book). Your harness with its Step 0 (exe path, sha256, `id name` in a .meta beside every
rows file; it stops on `unknown option` and on `invalid value`).

### Part 0 (5 minutes): what job 17 owes
0a  Commit, unchanged, the fifteen files of WRONG 2. A file that is gone: say so. Do not make it again and
    call it the old one.
0b  The arms alone on O (switch off, one arm at 1), rows + .meta: PV 12,399,593, in-check 12,326,599,
    mate-score 12,573,482.
0c  One line in NOTES_deepseek5.md: the `SoundArms.patch.txt` of job 15 is superseded by
    `tests_deepseek5_job17/SoundArms_full.patch.txt` (kimi5 read the old file and found the by-value cast).
0d  `git status --short` AFTER that commit, pasted: no `??` line inside your folders.

### Part A (30 minutes): kimi5's step mask. Does step 1 drop anything at an in-check node?
A1  A FRESH copy of the base. Apply kimi5's three patches in the order their first lines name (SoundArms,
    SoundRegret, SoundSteps). Commit the output of the three apply commands. If one does not apply: that is
    a finding; Part A ends there (the JOB does not) and you go on with Part B.
    The build with no option: bench 11 = 312,866, bench 13 = 862,329, `go perft 5` = 4,865,609. The names
    SoundStepMask, SoundRegretCount, SoundRegretProbe in the `uci` list.
A2  Rows on O with exact sums. My own engine's numbers too: none 12,573,318; SoundMatePruning true
    12,558,811; SoundPvArm 1: 12,399,593; SoundInCheckArm 1: 12,326,599. kimi5's, not mine: SoundMatePruning
    true + SoundStepMask 0 equals none on 200 of 200; SoundMatePruning true + SoundStepMask 1: 11,944,468;
    SoundPvArm 1 + SoundStepMask 1: 11,944,468.
A3  THE QUESTION. Three runs for which nobody has a number. BEFORE you run them, commit a file
    `prediction.txt` with one line each: "equal to <which row of A2> on 200 of 200: yes or no", and why.
        X1  SoundInCheckArm 1 + SoundStepMask 1      (the in-check case exempt from step 1 only)
        X2  SoundMateAlphaArm 1 + SoundStepMask 1    (the mate-score case exempt from step 1 only)
        X3  SoundInCheckArm 1 + SoundStepMask 62     (the in-check case exempt from every step BUT step 1)
    If X1 equals none on 200 of 200 and X3 equals "SoundInCheckArm 1" on 200 of 200, then step 1 drops no
    move at an in-check node of this tree, and kimi5's 505 per 1,000 counts moves that were searched anyway.
A4  The counter that settles it, in a scratch copy (counter only: the sum on O must stay 12,573,318, say
    so). At every in-check node, from the moment step 1 sets its skip flag: the quiet moves that still come
    out of the move picker, split into (a) searched and (b) skipped. Name file and line where the picker, in
    check, obeys or ignores that flag. Compare a + b with kimi5's 16,452 (its runs_O/k5_j5_cnt_d12.json,
    the sum of field d20).
A5  Sanitizers (address + undefined) on the patched build: 50 positions of O at depth 10, once with
    SoundMatePruning true + SoundStepMask 1 and once with SoundRegretCount true. Your planted-fault control
    first, as in your earlier jobs.

### Part B (the time that is left): job 16 Part C, done right
The shallower half from the SB fields, sets O and G: events per excess class, and the four verdicts adding
up to the events in every row. Known answer: every class above 40 is empty (WRONG 1). If the SB fields are
not in your counter build's output, say so and print what IS there; do not fill the table from db fields.

### The report
First three lines: (1) Part 0: done or not, with the `git status` line; (2) X1, X2, X3: your prediction and
the result of each; (3) one sentence: is the in-check step-1 cell real, and what shows it. Then the usual
sections (table of steps with evidence files, what you did not do, what you are not sure about, a better
way). Times: stamps.txt pasted. No interval and no ratio in the first three lines unless a committed script
printed it. No pull request, no engine source change in the repository: patches and scratch copies stay on
your machine, text files in your folder.
