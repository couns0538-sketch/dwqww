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
