# PREDICTION — deepseek6, long 3a (kimi5 LmrCutNode)

Written before the first measuring command of long 3a. Never edited after this commit.

Patch: `forge-combo29/tests_kimi5_job7/LmrCutNode.patch.txt` on kimi5's branch, copied verbatim here.
Clean copy: `/agent/repos/p3` at 6b98f2170a3210e71beed04bbd2553972c253ed7.
Build `/agent/repos/work/build-l3a/forge`, sha256 `0fb846a67ff2e9752836e47a8a8e8153eda0ee21eed196916fda6679adcc88ad`,
Release, g++ 13.3.0, `-march=x86-64-v4`.

## The new option, read off the patch

| option | type | default | min | max | what it does |
|---|---|---|---|---|---|
| `LmrCutNode` | spin | **2** | 0 | 4 | the reduction bonus at a cut node: `r += LmrCutNode` where base code has `r += 2` |

## Honesty check with the option at its default

Already run, all four met: 312866 / 862329 / 3024920 / 4865609 (`honesty_*.txt`).

## Identity at the default

| comparison | predicted | killed by |
|---|---|---|
| O under S14, `LmrCutNode=2`, vs long 1 `O_S14.rows` | **200 of 200 equal** (sum 9,500,069) | any row differs |
| G under S14, `LmrCutNode=2`, vs long 1 `G_S14.rows` | **353 of 353 equal** (sum 18,466,239) | any row differs |
| O no options, vs long 1 `O_none.rows` | **200 of 200 equal** (sum 12,573,318) | any row differs |

## Wiring on O under S14

`LmrCutNode` has 5 legal values; I measure all four that are not the default, because each costs 5 s.

| value | predicted sum on O/S14 | killed by |
|---|---|---|
| 0 | below 9,500,069 — the whole cut-node bonus removed, so nodes should FALL. I predict 9,000,000–9,500,000 | exactly 9,500,069 |
| 1 | below 9,500,069, close to it (one unit less). I predict 9,300,000–9,500,069 | exactly 9,500,069 |
| 3 | above 9,500,069. I predict 9,500,000–9,900,000 | exactly 9,500,069 |
| 4 | above the value at 3. I predict 9,600,000–10,100,000 | exactly 9,500,069 |

The killed-by condition for "wired" is only "the sum differs from 9,500,069"; the bands are my expected
size, and if a band is missed I will say the band was missed rather than move it.

Why I expect monotone growth here when `LmrGiveCheck` also grew: both add to `r` as the option grows, and
a larger `r` means a shallower re-search. This patch's sign is the same sign as the base code (`+=`), so
the direction should be the opposite of `LmrGiveCheck`'s (`-=`, which shrank as the option grew). If both
grow with the option, one of my two readings of "which way is bigger" is wrong, and the numbers decide
which.

## Out-of-range stop check

`LmrCutNode=9` must stop the run at once with `info string invalid value` (range is 0..4).
