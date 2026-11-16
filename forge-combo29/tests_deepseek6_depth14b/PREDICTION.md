# PREDICTION — deepseek6, the depth-14 identity on G and for the newer patches

Written before the first measuring run. Never edited after this commit.

## What is missing, and why it is worth 10 minutes

The long list's depth-14 step says "the identity must hold at every depth" and names O only. My `REPORT_deepseek6_depth14.md`
therefore proved five patches identical at depth 14 **on O**, and left two obvious holes:

1. **G at depth 14** for those same five patches — a second set at the deeper search.
2. **The newer patches** (`NodeLiterals`, `QsSteps`, `LmrFine`, `FailHighBlend`, `IirNoRoot`) at depth 14 — they
   passed their identities at depth 12 (and the sanitizer at depth 10) but were never tested at 14.

## Step 0: the depth-14 G baseline, measured first

There is no published depth-14 G sum, so the plain build defines it:

| run | predicted |
|---|---|
| plain base, G under S14, depth 14, run twice in two processes | the two rows files are **353 of 353 equal** |

I predict nothing about its VALUE (it is new data).

## Then the identities, all against that baseline (row for row, 353 positions)

| patch set | exe | predicted |
|---|---|---|
| LmrGiveCheck, defaults | `build-l2` | **353 of 353 equal** |
| LmrCutNode, defaults | `build-l3a` | **353 of 353 equal** |
| LmrTtPv, defaults | `build-l3b` | **353 of 353 equal** |
| SoundArms, defaults | `build-l4a` | **353 of 353 equal** |
| SoundSteps chain, defaults | `build-l4b` | **353 of 353 equal** |
| NodeLiterals, defaults | `build-l5a` | **353 of 353 equal** |
| LmrFine, defaults | `build-l5c` | **353 of 353 equal** |
| FailHighBlend=0, defaults | `build-j3` | **353 of 353 equal** |
| IirNoRoot=0, defaults | `build-l6` | **353 of 353 equal** |

Nine sets, one prediction: **every one is 353 of 353 equal, 9 of 9 met.** Kill: any differing row, which I will
name with its position index, fen, both node counts and both best moves.

Why I expect this to hold: every one of these patches replaces a literal with a tunable whose default IS that
literal (or guards a change behind `= 0`/`& mask` that is false at 0), so the identity is a property of the source,
not of the search. Depth 14 tests the claim that no default is depth-sensitive; the depth-12 and depth-10 results
already agree, and a third depth either confirms it or finds the one patch whose default is not inert.

## The cost, stated so the reading is honest

Depth 14 on G is 353 positions and took 12 s per 200 on O; G is 1.77x that, so roughly 20–25 s per run, about 4
minutes for the nine plus two baseline runs. I will report the actual wall times in `stamps.txt`.

## What I will NOT claim

- No strength result: these are node counts at a fixed depth.
- No claim about any MOVED value at depth 14 — only the defaults. Job 2 already showed moved values change sign
  across depths, so a moved-value claim at depth 14 would need its own prediction and its own runs.
