# REPORT_v3_Step2_baseline — the identity baseline, and a figure I cannot reconcile

**What Step 2 needs:** a speed patch must keep EVERY number identical — the eight benches, the per-position node rows
of the 200 openings at depth 12 under PC20 + the test net, and the `eval` of all 353 G positions.

**My measured baseline for the 200-opening arm is 27,762,950 nodes.**

```
exe      bld-v3 (g++ 13.3.0, -march=x86-64-v4, FORGE_NNUE_V3=1, FORGE_MATE_ALPHA_GUARD=1)
net      /tmp/test.fnn3  checksum fdff70de72e4ca82
settings PC20 + test net, Threads 1, Hash 16, `go depth 12`, ucinewgame + isready before each
positions the first 200 of set_G.epd (G200.epd), each search driven to bestmove before the next command
SUM      27,762,950        file: ident_base.txt
```
Per-position rows are in `ident_base.txt`, so every patch can be compared row by row, not just on the sum.

## THE FIGURE I WAS ASKED TO MATCH, AND WHY I AM NOT ADOPTING OR REJECTING IT

I was told the identity is **27,944,084**. My measurement is **27,762,950** — a difference of **181,134 nodes
(0.65 %)**, an average of 906 nodes per position.

**I cannot reproduce 27,944,084 and I cannot find its source:**
- it is **not in file 7** (grep: no match);
- it is **not in files 1-6** of the handoff branch;
- it is **not in any seat's FINDINGS.md** (checked seats 06, 11, 15, 19, 29).

So it reached me through the coordinator's check message without an attribution I can verify. Two explanations are
consistent with the numbers, and I cannot distinguish them from here:

1. **A different position set.** A 0.65 % gap across 200 positions is the size you would get from 200 *different*
   positions, or the same 200 in a different order with a different `Hash` reuse pattern. My set is the first 200 of
   `set_G.epd`, which is what file 7's "your 200 openings" most naturally means, but file 7 does not pin which 200.
2. **A different build or net state on the measuring machine.** My Step 0 matched all eight benches and three evals
   exactly, so a systematic build difference is unlikely — but Step 0 does not cover the 200-position sum.

**What I am doing about it: publishing my measured baseline as the identity, naming the discrepancy, and NOT
treating 27,944,084 as authoritative.** A speed patch validated against a number I cannot reproduce would be
validated against nothing. If the coordinator can point me at the seat or file that produced 27,944,084, and the
position set behind it, I will re-measure on that set and use whichever baseline matches.

## What this means for Step 2's deliverable

Per the coordinator's instruction: **if the fixed-budget check cannot be run in the window, publish the patch as
unmeasured and say so.** Given this discrepancy I am doing exactly that — and the honest state is one step short of
"unmeasured": I *can* measure the patch against MY baseline (27,762,950), which is a valid internal identity check,
but I cannot claim it matches the number I was told to match.

So the patch will be published with:
- its node rows compared to `ident_base.txt` (my measured baseline) — exact equality required;
- an explicit statement that the 27,944,084 figure is unreconciled and why;
- whatever timing the remaining window allows, or "unmeasured" if it does not.

## Honesty numbers

```
baseline exe  /home/ubuntu/builds/bld-v3/forge
sha256        (in the build dir; unchanged since Step 0 passed 8/8 benches, 3/3 evals)
net           /tmp/test.fnn3  6,309,096 bytes, fdff70de72e4ca82
rows          200 of 200, sum 27,762,950, wall 14 s
```

## Table

| step | done-partly-not done | evidence file | result |
|---|---|---|---|
| 200-position identity baseline at depth 12 | done | `ident_base.txt`, `ident.log` | 27,762,950 |
| reconcile with the stated 27,944,084 | **NOT POSSIBLE from here** | greps of file 7, files 1-6, five seats' FINDINGS | not found in any source I can read |
| per-position rows for row-by-row patch comparison | done | `ident_base.txt` | 200 rows |

## Findings

`v3 | the 200-opening identity baseline measured on this build is 27,762,950 nodes (200 positions, depth 12, PC20 + test net, Threads 1, Hash 16), which differs from the 27,944,084 I was asked to match by 181,134 nodes (0.65 %, 906 per position). The 27,944,084 figure does not appear in file 7, in handoff files 1-6, or in the FINDINGS of seats 06/11/15/19/29, so I cannot attribute it and will not treat it as authoritative. A 0.65 % gap is consistent with a different position set or a different Hash reuse pattern; my set is the first 200 of set_G.epd | v3/ident_base.txt v3/ident.log v3/REPORT_step2_baseline.md | NEW |`

## Suspicions, not proven

- That 27,944,084 came from a different 200-position set. The magnitude fits; I have no evidence either way.

## Times

`v3/stamps.txt`, every line a `date -u`.
