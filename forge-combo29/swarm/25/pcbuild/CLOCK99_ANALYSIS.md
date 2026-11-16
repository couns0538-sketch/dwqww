# clock-99 break: what is PROVEN, what is NOT, and the mechanism dead-ends

Seat 25, area 5. Build PC r15 (from FABLE_TO_swarm_5) under settings PC20, and the base build under default/S14.
Every score below is Threads 1, Hash 16.

## PROVEN (each with a command in the folder)

1. **Reachability (S-F11).** A legal 99-ply move list walks a live game to halfmove clock 99:
   start `8/8/4k3/8/8/4K3/4P3/4R2r w - - 0 1`, 99 non-resetting plies, reaching
   `4k3/8/8/8/R7/8/4P1K1/4r3 b - - 99 50` — not checkmate, not stalemate, not a threefold, insufficient = false,
   and `e1e2` (a clock-resetting capture) still legal. `verify_walk.py` replays all 99 moves and asserts every
   one is legal. On the PC build under PC20 that position scores `cp 0` in 661 nodes.
   *The move list was produced by a seeded search (reach.py), so it is a constructed-but-legal continuation,
   not a game played between two thinking players.*

2. **Not introduced by the PC patch.** Identical behaviour on the base build and the PC build under all three
   settings regimes (`clock99_builds.txt`):
   | build | default | S14 | S14 + available PC options |
   |---|---|---|---|
   | base | breaks at 99 | breaks at 99 | breaks at 99 (base has only OwnBook of the six) |
   | PC r15 | breaks at 99 | breaks at 99 | breaks at 99 |
   So it predates r15 and is not caused by CuckooRep / HistRework / TtPruneV2 / CorrHistV2 / MateAlphaGuard.

3. **The onset is exactly 99**, sweep 90..100 on one board: 90-98 all normal (18k-112k nodes), 99 collapses to
   341 nodes `cp 0`, 100 is `cp 0` (correctly). `clock_onset.txt`.

4. **Clock 99 alone does NOT trigger it.** The START position as a bare FEN at clock 99 scores `cp 18` in 7,006
   nodes; the V1 board at clock 0, 50, 95, 98 scores normally. So the trigger needs the CLOCK AND the BOARD.

5. **Shape is a root shortcut**: at depth 6 the V1 board gives 187 nodes and a 1-ply PV at clock 99 and at
   clock 100 (identical), versus 2,311 nodes and a 6-ply PV at clock 0 (`clock99_rootclass.txt`).

6. **A control board at clock 99 is fine.** V3 (`...4P3/8/P1P5/...` at clock 99) scores `cp 597` in 11,360
   nodes — identical to its clock-0 answer. So not every high-clock position is affected (`clock99_which.txt`).

## NOT PROVEN — and I stopped guessing

**The mechanism.** Three specific candidates were read in the source and each is refuted by the code itself:
- `Worker::is_draw` (src/search.cpp:1426-1436) tests `halfmove_clock() >= 100` — false at 99.
- The root block's `root_drawn` (src/search.cpp:2571-2580) under `FORGE_FIX_ROOT_DRAWN` tests only
  `is_insufficient_material()`; the V1 board has full material, so this cannot fire.
- `rule50_damped_static` (include/forge/search.hpp:362-366) is inert unless `EvalRule50Damp` is on, which is
  off by default and gave the same answer when toggled on/off.

So the observed zero comes from somewhere I have NOT identified. I am recording that plainly instead of
offering a fourth guess (seat 06 set exactly this standard with S-F18). What I can say is the *behaviour*,
reproducibly, on both builds.

**Severity in real play.** I proved a legal continuation reaches the position. I did NOT play two thinking
engines to it, so "this loses games" is not claimed. What IS claimed: any game that arrives at such a position
gets a wrong score and a non-resetting move.

## Why the mechanism search is worth continuing (for the next seat)
The discriminator between the breaking board V1 and the fine board V3 is NOT the count of resetting moves
(9 vs 9), NOT check, NOT castling, NOT material. The next step I would take is an instrumented build that
prints `is_draw`'s decision at each node near the root for V1 vs V3 at clock 99 — that is area 7/9 work with a
debug build, not something I can do by black-box testing, which is what I have been doing.
