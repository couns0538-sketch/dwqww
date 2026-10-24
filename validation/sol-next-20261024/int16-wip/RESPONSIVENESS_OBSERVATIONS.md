# Observations around the failed clocked screen

The original same-binary int16 WAC screen remains **FAILED / INCOMPLETE / UNPOOLED**. It stopped after492 completed positions at ON WAC.193. The engine's late best move was legal but arrived after the5-second watchdog and was not counted. The engine eventually exited0; the runner exited1.

The exact command was observed at16:10:49.581780Z. Depth11 output was observed at16:10:49.627222Z. The observer did not record its5-second deadline until16:11:02.010321Z; a legal best move was observed13.3516seconds after go. The late info line reported52066nodes/time13344, versus the previous25783nodes/time41. These observations do not identify where the delay occurred; the previous info time does not cover unfinished later work.

Two subsequent read-only native commands also exceeded their initial10-second tool wait: a small Python JSON/corpus extraction on CPU2 (session60847), and a `cat` of cgroup CPU files (session39011). Both later exited0. They are observations of delayed responsiveness, not proof of the original engine's CPU/steal/runqueue behavior. Cgroup throttling counters were captured only after the event and are cumulative; they cannot attribute this interval.

Root reported that its heavy QA jobs had closed before16:07:32Z. That does not establish the state of other host activity. No original per-process CPU-time or schedstat baseline survived for the exited failing process, so the original cause remains unresolved.

A separately authorized bounded diagnostic replayed only that exact FEN, with three fresh OFF/ON/OFF processes, the unchanged executable,1000ms movetime and the same5-second watchdog. All three returned the correct legal move b3e3 in about0.991seconds and exited0. It captured observer/all-child-thread schedstats every100ms, cgroup snapshots and child RUSAGE. `diagnostic-wac193/OBSERVATIONS.json` derives the search-window process CPU time separately from whole-child RUSAGE, which includes initialization/teardown. No failure was reproduced in these three cases. That does not change the original failed screen into a passing result or establish a root cause.

No production or WAC-runner source changed, no failed records were filtered, and no replay data is pooled into a WAC or speed result. Further clocked tests require root's resource lease and a new predeclared trial; no NPS test has been launched by this agent.
