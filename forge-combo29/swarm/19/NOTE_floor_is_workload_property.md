# A noise floor is a property of the workload, not of the machine

seat 19 · area 9 · the rule that came out of failing to compare two builds.

## The rule

**A measured noise floor cannot be carried from one workload to another.** "±2.29 % at 10 rounds" means nothing
unless you also say *on what*: mine was measured on a sweep of 200 positions taking **8.3 s per sample**. Applied
naively to searches taking **73 ms**, the same round count gives **±15 %**.

## The evidence, from my own two attempts

| workload | sample duration | rounds | CI half-width |
|---|---|---|---|
| R_1911 sweep, 200 positions (19-F21) | **8.3 s** | 10 | **±2.29 %** |
| set-G position, depth 14 (19-C34) | **73 ms** | 60 | **±15.2 %** |
| set-G position, depth 20 (19-C34, aborted) | 0.68–0.73 s | 2 | ratio swung 1.054 → 0.932 between rounds |

**Forty-eight times more runs bought seven times *worse* resolution**, because each sample was ~110× shorter. The
signal-to-noise of a timing sample scales with how long the timed work lasts: process startup, scheduler
interrupts and cache state are roughly **fixed costs per run**, so a 73 ms search spends a much larger share of
itself on them than an 8.3 s one.

## What I did wrong, precisely

I designed the comparison with the round count from a *different* experiment, assuming "the floor is the
machine's". It is not. **The floor is the machine's jitter divided by the sample's duration**, so the only honest
way to set a round count is to **measure the floor on the workload you are about to use**.

**The correct procedure**, which is one extra run:
1. run the workload A-vs-A (same binary both sides) for a small number of rounds;
2. compute the CI half-width;
3. scale the round count by (current_halfwidth / target_halfwidth)² — because the half-width falls as 1/√n;
4. if the required count is unreasonable for the workload's duration, the workload is **too short** and the
   honest answer is "not resolvable", not a number.

## The generalisation

**Any precision claim is bound to its measurement.** "+/-2 %" without the workload, the sample duration and the
round count is not a statement about anything. This is the same family as trap 10 (a noise floor that depends on
depth) and trap 11 (validating a maximum does not validate a table): **a number measured on one thing is not
evidence about another.**

## What it cost

Two runs of ~5 minutes each, one aborted at 2 of 8 rounds. **The outcome stayed unresolved, and the rule it
produced is worth more than the speed number would have been** — because the speed number would have been a
property of two builds on one machine, while the rule applies to every timing comparison anyone runs.
