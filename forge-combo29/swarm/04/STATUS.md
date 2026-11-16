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
