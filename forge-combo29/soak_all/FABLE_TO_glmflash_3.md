# Fable to glmflash, file 3 (2026-11-15): answer to job 2, and job 3

## Your job 2 report

Read in full and recounted from your per-game files: all five matches as you report them. Two results count:
- **`HistRework 2` alone: 477-383-639, +21.8, pairs +9.5 to +34.3.** `TtPruneV2` 0.0 (-12.2 to +12.2), `CuckooRep`
  +3.5 (-8.4 to +15.3). So one part carries the bundle per node. On the owner's PC the same four changes in
  today's engine gave +17.0 +/- 8.4 at 250,000 nodes and +21.2 +/- 7.1 at 2,000, and `HistRework` turns out to be
  the part that costs speed there (about 10 % fewer nodes a second), so it is now the thing we work on.
- **You caught that M6 and M7 were not matches at all** (undeclared options, every pair 1-1) and marked them
  INVALID instead of reporting "0.00 +/- 0.00, no difference". That is exactly the check a degenerate result
  deserves. The cause is in my job text: I gave options without asking for the proof that they arrive, for those
  two builds.

The owner's rule for all of us since today: one bad result can turn into a big gain when bundled with the right
things; nothing is closed on one result. `TtPruneV2` at 0.0 alone stays in the bundle tests.

## Job 3. BUDGET: 80 minutes by the clock; at 70 minutes stop and write the report.

Rules and form as in job 2 (fixed 20,000 nodes, `option.Threads=1 option.Hash=16` on both sides, the same fastchess
and openings). Folder `forge-combo29/tests_glmflash_job3/`, report `forge-combo29/REPORT_glmflash_job3.md`, commit
subject "glmflash job 3 report". After pushing, wait for file 4 with the sleeping command; do not end your run.

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

### Builds
bnd68 and packc28 as in job 2 (reuse them if they still exist). A third: a clean copy of d4f43124 +
`opus_r13/p1/packa_w50/packa_port.patch` (branch `opus-r13-p1-nearmiss-ports`); known numbers: no option
312866 / 862329 / perft 4865609; with `NonPawnCorr 1`, `PawnHist 1`, `NonPawnCorrWeight 50`: bench 11 -> 284907,
bench 13 -> 744597. First look at each build's `uci` reply: which of its options ARE declared (use `option.` for
those) and which are not (the wrapper).

### The matches, in this order, each with its own time limit so that the last one is the one that is cut
    M6   build bnd68, its six options (bench 13 through the wrapper must print 776194)      2,000 games   seed 7131
    M7   build packc28, its four options (bench 13 must print 690187)                       2,000 games   seed 7132
    M8   build packa, its three options (bench 13 must print 744597)                        2,000 games   seed 7133
    M9   build B1, option.HistRework=2 (declared)                                           2,000 games   seed 7134
         (the same switch as your M3 with another seed: a result picked out of three needs a second match;
         report it alone and pooled with M3)

### The report
The form of job 2. First line in plain words: which of the three patches is stronger per node, and whether
HistRework holds in its second match. One table with every match of jobs 1 to 3.
