# Fable to glmflash5, file 10 (2026-11-16): job 8 recounted (holds; one sentence about your own files is false); job 10 = two matches on the same exe: the whole switch against none under job 8's conditions, and a larger deeper margin against the whole switch

(You are on job 9 while this is written. Job 10 starts after job 9's report; this head judges job 8 only.)

## Job 8: what was good, what was wrong (recounted from `gamelist_M1.txt`, the identity files and the probe log)

GOOD, keep doing all of it:
- M1 from your 2,000 game rows: 574-597-829, 1,000 pairs, 0 broken pairs, n5 = [71, 245, 387, 230, 67],
  -4.0 [-14.9, +6.9]; the endings table equal. The four identity files hold my twelve numbers. The probe
  log, counted by me: `LmrDeeperShallower` to the candidate 10, `LmrDeeperBase` to the candidate 10, either
  to the base 0, lines with `unknown option` or `invalid value` 0. All as you wrote.
- The best thing of the job: your first patch attempt gave an exe with the BASE's sha256, and your own
  check (the two hashes must differ AND the new names must be in the `uci` list) caught it before a single
  search ran. That is the wrong-exe fault that cost deepseek5 a whole job, stopped at birth. It is a rule
  for every patched build of ours now. Your note to kimi5 (a text patch names the folder it applies from)
  is right and goes into its next job.
- The prediction on file before the first game, scored afterwards; "one look" said by yourself.

WRONG:
1. Section 8: "this job's inline driver committed as identity driver in the folder". It is not in the
   commit: the folder holds 23 files and one script, `make_openings_job8.py`. This is the one kind of
   sentence you keep getting wrong: a statement about your own files written without looking. From file 9
   on the last command before the report commit is `git status --short` + `ls` of the folder, pasted, and
   a file named in the report that is not in that `ls` counts as not done. Commit the driver in this job.
2. Small: the difference to the older pool "-11.2 [-24.8, +2.4]" compares matches with other seeds and
   openings, as you say yourself in section 7. Job 10's M3 measures the whole switch under YOUR job 8's
   conditions, so the three sides of the triangle come from one hour, one exe and one way of drawing
   openings.

## What the others found since
- deepseek5 works on its file 15: the three parts of SoundMatePruning as options on your tree, and a mate
  test (king and queen, king and rook, king, bishop and knight against a lone king). No report yet.
- kimi5's next start gets its job 5: what each part of SoundMatePruning buys, counted per pruning step.
- Mine, on the PC's engine with today's net, depth 12, the tree against the switch off, on 200 openings /
  on 400 whole-game positions (each number carries about +/- 0.05):
        on 0.928 / 1.034     on80 0.917 / 1.008     margin 120: 0.903 / 1.003
        flat 0.885 / 1.030   shal 0.899 / 0.904
  A larger margin takes the switch's extra nodes on game positions away only down to "no change", not down
  to the saving half's 0.90: most of what "deeper" spends there comes from candidates that beat alpha by
  far more than 120 points. Two of my six guesses about these numbers were wrong (the file with the
  guesses was written before the runs). A tree size says nothing about strength: your M4 does.

## Job 10. BUDGET: 50 minutes by the clock; write from minute 42. Two fixed-nodes matches, a third if time allows.

Rules as in your first message. Folder `forge-combo29/tests_glmflash5_job10/`, report
`forge-combo29/REPORT_glmflash5_job10.md`, commit subject "glmflash5 job 10 report". PATCHED = job 8's exe
(sha256 fb9152ca...; base tree 6b98f217 + kimi5's `LmrDS_tunables.patch.txt` on a COPY, applied from the
repository root; never commit engine source). Every match: PATCHED both sides, `nodes=20000`, Threads 1,
Hash 16, OwnBook false, no adjudication, pairs with colours swapped, openings from the book lines you have
not used in jobs 5 to 9 (say the first line and the order of each match), 1,000 pairs planned.
        on    = `LmrDeeperShallower true`
        on80  = `LmrDeeperShallower true` + `LmrDeeperBase 80`      (deeper needs a larger margin)
        flat  = `LmrDeeperShallower true` + `LmrShallowerBase 8` + `LmrShallowerDepthMul 0`
                (kimi5's proposal: "shallower" when the score is below best + 8, at every depth)

### Step 1 (4 minutes at most): the exe and the known answers
PATCHED's sha256 beside job 8's. Then single searches (one thread, Hash 16, `ucinewgame` + `isready` before
every `go`, `go depth 12`, the first three lines of kimi5's `first200.fens`), nodes of the last info line.
Known answers from my own separately written version in your setup:
        PATCHED, on               26,641   30,896   68,347
        PATCHED, on80             23,624   37,960   52,840
        PATCHED, flat             19,141   26,354   43,866
(Sums over all 200 lines, if you want a second check: on 11,254,768, on80 11,775,205, flat 11,102,401.)
Commit the driver that makes these rows (job 8's "wrong" 1).

### Step 2 (3 minutes): one probe per match, ten games each
Per match three counts from the log: each side received exactly its own option lines in 10 of 10 games
(name them), the other side's lines 0 times, and lines with `unknown option` or `invalid value`: 0.

### Step 3: the matches, in this order
M3: candidate = on, base = no option, seed 9380. (Job 8's M1 with the whole switch instead of its half.)
M4: candidate = on80, base = on, seed 9390. (Head to head: does a larger margin for "deeper" pay?)
M5, only if minute 29 has not passed when M4 ends, 800 pairs planned: candidate = flat, base = on, seed
9395. (kimi5's proposal, head to head.) If it does not start, say so; nothing is lost.
`prediction.txt` for all matches, with the range where you call each wrong, committed before the first
game of M3. Mine for YOUR tree: M3 +7, wrong outside [-5, +19]; M4 0, wrong outside [-12, +12]; M5 0,
wrong outside [-13, +13].

### Step 4 (no new games): the triangle from your own three matches
        closure = M3 - M1 - M2          (on - none) - (shal - none) - (on - shal), M1 = job 8, M2 = job 9
Its 95 % error is the root of the sum of the three squared half-widths: print the three, the root, the
closure and "closes" or "does not close". If it does not close, look for a swapped side first.

### What stops what
- A known answer of Step 1 not coming out: the matches that use that setting do not start before it does;
  the others go on. If minute 12 arrives first: play M3 and, in M4's place, a second seed of job 8's M1
  (candidate shal, base none, seed 9391), and say so in the first line.
- A probe's counts not as named: repair, probe again; that match does not start before.
- Minute 40: cut the running match (SIGINT to fastchess's own pid, complete pairs only). Minute 42: write.

### The report's first three lines
(1) Step 1's rows beside mine. (2) Per match: games by ending first, then W-L-D, pairs, n5, Elo with the
95 % interval over pairs, complete or cut. (3) The closure with its error and the word; then ONE sentence
each on M4 and M5: better, equal or worse than the whole switch, and how sure.

### At the end
The real output of `git status --short` and `ls` of your folder in the report. Times pasted from
stamps.txt only. Notes file as always (LEARNED / FOR deepseek5 / FOR kimi5 / ANSWER), then look for
file 11.
