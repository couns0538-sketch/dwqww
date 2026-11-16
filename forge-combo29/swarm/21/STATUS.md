## 2026-11-16T22:26:03Z
seat 21, area 1 (FEN INPUT). **Threads 1 in every run.** Builds: base 6b98f217, PC r15.

**WITHDRAWN: 21-F11.** I claimed a checkmated root's `score mate 0` was a fault. It is the
correct UCI score (`mate <y>` is relative to the side to move, so y=0 is "already mated"), and
`bestmove 0000` is right. Measured, not asserted: mated → `mate 0`; can mate in 1 → `mate 1`;
stalemated → `cp 0`; consistent on BOTH builds. `job20/wd/summary.md`. Nothing to repair.

**Current state of my area on the PC build**
- 21-F9 (halfmove≥100 misses a mate in 1): **REPAIRED on the PC build** (compile-time
  FORGE_FIX_ROOT_DRAWN, not the PC20 options; base + S14 still misses it).
- 21-F8 (`fullmove 0` refused): **still open on the PC build**.
- 21-F2 (refused FEN → `readyok` → search plays the old game): **still open on the PC build**.
- 21-F10 (parser strictness on 6,073 real positions): confirmed identical on the PC build.
- 21-F10b: the 20,000-mutation sweep on the PC build under PC20 is row-identical to the base.

**Next**: look for a NEW find in the PC patch's own new code paths — the six FORGE_FIX_
switches and the four search options — rather than re-testing the repaired door.
