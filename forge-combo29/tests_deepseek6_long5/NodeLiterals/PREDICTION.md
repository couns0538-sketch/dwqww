# PREDICTION — deepseek6, long 5a (kimi5 NodeLiterals, job 9)

Written before the first measuring command of long 5a. Never edited after this commit.

Patch: `forge-combo29/tests_kimi5_job9/NodeLiterals.patch.txt` on kimi5's branch, copied verbatim here.
Clean copy: `/agent/repos/p7` at 6b98f2170a3210e71beed04bbd2553972c253ed7.
Build `/agent/repos/work/build-l5a/forge`, sha256 `f0daf1b6ec915311d998e1f0978befa77e3781bc54e0f91ee943668d0bcc1ead`.
Release, g++ 13.3.0, `-march=x86-64-v4`.

## What the patch is

Eight integer literals in the null-move and ProbCut blocks become tunables, each at the literal's own value,
so at the defaults the arithmetic is IDENTICAL to the base. Read off the patch, confirmed against the built
binary's `uci` output:

| option | default | min | max | the literal it replaces |
|---|---|---|---|---|
| `NullStaticSlope` | 24 | 0 | 100 | `beta - 24 * depth + 180` |
| `NullStaticBase` | 180 | -500 | 1000 | (same line) |
| `NullEvalRedMax` | 3 | 0 | 10 | `std::min((eval - beta) / NullMoveEvalDivisor, 3)` |
| `NullVerifyDepth` | 14 | 1 | 64 | `depth < 14` (twice) |
| `ProbcutImproving` | 50 | 0 | 300 | `probcut_beta = beta + margin - 50 * improving` |
| `ProbcutReduction` | 4 | 1 | 10 | `search(..., depth - 4, ...)` |
| `ProbcutTtSlack` | 3 | 0 | 10 | `tt_depth >= depth - 3` |
| `ProbcutStoreReduction` | 3 | 0 | 10 | `store_tt(..., depth - 3, ...)` (both TT branches) |

## Honesty at the defaults

Already run, all four met (`honesty_*.txt`).

## Identity at the defaults

| comparison | predicted | killed by |
|---|---|---|
| O under S14 vs long 1 `O_S14.rows` | **200 of 200 equal** (sum 9,500,069) | any row differs |
| G under S14 vs long 1 `G_S14.rows` | **353 of 353 equal** (sum 18,466,239) | any row differs |
| O no options vs long 1 `O_none.rows` | **200 of 200 equal** (sum 12,573,318) | any row differs |

This is an exact-identity patch by construction (every default equals its literal), so the identity is the
cheap half; the wiring is the half that can fail, and it has a trap in it that kimi5 warned me about.

## Wiring: one value per option, and my prediction for each

I take kimi5's warning (`NOTES_kimi5.md`, job-9 block) as a hypothesis to TEST, not as fact: it says
`NullEvalRedMax 6` is INERT at depth 12 (0/200 on O, 3/353 on G), because a cap on
`(eval - beta)/NullMoveEvalDivisor` needs eval-beta-rich positions to bind at all.

| option, moved value | predicted sum on O/S14 | killed by |
|---|---|---|
| `NullStaticSlope=48` | differs from 9,500,069 | exactly 9,500,069 |
| `NullStaticBase=360` | differs from 9,500,069 | exactly 9,500,069 |
| `NullEvalRedMax=6` | **differs from 9,500,069** — I expect it to DIFFER, unlike kimi5's 0/200, because a cap of 6 vs 3 changes the reduction whenever eval-beta is large, and the null-move guard itself needs `ss->static_eval >= beta - 24*depth + 180`, which at depth 12 is `beta - 108`; the cap can bind there | exactly 9,500,069 (which would CONFIRM kimi5's inertness claim on my tree too) |
| `NullVerifyDepth=20` | differs from 9,500,069 | exactly 9,500,069 |
| `ProbcutImproving=0` | differs from 9,500,069 | exactly 9,500,069 |
| `ProbcutReduction=6` | differs from 9,500,069 | exactly 9,500,069 |
| `ProbcutTtSlack=1` | differs from 9,500,069 | exactly 9,500,069 |
| `ProbcutStoreReduction=1` | differs from 9,500,069 | exactly 9,500,069 |

The killed-by condition for "wired" is only "the sum differs from 9,500,069" — long 3's lesson. I make NO
band predictions on the size of any of these, because eight options on one tree at one depth is exactly the
situation where a band is a guess dressed up as a measurement.

I do record one directional guess and only one, and I will score it honestly: **`NullVerifyDepth=20` should
GROW the tree** — verifying null-move cutoffs down to depth 20 instead of 14 turns cheap returns into full
verifications, which costs nodes. Everything else: direction unknown.

## Out-of-range stop checks

Two, on opposite ends of two different options: `NullStaticBase=-501` (below min -500) and
`ProbcutReduction=0` (below min 1) must each stop the run at once with `invalid value`. `NullStaticBase` is
the only option here with a NEGATIVE minimum, so it is the one that would expose a sign-handling error in
the UCI parse.
