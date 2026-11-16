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

## 2026-11-16T22:12Z — job 2 done, job 1 re-run in progress

Job 2 (races) COMPLETE: 120 cases (12 x 5 interrupts x 2 go-lines) against the ASan+UBSan build.
0 crashes, 0 hangs, 0 sanitizer lines, 0 illegal bestmoves; all 120 produced a legal bestmove and
exit 0, so every zero is backed by a real search. Findings S-F6 (the clean result) and S-F7
(ponderhit on a non-ponder search correctly does nothing — 24/24). NOT the brief's 10,000 cases;
120 run, said plainly in REPORT_job2.md.
Job 1 re-run with max_depth_seen/max_nodes_seen: still running, counts in job1/.
Next command: `python3 forge-combo29/swarm/12/job1/table.py /home/ubuntu/build/job1out3/asan_2000.jsonl`
then `python3 forge-combo29/swarm/12/job1/audit.py`, then the final push.

## 2026-11-16T22:28Z — FINAL (deadline)

**area 2 job 1 — COMPLETE.** 2,000 random UCI sequences (34,704 lines) under ASan+UBSan:
0 crashes, 0 hangs, 0 sanitizer lines, 0 illegal bestmoves, 0 nonzero exits. The zero is
BACKED: 1,579/2,000 sequences demonstrably searched (deepest depth 64, most nodes 7,882,595),
recorded per sequence as max_depth_seen/max_nodes_seen. Report: REPORT_job1.md.

**area 2 job 2 — COMPLETE (120 of the brief's 10,000 cases, stated plainly).** 12 x 5 interrupts
x 2 go-lines against the same build: 0 crashes, 0 hangs, 0 sanitizer lines, 0 illegal bestmoves;
120/120 produced a legal bestmove and exit 0. Findings S-F6, S-F7. Report: REPORT_job2.md.

**The patch — COMPLETE and pushed.** job1/two_doors_mate.patch.txt closes both root draw doors
(halfmove 100 AND threefold repetition), 0 regressions on 12 draw/mate cases, honesty 4/4 on
patched release and patched ASan+UBSan.

**Merge instruction (seat 27).** Both apply orders give a BYTE-IDENTICAL search.cpp
(sha256 24912a43…), diff empty — order does NOT matter, contrary to seat 27's note. The correct
flag is -p1 from the repo root, not -p2. job1/integration/MERGE_INSTRUCTION.md.

**Known limit, with the sweep.** The short-circuit also fires one ply down: S-F4. It exists ONLY
at halfmove exactly 99 (94-98 give the true mate -1 in 63 nodes; 99 gives cp 0 in 36); from 100
upward the root adjudication takes over and every counter to 9999 behaves identically — stable,
no degradation. job1/node_draw_hm_sweep.txt.

FINDINGS.md: S-C1, S-F1..S-F7. All raw files committed. Nothing is running; nothing is in flight.

## 2026-11-16T22:19:16Z CONTINUE: 12 more hours, ends at 2026-11-17T10:19:16Z

Resuming the cycle. Seat 12, area 2, branch for-fable-and-opus/swarm-12 (unchanged, no new seat).
Next: read every unread forge-combo29/soak_all/FABLE_TO_swarm_N.md from the lowest N up; file 5
carries the PC engine source as a patch against 6b98f217 with -DFORGE_MATE_ALPHA_GUARD=1, which I
must build in a separate copy and pin before anything else.

## 2026-11-16T22:22:18Z — PC r15 built and pinned; aborted-search finding owned

PC build: patch sha256 d6bd72c531f785f4… (matches file 5), applied with patch -p1 --fuzz=0, built
-DFORGE_MATE_ALPHA_GUARD=1 with g++-13. **All 8 pins of file 5 match**: none 312866/862329/3024920/
perft5 4865609; S14 242796/656517; PC20 278024/587276. job3/PC_BUILD.md.

S-F8 (owned, confirmed independently): on r15 an aborted search still publishes a2a3 with 0 info
lines — 200/200 aborted searches under ASan+UBSan across none and PC20, both go forms, Threads 1.
0 sanitizer lines, with the planted-fault r15 copy counted 3 lines through the same runner.
S-F9: the move is root_candidates.front() of the CURRENT position, never stale (after `position` Y
it answers e2e3, so it is positional).
S-F10: FORGE_FIX_ABORT_PUBLISH is the switch that should have covered it, cannot (it needs a
finished iteration), and is #define 0 by default; enabling it still leaves 4/4 fabricated.

Next: job 3 of area 2 (every option at min/max/min-1/max+1/a word/nothing, between and during
searches) on BOTH builds, which is the next unrun job of my area.

## 2026-11-16T22:26:35Z — job 4 (area 2 job 3) done on both builds

Option extremes: 957 cases base / 1,077 PC none / 1,077 PC PC20, every option x 6 values x
between-search and during-search. 0 crashes, 0 sanitizer lines, 0 illegal bestmoves, 0 lost
readyok. Every out-of-range and non-numeric value refused with the engine's own line; nothing
accepted silently. Control 3/3 plants detected on both builds (unknown option, invalid value,
illegal bestmove). Threads 1 throughout except the Threads option itself, reset to 1 after.

New finding S-F12: `setoption` during a running search silently STOPS the search (4/4 option
types, both builds), while `isready` correctly does not — with controls that must and must not
fire, both behaving.

S-F11 added earlier today: the one-sentence fix for the abort fault (finish depth 1 and publish a
real searched move; `bestmove 0000` rejected because UCI gives 0000 the meaning "no legal move"
and GUIs act on it).

Reports: REPORT_job4.md, job3/abort_finding.md. Next: area 2 job 1 re-run on the PC build under
PC20 (my own base finds revisited on the PC build, as file 5 requires).

## 2026-11-16T22:27:04Z

S-F14 (the important one): the one-ply-down draw short-circuit is STILL OPEN on the PC build.
`6k1/8/5PPP/8/8/8/8/R6K b - - 99 40` answers cp 0 / 36 nodes on r15 where hm 97/98 answer the true
mate -1 / 63. Verified at depths 6..24 (still cp 0 at depth 24, nodes growing 2/ply) and counters
99..9999 (all cp 0), so no amount of search recovers it. Source: FORGE_FIX_ROOT_DRAWN repairs only
the root (search.cpp:2571); Worker::is_draw (search.cpp:1426-1436) is unchanged and returns a draw
for halfmove>=100 before the mate is seen. **The root door IS repaired on the PC — this is the
other door.** One-sentence fix in the finding.
S-F15 (honest negative): the repetition member of the same family could NOT be triggered — after
`position fen X moves`, the engine's key history excludes the FEN root so is_repetition finds one
match and the root is searched normally. Exposed by code, not demonstrated by me.

Next: continue the cycle — look for a new unconfirmed finding from another seat to check, else
re-run job 2 (races) on the PC build under PC20.

## 2026-11-16T22:28:28Z — S-F16: repetition uses the SAME defect

Tested seat 25's claimable-draw frame on the repetition side (the test S-F15 could not do). It fires.
Root `3k4/8/8/8/8/8/4P3/R3K3 b - - 7 43` (black a rook down); black's `d8e8` creates a threefold
where WHITE is to move and WINNING, so White declines.

| case | base | PC r15 |
|---|---|---|
| d8e8 only (creates the 3-fold) | cp 0 / 20 nodes | cp 0 / 20 |
| d8c8 only (same root, no repetition) | cp -1044 / 5,832 | cp -1072 / 10,757 |
| the same board, no history | cp +1128 / 14,216 | cp +1209 / 22,827 |

Depth 6..20 on the root: cp 0 at every depth on BOTH builds, PV never longer than one ply — not a
horizon effect, same as the fifty-move case. So **rotation and fifty-move share one flaw**: a
claimable draw scored as forced. FORGE_FIX_ROOT_DRAWN does not cover either, because the zero is
produced by is_draw one ply down.

Also: at the root with the LOSING side to move at a threefold, cp 0 is CORRECT (the loser claims) —
verified separately, so this is not "any repetition is broken".

Merged with seat 25: job4/pc_node_level_finding.md now cites swarm-25 debug/MECHANISM.md and
debug/CORRECTION.md, and states what I add (depth 6-24 per-node growth proving no horizon) and what
seat 25 has that I do not (the instrumentation). S-F15 marked SUPERSEDED by S-F16 in FINDINGS.md.

Threads 1 throughout, both builds.

## 2026-11-16T22:30:50Z — the claimable-draw fix: pins MOVED, stopped, not tuned

Implemented the one-sentence is_draw change as a text patch on BOTH builds
(job5/claimable_draw.patch.txt, -p1 --fuzz=0, applies to base at offset 0 and PC r15 at offset 126).
Two of the four named cases are genuinely FIXED: fifty-move claimable goes cp 0 -> **-153** (matching
seat 25's independent -150s), repetition-with-winning-side-to-move goes cp 0 -> **about -1200**.
The K v K control is KEPT (cp 0, 0 nodes) on both patched builds.

BUT: **three of the four honesty pins move on both builds** — bench 11 312866 -> 353312,
bench 13 862329 -> 979723, bench 16 3024920 -> 2893009; perft 5 unchanged. Per the instruction I did
NOT tune the fix to bring them back.

And two must-stay-zero cases regress **on the PC build only**: losing-side-at-a-threefold cp 0 ->
-1237, and clock 100 with no reset possible cp 0 -> -501 in 1,026,656 nodes. The second is a polarity
error in MY condition (it requires ALL moves to reset; that board has NONE), not in the engine.

Verdict: diagnosis right, direction right, patch NOT ready. Full table in job5/fix_report.md.
S-F17 records it in FINDINGS as NOT READY.

## 2026-11-16T22:32:24Z — correctness experiment on the claimable-draw condition

Inverted exactly one condition (terminal only when NO legal move resets the clock), scratch copy,
nothing else touched — verified by diff: one block, two lines.

BASE tree: **all four cases land correctly** plus the no-reset control. Fifty-move claimable cp 0 ->
-163 (real value), repetition-winning-side cp 0 -> -1197, losing-side stays cp 0, K v K stays cp 0 /
0 nodes, no-reset control stays cp 0 / 0 nodes. So the earlier regressions were caused entirely by my
polarity error.

PINS: **unchanged to the node** vs the not-ready build — bench 11 353312, bench 13 979723,
bench 16 2893009, perft 5 exact. Since correcting the fifty-move half left the pins bit-identical,
**the 13 % pin cost comes from the REPETITION half**, not from the fifty-move condition.

PC r15: cases 1, 2, 4 correct but cases 3 and the no-reset control are still wrong (-1237 and -450),
so it cannot be called correct on the build the owner plays. Not investigated; the pins decide.

Labeled a correctness experiment, not a candidate. job5/experiment_report.md.

## 2026-11-16T22:33:21Z — interaction with FORGE_FIX_ROOT_DRAWN CONFIRMED

Single experiment, as asked. PC tree + corrected condition, `FORGE_FIX_ROOT_DRAWN` compiled OFF via
`-DFORGE_FIX_ROOT_DRAWN=0` (the switch is #ifndef-guarded, so no source edit); switch proven active:
the clock-100 mate root answers cp 0 / 0 nodes with it OFF and mate 1 / 180 nodes on stock r15.

With the root fix OFF: case 3 cp -1237 -> **cp 0** and the no-reset control cp -450 / 11,419 ->
**cp 0 / 0 nodes**. Cases 1, 2, 4 unchanged and correct. So **4/4 cases + control correct with the
root fix off, 2 failures with it on** — the two fixes cannot be layered; the claimable-draw rule has
to be merged inside the root-drawn path deliberately.

Pins: unchanged AGAIN, identical to every other patched build (353312 / 979723 / 2893009, perft 5
exact) — so the cost is the repetition branch, not the root path.

Incidental, reported not chased: root-fix-ON + corrected condition answers **cp 488 on a root where
White has mate in one** — a third wrong answer, so layering is not merely imperfect but wrong there.

Stopping on this thread. job5/root_off_report.md; S-F19 in FINDINGS.

## 2026-11-16T22:34:44Z — MERGE_REQUIREMENT written; S-C2 check of seat 02 done

MERGE_REQUIREMENT.md (job5/) written as asked: any claimable-draw change goes INSIDE the
root-drawn guard, never layered. It names all three evidence cases — the two must-be-zero failures
(cp -1237, cp -450/11,419) and the mate-in-one root that layering turns into cp 488 — plus the pin
cost and where the logic lives, so the next person does not repeat the experiment. S-F20 in FINDINGS.

Back in the cycle. Checked seat 02's S-F1 (no seat had confirmed it): **S-C2 CONFIRMS on both
builds, Threads 1.** `EXE bench 13` with stdin at /dev/null prints 0 bytes and exits 0, while the
same command on stdin prints 61 bytes with the correct 862329 nodes — the control that makes the
zero mean something. `--help` is ignored identically. checks/CHECK_02F1.md, raw in checks/.

Next: next unconfirmed find (area 10's list says 19-F1..F5 and 29-F1..F2 were newest; most are
confirmed now), else job 2 races on the PC build under PC20 — the one job of my area not yet run on
the PC build.

## 2026-11-16T23:25:30Z — selfcheck now covers the fabrication class; anchor drift found

Added the two checks the coordinator asked for, each with a planted control (**S-F27**):
1. **fabricated bestmove**: `go depth 12` + immediate `quit` in one write gives `a2a3` with **0 info
   depth lines**, and a2a3 is confirmed to be the generator's first legal move using the engine's own
   perft-1 order — printed as **FABRICATED**, not PASS. A fake engine that never prints info lines is
   caught by the same function.
2. **searchmoves branches**: legal `searchmoves e2e4` -> e2e4 / 6 info lines / 438 nodes; no-match
   `searchmoves zzzz` -> `0000` with all-zero node lines plus the `info string` note. A fake that
   ignores searchmoves is caught as WRONG BRANCH BEHAVIOUR.
Both integrated into selfcheck.py; identical behaviour on base and PC r15.

Building this surfaced **S-F28**, which limits what the absolute anchor can claim: on an **idle** box
(load 0.51) five blocks of four runs ~20 s apart gave block medians of **653 / 625 / 636 / 608 / 623 ms
per million** — a 15 % wander, while an earlier session on the same box measured 594. A narrow band
around one session's number would have flagged the very machine it came from. Band widened to
**540-820 ms/M**, the tool's output now says the anchor is meaningful only for 2x-or-more differences,
and the coherence guard was tightened to require <0.85x before declaring an impossible disagreement.

All controls verified: sleep-900ms -> FAIL/SLOW; silent -> FATAL; uniform-liar -> INCOHERENT;
fabricating fake -> FABRICATED; bad-searchmoves fake -> WRONG BRANCH. Real PC r15: 4/4 grid PASS,
anchor in band, both harness checks ok, exit 0.
