## 2026-11-16T22:22:54Z
seat 21, area 1 (FEN INPUT). **Threads 1 in every run.** Both builds: base 6b98f217 and PC r15.

**HEADLINE: 21-F9 is REPAIRED on the PC build.** Base tree misses a mate in 1 at halfmove 100
in both colours; PC build finds it in both colours, under PC20 AND with no setoption. Cause
isolated to the compile-time FORGE_FIX_ROOT_DRAWN, not the PC20 options (base + S14 still
misses). `job18/isolate/summary.md`.

**Three finds SURVIVE on the PC build** (all Threads 1, PC20 and no-option runs agree):
- 21-F8: fullmove 0 still refused → stale board (perft 20 vs true 15).
- 21-F11: checkmated root still scored `mate 0`.
- 21-F2: refused FEN still answers readyok and the next search plays the old game.

**PC build verified**: patch sha256 d6bd72c5… matches file 5; all three honesty rows match
(default 312866/862329/3024920/4865609, S14 242796/656517, PC20 278024/587276).

**Next**: check whether 21-F11 (`mate 0`) also affects stalemate and insufficient-material
roots on the PC build, and run the area-1 job 1 mutation sweep on the PC build under PC20.
