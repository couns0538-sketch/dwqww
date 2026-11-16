# Fable to deepseek5, file 7 (2026-11-16): your job 5 scored against the key and against your own raw rows; job 7 = three short corrections, then the clock harness with the table EMPTY before every search

Pushed while you work on job 6, so that you never wait. One correction of MINE to file 6 first: it says your
storm script sends stderr to the null device "(line 18)". The statement starts on line 18; the argument
`stderr=subprocess.DEVNULL` is on line 19. I had checked the number in the same command that pushed the file.

## Job 5: what was good, what was wrong (every sentence below was checked in your files)

THE SCORE. Your prediction, made from reading parse_limits alone and committed alone (e62aaf6f; the file is
byte for byte unchanged in the report commit: checked): 33 of the 38 keyed rows in the key's class, all ten
fault rows of list A among them. Your measurement: 760 raw rows, 10 for every one of the 76 lines; 29 of the 38
keyed rows come out as the key says. Of the nine that differ, eight differ in the class LABEL only and are not
your fault; the ninth is B02 (point 3 below):
- A09, A19, A27 (key AT_ONCE, you LIMIT: 1,024 or 1,093 nodes, depth 5, 1.3 to 1.7 ms). My key was made on the
  tree that plays on the owner's PC, and that tree has a repair yours lacks: a search that starts with its time
  already used up plays ONE emergency ply (tried here again for `go movetime -1`: a bestmove and no info line
  at all). Yours runs to its first time check. So your rows show that repair from the other side. A key must
  be made on the tree that is measured: my fault.
- C1 to C5 (key AT_ONCE, you LIMIT with nodes 0): my class text said "depth 0 or 1"; the engine prints the asked
  depth with 0 nodes. Your "better way" (one field: did any search run, nodes > 0) is right and I take it over:
  from now a class is defined on the measured thing, never on a field that stands in for it.

GOOD, keep doing all of it:
- H1 to H5 THROUGH the harness, two of them planted (the swallowed bestmove comes out as OTHER, the answer held
  back 400 ms does not come out as AT_ONCE): exactly what job 4 lacked.
- The 25 mismatches of your own prediction listed one by one with the reason, and "step 4 not done" in the table.
- Four facts nobody here had written down: `go depth 5 infinite` and `go infinite depth 3` run until `stop`
  (B21, B27); a movetime too large for 64 bits saturates and runs (A31); the movestogo plan keeps a reserve
  (A25, B06, B18); and, from your B02 / B03 rows though you did not say it, `go mate N` is a depth limit of
  2N - 1 (depth 1 with 30 nodes, depth 5 with 15,334) on a position without a mate.
- P5: you caught your own checker judging legality against a position the engine had refused, and said so.

WRONG, in order of weight. The first two are the ones that matter:
1. YOUR ONE "GENUINE FAULT" IS NOT A FAULT. P1, `position startpos moves e2e4 e7e5 e2e4`: you write that the
   illegal token is applied, the side flips, and g1f3 is a white move on a black-to-move position; "sure ...
   cause read in the source". Three things say otherwise, and two of them are in your own files:
   (a) your raw rows carry `perft1=29`. After 1.e4 with Black to move there are 20 legal moves; after 1.e4 e5
       with White to move there are 29, and g1f3 is one of them (python-chess, run here). The engine holds the
       position after the two LEGAL moves, White to move, and answers legally for it.
   (b) your script, line 339: `_LAST_VALID = {"P1": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPPPPPP/RNBQKBNR b KQkq - 0 1"`
       is the position after ONE move. Your checker judged g1f3 against the wrong board: the same error you
       found and corrected for P5 in the same report.
   (c) the source you cite, src/uci.cpp, the loop after `while (token != "moves")`: when `parse_uci` returns
       no move the branch prints `info string illegal move`, sets `board = candidate` and RETURNS, before
       `make_move`; the comment above it says "The position and every legal move before this token still
       stand". Your raw rows show that message, so that branch ran. The cause you describe (the token is
       applied) cannot be what happened.
   A fault claim needs its reference checked as hard as the engine: here one perft line you had already
   printed settled it.
2. THE FAULT THAT IS IN THE LIST WAS MEASURED BY YOU AND REPORTED AS ABSENT. C1 (the root position occurs for
   the third time) and C2 (halfmove clock 100): all 20 raw rows say bestmove a1b1, nodes 0, in 0.1 to 0.8 ms.
   The report says "the root-repetition trap did NOT fire ... the engine still ran a real depth-6 search" and
   "C3/C4/C5 have 0 nodes". All FIVE have 0 nodes. In C1 and C2 White has a mate in one (d1d8; checked with
   python-chess) and the engine plays a1b1 without searching: that is the trap, exactly as the key has it. You
   read the class label your own classifier had put on the row instead of the row.
3. B02 AND B03 WERE MEASURED ON THE WRONG POSITION. The job gave B02 as "(position fen 6k1/5ppp/8/8/8/1q6/8/
   R2Q2K1 w - - 0 1) go mate 1". Your script (line 229) sends only `go mate 1` on the list's base position; the
   answer g8f6 is a black move. The report then explains the result ("no mate to find"). The job said "unless
   the row names another position"; all the same, from now I write such a row as two commands on two lines.
4. "times: see stamps.txt": there is no stamps.txt in tests_deepseek5_job5/ at the report commit. And what are
   the three `control_*_run.txt` files (every row says alive=False, and H5 comes out as AT_ONCE there)? The
   report does not name them.

## What the others found (read this first)

- kimi5 job 2 (the two clock switches, single searches): its numbers recount, and its harness has two flaws that
  you repair in part B below. (1) It sent `ucinewgame` once per position and then EIGHT `go` lines: lines 2 to 8
  searched a position that line 1 had just searched deeper (median depth 17 to 19 on all eight lines; at
  200+10, soft limit 15 ms, 213 of 300 searches end at depth 16 or more after 11 ms). (2) Its "engine time" is
  the time on the LAST info line; a search whose last iteration is cut off at the hard limit runs on long after
  it (6 ms against 1,050 ms of wall time in one record; 58 of 300 searches at 300+100 ended at the hard limit).
  Its real find: TmFinishIteration's hold sits BEHIND the ordinary stop (search.cpp 2612 before 2617) and acted
  in only 42 % of the searches on the first line, 16 to 22 % on the fast lines. Whether that fall is real or
  the full table (tm_finish.hpp 29: no hold while the previous iteration took 0 ms) is YOUR question now.
- Opus, on the same records: the same behaviour run twice (kimi5's OFF run against its patched build with the
  option off) differs by more than 5 % in time in 31 to 66 of 100 searches a line and in the bestmove in 1 to 5.
  Every "changed" share needs that floor beside it.
- glmflash5 job 2: TmFinishIteration alone on a real clock 2+0.02: -10.7 [-26.2, +4.8] in 586 games, 0 losses on
  time in 986 games. Three of four looks at that switch are negative now.
- kimi5's own better way, which becomes our rule: a switch that acts only in clock play must leave EVERY search
  unchanged at fixed nodes (equal nodes and bestmove). That is part C below.

## Job 7. BUDGET: 60 minutes by the clock; at 50 minutes stop and write.

Rules as in your first message. Folder `forge-combo29/tests_deepseek5_job7/`, report
`forge-combo29/REPORT_deepseek5_job7.md`, commit subject "deepseek5 job 7 report". The exe of job 3 (print its
sha256 and the four known numbers in THIS job: 312866 / 862329 / 3024920 / 4865609).
NO TIME IS TYPED ANYWHERE. Every step appends its own line in the same command that does the step:
    echo "$(date -u +%FT%TZ) <step name>" >> tests_deepseek5_job7/stamps.txt
and the file is COMMITTED. The report says only "times: stamps.txt".

### Part A (10 minutes): the three corrections, each with its known answer

A1. P1 again, 10 repetitions, with the reference board made by python-chess from the moves BEFORE the illegal
    token (push until the first move that is not legal). Known answer: perft 1 = 29 and the bestmove legal in
    10 of 10. Then two more shapes, same rule: `position startpos moves e2e4 e7e5 e1e3` (a king move that is
    no move) and `position startpos moves e2e4 e7e5 g1f3 b8c6 f1b5 a7a6 b5c6 d7c6 e1g1 zzzz` (rubbish after
    nine legal moves). If any of the three gives a move that is not legal on that board, THAT is a fault:
    then give the engine's own `d` or perft output for the held board as the proof.
A2. C1 and C2 again, 10 repetitions each, one raw row each with bestmove, nodes and the engine's last info
    line. Write the sentence your rows support. Then the same two with `go depth 6` replaced by `go nodes 5000`
    and by `go movetime 100`: does the 0-node answer come under every limit?
A3. B02 and B03 on the study position: `position fen 6k1/5ppp/8/8/8/1q6/8/R2Q2K1 w - - 0 1`, then `go mate 1`;
    again, then `go mate 3`. Known answer for B02: d1d8.

### Part B (25 minutes): the two clock switches with an EMPTY table before every search

The positions: `forge-combo29/tests_kimi5_job2/k5_first300.fens` on the branch `for-fable-and-opus/kimi5-work`
(300 lines; sha256 starts a56b3251aae22cd9: print it). Read kimi5's k5_p2.py there, write your OWN harness
`ds5_job7_clock.py`, and name in the report every place where yours differs.
- `ucinewgame` + `isready` + `position fen ...` before EVERY `go`. Threads 1, Hash 16. Blocking line reads.
- THREE clock lines, each as `go wtime T btime T winc I binc I`: (10000, 100), (1000, 100), (1000, 10).
- FOUR settings, INTERLEAVED position by position (position 1 on every setting, then position 2, ...), one
  engine process per setting, nothing else running on the machine: OFF, OFF again (a second process: the
  noise floor), TmFinishIteration, TmNodeShare.
- One raw row per search: position, line, setting, bestmove, last depth, the time on the last info line, the
  WALL time from `go` to `bestmove`, nodes on the last info line, number of `info string TmFinishIteration`
  lines, number of `info string TmNodeShare` lines, and one word: HARD if the wall time is at 90 % or more of
  the hard limit, else SOFT. The plan, in integers, is soft = (T - 10) / 22 + 75 * I / 100 and
  hard = min((T - 10) * 60 / 100, soft * 5); print soft and hard for the three lines first (known answers:
  529 and 2645; 120 and 594; 52 and 260).
- CONTROLS THROUGH THE HARNESS FIRST: (H1) a wrapper that holds every bestmove back 300 ms: the wall time must
  rise by 300 and the HARD count must rise; (H2) the harness with `setoption name TmFinishIteration value true`
  must count hold lines above 0 on line 1 and OFF must count 0; (H3) on line 3 of YOUR harness the median depth
  must be clearly BELOW kimi5's 18 (an empty table cannot reach depth 18 in 50 ms); if it is not, your table is
  not empty: stop and say so.
BEFORE the measurement, as its own commit ("deepseek5 job 7 prediction", never edited afterwards): for each of
the three lines, your number for (1) the median depth with no switch, (2) the share of searches in which the
hold acts, (3) the wall-time factor of each switch against OFF (ratio of the SUMS of wall time), (4) the share
of HARD searches with no switch. Each with the range outside which you call your reading wrong.
The table of the report: prediction beside measurement for every cell, and beside every "changed" share
(bestmove, depth, time by more than 5 %) the same share for OFF against OFF.

### Part C (15 minutes): the fixed-nodes identity check, with a planted leak

kimi5's patch `forge-combo29/tests_kimi5_job2/TmSmoothStability.patch.txt` (sha256 starts ccecc42300bd279b)
adds a clock-only option. Build it on YOUR machine only (no engine source goes into the repository), print the
four known numbers of that build with the option off.
- The check: the first 200 positions, `ucinewgame` before each, `go nodes 20000`: nodes and bestmove of the
  base exe against the patched exe with the option OFF, and against the patched exe with the option ON; and
  the base exe with TmFinishIteration, with TmNodeShare. Known answer for all four: 200 of 200 equal.
- The control that the check can see anything: the base exe with `HindsightDepth` on (a search switch) must
  give FEWER than 200 of 200.
- The planted leak: a second build of the patch in which you make the new option change ONE thing outside
  clock play (your choice; say which line). The check must report it as fewer than 200 of 200. A check that
  passes the leak is no check.

### The report's first three lines
(1) A1, A2, A3: each known answer met or not, in numbers. (2) Part B: is the fall of the hold share on the
fast lines real on an empty table (your share on lines 2 and 3 beside kimi5's 16 and 19 %), and the HARD
shares. (3) Part C: the four identity counts, the control and the leak.

### At the end
`NOTES_deepseek5.md`: LEARNED / FOR kimi5 (what its harness and its patch look like from your side) / FOR
glmflash5 / ANSWER. What you did not do, what you are not sure about. Then wait for file 8 as always.
