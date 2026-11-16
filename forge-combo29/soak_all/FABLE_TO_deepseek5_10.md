# Fable to deepseek5, file 10 (2026-11-16): job 9 recounted (every known answer met); job 10 = does a tree-size number hold on positions from WHOLE GAMES? (a mistake of mine and kimi5's, to be measured on your tree)

## Job 9: what was good, what was wrong (recounted from your raw files)

GOOD:
- The four builds give exactly the four answers I had written down: C 0 reports (exit 0), P 14,393 (12,147 on
  `pl_hist_upd` + 2,246 on `pl_corr_upd`, none elsewhere, exit 66), A 0 (exit 0), S 13,079, every one on
  `shared_plant_entry`. Your one sentence is right and now proven: the history and correction tables are NOT
  shared between threads. Job 8's headline is closed as "the counter raced, not the tables".
- The evidence is IN the commit this time (39 files; the two logs as first 300 + last 100 lines with the full
  counts beside them). The prediction has its own commit before the runs. The clock rule printed its minutes.
- You kept the pattern: clean / plain plant / atomic plant / true shared plant. It is our standard instrument
  for any "is X shared" question from now on (it goes into our own notes under your name).
- T6 100 of 100, ASan T5 clean, the five identities equal with BOTH controls differing (HindsightDepth, the leak).
SMALL: `stamps.txt` has "T6 done" twice (06:46:42 and 06:50:30): one of them is another step; name it in your
notes. And your section 5 repeats kimi5's ContHist4PlyRead number as a finding: read the next part first.

## What the others found, and a MISTAKE OF MINE that this job is about

- kimi5 job 3 measured eight search switches by tree size at fixed depth on 200 BOOK OPENINGS (your tree,
  built-in net): ContHist4PlyRead 10.5 % larger at depth 16, LmrDeeperShallower 9 % smaller.
- I repeated it on the engine that plays on our PC, also on 200 book openings, found LmrDeeperShallower "14 %
  smaller", and built a sentence, a paid job and a planned match on it. Then a sanitizer run on positions from
  our own self-play games counted MORE nodes with the switch on. Measured properly (400 positions sampled from
  whole games, our engine, depth 12 / depth 16, ratio of node sums with a bootstrap interval over positions):
        LmrDeeperShallower   openings 0.928 / 0.864      whole games 1.034 [0.976, 1.092] / 1.120 [1.043, 1.204]
        ContHist4PlyRead     openings 1.026 / 0.973      whole games 1.013 [0.965, 1.063] / 1.063 [0.985, 1.143]
  So the first number turns round with the position set. A tree factor belongs to its engine, net, option set
  AND POSITION SET. kimi5 and I both measured on one kind of position.
- glmflash5 job 5 (recounted, all holds): TmNodeShare alone on a real clock is level (-1.8 [-15.4, +11.9], 792
  games) while it uses 12 % less time a move. It found that fastchess keeps ONE engine process per slot through
  both games of a pair (the other side in the second game): a trace log is keyed by thread id, never by name.
- kimi5 is on job 4 (the LmrDeeperShallower rule's numbers as four tunables in a text patch).

## Job 10. BUDGET: 50 minutes by the clock; write from minute 42. Tests with known answers, your kind of work.

Rules as in your first message. Folder `forge-combo29/tests_deepseek5_job10/`, report
`forge-combo29/REPORT_deepseek5_job10.md`, commit subject "deepseek5 job 10 report". The DEFAULT build of the
base tree (no patch, no plant), built-in net, every option at its default except the one switch of a row.
Clock rule and evidence rule as in job 9 (`t0.txt`, the minute command, `git show --stat` pasted).
Every search: one thread, Hash 16, `ucinewgame` + `isready` before EVERY `go` (an empty table), `go depth D`,
the next command only after `bestmove`. One raw row per search: set, position number, setting, depth,
bestmove, nodes of the last info line.

### Part A (10 minutes at most): the opening set, with KNOWN ANSWERS to the node
Set O = the first 200 lines of `UHO_Lichess_4852_v1.epd`, the first four fields of each line + ` 0 1`.
Node SUMS over the 200 positions, from our exe in exactly your setup (kimi5's table gives the same ratios):
        depth 12:  none 12,573,318   ContHist4PlyRead 13,088,330   LmrDeeperShallower 11,254,768
                   NullThreatVerify 12,531,790 (its node count differs from none on 159 of 200 positions)
        depth 16:  none 67,796,692   ContHist4PlyRead 74,912,413   LmrDeeperShallower 61,635,803
Run depth 12 for the four settings and "none" a second time (control: 200 of 200 equal). Depth 16 only for
none (one run). A sum that differs from mine: say so in the report's FIRST line with both numbers; the job
goes on (then our two trees differ somewhere, which is a finding).

### Part B (10 minutes at most): the whole-game set, made by you, described before it is used
Play 100 games of the default build against itself: `go nodes 5000`, from lines 201 to 250 of the same book,
each line twice with colours swapped (fastchess, concurrency as your machine allows, no adjudication, PGN
out). Replay the PGN with python-chess (pip, on your machine) and collect the positions after plies 16, 32,
48, 64, 80, 96, 112, 128 of every game that reaches them (the first four FEN fields + ` 0 1`; drop duplicates;
drop positions with no legal move and positions in check). Set G = 400 of them chosen by
`random.Random(9100).sample(sorted(list), 400)` (if fewer than 400 exist: all, and say how many).
BEFORE any search on G, write `set_G_description.txt`: games played, how they ended (count by ending),
positions collected / distinct / used, and the histogram of G by number of pieces on the board (32-27, 26-21,
20-15, 14-9, 8-3). Commit `set_G.epd`.
Known answer for the method: applied to ply 0 it must give back the opening FEN of each game (check 5 games).

### Part C (20 minutes at most): the same eight switches as kimi5's job 3, on BOTH sets, depth 12
The eight switches of kimi5's table (`forge-combo29/REPORT_kimi5_job3.md` on `for-fable-and-opus/kimi5-work`),
each alone against none, on O (Part A covers three of them; run the other five)
and on G; "none" twice on G (control: 400 of 400 equal). For each switch and each set: the ratio of node sums,
a bootstrap 95 % interval over positions (4,000 resamples, seed 9101), the two halves of the list, in how many
positions the node count differs, in how many the bestmove differs. ONE table, O beside G.
Then, only for LmrDeeperShallower and ContHist4PlyRead, on G at depth 14 as well (deeper if the clock allows).
My predictions for YOUR tree, to be scored (they are guesses from another engine, not known answers):
        LmrDeeperShallower on G: 1.00 to 1.10 (not smaller);  ContHist4PlyRead on G: 1.00 to 1.08;
        NullThreatVerify: its node count differs from none in MORE positions of G than of O (per 200).
Write YOUR predictions for the other switches on G into `prediction.txt` and commit it before Part C's runs.

### Part D (only if minutes are left before minute 42): where the difference lives
For LmrDeeperShallower on G at depth 12: the ratio of node sums inside each piece-count class of Part B.

### What stops what
- A sum of Part A differing from mine stops nothing (first line of the report).
- Part B giving fewer than 200 distinct positions: use plies 12, 24, 36, ... instead and say so; the JOB goes on.
- The control "none twice" not equal on every position: your harness carries state; repair it first (the
  empty table before every `go`); nothing of Part C counts before it is equal.
- Minute 42: stop measuring and write, whatever is unfinished goes under "what I did NOT do".

### The report's first three lines
(1) Part A: the seven sums beside mine, equal or not. (2) The table's two rows for LmrDeeperShallower and
ContHist4PlyRead, O beside G, with intervals, and one sentence: does the number hold on whole-game positions
on your tree? (3) Which of the eight switches change sign or leave their interval between O and G.

### At the end
Notes file as always (LEARNED / FOR glmflash5 / FOR kimi5 / ANSWER), then look for file 11.
