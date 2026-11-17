# REPORT_v3_Step2_baseline — RECONCILED: 27,944,084 reproduces EXACTLY on seat 08's set

**The discrepancy I raised is closed, and the fault was mine: I measured a different position set.**

## The reconciliation

```
set                                  positions                          node sum
first 200 of set_G.epd (mine)        200                                27,762,950
seat 08's OG200 (O100 + G100)        200                                27,944,084   <- MATCHES the figure exactly
```

On seat 08's committed set `forge-combo29/swarm/08/job1/OG200.fens` my build reproduces **27,944,084 exactly**, and
the individual rows match too:

```
row 1  mine 110540   seat 08 110,540
row 2  mine 126001   seat 08 126,001
row 3  mine 118474   seat 08 118,474
```

**So the identity baseline for Step 2 is 27,944,084**, measured independently on my build. There is no unexplained
second baseline and nothing to re-open.

## What I got wrong, precisely

I measured "the first 200 of `set_G.epd`" because file 7 says "your 200 openings at `go depth 12`" without pinning
which 200, and my folder already held `set_G.epd`. That produced 27,762,950 — **a legitimate measurement of a different
set**, which I then reported as a gap against a figure whose provenance I had not established. I searched file 7,
handoff files 1–6 and five seats' FINDINGS, found nothing, and concluded the figure was unattributable.

**The figure WAS attributable — to seat 08, in `swarm/08/v3/profile/openings_baseline.txt` — and I never looked
there.** My search covered the handoff branch and the FINDINGS files but not other seats' `v3/` report folders. That
is the specific mistake: **I searched where I expected the number to live, not where a seat doing the same job would
have written it.**

This is the third time today I have built an explanation on an unsearched premise (hardware, perf redirection, now
provenance), and it is the same shape each time: a plausible story in place of one more lookup.

## The trap the coordinator flagged, and it did not bite

`profile_openings.py` in seat 08's folder hard-codes `/tmp/o100.fens`, which is not in the repo. The committed rows are
in `OG200.fens`, so I used that file directly rather than running their script. **The first-two-rows check
(110,540 / 126,001) confirms I read the right file** — that was the right way to validate the set before trusting the
sum, and it is why the reproduction is credible rather than coincidental.

## The corrected baseline, for Step 2

```
identity     27,944,084 nodes over 200 positions
positions    forge-combo29/swarm/08/job1/OG200.fens  (O100 + G100; first 100 of O then first 100 of G)
settings     depth 12, PC20 (the 20 option values) + OwnBook false, test net via NNUEArchFile then NNUEArch,
             Threads 1, Hash 16, ucinewgame + isready before every position, each search driven to bestmove
rows         v3/ident_OG200.txt  (200 rows + sum)
exe          /home/ubuntu/builds/bld-v3/forge
```

## Honesty numbers

```
exe   /home/ubuntu/builds/bld-v3/forge   g++ 13.3.0, -march=x86-64-v4, FORGE_NNUE_V3=1, FORGE_MATE_ALPHA_GUARD=1
net   /tmp/test.fnn3  checksum fdff70de72e4ca82
runs  200 of 200, sum 27,944,084, wall 15 s
```

## Table

| step | done-partly-not done | evidence file | result |
|---|---|---|---|
| fetch seat 08's position set | done | `OG200.fens` (from `for-fable-and-opus/swarm-08`) | 200 lines, first two as quoted |
| re-measure on that set | done | `ident_OG200.txt` | **27,944,084 EXACTLY** |
| first-two-rows sanity check | done | same | 110540 / 126001 match |
| my earlier "unattributable figure" claim | **WITHDRAWN** | this report | the figure was seat 08's, on a different set |
| my earlier 27,762,950 | kept, relabelled | `ident_base.txt` | a valid measurement of the first 200 of set_G |

## Findings

`v3 | the Step 2 identity baseline is RECONCILED at 27,944,084 nodes: on seat 08's committed position set (swarm/08/job1/OG200.fens = first 100 of O + first 100 of G) my build reproduces the sum exactly and the first three rows exactly (110540 / 126001 / 118474). My earlier 27,762,950 was the first 200 of set_G.epd — a different set, a valid measurement of the wrong thing. My claim that 27,944,084 was "unattributable" is WITHDRAWN: it is seat 08's figure in swarm/08/v3/profile/openings_baseline.txt, and I had searched only the handoff branch and FINDINGS files, not other seats' v3 report folders | v3/ident_OG200.txt v3/REPORT_step2_baseline.md | NEW |`

## Suspicions, not proven

- None. This row is settled by exact agreement on the sum and the first three rows.

## Times

`v3/stamps.txt`, every line a `date -u`.
