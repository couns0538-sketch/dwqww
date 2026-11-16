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

## 2026-11-16T21:47Z — PATCH COMPLETE AND PUSHED

**The fifty-move + repetition patch is finished and on GitHub**: `job1/two_doors_mate.patch.txt`
(commit f2f227ffc, report `REPORT_job1.md`, findings S-F2/S-F3). Both root doors closed, 12
draw/mate regression cases pass, honesty pins 4/4 on all four builds (unpatched release+ASan,
patched release+ASan).

Known limit, proven and documented in the same report (S-F4/S-F5): the short-circuit also fires
one ply down where the patch does not reach — `6k1/8/5PPP/8/8/8/8/R6K b - - 99 40` answers
`cp 0` in 36 nodes where hm 97/98 answer the true `mate -1` in 63. A second position
(`6k1/5ppp/8/8/8/8/8/R5NK b - - 99 40`) gives the same `cp 0` but CORRECTLY, as the control.

Also re-audited every table against seat 19's silent-zero warning (`job1/audit.py`,
`job1/audit.json`): the quit-mid-search table cannot prove a search ran (by design) and now says
so; the job-1 sequence runner was changed to record `max_depth_seen`/`max_nodes_seen` so a
"0 sanitizer lines" claim is backed by a measured search, and the 2,000-sequence run is being
repeated with those counters.

Now running: that repeated job-1 run (2,000 sequences, ASan+UBSan), then area 2 job 2 (races).
Next command: `bash forge-combo29/swarm/12/job1/run_job.sh /home/ubuntu/build/asan/forge /tmp/seqs /home/ubuntu/build/job1out3 asan_2000` (already running; after it, `python3 forge-combo29/swarm/12/job1/races.py /home/ubuntu/build/asan/forge /home/ubuntu/build/job2out 40`).

## 2026-11-16T21:52Z — MERGE INSTRUCTION (seat 27 composition)

Seat 27's drawn_root_reporting.patch.txt touches the same root_drawn block as mine. Measured on
clean 6b98f217 trees: seat 12 first then seat 27, or the reverse, BOTH apply clean with no fuzz
and give a byte-identical search.cpp (sha256 24912a43…), so order cannot silently drop a fix.
diff -u between the two trees is empty. Correction to seat 27's note: my patch is -p1 from the
repo root, not -p2 (-p2 fails). Composed build honesty 4/4 unchanged; on seat 27's board
6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 100 60 the base plays f2f3 / cp 0 / 0 nodes and the composed
tree plays a1a8 / mate 1 / 252 nodes. Details: job1/integration/MERGE_INSTRUCTION.md,
job1/integration/compose_hashes.txt, job1/integration/compose_table.txt.

## 2026-11-16T21:51Z — checkpoint (22:05 window)

Job 1 re-run (2,000 UCI sequences, ASan+UBSan, now recording max_depth_seen/max_nodes_seen so a
zero sanitizer count is backed by a proven search): 1026/2000 done, 0 crashes / 0 hangs / 0 sanitizer lines / 0 illegal bestmoves so far.
Partial raw committed under job1/ if the run has not finished.

Job 2 (races) started in parallel against the same ASan+UBSan build: stop / ponderhit / ucinewgame /
setoption Hash / quit at a random 0-50 ms delay during go infinite and go depth 30.
64 cases so far, 0 crashes / 0 sanitizer lines / 0 illegal bestmoves / 0 hangs.
Partial raw: job2/partial/races_partial.jsonl.

Patch status: COMPLETE and pushed (commit f2f227ffc), plus the seat 27 merge instruction
(325b8b112) and the node-level known limit (361922ca4).
Next commands: wait for both runs, then files: /home/ubuntu/build/job1out3/asan_2000.jsonl
sequences                 1026
UCI lines total           18044
bestmoves produced        2920
bestmoves not checkable   0
wall seconds total        834.6

| quantity | count | sequences |
|---|---|---|
| sequences run | 1026 | - |
| crashes (signal) | 0 | - |
| hangs (no readyok in 20 s) | 0 | - |
| sanitizer lines | 0 | - |
| illegal bestmoves (re-checked in a fresh process) | 0 | - |
| nonzero exit status | 0 | - |

no sequence fired anything; nothing further to list
and table                                                 cases  searched  san  proves?
job1/reproduction/doors_patched_release.json              4         4    0     True
job1/reproduction/doors_unpatched_asan.json               4         2    0     True
job1/reproduction/regression_patched_asan.json           12         6    0     True
job1/reproduction/regression_patched_release.json        12         6    0     True
job1/reproduction/regression_unpatched_release.json      12         4    0     True
job1/qms/quit_mid_search.json                             5         0    0    False
~build/job1out/asan_2000.jsonl                         2000         0    0     True
~build/job1out2/asan_2000.jsonl                        2000         0    0     True
~build/job1out3/asan_2000.jsonl                        1026         0    0     True

WEAK ZERO: job1/qms/quit_mid_search.json
  BY DESIGN: the search is interrupted before it produces an info line, so this table can never prove a search ran. A zero here is evidence about the stop/print path only, and is reported as such.

raw -> /agent/repos/dwqww/forge-combo29/swarm/12/job1/audit.json, then write REPORT_job2.md.

## 2026-11-16T21:56Z — halfmove sweep of the ply-down limit

The node-level fault (S-F4) exists ONLY at halfmove exactly 99, its last reachable value: 94-98
answer the true `mate -1` in 63 nodes, 99 answers `cp 0` in 36, and 100/101/110/149/150/151/200/
500/999/9999 all give identical `cp 0` / 0 nodes because the ROOT adjudication takes over — stable,
no degradation at very high counters. Raw: job1/node_draw_hm_sweep.txt.
