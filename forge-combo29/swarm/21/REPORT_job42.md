# REPORT job42 — 21-F12's example move: a board mismatch, not an error (recorded, not "fixed")

**What was asked.** Seat 20 confirmed 21-F12 and corrected my example, saying `searchmoves e1e8` is not
a legal move on my board, so it takes the empty-restriction path and yields `0000`; the 8-node behaviour
"reproduces only with the actual mating move d1d8". Action: fix the move, keep the finding.

**The answer.** **The correction does not apply to my board — we measured two different positions, and
both of us are right on ours.** `e1e8` IS a legal, mating move on the board I used, and my recorded
output for it shows exactly 8 nodes on the PC build. Seat 20's board has its rook on d1 instead of e1,
which is why its mating move is `d1d8` and why `e1e8` is illegal there.

I did **not** change the move, because changing it would make my finding line describe a position I
never measured. Instead the line now names the full FEN alongside the move, so the two boards cannot be
confused, and I record seat 20's board and its confirmation beside mine.

## The two boards, measured side by side

| board | white rook | mating move | legal there? | base build | PC build under PC20 |
|---|---|---|---|---|---|
| **mine** `6k1/5ppp/8/8/8/8/5PPP/4R1K1 w - - 100 60` | e1 | `e1e8` | **yes** | `e1e8`, **0 nodes** | `e1e8`, **8 nodes** |
| **seat 20's** `6k1/5ppp/8/8/8/8/5PPP/3R2K1 w - - 100 60` | d1 | `d1d8` | **yes** | `d1d8`, **0 nodes** | `d1d8`, **8 nodes** |

Reproduced just now with `go searchmoves <mating move> depth 4`, Threads 1, PC20 verified:

```
base  MY board, rook e1        e1e8   e1e8   nodes 0
pc20  MY board, rook e1        e1e8   e1e8    8
base  SEAT 20 board, rook d1   d1d8   d1d8   nodes 0
pc20  SEAT 20 board, rook d1   d1d8   d1d8    8
```

And the legality check on my board: 20 legal moves, `e1e8` among them, and playing it is checkmate.

## Why the two readings diverged

`6k1/5ppp/8/8/8/8/5PPP/4R1K1` puts the white rook on **e1**; `6k1/5ppp/8/8/8/8/5PPP/3R2K1` puts it on
**d1**. In the first, `e1e8` mates along the e-file; in the second there is no rook on e1 at all, so
`e1e8` is not a move and the restriction is empty — which on the PC build answers `0000` with 0 nodes,
exactly as seat 20 says. Neither observation is wrong; they are observations of different boards.

My original line carried the FEN in the same row, so the position was never hidden — but the move alone
was quoted in the summary I sent up, and that is how the two got crossed. Naming the FEN in the finding
line itself fixes the ambiguity.

## The split we agree on, and it is now recorded

The distinction seat 20 drew for its own record is the correct general statement, and it is worth having
in my file too:

- a restriction naming **at least one legal move** → the PC patch repairs it (the search runs: 8 nodes
  on both boards above, vs 0 on the base build);
- a restriction that is **empty or names no legal move** → not repaired; the PC build still answers
  `info string searchmoves restriction has no legal root moves` + `bestmove 0000` with 0 nodes.

I verified the second half myself in job23 (the illegal-name and no-name cases), so the split rests on
two independent measurements.

## Prediction outcome

No prediction was written for this job: it is a correction-and-record job with no measurement whose
outcome was uncertain — the question was simply which board each seat used, and that is answered by the
table above.

## Findings

`21-C19 | CONFIRMS 21-F12, with the board named` — on `6k1/5ppp/8/8/8/8/5PPP/4R1K1 w - - 100 60`
(my board) `go searchmoves e1e8 depth 4` gives `e1e8` with **8 nodes** on the PC build and **0 nodes**
on the base build; on seat 20's board `6k1/5ppp/8/8/8/8/5PPP/3R2K1 w - - 100 60` the same holds for
`d1d8`. The repair reaches a satisfiable restriction on both. Seat 20's correction is a board
difference, not an error in my line.

`21-F12` is unchanged in substance and now carries its FEN and the legal/illegal split.

## Suspicions, not proven

- Whether seat 20's board came from a different seat's write-up of the same idea. Two boards that differ
  by one rook file is exactly what a transcription does, so I would look for a third copy before
  assuming either was invented.

## What I did NOT do

- Did not edit the move to `d1d8`, because that would describe a position I never measured, and the
  finding would then not reproduce from my own command file — which is the rule I hold others to.

## What I am NOT sure about

- Whether any other seat's copy of this example also drifted. Cheap to check if someone has the list.

## Times

see `job42/stamps.txt`.
