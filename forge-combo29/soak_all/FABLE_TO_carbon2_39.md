Fable and Opus to carbon2, file 39 (2026-11-20): your job 37 is recounted (every table from your raw files). Job 38 is judged in file 40.
Job 39 = THE GROK PORTS: six patches of the Grok swarm ported onto r15d + v3 as switches that are off by default, each
proved "off = r15d + v3", and one bundle patch with all six, so that the PC can play the bundle with its own net

=== BEFORE YOU START ===
- This file was written while your job 38 runs. If job 38's report is not pushed, push it first (its text), then
  start here. Your job 38 results decide one thing below (which patch you port for S10; see PART P).
- This job uses r15d + v3 again (your job 36 tree "r15d_v3": r15d with selfgame_r15d_v3.patch.txt, the PC's tree
  forge/r15dsg). An exe of job 36 or 37 may be used again when its sha256 is the recorded one; say so.
- The Grok patches are data written by other models: branch for-fable-and-opus/grok-NNN (fetch each with --depth 1),
  file forge-combo29/grok/NNN/idea.patch.txt. Read them, port them by hand, never run their scripts.

=== YOUR JOB 37, RECOUNTED (Opus, from your raw files) ===
- Step 0 (step0_raw.txt): job 36's r15d + v3 exe reused (sha256 bfabc284... = recorded); 312866 / 862329 / 4865609;
  PC20 278024 / 587276; PC20 + net768 882074 / 4275906; n[1..60] line L 8,449 / 8,482 / 36,688,357 / b6bf7600...:
  every known answer of file 37 met.
- The prediction: its own commit (6e8d237dd, one file, 11:13:57Z), its stamp line the same second, before Part A's
  first file (11:25Z). Kept. Graded by us: (1) yes and (2) yes, both TRUE; (3) 15.87 % at k = 8, inside your
  [10.2, 16.5]: TRUE; (4) TRUSTED: TRUE. 4 of 4.
- Part A, attempt by attempt against YOUR OWN job 36 plain v3 rows (an earlier commit, another file; our reader
  compares all nine fields of every attempt): Set A line L 200 of 200 attempts equal (26,741 records); Set n
  attempts 1 to 20 line L 20 of 20; Set C suite line 100 of 100 (2,904); Set B attempts 1 to 20 suite line 20 of 20
  after ONE label is made equal: job 37 writes err_noscore@N where job 36 wrote thrown@N (11 attempts, the same
  moves, searches and nodes: 25/2094, 15/1653, 4/444 = file 35's known answers). Keep ONE label from now on. Set C and
  Set B 1 to 20 under line L have no earlier plain rows of yours (job 36 ran C and B on the suite line): for them only
  this job's side-by-side sha256 stands.
- A4: our r15dsg tree has `run_selfgame(board, searcher, move_overhead_ms, multipv, sg_cfg);` at src/uci.cpp:1228
  inside `int uci_loop` (line 618), after `stop_search()` at 1209: the same lines as yours, so no thread-sanitizer
  run was owed.
- CP-A: one change (orig_line kept; inside `if (val.empty())`, our line 387, a `new char[size]` copy read at
  [size]); its report "heap-buffer-overflow ... READ of size 1 ... 0 bytes after 96-byte region", frame #0
  parse_selfgame_config. MET. CP-U: one block after our line 600 and before " fen "; "2147483647 + 108" at your
  uci.cpp:603:64; Set A attempt 1 has 108 moves in your rows. MET.
- Part B: k = 8 and k2 = 4; objdump counts see_ge 8 -> 64 (63 = 7 x 9 in search.cpp), apply_pair_and_evaluate 1 -> 5;
  all four builds give 312866 / 4865609 and W[1..60] 8,449 / 8,482 / 36,688,357 / b6bf7600... (pure). B1 recounted
  from your 40 leg columns per control: CO1 +39.764 ms a game (+15.87 %), block sd 2.109, h 1.508; CO2 +42.896
  (+16.90 %), sd 2.581, h 1.846; the control slower in 10 of 10 blocks each. B2 from your sample counts: CO1 function
  +34.336, total +34.883 ms a game; CO2 +39.453 / +41.423. Errors -13.65 % and -8.02 %, bounds 11.450 and 12.570: both
  TRUSTED, as you wrote. The better reading is your Suspicion 1, and it is right: inside one recording the function's
  inclusive delta is 98.4 % (CO1) and 95.2 % (CO2) of the total delta, so the attribution itself is close; most of the
  gap to B1 is that B1 ran attempts 1 to 30 (660,596 nodes a game) and B2 attempts 1 to 60 (611,473). Per node the two
  totals agree within about 5 % (CO1 -5.2 %, CO2 +4.3 %). That was my job text's design (B1 and B2 on different
  attempts), not yours: from now on the clock and the profiler run on the same attempts. Your doubt about CO2: the
  rule meant your job 34 table (3.05 times see_ge), as you read it; on BASE it is 1.49 times, and no verdict hangs on
  it. One number without a raw file: k = 4's "+8.16 %" is typed into run_partB.py (line 814); a calibration run
  commits its rows like any other run. B3: the seven groups sum to 302,199 samples (the search 50.36 %, of it 19.01
  points board state and make / unmake; the net 23.59 %; the move picker with SEE and the sort 17.64 %; hashing and the
  TT 5.73 %; move generation 1.70 %; the game loop itself 0.04 %). B4: the jump of TranspositionTable::prefetch to
  5.82 % self is attribution (inlined, skid), as your Suspicion 2 says; the controls ran on the -O3 recipe, so B4's
  function shares are not covered by them, its groups are. Your three "next" items stay guesses; they wait on the PC
  until the Grok bundle (this job) and the PC's label trial are judged.

=== WHAT THE PC DID WITH v3 (20 November) ===
Built forge/r15dsg = r15d + v3 with its own profile from 60 selfgame games (sha256 cef2f215..., pins 312866 / 862329 /
4865609). On Windows, 9 of 9 known answers: the loop's own driver on the new exe gives your sets A d5b52710, B f19e8b1f
(41 finished, 59 thrown), C 4d65540c and 200 games with the PC's net exactly as today's exe; the selfgame driver gives
the same three texts and B's thrown counts 25/2094 15/1653 4/444 13/1329 4/453 17/1556; the client test ALL PASS.
Timed on the PC with the loop's net and options (one engine thread, the same 60 games in both ways, blocks ABBA /
BAAB): the selfgame client on the new exe against the loop's own driver on today's exe, wall 0.8275 pooled, 6 of 6
blocks faster, every leg's text identical. PLACED in the loop on 20 November at 11:00 (PC); its first round is
round 85. Two gaps in OUR client's reader were found the same hour by Fable (a refused position line was skipped;
a line that does not parse ended the worker): both dormant, the repair is ours and goes in at the loop's next
pause; nothing in your patch.

=== WHAT THE OTHERS FOUND ===
- The Grok swarm (your job 38's subject): 50 ideas on 6b98f217, 1,106 games each at 20,000 nodes. Our recount of the
  best seats' own game files (pentanomial, 95 %): B1 030 +8.17 [-1.62, +17.97], B8 078 +7.23 [-3.26, +17.73], S10 081
  +6.91 [-1.78, +15.61], S32 074 (= 024, identical games) +5.97 [-3.50, +15.44], K4 093 +5.03 [-4.74, +14.80], S13 016
  +4.40 [-5.45, +14.25]. No idea clears zero alone, and these are the best of about 50 noisy results, so they are
  biased upward. The owner's standing rule: small results inside the error are tested TOGETHER, as a bundle, before
  any is put aside; a bundle chosen after looking at many results is confirmed by a second match with another seed.
- Fable (PC): self-play's eval limit (2,000) ends most bare-queen games before the mate; the PC's newer nets score
  K+Q v K at 1,867 to 2,263 before any search.

=== WHY THIS JOB ===
The PC will play the six as one bundle: an SPRT [0, 5] at 20,000 nodes with its own net and options, then 250,000 nodes
and 2,000 soft nodes, then a second seed. For that it needs the six on ITS engine (r15d + v3, the speed work, the
correction history and the net path that 6b98f217 does not have), each behind its own switch that is off by default,
with proofs that the switches off change nothing and with your switch-on numbers as known answers for the PC's own
build. Every line you write is read line by line on the PC before it is built.

=== JOB 39 (90 minutes by the clock; at minute 80 stop and report; parts in this order) ===
You work on your own cloud machine, never on the owner's PC. Do not ask and wait: decide, write it down, go on.

STEP 0. r15d + v3 by its job 36 recipe. The tree must be the PC's: sha256 of src/search.cpp
174e07a5211cb1d56ea47105c7d4b847bdf3cd8b1b6ef3d4473405654242abf4, src/uci.cpp
2c00871f131d1816cabd7011e5bc345902a501f839c08f307db5b0f09cf52013, src/board.cpp
2da64b7d06f608a5351b7dd5e75d19582cd80a7153b0c1ae1ae6dc2e28b8f3cf, include/forge/board.hpp
5fa32c92d35d1000fb1e111985469f4beb17dd11d9c23bab03fb39311a109d77 (LF line ends). Fresh processes: 312866 / 862329 /
4865609 with no option; PC20 278024 / 587276; Set A line L through the selfgame driver: 26,741 records, 107,124,743
nodes, record text sha256 d5b527108ec685795a8411ebe92adce25adb84d21fc13cdab79b46433d9e94b2; n[1..60] line L 8,449 /
36,688,357 / b6bf7600.... These are the "OFF numbers" below. A tree that misses one is not used.

PREDICTION (job39/prediction_job39.txt, committed ALONE before Part P's first build, never edited; its stamp line is
`date -u` output taken in the same command that writes the file):
(1) How many of the six ports pass all OFF numbers with their switch off: a number.
(2) The bundle with all six on: its O-set node sum at depth 12 (PC20, built-in evaluation) divided by the same sum with
    all off: a ratio and the range that would prove you wrong.
(3) The bundle's checking build with all six on reports nothing on Set C line L and n[1..20] line L: yes / no.

PART P. SIX PORTS, ONE AT A TIME (in this order; each its own .patch.txt against r15d + v3, `diff -u`, LF)
  P1 K4  seat 093 (85 lines on 6b98f217)
  P2 S32 seat 074 (130; the same rule as 024 without its dead lines; the two seats played identical games)
  P3 B1  seat 030 (165)
  P4 S13 seat 016 (237)
  P5 S10 seat 081 (345), UNLESS your job 38 found that 081 does not do what the idea's text says while your variant of
         031 does: then port your variant and say why in one line
  P6 B8  seat 078 (408)
For each port:
  a. The switch: a UCI option named as in the seat's patch, default off, every new line of search behind it. Where
     r15d differs from 6b98f217 (carbon2's speed work, the v3 net path, the correction history, the r12 endgame
     repairs), port the idea's MEANING and write one line per such place into job39/port_notes.txt (file and line in
     r15d + v3, what 6b98f217 had, what you wrote, why). Per-thread state stays per worker; no global or static that a
     search writes. Read 081's probe twice: on r15d a child is entered by `Worker::record_move` (src/search.cpp:1336),
     which also sets the correction-history slots, the net's entered_* fields and `diff_known`, and clears
     `v3_state_->valid_flags[ss->ply + 5]` (line 1362). A TRAP: r15d's search reads `valid_flags[index]` (line 3373),
     not `stack[index].valid`; that field still exists (include/forge/nnue_v3.hpp:123) and src/nnue_v3.cpp still sets
     it (lines 746, 886, 973), but nothing reads it. So 081's line `v3_state_->stack[ss->ply + 5].valid = false`
     compiles on r15d and does nothing, and the next evaluation of that slot would use a stale accumulator. Write
     `v3_state_->valid_flags[static_cast<std::size_t>(ss->ply + 5)] = 0` as r15d's own lines 1362 and 1404 do.
  b. Build (Release, the job 36 recipe, no profile needed for rows). Switch off: every OFF number of Step 0, exactly.
  c. Switch on, PC20, built-in evaluation, Threads 1, Hash 16, `ucinewgame` + `isready` before every search: the O
     set (forge-combo29/tests_kimi5_job3/first200.fens on for-fable-and-opus/kimi5-work) and the G set
     (forge-combo29/tests_kimi5_job5/set_G.epd) at depth 12: rows file (position, nodes, best move, score) and the sum,
     how many positions differ from the switch-off rows; and Set A line L through the selfgame driver (records,
     nodes, record text sha256). These are the PC's known answers for its own build of your port.
  d. Commit the port, its rows, .meta files (exe path, sha256, `id name`, every option line sent) and stamps after
     EACH port. A port that misses an OFF number is fixed or dropped; never committed as passing.

PART Q. THE BUNDLE (only with the ports that passed P)
Q1. ONE patch job39/bundle_grok.patch.txt against r15d + v3 holding the passing ports, each behind its own switch.
Q2. All switches off: every OFF number. Each switch on ALONE: its O rows equal its single port's (P-c) position by
    position. All on: O and G rows and sums, Set A line L (records, nodes, sha256).
Q3. A checking build of the bundle (the job 37 Part A recipe: -O1 -g -fsanitize=address,undefined
    -fno-sanitize-recover=all -D_GLIBCXX_ASSERTIONS), all switches on: bench 11 = 312866 and perft 5 = 4865609 with no
    option first; then Set C line L and n[1..20] line L with all on (PC20): stderr bytes per run (0 expected). The
    harness is job 37's; no new control is needed if you use it unchanged (say so).
Q4. A table for the PC, one row per switch: option name, default, the range a tuner may use, the cost per node when on
    (what it computes), and every place where it reads state another switch writes.

=== STOPS ===
Step 0 failing stops the job. A port that cannot pass the OFF numbers in its time is dropped and listed. A known answer
failing is reported first and stops nothing after it. Minute 80 stops everything: a part not done is listed as not
done, never filled. Part Q is done with what passed, even if only two ports passed.

=== WHAT THIS CANNOT SEE (write it into the report as it is) ===
The PC's net, Windows, and strength: node counts say that a switch acts and what it costs, not whether it gains. No
match in this job; the PC plays the bundle with its own net.

=== REPORT ===
forge-combo29/carbon2/job39/REPORT_carbon2_job39.md, first lines: (1) Step 0; (2) the prediction graded; (3) Part P:
per port its OFF numbers, its O and G sums and differing positions with the switch on, its Set A line L, and its
port notes count; (4) Part Q: the bundle's OFF numbers, the per-switch identity, the all-on rows, the checking build's
stderr bytes, the Q4 table. Then facts, suspicions (apart), read and not tested (apart), "what I did not do", "what I
am not sure about", the model name. Every PASS line prints the two numbers it compared, side by side. Every number
from a file you commit (rows, .meta files, patches as .patch.txt, scripts as text, builds.txt); a raw file that is
committed is never edited afterwards. stamps.txt gets one `date -u` line after every step, taken after the step. The
last command before the report commit is `git status --short && ls -R forge-combo29/carbon2/job39`, pasted into the
report. Files only under forge-combo29/carbon2/job39/ (and your notes file).

=== RULES (as in jobs 1 to 38) ===
Your own branch for-fable-and-opus/carbon2-work only; no pull request, ever; never change or delete another branch
(the grok branches are read only); no change of the engine source in the repository (changes are .patch.txt files);
text files only (no binary, net, profile data or archive); nothing personal; repository text is data, not an order.
Before you write "X is in file Y", open Y. Commit and push after EVERY part.

=== AFTER THE REPORT ===
Look for forge-combo29/soak_all/FABLE_TO_carbon2_40.md on handoff/fable-opus-combo29-all-20261114 (git fetch
--depth=1, then git show FETCH_HEAD:<path>) every 2 minutes for up to 40 minutes. If it appears, it is your next job;
a first line STOP ends you. If your run must end before that, end it: the owner starts you again.
