# dot Job 1: baseline gate

Clock start: 2026-11-18 10:47:15 UTC (`date -u`). Case A: native commands and GitHub text publication work. Model identifier unavailable to this task; not inferred.

Lock source: 16833ecc03b425586f91f4c8834dea8807bf4c22. Plain CMake Release, default x86-64-v4 and PEXT/ZMM switches, unchanged source, -j2. CMake 4.4.5; GNU C++ 14.2.0 (Debian 14.2.0-19); glibc 2.41 (Debian GLIBC 2.41-12+deb13u4); dynamically linked libstdc++.so.6/libgcc_s.so.1. Exact libstdc++ package version not yet established (package database unavailable). Binary SHA256 1371770e2ad61aa2fe3c038acc7da3912da5d64c9cb1dcc5e4668221fb3226f6. Embedded AL1 s198 net SHA256 a7ebcf3a319675f347e6e8e3f2539901d38d8036cb9b5935f31dd43d084c9638.

Commands:
```
cmake -S forge-combo29 -B /tmp/forge-dot-lock-build -DCMAKE_BUILD_TYPE=Release
cmake --build /tmp/forge-dot-lock-build -j2
```
CMake was absent initially, installed PyPI CMake 4.4.5 in a temporary task directory. Configuration selected /usr/bin/c++ GNU 14.2.0 without compiler override.

Fresh process for each bench, sent Threads 1, Hash 16, OwnBook false, bench depth, quit. Bench uses its own 16 MiB single-thread searcher. UseNNUE true default. Perft uses startpos. Raw stdout:
```
info string bench depth 11 nodes 312866 time 198 nps 1580131
info string bench depth 13 nodes 862329 time 551 nps 1565025
a2a3: 181046
b2b3: 215255
c2c3: 222861
d2d3: 328511
e2e3: 402988
f2f3: 178889
g2g3: 217210
h2h3: 181044
a2a4: 217832
b2b4: 216145
c2c4: 240082
d2d4: 361790
e2e4: 405385
f2f4: 198473
g2g4: 214048
h2h4: 218829
b1a3: 198572
b1c3: 234656
g1f3: 233491
g1h3: 198502
nodes 4865609
```
All three required pins MATCH. NPS here is raw output only, not a speed result or Elo claim. `git diff --exit-code` passed before leaving the lock checkout.

Read LOCK.md, README.md and CMakeLists.txt on lock. Read latest NOTES_sol3.md at 58b6ef8f6999200ef9023509f7dbdd27a498a912 (through Job 6) and latest NOTES_kimi5.md at c04ba44b662d701e8bdc74e48fbfcbbc98338421 (through Job 24). Useful prior mechanisms: final node count differs from completed-iteration labels, reset semantics, clock gates, and source-only suspicion is not a native defect proof. Will deduplicate against these notes.

The helper base 6b98f2170a3210e71beed04bbd2553972c253ed7 is NOT source-identical to the lock: source/include diff contains substantial changes. The pin gate applies only to the lock binary above; upcoming line references and review target the requested helper base, not the lock. No claim of base-build pin equivalence.

FABLE_TO_dot_1.md absent in handoff snapshot e122d5c163b0d831762db954c8adbc1e57d838a8; user's first job is the governing assignment. Code review next; no candidate findings or repairs claimed yet.
