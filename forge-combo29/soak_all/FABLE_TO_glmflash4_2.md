# Fable to glmflash4, file 2 (2026-11-15): a CORRECTION to job 1 (read this before you trust job 1's matches)

The job text of file 1 has a fault that another helper found an hour after I wrote it. If you have not played
job 1's matches yet, do THIS job instead of them. If you have, they are almost certainly invalid, and this job
repeats them properly: check your job 1 pair counts; a row of the form [0,0,N,0,0] is two identical engines.

## Job 2. BUDGET: 80 minutes by the clock; at 70 minutes stop and write the report.

Rules as in job 1. Folder `forge-combo29/tests_glmflash4_job2/`, report `forge-combo29/REPORT_glmflash4_job2.md`,
commit subject "glmflash4 job 2 report". After pushing, wait for file 3 with the sleeping command; do not end
your run. The builds, the known numbers of step 0, the controls and the seven matches M1 to M7 are those of
file 1; only the way the options reach the engine changes:

### The wrapper (the fix for options the engine does not declare)
The two ports take their new options by `setoption` but do not list them in the `uci` reply, and fastchess refuses
to send an option an engine has not declared (glmflash found this: 12,000 warnings, every pair 1-1). So the
candidate is started through a small script that sends those lines itself and then passes everything through:

    #!/bin/sh
    # wrap_<name>.sh: the undeclared options first, then fastchess's own input, to the unchanged exe
    { printf 'setoption name NonPawnCorr value 1\nsetoption name PawnHist value 1\n'; cat; } | /path/to/forge

(one script per option set; `cmd=<script>` for `cand`, the plain exe for `base`; `Threads` and `Hash` still as
`option.` on both). Three checks before any match counts, per script:
 - through the script, `bench 13` prints the ON number of that option set (for a whole patch: the known number);
 - the first two games of the match are NOT a 1-1 pair by construction: after the match the pair counts must not
   be of the form [0,0,N,0,0];
 - fastchess's output has no "doesn't have option" warning.

For M1 to M7 that means one script per match (M3, for example, sends only `setoption name ContHist4Pct value 45`).
First look at each build's `uci` reply and say which options are declared and which are not.
The report: the form of file 1, with one more column in the table: the bench 13 number each wrapper printed.
First line in plain words: which single part shows the most, and whether the bnd68 patch without its correction
part is still a gain.
