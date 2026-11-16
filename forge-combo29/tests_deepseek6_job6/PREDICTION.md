# PREDICTION — deepseek6, job 6 (testing kimi5's job-13 dead/alive claims with rows)

Written before the first counted run. Never edited after this commit.

## What I am testing, and from where

kimi5's `REPORT_kimi5_job13.md` (branch `for-fable-and-opus/kimi5-work`) gives a 35-row table: 3 settings
**dead** at one tuner step, 32 **live**. My `readkimi13.py` parses that table into `kimi13_table.txt`
(35 rows, 3 dead, 32 live — agreeing with kimi5's own count). Every value and step below comes from that parse,
not from my typing.

## The control runs the job asks for, and what I expect BEFORE them

| control | prediction | killed by |
|---|---|---|
| `LmrHistoryDivisor` 5643 → **5644** | **dead** — the term is `clamp(history / divisor, -2, 2)`; 5643 → 5644 changes the quotient only where `|history|` lies in a narrow window that 5643 and 5644 round differently, and job 1 measured the ±500 move as live, so the term does bite somewhere; but a ONE-unit move at the divisor level most plausibly changes nothing on 200 positions. **I predict DEAD (200 of 200 equal on O).** | any differing position on O |
| `NullMoveBase` 5 → **6** | **alive** — job 1 measured 5→4 and 5→6 both live (0 of 200 nodes equal). | 200 of 200 equal on O |

If the first control differs, my reading of the divisor's use is wrong somewhere and I will say so rather than
quietly proceed; if the second is equal, my harness or the build is wrong and the job stops.

## The prediction the job asks for: how many of kimi5's 3 "dead" claims survive

**I predict all 3 survive (3 of 3).** Kill: 2 or fewer.

**The one I doubt most: `CaptureFutilityMultiplier` and `CaptureFutilityDepth` equally — and the reason is a
distinction kimi5 does not make.** They are dead because their ONLY read sits behind `tune::CaptureFutilityBase > 0`
(`search.cpp:1893`) and that base is 0 (default, not set by S14). That is a fact about the SOURCE, and I have
already confirmed it twice by measurement (job 1: value±c identical; job 2: B0's tree is 1.0066× S14's, so the
gate does something when open). What I doubt is not the claim but its SCOPE: "dead" here means "dead at the
engine's current default", not "dead at every reachable configuration" — open the gate (`CaptureFutilityBase 230`,
which is not in S14 and which the tuner does not move today) and both come alive, which job 3b counted (25,098
prunes at multiplier 100 against 11,236 at 250, and prunes out to L=9). **So my prediction is "3 of 3 survive as
worded" and my doubt is that the wording will mislead a reader who takes "dead" to mean "has no effect on the
engine" rather than "has no effect at this configuration".**

For `QsSeeMargin` I have no doubt at all: the SEE values are multiples of 100, so every margin in 0..99 is the same
comparison, and job 1's controls at 0 and 99 were exact identities while 100 differed exactly as the job's known
answer said.

## The 32 "live" claims: what would count as a failure

The job says: for every setting kimi5 calls alive, run S14 + (value + step) on O and at least one position must
differ. **I predict all 32 differ (32 of 32).** Kill: any live setting whose run is 200 of 200 equal on O.

I expect this to hold because job 1 already ran every one of these settings at value±c and every one differed —
kimi5's "live" column is in fact quoting my own job-1 counts. So this half of job 6 is a re-measurement of my own
work through a fresh harness, which is worth doing but which I do not expect to surprise me. **I say that plainly
rather than presenting it as independent confirmation of kimi5: it is not independent, because the numbers kimi5
marked "live" came from me.**

## What I will report if a claim fails

The job says one differing position is a finding and to name the position. I will give the index, the fen, both
node counts and both best moves, and I will say whether the failure is kimi5's claim being too narrow (it called
something dead that moves) or my harness being wrong (which the two controls are there to rule out).
