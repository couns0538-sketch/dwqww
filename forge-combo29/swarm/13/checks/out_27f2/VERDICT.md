# check of 27-F2: `go nodes N` below one root iteration

exe /home/ubuntu/b/rel/forge  sha256 e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83

| run | N | info lines | deepest depth | nodes (last info) | bestmove |
|---|---|---|---|---|---|
| fresh | 0 | 0 | None | None | `bestmove a2a3` |
| fresh | 1 | 0 | None | None | `bestmove a2a3` |
| fresh | 10 | 0 | None | None | `bestmove a2a3` |
| fresh | 24 | 0 | None | None | `bestmove a2a3` |
| fresh | 25 | 0 | None | None | `bestmove a2a3` |
| fresh | 26 | 1 | 1 | 26 | `bestmove d2d4` |
| fresh | 27 | 1 | 1 | 26 | `bestmove d2d4` |
| fresh | 30 | 1 | 1 | 26 | `bestmove d2d4` |
| fresh | 100 | 2 | 2 | 54 | `bestmove d2d4` |
| fresh | 100000 | 13 | 13 | 72062 | `bestmove e2e4` |
| warm | 25 | 0 | None | None | `bestmove a2a3` |
| warm | 26 | 1 | 1 | 26 | `bestmove d2d4` |
| warm | 27 | 1 | 1 | 26 | `bestmove d2d4` |

**Runner sanity control (N = 100000):** 13 info lines, 72062 nodes -> OK, the runner does see info lines

**27-F2 first half (N < 26: no info line at all):** HOLDS - every N below 26 produced 0 info lines
**27-F2 first half (N < 26: bestmove is a2a3):** HOLDS - every N below 26 answered bestmove a2a3
**27-F2 second half (N = 26 answers d2d4?):** HOLDS (actual: `bestmove d2d4`)

**Boundary, both ways:** N=24 quiet, N=25 quiet, N=26 1 info lines, depth 26, bestmove d2d4, N=27 1 info lines, depth 26, bestmove d2d4, N=30 1 info lines, depth 26, bestmove d2d4

**State effect (same N after a completed search, same process):** N=25 quiet, N=26 1 info lines, bestmove d2d4, N=27 1 info lines, bestmove d2d4
state makes no difference to these answers: YES