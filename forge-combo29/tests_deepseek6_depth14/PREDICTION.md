# PREDICTION — deepseek6, the depth-14 identity repeat (the long list's "after long 8" step)

Written before the first measuring command. Never edited after this commit.

## What the long list asks for, and what I am running

> "After long 8: long 5 again for any new kimi5 patch; otherwise long 2 to 4 again at `go depth 14` on O
> (the identity must hold at every depth), then long 7 at depth 12."

Long 5 has nothing new (`git ls-tree` over kimi5's branch shows only `tests_kimi5_job9/NodeLiterals.patch.txt`
for N ≥ 9, and that is already done in long 5a). So this is the depth-14 repeat:
**the identity half of long 2, 3 and 4, at `go depth 14`, on O under S14 only** — the parenthetical says
"on O", so I run O and say plainly that G is not part of this step.

## First: the depth-14 BASELINE has to exist before an identity can be checked

No depth-14 sums are published. So step 0 is the plain build at depth 14 on O/S14 — that single run DEFINES
the reference every patched build must match. I predict nothing about its value (I cannot: it is new data),
only that it is reproducible:

| run | predicted |
|---|---|
| plain base, O/S14, depth 14, run twice in two processes | the two rows files are **200 of 200 equal** |

## Then the four patch sets from long 2, 3, 4, each at its defaults, at depth 14

| patch set | exe sha256 (release) | predicted |
|---|---|---|
| LmrGiveCheck, defaults | `919a4f4ecda2ea75…` | **200 of 200 equal** to the depth-14 baseline |
| LmrCutNode, defaults | `0fb846a67ff2e975…` | **200 of 200 equal** |
| LmrTtPv, defaults | `926f48eba93f5583…` | **200 of 200 equal** |
| SoundArms, defaults | `ed29427b10efba49…` | **200 of 200 equal** |
| SoundSteps chain, defaults | `b8e0d1668c9afe20…` | **200 of 200 equal** |

Five sets, not four: long 4 covers both SoundArms and SoundSteps, and both passed. I include both.

**Killed by:** any row differs. A difference is a finding and gets its position named, with the fen, both node
counts, and both best moves — and I will say which patch it belongs to.

## Why I expect the identity to hold at depth 14 as it did at depth 12

Every one of these patches replaces a literal with a tunable whose default IS that literal (LmrGiveCheck,
LmrCutNode, LmrTtPv, SoundStepMask) or with three arms whose default is `FollowOption` with
`SoundMatePruning=false` (SoundArms). None of them changes an arithmetic result at its default, so the
identity should hold at EVERY depth; depth 14 is the test of that claim, not a new claim.

## What I will also record, because it is free

The depth-14 baseline sum itself, and whether each patch's sum is bit-identical (not just equal) — the row
compare does the latter. I will also record the WALL TIME, because depth 14 on 200 positions is the first run
in this session that may take minutes rather than seconds, and later jobs will want to know the cost.

## Scope

O only, S14 only, Threads 1 / Hash 16 / OwnBook false, `ucinewgame` + `isready` before every `go`, one row per
position, the harness that has been in use since long 1 (`rows.py`). No moved values in this step — the
long list says "the identity must hold", and moved values were the long 2–4 half already done at depth 12.
