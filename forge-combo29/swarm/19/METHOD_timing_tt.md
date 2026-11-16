# TIMING METHOD for a TT patch — how to prove a change to the probe path is actually faster

seat 19 · area 9. A page of judgement, as asked, with one thing measured rather than asserted: the noise floor
of this workload.

## The gap this fills

`RECIPE_tt_validation.md` gives counters that prove the TT code is **reached** — 54.7 % of probes hit the
replacement scan instead of bench's 0.006 %. It does not and cannot prove a patch is **faster**. This is how
to get that number, and what size of win is even measurable.

## 1. The workload

The same one: **the first 200 positions of `job1b/R_1911.fens`, `go depth 12` each, Hash 16, OwnBook false**,
one fresh engine process per timed sweep. Hash 16 because that is what `bench` builds and it is the case where
the table actually fills (54.7 %); Hash 32 gives 44.1 %, so pin it explicitly or the comparison drifts.

Each sweep is ~8.3 s, so a 10-round alternating design costs about **2 × 10 × 8.3 s ≈ 2.8 minutes**. That is
cheap enough to run for any patch worth keeping.

## 1b. State discipline — mandatory, and it is what broke my 19-F18

Seat 10's rule applies to this method: **a cold baseline is a fresh process or `ucinewgame`, never `Clear
Hash`.** Two identical unrestricted searches in one process give 56,720 → 4,951 → 4,516 nodes; three separate
processes give 56,720 each time.

**What this method does:** one fresh process per *sweep*, but the 200 positions inside a sweep run with **no
`ucinewgame` between them** — so each sweep is internally **warm**. Measured, that matters: the same 200
positions give **15,238,023 nodes warm** and **13,925,108 nodes cold** (+9.4 %), and the TT replacement-scan
count goes from 142 cold to 8,310,172 warm (`CORRECTION_19F18.md`).

**Why the noise floor still stands:** both sides of the control were warm in exactly the same way, and the node
total was identical (286,628) in all 20 runs. A like-for-like comparison is valid as long as both sides share
the discipline. **What would NOT be valid:** comparing a warm time against a cold time, or comparing my warm
absolute times against any cold figure from another seat.

**If you want cold timing**, put `ucinewgame` + `isready` before every `position` (that costs the +9.4 % of
node work back, and the sweep gets faster because the table starts empty). Either way: **write down which one
you used.** A timing table with no state discipline is not reusable.

## 2. The design — and the three things that must be true

**Paired, alternating, same machine, same binary-build-per-side:**

1. **Build each side TWICE.** Two builds of *identical* source are byte-identical on this project (19-C2
   verified the sha256 match), so a second build is a check that the build itself is reproducible — and if the
   hashes differ, something in the build is non-deterministic and the timing is not trustworthy.
2. **Alternate A/B within a round, one fresh process per run.** Never "10 runs of A, then 10 runs of B".
   That design produced a **false +3.6 % / +8.6 % "speedup"** on this machine (seat 29's 29-F5) because the
   machine's state drifts; my own 19-F7/19-C2 was the same mistake, where a block of runs dropped from
   ~443 ms to ~425 ms partway through and looked like a 4.2 % build difference that did not exist.
3. **Never interleave the builds inside one run.** One process runs one binary for the whole sweep.

## 3. The noise floor, measured on this workload tonight

`job4/noise_floor.py`: the same binary on both sides, so the true ratio is exactly **1.0000** and every
deviation is noise. 10 alternating rounds:

| quantity | value |
|---|---|
| node totals seen (all 20 runs) | 286,628 — identical every run |
| mean sweep time | 8.374 s (A) / 8.337 s (B) |
| sd | 3.01 % / 2.14 % of the mean |
| A-vs-B ratio (true value 1.0) | **0.9956** |
| 95 % CI half-width at 10 rounds | **± 2.29 %** |

**So on this workload, with 10 rounds, a speed change smaller than about 2.3 % cannot be distinguished from
noise.** That is the number to quote, and it is much better than the ±5 % I measured on `bench` in job 2 — a
timed sweep of 200 positions averages out the per-run jitter that `bench`'s 430 ms measurement is dominated by.

## 3b. Sizing your own experiment — rounds against detectable effect

**Measured:** 10 rounds → **±2.29 %**. **Extrapolated** from the 1/√n law (labelled as such so you know which
row is evidence and which is arithmetic):

| rounds | detectable effect at 95 % confidence | cost (2 × rounds × 8.3 s) | status |
|---|---|---|---|
| 10 | **±2.3 %** | ~2.8 min | **MEASURED** (0.9956 ratio on a true 1.0, sd 2.1–3.0 %) |
| 20 | ~1.6 % | ~5.6 min | extrapolated |
| 52 | ~1.0 % | ~14 min | extrapolated |
| 100 | ~0.7 % | ~28 min | extrapolated |
| 210 | ~0.5 % | ~58 min | extrapolated |

**The node total must be identical between the two sides at every round — expect 286,628. If it differs in
any round, the comparison is void:** the two sides are not running the same search, so no time ratio from them
means anything, and the patch is not a speed-only patch.

Scaling: the CI half-width falls as 1/√n, so the table above is just that law. Anything below 1 % is not
worth setting up on this VM.

## 4. What to compare, and what NOT to

- **Compare: mean wall time of the whole 200-position sweep**, monotonic clock, one number per sweep. Not
  per-position times (you would need 200× the samples for the same power).
- **Also record: the node total.** It must be **286,628 identical on both sides**. If it moved, the patch
  changed the search, and then it is not a speed-only patch — it needs the four honesty pins and a different
  conversation. The node total is the guard that stops a "faster" patch from being a different engine.
- **Do not compare nps from a single `bench` run.** bench's own 12 ms fixed cost (29-F3, confirmed as 19-C3)
  and its per-run 8-17 % jitter make it the wrong instrument for anything under ~5 %.
- **Do not compare across machines or across the day.** Same VM, same session, alternating.

## 5. The decision rule

For a patch P against base B:

- CI half-width from the base-vs-base control run on the same day, same workload → that is your resolution.
- If P's ratio CI **excludes 1.0** and the measured gain exceeds the control's half-width, call it faster.
- If P's ratio CI **contains 1.0**, the answer is "not shown faster", written plainly. Two of my three speed
  jobs tonight ended that way (19-F9 material key: 1.0059, CI [0.9680, 1.0454]) or worse (19-F10 prefetch:
  0.9190, definitively *slower*) and reporting them as such is the only honest option.
- If P's node total differs from 286,628, stop: it is not a speed-only patch.

## 6. A worked expectation for the TT specifically

The replacement scan fires on 54.7 % of 15.18 M probes ≈ **8.3 M times**. If a patch removed, say, half the
work in that scan and the scan were 2 % of runtime, the win would be ~1 % — **below the 2.3 % floor at 10
rounds** and needing ~52 rounds. That arithmetic is the reason this page matters: a plausible TT optimisation
is likely to be *unmeasurable* at a convenient sample size, and a seat that runs 10 rounds and reports
"+1.5 %" would be reporting noise. State the floor or the number means nothing.

## 7. Honest limits

- The noise floor was measured on **this** VM with **this** binary and workload. Opus or the owner must
  re-measure it on their machine; a quieter box could resolve smaller effects, a busier one none.
- I did not implement the paired timing runner. The pieces exist (`job4/noise_floor.py` is the sweep and the
  alternation; `job2/ratio_ci.py` computes the CI from an `nps.txt`), but wiring them into one script for
  patch-vs-base is the next seat's work, not something I am claiming to have done.
- The ±2.29 % assumes the two sides are run under the same conditions. My rounds ranged 7.98 s to 8.48 s
  within the control, which is machine drift — alternating absorbs it, blocking would not.

## 8. Files

`job4/noise_floor.py` (the control experiment), `job4/noise/RESULT.txt` (its output), and for the CI arithmetic
`job2/ratio_ci.py`.
