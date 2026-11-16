# STATUS — seat 07

## 2026-11-16T21:06:28Z (date -u)

seat 07
area 7 (READING THE CODE for faults) — job order: search, move picker+histories, position/move making, transposition table, UCI loop, time manager, evaluation, move generator
branch for-fable-and-opus/swarm-07
seed 701

Done: seat claimed, area/seed computed.
Next: build base worktree 6b98f217 and run the honesty check.

## 2026-11-16T21:09:33Z (date -u)

Honesty check PASSED on the release build (GCC 13.3.0, plain CMake Release, x86-64-v4):
bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, go perft 5 = 4865609.
Files: HONESTY.txt, job0/honesty.sh, job0/raw/*.
ASan+UBSan build made at build-asan (nm -C | grep -c __asan_ = 35, __ubsan_ = 15).

## 2026-11-16T21:34:00Z (date -u)

HARNESS CORRECTION (from seat 19's finding, relayed by the coordinator): my first
two harnesses (job1/limits_probe.sh, job1/searchstress.sh) pipelined `go` with a
following `isready`/`quit`. Seat 19 showed that closing stdin mid-search makes this
build answer a fabricated `bestmove ... 0 nodes`. Both of those runs are INVALID and
are not used for any result; the files stay for the record and are marked so.
Replaced by job1/uci_drive.py and job1/search_stress.py, which never pipeline: every
`go` is followed by reading stdout until `bestmove`, and the next command is only
sent after that.
Re-run with the correct harness (job1/raw_stress_asan, job1/stress_asan.log):
200/200 positions of set O at `go depth 10`, S14, ASan+UBSan: 0 hangs, 0 illegal
bestmoves, 0 zero-node answers, 3,740,105 nodes total, stderr file empty (0 lines).
Sanitizer proof for that run: build-asan has __asan_/__ubsan_ symbols, and the SAME
runner counts a planted heap over-read in a scratch copy (/tmp/faulty, faultprobe
command, 3 sanitizer lines) - job1/cases_planted.txt, job1/raw_planted/.
Also: 47 UCI edge cases driven correctly (job1/raw_drive, job1/drive.log): no hang,
no sanitizer line; two FEN-level refusals recorded (`invalid FEN`) as about-input.

Now: closing the `bestmove 0000` / searchmoves question properly (debug STL test,
three searchmoves cases, text patch, honesty pins unchanged).

Next command:
`cd /agent/repos/base/forge-combo29 && cmake -S . -B build-dbg -DCMAKE_BUILD_TYPE=RelWithDebInfo -DCMAKE_CXX_COMPILER=g++-13 -DCMAKE_CXX_FLAGS="-D_GLIBCXX_ASSERTIONS -fsanitize=address,undefined -fno-omit-frame-pointer" -DCMAKE_EXE_LINKER_FLAGS="-fsanitize=address,undefined" && cmake --build build-dbg -j4`
## 2026-11-16T21:41:14Z
job2 done: 2640 refuted (detector + reachability controls), searchmoves cases measured, patch applies --fuzz=0, honesty pins identical, bestmoves identical.
### git status --short
 M STATUS.md
 D job2/detector_control
?? REPORT_job2.md
?? job2/compare_searchmoves.py
?? job2/honesty.sh
?? job2/raw_patched/
?? job2/raw_patched_honesty/
?? job2/searchmoves_empty_root.patch.txt
### ls job2
cases_searchmoves.txt
compare_searchmoves.py
detector_control.cpp
honesty.sh
raw_dbg
raw_patched
raw_patched_honesty
raw_reach
searchmoves_empty_root.patch.txt
stamps.txt
uci_drive.py
Next: job 3 of area 7 (position and move making). Next command: cd /agent/repos/base/forge-combo29 && wc -l src/board.cpp

## 2026-11-16T21:41:57Z
job3 done: checked 17-S-F2 -> REFUTED (07-C1). Symptom of 17-S-F1 confirmed; cause is the fabricated depth line (07-F1), not an empty front().
Both instruments carry live positive controls. Next: area 7 job 1 again is done, so job 3 = position/move-making read (src/board.cpp).
### git status --short
 M FINDINGS.md
 M STATUS.md
?? REPORT_job3.md
?? job2/__pycache__/
?? job3/
### ls job3
cases_17sf2.txt
check_17SF2.py
raw_dbg
raw_reach
raw_reach2
reach_2640.py
stamps.txt

## 2026-11-16T21:46:56Z
job5 done: settled seat01-vs-07 on search.cpp:2640. Both-branch marker build: seat 01's cases fire MARK-2253 (root_candidates=0, restricted=1) and never MARK-2640; positive control (go nodes 5) fires MARK-2640 root_candidates=20. 07-C2 in FINDINGS.
### git status --short
 M FINDINGS.md
 M STATUS.md
?? REPORT_job5.md
?? job4/
?? job5/
### ls job5
cases_s01.txt
raw
stamps.txt

## 2026-11-16T21:48:05Z
job4+job6 done (board.cpp read): castling-after-capture, ep-without-capturer, king-across-null all clean, each probe failable via a planted fault; perft equal to python-chess on 14 special positions; key_after correct on 1,520,927 cases with a planted fault caught 608 times. No new FINDINGS: board.cpp is clean in the three areas asked about.
### git status --short
 M STATUS.md
 M job4/stamps.txt
?? REPORT_job6.md
?? job6/
### ls job4 job6
perft_board.py
raw
stamps.txt
---
board_probes.cpp
board_probes_run.txt
epkey_probe.cpp
epkey_run.txt
key_after_run.txt
key_after_test.cpp
stamps.txt

## 2026-11-16T21:49:49Z
job7 done: is_repetition() agrees with python-chess threefold on 62 plies (failable: planted twofold-as-draw gives 17 disagreements). SEE cross-check abandoned - my oracle was wrong twice, python-chess settled both cases the engine's way; see job7/SEE_NOTES.txt.
### git status --short
 M STATUS.md
?? REPORT_job7.md
?? job7/
### ls job7
check_repetition.py
repetition_probe.cpp
see_crosscheck.cpp
SEE_NOTES.txt
stamps.txt

## 2026-11-16T21:50:14Z
job8 done: has_legal_move() correct on 9,118 positions (python-chess + engine self-consistency), with a planted-fault control producing 26 disagreements. No finding: clean.
### git status --short
 M STATUS.md
?? REPORT_job8.md
?? job8/
### ls job8
check_legal_move.py
legal_move_probe.cpp
legal_move_run_control.txt
legal_move_run.txt
stamps.txt

## 2026-11-16T21:52:04Z
job9 done: S14 sum for O at depth 12 reproduces the brief exactly (9,500,069; 41,311/24,872/28,574). 07-C3 in FINDINGS. Also audited every harness of mine against seat 10's warm-search trap: none used Clear Hash as a baseline, none compared node counts across warm searches.
### git status --short
 M FINDINGS.md
 M STATUS.md
?? REPORT_job9.md
?? job9/
### ls job9
job9:
raw
run_d12.log
s14_sums.py
stamps.txt

job9/raw:
sum_d12.json

## 2026-11-16T21:55:06Z
job9+job10 done: G depth-12 S14 sum = 18,466,239 EXACT (07-C4); O d12 = 9,500,069 exact (07-C3). go/stop GUI cycle clean over 40 plies (07-C5) -- but my first version of that test was blind and passed the planted-fault control; fixed, control now fails as it must, both runs kept.
### git status --short
 M FINDINGS.md
 M STATUS.md
 M job9/stamps.txt
?? REPORT_job10.md
?? job10/
?? job9/raw_G/
?? job9/run_G_d12.log
### ls job9 job10
raw
raw_G
run_d12.log
run_G_d12.log
s14_sums.py
stamps.txt
---
go_stop_cycle.py
raw
raw_control
stamps.txt

## 2026-11-16T21:56:09Z
job9 (cont) + job11 done: O depth-14 S14 sum = 21,812,100 EXACT (07-C6) -- three of four published sums now reproduced. Clock: 9 controls, 0 overruns, 0 illegal moves (07-C7). IMPORTANT TRAP for other seats: the built-in book answers clock searches with NO info depth line; my first clock run measured book moves and looked clean -- fixed by OwnBook false + requiring a parsed node count.
### git status --short
 M FINDINGS.md
 M STATUS.md
 M job9/stamps.txt
?? REPORT_job11.md
?? job11/
?? job9/raw/sum_d14.json
?? job9/run_d14.log
### ls job11
job11:
clock_behaviour.py
raw
stamps.txt

job11/raw:
mtg_1.txt
mtg_2.txt
mtg_40.txt
sudden_10000.txt
sudden_1000.txt
tiny_100.txt
tiny_10.txt
tiny_30.txt
zero_0.txt

## 2026-11-16T21:56:50Z
job12 done: eval() is exactly colour-symmetric (0/600). Convention verified from the engine: eval is side-to-move-relative (eval.cpp:509), so eval(P)==eval(mirror(P)). Two earlier versions of my test asserted the wrong relation and are documented as my errors.
### git status --short
 M STATUS.md
?? REPORT_job12.md
?? job12/
?? job9/raw_G/sum_d14.json
?? job9/run_G_d14.log
### ls job12
job12:
eval_symmetry.py
__pycache__
raw
stamps.txt

job12/raw:
differences.txt

## 2026-11-16T21:56:56Z

All four published S14 sums reproduced exactly from cold starts:
| figure | published | mine | finding |
|---|---|---|---|
| O depth 12 | 9,500,069 | 9,500,069 | 07-C3 |
| G depth 12 | 18,466,239 | 18,466,239 | 07-C4 |
| O depth 14 | 21,812,100 | 21,812,100 | 07-C6 |
| G depth 14 | 43,345,893 | 43,345,893 | 07-C8 |
First-three O d12: 41,311 / 24,872 / 28,574 — also exact.


## 2026-11-16T21:57:37Z
job13 done: inline legality shortcut (board.hpp:321) correct on 289,809 pseudo-legal moves vs make/unmake brute force (07-C10). Control trap: my first planted fault was in board.cpp and was BLIND because the shortcut is inline in board.hpp; planting in the header gives 494 mismatches. Third time tonight a planted-fault control caught a blind test of mine.
### git status --short
 M FINDINGS.md
 M STATUS.md
?? REPORT_job13.md
?? job13/
### ls job13
is_legal_probe.cpp
is_legal_run_control_header.txt
is_legal_run.txt
stamps.txt

## 2026-11-16T21:57:56Z
job14 done: gives_check() correct on 260,053 legal moves vs make+in_check brute force (07-C11); header-planted control gives 3,999 missed checks, so the zero is real.
### git status --short
 M FINDINGS.md
 M STATUS.md
?? REPORT_job14.md
?? job14/
### ls job14
gives_check_probe.cpp
gives_check_run_control.txt
gives_check_run.txt
stamps.txt

## 2026-11-16T21:59:19Z
job15 done: TT invariants 4/4 held (07-C12). Second blind-control kind caught: a header-planted fault needs search.cpp REBUILT, not just the test file -- linking the prebuilt .o silently defeated my first control.
NOTE: this probe covers the LOCKED path (FORGE_SPD_TT_NOTLS=0); the shipped build uses 1 and is unprobed.
### git status --short
 M FINDINGS.md
 M STATUS.md
?? REPORT_job15.md
?? job15/
### ls job15
stamps.txt
tt_probe.cpp
tt_run_control.txt
tt_run.txt

## 2026-11-16T22:01:28Z
job16 done: CORRECTION -- CMakeLists.txt:32 sets TT_NOTLS=1, so the shipped build is the UNLOCKED path and my job15 probe forced =0. build-notls and build-rel are the same binary. Shipped path pin-verified: 312866/862329/3024920/4865609 (07-C13).
### git status --short
 M FINDINGS.md
 M STATUS.md
?? REPORT_job16.md
?? job16/
### ls job16
honesty.sh
raw_notls
stamps.txt
tt_probe_owned.cpp

## 2026-11-16T22:04:49Z
job17 done: book moves legal over 60 plies (16 book answers), matching decode_move's legal_moves() scan (07-C14). FIRST CONTROL WAS INCONCLUSIVE (removing the scan still passed because decoded moves happened to be legal); the valid control reverses from/to and fails at ply 0. Labeled honestly in the report.
### git status --short
 M FINDINGS.md
 M STATUS.md
?? REPORT_job17.md
?? job17/
### ls job17
job17:
book_moves.py
raw
raw_control
run.txt
stamps.txt

job17/raw:
transcript.txt

job17/raw_control:
transcript.txt

## 2026-11-16T22:05:40Z
job18 done: SEE oracle rebuilt on python-chess and VALIDATED against 5 hand-settled cases before use (07-C15). It corrected 3 of my own expectations. Result: 150 positions at depth 1, 0 illegal, 0 losing captures chosen. Scope stated: exercises the engine's choice, not see_ge's return value, which UCI does not expose.
### git status --short
 M FINDINGS.md
 M STATUS.md
?? REPORT_job18.md
?? job18/
### ls job18
job18:
oracle_selftest.py
__pycache__
raw
run.txt
see_oracle.py
selftest.txt
stamps.txt

job18/raw:
differences.txt

## 2026-11-16T22:06:41Z
job19 done: all time-manager pure-function properties hold under UBSan (07-C16): 1000 monotonicity cases, 560 node-share cases with the documented 1500/1000/500 scale, 420 clock-plan cases 1<=soft<=hard<=available. THREE of my UBSan controls were void before one fired (-O2 deleted it; constant didn't overflow; guard unreachable) -- all recorded.
### git status --short
 M FINDINGS.md
 M STATUS.md
?? REPORT_job19.md
?? job19/
### ls job19
run.txt
stamps.txt
tm_probe.cpp
ub_control.txt

## 2026-11-16T22:08:34Z
job20 done: increment-heavy controls never lose on time (0/160 plies), but the plan spends up to 79.6% of the clock on one move at movestogo 40 with increment == clock (07-C17). Reported as a BEHAVIOURAL observation for Opus, not a fault: hard<=available holds and the increment refunds the time.
### git status --short
 M FINDINGS.md
 M STATUS.md
?? REPORT_job20.md
?? job20/
### ls job20 job20/raw
increment_stress.py
raw
stamps.txt
inc_eq_clock_mtg40.txt
inc_eq_clock_sudden.txt
inc_gt_clock.txt
inc_half_clock_mtg40.txt
inc_tiny_clock.txt

## 2026-11-16T22:08:48Z
re-verification: 07-F1 reproduces identically on a fresh build (info depth 4 ... score cp 0 nodes 0 -> bestmove 0000 for searchmoves naming no legal root; control e2e4 gives 438 nodes), and job2/searchmoves_empty_root.patch.txt still applies to clean 6b98f217 with --fuzz=0 (dry-run exit 0). 07-C18.

## 2026-11-16T22:11:14Z
job21 done: checked 27-S-F7 (nobody had) -> CONFIRMS on 82 options / 437 cases, 0 refused valid values, 0 unknown options (07-C19). Control: advertising a PhantomOption gives 6 UNKNOWN detections. Stated gap: the REFUSED-VALID half has no control.
### git status --short
 M FINDINGS.md
 M STATUS.md
?? REPORT_job21.md
?? job21/
### ls job21
job21:
check_27SF7.py
raw
raw_control
stamps.txt

job21/raw:
summary.txt

job21/raw_control:
summary.txt

## 2026-11-16T22:12:49Z
job21 follow-up: closed the REFUSED-VALID control gap I had flagged. A refuse-max build now gives 58 REFUSED-VALID detections (vs 6 UNKNOWN from the phantom build), so BOTH bug classes are proven detectable and the 437-case clean run is meaningful in both directions.

## 2026-11-16T22:13:03Z
job22 done: the boolean S14 option NonPawnCorrection does take effect (false 56,720 nodes cp30 -> true 33,066 cp29), which the four sums could not prove because booleans use a different setoption branch (07-C20). Bonus: 56,720 matches seat 10's independent cold figure exactly. Stated gap: the other 10 booleans in that same chain were not verified by effect.
### git status --short
 M FINDINGS.md
 M STATUS.md
?? REPORT_job22.md
?? job22/
### ls job22
job22:
compare_npc.py
raw
stamps.txt

job22/raw:
result.txt

## 2026-11-16T22:17:18Z
NEW REAL FINDING 07-F2: LmrSignedCorrection is dead code. correction_cp = correction/256 is bounded to +-32 (CorrectionLimit 8192), so delta = correction_cp/64 is ALWAYS 0 -- 0 of 507,935 (reduction, correction) pairs change anything, and node counts are identical with the option off and on at startpos d12/d16 and middlegame d14. Control: /8 instead of /64 changes 374,845 of 507,935 pairs. No patch: a repair changes the tree, so it would break the honesty pins and needs a strength test, not a text patch.
Also: NullThreatVerify is live (differs on middlegame d14), so its startpos null result was a coincidence.
### ls job23 job24
bool_options.py
__pycache__
raw
run.log
stamps.txt
---
lmrdead.cpp
run.txt
stamps.txt

## 2026-11-16T22:18:05Z
job25 done -- 07-F2 WITHDRAWN. The coordinator's tuning-record search came back the other way: forge-combo29/REPORT_r3_03.md is a full report on LmrSignedCorrection, and it refutes me. Quoted at line 87: 'A one-ply step needs 64 centipawns, and each correction table caps at 32, so the step happens only when the pawn and material corrections are both saturated on the same side.' Line 78 records the divisor being deliberately changed /8 -> /64. The repo also ships tests_r3_03/lmr_signed_correction_test.cpp with {3, 64, 2, '64cp better subtracts one ply'}.
MY ERROR: corrected_eval SUMS three correction tables (pawn + material + optional non-pawn), so the bound is +-96 cp (defaults +-64), not the +-32 of a single table. Re-derived in job25/correction_boundary.cpp: 2013 of 5983 reachable pairs change the reduction, so the option is live, just rarely.
ANSWER for the owner: neither delete nor repair. The divisor was already repaired once and documented; leave the option alone and read REPORT_r3_03.md before touching it.
End of window.

## 2026-11-16T22:20:00Z (date -u) — END OF WINDOW

Stopping before 22:30 as instructed.

**Net result: ONE real engine defect, TWO withdrawn claims of my own, NINETEEN checks.**

- **07-F1** (real): `searchmoves` naming no legal root move, on a board that HAS legal moves, emits a
  fabricated `info depth N ... score cp 0 nodes 0` line before `bestmove 0000`. Patch
  `job2/searchmoves_empty_root.patch.txt` reuses the engine's own detection (search.cpp:2210), applies
  with `patch -p1 --fuzz=0`, keeps all four honesty pins and every bestmove identical (07-C18
  re-verified at the end of the window).
- **07-R1** (withdrawn): I claimed search.cpp:2640 read `front()` of an empty list. It cannot; 2253
  returns first. Proven with a two-branch marker build, and that same build **settled a three-seat
  contradiction** (07-C2, seat 01 wrong, seat 17's cause wrong, symptoms real).
- **07-R2** (withdrawn): I claimed `LmrSignedCorrection` is dead code. The repo's own
  `REPORT_r3_03.md` documents it fully and my bound forgot that `corrected_eval` sums three tables.
- Nineteen checks, most clean, each with a planted-fault control. **Five of my controls were
  initially blind** (go/stop cycle, eval symmetry, SEE oracle, option surface, UBSan overflow) — every
  one was caught by the control, and every correction is in its report.

**All four published S14 sums reproduce exactly from cold starts** (07-C3/C4/C6/C8): 9,500,069 /
18,466,239 / 21,812,100 / 43,345,893.

**Traps passed to other seats:** the book answers clock searches with no `info depth` line (07-C7);
`eval` is side-to-move-relative so symmetry checks must compare `eval(P) == eval(mirror(P))` (07-C9);
a planted fault must go in the file the code lives in — `board.hpp` for legality (07-C10) — and a
header fault needs every dependent translation unit recompiled (07-C12).

### final `git status --short`
(clean; a base-tree tracked file `run.log` that I had accidentally overwritten was restored to its
exact base content, and `git diff 6b98f217..HEAD` outside my folder is empty)

### final `ls` of my folder
`FINDINGS.md HONESTY.txt REPORT_job*.md SEAT.txt STATUS.md stamps.txt job0..job25`

Next command if resumed: `cd /agent/repos/dwqww && git log --oneline -1` then read FINDINGS.md.

## 2026-11-16T22:19:02Z CONTINUE: 12 more hours, ends at 2026-11-17T10:19:02Z

Seat kept: 07 (from ~/swarm_seat.txt), branch for-fable-and-opus/swarm-07, folder forge-combo29/swarm/07.
Next: read every unread forge-combo29/soak_all/FABLE_TO_swarm_N.md from lowest N up, per the owner's TEXT 2 starting with file 5 (the PC engine source), build it as it says, check its bench numbers, then carry on with area 7 against BOTH builds under settings PC20.

## 2026-11-16T22:20:49Z
PC r15 BUILD DONE (07-C21). Patch sha256 verified (d6bd72c5...), applied in a separate worktree /agent/repos/pcbase, 11 files, 0 rejects, built with -DFORGE_MATE_ALPHA_GUARD=1. ALL EIGHT published numbers match: none-regime 312866/862329/3024920/4865609, S14 242796/656517, PC20 278024/587276. Threads 1, Hash 16, fresh process per line. No unknown-option line in any regime, so MateAlphaGuard exists.
THREADING AUDIT (swarm rule): every measurement I ever made used Threads 1. Only job1's two threads4_* edge cases sent Threads 4 and they recorded bestmoves only, no scores or node counts. Nothing of mine needs a provisional label.
Read FABLE_TO_swarm 1 (earlier), 2, 3, 4, 5 now. File 3 corrects file 1's castling claim; file 4 separates pin and sum regimes; file 5 is the PC source.
Next: re-run my own finds (07-F1 and the C-series checks) on the PC build under PC20.

## 2026-11-16T22:27:49Z
MAJOR: 07-C22 + 07-C23.
(a) The three reported symptoms are TWO paths, not one. 07-F1 and the no-match-with-node-budget case share a path (empty root_candidates -> early branch at search.cpp:2581 -> one fake 'score cp 0 nodes 0' line per depth; 64 of them). The 19-F12 abort case is a DIFFERENT path: 0 depth lines, and a legal move from root_candidates.front() at search.cpp:3017. Discriminating proof: with quit at t=0 the answer is always the FIRST move of its own restriction (a2a3 / d2d4 / h2h4 / g2g3 for go depth 12 / searchmoves d2d4 / h2h4 / h2h4 g2g3).
(b) 07-F1 SURVIVES on the PC build under PC20 -- not repaired. I wrote a separate PC-tree patch (the base one's hunk 3 conflicts with FORGE_FIX_ROOT_DRAWN): applies --fuzz=0, all 8 PC pins unchanged, empty-root cases 64 zero-node lines -> 0, bestmove 0000 still returned, all controls and the 19-F12 path identical.
All figures Threads 1, Hash 16, PC20, fresh process per case.

## 2026-11-16T22:29:20Z
07-C24: the 0000 design question answered and written into the patch header. Measured on startpos/20 legal moves, go depth 6 searchmoves e2e5, Threads 1: (A) unpatched = 0000 + 6 fake 'score cp 0 nodes 0' lines; (B) my patch = 0000 + honest info string, 0 score lines; (C) full-root search = d2d4, 6 real lines, 1703 nodes; (D) no answer rejected. RECOMMENDATION: ship B -- a fabricated score is a defect, an honest 0000 is not, and B changes nothing a GUI does today. If a playable move is wanted it is a separate decision that must say so in an info line.
07-C25: the one-candidate boundary is correct. A searchmoves restriction leaving exactly ONE LEGAL candidate searches normally on both builds (base 438 nodes, PC20 344; single real capture 138 / 175), so the branch keys on emptiness, not on size. My first version of that test used a Black-to-move position where f3e5 was illegal -- python-chess caught it and the case was corrected.
PC20 baseline established: O depth 12 = 8,315,168 (base S14 was 9,500,069 -- different, as the PC build changes search; file 5 publishes only bench numbers for PC20, not sums).

## 2026-11-16T22:31:41Z
07-C26: PC20 BASELINE recorded in PC20_BASELINE.md -- set O depth 12 under PC20, Threads 1, Hash 16, one fresh process per position = SUM 8,315,168 over 200 positions, with per-position sha256 e6beb5f9... and nodes-only 2337b0d1..., the exact command, all 22 option lines in order, the five process rules, and instructions for a later seat to prove its harness against it. REPRODUCIBILITY PROVEN not assumed: a second independent run over the first 40 positions matched row by row, 0 mismatches, partial sum 1,548,134.
07-C27: all seven board-level checks still hold on the PC TREE (compiled against its own src/include): key_after 1,520,927/0 mismatches; castling+ep+king probes ALL PASSED; legality 289,809/0; gives_check 260,053/0; has_legal_move 9,118/0; repetition 62/0; perft on 14 special positions all EQUAL incl. every divide line. The PC patch did not regress board correctness.
Recorded in FINDINGS: my false boundary warning came from an illegal move of mine (Black to move), caught with python-chess -- same class as the five blind controls tonight.

## 2026-11-16T22:38:10Z
07-C28 -- THE BROADNESS ANSWER the owner needed. Per-position table, set O depth 12, both runs Threads 1/Hash 16/fresh process per position, and the base leg re-run reproduced the published 9,500,069 exactly. PC20 8,315,168 vs S14 9,500,069 = -1,184,901. NODE COUNT CHANGED IN 200 OF 200 POSITIONS (74 up, 126 down, median delta -4,888); BESTMOVE CHANGED IN 60 OF 200 (30%); SCORE CHANGED IN 195 OF 200 (97.5%). Nothing is untouched -> the PC's search changes are BROAD, not narrow. Full 200-row table in job34/raw/sum_delta.txt.
Caveat honoured: the runs differ in build AND settings, so each delta is a property of the pair (base+S14 vs PC+PC20), not of the PC patch alone. Separating them needs base+PC20 and PC+S14 sums, which I flagged rather than faked.
07-C29: the single unexplained base-vs-PC difference (promotion race, 8/P6k/8/8/8/8/8/K7 w d10) is FORGE_FIX_BARE_KING_LMR_CAP alone -- isolated by rebuilding with each switch singly. Both other switches give base's answer exactly; all three off matches base exactly. And the PC's a7a8q is the BETTER move (promotes immediately vs shuffling), so this is the bare-king work helping in at least one position.
Kept verbatim as instructed: 'a warning from a harness that has not validated its own input is not a finding.'

## 2026-11-16T22:42:27Z
07-C30 -- CAVEAT CLOSED, and the answer is an INTERACTION not a split. Four legs, set O depth 12, Threads 1/Hash 16, fresh process per position: base+S14 = 9,500,069; base+PC20 = 9,500,069; PC+S14 = 9,500,069; PC+PC20 = 8,315,168. The base build answers 'unknown option' for all five PC-only options (verified one by one), so base+PC20 is really S14. Consequence: the PC patch's fixes move ZERO nodes on this set at depth 12, and 100% of the -1,184,901 needs patch AND settings together. Saying 'patch X, settings Y' would be arithmetically wrong.
07-C31 -- WHICH OPTION DOES THE WORK (40 positions, depth 12, PC build): CorrHistV2 +208,947 (+12.4%) COSTS nodes; TtPruneV2 -163,541 (-9.7%) SAVES them; CuckooRep +72,364 (+4.3%); HistRework3 +15,655; HistRework2 +517; MateAlphaGuard and OwnBookOff exactly 0. All six net -138,940 (-8.2%). So PC20's saving is two options pulling opposite ways and only just netting negative -- not a broad win. CorrHistV2's cost may buy strength but that is a games question I did not measure. MateAlphaGuard's zero is EXPECTED: gated on is_mate_score(alpha), which these positions rarely reach.
Read FABLE_TO_swarm_6: draws by repetition/50-move scored 0 are NOT defects (owner's match program ends the game); multi-thread variation is NOT a defect; the PC's real path is softnodes 2000 / nodes 20000-50000-250000 / clock 6s+0.06 on game positions. My per-position work is the right shape for that path.

## 2026-11-16T22:50:06Z
07-C32 -- PER-OPTION TABLE AT ALL 200 POSITIONS, and it CORRECTS my 40-position one. Baseline S14 9,500,069 (same as the four legs, so comparable). TtPruneV2 -1,002,190 (-10.5%) = 85% of PC20's whole -1,184,901; CorrHistV2 +251,935 (+2.7%); HistRework3 -128,374; HistRework2 -57,443; CuckooRep -53,470; MateAlphaGuard 0; OwnBook false 0; all six -1,184,901 (-12.5%). CORRECTION: on 40 positions three of six options had the OPPOSITE sign (CuckooRep was +4.3%, now -0.6%), so my earlier 'two options cancelling' reading is withdrawn. Actionable line: TtPruneV2 is the only option big enough to matter on its own; CorrHistV2 costs 2.7% and needs a games argument.
07-C33 -- 100-POSITION DIFFERENTIAL: 0 of 100 positions differ at depth 12 under identical settings (Threads 1, Hash 16, OwnBook false), and the zero is PROVEN not blind: the same script on the known promotion-race position reports 1/1 differ (a1a2/1067/21,093 vs a7a8q/1124/36,405). This matches PC+S14 == base+S14 exactly, measured two independent ways. Explanation: the four FORGE_FIX switches target SPECIAL STATES (drawn root, go-parse, bare-king, hard-limit) that set O's ordinary middlegame positions never reach. So the PC patch's value is in those states, not in tree shape -- and the lever for ordinary play is the options, per 07-C32 almost entirely TtPruneV2.
Both items the coordinator asked for are done; not re-running anything else.

## 2026-11-16T22:55:09Z
07-C34 + 07-C35/07-F3 -- THE TWO-SAMPLE ANSWER the owner needed. Built both samples from real set-G material with python-chess classifying (job37/build_samples.py, tags in job37/raw/samples.json). Same settings on both builds: Threads 1, Hash 16, OwnBook false, depth 12, fresh process per run.
TARGETED 100 (30 bare-king stripped from G, 20 fifty-move-counter-100, 50 late endgames): 50 OF 100 DIFFER. Attribution: 30 = FORGE_FIX_BARE_KING_LMR_CAP (every bare-king case), 19 = FORGE_FIX_ROOT_DRAWN (every fifty-move case), 1 combination. The 50 late endgames did NOT differ at all -- these are not general endgame fixes, they are fixes for the named states.
ORDINARY 100 (G middlegames, material >= 26): 0 OF 100 DIFFER. So the patch is PRECISELY TARGETED, not a broad rewrite -- it changes exactly its own special states and leaves ordinary trees bit-identical. Now measured three independent ways (this, 07-C33's 0/100 on set O, and 07-C30's PC+S14 == base+S14).
07-F3, THE HEADLINE: the BASE tree is demonstrably WRONG on a fifty-move root where a pawn move can reset the counter. '8/6qk/8/8/8/1p4p1/4K3/8 b - - 100 1': base answers b3b2 with cp 0 and ZERO nodes (never searched, 12 fake depth lines); PC answers b3b2 with MATE 6 and 15,981 nodes. Black has Q + pawns b3/g3 vs a lone king and can reset the counter with a pawn move, so it is a win, not a draw. I first read this the OPPOSITE way -- file 6's 2N-1 <= 100-counter inequality says 11 <= 0, which would make the mate impossible -- until I checked that black has pawn moves. Recorded because the wrong reading would have been a false accusation against the PC build.
HONEST LIMITATION: no third-repetition roots could be built from G. I searched the first 60 G positions for a returning move pair: 0 of 60. G middlegames have pieces committed to progress. So all ROOT_DRAWN evidence here is fifty-move, not repetition.

## 2026-11-16T22:58:04Z
07-F4 -- THE FIFTY-MOVE RATE, and my own overclaim withdrawn. All 20/20 of the fifty-move-counter-100 positions have a counter-RESETTING move (pawn move or capture, decided by python-chess), so none is a genuine draw and base answers cp 0 with 0 nodes on every one. Referee = same board with counter 0: DECISIVE on 6 of 20, inconclusive at depth 12 on 10, noise band on 4. Of the 6 decisive: 1 is a win thrown away (cp 2950, the mate-6 case), 5 are LOSSES MASKED (cp -1601, -942, -477, -1039, -963).
  MY FIRST VERSION SAID '19 of 20 base errors (95%)' AND THAT WAS WRONG -- it counted cp -1601 and cp -6 alike as 'a win exists'. Withdrawn. Honest rate: decisive base error 6/20 (30%), thrown-away win 1/20. So ROOT_DRAWN's worth on this sample is ONE game-losing outcome in twenty, plus five cost-free corrected draws.
07-C36 -- BARE-KING REGRESSION SCAN: none found in 30. 14 neutral, 5 PC-better, 4 below margin, and 7 where PC's score is more negative by >=100cp. All 7 are positions where the side to move is being mated or beaten, and in EVERY ONE the PC score is closer to a depth-18 reference than base's (e.g. base -1735 vs PC -2112 where d18 says mate -6). More negative = more accurate there; base was under-estimating how lost it was. The depth-18 reference is what turned 7 would-be false accusations into 'no regression'.
07-C37 -- the mate-10-vs-mate-8 shape another seat reported does NOT appear in my 30: base reports no mate at all on these, so there is no case of base finding a shorter mate than the PC. That is a negative result about MY sample, not a refutation of their position -- their case likely needs a position where base's own search reaches the mate.
Caveat stated in the report: these rates are 'at depth 12 against a depth-18 reference', not ground truth; the 10 inconclusive fifty-move positions could move at greater depth.
Repetition sample left alone as instructed.

## 2026-11-16T23:06:35Z
07-C38 -- THE RATE IS NOW TIGHTENED, AND IT WENT DOWN, NOT UP: decisive base error **5 of 20 (25%)**, thrown-away win **1 of 20**. Reference re-run at depth 18 for all twenty and at depths 12/16/20/24 for the ten that matter, base build, Threads 1, Hash 16, OwnBook false, thresholds (+-300cp or any mate) fixed in the script BEFORE the run.
  NONE of the 14 inconclusive-at-12 became decisive at depth 18. The decisive count fell 6 -> 5 because position #7 read cp -477 at depth 12 and -84/-70/-52 at depths 16/20/24: a DEPTH-12 ARTEFACT, not a base error. Reporting only the depth-12 number would have overstated the case.
  The genuine cases only strengthened with depth: #0 cp -1601 -> mate -16 -> mate -9; #10 cp 2950 -> mate 4 and STABLE at 16/20/24. At depth 24 the decisive five are #0/#4/#10/#11/#13, of which #10 is the only thrown-away win and four are losses masked.
  Rate lineage: '19 of 20 (95%)' WITHDRAWN -> 6 of 20 (depth 12, 07-F4) -> **5 of 20 (depth 18-24, current)**. Worth of ROOT_DRAWN on this sample: one game-losing outcome in twenty, plus four cost-free corrected draws. Narrower than either earlier figure; that is the honest number.
Reproduction: the convergence sweep was run twice with identical results (job39/conv_reference.txt). Repetition sample still left alone as instructed.

## 2026-11-16T23:14:46Z FINAL

Full record in **FINAL.md** (this folder): every find with its state, build and settings; every C-series check; the withdrawn claims; and the three things I would put in front of the owner.

**State of my finds:**
- **07-F1** — `searchmoves` naming no legal root move on a board that HAS legal moves prints a fabricated `score cp 0 nodes 0` line per depth (64 of them) before `bestmove 0000`. **CONFIRMED by seat 10 (10-C15)**, independently observed by seat 17 as S-F1/S-F8. **Still present on PC r15.** PC-tree patch ready, every pin unchanged (07-C23). Builds base + PC r15; settings none/S14/PC20; Threads 1. **OPEN on the PC** in the sense that the patch is not applied there.
- **07-F3** — base declares a fifty-move root a draw without searching (`cp 0`, 0 nodes) while a mate exists; PC gets it right (`mate 6`). **OPEN** (no independent confirmation). base + PC r15, none, Threads 1.
- **07-F4** — base declares all 20 fifty-move sample roots drawn; reference shows 5 decisive (4 losses masked, 1 win thrown away). **OPEN.** Rate **SETTLED at depth 30** (07-C39): 0 of 6 changed category. base, none, Threads 1.
- **07-R1 WITHDRAWN** (2640 is not UB; the marker build also settled 01-vs-07, 07-C2). **07-R2 WITHDRAWN** (LmrSignedCorrection is not dead code — REPORT_r3_03.md documents it; bound is ±96 cp). Not to be re-opened.
- Two intermediate numbers of mine also withdrawn: the '95%' fifty-move rate, and 'PC20 is two options cancelling'.

**Best results for the owner:** (1) 07-F1 is the one PC-live defect, confirmed elsewhere, with a free patch; (2) **TtPruneV2 carries 85% of PC20's node effect** (07-C32, 200 positions); (3) **ROOT_DRAWN buys 1 game-losing outcome in 20** (settled at depth 30).

**Branch tip at FINAL:** 4693d6ece
**Files:** FINDINGS.md (46 rows), FINAL.md, STATUS.md, HONESTY.txt, PC20_BASELINE.md, 25 REPORT_job*.md, job0..job40, plus 2 text patches (job2 base-tree, job29 PC-tree).
**No engine source was committed; `git diff 6b98f217..HEAD` outside my folder is empty.**

## 2026-11-16T23:21:08Z
07-C40 -- SETTLED position 155 (seat 03 vs seat 02). PC r15 under PC20, Threads 1, Hash 16, depth 20, python-chess replaying the engine's own PV for each of white's four legal moves. White is a BARE KING vs Rb+B+N, so all four moves lose; the question is only which death is slowest.
  c6d6 mate -8 -> PV mates in 16 plies;  c6d7 mate -8 -> 16;  c6c5 mate -8 -> 16;  c6c7 mate -11 -> 22.
  The engine's free choice is c6c7, the WORST by 6 plies. So seat 03's SYMPTOM is real. But their explanation is imprecise: ALL FOUR lose, so 'scored as a forced loss' isn't the defect -- choosing the slowest loss is. And seat 02's defence is wrong on the merits: verifying that c6c7 really mates does not make it good when c6d6 mates 6 plies sooner. Both seats had a true fact and drew the wrong conclusion from it.
  Convention note: for scores against the side to move, plies-to-mate measured 2|N| exactly on all four (not 2N-1); systematic, so a convention difference, and the relative comparison is unaffected.
AUDIT METHOD (added to FINAL.md as the coordinator asked): my STATUS corruption was real and caught mechanically (line count + tail, rebuild from known-good prefix, verify no stray markers, repair as its own commit). But the same alarm is easy to raise falsely -- in a SHALLOW CLONE, 'git show' on a seat's first commit prints the whole tree as added, reporting tens of thousands of files that are not that seat's work. The correct audit is: git diff 6b98f217 <tip> -- . ':(exclude)forge-combo29/swarm/NN' -- which prints nothing for a clean seat. I ran it on my own branch: empty.

## 2026-11-16T23:26:43Z
07-C41 -- CONFIRMED seat 16's S-F4 (search is not exactly colour-symmetric) and EXTENDED it to the PC build under PC20, the owner's path. PC r15/PC20, Threads 1, Hash 16, depth 10, 120 G positions.
  Exact score symmetry 7/120 (5.8%) vs their 5.4%; bestmove mirrors 83/120 (69.2%) vs their 71.4%. Two independent samples on DIFFERENT builds agree within half a percentage point -- so the near-symmetry belongs to the search, not to one build.
  What their summary did not say, and I measured: the disagreement is mostly SMALL -- median gap 15 cp, 103/120 within 50 cp, and 18 pairs differ in bestmove while agreeing within 10 cp (pure tie ordering). The biggest gaps COLLAPSE with depth (289cp -> gap 1 at d18; 164cp -> gap 7 at d18), which is direct support for their 'order/depth dependence' attribution rather than a colour bias.
  SIXTH self-caught error of the run: my first version asserted the mirror score should be the NEGATION and reported 4/120. Board.mirror() swaps colours AND side to move while these scores are side-to-move relative, so the invariant is EQUALITY. The tell was same-sign pairs (orig -304 -> mirror -301). That is precisely the false-alarm class seat 16's own C5 documented -- I walked into a trap another seat had already written down.
  Housekeeping: the job42 report was briefly written inside job42/ instead of the seat root; moved to REPORT_job42.md and the __pycache__ removed.

## 2026-11-16T23:27:12Z
Added to FINAL.md as a standing rule: **for a side-to-move-relative score under a colour mirror the invariant is EQUALITY, not negation.** Board.mirror() swaps colours AND the side to move; eval and search scores are side-to-move relative (eval.cpp:509), so a +255 White advantage reads +255 for Black in the mirror. THE TELL: pairs called 'asymmetric' that have the SAME SIGN (orig cp -304 vs mirror cp -301) mean the checker is using negation. My wrong version reported 4/120; the correct one 7/120, and 25 of the first 40 'failures' were carrying the correct mirrored move. Written up with the note that seat 16 had already documented this trap in its C5 -- the strongest argument for reading other seats' checks before writing one.

## 2026-11-16T23:27:33Z
CORRECTION TO MY OWN 07-C41 (not a new claim): I wrote that I was 'extending' seat 16's symmetry finding to the PC build. **Seat 16's own S-F14 had already done exactly that** -- PC r15 under PC20, all 353 G positions (120/353 = 34% move-mismatch), and its S-F15 had already attributed the extra asymmetry to TtPruneV2. I did not read their later rows before writing mine, so my 'extension' duplicated their work.
  What still stands: an INDEPENDENT CONFIRMATION at depth 10 on a different 120-position subset -- 5.8% exact score symmetry vs their 5.4%, 69.2% mirrored bestmoves vs their 71.4%, and 30.8% move-mismatch consistent with their 34%. Two seats, same build, different subsets: a reproducibility check.
  What is genuinely mine to add: the disagreement is mostly small (median gap 15 cp, 103/120 within 50 cp) and the largest gaps COLLAPSE with depth (289 cp -> 1 cp at d18; 164 cp -> 7 cp), which supports their order/depth attribution.
Both FINDINGS 07-C41 and REPORT_job42.md now say this. The lesson is the same one as the negation error: I should read what other seats already established before claiming an extension of it.

## 2026-11-16T23:28:09Z
Put the mirror-invariant rule where other seats will actually see it: FINDINGS.md head, not only FINAL.md. It now states that a side-to-move-relative score under a colour mirror must be EQUAL, with the tell spelled out -- a negation-based checker reports FEWER symmetries and its 'failures' carry the CORRECT mirrored move (mine said 4/120 instead of 7/120, and 25 of the first 40 failures had the right mirrored move). Paired with the standing line 'a warning from a harness that has not validated its own input is not a finding.'
Also fixed stale bookkeeping in that header: it still said 'nineteen checks' when there are 41, and a leftover paragraph repeated the blind-control story after the new block.

## 2026-11-16T23:31:35Z
07-C42 -- CHECKED seat 10's 10-F53/10-F54 on a DISJOINT sample (the LAST 100 of G; they used the first 100). PC r15 PC20, Threads 1, Hash 16, fresh process per cell, determinism control passed.
  PARTLY CONFIRMS: budgets disagree on 24/100 (theirs 19/100), all-three-agree 76% (theirs 81%). The softnodes-20000 vs nodes-250000 figure matches closely -- 18/100 vs their 17/100 -- so the core claim 'the small self-play budget and the large match budget pick different moves about one time in six' HOLDS.
  PARTLY REFUTES 10-F54: they recommend nodes 50000 as the cheapest safe budget (92/100 agreement). I measure nodes50000 vs nodes250000 disagreeing on 22/100 vs their 8/100 -- so on my sample 50k is the LEAST stable of the three against 250k, not the most (20k agrees 82/100, 50k only 78/100). Of the 22, 12 are ties at the large budget and 10 are genuinely different.
  I am NOT claiming they measured wrongly -- different positions, and 24-vs-19 disagreements in 100 is within binomial noise. The conclusion is that 10-F54's recommendation is not safe to act on from 100 positions in either direction; a budget-safety claim needs a sample big enough to order the three rates, and two disjoint 100-position samples already disagree about the ordering.

## 2026-11-16T23:32:12Z
Added the general lesson to FINAL.md as a measurement rule, not just a finding detail: **100-position rates cannot order three budgets, or anything else that close.** Two DISJOINT 100-position samples flipped the ordering of the 20000 and 50000 budgets ten percentage points apart (seat 10: 50k agrees 92/100; mine: 78/100, with 20k better at 82/100). Neither is wrong -- 24-vs-19 in 100 is inside binomial noise -- and that IS the lesson: a rate of that size carries no ranking. Any budget-default choice needs a sample large enough that the ordering is stable under resampling.
  Noted the pattern across my own night: this is the fourth number that moved when the sample changed (fifty-move rate 95% -> 30% -> 25%; three of six PC20 option signs flipped between 40 and 200 positions). Small samples produce confident orderings that do not survive a different sample. Rule adopted: report a rate with its sample size and say whether it orders anything.

## 2026-11-16T23:35:19Z
07-C43 -- SETTLED the budget ordering properly, over ALL 353 positions, and the answer is that there is NO ordering. PC r15 PC20, Threads 1, Hash 16, fresh process per cell, the owner's three budgets.
  All three agree on 273/353 (77%), disagree on 80/353 (22.7%). Against nodes 250000: softnodes 20000 differs on 70, nodes 50000 on 69 -- one position apart.
  THE DECISIVE PART is the paired analysis, because these are the same positions and not independent samples: 59 of those disagreements are the SAME positions, with only 11 unique to 20000 and 10 unique to 50000. McNemar chi2 ~ 0.00, p ~ 1.00. The two budgets fail on the same trees.
  So 10-F54's '50000 is 2.1x safer' has NO support in either direction: seat 10's 100-sample said 50000 safer (8 vs 17), mine said worse (22 vs 18), and the full set says indistinguishable (69 vs 70, 59 shared). Both 100-sample orderings were noise, in OPPOSITE directions -- which is exactly why 07-C42 would not call them wrong.
  What the owner can act on: both small budgets differ from the match budget on about one position in five; choosing between 20000 and 50000 on node-count evidence is unsupported. If a single budget is needed the argument must come from time cost or a strength match.

## 2026-11-16T23:35:51Z
The damage-figure refusal now has its own heading in REPORT_job44.md, with the three specific reasons: (1) my re-scoring was generic, not seat 10's per-move discipline; (2) the largest gap I saw was 95,212 cp, which is a mate score collapsed through my cp conversion -- a distance artefact, not centipawns, and ranking by it would put artefacts at the top of a damage table; (3) a figure derived that way would look authoritative and be wrong. The report gives the disagreement rate and stops.
  Their 2-of-100 damage figure stands as the only disciplined measurement of it I have seen, and nothing in my 353-position run contradicts it. Anyone wanting damage must re-score per move.
  Message for the owner is unchanged and already relayed: both small budgets differ from the match budget about one position in five; the choice between them is unsupported by node counts; any single-budget argument has to come from time or games.

## 2026-11-16T23:39:07Z
07-C44 -- TESTED whether the two small budgets fail because both are simply too small. PC r15 PC20, Threads 1, Hash 16, 120 G positions, four budgets. Disagreements with nodes 250000: n20 = 22, n50 = 20, n100 = 8. So failing counts FALL sharply with budget, and 5 of the 8 n100 failures are shared with the small budgets -- consistent with 07-C43's account.
  MY SCRIPT'S VERDICT WAS WRONG AND I WITHDREW IT. It printed 'the intermediate budget fails on positions the small budgets do not -> different reasons', derived from MOVE INEQUALITY. Scoring the 3 disputed positions at 250000: #15 is two different losses (mate -12 vs cp -2196, incomparable units), #94 the 100k move is actually BETTER (348 vs 315), #118 a 65 cp preference. None is a regression.
  Same error class as my others: a verdict from a proxy (move inequality) that the real quantity (score) does not support. Caught only because I scored the disputed positions instead of trusting the script's summary line.
