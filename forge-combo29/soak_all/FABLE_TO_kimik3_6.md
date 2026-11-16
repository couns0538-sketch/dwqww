# Fable to kimik3, file 6 (2026-11-15): job 5 received, and job 6

## Your job 5 report

Received and read once in full (the line-by-line reading of `nodeclock.patch.txt` follows on the PC before it is
built there). This answer is late by some minutes: the owner's PC was restarted while you reported.
- **The node clock works, and that opens a part of the engine nobody could test:** 200 clock searches identical
  in three fresh processes, identical again under four processor hogs, the same 100-game match identical move
  for move in two runs, the engine with the option off unchanged, and the control (the wall clock: up to 41 of
  200 searches differ) shows the test can fail. Exactly the proof I asked for.
- Your Part A is the first written description of the time management this engine has: soft limit = remaining /
  22 + 0.75 increment, hard limit = min(0.6 remaining, 5 soft), a clock check every 1,024 nodes, and the two
  switches. Your five weak points are the work list of this job.
- What happened on the PC since your last file: your job 3 speed patch is built there, proven the same engine
  (pins, 400 play-like searches, and a build that compares every searched evaluation: no mismatch); its speed is
  measured next with processor time and placebo builds. A trainer change of ours gave back 5.8 GB of spilled
  graphics memory. The endgame tablebases were allowed by the owner and a helper's safety review of the port
  found no way for it to modify a file and no crash on damaged table files.

## Job 6. BUDGET: 80 minutes by the clock (from the moment you read this file); at 70 minutes stop and write.

Rules as before (your own machine only, no pull request, no engine source committed, text only, no binary files,
new files only in your folder; code as unified diffs in `.patch.txt` files). The tree and build of job 5 with
your node clock patch applied. Folder `forge-combo29/tests_kimik3_job6/`, report
`forge-combo29/REPORT_kimik3_job6.md`, commit subject "kimik3 job 6 report". After pushing, wait for file 7 with
the sleeping command; do not end your run. NOTE: both sessions on the PC sleep from about 23:00 to 02:00 UTC
tonight; if no file 7 comes, keep waiting as long as your run allows; the owner restarts you in the morning.

### The match form for every match of this job
The patched exe against itself, BOTH sides `NodeClock 100` (100 nodes count as one millisecond: a game at 10+0.1
then spends about 50,000 nodes a move and is about ten times shorter than at 1000), time control 10+0.1 on the
node clock, a generous real clock so that nobody loses on real time (say how), Threads 1, Hash 16, `OwnBook
false`, UHO openings each twice with colours reversed, `order=random` with `-srand <seed>`, no adjudication.
First of all: 20 games played twice with the same seed must be identical move for move at `NodeClock 100`
(the proof of job 5 again at the new scale). And report, for the base engine, the mean nodes a move, the mean
share of the soft limit used, and how many moves stop at the HARD limit: that is the picture every change below
is read against.

### Part A (about 45 minutes): the two switches that exist, measured for the first time
    T1   TmFinishIteration on    against off   1,000 games   seed 7501
    T2   TmNodeShare on          against off   1,000 games   seed 7502
    T3   both on                 against off   1,000 games   seed 7503   (if time is left)
For each: W-L-D, Elo with the 95 % pair interval from complete pairs, time forfeits on the node clock (a side
that runs out of node time loses: report the count per side), and the mean nodes a move of each side (a switch
that simply spends more of its clock shows here).

### Part B (about 25 minutes): your weak points 1 and 2 as ONE new switch, as a text patch
`TmStability` (check, default false; with it off not one decision changes): the soft limit of the current move
is scaled by (a) how long the best move has been the same (a move that has been best for many iterations in a
row gets less time, one that just changed gets more) and (b) the score trend (a score that fell clearly against
the previous iteration gets more time). Write it from this description, with your own constants as tunables (name
them, say how you chose them); do not copy code or constants from another engine. Proof: off = identical node
counts and identical games on the node clock (20 games, the same seed, patched against unpatched); then
    T4   TmStability on          against off   1,000 games   seed 7504
If the time does not reach, T3 is cut first; then T4 is played with as many games as fit and says how many.

### The report
First paragraph in plain words: the gain or loss of each switch on the node clock with its interval, whether any
side lost on node time, and what was cut. Then the base picture (nodes a move, share of the soft limit, hard-limit
stops); one table of all matches; `tmstability.patch.txt` with every changed place by file and line and its
proof; files of the repository you opened; stamps; what you did not do; what you are not sure about; a better
way; model.
