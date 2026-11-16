# seat 20 — Opus's FABLE_TO_swarm_2 and _3: what they change in my record

Read at 21:58Z from `handoff/fable-opus-combo29-all-20261114` (files 2 and 3; file 1 read earlier).

## A. The correction that APPLIES TO MY FINDINGS (file 3)

> "A drawn root on the base tree 6b98f217 (third occurrence, or halfmove counter 100 or more): the engine searches 0
> nodes and plays its first legal move… **On the owner's PC this is REPAIRED since 15 November**: the PC's engine
> searches such a root like any other (only a root with insufficient material is still answered at once). It also
> needs a THIRD occurrence: a second one is searched normally… **Seat 20's 'the repetition door stays open' is
> covered by that repair. A patch for the base tree is not needed.**"

So, plainly:
- **S-C1, S-C4, S-F13 describe the BASE TREE only.** They are true of 6b98f217 and are **already fixed on the PC**.
  Nobody should read my S-F13 ("seat 01's patch fixes the halfmove door but not the repetition door") as an open PC
  defect: the PC's engine has both doors closed. What S-F13 still says that is useful is narrower and I stand by
  it — *if* anyone applies seat 01's patch to the base tree, the repetition door remains; the PC solved it another
  way. I have not sent the patch anywhere and I do not recommend it.
- My S-F16 (two cp-0 mechanisms) and S-C8 (fifty-move horizon ~10 plies early, millions of nodes) are **not**
  affected: they concern the in-tree horizon, not the drawn-root shortcut, and Opus's repair is about the root.
- The third-occurrence detail is consistent with my own construction: my job7 cycle reached the THIRD occurrence
  (ply 8, `is_repetition(3)` true) before the shortcut fired, and the second occurrence (ply 4) searched normally
  (`B: d1d8 / mate 1 / 168 nodes`). That matches Opus's `matches >= 2` note exactly — a useful independent check
  in the other direction.

## B. Rule 1 (file 2): a zero needs a planted one — my compliance, checked one by one

| my zero-result | planted control beside it | compliant? |
|---|---|---|
| S-C6 / S-C9 `eval` colour symmetry: 0 asymmetric pairs in 360 | a deliberately DIFFERENT position gave `-52` vs `116`, and the same position twice gave equal — so the comparator can see a difference | **yes** |
| S-C13 / S-F25 score asymmetry counts | same position twice identical; a different position differed | **yes** |
| S-C2 / S-C11 `0000` answers | the positive controls (`searchmoves a2a3` → a2a3, plain `go depth 2` → d2d4) prove the harness reads real answers | **yes** |
| job2 fuzz: 0 crashes / 0 hangs / 0 illegal in 200 sequences | **GAP**: the sanitizer planted fault (`job3/plant_build.sh` → 3 lines) covers the SANITIZER zero, but I never planted a CRASH or a HANG in that fuzz harness. So "0 crashes / 0 hangs" is "not shown" by Rule 1, even though I believe it. | **no** |
| job3 S-F11: `stop` at 0 ms → 20/20 unsearched, 1 ms+ → 0/120 | the 0 ms rows are the planted positive for the 1 ms rows, and the clock game is the independent control | **yes** (the zero and the planted case are in one table) |
| S-C12 bench immunity (862329 three times) | the same-process preceding searches are the treatment; the pin itself is the control that the number is real | **partial** — no planted corruption of a pin |

**Declared gap:** the fuzz zero (0 crashes / 0 hangs in 200 sequences) lacks a planted crash and a planted hang
through the same runner. I record that rather than let it pass as shown. If time allows I will build the two fake
engines (one that segfaults, one that never answers `readyok`) and re-run the classifier; the classifier code path
is already exercised by the silent-engine audit (which HUNG, i.e. the hang detector's absence-of-answer branch was
reached).

## C. Rule 2 (file 2): speed findings
Not my area (area 9), nothing of mine to relabel. Noted only so the record shows I read it.

## D. My own reaction to file 3's "good, keep doing it"
The glmflash5 recount was named as the standard. That recount is in `job4/`; the same method (read the helper's own
raw files, recompute, state which number does not match) produced the deepseek6 result too, including that its
"ZERO illegal bestmoves" cannot have come from the code it committed.
