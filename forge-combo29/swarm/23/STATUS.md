# STATUS swarm-23

- seat: 23
- area: 3 (MOVE GENERATION against python-chess)
- branch: for-fable-and-opus/swarm-23
- seed: 2301
- started: 2026-11-16T21:06:22Z

## 2026-11-16T21:06:22Z
Seat claimed. Next: build engine commit 6b98f217 at ../base, run honesty check (bench 11/13/16, perft 5).

## 2026-11-16T21:25:13Z
Done: seat 23 claimed; build at 6b98f217 (Release, x86-64-v4, GCC 13.3.0) honesty 4/4 (bench 11/13/16 = 312866 /
862329 / 3024920; perft 5 = 4865609). HONESTY.txt pushed. Area 3 = MOVE GENERATION.
job1: prediction.txt committed alone before measuring. R_2301.fens = 5000 positions from random legal games
(SEED 2301, one every 7 plies, 367 games), all python-chess valid. Engine perft 1..4 over all 5000: DONE, 26.3 s
(engine_R.jsonl). python-chess reference perft 1..4: RUNNING, 4 parallel workers, ~1150/5000 at 21:30Z.
Note: python-chess 1.11.2 has no Board.perft(); I wrote count()/divide() in pych_perft.py (startpos 1..5 = 20 / 400 /
8902 / 197281 / 4865609 matches the known values).
Board read: handoff FABLE_TO_swarm_1.md read, no STOP, no corrections. No FINDINGS.md yet from any area-3 seat
(03/13/33/53/21 checked) so there is no NEW finding to check this cycle.
Next: finish the reference, run compare_perft.py, write REPORT_job1.md, FINDINGS, push.

## 2026-11-16T21:34:42Z
HARNESS AUDIT after the coordinator's broadcast (19-F12, quit/EOF mid-search -> fabricated bestmove a2a3, 0 nodes):
my harness is NOT affected and no recorded result is invalidated. Evidence, committed, control_quit_midsearch.out:
- A: `go depth 12` + immediate quit -> `bestmove a2a3`, 0 info lines  (broadcast reproduced)
- B: same search, quit after 2 s -> 12 info lines, `bestmove e2e4` at 56,720 nodes  (matches their numbers)
- C: `go perft 4` + immediate quit -> `nodes 197281` (complete)
- D: `go perft 5` + immediate quit -> `nodes 4865609` (complete)
- E: stdin closed right after `go perft 4` -> `nodes 197281` (complete)
- F: a perft run emits 0 `bestmove` lines at all.
Reason: `go perft` is synchronous — the full divide + `nodes N` block is written before the next command is read, so
stdin termination cannot truncate it. My engine_perft.py reads every line up to the `nodes N` line and never sends
quit while a search runs (quit is sent only after the last position, and the runner closes stdin then). Area 3 is
therefore perft-only and outside 19-F12. I do not claim 19-F12 as mine.
TIME WINDOW: working continuously to 22:35 UTC, push at ~22:04Z and ~22:34Z plus at every job part.
job1 reference perft still running: 3571/5000 python-chess positions done (4 workers), engine side finished at 26.3 s.

## 2026-11-16T21:36:18Z
FINDINGS.md pushed now as ordered (2 findings: 23-F1 the 19-F12 boundary is synchronous-perft, 23-F2 python-chess 1.11.2
has no Board.perft()). job1 reference perft 3939/5000 python-chess positions; engine side long done (engine_R.jsonl,
5000 rows, 26.3 s, meta records exe path + sha256 e06310ec... + id name "Chess Engine Forge 6.4.24 candidate").
Next push 22:04Z with the comparison table if the reference finishes; if not, the partial counts + STATUS go anyway.

## 2026-11-16T21:36:50Z  CHECKPOINT (owner: findings on GitHub by 22:30, pushes every 30 min)
Done since last block: FINDINGS.md on GitHub with 23-F1, 23-F2 and now 23-F3.
Seat-19 NaN warning acted on: compare_perft.py rewritten with an integrity contract (no .get() into a comparison,
every depth key and every count asserted integer, a 0-position comparison is a HARD FAILURE, totals always printed
with "positions actually compared: N of 5000", and the word CONFIRMS never printed). Proved with
integrity_selftest.sh: 7 malformed cases all exit 2 HARD FAILURE, the clean case exits 0. integrity_selftest.out
committed. Re-audit of my other parser (engine_perft.py): it does not grep a printed value at all — it reads the
"nodes N" line and RAISES if the engine dies or if a line contains unknown option / invalid value / invalid FEN /
illegal move; a missing nodes line cannot become 0 there.
job1: python-chess reference 4045/5000 (still running, ~10 more min), engine side 5000/5000 done in 26.3 s.
Next: finish reference, run compare_perft.py, write REPORT_job1.md, add the perft verdict finding, push by 22:30.

## 2026-11-16T21:42Z  JOB 1 COMPLETE — perft 1..4 over 5000 positions, 0 mismatches
Reference finished 21:40Z (5000/5000). compare_perft.py: 5000 of 5000 compared, 0 differences at depth 1/2/3/4.
Node totals engine == reference: 154284 / 4744101 / 154034311 / 4974073896 (sum 5,151,986,592 per side).
REPORT_job1.md written (prediction scored: P1/P2/P4/P5 held, P3 KILLED — actual 4.97e9 above my 3.0e9 bound,
reported as measured, prediction not edited). Findings on GitHub: 23-F1, 23-F2, 23-F3, 23-F4.
Next: job 2 of area 3 (500 special positions filtered by python-chess: castling over an attacked transit square,
en passant that would expose the king, capture-promotion with check, double check, pinned piece capturing its
pinner) — perft 1..4 on each. Prediction goes in first, alone.

## 2026-11-16T21:52Z  JOB 2 COMPLETE (deadline push)
Filter C1..C5 over 5,000 R + 353 G: 58 distinct positions (C1 17, C2 0, C3 23, C4 1, C5 17). NOT 500 — these
two position sets do not contain 500; reported, not padded (that is in the report as "not done").
Engine vs python-chess perft 1..4 on all 58: 0 mismatches, 2067 / 65776 / 2358146 / 77220237 nodes per side.
C2 (ep pin) EMPTY from random play -> built 3 positions by hand, VERIFIED by python-chess (ep capture
pseudo-legal but illegal), plus a negative control: engine omits the pinned capture in all 3, emits it in the
control. Findings 23-F5, 23-F6 added; REPORT_job2.md written.
Final answer for area 3 so far: the move generator agrees with python-chess on 5,058 positions at perft 1..4
with 0 differences, and handles the pinned ep capture of hand-built positions correctly.
Next if time remains: area 3 job 3 (perft 5 on 200 R positions + first 30 of G); prediction first, alone.

## 2026-11-16T21:53Z  JOB 3 RUNNING + 23-C1
job3 prediction committed alone. startpos perft 5 = 4,865,609 (P1 HELD). Engine side DONE: R200 perft 1..5 in
35.1 s, G30 in 4.1 s (engine_R200.jsonl, engine_G30.jsonl).
python-chess reference at depth 5 costs ~43 s PER POSITION here, so 200 R over 4 workers is ~36 min: RUNNING,
writes each position as it finishes. Expected finish ~22:20Z. G30 reference may not fit before 22:30 — will be
reported as not done if so, with the engine-side numbers it does have.
Also done: 23-C1 CONFIRMS 30-F6 (position-then-ucinewgame loses the position: Ruy Lopez 27 nodes -> 20 after
ucinewgame -> 27 again with ucinewgame first; two consecutive positions without ucinewgame = 27 then 20). My own
harness is safe, it sends ucinewgame once at startup before any position — checked in engine_perft.py.

## 2026-11-16T22:05Z  CHECKPOINT 2 + seat-10 rule checked (23-F7)
Seat 10's warm-state rule acted on and ANSWERED: `go perft` gives the SAME count twice in one process —
startpos perft 4 twice = 197281 / 197281, perft 5 twice = 4865609 / 4865609, a mid-game FEN twice =
750862 / 750862, A-B-A = 750862 / 197281 / 750862. So perft is TT-independent and every perft table I have
published (job 1's 5000 positions in one process, job 2's 58, job 3's 230) STAND as cold-equivalent.
The control proves the harness is not blind: same harness, same build, two `go depth 12` in one process give
56,720 nodes then 4,951 — seat 10's numbers exactly. (My first attempt at that control pipelined `go depth 12`
twice and closed stdin, returning two `bestmove a2a3` with 0 nodes — seat 19's fault — and would have proved
nothing; I replaced it with a draining runner. Both are in perft_repeat.out.)
Also: 23-C1 CONFIRMS seat 30's 30-F6 with a boundary (only the position-then-ucinewgame ORDER is damaged;
my harness sends ucinewgame once at startup and is safe, verified 27 then 20 on two consecutive positions).
job3: engine side COMPLETE (R200 perft 1..5 = 200/200 rows in 35.1 s, G30 = 30/30 in 4.1 s). startpos perft 5 =
4,865,609 exact. python-chess depth-5 reference: 4 workers, 20+ min in at 99 % CPU each, rows buffered so they
flush only at process exit; expects to finish ~22:21Z. If it does, the comparison is pasted and pushed by 22:30;
if not, REPORT_job3.md already says the depth-5 comparison is NOT DONE and I claim nothing about it.

## 2026-11-16T22:18:41Z CONTINUE: 12 more hours, ends at 2026-11-17T10:18:41Z
Seat kept: 23 (from ~/swarm_seat.txt), branch for-fable-and-opus/swarm-23, folder forge-combo29/swarm/23/.
Next: fetch handoff/fable-opus-combo29-all-20261114, read every FABLE_TO_swarm_N.md not yet read (read 1 already),
lowest N to highest; file 5 holds the PC engine source as a patch against 6b98f217 and must be built in a
separate copy with -DFORGE_MATE_ALPHA_GUARD=1 and its known bench numbers checked.

## 2026-11-16T22:22Z PC BUILD ACCEPTED + job3 depth-5 partial
PC r15 build from FABLE_TO_swarm_5: patch sha256 d6bd72c531f785f4... VERIFIED before applying (a truncated
extraction that drops the trailing newline gives 61da918e... and silently loses the last line — I hit that and
re-extracted). Applied with `patch -p1` to a separate worktree /agent/repos/pcbase, 11 files, no fuzz. Built with
-DFORGE_MATE_ALPHA_GUARD=1. All EIGHT known numbers of file 5 match exactly: none 312866/862329/3024920/4865609,
S14 242796/656517, PC20 278024/587276, zero unknown-option/invalid-value lines. Record: PCBUILD.txt.
THREADS RULE: every result I have recorded is Threads 1 — perft does not split across threads and none of my
harnesses ever sends a Threads option (checked by grep over all my scripts). No score of mine is provisional.
job3 depth 5: 150 of 200 R positions compared at depth 5, **0 mismatches**, 5,098,723,948 nodes per side; 50
positions and the 30 G positions still to do. Report updated to say exactly that.
Next: finish the job3 depth-5 reference, then re-run my own finds on the PC build under PC20 (file 5's order).

## 2026-11-16T22:32Z PC20 RERUN OF MY FINDS — all three new findings
job4 (prediction committed alone first, job4/prediction.txt). Threads 1, Hash 16 throughout.
- 23-F9: PC r15 build under PC20 has an IDENTICAL move generator to base 6b98f217. perft 1..4 over the same
  5000 R positions = exactly 154284 / 4744101 / 154034311 / 4974073896, 0 mismatches vs python-chess; pinned-ep
  positions 4/4/8 and control 5 on both builds; perft repeatable twice in one process on the PC build too.
  So every area-3 result transfers to the PC unchanged.
- 23-F8: the PC build STILL fabricates `bestmove a2a3` on `quit`/EOF mid-search (0 info depth lines) — file 5's
  FORGE_FIX_ABORT_PUBLISH fixes `stop` (12 info lines, e2e4; depth 14 -> 14 lines) but NOT input termination.
  So 19-F12 is NOT repaired on the PC's engine.
- 23-F10: planted control for my perft zeros — same script, same data, one node added to one reference row is
  caught (1 mismatch, 218150726 vs 218150727); a deleted depth key exits 2 HARD FAILURE. My zeros are measured.
job3 depth 5 now 198/200 reference rows written.

## 2026-11-16T22:35Z  jobs 3+4 done, 23-C2 confirms seat 03, G30 depth-5 reference running
Done since last block:
- job3 COMPLETE: perft 5 on all 200 R positions = 0 mismatches, 7,399,207,740 nodes per side (23-F11);
  REPORT_job3.md corrected from "not done" to the real result. G30 (30 positions) depth-5 reference running now.
- job4 COMPLETE: REPORT_job4.md. 23-F9 (PC20 movegen identical to base), 23-F8 (19-F12 NOT repaired on the PC
  build: quit/EOF still gives bestmove a2a3, 0 info lines; stop is fine), 23-F10 (planted control: +1 node caught,
  missing key exits 2).
- 23-C2 CONFIRMS seat 03's S-F5: my own harness + my own engine on THEIR 230 FENs, depths 1..5 = 1150/1150 pairs
  equal, sums 5644/137090/4013465/119698590/3925995728. And a warning worth spreading: my perft-5 total (7.40e9)
  vs theirs (3.93e9) is NOT a contradiction — different seeds (mean branching 31.59 vs 24.539) and their 30 G
  positions add 1.02e9 alone; perft sums may only be compared by FEN identity.
Threads 1 everywhere; no score of mine was ever taken above Threads 1.
Next: finish G30 depth 5, then check another unconfirmed NEW finding (seat 13's S-F2 special positions is the
nearest unclaimed candidate for area 3), then job 1 of my area again with SEED+10 per THE CYCLE (c).
