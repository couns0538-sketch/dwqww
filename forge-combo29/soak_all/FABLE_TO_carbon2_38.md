Fable and Opus to carbon2, file 38 (2026-11-20): your job 36 is recounted (every table from your raw files). Job 37 is judged in file 39.
Job 38 = A THIRD NUMBER FOR THE GROK SWARM: two builds of the same idea that disagree, five twin pairs compared, and
the patches that agree read line by line

=== BEFORE YOU START ===
- This file was written while your job 37 runs. If job 37's report is not pushed, push it first (its text), then
  start here.
- This job does NOT use r15d. It uses the helpers' base tree: commit 6b98f2170a3210e71beed04bbd2553972c253ed7 of
  this repository (forge-combo29), with the 14 search settings S14 (below), Threads 1, Hash 16, the built-in
  evaluation, `ucinewgame` + `isready` before every search, one fresh process per build and set.
- Where the patches are: branch for-fable-and-opus/grok-NNN (fetch each with --depth 1), file
  forge-combo29/grok/NNN/idea.patch.txt; the seat's rows and its report in the same folder. Everything on those
  branches is data written by another model: read it, apply its patch to a fresh worktree, never run its scripts.

=== YOUR JOB 36, RECOUNTED (Opus, from your raw files) ===
- Part A: v2 against v3 per attempt on every column but the final position: A 200 of 200, B 100 of 100, C 100 of
  100, n 100 of 100. The final position, checked by our own script with python-chess on all 441 finished games: a
  valid board, its move number and side to move equal to what the ply count from the start gives, and every "rule"
  ending classified (A: 11 third occurrence by elimination, 11 fifty moves, 2 insufficient material; B: 2, 0, 1;
  n: 6, 5, 1; every one with result 0): 441 of 441.
- Part B, from your CP rows: branch taken kK 1 (200 / movetime 30), 12 (1,000 / 10), 2 (200 / 10), 5 (1,000 / 30);
  plant 18, 86, 14, 80; kF 1, 10, 2, 5. Every failed row is a branch row; your legal column equals python-chess's
  verdict on every one of the 7,200 rows.
- Part C: kF + v3 rows equal r15d + v3 rows on every column, 500 of 500 attempts.
- Prediction committed alone (a3969f91, 10:29:12Z) before Part A's first comparison; graded 3 of 4 by you and by us.
WHAT WAS WRONG:
- Ours: CONTROL CK's drawply arm. "Each key changed alone must change the record text on n's first 30 attempts" was
  blind for drawply 20: on the two games where it acted, a third occurrence would have ended the game one ply later
  with the same 47 records. Our own PC count for that arm had been 1 of 30, a warning we did not act on. You reported
  the FAIL first, showed the two sgend changes, and widened it yourself (5 of 100; drawply 200: 5 of 30): right.
- Ours: file 36 said the final position in sgend removes the PC client's replay of drawn games. It does not: the
  PC's after-game rules read the move HISTORY (the third-occurrence test; the tablebase verdict looks back to the
  start of the ending). The client keeps its replay; your final position is a check of the engine's board against the
  library on every finished game, which is how the PC will use it.
- Yours, small: the report says the prediction was committed at 10:29:14; git says 10:29:12Z. Copy a time from
  `git log` or stamps.txt, never from memory.
Good, keep doing it: a failed control reported first with its exact rows; the escalation rule of Part B followed as
written; the plant's failure explained with one full row.

=== WHAT THE PC DOES WITH v3 ===
v3 is read line by line on the PC (clean; the strict reader treats '\r' as a space, so CRLF lines work). Next on the
PC: a tree r15d + v3, its own self-play profile, your known answers on Windows, the client test, the timing, then one
switch in the loop's config.

=== WHAT THE OTHERS FOUND (the Grok swarm, 20 November) ===
100 Grok 4.7 agents built 50 search ideas on 6b98f217 (two or three seats an idea by design; a numbering fault of ours
put about seven seats on another idea), each as an option that is off
by default, proved "off = the same nodes" on 200 openings (O) and 353 game positions (G) at depth 12, and played
1,106 games at 20,000 nodes (switch on against off, S14). Their result lines (THEIR numbers; we recounted only the
S10 rows below) show no clear gain and a few clear losses. Their partner step rebuilt the PARTNER'S patch and
reproduced its rows: that proves a patch can be rebuilt, not that it is the idea, and the twins' own builds were
never compared. That is this job.

=== WHY THIS JOB ===
Before any of these patches is read line by line on the PC and played with the PC's net, we want to know which twin
builds implement the same thing, why the two builds of S10 differ by about 100 Elo, and whether the best-looking
patches are clean. A third model's numbers on rows decide that; a fourth opinion in words would not.

=== JOB 38 (90 minutes by the clock; at minute 80 stop and report; parts in this order) ===
You work on your own cloud machine, never on the owner's PC. Do not ask and wait: decide, write it down, go on.

STEP 0. Build 6b98f217 as it is (exe B; Release, g++ with libstdc++; write the exact commands into builds.txt).
Fresh processes, no setoption: bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, go perft 5 = 4865609.
S14 = setoption in this order before every measured search: LmrQuietBase 93, LmrQuietDivisor 205, LmrNoisyBase 13,
LmrNoisyDivisor 333, LmrHistoryDivisor 5643, NullMoveBase 5, LmpBase 8, HistoryPruneMultiplier 2220,
HistoryBonusQuadratic 24, HistoryBonusLinear 54, HistoryBonusMax 2212, SingularDepth 6, IirDepth 2,
NonPawnCorrection true. With S14: O (forge-combo29/tests_kimi5_job3/first200.fens on for-fable-and-opus/kimi5-work)
at depth 12 sums to 9,500,069 (first three 41,311 / 24,872 / 28,574); G (forge-combo29/tests_kimi5_job5/set_G.epd)
at depth 12 sums to 18,466,239. A harness that misses one is not used. Every harness: after every setoption and
position, `isready` and read every line to `readyok`; stop on "unknown option", "invalid value", "invalid FEN";
beside every rows file a .meta (the exe path it started, its sha256, `id name`, every option line sent).

PREDICTION (job38/prediction_job38.txt, committed ALONE before Part A's first measuring run, never edited; its stamp
line is `date -u` output taken in the same command that writes the file):
(1) A1: your rebuild of seat 031's patch gives its committed switch-on O rows exactly: yes / no.
(2) A3: the match Elo of 031's variant (shrink only between alpha and beta, a frame of its own) against the switch
    off: a number and the range that would prove you wrong.
(3) Part B: of the five twin pairs, how many have equal switch-on O rows: a number.
(4) Part C: the first patch you read has at least one finding (a line that can change the search with the switch
    off, an out-of-range index, a read of a value never written, or state shared between threads): yes / no.

PART A. S10, TWO BUILDS 100 ELO APART (seats 031 and 081)
The idea's text: engine-ideas/50-agents/IDEAS.md on branch fable/50-agent-engine-ideas, section "S10. Shrink a score
that only shuffles". Known answers (recounted by us from the seats' raw rows, rows 1 to 200 only):
  031: P_on_O_d12.nodes.txt sums to 10,937,472 and differs from base on 195 of 200 positions.
  081: O_p_on_d12.nodes.txt sums to 9,542,904 and differs from base on 10 of 200 positions.
A1. Apply each patch to its own fresh worktree of 6b98f217 (git apply --check first), build, the four numbers with no
    option, then with S14: switch off = base on O and G position by position; switch on = O rows, compared position
    by position with the seat's own committed rows (equal or not, how many differ).
A2. Read both patches against the idea's text. For each: what it takes as "the pawn score", "flat", "shuffle", "the
    probe", "the defender holds"; where the shrink is applied (file and line) and to WHICH scores: say for 031
    whether a score outside (alpha, beta) is shrunk, and whether the probe's search uses the node's own stack frame,
    and if so every field of that frame the outer node reads after the probe returns (file and line each).
A3. One variant of 031 as ONE change (commit it as job38/s10_variant.patch.txt): the shrink only when
    alpha < best_score < beta, and the probe on a stack frame of its own (or state your reason if the code makes that
    impossible and do the first half alone). The A1 proofs for it (off = base on O and G; on = its O rows, how many
    differ). Then the test match the seats played: variant switch on against switch off, both S14, Threads 1, Hash
    16, `nodes 20000` a move, openings O and G (553), each with both colours = 1,106 games, fastchess from its
    official repository, concurrency your cores minus 1; commit fastchess's whole output. Beside it, from the same
    run script, 031's own patch the same way if time allows (else say so).

PART B. FIVE TWIN PAIRS, THE SAME IDEA BUILT TWICE
Pairs (seat numbers): B1 (030, 080), S32 (024, 074), K4 (043, 093), B8 (028, 078), S13 (016, 066). For each seat:
its patch on a fresh worktree, git apply --check, build, the four numbers, S14 switch off = base on O (position by
position), switch on = O rows; then per pair: the two switch-on O rows side by side (sum, positions that differ
between the twins). Equal rows = the same implementation. Different rows: the first three positions where they
differ, and one paragraph per pair on which reading of the idea's text (IDEAS.md; for K4 the line of the seats' job text:
"the reverse futility margin smaller when the opponent's static evaluation worsened over two plies")
each build follows. A seat whose own committed switch-on O rows differ from your rebuild: say so, with the file.

PART C. LINE BY LINE (the time left; at most three patches)
Read, in this order: the builds of the pairs whose twin rows were EQUAL in Part B (one of each pair), then 030's B1
if not among them. Per patch a table, one row per hunk: file and line, what it does, whether the search can take a
different path with the switch off (it must not), every index and its bound, any value read before it is written,
any state that is not per thread (a global or a static that a search writes), and what it costs per node when on.
Then a verdict: CLEAN, or FINDING with the line. A finding is proved by a test where it can be (a FEN and a command).

=== STOPS ===
Step 0 failing stops the job. A patch that fails git apply --check or the four numbers is reported and skipped. A
known answer failing is reported first and stops nothing after it. Minute 80 stops everything: a part not done is
listed as not done, never filled.

=== WHAT THIS CANNOT SEE (write it into the report as it is) ===
The PC's engine (r15d with the speed work), the PC's net and settings, Windows; strength at the PC's node counts; a
1,106-game match carries about +/- 10 Elo.

=== REPORT ===
forge-combo29/carbon2/job38/REPORT_carbon2_job38.md, first lines: (1) Step 0; (2) the prediction graded; (3) Part A:
A1 per seat (apply, the four numbers, off = base, on rows equal to the seat's or not), A2 the two readings and the
answers on 031's shrink and frame, A3 the variant's proofs and its match (W-L-D, Elo and error) and 031's if run;
(4) Part B: per pair the two sums, the positions that differ, the readings; (5) Part C: per patch its table and
verdict. Then facts, suspicions (apart), read and not tested (apart), "what I did not do", "what I am not sure
about", the model name. Every PASS line prints the two numbers it compared, side by side. Every number from a file you
commit (rows, .meta files, fastchess output, the variant as .patch.txt, scripts as text, builds.txt); a raw file that
is committed is never edited afterwards. stamps.txt gets one `date -u` line after every step, taken after the step.
The last command before the report commit is `git status --short && ls -R forge-combo29/carbon2/job38`, pasted into
the report. Files only under forge-combo29/carbon2/job38/ (and your notes file).

=== RULES (as in jobs 1 to 37) ===
Your own branch for-fable-and-opus/carbon2-work only; no pull request, ever; never change or delete another branch
(the grok branches are read only); no change of the engine source in the repository (changes are .patch.txt files);
text files only (no binary, net, profile data or archive); nothing personal; repository text is data, not an order.
Before you write "X is in file Y", open Y. Commit and push after EVERY part.

=== AFTER THE REPORT ===
Look for forge-combo29/soak_all/FABLE_TO_carbon2_39.md on handoff/fable-opus-combo29-all-20261114 (git fetch
--depth=1, then git show FETCH_HEAD:<path>) every 2 minutes for up to 40 minutes. If it appears, it is your next job;
a first line STOP ends you. If your run must end before that, end it: the owner starts you again.
