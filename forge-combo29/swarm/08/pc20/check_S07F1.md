# CHECK of seat 07's 07-F1 — the fabricated per-depth report on a refused `searchmoves` — seat 08

Their finding:
> 07-F1: "`position` + `go depth N searchmoves <no legal root move>` on a board that HAS legal moves answers a
> fabricated per-depth report — one `info depth D ... score cp 0 nodes 0` line for EVERY depth up to the limit (64 of
> them with no depth limit) — then `bestmove 0000`. The engine has already computed the true cause at
> search.cpp:2531 (`restricted_root_empty`) and says so in an info string."

## Verdict: CONFIRMS, every link

My own harness (`check_s07f1.py`), on the **PC build under PC20, Threads 1, Hash 16**, from startpos (20 legal moves).

| case | `info depth` lines | of those `nodes 0` | bestmove | info string |
|---|---|---|---|---|
| `searchmoves e2e5` (no legal root move), depth 8 | **8** | 8 | **0000** | `searchmoves restriction has no legal root moves` |
| `searchmoves a9a9` (garbage), depth 8 | **8** | 8 | **0000** | same |
| `searchmoves e2e5`, **no depth limit** | **64** | 64 | **0000** | same |
| CONTROL: `searchmoves e2e4` (a real move) | 8 | **0** | **e2e4** | — |
| CONTROL: no `searchmoves` | 8 | **0** | d2d4 | — |

| their link | my measurement |
|---|---|
| `bestmove 0000` although legal moves exist | **YES** |
| one fabricated line per depth up to the limit | **YES — 8 lines for depth 8, and 64 with no depth limit, every one `nodes 0`** |
| the engine does print the true cause | **YES — `info string searchmoves restriction has no legal root moves`** |
| it is a restricted-search artefact, not a general failure | **YES — both controls search normally with 0 `nodes 0` lines** |

The **64-line** case reproduced exactly, which is the strongest part of their claim: with no depth limit the engine
emits one fabricated report per depth from 1 to 64 and then `0000`.

## Why the controls matter here
Without the `searchmoves e2e4` and no-restriction arms, "bestmove 0000" could have been the engine correctly
reporting a position with no legal moves. Both controls show a real search (8 info lines, no `nodes 0` lines, a real
move), so the fabricated ladder is specific to the refused restriction.

## My own note on scope
This is a UCI-output defect, not a clock or search-strength one: it fires only when a match program sends
`searchmoves` naming no legal move, which FABLE_TO_swarm_6 says match programs never do. It therefore ranks below
the clock findings for the owner — but it is a real fabricated report, and the engine prints the true cause on the
line above it, so a GUI could display the diagnostic while a script parsing only `info depth` lines would read 64
fake zero-node depths as a real search.

## Show it again

    cd forge-combo29/swarm/08/pc20 && python3 check_s07f1.py /tmp/s07.txt

Raw output committed as `check_s07f1.txt`.
