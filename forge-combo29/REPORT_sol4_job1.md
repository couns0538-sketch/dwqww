# sol4 — Job 1 Forge baseline and source review

Case A, Codex Cloud on Linux x86-64. Model GPT-6 (Codex). Recorded 2026-11-18T06:48:29Z. [First note](NOTES_sol4.md)

## Build identity and lock pins

- Build A source is `for-fable-and-opus/astra-0017-v3-path` at `6b98f2170a3210e71beed04bbd2553972c253ed7`. I used plain CMake Release with Unix Makefiles, default `x86-64-v4`, PEXT and ZMM enabled, strict floating-point flags, and the v3 path off.
- Compiler GCC C++ 14.2.0 (Debian 14.2.0-19), linked libstdc++ `libstdc++.so.6.0.33` (Debian 14.2.0-19), and glibc 2.41 (Debian 2.41-12+deb13u4). CMake 4.2.3 was installed in workspace scratch because it was absent from PATH.
- Build A engine SHA-256 `2f545495d4e3e2b59af49fbb18212ec2ed8ae297d801e58647cfea37cd18e785`.
- The embedded AL1 s198 weights have 256 hidden units per side. The source include SHA-256 is `a7ebcf3a319675f347e6e8e3f2539901d38d8036cb9b5935f31dd43d084c9638`. No external net was loaded.
- The cloud clock recorded the build from `2026-11-18T06:38:46Z` to `2026-11-18T06:38:54Z`, and the pins from `2026-11-18T06:39:58Z` to `2026-11-18T06:39:59Z`.

From `forge-combo29/` using CMake 4.2.3:

```sh
cmake -S . -B "$BUILD" -DCMAKE_BUILD_TYPE=Release
cmake --build "$BUILD" --parallel 4
```

Build A stdin. Unlisted options stayed at their defaults, including MultiPV 1. Bench constructs its own fresh 16 MiB searcher and clears it between FENs at `src/uci.cpp:597–619`.

```text
setoption name Threads value 1
setoption name Hash value 16
setoption name OwnBook value false
setoption name UseNNUE value true
bench 11
bench 13
position startpos
go perft 5
quit
```

All three match [LOCK.md](LOCK.md). The perft root counts sum to the total. Raw combined stdout and stderr:

```text
info string bench depth 11 nodes 312866 time 202 nps 1548841
info string bench depth 13 nodes 862329 time 550 nps 1567870
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

## 1. MultiPV cumulative nodes

The primary worker's `total_nodes()` excludes the standalone alternate worker. Each alternate search is counted in the main worker's `extra_nodes_` at `src/search.cpp:2505`. The emitted count resets at `2521` and sums the primary cumulative count and only alternate searches that supplied lines at that depth. The final soft-node marker uses `total_nodes() + extra_nodes_` at `2630–2643`. In the complete depth-2 reproduction, exactly the 2 alternate nodes from depth 1 are missing from the final lines' maximum. The same omission affects UCI NPS because the formatter derives it from displayed nodes at `2228–2245`.

The patch uses the complete cumulative count at emit time. Forge searches all available lines for a depth before emitting them, so every line in one emitted depth group carries the same total. The patch leaves the search limits, line ordering and scores alone. This is a reporting defect after a fully completed iteration. The separate stopped-iteration case Sol3 identified compares an earlier completed line against work that intentionally continued after that line was emitted. [Original MultiPV stop work](REPORT_t21.md) · [Soft-node count contract](REPORT_r3_12.md#semantics)

Build B uses Build A flags, toolchain, weights and the same object files except for `search.cpp.o`. I checked the unified diff with `git apply --check`, streamed GNU patch output into the compiler with `patch -p1 -o -`, and linked the separate candidate binary. Build B SHA-256 is `b137bc60b46d068b2a931159077d5f2e87e45c35578fd9c71f25163c38eeb8e6`. Patch SHA-256 is `0f1e36786212b1554977cd1720dc197e85f70d86d4c36ce659132d61d59d2d03`. [Unified diff](sol4_multipv_nodes.patch.txt)

### Deciding regression

Save as `check_multipv_nodes.py` and run `timeout 10s python check_multipv_nodes.py /path/to/forge` on each binary. Require complete depth-1 and depth-2 output, legal selected root moves, and a node count below the soft target. The last depth-2 node count must equal `info string softnodes nodes`.

```python
import re
import subprocess
import sys

commands = (
    "setoption name Threads value 1",
    "setoption name Hash value 16",
    "setoption name OwnBook value false",
    "setoption name UseNNUE value true",
)
failed = False
for ranks in (1, 2):
    lines = []
    with subprocess.Popen([sys.argv[1]], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, text=True) as engine:
        request = (*commands, f"setoption name MultiPV value {ranks}", "position startpos",
                   "go depth 2 softnodes 1000000 searchmoves e2e4 d2d4")
        for command in request:
            print(f"> {command}")
        engine.stdin.write("\n".join(request) + "\n")
        engine.stdin.flush()
        for line in engine.stdout:
            line = line.rstrip("\n")
            print(line)
            lines.append(line)
            if line.startswith("bestmove "):
                break
        assert lines[-1].split()[:2] in (["bestmove", "e2e4"], ["bestmove", "d2d4"])
        engine.stdin.write("quit\n")
        engine.stdin.flush()
        assert engine.wait() == 0
    groups = []
    for depth in (1, 2):
        info = [line for line in lines if line.startswith(f"info depth {depth} ")]
        assert len(info) == ranks
        if ranks == 2:
            assert [int(re.search(r" multipv (\d+) ", line)[1]) for line in info] == [1, 2]
        groups.append([int(re.search(r" nodes (\d+) ", line)[1]) for line in info])
    totals = [int(line.split()[-1]) for line in lines if line.startswith("info string softnodes nodes ")]
    assert len(totals) == 1 and 0 < totals[0] < 1_000_000
    ok = groups[-1][-1] == totals[0]
    print(f"{'PASS' if ok else 'FAIL'} MultiPV={ranks}: last info nodes={groups[-1][-1]}, actual nodes={totals[0]}")
    failed |= not ok
sys.exit(int(failed))
```

Build A, 2026-11-18T06:40:43Z, exit 1:

```text
> setoption name Threads value 1
> setoption name Hash value 16
> setoption name OwnBook value false
> setoption name UseNNUE value true
> setoption name MultiPV value 1
> position startpos
> go depth 2 softnodes 1000000 searchmoves e2e4 d2d4
info depth 1 seldepth 1 score cp 1 nodes 3 nps 1000 hashfull 0 time 3 pv d2d4
info depth 2 seldepth 2 score cp 49 nodes 13 nps 4333 hashfull 0 time 3 pv d2d4 d7d6
info string softnodes nodes 13
bestmove d2d4
PASS MultiPV=1: last info nodes=13, actual nodes=13
> setoption name Threads value 1
> setoption name Hash value 16
> setoption name OwnBook value false
> setoption name UseNNUE value true
> setoption name MultiPV value 2
> position startpos
> go depth 2 softnodes 1000000 searchmoves e2e4 d2d4
info depth 1 multipv 1 score cp 1 seldepth 1 nodes 3 nps 500 hashfull 0 time 6 pv d2d4
info depth 1 multipv 2 score cp -11 seldepth 1 nodes 5 nps 833 hashfull 0 time 6 pv e2e4
info depth 2 multipv 1 score cp 49 seldepth 2 nodes 13 nps 2166 hashfull 0 time 6 pv d2d4 d7d6
info depth 2 multipv 2 score cp 37 seldepth 2 nodes 23 nps 3833 hashfull 0 time 6 pv e2e4 e7e6
info string softnodes nodes 25
bestmove d2d4
FAIL MultiPV=2: last info nodes=23, actual nodes=25
```

Build B, verified at 2026-11-18T06:42:50Z, exit 0:

```text
> setoption name Threads value 1
> setoption name Hash value 16
> setoption name OwnBook value false
> setoption name UseNNUE value true
> setoption name MultiPV value 1
> position startpos
> go depth 2 softnodes 1000000 searchmoves e2e4 d2d4
info depth 1 seldepth 1 score cp 1 nodes 3 nps 0 hashfull 0 time 0 pv d2d4
info depth 2 seldepth 2 score cp 49 nodes 13 nps 0 hashfull 0 time 0 pv d2d4 d7d6
info string softnodes nodes 13
bestmove d2d4
PASS MultiPV=1: last info nodes=13, actual nodes=13
> setoption name Threads value 1
> setoption name Hash value 16
> setoption name OwnBook value false
> setoption name UseNNUE value true
> setoption name MultiPV value 2
> position startpos
> go depth 2 softnodes 1000000 searchmoves e2e4 d2d4
info depth 1 multipv 1 score cp 1 seldepth 1 nodes 5 nps 1000 hashfull 0 time 5 pv d2d4
info depth 1 multipv 2 score cp -11 seldepth 1 nodes 5 nps 1000 hashfull 0 time 5 pv e2e4
info depth 2 multipv 1 score cp 49 seldepth 2 nodes 25 nps 4166 hashfull 0 time 6 pv d2d4 d7d6
info depth 2 multipv 2 score cp 37 seldepth 2 nodes 25 nps 4166 hashfull 0 time 6 pv e2e4 e7e6
info string softnodes nodes 25
bestmove d2d4
PASS MultiPV=2: last info nodes=25, actual nodes=25
```

Build B reproduced the Build A lock pins under the same setup, including all perft root counts. The existing `tests_t15/test_multipv.cpp` and `tests_t21/multipv_stop_test.cpp` exited 0 on both source variants, linked with the corresponding search object. The first t15 invocation from the scratch directory failed to find its repository-relative fixture. Both final runs used the repository root. The existing tests cover MultiPV 1 depth-12 parity, legal ranked lines, one-move mate, a hard-node-limited search and external stop during MultiPV. No speed or strength comparison was run.

## 2. Secondary mate search

`src/uci.cpp:118` sets `mate_moves`. The alternate search explicitly clears it at `src/search.cpp:2486–2496`, which enables IIR at `1783–1784`. In the witness below the alternate root has no TT move and the restricted root does not store its own entry (`2093`). At advertised depth 3, IIR changes the alternate's root depth to 2. The winning quiet queen move then lies past the regular search horizon. Non-check qsearch generates captures and promotions (`670–680,889–891`).

Use Build A, Threads 1, Hash 16 MiB, OwnBook false, UseNNUE false (classical evaluation), IirDepth 1 and fresh search processes. Set the board to `8/8/8/8/1Q6/8/8/k2K4 w - - 0 1`. Each selected White king move leaves Black only `a1a2`. After `b4b2#`, the queen covers a1 and a3 and the White king covers b2. Both lines therefore have the same mate distance independently of the engine. The test requires both depth-3 ranks to show `mate 2` with the corresponding legal mating variation. The two single-PV controls establish that Forge finds it with mate mode active. The displayed MultiPV counts below are UCI telemetry from Build A.

Raw Build A run, 2026-11-18T06:43:46Z to 06:43:47Z:

```text
> setoption name Threads value 1
> setoption name Hash value 16
> setoption name OwnBook value false
> setoption name UseNNUE value false
> setoption name IirDepth value 1
> setoption name MultiPV value 1
> position fen 8/8/8/8/1Q6/8/8/k2K4 w - - 0 1
> go mate 2 searchmoves d1c1
info depth 1 seldepth 1 score cp 951 nodes 2 nps 0 hashfull 0 time 0 pv d1c1
info depth 2 seldepth 2 score cp 903 nodes 5 nps 0 hashfull 0 time 0 pv d1c1 a1a2
info depth 3 seldepth 4 score mate 2 nodes 12 nps 0 hashfull 0 time 0 pv d1c1 a1a2 b4b2
bestmove d1c1
> setoption name Threads value 1
> setoption name Hash value 16
> setoption name OwnBook value false
> setoption name UseNNUE value false
> setoption name IirDepth value 1
> setoption name MultiPV value 1
> position fen 8/8/8/8/1Q6/8/8/k2K4 w - - 0 1
> go mate 2 searchmoves d1c2
info depth 1 seldepth 1 score cp 953 nodes 2 nps 0 hashfull 0 time 0 pv d1c2
info depth 2 seldepth 2 score cp 905 nodes 5 nps 0 hashfull 0 time 0 pv d1c2 a1a2
info depth 3 seldepth 4 score mate 2 nodes 12 nps 0 hashfull 0 time 0 pv d1c2 a1a2 b4b2
bestmove d1c2
> setoption name Threads value 1
> setoption name Hash value 16
> setoption name OwnBook value false
> setoption name UseNNUE value false
> setoption name IirDepth value 1
> setoption name MultiPV value 2
> position fen 8/8/8/8/1Q6/8/8/k2K4 w - - 0 1
> go mate 2 searchmoves d1c1 d1c2
info depth 1 multipv 1 score cp 953 seldepth 1 nodes 3 nps 53 hashfull 0 time 56 pv d1c2
info depth 1 multipv 2 score cp 951 seldepth 1 nodes 5 nps 89 hashfull 0 time 56 pv d1c1
info depth 2 multipv 1 score cp 951 seldepth 2 nodes 4 nps 70 hashfull 0 time 57 pv d1c1
info depth 2 multipv 2 score cp 905 seldepth 2 nodes 12 nps 210 hashfull 0 time 57 pv d1c2 a1a2
info depth 3 multipv 1 score mate 2 seldepth 4 nodes 17 nps 298 hashfull 0 time 57 pv d1c2 a1a2 b4b2
info depth 3 multipv 2 score cp 903 seldepth 3 nodes 24 nps 421 hashfull 0 time 57 pv d1c1 a1a2
bestmove d1c2
```

The next regression should include a position where an alternate proves mate before the target depth. Merely retaining `mate_moves` can trigger the early-mate break at `2552`, while the caller at `2506–2508` treats any shallower alternate as interrupted.

## 3. Alternate table on an empty clock

`src/search.cpp:2280–2319` uses a prepared legal move or a capped one-ply emergency search when no clock remains. The cold MultiPV path allocates a second table at `2384–2392` before determining the admissible number of lines at `2473`. `TranspositionTable::resize()` value-initializes the clusters at `362–369`. One admissible root move cannot produce a second line. Checking that count before creating the alternate state would avoid work on the empty-clock path and on normal one-root searches.

Use two fresh Build A processes with Threads 1, Hash 64 MiB, OwnBook false, UseNNUE true, embedded AL1 s198 and default overhead. Set MultiPV 1 and 2 respectively. After `isready` returns `readyok`, read `VmHWM` from `/proc/<pid>/status`. Then send `position startpos` and `go wtime 0 btime 0 searchmoves e2e4`, wait for `bestmove` and read `VmHWM` again while the engine is still alive. The deciding follow-up can count calls at the alternate allocation site directly. There must be none with one eligible move. Use two eligible moves and adequate time as the control that still takes that allocation path and produces two legal lines. The following is a single baseline sample, not a latency estimate.

```text
info depth 1 seldepth 1 score cp -11 nodes 2 nps 0 hashfull 0 time 0 pv e2e4
bestmove e2e4
MultiPV=1, VmHWM 105012 -> 105012 KiB, delta 0 KiB
info depth 1 multipv 1 score cp -11 seldepth 1 nodes 2 nps 11 hashfull 0 time 177 pv e2e4
bestmove e2e4
MultiPV=2, VmHWM 105064 -> 142676 KiB, delta 37612 KiB
```
