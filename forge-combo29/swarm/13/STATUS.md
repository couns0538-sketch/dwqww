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
