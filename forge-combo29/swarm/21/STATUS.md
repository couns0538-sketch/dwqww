## 2026-11-16T22:31:17Z
seat 21, area 1 (FEN INPUT) + protocol edges. **Threads 1 in every run.** Builds: base 6b98f217,
PC r15 (ASan+UBSan builds of both; PC Release verified against file 5).

**New this cycle**
- **21-C8 CONFIRMS 24-C1**: on my own harness the base build gives the "no legal named move" info
  line + `0000` for an illegal name and for no name, one/two legal names search normally.
- **21-F12 NEW**: the PC build's drawn-root repair REACHES `searchmoves` — at halfmove 100
  `go searchmoves e1e8 depth 4` searches 8 nodes on the PC build vs 0 nodes on the base build.
- **21-C7 CONFIRMS 30-F1** on both builds (seven `go` forms, one legal bestmove after `stop`).
- **21-F11 WITHDRAWN by me**: `mate 0` on a checkmated root is correct UCI, not a fault.

**Area-1 state on the PC build**: F9 repaired; F8, F2 still open; F10 identical; F12 new.

**Next**: check whether `position fen ... moves` and the illegal-prefix rule behave the same on the
PC build (job16 proved the form on base), then look at the PC patch's NNUE path for a
sanitizer-only run.
