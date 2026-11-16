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

## 2026-11-16T23:00:41Z FALSE DEFECT CAUGHT IN MY OWN HARNESS — isready during search is HARMLESS
My new test said "isready during a search stops bestmove on BOTH builds, 3/3 cases, 45 s". I did not report it;
I checked it, and it was MY BUG: after sending isready I read until readyok, and the engine's bestmove for the
running search arrives IN THAT SAME BATCH. Measured batch: 'info depth 12 ... nodes 56720' then
'bestmove e2e4' then 'readyok'. My code then waited for a SECOND bestmove that never comes.
=> Seat 19's 19-F14 is right: isready during a search is harmless on base (S14) and on PC r15 (PC20).
Recorded as 04-C4 in FINDINGS.md, with the retraction explicit. No defect claim filed.
This is the second time a gate in my own tooling caught me (the first was check_quit printing PASSED with every
case missing). Both are in the findings file rather than quietly fixed.

## 2026-11-16T23:05:45Z QUIT/EOF ON BOTH BUILDS + isready HARNESS FIXED AND CONFIRMED
04-F19: quit/EOF fault survives on PC r15 under PC20 — not repaired by any of the eight fixes.
  PC r15/PC20 startpos: control d2d4 @ 21,600 nodes / 12 info lines; quit-immediately -> a2a3, 0 info lines;
  EOF -> same. Base/S14 identical in shape (control d2d4 @ 22,459; quit/EOF -> a2a3 @ 0 info).
  So FORGE_FIX_ABORT_PUBLISH does NOT cover the input-termination path.
04-C4 corrected and confirmed after fixing my harness (it had been waiting for a SECOND bestmove; the real one
  arrives in the same read batch as readyok). Corrected result: isready during a search is HARMLESS on both
  builds (PC: bestmove True, 21,600 nodes, 0.23 s; base: True, 22,459 nodes, 0.22 s). 19-F14 stands.
NEXT: explosion numbers on PC20 (the last item on the coordinator's list).

## 2026-11-16T23:06:11Z EXPLOSION ON PC20 — CROSSES THE 10x THRESHOLD, AS A TIME OVERRUN
Extreme FEN, go depth 12, PC r15/PC20, fresh process per run:
  Threads 1: 75,311 nodes, 0.030 s, IDENTICAL 6/6
  Threads 4: 3.05M .. 125.4M nodes (max 1,665x T1); wall 0.21 s .. 7.13 s (max 238x T1); 5 distinct scores in 6
File 6's D1 asks for "no bestmove within 10x the 1-thread time". Here bestmove DOES arrive but the worst run
takes 238x, so it fails the 10x TIME criterion without being a literal hang. I state both readings.
Scope: extreme lost position, bestmove f3f8 never varied, owner's PC is Threads 1 => threaded-use hazard only.

## 2026-11-16T23:06:34Z 04-F21 the fabrication is reachable on the PC match path (go nodes 20000)
PC r15/PC20/T1: go nodes 20000 read normally -> d2d4 after 11 depth lines. Same command with quit written
immediately -> bestmove a2a3 with 0 INFO LINES. Both write patterns fabricate 5/5 (one write with go+quit;
two separate writes, no sleep). Window: quit at 0 ms fabricates; at 1 ms already a real search (g7g6, 5 info
lines); at 200 ms a full 18-line search. => unsafe only if stdin closes in the same breath as go, which is what a naive pipe of the whole script into the engine does.
NEXT: REPORT_quit_path.md, then keep working; FINAL when the window closes at 10:18:50Z.

## 2026-11-16T23:10:24Z 04-F24 BREADTH: PC BUILD CLEAN AT THREADS 8 ACROSS 7..32 PIECES
13 positions (7,9,11,13,15,17,19,23,25,27,29,31,32 pieces), PC r15 TSan build, PC20, Threads 8, depth 10,
fresh process each: 0 TSan reports in 13 searches; every search legal bestmove, no refusals.
Planted control at Threads 8 through the same runner: 3 reports. Combined with 04-F22: 23 TSan searches on the
PC build, 0 reports, with a positive planted control at every thread count used.

## 2026-11-16T23:15:10Z 04-F26 SHARED TT CLEAN AT MAX EVICTION PRESSURE (Hash 1 MB, 16 threads, depth 18)
The TT is what every worker touches, so I hammered exactly that: Hash **1 MB**, Threads 8 and 16, go depth 18,
4 positions (startpos / opening / middlegame / endgame), fresh process each, PC r15 TSan build, PC20:
  0 TSan reports in 8 searches; walls 5.8-40.2 s (genuinely deep); all bestmoves legal; no refusals.
  Planted control at T8 and T16: 3 reports each.
Also a second pass at Hash 16 MB / depth 16 / T8,T16: 0/8.
TOTAL across my TSan work on the PC build: 31 searches, 0 reports — threads 1/2/4/8/16, depths 10-18,
hash 1-16 MB, 7-32 pieces, positive planted control at every thread count used.

## 2026-11-16T23:17:56Z FINAL — seat 04, area 4 (threads and sanitizers), 12-hour run

Builds used, named in every finding line: **base 6b98f217** (`/home/ubuntu/builds/rel/forge`, sha256 in
`honesty/meta.txt`) and **PC r15** (file 5's patch, sha256 verified d6bd72c531f785f4, applied with `patch -p1`
in a separate copy, built with `-DFORGE_MATE_ALPHA_GUARD=1`). Settings named as none / S14 / PC20 throughout.
Sanitizer builds: base and PC under `-fsanitize=thread -O1 -g`, `nm __tsan_` = 21 on each.
Honesty pins on the base build: 312866 / 862329 / 3024920 / 4865609, all four match.
PC build numbers: pins 312866/862329/3024920/4865609, S14 242796/656517, PC20 278024/587276 — all seven match.

### 1. TSan breadth and the shared table (the strongest result of this run)
- **04-F24** — 13 positions spanning 7..32 pieces, **Threads 8**, PC build, PC20: **0 reports in 13 searches**.
  Planted control at Threads 8: 3 reports. (Open.)
- **04-F26** — the shared TT under **maximum eviction pressure**: Hash **1 MB**, Threads **8 and 16**,
  `go depth 18`, walls 5.8-40.2 s, 4 positions: **0 reports in 8 searches**; planted control 3 reports at both
  thread counts. A second pass at Hash 16 MB / depth 16 / T8,T16 was also 0/8. (Open.)
- **04-F22** — first sanitizer pass on the PC build: 0 reports in 10 searches at Threads 1/2/4/8. (Open.)
- Combined: **31 TSan searches on the PC build, 0 reports** — threads 1/2/4/8/16, depths 10-18, hash 1-16 MB,
  7-32 pieces, with a positive planted control at **every** thread count used.
- **04-F25** — the inference: the multi-thread score variance is **not a data race**, it is timing-dependent
  shared-table content. Caveat kept explicitly: TSan sees instrumented code only; I discharged the specific SIMD
  risk by showing the vector stores write per-worker accumulators (`search.hpp:442,507`) and the shared net is
  only replaced after `stop_search()` (`uci.cpp:390-391`). (Open, and as strong as TSan allows.)

### 2. Score-variance guidance for anyone who tunes on this machine
- **04-F12** — survives file 6's D5 only: 20 one-thread runs at each depth 12..16 gave **one identical score per
  depth** (band width **0**), while Threads 4 fell outside it at **all five** depths, deviation
  **26/44/22/22/48 cp**, not shrinking with depth. D1/D2/D3 clean.
- **04-F13** — the practical rule, from measured noise on ordinary positions: sd **17.5 cp**, worst 48 cp, so
  **10 cp needs 48 runs per arm, 20 cp needs 12, 30 cp needs 6**; one run per arm resolves nothing under ~48 cp.
  **Tune at Threads 1**, where this engine is bit-reproducible and the question disappears.
- **04-F19/F21** — the quit/EOF fabrication (19-F12) is **not** fixed by r15, and it is reachable on the match
  path (`go nodes 20000` + immediate quit -> `a2a3`, 0 info lines). **The window is 0 ms**: quit at 1 ms gives a
  real search. So it is a **documentation item** — never pipe a whole script into the engine — not a defect in
  play. The owner's match programs are not exposed.
- **04-F20** — the "explosion" on PC20: T1 75,311 nodes / 0.030 s identical 6/6 versus T4 up to 125.4 M nodes
  and 7.13 s (**238x** the one-thread time). Fails file 6's 10x *time* criterion without being a literal hang;
  both readings stated. Threaded-use hazard only; bestmove never varied.

### 3. The node-budget procedure for the owner's matches
- **04-F16** — exact rule: `go nodes N` finishes the iteration it is in. Budget **equal to a boundary uses 100%**
  of itself; one node below drops a whole iteration (19,831 -> 9,155 work; 19,832 -> 19,832).
- **04-F17** — a fixed round budget **cannot** work: boundaries at/above 20,000 span **20,283-38,996 (1.92x)**;
  at 50,000 they span **53,570-173,222 (3.23x)**. Sending B = 20,000 starves **10 of 10** positions by a whole
  iteration (18-65% of their work).
- **04-F18** — **family grouping does not help**: within-family spread 1.76x-2.02x versus 2.04x across all 30.
- **04-F14/F15** — `go nodes` always **undershoots** (0.61x-0.99x, stops at a finished iteration);
  `go softnodes 2000` **overshoots** to 1.34x. Both deterministic.
- **One page for him: `job3/HOWTO_node_budgets.md`** — the printf command to read a position's boundaries, how to
  pick the at-or-above one, how to feed it to a match script, and the three scripts that do it.

### 4. THE SANITIZER-FLAGS TRAP — read this before building a sanitized PC binary
- **04-F23** — `-DCMAKE_CXX_FLAGS="-fsanitize=thread -g -O1"` **REPLACES** the
  `-DCMAKE_CXX_FLAGS=-DFORGE_MATE_ALPHA_GUARD=1` the PC build requires. The resulting exe answers
  `info string unknown option MateAlphaGuard`, so **PC20 cannot be sent to it at all** and any "PC20 measurement"
  on it measured nothing. The define must go **inside the same CMAKE_CXX_FLAGS string**:
  `-DCMAKE_CXX_FLAGS="-fsanitize=thread -g -O1 -DFORGE_MATE_ALPHA_GUARD=1"`. Verify both with
  `nm -C forge | grep -c __tsan_` (expect 21) **and** `./forge <<< uci | grep -c MateAlphaGuard` (expect 1).
  I lost time to this myself; it will cost anyone else the same hour.

### 5. The PC's real paths, clean
- **04-F27** — the strength-match clock path (6 s + 0.06, Threads 1, PC20): **two full 40-move games, 0
  problems**, every move legal and inside its time, depths 16-24 and 18-30, clocks never run down.
- **04-F15** — `go softnodes 2000` deterministic 10/10 (g7g6, -306, depth 7, 2,671 nodes).
- **04-F26/F24** — no race on any path tested at up to 16 threads.

### What I got wrong, and where it is written down
- **04-F10a — WITHDRAWN.** I framed a varied *move* above Threads 1 as raising severity. File 6 says that is
  design; every move chosen was legal. Kept as an observation only.
- **04-C4 — a false defect I caught before filing.** My first `isready`-during-search test said both builds hung
  (3/3 at 45 s). It was my harness: the running search's `bestmove` arrives **in the same read batch as
  `readyok`**, and my code then waited for a second bestmove. Fixed; corrected result is harmless on both builds,
  confirming 19-F14. I did not file the false version.
- **04-F17 was lost once** to a shell backtick expansion and silently missing from this file for a while; it is
  restored above from the committed raw data, and I verified the ids by script rather than by eye.

### Honest limits
- Every TSan zero is bounded by instrumented-code coverage (see 04-F25's caveat).
- The score variance is characterised, **not fixed** — no patch is offered and none was attempted, per instruction.
- Threads 16 in the original job-1 sweep is incomplete (18/100); it was stopped deliberately so timing work ran on
  a quiet machine, and the later TSan passes cover 16 threads properly.
- All results are from a 4-core machine with the built-in evaluation. The PC's own trained net is not shared, so
  evaluation-dependent results remain questions for the PC.
- No engine source was changed in the repository; no patch is committed; no pull request was opened.

### Files
`FINDINGS.md` (32 lines: 04-F1..F27, 04-C1, 04-C1b, 04-C2, 04-C4, plus the withdrawn 04-F10a),
`REPORT_job1.md`, `job2/REPORT_fixednodes.md`, `job3/HOWTO_node_budgets.md`, `job4/REPORT_quit_path.md`,
`PC_BUILD.txt`, and raw JSONL under `job1/hang/`, `job2/raw/`, `job3/raw/`, `job4/raw/`, `job5/raw/`,
`job6/raw/`.
