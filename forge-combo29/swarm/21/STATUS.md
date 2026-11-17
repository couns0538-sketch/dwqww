## 2026-11-17T01:03:54Z (from `date -u`)
seat 21. **Threads 1 in every run.** PC build r15 under PC20 unless stated.

**NEW and important: 21-F24 — the PC build's drawn-root mate repair is SHALLOW-ONLY.**
Board `6k1/8/5K2/8/8/8/8/7Q w - - 100 60` is **mate in 2 by SIX verified moves** (`h1b7`, `h1h5`, `h1h4`,
`h1h3`, `h1h2`, `h1g2`; no mate in 1 — proved by enumerating every move and every reply).

| build | drawn root, mate in 2 |
|---|---|
| **PC (PC20)** | `h1g1`, **`cp 0`** at depth 4, depth 10, nodes 20000 AND nodes 200000 — **misses it** |
| base | `h1a1`, `cp 0`, 0 nodes — misses it (it adjudicates) |

At counter 0 both builds pick a winning move (PC `h1h4`, base `h1b7`), so this is the **drawn-root path**,
not move selection. Compare with mate-in-1 at a drawn root: PC reports `mate 1` correctly. So the patch's
repair covers **exactly one ply of mate and no more** — which sharpens 21-F19 and bounds the design note:
"search the root then take the draw score" only helps if the search is deep enough to see the win.

**21-C22**: that board's distance is proved, not assumed. **A unit error of mine, four attempts**: UCI
`score mate K` counts MOVES, not plies, so `mate 2` is 3 plies; my solver mixed the two and I "fixed" it
against the wrong reference twice. The shipped solver returns MOVES and is asserted. It also **rejected a
board I had labelled mate-in-3** (it was mate in 2) — which is why this job reports mate-1 and mate-2 cases
and **no mate-3 case**: I could not verify a mate-3 board in the time and will not ship a guessed one.

**21-C20 stands**: the five-case acceptance spec (`ACCEPTANCE_drawn_root.md`, verified line by line in
21-C21) still shows base failing S1/S4 and PC failing S2/S5, pins exact on both.

**Next**: merge the mate-in-2 case into `job43/acceptance.py` so the spec's mate cases are S1 (mate 1) and
S6 (mate 2), and find a verified mate-in-3 board by search rather than by hand.
