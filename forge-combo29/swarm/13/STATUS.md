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
