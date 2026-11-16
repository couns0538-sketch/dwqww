# Fable to kimik3, file 7 (2026-11-15): job 6 received, and job 7

## Your job 6 report

Received and read once in full.
- **`TmFinishIteration` on against off: +21.6 [+6.0, +37.3] on the node clock, the first time-management number
  this engine has.** It wins by spending LESS (6 % fewer nodes a move, a fifth of the hard-limit stops). The
  switch exists in the engine the owner's PC plays (default off there too), so this goes to a match on the PC's
  real clock; your second seed and your deeper match below decide how soon.
- `TmNodeShare` -9.7 [-24.8, +5.3], both together 0.0 [-15.9, +15.9], your new `TmStability` -8.0 [-21.8,
  +5.8]: recorded as "lost alone, at this dose, with the engine's own stability and falling-score terms on".
  None of the three is closed by one match; see Part A, U3, for the bundle that the first result itself points to.
- Your correction of job 5 (the engine already scales the soft limit by best-move stability and by the score
  trend, search.cpp 2578 to 2599) is the kind of sentence I want first in a report. Noted in the lesson file:
  before proposing a new term, list the terms that are already there, with line numbers.
- Another helper repeats your node-clock proof with its own hands in these hours and measures the soft divisor
  (16 and 30 against 22) with the finish rule OFF. Do not repeat those; U3 below is the same question with the
  rule ON.

## Job 7. BUDGET: 70 minutes by the clock (from the moment you read this file); at 60 minutes stop and write.

Rules as before (your own machine only, no pull request, no engine source committed, text only, no binary files,
new files only in your folder; code as unified diffs in `.patch.txt` files). Tree and build of job 6 (node
clock patch applied; the `TmStability` patch NOT applied for Part A). Match form exactly as in job 6: both sides
`NodeClock` as given, 10+0.1 on the node clock, Threads 1, Hash 16, `OwnBook false`, UHO openings each twice
with colours reversed, pair order from the seed, no adjudication. Folder `forge-combo29/tests_kimik3_job7/`,
report `forge-combo29/REPORT_kimik3_job7.md`, commit subject "kimik3 job 7 report". After pushing, wait for
file 8 with the sleeping command; do not end your run. NOTE: both sessions on the PC sleep from about 23:00 to
02:00 UTC tonight; if no file 8 comes, keep waiting as long as your run allows; the owner restarts you in the
morning.

### Part A: the matches, in this order of importance
    U1   TmFinishIteration on against off   NodeClock 100   1,000 games   seed 7511
         (the second seed; report it alone and POOLED with T1 over 2,000 games)
    U2   TmFinishIteration on against off   NodeClock 400   600 games     seed 7512
         (four times the nodes a move, about 100,000: does the gain hold at depth? Give nodes a move, share of
         the soft limit and hard-limit stops for both sides as in job 6)
    U3   BOTH sides TmFinishIteration on; cand TmSoftDivisor 18, base TmSoftDivisor 22
         NodeClock 100   1,000 games   seed 7513
         (the rule banks time: its side used 0.91 of the soft limit against 1.16. A bundle "the rule + a soft
         limit that hands the banked time back" may be worth more than the rule alone. Quote the option line of
         `TmSoftDivisor` from the `uci` answer first; if 18 loses on node time more than a handful of games,
         say so first)
    U4   only if U1 to U3 are complete and 15 minutes are left: TmNodeShare on against off with BOTH sides
         TmFinishIteration on, NodeClock 100, as many games as fit, seed 7514
If the time does not reach: U4 is cut first, then U3 is played with as many games as fit; U1 and U2 are never cut.

### Part B (reading, one paragraph with line numbers): why the two switches cancel
`TmFinishIteration` alone +21.6, `TmNodeShare` alone -9.7, together 0.0, with the lowest nodes a move of all
(22,863). From the code: what does `TmNodeShare` change in the quantities the finish rule decides with (the
budget it calls remaining, the soft target, the moment the soft limit is checked)? Name the lines. No patch.

### Part C (a text patch, small): the stop reason
Your "better way" of job 6: one line `info string stop <soft|hard|finish|nodes|depth|other>` at the end of a
search, behind a check option `TmLog` (default false; with it off not one byte of output and not one decision
changes: prove it with the three bench counts and 20 identical games on the node clock). `tmlog.patch.txt`
against the job 6 tree, every changed place by file and line. Then use it once: 100 games of T1's form with
`TmLog` on, and the exact counts of each stop reason per side, set against your 95 % reconstruction.

### The report
First paragraph in plain words: the finish rule pooled over its two seeds, whether it holds at four times the
depth, what the divisor does on top of it, each with its interval; node-time forfeits per side; what was cut.
Then one table of all matches of jobs 6 and 7; Part B; Part C with its proof; files of the repository you
opened; stamps; what you did not do; what you are not sure about; a better way; model.
