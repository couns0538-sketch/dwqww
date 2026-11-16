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
