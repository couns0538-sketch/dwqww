# Leaf clock-100 mate rule — findings

Seat: owner-audit of `forge-combo29`. Base commit `6b98f217`.
Everything below is measured on builds made from that commit; nothing is quoted from another seat.

## Verdict: SHIP the leaf patch, ON TOP OF both shipped root patches. Pin cost zero.

The rule at `search.cpp:1302-1304` scored every node at halfmove >= 100 as a draw unless the
side to move was checkmated. That is one ply too low, and it is direction-dependent in the way
the brief described. The patch makes the clock-100 node worth **mate** when the side to move has
a move that mates at once, and a draw otherwise.

It fixes the whole band, not one cell: **14/14 band cells correct against an independent oracle,
where base and the two-patch tree are both 12/14 and miss exactly the two cells that a one-cell
repair would also have missed.**

---

## 1. What the defect actually is, derived from the code

`is_draw` fires at `halfmove_clock() >= 100`. In a search, a node at ply `q` from a root whose
clock is `H` sits at clock `H + q`. So the node at ply `p - 1` (the parent of the would-be mating
move at ply `p`) sits at `H + p - 1`, and it is **refused expansion** once that reaches 100:

```
base band:   a mate at ply p is found  iff  p <= 100 - H      (else the parent is a draw node)
```

That is exactly the coordinator's 80/80 measurement: `p=2` starts missing at `H=99`,
`p=4` at `H=97`, `p=6` at `H=95`. It is not about "halfmove 99"; it is a band, one cell wide per
mate length.

## 2. The correct rule, and why the boundary is one ply later

`p <= 101 - H` is the truth, not `p <= 100 - H`. The fifty-move draw is a **claim**, and
FIDE 9.3 makes a claim **optional**. Two consequences the old leaf rule conflated:

- A move that **mates** ends the game immediately. The opponent never gets to claim, so a mate
  delivered at clock 100 **beats** the draw.
- Any **other** move passes the turn over at clock `>= 101`, where the opponent simply claims.
  So a mate in one is the **only** continuation at the limit that is not a draw.

Therefore a clock-100 node has value `mate_in(1)` if the side to move can mate at once, and `0`
otherwise. Note the direction: this makes a mate **delivered by the side to move** at clock 100
count, and a mate **against** it not count — which is the asymmetry the brief described, now
derived from the rule rather than observed.

I verified this boundary with my own claim-model solver (`scripts/oracle_claim_model.py`,
python-chess move generation, exact-value TT, no bounds stored): `p=2` is a genuine mate through
`H=99` and a genuine draw at `H=100`; `p=4` is a genuine mate through `H=97` and a draw at `H=98`.
The old band was missing the cell one ply before each of those.

## 3. The change

`src/search.cpp` + `include/forge/search.hpp`. `is_draw` becomes a thin wrapper over a new
`leaf_score`, which returns `ValueNone` when the node must be searched. The two leaf call sites
(`search`, `qsearch`) use the returned score directly. A new `has_mating_move` scans only the
**checking** moves (only a check can mate), making and unmaking the board in place.

Checkmate is deliberately **not** settled in `leaf_score`: it returns `ValueNone`, and the
caller's move loop scores a node with no legal reply as `mated_in(ply)` exactly as before. That
keeps all existing mate accounting untouched. **This is a fix I had to make to my own first
attempt, and it is the one error worth recording**: my first version returned a draw for a
checkmated node at clock >= 100, which regressed `H=98`/`p=2` from `mate -1` to `cp -3331` and
`H=96`/`p=4` from `mate -2` to `cp 0`. The band sweep caught it; reading the code had not.

No other file changes. The change is 4 call-site lines and two new helpers; nothing else in the
search is touched.

## 4. Acceptance cells, and the ones a narrow fix would miss

Band cells for `p=2` (fixture `6k1/8/5PPP/8/8/8/8/R6K b`) and `p=4` (fixture `6k1/8/6K1/8/8/8/8/R7 b`),
scored against the oracle. `H=100`/`H=98` cells are the **root guard** (0 nodes) and are kept
separate by node count, as the brief requires.

| fixture | H | truth (oracle) | base | composed (12+27) | **fixed** |
|---|---|---|---|---|---|
| p=2 | 98 | mate -1 | mate -1 | mate -1 | mate -1 |
| p=2 | **99** | **mate -1** | **cp 0 (36 n)** | **cp 0 (36 n)** | **mate -1 (36 n)** |
| p=2 | 100 | cp 0 (root guard) | cp 0 (0 n) | cp 0 (0 n) | cp 0 (0 n) |
| p=4 | 96 | mate -2 | mate -2 | mate -2 | mate -2 |
| p=4 | **97** | **mate -2** | **cp 0 (634 n)** | **cp 0 (634 n)** | **mate -2 (506 n)** |
| p=4 | 98 | cp 0 | cp 0 (301 n) | cp 0 (301 n) | cp 0 (301 n) |

The two bold rows are the whole point. Both search real nodes (36 and 634) so they are genuine
band cells, not the root guard. **Base and the two-patch tree score identically on all 14 cells —
12/14 — and the fixed build is 14/14.** A repair validated only on `H=99`/`p=2` would leave the
`p=4` cell wrong and this table is how that would have been visible.

`H=100`/`H=98`/`H=99` on the p=4 fixture remain `cp 0` **and the oracle agrees they are draws**,
so the unchanged cells are correct rather than merely unchanged.

## 5. The control, and why it is a different code path

`6k1/5ppp/8/8/8/8/8/R5NK b - - 99 40` stays `cp 0` on all three builds (227 nodes at H=99,
487 at H=98), unchanged by the patch. It is correct because Black has six pawn moves that reset
the clock — measured with python-chess, not asserted.

**The control must not be pooled with the band cells**, and here is the separation by node count
the brief asked for: this control returns a **searched** `cp 0` from a real evaluation (227 nodes),
whereas a bare-king or root-guard draw returns `cp 0` with **0 nodes** from the root guard. Those
are two different code paths and my harness keeps them apart: the band sweep only counts cells
whose base node count is `> 0`, and the seven families include bare-king and insufficient-material
cases explicitly as 0-node root-guard cases.

## 6. Honesty pins — all 11, bit-identical, on four builds

`LOCK.md` pins, Threads 1, Hash 16, OwnBook false: net on `bench 11/13/16/20/22`, net off the
same five, and `perft 5`.

| build | b11 | b13 | b16 | b20 | b22 | n11 | n13 | n16 | n20 | n22 | perft5 | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| base | 312866 | 862329 | 3024920 | 12389307 | 34048354 | 375354 | 907205 | 2448617 | 13573040 | 24506465 | 4865609 | PASS |
| composed | 312866 | 862329 | 3024920 | 12389307 | 34048354 | 375354 | 907205 | 2448617 | 13573040 | 24506465 | 4865609 | PASS |
| **fixed** | 312866 | 862329 | 3024920 | 12389307 | 34048354 | 375354 | 907205 | 2448617 | 13573040 | 24506465 | 4865609 | PASS |
| **fixed ASan+UBSan** | 312866 | 862329 | 3024920 | 12389307 | 34048354 | 375354 | 907205 | 2448617 | 13573040 | 24506465 | 4865609 | PASS |

The four honesty pins named in the brief — 312,866 / 862,329 / 3,024,920 / perft 5 4,865,609 —
are bit-identical on release **and** on ASan+UBSan, which also produced **zero** sanitizer lines
across the whole pin run.

**The sanitizer is proved to have run**: `scripts/planted_fault.sh` plants a heap overflow inside
`has_mating_move` — the function this patch adds — builds ASan+UBSan, and requires a report that
*names that function*. It does:

```
runtime error: store to address 0x5020000010ac with insufficient space for an object of type 'volatile int'
ERROR: AddressSanitizer: heap-buffer-overflow
SUMMARY: AddressSanitizer: heap-buffer-overflow ... in forge::Worker::has_mating_move(forge::Board&) const
```

**Pin cost: zero.** The rule only fires at clock `>= 100`, and no bench FEN reaches one, so all
eleven pins are unchanged by construction — and measured, not merely argued.

## 7. It does not search one ply deeper everywhere

40 ordinary positions (the 8 bench FENs + 32 positions from real opening lines, all at ordinary
clocks), depth 14, base versus fixed, Threads 1:

- **node+score identical: 40/40**
- **positions with any node delta: 0/40**
- **max |delta|: 0.0000 %**

So the fix is not "one ply deeper": a deeper search would move every one of these. The change is
confined to nodes at the clock limit.

## 8. Adversarial families: 7/7, and the base fails the ones that matter

| family | base | composed (12+27) | **fixed** |
|---|---|---|---|
| F1 fifty-move, one mate (hm100) | FAIL (0 n, cp 0) | PASS (216 n, mate 1) | PASS (216 n, mate 1) |
| F2 fifty-move, two mates (hm100) | FAIL | PASS (216 n) | PASS (216 n) |
| F3 near-miss stalemate | PASS (cp 0) | PASS (cp 0) | PASS (cp 0) |
| **F4 mate at the boundary (hm99, p=2)** | **FAIL (cp 0)** | **FAIL (cp 0)** | **PASS (mate -1)** |
| F5 near-miss mate-in-2 at hm100 | PASS (cp 0, 0 n) | PASS | PASS |
| F6 insufficient material | PASS (cp 0) | PASS | PASS |
| F7 threefold root that also mates | FAIL (0 n, cp 0) | PASS (216 n, mate 1) | PASS (216 n, mate 1) |

Totals: base **3/7**, composed **6/7**, fixed **7/7**.

**F1, F2 and F7 are the root repair's cells and are already fixed by the shipped patches** — this
patch adds nothing there and breaks nothing there (node counts and scores byte-identical). **F4 is
the leaf cell, and it is the one only this patch fixes.** F3, F5 and F6 are near-misses that must
*not* cancel, and they do not on any build. Every mate claim is checked with python-chess against
the printed best move, never against the engine's own score.

## 9. Composition with both shipped patches

- The two shipped patches alone compose to `search.cpp` sha256 **`24912a43d315243f2f9dcb0ea032e7160633b99483c0a5e26541e870b2a26671`** — reproduced here, matching the brief.
- Adding this seat's patch in **either order** gives **`257f177c818eb40e0d37d963b82875ad0f97c4eee2723b55e21d430397d18311`** for both orders (`scripts/compose.sh`, `evidence/compose.txt`).
- **Reverse-applying this seat's patch to the fixed tree restores `24912a43…` byte-for-byte**, which is the strongest available statement that the fix is *exactly* the two shipped patches plus this change and nothing else.
- This seat's patch also applies cleanly to the **bare base** (sha256 `c899e7e2…`), so it is independent of the other two.
- **The `-p` trap is real and is handled**: seat 12's hunks name `a/forge-combo29/src` so they need `-p2` from inside `forge-combo29/`; seat 27's and this seat's name `a/src` so they need `-p1`. One flag for all three silently skips seat 12's hunk — which is exactly what happened on my first attempt.

The whole 11-pin set and the 14-cell band sweep were run on the fully composed tree, not on this
patch in isolation.

## 10. What this fixes, and what it is worth

**It fixes a rare miss correctly. It does not recover lost games.** The exposure bound the brief
gives — 798 of 792,081 plies inside the band across 5,689 games, one with a forced mate, and that
one in the FOUND cell — is the honest scale, and I did not attempt to reproduce that corpus. An
independent, much cruder probe of my own (200 uniform-random games, 65,453 plies) found **350
plies at clock >= 98, i.e. 0.53%**, consistent with "reachable and rare". Uniform-random play
resets the clock constantly, so that figure is an upper-ish bound on the *opportunity*, not on
the *cost*.

Two limits worth stating rather than burying:

- **A mate in two or more at a clock-100 node is still adjudicated drawn** (F5). That is
  *correct*, not a limit of the patch: at clock 100 the side to move has only a mate in one
  available before the opponent can claim, so a longer mate is genuinely unavailable to it. The
  oracle agrees F5 is a draw.
- **The claim itself is still modelled as forced by the engine at clock >= 100 for the
  *opponent***. The patch only adds the one exception the rules compel. It does not implement
  optional-claim semantics generally, and the findings doc records that a general
  claimable-draw fix must not be layered on the root patches (it moves three bench pins). **This
  patch does not move any pin**, so it does not have that problem.

## 11. Reproduce

```
scripts/compose.sh   /path/to/dwqww evidence/compose.txt     # byte-identity, both orders
scripts/pins.sh      ./forge evidence/pins.txt               # the 11 pins
scripts/sweep_band.py ./forge                               # the 14 band cells vs the oracle
scripts/delta_40_positions.py base/forge fixed/forge 14 out.json
scripts/seven_families.py ./forge out.json                   # 7/7
scripts/planted_fault.sh /path/to/fixed/tree out.txt         # the sanitizer really runs
```

Build trap, as given: `/usr/bin/c++` is clang 18 with a broken header path. Build with
`-DCMAKE_CXX_COMPILER=/usr/bin/g++` and `LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13`.
