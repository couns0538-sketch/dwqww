# P0: reproduce time forfeit
Source: src/search.cpp:561-590,674-676,778-780,1127-1153,1293-1315. STATE.json reports one candidate time forfeit, runner exit 1 and no valid Elo. Hypotheses: missed engine stop deadline or shared-CPU starvation. The frozen exact-position replay is in validation/hourly/2026-10-19-initial/diagnostics/timeout-cold-replay/protocol.json. Status UNTESTED.
