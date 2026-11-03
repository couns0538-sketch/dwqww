# Initial workload observations

Read-only progress observations: health-baseline01.json at 12:48:01 Vienna and
health-baseline02.json at 12:53:20 Vienna on 2026-11-03.

The gate advanced from 182 to 222 completed games: 40 games in 319 seconds,
0.12539 games/second. Training advanced from epoch2 1862/9307 to 3724/9307;
reported rate increased from 9.00 to 9.24 iterations/second. Previous completed
epochs reported 9.67 and 9.93 iterations/second. Current observed rate is within
10% of both. These establish initial progress, not a causal performance claim.

Keep computation to one Idle worker initially. One launcher test was refused
when all admitted CPUs were above 70%; that refusal is retained as resource
evidence, not silently bypassed. A subsequent observation showed CPUs2/3 at
28%/4% busy, confirming load varies. Do not raise priority or admission limits.

Only the exact two progress log files named in the observation receipts were
read; no queue state, controls, runtime imports or workload changes occurred.
At each hourly check compare fresh windows; sustained degradation >10% reduces
owned work. New gate/process identity requires a new baseline.
