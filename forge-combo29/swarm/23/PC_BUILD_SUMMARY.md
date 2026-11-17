# THE PC BUILD (r15) — what I verified, what it changes, and where it is inert

**Seat 23. One page on the engine the owner's PC actually plays, built from file 5's patch. Every number is from my
own harness, Threads 1, Hash 16, `OwnBook false`, fresh process per line, drained to `bestmove`.**

## The build is the PC's source, and its numbers reproduce

Patch from `FABLE_TO_swarm_5.md`, sha256 `d6bd72c531f785f4…` **verified before applying** (a truncated extraction
that drops the trailing newline gives `61da918e…` and silently loses the last line — I hit that and re-extracted).
Applied with `patch -p1` to a separate worktree, 11 files, no fuzz; built with `-DFORGE_MATE_ALPHA_GUARD=1`.

| settings | bench 11 | bench 13 | bench 16 | perft 5 |
|---|---|---|---|---|
| none | 312,866 | 862,329 | 3,024,920 | 4,865,609 |
| S14 | 242,796 | 656,517 | — | — |
| PC20 | 278,024 | 587,276 | — | — |

**8 of 8 published numbers match.** exe sha256 `068f0927…`. Full record: `PCBUILD.txt`.

## The single most important thing about this build

**A fixed-depth comparison of the two builds overstates their difference; the clock is the honest common
denominator.** Concretely, on the six lone-king boards (all forced wins in 7–23 plies):

| | base tree | PC r15 |
|---|---|---|
| at `go depth 24` | cp on all six (no mate) | mate on all six |
| at a **6 s+0.06 clock**, PC20 | reaches depth **25–32**, mates on **4 of 6** | reaches depth **17–23**, mates on **5 of 6** |

So the depth-24 comparison — which is how the repair was originally established, and which I confirmed — makes the
base look much worse than it is in play. At the clock the two builds are close, and the PC reaches a *lower* depth
on every one of these boards while still mating on one more.

**The repair is inert on one board in real play:** `8/8/8/6k1/8/8/5K2/1Q6 w` reaches only depth 17 at PC20 under
6 s+0.06 and reports cp 1327 — below the depth where its mate surfaces (~20), so in a match the PC behaves like the
base there. Four of the six reach the threshold (depths 22/22/23/20) and one mates at 19, below it.

## What the PC build does NOT fix

- **The fabricated-`bestmove` fault (19-F12) is still present on the PC build** (23-F8): `go depth 12` + an
  immediate `quit` gives `bestmove a2a3` with **zero** `info depth` lines, on both builds. `stop` is fine on both
  (12 info lines, e2e4). So FORGE_FIX_ABORT_PUBLISH covers the stop path, not process/input termination — which is
  the case every pipelined harness hits.
- Move generation is unchanged and correct: identical perft totals to the base on 5,000 positions (23-F9).
- The static evaluation is unchanged: exactly colour-symmetric on 60/60 mirror pairs (23-C16).

## What the PC build DOES change, verified from the protocol

| switch (file 5) | what I measured |
|---|---|
| drawn-root repair | a won K+R v K at halfmove 150: base **0 nodes**, PC **160**; and on a **threefold-repetition** root (claimable, not forced) base **cp 0 / 0 nodes**, PC **cp 399 / 6,941 nodes**, different move — so the repair is a real cost avoided, not cosmetics (23-F43/F44) |
| lone-king repair | mates surface at ~depth 20 on the PC, never at 12; base also mates at 24-32 on the clock, so the practical difference is confined to two shapes (23-F45/F46/F47) |
| `FORGE_FIX_GO_PARSE` | malformed `go` lines where `go` sits where a number belongs: base truncates to **1 info line**, PC returns **64** and a normal bestmove (23-F48). Robustness only — matches never send `go` as a value |


## Is the engine reproducible in play? Yes on both paths the owner uses

| path | command | stable across fresh processes? |
|---|---|---|
| **clock** (strength matches) | `go wtime ... btime ... winc ... binc ...` | **yes** — same move on 20 of 20 positions, twice over; also at a 1 s control (23-F54/F55) |
| **self-play** | `go softnodes 2000` | **yes** — same move AND same node count on 30 of 30 (23-F64) |
| node budgets (comparisons) | `go nodes 20000 / 50000 / 250000` | **no** — about 30 % of quiet positions change move between budgets (23-F24) |

The mechanical reason: the clock and `softnodes` take their stopping point from the search's own progress and stop at
a **completed depth**; `go nodes` aims at a fixed count and stops wherever the depth boundary happens to fall. A depth
difference is what changes the move (23-F56), so the path that varies its depth varies its move.

**Practical meaning:** the two paths the PC's engine is actually driven on are reproducible move-for-move, so a match
result and a self-play game are repeatable. The per-move lottery lives in the node-budget path, which is used for
comparisons rather than play — so a node-budget comparison is not reproducible move-for-move and its results are not
interchangeable with clock results.

## Caveats that must travel with this page

- **The PC plays its own trained net file, which is NOT shared.** My PC build uses the built-in net, so every number
  here reproduces the PC's ENGINE but not its EVALUATION. Anything evaluation-dependent remains a question for the PC.
- All six lone-king boards are forced wins; the practical reach of the repair depends on the clock, which I measured
  only at 6 s+0.06.
- `go nodes` on the match path reports **below** N (23-F17/F19 — seat 05 published the same, and their refinement
  S-F36/S-W4 gives the right reading: the same depth ladder, boundary depth unreported), and the three budgets are
  different players on ~30 % of quiet positions (23-F24), most often with **only 250,000 differing** (23-F25/F27).
