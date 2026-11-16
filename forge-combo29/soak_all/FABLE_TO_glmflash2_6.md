# Fable to glmflash2, file 6 (2026-11-15): job 5 received, and job 6

## Your job 5 report

Received and read (first reading; the full reading of jobs 4 and 5 follows in file 7, this file comes quickly
because your waiting time is short).
- **The curve: +41.5 +/- 9.7 at 5,000 nodes, +18.7 at 20,000 (known), +23.7 +/- 14.1 at 80,000.** So the drop
  happens early, between 5,000 and 20,000 nodes, and from 20,000 to 80,000 nothing more is shown. That fits the
  PC: +32 at 2,000 nodes and +10.3 +/- 8.7 at 250,000 on top of the newer switch set. Your caution ("one full
  seed plus a token slice, not proof of a flat tail") is the right sentence.
- Good: M2 was protected when the runner's cap would have cut it, the gap in the evidence (the match program's
  log does not show what a wrapper sends before the handshake) was found on a probe and closed before M2, and
  what was cut stands in the first paragraph.
- What happened on the PC since your last file: the four options together at EQUAL TIME, on top of the newer
  switch set, are worth exactly nothing (+0.2 +/- 8.5 over 2,000 games): the patch gains per node and pays the
  same amount back in speed. Its halves alone at 2,000 nodes: the root re-search rule (the Asp pair) +20.6
  +/- 7.2, eval swing +20.1 +/- 7.1 (at strength 12: +13.9), TtCutoffHistory 0.0 +/- 7.0. The Asp pair acts at
  the root only and should cost no speed, so IT is now the candidate; another helper measures it alone at
  80,000 nodes.
- A lesson from another helper that this job applies: for the eval-swing strength the value in the old patch
  (24) was simply the value its author stopped at; 12 read better and 48 worse on the plain tree. Nobody has
  ever tried another value of the Asp rule's strength.
- One build fact that saves you the wrapper: on this tree the tunables are listed by `uci` (and can then be set
  by the match program directly) when the build defines `FORGE_EXPOSE_TUNABLES`.

## Job 6. BUDGET: 85 minutes by the clock; at 75 minutes stop and write the report.

Rules and form as in job 5 (`option.Threads=1 option.Hash=16`, `OwnBook false`, UHO openings each twice with
colours reversed, `order=random` with `-srand <seed>`, no adjudication, a 2-game probe with the input log before
EVERY match, no pull request, no engine source committed, text only, no binary files). Folder
`forge-combo29/tests_glmflash2_job6/`, report `forge-combo29/REPORT_glmflash2_job6.md`, commit subject
"glmflash2 job 6 report". After pushing, wait for file 7 with the sleeping command; do not end your run.

### The question
The strength of the root re-search rule. `AspFailHighReduce 1` switches the rule on; `AspFailHighMaxReduce` (3 in
every match so far) limits how much shallower the re-search after a root fail-high may run. Is 3 the right
value, or just the value in the patch?

### What to build
The tree of job 5 (commit `d4f43124dde1d1e37de90e18930e374f32ea7ffa` plus
`opus_r13/p1/packc28/packc28_port.patch`), this time with
`-DCMAKE_CXX_FLAGS="-DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1"` beside your usual flags. Known answers:
no option `bench 11` 312866, `bench 13` 862329, `go perft 5` 4865609; the four options of job 5: `bench 13`
690187 (now set directly, no wrapper). The `uci` answer must list `AspFailHighReduce` and
`AspFailHighMaxReduce` with their ranges: copy the two lines into the report (the range tells you which values
exist). New numbers to report: `bench 13` with `AspFailHighReduce 1` and `AspFailHighMaxReduce` 1, 2, 3, 5
(four numbers; if two of them are equal, say so: then those two values search the same tree there).

### The matches (20,000 nodes; the same exe on both sides)
    C     control at 20,000 against 10,000 nodes, no options, 300 games, seed 7260: near +200. Take the games
          per second from C and set every later limit from it.
    S1    Asp on, MaxReduce 2   against none                 2,000 games   seed 7261
    S2    Asp on, MaxReduce 5   against none                 2,000 games   seed 7262
    S3    Asp on, MaxReduce 5   against Asp on, MaxReduce 3  2,000 games   seed 7263   (the direct comparison)
    S4    Asp on, MaxReduce 1   against none                 2,000 games   seed 7264   (if time is left)
(MaxReduce 3 against none is known: +13.5 [+5.7, +21.0] pooled over three seeds; do not replay it.) If the
uci range does not allow 5, take the largest value it allows and say so. If the time does not reach, S4 is cut
first, then S3.

### The report
First line in plain words: the gain per node of the Asp rule at MaxReduce 2 and 5 beside the known 3 (+13.5),
each with its 95 % pair interval from complete pairs, and which value you would play. Say in the FIRST paragraph
what was cut or not reached. One table of all matches; the known answers and the four new bench numbers; the
two uci lines; the probes; files opened; stamps (with C's games per second and the limits derived from it); what
you did not do; what you are not sure about; a better way; model.
