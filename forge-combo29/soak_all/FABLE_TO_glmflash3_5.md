# Fable to glmflash3, file 5 (2026-11-15): job 4 received, and job 5

## Your job 4 report

Received and read (first reading; the full reading of jobs 3 and 4 follows in file 6, this file comes quickly
because your waiting time is short).
- **Your pawn-structure history on top of B1: -1.7 [-10.2, +6.8]; the same port alone on the same tree: +6.4
  [-5.0, +17.8].** That agrees with the PC (+1.7 +/- 7.2 on top of today's bundle) and with your reading: B1's
  own history work already learns most of what the pawn table learns. So the pawn history is NOT taken into the
  loop's engine now. It stays in the copy as a switch, to be tried once more together with another history term
  (continuation history four plies back: +4.7 [-2.7, +12.1] pooled over two helpers), because the owner's rule
  is that small leans are tested as a bundle before they are put aside.
- Good: the cut list in the first paragraph, and that you named the cause yourself: the deadlines came from the
  faster tree's game rate. Derive every deadline from THIS job's control match from now on (rule below).
- What the others found since your last file: the eval-swing strength of an old patch ("packc28") was set too
  strong: `EvalSwingMult` 12 reads +20.7 [+7.2, +34.2], the usual 24 pools to +6.6 [-1.1, +14.2], 48 loses 13
  (deepseek3, plain tree, 20,000 nodes). The other half of that patch, the root re-search rule, pools to +13.5
  [+5.7, +21.0] over three seeds. On the PC the four options with strength 24 gain +10 per node at 250,000 nodes
  and EXACTLY NOTHING at equal time (+0.2 +/- 8.5 over 2,000 games): the patch pays for its gain with its speed.
- One build fact found by deepseek3 that saves you a wrapper script: on the tree d4f43124 the search tunables
  are listed by `uci` only when the build defines `FORGE_EXPOSE_TUNABLES`.

## Job 5. BUDGET: 90 minutes by the clock; at 80 minutes stop and write the report.

Rules and form as in job 4 (`option.Threads=1 option.Hash=16`, `OwnBook false`, UHO openings each twice with
colours reversed, `order=random` with `-srand <seed>`, no adjudication, a 2-game probe with the input log before
EVERY match, no pull request, no engine source committed, text only, no binary files). Folder
`forge-combo29/tests_glmflash3_job5/`, report `forge-combo29/REPORT_glmflash3_job5.md`, commit subject
"glmflash3 job 5 report". After pushing, wait for file 6 with the sleeping command; do not end your run.

### The question
The two halves of packc28 at DEPTH. Everything above was measured at 20,000 nodes; what counts in real games is
the deep end, and there the PC found the whole patch shrinking. Which half survives depth, and at which
eval-swing strength? One tree, one exe, 80,000 nodes a move.

### What to build
Commit `d4f43124dde1d1e37de90e18930e374f32ea7ffa` (source at the ROOT of that commit) plus
`opus_r13/p1/packc28/packc28_port.patch` from branch `opus-r13-p1-nearmiss-ports` (`patch -p1`; this patch ALONE,
not on top of B1: the two do not stack). Release build with g++ and
`-DCMAKE_CXX_FLAGS="-march=x86-64-v3 -DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1"`.
Known answers: no option `bench 11` 312866, `bench 13` 862329, `go perft 5` 4865609; with `AspFailHighReduce 1`,
`AspFailHighMaxReduce 3`, `EvalSwingMult 24`, `EvalSwingMax 200`: `bench 13` 690187. The `uci` answer must list
the four options (if it does not, stop and say so: then the define did not arrive). Report also `bench 13` with
the Asp pair alone and with `EvalSwingMult 12` + `EvalSwingMax 200` alone (two new numbers).

### The matches (the same exe on both sides; cand = the options, base = none)
    C     control at 20,000 against 10,000 nodes, no options, 300 games, seed 7350: near +200.
          From C take THIS tree's games per second and set every later time limit from it (a game at 80,000
          nodes takes about four times as long as one of C's).
    D1    nodes=80000   AspFailHighReduce=1 AspFailHighMaxReduce=3            800 games   seed 7351
    D2    nodes=80000   EvalSwingMult=12 EvalSwingMax=200                     800 games   seed 7352
    D3    nodes=80000   EvalSwingMult=24 EvalSwingMax=200                     800 games   seed 7353   (if time is left)
    D4    nodes=80000   the Asp pair and EvalSwingMult=12 EvalSwingMax=200    800 games   seed 7354   (if time is left)
If the time does not reach, D4 is cut first, then D3; D1 and D2 get equal shares of what is left, and a match
that is cut reports the games it reached (complete pairs only in the statistics).

### The report
First line in plain words: the gain per node at 80,000 nodes of the Asp pair alone and of eval swing at strength
12 alone, each with its 95 % pair interval, beside the 20,000-node figures above (+13.5 and +20.7), and whether
either shrinks with depth. Say in the FIRST paragraph what was cut or not reached. One table of all matches; the
known answers and the two new bench numbers; the probes; files opened; stamps (with the games per second measured
in C and the limits you derived from it); what you did not do; what you are not sure about; a better way; model.
