# CHECK of seat 17 S-F1 / S-F2 — mechanism at 2640 REFUTED (self-correction of my own S-C3)

This file originally claimed that `search.cpp:2640 root_candidates.front()` **is** reached with an empty
list and yields a garbage Move printed as `0000`. **That mechanism claim is withdrawn. I was wrong.**

## What my claim rested on, stated plainly
It was an **inference**, not an instrument. I observed `bestmove 0000` on a board with 20 legal moves, read
the source, saw an unguarded `front()` at 2640 and an `restricted_root_empty` flag at 2210, and concluded the
read must have happened. I had no marker build and no debug-STL build. ASan/UBSan reporting nothing was
consistent with my story, so I treated it as weakly supportive; that was backwards — silence was equally
consistent with there being no read at all.

## The evidence that settles it, from three seats

**Seat 17 (marker build).** Control-flow markers show every empty-candidate search leaving at the `2253` early
block — its marker output is `EARLY_PATH cand=0 legal=20` with no `PAST_EARLY` hit on any searchmoves case;
its control marker fires at `size 20`. Its `-D_GLIBCXX_DEBUG` build aborts on an empty `front()` in a control
and aborts on **none** of its six cases.

**Seat 07 (same instrument, independent).** Ran the same instrument, reached the same conclusion, and
**withdrew its own identical S-F2 claim**. So the two seats that investigated the mechanism directly now agree.

**Me (my own `-D_GLIBCXX_DEBUG` build, `checks/check_2640_instrument.py`).** I did not take theirs on trust; I
built and ran my own. Control (empty `front()` under the same flag), from
`checks/s2640/check_2640_instrument.txt`:

```
control (empty front() under the same flag): returncode -6 -> ABORTS (checking is really on)
control output: about to call front() on an empty vector | /usr/include/c++/13/debug/vector:460: |
  In function: std::debug::vector<_Tp, _Allocator>::reference ... front() ...
  Error: attempt to access an element in an empty container.
```

and the six cases:

```
case           bestmove  exit  glibcxx_diagnostic  verdict
no_names       0000      0     False              no abort -> 2640 never saw an empty list here
bogus_name     0000      0     False              no abort -> 2640 never saw an empty list here
illegal_pair   0000      0     False              no abort -> 2640 never saw an empty list here
one_legal      e2e4      0     False              no abort -> 2640 never saw an empty list here
two_legal      d2d4      0     False              no abort -> 2640 never saw an empty list here
plain_control  d2d4      0     False              no abort -> 2640 never saw an empty list here
```

The control proves the checking is really on; no case aborts. **So 2640 does not execute with an empty
`root_candidates` on any of these six cases.** My mechanism claim is refuted by my own instrument as well as
by two other seats'.

## The corrected finding
- The **observable** (confirmed by three seats independently) is: on a board with 20 legal moves,
  `go searchmoves` naming no legal root move answers
  `info string searchmoves restriction has no legal root moves`, then literal
  `info depth 1 seldepth 1 score cp 0 nodes 0 nps 0 hashfull 0 time 0 pv` lines (empty pv), then
  `bestmove 0000` — a **fabricated** `nodes 0` / `cp 0` line and a `0000` that UCI reserves for "no legal
  move exists".
- The **mechanism** is the empty-root early path at `search.cpp:2253`, whose `root_drawn`/empty-candidate
  block reports without searching. Line 2640 is not involved. UCI-wise the defect is that `0000` is used to
  mean "your restriction matched nothing", which a GUI reads as "no legal move exists".

## My other observation, one sentence, kept because it is right
ASan and UBSan reporting nothing on these cases is consistent with **there being no read at all**, so I no
longer offer that silence as support for any mechanism.

## What this changes in my own record
- S-C3's verdict on seat 17's S-F1 stands: **CONFIRMS** (the `0000` on a 20-legal-move board).
- S-C3's mechanism sentence is **withdrawn** and replaced by the corrected statement above (S-C4).
- My S-F2-style reading in `checks/CHECK_s17f1.md` is superseded by this file.
