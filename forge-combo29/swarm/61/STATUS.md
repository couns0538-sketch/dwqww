# swarm/61 — verification seat, live status

**RECHECK.md is written.** **Claims examined: 39. Agree: 35. Disagree: 4.**
The header counts are verified mechanically by `verify_recheck_counts.py` (5/5), not hand-written —
my first hand-written header said 34/30/4 and the checker caught it.

## Headline

1. **D1 — the PC20 per-node row pairs a point estimate with a different estimator's interval.**
   +6.4% is the pooled ratio (1.0643); the interval [1.0670, 1.0876] is centred on the mean-of-ln
   (1.0736). The pooled estimate lies *outside* its own interval. The conclusion survives — every
   construction excludes 1.0 — so this is a pairing fault, not a dead finding.
2. **D2 — the same row's sign share is 163/180, not 162/180.** 90.0% either way.
3. **D3 — `-DFORGE_MATE_ALPHA_GUARD=1` is not the repaired build.** It yields sha256 `84bfb5d6…`,
   byte-identical to seat 19's prefetch CTRL, and it still bails on a threefold root exactly like
   base. The real repair (`FORGE_FIX_ROOT_DRAWN`) is **not committed as source in any reachable
   branch**, so every "PC r15" column in the report is traceable to prose only.
4. **D4 — the "one ply lower" board's 36 nodes is depth-12 only** (48/60/72 deeper). The finding
   that matters, that no depth fixes it, is confirmed at depth 24.

## What agrees

- All four honesty pins, re-derived on my own build: 312866 / 862329 / 3024920 / perft 5 4865609.
- Every drawn-root figure except D4: 7,581; 0; 0; the halfmove sweep 7581/7580/7723/200/0; the
  move==generator-head identity (2/2); the mate-in-one forfeit; `depth 64`/`seldepth 64`/`nodes 0`;
  the `min(depth,64)` info-line counts (10/64/64); the empty-PV detector; counters 97/98 `mate −1`.
- PC20 node saving: all 464 committed rows reproduce 0.9131 and the CI to within 0.0017 (5/5).
- Prefetch: 8/8 from committed pairs, plus an **independent re-measurement of +10.64% at n=130**
  on a rebuilt patched engine whose binary is byte-identical (`193c9a78…`) to the committed one.

## Corrections to my own earlier work

- My first 2-occurrence reading was **22,108**, not 7,581 — depth 12 plus a warm TT. With
  `ucinewgame` and the source's depth 10 it is 7,581. The report was right; I was wrong.
- My first "PC build" was byte-identical to base because `CMAKE_CXX_FLAGS` did not reach the
  compiler. Rebuilt correctly; it is still not the repair build (D3).

## Faults in my own harness, found by running rather than reading

Each is the "waiting on the wrong line" class the report warns about:

1. `parse_search` required a token after `pv`, so it **skipped the bail's own line** and reported
   "no info lines" instead of `nodes 0`.
2. `perft()` waited for `Nodes searched`; the engine prints **`nodes <N>`**. Hung to timeout.
3. `perft()` sent an extra `isready` after `set_position` had drained its own `readyok`.

`selftest_faults.py` plants a fault in each recheck script's evidence and requires exit 1:
**3/3 caught.**

## FEN-diagnostic finding, applied to source harnesses

Measured on my build: the diagnostic is **always emitted** and always precedes the first
`info depth`, so the safe rule is to scan from `position` through `bestmove`. Two source harnesses
(`swarm/19/checks/prefetchreal/run.py`, `swarm/23/job68/final_recheck.py`) send `isready` after
`position` and read only from `go` onward — case A, where a refused FEN is consumed silently.
Neither validates FENs. **4 of the 600 FENs in `their_600.fens` fail python-chess validation.**
The prefetch numbers are nonetheless safe, because their 130 pairs show node ratio exactly
1.000000, which a substituted position would have broken.

## Remaining

`recheck_pins.py`'s perft leg still has fault 2 above. Pins are deprioritised and verified by the
repo's own `check_pins.sh`, so I am leaving it and recording it rather than papering over it.
