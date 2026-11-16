seat: 04
branch: for-fable-and-opus/swarm-04
area: 4
seed: 401

## 2026-11-16T21:06:29Z
seat claimed. next: STEP 2 build of 6b98f217 + honesty check.

## 2026-11-16T21:20:30Z
STEP 2 done: 4/4 honesty numbers match (forge-combo29/swarm/04/honesty/HONESTY.txt). TSAN build built (nm __tsan_ = 21).
Sanitizer proof (1) done: planted unlocked-global counter on a scratch copy at /home/ubuntu/planted (search.cpp:2154)
is reported by TSan through THE SAME RUNNER (job1/planted_proof_raw.txt). Proof (2) done.
job1 running: Threads 1,2,4,8,16 x 100 G positions x depth 12 x 2 reps = 1000 searches, one process each.
Progress: 2026-11-16T21:20:30Z rep1_t1=100 rep1_t1.log= rep1_t2=100 rep1_t2.log= rep1_t4=90 rep1_t4.log= 

## 2026-11-16T21:36:19Z CHECKPOINT PUSH
HARNESS AUDIT after seat 19's warning: my runner (job1/run_searches.py) writes `quit` at exactly one place
(line 91, inside Engine.close()) and only AFTER read_until("bestmove") returned; every search is its own
process. audit_harness.py over the records written so far: 0 records with no node count, 0 with 0 nodes,
0 with a2a3-at-0-nodes, 100 % of bestmoves legal (job1/audit_harness.txt). My job1 records are NOT
pipelined-quit records; no re-run is needed for that reason.
quit/EOF probe (job1/quit_eof.py, CHECK of 19-F12, not my own finding): control A on startpos = e2e4 at
56,720 nodes / 12 info lines; B (`quit` immediately) and C (EOF) = bestmove a2a3 with 0 info lines.
So 19-F12 reproduces on my release build. Full 3-position x 8-case table running now.
job1 sweep (TSAN, Threads 1/2/4/8/16 x 100 G positions x 2 reps): rep1 t1/t2/t4/t8 done, t16 running.
Next command: cd /home/ubuntu/runs && tail -3 stamps.txt; python3 /agent/repos/dwqww/forge-combo29/swarm/04/job1/analyse.py /home/ubuntu/runs

## 2026-11-16T21:54:02Z HANG PRIORITY + CHECKPOINT
HANG INVESTIGATION (coordinator's priority) — verdict: NO deadlock, but a real thread-scaled blow-up.
- Repro: 20 fresh processes, Threads 4, depth 12, FEN 5R2/1p5k/6p1/8/1K6/5q2/8/8: 0 hangs, walls 0.174-69.301 s.
- Threads 1 identical 10/10 at 79,980 nodes / 0.03 s. Threads 4: 2.7M-1.25B nodes. Threads 8: 1.95B nodes / 103.9 s.
  bestmove f3f8 at EVERY thread count => cost blow-up, not a wrong move. Table: job1/table_threads.md
- Stacks (gdb -p, batch, text, 2 captures): all 8 workers inside qsearch/search/pick_best/fill_pseudo_legal/
  make_move, 2 transiting pthread_mutex_lock; main thread in read(0). NONE parked waiting for a split point,
  NONE failing to observe stop. So not the split-point deadlock and not a missed stop — work is being spent.
- TSan at every thread count: 0 race reports in 400 searches, with the planted-fault proof live.
- Depth axis at Threads 4: d10 0.10s / d11 0.17s / d12 0.77s (max 69.3) / d13 2.15s.
COLD-START (seat 10): every hang run is a FRESH process with ucinewgame BEFORE position. I also found the
ordering trap: ucinewgame after position resets to startpos — my first hang probe did that and measured startpos
20 times; discarded and re-run.
INTEGRITY (seat 19): check_quit.py has a gate that refuses a verdict when a field is missing. It caught my own
stale records AND a PASSED-while-all-missing bug in itself; both fixed. Quit re-run in progress.
FINDINGS.md + REPORT_job1.md pushed. Next command:
  cd /home/ubuntu/runs && python3 /agent/repos/dwqww/forge-combo29/swarm/04/job1/check_quit.py /home/ubuntu/runs/quit_rel2

## 2026-11-16T21:58:36Z CORRECTNESS + GENERALITY (coordinator's 3 follow-ups)
STEP 2 (correctness) DONE — the waste DOES change the score. Hang FEN, fresh process each cell:
  Threads 1 d12 = +2188 cp (2/2 runs identical), d14 = +2315 cp (2/2 identical), bestmove f3f8
  Threads 4 d12 = mate 17 / mate 15 (the two runs DISAGREE), d14 = mate 13 / mate 12, bestmove f3f8
  => same bestmove everywhere, but Threads 1 never sees the mate and Threads 4 reports a different
     mate distance on every run at the same depth. Correctness consequence, not only time.
STEP 1 (generality) DONE — the explosion is NOT general. Two same-shape positions:
  6k1/5pp1/8/8/8/8/1q3PPP/6K1 w : 221,942 -> 494,718 nodes (2.2x) T1->T4, <0.06 s
  8/6k1/8/8/8/5q2/5PPP/6K1 w   :  10,385 -> 116,072 nodes (11x)   T1->T4, <0.02 s
  hang FEN                      :  79,980 -> 1,253,000,000 (15,600x)
STEP 3 (aspiration / NullMove) NOT DONE — out of time after steps 1 and 2; recorded as not done.
Table: job1/table_divergence.md. Next command:
  python3 job1/divergence.py /home/ubuntu/builds/rel/forge /tmp/d3 asp --threads 4 --depths 12 --runs 2 --opts AspirationDelta=200

## 2026-11-16T22:00:56Z FINAL — THE FINDING, AND THE TWO NAMED GAPS
THE SENTENCE FOR THE OWNER: at identical settings Threads 4 gives a different mate distance on successive
runs (17 and 15 at depth 12; 13 and 12 at depth 14), and with null move effectively off, three runs gave
+2402 cp, mate 14 and mate 21. A multi-threaded SCORE is not reproducible even when the MOVE is (f3f8 every
time). That is the finding; the node count is only the symptom that exposed it.
STEP 3 DONE, NEGATIVE: AspirationDelta=200 -> +2637 then mate 14; NullMoveMinDepth=10 -> +2402, mate 14,
mate 21. Neither the aspiration window nor null move is the cause. (04-F8)
NOT STARTED, as instructed, each with its exact next command in REPORT_job1.md:
  GAP 1 shape condition:
    python3 forge-combo29/swarm/04/job1/divergence.py /home/ubuntu/builds/rel/forge /tmp/shape bisect \
      --threads 1,4 --depths 12 --runs 2 --fen '5R2/1p5k/6p1/8/1K6/5q2/8/8 b - - 0 1'
  GAP 2 divergence at a fixed NODE count rather than a fixed depth:
    python3 forge-combo29/swarm/04/job1/divergence.py /home/ubuntu/builds/rel/forge /tmp/nodes nodes100m \
      --threads 1,4 --depths 12 --runs 3 --limit 300   (needs a --go variant sending go nodes 100000000)
Files: FINDINGS.md (10 lines: 04-F1..F8, 04-C1..C2), REPORT_job1.md, job1/table_threads.md,
job1/table_divergence.md, job1/table_quit.md, job1/hang/ (raw JSONL + gdb stacks), honesty/.
No source file changed; no patch offered; no PR opened.

## 2026-11-16T22:05:39Z QUIT TABLE NOW GATED AND COMPLETE
quit/EOF check of 19-F12 re-run end to end with the integrity fields; gate prints PASSED
(job1/table_quit_gate.txt, exit 0), table rebuilt from the raw JSONL (job1/table_quit.md).
Answers to the two open questions, now measured rather than inferred:
  Q2 nonzero nodes on a fabricated bestmove: NO — 0 info lines in every fabricated case.
  Q3 illegal move: NO — every fabricated move legal (a2a3 on startpos, d5d4 on the middlegame FEN).
A_control (reads to bestmove, then quits) = e2e4 at 56,720 nodes; B/C/G fabricate.

## 2026-11-16T22:05:46Z STOPPED — deadline reached (per instruction: push and stop at 22:30)
Branch tip reflects: honesty 4/4, TSan build + planted-fault proof, 400-search TSan sweep (0 race reports),
the hang investigation (no deadlock; FEN-specific 15,600x node blow-up), the score-nondeterminism finding,
aspiration/nullmove ruled out, gated quit table confirming 19-F12 with Q2/Q3 answered.
11 FINDINGS lines (04-F1..F8, 04-C1, 04-C1b, 04-C2). No source changed, no patch, no PR.
NEXT COMMAND (gap 2, fixed node count) if this seat is resumed:
  python3 forge-combo29/swarm/04/job1/divergence.py /home/ubuntu/builds/rel/forge /tmp/nodes nodes100m \
    --threads 1,4 --depths 12 --runs 3 --limit 300

## 2026-11-16T22:19:37Z CONTINUE: 12 more hours, ends at 2026-11-17T10:19:37Z
Read FABLE_TO_swarm_2, 3, 4, 5 (1 was read earlier). Rules now in force for me: a zero needs a planted case
through the SAME harness; pins are taken with NO setoption, sums under S14; PC20 = S14 + CuckooRep true,
HistRework 2, TtPruneV2 true, CorrHistV2 true, MateAlphaGuard true, OwnBook false.
PC BUILD DONE: patch sha256 d6bd72c531f785f4 verified, applied with patch -p1 in a separate copy, built with
-DFORGE_MATE_ALPHA_GUARD=1. ALL SEVEN known numbers match to the digit (pins 312866/862329/3024920/4865609,
S14 242796/656517, PC20 278024/587276), no unknown option. See PC_BUILD.txt and pc_build/.
NEXT: re-run my own finds on the PC build under PC20 — first the score-nondeterminism (04-F7), since it is the
finding that matters; then the thread-node blow-up (04-F1); then the quit/EOF fault (04-C1).

## 2026-11-16T22:19:57Z 04-F9: THE PC BUILD SCORE IS NONDETERMINISTIC TOO — 4 runs, 4 scores
On PC r15 under PC20, Threads 4, depth 12, hang FEN, fresh process each run:
  +2576 cp / mate 13 / mate 18 / mate 16   (four distinct scores, four runs)
  nodes 5,008,136 / 7,217,375 / 8,242,575 / 31,386,512
Threads 1 under the SAME settings: +2207 cp in 4/4 runs, 75,311 nodes identical each time.
bestmove f3f8 in every run. So the PC's eight fixes do NOT repair the nondeterministic score, and this is the
engine the owner actually plays. This is the strongest form of 04-F7.

## 2026-11-16T22:20:39Z 04-F10 — IT IS GENERAL AND IT CHANGES THE MOVE
Ordinary middlegame from G, 1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1, PC r15 under PC20,
go depth 12, Threads 4, ten fresh processes: 9 DISTINCT SCORES in 10 runs AND TWO DIFFERENT MOVES
(g7g6 in 7 runs, e5e4 in 3). Threads 1: -293 in 5/5, 31,779 nodes every time.
04-F11: already at Threads 2 — hang FEN, six runs, six distinct scores.
So the "shape condition" question is answered in the negative: it is not a special class of position. The defect
is ordinary middlegame depth-12 search at Threads >= 2, and it reaches move choice.

## 2026-11-16T22:25:24Z FIXED-NODE TEST: IT IS A THREADING FAULT, NOT A DEPTH ARTEFACT
Ordinary FEN 1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b, PC r15, PC20, go nodes 2000000:
  Threads 1: e5e4 / -302 / depth 24 / 1,651,453 nodes — IDENTICAL in 6/6 runs
  Threads 4: e5e4, g7g6, e5e4, e5e4, g7g6, e5e4 with scores -308, -297, -313, -299, -291, -306
             at depths 19, 19, 18, 18, 21, 18 — SIX runs, SIX distinct scores, TWO distinct moves
So at an identical node budget the threads still disagree => threading fault in the search, NOT a depth-limit
artefact. Also note Threads 4 stops at a SHALLOWER depth (18-21) than Threads 1 (24) for the same budget.
RUNNING NOW: go nodes 200000000 at T1 and T4, 10 runs each (slow, ~2 min/run; first T1 run e5e4 -388 d39).
THEN: the base build at Threads 4 (same test), to tell the owner whether this predates r15.

## 2026-11-16T22:40:46Z RE-TESTED F9/F10/F11 AGAINST FILE 6 — SURVIVES D5 ONLY
Ran file 6's own five-test defect check rather than defending my framing.
ONE-THREAD REFERENCE: 20 runs at each of depths 12-16 under PC20 gave ONE identical score at every depth
(-293, -272, -292, -283, -273) — the band is WIDTH 0. Threads 4: outside that band at ALL FIVE depths,
max deviation 26 / 44 / 22 / 22 / 48 cp. The deviation does NOT shrink with depth (26 at d12, 48 at d16),
which is file 6's D5 condition. D1 hang: no. D2 crash: no. D3 illegal: no (40 Threads-4 runs). D4 sanitizer:
not shown (release). => survives D5 ONLY.
WITHDRAWN: my framing that the varied MOVE in 04-F10 was a defect. File 6 says a varied move above Threads 1 is
design; every move it chose was legal. Kept as an observation, not a defect.
CAVEAT I must state: the owner's PC plays Threads 1, where this engine is exactly reproducible. So this is a
hazard for threaded tuning/testing, not for PC games. Priority accordingly low.
NOW PIVOTING to the PC's real path per file 6: PC build, PC20, Threads 1, Hash 16, go softnodes 2000,
go nodes 20000/50000/250000, clock 6s+0.06.

## 2026-11-16T22:41:43Z D5 TURNED INTO GUIDANCE + PC NODE PATH DONE
04-F13 threaded-A/B rule, from measured noise on ordinary positions (hang FEN excluded so as not to overstate):
  sd 17.5 cp, worst 48 cp. 10 cp effect needs 48 runs/arm; 20 -> 12; 25 -> 8; 30 -> 6; 50 -> 2.
  One run per arm resolves nothing under ~48 cp. Practical rule: tune at Threads 1, where this engine is
  bit-reproducible; the problem then does not exist.
04-F14 go nodes on PC build: deterministic, stops at a FINISHED iteration, and always UNDERSHOOTS:
  15k->9,155 (0.61x) 20k->19,832 (0.99x) 30k->19,832 (0.66x) 40k->31,779 50k->31,779 (0.64x)
  70k->52,904 100k->97,289 (0.97x) 250k->170,070 (0.68x). 30k and 20k are the SAME result (both stop after d11).
  So a PC match at fixed go nodes is NOT at a fixed node count; a budget just past a boundary is wasted.
04-F15 go softnodes 2000: deterministic 10/10, g7g6 / -306 / depth 7 / 2,671 nodes (1.34x OVERSHOOT).
NEXT: quit/EOF re-check on PC20, then the explosion numbers on PC20.

## 2026-11-16T22:42:15Z ITERATION BOUNDARIES — the practical match-configuration table
Rule, verified exactly: go nodes N finishes the iteration it is IN. Budget == a boundary uses 100% of itself;
budget == boundary-1 drops a whole iteration. Measured: 19,831 -> 9,155 work (0.46x); 19,832 -> 19,832 (1.00x);
31,778 -> 19,832 (0.62x); 31,779 -> 31,779 (1.00x).
ADVICE: send the boundary value itself, not a round number above it.
ORDINARY FEN 1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b depth 10-17: 9,155 / 19,832 / 31,779 / 52,904 / 97,289 / 121,306 /
  170,070 / 288,912
STARTPOS depth 9-18: 7,131 / 8,569 / 13,604 / 21,600 / 28,565 / 46,854 / 78,579 / 104,892 / 166,281 / 377,485
Both reproducible 2/2 runs. CORRECTION: the six numbers I quoted earlier are the ORDINARY FEN's, not startpos's.
Boundaries are position-specific — derive them per position from the nodes field of each `info depth k` line.
Table: job3/table_boundaries.md. NEXT: quit/EOF re-check on PC20.

## 2026-11-16T22:43:07Z BOUNDARY SPREAD — A FIXED ROUND BUDGET CANNOT WORK (measured)
Ten openings of set O, PC r15/PC20/Threads 1, boundary at or above the target:
  target 20,000 -> boundaries 20,283 .. 38,996 (median 22,612) = 1.92x spread
  target 50,000 -> boundaries 53,570 .. 173,222 (median 62,455) = 3.23x spread  (spread WIDENS with target)
Cost of guessing at target 20,000: B=20,000 -> 0 of 10 positions get full work (all lose an iteration,
18%-65% of their work); B=22,000 -> 5 of 10; B=30,000 -> 9 of 10; B=39,000 -> 10 of 10 but up to 88% over-searched.
So there is NO safe round number. Rule: compute per position, or accept up to 65% under-search / 88% over-search.
This corrects the hope behind the question: the spread is not a few percent, it is 2x-3x.

## 2026-11-16T22:43:52Z FAMILY SPREAD: NO, GROUPING DOES NOT RESCUE A FIXED BUDGET + HOWTO WRITTEN
Ten distinct positions from each of three families (1.e4 e5 / 1.d4 d5 / 1.c4 e5), boundary at/above 20,000:
  A 20,572-36,210 (1.76x)   B 20,631-41,660 (2.02x)   C 20,466-36,767 (1.80x)   ALL 30: 2.04x
Within-family spread == across-family spread, so one budget per family is no better than one global budget:
family max gives full work but over-searches the fastest position by 76% / 102% / 80%.
=> per-position computation is the only correct route. One-page procedure + exact commands:
  job3/HOWTO_node_budgets.md  (scripts: boundaries.py, boundary_spread.py, family_spread.py)
NEXT: quit/EOF re-check on PC20 (still running), then explosion numbers on PC20.
