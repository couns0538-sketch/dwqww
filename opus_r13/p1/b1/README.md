# b1 - BundlePreset=B1 (CorrHistPlus 1 + HistRework 2 + CuckooRep + TtPruneV2) on the lock tree, LTO+PGO -Expose - UNPROVEN

Rank 1 of R13 P1 (old results on plain builds / old bases: 69B1 H1 +11.3; confirm 69B1c +8.34, LLR 2.77 at the 3000-game cap).
Gate-ready candidate for the crew gate vs the lock FD3A5190 (UHO book first; 8moves_v3 second, never pooled). No Elo claim.

## Exe (not in git)
- `C:\o13\handoff\b1\forge_ltopgo_b1k.exe` (built at `C:\o13\w\b1k_pc1\src_copy\forge_ltopgo_b1k_pc1.exe`)
- sha256 **e950c77e7832e7f32d701bf1424d65553957ca8486e8bd1d29d922f9b1e25900** (pc1 = pc2, kit v2.3 md5 729fe727, -Expose, workload v1)
- Source: lock d4f4312 (= src_al1s198_clean) + `b1_port.patch` (`patch -p1` on a clean lock copy); how it was made:
  `../../tools/port_b1.py` after `patch -p1 -F0` of A1 a8b63aae and C6 2cb0babd (see IDEA_SOURCE.md).

## Gate line (engine A = this exe; engine B = lock FD3A5190, no options)
```
setoption name BundlePreset value B1
```
Equivalent explicit lines (same nodes): `CorrHistPlus 1`, `HistRework 2`, `CuckooRep true`, `TtPruneV2 true`.

## PC precondition (check before game 1)
- exe sha256 as above; OFF bench (no setoption) d11..d22 = 312866/862329/3024920/12389307/34048354.
- With the gate line: **bench 13 = 758456 nodes** (d11..d22 = 280182 / 758456 / 3357587 / 11208630 / 20560049).

## Port proof (binding): identical nodes to forge-bundle-int b7c17722 (BUNDLES.md, AL1 net, same OFF pins)
| config | forge-bundle-int (BUNDLES.md) | this port, plain build | this port, LTO+PGO |
|---|---|---|---|
| BundlePreset B1, d11/13/16/20/22 | 280182/758456/3357587/11208630/20560049 | same | same |
| TtPruneV2 only | 309157/736967/2960397/12062561/34293668 | same | - |
| CorrHistPlus 1 only, d11 | 318363 | 318363 | - |
| OFF | 312866/862329/3024920/12389307/34048354 | same (+ perft, per-FEN d13 nodes) | same |
Line set vs the original feature commits (A1, C6 x3, C2): differences are the O3-split layout lines (macro instances,
.inc includes, search_options.hpp/options.inc/thread_data.hpp declarations), which the port expresses as one template
parameter and an options block in search.hpp, plus TtPruneV2/BundlePreset lines that are not in those commits
(they come from forge-bundle-int; FB2-J3's own diff also holds CorrHistV2/SingularV2/LmrTableV2). logs/b1_lineset_vs_original_commits.txt.

## Checks (evidence in ../logs/)
| check | result | evidence |
|---|---|---|
| pc1 = pc2 exe sha256 | PASS (e950c77e…) | logs/kit_b1k/SUMMARY_pc1.txt, SUMMARY_pc2.txt |
| OFF pins d11-d22, perft 4865609/193690690, per-FEN d13 nodes (plain = LTO+PGO) | ALL OK | logs/kit_b1k/off.compare.txt |
| ON BundlePreset=B1 (plain = LTO+PGO, live) | 280182/758456/3357587/11208630/20560049 | logs/kit_b1k/opt1.compare.txt |
| ON CorrHistPlus=7 (all keys; plain = LTO+PGO, live) | 317529/866764/2715911/8754177/26756688 | logs/kit_b1k/opt2.compare.txt |
| real -Wmissing-profile warnings / vfmadd | 0 / 0 | SUMMARY |
| uci: CorrHistPlus 0, HistRework 0, CuckooRep false, TtPruneV2 false, BundlePreset OFF; parameters CorrContWeight / CorrMinorWeight / CorrNonPawnWeight 100 | PASS | logs/b1.json |
| T1/T4 go movetime 1000, 4 positions, OFF and B1: bestmove legal (engine's own go perft 1) | 16/16 | logs/b1.json |
| mate probe (22 forced mates, 3M nodes, TtPruneV2 prunes): mates found OFF 19, B1 21; no mate lost | PASS | logs/b1.json |
| CI ASan+UBSan self-play (Linux g++ 13.3): default / B1 / max (CorrHistPlus 7, HistRework 3, CuckooRep, TtPruneV2, weights 300): 0 sanitizer lines, 0 illegal | PASS (run 41210111829, job b1) | logs/ci_san_41210111829_b1.txt |

Notes
- CuckooRep's 8 R3 macro instances are one template parameter here (`search<true>` / `qsearch<true>`); the wrappers
  (`search_cuckoo` / `qsearch_cuckoo`) are bundle-int's cuckoo.inc unchanged. OFF runs `search<false>` = the lock body.
- B2-B4 are not offered (BundlePreset var OFF, B1): they need CorrHistV2 / LmrTableV2, which are not ported.
