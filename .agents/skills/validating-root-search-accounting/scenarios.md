# Scenarios and verification limits

| Situation | Required interpretation/action |
|---|---|
| Best move changes ordinal across depths or aspiration retries | Reconstruct cumulative work by full Move identity; preserve the declared retry/reset policy. |
| Two promotions share from/to | Keep promotion and flags in the key; use canonical legal moves. |
| An aborted child increases local nodes | Preserve the source's unfinished-child exclusion; do not force bucket sums to equal the denominator. |
| Lookup misses in Release | Guard the write; expose the invariant in debug and test the exceptional path. Keep lookup work outside non-root recursion. |
| A model agrees but actual traced PV differs from untouched search | Instrumentation is not yet a valid oracle; investigate before attributing counter differences. |
| Offline factor changes; a different candidate's hosted match is running | Report arithmetic only. Neither an observed timed stop nor this candidate's Elo has been established. |

## Recorded failing control

The archived actual 6.4.7 search has four-FEN untimed PV/score/node instrumentation parity. At middlegame depth 7, selected `c3d5`'s ordinal bucket contains 1355 nodes from 4 moves, while that move contributes 601 of 3355 local nodes. Offline effort factors are 1.146125 versus 1.370864. Metadata explicitly records `timed_stop_observed=false`; these are counter/arithmetic observations.

At authoring, source `7125b337` implements the stable-identity candidate; candidate trace agreement and full GREEN remain pending. Hosted job `39325939081` concerns 6.4.7, not this 6.4.8 change. Read STATUS for later evidence.

## Skill verification

Frontmatter, links, current source invariants, archive metadata and these scenario judgments were checked statically. No new engine test, match, fresh-agent comparison or skill-effectiveness study was performed to author these files. This reference does not upgrade candidate validation status.
