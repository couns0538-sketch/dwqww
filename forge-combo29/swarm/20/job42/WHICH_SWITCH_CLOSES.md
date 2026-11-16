# seat 20 — job 42: no PC20 switch closes any of my four LIVE findings

My PC20 rerun (S-F33) found four of my base-tree findings still live on the PC build: empty `searchmoves` → `0000`,
`ucinewgame` resetting the board, the 1000-cluster `hashfull` window, and `go nodes 1` returning an unexamined
first legal move. A bundle result cannot say *which* switch, if any, is responsible — so I tested each PC20 switch
alone on the PC r15 build, `Threads 1`, `Hash 16` (and `Hash 1024` for the hashfull row).

| settings | F3 empty `searchmoves` | F8 `go nodes 1` | `hashfull` at Hash 16 / 1024 |
|---|---|---|---|
| defaults (no setoption) | `0000` | `c2b1` | 28 / **0** |
| S14 only | `0000` | `c2b1` | 32 / **0** |
| S14 + `CuckooRep true` | `0000` | `c2b1` | 32 / **0** |
| S14 + `HistRework 2` | `0000` | `c2b1` | 24 / **0** |
| S14 + `TtPruneV2 true` | `0000` | `c2b1` | 15 / **0** |
| S14 + `CorrHistV2 true` | `0000` | `c2b1` | 27 / **0** |
| S14 + `MateAlphaGuard true` | `0000` | `c2b1` | 32 / **0** |
| **PC20 (all of them)** | **`0000`** | **`c2b1`** | **14 / 0** |

(The `ucinewgame` reset does not depend on any of these switches — it is `board.set_fen(StandardStartFen)` in the
UCI loop, unchanged by the patch — so it was not swept separately.)

## The answer
**No switch, alone or together, changes any of the four.** All four are therefore genuine open defects on the
engine the owner's PC plays, not artefacts of the PC20 bundle:

1. empty or illegal `searchmoves` → `bestmove 0000` on a board with 20 legal moves (still live; S-C2/S-C11/S-C17
   family);
2. `ucinewgame` silently resetting the board to startpos (still live; S-C3);
3. `hashfull` reading 0 at Hash 1024 while the table fills (still live; S-C10) — note the Hash-16 value moves
   between 14 and 32 depending on the search switches, but the **1024 value is 0 in every configuration**, which is
   the defect;
4. `go nodes 1` returning a first legal move without searching (still live; S-F11) — and note it returns `c2b1`
   here, not the `a2a3` I recorded on the base tree, which is a **different first move in the engine's own order**,
   consistent with S-F27 (the protocol cannot reveal that order).

## Why this matters
For the owner: these four are worth fixing on the PC's tree, and nothing about the r15 patch addresses them.
For the swarm: any seat that reports one of these on the PC build under PC20 is reporting something real, not a
bundle effect — the switch-by-switch sweep above is the evidence.

## Rule-1 note
The zero here is "no switch changes the behaviour" — the positive control is the *same four behaviours appearing*
in every row, and the `hashfull` 16-column varying (14, 15, 24, 27, 28, 32) proves the sweep really did change
search behaviour between rows rather than failing to apply the options.

## Limits
- One position per finding; `Hash 16` unless stated; `Threads 1` throughout.
- I did not sweep the seven fixed-defect switches (FORGE_FIX_*) because they are compile-time in the patch, not
  UCI options.
