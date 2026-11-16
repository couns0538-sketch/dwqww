# The PC regression is an INTERACTION with `FORGE_FIX_ROOT_DRAWN` — confirmed by measurement

**Correctness experiment, not a candidate.** Seat 12, area 2. **Threads 1 throughout.**

## The question and the answer

The corrected claimable-draw condition got all four cases right on the base tree, but on PC r15 two
must-be-zero cases still failed. I suspected the cause was an interaction with r15's own
`FORGE_FIX_ROOT_DRAWN` and said so as a hypothesis.

**The experiment confirms it.** With `FORGE_FIX_ROOT_DRAWN` compiled off, both failing cases land
correctly, and every other case is unchanged:

| case | requirement | root fix **ON** | root fix **OFF** |
|---|---|---|---|
| 1 fifty-move claimable, reset available | stop being 0 | cp -163 / 348,348 | cp -163 / 348,348 (same) |
| 2 repetition, WINNING side to move | stop being 0 | cp -1259 / 78,615 | cp -1259 / 78,615 (same) |
| **3 repetition, LOSING side to move** | **stay 0** | **cp -1237 ✘** | **cp 0 ✔** |
| 4 forced draw K v K | **stay 0** | cp 0 / 0 nodes | cp 0 / 0 nodes (same) |
| **control: clock 100, NO reset possible** | **stay 0** | **cp -450 / 11,419 ✘** | **cp 0 / 0 nodes ✔** |

**4 of 4 cases plus the control correct with the root fix off; 2 failures with it on.** So the two
changes do not compose as layers — they must be merged deliberately in the root-drawn path.

## The switch really was off (without this, the result means nothing)

`FORGE_FIX_ROOT_DRAWN` is `#ifndef`-guarded (`src/search.cpp:35-36`), so I set it from the command
line — `-DCMAKE_CXX_FLAGS="-DFORGE_MATE_ALPHA_GUARD=1 -DFORGE_FIX_ROOT_DRAWN=0"` — and **edited no
source for it**. Proof it took effect, on a clock-100 root with a mate in one
(`6k1/5ppp/8/8/8/8/8/R5NK w - - 100 40`, depth 10):

| build | answer |
|---|---|
| stock PC r15 (root fix ON) | `a1a8` / **mate 1** / 180 nodes |
| root fix ON + corrected condition | `a1a7` / cp 488 / 7,625 nodes |
| **root fix OFF + corrected condition** | `g1e2` / **cp 0 / 0 nodes** |

The OFF build falls back to the 0-node root adjudication, which is exactly what the switch is
supposed to control. So the comparison above is between a build with the root path enabled and one
without it, and nothing else differs.

### One incidental observation worth flagging (not chased)

The middle row is interesting: **root fix ON + my corrected condition gives `cp 488` on a root where
White has mate in one.** That is neither the unpatched `mate 1` nor the correct behaviour; it is a
third, wrong answer produced by the two changes together. I am reporting it and **not** chasing it,
per the instruction to stop on this thread — but it is another face of the same interaction and it
means "layering" is not merely imperfect here, it is actively wrong on that position.

## Pins for the root-off build: unchanged again

| pin | required | root fix OFF |
|---|---|---|
| bench 11 | 312866 | **353312** ✘ |
| bench 13 | 862329 | **979723** ✘ |
| bench 16 | 3024920 | **2893009** ✘ |
| go perft 5 | 4865609 | 4865609 ✔ |

Bit-identical to both previous patched builds. Turning the root fix off does not touch the pin cost
either, which is consistent with the earlier inference that the cost comes from the repetition branch
of `is_draw` and not from anything in the root path.

## What this tells the owner for the match decision

| question | answer |
|---|---|
| Can the two fixes coexist as independent layers? | **No.** With the root fix on, two must-be-zero cases are wrong and a mate-in-one root reports +488. |
| Can they coexist at all? | **Yes, but only as one deliberate change**: the claimable-draw rule has to be decided *inside* the root-drawn path, so the root adjudicates claims for the side entitled to them while the tree returns real evaluations. That is a merge, not a stack of two patches. |
| What does a correct version cost? | About **+13 % bench 11, +13.6 % bench 13, -4.4 % bench 16**, unchanged across all four patched builds — the repetition branch. |
| Is it ready? | **No.** Nothing here is a candidate: the interaction is diagnosed, not resolved, and the pins move. |

## Files

- `job5/four_cases_root_off.txt` — the four-case table, raw, root fix on vs off.
- `job5/pins_root_off.txt` — pins for the root-off build, raw.
- `job5/root_off_meta.txt` — exe hashes, the exact build line, the switch-effect proof, Threads 1.
- Predecessors: `job5/experiment_report.md` (the base-tree correctness experiment),
  `job5/fix_report.md` (the not-ready first attempt).

## What I am NOT claiming

- Not that the merge has been done, or that I know exactly where in the root-drawn path it belongs.
- Not that the +488 root is understood beyond "the two changes interact".
- Not that a correct merged version would keep the same pin cost — it might not.
