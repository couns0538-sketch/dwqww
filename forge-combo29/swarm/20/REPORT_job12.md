# REPORT job12 — seat 20, area 10 job 1 (eighth check): seat 05's S-F1 and seat 25's S-F1

**what was asked** — Reproduce the mate-distance finding two seats reported on the same board
`8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1`: at depth 12 the engine reports `score mate -12` with an 18-ply PV that is not
checkmate.

**the answer** — **CONFIRMS both, with a condition neither seat stated: it happens only with the project's S14
tunables set.** Under S14: depth 12 = `mate -12` with an 18-ply all-legal PV ending in a non-mate position with 2
legal moves left (exactly seat 25's number); depth 14 = `mate -9` with 15 of 18 plies. Under the engine's DEFAULT
settings the same board is consistent at depths 10/12/14/16/20 (mate −7/−7/−6/−4/−4, every PV ending in checkmate in
exactly the claimed number of plies). And S14 makes the mate *slower to converge*: S14 depth 16 proves a 12-ply
mate, while default depth 16 proves an 8-ply mate — so S14's depth-12 claim of 24 plies is a two-fold overstatement
of the true distance.

**how sure** — certain for the measurements; the attribution to "the S14 values" is a correlation over one board,
and I did not bisect the 14 options.

## Honesty numbers
`/agent/repos/build-base/forge` sha256 `e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83`, pins
4/4 (`../HONESTY.txt`). Every `setoption` was followed by `isready` and the transcripts were scanned for
`unknown option` / `invalid value` — none appeared in any run (`refusals` field in the JSON is empty).

## Step table
| step | done-partly-not done | evidence file | result |
|---|---|---|---|
| prediction, alone | done | `PREDICTION.txt` | 5 predictions |
| first run, DEFAULT settings | done, CONTRADICTED prediction 1 | `out_check.txt` | every mate PV consistent |
| S14 applied, side by side | done | `out_check_s14.txt`, `check_mate_pv_s14.json` | bug reproduces exactly at depth 12/14 |
| PV replayed with python-chess | done | same | 18/18 legal, ends NOT in mate, 2 legal moves after |
| cross-depth true value | done | `out_check_s14.txt` | S14 d16 mate −6 (12 plies), default d16 mate −4 (8 plies) |

## Findings
1. **S-C9 = CONFIRMS seat 05's S-F1 and seat 25's S-F1**, with the S14 condition.
2. **S-F17: the instability is tuning-dependent.** S14 depth 12 claims 24 plies; S14 depth 16 proves 12; default
   depth 16 proves 8. The distance is wrong at intermediate depths under S14 and consistent under defaults.

### Suspicions, not proven
- That the cause is S14's LMR/history values changing move ordering so a longer defensive line is found first.
  Plausible, not bisected.
- Whether a PV truncated at 18 of 24 plies is itself reportable. Many engines truncate; the cross-depth
  inconsistency is the part I would send to the PC.

## What I did NOT do
- No bisection of the 14 S14 options.
- Not run on the 353-position G set (their single board only).
- Not on the job7 patched build.
- No hand-built proof of the true mate length (I relied on the engine's own deeper consistent PVs).

## What I am NOT sure about
- Whether the true mate distance is 8 plies (default depth 16's answer). Its PV is verified checkmate, which makes
  it a proof of "at most 8", not of "exactly 8". An even shorter mate would invalidate "exactly".

## Times: see `stamps.txt`
## The last command's output
```
$ ls forge-combo29/swarm/20/job12/
CHECK_s05F1_s25F1.md  PREDICTION.txt  check_mate_pv.py  out_check.txt
check_mate_pv_s14.json  check_mate_pv_s14.py  out_check_s14.txt  stamps.txt
```
