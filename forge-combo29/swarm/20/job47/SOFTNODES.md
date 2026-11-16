# seat 20 — job 47: `go softnodes N` on the PC build under PC20, Threads 1 (the PC's self-play path)

Suggested area from FABLE_TO_swarm_6, and the owner's real self-play uses `go softnodes 2000`. Questions asked:
deterministic run to run? stops at a finished depth? how far past N? All answers below are **5 fresh processes per
cell**, PC r15 build, PC20, `Threads 1`, `Hash 16`.

## Answers

1. **Deterministic: YES, 12 of 12 cells, 5/5 identical each.** Score, bestmove AND node count were identical across
   all five runs in every cell — including the node count, which is the strictest test.
2. **Stops at a finished depth: YES.** In every cell the number of `info depth` lines with a pv equals the number of
   lines (`pv-lines n/n` in the table) — every reported depth carries a pv, so no partial iteration is published.
3. **How far past N: between +5.4 % and +106 %**, position- and N-dependent:

| position | softnodes 500 | 2000 | 5000 | 20000 |
|---|---|---|---|---|
| real game G1 (`1r6/2k2pp1/...`) | 626 (**+25.2 %**) d4 | 2,671 (**+33.6 %**) d7 | 5,852 (**+17.0 %**) d9 | 31,779 (**+58.9 %**) d12 |
| real game G2 (`r3r1k1/...`) | 532 (**+6.4 %**) d5 | 3,312 (**+65.6 %**) d8 | 6,124 (**+22.5 %**) d9 | 21,089 (**+5.4 %**) d11 |
| startpos | 971 (**+94.2 %**) d5 | 4,121 (**+106.0 %**) d7 | 6,170 (**+23.4 %**) d8 | 21,600 (**+8.0 %**) d12 |

Bestmoves and scores were stable across N within each position (G1 always `g7g6`, startpos always `d2d4`).

## The contrast that makes the overrun meaningful
The **hard** limit on the same build and position does not overrun: `go nodes 2000` → nodes 1,574 (×3 identical),
`go nodes 5000` → 3,891 (×3 identical). So a "soft" overrun is a property of `softnodes` specifically — it stops at
the END of the current iteration, which is exactly the documented intent — and not a harness artefact.

## What this means for the owner
- **The PC's self-play is reproducible.** `go softnodes 2000` gives the same move, score and node count every time,
  so a self-play game can be replayed exactly. That is a stronger guarantee than the matches need and it is worth
  knowing it holds.
- **The real node budget for `softnodes 2000` is 2,671–4,121 nodes on these positions**, not 2,000 — up to +106 %.
  Any timing or cost model that assumes "2000 nodes" under-counts by up to a factor of two on startpos-like
  positions. For match cost estimates this matters; for strength it does not.
- Every published depth is complete, so a depth-based consumer (pv, mate scores) can trust the last line.

## Honest limits
- Three positions (two from real games, one startpos). The overrun percentage varies with the position, so the
  spread I measured is a sample of that variation, not a bound.
- The PC's own games use its trained net, which is not shared; these are built-in-net numbers. The *determinism*
  conclusion is a property of the search, not the net, but the specific node counts would change.
- `Threads 1` only, as the rule requires, and as the PC plays.
- I did not test `softnodes 0` or a softnodes value near the 26-node root-iteration boundary (my S-C26).

## Rule-1 controls (asserted in the script)
A planted fake engine returning a random node count per run was flagged NON-deterministic (nodes 1846/1868/2028/
2073/2155), and a planted constant one passed; the script aborts if either control misbehaves. So "deterministic
5/5" is shown, not assumed.
