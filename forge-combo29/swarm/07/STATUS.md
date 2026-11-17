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

## 2026-11-16T23:39:34Z
Added the 'incomparable units' rule in two places where it will be found:
  (a) REPORT_job44.md, its own subsection: a damage table's subtraction is only valid when both scores are centipawns. Position #15 of job45 has the 100k move at mate -12 and the 250k move at cp -2196; subtracting them invents ~9,800 cp of damage, and mate -12 is arguably the BETTER move since the loss is definite rather than a horizon guess. Any automated damage table must EXCLUDE pairs where either score is a mate score, or list them separately as 'both sides lost' -- otherwise mate scores dominate the top of the ranking, which is exactly what my own 95,212 cp artefact would have been.
  (b) FINDINGS.md header, beside the mirror rule and the 'warning from an unvalidated harness' line, so other seats read it before building one.
Intermediate-budget result kept as the account of WHY the small budgets fail together: 22 -> 20 -> 8 with 5 of 8 shared (07-C44), failures thinning as budget rises, no ordering between 20000 and 50000 (07-C43).

## 2026-11-16T23:40:21Z
07-C45 -- REFUTED seat 27's S-F12 ('the clock is ignored entirely when Black is to move'). Most serious unverified claim on the board and nobody had checked it. PC r15 PC20, Threads 1, Hash 16, fresh process per cell, wall-clock timed.
  On their FEN with BLACK to move: wtime 0/1/3/10 -> 39 nodes, 1 depth line, e7c8; 50 -> 918 nodes f1g1; 200 -> 11,488; 1000 -> 53,919 depth 18; 3000 -> 178,324 depth 22, 90 ms. The tree grows four orders of magnitude and the move changes. The clock is honoured on both sides, and on a second board of my own.
  Controls passed: movetime 5 = 1.3 ms/497 nodes vs movetime 3000 = 2,990 ms/4,306,146 nodes -- the harness sees a short search clearly. Every cell reproduced on a second run.
  LIKELY SOURCE OF THEIR FIGURE: their 'depth 20, 286,156 nodes, ~124 ms for every wtime' is EXACTLY the BASE build at wtime 3000 in my table (286,156 nodes, 20 lines, 120 ms, twice). So that number appears to come from the base build or from S14 rather than PC r15/PC20. I could not reproduce 'clock ignored' on either build -- the base build scales too (39 -> 286,156).

## 2026-11-16T23:41:16Z
07-C45 updated: seat 27's clock claim now has THREE independent refutations, and they agree cell-for-cell rather than just in verdict. Cross-seat table on the PC build, Black to move, on seat 27's own FEN:
  wtime 0/1/3/10 -> 39 nodes in all three seats; wtime 200 -> 11,488 in all three; wtime 3000 -> 178,324 in all three.
  Seat 07 and seat 30 agree on EVERY cell; seat 25 matches 6 of 8 (differs at wtime 50 and 1000, likely different build/regime).
  Seat 25 also measured the BASE tree and found no asymmetry, which removes the 'different build explains it' escape; seat 30 turned the same ladder into a positive control (30-F51: monotone in wtime on both builds and both colours, 12 positions x 4 clocks x 2 builds).
  The one real fact behind their claim, which all three of us had to explain the same way: wtime 0 and wtime 10 give identical answers, and that is the documented time <= Move Overhead emergency branch (seat 08's 08-F5) -- expected behaviour, not 'the clock ignored'. Seat 27 generalised a real small-budget identity to 'every N', and that is what the three checks refute.

## 2026-11-16T23:42:38Z
07-C46 -- CONFIRMED seat 21's 21-F12, and it SHARPENS my 07-F1 rather than conflicting with it. PC r15 PC20 vs base, Threads 1, Hash 16, halfmove 100, positions verified legal with python-chess first:
  legal named move (searchmoves g8h8): base g8h8 with 0 nodes, PC g8h8 with 8 nodes -> REPAIRED on PC.
  no legal named move (searchmoves a1a2): BOTH builds answer 0000 + the info line + 0 nodes -> UNCHANGED, which is 07-F1.
  So searchmoves has two sub-cases at a drawn root: the PC repaired the legal-named one and left the empty-intersection one. 07-F1 is precisely the empty-intersection case and nothing wider -- anyone reading my earlier line as 'searchmoves is broken on the PC build' would be over-reading it.
  TWO errors of mine on the way, both caught before reporting: (1) my first FEN was REFUSED ('side that moved left its king in check') so the engine kept STARTPOS and I measured the wrong board -- the tell was the plain case answering e2e4, impossible in a position with a lone black king on h8; (2) I then named g8f7, which is not legal there (only g8h8 is), caught with python-chess.

## 2026-11-16T23:43:11Z
Promoted the position-not-accepted tell to THE FIRST RULE in the FINDINGS header, ahead of the mirror and damage-table rules, because it caught me three separate times tonight and is the cheapest to apply:
  > **If the answer does not belong to the position, the position was not accepted.** The engine REFUSES an invalid FEN and keeps the PREVIOUS board, so a harness that does not read the setup output confidently measures the wrong position and reports it as a result. The tell is in the answer: a move that could not occur on the board you sent means the board you sent was rejected (mine gave e2e4 for a position with a lone black king on h8). Read every line between position and readyok, sanity-check the bestmove is legal on YOUR board, and validate every FEN with python-chess first -- which alone would have caught two of my three occurrences.
  Also added a fifth rule: a small-sample rate does not order anything (two disjoint 100-position samples flipped a ten-point budget ordering; 353 positions showed them indistinguishable).

## 2026-11-16T23:48:45Z
07-C47 -- checked seat 11's S-F91 (HARD_LIMIT_EMERGENCY's benefit is determinism) and found the METHOD cannot carry the conclusion. PC r15 PC20 + a variant with only that switch off, Threads 1, Hash 16, t=11..60.
  My sweep found 15/50 differing (theirs 5/50) -- but the decisive part is internal: repeating the differing values 5x each, 4 OF 15 SWEEP VALUES WERE NOT REPRODUCED BY THEIR OWN REPEATS ON THE SAME BINARY. At t=11/14/19/20 the sweep recorded (d2d4, 412) and all five repeats gave (d2d4, 971). Sweep-ON reproduced 11/15, sweep-OFF 13/15.
  So a node count at an 11-60 ms clock is NOT a stable measurement on this machine, on either build. Neither my 15/50 nor their 5/50 is a reproducible count, and 'ON was stable 601 nodes 5/5 while OFF was unstable' cannot be established by node counts at all.
  What IS stable: the bestmove, across every repeat (always d2d4 except t=11 OFF giving c2c3). So a determinism claim here must be made on the MOVE. That is a fair restatement of their thesis and I would support it on that basis.
  Same lesson as 07-C42/C43 in a different guise: a quantity that LOOKS exact is irreproducible when the stopping condition is a clock. I have hit it twice now.

## 2026-11-16T23:49:18Z
07-C48 -- RESTATED seat 11's S-F91 on the MOVE, the only quantity 07-C47 shows is reproducible, and in that form the thesis SURVIVES:
  ON: move changed across repeats at 0 of 15 differing clock values. OFF: same, 0 of 15. Both builds are deterministic on the move at these clocks.
  The ONLY move difference in the whole exercise is t=11: shipped build plays d2d4, switch-off build plays c2c3 -- the unsearched first-legal-move answer that switch exists to prevent.
  So the supported thesis is narrower and datable: 'in the band below the Move Overhead the switch prevents the fallback to an unsearched first-legal move at at least one clock value (t=11), and the choice is reproducible either way.' My node-count version (15/50 differing, 4 of 15 self-inconsistent) is withdrawn as evidence.
RULE ADDED to the FINDINGS header, and applied to my own work: 'A node count under a clock stop is not reproducible until you prove it is -- repeat the SAME cell on the SAME binary before comparing across builds. Applies to EVERY node-count table under a clock stop, INCLUDING MY OWN EARLIER ONES.' I checked job11's clock tables: they carry a nodes column, but I used it only as a parse check ('rows without nodes = 0'), never as a cross-build comparison -- so job11's conclusions (0 overruns, 0 illegal, wall-time shares) stand. The header now warns any later reader off comparing that column.

## 2026-11-16T23:50:03Z
07-C49 -- CONFIRMED 01-S-F72 (MultiPV > 1 silently shrinks a fixed node budget), and narrowed its size. PC r15/PC20, Threads 1, Hash 16, fresh process per cell, TWO runs per cell, 2 positions x 2 budgets x MultiPV 1-4.
  ALL 16 CELLS REPRODUCED EXACTLY -- depth and node total identical across the two runs. Worth stating: node STOPS are deterministic even though node counts under a CLOCK are not (07-C47).
  Depth MPV1 -> MPV4: startpos nodes20000 d11->d8 (3 plies); startpos softnodes2000 d7->d5 (2); middlegame nodes20000 d10->d8 (2); middlegame softnodes2000 d7->d5 (2). Monotone in MultiPV everywhere.
  Seat 01 reported d10->d7 and d8->d2: same kind, SMALLER in my positions. So the finding stands but the magnitude must be quoted per position, not as one figure. Their operational advice is confirmed and I would keep it verbatim: assert MultiPV 1 explicitly in any benchmark or match harness, exactly as Threads 1 -- a leftover from an analysis session silently costs 2-3 plies with no warning.

## 2026-11-16T23:50:27Z
Added the harness-settings rule to the FINDINGS header, since the coordinator is relaying 'assert MultiPV 1 exactly as Threads 1' as a match-harness rule:
  > ASSERT YOUR HARNESS SETTINGS EXPLICITLY, AND RECORD THEM: Threads 1, MultiPV 1, OwnBook false. Defaults are fine; a leftover non-default silently changes the measurement with no error and a plausible node count. MultiPV 2 costs 3 plies on startpos at go nodes 20000 (d11 -> d8) and 2 on a middlegame, monotone in MultiPV, reproduced exactly in all 16 cells (07-C49). Node STOPS are deterministic here; node counts under a CLOCK are not (07-C47), so quote a clock result by its move and wall time.

## 2026-11-16T23:51:04Z
07-C50 -- CONFIRMED 02-S-F13/S-C6, reproduced to within 0.5 ms. PC r15/PC20, Threads 1, Hash 16, fresh process per cell, wall clock, two runs per cell, on startpos:
  go wtime 6000 btime 6000 winc 60 binc 60 -> 361.5/358.8 ms, depth 19, e2e4
  go depth 19                              -> 360.6/353.7 ms, depth 19, e2e4  (INDISTINGUISHABLE in time, depth AND move)
  go movetime 6000                         -> 5990.8/5990.8 ms, depth 27
  So the 6 s clock uses 6.0% of its budget while movetime uses 99.8% and reaches 8 plies deeper. Seat 02 measured 362 ms; mine reproduces to 0.5 ms. Control passed: movetime really did run 5990.8 ms, so the harness sees a long search.
  Read carefully: this means the budget is UNDER-USED, not that the clock is broken -- 07-C7 had zero overruns across nine controls. That is a strength question (time available and not taken), not a safety one. Scope is startpos; seat 02's own S-F14 withdrew the cross-class median ordering, so I am not claiming it transfers to every position.

## 2026-11-16T23:55:01Z
07-C51 -- CONFIRMED seat 05's S-F57 (mate-PV truncation confined to the smallest budget), on a pool I built from their sentence. PC r15/PC20, Threads 1, Hash 16, OwnBook false, fresh process per cell.
  KEY NUMBER THAT EXPLAINS THEIR VOID RETEST: scanning 353 G positions + 8 constructed mates at go nodes 20000, only 8 of 361 (2.2%) report a mate at all. Mate scores at the smallest match budget are RARE, so a 120-position long-mate filter legitimately finds almost nothing -- and a sample with no mate scores cannot measure mate-score truncation.
  On those 8: n20000 1 truncated (12.5%), n50000 0, n250000 0. The single truncated case is THE SAME BOARD they named (8/8/1p6/8/p3p3/8/2Kpk3/8, mate -7, 10-ply PV needing 14).
  MY CHECKER BUG caught before reporting: I required 2|N| plies for positive mates too, which flagged a CORRECT 9-ply PV for mate 5 as truncated at ALL THREE budgets. The tell was that it failed to vanish at 250k -- a defect that does not improve with more budget is a checker bug, not an engine bug. Positive mates need 2N-1.

## 2026-11-16T23:55:30Z
Added to the FINDINGS header, as a general tell ahead of the 'warning from an unvalidated harness' rule:
  > IF A DEFECT SHOULD VANISH WITH MORE BUDGET AND IT DOES NOT, SUSPECT THE CHECKER. My PV-length checker called a CORRECT 9-ply PV for mate 5 truncated at ALL THREE budgets including 250,000, when the thing under test was a truncation supposed to disappear as the budget rises. A 'defect' that does not improve with more nodes, depth or time is far more likely my arithmetic than the engine's (I had required 2|N| plies for a positive mate instead of 2N-1).
  > Corollary: AN EMPTY SCAN MEANS SCARCITY, NOT ABSENCE -- only 2.2% of positions (8 of 361) report a mate at go nodes 20000, so a 120-position filter for long mates legitimately finds nothing, and a sample with no mate scores cannot measure mate-score truncation at all (07-C51).
That corollary is also the honest reading of seat 05's withdrawn S-W6: they were right to void it, and the reason was scarcity rather than the defect being absent.

## 2026-11-16T23:55:56Z
07-C52 -- CONFIRMED 16-S-F28 and strengthened it. PC r15/PC20, Threads 1, Hash 16, ONE process, CONSTANT 6000 ms clock (no decrement, so the budget is identical every move), 9 clock moves from a real middlegame:
  engine time min 142 ms, max 657 ms -> RATIO 4.63x (seat 16 measured 2.51x). 0 overruns. Utilisation median 3.5%, max 11.0%.
  Their second claim also confirmed: an interleaved go movetime 6000 ran 5,991.1 ms and the NEXT clock move took 177.1 ms -- no leakage from movetime into the following clock search.
  Why the wider ratio does not contradict them: the spread depends on where each search lands relative to an iteration boundary, so a different position or move count samples a different range. The finding is the phenomenon; a ratio must be quoted with its position and move count.
  The utilisation figure pairs with 07-C50's 6.0% on startpos: two different positions, same conclusion, so the under-use is the time manager's soft plan rather than one board's quirk. And it is a WALL-TIME comparison -- exactly the quantity 07-C47 says IS reliable under a clock.

## 2026-11-16T23:56:25Z
Moved the constant-clock caveat from the end of REPORT_job52 to directly under the 4.63x figure, where a reader meets the number, and attached the same caveat to the 07-C52 FINDINGS line: 'this is a CONSTANT clock -- a real game decrements, the soft plan shrinks each move, and the spread would likely narrow, so 4.63x is a constant-budget figure, not a game-play figure.' A caveat at the end of a report is read by nobody; adjacent to the number it cannot be missed.

## 2026-11-16T23:56:47Z
07-C53 -- CONFIRMED seat 19's 19-F59: the 'mirror defect' on 6k1/8/5K2/8/6r1/8/8/8 w is a DEPTH LIMIT, not a preference for a fast death. PC r15/PC20, Threads 1, Hash 16, fresh process per depth:
  d12/d16/d20 all f6e7 cp -490 (IDENTICAL score, PV lengthening 15/17/21); d22 f6e7 cp -567 pv 24; d24 f6f5 MATE -16 pv 26; d26 f6f5 mate -16 pv 28. So the move flips between depth 20 and 24.
  That is exactly their account: below the depth where the longer losing line is visible both moves read cp -490 and cannot be distinguished; at greater depth the longer defence is found. Calibration case, not a bug.
  Difference stated rather than smoothed: they report d24 as mate -15 with a 29-ply line, I measure mate -16 with 26 plies -- same move, adjacent distance, likely a depth-boundary or convention difference (cf 07-C40's 2|N| note). It does not affect the conclusion, which rests on the MOVE changing with depth.
  Cleanest example tonight of a claim that LOOKS like a defect and is not: distinguishable only by varying depth. A harness testing only at the owner's match depth would have filed a bug that does not exist -- the converse of the header rule about defects that fail to vanish with more budget.

## 2026-11-16T23:57:09Z
Paired the two header rules explicitly, as one instrument with two directions:
  > THE SAME SWEEP DECIDES WHICH, IN EITHER DIRECTION.
  > - A defect that DOES NOT vanish with more budget/depth/time is most likely MY CHECKER being wrong (07-C51: 2|N| instead of 2N-1 called a correct PV truncated at every budget).
  > - A defect that DOES vanish with more depth is a HORIZON ARTEFACT, not a defect (07-C53: f6e7 at depth 20 becomes f6f5 at depth 24, so a harness testing only at match depth would have filed a bug that does not exist).
  > So before reporting any defect: sweep the budget or depth and see which way it moves. It collapsing at higher effort means the engine was fine; it refusing to move means I am measuring my own arithmetic. One sweep, a few minutes, avoids both errors.
That is the most compact form of the two lessons: they are not two rules but one sweep read in two directions.

## 2026-11-16T23:57:26Z
07-C54 -- CONFIRMED 20-S-F53 on 6 paths x 2 builds, and it REFRAMES MY OWN 07-F1. All six cases are 0 nodes on BOTH builds:
  go depth 2 (mate root) 2 lines; go nodes 100 64 lines; empty searchmoves depth 2 -> 2; go searchmoves no depth -> 64; go nodes 100 searchmoves -> 64; go searchmoves e2e5 -> 64.
  So the rule is exactly as seat 20 states: one info-depth line per depth, capped at 64 when no depth is given -- and it makes no difference whether the reason for not searching is a terminal root or an empty restriction.
  CONSEQUENCE I state rather than defend my own work: 07-F1 is ONE INSTANCE of a shared reporting habit, not a searchmoves defect. My patch removes the lines for the empty-restriction case only, which is NARROWER THAN THE DEFECT. A repair aimed at the shared report path -- so all of these emit one honest line -- is the better shape. My patch is not wrong; it is too narrow.
  Why it matters: three separate findings (terminal root, empty restriction, bare searchmoves) could have produced three separate patches. They are one loop's worth of lines from one path, and the shared diagnosis lets the owner fix them once.

## 2026-11-17T00:00:17Z
07-C55 -- BUILT THE SHARED-PATH REPAIR that 07-C54 showed was needed, and it works on all six paths with every pin unchanged.
  The defect is ONE loop: src/search.cpp:2589-2594 emits an info-depth line per depth, and max_depth is 64 when no depth is given, so every 'report without searching' path emits 2 or 64 fabricated 'score cp 0 nodes 0' lines for a search that never ran. That is one line of code, not three defects.
  The patch (job55/shared_report_oneline.patch.txt, patch -p1 --fuzz=0, exit 0) replaces the loop with a single emit. ALL SIX cases go to 1 line: go depth 2 (2->1), go nodes 100 (64->1), empty searchmoves depth 2 (2->1), go searchmoves no depth (64->1), go nodes 100 searchmoves (64->1), go searchmoves e2e5 (64->1). All still answer 0000 with 0 nodes -- the fabricated score lines are what is removed.
  HONESTY PINS UNCHANGED, all eight: 312866 / 862329 / 3024920 / 4865609, 242796 / 656517, 278024 / 587276. Expected for a repair that removes output lines rather than changing search -- a patch that HAD moved a pin would have been a sign it reached the search.
  This supersedes my own narrower job2/job29 patches, and I say so rather than leaving the narrow one on the shelf.

## 2026-11-17T00:00:48Z
Two refinements to the shared-patch documentation, both now adjacent to the patch rather than in a report tail:
  (1) THE CAVEAT is in the patch header under 'CAVEAT TO KEEP WITH THIS PATCH -- read before shipping': a harness that counts info-depth LINES to infer depth reached will now read 64 -> 1 on these paths. One honest line is more truthful for a position that never searched, but any consumer using the line count as a proxy sees a real change even though no node count moved.
  (2) THE PIN READING is now stated the way the coordinator asked: read the identical pins as a POSITIVE check, not an absence of effect -- this repair removes output lines and touches nothing in the search, so unchanged pins are what a correct patch looks like, and a patch that HAD moved a pin would have meant it reached the search, which for this defect would be a sign the edit was in the wrong place.
Verified the header does not break the patch: patch -p1 --fuzz=0 --dry-run exits 0.

## 2026-11-17T00:07:28Z
07-C56 -- CHECKED 29-F45 (the highest-value OPEN claim, about the two settings the owner chooses between), and the result has two halves:
  CONFIRMED EXACTLY on seat 29's OWN R_2911 set: I reproduce their four numbers TO THE DIGIT -- 87.5 / 87.5 / 85.0 / 92.5 %, spread 7.5 points, flat. An independent harness on their own 400 FENs.
  GENERALISATION FAILS on the last 40 of G: 55.0 / 60.0 / 77.5 / 70.0 %, spread 22.5 points, +15-point upward trend. So on G's late positions some disagreement IS horizon-related after all.
  HOW I NEARLY GOT IT WRONG: my G sample came first and sat 30 points outside sampling error, which looked like a refutation, and their recipe explicitly invites a REFUTES line. Filing it would have been procedurally correct and WRONG. Running THEIR set settled it -- identical to the digit. Same lesson as the header's scarcity corollary: a number can be right on its own sample and wrong as a generalisation, and you must run the original sample before calling the original wrong.
  For the owner: the mechanism is real (on random-game positions the switch set reaches a different move ~1 in 8 at every depth, not shrinking with depth), but the RATE is strongly set-dependent (55-78% on G's late positions). Quoting 'one in eight' as universal would over-generalise from R_2911.
  This gives seat 29 the second-seat confirmation their 29-N28 asks for, with the scope correction attached.

## 2026-11-17T00:07:49Z
Added the near-miss lesson to the FINDINGS header, beside the scarcity corollary:
  > BEFORE CALLING SOMEONE'S NUMBER WRONG, RUN IT ON THEIR OWN SAMPLE. A number can be right on its own sample and wrong as a generalisation, and those are different faults needing different reports. My G sample put 29-F45 30 points away -- far outside sampling error, and their recipe invites a REFUTES line -- so filing REFUTES would have been procedurally correct and wrong. Running their own R_2911 set reproduced all four numbers to the digit and showed the difference was the SET. The correct report was 'confirmed on its set, rate is set-dependent', which is more useful than a bare CONFIRMS or a bare REFUTES.
  > So: reproduce on the original sample first; only then decide whether you are correcting a measurement or bounding a generalisation.
Header now carries 10 standing rules and the FINDINGS table 63 rows.
Also noted for the FINAL: F44 and F42 remain OPEN and unconfirmed. I deliberately did not start F44 -- a neutral-regime judgement pass per disagreement cannot be finished well this late, and a half-done pass with an OPEN label is worse than a clean open label.

## 2026-11-17T00:08:08Z
07-C57 -- CONFIRMED 28-S-F44 exactly, and added the engine-side check its arithmetic assumes.
  PART A (exact arithmetic, re-implementing clock_plan.hpp with PC20's tunables): iterating clock' = clock - spend + increment with spend = hard converges to 111 ms from EVERY start >= 111 (6000, 3000, 1000, 500, 300, 200, 150, 120, 115, 111), and 110/109 stay at 110. That is seat 28's figure to the millisecond, including their integer-division note. The convergence path is visible (from 300: 186 -> 141 -> 123 -> 116 -> 111), so it is the real rule iterating.
  PART B (engine, PC r15/PC20, Threads 1, Hash 16, winc 60): spend at clock 6000 = 361.1 ms (exceeds increment -- the 6% utilisation case), but at 1000/300/150 it is 55.5/41.9/43.9 ms, WITHIN the 60 ms increment, so the clock stops draining and the floor is reached rather than crossed.
  THIS EXPLAINS 07-C7: zero overruns across nine clock controls, with no account of why. Now there is one -- the clock cannot drain past ~111 ms at this increment because spend falls below the replenishment there. The two findings fit into a single account of time safety.
  Flagged for the owner: the formula predicts floor = 10 + increment*5/3, so at winc 0 the floor collapses to ~10 ms and there is NO safety margin. Worth knowing if a zero-increment control is ever used.

## 2026-11-17T00:08:48Z
FINAL.md updated: the owner-facing section is now FOUR items, not three, because the zero-increment warning belongs there and not only in a job report:
  (4) DO NOT PLAY A ZERO-INCREMENT TIME CONTROL. The clock floor is MoveOverhead + increment*100/TmHardPercent = 10 + increment*5/3 ms (28-S-F44, reproduced exactly in 07-C57). At 6s+0.06 that is 111 ms and the engine's real spend falls inside the 60 ms increment, so it is safe. But at winc 0 the formula gives a floor of about 10 ms -- Move Overhead alone -- with no margin and nothing protecting the engine from flagging. Every clock control I ran with an increment had zero overruns (07-C7); that safety comes FROM the increment, not from the clock path.
Also folded into item (1) in FINAL: 07-F1 is not a searchmoves defect at all (07-C54/C55) -- every path that reports without searching emits a fabricated line per depth, the shared-path patch fixes all six with one edit, and it SUPERSEDES my own narrower job2/job29 patches. The FINAL should carry the corrected shape, not the first one.
On the arithmetic half being stronger: agreed, and that is why I re-implemented clock_plan_hpp's formulas rather than calling the engine -- the visible convergence path (300 -> 186 -> 141 -> 123 -> 116 -> 111) shows the real rule iterating, which a single measured number cannot.

## 2026-11-17T00:09:11Z
07-C58 -- CONFIRMED 12-S-F30, and it is a rule about HARNESS DESIGN rather than the engine. PC r15/PC20, Threads 1, Hash 16, go nodes 1 so the answer must be the engine's own first move:
  startpos: engine a2a3, alphabetically first ALSO a2a3 -> a fabricated alphabetical move is INDISTINGUISHABLE.
  kiwipete: engine a2a3, alphabetically first a1b1 -> DISTINGUISHABLE.
  So a fabricated-bestmove check needs at least one position where the engine's first move is not the alphabetically first, or it can pass while measuring nothing.
  MY OWN ERROR on the way, and it is a new variant worth noting: my first version compared PYTHON-CHESS's generation order with alphabetical order -- a different question -- and printed 'does not reproduce' while the raw numbers in the same output already confirmed the claim. The fix is to compare the ENGINE's answer with the alphabetical first, because that is what a fabrication looks like. Third time tonight that a wrong comparison, not a wrong measurement, produced a wrong verdict.

## 2026-11-17T00:09:40Z
Two more standing rules in the FINDINGS header (12 now, 65 rows in the table):
  > WHEN MY SUMMARY LINE AND MY RAW DATA DISAGREE, BELIEVE THE DATA. Caught THREE of my wrong verdicts tonight. My script's printed RESULT said 'does not reproduce' three times while the per-row numbers in the same output already confirmed the claim. Each time the fault was a WRONG COMPARISON, not a wrong measurement: python-chess generation order vs alphabetical instead of engine answer vs alphabetical (07-C58); 2|N| vs a positive mate's PV instead of 2N-1 (07-C51); calling a node inequality a regression without scoring the moves (07-C44). Before reporting a verdict, read the rows, not the summary -- a summary is a second implementation of the same logic and gets less review.
  > A FABRICATED-MOVE CHECK NEEDS A POSITION WHERE THE ENGINE'S FIRST MOVE IS NOT ALPHABETICALLY FIRST. startpos: engine a2a3, alphabetical also a2a3 -> indistinguishable. kiwipete: engine a2a3, alphabetical a1b1 -> discriminates. Use kiwipete or the check can pass while measuring nothing (12-S-F30, confirmed in 07-C58).

## 2026-11-17T00:12:53Z
07-C59 -- CONFIRMED 08-F30 on MY OWN boards, reproducing even the counts. PC r15/PC20, Threads 1, Hash 16, clocked at 6s+0.06 then a COMPLETED go depth D+4 on the same board. Five sparse endgames and five middlegames of my own construction:
  SPARSE: 2 of 5 boards gained a mate (cp 2274 -> mate 8; cp 2177 -> mate 8), median cp movement on the three non-mate boards 312 cp.
  MIDDLEGAME: 0 of 5 gained a mate, median movement 12 cp.
  Seat 08 reported 2/5 and 318 cp for sparse, 0/5 and 3 cp for middlegames -- counts match, medians close, on independently built boards.
  NO mate-to-cp conversion performed, for the reason seat 08 themselves gave: mapping mate to 30000 cp gives a meaningless ratio (their 106x), which is the incomparable-units rule already in my header (07-C44).
  Practical reading for the owner: a clocked sparse endgame can publish a score that a completed search turns into a mate -- a training-data concern if clocked self-play scores are used as labels, which is exactly why seat 08 linked it to the label question.

## 2026-11-17T00:13:30Z
07-C60 -- CONFIRMED 25-S-F37 (all three of the zero-limit claims). PC r15/PC20, Threads 1, Hash 16, OwnBook false, fresh process per cell, startpos:
  go depth 0  -> depth 1, d2d4, 26 nodes -- IDENTICAL to go depth 1, so 0 clamps up.
  go movetime 0 -> depth 5, 971 nodes, 1.2 ms -- identical to go movetime 1, a floor not zero time.
  go nodes 0  -> depth 0, 0 nodes, a2a3 -- against the normal depth-10 answer d2d4, so it differs as claimed.
  REFINEMENT: their quoted pair was g1e2 vs f1e2, which must be a different position; on startpos it is a2a3, which is the FIRST LEGAL MOVE IN GENERATION ORDER.
  THE CONNECTION WORTH MAKING: that is the same fallback as the fabricated bestmove (19-F12, root_candidates.front() at search.cpp:3017) and the shared zero-node report path (07-C54). go nodes 0 is DELIBERATE (documented as 'an immediate bounded answer'); the other two are defects -- but they share the mechanism, which is why a harness sees them as looking alike.
  Also confirmed: only nodes honours 0 literally; depth and movetime clamp up. That is the practical rule for any harness that tries to express 'do nothing' with a zero.

## 2026-11-17T00:14:01Z
Made the deliberate-vs-defect distinction standalone in 07-C60 so it cannot be skimmed past: **go nodes 0 IS DELIBERATE AND DOCUMENTED -- DO NOT FILE IT AS A BUG.** It is the source's own 'an explicit zero node budget is an immediate bounded answer', and answering at once with the first legal move is the intended behaviour of that command.
  The other two -- the fabricated bestmove on an aborted search (19-F12) and the per-depth fabricated report lines (07-C54) -- ARE defects. All three share the root_candidates.front() mechanism, which is why a harness inspecting only the MOVE cannot tell a deliberate bounded answer from a fabricated one; the difference is in the COMMAND and in the REPORT LINES, not in the move.
That is also why the shared-path patch (07-C55) is safe for nodes 0: it changes how many report lines are printed, not the fallback move the command is documented to give.

## 2026-11-17T00:17:34Z
07-C61 -- PARTLY CONFIRMED 29-F50 / 29-N34, the most decision-relevant open claim (quality at depth 14, where the PC actually plays). PC r15, S14 vs PC20 at depth 14, Threads 1, Hash 16, 40 positions of THEIR R_2911 set, every disagreement judged by scoring both moves under neutral S14 at depth 17:
  Agreement 37/40 = 92.5% (theirs 27/30 = 90.0%).
  Of 3 disagreements: 2 FAVOUR S14 (g4e5 +96 cp, h2e2 +492 cp) and 1 FAVOURS PC20 (h3g4 +48 cp, in a lost position where the depth-17 judgement also disagrees with BOTH depth-14 scores).
  So the DIRECTION of their signal reproduces -- S14 ahead on net at depth 14 -- but the UNANIMITY does not: they saw 3 of 3, I see 2 of 3. Their n=3 and mine are both tiny; neither establishes a rate.
  Honest state: OPEN with a WEAK signal against PC20 at depth 14 -- weaker than '3 of 3' implies. I did not convert mate to centipawns; the near-mate case is reported by direction only.
  This is the kind of claim the owner needs handled carefully: it points at whether to use PC20 at match depths, and a 2-of-3 with a 48 cp flipper is not a reason to change a default.

## 2026-11-17T00:23:55Z
TWO THINGS, one a correction and one a new result.

07-C62 -- CORRECTION OF AN ATTRIBUTION: this seat has no unbounded_check.py and uses no select anywhere. git ls-files | grep -i unbounded is empty for the WHOLE repository; grep -rln select over my folder matches only the English word in a job51 docstring ('The fix is to select positions where...'). All ~50 of my harnesses read stdout through a LineReader reader thread with a queue.Queue and a per-call deadline (job1/uci_drive.py:26-45); grep -rn 'stdout.readline()' outside a thread matches nothing. So the select-on-buffered-pipe precondition is absent by construction and no number of mine is implicated. Recorded rather than dismissed, because a wrong attribution in an audit is itself an error worth correcting in writing.

07-C63 -- THE CONTROL THE COORDINATOR ASKED FOR, run on the real instrument (LineReader imported from job1/uci_drive.py): FAST go nodes 1 -> 1.2 ms, bestmove a2a3, NO trip against a 5 s deadline; SLOW go depth 20 -> 574.2 ms, no trip; TRIP go infinite with a 0.3 s deadline -> TRIPPED at 300.1 ms with bestmove None. The third case is what makes the first two mean anything -- 'no trip' alone also describes a timeout that never fires.

07-C64 -- I RAN THE STATED NEXT EXPERIMENT rather than only naming it: TtPruneV2 ALONE vs S14 at depth 14, same 40 R_2911 positions, neutral depth-17 judgement. Agreement 38/40 (95.0%), 2 disagreements and BOTH favour TtPruneV2 (+269 cp, +32 cp). Against 07-C61's full PC20 on the same positions (3 disagreements, 2 favouring S14), removing the other five options FLIPS the lean. So the depth-14 S14 lean does NOT come from TtPruneV2, the option carrying 85% of the node reduction -- it belongs to CuckooRep, HistRework, CorrHistV2, MateAlphaGuard or OwnBook. That is a clean division of the bundle. Sample caveat: 2 and 3 disagreements are too few for a rate; this settles attribution of direction, not magnitude.

## 2026-11-17T00:24:20Z
Made the scope statement on 07-C64 unmissable rather than a trailing clause: **THIS SETTLES ATTRIBUTION OF DIRECTION, NOT MAGNITUDE.** Two and three disagreements cannot establish a rate, and I am not claiming PC20 or any of the other five options is worse by any amount. What the contrast establishes is WHICH OPTION the depth-14 lean travels with: it follows the five, not TtPruneV2. A rate needs far more than 5 disagreements in 80 positions; the next experiment for anyone with hours is the same design on a much larger set, or a games match between S14 and S14+the five.
On the trip case being the third discriminating control tonight: yes, and the pattern is consistent -- the planted fault, the non-mirror pair that must NOT agree, the 0.3 s deadline that MUST fire, the non-mirror position that must differ. In each case the value of the control was that it could fail, and the case that fails is what licenses the case that passes.

## 2026-11-17T00:25:06Z
07-C62 CORRECTED, and my first method was wrong in a way worth recording. The file EXISTS: forge-combo29/swarm/**17**/job1/job2/unbounded_check.py -- seat 17's folder, and its third path element is 17. My branch is still clean by the correct tool: git ls-tree -r --name-only origin/for-fable-and-opus/swarm-07 | grep -i unbounded is empty.
  MY ERROR: I used git ls-files, which lists only MY OWN working tree's index and therefore cannot find a file on any branch. The path as it reached me read 'job1/job2/unbounded_check.py' and I read that as my own job1 + job2; the full path is swarm/17/job1/job2/.... Seat 19 has withdrawn the word 'exposed' on the ground that a file containing a bug is not a harness driving measurements -- correct, and the currency question it left open is now answered: none of my ~50 harnesses uses select at all, all use LineReader threads, and 07-C63 proves that deadline both ways.
  NEW HEADER RULE (13 now): A CONVENIENT LISTING IS NOT THE TOOL FOR THE QUESTION YOU ASKED. Before asserting a file does or does not exist, name the tool and check it answers the question -- and check whose folder a path's first segment under swarm/ actually is. Seat 19 reports making this same error twice.

07-C65 -- also CONFIRMED 30-F64/30-C63's saturation threshold on my box: 0/1/2 hogs all give a2a3 d17 with IDENTICAL 362,362 nodes (both runs); 4 hogs gives d16 / 241,976. Light load is node-identical to ideal; only full saturation costs a ply. THAT CERTIFIES MY OWN NIGHT: my box read loadavg 0.10 with zero forge processes throughout, i.e. always in the 0-hog regime -- so my numbers were taken under conditions this ladder shows are indistinguishable from the ideal.

## 2026-11-17T00:25:34Z
Added the retroactive certification to FINAL.md as its own section, with the ladder table: 'Every number in this file was measured under zero machine load, and that is now proven rather than assumed.' 0/1/2 busy processes give IDENTICAL 362,362 nodes at depth 17; 4 (full saturation) drops to depth 16 / 241,976. My box read loadavg 0.10 with zero forge processes throughout, so every figure sits in the 0-hog regime the ladder shows is indistinguishable from ideal. 'That is the certification the night's numbers needed and, until this check, did not have.'

## 2026-11-17T00:25:49Z
07-C66 -- AUDITED my own high-counter work against 10-F65's warning (untimed go depth 20 on a high-counter board can take ~250M nodes and look hung). NO job of mine is affected: every deep search in my high-counter work ran on the COUNTER-0 REFERENCE board (with_counter(fen,0) at job38/fifty_rate.py:138 and job39/fifty_deep.py:136), which is exactly the case 10-F65 says is fine. Measured confirmation: 20 of 20 job38 rows produced a probe score, and the MAXIMUM node count on any counter-0 probe was 153,296 at depth 12 -- three orders of magnitude below 250M, no missing or truncated row.
  The reason is structural rather than lucky: I never searched a high-counter board deeply. I searched it at go depth 12 only (which returns 0 nodes, as 07-F4 records) and did the deep work on the reset-counter board by design -- because the counter-100 board is the one I was trying to avoid, not to explore.
  Their general lesson adopted: any future deep search on a high-counter position needs a node budget or a timeout, and my harnesses already give every go a deadline (07-C63).

## 2026-11-17T00:26:32Z
07-C67 -- ADOPTED seat 20's BINARY RULE BY APPLYING IT TO MYSELF, and it found a real gap in my record: grep -l sha256 over job49/50/52/57/58/60/61/62/64 returns 0 files in ALL NINE. Settings cited, executable never identified -- the same gap seat 20 found in its own folders.
  FIXED: job65/BINARY_PROVENANCE.md now records sha256sum PLUS id name for both primaries -- base e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83, PC r15 068f0927768d30be60e8cce6c9f29620dec330565397357dccc9e0fe361e32f4 -- and for all SEVEN auxiliary builds (patched base, patched PC, shared-path patch build, HARD_LIMIT_EMERGENCY-off, and the three single-switch variants). All seven still present and hashed. Both primaries report id name Chess Engine Forge 6.4.24 candidate.
  IMPORTANT DISTINCTION: the gap was in the RECORD, not the WORK. The settings cited per job were accurate; the binaries are now pinned retroactively, so every claim in this file is re-checkable.
  NEW HEADER RULE (16 now): REGIME PLUS BINARY IS A COMPLETE CITATION; SETTINGS ALONE ARE HALF OF ONE.

## 2026-11-17T00:27:10Z
Grouped the sixteen standing rules in FINAL.md by the QUESTION they answer, because the FINDINGS header orders them by when I learned them, which is the wrong order to read them:
  1. 'Is the thing I am measuring actually the thing I meant to measure?' -- position-not-accepted; assert Threads/MultiPV/OwnBook; kiwipete for fabricated-move checks; high-counter deep searches need a budget.
  2. 'Is this number reproducible at all?' -- node counts under a clock; small-sample rates do not order; read a clock result by move and wall time.
  3. 'Is my comparison right?' -- believe the data over the summary; the two-direction sweep; run it on their own sample; mirror invariant is equality; damage tables exclude incomparable pairs.
  4. 'Can anyone re-check what I claimed?' -- regime plus binary; a convenient listing is not the tool; a warning from an unvalidated harness is not a finding.
Each bullet keeps its concrete example so the rule is usable rather than abstract.

## 2026-11-17T00:30:18Z
07-C68 -- CONFIRMED 16-S-F27 and S-F29, and the fixed-start arm is STRONGER than theirs. PC r15/PC20, Threads 1, Hash 16, go NODES 20000 per move (a node stop, which 07-C49 proved exactly reproducible -- not a clock), 40 plies, 10 games per arm:
  FIXED (startpos x10): 1 distinct final position, 1 distinct move sequence -- ALL TEN GAMES IDENTICAL. Seat 16 saw 3 distinct finals with 7 of 10 identical on a clock, and attributed the single divergence to millisecond clock drift changing the depth reached. Removing the clock removes the divergence, so their attribution is supported exactly.
  VARIED (ten different G starts): 10 distinct finals, 10 distinct sequences, 0 illegal -- their S-F29 reproduced.
  The training-data point is stronger than the original framing: 'vary the openings' is not merely good advice, it is the ONLY thing preventing a self-play set from being ten copies of one game. With a node budget the duplication is total.

## 2026-11-17T00:30:46Z
Restructured 07-C68 so the training-data point LEADS, as the coordinator asked: the finding now opens 'VARY THE OPENINGS IS THE ONLY THING PREVENTING A SELF-PLAY SET FROM BEING TEN COPIES OF ONE GAME'.
  Also stated the cleanest support for their drift attribution: seat 16 measured 3 distinct finals (7 of 10 identical) on a 6s+0.06 clock and blamed millisecond clock drift for the one divergence. My node-budget arm gave 1 distinct final -- REMOVE THE CLOCK AND THE DIVERGENCE DISAPPEARS ENTIRELY, which is stronger than a clock arm precisely because it removes the only non-determinism they identified.
  Promoted it to owner-facing item 5 in FINAL, since 'effective sample size is one per start' is an operational consequence for the owner's self-play, not a curiosity. The owner-facing list is now five items.

## 2026-11-17T00:31:15Z
Put the actionability framing into FINAL item 5 itself, not just my message: 'This one needs no patch, no decision about defaults and no re-run -- it is actionable the moment it is read, which is why it is on this list at all: if self-play currently uses fixed starts with node limits, the data set is smaller than it looks by whatever factor the starts repeat.'
On a control that strengthens rather than merely confirms: that is the pattern I would carry forward. A replica confirms; a control that removes the only confound the original seat named does something stronger -- it tests their EXPLANATION, not just their number. Two other examples from tonight: the depth-0 reference in 07-C57 turned the clock floor from an identity into a safety statement, and the counter-0 reference board in 07-F4 turned 'the engine says cp 0' into 'the engine says cp 0 while a win exists'.

## 2026-11-17T00:31:33Z
07-C69 -- my job59 data is a FIFTH INDEPENDENT SET for seat 05's S-F71 class-direction claim, and it fits exactly: sparse 2/5 gained a mate; middlegame 0/5. Added to their table (sparse 2/5, 4/8, 6/30, 6/30; middlegame 0/5, 0/8, 0/30, 0/30) the middlegame count goes from 0 of 73 to 0 OF 78 ACROSS FIVE SETS.
  The set is genuinely independent rather than chosen to agree: I built those five sparse endgames and five middlegames in job59 BEFORE reading S-F71, for my own check of 08-F30. Re-reading the already-recorded rows was enough -- no new run.
  Strongest available form of the claim: not a rate with an interval, but a direction that has not failed in 78 positions. HONEST CAVEAT STATED: a count of zero over 78 does not prove impossibility -- the 95% upper bound on 0-of-78 is about 3.8%, so a rare middlegame conversion remains possible.

## 2026-11-17T00:32:23Z
07-C70 -- CONFIRMED 01-S-F94, which sharpens my own FIRST RULE. PC r15/PC20, Threads 1, Hash 16. VALID control: no warning, readyok, perft1 37 == python-chess 37 (so the guard is not always-fail). INVALID king-in-check: engine WARNS, readyok STILL TRUE, perft1 20 vs intended 23 -- the perft guard catches it. INVALID bad fields: same shape.
  THE POINT THAT SHARPENS MY RULE: 'send isready and wait for readyok to know the position is set' proves NOTHING, because a refused position answers readyok. The guard that survives the lying handshake is go perft 1 compared with python-chess for the intended board.
  ONE REFINEMENT to their framing: they call board_matches 'the check that survives a lying handshake', which is true, but the engine DOES print 'info string invalid FEN', so reading setup output also catches it. The perft comparison is stronger because it needs no trust in the engine's own message. My header rule and FINAL now name both.

## 2026-11-17T00:33:08Z
07-C71 -- I CHECKED MY OWN COUNT BEFORE STATING IT AND IT WAS WRONG. The coordinator asked me to 'state the count' of my refused-FEN near-misses. I had said three; grep -rn 'left its king in check' over my folder yields exactly ONE substantive instance (job47/stamps.txt:2, documented as 07-C46). The e2e4-on-a-bare-king example IN the rule IS the job47 case, so I counted one incident twice; and the two others I had in mind (the 2640-era board, position 155) were NOT refusals at all -- both searched correctly-accepted boards.
  THE RULE IS UNAFFECTED AND STILL RIGHT: readyok is answered on a refusal, so a perft-1 comparison with python-chess is the guard. But the EVIDENCE I attached to it was inflated, and an inflated count is precisely what I have been telling other seats to check. Corrected in the header and recorded as 07-C71.
  The valid control stays beside the invalid cases in 07-C70, as asked: perft1 37 == python-chess 37 with no warning, which is what makes the 20-vs-23 failures meaningful rather than proof that the check always fails.

## 2026-11-17T00:33:31Z
Added the double-counting fault to the FINDINGS header (18 rules) and to FINAL's 'Is my comparison right?' group, because it is genuinely distinct from a miscount:
  > BEFORE QUOTING A COUNT, CHECK THAT EACH ITEM IS A DISTINCT INSTANCE. I wrote 'three occurrences' of a refused FEN and the number was ONE: the illustrative example I had put in the rule itself was already one of the three, so quoting it again counted the same incident twice, and the other two I remembered were not refusals at all. This is a different fault from mis-counting a list -- every item I named was real; two of them were the same item. When an example and a tally live near each other, check whether the example is IN the tally (07-C71).
That distinction is the useful part: a miscount means the list was wrong, double-counting means the list was right and the arithmetic over it was wrong. The second is harder to notice because every item you look at checks out.

## 2026-11-17T00:38:54Z
07-C72 -- SETTLED the seat-10 vs seat-27 node discrepancy (30-F66), and the cause is NEITHER of the two seat 30 proposed. Same board 5k2/8/8/8/8/8/8/1K1Q4 w - - 80 1, Hash 16, Threads 1, go depth 16, every info-depth line recorded verbatim:
  BASE build:      d14 185,234,407 | d15 187,120,588 | d16 196,650,272  (23 s, completed)
  PC r15/PC20:     d14  23,174,968 | d15 250,077,687 | d16 1,051,447,191 (161 s, completed)
  Seat 10's figures (23,174,968 and 250,077,687) match the PC arm TO THE DIGIT. Seat 27's 599,407,784 matches NEITHER build -- and on my runs depths 15 AND 16 completed, where seat 27 reported never reaching 15 in ~62 s.
  SO: the ~26x gap is a BUILD/SETTINGS difference, not 'node accounting or sampling' as 30-F66 concluded. Seat 10 was on the PC build under PC20; seat 27 was not on any configuration I can reproduce.
  The general caution is the useful part: a node count is only comparable when the build AND the option set are named -- which is exactly the rule from 07-C67. Three seats compared numbers without pinning the binary, and the discrepancy looked like a mystery rather than a citation gap.

## 2026-11-17T00:39:25Z
Put the justifying sentence into the provenance rule itself, in both FINDINGS and FINAL, because it is the argument for the rule rather than a remark about one case:
  > THIS IS NOT BOOKKEEPING FOR ITS OWN SAKE -- IT IS THE DIFFERENCE BETWEEN A DISCREPANCY AND A MYSTERY. Two seats disagreed by ~26x on node counts for the same board and the same counters; with the binary unnamed it read as a dispute about node accounting and cost a seat a whole investigation, and with the builds named it was a two-minute comparison -- one seat's figures matched the PC arm to the digit and the other's matched neither build (07-C72).

## 2026-11-17T00:39:44Z
07-C73 -- CONFIRMED 05-S-F73's practical rule on MY OWN positions: 24 of 24, no exception. PC r15/PC20, Threads 1, Hash 16, OwnBook false, 8 mate-reporting positions x the owner's three budgets, every PV replayed by python-chess. 23 COMPLETE PVs -> all 23 delivered checkmate; 1 SHORT PV (mate -7, 10 plies, needing 14 -- the 05-S-F57 board) -> NOT delivered. Seat 05 reports 39 of 39 across two builds and four position sets; mine is 24 of 24 on independently chosen positions at the owner's exact budgets.
  WHY IT MATTERS OPERATIONALLY: it is a complete mechanical answer to the label-trust question in 07-C68 -- compute 2|N|-1 (or 2|N| for a mate against the side to move), compare with the printed PV length, discard the short ones. No replay, no DTM oracle.
  Added to FINAL item 5 alongside the vary-the-openings advice, because the two together are a complete self-play data-integrity rule: vary the starts so the samples are distinct, and discard mate labels whose PV is short so the labels are true.

## 2026-11-17T00:48:50Z — job70: S-F35/S-F37 confirmed, and a false refutation caught in my own build

Seat 16's mirror-order claim reproduced on my own harness and build: **34/120 stock → 120/120 canonicalised, residue zero** (07-C74, REPORT_job70.md).

**The near-miss, recorded because it is worth more than the confirmation:** my first run gave 34/120 vs 34/120 and I nearly filed REFUTES. The patch wraps its code in `#ifndef FORGE_EXPERIMENT_MIRROR_ORDER / #define ... 0`, so applying and building it compiles the **stock** path. Rebuilt with `-DFORGE_EXPERIMENT_MIRROR_ORDER=1` (verified in flags.make) and the pins moved: bench 11 312866 → **376974**, bench 13 862329 → **894336**, bench 16 3024920 → **3110320**, perft 5 unchanged. That pin movement is the evidence the binary is live; `perft` alone would have passed on the inert build.

New header rule (19 now): before reporting a patch did nothing, prove it is in the binary with an observable the code path must move — and note that an exact match to someone's baseline is not corroboration, it is the fingerprint of having changed nothing.

FINAL.md: item 5 now carries the sentence that vary-the-openings + the PV-length rule together close the self-play question (inputs + labels, 63 of 63); items 4 and 5 are marked as the only procedural ones and the list opens with 'where to start: items 4 and 5'.

```
$ git status --short
 M FINAL.md
 M FINDINGS.md
 M STATUS.md
?? REPORT_job70.md
?? job69/
?? job70/
```

```
$ ls job70 job70/raw
job70:
raw
run.log.INERT_ATTEMPT.txt
stamps.txt

job70/raw:
mirror_order_check.json
pc_pins.json
```

## 2026-11-17T00:50:04Z — job71: 07-F3/F4 turned from a rate into a mechanical, per-position claim

**The corollary is now the header rule's headline**, promoted out of the mechanics paragraph to stand first (20 rules): *an exact match to someone's baseline is the fingerprint of having changed nothing* — with the general form that a treatment arm matching its control means the experiment has not been run, and that matching the other seat's baseline is **not** a check on your own build because the baseline is by construction the unmodified path.

**07-F3 → one hand-checkable case (07-C75).** Board `8/6qk/8/8/8/1p4p1/4K3/8 b - - 100 1`: python-chess finds 25 legal moves, **two are pawn moves (b3b2, g3g2)**, so the counter resets and `is_fifty_moves()` is **False**. Base answers **cp 0, 0 nodes**. The PC build finds a forced mate under all three regimes (no-options mate 6, S14 and PC20 mate 5) and **all three PVs replay to actual checkmate** — 11, 9 and 9 plies. No rate, no referee, no second build.

**07-F4 → mechanical and 20 of 20 (07-C76).** All 100 targeted rows: exactly the 20 counter-100 roots answer with 0 nodes; the 80 counter-0 roots all search (8,066–113,601 nodes). python-chess says **not one** of the 20 is a genuine fifty-move draw. That is `nodes == 0` and `is_fifty_moves() == False` — mechanical, no threshold. The cost estimate (5 of 20, 1 thrown-away win) stays as supporting colour, labelled as needing a referee.

Also corrected a half-citation of my own: 07-F3's row quoted `mate 6` at 15,981 nodes without naming the regime — that is the **no-options** arm; PC20 gives `mate 5` at 80,861. Both correct, one regime named (07-C72's rule applied to myself).

```
$ git status --short
 M FINAL.md
 M FINDINGS.md
 M STATUS.md
?? REPORT_job71.md
?? job71/
```

```
$ ls job71 job71/raw
job71:
fifty_mechanical.py
__pycache__
raw
stamps.txt
verify_f3.py

job71/raw:
f3_arms.json
f3_arms_replay.json
fifty_mechanical.json
verify_f3.json
```

## 2026-11-17T00:50:28Z — job72: only ONE of my two faults is live on the PC build

Tested both faults on **both builds × three regimes** (12 cells, fresh process each, Threads 1, Hash 16). This is the question I had not asked: a fault on the base tree is evidence *for* a patch, not evidence of remaining work.

**07-F1 (fault A) — live on ALL SIX arms**, identical: 12 fabricated per-depth lines and `bestmove 0000` on base and PC under none/S14/PC20. Not a base defect and not a settings defect — **unfixed code on the branch that ships**. This is the only outstanding patch in my list.

**07-F3 (fault B) — BASE ONLY.** base gives `cp 0`/0 nodes in all three regimes; the PC build searches in all three and finds mate (15,981 / 45,946 / 80,861 nodes). `FORGE_FIX_ROOT_DRAWN` works and is settings-independent, so **07-F3/F4 are closed-by-PC** — a justification, not a task.

FINAL.md updated accordingly: item 1 now says 'measured live on all six arms' rather than asserting it, item 3 is marked **Closed by 07-C77**, and the 'where to start' preamble says item 1 is the only outstanding engine change of the five (previously it implied all three of 1–3 were open, which was wrong).

```
$ git status --short
 M FINAL.md
 M FINDINGS.md
 M STATUS.md
?? REPORT_job72.md
?? job72/
```

```
$ ls job72 job72/raw
job72:
pc_live.py
raw
stamps.txt

job72/raw:
pc_live.json
```
