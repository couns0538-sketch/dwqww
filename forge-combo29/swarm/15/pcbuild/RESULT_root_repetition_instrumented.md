# The thrice-repeated root: instrumented. The test IS called and DOES return true — the guard ignores it.

This is the definitive answer to the question the coordinator set. **Threads 1** for every number.
Two builds, both instrumented the same way, both with their honesty pins re-checked unchanged.

## What was instrumented

A stderr line (never stdout, so no UCI output is altered) executed at the root of
`Worker::search`, immediately before `root_drawn` is computed. It prints the guard value, the
halfmove counter, the root move count, the key-history length, **the result of
`board.is_repetition()` obtained by calling it unconditionally**, and whether the guard uses it.

The call is unconditional *because the guard in the PC build never calls it* — so without forcing the
call we could not tell "never called" from "called and false".

Text patches (unified diff, `.patch.txt`, both apply with `patch -p1`, no fuzz):
- `instr/root_rep_instrument.patch.txt` — PC r15 tree (src/search.cpp + a read-only accessor in
  include/forge/board.hpp)
- `instr/root_rep_instrument_base.patch.txt` — base tree 6b98f217 (src/search.cpp only)

## The answer for the PC build (r15, PC20, `FORGE_FIX_ROOT_DRAWN=1`)

`root_instr_pc.txt`:

```
=== 1 occurrence(s) of the final position (0 plies) ===
  ROOT-REP guard=1 halfmove=0 legal=20 key_history=1  is_repetition()=false WOULD_BE_DRAWN=false used_by_guard=NO
=== 2 occurrence(s) of the final position (4 plies) ===
  ROOT-REP guard=1 halfmove=4 legal=20 key_history=5  is_repetition()=false WOULD_BE_DRAWN=false used_by_guard=NO
=== 3 occurrence(s) of the final position (8 plies) ===
  ROOT-REP guard=1 halfmove=8 legal=20 key_history=9  is_repetition()=true  WOULD_BE_DRAWN=true  used_by_guard=NO
=== 4 occurrence(s) of the final position (12 plies) ===
  ROOT-REP guard=1 halfmove=12 legal=20 key_history=13 is_repetition()=true WOULD_BE_DRAWN=true  used_by_guard=NO
```

**Neither of the two readings I offered is right.** The test IS called (when forced) and it DOES
return `true` at three occurrences — so the detection logic is correct and agrees with python-chess,
which also calls that board a threefold. What is different is that the guard **does not consult it**:
under `FORGE_FIX_ROOT_DRAWN` the root-drawn condition is reduced to

```cpp
const bool root_drawn = !legal.empty() && board.is_insufficient_material();
```

with the comment above it saying, in the source itself, "A third occurrence or an expired
fifty-move counter is searched like any other root." So this is **deliberate behaviour of the patch,
not a bug in the repetition test.** The `is_repetition()` call was removed from the root condition,
and the earlier condition is still visible in the `#else` branch.

## The base tree, same instrumentation, for contrast

`root_instr_base.txt`:

```
=== 2 occurrence(s) ... ===  ROOT-REP-BASE halfmove=4  is_repetition()=false used_by_guard=YES   -> cp 26, 4099 nodes
=== 3 occurrence(s) ... ===  ROOT-REP-BASE halfmove=8  is_repetition()=true  used_by_guard=YES   -> cp 0,  0 nodes
=== 4 occurrence(s) ... ===  ROOT-REP-BASE halfmove=12 is_repetition()=true  used_by_guard=YES   -> cp 0,  0 nodes
```

Identical detection, opposite use. This is the whole difference between the two builds on this
board, in two lines.

## Honesty pins, with the instrumentation applied

`honesty_instrumented.txt` — stderr writes cannot change node counts, and they did not:

| build | bench 11 | bench 13 | bench 16 | perft 5 |
|---|---|---|---|---|
| PC r15 + instrumentation | 312866 | 862329 | 3024920 | 4865609 |
| base 6b98f217 + instrumentation | 312866 | 862329 | 3024920 | 4865609 |

All four pins on both, unchanged. (Pins are default-option numbers — see 15-C3.)

## So what is the "fix"?

There is nothing to fix in the repetition test. The decision to search a thrice-repeated root is a
design choice of `FORGE_FIX_ROOT_DRAWN`, made on purpose, and its own comment says so. Whether that
choice is *right* is a question for the owner, not a defect I can report. The consequences I can state:

- A threefold at the root is played on rather than declared drawn, so a game that reaches the same
  position a third time does not end there by the engine's own adjudication. A GUI or arbiter that
  knows the rule would still end it; the engine's score will simply look like a normal position.
- The engine will not *lose* anything to this — it evaluates the position on its merits — but in a
  match scored by the engine's own game loop, a drawn-by-repetition game could run on.

If the owner wants the old behaviour back on the PC build, the minimal change is to restore
`board.is_repetition()` to the `root_drawn` condition — i.e. build with `FORGE_FIX_ROOT_DRAWN=0`, or
edit that one line. I did **not** test `FORGE_FIX_ROOT_DRAWN=0`; that is the obvious next experiment
and I say plainly that it is untested rather than guessing its result.

## Corrections to my own earlier framing

- I previously treated this as a likely defect ("the root check is the gap", 15-F21). The
  instrumentation shows the check is *deliberately bypassed*, which is a different thing. 15-F21's
  measurement stands — in-tree repetition works, root repetition is not used — but its framing as a
  "gap" overstates it; it is a removed call, by design, with a comment saying so.
- My two candidate readings in 15-F16 ("check does not fire" vs "machinery changed") were both
  wrong; the third possibility — "it fires but is not consulted" — is the actual one, and only
  instrumenting could have found it.

---

## The follow-up I said was untested: `-DFORGE_FIX_ROOT_DRAWN=0` on the PC tree

Built the PC tree with `-DFORGE_MATE_ALPHA_GUARD=1 -DFORGE_FIX_ROOT_DRAWN=0`. **All four honesty
pins unchanged** (312866 / 862329 / 3024920 / 4865609, default option regime). Threads 1,
regime PC20. Raw: `fix0_test.txt`.

### What comes back

```
repetition:
occurrences  score   nodes   verdict
1            cp 20   8569    searched
2            cp 20   8569    searched
3            cp 0    0       DECLARED DRAWN
4            cp 0    0       DECLARED DRAWN

fifty-move thread:
CASE 2  mate in one, halfmove 100   score=cp 0   nodes=0   bestmove a1b1   <-- the MATE BUG IS BACK
CASE 4  pawn-move mate, halfmove 100 score=cp 0  nodes=0   bestmove a7a8q  <-- and here
CASE 1  mate in one, halfmove 99    score=mate 1 nodes=144 a1a8            <-- control still fine
CASE 5  checkmate / stalemate       mate 0 / cp 0, 0000                    <-- unchanged, correct
```

### So the two behaviours are the same switch, and they conflict

`FORGE_FIX_ROOT_DRAWN` does both jobs at once:

- **ON (PC default)**: a drawn root is searched, so a mate at halfmove 100 is FOUND (`mate 1`, 144
  nodes) — and a thrice-repeated root is also searched (`cp 23`, 13,424 nodes).
- **OFF**: a thrice-repeated root is correctly declared drawn (`cp 0`, 0 nodes) — and a mate at
  halfmove 100 is LOST again (`cp 0`, 0 nodes, `a1b1`), exactly the base-tree defect.

**The owner cannot have both with this switch alone.** This is the useful part of the answer: the
"thrice-repeated root is searched" behaviour is not a separate bug to be patched away, it is the
price of the mate repair in the same flag. A proper fix would separate the two conditions — keep
`halfmove_clock >= 100` out of `root_drawn` (which is what repairs the missed mate) while keeping
`is_repetition()` in it (which is what declares the repetition) — i.e. two flags or one flag with the
conditions split. The instrumentation in this file is exactly what shows the conditions are
separable, since `is_repetition()` returns the correct answer independently.

I did **not** build or test that split. It is a one-line change to `root_drawn` and an obvious next
experiment; I am naming it rather than claiming it works.
