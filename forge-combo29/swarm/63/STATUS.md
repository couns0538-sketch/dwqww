# Seat 63 — STATUS

Branch `for-fable-and-opus/swarm-63` · base `6b98f217` · folder `forge-combo29/swarm/63/`

## 2026-11-17T04:35Z — VERDICT: SHIP BOTH PATCHES

Everything below is measured; scripts and raw output are in `job1/`.

**1. Composition.** Both orders give one byte-identical `search.cpp`,
sha256 `24912a43d315243f2f9dcb0ea032e7160633b99483c0a5e26541e870b2a26671`.
Every application's exit code checked individually (0/0 both ways). The warned `-p1` trap
is loud, not silent: wrong strip level exits 1 with `1 out of 1 hunk ignored`.

**2. Honesty pins.** Release and ASan+UBSan, base and patched, DEFAULT options:
312866 / 862329 / 3024920 / perft 5 4865609 on all four builds, zero sanitizer lines.
Instrumentation is not vacuous (`__asan_` 35, `__ubsan_` 15; a planted heap over-read is
caught by the same runner).

**3. Scan cost — the question that decided shippability.** Paid on drawn roots only:
- 0 of 125 non-drawn roots entered the scan (5 constructed, 120 random real positions,
  76 of which have 30+ legal moves);
- 13 of 13 drawn roots did (6 constructed, 7 real KQvK/KRvK endgames).
Cost when it runs: 220–280 ns per legal move, 5–9 µs per drawn root, against a 20–80 ms
depth-12 search. **The "cost on every search" defect is not present.**

**4. Adversarial families.** All seven handled correctly. The decisive one: at halfmove 100
with exactly one mate available, base plays `b3b1` (not a mate, `cp 0`); patched plays
`b3a3` (`score mate 1`). Stalemate, non-mating check, and mate-in-2 correctly do NOT
cancel the adjudication. A threefold root that also has a mate gives base `h1f2` vs
patched `b3a3`/`mate 1`.

**5. `depth 1` contract.** 16 observations, no violation. Drawn root: base 8 lines to
`depth 8`, patched 1 line at `depth 1`. Under `go infinite`/`movetime`/`nodes` the base
claims `depth 64` with 0 nodes; patched claims `depth 1`. Normal searches after drawn roots
are node-identical (16646).

**Open cosmetic items:** the patch comment "adjudication is exactly as before" is slightly
too strong (`searchmoves` excluding the mating move now searches); `std::min(1, max_depth)`
is inert because `max_depth` is clamped to >= 1.

## Next

Nothing outstanding. Report and findings are pushed; no PR opened, per the brief.
