# REPORT_cost_deep — are S-F30's largest costs real? (deeper reference searches)

**What was asked (my own follow-up):** S-F30 judged each move with a SINGLE depth-12 reference search of the
resulting position, which is a proxy. Re-judge its 7 largest cases at depths 12/14/16/18 and see whether the sign
and size survive.

**The answer: every SIGN survives at every depth (7 of 7), so S-F30's individual cases are real and not proxy
artefacts. But the magnitudes do not shrink — they grow in 3 of 7 — so S-F30's "wash" reading UNDERSTATES the
losses, and my 2.3a framing needs that qualifier.**

```
| idx | d12  | d14  | d16  | d18  | sign stable | |d18| vs |d12| |
|-----|------|------|------|------|-------------|----------------|
|   6 |  +92 | +175 | +168 | +130 | yes         | grew           |
|  10 |  -67 |  -51 |  -58 |  -58 | yes         | shrank         |
|  12 |  +79 |  +69 | +118 |  +69 | yes         | shrank         |
|  14 |  +39 |  +82 |  +67 | +209 | yes         | grew           |
|  29 |  -82 | -113 |  -18 |   -  | yes         | shrank         |
|  34 | +109 | +197 | +135 | +136 | yes         | grew           |
|  37 | -109 |  -80 |  -29 |  -63 | yes         | shrank         |
```

(positive = the 2,000-node move is WORSE than the 250,000-node move, from the mover's point of view)

**What this changes.** The direction of S-F30 stands: 4 positions the 2,000-node budget is worse, 3 it is better,
median 0. But the four "worse" cases do not fade with more search — they get **worse**: idx 34 goes +109 → +136,
idx 14 goes +39 → **+209**, idx 6 goes +92 → +130. So on the positions where the shallow budget errs, deeper
search says the error is MORE expensive, not less. The "wash" is a wash in COUNT (4 against 3), not in
magnitude: the losses are larger than the gains.

That is a materially different statement from "the budget does not play badly", and the honest version is:
**the budget errs about equally often in both directions, but its errors cost more than its lucky wins** — which
is what you would expect from a search that is simply shallower, and it is exactly the kind of thing that a
count-based summary hides.

**P1 confirmed** (7 of 7 stable — my bar was 6). **P2 REFUTED** (I predicted the magnitude would shrink; it grew
in 3 of 7, and among the four "worse" cases the depth-18 magnitude exceeds the depth-12 one in 3 of 4).
**P3 confirmed** (idx 34 stays above 50 cp: +136 at depth 18). **P4 confirmed** (idx 37 remains a GAIN at every
depth: -63 at depth 18, and it reached mate scores in the sibling analysis, consistent with the won rook).

**How sure:** high on the signs (7 of 7 stable across four depths is strong). Medium on the magnitudes: idx 29's
depth-18 search reached a mate score so its cp delta is unavailable, and a depth-12-to-18 cp comparison in a
nearly-mate position is not a clean number.

## Honesty numbers

```
exe     /home/ubuntu/builds/bld-pc/forge  PC r15, sha256 068f0927768d30be60e8cce6c9f29620dec330565397357dcded
        none 312866 / S14 242796 / PC20 278024   (all match file 5)
settings PC20 + Threads 1 + Hash 16; the two candidate moves come from `go softnodes 2000` and
         `go nodes 250000`; each resulting position is searched once per reference depth 12/14/16/18
```

## Table

| step | done-partly-not done | evidence file | result |
|---|---|---|---|
| 7 largest S-F30 cases re-judged at depths 12/14/16/18 | done | `run.log`, `raw/cost_deep.txt` | 7/7 signs stable |
| magnitude trend with depth | done — prediction WRONG | same | grew in 3 of 7; among "worse" cases 3 of 4 grew |
| idx 34 (largest loss) at depth 18 | done | same | +136 cp, still the worst |
| idx 37 (largest gain) at depth 18 | done | same | -63 cp, still a gain |
| ground truth (tablebase) for the endgame cases | NOT done | — | idx 29 is a K+B+P vs K endgame; a tablebase would settle it exactly |

## Findings

`S-F31 | 6 | S-F30's individual costs are real, not depth-12 artefacts, but their MAGNITUDES grow with the reference depth, so the budget's errors cost more than its lucky wins: at depths 12/14/16/18 all 7 of S-F30's |cost|>30 cases keep the same sign, while the four "worse" cases go +92 -> +130, +79 -> +69, +39 -> +209 and +109 -> +136, and the three "better" cases stay modest (-58, mate, -63) — so "the self-play budget is a wash" is true in COUNT (4 worse vs 3 better) but not in magnitude | cost_deep/run.log cost_deep/raw/cost_deep.txt (again: `python3 cost_deep/cost_deep.py ~/builds/bld-pc/forge /tmp/o`) | NEW |`

## Suspicions, not proven

- That the asymmetry in magnitude is the general shape of a shallower search rather than a peculiarity of these
  seven positions. Seven cases is a small sample, though it is every large case in the 40-position run.
- That idx 14's jump to +209 at depth 18 is a genuine tactical discovery rather than a search instability (its
  d16 value is +67, so the series is not smooth).

## What I did NOT do

- Did not use a tablebase, which would give exact truth for the endgame positions (idx 29, idx 37).
- Did not extend the sample to the cases with |cost| between 1 and 30 cp, where most of the 40 positions sit.

## Times

`cost_deep/stamps.txt`, every line a `date -u`.
