# CHECK of seat 21's 21-F12 — the PC drawn-root repair reaches `searchmoves` — seat 08

Their claim:
> 21-F12: "The PC build's drawn-root repair REACHES `searchmoves`: at halfmove 100, `go searchmoves e1e8 depth 4`
> searches **8 nodes** and returns the mating move, where the base build answers **0 nodes** for the same line. The
> 'no legal named move' case is unchanged on the PC build (still `0000` + the info line, 0 nodes)."

## Verdict: CONFIRMS — including the exact 8-node figure

I built the board myself rather than taking theirs: `7k/8/6K1/8/8/8/8/4R3 w - - 100 1`, and verified in python-chess
**before** using it that `e1e8` is legal and delivers checkmate at halfmove counter 100. So the position really is a
mate-in-1 on a board where the base tree's drawn-root shortcut applies.

| build | command | nodes | bestmove | info string |
|---|---|---|---|---|
| base 6b98f217 | `go searchmoves e1e8 depth 4` | **0** | e1e8 | — |
| **PC r15** | `go searchmoves e1e8 depth 4` | **8** | e1e8 | — |
| base, CONTROL no searchmoves | `go depth 4` | **0** | e1a1 | — |
| **PC, CONTROL no searchmoves** | `go depth 4` | **85** | **e1e8** | — |
| PC, CONTROL illegal name | `go searchmoves a1a8 depth 4` | 0 | **0000** | `searchmoves restriction has no legal root moves` |

| their statement | my measurement |
|---|---|
| base answers 0 nodes for the searchmoves line at halfmove 100 | **0 nodes** |
| PC SEARCHES it | **8 nodes — their exact figure** |
| the no-legal-named-move case unchanged on PC (0000 + info line, 0 nodes) | **0000 + info string, 0 nodes** |

## The sharper result, which their line implies but does not state

The no-searchmoves control is the more dramatic case: **on this halfmove-100 board the base build returns `e1a1` in 0
nodes — a non-mating move from a mate-in-1 — while the PC build returns the mate `e1e8` in 85 nodes.** So the repair
is visible not only in the `searchmoves` corner but in the plain `go depth 4` path, and the base tree's shortcut loses
a mate in one there while the PC build finds it.

That matters because it is the same defect FABLE_TO_swarm_3/6 describe as repaired on the PC; my check shows the size
of the repair on a board I constructed to test exactly it.

## Controls (all enforced)
- the board is verified in python-chess to have `e1e8` as a legal **mate** before any engine runs;
- the no-searchmoves arm proves the harness can tell a shortcut (0 nodes, wrong move) from a search (85 nodes, right
  move) on the same board;
- the illegal-name arm proves the `searchmoves` plumbing still reports the empty-restriction case properly, so a
  nonzero node count in the mate row is a real search and not a harness artefact.

## What I did NOT do
- Did not sweep other halfmove counters or other mate distances; one board, one counter value (100).
- Did not test the base tree with `FORGE_FIX_ROOT_DRAWN` off explicitly — the base tree simply has no such switch.
- All Threads 1.

## Show it again

    cd forge-combo29/swarm/08/pc20 && python3 check_s21f12.py /tmp/s21.txt
