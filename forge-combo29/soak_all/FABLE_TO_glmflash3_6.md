# Fable to glmflash3, file 6 (2026-11-15): job 5 received, and job 6

## Your job 5 report

Received and read (first reading; the full reading of jobs 3 to 5 follows in file 7). This answer is late by some
minutes: the owner's PC was restarted while you reported.
- **At 80,000 nodes on the plain tree: the Asp pair alone +8.3 [-6.6, +23.2], eval swing at strength 12 alone
  +18.3 [+3.3, +33.3], at strength 24 alone +6.8 [-9.2, +22.8]** (800 games each). You say yourself that 800
  games cannot show a shrink of a few Elo against the 20,000-node figures (+13.5 and +20.7). What they do show:
  the order of the two strengths holds at depth, 12 ahead of 24.
- Good: the cut list in the first paragraph, and the measured game rate against the predicted one (the estimate
  was 20 % optimistic; the limits were caps and held).
- What the PC found meanwhile on top of today's switch set at 2,000 nodes: the Asp pair alone +20.6 +/- 7.2, eval
  swing 24 alone +20.1 +/- 7.1, eval swing 12 alone +13.9 +/- 7.1. So on the newer tree and at shallow depth 24
  is not worse than 12, on your plain tree at depth 12 is clearly ahead. The four options with strength 24
  together are worth nothing at equal time on the PC; the Asp pair is the candidate there because it costs no
  speed, and it gets a match at 250,000 nodes.
- NOTE: both sessions on the PC sleep from about 23:00 to 02:00 UTC tonight. If no file 7 comes after your
  report, keep waiting with the sleeping command as long as your run allows; the owner restarts you in the
  morning with your restart line, which finds the newest job by itself.

## Job 6. BUDGET: 90 minutes by the clock (from the moment you read this file); at 80 minutes stop and write.

Rules, tree, build and match form exactly as in job 5 (commit d4f43124 plus the packc28 port alone, built with
`-DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1`; `option.Threads=1 option.Hash=16`, `OwnBook false`, UHO
openings each twice with colours reversed, `order=random` with `-srand <seed>`, no adjudication, a 2-game probe
before every match; no pull request, no engine source committed, text only). Folder
`forge-combo29/tests_glmflash3_job6/`, report `forge-combo29/REPORT_glmflash3_job6.md`, commit subject
"glmflash3 job 6 report". After pushing, wait for file 7 with the sleeping command; do not end your run.

### The question
The pair we may really play is "the Asp rule + eval swing at strength 12". It was never measured together, and
its two halves each have one seed at depth. This job gives the pair its first number and each half its second
seed, all at 80,000 nodes.

### The matches (the same exe on both sides; cand = the options, base = none)
    C     control at 20,000 against 10,000 nodes, no options, 300 games, seed 7360: near +200; take the games
          per second from C and set every later limit from it (a game at 80,000 nodes takes about four times as
          long as one of C's; your job 5 estimate was 20 % optimistic: allow for it)
    E1    nodes=80000   AspFailHighReduce=1 AspFailHighMaxReduce=3 EvalSwingMult=12 EvalSwingMax=200   800 games   seed 7361
    E2    nodes=80000   EvalSwingMult=12 EvalSwingMax=200                                              800 games   seed 7362   (second seed of D2)
    E3    nodes=80000   AspFailHighReduce=1 AspFailHighMaxReduce=3                                     800 games   seed 7363   (second seed of D1)
    E4    nodes=80000   the pair of E1 against EvalSwingMult=12 EvalSwingMax=200 alone                 800 games   seed 7364   (what the Asp rule ADDS; if time is left)
New `bench 13` number to report before the matches: the four options of E1 together (Asp pair + swing 12, Max 200).
If the time does not reach: E4 is cut first, then E3; E1 and E2 get equal shares of what is left.

### The report
First line in plain words: the pair at 80,000 nodes with its 95 % pair interval; then swing 12 alone and the Asp
pair alone, each POOLED over job 5's seed and this one's (state both seeds and the pooled interval). Say in the
FIRST paragraph what was cut or not reached. One table of all matches of jobs 5 and 6 at 80,000 nodes; the new
bench number; the probes; stamps (with C's rate and the limits derived from it); what you did not do; what you
are not sure about; a better way; model.
