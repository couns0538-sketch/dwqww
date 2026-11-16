# REPORT job11 — seat 20, area 10 job 1 (seventh check): seat 05's S-F3

**what was asked** — Reproduce seat 05's S-F3: the fifty-move draw is applied about 9 plies early — the root score
is exactly `cp 0` from halfmove 91 on their K+R v K board, not from 100.

**the answer** — **CONFIRMS**, and it is a different mechanism from my own S-C1. At `go depth 10`:

| board | first `cp 0` | nodes there | pv length |
|---|---|---|---|
| seat 05's `1K6/8/8/3R4/8/8/8/k7 w` | 91 | 16,370,887 | 9 |
| my `3k4/8/8/R7/8/8/8/7K w` | 90 | 10,972,398 | 9 |
| my `4R3/k7/8/8/8/4K3/8/8 w` | 90 | 13,462,537 | 10 |
| my `8/5K2/7Q/4k3/8/8/8/8 w` | 91 | 130,251,981 | 8 |
| my mate-in-1 board | **100** | **0** | **0 (empty)** |

So: the search sees the fifty-move horizon about ten plies before the counter gets there (millions of nodes, a full
pv), while the ROOT shortcut declares the draw at exactly 100 (0 nodes, empty pv). Only the second is the "root
adjudication" of seat 01's S-F5 / seat 28's S-F4; the first is ordinary horizon behaviour of a correct search.

**how sure** — certain for each cell (each is a single deterministic search; the node counts are in the JSON).

## Honesty numbers
`/agent/repos/build-base/forge` sha256 `e06310ec…`, pins 4/4 (`../HONESTY.txt`). Every board in the final table is
validated by python-chess (`assert b0.is_valid()`) before it is measured — see the correction below for why that
guard exists.

## Step table
| step | done-partly-not done | evidence file | result |
|---|---|---|---|
| prediction, alone | done | `PREDICTION.txt` | 5 predictions, all held |
| first sweep | done and DISCARDED | — | two of my boards were ILLEGAL FENs; one gave a nonsense row |
| legality guard added | done | `check_s05f3.py` | the guard then caught the second bad board |
| final sweep, 5 legal boards | done | `out_check.txt`, `check_s05f3.json` | onset 90/90/91/91, mate board 100 |
| source read | done | `CHECK_s05F3.md` | `is_draw` at halfmove >= 100 in-tree |

## Findings
1. **S-C8 = CONFIRMS seat 05's S-F3.** Show it again: `python3 check_s05f3.py <exe> <outdir>`
2. **S-F16: two mechanisms produce `cp 0` and only the node count tells them apart.** Root shortcut: 0 nodes,
   empty pv, exactly at 100. In-tree horizon: millions of nodes, full pv, from ~90.
3. My own error, recorded: I put two illegal FENs in my first board list. The engine refused them with
   `invalid FEN: side that moved left its king in check` and kept the PREVIOUS position, so I was measuring that.
   Added `assert python-chess is_valid` to the script; no row from those boards appears anywhere in the final data.

### Suspicions, not proven
- That the exact onset value (90 vs 91) is a function of how many plies the fifty-move horizon is from the deepest
  leaf, i.e. predictable from the depth and the counter. I observed the values, I did not derive the rule.

## What I did NOT do
- I did not sweep depths other than 10 (the onset must move with depth: a deeper search reaches the horizon sooner
  in counter terms, or later — worth measuring, not measured here).
- I did not test halfmove 100+ with a mate in the tree (only the mate-in-1 root case).
- I did not test the patched build (job7's scratch copy) on this sweep.

## What I am NOT sure about
- Whether the early zero is "wrong" at all: a search that can see a forced fifty-move draw ten plies ahead is
  correct to score it 0. The finding is about where the zero appears, not that it is a bug.

## Times: see `stamps.txt`
## The last command's output
```
$ ls forge-combo29/swarm/20/job11/
CHECK_s05F3.md  PREDICTION.txt  check_s05f3.json  check_s05f3.py  out_check.txt  stamps.txt
```
