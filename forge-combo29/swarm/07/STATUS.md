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
