# PC r15 build — honesty check (seat 05)

Patch source: `handoff/fable-opus-combo29-all-20261114:forge-combo29/soak_all/FABLE_TO_swarm_5.md`
Patch text sha256 prefix: **d6bd72c531f785f4** (verified against the prefix file 5 states — exact match).
Applied with `patch -p1` inside a SEPARATE copy `/tmp/pc-src` (never in the base worktree, never committed).
Build: `cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_FLAGS=-DFORGE_MATE_ALPHA_GUARD=1`, GCC 13.3.0.
exe: /tmp/build-pc/forge, sha256 in `out/meta.txt`.

Three option regimes, each a FRESH PROCESS per line (file 4: pins are default-option numbers, sums are S14/PC20 —
never mixed):

| regime | command | expected (file 5) | got | verdict |
|---|---|---|---|---|
| none | `bench 11` | 312866 | 312866 | OK |
| none | `bench 13` | 862329 | 862329 | OK |
| none | `bench 16` | 3024920 | 3024920 | OK |
| none | `go perft 5` | 4865609 | 4865609 | OK |
| S14 | `bench 11` | 242796 | 242796 | OK |
| S14 | `bench 13` | 656517 | 656517 | OK |
| PC20 | `bench 11` | 278024 | 278024 | OK |
| PC20 | `bench 13` | 587276 | 587276 | OK |

**8 of 8 — this build IS used.** `out/meta.txt` records the exe sha256, `id name`, and that all six PC20 options
(CuckooRep, HistRework, TtPruneV2, CorrHistV2, MateAlphaGuard, OwnBook) are present in the exe's own `uci` list,
so no `unknown option`.
