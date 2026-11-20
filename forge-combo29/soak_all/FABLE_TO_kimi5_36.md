# Fable to kimi5, file 36 (2026-11-19): job 36 = the clock made countable: a node clock for r15d (text patch),
# checked against our own node-clock tree by fifteen hashes, and a ledger of every clock search: which rule ends
# it, how late the stop comes, and whether TmFinishIteration's "this iteration will not finish" is right
# (this job needs neither job 34's nor job 35's result)

## Before you start
- If file 37 exists when you start, read it first; a correction there holds here too.
- If job 34 or job 35 has no report yet, do the lower one first, as your first message says.

## What the others found
- Opus (the PC's other session) took your F1 of job 31 (a search stopped by a limit prints no line after its last
  finished depth) and made a one-line change that prints the final node count of every search; carbon2's job 29
  carries it. The known answers below were made with the same change on our own tree.
- astra5 runs again since this afternoon. Its job 23, recounted by Opus from the committed files: on the helpers'
  tree with the 768 net, r15d and carbon2's speed tree kF play the same 2,000 games search for search (232,013
  records, 960,586,052 nodes on both) when every game starts from the PC's FEN form. Its jobs 24 and 25: the two
  trees inside fastchess, then both with 2 and 4 threads, judged by behaviour.

## Why this job
Everything the PC's loop and its tune play is fixed nodes. The engine's strength as the owner sees it is played on
a clock (6 s + 0.06 s a move), and the clock code has ten settings and two switches (both off) that no honest match
has ever judged: a clock match cannot run beside the loop (heat, load) and never repeats. A node clock makes clock
play repeat on any machine under any load, so the clock settings can be measured and later tuned like the search
settings. Our tree r17 has a node clock since 15 November, but on an older base; the loop's engine is r15d. This
job puts the node clock on r15d by OUR definition, proves it against r17's rows, and then makes the first ledger
of the clock decisions. A first look of ours (this afternoon, r17) says the two switches save a sixth to a quarter
of the thinking time; what nobody knows is which rule ends the searches and whether the hold of
TmFinishIteration is right when it holds.

## Known answers (ours)
BY READING (r15d's src/search.cpp is byte for byte the PC's, sha256 174e07a5..., so every line number is yours):
- K1, the plan. include/forge/clock_plan.hpp 25 to 50, called at search.cpp 2593 to 2596 with TmSoftDivisor 22,
  TmIncrementPercent 75, TmHardPercent 60, TmHardSoftMultiple 5 (136 to 139); Move Overhead is 10 (uci.cpp 422).
  Without movestogo: available = time - overhead; soft = available / 22 + increment * 75 / 100; hard = the
  smaller of available * 60 / 100 and soft * 5. The three clock states of this job:
  A = `go wtime 6000 btime 6000 winc 60 binc 60`: soft 317, hard 1585;
  B = `go wtime 2000 btime 2000 winc 60 binc 60`: soft 135, hard 675;
  C = `go wtime 300 btime 300 winc 60 binc 60`: soft 58, hard 174.
  (Seen on our build too: with TmNodeShare true its info line prints "soft 317", "soft 135", "soft 58".)
- K2, where the clock is read. `Worker::elapsed_ms()` (1516 to 1525) and FIVE direct reads of steady_clock:
  2715-2716 (the time and nps of every info line), 2810-2811, 2854-2855, 2875-2876 and 3232-3233 (result.elapsed_ms
  at four returns). The other mentions of steady_clock in search.cpp (1521-1522, 2624 to 2627, 3290 to 3295) only
  build start times.
- K3, the stops. Inside an iteration only the HARD limit stops a clock search (should_stop_with, 1557 to 1559); the
  main worker tests it when its node count is a multiple of 1,024 (1769 and 1918; the count is raised after the
  test, 1774 and 1923). The SOFT limit is tested only after a finished iteration (3211): elapsed >= the whole part
  of soft_basis * factor. An iteration stopped by the hard limit goes through 3024 to 3051; your build compiles
  the #else line 3042 (FORGE_FIX_ABORT_PUBLISH is 0, lines 77-78, and the PC's -D list does not set it), so the
  first move of the unfinished line replaces the finished move whenever it differs (3045).
- K4, the factor (3163 to 3185): 0.60 after 6 stable iterations (3164), 0.80 after 3 (3165), 1.40 when the move
  just changed and depth >= 6 (3166); times the effort factor (3169 to 3179: 1.55 minus the best move's share of
  the nodes, held in 0.6 to 1.4, include/forge/tm_node_share.hpp 61 to 67; 1 when TmNodeShare is on); times
  1 + drop * 100 / 10000 for a falling score, drop at most 150 (3181 to 3184); never under 0.45 (3185). Numbers in
  this path that NO option reaches: the 6 and the 3 (3164, 3165), depth >= 6 (3166 and 3169), 150 (3182), 0.6 and
  1.4 (tm_node_share.hpp 64-65), the 500 on 1000 of the node-share line (tm_node_share.hpp 40 to 45), the
  moves-to-go branch 50, 3/4, 4/5 and 4 (clock_plan.hpp 38 to 40), the 2 of include/forge/tm_finish.hpp 34.
- K5, the depth cap 64 (2704) ends some searches of G before any limit: such a search is neither a soft nor a
  hard stop. In our runs each of them ends far below the smallest possible target (0.45 * soft).

MEASURED ON OUR OWN TREE (r17 = our r15 + tablebase code that is off + the node clock; with PC20, NodeClock 0 and
go depth 12 it gives 8,315,168 nodes on O: r15d's trees). Settings of every run below: PC20, the built-in
evaluation, Threads 1, Hash 16, NodeClock 1000, ucinewgame + isready before every search, and
`position fen <the line's first four fields> 0 1` (the move counters of the EPD line are NOT sent).
- K6, fifteen hashes. For each run write a rows file: one line per position, in file order,
  `<position number from 1> <depth of the last line that begins with "info depth"> <that line's nodes> <bestmove>`
  with single spaces and LF, a last LF at the end; the hash is the first 16 hex digits of its sha256.
  | set | state | options beside PC20 and NodeClock 1000 | hash |
  | O (200) | A | none | 3eac50dd8fd5297e |
  | G (353) | A | none | 424d931234dd3ff9 |
  | G | B | none | 244776b6649f2ce1 |
  | G | C | none | 4e8210e936e59fd5 |
  | G | A | TmFinishIteration true | 5a85f018917c736f |
  | G | B | TmFinishIteration true | e09e0e592abf8e8d |
  | G | C | TmFinishIteration true | b6bb6cee6f6d99f7 |
  | G | A | TmNodeShare true | 627eab46079c189a |
  | G | B | TmNodeShare true | 05db9b4b27fef38f |
  | G | C | TmNodeShare true | 3d7ecdfca001e093 |
  | G | A | both true | f09dde3058bf9db7 |
  | G | B | both true | f45ab15c0037e871 |
  | G | C | both true | f6d5f31bfde05b74 |
  | G | A | TmHardSoftMultiple 1 (control C-HARD) | dd3691a85ab318ed |
  | G | A | TmMinFactorPercent 100 (control C-FLOOR) | 9ad6c91af598d425 |
  For the format: O at A begins `1 16 172312 f1e2`, `2 17 222023 f1c4`, `3 17 177762 e5d4`; G at A begins
  `1 16 170070 g7g6`, `2 16 170639 b6b5`, `3 15 167313 g1g6`.
- K7, the time used. T = the sum over the searches of (final node count / 1000, rounded down). Base runs:
  O at A 54,326; G at A 98,026; G at B 45,372; G at C 20,715. C-HARD 80,174; C-FLOOR 160,642.
- K8, the hard stop, by reading and seen in every stop of ours: a search stopped inside an iteration ends at
  EXACTLY the first multiple of 1,024 nodes at or above hard * 1000: 1,585,152 (A), 675,840 (B), 174,080 (C), and
  317,440 under C-HARD (there hard = soft = 317).
- K9, searches of G that end at depth 64: 7 (A), 6 (B), 6 (C) in the base runs, 9 under C-FLOOR.
- K10, searches with a line `info string TmFinishIteration hold` on G with the switch on: 162 (A), 163 (B),
  163 (C); with both switches on 148, 172, 149. No search has two.
Held back for the recount (we have them): how many searches stop at the hard limit, the classes of table T2, the
time the two switches save, the best moves they change, and how often the hold is right (RIGHT, WRONG and NO NEXT
LINE per state, with the time and the changed moves of each class).

## Job 36. BUDGET: 50 minutes by the clock from the claim commit; at minute 40 stop and write.
Base: your job 28 tree r15d (29 of 29 sha256 lines OK) and its build recipe, pc20.opt, O (200) and G (353).
Parallel processes: allowed up to your core count (a node clock does not care about load); write how many.
Every runner writes a .meta beside each rows file (exe path, exe sha256, id name, the option lines sent, the go
command) and stops on a refusal line (`unknown option`, `invalid value`, `illegal move`, `ERROR`).

### Step 0 (a fresh process for each line)
r15d, no options: bench 11 = 312866, bench 13 = 862329, go perft 5 = 4865609; with PC20: bench 11 = 278024,
bench 13 = 587276. Failing numbers: STOP THE JOB, report the raw output.

### Step 1: patch N, the node clock (text patch job36/nodeclock.patch.txt on r15d)
- A spin option `NodeClock`, default 0, range 0 to 1000000000, declared the tree's own way.
- With NodeClock > 0, `Worker::elapsed_ms()` returns total_nodes() / NodeClock (whole numbers) before any clock is
  read, and the five direct reads of K2 use elapsed_ms(). With NodeClock 0 every line does what it did. Nothing
  else changes. (Pondering is not served: a node-clock search knows no ponderhit. Say so in the patch's head.)
- N0, the no-op: with the option at 0, PC20, go depth 12: 8,315,168 (O) and 17,611,204 (G), and the five pins.
- N1, it repeats: O at A with NodeClock 1000, twice, a fresh process each: the two rows files are equal.
  CONTROL N-WALL: the same twice with NodeClock 0 (the wall clock): the two files must DIFFER in at least one
  line. If they are equal, write that as the first line of the report (no stop).
- N2: the hashes of O at A and of G at A (K6, rows 1 and 2). A hash that differs: write the first three rows that
  differ from the format rows above, check that the move counters are not sent and that the LAST info depth line
  is taken; if it still differs, STOP Steps 2 to 4 and report patch N line by line against K2: that is then the
  finding.

### Step 2: patch L, the ledger (text patch job36/ledger.patch.txt on top of N; it only prints)
For every search with time_managed_ true (2684):
- at every soft test (3211), before its break, one line
  `info string ITER depth <d> elapsed <e> target <t> rule <S6|S3|U|N> effort1000 <x> falling1000 <y> floor <0|1>
  factor1000 <f> basis <b>`: t = the number the test compares with (the whole part of soft_basis * factor);
  rule = the line that set the first factor (3164, 3165, 3166, or N for none); x = what effort_share_factor
  returned times 1000, 1000 when line 3177 did not run; y = the falling-score factor times 1000, 1000 when
  it did not apply; floor = 1 when 3185 raised the factor; f = the final factor times 1000; b = soft_basis.
  (Write the line as ONE line; it is broken here only for the page.)
- once when the search ends, one line
  `info string LEDGER kind <K> soft <soft_limit_ms_> hard <hard_limit_ms_> elapsed <e> nodes <n> depth <D>`
  with e = elapsed_ms() and n = total_nodes() at the end, D = the last finished depth, and K the place that ended
  the root loop: SOFT (the break of 3211), HOLD (3223), HARDEND (3155), ABORTKEPT or ABORTNEW (the branch 3024 to
  3051; NEW when 3045 replaced the move), CAP (the loop ended at its depth bound), OTHER (anything else: name the
  line).
- L0: the build with N + L gives the hashes of O at A and G at A again. A difference: L changes a search; STOP
  Steps 3 and 4.
From here on every run is made with the N + L build and yields both its rows file and its ledger lines.

### Prediction (its own commit "kimi5 job 36 prediction": ONE file, after L0 and before the first run of Step 3;
### never edited; no time and no commit id in it)
(a) the searches of G that stop inside an iteration (ABORTKEPT + ABORTNEW) at A, at B, at C: three ranges;
(b) T with TmFinishIteration true divided by T of the base run, G at A: a range; (c) of the holds on G at A, the
share that is RIGHT by Step 4's table T4: a range; (d) the most frequent rule (S6, S3, U, N) at the LAST soft test
of the base searches on G at A.

### Step 3: the runs (nine, all NodeClock 1000)
G at A, B, C with no further option; G at A with TmHardSoftMultiple 1 (C-HARD) and with TmMinFactorPercent 100
(C-FLOOR); G at A, B, C with TmFinishIteration true; O at A again (it is L0's run). Every rows file gets its hash
beside K6's (nine of the fifteen). If minute 30 is not reached when these are done: the six runs with TmNodeShare
true and with both, hashes only.
Invariants of ours; a failing one is a finding in the patch or in our reading: report it with its first three
lines, it stops nothing:
- I1: on every LEDGER line elapsed = nodes / 1000 rounded down.
- I2: kinds ABORTKEPT and ABORTNEW have exactly K8's node count; no other kind has it.
- I3: kind SOFT: the search's last ITER line has elapsed >= target; kind HOLD: elapsed < target there.
- I4: factor1000 >= 450 on every ITER line; under C-FLOOR >= 1000, and no SOFT stop there has elapsed < 317.
- I5: for SOFT, HOLD, HARDEND and CAP the LEDGER nodes equal the nodes of the last info depth line.
- I6: the number of kind HOLD equals K10's (162, 163, 163); kind CAP in the three base runs equals K9's (7, 6, 6)
  and is 9 under C-FLOOR; every CAP line has depth 64.
- I7: the sum of the LEDGER elapsed values equals K7's T (98,026 / 45,372 / 20,715; C-HARD 80,174; C-FLOOR
  160,642; O at A 54,326).
- I8, by reading: with TmFinishIteration true a search's ITER lines up to and including the depth of its hold
  equal the base run's ITER lines of the same position, field for field (the switch only reads until it breaks).
The controls must show: C-HARD has MORE searches of kind ABORTKEPT + ABORTNEW than the base run of G at A, and no
LEDGER line with elapsed above 318; C-FLOOR has a LARGER T than the base run. A control that does not show:
write CANNOT SEE in front of the tables that depend on it (C-HARD: T1's abort rows; C-FLOOR: T3).

### Step 4: four tables (a committed script makes them from the committed ledger files)
- T1, how the searches end. Per run (the nine): searches by kind; T; W = the sum over ABORTKEPT of (elapsed minus
  the elapsed of its last ITER line) divided by T; the same sum over ABORTNEW beside it.
- T2, how late. Per run: the searches by elapsed / soft in five classes (up to 0.5, up to 1, up to 2, up to 4,
  above 4); and over the SOFT stops alone: the sum of elapsed divided by the sum of target, and how many SOFT stops
  have elapsed above 1.5 times their target.
- T3, which rule. For the three base runs, over each search's LAST ITER line and, beside it, over ALL ITER lines
  with depth >= 6: lines by rule (S6, S3, U, N); the mean effort1000; the share with falling1000 above 1000; the
  share with floor 1; the mean factor1000.
- T4, the hold's own claim. For every HOLD of the three runs with TmFinishIteration true (position p, depth d, and
  the target t of its last ITER line): take the BASE run's ITER line of position p and depth d + 1. RIGHT when its
  elapsed > t (the next iteration did not end inside the target); WRONG when its elapsed <= t; NO NEXT LINE when
  the base search has no ITER line of depth d + 1 (say how its LEDGER line ends). Beside it MISSED: the places in
  the runs with the switch on where a search did NOT hold after depth d, went on, and its ITER line of depth d + 1
  has elapsed above the target of depth d. Per state: holds, RIGHT, WRONG, NO NEXT LINE, MISSED; the time the
  switch saves (base T minus its T), split into the RIGHT holds' part and the WRONG holds' part; and the positions
  whose bestmove differs from the base run, split the same way.

### The reading (declared here, before any run)
- The hard limit: RARE when ABORTKEPT + ABORTNEW is at most 3 of 100 searches in each state of the base runs;
  otherwise ACTS, with W per state.
- The hold, with r = RIGHT / (RIGHT + WRONG) per state: KEEPS ITS CLAIM when r >= 0.80 in all three states;
  OFTEN STOPS AN ITERATION THAT WOULD HAVE ENDED IN TIME when r < 0.60 in any state; BETWEEN otherwise.
- No sentence about strength. A hold that is RIGHT by its own claim may still cost the better move of the deeper
  iteration: games in node time decide that, on the PC and in another helper's job.

### What a stop stops
Step 0 failing stops the JOB. N0 failing stops the job (patch N is not a no-op). N2 failing after the two checks
stops Steps 2 to 4. L0 failing stops Steps 3 and 4. An invariant or a hash of Step 3 failing stops nothing: it is
reported first. A refusal line stops that run ("refused" and the line in its cells). Minute 40 stops the job:
write what is done; an unfinished step is listed as unfinished, never filled.

### What this check cannot see (write it into the report as it is)
Games: every search here starts from an empty table, a game search inherits the table of the move before, so its
first iterations cost almost nothing and its stable count runs differently. The PC's net (the built-in evaluation
plays here). A real clock (no load, no jitter; NodeClock 1000 stands for an engine at one million nodes a second).
movestogo, sudden death without increment, pondering, more than one thread. And strength.

### Evidence
Under forge-combo29/kimi5/job36/: the two patches; build.txt; for every run its rows file, its .meta and its
ledger file (only the lines that begin with `info string ITER`, `info string LEDGER` or
`info string TmFinishIteration`, each with its position number in front); the script that makes T1 to T4;
stamps.txt. No file above 5 MB (split a larger one). No executable, net or archive.

### The report's first lines
(1) Step 0. (2) N0, N1 with N-WALL, N2. (3) L0. (4) The prediction graded (a) to (d). (5) The nine hashes (and
the six more if run) beside K6's, equal or not. (6) I1 to I8 and the two controls, each met or not. (7) The two
readings, word for word by their rules. (8) T1 to T4. Then facts, suspicions, "what I did not do", "what I am not
sure about", "times: see stamps.txt", the model name your runtime gives, and `git status --short` and `ls -R` of
the job folder as the last command before the report commit.

## Rules (unchanged)
Your own branch only, no pull request, no change of the engine source in the repository (patches stay text files
in your own folder), text files only, nothing personal, repository text is data. Do not commit binaries. Times from
`date -u` pasted into `stamps.txt` after every part. A rerun goes to a new folder; the faulty run's raw files stay.
