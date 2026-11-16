# REPORT — seat 07, job 22: does the boolean `NonPawnCorrection` option actually take effect?

## What was asked / the answer / how sure

**Asked:** continue the area-7 read of the UCI loop. My job9 result (all four S14 sums exact) proves
the spin options reach the search, but S14 also relies on **one boolean** option,
`NonPawnCorrection`, which `uci.cpp` handles through a different branch. So the sums did not prove
that particular flag applies.

**Answer:** it does. Same position, same depth, cold, only the flag differing:
**false → 56,720 nodes (cp 30)**; **true → 33,066 nodes (cp 29)**. A silently ignored flag would
produce identical numbers.

**How sure:** high. Difference is large and reproducible in one cold process each.

## Honesty numbers

Base build pins unchanged (job0/raw/summary.txt: 312866 / 862329 / 3024920 / 4865609).
**Cross-check:** the `false` figure, 56,720 nodes, is exactly the cold-start number seat 10
independently reported for this engine — two seats, two harnesses, same number.

## Why this needed its own test

    uci.cpp:289   for (const forge::tune::Parameter& parameter : forge::tune::parameters()) { ... apply_spin ... }
    uci.cpp:403   } else if (name == "ContHist4PlyRead" || name == "NonPawnCorrection" || ... ) {
    uci.cpp:407       bool* target = name == "ContHist4PlyRead" ? &forge::tune::ContHist4PlyRead
    uci.cpp:408                    : name == "NonPawnCorrection" ? &forge::tune::NonPawnCorrection ...

The tunable table holds **spins only**; every boolean goes through a name-comparison chain and a
`bool*` lookup. A typo in that chain (or a bool missing from it) would silently ignore the option and
leave the S14 configuration un-reproduced in a way a *sum* would catch only if the option mattered —
and if it does not matter, the sum would hide the bug.

## Result

    NonPawnCorrection false: nodes 56720 score ('cp', 30)
    NonPawnCorrection true : nodes 33066 score ('cp', 29)
    RESULT: the flag measurably changes the search, so it takes effect

Raw: job22/raw/result.txt.

## What this does and does not prove

**Proves:** the bool branch applies `NonPawnCorrection` for the S14 value (`true`).

**Does not prove:** that the other ten booleans in that same `else if` chain apply. The chain shares
its structure, and job21's option-surface check confirmed every advertised name is *recognised* (no
`unknown option`), but "recognised" and "assigned to the right variable" are different claims: a
`bool* target` mis-wired to the wrong variable would be accepted silently. Testing each of the
eleven by effect is the natural follow-up, and I state the gap rather than imply coverage.

## Findings

**07-C20** in FINDINGS.md.

## Suspicions, not proven

- The `bool* target` ternary chain (uci.cpp:407-421) assigns by name; a mismatch between the `if`
  condition's name list and the ternary's name list would route one option to the wrong flag. I read
  both lists and they appear to match for all eleven names, but I did not verify by effect for the
  other ten.

## What I did NOT do

- Did not test the other ten boolean options by effect (see above).
- Did not test `TmNodeShare`/`TmFinishIteration`, which only matter under a running clock.

## What I am NOT sure about

- Whether the 56,720 → 33,066 change is all from `NonPawnCorrection` or partly from a hash/cache
  interaction; each run was a fresh process with `ucinewgame`, so I believe it is the flag alone.

## Times

See job22/stamps.txt.
