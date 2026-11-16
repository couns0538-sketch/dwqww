## 2026-11-16T22:18Z
seat 21, area 1 (FEN INPUT under ASan + UBSan), branch for-fable-and-opus/swarm-21

**New since 22:08**
- job9: CHECK of seat 30's 30-F7 → **CONFIRMS**. On boards I chose (not seat 30's): a black
  mate-in-1 and a white mate-in-1 are both missed at halfmove 100 (`cp 0`, 0 nodes, non-mating
  moves) by `go depth 5` and `go nodes 100`, and both found at counter 99 (`mate 1`, 105
  nodes); a quiet rook-up board answers 0 nodes at 100 and searches 759 nodes at 99. Both
  counter-99 controls held. Every case asserts the FEN was accepted and that a `nodes` value
  was parsed, so neither the stale-board trap nor an empty parse can produce a false CONFIRMS.
  `job9/out/summary.md` via `job9/check_30f7.py`. → `21-C3`.

**Findings**: 21-F1..F10, 21-C1 (CONFIRMS 30-F6), 21-C2, 21-C3 (CONFIRMS 30-F7).

**Next**: area 1 job 3 again with a seed-2111 game (long `position startpos moves` lists),
and 08-F5 remains unchecked by anyone — I will take it if time allows.
Next command: `cd forge-combo29/swarm/21 && python3 job4/long_moves.py ~/b/asan/forge job10/out 1000`
