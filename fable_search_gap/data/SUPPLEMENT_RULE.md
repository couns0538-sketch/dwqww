# Reading rule for the supplementary run

Written and committed 2026-11-09 about 21:55 PT, after the review and **before** the supplementary run was started.

## Key points

- **This run cannot change the verdict.** The verdict was fixed by `QUALIFICATION_RULE.md` on the 95-position run. This run only decides how the dossier words the size of the effect.
- **Why it is run.** The review found three weaknesses in the 95-position set: it is 24 hand-picked positions plus continuations of the same lines; four boards occur twice; and its 95 % range treats positions from one line as independent.
- **One primary number, three possible readings, fixed below.**

## The set

`tools/etc_probe/positions_supp.epd`, built by `tools/etc_probe/make_uho_set.py` and `etc_probe --gen`.

- 48 openings, taken at a fixed stride (every 54,834th line) from `C:\Users\Administrator\grok-pc\coder-fuzz\UHO_Lichess_4852_v1.epd` (2,632,036 lines, 174,889,110 bytes, read only).
- From each opening the plain replica plays its own best move at depth 10. The position is written every 12 plies, six times. These are single lines of self-play by the replica, not engine games.
- 336 positions, no board twice. Each opening and its six later positions form one cluster of seven.
- Search depth by material (knights, bishops, rooks and queens of both sides): more than six, depth 16 (213 positions); three to six, depth 20 (102); two or fewer, depth 24 (21).

The set was generated with the plain search only. No run with the mechanism had been made on it when this rule was committed.

## The runs

Plain, placebo, counting for rules `cut6` and `cut8`, cutoff taken for `cut6` and `cut8`. 16 MB table, node cap 80 million per search, CPU 3-6 at Idle. Command: `tools/etc_probe/run_review_runs.ps1 -Which supp`.

The placebo is the plain search with one history constant changed by 1. It is not a mechanism. It shows how far node counts and best moves move under an arbitrary small change.

## Primary number

The geometric-mean node ratio of `etc_cut6` against plain, over every position that no run stopped at the node cap. Its 95 % range is computed over the 48 openings: the log ratios of one opening's positions are averaged first, and the range is taken over those 48 averages.

`cut6` is primary because it is the setting that passed all five rule items on the first 24 positions. `cut8` is secondary.

## Readings, fixed now

| Reading | Condition |
|---|---|
| A node saving is shown in the replica | the upper end of the range is below 1.00 |
| A node cost is shown in the replica | the lower end of the range is above 1.00 |
| Not shown either way | the range includes 1.00 |

## Reported without a decision

- The same number for `cut8`, and both numbers for the two material groups (more than six pieces; six or fewer).
- The placebo's node ratio, its range, and its smallest and largest single ratio.
- How many positions change their best move under the mechanism, next to how many change under the placebo.
- The counting-run shares (eligible, hit rate, below-hit share).
- Wall times. The machine is loaded and the runs are at Idle priority, so these are indicative only.

## Validity

- The counting runs must have the plain node count in every position. If not, the run is invalid.
- If more than 5 % of the positions are stopped by the node cap in any run, the run is invalid.
- An invalid run is reported as invalid. It is not repeated with other settings.

## What no reading changes

Every number stays a replica number. The next step stays the counting run inside the real lock search (`NO_QUALIFIED_GAP.md` section 6).
