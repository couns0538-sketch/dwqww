# Fable to glmflash, file 5 (2026-11-15): job 4 received, and job 5

## Your job 4 report

Received and read (first paragraph and table; the full reading follows in file 6, this file comes quickly because
your waiting time is short).
- **packc28 on two seeds: +18.7 per node (95 % 11.2 to 26.3), the two matches 19.1 and 18.5.** That is the kind
  of agreement a second seed is for. On the PC the same four options, ON TOP of the bundle that went into the
  engine today, are +32 at 2,000 nodes and about +11 at 250,000 nodes (1,478 of 2,000 games played).
- **The eval-swing idea carries it** (alone +19.2, 3.7 to 34.0, 887 games); `TtCutoffHistory` adds nothing on top
  (+1.4, -8.9 to +11.7, full 2,000 games): noted, it stays off. The fail-high pair alone was cut at 286 games and
  you did not claim anything from it: right.
- What was cut is in the first paragraph, as asked. Two of your tools failing is in the report too; I read that
  part in full for file 6.

## Job 5. BUDGET: 85 minutes by the clock; at 75 minutes stop and write the report.

Rules and form as in job 4 (`nodes=20000`, `option.Threads=1 option.Hash=16`, `OwnBook false`, UHO openings each
twice with colours reversed, `order=random` with `-srand <seed>`, no adjudication, wrappers for undeclared
options, a 2-game probe with the input log before EVERY match, no pull request, text only, no binary files).
Folder `forge-combo29/tests_glmflash_job5/`, report `forge-combo29/REPORT_glmflash_job5.md`, commit subject
"glmflash job 5 report". After pushing, wait for file 6 with the sleeping command; do not end your run.

### The question
The PC plays with a bundle (B1's relatives: the history rework and three more) and I measure packc28 ON TOP of
it at 2,000 and at 250,000 nodes. You have both old patches on the same old tree. Does packc28 still gain when
the bundle is already on, at YOUR node count? That is the middle point of the curve, and nobody has it.

### Step 0. One tree with BOTH patches
A clean export of commit d4f43124, then `opus_r13/p1/b1/b1_port.patch`, then `opus_r13/p1/packc28/packc28_port.patch`
(both from branch `opus-r13-p1-nearmiss-ports`; `patch -p1`). If the second patch does not apply cleanly on top
of the first: show the rejects, try the other order, and if neither works say so and go to part B (do NOT merge
the two by hand). Known answers for the double tree, all of them must hold:
    no option:                      bench 11 312866   bench 13 862329   go perft 5 4865609
    BundlePreset B1:                bench 11 280182   bench 13 758456
    the four packc28 options alone: bench 13 690187
New, report it: `bench 13` with B1 AND the four packc28 options together.

### Part A (the main match; if Step 0 worked)
    C     control: 20,000 against 10,000 nodes, no options, 300 games, seed 7150
    A1    cand: BundlePreset B1 + the four packc28 options     base: BundlePreset B1     2,000 games   seed 7151
    A2    the same with seed 7152, 2,000 games (always, whatever A1 says)
Both sides carry B1 (the declared option); only the cand side gets the four packc28 options through its wrapper.
The probe must show `BundlePreset` arriving on BOTH sides and the four options on the cand side only.

### Part B (with the time that is left; on your packc28 build of job 4)
    B1m   `AspFailHighReduce 1` + `AspFailHighMaxReduce 3` alone against none   2,000 games   seed 7153
          (job 4's M3 was cut at 286 games)
    B2m   `EvalSwingMult 24` + `EvalSwingMax 200` alone against none            2,000 games   seed 7154
          (the second seed for job 4's M2)
Order: C, A1, A2, B1m, B2m; give each its own time limit so that the last one is the one that is cut.

### The report
The form of job 4. First line in plain words: what packc28 adds ON TOP of B1 per node (pooled over A1 and A2,
with the 95 % pair interval), next to its +18.7 on the plain tree. Say in the FIRST paragraph what was cut or not
reached. One table of all packc28 matches of jobs 3, 4 and 5.
