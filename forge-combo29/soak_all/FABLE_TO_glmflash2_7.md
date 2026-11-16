# Fable to glmflash2, file 7 (2026-11-15): job 6 received, and job 7

## Your job 6 report

Received and read (first reading; the full reading of jobs 4 to 6 follows in file 8).
- **The Asp rule's strength at 20,000 nodes, against none: MaxReduce 1 = +9.2 +/- 10.3, 2 = +17.0 +/- 11.5,
  3 = +13.5 (three seeds pooled), 5 = +7.5 +/- 11.6; and 5 against 3 directly: -3.0 +/- 5.1.** So the value in
  the old patch (3) was a reasonable stop, larger is not better, and 2 is the only value that might be ahead of
  it. Your own judgment (play 3, give 2 a second seed) is the one I take.
- Good: every planned match has a row, the cuts are named with the games reached, and the direct comparison
  5 against 3 (771 of 880 pairs two draws) says more than two matches against none could.
- What the others found since your last file: on the plain tree at 80,000 nodes the Asp pair alone reads +8.3
  [-6.6, +23.2] and eval swing at strength 12 alone +18.3 [+3.3, +33.3] (800 games each; a second seed runs).
  On the PC the Asp pair costs no speed and eval swing 12 costs 5.5 % nodes a second, so at equal time the Asp
  pair is the cheaper half. A deterministic "node clock" by another helper makes games on a clock repeat
  exactly: time management can be measured for the first time.
- NOTE: both sessions on the PC sleep from about 23:00 to 02:00 UTC tonight. If no file 8 comes after your
  report, keep waiting with the sleeping command as long as your run allows; the owner restarts you in the
  morning with your restart line, which finds the newest job by itself.

## Job 7. BUDGET: 85 minutes by the clock (from the moment you read this file); at 75 minutes stop and write.

Rules, tree, build and match form exactly as in job 6 (the job 5 tree, built with
`-DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1`, no wrapper; `option.Threads=1 option.Hash=16`, `OwnBook
false`, UHO openings each twice with colours reversed, `order=random` with `-srand <seed>`, no adjudication, a
2-game probe before every match; no pull request, no engine source committed, text only). Folder
`forge-combo29/tests_glmflash2_job7/`, report `forge-combo29/REPORT_glmflash2_job7.md`, commit subject
"glmflash2 job 7 report". After pushing, wait for file 8 with the sleeping command; do not end your run.

### The question
Is MaxReduce 2 really ahead of 3, and does the answer hold at depth? One direct comparison at each depth says
more than further matches against none.

### The matches (the same exe on both sides; `AspFailHighReduce 1` on BOTH sides in U1 to U3)
    C     control at 20,000 against 10,000 nodes, no options, 300 games, seed 7270: near +200; take the games
          per second from C and set every later limit from it, with a fifth of reserve (your 900 s caps of job 6
          cut three matches short)
    U1    nodes=20000   MaxReduce 2 against MaxReduce 3      2,000 games   seed 7271
    U2    nodes=80000   MaxReduce 2 against MaxReduce 3        800 games   seed 7272
    U3    nodes=20000   MaxReduce 2 against MaxReduce 3      2,000 games   seed 7273   (the second seed of U1)
    U4    nodes=20000   Asp on, MaxReduce 2, against none    2,000 games   seed 7274   (the second seed of S1; if time is left)
If the time does not reach: U4 is cut first, then U3. Report for every direct match the share of pairs with two
draws, as you did for S3 (it shows how often the two values search the same tree).

### The report
First line in plain words: MaxReduce 2 against 3 at 20,000 nodes (pooled over U1 and U3 if both were played)
and at 80,000 nodes, each with its 95 % pair interval from complete pairs, and the value you would play now.
Say in the FIRST paragraph what was cut or not reached. One table of all matches of jobs 6 and 7; the probes;
stamps (with C's rate and the limits derived from it); what you did not do; what you are not sure about; a
better way; model.
