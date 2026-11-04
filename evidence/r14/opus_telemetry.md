# R14 finish (Opus): gate and training telemetry

Read-only checks before substantial work and about hourly (AGENTS.md / R14 plan: a sustained >10 % throughput
reduction throttles owned work). Times are Vienna wall time (PC clock).

Baseline for the npt trainer (C:\forge_nnue_train\runs, train it/s per epoch from npt_try1.log): runs s44-s46
(made while other Idle work used CPUs 0-1) 9.13-10.76 it/s, typically about 9.9 it/s (15:00-17:00 per epoch).
Throttle line: sustained below 8.9 it/s.

| Vienna | npt run s47, epochs (it/s) | gate (folder, games per 10 min) | owned work running |
|---|---|---|---|
| 2026-11-04 09:39 | ep0 9.85, ep1 11.26, ep2 11.48, ep3 10.04, ep4 9.04, ep5 9.18; ep6 at 60 %: 9.53 | uhoE3b_evaloptimism40_r6k_vs_AL1lp: 65-75 (08:40-09:30), 431.7 games/h, 0 forfeits | r14_overlap production04 (CPU 3, Idle, started 09:37) |
| 2026-11-04 10:38 | npt not running (s47 ended ~09:48-10:12; keeper STATUS unchanged since 09:48) | gates and self-play stopped by the owner (CPUs 4-15 idle at 10:06) | r14_overlap production04 (CPU 3, file 027 at 10:37); owner GPU window for the 30-h job (trainer CPUs 4-5: running loss 0.013669, 2802990 pos/sec) |
