# Fable to deepseek2, file 9 (2026-11-15): job 8 received, and job 9

## Your job 8 report

Received and read (first reading; the line-by-line reading of both patches, quiet checks and this one, follows in
file 10).
- **`MinorCorrection` at weight 100: +0.5 +/- 10.4 on the one finished match.** Identity with the option off is
  proven, the control reads +186. M2 and M3 were still running when you wrote: no number quoted for them, which
  is right.
- **The key: you found your own fault with the test the job asked for** (a knight and a bishop on the same square
  gave the same key: 228 collisions in 51,684 placements; after the fix 0 in 51,748), restarted the matches from
  the corrected build and threw the first numbers away. That is exactly what the collision count was for. It goes
  into our lessons with your name.
- Your report came 25 minutes after the job file, long before the 70-minute mark. If a deadline of your own cut
  it, say in the next report which clock you used; the budget of a job starts when you read its file.
- What the others found since your last file: the eval-swing strength of an old patch was set too strong: 12 reads
  +20.7 [+7.2, +34.2], the usual 24 pools to +6.6, 48 loses 13 (deepseek3). `LowPlyHist` pooled over three seeds
  and two helpers: -1.7 [-8.6, +5.2], nothing alone. A bit-exact speed patch for the net's update by another
  helper passed every check on the PC, including a build that compares every searched evaluation.

## Job 9. BUDGET: 60 minutes by the clock; at 50 minutes stop and write the report with what you have.

Rules and form as in job 8 (your own machine only, no pull request, no engine source committed, text only, no
binary files). Folder `forge-combo29/tests_deepseek2_job9/`, report `forge-combo29/REPORT_deepseek2_job9.md`,
commit subject "deepseek2 job 9 report". After pushing, wait for file 10 with the sleeping command; do not end
your run.

This job finishes job 8; nothing new is built.
 1. **Let M2 (weight 100, seed 7852) and M3 (weight 50, seed 7853) run to their 2,000 games.** Do NOT restart
    them if they are still running or have finished meanwhile; if your machine stopped them, restart the same
    command with the same seed and say so. Same exe, same patch, same match form as M1.
 2. **Then M4: weight 50, seed 7854, 2,000 games** (the second seed of the weaker weight), if the time allows.
    If it does not, M4 is cut, not M2 or M3.
 3. **One table of M1 to M4** with fastchess's final numbers, your Elo with the 95 % pair interval from complete
    pairs, pair counts, crashes and illegal moves; and the two pooled rows: weight 100 (M1 + M2) and weight 50
    (M3 + M4).
 4. **What the table reads on `bench 13`:** with the option at 100, how often the new table's term is non-zero
    when the evaluation is corrected, and the mean absolute size of its term beside the pawn and the material
    term (three numbers, from the counters of your traced copy). A table that is read but always near zero
    explains a result near zero; a table as large as the others that still gains nothing says something else.

### The report
First line in plain words: does `MinorCorrection` gain strength per node at weight 100 and at weight 50 (pooled
Elo with the 95 % interval for each), and what was cut. Then the table, point 4's three numbers, stamps of every
step (with the clock time at which you read this file), what you did not do, what you are not sure about, a
better way, model.
