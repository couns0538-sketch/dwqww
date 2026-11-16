# PREDICTION — deepseek6, long 4b (kimi5 SoundSteps, on the chain its header requires)

Written before the first measuring command of long 4b. Never edited after this commit.

## Why a chain and not a clean copy

`SoundSteps.patch.txt` line 1 says `# applies from the repository root, AFTER SoundRegret.patch.txt:
patch -p1 < SoundSteps.patch.txt`. I verified this rather than trusting the comment:
`patch -p1 --fuzz=0 --dry-run < SoundSteps.patch.txt` on a clean 6b98f217 **fails** ("Hunk #1 FAILED at
354", the `search.hpp` hunk that adds `SoundStepMask` next to the `SoundRegretCounts` the earlier patch
introduces) and on the chain it **passes**. The apply log of all four steps is `patch_apply.txt`.

So this build is SoundArms + SoundRegret + SoundSteps, each with `patch -p1` and `--fuzz=0`.
SoundArms alone was already proven an identity in long 4a. SoundRegret's own option defaults are
`SoundRegretCount=false` and `SoundRegretProbe=false` (read from its `uci` output), and I predict those
too are inert — but I say plainly that **this report is not a clean single-patch test of SoundSteps**; it is
a chain test, and the only option unique to SoundSteps is `SoundStepMask`.

Clean copy: `/agent/repos/p6` at 6b98f2170a3210e71beed04bbd2553972c253ed7.
Build `/agent/repos/work/build-l4b/forge`, sha256 `b8e0d1668c9afe202a07ece8ad029914e0c44c029bb64fccf0f46c555a098dd2`.

## The new option unique to this patch

| option | type | default | min | max | what it does |
|---|---|---|---|---|---|
| `SoundStepMask` | spin | **63** | 0 | 63 | inside an arm's case, the six prune steps whose bit is SET in the mask are skipped. 63 = skip all six (today's arm behaviour), 0 = skip none (the case prunes like an ordinary node) |

The patch's own comment fixes the bit order: bit 0 = s1 (LMP), bit 1 = s2 (futility), bit 2 = s3
(history prune), bit 3 = s4 (quiet SEE), bit 4 = s5 (capture futility), bit 5 = s6 (noisy SEE).
The gate is `sound_mate_case ? SoundStepMask : 0`, so OUTSIDE an arm's case the mask can never matter.
That is the most important prediction here: **with all three arms at 0 (`FollowOption`) and
`SoundMatePruning=false`, `SoundStepMask` must be inert for EVERY value, because `sound_mate_case` is false.**

## Honesty at the defaults

Already run, all four met (`honesty_*.txt`).

## Identity at the defaults (`SoundStepMask=63`, arms at 0, `SoundMatePruning=false`)

| comparison | predicted | killed by |
|---|---|---|
| O under S14 vs long 1 `O_S14.rows` | **200 of 200 equal** (sum 9,500,069) | any row differs |
| G under S14 vs long 1 `G_S14.rows` | **353 of 353 equal** (sum 18,466,239) | any row differs |
| O no options vs long 1 `O_none.rows` | **200 of 200 equal** (sum 12,573,318) | any row differs |

## The wiring question, stated the way the code demands it

`SoundStepMask` cannot be "wired" without a case being active. So the test has two halves and BOTH must be
shown:

**(a) inert when no case is active** — this is a prediction, not a formality:

| check | predicted | killed by |
|---|---|---|
| `SoundStepMask=0`, arms all 0, `SoundMatePruning=false`, on O/S14 | **exactly 9,500,069, 200 of 200 rows equal** | any row differs |
| `SoundStepMask=21` (bits 0,2,4), same conditions, on O/S14 | **exactly 9,500,069, 200 of 200 rows equal** | any row differs |

**(b) wired when a case IS active** — with the PV arm forced on, the mask must select which steps survive:

| check | predicted sum on O/S14 | killed by |
|---|---|---|
| `SoundPvArm=1;SoundStepMask=63` | **9,966,105** — this is exactly long 4a's `SoundPvArm=1` number, row for row | any difference (that would mean the chain itself moved something) |
| `SoundPvArm=1;SoundStepMask=0` | differs from both, and I expect it to be LOWER than 9,966,105: with every step allowed inside a PV case the tree should return toward the base, near 9,500,069. Band 9,400,000–9,966,104 | equal to 9,966,105 (mask not wired) |
| `SoundPvArm=1;SoundStepMask=1` (only LMP skipped) | strictly between the two: 9,500,069 < x < 9,966,105 | outside that open interval |
| `SoundPvArm=1;SoundStepMask=62` (all but LMP) | strictly between the two as well | outside that open interval |

The two single-bit runs are what make this a wiring test rather than a smoke test: if the mask reaches the
code, one bit must give a different tree from a five-bit complement of it. I do NOT predict which of
`mask=1` and `mask=62` is bigger — that needs the step sizes, which I have not measured.

## Out-of-range stop checks

`SoundStepMask=64` must stop (`invalid value`; the range is 0..63, read off the built binary). And a word
value `SoundStepMask=true` must also stop: it is a spin, not a check.

## What would be a finding rather than a tolerance

- If (a) shows ANY difference, the gate `sound_mate_case ? SoundStepMask : 0` does not behave as its own
  comment says, and that is a defect in the patch worth reporting.
- If (b)'s `mask=63` run differs from long 4a at all, the chain (SoundRegret underneath it) is not neutral
  at its defaults, which is a separate finding about SoundRegret.
