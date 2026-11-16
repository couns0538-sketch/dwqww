# S-F14 — the one-ply-down draw short-circuit is STILL OPEN on the PC build (r15), and no depth fixes it

Seat 12, area 2. This is my base-tree finding S-F4 re-run on the PC build as file 5 requires, and
it is the opposite of the root door: **the root door is repaired on r15, the node-level one is not.**

**Threads 1 throughout** (no `Threads` option is sent). Builds: base release 6b98f217, PC r15 =
base + `pc_r15.patch` (`-DFORGE_MATE_ALPHA_GUARD=1`), pinned 8/8 in `job3/PC_BUILD.md`.

## The position and why `cp 0` is wrong

```
6k1/8/5PPP/8/8/8/8/R6K b - - 99 40
```

Black to move. Black has **exactly two legal moves**, `g8h8` and `g8f8`; both keep the halfmove
counter at 100 (no pawn moves and no captures exist for Black), and on both children White mates at
once with `Ra8#`. python-chess confirms each child (e.g. after `g8h8`: `7k/8/5PPP/8/8/8/8/R6K w -
- 100 41`, mate `a1a8`). The truth is therefore **mate -1**: Black is lost by force.

## Measured — base vs PC r15, only the counter changes

| halfmove | base 6b98f217 | **PC r15** | truth |
|---|---|---|---|
| 97 | g8h8 / **mate -1** / 63 nodes | g8h8 / **mate -1** / 63 nodes | mate -1 ✔ |
| 98 | g8h8 / **mate -1** / 63 nodes | g8h8 / **mate -1** / 63 nodes | mate -1 ✔ |
| **99** | g8f8 / **cp 0** / 36 nodes | g8f8 / **cp 0** / 36 nodes | **mate -1 ✘** |
| 100 | g8f8 / cp 0 / 0 nodes | g8f8 / **cp 0 / 36 nodes** | (root drawn) |

Two separate facts in that table:

1. **At 99 both builds are wrong, identically** — 36 nodes, `cp 0`, the losing side credited with a
   draw it cannot reach.
2. **At 100 the builds differ, and the PC is the better one**: base answers from the root
   adjudication in 0 nodes (the `root_drawn` defect); r15 *searches* (36 nodes) and still reaches
   `cp 0` — because the node-level return catches both children, not because of the root.

## Deeper searches do not fix it

| depth | PC r15 at halfmove 99 |
|---|---|
| 8 | g8f8 / cp 0 / 24 nodes |
| 12 | g8f8 / cp 0 / 36 nodes |
| 16 | g8f8 / cp 0 / 48 nodes |
| **20** | **g8f8 / cp 0 / 60 nodes** |

The node count grows by 2 per ply and the score never moves: the tree is being cut at the two
children, so **more thinking time cannot recover this** — it is not a horizon effect.

## This is seat 25's mechanism, and here is what I add to it

Seat 25 (`swarm-25: debug/MECHANISM.md`, `debug/CORRECTION.md`) has the full explanation with an
instrumented build, and it is the better statement of the mechanism: `Worker::is_draw` returns draw
for a child whose clock is 100, which is correct for that node, but a fifty-move draw must be
**claimed** — the winning side simply resets the clock with a pawn move or capture — so scoring it 0
unconditionally treats a *claimable* draw as a *forced* one, and at clock 99 a lost position is
valued 0.

**What I add that seat 25 does not have:** the per-node growth from depth 6 to depth 24 on the same
board, showing the score never moves and the tree is cut at the child every time — so this is not a
horizon effect and no amount of search time recovers it (`job4/pc_node_level_depth_sweep.txt`), plus
the fact that it is still open on the PC build after `FORGE_FIX_ROOT_DRAWN`.
**What seat 25 has that I do not:** the instrumentation proving no root shortcut fires and that the
root's 0 is a consistent maximum over its children (`[DBG ROOT ITER SEARCHED]`, 109 `is_draw TRUE`
lines all at clock 100).

## Why, in the source (read after the measurement, and it matches)

`src/search.cpp:1426-1436` of the PC build — `Worker::is_draw`, unchanged in shape from the base
tree:

```cpp
bool Worker::is_draw(const Board& board, int ply) const {
    (void)ply;
    if (board.halfmove_clock() >= 100) {
        // Checkmate on the hundredth half-move still wins; everything else is a draw.
        return !board.in_check() || board.has_legal_move();
    }
    ...
}
```

At the two children the counter is 100, White is **not** in check, and White **has** a legal move,
so the condition returns `true` — a draw — before White's mate is ever looked at. The comment's own
carve-out ("checkmate on the hundredth half-move still wins") covers a board where the side to move
is already mated or stalemated; it does not cover "the side to move is about to mate".

`FORGE_FIX_ROOT_DRAWN` (r15, `search.cpp:2571`) only changes the *root* path; it does not touch
`is_draw`, so the in-tree return is untouched. That is exactly why the root door shows repaired and
this one does not.

## The control that keeps this honest

Same board shape with a counter-resetting escape:

```
6k1/5ppp/8/8/8/8/8/R5NK b - - 99 40
```

Black has six pawn moves that reset the counter to 0 and keep playing, so `cp 0` here is
**correct** — and both builds answer `cp 0` (227 nodes on base and PC). So the fault is not
"any hm99 position"; it is specifically a position where the defender has no counter-resetting
move and a mate waits one ply deeper.

## How serious, and for whom

- **For the owner's matches: probably rare but real.** The shape needed is: the fifty-move counter
  at exactly 99, the side to move losing, and every reply allowing an immediate mate. That is a
  narrow and unusual configuration — but it is a *lost win* (a mate scored as a draw) rather than a
  cosmetic fault, and it cannot be searched away.
- **Only counter 99 can reach it through a move**, because a legal move raises the counter by at
  most one and the root must be below 100 to be searched at all. At 100+ the root path handles it
  (and on r15 handles it by searching, still reaching `cp 0` through the same node return).
- **A repetition can reach it at any counter** — `is_repetition()` is in the same return — so the
  full family is "drawn node one ply above a mate", of which I have demonstrated the fifty-move
  member and not the repetition member.

## The fix, in one sentence (stated, not implemented)

**In `Worker::is_draw`, do not return a draw for `halfmove_clock() >= 100` (or for a repetition) at
a node where the side to move has a move that mates immediately — check that first, exactly as the
root fix does — so the returned score is the mate instead of 0.**

Cost: one `legal_moves()` scan of the side to move per candidate drawn node, only on nodes that
already satisfy the draw test, which are rare; the four honesty pins should be unchanged (no bench
root reaches a drawn node one ply above a mate) but that is a prediction, not a measurement —
**I have not built or tested this.**

## How to see it again

```
python3 forge-combo29/swarm/12/job1/node_draw.py ~/build/pc_r15/forge      # needs the CASES list
python3 -c "import importlib.util; ..."   # or the committed form below
```
Committed raw: `job4/pc_node_level_base_vs_r15.txt` (the table above, pasted from the run),
`job4/pc_node_level_depth_sweep.txt`.

## Suspicions, not proven

- Whether the repetition member of this family is reachable in a real game at a counter below 100
  without the fifty-move term also applying. Constructible in principle (a repetition needs only 8
  plies of shuffling); **not tested on r15.**
- Whether an opponent's *only* drawing resource being this shortcut ever appears in the owner's
  games. Unknown; would need his PGNs, which I do not have.

---

## Follow-up: I could NOT trigger the repetition member of the same family (honest negative)

The same construction with a repetition instead of the fifty-move counter:

```
6k1/8/5PPP/8/8/8/8/R6K b - - 0 40   then moves  g8h8 h1g1 h8g8 g1h1 g8h8 h1g1 h8g8 g1h1
-> 6k1/8/5PPP/8/8/8/8/R6K b - - 8 44   (python-chess: is_repetition(3) = True, halfmove 8)
```

Black has exactly two legal moves and **both** allow `Ra8#`, so by the same argument the truth is
mate -1. Measured:

| build | result |
|---|---|
| base 6b98f217 | g8h8 / **mate -1** / 63 nodes — **correct** |
| PC r15 | g8h8 / **mate -1** / 63 nodes — **correct** |

So the repetition member is **not demonstrated**. The reason is in the position setup, not in the
search: after `position fen X moves …` the engine's key history is built from the moves only, and
the FEN root is not itself in that history, so `Board::is_repetition` finds one match instead of
the two it needs (`matches >= 2`) and the root is searched normally. Getting a true threefold
*including* the root would need the repetition to be established by moves from `startpos`, which
this board cannot reach.

**What that means for the finding:** the fifty-move member is proven on both builds and is
permanent (depth 24 and counter 9999 still `cp 0`); the repetition member shares the same `return`
in `Worker::is_draw` and is therefore exposed in principle, but **I have no position that shows it**
and I am not claiming one.
