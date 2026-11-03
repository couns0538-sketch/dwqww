# Initial preflight review

Read-only reviewer inspected PLAN, AGENTS and four setup/observation/input scripts.
Confirmed findings:

1. TickCount64 unavailable on PowerShell5.1: change to Stopwatch ticks/frequency.
2. Hash verifier lacked post-hash disk checks before receipt allocation: add both
   floor checks immediately after hashing and before successful completion.
3. Runtime setup changed parent environment: snapshot/restore in finally required.
4. Runtime setup checked resources only initially: phase admission and monitored
   package processes required before reuse.

Observed runtime setup executed in a disposable shell and installed only below
D:/a14; no parent long-lived environment or protected packages were used. Findings
3/4 still require fixing for reusable script safety. First red preflight/launcher
run retained four failures under evidence/test_logs/r14/preflight-red01.

Interpretation: exactly two external progress logs may be read to satisfy the
user's before/hourly workload checks. This narrow user instruction overrides the
generic skill's protected-log prohibition; no runtime, queues, locks or controls
are accessed. Observations alone do not certify normal throughput.
