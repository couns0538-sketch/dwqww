# REPORT job24 — `position fen ... moves` and the illegal-prefix rule on the PC build

**What was asked.** (My own next step.) job16 established on the base tree that
`position fen <FEN> moves <moves>` is applied. This job measures whether the PC build behaves the
same, since the patch rewrites parts of the `go` parser.

**The answer.** Identical on both builds, and exact against python-chess in every case.

| build | case | perft 1 engine | perft 1 python | perft 2 engine | perft 2 python | match |
|---|---|---|---|---|---|---|
| pc | `fen F moves e1d1` | 8 | 8 | 160 | 160 | yes |
| pc | `fen F` only (control) | 20 | 20 | 153 | 153 | yes |
| pc | 200 legal plies | 27 | 27 | 936 | 936 | yes |
| pc | 200 plies + illegal at 10 | 26 | 26 | 726 | 726 | yes |
| pc | refused FEN in the `fen ... moves` form | pre 20, post 20 | – | – | – | old position kept |
| base | the same four cases | identical | identical | identical | identical | yes |
| base | refused FEN in the `fen ... moves` form | pre 20, post 20 | – | – | – | old position kept |

**How sure.** High. Fresh process per case, Threads 1, `nodes` line asserted present, every
comparison against a python-chess count computed on a board copy.

## Prediction outcome

P1–P5 all held.

## Findings

`21-C9 | CONFIRMS the fen+moves form on both builds` — including the negative result that a FEN
refused inside the `fen ... moves` form still keeps the OLD position (the 21-F2 trap), so that
trap is not specific to the bare `position fen` form and is not repaired by the PC patch.

## Suspicions, not proven

- The refused-in-`fen ... moves` case produces `info string invalid FEN` and then keeps the old
  board, exactly as the bare form does. I did not test whether the `moves` after a refused FEN are
  applied to the old board (which would be worse); the perft count says they were not.

## What I did NOT do

- Did not test `position fen F moves` with no moves after the keyword.
- Did not test a FEN plus moves where the moves are illegal from the FIRST ply in this form (job4
  covers that for `position startpos moves`).

## What I am NOT sure about

- Whether any GUI uses the `fen ... moves` form; if none does, this whole check is defensive only.

## Times

see `job24/stamps.txt`.
