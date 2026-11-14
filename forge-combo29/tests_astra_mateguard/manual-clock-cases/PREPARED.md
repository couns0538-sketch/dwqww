# Manual clock commands prepared; no engine runs yet

A compiled C++ helper covers all seven go commands from the unchanged tests_t3/clock_commands.txt, in their original order and with the listed position commands retained. One fresh engine per mode will run the full sequence at Threads 1, Hash 16, OwnBook false and Move Overhead 10. The frozen Release/ASAN binary hashes, original command/parser files, command order, environment and cwd are pinned in preparation-provenance.txt.

The helper uses the existing UCI transport with only a private byte-observer and nonthrowing timed-read extension; its exact patch is retained. Full engine stdout/stderr and submitted stdin are flushed as raw bytes, with monotonic chunk timestamps and the complete transport transcript. It waits for each bestmove before proceeding. Both huge-clock cases receive an explicit stop after the 150 ms checkpoint; actual send/read times and any premature bestmove are recorded. Event-derived observations independently cross-check the helper result.

The file's approximate 70 ms and 1 ms descriptions do not specify wall-time tolerances on a shared VM. Those cases retain measured wall time and engine-reported time without invented pass bands. For the huge-clock cases the concrete observation is no bestmove received before the timed stop, plus normal completion afterward. This observes UCI behavior; scheduling/pipe delays prevent inference of an exact internal engine timestamp.

No separate original t3 report is present in the accepted tree or the introducing commit 92e77995566eee19b72d67d0358e98796829f2c0. Parent confirmed that the exact annotated command file and current clock_parse_test are the authoritative context. No other branches were fetched.

Root can later execute both modes with:

`node /workspace/work/r4-clock-manual/run-clock.mjs --execute-authorized`

Each mode has a 90-second native bound (plus two-second kill grace), 95-second outer bound, 10-second startup bound, five-second response bound and three-second observed shutdown. The controller fixes a 200-second total budget and checks the original global deadline. These are operational bounds, not timing acceptance thresholds. An incomplete mode remains incomplete, never a passing case count. ASAN uses the unchanged plan's ASAN_OPTIONS and UBSAN_OPTIONS. This is command-inventory coverage, not a clock strength match or throughput measurement.

Preparation only: compile with -Wall -Wextra -Werror succeeded without warnings; Node syntax check passed; no native helper or engine was run. Initial build warnings and the corrected final compiler output remain preserved. Exact build/run helpers and inert copies are available for publication.
