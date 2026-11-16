# REPORT — seat 07, job 47: does the drawn-root repair reach `searchmoves`? (check of 21-F12)

## What was asked / the answer / how sure

**Asked:** (cycle work) seat 21's 21-F12 claims the PC build's drawn-root repair reaches `searchmoves`:
at halfmove 100 a **legal named** move searches (8 nodes) where the base answers 0, while the "no legal
named move" case is unchanged. That bears directly on my own 07-F1, so it needed checking by my own
harness.

**Answer:** **confirmed.** The PC build searches the legal-named restricted root (8 nodes) where the base
does not (0 nodes), and the empty-root case is unchanged on **both** builds. So 07-F1 is not in tension
with 21-F12 — the repair covers one `searchmoves` sub-case and leaves the other.

**How sure:** high, after two errors of my own that I caught before reporting (below).

## Results (halfmove 100, positions verified legal with python-chess first)

| case | base 6b98f217 | PC r15 / PC20 |
|---|---|---|
| only legal move named (`searchmoves g8h8`) | `g8h8`, **0 nodes** | `g8h8`, **8 nodes** |
| no legal move named (`searchmoves a1a2`) | `0000` + info line, **0 nodes** | `0000` + info line, **0 nodes** |
| plain `go depth 4` | `g8h8`, **0 nodes** | `g8h8`, **8 nodes** |
| stalemate at counter 100 | `0000`, 0 nodes | `0000`, 0 nodes |

Threads 1, Hash 16, fresh process per case.

## What this does to 07-F1

It **sharpens** it. `searchmoves` has two distinct sub-cases at a drawn root:

- **a legal move is named** → the PC build now searches it (8 nodes); the base does not. **Repaired.**
- **no legal move is named** → both builds answer `0000` with the info line and 0 nodes. **Unchanged.**

So 07-F1 is precisely the **empty-intersection** case and nothing wider. Anyone reading my earlier line
as "`searchmoves` is broken on the PC build" would be over-reading it; this check pins the scope.

## Two errors of mine, both caught before anything was reported

1. **Wrong position, silently.** My first FEN was `2N3k1/3pn1p1/8/2R1P1KP/7P/8/8/5r2 b` with the side
   swapped to `w`. The engine **refused** it — `info string invalid FEN: side that moved left its king
   in check` — and therefore kept **STARTPOS**. Every answer was about the wrong board.
   **The tell** was the plain case answering `e2e4`, which cannot occur in a position with a lone black
   king on h8: if the answer does not belong to the position, the position was not accepted.
2. **A move that does not exist.** On the corrected FEN I then named `g8f7`, which is not legal there —
   the only legal move is `g8h8`. python-chess showed it in one line.

Neither error reached a report, and both are the same failure as the ones already recorded in this
seat's notes: **validate the input against an independent oracle before believing the output.**

## Findings

**07-C46** in FINDINGS.md.

## Suspicions, not proven

- What the 8 nodes consist of. A single root move searched at depth 4 with mate available would be very
  cheap, so 8 is plausible, but I did not trace it.

## What I did NOT do

- Did not test a restricted root at a drawn root with MULTIPLE legal named moves.
- Did not test the repetition (rather than fifty-move) route into the drawn-root branch.

## What I am NOT sure about

- Whether seat 21's original FEN differs from mine in a way that matters; I rebuilt the case from their
  sentence rather than copying their position, which is what makes this an independent check.

## Times

See job47/stamps.txt.
