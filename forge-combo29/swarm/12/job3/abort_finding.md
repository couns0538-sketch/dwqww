# S-F8 — the fabricated bestmove on the PC build (r15): what it is, and which switch was supposed to cover it

Seat 12, area 2. Confirmed independently, and it matches seat 19's number exactly.

**Threads 1 in every line below** (no `Threads` option is ever sent; the default is 1).
Builds: **PC r15** = base 6b98f217 + `pc_r15.patch` (sha256 `d6bd72c531f785f4…`),
`-DFORGE_MATE_ALPHA_GUARD=1`, all 8 pins of file 5 matched (`job3/PC_BUILD.md`).

## 1. It is still there on r15, under ASan+UBSan, in both regimes

`abort_asan.py`, 25 fresh processes per form, 2 forms, 2 regimes, kiwipete:

| regime | go form | fabricated | sanitizer lines | moves |
|---|---|---|---|---|
| **none** (no setoption) | `go depth 12` + `quit` at once | **25/25** | **0** | a2a3 ×25 |
| **none** | `go infinite` + `quit` at once | **25/25** | **0** | a2a3 ×25 |
| **PC20** | `go depth 12` + `quit` at once | **25/25** | **0** | a2a3 ×25 |
| **PC20** | `go infinite` + `quit` at once | **25/25** | **0** | a2a3 ×25 |

**200 of 200 aborted searches published a move with no `info depth` line at all.** This agrees with
seat 19 (a2a3 / 0 nodes vs e2e4 / 56,720 correctly driven; a2a3 vs d2d4 / 21,600 under PC20).

The sanitizer zero has its two proofs recorded in the same output file: `nm -C` counts 35
`__asan_` / 15 `__ubsan_` symbols on `pc_r15_asan`, and the **planted-fault copy of the same r15
source** — heap over-read in `uci.cpp` behind a command the harness sends — is counted by the
**same `one_run()` function**: 3 sanitizer lines, exit 1. So the zero is measured, not a harness
that cannot see.

## 2. What the fabricated move IS on r15: the first root candidate — NOT a stale move

This is the coordinator's question, and the answer is the reassuring one. One process per probe,
`stale_move.py`, PC20 and `none` identical:

| probe | first legal move of the position | real search in that process | aborted answer | verdict |
|---|---|---|---|---|
| A cold abort, kiwipete | **a2a3** | — | **a2a3** | FIRST ROOT CANDIDATE |
| B warm abort: real `go depth 10` → **e2a6**, then aborted `go depth 14` | a2a3 | e2a6 | **a2a3** | not the earlier answer → positional |
| C warm abort across positions: real search on X (→ e2a6), then **position Y** and aborted `go` | Y's first legal move is **e2e3** | e2a6 | **e2e3** | Y's first root candidate → positional, not stale |

**The fault has not changed shape.** It is always `root_candidates.front()` of the position
currently on the board — measured against the engine's own perft-1 order, not assumed. In probe C
the aborted answer switched to Y's first legal move (`e2e3`), which is the decisive test: a stale
bestmove would have echoed `e2a6`. So it is the same positional fallback as on the base tree
(`src/search.cpp:3017` in the patched build, unchanged), not a dangling or uninitialised value.

That is also why the sanitizer stays silent: the value read is index 0 of a fully built
`MoveList` owned by the search frame — reported earlier in `job1/quit_mid_search.md` (100
interrupted searches, 0 sanitizer lines, plant counted 3).

## 3. The sentence the owner needs: which switch was meant to cover it, and what it does

File 5 advertises `FORGE_FIX_ABORT_PUBLISH` and `FORGE_FIX_ISREADY_PENDING` as "aimed straight at
the aborted-search fault". Tested on the PC build:

**`FORGE_FIX_ABORT_PUBLISH` was the switch that should have covered it, and it cannot: it chooses
between two moves that only exist once an iteration has finished — the unfinished line and the
finished best move — so it never runs when the stop arrives before depth 1 completes, and the
surviving `if (result.best_move.is_none()) result.best_move = root_candidates.front();` publishes
a2a3 instead. It is also compiled OUT by default (`#define FORGE_FIX_ABORT_PUBLISH 0`,
`search.cpp:76-78`, with the in-patch comment "Default 0 since 16:45: measured, it is not a
repair"), so a stock PC build does not contain even that partial behaviour.**

Measured, not read: I built r15 a third time with `-DFORGE_FIX_ABORT_PUBLISH=1` and ran the same
four cases — **still 4/4 fabricated, still `a2a3`** (`job3/ab_pc_fix.txt`). So turning the switch
on does not fix it either; the switch is about a different question.

`FORGE_FIX_ISREADY_PENDING` is about `isready` answering `readyok` while no net file is named; it
has nothing to do with what a stopped search publishes. Not implicated, not a candidate.

### Why this is not a strength cost in normal play

The boundary is "stop before the first iteration finishes", which on this hardware is under
~10 ms (measured delay sweep: 0/1/5/10 ms → 0 info lines and `a2a3`; 20 ms → 7 info lines and
`d5e6`; 50 ms+ → 10-12 lines and `e2a6`). A GUI never stops a search that fast. So: a real
protocol defect, present on the PC build, with no measurable effect on a game — and a live trap for
any harness that pipelines `quit`, which is exactly how seat 19 and I both found it.

## The repair I would suggest (NOT written — needs the owner's decision and a bench)

At `src/search.cpp:3017`, distinguish "no iteration ever finished" from "an iteration finished but
left no best move". In the first case either keep searching until depth 1 completes despite the
stop (microseconds here), or print `bestmove 0000` plus an `info string`. The first is what
`FORGE_FIX_ISREADY_PENDING` already does in spirit for a different question. **I have not built or
tested either variant.**

## How to see all of it again

```
python3 forge-combo29/swarm/12/job3/abort_asan.py  ~/build/pc_r15_asan/forge /tmp/o.json --planted ~/build/pc_planted/forge
python3 forge-combo29/swarm/12/job3/abort_asan.py  ~/build/pc_r15_asan/forge /tmp/o20.json --pc20 --planted ~/build/pc_planted/forge
python3 forge-combo29/swarm/12/job3/stale_move.py  ~/build/pc_r15/forge /tmp/s.json
python3 forge-combo29/swarm/12/job3/abort_probe.py ~/build/pc_abortfix/forge /tmp/f.json
```

Raw files committed: `job3/abort_asan_none.json`, `job3/abort_asan_pc20.json`,
`job3/stale_none.json`, `job3/stale_pc20.json`, `job3/ab_pc_r15_none.json`,
`job3/ab_pc_fix.json`, `job3/ab_base_none.json`.

## Suspicions, not proven

- Whether the PC's own match harness ever interrupts a search inside the first iteration. Unknown;
  needs the GUI, which I do not have.
- Whether a GUI that sends `stop` immediately after `go infinite` on a slow position could reach
  the same path in practice. Unmeasured.
