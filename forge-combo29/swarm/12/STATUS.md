# STATUS — swarm seat 12 (area 2: UCI COMMANDS under ASan + UBSan)

seat 12
branch for-fable-and-opus/swarm-12
folder forge-combo29/swarm/12/
area 2 (ASW = ((12-1) mod 10)+1 = 2) — UCI COMMANDS under ASan + UBSan
seed 1201

## 2026-11-16T21:08Z

Done: seat claimed, release build of 6b98f217 with GCC 13.3.0 (`-march=x86-64-v4`, AVX-512F
and BMI2 both present on this box), honesty check 4/4.
ASan+UBSan build running in the background.
Next: HONESTY.txt committed, then area 2 job 1 (2,000 random UCI command sequences).

Times: see job*/stamps.txt and `date -u` lines in each commit.

## 2026-11-16T21:35Z

Done: honesty 4/4 on release AND on ASan+UBSan (nm 35/15). job1: 2,000 random UCI sequences
under ASan+UBSan — 0 crashes / 0 hangs / 0 sanitizer lines / 0 illegal bestmoves (harness
re-verified against the fabricated-bestmove rule from seat 19). S-C1 (CONFIRMS seat 06 S-F2),
S-F1 (`ucinewgame` resets the board to startpos, src/uci.cpp:254-257).
Answered the coordinator's memory question about quit-mid-search: NOT a memory fault — the
printed move is root_candidates.front() (5/5 positions equal to the engine's own perft order),
100 interrupted searches, 0 sanitizer lines, planted-fault control counted 3 lines.
Both root-draw doors reproduced (halfmove 100 and threefold repetition, matched pair, mate in 1
missed in each) and `two_doors_mate.patch.txt` closes both; honesty pins unchanged 4/4 on both
patched builds.
Running now: the door pair on the patched builds, then area 2 job 2 (races).
Next: `python3 forge-combo29/swarm/12/job1/two_doors.py ~/build/release_patched/forge /tmp/doors_patched.json`
