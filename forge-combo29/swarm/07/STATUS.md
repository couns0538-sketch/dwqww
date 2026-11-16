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
