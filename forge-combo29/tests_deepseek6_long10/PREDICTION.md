# PREDICTION — deepseek6, long 10 (R: kimi5's SoundRegret patch, independently reproduced)

Written before the first counted R4 run. Never edited after this commit.

## R1 to R3, already met and recorded here so the predictions rest on them

- **R1**: `SoundRegret.patch.txt` sha256 `1020849555c1f8…` **starts with `10208495`** as file 7 requires.
  It does NOT apply to a clean 6b98f217 (2 of 3 uci.cpp hunks fail): its own first line says
  `# applies from the repository root, AFTER SoundArms.patch.txt`, and `SoundArms.patch.txt`'s sha256
  `57524c71d5ae…` also starts with the `57524c71` that file 7's long 19 quotes. So the item is the chain
  **SoundArms then SoundRegret**, and both applied with `patch -p1 --fuzz=0` and exit 0 (`patch_apply.txt`).
- **R2**: build sha256 `dc2a3e805a183691…`; pins **312866 / 862329 / 3024920 / 4865609** all exact; the `uci` list
  shows the five new options with their defaults: `SoundPvArm` 0 (-1..1), `SoundInCheckArm` 0 (-1..1),
  `SoundMateAlphaArm` 0 (-1..1), `SoundRegretCount` false, `SoundRegretProbe` false.
- **R3**: defaults + S14 identity is **200 of 200 on O** (9,500,069) and **353 of 353 on G** (18,466,239),
  against my own long-1 S14 rows.

## R4: the settings kimi5 actually ran, and what I expect

kimi5's `runs_O/` and `runs_G/` hold twelve configurations each, at **no S14** (its base sum on O is the
no-options 12,573,318). Its own exe sha256 is `b8e0d1668c9afe20…`, which is exactly the binary my long-4b
SoundSteps chain build produced, so the two of us were already running the same code for these settings.

| config | kimi5's setopts | kimi5 O sum | my prediction |
|---|---|---|---|
| `none` | (none) | 12,573,318 | **equal to my no-option base on every position** |
| `smp` | `SoundMatePruning=true` | 12,558,811 | equal, position by position |
| `pv` | `SoundPvArm=1` | 12,399,593 | equal |
| `chk` | `SoundInCheckArm=1` | 12,326,599 | equal |
| `mat` | `SoundMateAlphaArm=1` | 12,573,482 | equal |
| `pvchk` | `SoundPvArm=1;SoundInCheckArm=1` | 12,558,811 | equal |
| `off7` | `SoundMatePruning=true` + all three arms `-1` | 12,573,318 | equal |
| `cnt` | `SoundRegretCount=true` | 12,573,318 | equal |
| `cntsmp` | `SoundMatePruning=true;SoundRegretCount=true` | 12,558,811 | equal |
| `mask0` | `SoundMatePruning=true;SoundStepMask=0` | 12,573,318 | equal |
| `mask1` | `SoundMatePruning=true;SoundStepMask=1` | 11,944,468 | equal |
| `pvmask1` | `SoundPvArm=1;SoundStepMask=1` | 11,944,468 | equal |

**I predict all 12 configurations reproduce kimi5's rows EXACTLY — 12 of 12, every position, nodes AND best
moves.** Kill: any configuration with a differing node count. I expect R4 for this patch to be a clean pass
because the option code is the same in both builds (identical sha256 of the exe my long-4b chain built, which is
kimi5's `b8e0d166…`), so the only way to differ is a different harness.

## The one number I expect to be interesting

`mask1` and `pvmask1` have the SAME sum (11,944,468) and the same first three (20,223 / 39,123 / 44,776) in
kimi5's files, even though one forces `SoundMatePruning=true` and the other `SoundPvArm=1`. kimi5 reported that
`mask1` on O is "the PV case" only, because the in-check arm's case needs `SoundMatePruning=true` to be live and
`SoundStepMask` only gates INSIDE an active case. **I predict these two configurations are row-for-row identical
on O**, and if they are not, one of the two mechanisms I just described is wrong.

## R5 (the sanitizer half)

After R4: an ASan+UBSan build of the same chain with one planted fault that must be reported, over O at the
settings kimi5 tested. **I predict 0 sanitizer lines at every setting and 1+ reported for the planted fault.**
