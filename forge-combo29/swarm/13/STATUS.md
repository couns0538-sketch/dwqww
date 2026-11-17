# STATUS seat 13

## 2026-11-16T21:07:41Z

seat    13
branch  for-fable-and-opus/swarm-13
folder  forge-combo29/swarm/13
area    3 (move generation against python-chess)
seed    1301
base    6b98f2170a3210e71beed04bbd2553972c253ed7

HONESTY: all four pins MATCH (312866 / 862329 / 3024920 / 4865609). Build used.
Build: /home/ubuntu/b/rel/forge, g++ 13.3.0, -march=x86-64-v4, sha256 e06310ec...
Next: area 3 job 1 -- perft 1..4 on 5,000 R positions.

## 2026-11-16T21:24:45Z

DONE area 3 job 1: perft 1..4 on 5,000 R positions (SEED 1301). 20,000/20,000 pairs equal, 0 differences.
Controls both pass (published perft values reproduced; planted 1-node error caught by the checker).
Report: job1/REPORT_job1.md. Finding S-F1 written (null result, NEW).
Times: engine side 12.2 s, reference side ~850 s wall over 4 shards.
Next command: cd forge-combo29/swarm/13 && tail -1 STATUS.md   # then start area 3 job 2 (special positions)

## 2026-11-16T21:25:40Z

DONE check of 21-F1: CONFIRMS. Own harness, 5 cases, all hold. checks/CHECK_21F1.md.
Consequence noted: the brief/Opus "impossible castling is accepted" line does not hold at 6b98f217.
Next command: cd forge-combo29/swarm/13 && git log --oneline -1

## 2026-11-16T21:36:16Z

HARNESS AUDIT after coordinator broadcast of 19-F12 (fabricated bestmove on mid-search quit):
- Reproduced 19-F12 myself on my build: pipelined `go depth 12` + `quit` -> `bestmove a2a3`, 0 info lines;
  same search read to bestmove -> `e2e4` nodes 56720. Real, and it is seat 19's finding, not mine.
- AUDIT of my own harnesses: job1/job2 engine_perft.py read stdout to `nodes` after every command and
  send `quit` only at the end -> NOT affected. job2/divide_check.py and checks/check_21f1.py use
  `subprocess.run(input=...)` pipelining.
- TESTED whether pipelining invalidates them: perft is SYNCHRONOUS on this build. Pipelined
  `go perft 6` = 119060324 = interactive `go perft 6`; pipelined perft 5 = 4865609; pipelined
  bench 13 = 862329. The fabrication fires on ASYNC SEARCH `go nodes/depth` + quit, not on perft.
- So job1/job2 perft results and all perft-based findings STAND on this evidence; honesty pins re-checked.
- Re-running the honesty pins interactively anyway (no mid-search stdin close); script
  honesty/recheck_interactive.py committed.

Next command: python3 honesty/recheck_interactive.py ~/b/rel/forge

## 2026-11-16T21:38:30Z

INTEGRITY AUDIT written: INTEGRITY_AUDIT.md. Three of my own faults found and fixed:
1. 19-F12 reproduced (pipelined quit + async search -> fabricated `bestmove a2a3`). Tested: perft and
   bench are SYNCHRONOUS and unaffected (pipelined perft 6 = 119060324 = interactive). My perft
   results and S-C1 stand. Honesty pins re-run interactively: ALL FOUR MATCH.
2. job1/compare.py silently SKIPPED missing records -> an empty reference file would print "0
   differing". Now raises on empty/missing/nan/short input and refuses to pass with 0 pairs compared.
   Four planted-fault controls prove it fails when it should.
3. job2/ref_par.py merged STALE /tmp shard files after I rebuilt the set -> invented 1,929 phantom
   differences. Ground truth checked directly: engine matched python-chess (33/36/32), stale file did not.
   ref_par now uses a fresh tempdir and checks shard exit codes + record counts, refusing to write
   output on any mismatch.
CONSEQUENCE: my earlier job2 "0 differences" was INVALID and is void. job2 is being re-run from scratch
with hardened tooling; the report will carry the re-run numbers only.
Job2 re-run in progress now (reference perft, 4 shards).

Next command: cd forge-combo29/swarm/13/job2 && python3 compare.py raw_engine.txt raw_ref.txt special500.fens comparison.md 494

## 2026-11-16T21:42:17Z

DONE area 3 job 2 (re-run, valid this time): 494 special positions, perft 1..4.
  1,976 pairs compared, 0 differing. Divide check: 0 of 494 root-move-set differences,
  0 per-move-count differences, 0 class-property failures.
  Report job2/REPORT_job2.md. Finding S-F2 added.
  Coverage stated honestly: ep-exposing = 7 only (all that exist in the pool); the "rook destination
  attacked" class cannot exist (same square as king transit) and is replaced by rook-PATH attacked (77).
Next command: cd forge-combo29/swarm/13/job2 && python3 divide_check.py ~/b/rel/forge special500.fens special500.tsv /tmp/div

## 2026-11-16T21:44:11Z

DONE check of 27-F2: CONFIRMS. checks/CHECK_27F2.md. Boundary at N=26 confirmed both ways, with a
big-N sanity control and a state control. (This is distinct from 19-F12: this one happens with a
finished search under a tiny budget, 19-F12 with a search cut short.)
Job3 (perft 5, 230 positions) engine side done, reference side running.
Next command: cd forge-combo29/swarm/13/job3 && python3 compare.py raw_engine.txt raw_ref.txt all230.fens comparison.md 230

## 2026-11-16T22:04:32Z

WARM/COLD AUDIT after seat 10's rule:
- I never used `Clear Hash` anywhere (`grep -rn "Clear Hash" --include=*.py` in my folder: no hits).
- My perft measurements do run many commands in one process, so I tested whether perft varies with
  state: 3 consecutive `go perft 4` on startpos in ONE process all answered `nodes 197281`
  (count of correct answers = 3/3), identical to a fresh process. Perft is a pure tree walk and does
  not use the TT, so my perft tables are valid warm or cold.
- My searches (check_21f1 case nodes, 27-F2) each start with `uci`/`isready` and the 27-F2 table is
  explicitly labelled and includes a warm-vs-fresh control row set - it is labelled there, not hidden.
- NO node-count table of mine is a cross-search warm comparison: the only search node numbers I
  report are single-search values (56,720-style) or per-position cold values.
Job3: engine perft 4+5 on 230 positions done (all OK); reference running, 1 shard left.
Next command: cd forge-combo29/swarm/13/job3 && python3 compare.py raw_engine.txt raw_ref.txt all230.fens comparison.md 230

## 2026-11-16T22:04:54Z

DONE area 3 job 3: perft 4 AND 5 on 230 positions (200 R + first 30 of G).
  460 pairs compared, 0 differing. Engine perft-5 total 4,380,654,195 nodes, 20.2 s.
  Reference finished in 1301 s (my prediction wrongly said it would not finish - recorded in the report).
  Report job3/REPORT_job3.md. Finding S-F3 added. Area 3 jobs 1, 2 and 3 are all complete.
Next command: cd forge-combo29/swarm/13 && git log --oneline -1   # cycle: back to (a) look for unconfirmed findings

## 2026-11-16T22:05:38Z

DONE check of 19-F23: CONFIRMS. checks/CHECK_19F23.md. bench is warm-immune (5x862329 in one
process = 5 separate), mechanism verified by opening uci.cpp:611/617 and search.cpp:2679; contrast
measured: go depth 12 in one process = 56720 / 4951 / 4516, fresh = 56720.
Area 3 jobs 1, 2, 3 complete. Checks: S-C1 (21-F1), S-C2 (27-F2), S-C3 (19-F23).
Next command: cd forge-combo29/swarm/13 && git log --oneline -1

## 2026-11-16T22:13:42Z

CYCLE step (c): job 1 repeat started with next seed. job1b/ = 5,000 positions from SEED 1311,
harnessed with the HARDENED compare.py/ref_par.py.
  Engine side DONE: 20,000/20,000 records OK, 12.3 s.
  Reference side RUNNING (4 shards, ~15 min expected, same as the first run).
  Prediction committed before measuring (prediction.txt), including the "what differs" note the brief asks for.
Blocker for the 22:30 push: the reference pass has not finished yet; if it does not finish I will push
the engine-side counts and label the comparison NOT DONE rather than guess.
Next command: cd forge-combo29/swarm/13/job1b && python3 compare.py raw_engine.txt raw_ref.txt R_1311.fens comparison.md 5000

## 2026-11-16T22:18:02Z

DONE job 1 repeat (cycle step c), seed 1311: 20,000/20,000 pairs compared, 0 differing, 612 s ref.
  Report job1b/REPORT_job1b.md, with the required "what differs from the first run" section.
  Finding S-F4 added.
AREA 3 STATUS: jobs 1, 1-repeat, 2, 3 all complete. Checks: S-C1 (21-F1), S-C2 (27-F2), S-C3 (19-F23).
  Findings: S-F1, S-F2, S-F3, S-F4 (all move-generation agreement; no engine defect found in my area).
Next command: cd forge-combo29/swarm/13 && git log --oneline -1

## 2026-11-16T22:18:15Z

DONE divide-check control (from seat 06's S-F22): planted a compensating error in a real perft-2
divide (+1 a4a3, -1 a5b4) so the TOTAL stayed 1265 -> my move-by-move check caught both, a
totals-only check would have passed. job2/DIVIDE_CONTROL.md, finding S-C4.
IMPORTANT LIMIT STATED THERE: my perft 3/4/5 comparisons are totals only.
Next command: cd forge-combo29/swarm/13 && git log --oneline -1

## 2026-11-16T22:19:12Z CONTINUE: 12 more hours, ends at 2026-11-17T10:19:12Z

Seat 13 kept (from ~/swarm_seat.txt), branch for-fable-and-opus/swarm-13. No new seat taken.
Plan: (1) read every unread FABLE_TO_swarm_N.md from lowest N up, including file 5 (PC build source);
(2) build the PC build in a SEPARATE copy with -DFORGE_MATE_ALPHA_GUARD=1 and check its known bench numbers;
(3) re-run my own finds on BOTH builds under settings PC20, labelling each finding with build + settings;
(4) THE CYCLE as before.
Next command: git fetch handoff branch and list FABLE_TO_swarm_*.md

## 2026-11-16T22:20:45Z

READ ALL FABLE FILES: 1 (earlier), 2, 3, 4, 5 in full. Applied what they say:
- File 3's castling correction = exactly my S-C1 (21-F1). Good, no conflict.
- File 4: pins are DEFAULT-option numbers, sums are S14 numbers. My pins were default -> valid.
- File 2 Rule 1 (a zero needs a planted one): my job1/job1b zeros have the planted-nan/empty/truncated
  controls in job1/control.md and the hardened compare.py controls; job2 has DIVIDE_CONTROL.md.
- PC BUILD DONE: patch sha256 prefix d6bd72c531f785f4 verified, 11 files patched with no fuzz,
  built with -DFORGE_MATE_ALPHA_GUARD=1. ALL KNOWN NUMBERS MATCH: none (312866/862329/3024920/4865609),
  S14 (242796/656517), PC20 (278024/587276). pcbuild/PCBUILD.md + pc_build_check.txt.
- Threads 1 + Hash 16 now sent explicitly in every run per the swarm rule.
Both builds live: base /home/ubuntu/b/rel/forge, PC r15 /home/ubuntu/b/pc/forge.
Next command: build the per-divide perft 4 check (closes my own stated totals-only limit)

## 2026-11-16T22:23:25Z

JOB 4 (closing my stated totals-only limit) IN PROGRESS: perft 4 with a PER-DIVIDE comparison of
every root move against python-chess, on 200 R positions, on BOTH builds (base + PC r15) and under
both regimes (none, PC20). Threads 1, Hash 16 sent explicitly everywhere.
  Rule-1 control DONE first (job4/CONTROL_DIVIDE.md): identity NOT flagged; compensating +1/-1 with
  the total unchanged (197281) CAUGHT; missing move CAUGHT; extra move CAUGHT.
  Run order: base_none -> base_pc20 -> pc_none -> pc_pc20. base_none engine side done (200/200),
  python reference comparing (the slow part).
STALE-SHARD WRITE-UP DONE as its own document (see internal/ report path in my message).
Next command: cd forge-combo29/swarm/13/job4 && cat status.txt

## 2026-11-16T22:47:15Z

DONE job 4 (the coordinator's first new job): perft 4 at the DIVIDE level, 200 R positions.
  base Threads1/Hash16 : 5,182 root moves, 0 differing
  PC r15 Threads1/Hash16: 5,182 root moves, 0 differing
  PC r15 PC20          : 5,182 root moves, 0 differing
  base + PC20          : CORRECTLY REFUSED (base exe does not advertise CuckooRep etc.)
  Rule-1 control passed first: identity not flagged; compensating +1/-1 with total unchanged
  (197281) CAUGHT; missing CAUGHT; extra CAUGHT.
  Report job4/REPORT_job4.md; finding S-F5. My stated totals-only limit is now closed for depth 4.
READ FABLE 6: perft treated as done/transferable. Priority moves to the PC path. Next: suggested new
area -- go softnodes N on PC build under PC20, Threads 1: determinism, finished depth, overshoot.
Next command: cd forge-combo29/swarm/13/job5 && python3 softnodes.py

## 2026-11-16T22:49:33Z

DONE suggested area (FABLE 6): go softnodes on PC r15 + PC20 + Threads 1 + Hash 16.
  DETERMINISTIC 63/63 (each case run twice in separate fresh processes; also identical across two
  separate script invocations). STOPS AT A FINISHED DEPTH 63/63 (proven by re-searching each position
  with `go depth <the depth reached>` and requiring the same node count). Rule-1 control: 5 plants
  flagged as different, 2 identity cases correctly not flagged.
  OVERSHOOT: median 22-29 % past N; worst 409,130 past a 250,000 budget = 164 % = 659,130 nodes on
  one move of a real game position. Findings S-F6, S-F7. Report job5/REPORT_job5.md.
Next command: cd forge-combo29/swarm/13 && git log --oneline -1   # cycle: look for unconfirmed finds on the PC path

## 2026-11-16T22:58:23Z

DONE job 6 (coordinator job 1): perft 4 at the DIVIDE level on 200 REAL-GAME G positions.
  base Threads1/Hash16 : 5,107 root moves, 0 differing
  PC r15 Threads1/Hash16: 5,107 root moves, 0 differing
  PC r15 PC20          : 5,107 root moves, 0 differing
  Rule-1 control re-run on G material: compensating +1/-1 with total unchanged at 743,255 CAUGHT;
  missing CAUGHT; extra CAUGHT; identity not flagged.
  Sample = fixed stride over all 353 G positions (not the first 200), proportions checked.
  Finding S-F8. MOVE-GENERATION CHAPTER CLOSED at depths 1-4, divide granularity, both material
  types, all three build/settings combos; stated limits: depth 5 totals-only, python-chess is the
  only oracle, refused-FEN positions untestable this way. Report job6/REPORT_job6.md.
Next: PC path per file 6 (job 7), own limit stated (12 G positions, not the owner's match games).

## 2026-11-16T22:58:54Z

DONE job 7 (coordinator job 2, PC path per file 6): go nodes at the three match budgets + 2,000.
  DETERMINISTIC 48/48 (each run repeated, separate fresh processes). BUDGET RESPECTED 48/48 as a HARD
  CAP (worst 96 nodes under). Legal bestmove 48/48. Rule-1 control: 6 plants caught, 2 identities not.
  Median depth: 6 @2k, 10 @20k, 12 @50k, 16 @250k. Utilisation 0.68 -> 0.83.
  CONTRAST with S-F7: softnodes overshoots up to 164 %, go nodes never exceeds.
  Checked rather than assumed: position 7's -284 -> -1364 jump at 250k is a REAL black promotion
  (PV verified legal move by move), not a bug.
  Finding S-F9. LIMIT STATED: 12 G positions, not the owner's match games.
Next command: cd forge-combo29/swarm/13 && git log --oneline -1

## 2026-11-16T22:59:42Z

DONE CLOSURE NOTE: MOVE_GENERATION_CLOSED.md (one page, as asked). What it says:
  - 6 jobs, 6 material types, depths 1-5, divide granularity at depths 2 and 4 on THREE build/settings
    combos (base Th1/Hash16, PC r15 Th1/Hash16, PC r15 PC20).
  - 11,124 position-set entries = 10,482 distinct FENs; 42,436 totals-granularity pairs + 10,783
    divide-granularity root moves compared; 0 differences anywhere.
  - The four limits, stated: depth 5 totals-only; python-chess is the only oracle; refused-FEN
    positions untestable this way; sampling (R synthetic, G = 200 of 353).
  - Explicitly NOT concluded: move generation is not move choice.
  - The line: MOVE GENERATION IS CLOSED as of 6b98f217 and PC r15.
VERIFIED RATHER THAN TYPED, and it caught two things:
  (a) my first aggregate "5,494 distinct positions" was a guess and WRONG; real value 10,482 distinct
      (11,124 entries, sets overlap). Fixed.
  (b) job 1's comparison.md came from the OLD silent-skip checker and had NO denominator, so it could
      not prove its own 20,000. I re-ran the hardened checker over job 1's committed raw files:
      20,000 of 20,000 compared, 0 differing -> job1/comparison_hardened.md now supersedes it.
  Every aggregate in the note is now the pasted output of closure_verify.py (closure_verify.txt).
Next command: cd forge-combo29/swarm/13 && python3 closure_verify.py   # then PC path with remaining time

## 2026-11-16T23:00:36Z

DONE job 8 (remaining PC path): the owner's clock mode, 6 s + 0.06 s, PC r15 + PC20 + Threads 1.
  4 games x 20 plies = 80 clocked moves with real clock state carried move to move.
  0 overruns, 0 illegal moves. BUT only 4.1 % clock utilisation (median 207 ms of 6,000), median
  depth 19, ~1.84 M nodes/s. Allocation scales with the clock (6s->0.36s, 30s->1.28s, movestogo 40->88ms).
  Deterministic in nodes/depth/move (650,246 / depth 19 / e2e4 five times); only wall time moves +-2ms.
  Recorded as a QUESTION not a defect: using 4 % of the clock may be leaving strength on the table, but
  it may be deliberate, and the owner's PC is slower than this idle 4-core VM so his utilisation differs.
  Finding S-F10. Report job8/REPORT_job8.md.
MOVE GENERATION DECLARED CLOSED in MOVE_GENERATION_CLOSED.md (aggregates verified by closure_verify.py).
Next command: cd forge-combo29/swarm/13 && git log --oneline -1

## 2026-11-16T23:01:08Z

Cycle continues on the PC path. Next job closes a gap I named myself in job 7: "all 12 positions
scored cp, none mate, so the mate-score path at these budgets is untested here".
Job 9: forced-mate positions at the PC's three match budgets (PC20, Threads 1, Hash 16): does a
reported mate score imply a mate actually reachable in 2M-1 plies (M>0) or 2|M| plies (M<0),
verified by replaying the PV, and is it stable across 20000/50000/250000?
Next command: cd forge-combo29/swarm/13/job9 && python3 mates.py

## 2026-11-16T23:11:55Z

DONE job 9 (closes a gap I named myself in job 7: mate scores were untested on the PC path).
  21 positions (14 mate-in-1, 3 mate-in-2, 2 mate-in-3, 2 deliberate no-mate controls), true
  distances computed exhaustively in python-chess. 3 budgets = 63 runs.
  57 positive mate claims, 0 not delivered by the engine's own PV, 0 distance disagreements,
  0 illegal bestmoves, 0 score changes between budgets. mate 1/2/3 delivered at plies 1/3/5 exactly.
  Rule-1 control: real claim accepted, 4 planted failures (claim too short, truncated PV, illegal PV
  move, empty PV) all rejected.
  Finding S-F11. NOT covered and stated: negative mate scores; mates deeper than 3; elementary endings only.
Next command: cd forge-combo29/swarm/13 && git log --oneline -1

## 2026-11-16T23:16:49Z

DONE job 9b: closes the NEGATIVE mate gap I declared open in job 9.
  6 real lost G positions (side to move down >= 700cp) x 2 budgets = 12 runs.
  4 negative mate claims, 4/4 CORRECT: opponent forces mate within 2|M|-1 plies (exhaustive python-chess)
  AND the engine's own PV mates at exactly that ply (-3 -> ply 6, -4 -> ply 8).
  8 large negative cp scores (-245..-3669); 0 non-negative scores in any lost position.
  I DID THIS WRONG FIRST: my initial check reused the positive-mate predicate and reported all 4 as
  WRONG. The engine was right and my test asked the wrong question (for mate -M the OPPONENT forces
  the mate). Recorded in NEGATIVE_MATES.md because it is the same failure class as the stale shard:
  a checker that cannot tell "engine wrong" from "my check wrong", here inventing a false engine defect.
  Finding S-F12.
Next command: cd forge-combo29/swarm/13 && git log --oneline -1

## Mon Nov 16 11:17:48 PM UTC 2026

JOB 10 (reproduction attempt for another seat's under-reported mate at go nodes 20000): NO HIT.
  27 boards (21 job-9 mate + 6 job-9b lost) x 5 reps x 2 disciplines = 270 runs, all at go nodes 20000.
  200 mate claims, 0 under-reported, 0 boards affected. Detector control: 6/6 correct (real claim
  passes; too-short claim, truncated PV, empty PV, illegal PV all flagged; cp is not a claim).
  Full determinism: 0 of 54 board x discipline groups varied across reps; 0 node-count variation;
  fresh vs shared process agreed on all 27 boards.
  This does NOT refute their 2-of-14: my boards are not theirs, and mine are elementary mates that
  solve trivially at 20k. Most likely reason for the clean sweep, stated as a suspicion: the defect
  needs a HARD mate at that budget, which my reference set cannot verify cheaply.
  My own control mistake, recorded: first version picked a mate-in-1 board where 3 plants were
  indistinguishable, and it reported failures. Fixed by using a mate-in-2 board.
  Finding S-F13. Report job10/REPORT_job10.md.
Next command: cd forge-combo29/swarm/13 && git log --oneline -1   # then FINAL at the 12-hour close

## Mon Nov 16 11:18:59 PM UTC 2026 PROVISIONAL FINAL — NOT THE CLOSE

**The 12-hour window ends 2026-11-17T10:19Z, so about 11 hours of work remain after this block.** I am
writing this now because the coordinator asked for it, but it is a snapshot, not the close: I continue
working and will write the real FINAL at 10:19Z. Nothing here is retracted later without a note.

### Move generation: CLOSED
See MOVE_GENERATION_CLOSED.md (aggregates produced by closure_verify.py, not typed). The chapter needs
no further perft work on commit 6b98f217 or PC r15.

### Every finding of mine, with state, build and settings

| id | what | state | build | settings |
|---|---|---|---|---|
| S-F1 | perft 1-4 agree with python-chess on 5,000 R positions (seed 1301), 20,000 pairs, 0 differences | open (not independently confirmed) | base 6b98f217 | default, Threads 1 |
| S-F2 | 494 edge-case positions agree at perft 1-4 (1,976 pairs) and perft-2 divide (494), 0 differences | open | base | default, Threads 1 |
| S-F3 | perft 4 and 5 agree on 230 positions (460 pairs), 0 differences, 4.38e9-node walk | open | base | default, Threads 1 |
| S-F4 | job 1 reproduces on an independent seed 1311 (20,000 pairs, 0 differences) | open | base | default, Threads 1 |
| S-F5 | perft 4 at DIVIDE level on 200 R: 5,182 root moves, 0 differences | open | base + PC r15 | Threads 1/Hash 16 (+PC20) |
| S-F8 | perft 4 at DIVIDE level on 200 real-game G: 5,107 root moves, 0 differences | open | base + PC r15 | Threads 1/Hash 16 (+PC20) |
| S-F6 | go softnodes is deterministic (63/63) and stops at a finished depth (63/63) | open | PC r15 | PC20, Threads 1, Hash 16 |
| **S-F7** | **softnodes overshoots its budget up to 164 % (659,130 nodes on a 250,000 budget)** | **CONFIRMED by seat 01 (S-C8) and seat 02 (S-C9), both to the node** | PC r15 | PC20, Threads 1, Hash 16 |
| S-F9 | go nodes is deterministic (48/48) and a HARD cap (48/48, never exceeded) | open | PC r15 | PC20, Threads 1, Hash 16 |
| S-F10 | clock 6s+0.06s: 0 overruns, 0 illegal, but only 4.1 % clock utilisation (median 207 ms) | open; recorded as a QUESTION not a defect | PC r15 | PC20, Threads 1, Hash 16 |
| S-F11 | 57/57 positive mate claims delivered by the engine's own PV in exactly the claimed plies | open | PC r15 | PC20, Threads 1, Hash 16 |
| S-F12 | 4/4 negative mate claims correct (opponent forces mate within 2 abs(M)-1 plies) | open | PC r15 | PC20, Threads 1, Hash 16 |
| S-F13 | NO under-reported mate at go nodes 20000 over 270 runs / 27 boards (bounds another seat's 2-of-14) | open (a bound, not a refutation) | PC r15 | PC20, Threads 1, Hash 16 |
| S-F14 | DEPTH-64 CLAMP: a proven mate reports depth 64 at ~1,152 nodes on a 20,000 budget | open | base AND PC r15 | Threads 1/Hash 16, and with MateAlphaGuard on and off |
| S-C1 | CONFIRMS 21-F1 (impossible-castling FEN is REFUSED; 8,902 is stale startpos; python perft 3 = 8,802) | my check, own harness | base | default |
| S-C2 | CONFIRMS 27-F2 (go nodes N<26 gives a2a3 with 0 info lines; N=26 gives d2d4) | my check, own harness | base | default |
| S-C3 | CONFIRMS 19-F23 (bench is warm-immune: 5x862329 in one process; mechanism verified in source) | my check, own harness | base | default |
| S-C4 | beyond 06-F22: divide check CATCHES a compensating error (total unchanged at 1,265) | my control | base | default |

### Method notes (the two traps, worth more than some of the results)

1. **The depth-64 clamp (S-F14).** When a mate is proven the engine keeps emitting `info depth` up to
   64, adding ~18 nodes per line, and stops there using 5.8 % of a 20,000-node budget. Identical on both
   builds and with MateAlphaGuard on or off; absent on non-mate boards. Consequences: "depth reached"
   is a sentinel rather than a depth on any board with a mate; a latency harness that gates on depth
   records a falsely fast time exactly where it thinks it is measuring deep search; and a table that
   averages depth over mixed positions compares a number with a constant. Rule: treat depth >= 64 as
   "mate proven", never gate timing on depth, and time by nodes or clock.

2. **A control that disagrees with itself is a signal, not a nuisance.** I hit this twice.
   (a) In job 9b my first negative-mate check reported all four claims WRONG; the engine was right and
   my predicate was wrong -- for `mate -M` the OPPONENT forces the mate, so the positive-mate predicate
   cannot be reused. (b) In job 10 my first under-report control used a mate-in-1 board, where "claim
   mate 1, PV mates at ply 1" is genuinely correct, so three plants were indistinguishable and showed
   as failures. Both times the tell was the same: the control failed in a way that pointed at the
   engine rather than at the test. Rule: when a control "fails", suspect the control first, and check
   that the plant is actually distinguishable from the pass case before believing either.

3. **A tool fault that fabricates differences** (internal/stale-shard-fabrication.md in the project
   store): shards keyed by NAME rather than content hash invented 1,929 phantom engine differences
   after I rebuilt a position set. Fixed by keying on the content hash, asserting record counts, and
   refusing to report a pass when zero pairs were compared. Job 2's first result was voided and re-run.

### What I did not do
Sanitizer runs (not my area); depth-5 divide (justified by cost, agreed); matching against the owner's
own match games (I do not have them -- my real-game material is 12 and 200 positions from set G);
strength measurement of the clock-utilisation question in S-F10, which needs a match another seat has
specced; and any third perft oracle beyond python-chess.

## Mon Nov 16 11:19:14 PM UTC 2026

CORRECTION TO MY OWN TIMING: I first wrote the FINAL block at 22:19Z believing the 12-hour window was
closing. It is not — the window ends 2026-11-17T10:19Z, so ~11 hours remain. I relabelled that block
PROVISIONAL FINAL and continue working. Recording the mistake rather than quietly deleting it: an early
FINAL would have stopped the work eleven hours short, which is exactly the failure the owner's
"do not stop early" instruction is about.

S-F7 is now CONFIRMED BY TWO OTHER SEATS with their own harnesses, to the node:
  seat 01 S-C8: reproduced 163.7 % / 659,130 nodes / depth 17 / g5h5 on my worst-case position.
  seat 02 S-C9: reproduced my three worst cells exactly (659,130; 514,093; 612,735) and corrected its
  own wider range using my data. So S-F7 counts under the swarm rule (a find counts when another seat
  confirmed it with a harness of its own) — it does not need to stay "open" in my table.
Next command: cd forge-combo29/swarm/13 && git log --oneline -1

## Mon Nov 16 11:25:31 PM UTC 2026

S-F7 STATE UPDATED to "CONFIRMED by seat 01 (S-C8) and seat 02 (S-C9)", both reproducing my numbers to
the node, as the swarm rule requires.

S-F14 CORRECTED AND STRENGTHENED (was too narrow). I had said "when a mate is proven the engine reports
depth 64". Further testing shows 64 is a hard CAP ON THE DEPTH COUNTER, reachable by any search that
climbs that far:
  mate-in-1, go nodes 20000 -> 64 lines, depth 64, nodes 1152 (5.8 % of budget)
  same board, N=200 -> depth 11 (198 nodes); N=500 -> depth 27 (486); N>=1152 -> depth 64 always
  mate-in-3, go nodes 250000 -> ALSO depth 64 (106,199 nodes) and does NOT stop (no bestmove in 25 s)
  non-mate board, go depth 70 -> climbs normally (29 lines in 25 s), never reaches 64
  identical on base and PC r15, MateAlphaGuard true and false.
Hazard: depth 64 is not a depth; a depth-gated latency harness returns falsely fast on any board that
hits the cap; go depth D with D>64 can never be satisfied.
AND: my first published reproduction one-liner was WRONG — it piped `quit` straight after `go`, which is
19-F12, and printed 0 info lines. A clean-looking zero that measured nothing. Fixed in CLAMP.md with the
working form (sleep before quit, or read to bestmove). Both traps now demonstrated in one file.
Next command: cd forge-combo29/swarm/13/job10 && python3 clamp.py ~/b/rel/forge

## Mon Nov 16 11:26:15 PM UTC 2026

CLAMP.md reproduction section RESTRUCTURED so a reader cannot copy a broken command: the working form
(and `clamp.py`, which reads to bestmove) now comes FIRST, and the pipe-and-quit form is quarantined
under an explicit "DO NOT USE" heading with its real output (0) shown and labelled as the 19-F12
fabrication trap, not as evidence the cap is absent. The required discipline is stated in one line:
read to bestmove or sleep before quit.
Verified after editing, on BOTH builds: correct form prints 64, wrong form prints 0.
Next command: cd forge-combo29/swarm/13 && git log --oneline -1

## Mon Nov 16 11:35:17 PM UTC 2026

CLAMP.md reproduction section reordered as asked (working form + clamp.py FIRST, the pipe-and-quit form
quarantined under "DO NOT USE" with its real output 0 shown and labelled as the 19-F12 fabrication trap).
Verified after editing on BOTH builds: correct form 64, wrong form 0.

THEN I TESTED THE CAP'S CONSEQUENCE AND CORRECTED MYSELF AGAIN. I had written that `go depth D` with D>64
"can never be satisfied". That is WRONG: measured on PC20/Threads 1/Hash 16, `go depth 65` and `go depth
70` both return `bestmove a1a8` in 0.00 s, clamped at reported depth 64. So such a request does not hang
the engine; it only hangs a HARNESS that waits for depth D to be reached. job11/DEPTH_CAP_ADDENDUM.md,
and CLAMP.md now carries the correction with a pointer.

A HARNESS BUG OF MINE found on the way, recorded in the addendum: my first depthcap.py used select() on a
text-mode pipe, which loses lines already sitting in Python's buffer. It produced non-monotonic
nonsense — `go depth 60` timing out while `go depth 63` answered in 0.00 s, and `go depth 10` timing out
on a 0.01 s position. Replaced with a reader thread; results became monotonic. The tell was results
contradicting themselves (a deeper request answering faster), which means the instrument is broken.
The pre-fix run is kept at job11/out/ so the bad table can be inspected.
Next command: cd forge-combo29/swarm/13/job11 && python3 depthcap.py ~/b/pc/forge /tmp/dc 15

## Mon Nov 16 11:36:33 PM UTC 2026

JOB 12: are the PC's six options wired? Yes for all six, but OwnBook is only CONDITIONALLY active:
  5 of 6 change behaviour on my probes (bench 11 and depth-12 searches); OwnBook changed nothing.
  Root cause in source: src/uci.cpp:679-681 gates the book on `game_search` = clock or movetime only,
  so `go depth` (analysis) never consults it. My probes used go depth, which is why it looked inert.
  On the GAME path the effect is large and I measured it:
    startpos go movetime 200: OwnBook true -> e2e4, 0 info lines, ZERO search; false -> 16 depth lines.
    startpos go wtime 6000...: true -> e2e4; false -> d2d4 (DIFFERENT MOVE).
    walking a game with movetime 100: the first 16 plies were ALL book moves, zero search.
  Consequences for the owner's matches: a book-on match and a book-off match measure different things;
  go-depth probes can never detect a book problem; and a book answer emits NO info lines, so a harness
  that waits for `info depth` mis-classifies it (third trap of the same family as S-F14 and 19-F12).
  Finding S-F15. Report job12/REPORT_job12.md. Not a defect, and I say so.
Next command: cd forge-combo29/swarm/13 && git log --oneline -1

## Mon Nov 16 11:37:10 PM UTC 2026

WROTE THE THREE-CASE NOTE as asked: internal/absence-of-output-traps.md in the project store, covering
depth-64 (S-F14), quit-mid-search (19-F12) and book-move-no-info-lines (S-F15), with the shared tell
("the output reports what it did, not what you asked for; the disagreement is the signal") and a
four-question checklist. All three cases RE-VERIFIED on the PC build before writing: case 1 -> bestmove
a2a3; case 2 -> 64 info lines; case 3 -> book move e2e4 with no info depth lines.
Also added a short pointer at forge-combo29/swarm/13/HARNESS_TRAPS.md so a reader in the repo finds the
note, with the three verified commands.
Note (a) from the last job stands as the answer to a question several seats were circling: all six PC20
options change bench 11 and/or the depth-12 searches, so none of them is inert.
Next command: cd forge-combo29/swarm/13 && git log --oneline -1

## Mon Nov 16 11:37:53 PM UTC 2026

JOB 13: is the built-in book's play good by the engine's own judgement? (follows S-F15)
  Of the 16 book plies: book move = engine move on 4, differs on 12. But the score gap at EQUAL depth 12
  is median 0 cp, range -26 to +18 cp, and NONE is >=50 cp worse. So the book plays different-but-
  equivalent moves; no evidence it walks into trouble.
  Method note: compared at equal depth by playing each candidate and searching the reply at go depth 12,
  rather than comparing the two clock searches' own differing depths.
  LIMITS stated: one book line only; depth 12 is shallow; this is NOT a strength claim and says nothing
  about whether a book-on match scores better or worse.
  Corrected my own first pass: "16 comparisons / 12 disagreements" had mixed in the 4 post-book plies;
  the statistics are over the 16 book plies only.
  Finding S-F16. Report job13/REPORT_job13.md.
Next command: cd forge-combo29/swarm/13 && git log --oneline -1

## Mon Nov 16 11:38:46 PM UTC 2026

JOB 14: verified FABLE file 6's headline claim — the PC build REPAIRS the drawn-root defect. All 9 checks hold:
  halfmove 100: base 0 nodes, plays a1b1, MATE MISSED | PC 144 nodes, mate 1, a1a8
  halfmove 150: same | genuine THIRD-OCCURRENCE root: base 0 nodes mate missed | PC finds it
  controls: both builds find the mate at halfmove 0 and 99; both find it at TWO occurrences;
  both still answer K vs K at once (0 nodes) — so the repair did not overshoot.
  Finding S-F17. Report job14/REPORT_job14.md.

TWO MISTAKES of mine in this job, both caught by asserting the construction rather than the result:
  (1) first case E used a bare `position fen` — a FEN carries no occurrence history, so the case tested
      NOTHING and "passed";
  (2) second attempt used `position ... moves` but keyed the repetition count on the FULL FEN, whose move
      counters change each shuffle, so it reported 1 occurrence for a real 3-fold. My own guard fired.
  Now keyed on pieces+side+castling+ep like the engine, and the guard permanently refuses to run the case
  unless the position is genuinely on the board three times.
  Lesson recorded: a test that PASSES FOR THE WRONG REASON is harder to spot than one that fails, because
  expected and observed agree. Assert the input construction, not just the outcome.
Next command: cd forge-combo29/swarm/13/job14 && python3 drawroot.py ~/b/rel/forge ~/b/pc/forge /tmp/dr

## Mon Nov 16 11:39:27 PM UTC 2026

ADDED CASE 4 TO THE TRAPS NOTE (coordinator's request): "a test that PASSES FOR THE WRONG REASON",
from job 14's drawn-root verification.
- internal/absence-of-output-traps.md is now "four traps with one shared tell", with case 4 in full: the
  bare-FEN attempt (no occurrence history, so the case could never fail) and the full-FEN-string count
  (counters advance each shuffle, so a real 3-fold counted as 1).
- The generalising fix is stated as a rule: ASSERT THE INPUT CONSTRUCTION, not just the outcome — the
  position really occurs three times (counted as pieces+side+castling+ep, the way the engine counts), the
  halfmove clock really is >=100 and did not reset, the search really ran (nodes>0), a `book move` line was
  really present.
- Extended the shared tell accordingly: when expected and observed AGREE on a test that could not have
  failed, that agreement is not evidence either.
- Made the note internally consistent for four cases (title, intro, "three of the four bit me directly",
  checklist item 1b, and the cross-reference, which now calls stale-shard-fabrication a FIFTH shape —
  a fabricated presence rather than an absence).
- Updated the repo-side pointer forge-combo29/swarm/13/HARNESS_TRAPS.md to the same four cases + the
  construction-assertion rule.
Next command: cd forge-combo29/swarm/13 && git log --oneline -1

## Mon Nov 16 11:40:25 PM UTC 2026

JOB 15: which of the PC patch's seven fixes are actually ACTIVE? Read the `#define` defaults in the
patch itself rather than a summary. Findings S-F18:
  ON : ROOT_DRAWN (verified S-F17), HARD_LIMIT_EMERGENCY, BARE_KING_LMR_CAP, GO_PARSE, ISREADY_PENDING
  OFF: FORGE_FIX_BARE_KING_ONE_THREAD (0 since 16:30) and FORGE_FIX_ABORT_PUBLISH (0 since 16:45)
       each with the patch's own measured reason; the gentle LMR_CAP replaces the former. A reader who
       assumes "the patch fixes abort-publish / one-thread bare-king mates" is wrong — it does neither.
  VERIFIED WORKING: GO_PARSE. `go wtime btime 50` -> base 1 info line / 26 nodes / depth 1; PC 5 lines /
       1001 nodes / depth 5. Control `go wtime 50 btime 50` -> IDENTICAL on both builds, so the
       difference is the malformed line, not a general search difference.
  CONSISTENT-BUT-NOT-ISOLATED: HARD_LIMIT_EMERGENCY (11ms and 10ms behave the same on both builds).
  UNTESTED and said so: ISREADY_PENDING (needs NNUEArch, not advertised here) and the full
       BARE_KING_LMR_CAP missed-mate sweep (needs 400 lone-king positions with warm history).

MY OWN TEST BUG, recorded: my first K+R vs K FEN was STATUS_OPPOSITE_CHECK (black in check, white to
move), so the engine REFUSED it, kept startpos, and "answered" e2e4 — which looks exactly like an illegal
move in a KRK ending and was my fault. SIXTH member of the absence-of-output family: the refusal message
was present but the board silently stayed the old one. Guard added: verify the FEN with python-chess
(is_valid and no OPPOSITE_CHECK) before comparing builds, or you compare two searches of startpos.
Next command: cd forge-combo29/swarm/13/job15 && python3 pcfixes.py ~/b/rel/forge ~/b/pc/forge /tmp/pf

## Mon Nov 16 11:41:05 PM UTC 2026

ADDED CASE 5 to the traps note: an illegal FEN refused while the OLD board keeps answering (S-F18,
job 15). Distinct from cases 1-4 because the engine DOES tell you and the wrong answer is still
plausible: my K+R vs K FEN was STATUS_OPPOSITE_CHECK, the engine refused it, kept startpos, and
answered e2e4 — which reads as an illegal move from a KRK ending. Guard: verify each FEN is accepted
(python-chess is_valid() and not STATUS_OPPOSITE_CHECK) before comparing anything about its answer.
Both copies updated and reordered/renumbered consistently: internal/absence-of-output-traps.md
("five traps"), and forge-combo29/swarm/13/HARNESS_TRAPS.md (five rows + the extended
construction-assertion rule, which now includes the FEN-acceptance check).
Next command: cd forge-combo29/swarm/13 && git log --oneline -1

## Mon Nov 16 11:46:11 PM UTC 2026

JOB 16: attempted the BARE_KING_LMR_CAP test. RESULT: NO FINDING, and I am recording it as such rather
than as a pass. 19 verified lone-king mate positions x depth 14 x 2 builds x 2 disciplines (cold/warm) =
76 runs, and EVERY mate was found on BOTH builds (19/19 everywhere, 0 missed).
  That does NOT confirm the fix. With zero misses on the base build there is nothing to improve, which
  means my material does not exercise the fault at all: 14 of the 19 are mate-in-1, found at depth 1
  regardless of pruning. The patch's claim is specific - a QUIET mating move pruned once history tables
  are warm, 38 of 400 missed - and my set has neither hard mates nor genuinely warm histories
  (`ucinewgame` does not necessarily clear the histories).
  Calling this a confirmation would be exactly the vacuous pass I documented as case 4 of the traps note.
  Two generator attempts FAILED and are recorded so they are not repeated: exhaustive mate search to 9
  plies did not finish in the command limit; a "piece two squares away" heuristic produced ZERO mates.
  FORGE_FIX_BARE_KING_LMR_CAP therefore remains UNTESTED (job 15 said so; this does not change it).
  The script now accepts REUSE_POSITIONS=<json> so a seat with a hard lone-king set can get the real answer.
  Report job16/REPORT_job16.md. No finding line added.
Next command: cd forge-combo29/swarm/13 && git log --oneline -1

## Mon Nov 16 11:46:48 PM UTC 2026

JOB 16 report edited per the coordinator's direction — the reusable part is now the summary line:
  "No finding: my 19 positions were too easy (14 are mate-in-1) so zero misses appeared on either build,
  which cannot confirm the fix. The reusable part is loneking.py + its REUSE_POSITIONS=<json> path — any
  seat holding a hard lone-king set can point it at that file and get the real answer in about a minute,
  with cold and warm disciplines and both builds handled."
FORGE_FIX_BARE_KING_LMR_CAP remains marked UNTESTED, with the FOUR REQUIREMENTS set out as a numbered
list and the exact command to run once a hard set exists:
  REUSE_POSITIONS=<hard-set.json> python3 loneking.py ~/b/rel/forge ~/b/pc/forge /tmp/lk 30 14 9
Window noted: ends 2026-11-17T10:18:40Z, about 10 hours out. Continuing at cadence with STATUS every 25
minutes and the real FINAL at the close.
Next command: cd forge-combo29/swarm/13 && git log --oneline -1

## Mon Nov 16 11:48:48 PM UTC 2026

JOB 17: answers S-F10's open question — how does the engine allocate its clock? S-F19.
  ALLOCATION IS DEPTH-STEP QUANTISED, NOT PROPORTIONAL: `go wtime` 10,000 / 12,000 / 15,000 / 20,000 ALL
  give the identical search (depth 23, 1,520,334 nodes, ~800 ms). 8,000 -> depth 19; 30,000 -> depth 25.
  So the fraction used FALLS as the clock grows: 7.9 % at 10 s, 4.0 % at 20 s. Raising the clock from 10 s
  to 20 s changes NOTHING on this position.
  ALSO: `movestogo 0` gives the LARGEST allocation of any cell — 29.3 % of a 6 s clock, depth 26 — versus
  2.4 % with movestogo omitted. If the owner's match tooling emits movestogo 0 the engine thinks hard;
  worth knowing either way.
  Reproducible to ~1 ms, identical node counts across repeats.
  S-F10's ~4 % headline is confirmed in magnitude (2.4-2.7 % on this position vs S-F10's 4.1 % median over
  80 moves on 4 positions); what this adds is that the cause is depth quantisation, not a fixed share.
MY OWN MISTAKE, recorded again: my first timealloc.py PC20 list OMITTED ALL FOURTEEN S14 SETTINGS, so the
  grid measured PC6 while labelling itself PC20 and doubled the allocation figure (457 ms vs the true
  145 ms). Caught by bisecting an unexplained 2x difference; the tell was again a number contradicting its
  neighbours (fraction rising then falling across a monotonic sweep). The script now asserts
  len(PC20)==22. out/ and out2/ are deliberately kept as the mislabelled PC6 runs; out3/ is the corrected data.
Next command: cd forge-combo29/swarm/13 && git log --oneline -1

## Mon Nov 16 11:50:59 PM UTC 2026

SETTINGS-LIST GUARD now STRUCTURAL, as asked (this was the second occurrence, and auditing found a third):
  NEW lib/settings.py: canonical BASE / S14 / PC6 / PC20 with assertions AT IMPORT — lengths 2/14/6/22,
  no duplicate names, and MEMBERSHIP of all 20 named options (a length check alone would pass a list that
  swapped one entry for another). Plus describe(opts) for report-ready labels and check(opts,...) for
  scripts that build their own.
  AUDIT of all 12 list-bearing scripts (lib/AUDIT_settings_lists.md): 10 were already complete. FOUND A
  THIRD INSTANCE: job11/depthcap.py named its 4-option list PC20 (no S14 at all). Fixed to import the
  canonical list and RE-RAN under real PC20: its conclusions HOLD unchanged (go depth 65 and 70 still
  answer with a bestmove, max reported depth still 64, 2 of 4 above-64 requests answered) — the finding
  was structural, so this is measured now rather than assumed. DEPTH_CAP_ADDENDUM.md records the label
  correction and keeps both runs.
  Every PC20 script in my folder now carries `assert len(PC20) == 22`. Verified by smoke-running
  job5/softnodes.py after the edit: reproduces the known overshoot exactly (671/2121).
  Finding S-F20.
Next command: cd forge-combo29/swarm/13 && git log --oneline -1

## Mon Nov 16 11:52:14 PM UTC 2026

JOB 18: is S-F19's clock plateau general or one position's artefact? GENERAL — S-F21.
  5 positions x 11 clock values (1s..60s), canonical PC20 (lib/settings.py, asserted):
    all 5 plateau; 11 clock values give only 6-8 DISTINCT node counts per position.
    QUEEN ENDGAME: identical 1,159,670-node depth-16 search from 4 s ALL THE WAY TO 15 s.
    startpos: 6 distinct counts, 5 plateaus; rook endgame 7 distinct, plateau 6-12 s; tactical 8 distinct.
  Step points DIFFER per position (rook 6-12s, queen 4-15s, startpos 15-30s) — that is why this is an
  allocator property rather than a coincidence of one position. Repeatable: startpos at 10s and 12s gives
  depth 20 / 925,222 nodes six times over.
  PRACTICAL: on such positions, giving the engine 15 s instead of 5 s may change NOTHING about its move,
  so a match set at a generous time control may be measuring the same play as a much faster one.
  NOT claimed: that this costs strength (a search stopping at a finished depth is not handicapped, it just
  does not use the time). Mechanism ("target depth from clock, stop at finished depth") is inferred from
  data + the patch comment, not instrumented.
Next command: cd forge-combo29/swarm/13 && git log --oneline -1

## Mon Nov 16 11:52:43 PM UTC 2026

FRAMING PASS on FINDINGS.md, as asked: "not a defect, no strength claim" is now explicit in the finding
lines most likely to be over-read (S-F10, S-F19, S-F21), and the property findings carry "Property, not a
defect" (S-F6 deterministic+finished-depth, S-F9 hard node cap, S-F14 depth-64 cap). S-F20 is deliberately
NOT framed that way because it IS a fault — in my own tooling, not the engine.
FINDINGS.md now opens with a classification header so a reader can tell at a glance:
  null result / property-not-a-defect / NOT A DEFECT NO STRENGTH CLAIM / confirms-a-fix /
  fault-in-MY-tooling / my checks of other seats.
Table structure verified intact (7 columns per row) after the edits.
FINAL_NOTES.md updated to carry this framing requirement into the close.
Next command: cd forge-combo29/swarm/13 && git log --oneline -1

## Mon Nov 16 11:56:23 PM UTC 2026

JOB 19: measured the match-relevant step of S-F21 — does the TIME CONTROL change the MOVE? S-F22.
  40 real G positions x 4 clocks (2k/6k/20k/60k ms), PC20, Threads 1, Hash 16, winc 60, fresh process:
    2000 vs 6000   : same move 34/40 (85.0 %)
    2000 vs 60000  : same move 31/40 (77.5 %)  <- the LOW end moves differ most
    20000 vs 60000 : same move 39/40 (97.5 %)  <- the TOP of the range barely moves
  SHARP RESULT: across all 240 pairwise comparisons, IDENTICAL node counts ALWAYS gave an identical move
  (6 of 6, zero exceptions) — so the quantisation plateau is literally the same search, not just the same
  amount of work. (Converse not true: 195 of 234 differing-node cases still played the same move.)
  IMPORTANT CORRECTION TO MY OWN FRAMING: "a generous time control may change nothing about the move" is
  right, but the measured rate is ~1 position in 5 differing at the low end — so a time control is NOT
  interchangeable with any other. Recorded explicitly in the report rather than leaving the stronger
  impression standing.
  Still NOT A DEFECT and NO STRENGTH CLAIM: not measured whether the changed moves are better.
Next command: cd forge-combo29/swarm/13 && git log --oneline -1

## Mon Nov 16 11:57:20 PM UTC 2026

FINDINGS.md structure VERIFIED CLEAN by FINDINGS_check.py (exit 0):
  22 S-F rows, all 7 columns; 4 S-C rows, all 6 columns; no missing ids in S-F1..S-F22.
The check caught two things I would otherwise have shipped: S-C3 had 7 columns (should be 6) and S-F12
had been mangled by one of my own earlier escape attempts. Both rebuilt from verified content.
I also briefly mis-set the checker's own expectation (5 instead of 6) and it immediately flagged all four
S-C rows — which is the checker working correctly on a wrong assumption, not the data being wrong. Reverted
and re-run: exit 0.
S-F22 was reordered to LEAD with the 6-of-6 result as asked, with "NOT A DEFECT, NO STRENGTH CLAIM" and the
not-measured note about whether the changed moves are better both retained.
Next command: cd forge-combo29/swarm/13 && python3 FINDINGS_check.py

## Mon Nov 16 11:58:01 PM UTC 2026

ADDED THE TWO INSTRUMENT LESSONS to the traps note, both copies:
  A. "A markdown table is not validated by looking at it" — seven malformed rows from literal pipes in
     shell commands and arithmetic, invisible in a terminal; only a structural check sees it.
  B. "A checker that disagrees with itself is the checker working" — when I mis-set FINDINGS_check.py's
     own expected column count it flagged all four S-C rows, which was the instrument failing on my wrong
     assumption, not four rows failing independently.
  internal/absence-of-output-traps.md is retitled "five traps, two instrument lessons, one shared tell"
  with both lessons in full; forge-combo29/swarm/13/HARNESS_TRAPS.md carries the condensed versions.
  Recorded as S-F23 (method/report) so it is visible in FINDINGS.md too.
Next command: cd forge-combo29/swarm/13 && python3 FINDINGS_check.py && git log --oneline -1

## Mon Nov 16 11:58:05 PM UTC 2026

The new S-F23 row was ITSELF malformed on first write (9 columns — my own text contained pipe characters),
and FINDINGS_check.py caught it immediately. Rebuilt without literal pipes; check now exit 0: 23 finding
rows all 7 columns, 4 check rows all 6 columns, no missing ids. That is the second time in ten minutes the
check has paid for itself, on the very row describing the lesson it enforces.
Next command: cd forge-combo29/swarm/13 && python3 FINDINGS_check.py

## Mon Nov 16 11:59:13 PM UTC 2026

CYCLE STEP (a) — checked an unconfirmed finding: seat 01's S-F8 (over-65535 halfmove/fullmove silently
clamped). Verdict: S-C5 CONFIRMS 01-F8, with the base-vs-PC comparison showing its stated consequence
exactly. checks/CHECK_01F8.md.
  base 6b98f217: halfmove 100 / 65535 / 65536 / 70000 / 300000 ALL give 0 nodes and MISS the mate
    (a1b1 instead of a1a8) — identical behaviour once the counter is >= 100, which is seat 01's claim.
  PC r15: EVERY one of those values FINDS the mate (mate 1, 144 nodes) because the drawn-root repair (S-F17)
    removes the shortcut — so the whole class of absurd-counter FENs is HARMLESS on the owner's build.
  No over-65535 value is ever refused, on either build, across ten FENs covering both fields.
  Acceptance verified by a perft-1 probe with startpos set FIRST: every case gives 17 (the new board's
    legal moves, checked in python-chess) not 20 (startpos) — so the board really was replaced, which is the
    trap that produced a false defect report earlier in this run (traps note case 5).
  STATED LIMIT: the stored value itself is NOT observable from UCI (both 65535 and 70000 are >= 100 and every
    consumer compares against 100), so the uint16 CLAMP is seat 01's source reading, not my measurement; I
    confirm the consequence they state, not the storage width.
  My own slip, corrected: the script printed "mate board gives 38" as the expected perft-1; the true value
    is 17, verified in python-chess. The printed measurement was always right; the comment was wrong.
Next command: cd forge-combo29/swarm/13 && python3 FINDINGS_check.py

## Mon Nov 16 11:59:55 PM UTC 2026

ADDED LESSON C to the traps note, as asked: "the comment can be wrong while the measurement is right —
the inverse of the usual case". In the over-65535 check the printed value `perft 1 = 17` was correct while
my hand-typed annotation beside it said "the mate board gives 38" when it has 17 legal moves. Normally the
number is wrong and the label right, so you read the label and miss the number; here a plausible annotation
lends a trustworthy figure an authority it never earned.
  internal/absence-of-output-traps.md retitled "five traps, THREE instrument lessons, one shared tell";
  HARNESS_TRAPS.md carries the condensed version.
THEN I APPLIED IT rather than only recording it: check_01f8.py now COMPUTES both expectations from
python-chess (startpos = 20, mate board = 17) and prints an explicit verdict ("ACCEPTED (the new board)" /
"STARTED FROM STARTPOS - the FEN was probably refused" / "UNEXPECTED"), instead of a typed annotation.
Re-ran: all three cases read "ACCEPTED (the new board)". No hand-typed expectation remains in that output.
FINDINGS_check.py still green (23 S-F, 5 S-C).
Next command: cd forge-combo29/swarm/13 && python3 FINDINGS_check.py

## Tue Nov 17 12:00:21 AM UTC 2026

Added the generalisation beside the settings rule, as asked, in lib/AUDIT_settings_lists.md:
  "An expected value written inline in an output line is an unverified assertion, exactly like a settings
  list." Same class of object — a hand-maintained claim about what the code should do, sitting beside
  machine output and borrowing its authority — and the same fix: compute the expectation
  (chess.Board().legal_moves.count()) rather than type it, or keep it out of the output.
  Generalized further in the same paragraph: the family is ANY hand-maintained duplication of a fact the
  machine already knows — settings lists, expected values, reference shard paths, option-name spellings.
  Remedy is always: derive from one source, assert the derivation.
Also cross-linked that reasoning from lib/settings.py itself, so a reader of the code finds it; verified the
module still imports and PC20 is still 22.
Next command: cd forge-combo29/swarm/13 && python3 FINDINGS_check.py

## Tue Nov 17 12:01:30 AM UTC 2026

JOB 20: closed the caveat I have carried through S-F19/S-F21/S-F22 — are the clock-changed moves better or
worse? S-F24: BETTER, 4 of 5.
  16 G positions, 2,000 vs 60,000 ms; 5 changed their move. Equal-depth-16 scoring of BOTH candidate moves
  (play it, search the reply, negate — the job-13 technique) rather than comparing the two clock searches'
  own differing depths:
    pos 0  +3 cp | pos 6 +156 cp | pos 7 +58 cp | pos 14 -33 cp | pos 15 +984 cp
    median +58 cp; longer-clock move better in 4, worse in 1, equivalent 0.
    median depth 15 (2 s) -> 24 (60 s): the mechanism is visible in the data.
  The +984 outlier was HAND-VERIFIED: after c6b5 white scores +3231 (black -3231); after h6h5 white +2231
  (black -2231) — both lost for black, but the shallow move walks into ~1,000 cp worse.
  LIMITS: SELF-CONSISTENCY (the judge is the same engine), depth 16 is an arbitrary judge, 5 changed
  positions is a small base, and a score gain is not a game result. NO MATCH RUN, so NO ELO CLAIM.
Next command: cd forge-combo29/swarm/13 && python3 FINDINGS_check.py

## Tue Nov 17 12:02:10 AM UTC 2026

CYCLE STEP (a) — checked seat 16's S-F27/S-F29: S-C6 CONFIRMS BOTH, and SHARPENS S-F27 from 3 to 1.
  Method deliberately different from theirs: FIXED NODE budget (go nodes 4000) instead of a clock, 40 plies,
    fresh process per game, PC20/Threads 1/Hash 16, finals compared on pieces+side+castling+ep.
  Result: 10 games from ONE start -> exactly 1 distinct final AND 1 distinct move sequence (seat 16 measured
    3 distinct finals with a clock). 10 games from 10 different G starts -> 10 distinct finals, 10 distinct
    sequences.
  This DIRECTLY SUPPORTS their proposed mechanism: they attributed the 3-vs-1 residue to millisecond clock
    drift changing the reached depth; removing the clock makes the convergence exact. Obtained by removing the
    suspected cause rather than arguing about it.
  PRACTICAL: a self-play data set from a single start contains ONE game however much compute is spent;
    variety must come from the starts. That is a data-generation rule, not an engine defect.
  LIMITS: 10 games, 40 plies, 4,000 nodes — short and shallow; fixed-node budget only (not fixed-depth, and
    no ucinewgame-between-games variant); checked move sequences as well as finals because identical finals
    alone would not prove identical games.
Next command: cd forge-combo29/swarm/13 && python3 FINDINGS_check.py

## Tue Nov 17 12:03:00 AM UTC 2026

CYCLE STEP (a): checked seat 12's 12-F1 -> S-C7 CONFIRMS it, and the check CORRECTED MY OWN JOB 16.
  CONFIRMED: `ucinewgame` resets the board to startpos. `position fen <K+P>` then go -> e1d2 / 10 nodes;
    `position fen <K+P>`, ucinewgame, go -> d2d4 / 26 nodes (startpos depth 1). Same on both builds.
    Source read at src/uci.cpp:386-389: stop_search(); searcher.clear(); board.set_fen(StandardStartFen).
  BEYOND THE FINDING, and it matters: ucinewgame is a COLD reset — it clears the TT, so three identical
    depth-12 searches give 52,591 / 52,591 / 52,591 WITH it between, versus 52,591 / 27,239 / 21,407
    WITHOUT. So ucinewgame is the cold-start control and NOT a way to obtain a warm search.
  CONSEQUENCE FOR MY OWN WORK: job 16's "warm" arm (one process, ucinewgame between) was never warm — it was
    the same experiment as the cold arm, which is exactly why all 38 cold/warm pairs came out identical. The
    NULL RESULT stands, but the label overstated what was done. REPORT_job16.md now carries an explicit
    correction and no longer claims to have tested warm behaviour.
  AUDIT: all three of my scripts that send ucinewgame send `position` AFTER it, so none is affected by the
    board-reset trap (checks/check_27f2.py, job10/underreport.py, job16/loneking.py).
Next command: cd forge-combo29/swarm/13 && python3 FINDINGS_check.py

## Tue Nov 17 12:03:26 AM UTC 2026

CHECK_12F1.md now states ALL THREE warm runs explicitly rather than summarising them, since the three
values are the evidence:
  with ucinewgame between : 52,591 / 52,591 / 52,591  (bestmove g7g6 each time)
  without (warm table)    : 52,591 / 27,239 / 21,407  (bestmove g7g6 each time)
  i.e. the second and third searches cost 51.8 % and 40.7 % of the first — the reuse is visible in the
  numbers. Both builds identical (out_12f1/ and out_12f1_base/).
  Worth noting for interpretation: the BESTMOVE did not change across all six searches, so the warm table
  changes the COST, not the choice, on this position — which is exactly why a warm/cold harness difference
  can silently corrupt node-count comparisons while leaving moves looking fine.
Scope audit from the same pass stands: all three of my scripts that send ucinewgame send `position` AFTER it,
so none is exposed to the board-reset trap.
Next command: cd forge-combo29/swarm/13 && python3 FINDINGS_check.py

## Tue Nov 17 12:17:13 AM UTC 2026

FULL PROCESS-REUSE AUDIT written: lib/AUDIT_process_reuse.md. And I TESTED my own guess instead of publishing it.
  I first wrote that job17/18/19 were "likely safe because a systematic shift would cancel". WRONG in part:
    job17's OWN cell at go wtime 6000 gives depth 18 / 314,239 nodes single-fresh, but depth 24 / 331,560
    after 10 earlier searches in one process — identical request, different answer. So job17's non-plateau
    depth column is NOT comparable across rows.
  BUT THE HEADLINE SURVIVES: sweeping clocks fresh-per-search, 10,000 / 15,000 / 20,000 ms ALL give
    depth 23 / 1,520,334 nodes identically — the plateau is exactly as S-F19/S-F21 described, verified
    under the strict discipline. So S-F19/S-F21 STAND with a caveat on individual non-plateau cells.
  S-F11 SURVIVES: re-ran mates_run.py fresh-per-search -> 57 positive claims, 0 not delivered, 0 distance
    disagreements, identical to the original. Only incidental bestmoves/cp values differed.
  S-F12 UNAFFECTED: negative_mates.py already spawned a process per call; re-ran -> 4/4 correct, 8 negative
    cp, reproduces exactly.
  S-F24: WITHDRAWN and corrected (1 of 16, +17 cp).
  S-F22: likely safe (bestmoves matched fresh vs warm on the spot check) but NOT re-run -> treat percentages
    as provisional; that re-run is the outstanding item.
GUARD ADDED: lib/freshguard.py — SearchCounter asserts one search per process at result-writing time, refuses
  allow_reuse without a reason, and fails when NOTHING was recorded so a harness cannot pass vacuously.
  Self-test (python3 lib/freshguard.py) covers all five cases; it passes.
  mates_run.py and clockgain.py now use a fresh process per search, structurally.
Next command: cd forge-combo29/swarm/13 && python3 lib/freshguard.py && python3 FINDINGS_check.py

## Tue Nov 17 12:21:05 AM UTC 2026

S-F22 FINISHED UNDER THE STRICT DISCIPLINE — and it REPRODUCED EXACTLY. This was the last item owed on the
clock thread.
  Re-ran clockmoves.py with a fresh process per search, enforced by lib/freshguard.py
  (SearchCounter.assert_single_use). All SIX percentages identical to the original:
    2000v6000 34/40 | 2000v20000 31/40 | 2000v60000 31/40 | 6000v20000 33/40 | 6000v60000 33/40 |
    20000v60000 39/40 — every one the same as before.
  And the sharp result held: in the strict data, IDENTICAL node counts gave an IDENTICAL move 7 times out of 7,
    zero exceptions.
  So S-F22 was never contaminated — its run() always spawned a process per search. It is now STRUCTURALLY
    guaranteed rather than true-by-inspection, and its state is CONFIRMED rather than provisional.
FINAL_NOTES.md now carries the double-own-goal note (two "likely safe" guesses contradicted by five-minute
tests tonight) as the strongest argument for the guard replacing the guess, plus the current corrected state
of S-F24 / S-F11 / S-F12 / S-F19 / S-F21 / S-F22 so the close cannot get them wrong.
Next command: cd forge-combo29/swarm/13 && python3 FINDINGS_check.py && python3 lib/freshguard.py
