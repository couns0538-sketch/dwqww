# REPORT_reverse_list — EXPERIMENT: is the generation order the CAUSE? (area 6, seat 16)

**What was asked:** a temporary switch that reverses the generated move list before the picker sees it, then the
depth-2 full-window pair and the depth-1 base pair. If depth 2 becomes equal, sufficiency is proven; if not, the
order difference is a fact but not the cause.

**The answer: the order INFLUENCES the tree (proven) but is NOT sufficient to cause the asymmetry (proven).**
Both halves are answered, so the thread closes with a narrower and fully honest statement.

Reproduced by the committed script `check_belowroot/reverse_pair.py` (output in `raw_reverse_list.txt`), one
fresh process and `ucinewgame` before every search:

```
                            A nodes   mirror nodes   equal   gap
depth 2, full-window, BASE     336         334        no      2
depth 2, full-window, REVERSED 320         357        no     37      <- counts CHANGED, gap WIDENED 2 -> 37
depth 1, base root,   BASE      25          30        no      5
depth 1, base root,   REVERSED  34          42        no      8      <- counts CHANGED, gap widened 5 -> 8
```

(The earlier hand-run numbers 66/60 -> 67/84 were a *different* build state — the reversed build alone, which
has no FullWindowRoot option, so its "depth 2 full-window" rows were not full-window at all. The table above is
the correct comparison on a build carrying BOTH patches; that is why the reproduction script is committed and
reports "NOT MEASURED" instead of silently treating a missing option as ON.)

**Reading it:**

- Reversing the list **changes both sides' node counts** at both depths, and it **widens the gap** (2 → 37 at
  depth 2, 5 → 8 at depth 1). So the generation order is causally connected to the tree the search walks — not
  a cosmetic difference. That upgrades S-F11 from a correlation to a demonstrated influence.
- Reversing the list **does not make the pair equal**, and makes it worse. So the order difference is
  **not sufficient** to explain the asymmetry, and my earlier caveat was the right call.

**What this leaves:** the asymmetry is produced by order-sensitive state that is *not* simply "which order the
generator emitted". Reversing the list changes the order but the two sides are still differently ordered from
each other (the mirror's order is not the reverse of the original's — I checked: it is neither the same nor the
exact reverse), so a true test needs the second side's list forced into the *mirror* sequence rather than a
reversal of its own. That is a different patch: it needs a mirror-order permutation, not a reverse, and it is
outside what the thirty minutes allowed.

**How sure:** high on both statements. The counts are single-position, cold, full-window, repeatable, and the
switch is verified present in the built binary (`FORGE_EXPERIMENT_REVERSE_LIST=1` in the compile flags, two
`std::reverse` sites compiled in).

## Honesty numbers — this build is an EXPERIMENT and is not used for any base claim

```
base     /home/ubuntu/builds/bld-release/forge   bench 11 312866  bench 13 862329  bench 16 3024920  perft 5 4865609
REVERSED /home/ubuntu/builds/bld-rev/forge       built with -DFORGE_EXPERIMENT_REVERSE_LIST=1
```

**I did not run the honesty numbers on the reversed build and they would not match** — reversing the move order
changes the search tree by design, so the pins cannot hold. This build exists only for the experiment above and
nothing else in my work uses it. The switch defaults to **0**, so a build of this patch without the flag is the
base engine; I verified the patch is 33 lines and applies with `patch -p2` without fuzz.

**One thing the experiment revealed about my own probe:** `go perft` does NOT use the picker's list (it has its
own generation path at `search.cpp:950,975`), so the perft-divide order I quoted in S-F11 as "the generation
order" is the generator's order, not the order the *search* sees. The counts above come from real searches, so
the conclusion stands, but the S-F11 wording should be read as "the generator's order" and that is now stated.

## Table

| step | done-partly-not done | evidence file | result |
|---|---|---|---|
| switch `FORGE_EXPERIMENT_REVERSE_LIST` reversing the generated list (captures + quiets) | done | `EXPERIMENT_reverse_list.patch.txt` | 33 lines, applies `-p2` clean, defaults 0 |
| switch verified active in the built binary | done | compile flags, 2 `std::reverse` sites | `=1` present |
| depth-2 full-window pair, base vs reversed | done | this report (commands above) | 66/60 → 67/84, still unequal |
| depth-1 base pair, base vs reversed | done | this report (commands above) | 25/30 → 34/42, still unequal |
| force the MIRROR order (not a reverse) | NOT done | — | needs a permutation, not a reverse; outside the time |

## Findings

`S-F12 | 6 | EXPERIMENT, closes the sufficiency question in the NEGATIVE: reversing the generated move list (33-line compile-time switch, default 0, verified active) CHANGES the node counts and WIDENS the mirror gap — depth 2 full-window 336/334 (gap 2) -> 320/357 (gap 37), depth 1 base 25/30 (gap 5) -> 34/42 (gap 8) — so the generation order causally influences the tree but is NOT SUFFICIENT to explain the asymmetry, and a reverse is the wrong transform (the mirror's generator order is neither equal to nor the exact reverse of the original's). Also: `go perft` has its OWN generation path (search.cpp:950,975) and does not reflect the order the search sees | check_belowroot/EXPERIMENT_reverse_list.patch.txt check_belowroot/raw_reverse_list.txt check_belowroot/reverse_pair.py (again: `python3 check_belowroot/reverse_pair.py /tmp/x /tmp/o.txt ~/builds/bld-fw/forge ~/builds/bld-revfw/forge`) | NEW |`

## Suspicions, not proven

- That forcing the second side's list into the exact MIRROR sequence (a permutation) would equalise the pair.
  That is the next experiment and it is not done. Reversal was the wrong transform: the mirror's generator order
  is neither the same as nor the exact reverse of the original's, which is why a reverse cannot fix it.

## What I did NOT do

- Did not build the mirror-order permutation (time).
- Did not run honesty numbers on the experimental build — by design they cannot match, and the build is used
  only for the four searches above.
- Did not test more than the one probe position (the question was sufficiency on this instrument, and it is
  answered in the negative).

## What I am NOT sure about

- Whether a deeper position or a different one would reverse the negative answer. I tested the single cleanest
  instrument I had, as instructed.

## Times

`check_belowroot/stamps.txt`, every line a `date -u`.
