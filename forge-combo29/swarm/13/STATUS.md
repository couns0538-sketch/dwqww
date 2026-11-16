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
