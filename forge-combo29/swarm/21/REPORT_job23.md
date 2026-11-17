# REPORT job23 — `searchmoves` on both builds, and the drawn-root fix reaching restricted searches

**What was asked.** (My own next step.) Seats 02 and 24 found that `go searchmoves` with no legal
named move answers `info string searchmoves restriction has no legal root moves` + `bestmove 0000`
on the base tree. This job asks what the PC build does, since its `FORGE_FIX_ROOT_DRAWN` changed
the root path — and specifically whether that fix also reaches a `searchmoves`-restricted search.

**The answer.** 24-C1 reproduces on my own harness for the base build, and on the PC build the
no-legal-name case is unchanged (`0000` + the info line, 0 nodes). The new part: **at a drawn
root (halfmove 100) a restricted search now actually searches on the PC build (8 nodes) where the
base build still answers 0 nodes.** So the root-draw repair reaches restricted searches too.

**How sure.** High. Six cases × two builds, fresh process each, Threads 1, FEN acceptance
asserted, every case raised if no bestmove arrived.

## Table (pasted from `job23/out/summary.md`)

| build | case | go line | bestmove | nodes | answer lines |
|---|---|---|---|---|---|
| pc | 1 illegal name | `go searchmoves e2e5 depth 2` | `0000` | 0 | `searchmoves restriction has no legal root moves` |
| pc | 2 one legal name | `go searchmoves e2e4 depth 2` | `e2e4` | 10 | – |
| pc | 3 two legal names | `go searchmoves d2d4 e2e4 depth 4` | `d2d4` | 91 | – |
| pc | 4 legal name at hm100 | `go searchmoves e1e8 depth 4` | `e1e8` | **8** | – |
| pc | 5 no names | `go searchmoves depth 2` | `0000` | 0 | same info line |
| pc | 6 legal knight | `go searchmoves g1f3 depth 4` | `g1f3` | 41 | – |
| base | 1 illegal name | `go searchmoves e2e5 depth 2` | `0000` | 0 | same info line |
| base | 2 one legal name | `go searchmoves e2e4 depth 2` | `e2e4` | 10 | – |
| base | 3 two legal names | `go searchmoves d2d4 e2e4 depth 4` | `d2d4` | 91 | – |
| base | 4 legal name at hm100 | `go searchmoves e1e8 depth 4` | `e1e8` | **0** | – |
| base | 5 no names | `go searchmoves depth 2` | `0000` | 0 | same info line |
| base | 6 legal knight | `go searchmoves g1f3 depth 4` | `g1f3` | 41 | – |

## Prediction outcome

P1–P6 all held.

## Findings

`21-C8 | CONFIRMS 24-C1` — the base build reproduces the "no legal named move" answer exactly
(`0000` plus the info line, 0 nodes) for an illegal name and for no name at all, while one and two
legal names search normally. `21-F12 | NEW` — on the PC build the drawn-root repair reaches
`searchmoves`: at halfmove 100 a restricted search searches 8 nodes, where the base build answers
`0` nodes. The PC build still answers `0000` when no named move is legal, so that behaviour is
unchanged by the patch.

## Suspicions, not proven

- The PC build's 8 nodes for `go searchmoves e1e8 depth 4` is a very small search. It returns the
  mating move, so it is not wrong, but whether a deeper restricted search at that root would
  behave differently I did not test.
- Whether the `0000` + info line for "no legal named move" is a *fault*. It is a defensible
  reading of a restricted search, and it also matches the brief's known list of engine answers; I
  record it as behaviour, not as a fault.

## What I did NOT do

- Did not test `searchmoves` with a repeated name, or with more names than legal moves.
- Did not test `searchmoves` combined with `infinite` + `stop`.

## What I am NOT sure about

- Whether the owner considers `bestmove 0000` for an empty restriction desirable; 24-C1 records it
  as behaviour and my check agrees, but no one has asked the owner.

## Times

see `job23/stamps.txt`.
