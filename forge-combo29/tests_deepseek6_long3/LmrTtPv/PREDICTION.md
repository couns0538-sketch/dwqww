# PREDICTION — deepseek6, long 3b (kimi5 LmrTtPv)

Written before the first measuring command of long 3b. Never edited after this commit.

Patch: `forge-combo29/tests_kimi5_job7/LmrTtPv.patch.txt`, copied verbatim here.
Clean copy: `/agent/repos/p4` at 6b98f2170a3210e71beed04bbd2553972c253ed7.
Build `/agent/repos/work/build-l3b/forge`, sha256 `926f48eba93f5583b6b6cb117de92852d85b7d4113c15526f537282cc18611c2`.

## The new option, read off the patch

| option | type | default | min | max | what it does |
|---|---|---|---|---|---|
| `LmrTtPv` | spin | **1** | 0 | 4 | the LMR credit at a TT-PV node: `r -= LmrTtPv` where base code has `r -= 1` |

## Honesty at the default

Already run, all four met (`honesty_*.txt`).

## Identity at the default

| comparison | predicted | killed by |
|---|---|---|
| O under S14 vs long 1 `O_S14.rows` | **200 of 200 equal** (sum 9,500,069) | any row differs |
| G under S14 vs long 1 `G_S14.rows` | **353 of 353 equal** (sum 18,466,239) | any row differs |
| O no options vs long 1 `O_none.rows` | **200 of 200 equal** (sum 12,573,318) | any row differs |

Note this option sits behind `(quiet || !ss->tt_pv || move_count > 4)`, so at `move_count <= 4` a TT-PV
quiet move is not reduced at all and the line cannot matter there. That narrows where a moved value can
be felt, but not whether it is wired.

## Wiring on O under S14

| value | predicted sum on O/S14 | killed by |
|---|---|---|
| 0 | above 9,500,069 (the TT-PV credit removed, so shallower re-search everywhere it applies) — I predict 9,500,000–9,900,000 | exactly 9,500,069 |
| 2 | below 9,500,069 (more credit) — I predict 9,300,000–9,500,000 | exactly 9,500,069 |
| 3 | below the value at 2 — I predict 9,100,000–9,500,000 | exactly 9,500,069 |
| 4 | below the value at 3 — I predict 9,000,000–9,500,000 | exactly 9,500,069 |

This is the opposite sign to `LmrCutNode` (that one is `+=`, this one `-=`), so I expect the sums to fall
as the option grows, mirroring what `LmrGiveCheck` did. If instead they rise, my "which way is bigger"
reading is wrong again and the numbers will say so.

The killed-by condition for "wired" is only "the sum differs from 9,500,069".

## Out-of-range stop check

`LmrTtPv=9` must stop the run at once (`invalid value`; range 0..4).
