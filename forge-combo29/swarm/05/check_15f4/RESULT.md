# CHECK of seat 15's 15-F4 — seat 05 (area 5)

## Verdict: CONFIRMS, on my own positions, and it applies to my own job 2 — which I say plainly below

Seat 15's 15-F4: *"K v K, KN v K, KB v K and threefold-repetition roots all score exactly cp 0 at depth 10 S14,
but they answer with an EMPTY PV (`... time 0 pv`) and 0 nodes, so any harness that greps for `" pv "` (with a
move) silently loses these 80 positions."*

My own check, on **my** job2 positions (seed 501), my own harness, depth 10, S14:

| set | positions | cp 0 | 0 nodes | EMPTY pv | pv WITH moves |
|---|---|---|---|---|---|
| K v K | 6 | 6 | 6 | **6** | 0 |
| KN v K | 6 | 6 | 6 | **6** | 0 |
| KB v K | 6 | 6 | 6 | **6** | 0 |
| KNN v K (control) | 6 | 0 | 0 | 0 | **6** |

The literal line, verbatim from the run:

```
info depth 1 seldepth 1 score cp 0 nodes 0 nps 0 hashfull 0 time 0 pv
```

## The control that makes it a measurement
KNN v K is *not* a dead draw, and on those positions the same harness sees a **non-empty** pv with 10 moves and
real node counts (7,868–20,445). So the empty pv is a property of the dead-draw positions, not an artefact of how I
read the output. Without this control, "I found empty pvs" would be indistinguishable from "my parser is broken".

## This applies to my own job 2, and here is exactly how much
In my job2 raw files the split is:

| set | empty-pv lines | pv lines with moves |
|---|---|---|
| K v K | 200 | 0 |
| KN v K | 200 | 0 |
| KB v K | 200 | 0 |
| threefold | 200 | 0 |
| KNN v K | 0 | 200 |
| fifty99 | 0 | 200 |

(`job2/out/empty_pv_audit_job2.txt`.) **My job2 conclusions survive**, because:
- my `analyse_job2.py` regex is `\binfo\b.*\bpv\b`, which MATCHES the empty-pv line and reads its `score cp 0`
  correctly — so the `cp 0` figures in S-F5/S-F6 are scores from real info lines, not from absent lines;
- my REPORT_job2 makes **no claim about the pv content** of those sets — I said "cp 0 with 0 nodes" and never
  "the pv is …". I grepped my own report to confirm that before writing this line.
- What 15-F4 *would* have broken is a claim of the form "the pv of a drawn root is X", and a harness counting
  `" pv <move>"` as the presence test. I did neither, but I came close: my TABLE A in job1 counted `with_pv=553`
  using a regex that would also have counted an empty pv. That count would have been misleading if any of the 553
  had been empty — none was (`job1/out/empty_pv_audit.txt`: 6,636 pv lines checked, **0 empty**, 0 positions with
  an empty last pv), so the job1 number stands too.

## Beyond their finding
- **The exact empty-pv line and its depth count**: for a dead-draw root the engine emits **one empty-pv `info`
  line per depth** (6 positions × 10 depths = 60 lines in this run), not one line total. A harness that reads
  "the last pv line" gets an empty one at every depth, so "last pv" is empty whichever depth it stops at.
- **The distinction a harness needs**: three cases must be told apart — no pv line, pv line with no moves, pv line
  with moves. My check classifies all three; the third is the only one that can be replayed.

## Reproduce
```
python3 check_15f4.py /tmp/build-rel/forge
```
Raw: `raw/check_15f4.txt`.

## What I did NOT establish
- Any cause in source.
- Whether the threefold roots behave identically to the material draws in this respect. My threefold raw files
  show 200/200 empty pv lines (`job2/out/empty_pv_audit_job2.txt`), which matches, but this check re-ran only the
  four material sets.
