# CHECK of seat 15's 15-F3 — seat 05 (area 5)

## Verdict: CONFIRMS, on my own positions, with the control the claim needs

Seat 15's 15-F3 (their words): *"With S14 (DeadMaterial off) the engine scores KNN v K as a win — 19 of 20 such
positions at depth 10 report cp 147…309 — although KNN v K cannot be won by force; setting `DeadMaterial true`
makes all 20 report cp 0."*

I checked this with a harness written from that sentence alone, on **my own 20 KNN v K positions**
(`../job2/positions/KNNvK.epd`, generated in job2 with `random.Random(501)`) — not seat 15's positions.

| configuration | result on my 20 positions |
|---|---|
| S14, `DeadMaterial false` (off) | **20/20 non-zero `cp`, range 159 … 354**, 0 mate scores |
| S14, `DeadMaterial true` | **20/20 exactly `cp 0`** |

So both halves of their claim reproduce. My range (159–354) is close to theirs (147–309) but not identical, which
is expected: different positions.

## The control that makes this a measurement rather than a coincidence

Zeroing KNN v K is only *correct* if it is the dead-material rule doing it, and not the option blindly zeroing
everything. Control C2: the same `DeadMaterial true` option, applied to five **K+Q/K+R versus lone king** wins
(`../job2/positions/fifty0.epd`), must leave them non-zero. It does:

```
cp 472   1K6/8/8/3R4/8/8/8/k7 w - - 0 1
cp 966   8/5K2/7Q/4k3/8/8/8/8 w - - 0 1
cp 501   8/8/3R4/k7/8/8/3K4/8 w - - 0 1
cp 1162  4K3/8/8/8/1Q6/7k/8/8 w - - 0 1
cp 472   8/8/1R6/8/8/2K2k2/8/8 w - - 0 1
```

So the option is selective: it zeroes the material set that genuinely cannot mate and leaves a winning set alone.
Without this control, "20/20 became cp 0" would be consistent with an option that zeroes everything, which would
have been a different (and worse) finding.

## What is beyond their finding
- **The off-state is 20/20, not 19/20.** Every one of my 20 KNN v K positions is scored as a win with DeadMaterial
  off, not 19 of 20. So the off-state is not a borderline case at all on my set.
- **C2 shows the option's scope** — a point 15-F3 does not make and which is what makes its second half meaningful.

## Reproduce

```
python3 check_15f3.py /tmp/build-rel/forge
```

Exit status is non-zero if any parse fails, so a missing `info`/score line can never be read as a score. Raw output:
`raw/check_15f3.txt`.

## Assertions enforced (seat 19's parse warning)
Every score comes from a matched `score (mate|cp) N` regex on a real `info ... pv` line; a missing line or a
non-matching line raises `FAIL-LOUD` and exits 1. The run above has zero assertion failures, and it prints
`RESULT: every parse asserted; both controls passed; the comparison above is a measurement`.

## What I did NOT establish
- Whether `cp 159…354` is *wrong* for KNN v K or merely a large but legitimate evaluation for a position where mate
  cannot be forced. The engine is not claiming a mate, and KNN v K does have mating possibilities (helpmates), so a
  positive evaluation is defensible; the finding is about the DeadMaterial switch changing it, which I confirmed.
- Any cause in source; I did not read `eval.cpp` for this check.
- Whether the same switch changes KN v K or KB v K. I did not test those in this check (they were `cp 0` in job2
  even with DeadMaterial off, per S-F6, so there is nothing for the switch to change there).
