seat 02
area 2 (UCI COMMANDS under ASan + UBSan)
branch for-fable-and-opus/swarm-02
seed 201 (run 2 seed 211)

## 21:12Z-21:55Z — engine, all three area-2 jobs
SEAT 02. Release build 6b98f217 sha256 e06310ec..., HONESTY PASS (bench 11 312866 / 13 862329 / 16 3024920 /
perft 5 4865609). ASan+UBSan build sha256 b109a0a5..., BOTH required proofs (nm 35 __asan_ / 15 __ubsan_; a
planted fault on a scratch copy counted 3 lines through the same runner, control 0).
JOB 1 (v3, the third harness): 2,000 sequences, 5,827 `go` = 5,827 `bestmove`, 0 crash / 0 hang / 0 sanitizer /
0 illegal. v1 WITHDRAWN for 19-F12: HARNESS_INVALIDATION.md explains what was wrong and what it invalidated.
JOB 2: 5,000 race runs (stop, ponderhit, ucinewgame, setoption Hash, quit during a search), 0 faults.
JOB 3: 82 options x 6-7 values, 550 cases, idle and during a search, 0 faults.

## 21:56Z-22:06Z — checks of other seats, and both broadcast audits
S-C1 CONFIRMS 08-F2: the movetime loss is a fixed 9.4 ms ABSOLUTE subtraction (same at movetime 50 and 200),
and zeroing Move Overhead removes it. Guards added after seat 19's warning: an empty cell or a NaN ABORTS the
verdict (both proven to fire).
S-C2 REFUTES the "silent" half of seat 11's S-F8: the engine DOES print `unknown option UseNNUE false`. The
ignore mechanism is confirmed; a truly silent swallow does not happen.
S-C3 CONFIRMS seat 10's warm-search rule with their exact digits (56,720 cold / 4,951 / 4,516 warm / 56,720
after ucinewgame / 40,569 after Clear Hash). NEW: `bench` is IMMUNE to it (467,411 in all four regimes), so
only `go` searches are affected.
S-C4 CONFIRMS seat 20's S-F20 (LmpBase=8 loses the mate at d10/d12, mate-in-1 untouched). NEW: `mate -9` at d14
converges to `mate -4` at d16/d18 for BOTH settings, so the cost is a two-ply delay plus ~2.1x nodes, not a
worse final answer.
S-C5 CONFIRMS seat 16's S-F6 (book only on `go wtime`/`go movetime`, never on depth/nodes/infinite). NEW: a book
hit CHANGES THE MOVE (startpos: book plays c2c4, the same position searched plays e2e4).
Audit of every node-count result of mine: warm_audit/AUDIT_my_results.md — none used Clear Hash as a baseline;
the only multi-search process is S-C1's latency cells, warm identically in all four, and latency is not nodes.

## 22:00Z — cycle item 2(c)
JOB 1 RUN 2 (seed 211, fresh R set of 996 positions from 60 random games): 2,000 sequences, 5,779 go = 5,779
bestmove, 0 faults. S-F2 reproduced independently: 59 `0000`-on-a-board-with-legal-moves from 42 empty
`searchmoves` lines. Two of my nine predictions FAILED and are recorded as failures (book share 786 against my
0-200 band; driver-stopped searches 1,072 against my 400-900 band). REPORT_job1_run2.md.

## FINDINGS FILED (all in FINDINGS.md, all pushed)
S-F1 argv ignored (since independently confirmed as seat 10's 10-C1) | S-F2 empty `searchmoves` -> `0000` on a
board with 20 legal moves (now also confirmed by seat 20's S-C2) | S-F3 `ponderhit` on a non-ponder search is a
no-op | S-F4 a clock naming only the opponent's side sets NO limit | S-F5 button `Clear Hash` answers "invalid
value" when given a value | S-C1..S-C5 as above.

## state
All three area-2 jobs are DONE, cycle item 2(c) is DONE, five other-seat findings are checked, and every
broadcast warning has been acted on and audited. Reports: REPORT_job1.md, REPORT_job1_run2.md,
REPORT_job2.md, REPORT_job3.md, plus REPORT_job1_v1_WITHDRAWN.md which is kept on purpose.
## 22:12Z — GUI guidance pass (coordinator request)
GUI_GUIDANCE.md gives the one sentence a GUI author needs for S-F3, S-F4 and S-F5, each with the measurement
that decides it:
- S-F3: the engine is RIGHT to ignore `ponderhit` on a non-ponder search. Proven: `go ponder wtime 400 btime 400`
  + `ponderhit` ends by itself at 455 ms against a ~390 ms budget (job2/probe_ponderhit.py, out_ponderhit/),
  while `go infinite` + `ponderhit` runs on. So a GUI must send `stop` to cancel and only `ponderhit` to end a
  ponder. Rejected "honour the real clock" (no clock exists on a depth search) and "treat it as an error"
  (harmless command, some GUIs send it speculatively).
- S-F4: should keep never reading the opponent's clock (a huge `btime` DOES bound a White-to-move search — so it
  is not "ignoring a missing clock"), but when NEITHER clock belongs to the side to move it should print an
  `info string` and search a BOUNDED default instead of silently searching forever. Rejected "use the named
  clock" (spends the wrong player's time and hides the GUI bug) and "refuse" (leaves the GUI with no move).
  Evidence: finding_clock/partial_clock_options.txt, 8 rows.
- S-F5: ONE bug in ONE hand-written branch, not a class. This build has exactly one `type button` option and the
  word `button` appears in the whole source only where it is advertised (src/uci.cpp:247); there is no option-type
  dispatch, so nothing else can share the defect. finding_button/button_class.txt.

## 22:17Z — TODAY vs SHOULD added to GUI_GUIDANCE.md (coordinator request, final item)
A table of what the engine does TODAY per case, measured (today_state/today_state.txt, interactive driver):
S-F3 `ponderhit` on a non-ponder search -> silently ignored, search runs on, **0 info string lines**.
S-F4 `go` with only the opponent's clock -> silently unbounded, **0 info string lines**.
S-F5 button `Clear Hash` given a value -> refuses, and **DOES print** `info string invalid value for option
Clear Hash`. The asymmetry is the finding that matters for a GUI: the two dangerous cases are silent, so the
only defence is GUI-side — never send `go` without the side-to-move's clock, and never use `ponderhit` to
cancel. One probe in my first attempt collected output AFTER the setoption and wrongly showed S-F5 as silent;
corrected and re-measured before publishing.

COMPLETE. Nothing running, nothing pending.

Exact next command:
  cd /agent/repos/dwqww && git log --oneline -1

## 2026-11-16T22:18Z CONTINUE: 12 more hours, ends at 2026-11-17T10:18Z
Seat kept: 02 (from ~/swarm_seat.txt), branch for-fable-and-opus/swarm-02. No new seat taken.
Plan for the 12 hours, in the order the owner set:
1. read every FABLE_TO_swarm_N.md I have not read yet, lowest to highest (I have read 1, 2 and 3);
2. build the PC engine from FABLE_TO_swarm_5.md in a SEPARATE copy against 6b98f217 with
   -DFORGE_MATE_ALPHA_GUARD=1, and check the bench numbers that file states;
3. re-run my own findings on the PC build under PC20 and say in each finding line which build and settings;
4. then THE CYCLE: area-2 jobs on both builds, checks of other seats, STATUS every 25 minutes or less.
Final block "## <time> FINAL" with every find of mine, its state and the build it used, before 10:18Z.

## 2026-11-16T22:41Z — PC r15 build done and verified; my findings re-run on it
Read FABLE_TO_swarm_4.md and FABLE_TO_swarm_5.md in full (1, 2, 3 were already read).
PC r15 built in a SEPARATE copy (/agent/repos/pc) from 6b98f217: patch extracted from file 5, sha256
d6bd72c531f785f40421be1cc542743922a944fb0973d05831788440309c1a1a == file 5's stated prefix; patch -p1 with
0 fuzz / 0 offsets / no .rej; 11 files touched, CMakeLists untouched; -DFORGE_MATE_ALPHA_GUARD=1; BUILD_EXIT=0.
ALL EIGHT stated bench numbers reproduce exactly (none: 312866/862329/3024920/4865609; S14: 242796/656517;
PC20: 278024/587276). The PC build is USABLE. pc_build/README.md.
Threads 1 set explicitly on every run (seat 04's rule); every search cold in a fresh process; interactive driver.

RESULT of re-running my four findings on the PC build under PC20: NONE of them is repaired.
S-F2 `0000` on an empty searchmoves: still there. S-F3 ponderhit no-op: still there (and correct). S-F4
opponent-only clock searches forever: still there, silent. S-F5 Clear Hash with a value: still there.
NEW S-F6: `go btime wtime 50` — an eaten-keyword parse — DOES hang the base build (2000 ms) and is FIXED on
the PC build (2.4 ms); that is FORGE_FIX_GO_PARSE, and it is a DIFFERENT mechanism from S-F4, which the patch
does not touch. pc_rerun/RESULT.md.

Harness note: my first base-vs-PC comparison left OwnBook at its default on the base build and two rows came
back from the BOOK in ~1 ms, which reads exactly like "the defect is gone". Fixed to OwnBook false on both
builds plus an assertion that aborts on any `book move` line in those rows.

Next: area-2 job work on BOTH builds, starting with the S-F6 family (which other `go` keyword orders hang?) and
re-running job 1 and job 3 on the PC build under PC20.
