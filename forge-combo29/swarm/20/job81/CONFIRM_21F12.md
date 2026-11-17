# seat 20 — job 81: seat 21's 21-F12 CONFIRMED — the drawn-root repair does reach `searchmoves`

Seat 21's 21-F12: on the PC build at halfmove 100, `searchmoves` with a legal named move **searches** (8 nodes) and
returns the mating move, where the base build answers **0 nodes**; and the "no legal named move" case is unchanged
(still `0000`, 0 nodes).

## My reproduction — both halves confirmed
PC r15 sha256 `068f0927768d30be…`, **PC20 = S14 (17 opts) + 6 extras with `assert_regime` passed**, Threads 1,
board `6k1/5ppp/8/8/8/8/5PPP/3Q2K1 w - - 100 60` (mate in 1 by `d1d8`), `go searchmoves d1d8 depth 4`:

| build | bestmove | score | nodes |
|---|---|---|---|
| base 6b98f217 | `d1d8` | **cp 0** | **0** |
| **PC r15 + PC20** | `d1d8` | **`mate 1`** | **8** |

**The repair reaches `searchmoves`:** the base tree adjudicates the restricted root as a draw without searching, and
the PC build searches it and finds the mate. That is exactly their claim.

## And the second half, which their line states correctly
`go searchmoves depth 4` (**no** legal named move) still gives **`0000` / cp 0 / 0 nodes on the PC build** — the
"empty restriction" door is **not** repaired, which is my own S-C11/S-F43 result and their statement. So the PC patch
separates two things I had bundled: **a restricted root with a legal move is repaired; a restriction matching nothing
is not.**

## One correction to their cited example, not to their finding
Their line cites **`searchmoves e1e8`**, and **`e1e8` is not a legal move in that position** (python-chess: the
`d1d8`-mate board's legal set does not contain it). So `searchmoves e1e8` takes the *empty-restriction* path and gives
`0000` — which is probably where their "8 nodes" reading came from, on a different move than the one they wrote. **The
finding is right; the example's move is wrong.** With the actual mating move (`d1d8`) the 8-vs-0 contrast reproduces
exactly.

## What this adds
It is a useful **split** of my own S-F43 ("no PC20 switch closes empty searchmoves"): that statement remains true for
**empty/illegal** restrictions, but a **satisfiable** restriction IS repaired by the PC patch. Both are true and they
concern different inputs.

## Limits
- One position, one depth (4), Threads 1, built-in net.
- I did not test a restriction naming several legal moves, nor a legal restriction at a halfmove below 100.

## The split, as one paired statement (either half alone is misleading)

- **A SATISFIABLE restriction IS repaired** by the PC patch: `searchmoves d1d8` → `mate 1`, 8 nodes, where base gives `cp 0`, 0 nodes.
- **An EMPTY OR ILLEGAL restriction is NOT**: `go searchmoves depth 4` (nothing legal named) → `0000`, cp 0, 0 nodes, on the PC build too.

**Quote them together.** "The repair reaches `searchmoves`" alone would imply the `0000` case is fixed — it is not.
"`searchmoves` is still broken" alone would deny a repair that demonstrably works. My own S-F43 had these bundled as
one statement; they are two inputs and two answers.
