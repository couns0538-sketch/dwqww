# PREDICTION — deepseek6, long 4a (kimi5 SoundArms)

Written before the first measuring command of long 4a. Never edited after this commit.

Patch: `forge-combo29/tests_kimi5_job5/SoundArms.patch.txt` on kimi5's branch, copied verbatim here.
Clean copy: `/agent/repos/p5` at 6b98f2170a3210e71beed04bbd2553972c253ed7.
Build `/agent/repos/work/build-l4a/forge`, sha256 `ed29427b10efba4922b384bf23ccfa7c7ac243e68cc4e51e180267e2f3c573b6`.

## The new options, read off the patch and confirmed from the built binary's `uci` output

| option | type | default | min | max | what it does |
|---|---|---|---|---|---|
| `SoundPvArm` | spin | **0** | -1 | 1 | per-case arm for the PV case: -1 = ForceOff, 0 = FollowOption, 1 = ForceOn |
| `SoundInCheckArm` | spin | **0** | -1 | 1 | same, for the in-check case |
| `SoundMateAlphaArm` | spin | **0** | -1 | 1 | same, for the mate-alpha case |

The mapping is by name, not by cast (the patch says so in a comment: the enum order is
FollowOption, ForceOff, ForceOn, so a numeric cast would map 1 to ForceOff).

## What these arms gate (read at `src/search.cpp:1836-1841` in the base)

```
sound_mate_case = (sound_arm_enabled(SoundArmPv)      && pv_node)
               || (sound_arm_enabled(SoundArmInCheck) && in_check)
               || (sound_arm_enabled(SoundArmMateAlpha)&& is_mate_score(alpha));
if (!sound_mate_case && ... ) { <the whole shallow-depth move-loop pruning block> }
```
and `sound_arm_enabled(FollowOption)` returns the value of `SoundMatePruning`, whose default is **false**.
`ForceOff` returns false, `ForceOn` returns true.

`SoundMatePruning=false` is also the base engine's setting in every run of mine, so at the defaults this
patch only re-expresses "false" three more ways.

## Honesty check at the defaults

Already run, all four met: 312866 / 862329 / 3024920 / 4865609 (`honesty_*.txt`).

## Identity at the defaults

| comparison | predicted | killed by |
|---|---|---|
| O under S14 vs long 1 `O_S14.rows` | **200 of 200 equal** (sum 9,500,069) | any row differs |
| G under S14 vs long 1 `G_S14.rows` | **353 of 353 equal** (sum 18,466,239) | any row differs |
| O no options vs long 1 `O_none.rows` | **200 of 200 equal** (sum 12,573,318) | any row differs |

## The wiring checks, and one prediction I can be wrong about

This patch has a property the earlier ones did not: **one of its two non-default values must be inert.**
`-1` (ForceOff) is exactly what the default already resolves to while `SoundMatePruning` is false, so
`SoundPvArm=-1` is a value that CANNOT change the tree. If it does change it, the arm is reaching
something other than the three-case predicate and that is a finding, not a tolerance.

| check | predicted sum on O under S14 | killed by |
|---|---|---|
| `SoundPvArm=1` (ForceOn) | differs from 9,500,069 — the pruning block is skipped at every PV node, so I expect the tree to GROW. Band 9,500,000–14,000,000 | exactly 9,500,069 |
| `SoundInCheckArm=1` | differs from 9,500,069, and by LESS than the PV arm (in-check nodes are rarer than PV nodes) | exactly 9,500,069 |
| `SoundMateAlphaArm=1` | differs from 9,500,069, and by less than the PV arm | exactly 9,500,069 |
| `SoundPvArm=-1` | **exactly 9,500,069, and 200 of 200 rows equal** to the default run | any row differs (that would be a finding) |
| `SoundMatePruning=true` with all three arms at 0 | differs from 9,500,069 (the option itself is wired) | exactly 9,500,069 |

The `SoundMatePruning=true` row is the control that ties the arms to the option they follow: if the option
is wired but the arms are not, the arms' `=1` runs are what will show it.

## Out-of-range stop check

`SoundPvArm=2` must stop the run (`invalid value`; range -1..1). And the patch's own comment warns that a
numeric cast would mis-map the values, so I will also send the arm as the WORD `true` once: a spin option
must reject it, which proves these are spins and not checks.
