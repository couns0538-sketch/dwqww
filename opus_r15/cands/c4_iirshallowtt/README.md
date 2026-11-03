# C4 IirShallowTt - internal iterative reduction for a too shallow hash entry (UNPROVEN)

Gate line: engine A = `D:\o15\cands\c4_iirshallowtt\forge_ltopgo_c4iir.exe` + `setoption name IirShallowTt value 1`,
engine B = the lock. Exe sha256, ON bench and check results: `D:\o15\cands\INDEX.md` and `logs/RESULT.json`.
Patch: `c4_iirshallowtt.patch` (src/search.cpp only, +9), applies with `patch -p1` to git d4f4312.

## What it changes
The lock reduces the depth by one at PV and cut nodes (not in check, depth >= IirDepth = 4) when there is no hash
move. With the option, the same one-ply reduction also applies when a hash move exists but its entry is more than
IirDepth plies shallower than this search (`tt_depth < depth - IirDepth`). Option `IirShallowTt` (spin 0..1, default 0).

## Why it should gain
Internal iterative reduction exists because a node without a hash move will probably be ordered badly and is likely
less important than one with a good hash move; a hash move from a search more than four plies shallower carries
little of that ordering knowledge (it often comes from a quiescence or very low-depth store), so the same argument
applies to it. Searching such a node one ply shallower first keeps the work where the table already knows the
position well, and the next iteration - which then finds a deeper entry here - does the full-depth work only for the
nodes that still matter (ON bench d22 19,939,843 vs 34,048,354 nodes).

## OFF identity
`IirShallowTt 0` fails the first test: the lock's search. Kit OFF node identity ALL OK, bench d11-d22 + perft = pins.

## Own review (structured self-review, NOT independent)
- The two IIR tests exclude each other (no hash move / a hash move), so a node is reduced at most once.
- `tt_depth` is -1 without a TT hit; a hash move implies a hit, so the comparison uses a real stored depth.
- Singular extension needs `tt_depth >= depth - 3` (before the reduction), so it never runs at a node this rule
  reduces; a singular verification search (excluded move) sees a deep entry and is not reduced by it.
- Quiescence stores depth 0: positions first met in quiescence and later in the main search at depth >= 5 are now
  reduced once - that is the intended case, not a side effect.
- Risk: PV nodes after an aspiration re-search that only hit shallow entries lose one ply once; the next iteration
  restores it. Node counts at depth drop a lot (d13 724,372 vs 862,329), which is not strength by itself.
- PGO cold-path note as for every option line.
