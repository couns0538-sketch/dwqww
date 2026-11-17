# seat 20 — job 76: at `go nodes 20000` the engine claims a 14-ply mate where the truth needs 8

**The number to lead with: two-fold.** `go nodes 20000` reports **`mate −7`**, which requires a 14-ply mate; the true
forced distance on that board is **8 plies**, proved exhaustively. The engine reports a mate **twice as far away as it
is** — and 20,000 nodes is one of the owner's three match budgets.

Seat 05's S-F64 claims the mate-PV truncation is a *narrow window that lands on a real match budget*, not one
position's quirk. I checked it on the board I know best — `8/8/1p6/8/p3p3/8/2Kpk3/8 w`, whose **true forced distance is
mate −4 = 8 plies**, proved exhaustively in job16 (False at 1..7 plies, True at 8).

Exe: PC r15, sha256 `068f0927768d30be…`, `id name Chess Engine Forge 6.4.24 candidate`.
Settings: **PC20 = S14 (17 options) + 6 extras**, `assert_regime(..., "PC20")` passed — named with its count per the
practice from seat 30's retraction. Threads 1, Hash 16.

## Result

| `go nodes` | score | depth | nodes used | PV plies | verdict |
|---|---|---|---|---|---|
| **20,000** | **mate −7** | 8 | 18,729 | **10** | **TRUNCATED — short by 4** (needs 14 for −7) |
| 50,000 | mate −4 | 16 | 49,511 | 8 | full PV, and the **true** distance |
| 250,000 | mate −4 | 64 | 231,640 | 8 | full PV, true distance |

## What this confirms
1. **The truncation lands on `go nodes 20000` — one of the owner's three match budgets.** At that budget the engine
   reports **`mate −7` with a 10-ply PV**, i.e. a mate distance it cannot back, while the truth is −4. At 50,000 and
   250,000 it is correct.
2. **It is a window, exactly as seat 05 describes.** The same position is wrong at 20,000 and right at 50,000 — so the
   defect is not "PC20 mishandles mates" but "a specific node budget truncates the PV".
3. **This is on a board whose true distance I proved by exhaustive search**, so unlike most mate-PV findings the
   "needs N plies" column is not taken from the engine's own claim.
4. **The score at 20,000 is wrong in distance, not merely short in display:** `mate −7` claims a 14-ply mate where the
   real one is 8 plies. That is the same class as my S-F22 finding on the base tree, reproduced here on the PC build at
   a match budget.

## Why it matters for the owner
A match run at 20,000 nodes can, on a long-mate position, print a mate distance that overstates the defence — and
`go nodes 20000` is one of the three budgets his matches actually use. It does not change the chosen MOVE here
(`c2b1` at 20,000, matching the depth-20 answer), but a GUI reading the score sees `mate −7` when the true value is
`mate −4`.

## Limits
- One position, three budgets. Seat 05's S-F64 is the wider sample and this is an independent corroboration of the
  shape, not a rate.
- `go nodes` only; the clock path was not re-tested here (S-F49 covers the clock separately).
- Built-in net, Threads 1.


## Does the wrong SCORE ever become a wrong MOVE? — checked, and no

The severity question. Same PC20 settings, `go nodes 20000` vs `go depth 20`, on three boards:

| board | `go nodes 20000` | `go depth 20` | move |
|---|---|---|---|
| S-F19 board (true mate −4) | c2b1 / **mate −7** / 10-ply PV | c2b1 / mate −4 / 8-ply PV | **SAME** |
| seat 05's violator | b3c2 / **cp 4056** / 10-ply PV | b3c2 / mate 7 / 13-ply PV | **SAME** |
| mate-in-1 control | d1d8 / mate 1 / 1 ply | d1d8 / mate 1 / 1 ply | **SAME** |

**The move is identical in all three**, including on seat 05's violator where the node budget reports `cp 4056` instead
of `mate 7`. So the defect is confined to **the reported score and PV** — a mate distance that overstates the defence,
and a mate that reads as a large centipawn advantage. **Move choice at a match budget is unaffected in these three
cases**, which is the reassuring half and bounds the severity: this is a reporting defect, not a playing one.

That also means the risk is where the score is *consumed*: a GUI showing `mate −7` when it is `mate −4`, or a
mate-distance-based adjudication, or an operator reading the eval. Not a lost game.
