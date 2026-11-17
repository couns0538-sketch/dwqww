# Exact-integer confirmations of other seats — the shape the FINAL draws from

seat 19 · area 9 · every check I ran on another seat's finding that reproduced **exact integers**, not
approximations and not derived tables. This is the part of my work that survived my own oracle retraction.

| id | seat checked | what was reproduced | how exact |
|---|---|---|---|
| **19-C19** | 29-F4 (king lines) | `refresh_king_lines` **804,371** calls, **779,027** from `has_legal_move` | **digit for digit**; plus new bench-16 (2,826,465 / 2,731,439) and PC20 (547,691 / 532,093) |
| **19-C23** | 25's counter sweep | counter 0 → `mate -16` at **7,608,471** nodes; counter 1 → `mate -16` at **15,702,225** | **2.06×**, its claim reproduced; plus the depth qualifier (at depth 20 counters 0–50 are identical) |
| **19-C25** | 21-F12 (searchmoves) | PC r15 **8 nodes / `mate 1`**; base **0 nodes / `cp 0`** | its claim exactly; plus the empty-PV observation |
| **19-C26** | 24-F31 (Threads-1) | **40 of 40** positions identical in **move and node count** | independently, on my harness, base tree |
| **19-C27** | 05's S-F58 | `mate +11` / **44,749** nodes / **18-ply** PV / depth 11 at `nodes 50000`; `mate +7` / **138,869** / 13-ply / depth 14 at 250,000 | **all five figures**, digit for digit |

## Why this is the right shape for the FINAL

**Every one is a reproduction of an integer someone else published, or a counter I read from the engine's own
output.** None depends on a derived table — which matters because my one derived table (the DTM oracle) turned out
to be wrong and was retracted (19-R2, trap 11).

**19-C26 is the strongest reproducibility result of the night**, and it supports my own Threads-1 claim
(19-F24) **from the other direction**: I asserted my results were Threads-1 because I never set the option;
seat 24 asserted Threads 1 is bit-exact; and I then verified 40 of 40 identical move-and-node-count pairs on
**an independent harness from the one that made the claim.** Two seats, two harnesses, same conclusion.

## The rule these follow

**Reproduce an integer, or read a counter. Do not re-derive a value and report it as fact** unless the derivation
has been spot-checked cell by cell — which is the lesson of `RETRACTION_dtm_oracle.md`.
