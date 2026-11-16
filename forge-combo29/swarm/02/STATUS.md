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

## 2026-11-16T22:58Z — S-F6 mapped across the whole go-keyword family (both builds)
72 ordered pairs of `go X Y 50`, both builds, Threads 1, OwnBook false, fresh process per case.
25 pairs: base HANGS, PC ends -> repaired by FORGE_FIX_GO_PARSE. 23 pairs hang on BOTH -> the fix does not
cover them, so the GUI-side rule (send the side-to-move's clock) is still needed on the PC build.
19 pairs fine on both.
5 pairs LOOKED like PC regressions (base ended in 1 ms, PC kept searching). Investigated: NOT regressions —
the base answer was ONE ply of a 50-ply request (`info depth 1 … cp 350`, 1 info line) because the parameter
was eaten, while the PC build searched to depth 24 / 4.6 M nodes. My 1-second grace window was too short for a
depth-50 search; the automated table alone would have said the opposite. pc_rerun/RESULT.md, raw
go_family_results.json + go_family_regression_check.txt.

PC ASan+UBSan build also done (build-pc-asan, -DFORGE_MATE_ALPHA_GUARD=1 + sanity).
Next: re-run area-2 job 1 and job 3 against the PC build under PC20 (job 1 on the PC ASan build), and check
another seat's unchecked finding.

## 2026-11-16T23:20Z — NEW FINDING S-F7 (both builds, PC20 too): Hash x MultiPV 167x slowdown
Found while chasing two "missing bestmove" lines in the PC job-1 run; they were not hangs but this.
`Hash 2048` + `MultiPV 8`, `go depth 6` from startpos, Threads 1: **7180 ms base / 7108 ms PC**, against 2 ms at
MultiPV 1 — with the SAME 48 info lines, so the engine is not searching more. Cause read in the source:
the extra-PV loop calls `alt_shared->tt.clear()` once per extra line, and `tt.clear()` walks every cluster
(src/search.cpp:372). Measured: one clear costs 172 ms at 2048 MB, and the MultiPV overhead is ~42-47 clears'
worth at 512 MB and above. Confirmed under the full PC20 set on the PC build (16 MB: 51 ms, 2048 MB: 6966 ms).
NOT touched by the PC r15 patch. hash_multipv/RESULT.md + scaling.txt + clear_vs_multipv.json.

## 2026-11-16T23:20Z — PC build job 1 done (2,000 sequences, PC20, ASan)
5,827 `go`, 5,825 `bestmove`, 0 crashes, 0 hangs, 0 sanitizer lines, 0 illegal bestmoves, 0 refused options.
Two sequences flagged "no bestmove": both were the S-F7 slowdown under the 20 s driver timeout, not hangs —
`go depth 6` replayed at 11.5 s in a sequence that had set Hash 1000000000 (clamped to 2048) and MultiPV 8.
Base build had 0 such flags only because its random draw differed. job1_pc/.

## 2026-11-16T23:45Z — S-F7 threshold grid DONE (owner's two questions)
TABLE 1, depth on a 5 s clock (PC r15, Threads 1, 3 runs/cell):
            MPV1  MPV2  MPV3  MPV5  MPV8
  Hash 16   d16   d15   d14   d13   d12
  Hash 64   d16   d14   d14   d10   d9
  Hash 256  d16   d8    d8    d4    d2
  Hash 2048 d16   d1    d1    d1    d1
=> MultiPV 3 at Hash 256 is ALREADY RUINED (d8 against d16). Safe region: MultiPV 1 at any Hash, or Hash <= 16 MB
at any MultiPV. The two knobs multiply; neither is dangerous alone.
TABLE 3, fixed depth `go depth 12`: 31 ms (Hash 16, MPV 1), 40 ms (Hash 2048, MPV 1), **13709 ms** (Hash 2048,
MPV 8) — same depth 12, same result, 343x. So it is also a latency problem for batch analysis, not just a clock
problem. No fix attempted, as instructed.
Next: re-run area-2 job 3 (option sweep) on the PC build under PC20, then check another seat's NEW finding.

## 2026-11-16T23:58Z — S-F7e: the per-line clear is LOAD-BEARING (measured with a control)
Built a scratch variant (/agent/repos/pc-noclear) with exactly `alt_shared->tt.clear()` commented out; the change
is committed as TEXT (hash_multipv/remove_per_line_clear.patch.txt). The variant passes all four honesty pins
identically, so it is a valid build.
Result at depth 8, MultiPV 4, Threads 1, Hash 16: the MultiPV lines DIFFER — with clear cp 73 / cp 68 / cp -18,
without cp 68 / cp 52 / cp -18; bestmove unchanged (d4c5). Control: at MultiPV 1 (the clear never executes in
EITHER build) the two builds are BIT-IDENTICAL, so the difference is the clear and not build variance.
Speed win if removable: depth 12, Hash 2048, MultiPV 8 goes 13.9 s -> 1.1 s (12.6x), MultiPV 1 unchanged.
=> Removing it is a behaviour change needing a match, not a free speed patch; a cheap cluster-local clear must be
validated against the with-clear numbers. I also CORRECTED my earlier reading: I had guessed the surviving entries
were irrelevant, and the no-clear scores moving suggests otherwise.
hash_multipv/RESULT.md, clear_dependency_probe.json.

Next: area-2 job 3 on the PC build (92 options, vs 82 on base — new options to test), then another seat's finding.

## 2026-11-17T00:05Z — owner's real match path measured; NEW S-F9 (distinct from S-F7)
PC20's 22 option names contain NO MultiPV and the engine default is 1 => the owner's match path (softnodes 2000,
nodes 20000/50000/250000, clock 6+0.06) runs at MultiPV 1 and the S-F7 collapse cannot reach it.
BUT S-F9 (new, different mechanism): a fixed NODE budget is DILUTED by MultiPV. `go nodes 20000` d9 at MPV 1 vs
**d3** at MPV 8; nodes 50000 d12->d5; nodes 250000 d15->d10; **softnodes 2000 d7->d1** (a one-ply training label
for the owner's self-play); clock 6+0.06 d19->d10. Hash 16 throughout, so this is budget splitting, not the
table-clear cost. match_path/RESULT.md + raw_rows.txt.

Read FABLE_TO_swarm_6.md in full in the previous block: fifty-move/repetition cp 0 is NOT a defect; multi-thread
score spread is NOT a defect; the owner's path is PC20/Threads 1/softnodes 2000/nodes N/clock 6+0.06.
Next: `go nodes` determinism + the 6+0.06 clock overshoot on the PC path, then another seat's finding.

## 2026-11-17T00:20Z — S-F9/S-F10 resolved: dilution is NOT 1/M, and the safe rule is written
`go nodes 20000`, MultiPV 1/2/4/8, PC20, Threads 1, Hash 16, 3 runs/cell, all deterministic:
MultiPV 1 -> depth 11 (19,832 nodes); MultiPV 2 -> d10; MultiPV 4 -> d8 with only 3 of 4 lines emitted at that
depth; MultiPV 8 -> d7 with only **2 of 8** lines emitted at that depth. The budget is spent LINE BY LINE per
depth, not divided by M, so the search stops MID-ITERATION. Complete line sets: MultiPV 4 through depth 7,
MultiPV 8 through depth 6. S-F10 records the truncated line set; S-F9 remains the depth loss.
SAFE_RULE_selfplay.md states the rule in file 6's terms: **MultiPV 1 always** (softnodes 2000: d7 -> d1 at MPV 8;
nodes 20000: d9-11 -> d3-7; clock 6+0.06: d19 -> d10), and PC20 does not set MultiPV (22 option names, none is
MultiPV; default 1) so the owner's path is already safe unless a GUI leaves a value behind.
`go nodes` determinism: 9 of 9 cells byte-identical across 5 runs.
Also cleaned up: removed two committed .pyc files and three stray empty .txt files from the repo root, added a
.gitignore. Text-only rule now enforced in my folder.

Next: clock 6+0.06 overshoot vs file 6's expectation, then check a seat's NEW finding.

## 2026-11-17T00:52Z — authoritative 20-board clock sample (S-F13) + a correction of my own (S-F14)
4 shape classes x 5 of MY OWN boards, 5 runs each, PC20, Threads 1, Hash 16, 6s+0.06, 100 runs per class.
TABLE 1/2 (median / p99 / worst / worst-as-%-of-clock, median utilisation):
  sparse_few  207.5 / 1585.6 / 1585.8 / 26.2%   3.4%
  sparse_many 353.0 /  696.8 /  701.9 / 11.6%   5.8%
  full_few    197.4 /  516.4 /  575.9 /  9.5%   3.3%
  full_many   303.0 /  545.6 /  542.2 /  8.9%   5.0%
TABLE 3 (the mechanism): wall time IS the last completed iteration's cost — class medians match 0.99-1.00x,
Spearman rho 0.998 over 20 boards, 17 of 20 within 2%. The clock tail is an ITERATION-COST tail.
The exception that matters: `8/8/6k1/Q7/1P4PP/1K3P2/8/8 b` = 1585.6 ms while its last iteration was 667 ms, i.e.
CUT AT THE HARD LIMIT — and that reproduces seat 08's 1585.4 ms to 0.2 ms on a board set they never used.
CORRECTION (S-F14): my class medians order OPPOSITE to 08-F28 (mine sparse_few 207.5 vs full_many 303.0 = 0.68x;
theirs 853.1 vs 161.2 = 5.3x), so I WITHDRAW my S-F12 median-ordering claim and keep only the tail claim. A
5-board class median samples which boards sit near an expensive iteration boundary, not a class property.
clock_6s/CLASS_SAMPLE.md, tail_rows.json, correlation.json.

Next: re-check the hard-limit tail on more sparse boards (is it a rate or a one-off?), then a seat's NEW finding.
