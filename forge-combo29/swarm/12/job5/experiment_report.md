# Correctness experiment: the corrected claimable-draw condition

**This is a correctness experiment, NOT a candidate patch.** Nothing here is offered for merging.
Seat 12, area 2. **Threads 1 throughout** (no `Threads` option is sent anywhere).

## What was changed, and only that

The not-ready patch's fifty-move block required **every** legal move to reset the clock before it
called the node terminal. That is the wrong polarity. The only change made here is that condition:

```diff
     if (board.halfmove_clock() >= 100) {
         for (const Move move : board.legal_moves()) {
-            if (!move.is_capture() && piece_type(board.piece_at(move.from)) != Pawn) return false;
+            if (move.is_capture() || piece_type(board.piece_at(move.from)) == Pawn) return false;
         }
-        return true;      // every move resets the counter: the claim cannot be avoided
+        return true;      // no reset available: a genuine fifty-move draw
     }
```

`job5/experiment_condition.diff.txt` is the full diff against the not-ready tree: **one block, two
lines changed plus a comment** — verified, not asserted. Nothing else was touched, and the patch has
not been tuned further.

## The four cases, and what they need to do

| case | requirement | base not-ready | **base EXPERIMENT** | PC not-ready | **PC EXPERIMENT** |
|---|---|---|---|---|---|
| **1** fifty-move claimable, reset available | stop being 0 | cp -153 / 357,316 | **cp -163 / 348,348 ✔** | cp -153 / 357,316 | **cp -163 / 348,348 ✔** |
| **2** repetition, WINNING side to move | stop being 0 | cp -1197 / 38,350 | **cp -1197 / 38,350 ✔** | cp -1259 / 78,615 | **cp -1259 / 78,615 ✔** |
| **3** repetition, LOSING side to move | **stay 0** | cp 0 ✔ | **cp 0 ✔** | cp -1237 ✘ | **cp -1237 ✘ still wrong** |
| **4** forced draw K v K | **stay 0** | cp 0 / 0 nodes ✔ | **cp 0 / 0 nodes ✔** | cp 0 / 0 ✔ | **cp 0 / 0 nodes ✔** |
| extra: clock 100, NO reset possible | **stay 0** | cp 0 ✔ | **cp 0 / 0 nodes ✔** | cp -501 ✘ | **cp -450 / 11,419 ✘ still wrong** |

### On the base tree: all four land correctly

1 → -163 (the real value; seat 25 measured the position's worth as "-150s"), 2 → -1197, 3 → stays 0,
4 → stays 0 in 0 nodes, and the no-reset control → stays 0 in 0 nodes. **The corrected condition is
right, and the earlier regressions were caused entirely by the polarity error, exactly as
diagnosed.**

### On the PC build: cases 1, 2, 4 correct, but 3 and the no-reset control are still wrong

- **Case 3** (losing side to move at a threefold, `cp 0` correct because the loser claims): PC gives
  **-1237**, unchanged from the not-ready build.
- **The no-reset control** (`4k3/8/8/8/8/8/8/R3K2r w - - 100 1`): PC gives **-450 in 11,419 nodes**,
  where both unpatched builds and the base experiment give **0**.

Note the PC's no-reset number changed from -501 / 1,026,656 to -450 / 11,419 with this condition
fix, so the condition *does* affect it — but it does not make it zero.

**I did not investigate why the PC differs**, since the pins decide the question and the pins are
unchanged. The likely reason is that the PC build's own `FORGE_FIX_ROOT_DRAWN` changes which side's
claim reaches the root, and my patch's root/branch interaction with it is untested. That is a
hypothesis, not a measurement.

## The pins: unchanged and still moved

| pin | required | base EXPERIMENT | PC EXPERIMENT |
|---|---|---|---|
| bench 11 | 312866 | **353312** ✘ | **353312** ✘ |
| bench 13 | 862329 | **979723** ✘ | **979723** ✘ |
| bench 16 | 3024920 | **2893009** ✘ | **2893009** ✘ |
| go perft 5 | 4865609 | 4865609 ✔ | 4865609 ✔ |

**Identical to the not-ready build, to the node.** Fixing the condition did not change the pins at
all — which makes sense: the pinned bench positions evidently hit the *repetition* half of the
change (whose code is identical in both versions), not the fifty-move half I corrected.

## So: does a correct version of this fix exist, and what does it cost?

| question | answer |
|---|---|
| Does a version exist that gets all four cases right? | **Yes, on the base tree.** All five checks pass there with a two-line condition change. |
| Is it free? | **No.** Three of four pins move by 13 %, 13.6 % and 4.4 % on the base tree — the same numbers as the not-ready build. |
| Is it correct on the PC build? | **No.** Two must-be-zero cases are still wrong there, so it cannot be called correct on the build the owner plays. |
| Does the pin cost come from the fifty-move or the repetition half? | **The repetition half**: correcting the fifty-move condition left the pins bit-identical, and the repetition branch is what the two versions share. That is an inference from the pins being unchanged, not a separate experiment. |

**For the owner's match decision:** a correct version of the *repetition* part of this change exists
and is worth testing only if a 13 % bench-node increase is acceptable — because that cost comes from
the repetition branch, which is the part that did not change between these two builds. The
fifty-move correction is behaviourally right but pin-neutral here, so on this evidence it is not
where the cost is.

## Files

- `job5/experiment_condition.diff.txt` — the entire change (one block).
- `job5/four_cases_experiment.txt` — the four-case run, raw, both experiment builds.
- `job5/pins_experiment.txt` — the pin runs, raw, both experiment builds.
- `job5/experiment_meta.txt` — exe hashes, date, Threads 1, "NOT a candidate".
- Not-ready predecessor: `job5/fix_report.md`, `job5/claimable_draw.patch.txt`.

## What I am NOT claiming

- Not that this is shippable, on either build.
- Not that the PC divergence is understood — only that it exists and is unaffected by this change.
- Not that the pin cost is inherent to a correct fix; a narrower version might be pin-neutral, and I
  have not tried one.
