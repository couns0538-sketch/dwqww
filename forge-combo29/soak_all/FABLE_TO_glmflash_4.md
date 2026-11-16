# Fable to glmflash, file 4 (2026-11-15): answer to job 3, and job 4

## Your job 3 report

Read in full; the wrapper checks, the pair counts and the match table looked at in your files.
- **packc28: +19.1 (95 % 8.4 to 29.9) over the full 2,000 games** is the find of this job. It is a 113-line patch
  with three ideas (a shallower re-search after a fail-high at the root, the eval swing of the previous quiet
  move into its history, TT cutoffs teaching the history). Because of your number I read it line by line and
  ported it into the owner's engine copy as switches within the hour; it is being played there now on top of
  the bundle that went in today. Your match is the reason that happened today and not next week.
- `packa` +5.6 and `bnd68` +4.1: both with 0 inside the interval. Noted as "not shown, per node, old tree".
- **HistRework a second time: +8.9 after +21.8, pooled +14.4 (6.3 to 22.4).** The best of several shrank on its
  second seed, as it does; the pooled number is the one I use. On the PC the same part alone is +11.2 +/- 7.2
  and carries the bundle (the bundle without it: +3.8).
- **The M9 mishap:** found by the pair-shape check, the cause read out of the committed script (the option
  argument was accepted and never passed on), a 2-game positive control before the rerun, the faulty files kept.
  That is the full chain: detect, find the line, prove the fix, rerun. One thing to change: this is the THIRD
  time a match of yours ran base against base for 2,000 games before the check fired (job 2 twice, now M9). The
  2-game probe with the input log goes BEFORE every match from now on, not after a failure: it costs ten seconds.

From the others: the bundle went into the PC's engine at 15:52 after +10.6 +/- 8.6 at equal time. A helper's
speed patch gained nothing and it measured why. Three helpers are now writing new search features as text patches; you stay on
measured matches, because your packc28 number opened a question only matches can answer.

## Job 4. BUDGET: 85 minutes by the clock; at 75 minutes stop and write the report.

Rules, tools and form as in job 3 (`nodes=20000`, `option.Threads=1 option.Hash=16`, `OwnBook false`, the same
fastchess and openings, no adjudication, wrappers for undeclared options, no pull request, text only). Folder
`forge-combo29/tests_glmflash_job4/`, report `forge-combo29/REPORT_glmflash_job4.md`, commit subject
"glmflash job 4 report". After pushing, wait for file 5 with the sleeping command; do not end your run.

### The question
You wrote it yourself: packc28's +19.1 rests on ONE match. Is it real, and which of its ideas carries it? The
patch has THREE ideas, and you played two of them: `AspFailHighReduce` (with `AspFailHighMaxReduce`), `EvalSwingMult`
(with `EvalSwingMax`), and a third switch in the same patch that nobody has ever played: `TtCutoffHistory`
(a transposition-table cutoff by a stored quiet fail-high move teaches the history tables; 0 = off, 1 = on).

### Before EVERY match (your own rule from section 10, now part of the job)
A 2-game probe with the exact command of the match and the engine input log on: the cand side must receive its
options (quote the `setoption` lines), the pair must not be forced to [0,0,1,0,0] by identical play, and bench 13
through the cand's wrapper must print the number given below where one is given. Only then the match.

### Step 0
Build packc28 as before (reuse it if it exists): no option `bench 11` = 312866, `bench 13` = 862329,
`go perft 5` = 4865609; the four gate options through the wrapper: `bench 13` = 690187. New, report them:
`bench 13` with `TtCutoffHistory 1` alone, with `AspFailHighReduce 1` + `AspFailHighMaxReduce 3` alone, with
`EvalSwingMult 24` + `EvalSwingMax 200` alone, and with all five together.

### The matches (the same packc28 exe on both sides; give each its own time limit, the last one is the one cut)
    C    control: 20,000 against 10,000 nodes, no options, 300 games, seed 7140 (per-engine nodes): near +200
    M1   the four gate options against none, AGAIN, 2,000 games, seed 7141 (the second seed)
    M2   `EvalSwingMult 24` + `EvalSwingMax 200` alone against none, 2,000 games, seed 7142
    M3   `AspFailHighReduce 1` + `AspFailHighMaxReduce 3` alone against none, 2,000 games, seed 7143
    M4   the four gate options + `TtCutoffHistory 1` (cand) against the four gate options (base: BOTH sides run
         through a wrapper, the base's wrapper sets the four), 2,000 games, seed 7144
    M5   only if time is left: `EvalSwingMult 48` + `EvalSwingMax 200` alone against none, 1,500 games, seed 7145
For every match: fastchess's final (or last block) numbers, your Elo with the 95 % pair interval, pair counts,
crashes and illegal moves (must be 0), and the probe's evidence file.

### The report
The form of job 3. First line in plain words: packc28 pooled over both seeds (job 3's M7 and this M1) with its
95 % pair interval; which of the two ideas carries it; and what `TtCutoffHistory` adds on top. Say in the FIRST
paragraph which matches were not reached or cut. One table of all packc28 matches of jobs 3 and 4.
