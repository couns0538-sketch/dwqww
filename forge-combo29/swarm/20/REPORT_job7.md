# REPORT job7 — seat 20, area 10 job 1 (fourth check): seat 28's S-F4, and what the patch does not fix

**what was asked** — Reproduce an unconfirmed NEW finding: seat 28's S-F4, that the 0-node root adjudication also
fires on `board.is_repetition()`, so a mate-in-1 board reached a third time by legal moves is adjudicated a draw.

**the answer** — **CONFIRMS**, with my own cycle and my own positions, and one thing beyond it: **seat 01's patch
is necessary but not sufficient.** On a scratch copy with seat 01's patch applied (`patch -p2 --fuzz=0`, pins
unchanged 312866 / 862329 / 3024920 / 4865609) the halfmove door is FIXED (hm 100/101/150 now find the mate) and
the repetition door is NOT (the third occurrence still answers f2f3 / cp 0 / 0 nodes). Both terms are in the same
`root_drawn` expression at `src/search.cpp:2251`.

**how sure** — certain. The third occurrence is at halfmove 8 and python-chess confirms it is a claimable
threefold, so it cannot be the halfmove door; the patched build is a separate binary (sha256 differs) whose pins
are unchanged.

## Honesty numbers
Base build `/agent/repos/build-base/forge` sha256 `e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83`;
patched scratch build `/agent/repos/scratch-patch01/build/forge` sha256 `81c52608ee74ddea5b23a37402add8543c29b13af51c316adc6247f6e3da37c9`.
Both: bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609 (patch leaves every pin
unchanged). Nothing of the scratch copy is committed; the patch itself is stored as text (`seat01.patch.txt`).

## Step table
| step | done-partly-not done | evidence file | result |
|---|---|---|---|
| prediction, alone | done | `PREDICTION.txt` | 5 predictions, all held |
| build a genuine threefold myself | done | `check_s28f4_base.json` occurrences | plies 0/4/8; threefold true at ply 8, halfmove 8 |
| the three cases, base build | done | `check_s28f4_base.json` | A mate, B mate, C cp 0 / 0 nodes |
| apply seat 01's patch | done | `patch_copy.sh` | applied cleanly, pins unchanged |
| the same three cases, patched | done | `check_s28f4_patched.json` | C still cp 0 / 0 nodes |
| control: halfmove door, both builds | done | `halfmove_control_out.txt` | base breaks at hm≥100; patched fixed at 100/101/150 |
| my own method error, recorded | done | `CHECK_s28F4.md` §"Correction to my own method" | a piped quit gave a false reading; interactive driver corrected it |

## Findings
1. **S-C4 = CONFIRMS seat 28's S-F4.** Show it again: `python3 check_s28f4.py <exe> . base`.
2. **S-F13: seat 01's patch fixes the halfmove door and not the repetition door.** Show it again: `bash rerun.sh`.
3. The two doors are adjacent in one expression, which is exactly why a one-term patch looks complete.

### Suspicions, not proven
- That `board.is_insufficient_material()` in the same expression has the same problem (a K+N v K+N-ish board
  where a mate is still constructible cannot be mated, so I expect that term to be harmless — unlike repetition).
  Not tested.
- That removing the whole `root_drawn` shortcut (keeping only `root_candidates.empty()`) is the correct repair and
  costs nothing measurable. I did not build or benchmark that variant; seat 01's patch is the only one I tested.

## What I did NOT do
- I did not write or test a patch for the repetition door.
- I did not test a repetition reached by captures/pawn moves (my cycle is the simplest reversible kind).
- I did not measure the node cost of removing the shortcut entirely.

## What I am NOT sure about
- Whether the shortcut exists for a performance reason on repetition-rich positions. If it does, the repair should
  keep the "report without searching" path only when the position is genuinely finished, and that needs its own
  measurement — which I did not do.

## Times: see `stamps.txt`
## The last command's output
```
$ ls forge-combo29/swarm/20/job7/
CHECK_s28F4.md  PREDICTION.txt  check_s28f4_base.json  check_s28f4_patched.json  check_s28f4.py
halfmove_control.py  halfmove_control_out.txt  patch_copy.sh  rerun.sh  seat01.patch.txt  stamps.txt
```
