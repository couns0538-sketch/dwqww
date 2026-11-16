# AUDIT: does any single replacement-scan percentage survive as a HEADLINE? (seat 29)

Run after the 29-F39 correction, over the whole seat folder. Every surviving instance of 11.1 / 26.5 / 19.5 / 54.7 /
44.8 is listed with what it is: a historical record, a correction pointer, or a cell of the four-cell table.

## The two statements allowed to appear as current
1. bench 13 reaches the age/depth comparison **50 times in 861,904 probes (0.006 %)**, matching seat 19's 19-F18
   bench figure to the digit.
2. In real play the share is **configuration-dependent**: 6.3 % (Hash 16, depth 10), 44.8 % (Hash 16, depth 12),
   0.1 % (Hash 64, depth 10), 2.4 % (Hash 64, depth 12) — always quoted with depth AND hash. Probe counts are
   identical across Hash sizes at a given depth, so what varies is SATURATION (how often a scan finds an empty
   slot), not the search.

## Where each surviving figure sits, and why it is not a headline
| file : line | figure | status |
|---|---|---|
| `FINDINGS.md:45` | 44.8 / 0.1 / 2.4 | the four-cell table inside the 29-F35 rule — CORRECT FORM |
| `FINDINGS.md:49` | 54.7 (seat 19's) | explicitly placed inside my measured range — CORRECT FORM |
| `FINDINGS.md:115` (29-C8) | 26.5 | row carries "SUPERSEDED IN PART by 29-F37" — HISTORICAL |
| `FINDINGS.md:116` (29-F37) | 26.5 / 19.5 / 13.6 / 11.1 | the set-size convergence record, which is what established that SETTINGS and not set size caused the earlier gap — HISTORICAL |
| `FINDINGS.md:118` (29-F38) | — | marked "SUPERSEDED BY 29-F39 — do not quote the 11.1 %" — CORRECTION POINTER |
| `FINDINGS.md:119` (29-F39) | 0.1 / 44.8 | the finding that does the superseding — CORRECT FORM |
| `FINDINGS.md:120` (29-N20) | 11.1 | the instruction not to quote it — CORRECTION POINTER |
| `FINAL_NOTES.md:6` | 11.1 | opens with "that was wrong to present as a single number" — CORRECTION |
| `FINAL_NOTES.md:13` | four-cell table | CORRECT FORM |
| `FINAL_NOTES.md:24` | 0.1 to 44.8, 54.7 inside the range | CORRECT FORM |
| `STATUS.md` (several blocks) | all of the above | append-only diary: earlier blocks record what I believed WHEN. Not rewritten; blocks from 29-F39 onward say the figure was overturned. |
| `REPORT_job2.md:25` | 0.006 | unrelated: the `__restrict` instruction-count result, a different measurement |

## Result
**No single percentage survives as a headline anywhere in the folder.** Every instance is either (a) the corrected
four-cell table quoted with depth and hash, (b) a historical record explicitly marked superseded, or (c) an
instruction not to quote the old figure. `STATUS.md` is deliberately append-only and is not edited retroactively:
its earlier blocks are the honest record of what I concluded at the time, and the later blocks correct them.

Reproduce this audit:
```bash
cd forge-combo29/swarm/29 && grep -rn "11\.1\|26\.5\|19\.5\|54\.7\|44\.8" --include=*.md . | grep -v "^./slots/raw_"
```
