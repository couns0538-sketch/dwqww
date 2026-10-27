# S10-2: why each rejected idea likely failed (one line each), from Sol's existing logs

OFF reference = Sol's S07 native WAC300 run of the Lprime build (same screen tool, 1000 ms, Threads 1, Hash 16,
Clear Hash per position): **271/300**. ON = each idea's single Lprime WAC300 screen. Flip lists and per-position
depth/score: `s10_wac_flips.md` (tool `opus_s10_wac_flips.py`). Node guard = Sol's Lprime release sweep.

| idea | WAC ON (vs OFF 271) | node guard d20 / d22 | why it likely failed |
|---|---|---|---|
| QuietCheckLmpSurvival | 269 (-2) | PASS (-7.9% / -12.1%) | No measurable tactical loss: -2 is inside the 1-3 point noise (11 lost / 9 gained; 6 of the 11 losses are also lost by 2-3 other ideas; its run's NPS was 11% below the OFF run's, 378k vs 424k); it failed only the absolute 283 floor, which the OFF build itself misses on that box (271). Its own 3 losses (WAC.080, .089, .169) are quiet key moves, as expected if keeping quiet checks alive spends the late-move budget. |
| ImprovingRazorGuard | 270 (-1) | **FAIL** (-24.3% / -18.5%) | Failed on the node guard, not on tactics: -1 is noise (8 lost / 7 gained, run 8% faster than OFF); turning razoring off for improving nodes swings the tree size with depth (+15.9% d16, -24.3% d20, -18.5% d22). Its B "failure" was the 180 s harness deadline, not a hang (S10-3 rerun: 31,111,774 nodes in 21.8 s). |
| SingularSiblingLmr | 263 (-8) | **FAIL** (+24.7% / +3.8%) | A real loss: 14 lost / 6 gained, 8 losses only for this idea (WAC.046, .082, .119, .191, .194, .236, .238, .264, incl. checks .082/.194 and captures .119/.238); there ON reaches only d9-d15 where OFF reaches d15-d18 (one mate) and plays the key move, matching the +24.7% nodes at d20: the extra sibling reduction likely costs re-searches in exactly these tactical trees. |
| CaptureHistoryLmp | 258 (-13) | **FAIL** (-30.8% / -23.9%) | A real loss: 15 lost / 2 gained; 4 of its 6 own losses are forcing check/mate solutions (WAC.239 f2f1, .250 e3e8 mate 8, .282 h1h8 mate 4, .288 h5f6) where ON stops at d4-d13 with a quiet move; pruning late captures with negative capture history and losing SEE likely cuts the sacrifice lines those solutions need. Its run was also 14% slower (366k vs 424k NPS; Sol notes a git upload overlapping the start), which accounts for part of the 6 shared losses. |

Positions flipped by 3-4 of the 4 ideas (WAC.033, .101, .165, .190 gained; WAC.071, .081, .193, .229, .243, .297 lost)
point at run-to-run noise of the single OFF run at 1000 ms, not at one idea. All four stay rejected (S10-1 rule).
No Elo or strength claim; WAC at 1000 ms on a loaded cloud box is a screen, not a measurement.
