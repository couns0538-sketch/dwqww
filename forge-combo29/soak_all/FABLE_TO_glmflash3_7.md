# Fable to glmflash3, file 7 (2026-11-15): job 6 received, and job 7

## Your job 6 report

Received and read (first reading; the full reading of jobs 3 to 6 follows in file 8).
- **The pair at 80,000 nodes, first number: +17.0 [-3.4, +37.5] (450 games). Eval swing 12 alone, pooled over
  its two seeds: +16.1 [+4.0, +28.3].** So at depth the swing term at strength 12 is established on your plain
  tree, and the pair is so far not more than the swing term alone (+17 against +16, both wide). That is the
  same picture the history pair gave another helper tonight (two terms, +9.0 together, no more than the better
  half): a sum of two gains must be measured, never added.
- Good: the first paragraph says what was cut and why, with the measured rate (0.54 games a second against the
  predicted 0.56), and the new bench number is set against the two halves' numbers (776151 against 649268 and
  748790), which shows that each half acts inside the pair.
- Two things to repair in your chain script, both from your own section 9: the control's probe ran AFTER its
  match again (put the probe call into the template, before every match, so it cannot be forgotten); and the
  table of section 4 carries the three job-6 rows twice (the second commit filled placeholders and left the
  first copies in). A table that is pushed with placeholders is a report that is not finished: write the file
  once, when the numbers exist.
- What your real window is: about 28 minutes of matches after the control, whatever the budget line says. Job
  7 is sized for that.
- NOTE: both sessions on the PC sleep from about 23:00 to 02:00 UTC tonight. If no file 8 comes after your
  report, keep waiting with the sleeping command as long as your run allows; the owner restarts you in the
  morning with your restart line, which finds the newest job by itself.

## Job 7. BUDGET: 60 minutes by the clock (from the moment you read this file); at 50 minutes stop and write.

Rules, tree, build and match form exactly as in jobs 5 and 6 (commit d4f43124 plus the packc28 port alone,
built with `-DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1`; `option.Threads=1 option.Hash=16`, `OwnBook
false`, UHO openings each twice with colours reversed, `order=random` with `-srand <seed>`, no adjudication, a
2-game probe BEFORE every match; no pull request, no engine source committed, text only). Folder
`forge-combo29/tests_glmflash3_job7/`, report `forge-combo29/REPORT_glmflash3_job7.md`, commit subject
"glmflash3 job 7 report". After pushing, wait for file 8 with the sleeping command; do not end your run.

### The question
The Asp rule is the half the PC may really adopt, because it costs no speed (the swing term costs 5.5 % of the
nodes a second there). At depth it has ONE seed (+8.3 [-6.6, +23.2]). This job gives it the second seed, and
then asks what it adds on top of the swing term.

### The matches (the same exe on both sides), in this order, no other match
    C     control at 20,000 against 10,000 nodes, no options, 100 games, seed 7370: near +200 (it only shows
          that the harness works; take the games per second from your job 6 figures, not from these 100 games)
    F1    nodes=80000   cand AspFailHighReduce=1 AspFailHighMaxReduce=3, base none            800 games   seed 7363
    F2    nodes=80000   cand the Asp pair + EvalSwingMult=12 EvalSwingMax=200,
                        base EvalSwingMult=12 EvalSwingMax=200 alone                          as many games as fit, up to 800, seed 7364
F1 is played to its full 800 games before F2 starts, even if F2 then gets nothing: one finished match is worth
more than two halves. F2 is stopped by the clock on a complete pair; under 200 games it is reported as "too
short to say anything".
Before the matches: `bench 13` with no option (862329) and with the Asp pair alone (your job 5 number 649268)
as the check that the build is the same one.

### The report
First line in plain words: the Asp pair alone at 80,000 nodes POOLED over seeds 7351 and 7363, with both seeds
and the pooled 95 % pair interval; then what F2 says, or that it was not reached. First paragraph: what was cut.
One table of all matches of jobs 5 to 7 at 80,000 nodes, every row once; the probes (each BEFORE its match:
give the two stamps); stamps; what you did not do; what you are not sure about; a better way; model.
