## 2026-11-17T00:29:29Z (from `date -u`)
seat 21. **Threads 1 in every run.** PC build r15 under PC20 unless stated.

**1. 21-F12 / seat 20's correction — a BOARD MISMATCH, not an error.**
Seat 20 says `e1e8` is illegal on my board. It is not: my board is rook-on-**e1**
(`6k1/5ppp/8/8/8/8/5PPP/4R1K1`, 20 legal moves, `e1e8` legal and mating) and my recorded output for it
is **8 nodes** on the PC build. Seat 20's board has the rook on **d1** (`…/3R2K1`), where `d1d8` is the
mating move and `e1e8` is illegal. Both measured just now side by side:

| board | mating move | base | PC20 |
|---|---|---|---|
| mine, rook e1 | `e1e8` | 0 nodes | **8 nodes** |
| seat 20's, rook d1 | `d1d8` | 0 nodes | **8 nodes** |

I did **not** change the move — that would describe a position I never measured. The finding line now
names the FEN. `21-C19`. The split we agree on is recorded: a restriction naming at least one legal move
is repaired by the PC patch; an empty or all-illegal restriction is not (still `0000`, 0 nodes — which I
verified independently in job23).

**2. 21-F22 call-out to seat 03** is in the finding line, addressed, with what its existing four switch
variants could settle that I did not (WHICH switch carries the node explosion). I have no channel to
seat 03 and write nothing to its branch.

**3. Job40 is now DONE — 21-F23.** Wider window (counters 85–94) via `go nodes` only, so 21-F22 cannot
poison it: **0 hits** on the **52.6 %** of move-pairs decided exactly (182 of 346). All **13** positions
offering a draw-saving move had it taken at both `go nodes 20000` and `100000`. The **7 undecided**
positions are labelled undecided, never no-hit.
Combined with 21-F21 (0 of 50 in the 1–5 window): **no position has produced a move whose forced result
was worse than an available alternative.**
Three failed runs before it are recorded in `job40/stamps.txt` (500 s wall; the 21-F22 timeout; a
`KeyError` from my own rename). None yielded a claim.

**Next**: the design note's acceptance test as a runnable spec — a drawn root with a mate must report
`mate 1`, a drawn root without one must report `cp 0`, pins unmoved — so the owner can apply
`DESIGN_drawn_root.md` and check it in one command.
