# The one-sentence `is_draw` fix: pins MOVED and one case regressed — reported, not tuned

Seat 12, area 2, at the coordinator's instruction: implement the claimable-draw change as a text
patch on both builds, check the four honesty pins, test the four named cases, and **if the pins move,
say so and stop rather than tuning the fix to make them match.**

**Pins moved. I stopped. This patch is NOT offered as ready.** Everything below is reported as
measured.

**Threads 1 throughout** (no `Threads` option is sent anywhere in this work).

## The patch

`job5/claimable_draw.patch.txt` — a unified diff against `forge-combo29/src/search.cpp`, applying
with `patch -p1 --fuzz=0` from the repository root on **both** trees (base 6b98f217: clean, 0 offset;
PC r15: hunk at offset 126 lines, no fuzz). The two `is_draw` functions are byte-identical in both
builds, so one patch serves both and I verified the patched function bodies are byte-identical.

What it does, in the coordinator's words: a claimable draw is no longer treated as terminal for a
side that can still reset the clock or vary the move.

```cpp
    if (!board.in_check() && !board.has_legal_move()) return true;   // stalemate
    if (board.is_insufficient_material()) return true;               // nobody can mate
    if (board.halfmove_clock() >= 100) {
        for (const Move move : board.legal_moves()) {
            if (!move.is_capture() && piece_type(board.piece_at(move.from)) != Pawn) return false;
        }
        return true;      // every move resets the counter: the claim cannot be avoided
    }
    return false;         // a repetition is claimable and refusable: real evaluation
```

Note the third block is my attempt at "only terminal when the claim cannot be avoided", and **it is
one of the two things that went wrong** (see the PC regression below).

## Honesty pins: MOVED on both builds

| pin | required | base unpatched | **base + fix** | PC r15 unpatched | **PC r15 + fix** |
|---|---|---|---|---|---|
| bench 11 | 312866 | 312866 | **353312** ✘ | 312866 | **353312** ✘ |
| bench 13 | 862329 | 862329 | **979723** ✘ | 862329 | **979723** ✘ |
| bench 16 | 3024920 | 3024920 | **2893009** ✘ | 3024920 | **2893009** ✘ |
| go perft 5 | 4865609 | 4865609 | 4865609 ✔ | 4865609 | 4865609 ✔ |

**Three of four pins move on each build, and by a lot** (+13 % on bench 11, +13.6 % on bench 13,
-4.4 % on bench 16). Per the instruction I did **not** adjust the fix to bring them back. A change
that moves the pins is not node-neutral and cannot be merged as a "repair" the way seat 01's
root-drawn patch could.

Why it moves them: at least one bench position evidently reaches a drawn node (repetition or
fifty-move) whose evaluation is now returned instead of 0, so the search explores a different tree.
That is the fix doing what it says — which is exactly why it cannot be free.

## The four named cases

`job5/four_cases.txt` (raw). All four builds, `go depth 12`, Threads 1.

| case | base unpatched | **base + fix** | PC unpatched | **PC + fix** | required |
|---|---|---|---|---|---|
| **1** fifty-move claimable, reset available | cp 0 / 557 | **cp -153 / 357,316** | cp 0 / 557 | **cp -153 / 357,316** | no longer 0 ✔ **fixed** |
| **2** repetition, WINNING side to move | cp 0 / 96 | **cp -1197 / 38,350** | cp 0 / 96 | **cp -1259 / 78,615** | no longer 0 ✔ **fixed** |
| **3** repetition, LOSING side to move | cp 0 | cp 0 | cp 0 | **cp -1237** ✘ | must stay 0 — **REGRESSED on PC** |
| **4** forced draw, K v K | cp 0 / 0 nodes | **cp 0 / 0 nodes** ✔ | cp 0 / 0 | **cp 0 / 0 nodes** ✔ | must stay 0 ✔ **kept** |
| extra control: clock 100, no reset possible | cp 0 / 0 | cp 0 / 0 ✔ | cp 0 / 48 | **cp -501 / 1,026,656** ✘ | must stay 0 — **REGRESSED on PC** |

### Case 1 and 2 are genuinely fixed

Case 1 becomes **-153 cp**, which matches seat 25's independently measured real value of the position
("-150s", their clock-0 measurement). Case 2 becomes about **-1200**, matching the plain-FEN control
of the same board. So the diagnosis was right and the direction of the fix is right.

### Case 4, the control the coordinator flagged, is KEPT

K v K is still **cp 0 in 0 nodes** on both patched builds — the insufficient-material branch still
returns before anything else. This is the case a bad fix breaks, and it did not break.

### Case 3 and the no-reset control REGRESSED on the PC build — and only there

- **Case 3** (losing side to move at a threefold, `cp 0` correct because the loser claims): base+fix
  keeps `cp 0` ✔, but PC+fix answers **`cp -1237`** ✘. The losing side should have been allowed to
  claim and was not.
- **The no-reset control** (`4k3/8/8/8/8/8/8/R3K2r w - - 100 1`, clock at 100 with no pawn move and
  no capture available anywhere, so the fifty-move claim genuinely cannot be avoided): both
  unpatched builds correctly say `cp 0`; **PC+fix says `cp -501` in 1,026,656 nodes** ✘. My
  "only terminal when every move resets the counter" test failed to recognise this board, because
  that board's legal moves are rook and king moves which are neither pawn moves nor captures — so my
  condition `return true` requires *all* moves to reset, and here *none* do, which is the opposite
  case and it fell through to "not a draw".

That second bullet is a defect in **my** patch's logic, not in the engine: the correct condition is
"the claim cannot be avoided" only when the *claimant* has no move that resets, i.e. when it is the
side that wants the draw that is stuck — and that is not what I wrote. I am reporting it rather than
repairing it, per the instruction to stop when the pins move.

The PC-only difference in case 3 is unexplained by me: the two builds share the same patched
`is_draw` body, so the divergence must come from the PC build's other changes (its root-draw fix
changes which side's claim reaches the root). **I did not investigate it**, because the pins had
already ruled the patch out.

## Verdict

| question | answer |
|---|---|
| Is the diagnosis right? | **Yes.** Cases 1 and 2 move from 0 to the correct values, matching independent measurements. |
| Is this patch ready to merge? | **No.** Three of four honesty pins move on both builds, and on the PC build two cases that must stay 0 do not. |
| Was the fix tuned to make the pins match? | **No.** Pins were measured once, reported as they came out, and I stopped. |
| What is worth keeping? | The K v K control holds, which shows the insufficient-material/stalemate part of the restructure is safe; and case 1/2 landing on the right numbers is strong evidence the diagnosis is correct. |

## What a real repair would need (stated, not done)

1. The claimable-draw exception must not be applied when the **claiming** side is the one with no
   reset available (my condition has the polarity wrong for the no-reset board).
2. The pins must be re-taken **before** any behaviour change is accepted; a change that moves bench
   11 by 13 % is a behaviour change and needs a match, not just a pin.
3. Given (2), the honest recommendation is **do not ship this as a repair**; the safe subset is
   "never score a repetition as 0 at a node where the side to move is winning", which is narrower
   and might be pin-neutral — **untested, and I am not proposing to test it now.**

## Files

- `job5/claimable_draw.patch.txt` — the patch (applies to both trees, `-p1 --fuzz=0`).
- `job5/pins_fixed.txt` — the pin runs, raw.
- `job5/four_cases.txt` — the four-case table, raw, all four builds.
- `job5/four_cases.py` — the harness.
- `job5/fix_meta.txt` — patch sha256, both fixed exe sha256, date, threads.
