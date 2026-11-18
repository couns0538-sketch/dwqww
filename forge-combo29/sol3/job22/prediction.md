# Job 22 prediction

Ranges count distinct substantive sanitizer findings. Runtime startup
failures have their own status. The T runs each keep the node-limit,
timed-stop and game portions in one engine process.

| Build | Workload | Distinct reports |
| --- | --- | ---: |
| AU-r15d | A, 200 depth-9 positions | 0 |
| AU-r15d | A, 10 soft-node games | 0 |
| AU-kF | A, 200 depth-9 positions | 0 |
| AU-kF | A, 10 soft-node games | 0 |
| T-r15d | B, node limits, timed stops and four games | 0–2 |
| T-kF | B, node limits, timed stops and four games | 0–2 |

The canonical builds reproduce the net768 pins with assertions on.
The earlier exactness checks covered many of the same engine paths.
The threaded runs also change worker counts and interrupt searches,
so I allow a wider range for those processes.
