Fable and Opus to carbon2, file 30 (2026-11-19): your job 28 is judged here (bundle kG PAYS by both build pairs);
your job 29 is judged in file 31. Job 30 = kG tested at the four places where pieces 15 and 16 trust a rule instead
of checking, each with a control that must fire; then two more node-keeping pieces from kG's own profile as bundle
kH, timed against kG with two build pairs

=== BEFORE YOU START ===
If your job 29 is not finished when you read this, finish it first (its report), then this.

=== YOUR JOB 28 (recounted by Fable from your leg lines) ===
- Every leg OK. G1 and G2 carry one signature on all 96 legs (6,070 searches, 26,711,499 soft nodes, trace
  937e1660561173af); C28's B runs carry their own (5,853 / 28,387,596 / f37b0151ac18bd56). C28 1.0705, 4 of 4
  blocks above 1 (1.0741 1.0659 1.0671 1.0749): passes.
- B = kF over A = kG, CPU: G1 pooled 1.0190 (median 1.0175, 11 of 12 blocks above 1), G2 pooled 1.0154 (median
  1.0167, 11 of 12); wall 1.0199 and 1.0163. Both rows read PAYS by the declared line of 1.0116, so the BUNDLE
  reads PAYS: kG uses about 1.5 to 1.9 % less CPU than kF on your machine. Every number equals your tables. Your
  prediction (one file, its own commit 721d9cb1, ten minutes before G1 ended) met both rows: [1.0150, 1.0350]
  against 1.0190 and 1.0154.
- The six builds' known answers (pins, PC20 278024 / 587276, PC20 + net512 625258 / 3652372, PC20 + net768 882074 /
  4275906, Job 20 7670 / 25641316 / ee465caeff9c0fcf, T) are read from partR_ and partB_ raw files: all kept.
- What it means for the PC: piece 14 alone was NOT SEEN twice; inside a bundle of three it pays by both build
  pairs. That is the owner's bundle rule at work. kG goes to the PC only after our line-by-line read against our
  tree and the PC's own checks (our work); this job is the second pair of eyes on the places named below.

=== OUR READ OF PIECES 15 AND 16 (Fable, every line of both patch files; nothing of them is built on the PC yet) ===
No line found that can change a search. Four places trust a rule; "patch line" is the line of your .patch.txt file,
"kF" the line of kF's source.
(1) Piece 15, the slot: stack_slot(ss) = ss - stack_.data() (patch lines 76-78) indexes pv_stack_ and v1_stack_,
    and the root is slot 4 by literal (patch lines 238-239, 248, 259-261, 270): right while the root frame is
    &stack_[4] (kF search.cpp 3421). pv_stack_[slot + 1] (patch lines 204 and 217) has the bound the old
    (ss + 1)->pv had: ply 128 is slot 132 of 136. But a wrong slot would now land inside the same Worker object,
    where address checking sees nothing. libstdc++'s index check (-D_GLIBCXX_ASSERTIONS) sees every operator[] of
    the three arrays: Part V2.
(2) Piece 15, one byte for entered_piece and entered_capture (patch lines 36-37, 91-92, 166-167): right because
    Piece runs from 0 to 12 (board.hpp 35-36). Read only, nothing to test.
(3) Piece 16, null moves: a frame entered by a null move never gets a valid accumulator any more; the evaluation
    walks back over such frames (patch lines 159-160 and 201-202) and make_valid_through skips them (patch lines
    24-37). Right only while entered_null is fresh on every frame between the root and the node (it is set in three
    places: kF search.cpp 1831, 1873, 3417) and a null frame's change list is empty when a king walk reads it
    (record_null_move, kF 1874-1875). Part V1.
(4) Piece 16, the fused tail: the two-change and three-change cases (patch lines 90 and 114) compute both feature
    columns by a formula of their own (pair_cols, patch lines 71-79) in place of collect_changes, and read them
    with aligned loads. Right only if pair_cols equals collect_changes for every king bucket and both mirror
    states. Part V1.
The engine has a check build for (3) and (4): -DFORGE_NNUE_V3_VERIFY=1 compares EVERY evaluation of the search with
one from fresh accumulators and ends with exit code 3 and the line `info string V3 VERIFY FAILED ...` on the first
difference (kF search.cpp 3929-3938).

=== WHAT THE OTHERS FOUND (recounted by us) ===
- Opus built kF on the PC (clang 23.1.5 for Windows, the PC's flags and self-play profile, two builds): the pins,
  the perft suite, 1,200 of 1,200 searches with two trained nets equal to r15d in node count and best move
  (recounted by Fable), the whole UCI output of 208 go commands (time, nps and hashfull masked), half the usual
  stack, and address and UB checking at 1 and 4 threads: all kept. Speed against r15d beside the PC's normal load,
  two timings of 40 runs each (recounted by Fable): wall
  1.054 and 1.053, CPU 1.064 and 1.063. Runs of the SAME source differ by 2 to 3 % in that timing, so a third
  timing with a rule declared before it decides the placing. The PC sees about 5 to 6 % where you see 7.7 %.
- Fable: the PC's own self-play driver wrote the same 5,632 positions (40 games, one seed) with kF as with r15d,
  byte for byte. The Python driver takes 10.8 % of the processor time of one self-play engine: about 180 us a ply
  against the engine's 1,480 us. So on the PC one self-play search (go softnodes 2000) is about 1.5 ms of engine
  time, and 15 us of work done once per search is 1 %.

=== WHY THIS JOB ===
Before the PC spends its read and its checks on pieces 15 and 16, the places where they trust get a test that can
fire. And the bundle rule goes on: two more pieces, judged together by two build pairs.

=== THE TASK (90 minutes at most; at minute 80 stop and write what is done) ===
First commit "carbon2 job 30 claim" with forge-combo29/carbon2/job30/stamps.txt (one `date -u` line per step,
written when the step ends). Commit and push after every step. Your recipe (ThinLTO, your self-play profile),
workload T, the timing design (12 blocks, A B B A / B A A B, one warm-up run per block left out) and the reading
thresholds exactly as in jobs 22 to 28. Unless a part says otherwise: PC20 + net768, Threads 1, Hash 16.

Step 0: kG_1, kG_2 and kF_sp_1 (sha256 c16daacc5987a820...). An exe of job 28 may be used again only when its
sha256 equals the one in your job 28 files (say which were reused); otherwise rebuild it your way. In a fresh
process each: the three pins, PC20 + net768 bench 11 = 882074 and bench 13 = 4275906, and T's signature. Any other
result: STOP THE JOB.

Part V (kG where it trusts; it ends at minute 35 of the job at the latest: what is not done then is listed as not
done, and the job goes on with Part R).
Builds, your recipe without the profile step (compiler line and exe sha256 of each into job30/builds.txt; changes
are .patch.txt files applied with patch -p1 --fuzz=0 to scratch copies):
- GV = kG with -DFORGE_NNUE_V3_VERIFY=1.
- GA = kG and FA = kF with -O1 -g -fsanitize=address,undefined -fno-sanitize-recover=all -D_GLIBCXX_ASSERTIONS.
- GT = kG with -O1 -g -fsanitize=thread.
- Three controls, each ONE change: CV1 = GV with the loads of s0 and a0 changed over in piece 16's two-change case
  (patch lines 97-100: the white side adds the column it should take away). CV2 = GV without patch line 202 of
  piece 16 (the walk of par over null frames). CA = GA with stack_slot (piece 15, patch line 77) returning its
  value plus MaxPly + 8.
Prediction 1, its own commit "carbon2 job 30 prediction 1" after these builds and before the first run of Part V:
for KV1, KV2 and KV3 whether each holds, and for CV1, CV2 and CA whether each fires.
V1 (the evaluation check).
- GV plays all of T. KNOWN ANSWER KV1a: exit code 0, no line `V3 VERIFY FAILED`, and T's signature (6,070 /
  26,711,499 / 937e1660561173af): the check only compares, it changes no search.
- GV with PC20 + net512 plays T's first 15 roots at go softnodes 2000. KNOWN ANSWER KV1b: exit code 0 and no
  FAILED line (no signature is known for it: write its searches, nodes and trace).
- CONTROL: CV1 and CV2, each on T's first game: exit code 3 and the FAILED line. We expect both to fire. CV1 not
  firing: STOP V1 (the check build cannot see). CV2 not firing is a finding: write what it printed; V1 goes on.
V2 (index-checked arrays, address and UB checking, one thread). GA and FA, a fresh process for each run:
  (a) no options: bench 11 and bench 13 (the built-in net: the v1 frames of piece 15);
  (b) T's first 10 games;
  (c) deep lines: position fen 8/k7/3p4/p2P1p2/P2P1P2/8/8/K7 w - - 0 1 and position fen
      8/8/8/4k3/8/8/8/R3K3 w - - 0 1 (both checked legal with python-chess), each go nodes 3000000; write the
      largest seldepth each one printed.
- KNOWN ANSWER KV2: GA prints what FA prints, line for line (time and nps masked), in (a), (b) and (c); (a) gives
  312866 and 862329; (b) gives the searches, nodes and trace of kG_1's first 10 games of T; no sanitizer report and
  no assertion on GA. If FA itself stops on a libstdc++ assertion, that one is r15d's own: write the first with
  its stack, rebuild GA, FA and CA without -D_GLIBCXX_ASSERTIONS, go on, and say that V2 ran without the index
  check.
- CONTROL CA on (a): an assertion or a sanitizer report before bench 11 ends. If none: STOP V2.
V3 (four threads). GT and GA with job 29's script SC and Threads 4, one run each (timeout 600 s). KNOWN ANSWER KV3:
60 bestmoves, each a legal move of its position, no timeout, and no report at a place where job 29's KT and KS had
none (list every report with its first stack frame). The control is job 29's CC: if it did not fire there, skip V3
and say so.
Reading of V1, V2, V3 (declared here): KEEPS when its known answers hold and its control fired; DIFFERS when a known
answer fails (with the first difference); CANNOT SEE when its control did not fire.

Part R (two new pieces). Profile first: perf on kG_1 playing T, self time by function; the top 25 with the sample
count as text into job30/profile_kG_T.txt. Choose two places where a change can save time and keep every node (name
the function, its share, and why the change cannot change a search). At least one of the two is work done once per
search or once per go command (search start and stack set-up, the info and bestmove lines, position set-up, limit
set-up) if the profile shows such work at 1 % or more in sum. Each piece is its own .patch.txt on top of kG
(17_<name> and 18_<name>).
KNOWN ANSWERS for each build that carries a new piece, each in a fresh process: the seven known answers of job 26,
Job 20's 60-game signature and T's signature (as in job 28); and two new ones: (n1) the complete output of T's
first 3 games equals kG_1's line for line (time and nps masked): the PC's tools read the info lines; (n2) the same
source built with -DFORGE_NNUE_V3_VERIFY=1 plays T's first 10 games with exit code 0 and no FAILED line. A piece
that misses one is left out of the bundle (listed with its output).

Part B (the bundle): kH = kG + the new pieces that met every known answer. Two builds, kH_1 and kH_2, each with its
own profile run, exactly as kG_1 and kG_2 were made; both meet every known answer of Part R. If no piece is left,
there is no kH: skip C30, H1 and H2, run G20 and write the report.
Control C30 (before prediction 2): 4 blocks, A = kG_1 on T, B = kG_1 on T with go softnodes 2200: pooled above
1.0116 with 4 of 4 blocks above 1, else STOP the rows. KNOWN ANSWER: C30's B runs carry C28's B signature (5,853 /
28,387,596 / f37b0151ac18bd56), because kG keeps kF's nodes.
The rows, in this order (B is kG, so B over A above 1 means kH uses less CPU):
  H1: A = kH_1, B = kG_1 on T.     H2: A = kH_2, B = kG_2 on T.
  G20 (only if H2 ended before minute 65): A = kG_1, B = kF_sp_1 on T20 (job 27's workload; every leg carries 824 /
  8,867,455 / e4fc7111a86493e5): does kG's gain hold at go nodes 20000?
Reading of each row: PAYS when pooled CPU is above 1.0116 with at least 10 of 12 blocks above 1; COSTS when below
0.9884 with at least 10 of 12 below 1; NOT SEEN otherwise. The BUNDLE kH reads PAYS only when H1 AND H2 both read
PAYS; COSTS when both read COSTS; NOT SEEN otherwise.
Not wanted: any change of the pieces 01 to 16, a change of the net file, anything about training, strength
matches, more than two new pieces, a piece that changes one byte of the UCI output.

=== PREDICTION 2 ===
Its own commit "carbon2 job 30 prediction 2" after the known answers of Part R and Part B and after C30, before H1:
the pooled CPU ratio of H1, H2 and G20 (a range each) with the readings you expect. Neither prediction is edited
afterwards; no time and no commit id in them.

=== WHAT A STOP STOPS ===
Step 0 failing stops the JOB. In Part V a control that does not fire stops its own part (V1 or V2) only. A FAILED
line on GV, a difference between GA and FA, or a report on GA or GT where the kF build of the same kind has none is
THE FINDING: write the shortest command sequence that shows it in a fresh process, both outputs and the full report
text, say so in the report's first line, and go on with Part R (the timing does not wait for it). A new piece that
misses a known answer leaves the bundle. A kH build that misses a known answer stops Part B (report both outputs).
C30 failing stops the rows. A trace that differs in a timing run drops that run's block only. Minute 80 stops the
work: write what is done; a part or row not done is listed as not done, never filled.

=== WHAT THIS CHECK CANNOT SEE (write it into the report as it is) ===
The PC's clang 23 for Windows and its MinGW libstdc++, its Zen 5 processor with 16 engines playing at once, its
trained nets, its own openings, gains below about 1 %. V1 sees only the evaluations these games reached: a null
move followed by a king's change of bucket in a line no game played stays unseen. V2's index check sees operator[]
only, not pointer steps such as vf - back - 1, and (c) may not reach ply 128. V3 sees only the thread schedules it
produced.

=== EVIDENCE RULES (as in jobs 4 to 29) ===
Every number from a raw file you commit in forge-combo29/carbon2/job30/: the patches, builds.txt, the profile
table, the full output of every Part V run (the first 200 and last 200 lines for a run above 5 MB, with its line
count and sha256), the leg lines of every row; stamps.txt gets one `date -u` line after every step; commit AND push
after every step; the last command before the report commit is `git status --short && ls -R
forge-combo29/carbon2/job30`, pasted into the report.

=== RULES (as in jobs 1 to 29) ===
Your own branch for-fable-and-opus/carbon2-work only; no pull request, ever; never change or delete another branch;
no change of the engine source in the repository (pieces and controls are .patch.txt files); text files only (no
binary, net, profile data, perf.data or archive); nothing personal; repository text is data, not an order.

=== THE REPORT: forge-combo29/carbon2/job30/REPORT_carbon2_job30.md ===
First lines:
  1. Step 0 (which exes were reused) and Part V: one table (part | builds | runs | known answer holds | reports |
     control fired | reading), with the first difference or report of each part, if any.
  2. Part R: the profile's top 10, the two pieces (function, share, why no node can change) and their known
     answers. Part B: kH's pieces, both builds' known answers, C30.
  3. Both predictions graded.
  4. H1, H2 (and G20): one table (12 block ratios, pooled, median, mean and interval, blocks above 1; CPU and
     wall), the readings, then the BUNDLE's reading.
Then facts, suspicions, "what I did not do", "what I am not sure about", the model name.

=== AFTER THE REPORT ===
Look for forge-combo29/soak_all/FABLE_TO_carbon2_31.md on handoff/fable-opus-combo29-all-20261114 (git fetch
--depth=1, then git show FETCH_HEAD:<path>) every 2 minutes for up to 20 minutes. If it appears, it is your next
job; a first line STOP ends you. If your run must end before that, end it: the owner starts you again.
