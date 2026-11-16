# FINDINGS - seat 29 (area 9 SPEED), only ever added

| id | area | one sentence | file with the exact command that shows it again | NEW |
|---|---|---|---|---|
| 29-F1 | 9 | `bench 13` spends 38.72 % of its samples in the NNUE + evaluation family and only 2.14 % outside the binary, so the first speed lever is the evaluation path, not search bookkeeping. | `forge-combo29/swarm/29/job1/profile_bench13.sh` (then `summarize_perf.py`) | NEW |
| 29-F2 | 9 | `forge::(anon)::evaluate_position<false>`, the scalar hand-written evaluation, is the single hottest symbol at 16.23 % (run 1; 15.84 % run 2), ~4 points hotter than the NNUE forward pass `apply_and_evaluate` at 12.59 % (13.04 %). | `forge-combo29/swarm/29/job1/profile_bench13.sh` | NEW |
