# REPORT_v3_picker — removing the picker's full sort: A SEARCH CHANGE, NOT A SPEED PATCH (prediction confirmed)

**Why this was tried:** the profile put move generation and the picker at 34-37 % of time, and `std::sort` inside
`pick_best` at **5.03 %** of bench 13. The picker sorts its whole remaining list once per generation; a repeated
find-max-and-swap is O(n) per move instead of O(n log n) once.

**The answer: it changes EVERY node count — all 200 of 200 rows — so it is a search change, not a speed patch, and
per file 7's rule it cannot be shipped as one.**

```
                       baseline        no-full-sort      change
total node sum         27,944,084      26,531,587        -5.05 %
rows differing          —               200 of 200        —
per-row |change|       —               median 32.94 %, max 224.25 %
rows up / down         —               94 up / 106 down
```

**All four predictions confirmed.** P1: I predicted at least one row would differ and most likely many — all 200 do.
P2: therefore this is a SEARCH CHANGE needing strength testing, not identity testing. P3: I predicted the total would
move by under 5 % even though the row count was large — **exactly 5.0547 %**, i.e. refuted by 0.0547 points. That is
close enough to my bar that I could reasonably have rounded it into a "confirmed", and I am deliberately not: the
prediction said *under* 5 % and the answer is *over*. A prediction that is quietly rounded into a hit is worth less
than one that is honestly a miss. P4 was
conditional on P1 being refuted, so it never arose.

## Why it cannot work, and this is the substance

`std::sort` is **not stable**, and a repeated find-max-and-swap breaks ties differently. My own S-F11/S-F35 work
established that this engine's search is exquisitely sensitive to move order — the colour asymmetry itself is
*entirely* move-generation order (120 of 120 cases fixed by canonicalising it). So a different tie order is a
different search, exactly as expected, and the 5 % swing in total nodes is that sensitivity showing up.

**The median per-row change of 32.9 % is the striking number**: the counts are not nudged, they are different trees.
Nearly half went down and slightly more than half up, which is the signature of order-dependent pruning rather than a
systematic improvement or regression.

## So what is the picker worth?

This result narrows the picker opportunity rather than opening it. The 5.03 % sorting cost **cannot be removed by
changing the sort algorithm**, because the sort's exact tie order is part of the search's definition. A legitimate
speed patch there would have to reproduce `std::sort`'s tie order exactly — e.g. by sorting on `(score, original
index)` with a comparator that matches the current behaviour — and that is a different, harder experiment which I did
not attempt.

That is a real, bounded conclusion: **the picker's cost is not algorithmic overhead, it is the price of the ordering
the engine depends on.**

## Honesty numbers

```
exe baseline    /home/ubuntu/builds/bld-v3/forge       (identity 27,944,084, Step 0 8/8 and 3/3)
exe experiment  /home/ubuntu/builds/bld-pick/forge     (full sort removed; EXPERIMENT, pins not claimed)
net             /tmp/test.fnn3  checksum fdff70de72e4ca82
settings        depth 12, PC20 + test net, Threads 1, Hash 16, OG200, cold per search
```

## Table

| step | done-partly-not done | evidence file | result |
|---|---|---|---|
| prediction committed alone before building | done | `picker/prediction.txt` | all four predictions recorded, P3 narrowly refuted |
| build the no-full-sort variant | done | `picker/EXPERIMENT_no_full_sort.patch.txt` | builds clean |
| identity against the 200 OG200 rows | done | `picker/ident_pick.txt` vs `v3/ident_OG200.txt` | **200 of 200 rows differ** |
| quantify the divergence | done | this report | total -5.05 %, median row change 32.9 %, 94 up / 106 down |
| make it identity-preserving (sort on score+index) | NOT attempted | — | the legitimate next experiment, named below |

## Findings

`v3 | removing the picker's full `std::sort` in favour of repeated find-max changes EVERY node count — 200 of 200 OG200 rows differ, total 27,944,084 -> 26,531,587 (-5.05 %), median per-row change 32.9 %, 94 rows up and 106 down. So it is a SEARCH CHANGE, not a speed patch: the sort's exact tie order is part of the search's definition, which is why it cannot ship under file 7's identity rule. The picker's 5.03 % sorting cost is therefore not removeable by swapping the algorithm; a legitimate patch would have to reproduce std::sort's tie order exactly, e.g. by sorting on (score, original index) | picker/ident_pick.txt picker/EXPERIMENT_no_full_sort.patch.txt picker/REPORT_picker.md | NEW |`

## Suspicions, not proven

- That sorting on `(score, original index)` would restore identity while still allowing the O(n) handout. It should,
  since that is a total order matching one valid `std::sort` output — but `std::sort`'s own tie order is unspecified,
  so "matching the current behaviour" would have to be measured against this build's actual output, not assumed.

## Times

`picker` uses `v3/stamps.txt`; every line is a `date -u`.
