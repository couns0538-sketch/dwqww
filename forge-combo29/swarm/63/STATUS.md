# Seat 63 — repair verification of the drawn-root repair

Branch: `for-fable-and-opus/swarm-63` · base `6b98f217` · folder `forge-combo29/swarm/63/`

## 2026-11-17T04:1x

Starting position of this seat: an adversarial review of the composed drawn-root repair
(seat 12 `two_doors_mate.patch.txt` + seat 27 `drawn_root_reporting.patch.txt`).

Done so far, all measured, none typed:

1. **Composition reproduced.** Both application orders give one identical file:
   sha256 `24912a43d315243f2f9dcb0ea032e7160633b99483c0a5e26541e870b2a26671`.
   Mate-first: `EXIT_mate=0`, `EXIT_report=0` (report hunk lands at 2275, offset 19).
   Report-first: `EXIT_report=0`, `EXIT_mate=0`.
   Using ONE `-p1` level for both patches fails loudly, not silently:
   `patch` exits 1 with `1 out of 1 hunk ignored` in both directions.

2. **Four honesty pins, release, DEFAULT options:** base and patched both give
   312866 / 862329 / 3024920 / perft 5 = 4865609. Patch moves nothing.

3. **ASan+UBSan builds:** `nm -C forge | grep -c __asan_` = 35, `__ubsan_` = 15 on both
   the base and the patched ASan build, so a "0 sanitizer lines" result on those is not
   vacuous. Pins under the sanitizer are being run now.

4. **First adversarial matrix result (release, `go depth 8`, Threads 1):** the base defect
   is real and the repair fixes it. Fixture B (exactly one mate at halfmove 100) has
   bestmove `b3a3`; the BASE plays `b3b1`, which is not a mate.
   Every drawn root on the base reports `max depth 8` with `nodes 0`; on the patched
   build the same roots report `max depth 1` with `nodes 0`.

## Next

- Cost of the per-move scan (item 3 of the assignment): whether it is paid on EVERY
  search or only on drawn roots. The patch text gates the loop on
  `root_draw_adjudicated`, so my prediction is "drawn roots only" — unmeasured as yet,
  and this is the question that decides shippability.
- Pins on the two ASan builds.
- Wire comparison of the depth reporting before/after.
- FINDINGS.md with the ship/no-ship verdict.
